import streamlit as st
import pdfplumber
import re
from fpdf import FPDF

# --- 1. THE UNIVERSAL ANALYTE DICTIONARY ---
# This DB holds the rules for parsing and adjusting every single element.
# 'type': Mineral, Metal, Vitamin, or Ratio
# 'regex': The pattern to find it in the PDF
# 'unit': Display unit (mg/dL, %, etc.)

ANALYTE_DB = {
    # --- MINERALS ---
    'Calcium':      {'type': 'Mineral', 'regex': r"Calcium\s+([\d,.]+)", 'unit': 'mg/L'},
    'Magnesium':    {'type': 'Mineral', 'regex': r"Magnesium\s+([\d,.]+)", 'unit': 'mg/L'},
    'Phosphorus':   {'type': 'Mineral', 'regex': r"Phosphorus\s+([\d,.]+)", 'unit': 'mg/L'},
    'Silicon':      {'type': 'Mineral', 'regex': r"Silicon\s+([\d,.]+)", 'unit': 'mg/L'},
    'Sodium':       {'type': 'Mineral', 'regex': r"Sodium.*?\s+([\d,.]+)", 'unit': 'mg/L'},
    'Potassium':    {'type': 'Mineral', 'regex': r"Potassium.*?\s+([\d,.]+)", 'unit': 'mg/L'},
    'Copper':       {'type': 'Mineral', 'regex': r"Copper\s+([\d,.]+)", 'unit': 'mg/L'},
    'Zinc':         {'type': 'Mineral', 'regex': r"Zinc\s+([\d,.]+)", 'unit': 'mg/L'},
    'Iron':         {'type': 'Mineral', 'regex': r"Iron.*?\s+([\d,.]+)", 'unit': 'mg/L'},
    'Manganese':    {'type': 'Mineral', 'regex': r"Manganese.*?\s+([\d,.]+)", 'unit': 'mg/L'},
    'Chromium':     {'type': 'Mineral', 'regex': r"Chromium\s+([\d,.]+)", 'unit': 'mg/L'},
    'Vanadium':     {'type': 'Mineral', 'regex': r"Vanadium\s+([\d,.]+)", 'unit': 'mg/L'},
    'Boron':        {'type': 'Mineral', 'regex': r"Boron\s+([\d,.]+)", 'unit': 'mg/L'},
    'Cobalt':       {'type': 'Mineral', 'regex': r"Cobalt.*?\s+([\d,.]+)", 'unit': 'mg/L'},
    'Molybdenum':   {'type': 'Mineral', 'regex': r"Molybdenum.*?\s+([\d,.]+)", 'unit': 'mg/L'},
    'Iodine':       {'type': 'Mineral', 'regex': r"[Il]odine\s+([\d,.]+)", 'unit': 'mg/L'},
    'Lithium':      {'type': 'Mineral', 'regex': r"Lithium\s+([\d,.]+)", 'unit': 'mg/L'},
    'Germanium':    {'type': 'Mineral', 'regex': r"Germanium\s+([\d,.]+)", 'unit': 'mg/L'},
    'Selenium':     {'type': 'Mineral', 'regex': r"Selenium\s+([\d,.]+)", 'unit': 'mg/L'},
    'Sulfur':       {'type': 'Mineral', 'regex': r"Sulphur\s+([\d,.]+)", 'unit': 'mg/L'},
    'Fluorine':     {'type': 'Mineral', 'regex': r"Fluor\s+([\d,.]+)", 'unit': 'mg/L'},

    # --- HEAVY METALS ---
    'Aluminum':     {'type': 'Metal', 'regex': r"Aluminium\s+([\d,.]+)", 'unit': 'µg/L'},
    'Antimony':     {'type': 'Metal', 'regex': r"Antimony.*?\s+([\d,.]+)", 'unit': 'µg/L'},
    'Silver':       {'type': 'Metal', 'regex': r"Silver\s+([\d,.]+)", 'unit': 'µg/L'},
    'Arsenic':      {'type': 'Metal', 'regex': r"Arsenic.*?\s+([\d,.]+)", 'unit': 'µg/L'},
    'Barium':       {'type': 'Metal', 'regex': r"Barium.*?\s+([\d,.]+)", 'unit': 'µg/L'},
    'Beryllium':    {'type': 'Metal', 'regex': r"Beryllium.*?\s+([\d,.]+)", 'unit': 'µg/L'},
    'Bismuth':      {'type': 'Metal', 'regex': r"Bismuth\s+([\d,.]+)", 'unit': 'µg/L'},
    'Cadmium':      {'type': 'Metal', 'regex': r"Cadmium\s+([\d,.]+)", 'unit': 'µg/L'},
    'Mercury':      {'type': 'Metal', 'regex': r"Mercury\s+([\d,.]+)", 'unit': 'µg/L'},
    'Nickel':       {'type': 'Metal', 'regex': r"Nickel\s+([\d,.]+)", 'unit': 'µg/L'},
    'Platinum':     {'type': 'Metal', 'regex': r"Platinum\s+([\d,.]+)", 'unit': 'µg/L'},
    'Lead':         {'type': 'Metal', 'regex': r"Lead\s+([\d,.]+)", 'unit': 'µg/L'},
    'Thallium':     {'type': 'Metal', 'regex': r"Thallium.*?\s+([\d,.]+)", 'unit': 'µg/L'},
    'Thorium':      {'type': 'Metal', 'regex': r"Thorium.*?\s+([\d,.]+)", 'unit': 'µg/L'},
    'Gadolinium':   {'type': 'Metal', 'regex': r"Gadolinium.*?\s+([\d,.]+)", 'unit': 'µg/L'},
    'Tin':          {'type': 'Metal', 'regex': r"Tin\s+([\d,.]+)", 'unit': 'µg/L'},

    # --- VITAMINS & COFACTORS ---
    'Vit_A':        {'type': 'Vitamin', 'regex': r"Vitamin A\s+(\d+)%", 'unit': '%'},
    'Vit_C':        {'type': 'Vitamin', 'regex': r"Vitamin C\s+(\d+)%", 'unit': '%'},
    'Vit_E':        {'type': 'Vitamin', 'regex': r"Vitamin E\s+(\d+)%", 'unit': '%'},
    'Vit_B6':       {'type': 'Vitamin', 'regex': r"Vitamin B6\s+(\d+)%", 'unit': '%'},
    'Vit_B9':       {'type': 'Vitamin', 'regex': r"Vitamin B9.*?\s+(\d+)%", 'unit': '%'},
    'Vit_B12':      {'type': 'Vitamin', 'regex': r"Vitamin B12\s+(\d+)%", 'unit': '%'},
    'Vit_D':        {'type': 'Vitamin', 'regex': r"Vitamin D\s+(\d+)%", 'unit': '%'},
}

# --- 2. CONFIGURATION & HELPERS ---
st.set_page_config(page_title="Universal OligoScan Adjuster", layout="wide")

def clean_text(text):
    """Sanitize text for PDF (Latin-1)"""
    if not isinstance(text, str): return str(text)
    replacements = {"⛔": "[BLOCKED]", "⚠️": "[RISK]", "✅": "[OK]", "🧬": "", "✔": ""}
    for char, rep in replacements.items():
        text = text.replace(char, rep)
    return text.encode('latin-1', 'replace').decode('latin-1')

def extract_all_data(pdf_file):
    """Loops through ANALYTE_DB and finds every value."""
    data = {}
    full_text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            full_text += page.extract_text() + "\n"
    
    for name, config in ANALYTE_DB.items():
        match = re.search(config['regex'], full_text, re.IGNORECASE)
        if match:
            try:
                val = float(match.group(1).replace(',', '.'))
                data[name] = val
            except ValueError:
                data[name] = 0.0
        else:
            data[name] = 0.0
    return data

# --- 3. THE UNIVERSAL ADJUSTMENT ALGORITHM ---
def run_universal_adjustment(data, skin_type):
    adjusted = {}
    logic_log = []
    
    # --- A. DETERMINE GLOBAL PHYSICS FACTORS ---
    # Skin Optics: Spectrophotometry over-reads on pale skin (reflection) 
    # and under-reads on dark skin (absorption).
    # We apply this BASE CORRECTION to ALL Minerals/Vitamins.
    
    optical_factor = 1.0
    if skin_type == "I-II (Pale)":
        optical_factor = 0.90 # Dampen signal by 10%
        logic_log.append("Physics: Pale skin high reflectance -> Applied 0.90x damper to all minerals.")
    elif skin_type == "III-IV (Medium)":
        optical_factor = 1.10 # Boost signal by 10%
        logic_log.append("Physics: Medium skin absorption -> Applied 1.10x boost to all minerals.")
    elif skin_type == "V-VI (Dark)":
        optical_factor = 1.25 # Boost signal by 25%
        logic_log.append("Physics: Dark skin high absorption -> Applied 1.25x boost to all minerals.")

    # --- B. DETERMINE DETOX STATUS ---
    sulfur = data.get('Sulfur', 0)
    b6 = data.get('Vit_B6', 100)
    b12 = data.get('Vit_B12', 100)
    
    is_blocked = (sulfur < 48.1) or (b6 < 60) or (b12 < 60)
    
    if is_blocked:
        logic_log.append(f"Detox Blocked: Sulfur({sulfur}) or B6/B12(<60%) low. Metals retained.")

    # --- C. ITERATE THROUGH DICTIONARY ---
    for name, config in ANALYTE_DB.items():
        raw = data.get(name, 0.0)
        final_val = raw
        
        # 1. MINERALS & VITAMINS (Apply Optical Physics)
        if config['type'] in ['Mineral', 'Vitamin']:
            # Base Correction
            final_val = raw * optical_factor
            
            # Specific Overrides (Layered on top)
            if name == 'Magnesium':
                final_val = final_val * 1.35 # Serum Correlation Factor
            if name == 'Zinc' and skin_type == "I-II (Pale)":
                # Zinc is especially reflective in pale skin, ensure dampening holds
                pass 

        # 2. HEAVY METALS (Apply Blockage Logic)
        elif config['type'] == 'Metal':
            # If detox is blocked, ANY low reading is suspect.
            if is_blocked and raw < 0.02:
                final_val = raw * 3.5 # Universal Retention Multiplier
            else:
                final_val = raw

        adjusted[name] = round(final_val, 4)

    # --- D. RECALCULATE RATIOS (Dynamic) ---
    # We calculate these fresh from the ADJUSTED values
    ratios = {}
    try:
        ratios['Ca/Mg'] = round(adjusted['Calcium'] / adjusted['Magnesium'], 2) if adjusted['Magnesium'] else 0
        ratios['Ca/P'] = round(adjusted['Calcium'] / adjusted['Phosphorus'], 2) if adjusted['Phosphorus'] else 0
        ratios['K/Na'] = round(adjusted['Potassium'] / adjusted['Sodium'], 2) if adjusted['Sodium'] else 0
        ratios['Cu/Zn'] = round(adjusted['Copper'] / adjusted['Zinc'], 2) if adjusted['Zinc'] else 0
    except:
        pass
        
    return adjusted, ratios, logic_log, is_blocked

# --- 4. PDF REPORT GENERATOR ---
def create_full_report(patient_name, original, adjusted, ratios, logs, blocked):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    
    # Title
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, clean_text(f"Analyte Regression Report: {patient_name}"), ln=True, align='C')
    pdf.ln(5)
    
    # Logic Summary
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 8, "Adjustment Logic Applied:", ln=True)
    pdf.set_font("Arial", 'I', 9)
    for log in logs:
        pdf.cell(0, 5, clean_text(f"- {log}"), ln=True)
    pdf.ln(5)

    # --- TABLE BUILDER ---
    def add_section(title, category_filter):
        pdf.set_font("Arial", 'B', 11)
        pdf.set_fill_color(220, 220, 220)
        pdf.cell(50, 8, clean_text(title), 1, 0, 'L', 1)
        pdf.cell(35, 8, "Raw", 1, 0, 'C', 1)
        pdf.cell(35, 8, "Adjusted", 1, 0, 'C', 1)
        pdf.cell(35, 8, "Change", 1, 0, 'C', 1)
        pdf.cell(35, 8, "Unit", 1, 1, 'C', 1)
        pdf.set_font("Arial", '', 10)
        
        for name, config in ANALYTE_DB.items():
            if config['type'] == category_filter:
                raw = original.get(name, 0.0)
                adj = adjusted.get(name, 0.0)
                
                # Visual Diff
                diff = round(adj - raw, 4)
                change_str = f"{diff:+}" if diff != 0 else "-"
                
                # Colors
                pdf.set_text_color(0, 0, 0)
                if category_filter == 'Metal' and blocked and diff > 0:
                    pdf.set_text_color(200, 0, 0) # Red for hidden metals
                    pdf.set_font("Arial", 'B', 10)
                elif diff != 0:
                    pdf.set_font("Arial", 'B', 10)
                else:
                    pdf.set_font("Arial", '', 10)
                
                pdf.cell(50, 7, clean_text(name), 1)
                pdf.cell(35, 7, str(raw), 1, 0, 'C')
                pdf.cell(35, 7, str(adj), 1, 0, 'C')
                pdf.cell(35, 7, change_str, 1, 0, 'C')
                pdf.cell(35, 7, clean_text(config['unit']), 1, 1, 'C')
        pdf.ln(5)

    add_section("MINERALS", "Mineral")
    add_section("HEAVY METALS (Projected)", "Metal")
    add_section("VITAMINS", "Vitamin")
    
    # Ratios Section
    pdf.set_font("Arial", 'B', 11)
    pdf.set_fill_color(220, 220, 220)
    pdf.cell(50, 8, "RATIOS (Recalc)", 1, 0, 'L', 1)
    pdf.cell(140, 8, "Value derived from Adjusted Minerals", 1, 1, 'C', 1)
    pdf.set_font("Arial", '', 10)
    pdf.set_text_color(0,0,0)
    
    for name, val in ratios.items():
        pdf.cell(50, 7, clean_text(name), 1)
        pdf.cell(140, 7, str(val), 1, 1, 'C')

    return pdf.output(dest='S').encode('latin-1', 'replace')

# --- 5. UI ---
st.title("🧬 Universal Analyte Regression Tool")
st.sidebar.header("Configuration")
patient_name = st.sidebar.text_input("Patient Name", "Patient X")
skin_type = st.sidebar.selectbox("Fitzpatrick Skin Type", ["I-II (Pale)", "III-IV (Medium)", "V-VI (Dark)"])

uploaded_file = st.file_uploader("Upload OligoScan PDF", type="pdf")

if uploaded_file:
    # 1. Parse All
    data = extract_all_data(uploaded_file)
    
    # 2. Universal Regression
    adj_data, new_ratios, logs, blocked = run_universal_adjustment(data, skin_type)
    
    # 3. Display
    st.subheader(f"Analysis Status: {'⛔ BLOCKED' if blocked else '✅ OPTIMAL'}")
    
    # Preview Tabs
    tab1, tab2, tab3 = st.tabs(["Minerals", "Metals", "Logs"])
    
    with tab1:
        st.dataframe({
            "Analyte": [k for k,v in ANALYTE_DB.items() if v['type']=='Mineral'],
            "Raw": [data[k] for k,v in ANALYTE_DB.items() if v['type']=='Mineral'],
            "Adjusted": [adj_data[k] for k,v in ANALYTE_DB.items() if v['type']=='Mineral']
        })
        
    with tab2:
         st.dataframe({
            "Analyte": [k for k,v in ANALYTE_DB.items() if v['type']=='Metal'],
            "Raw": [data[k] for k,v in ANALYTE_DB.items() if v['type']=='Metal'],
            "Adjusted": [adj_data[k] for k,v in ANALYTE_DB.items() if v['type']=='Metal']
        })
        
    with tab3:
        for l in logs: st.write(f"- {l}")

    # 4. Download
    pdf_bytes = create_full_report(patient_name, data, adj_data, new_ratios, logs, blocked)
    st.download_button("📄 Download Complete Regression Report", pdf_bytes, f"{patient_name}_Full_Report.pdf", "application/pdf")
