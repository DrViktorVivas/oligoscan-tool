import streamlit as st
import pdfplumber
import re
from fpdf import FPDF

# --- 1. THE ANALYTE KNOWLEDGE BASE ---
# Defines Regex (how to find it) and Physiology (how to interpret it)
ANALYTE_DB = {
    # --- INTRACELLULAR (High Fidelity for Depletion) ---
    'Magnesium':    {'type': 'Intracellular', 'regex': r"Magnesium.*?\s+([\d,.]+)", 'unit': 'mg/L'},
    'Potassium':    {'type': 'Intracellular', 'regex': r"Potassium.*?\s+([\d,.]+)", 'unit': 'mg/L'},
    'Zinc':         {'type': 'Intracellular', 'regex': r"Zinc.*?\s+([\d,.]+)", 'unit': 'mg/L'},
    'Phosphorus':   {'type': 'Intracellular', 'regex': r"Phosphorus.*?\s+([\d,.]+)", 'unit': 'mg/L'},
    'Selenium':     {'type': 'Intracellular', 'regex': r"Selenium.*?\s+([\d,.]+)", 'unit': 'mg/L'},
    'Lithium':      {'type': 'Intracellular', 'regex': r"Lithium.*?\s+([\d,.]+)", 'unit': 'mg/L'},
    'Germanium':    {'type': 'Intracellular', 'regex': r"Germanium.*?\s+([\d,.]+)", 'unit': 'mg/L'},
    'Molybdenum':   {'type': 'Intracellular', 'regex': r"Molybdenum.*?\s+([\d,.]+)", 'unit': 'mg/L'},
    
    # --- EXTRACELLULAR / REGULATORY (Stress Indicators) ---
    'Calcium':      {'type': 'Extracellular', 'regex': r"Calcium.*?\s+([\d,.]+)", 'unit': 'mg/L'},
    'Sodium':       {'type': 'Extracellular', 'regex': r"Sodium.*?\s+([\d,.]+)", 'unit': 'mg/L'},
    'Copper':       {'type': 'Extracellular', 'regex': r"Copper.*?\s+([\d,.]+)", 'unit': 'mg/L'},
    'Silicon':      {'type': 'Extracellular', 'regex': r"Silicon.*?\s+([\d,.]+)", 'unit': 'mg/L'},
    'Iron':         {'type': 'Extracellular', 'regex': r"Iron.*?\s+([\d,.]+)", 'unit': 'mg/L'},
    'Manganese':    {'type': 'Extracellular', 'regex': r"Manganese.*?\s+([\d,.]+)", 'unit': 'mg/L'},
    'Chromium':     {'type': 'Extracellular', 'regex': r"Chromium.*?\s+([\d,.]+)", 'unit': 'mg/L'},
    'Vanadium':     {'type': 'Extracellular', 'regex': r"Vanadium.*?\s+([\d,.]+)", 'unit': 'mg/L'},
    'Boron':        {'type': 'Extracellular', 'regex': r"Boron.*?\s+([\d,.]+)", 'unit': 'mg/L'},
    'Cobalt':       {'type': 'Extracellular', 'regex': r"Cobalt.*?\s+([\d,.]+)", 'unit': 'mg/L'},
    'Iodine':       {'type': 'Extracellular', 'regex': r"[Il]odine.*?\s+([\d,.]+)", 'unit': 'mg/L'},
    'Sulfur':       {'type': 'Extracellular', 'regex': r"Sulphur.*?\s+([\d,.]+)", 'unit': 'mg/L'},
    'Fluorine':     {'type': 'Extracellular', 'regex': r"Fluor.*?\s+([\d,.]+)", 'unit': 'mg/L'},

    # --- HEAVY METALS (Accumulation) ---
    'Aluminum':     {'type': 'Metal', 'regex': r"Aluminium.*?\s+([\d,.]+)", 'unit': 'µg/L'},
    'Antimony':     {'type': 'Metal', 'regex': r"Antimony.*?\s+([\d,.]+)", 'unit': 'µg/L'},
    'Silver':       {'type': 'Metal', 'regex': r"Silver.*?\s+([\d,.]+)", 'unit': 'µg/L'},
    'Arsenic':      {'type': 'Metal', 'regex': r"Arsenic.*?\s+([\d,.]+)", 'unit': 'µg/L'},
    'Barium':       {'type': 'Metal', 'regex': r"Barium.*?\s+([\d,.]+)", 'unit': 'µg/L'},
    'Beryllium':    {'type': 'Metal', 'regex': r"Beryllium.*?\s+([\d,.]+)", 'unit': 'µg/L'},
    'Bismuth':      {'type': 'Metal', 'regex': r"Bismuth.*?\s+([\d,.]+)", 'unit': 'µg/L'},
    'Cadmium':      {'type': 'Metal', 'regex': r"Cadmium.*?\s+([\d,.]+)", 'unit': 'µg/L'},
    'Mercury':      {'type': 'Metal', 'regex': r"Mercury.*?\s+([\d,.]+)", 'unit': 'µg/L'},
    'Nickel':       {'type': 'Metal', 'regex': r"Nickel.*?\s+([\d,.]+)", 'unit': 'µg/L'},
    'Platinum':     {'type': 'Metal', 'regex': r"Platinum.*?\s+([\d,.]+)", 'unit': 'µg/L'},
    'Lead':         {'type': 'Metal', 'regex': r"Lead.*?\s+([\d,.]+)", 'unit': 'µg/L'},
    'Thallium':     {'type': 'Metal', 'regex': r"Thallium.*?\s+([\d,.]+)", 'unit': 'µg/L'},
    'Thorium':      {'type': 'Metal', 'regex': r"Thorium.*?\s+([\d,.]+)", 'unit': 'µg/L'},
    'Gadolinium':   {'type': 'Metal', 'regex': r"Gadolinium.*?\s+([\d,.]+)", 'unit': 'µg/L'},
    'Tin':          {'type': 'Metal', 'regex': r"Tin.*?\s+([\d,.]+)", 'unit': 'µg/L'},
    
    # --- VITAMINS ---
    'Vit_B6':       {'type': 'Vitamin', 'regex': r"Vitamin B6\s+(\d+)%", 'unit': '%'},
    'Vit_B12':      {'type': 'Vitamin', 'regex': r"Vitamin B12\s+(\d+)%", 'unit': '%'},
}

# --- 2. CONFIG & HELPERS ---
st.set_page_config(page_title="OligoScan Clinical Interpreter", layout="wide")

def clean_text(text):
    if not isinstance(text, str): return str(text)
    replacements = {"⛔": "[BLOCKED]", "⚠️": "[RISK]", "✅": "[OK]", "🧬": "", "✔": ""}
    for char, rep in replacements.items():
        text = text.replace(char, rep)
    return text.encode('latin-1', 'replace').decode('latin-1')

def extract_all_data(pdf_file):
    data = {}
    full_text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            full_text += page.extract_text() + "\n"
    
    # Updated Regex Engine: Uses ".*?" to skip chemical symbols (e.g. "Calcium Ca 400")
    for name, config in ANALYTE_DB.items():
        match = re.search(config['regex'], full_text, re.IGNORECASE)
        if match:
            try:
                # Handle "10,9" European decimals
                clean_val = match.group(1).replace(',', '.')
                data[name] = float(clean_val)
            except ValueError:
                data[name] = 0.0
        else:
            data[name] = 0.0
    return data

# --- 3. TRANSFORMATION & INTERPRETATION ENGINE ---
def run_clinical_analysis(data, skin_type):
    adjusted = {}
    inferences = []
    
    # 1. OPTICAL PHYSICS CORRECTION (The Baseline)
    optical_factor = 1.0
    if skin_type == "I-II (Pale)": optical_factor = 0.90
    elif skin_type == "III-IV (Medium)": optical_factor = 1.10
    elif skin_type == "V-VI (Dark)": optical_factor = 1.25

    # 2. DETOX BLOCKAGE CHECK
    sulfur = data.get('Sulfur', 0)
    b6 = data.get('Vit_B6', 100)
    b12 = data.get('Vit_B12', 100)
    is_blocked = (sulfur < 48.1) or (b6 < 60) or (b12 < 60)
    
    if is_blocked:
        inferences.append("⚠️ DETOX BLOCKAGE: Low Sulfur or Methylation detected. Metals likely retained (False Negatives).")

    # 3. ANALYTE PROCESSING LOOP
    for name, config in ANALYTE_DB.items():
        raw = data.get(name, 0.0)
        final_val = raw
        
        # Apply Optical Physics to Minerals
        if config['type'] in ['Intracellular', 'Extracellular']:
            final_val = raw * optical_factor
            
            # Specific Corrections
            if name == 'Magnesium': final_val *= 1.35
            if name == 'Zinc' and "Pale" in skin_type: final_val = raw * 0.90 # Overrides general factor
            
        # Apply Metal Projection
        elif config['type'] == 'Metal':
            if is_blocked and raw < 0.02: final_val = raw * 3.5
            
        adjusted[name] = round(final_val, 4)

    # 4. CLINICAL RATIOS & HYPOTHESES (The "Switch" Logic)
    ratios = {}
    
    # A. Ca/Mg (Autonomic Tone)
    # Normative range approx 2.0 - 5.0 (varies by lab, using simplified logic)
    try:
        ca_mg = adjusted['Calcium'] / adjusted['Magnesium'] if adjusted['Magnesium'] > 0 else 0
        ratios['Ca/Mg'] = round(ca_mg, 2)
        if ca_mg > 8.0:
            inferences.append(f"🔥 Sympathetic Dominance (Ca/Mg {ca_mg}): High Calcium tone relative to Magnesium reserves.")
        elif ca_mg < 3.0:
            inferences.append(f"💧 Parasympathetic Slump (Ca/Mg {ca_mg}): Magnesium dominance or Calcium loss.")
    except: pass

    # B. Na/K (Vitality / Adrenal)
    # Ideally ~2.5 to 4.0
    try:
        na_k = adjusted['Sodium'] / adjusted['Potassium'] if adjusted['Potassium'] > 0 else 0
        ratios['Na/K'] = round(na_k, 2)
        if na_k < 1.5:
            inferences.append(f"⚡ Adrenal/Vitality Stress (Na/K {na_k}): Low Sodium relative to Potassium. Possible inversion.")
    except: pass
    
    # C. Zn/Cu (Immune/Inflammation)
    # Ideally ~0.7 to 1.0 (Zinc usually higher than Cu in tissue?) -- Adjust based on your preferred reference
    try:
        zn_cu = adjusted['Zinc'] / adjusted['Copper'] if adjusted['Copper'] > 0 else 0
        ratios['Zn/Cu'] = round(zn_cu, 2)
        if zn_cu < 0.7:
             inferences.append(f"🛡️ Immune Vulnerability (Zn/Cu {zn_cu}): Copper excess or Zinc depletion.")
    except: pass

    return adjusted, ratios, inferences, is_blocked

# --- 4. PDF REPORT GENERATOR ---
def create_clinical_report(patient_name, original, adjusted, ratios, inferences):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    
    # Header
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, clean_text(f"Physiological Analysis: {patient_name}"), ln=True, align='C')
    pdf.ln(5)
    
    # Clinical Hypotheses Section
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "CLINICAL HYPOTHESES (Tissue-Based)", 1, 1, 'L', 1)
    
    pdf.set_font("Arial", '', 10)
    pdf.multi_cell(0, 8, clean_text("Based on the 'Transformation Framework' (2026 Standards):"))
    pdf.ln(2)
    
    for inf in inferences:
        # Check for keywords to bold/color (simulated with standard font here)
        prefix = "[!]" if "⚠️" in inf else "[i]"
        pdf.multi_cell(0, 6, clean_text(f"{prefix} {inf}"))
    pdf.ln(5)

    # --- TABLE BUILDER ---
    def add_table(title, type_filter, description):
        pdf.set_font("Arial", 'B', 11)
        pdf.set_fill_color(220, 225, 255)
        pdf.cell(0, 8, clean_text(f"{title} ({description})"), 1, 1, 'L', 1)
        
        # Headers
        pdf.set_fill_color(245, 245, 245)
        pdf.set_font("Arial", 'B', 9)
        pdf.cell(50, 6, "Analyte", 1, 0, 'L', 1)
        pdf.cell(30, 6, "Raw", 1, 0, 'C', 1)
        pdf.cell(30, 6, "Adjusted", 1, 0, 'C', 1)
        pdf.cell(80, 6, "Physiological Implication", 1, 1, 'L', 1)
        
        pdf.set_font("Arial", '', 9)
        
        for name, config in ANALYTE_DB.items():
            if config['type'] == type_filter:
                raw = original.get(name, 0.0)
                adj = adjusted.get(name, 0.0)
                
                # Dynamic Interpretation
                impl = ""
                if type_filter == "Intracellular":
                    if adj < 10: impl = "Systemic Depletion Likely" # Thresholds are illustrative
                    else: impl = "Cellular Reserve Stable"
                elif type_filter == "Extracellular":
                    impl = "Metabolic/Regulatory Marker"
                elif type_filter == "Metal":
                    if adj > raw: impl = "Projected Hidden Burden"
                    else: impl = "Trace / No Accumulation"
                
                pdf.cell(50, 6, clean_text(name), 1)
                pdf.cell(30, 6, str(raw), 1, 0, 'C')
                pdf.cell(30, 6, str(adj), 1, 0, 'C')
                pdf.cell(80, 6, clean_text(impl), 1, 1, 'L')
        pdf.ln(5)

    add_table("INTRACELLULAR ELEMENTS", "Intracellular", "High Fidelity: Reflects Systemic Status")
    add_table("EXTRACELLULAR ELEMENTS", "Extracellular", "Metabolic Stress Indicators")
    add_table("TOXIC METALS", "Metal", "Chronic Tissue Storage")
    
    # Ratios Table
    pdf.set_font("Arial", 'B', 11)
    pdf.set_fill_color(220, 225, 255)
    pdf.cell(0, 8, "PREDICTIVE RATIOS", 1, 1, 'L', 1)
    
    pdf.set_font("Arial", '', 10)
    for name, val in ratios.items():
        pdf.cell(50, 7, clean_text(name), 1)
        pdf.cell(140, 7, str(val), 1, 1, 'L')

    return pdf.output(dest='S').encode('latin-1', 'replace')

# --- 5. UI ---
st.title("🧬 Physiological Analysis Tool (v4.0)")
st.sidebar.header("Patient Context")
patient_name = st.sidebar.text_input("Name")
skin_type = st.sidebar.selectbox("Skin Type", ["I-II (Pale)", "III-IV (Medium)", "V-VI (Dark)"])

uploaded_file = st.file_uploader("Upload OligoScan PDF", type="pdf")

if uploaded_file:
    data = extract_all_data(uploaded_file)
    adj_data, ratios, inferences, blocked = run_clinical_analysis(data, skin_type)
    
    # Display Hypotheses
    st.subheader("Clinical Hypotheses")
    for inf in inferences:
        if "⚠️" in inf: st.error(inf)
        elif "🔥" in inf: st.warning(inf)
        else: st.info(inf)
        
    # Data Preview
    with st.expander("View Adjusted Data"):
        st.write(adj_data)

    # Download
    pdf_bytes = create_clinical_report(patient_name, data, adj_data, ratios, inferences)
    st.download_button("📄 Download Clinical Analysis", pdf_bytes, "Analysis_Report.pdf", "application/pdf")
