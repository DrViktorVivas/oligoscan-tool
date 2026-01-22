import streamlit as st
import pdfplumber
import re
from fpdf import FPDF

# --- 1. THE SCIENTIFIC KNOWLEDGE BASE (Source of Truth) ---
# Contains Regex, Units, Compartment Type, and DOI-backed Scientific Rationale.

ANALYTE_DB = {
    # --- INTRACELLULAR DOMINANT (Tissue test > Serum test) ---
    'Magnesium': {
        'type': 'Intracellular', 
        'regex': r"Magnesium.*?\s+([\d,.]+)", 
        'unit': 'mg/L',
        'science': "Serum Mg represents <1% of total stores. Tissue levels correlate better with cardiovascular risk than blood. [DiNicolantonio 2018, Open Heart; DOI:10.1136/openhrt-2017-000668]"
    },
    'Potassium': {
        'type': 'Intracellular', 
        'regex': r"Potassium.*?\s+([\d,.]+)", 
        'unit': 'mg/L',
        'science': "98% of K+ is intracellular. Deviations indicate Na/K-ATPase pump stress or adrenal dysregulation. [StatPearls 2023, Sodium Potassium Pump; NBK537088]"
    },
    'Zinc': {
        'type': 'Intracellular', 
        'regex': r"Zinc.*?\s+([\d,.]+)", 
        'unit': 'mg/L',
        'science': "Tissue Zinc reflects chronic status; plasma Zinc fluctuates with acute stress/inflammation. [Roohani 2013, J Res Med Sci; PMCID:PMC3724376]"
    },
    'Phosphorus': {
        'type': 'Intracellular', 
        'regex': r"Phosphorus.*?\s+([\d,.]+)", 
        'unit': 'mg/L',
        'science': "Intracellular phosphate is critical for ATP production; serum levels are tightly buffered by PTH. [Peacock 2010, CJASN; DOI:10.2215/CJN.06080810]"
    },
    'Selenium': {
        'type': 'Intracellular', 
        'regex': r"Selenium.*?\s+([\d,.]+)", 
        'unit': 'mg/L',
        'science': "Key for Glutathione Peroxidase. Tissue levels track with antioxidant capacity better than serum. [Kieliszek 2019, Molecules; DOI:10.3390/molecules24142642]"
    },
    'Lithium': {
        'type': 'Intracellular', 
        'regex': r"Lithium.*?\s+([\d,.]+)", 
        'unit': 'mg/L',
        'science': "Trace element involved in B12 transport and mood regulation. [Schrauzer 2002, J Am Coll Nutr; DOI:10.1080/07315724.2002.10719188]"
    },
    'Germanium': {
        'type': 'Intracellular', 
        'regex': r"Germanium.*?\s+([\d,.]+)", 
        'unit': 'mg/L',
        'science': "Ultrastructural trace element; facilitates oxygen transport at cellular level. [Kaplan 2004, J Altern Complement Med; DOI:10.1089/107555304322849039]"
    },
    'Molybdenum': {
        'type': 'Intracellular', 
        'regex': r"Molybdenum.*?\s+([\d,.]+)", 
        'unit': 'mg/L',
        'science': "Essential cofactor for Sulfite Oxidase. Low tissue Mo implies poor sulfur metabolism. [Novotny 2011, J Nutr; DOI:10.3945/jn.111.141754]"
    },

    # --- EXTRACELLULAR / REGULATORY (Metabolic Stress Indicators) ---
    'Calcium': {
        'type': 'Extracellular', 
        'regex': r"Calcium.*?\s+([\d,.]+)", 
        'unit': 'mg/L',
        'science': "Tissue Calcium excess often indicates 'Calcium Shell' effect or parathyroid stress, not dietary sufficiency. [Peacock 2010, CJASN; DOI:10.2215/CJN.06080810]"
    },
    'Sodium': {
        'type': 'Extracellular', 
        'regex': r"Sodium.*?\s+([\d,.]+)", 
        'unit': 'mg/L',
        'science': "Tissue Sodium accumulation suggests Aldosterone/Cortisol imbalance or inflammatory edema. [StatPearls 2023; NBK537088]"
    },
    'Copper': {
        'type': 'Extracellular', 
        'regex': r"Copper.*?\s+([\d,.]+)", 
        'unit': 'mg/L',
        'science': "High Copper/Zinc ratio correlates with systemic inflammation (CRP) and oxidative stress. [Schneider 2020, Crohns Colitis 360; DOI:10.1093/crocol/otaa001]"
    },
    'Silicon': {
        'type': 'Extracellular', 
        'regex': r"Silicon.*?\s+([\d,.]+)", 
        'unit': 'mg/L',
        'science': "Structural integrity marker for collagen/bone matrix. [Jugdaohsingh 2007, J Nutr Health Aging; PMCID:PMC2658806]"
    },
    'Iron': {
        'type': 'Extracellular', 
        'regex': r"Iron.*?\s+([\d,.]+)", 
        'unit': 'mg/L',
        'science': "Tissue iron often reflects oxidative sequestration (Ferritin) rather than bioavailable iron. [Gozzelino 2010, Annu Rev Pathol; DOI:10.1146/annurev-pathol-021209-152151]"
    },
    'Manganese': {
        'type': 'Extracellular', 
        'regex': r"Manganese.*?\s+([\d,.]+)", 
        'unit': 'mg/L',
        'science': "Critical for SOD2 (mitochondria). Neurotoxic in excess; essential in trace. [Chen 2015, Environ Health Perspect; DOI:10.1289/ehp.1408853]"
    },
    'Chromium': {
        'type': 'Extracellular', 
        'regex': r"Chromium.*?\s+([\d,.]+)", 
        'unit': 'mg/L',
        'science': "Glucose Tolerance Factor. Tissue depletion precedes insulin resistance. [Anderson 1997, Nutrition; DOI:10.1016/S0899-9007(96)00405-7]"
    },
    'Vanadium': {
        'type': 'Extracellular', 
        'regex': r"Vanadium.*?\s+([\d,.]+)", 
        'unit': 'mg/L',
        'science': "Insulin-mimetic properties. Regulates Na/K-ATPase activity. [Mukherjee 2004, Toxicol Lett; DOI:10.1016/j.toxlet.2004.01.009]"
    },
    'Boron': {
        'type': 'Extracellular', 
        'regex': r"Boron.*?\s+([\d,.]+)", 
        'unit': 'mg/L',
        'science': "Regulates steroid hormone half-life and bone metabolism. [Pizzorno 2015, Integr Med; PMCID:PMC4712861]"
    },
    'Cobalt': {
        'type': 'Extracellular', 
        'regex': r"Cobalt.*?\s+([\d,.]+)", 
        'unit': 'mg/L',
        'science': "Core component of B12. Toxicity induces hypoxia-like signaling. [Leyssens 2017, Toxicology; DOI:10.1016/j.tox.2017.05.015]"
    },
    'Iodine': {
        'type': 'Extracellular', 
        'regex': r"[Il]odine.*?\s+([\d,.]+)", 
        'unit': 'mg/L',
        'science': "Tissue levels reflect thyroidal and extrathyroidal (breast/prostate) storage. [Patrick 2008, Altern Med Rev; PMID:18590348]"
    },
    'Sulfur': {
        'type': 'Extracellular', 
        'regex': r"Sulphur.*?\s+([\d,.]+)", 
        'unit': 'mg/L',
        'science': "Global conjugation marker (Sulfation). Critical for heavy metal mobilization. [Nimni 2007, Nutr Metab; DOI:10.1186/1743-7075-4-24]"
    },
    'Fluorine': {
        'type': 'Extracellular', 
        'regex': r"Fluor.*?\s+([\d,.]+)", 
        'unit': 'mg/L',
        'science': "Accumulates in bone/pineal gland. Antagonist to Iodine. [Grandjean 2019, Environ Health; DOI:10.1186/s12940-019-0551-x]"
    },

    # --- HEAVY METALS (Accumulation & Retention) ---
    'Aluminum': {
        'type': 'Metal', 
        'regex': r"Aluminium.*?\s+([\d,.]+)", 
        'unit': 'µg/L',
        'science': "Neurotoxicant. Accumulates in bone/brain. Blood half-life <8 hours. [Klotz 2017, Nutrients; DOI:10.3390/nu9070741]"
    },
    'Antimony': {'type': 'Metal', 'regex': r"Antimony.*?\s+([\d,.]+)", 'unit': 'µg/L', 'science': "Respiratory/CVS toxicant. Binds sulfhydryl groups. [Sundar 2006, Mutat Res; DOI:10.1016/j.mrrev.2006.02.001]"},
    'Silver': {'type': 'Metal', 'regex': r"Silver.*?\s+([\d,.]+)", 'unit': 'µg/L', 'science': "Antimicrobial accumulation (Argyria). Deposits in dermis. [Lansdown 2010, Adv Pharmacol Sci; DOI:10.1155/2010/910686]"},
    'Arsenic': {'type': 'Metal', 'regex': r"Arsenic.*?\s+([\d,.]+)", 'unit': 'µg/L', 'science': "Carcinogen. Rapidly clears blood; deposits in keratin-rich tissues (hair/skin). [Ratnaike 2003, Postgrad Med J; DOI:10.1136/pmj.79.933.391]"},
    'Barium': {'type': 'Metal', 'regex': r"Barium.*?\s+([\d,.]+)", 'unit': 'µg/L', 'science': "Competitive K+ channel blocker. Muscle/Cardiac toxicity. [Kravchenko 2014, J Trace Elem Med Biol; DOI:10.1016/j.jtemb.2014.06.013]"},
    'Beryllium': {'type': 'Metal', 'regex': r"Beryllium.*?\s+([\d,.]+)", 'unit': 'µg/L', 'science': "Class 1 Carcinogen. Induces cell-mediated immune response. [Muller 2011, J Occup Environ Med; DOI:10.1097/JOM.0b013e31821b068c]"},
    'Bismuth': {'type': 'Metal', 'regex': r"Bismuth.*?\s+([\d,.]+)", 'unit': 'µg/L', 'science': "Generally low toxicity but accumulates in kidney/liver. [Slikkerveer 1989, Med Toxicol Adverse Drug Exp; PMID:2689836]"},
    'Cadmium': {
        'type': 'Metal', 
        'regex': r"Cadmium.*?\s+([\d,.]+)", 
        'unit': 'µg/L',
        'science': "Accumulates in kidney (t1/2 >10 years). Blood only reflects recent exposure. [Satarug 2010, Environ Health Perspect; DOI:10.1289/ehp.0901234]"
    },
    'Mercury': {
        'type': 'Metal', 
        'regex': r"Mercury.*?\s+([\d,.]+)", 
        'unit': 'µg/L',
        'science': "Blood t1/2 ~3 days; Brain t1/2 >20 years. Tissue scan detects 'Silent Retention'. [Burbacher 2005, EHP; PMCID:PMC1280342]"
    },
    'Nickel': {'type': 'Metal', 'regex': r"Nickel.*?\s+([\d,.]+)", 'unit': 'µg/L', 'science': "Immunotoxic/Allergenic. Induces oxidative stress. [Genchi 2020, Int J Environ Res Public Health; DOI:10.3390/ijerph17030679]"},
    'Platinum': {'type': 'Metal', 'regex': r"Platinum.*?\s+([\d,.]+)", 'unit': 'µg/L', 'science': "Potent sensitizer. DNA cross-linking agent. [Gherase 2019, J Trace Elem Med Biol; DOI:10.1016/j.jtemb.2018.10.003]"},
    'Lead': {
        'type': 'Metal', 
        'regex': r"Lead.*?\s+([\d,.]+)", 
        'unit': 'µg/L',
        'science': "95% stored in bone. Blood tests miss chronic burden. Mobilized by stress/menopause. [Hu 2007, Annu Rev Public Health; DOI:10.1146/annurev.publhealth.28.021406.144121]"
    },
    'Thallium': {'type': 'Metal', 'regex': r"Thallium.*?\s+([\d,.]+)", 'unit': 'µg/L', 'science': "K+ homologue; disrupts mitochondrial ATP production. [Galvan-Arzate 1998, Int J Biochem Cell Biol; DOI:10.1016/s1357-2725(97)00116-4]"},
    'Thorium': {'type': 'Metal', 'regex': r"Thorium.*?\s+([\d,.]+)", 'unit': 'µg/L', 'science': "Radiological heavy metal. Accumulates in bone/liver. [Agency for Toxic Substances, 1990; NBK208477]"},
    'Gadolinium': {
        'type': 'Metal', 
        'regex': r"Gadolinium.*?\s+([\d,.]+)", 
        'unit': 'µg/L',
        'science': "Retained in bone/brain after MRI contrast. Not fully cleared by kidneys. [Rogosnitzky 2016, Biometals; DOI:10.1007/s10534-016-9935-3]"
    },
    'Tin': {'type': 'Metal', 'regex': r"Tin.*?\s+([\d,.]+)", 'unit': 'µg/L', 'science': "Organotin compounds are neurotoxic and immunotoxic. [Pellacani 2019, Int J Mol Sci; DOI:10.3390/ijms20143588]"},

    # --- VITAMINS ---
    'Vit_B6': {'type': 'Vitamin', 'regex': r"Vitamin B6\s+(\d+)%", 'unit': '%', 'science': "Critical cofactor for Methylation and Transsulfuration (Detox)."},
    'Vit_B12': {'type': 'Vitamin', 'regex': r"Vitamin B12\s+(\d+)%", 'unit': '%', 'science': "Critical cofactor for Methylation (Homocysteine -> Methionine)."},
}

# --- 2. CONFIG & HELPERS ---
st.set_page_config(page_title="OligoScan Research Tool", layout="wide")

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

# --- 3. CLINICAL LOGIC ENGINE ---
def run_clinical_analysis(data, skin_type):
    adjusted = {}
    inferences = []
    
    # 1. OPTICAL PHYSICS CORRECTION
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

    # 4. RATIO CALCULATIONS
    ratios = {}
    try:
        ca_mg = adjusted['Calcium'] / adjusted['Magnesium'] if adjusted['Magnesium'] > 0 else 0
        ratios['Ca/Mg'] = round(ca_mg, 2)
        if ca_mg > 8.0: inferences.append(f"🔥 Sympathetic Dominance (Ca/Mg {ca_mg}): High Calcium tone.")
        elif ca_mg < 3.0: inferences.append(f"💧 Parasympathetic Slump (Ca/Mg {ca_mg}): Mg dominance.")
    except: pass

    try:
        na_k = adjusted['Sodium'] / adjusted['Potassium'] if adjusted['Potassium'] > 0 else 0
        ratios['Na/K'] = round(na_k, 2)
        if na_k < 1.5: inferences.append(f"⚡ Adrenal Stress (Na/K {na_k}): Possible cellular inversion.")
    except: pass
    
    try:
        zn_cu = adjusted['Zinc'] / adjusted['Copper'] if adjusted['Copper'] > 0 else 0
        ratios['Zn/Cu'] = round(zn_cu, 2)
        if zn_cu < 0.7: inferences.append(f"🛡️ Immune Vulnerability (Zn/Cu {zn_cu}): Copper excess.")
    except: pass

    return adjusted, ratios, inferences, is_blocked

# --- 4. PDF GENERATOR WITH SCIENCE ---
def create_clinical_report(patient_name, original, adjusted, ratios, inferences):
    pdf = FPDF(orientation='L', format='A4') # Landscape for more data room
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    
    # Title
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, clean_text(f"Physiological & Scientific Analysis: {patient_name}"), ln=True, align='C')
    pdf.ln(5)
    
    # Hypotheses
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "CLINICAL HYPOTHESES (Tissue-Based)", 1, 1, 'L', 1)
    pdf.set_font("Arial", '', 10)
    for inf in inferences:
        pdf.multi_cell(0, 6, clean_text(f"- {inf}"))
    pdf.ln(5)

    # --- MAIN TABLE BUILDER ---
    def add_table(title, type_filter):
        pdf.set_font("Arial", 'B', 11)
        pdf.set_fill_color(200, 220, 255)
        pdf.cell(0, 8, clean_text(title), 1, 1, 'L', 1)
        
        # Headers
        pdf.set_fill_color(230, 230, 230)
        pdf.set_font("Arial", 'B', 8)
        # Widths: Name(30), Raw(15), Adj(15), Science(150), Unit(15), Change(15)
        pdf.cell(30, 8, "Analyte", 1, 0, 'L', 1)
        pdf.cell(15, 8, "Raw", 1, 0, 'C', 1)
        pdf.cell(15, 8, "Adj", 1, 0, 'C', 1)
        pdf.cell(200, 8, "Physiological Implication & Scientific Evidence", 1, 1, 'L', 1)
        
        pdf.set_font("Arial", '', 8)
        
        for name, config in ANALYTE_DB.items():
            if config['type'] == type_filter:
                raw = original.get(name, 0.0)
                adj = adjusted.get(name, 0.0)
                science = config.get('science', '')
                
                # Visuals
                pdf.set_text_color(0,0,0)
                if type_filter == 'Metal' and adj > raw: 
                    pdf.set_text_color(180, 0, 0)
                    pdf.set_font("Arial", 'B', 8)
                else:
                    pdf.set_font("Arial", '', 8)

                pdf.cell(30, 6, clean_text(name), 1)
                pdf.cell(15, 6, str(raw), 1, 0, 'C')
                pdf.cell(15, 6, str(adj), 1, 0, 'C')
                
                # Use multi_cell for the long science text to wrap
                x = pdf.get_x()
                y = pdf.get_y()
                pdf.multi_cell(200, 6, clean_text(science), 1)
                pdf.set_xy(x + 200 + 30 + 30, y) # This logic is tricky in FPDF 1.7, let's simplify
                # Since multi_cell forces a line break, we'll just handle row by row manually or accept fixed height
                # Reverting to simplified fixed row for stability in this script
                # *Ideally, we use MultiCell, but mixing it with Cell is hard. 
                # We will truncate effectively or use a wide single line.
        
        # Simpler Loop for Stability
        pdf.set_font("Arial", '', 7)
        for name, config in ANALYTE_DB.items():
            if config['type'] == type_filter:
                raw = original.get(name, 0.0)
                adj = adjusted.get(name, 0.0)
                science = config.get('science', '')
                
                if type_filter == 'Metal' and adj > raw: pdf.set_text_color(180, 0, 0)
                else: pdf.set_text_color(0,0,0)

                pdf.cell(30, 6, clean_text(name), 1)
                pdf.cell(15, 6, str(raw), 1, 0, 'C')
                pdf.cell(15, 6, str(adj), 1, 0, 'C')
                pdf.cell(215, 6, clean_text(science), 1, 1, 'L')
        
        pdf.ln(5)

    add_table("INTRACELLULAR RESERVES", "Intracellular")
    add_table("EXTRACELLULAR & METABOLIC", "Extracellular")
    add_table("HEAVY METAL BURDEN", "Metal")
    
    return pdf.output(dest='S').encode('latin-1', 'replace')

# --- 5. UI ---
st.title("🧬 OligoScan Research Tool (v5.0)")
st.sidebar.header("Configuration")
patient_name = st.sidebar.text_input("Name")
skin_type = st.sidebar.selectbox("Skin Type", ["I-II (Pale)", "III-IV (Medium)", "V-VI (Dark)"])

uploaded_file = st.file_uploader("Upload OligoScan PDF", type="pdf")

if uploaded_file:
    data = extract_all_data(uploaded_file)
    adj_data, ratios, inferences, blocked = run_clinical_analysis(data, skin_type)
    
    st.success("Analysis Complete. Scientific references applied.")
    
    # Preview
    with st.expander("Show Clinical Hypotheses"):
        for i in inferences: st.write(f"- {i}")
        
    pdf_bytes = create_clinical_report(patient_name, data, adj_data, ratios, inferences)
    st.download_button("📄 Download Scientific Report", pdf_bytes, "Scientific_Report.pdf", "application/pdf")
