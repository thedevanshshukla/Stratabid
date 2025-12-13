import os
import re
import json
import requests
import numpy as np
import pandas as pd
from typing import Dict, Any, List

# Import data from your setup file
from setup_data import SAMPLE_RFP_TEXT, DATASHEET_RECORDS, setup_vector_db, TESTS_PRICING

# ==========================================
# 1. SALES AGENT (The Parser)
# ==========================================
class SalesAgent:
    def __init__(self, api_key_env_var: str = "GEMINI_API_KEY"):
        self.api_key = os.environ.get(api_key_env_var)

    def parse_rfp(self, text: str) -> Dict[str, Any]:
        return self._fallback_parse(text)

    def _fallback_parse(self, text: str) -> Dict[str, Any]:
        """Robust parsing that handles both JSON inputs and Regex extraction."""
        
        # --- 1. TRY JSON PARSING FIRST ---
        # If the user pastes valid JSON (like your test case), use it directly!
        try:
            cleaned = text.strip()
            if cleaned.startswith("{") and cleaned.endswith("}"):
                data = json.loads(cleaned)
                return {
                    "Voltage": float(data.get("Voltage", 1.1)),
                    "Cores": float(data.get("Cores", 3)),
                    "Conductor_Material": data.get("Conductor_Material", "Aluminum"),
                    "Insulation_Type": data.get("Insulation_Type", "XLPE"),
                    "Fire_Retardant": bool(data.get("Fire_Retardant", False)),
                    "Quantity_m": int(data.get("Quantity_m", 1000))
                }
        except Exception:
            pass # Not valid JSON, fall back to Regex logic below

        # --- 2. FALLBACK TO REGEX ---
        t = text.lower()
        
        # Quantity
        qty = 1000
        m_qty = re.search(r"(\d{3,7})\s*m", t)
        if m_qty: qty = int(m_qty.group(1))

        # Voltage
        voltage = 1.1
        m_volt = re.search(r"(\d+(\.\d+)?)\s*k?v", t)
        if m_volt: voltage = float(m_volt.group(1))

        # Cores
        cores = 3.0
        m_core = re.search(r"(\d+(\.\d+)?)\s*-?\s*(?:core|c)\b", t)
        if m_core: cores = float(m_core.group(1))

        # Material
        cond = None
        
        # 1. Check for specific known metals (STRICTER REGEX)
        # \b ensures we match "Al" as a whole word, not inside "Materi-al"
        if re.search(r"\b(copper|cu)\b", t):
            cond = "Copper"
        elif re.search(r"\b(aluminum|aluminium|al)\b", t):
            cond = "Aluminum"
        
        # 2. Smart Regex: Catch whatever follows "Conductor:" if not found above
        if not cond:
            # Matches "Conductor: Stranded Nickel" -> captures "Nickel"
            m_generic = re.search(r"conductor\s*[:\-]?\s*(?:stranded\s+)?([a-z]+)", t)
            if m_generic:
                cond = m_generic.group(1).capitalize()

        # Insulation
        ins = "XLPE"
        if "pvc" in t: ins = "PVC"

        # Fire Retardant
        fr = False
        if any(x in t for x in ["fire retard", "frls", "fr grade"]): fr = True

        return {
            "Voltage": voltage,
            "Cores": cores,
            "Conductor_Material": cond,
            "Insulation_Type": ins,
            "Fire_Retardant": fr,
            "Quantity_m": qty
        }

# ==========================================
# 2. TECHNICAL AGENT (The Matcher)
# ==========================================
class TechnicalAgent:
    def __init__(self):
        # FIX: Ensure records is a DataFrame
        self.records = pd.DataFrame(DATASHEET_RECORDS)
        # Initialize Vector DB
        self.index, self.embeddings, self.model = setup_vector_db(DATASHEET_RECORDS)

    # In agents.py -> TechnicalAgent class

    def search(self, rfp_spec: Dict[str, Any], top_k: int = 3) -> List[Dict[str, Any]]:
        # 1. Semantic Search (Vector DB)
        query = self._rfp_to_query_text(rfp_spec)
        q_emb = self.model.encode([query], convert_to_numpy=True)[0]
        
        # Search FAISS (Get raw candidates based on text similarity)
        D, I = self.index.search(np.array([q_emb]), top_k)
        
        results = []
        for dist, idx in zip(D[0], I[0]):
            rec = self.records.iloc[idx].to_dict()
            
            # 2. Calculate Spec Match Score (The "Real" Accuracy)
            score = self.calculate_spec_match(rfp_spec, rec)
            results.append({
                "record": rec, 
                "distance": float(dist), 
                "Spec_Match_%": score
            })
        
        # --- CRITICAL FIX: RE-SORT BY SCORE ---
        # Ignore vector rank; trust the rule-based score.
        # This moves the 100% match to Rank 1.
        results.sort(key=lambda x: x["Spec_Match_%"], reverse=True)
        # --------------------------------------
            
        return results

    def _rfp_to_query_text(self, rfp_spec: Dict[str, Any]) -> str:
        parts = []
        for k, v in rfp_spec.items():
            if v: parts.append(f"{k}: {v}")
        return "; ".join(parts)

    def calculate_spec_match(self, rfp_spec, sku_spec):
        """
        Calculates Spec Match % using Weighted Average Formula:
        Score = 100 * (Sum(w_i * score_i) / Sum(w_i))
        """
        
        # --- 1. DEFINE WEIGHTS (w_i) ---
        # Adjust these to change business priority
        weights = {
            "Voltage": 35.0,        # Critical safety param
            "Material": 30.0,       # Critical cost param
            "Cores": 20.0,          # Functional param
            "Insulation": 10.0,     # Standard param
            "Fire_Retardant": 5.0   # Feature param
        }
        
        # --- 2. CALCULATE INDIVIDUAL SCORES (score_i) ---
        # Each score is between 0.0 and 1.0
        scores = {}
        
        # A. Voltage Logic (Numeric Range / Proximity)
        r_volt = float(rfp_spec.get("Voltage", 1.1))
        s_volt = float(sku_spec.get("Voltage", 1.1))
        
        if s_volt >= r_volt:
            scores["Voltage"] = 1.0  # Perfect or Safe Overkill
        else:
            # Proximity Penalty: 33kV for 132kV gets partial credit (0.25), 
            # 1.1kV for 132kV gets almost zero (0.008).
            scores["Voltage"] = s_volt / r_volt 

       # B. Material Logic (Categorical Strict & Case Insensitive)
        # 1. Safe get and lowercase the RFP requirement
        raw_rmat = rfp_spec.get("Conductor_Material")
        r_mat = str(raw_rmat).lower() if raw_rmat else None
        
        # 2. Safe get and lowercase the Database Record
        s_mat = str(sku_spec.get("Conductor_Material", "")).lower()
        
        if r_mat is None:
            # SAFETY CATCH: Parser couldn't find material. 
            scores["Material"] = 0.0 
        elif r_mat in s_mat or s_mat in r_mat:
            scores["Material"] = 1.0 # Match! (e.g. "aluminum" == "aluminum")
        else:
            scores["Material"] = 0.0 # Mismatch (e.g., copper != aluminum)

        # C. Cores Logic (Numeric Exact vs Wasteful)
        r_core = float(rfp_spec.get("Cores", 3))
        s_core = float(sku_spec.get("Cores", 3))
        
        if s_core == r_core:
            scores["Cores"] = 1.0
        elif s_core > r_core:
            scores["Cores"] = 0.5  # Partial credit (Usable but wasteful)
        else:
            scores["Cores"] = 0.0  # Fail (Not enough wires)

        # D. Insulation Logic (Categorical Loose)
        r_ins = str(rfp_spec.get("Insulation_Type", "XLPE")).lower()
        s_ins = str(sku_spec.get("Insulation_Type", "")).lower()
        scores["Insulation"] = 1.0 if r_ins in s_ins else 0.0

        # E. Fire Retardant Logic (Boolean)
        r_fr = rfp_spec.get("Fire_Retardant", False)
        s_fr = sku_spec.get("FR_Grade", False) # Key mapped correctly
        
        if r_fr and not s_fr:
            scores["Fire_Retardant"] = 0.0 # Requested but missing -> Fail
        else:
            scores["Fire_Retardant"] = 1.0 # Present OR Not Requested -> Pass

        # --- 3. APPLY FORMULA ---
        # Numerator: Sum(Weight * Score)
        weighted_sum = sum(weights[k] * scores[k] for k in weights)
        
        # Denominator: Sum(Weights)
        total_weight = sum(weights.values())
        
        # Final Percent
        final_match_percent = (weighted_sum / total_weight) * 100.0
        
        return round(final_match_percent, 1)

    def build_comparison_table(self, rfp_spec, matches):
        rows = []
        keys = ["Voltage", "Cores", "Conductor_Material", "Insulation_Type", "Fire_Retardant"]
        
        for k in keys:
            row = {"Parameter": k, "RFP Requirement": rfp_spec.get(k)}
            for i, m in enumerate(matches):
                # Map Key for Display
                lookup_key = "FR_Grade" if k == "Fire_Retardant" else k
                val = m["record"].get(lookup_key)
                
                # Format Booleans for readability
                if isinstance(val, bool): val = "Yes" if val else "No"
                if isinstance(row["RFP Requirement"], bool): 
                    row["RFP Requirement"] = "Yes" if row["RFP Requirement"] else "No"
                
                row[f"Rank #{i+1} SKU"] = val
            rows.append(row)
        return rows

# ==========================================
# 3. PRICING AGENT (The Calculator)
# ==========================================
class PricingAgent:
    def price_tests_and_consolidate(self, product_recs, tests_required, quantity_m):
        consolidated = []
        
        for p in product_recs:
            rec = p["record"]
            
            # 1. Material Cost
            base_price = rec.get("Base_Price_per_m", 0)
            mat_price = base_price * quantity_m
            
            # 2. Service Cost
            serv_price = sum(TESTS_PRICING.get(t, 0) for t in tests_required)
            
            # 3. Total
            total = mat_price + serv_price
            
            consolidated.append({
                "SKU_ID": rec.get("SKU_ID"),
                "Material_Price": mat_price,
                "Services_Price": serv_price,
                "Total_Price": total
            })
            
        return {"per_product": consolidated}