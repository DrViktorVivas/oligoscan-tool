import streamlit as st
import pdfplumber
import re
from fpdf import FPDF

# --- 1. SCIENTIFIC KNOWLEDGE BASE ---
ANALYTE_DB = {
    # --- INTRACELLULAR (Tissue > Serum) ---
    'Magnesium': {
        'type': 'Intracellular', 
        'regex': r"Magnesium.*?\s+([\d,.]+)", 
        'unit': 'mg/L',
        'science': "Serum Mg represents <1% of total stores. Tissue levels correlate better with cardiovascular risk. [DiNicolantonio 2018; DOI:10.1136/openhrt-2017-000668]"
    },
    'Potassium': {
        'type': 'Intracellular', 
        'regex': r"Potassium.*?\s+([\d,.]+)", 
        'unit': 'mg/L',
        'science': "98% of K+ is intracellular. Deviations indicate Na/K-ATPase pump stress or adrenal dysregulation. [StatPearls 2023; NBK537088]"
    },
    'Zinc': {
        'type': 'Intracellular', 
        'regex': r"Zinc.*?\s+([\d,.]+)", 
        'unit': 'mg/L',
        'science': "Tissue Zinc reflects chronic status; plasma Zinc fluctuates with acute stress. [Roohani 2013; PMCID:PMC3724376]"
    },
    'Phosphorus': {
        'type': 'Intracellular', 
        'regex': r"Phosphorus.*?\s+([\d,.]+)", 
        'unit': 'mg/L',
        'science': "Intracellular phosphate is critical for ATP production. [Peacock 2010; DOI:10.2215/CJN.06080810]"
    },
    'Selenium': {
        'type': 'Intracellular', 
        'regex': r"Selenium.*?\s+([\d,.]+)", 
        'unit': 'mg/L',
        'science': "Key for Glutathione Peroxidase. Tracks antioxidant capacity better than serum. [Kieliszek 2019; DOI:10.3390/molecules24142642]"
    },
    'Lithium': {'type': 'Intracellular', 'regex': r"Lithium.*?\s+([\d,.]+)", 'unit': 'mg/L', 'science': "Trace element involved in B12 transport and mood regulation."},
    'Germanium': {'type': 'Intracellular', 'regex': r"Germanium.*?\s+([\d,.]+)", 'unit': 'mg/L', 'science': "Facilitates oxygen transport at cellular level. [Kaplan 2004]"},
    'Molybdenum': {'type': 'Intracellular', 'regex': r"Molybdenum.*?\s+([\d,.]+)", 'unit': 'mg/L', 'science': "Cofactor for Sulfite Oxidase. Low tissue Mo implies poor sulfur metabolism."},

    # --- EXTRACELLULAR (Stress Markers) ---
    'Calcium': {
        'type': 'Extracellular', 
        'regex': r"Calcium.*?\s+([\d,.]+)", 
        'unit': 'mg/L',
        'science': "Tissue Calcium excess often indicates 'Calcium Shell' effect or parathyroid stress. [Peacock 2010]"
    },
    'Sodium': {
        'type': 'Extracellular', 
        'regex': r"Sodium.*?\s+([\d,.]+)", 
        'unit': 'mg/L',
        'science': "Tissue accumulation suggests Aldosterone/Cortisol imbalance or edema. [StatPearls 2023]"
    },
    'Copper': {
        'type': 'Extracellular', 
        'regex': r"Copper.*?\s+([\d,.]+)", 
        'unit': 'mg/L',
        'science': "High Copper/Zinc ratio correlates with systemic inflammation (CRP). [Schneider 2020]"
    },
    'Silicon': {'type': 'Extracellular', 'regex': r"Silicon.*?\s+([\d,.]+)", 'unit': 'mg/L', 'science': "Structural integrity marker for collagen/bone matrix."},
    'Iron': {'type': 'Extracellular', 'regex': r"Iron.*?\s+([\d,.]+)", 'unit': 'mg/L', 'science': "Tissue iron often reflects oxidative sequestration (Ferritin)."},
    'Manganese': {'type': 'Extracellular', 'regex': r"Manganese.*?\s+([\d,.]+)", 'unit': 'mg/L', 'science': "Critical for SOD2 (mitochondria). Neurotoxic in excess."},
    'Chromium': {'type': 'Extracellular', 'regex': r"Chromium.*?\s+([\d,.]+)", 'unit': 'mg/L', 'science': "Glucose Tolerance Factor. Tissue depletion precedes insulin resistance."},
    'Vanadium': {'type': 'Extracellular', 'regex': r"Vanadium.*?\s+([\d,.]+)", 'unit': 'mg/L', 'science': "Insulin-mimetic. Regulates Na/K-ATPase activity."},
    'Boron': {'type': 'Extracellular', 'regex': r"Boron.*?\s+([\d,.]+)", 'unit': 'mg/L', 'science': "Regulates steroid hormone half-life and bone metabolism."},
    'Cobalt': {'type': 'Extracellular', 'regex': r"Cobalt.*?\s+([\d,.]+)", 'unit': 'mg/L', 'science': "Core component of B12. Toxicity induces hypoxia signaling."},
    'Iodine': {'type': 'Extracellular', 'regex': r"[Il]odine.*?\s+([\d,.]+)", 'unit': 'mg/L', 'science': "Tissue levels reflect thyroidal and extrathyroidal storage."},
    'Sulfur': {'type': 'Extracellular', 'regex': r"Sulphur.*?\s+([\d,.]+)", 'unit': 'mg/L', 'science': "Global conjugation marker. Critical for heavy metal mobilization."},
    'Fluorine': {'type': 'Extracellular', 'regex': r"Fluor.*?\s+([\d,.]+)", 'unit': 'mg/L', 'science': "Accumulates in bone/pineal gland. Antagonist to Iodine."},

    # --- HEAVY METALS ---
    'Aluminum': {'type': 'Metal', 'regex': r"Aluminium.*?\s+([\d,.]+)", 'unit': 'µg/L', 'science': "Neurotoxicant. Accumulates in bone/brain. Blood half-life <8 hours."},
    'Antimony': {'type': 'Metal', 'regex': r"Antimony.*?\s+([\d,.]+)", 'unit': 'µg/L', 'science': "Respiratory/CVS toxicant. Binds sulfhydryl groups."},
    'Silver': {'type': 'Metal', 'regex': r"Silver.*?\s+([\d,.]+)", 'unit': 'µg/L', 'science': "Antimicrobial accumulation (Argyria). Deposits in dermis."},
    'Arsenic': {'type': 'Metal', 'regex': r"Arsenic.*?\s+([\d,.]+)", 'unit': 'µg/L', 'science': "Carcinogen. Rapidly clears blood; deposits in keratin-rich tissues."},
    'Barium': {'type': 'Metal', 'regex': r"Barium.*?\s+([\d,.]+)", 'unit': 'µg/L', 'science': "Competitive K+ channel blocker. Muscle/Cardiac toxicity."},
    'Beryllium': {'type': 'Metal', 'regex': r"Beryllium.*?\s+([\d,.]+)", 'unit': 'µg/L', 'science': "Class 1 Carcinogen. Induces cell-mediated immune response."},
    'Bismuth': {'type': 'Metal', 'regex': r"Bismuth.*?\s+([\d,.]+)", 'unit': 'µg/L', 'science': "Accumulates in kidney/liver. Generally low toxicity."},
    'Cadmium': {'type': 'Metal', 'regex': r"Cadmium.*?\s+([\d,.]+)", 'unit': 'µg/L', 'science': "Accumulates in kidney (t1/2 >10 years). Blood only reflects recent exposure."},
    'Mercury': {'type': 'Metal', 'regex': r"Mercury.*?\s+([\d,.]+)", 'unit': 'µg/L', 'science': "Brain t1/2 >20 years. Tissue scan detects 'Silent Retention'."},
    'Nickel': {'type': 'Metal', 'regex': r"Nickel.*?\s+([\d,.]+)", 'unit': 'µg/L', 'science': "Immunotoxic/Allergenic. Induces oxidative stress."},
    'Platinum': {'type': 'Metal', 'regex': r"Platinum.*?\s+([\d,.]+)", 'unit': 'µg/L', 'science': "Potent sensitizer. DNA cross-linking agent."},
    'Lead': {'type': 'Metal', 'regex': r"Lead.*?\s+([\d,.]+)", 'unit': 'µg/L', 'science': "95% stored in bone. Mobilized by stress/menopause."},
    'Thallium': {'type': 'Metal', 'regex': r"Thallium.*?\s+([\d,.]+)", 'unit': 'µg/L', 'science': "K+ homologue; disrupts mitochondrial ATP production."},
    'Thorium': {'type': 'Metal', 'regex': r"Thorium.*?\s+([\d,.]+)", 'unit': 'µg/L', 'science': "Radiological heavy metal. Accumulates in bone/liver."},
    'Gadolinium': {'type': 'Metal', 'regex': r"Gadolinium.*?\s+([\d,.]+)", 'unit': 'µg/L', 'science': "Retained in bone/brain after MRI contrast."},
    'Tin': {'type': 'Metal', 'regex': r"Tin.*?\s+([\d,.]+)", 'unit': 'µg/L', 'science': "Organotin compounds are neurotoxic and immunotoxic."},

    # --- VITAMINS ---
    'Vit_B6': {'type': 'Vitamin', 'regex': r"Vitamin B6\s+(\d+)%", 'unit': '%', 'science': "Methylation cofactor."},
    'Vit_B12': {'type': 'Vitamin', 'regex': r"Vitamin B12\s+(\d+)%", 'unit': '%', 'science': "Methylation cofactor."},
}

# --- 2. CONFIG & HELPERS ---
st.set_page_config(page_title="OligoScan Visual Analyzer", layout="wide")

def clean_text(text):
    if not isinstance(text, str): return str(text)
    replacements = {"⛔": "[BLOCKED]", "⚠️": "[RISK]", "✅": "[OK]", "🔥": "[HIGH]", "💧": "[LOW]", "⚡": "[STRESS]", "🛡️": "[IMMUNE]", "🧬": "", "✔": ""}
    for char, rep in replacements.items():
        text = text.replace(char, rep)
    return text.encode('latin-1', 'replace').decode('latin-1')

def extract_all_data(pdf_file):
    data = {}
    full_text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            full_text += page.extract_text() + "\n"
    
    for name, config in ANALYTE_DB.items():
        match = re.search(config['regex'], full_text, re.IGNORECASE)
        if match:
            try:
                clean_val = match.group(1).replace(',', '.')
                data[name] = float(clean_val)
            except ValueError:
                data[name] = 0.0
        else:
            data[name] = 0.0
    return data

# --- 3. ANALYSIS LOGIC ---
def run_clinical_analysis(data, skin_type):
    adjusted = {}
    inferences = []
    
    # 1. OPTICS
    optical_factor = 1.0
    if skin_type == "I-II (Pale)": optical_factor = 0.90
    elif skin_type == "III-IV (Medium)": optical_factor = 1.10
    elif skin_type == "V-VI (Dark)": optical_factor = 1.25

    # 2. BLOCKAGE
    sulfur = data.get('Sulfur', 0)
    b6 = data.get('Vit_B6', 100)
    b12 = data.get('Vit_B12', 100)
    is_blocked = (sulfur < 48.1) or (b6 < 60) or (b12 < 60)
    
    if is_blocked:
        inferences.append("⚠️ DETOX BLOCKAGE: Low Sulfur or Methylation (B6/B12). Metals likely retained.")

    # 3. ADJUSTMENT
    for name, config in ANALYTE_DB.items():
        raw = data.get(name, 0.0)
        final_val = raw
        
        if config['type'] in ['Intracellular', 'Extracellular']:
            final_val = raw * optical_factor
            if name == 'Magnesium': final_val *= 1.35
            if name == 'Zinc' and "Pale" in skin_type: final_val = raw * 0.90
            
        elif config['type'] == 'Metal':
            if is_blocked and raw < 0.02: final_val = raw * 3.5
            
        adjusted[name] = round(final_val, 4)

    # 4. RATIOS
    ratios = {}
    try:
        ratios['Ca/Mg'] = round(adjusted['Calcium'] / adjusted['Magnesium'], 2) if adjusted['Magnesium'] else 0
        ratios['Na/K'] = round(adjusted['Sodium'] / adjusted['Potassium'], 2) if adjusted['Potassium'] else 0
        ratios['Zn/Cu'] = round(adjusted['Zinc'] / adjusted['Copper'], 2) if adjusted['Copper'] else 0
    except: pass

    # Add inferences based on ratios
    if ratios.get('Ca/Mg', 0) > 8.0: inferences.append(f"🔥 Sympathetic Dominance (Ca/Mg {ratios['Ca/Mg']})")
    elif ratios.get('Ca/Mg', 0) < 3.0: inferences.append(f"💧 Parasympathetic Slump (Ca/Mg {ratios['Ca/Mg']})")
    
    if ratios.get('Na/K', 0) < 1.5: inferences.append(f"⚡ Adrenal Stress (Na/K {ratios['Na/K']})")
    if ratios.get('Zn/Cu', 0) < 0.7: inferences.append(f"🛡️ Immune Vulnerability (Zn/Cu {ratios['Zn/Cu']})")

    return adjusted, ratios, inferences

# --- 4. VISUAL PDF GENERATOR ---
def draw_gauge(pdf, label, value, min_val, max_val, ideal_min, ideal_max, unit=""):
    """
    Draws a horizontal 'Traffic Light' gauge on the PDF.
    """
    # Layout Config
    x_start = pdf.get_x()
    y_start = pdf.get_y()
    bar_width = 100
    bar_height = 6
    
    # 1. Draw Text Label
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(40, 8, clean_text(label), 0, 0, 'L')
    
    # 2. Draw Background Bar (Gray)
    pdf.set_fill_color(230, 230, 230)
    pdf.rect(x_start + 40, y_start + 1, bar_width, bar_height, 'F')
    
    # 3. Draw Ideal Zone (Green)
    # Map values to pixels
    def get_pos(val):
        pct = (val - min_val) / (max_val - min_val)
        pct = max(0, min(1, pct)) # Clamp
        return (x_start + 40) + (pct * bar_width)

    ideal_x1 = get_pos(ideal_min)
    ideal_x2 = get_pos(ideal_max)
    
    pdf.set_fill_color(180, 255, 180) # Light Green
    pdf.rect(ideal_x1, y_start + 1, ideal_x2 - ideal_x1, bar_height, 'F')
    
    # 4. Draw Patient Marker (Black Line + Triangle)
    marker_x = get_pos(value)
    pdf.set_draw_color(0, 0, 0)
    pdf.set_line_width(0.5)
    # Line
    pdf.line(marker_x, y_start, marker_x, y_start + bar_height + 1)
    # Value Text
    pdf.set_font("Arial", 'B', 8)
    pdf.set_xy(marker_x - 5, y_start - 4)
    pdf.cell(10, 4, str(value), 0, 0, 'C')
    
    # Reset Position
    pdf.set_xy(x_start, y_start + 10)

def create_visual_report(patient_name, original, adjusted, ratios, inferences):
    pdf = FPDF(orientation='L', format='A4')
    pdf.add_page()
    
    # -- HEADER --
    pdf.set_font("Arial", 'B', 18)
    pdf.cell(0, 10, clean_text(f"OligoScan Visual Analysis: {patient_name}"), ln=True, align='C')
    pdf.ln(5)
    
    # -- RATIO DASHBOARD (Graphics) --
    pdf.set_fill_color(240, 240, 250)
    pdf.rect(10, 25, 277, 50, 'F') # Blue background box
    pdf.set_y(30)
    
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "SYSTEMIC REGULATION DASHBOARD (Adjusted Ratios)", ln=True)
    pdf.ln(2)
    
    # Draw Gauges
    # Ca/Mg: Range 0-12, Ideal 3.0-5.5
    draw_gauge(pdf, "Ca/Mg (Autonomic)", ratios.get('Ca/Mg', 0), 0, 12, 3.0, 5.5)
    
    # Na/K: Range 0-6, Ideal 2.0-4.0
    draw_gauge(pdf, "Na/K (Adrenal)", ratios.get('Na/K', 0), 0, 6, 2.0, 4.0)
    
    # Zn/Cu: Range 0-3, Ideal 0.7-1.2
    draw_gauge(pdf, "Zn/Cu (Immune)", ratios.get('Zn/Cu', 0), 0, 3, 0.7, 1.2)
    
    pdf.ln(10)
    
    # -- CLINICAL NOTES --
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 8, "Clinical Inferences:", ln=True)
    pdf.set_font("Arial", '', 10)
    for inf in inferences:
        pdf.multi_cell(0, 6, clean_text(f"• {inf}"))
    pdf.ln(8)

    # -- PERFECT ALIGNMENT TABLE --
    def add_table_section(title, filter_type):
        pdf.set_font("Arial", 'B', 11)
        pdf.set_fill_color(50, 50, 100)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 8, clean_text(title), 1, 1, 'L', 1)
        
        # Column Headers
        pdf.set_fill_color(220, 220, 220)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", 'B', 9)
        
        # Define Fixed Widths
        w_name = 35
        w_raw = 20
        w_adj = 20
        w_sci = 202 # Remaining width A4 Landscape
        
        pdf.cell(w_name, 6, "Analyte", 1, 0, 'L', 1)
        pdf.cell(w_raw, 6, "Raw", 1, 0, 'C', 1)
        pdf.cell(w_adj, 6, "Adj", 1, 0, 'C', 1)
        pdf.cell(w_sci, 6, "Physiological Relevance & Evidence", 1, 1, 'L', 1)
        
        pdf.set_font("Arial", '', 8)
        
        for name, config in ANALYTE_DB.items():
            if config['type'] == filter_type:
                raw = original.get(name, 0.0)
                adj = adjusted.get(name, 0.0)
                science = config.get('science', '')
                
                # Logic for Coloring
                pdf.set_text_color(0,0,0)
                if filter_type == 'Metal' and adj > raw:
                    pdf.set_text_color(200, 0, 0) # Red for Hidden
                
                # ALIGNMENT TRICK: Use MultiCell for science, record height
                x = pdf.get_x()
                y = pdf.get_y()
                
                # 1. Print Science column first to get height
                pdf.set_xy(x + w_name + w_raw + w_adj, y)
                pdf.multi_cell(w_sci, 5, clean_text(science), 1, 'L')
                
                new_y = pdf.get_y()
                row_height = new_y - y
                
                # 2. Go back and print the other columns with that height
                pdf.set_xy(x, y)
                pdf.cell(w_name, row_height, clean_text(name), 1, 0, 'L')
                pdf.cell(w_raw, row_height, str(raw), 1, 0, 'C')
                pdf.cell(w_adj, row_height, str(adj), 1, 0, 'C')
                
                # 3. Move cursor to next line
                pdf.set_xy(x, new_y)
        
        pdf.ln(5)

    add_table_section("INTRACELLULAR RESERVES", "Intracellular")
    add_table_section("EXTRACELLULAR / REGULATORY", "Extracellular")
    add_table_section("TOXIC METAL BURDEN", "Metal")

    return pdf.output(dest='S').encode('latin-1', 'replace')

# --- 5. UI ---
st.title("🧬 OligoScan Visual Analyzer (v6.0)")
st.sidebar.header("Patient Context")
patient_name = st.sidebar.text_input("Name")
skin_type = st.sidebar.selectbox("Skin Type", ["I-II (Pale)", "III-IV (Medium)", "V-VI (Dark)"])

uploaded_file = st.file_uploader("Upload OligoScan PDF", type="pdf")

if uploaded_file:
    data = extract_all_data(uploaded_file)
    adj_data, ratios, inferences = run_clinical_analysis(data, skin_type)
    
    st.success("Analysis Complete.")
    
    # On-screen preview
    col1, col2, col3 = st.columns(3)
    col1.metric("Ca/Mg Ratio", ratios.get('Ca/Mg', 0))
    col2.metric("Na/K Ratio", ratios.get('Na/K', 0))
    col3.metric("Zn/Cu Ratio", ratios.get('Zn/Cu', 0))
    
    pdf_bytes = create_visual_report(patient_name, data, adj_data, ratios, inferences)
    st.download_button("📄 Download Visual Report", pdf_bytes, "Visual_Report.pdf", "application/pdf")
