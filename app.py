import streamlit as st
import pdfplumber
import re
from fpdf import FPDF

# --- 1. SCIENTIFIC KNOWLEDGE BASE & REFERENCE RANGES ---
ANALYTE_DB = {
    # --- INTRACELLULAR ---
    'Magnesium': {
        'type': 'Intracellular', 'regex': r"Magnesium.*?\s+([\d,.]+)", 'unit': 'mg/L',
        'min': 30.5, 'max': 75.7,
        'science': "Serum Mg misses 99% of deficiency. Tissue levels predict cardiovascular risk better than blood. [DiNicolantonio 2018; DOI:10.1136/openhrt-2017-000668]"
    },
    'Potassium': {
        'type': 'Intracellular', 'regex': r"Potassium.*?\s+([\d,.]+)", 'unit': 'mg/L',
        'min': 9.0, 'max': 39.0,
        'science': "98% of K+ is intracellular. Low tissue levels suggest Na/K-ATPase pump failure or adrenal exhaustion. [StatPearls 2023; NBK537088]"
    },
    'Zinc': {
        'type': 'Intracellular', 'regex': r"Zinc.*?\s+([\d,.]+)", 'unit': 'mg/L',
        'min': 125.0, 'max': 155.0,
        'science': "Tissue Zinc reflects chronic status, whereas plasma Zinc fluctuates acutely with inflammation/stress. [Roohani 2013; PMCID:PMC3724376]"
    },
    'Phosphorus': {
        'type': 'Intracellular', 'regex': r"Phosphorus.*?\s+([\d,.]+)", 'unit': 'mg/L',
        'min': 144.0, 'max': 199.0,
        'science': "Intracellular phosphate is critical for ATP production. Serum levels are tightly buffered by PTH. [Peacock 2010; DOI:10.2215/CJN.06080810]"
    },
    'Selenium': {
        'type': 'Intracellular', 'regex': r"Selenium.*?\s+([\d,.]+)", 'unit': 'mg/L',
        'min': 0.95, 'max': 1.77,
        'science': "Key for Glutathione Peroxidase. Tissue levels track antioxidant capacity better than serum. [Kieliszek 2019; DOI:10.3390/molecules24142642]"
    },
    'Lithium': {
        'type': 'Intracellular', 'regex': r"Lithium.*?\s+([\d,.]+)", 'unit': 'mg/L',
        'min': 0.052, 'max': 0.120,
        'science': "Trace element involved in B12 transport and mood stability. [Schrauzer 2002; DOI:10.1080/07315724.2002.10719188]"
    },
    'Germanium': {
        'type': 'Intracellular', 'regex': r"Germanium.*?\s+([\d,.]+)", 'unit': 'mg/L',
        'min': 0.003, 'max': 0.028,
        'science': "Ultrastructural element; facilitates cellular oxygen transport. [Kaplan 2004; DOI:10.1089/107555304322849039]"
    },
    'Molybdenum': {
        'type': 'Intracellular', 'regex': r"Molybdenum.*?\s+([\d,.]+)", 'unit': 'mg/L',
        'min': 0.035, 'max': 0.085,
        'science': "Essential cofactor for Sulfite Oxidase. Low tissue Mo implies poor sulfur metabolism/detox. [Novotny 2011; DOI:10.3945/jn.111.141754]"
    },

    # --- EXTRACELLULAR ---
    'Calcium': {
        'type': 'Extracellular', 'regex': r"Calcium.*?\s+([\d,.]+)", 'unit': 'mg/L',
        'min': 279.0, 'max': 598.0,
        'science': "High tissue Calcium often indicates 'Calcium Shell' effect (unavailable) or parathyroid stress. [Peacock 2010; DOI:10.2215/CJN.06080810]"
    },
    'Sodium': {
        'type': 'Extracellular', 'regex': r"Sodium.*?\s+([\d,.]+)", 'unit': 'mg/L',
        'min': 21.0, 'max': 89.0,
        'science': "Tissue accumulation suggests Aldosterone/Cortisol imbalance or inflammatory edema. [StatPearls 2023; NBK537088]"
    },
    'Copper': {
        'type': 'Extracellular', 'regex': r"Copper.*?\s+([\d,.]+)", 'unit': 'mg/L',
        'min': 11.0, 'max': 28.0,
        'science': "High Copper/Zinc ratio correlates with systemic inflammation (CRP) and oxidative stress. [Schneider 2020; DOI:10.1093/crocol/otaa001]"
    },
    'Silicon': {
        'type': 'Extracellular', 'regex': r"Silicon.*?\s+([\d,.]+)", 'unit': 'mg/L',
        'min': 15.0, 'max': 31.0,
        'science': "Structural integrity marker for collagen/bone matrix. [Jugdaohsingh 2007; PMCID:PMC2658806]"
    },
    'Iron': {
        'type': 'Extracellular', 'regex': r"Iron.*?\s+([\d,.]+)", 'unit': 'mg/L',
        'min': 5.0, 'max': 15.0,
        'science': "Tissue iron often reflects oxidative sequestration (Ferritin) rather than bioavailable iron. [Gozzelino 2010; DOI:10.1146/annurev-pathol-021209-152151]"
    },
    'Manganese': {
        'type': 'Extracellular', 'regex': r"Manganese.*?\s+([\d,.]+)", 'unit': 'mg/L',
        'min': 0.31, 'max': 0.75,
        'science': "Critical for SOD2 (mitochondria). Neurotoxic in excess; essential in trace. [Chen 2015; DOI:10.1289/ehp.1408853]"
    },
    'Chromium': {
        'type': 'Extracellular', 'regex': r"Chromium.*?\s+([\d,.]+)", 'unit': 'mg/L',
        'min': 0.82, 'max': 1.25,
        'science': "Glucose Tolerance Factor. Tissue depletion often precedes insulin resistance. [Anderson 1997; DOI:10.1016/S0899-9007(96)00405-7]"
    },
    'Vanadium': {
        'type': 'Extracellular', 'regex': r"Vanadium.*?\s+([\d,.]+)", 'unit': 'mg/L',
        'min': 0.009, 'max': 0.083,
        'science': "Insulin-mimetic properties. Regulates Na/K-ATPase activity. [Mukherjee 2004; DOI:10.1016/j.toxlet.2004.01.009]"
    },
    'Boron': {
        'type': 'Extracellular', 'regex': r"Boron.*?\s+([\d,.]+)", 'unit': 'mg/L',
        'min': 0.84, 'max': 2.87,
        'science': "Regulates steroid hormone half-life and bone metabolism. [Pizzorno 2015; PMCID:PMC4712861]"
    },
    'Cobalt': {
        'type': 'Extracellular', 'regex': r"Cobalt.*?\s+([\d,.]+)", 'unit': 'mg/L',
        'min': 0.025, 'max': 0.045,
        'science': "Core component of B12. Toxicity induces hypoxia-like signaling. [Leyssens 2017; DOI:10.1016/j.tox.2017.05.015]"
    },
    'Iodine': {
        'type': 'Extracellular', 'regex': r"[Il]odine.*?\s+([\d,.]+)", 'unit': 'mg/L',
        'min': 0.32, 'max': 0.59,
        'science': "Tissue levels reflect thyroidal and extrathyroidal (breast/prostate) storage. [Patrick 2008; PMID:18590348]"
    },
    'Sulfur': {
        'type': 'Extracellular', 'regex': r"Sulphur.*?\s+([\d,.]+)", 'unit': 'mg/L',
        'min': 48.1, 'max': 52.0,
        'science': "Global conjugation marker (Sulfation). Critical for heavy metal mobilization. [Nimni 2007; DOI:10.1186/1743-7075-4-24]"
    },
    'Fluorine': {
        'type': 'Extracellular', 'regex': r"Fluor.*?\s+([\d,.]+)", 'unit': 'mg/L',
        'min': 0.41, 'max': 1.75,
        'science': "Accumulates in bone/pineal gland. Antagonist to Iodine. [Grandjean 2019; DOI:10.1186/s12940-019-0551-x]"
    },

    # --- HEAVY METALS ---
    'Aluminum': {'type': 'Metal', 'regex': r"Aluminium.*?\s+([\d,.]+)", 'unit': 'µg/L', 'min': 0, 'max': 0.015, 'science': "Neurotoxicant. Accumulates in bone/brain. Blood half-life <8 hours. [Klotz 2017; DOI:10.3390/nu9070741]"},
    'Antimony': {'type': 'Metal', 'regex': r"Antimony.*?\s+([\d,.]+)", 'unit': 'µg/L', 'min': 0, 'max': 0.005, 'science': "Respiratory/CVS toxicant. Binds sulfhydryl groups. [Sundar 2006; DOI:10.1016/j.mrrev.2006.02.001]"},
    'Silver': {'type': 'Metal', 'regex': r"Silver.*?\s+([\d,.]+)", 'unit': 'µg/L', 'min': 0, 'max': 0.010, 'science': "Antimicrobial accumulation (Argyria). Deposits in dermis. [Lansdown 2010; DOI:10.1155/2010/910686]"},
    'Arsenic': {'type': 'Metal', 'regex': r"Arsenic.*?\s+([\d,.]+)", 'unit': 'µg/L', 'min': 0, 'max': 0.008, 'science': "Carcinogen. Rapidly clears blood; deposits in keratin-rich tissues. [Ratnaike 2003; DOI:10.1136/pmj.79.933.391]"},
    'Barium': {'type': 'Metal', 'regex': r"Barium.*?\s+([\d,.]+)", 'unit': 'µg/L', 'min': 0, 'max': 0.006, 'science': "Competitive K+ channel blocker. Muscle/Cardiac toxicity. [Kravchenko 2014; DOI:10.1016/j.jtemb.2014.06.013]"},
    'Beryllium': {'type': 'Metal', 'regex': r"Beryllium.*?\s+([\d,.]+)", 'unit': 'µg/L', 'min': 0, 'max': 0.005, 'science': "Class 1 Carcinogen. Induces cell-mediated immune response. [Muller 2011; DOI:10.1097/JOM.0b013e31821b068c]"},
    'Bismuth': {'type': 'Metal', 'regex': r"Bismuth.*?\s+([\d,.]+)", 'unit': 'µg/L', 'min': 0, 'max': 0.010, 'science': "Generally low toxicity but accumulates in kidney/liver. [Slikkerveer 1989; PMID:2689836]"},
    'Cadmium': {'type': 'Metal', 'regex': r"Cadmium.*?\s+([\d,.]+)", 'unit': 'µg/L', 'min': 0, 'max': 0.008, 'science': "Accumulates in kidney (t1/2 >10 years). Blood only reflects recent exposure. [Satarug 2010; DOI:10.1289/ehp.0901234]"},
    'Mercury': {'type': 'Metal', 'regex': r"Mercury.*?\s+([\d,.]+)", 'unit': 'µg/L', 'min': 0, 'max': 0.010, 'science': "Brain t1/2 >20 years. Tissue scan detects 'Silent Retention'. [Burbacher 2005; PMCID:PMC1280342]"},
    'Nickel': {'type': 'Metal', 'regex': r"Nickel.*?\s+([\d,.]+)", 'unit': 'µg/L', 'min': 0, 'max': 0.006, 'science': "Immunotoxic/Allergenic. Induces oxidative stress. [Genchi 2020; DOI:10.3390/ijerph17030679]"},
    'Platinum': {'type': 'Metal', 'regex': r"Platinum.*?\s+([\d,.]+)", 'unit': 'µg/L', 'min': 0, 'max': 0.005, 'science': "Potent sensitizer. DNA cross-linking agent. [Gherase 2019; DOI:10.1016/j.jtemb.2018.10.003]"},
    'Lead': {'type': 'Metal', 'regex': r"Lead.*?\s+([\d,.]+)", 'unit': 'µg/L', 'min': 0, 'max': 0.010, 'science': "95% stored in bone. Mobilized by stress/menopause. [Hu 2007; DOI:10.1146/annurev.publhealth.28.021406.144121]"},
    'Thallium': {'type': 'Metal', 'regex': r"Thallium.*?\s+([\d,.]+)", 'unit': 'µg/L', 'min': 0, 'max': 0.002, 'science': "K+ homologue; disrupts mitochondrial ATP production. [Galvan-Arzate 1998; DOI:10.1016/s1357-2725(97)00116-4]"},
    'Thorium': {'type': 'Metal', 'regex': r"Thorium.*?\s+([\d,.]+)", 'unit': 'µg/L', 'min': 0, 'max': 0.002, 'science': "Radiological heavy metal. Accumulates in bone/liver. [ATSDR 1990; NBK208477]"},
    'Gadolinium': {'type': 'Metal', 'regex': r"Gadolinium.*?\s+([\d,.]+)", 'unit': 'µg/L', 'min': 0, 'max': 0.005, 'science': "Retained in bone/brain after MRI contrast. Not fully cleared by kidneys. [Rogosnitzky 2016; DOI:10.1007/s10534-016-9935-3]"},
    'Tin': {'type': 'Metal', 'regex': r"Tin.*?\s+([\d,.]+)", 'unit': 'µg/L', 'min': 0, 'max': 0.010, 'science': "Organotin compounds are neurotoxic and immunotoxic. [Pellacani 2019; DOI:10.3390/ijms20143588]"},
    
    # --- VITAMINS ---
    'Vit_B6': {'type': 'Vitamin', 'regex': r"Vitamin B6\s+(\d+)%", 'unit': '%', 'min': 60, 'max': 100, 'science': "Critical cofactor for Methylation and Transsulfuration."},
    'Vit_B12': {'type': 'Vitamin', 'regex': r"Vitamin B12\s+(\d+)%", 'unit': '%', 'min': 60, 'max': 100, 'science': "Critical cofactor for Methylation."},
}

# --- 2. CONFIG & HELPERS ---
st.set_page_config(page_title="OligoScan Advanced Analyzer", layout="wide")

def clean_text(text):
    if not isinstance(text, str): return str(text)
    replacements = {"⛔": "[BLOCKED]", "⚠️": "[RISK]", "✅": "[OK]", "🔥": "[HIGH]", "💧": "[LOW]", "⚡": "[STRESS]", "🛡️": "[IMMUNE]", "🧬": "", "✔": ""}
    for char, rep in replacements.items():
        text = text.replace(char, rep)
    return text.encode('latin-1', 'replace').decode('latin-1')

def classify_analyte(val, min_ref, max_ref):
    """
    Revised 7-Point Clinical Scale:
    Very Low | Low | Lower-End Normal | Normal | High-End Normal | High | Very High
    """
    if val <= 0: return "N/A"
    
    # Threshold Calculations
    r_range = max_ref - min_ref
    one_third = r_range / 3
    
    # Logic
    if val < min_ref * 0.9: return "Very Low"
    if val < min_ref: return "Low"
    
    # Normal Range Split (3 Parts)
    if val < (min_ref + one_third): return "Lower-End Normal"
    if val < (min_ref + 2 * one_third): return "Normal"
    if val <= max_ref: return "High-End Normal"
    
    if val < max_ref * 1.1: return "High"
    return "Very High"

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
    classifications = {}
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

    # 3. ADJUSTMENT LOOP
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
        
        # 4. CLASSIFICATION
        if 'min' in config:
            classifications[name] = classify_analyte(final_val, config['min'], config['max'])
        else:
            classifications[name] = "-"

    # 5. RATIOS
    ratios = {}
    try:
        ratios['Ca/Mg'] = round(adjusted['Calcium'] / adjusted['Magnesium'], 2) if adjusted['Magnesium'] else 0
        ratios['Na/K'] = round(adjusted['Sodium'] / adjusted['Potassium'], 2) if adjusted['Potassium'] else 0
        ratios['Zn/Cu'] = round(adjusted['Zinc'] / adjusted['Copper'], 2) if adjusted['Copper'] else 0
    except: pass

    if ratios.get('Ca/Mg', 0) > 8.0: inferences.append(f"🔥 Sympathetic Dominance (Ca/Mg {ratios['Ca/Mg']})")
    elif ratios.get('Ca/Mg', 0) < 3.0: inferences.append(f"💧 Parasympathetic Slump (Ca/Mg {ratios['Ca/Mg']})")
    if ratios.get('Na/K', 0) < 1.5: inferences.append(f"⚡ Adrenal Stress (Na/K {ratios['Na/K']})")
    if ratios.get('Zn/Cu', 0) < 0.7: inferences.append(f"🛡️ Immune Vulnerability (Zn/Cu {ratios['Zn/Cu']})")

    return adjusted, classifications, ratios, inferences

# --- 4. PDF GENERATOR ---
def create_report_pdf(patient_name, original, adjusted, classifications, ratios, inferences):
    pdf = FPDF(orientation='P', format='A4')
    pdf.add_page()
    
    # HEADER
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, clean_text(f"OligoScan Advanced Analysis: {patient_name}"), ln=True, align='C')
    pdf.ln(5)

    # INFERENCES
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 8, "CLINICAL SUMMARY", 1, 1, 'L', 1)
    pdf.set_font("Arial", '', 10)
    for inf in inferences:
        pdf.multi_cell(0, 6, clean_text(f"• {inf}"))
    pdf.ln(5)

    # TABLE GENERATOR FUNCTION
    def add_table_section(title, filter_type):
        pdf.set_font("Arial", 'B', 12)
        pdf.set_fill_color(50, 50, 100)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 8, clean_text(title), 1, 1, 'L', 1)
        
        pdf.set_text_color(0, 0, 0)
        
        for name, config in ANALYTE_DB.items():
            if config['type'] == filter_type:
                raw_val = original.get(name, 0.0)
                adj = adjusted.get(name, 0.0)
                status = classifications.get(name, "-")
                science = config.get('science', '')
                
                # --- ROW 1: DATA (Name | Raw | Adjusted | Status) ---
                pdf.set_fill_color(230, 235, 250) # Light Blue
                pdf.set_font("Arial", 'B', 10)
                
                # Colors for Status
                if "Very Low" in status or "Very High" in status: pdf.set_text_color(200, 0, 0)
                elif "Low" in status or "High" in status: pdf.set_text_color(150, 0, 0)
                elif "Normal" in status or "OK" in status: pdf.set_text_color(0, 100, 0)
                else: pdf.set_text_color(0,0,0)
                
                # Columns: Name(50), Raw(25), Adj(25), Status(90)
                pdf.cell(50, 7, clean_text(name), 1, 0, 'L', 1)
                
                # Raw Value (Black)
                pdf.set_text_color(0, 0, 0)
                pdf.set_font("Arial", '', 10)
                pdf.cell(25, 7, str(raw_val), 1, 0, 'C', 1)
                
                # Adjusted Value (Black)
                pdf.cell(25, 7, f"{adj}", 1, 0, 'C', 1)
                
                # Status Text (Colored)
                if "Very Low" in status or "Very High" in status: pdf.set_text_color(200, 0, 0)
                elif "Low" in status or "High" in status: pdf.set_text_color(150, 0, 0)
                elif "Normal" in status or "OK" in status: pdf.set_text_color(0, 100, 0)
                
                pdf.set_font("Arial", 'B', 10)
                pdf.cell(90, 7, clean_text(status), 1, 1, 'C', 1)
                
                # --- ROW 2: SCIENCE (Full Width) ---
                pdf.set_text_color(80, 80, 80) # Dark Gray
                pdf.set_font("Arial", 'I', 8)
                pdf.set_fill_color(255, 255, 255) # White
                
                # Full width cell below
                pdf.multi_cell(0, 5, clean_text(f"Evidence: {science}"), 1, 'L', 0)
                
        pdf.ln(5)

    add_table_section("INTRACELLULAR ELEMENTS", "Intracellular")
    add_table_section("EXTRACELLULAR ELEMENTS", "Extracellular")
    add_table_section("TOXIC METALS", "Metal")
    
    return pdf.output(dest='S').encode('latin-1', 'replace')

# --- 5. UI ---
st.title("🧬 OligoScan Advanced Tool (v8.0)")
st.sidebar.header("Configuration")
patient_name = st.sidebar.text_input("Patient Name")
skin_type = st.sidebar.selectbox("Skin Type", ["I-II (Pale)", "III-IV (Medium)", "V-VI (Dark)"])

uploaded_file = st.file_uploader("Upload OligoScan PDF", type="pdf")

if uploaded_file:
    data = extract_all_data(uploaded_file)
    adj, classes, ratios, inf = run_clinical_analysis(data, skin_type)
    
    st.success("Analysis Complete.")
    
    pdf_bytes = create_report_pdf(patient_name, data, adj, classes, ratios, inf)
    st.download_button("📄 Download Clinical Report", pdf_bytes, "Clinical_Report.pdf", "application/pdf")
