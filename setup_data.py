import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss

# --- 1. EXPANDED MOCK DATASHEET REPOSITORY ---
# We now include a variety of cables: LT (Low Tension), HT (High Tension), Control Cables, etc.
# --- 1. EXPANDED MOCK DATASHEET REPOSITORY ---
DATASHEET_RECORDS = [
    # --- 1.1 kV Segment (Low Tension) ---
    {
        'SKU_ID': 'LT-AL-XLPE-4C-1.1-FR', 
        'Voltage': 1.1, 'Cores': 4, 'Conductor_Material': 'Aluminum', 'Insulation_Type': 'XLPE', 'FR_Grade': True, 
        'Base_Price_per_m': 150.0, 'Spec_Description': '1.1kV 4-Core Aluminum XLPE Armoured Power Cable, Fire Retardant (FR).',
        'Stock_Available': 15000  # ✅ High Stock
    },
    {
        'SKU_ID': 'LT-CU-XLPE-4C-1.1-FR', 
        'Voltage': 1.1, 'Cores': 4, 'Conductor_Material': 'Copper', 'Insulation_Type': 'XLPE', 'FR_Grade': True, 
        'Base_Price_per_m': 450.0, 'Spec_Description': '1.1kV 4-Core Copper XLPE Armoured Power Cable, Fire Retardant.',
        'Stock_Available': 500    # ⚠️ Low Stock (Use this to test failure)
    },
    {
        'SKU_ID': 'LT-AL-PVC-4C-1.1',     
        'Voltage': 1.1, 'Cores': 4, 'Conductor_Material': 'Aluminum', 'Insulation_Type': 'PVC',  'FR_Grade': False, 
        'Base_Price_per_m': 120.0, 'Spec_Description': '1.1kV 4-Core Aluminum PVC Unarmoured Cable, General Purpose.',
        'Stock_Available': 5000
    },
    {
        'SKU_ID': 'LT-AL-XLPE-3.5C-1.1',  
        'Voltage': 1.1, 'Cores': 3.5, 'Conductor_Material': 'Aluminum', 'Insulation_Type': 'XLPE', 'FR_Grade': True, 
        'Base_Price_per_m': 140.0, 'Spec_Description': '1.1kV 3.5-Core Aluminum XLPE Power Cable.',
        'Stock_Available': 8000
    },
    
    # --- 3.3 kV to 6.6 kV Segment (Medium Voltage) ---
    {
        'SKU_ID': 'MV-AL-XLPE-3C-3.3-FR', 
        'Voltage': 3.3, 'Cores': 3, 'Conductor_Material': 'Aluminum', 'Insulation_Type': 'XLPE', 'FR_Grade': True, 
        'Base_Price_per_m': 350.0, 'Spec_Description': '3.3kV 3-Core Aluminum XLPE HT Cable, FRLS Grade.',
        'Stock_Available': 4000
    },
    {
        'SKU_ID': 'MV-CU-XLPE-3C-3.3',    
        'Voltage': 3.3, 'Cores': 3, 'Conductor_Material': 'Copper', 'Insulation_Type': 'XLPE', 'FR_Grade': False, 
        'Base_Price_per_m': 800.0, 'Spec_Description': '3.3kV 3-Core Copper XLPE HT Cable.',
        'Stock_Available': 1200
    },
    {
        'SKU_ID': 'MV-AL-XLPE-3C-6.6-FR', 
        'Voltage': 6.6, 'Cores': 3, 'Conductor_Material': 'Aluminum', 'Insulation_Type': 'XLPE', 'FR_Grade': True, 
        'Base_Price_per_m': 550.0, 'Spec_Description': '6.6kV 3-Core Aluminum XLPE HT Cable, Screened.',
        'Stock_Available': 3000
    },

    # --- 11 kV to 33 kV Segment (High Tension) ---
    {
        'SKU_ID': 'HT-AL-XLPE-3C-11-FR',  
        'Voltage': 11.0, 'Cores': 3, 'Conductor_Material': 'Aluminum', 'Insulation_Type': 'XLPE', 'FR_Grade': True, 
        'Base_Price_per_m': 850.0, 'Spec_Description': '11kV 3-Core Aluminum XLPE High Tension Cable, Armoured.',
        'Stock_Available': 2500
    },
    {
        'SKU_ID': 'HT-CU-XLPE-3C-11-FR',  
        'Voltage': 11.0, 'Cores': 3, 'Conductor_Material': 'Copper', 'Insulation_Type': 'XLPE', 'FR_Grade': True, 
        'Base_Price_per_m': 1800.0, 'Spec_Description': '11kV 3-Core Copper XLPE High Tension Cable.',
        'Stock_Available': 600
    },
    {
        'SKU_ID': 'HT-AL-XLPE-1C-33',     
        'Voltage': 33.0, 'Cores': 1, 'Conductor_Material': 'Aluminum', 'Insulation_Type': 'XLPE', 'FR_Grade': True, 
        'Base_Price_per_m': 1200.0, 'Spec_Description': '33kV 1-Core Aluminum XLPE EHV Cable.',
        'Stock_Available': 1500
    },
    {
        'SKU_ID': 'HT-AL-XLPE-3C-33-FR',  
        'Voltage': 33.0, 'Cores': 3, 'Conductor_Material': 'Aluminum', 'Insulation_Type': 'XLPE', 'FR_Grade': True, 
        'Base_Price_per_m': 2500.0, 'Spec_Description': '33kV 3-Core Aluminum XLPE EHV Cable, Fire Retardant.',
        'Stock_Available': 2000
    },

    # --- Specialized / Control Cables ---
    {
        'SKU_ID': 'CTRL-CU-PVC-12C-1.1',  
        'Voltage': 1.1, 'Cores': 12, 'Conductor_Material': 'Copper', 'Insulation_Type': 'PVC',  'FR_Grade': False, 
        'Base_Price_per_m': 200.0, 'Spec_Description': '1.1kV 12-Core Copper PVC Control Cable.',
        'Stock_Available': 10000
    },
    {
        'SKU_ID': 'SOLAR-CU-XLPO-1C-1.5', 
        'Voltage': 1.5, 'Cores': 1, 'Conductor_Material': 'Copper', 'Insulation_Type': 'XLPO', 'FR_Grade': True, 
        'Base_Price_per_m': 80.0, 'Spec_Description': '1.5kV 1-Core Solar DC Cable, UV Resistant.',
        'Stock_Available': 50000
    },
]

# --- 2. SETUP VECTOR DATABASE ---
def setup_vector_db(records_list=None):
    """Initializes and returns a FAISS index and the sentence transformer model."""
    if records_list is None:
        records_list = DATASHEET_RECORDS
        
    df = pd.DataFrame(records_list)
    
    # We use a small, fast model for the prototype
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    descriptions = df['Spec_Description'].tolist()
    embeddings = model.encode(descriptions, convert_to_numpy=True)
    
    # Create FAISS index
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)
    
    print(f"✅ Vector Database (FAISS) Initialized with {len(df)} diverse SKUs.")
    return index, embeddings, model

# --- 3. SAMPLE DATA FOR DEMO ---
# Default Text for the "Paste Here" box
SAMPLE_RFP_TEXT = """Request for Proposal (RFP) - ID: PSU-2025-X99

Project: Grid Expansion Phase IV
Material Required: Low Tension Power Cables

Technical Specifications:
1. Voltage Grade: 1.1 kV
2. Cores: 4 Core
3. Conductor: Stranded Aluminum
4. Insulation: XLPE
5. Special Requirement: Must be Fire Retardant (FR) type.

Quantity: 5000 meters
Delivery: Within 8 weeks
Required Tests: Routine Test, Type Test, and Fire Resistance Test."""

# Mock Pricing for Services (Used by Pricing Agent)
TESTS_PRICING = {
    "Routine Test": 5000.00,
    "Type Test": 25000.00,
    "Fire Resistance Test": 15000.00,
    "Drum Packing": 2000.00
}

# Mock Registry for "Scanning" mode (if used)
SAMPLE_RFPS = [
    {"id": "RFP-101", "title": "Metro Rail Cabling", "due_date": pd.Timestamp.now() + pd.Timedelta(days=10), "text": SAMPLE_RFP_TEXT, "tests_required": ["Routine Test"]},
    {"id": "RFP-102", "title": "Solar Park DC Lines", "due_date": pd.Timestamp.now() + pd.Timedelta(days=60), "text": "Requirement for 1.5kV Solar DC Cable...", "tests_required": ["Type Test"]},
]