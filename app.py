import streamlit as st
import time
import pandas as pd
from datetime import datetime, timedelta
from agents import SalesAgent, TechnicalAgent, PricingAgent
from setup_data import SAMPLE_RFP_TEXT

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Asian Paints Challenge IV | Agentic RFP Engine",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .big-font { font-size:24px !important; font-weight: bold; }
    .success-box { padding: 20px; background-color: #d4edda; color: #155724; border-radius: 10px; border: 1px solid #c3e6cb; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR ---
st.sidebar.title("Agent Command")
st.sidebar.info("System Ready")
st.sidebar.markdown("---")
st.sidebar.subheader("Configuration")
auto_mode = st.sidebar.checkbox("Enable Auto-Submit", value=True)
st.sidebar.markdown("*Uncheck to require human approval.*")

# --- MAIN LAYOUT ---
st.title("Automated RFP Response Engine")
st.markdown("### End-to-End B2B Tender Automation for Wires & Cables")

# ==========================================
# PHASE 1: INPUT & SALES AGENT
# ==========================================
st.markdown("---")
st.header("1. RFP Input (Sales Agent)")

col1, col2 = st.columns([2, 1])

with col1:
    # MANUAL INPUT FIELD
    rfp_input_text = st.text_area(
        "Paste RFP Requirement Text:", 
        height=200, 
        value=SAMPLE_RFP_TEXT, # Pre-fill with sample for easy demo
        help="Paste the raw text from the tender document here."
    )
    
    process_btn = st.button("Process RFP", type="primary")

with col2:
    st.info("**Demo Tip:** You can edit the text on the left to test different scenarios (e.g., change '1.1kV' to '3.3kV' or remove 'Fire Retardant').")

if process_btn:
    # --- START WORKFLOW ---
    
    # 1. PARSING
    sales = SalesAgent()
    with st.spinner("Sales Agent is parsing requirements..."):
        time.sleep(1.0) # Illusion of processing
        
        # Parse the input text
        rfp_spec = sales.parse_rfp(rfp_input_text)
        
        # Create a Mock RFP Object wrapper so the rest of the app works
        selected_rfp = {
            "id": "MANUAL-INPUT-001",
            "title": "Manual Web Submission",
            "due_date": datetime.now() + timedelta(days=45), # Fake due date
            "text": rfp_input_text,
            "tests_required": ["Routine Test", "Type Test"] # Default assumption
        }
    
    st.success("RFP Parsed Successfully!")
    
    # Show Parsed Structure
    with st.expander("View Structured Data (JSON)", expanded=True):
        st.json(rfp_spec)

    # ==========================================
    # PHASE 2: TECHNICAL AGENT
    # ==========================================
    st.markdown("---")
    st.header("2. Technical Agent: Semantic Matching")
    
    tech = TechnicalAgent()
    
    with st.spinner("Querying Vector Database & Calculating Scores..."):
        time.sleep(0.5) 
        # Note: We pass the FULL rfp_spec here now
        matches = tech.search(rfp_spec, top_k=3)
    
    if not matches:
        st.error("No matching products found.")
        st.stop()

    # Display Top 3 Cards
    cols = st.columns(3)
    best_match = matches[0]
    
    for i, match in enumerate(matches):
        with cols[i]:
            score = match['Spec_Match_%']
            sku = match['record']['SKU_ID']
            if i == 0:
                st.metric(label=f"🥇 Rank {i+1}: {sku}", value=f"{score}% Match", delta="Recommended")
            else:
                st.metric(label=f"🥈 Rank {i+1}: {sku}", value=f"{score}% Match")
    
    # Comparison Table
    st.subheader("Spec-Match Analysis")
    
    # Generate the comparison data
    comp_data = tech.build_comparison_table(rfp_spec, matches)
    
    # --- CRITICAL FIX START ---
    # Convert dictionary to DataFrame AND force all data to text (string)
    # This prevents the "ArrowInvalid" crash by treating numbers as text.
    df_comp = pd.DataFrame(comp_data).astype(str) 
    # --- CRITICAL FIX END ---
    
    # Display the dataframe
    # Updated syntax for newer Streamlit versions
    st.dataframe(df_comp, width="stretch")

    # ==========================================
    # PHASE 3: PRICING AGENT
    # ==========================================
    time.sleep(0.5)
    st.markdown("---")
    st.header("3. Pricing Agent: Cost Calculation")
    
    pricing = PricingAgent()
    qty = rfp_spec.get("Quantity_m", 0)
    # Logic: If user didn't mention tests, assume standard ones
    tests_required = selected_rfp["tests_required"]
    
    # Sort matches by score just in case
    top_per_product = sorted(matches, key=lambda x: x["Spec_Match_%"], reverse=True)
    
    pricing_report = pricing.price_tests_and_consolidate(top_per_product, tests_required, qty)
    best_option_cost = pricing_report['per_product'][0]
    
    p_col1, p_col2, p_col3 = st.columns(3)
    p_col1.metric("Material Cost", f"₹{best_option_cost['Material_Price']:,.2f}")
    p_col2.metric("Testing Services", f"₹{best_option_cost['Services_Price']:,.2f}")
    p_col3.metric("Grand Total Bid", f"₹{best_option_cost['Total_Price']:,.2f}", delta="Competitive")

    # ==========================================
    # PHASE 4: DECISION AGENT
    # ==========================================
    # ==========================================
    # PHASE 4: DECISION AGENT
    # ==========================================
    st.markdown("---")
    st.header("4. Decision Agent: Approval")
    
    spec_threshold = 90.0
    
    # 1. Get Data
    actual_score = best_match['Spec_Match_%']
    required_qty = rfp_spec.get("Quantity_m", 0)
    available_stock = best_match['record'].get('Stock_Available', 999999) # Default to infinite if missing
    
    # 2. Logic Checks
    is_spec_good = actual_score >= spec_threshold
    is_stock_good = available_stock >= required_qty
    
    d_col1, d_col2 = st.columns([2, 1])
    
    with d_col1:
        st.write("**Policy Check:**")
        st.write(f"- Spec Match ({actual_score}%) >= {spec_threshold}%")
        
        # Display Stock Check
        if is_stock_good:
            st.write(f"- Inventory: {available_stock}m > {required_qty}m")
        else:
            st.write(f"- Inventory: {available_stock}m < {required_qty}m (Insufficient Stock)")
    
    with d_col2:
        if is_spec_good and is_stock_good:
            if auto_mode:
                st.success("AUTO-APPROVED")
                st.toast("Bid sent to ERP!")
            else:
                st.warning("READY FOR SUBMISSION")
                st.button("Human Approve & Send")
        elif not is_stock_good:
             st.error("MANUAL REVIEW (Out of Stock)")
        else:
             st.error("MANUAL REVIEW (Spec Mismatch)")