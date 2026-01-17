import streamlit as st
import pdfplumber
import re
from fpdf import FPDF

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="OligoScan Adjustment Tool", layout="centered")
st.title("🧬 OligoScan Clinical Adjustment Tool")
st.markdown("""
**Full Spectrum Analysis:**
* **Correction:** Adjusts Zinc (Skin Optics) and Magnesium (Serum Correlation).
* **Projection:** Recalculates Heavy Metal burden if Detox Blockage (Sulfur/Methylation) is detected.
* **Validation:** Lists all other analytes as confirmed/unchanged.
""")

# --- 2. HELPER FUNCTIONS ---
def clean_text(text):
    """Sanitize text for Latin-1 PDF encoding."""
    if not isinstance(text, str): return str(text)
    replacements = {"⛔": "[BLOCKED]", "⚠️": "[RISK]", "✅": "[OK]", "🧬": "", "🔴": "[ALERT]", "✔": ""}
    for char, rep in replacements.items():
        text = text.replace(char, rep)
    return text.encode('latin-1', 'replace').decode('latin-1')

def extract_data_from_pdf(pdf_file):
    data = {}
    full_text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            full_text += page.extract_text() + "\n"
    
    # Regex for ALL analytes found in the provided reports
    # Captures formats like "Silicon 10,9" or "Sodium Na 74.7"
    patterns = {
        # --- MINERALS ---
        'Calcium': r"Calcium\s+([\d,.]+)",
        'Magnesium': r"Magnesium\s+([\d,.]+)",
        'Phosphorus': r"Phosphorus\s+([\d,.]+)",
        'Silicon': r"Silicon\s+([\d,.]+)",
        'Sodium': r"Sodium.*?\s+([\d,.]+)",
        'Potassium': r"Potassium.*?\s+([\d,.]+)",
        'Copper': r"Copper\s+([\d,.]+)",
        'Zinc': r"Zinc\s+([\d,.]+)",
        'Iron': r"Iron.*?\s+([\d,.]+)",
        'Manganese': r"Manganese.*?\s+([\d,.]+)",
        'Chromium': r"Chromium\s+([\d,.]+)",
        'Vanadium': r"Vanadium\s+([\d,.]+)",
        'Boron': r"Boron\s+([\d,.]+)",
        'Cobalt': r"Cobalt.*?\s+([\d,.]+)",
        'Molybdenum': r"Molybdenum.*?\s+([\d,.]+)",
        'Iodine': r"[Il]odine\s+([\d,.]+)", # Handles OCR 'lodine' vs 'Iodine'
        'Lithium': r"Lithium\s+([\d,.]+)",
        'Germanium': r"Germanium\s+([\d,.]+)",
        'Selenium': r"Selenium\s+([\d,.]+)",
        'Sulfur': r"Sulphur\s+([\d,.]+)",
        'Fluorine': r"Fluor\s+([\d,.]+)",
        
        # --- HEAVY METALS ---
        'Aluminum': r"Aluminium\s+([\d,.]+)",
        'Antimony': r"Antimony.*?\s+([\d,.]+)",
        'Silver': r"Silver\s+([\d,.]+)",
        'Arsenic': r"Arsenic.*?\s+([\d,.]+)",
        'Barium': r"Barium.*?\s+([\d,.]+)",
        'Beryllium': r"Beryllium.*?\s+([\d,.]+)",
        'Bismuth': r"Bismuth\s+([\d,.]+)",
        'Cadmium': r"Cadmium\s+([\d,.]+)",
        'Mercury': r"Mercury\s+([\d,.]+)",
        'Nickel': r"Nickel\s+([\d,.]+)",
        'Platinum': r"Platinum\s+([\d,.]+)",
        'Lead': r"Lead\s+([\d,.]+)",
        'Thallium': r"Thallium.*?\s+([\d,.]+)",
        'Thorium': r"Thorium.*?\s+([\d,.]+)",
        'Gadolinium': r"Gadolinium.*?\s+([\d,.]+)",
        'Tin': r"Tin\s+([\d,.]+)",
        
        # --- VITAMINS ---
        'Vit_B6': r"Vitamin B6\s+(\d+)%",
        'Vit_B12': r"Vitamin B12\s+(\d+)%"
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, full_text, re.IGNORECASE)
        if match:
            try:
                # Handle European decimals (10,9 -> 10.9)
                clean_val = match.group(1).replace(',', '.')
                data[key] = float(clean_val)
            except ValueError:
                data[key] = 0.0
        else:
            data[key] = 0.0
            
    return data

# --- 3. UNIVERSAL ADJUSTMENT ENGINE ---
def run_adjustment(data, skin_type, patient_name):
    flags = []
    results = {}
    
    # 1. Blockage Status
    sulfur = data.get('Sulfur', 0)
    vit_b6 = data.get('Vit_B6', 100)
    vit_b12 = data.get('Vit_B12', 100)
    
    is_blocked = (vit_b6 < 60) or (vit_b12 < 60) or (sulfur < 48.1)
    status_msg = "⛔ DETOX BLOCKED" if is_blocked else "✅ OPTIMAL"
    
    if is_blocked:
        flags.append(f"Blockage Detected: Sulfur ({sulfur}) or B6/B12 (<60%) is low.")
        flags.append("Action: Applied 3.5x Projection Multiplier to all Heavy Metals.")

    # 2. Iterate ALL Data Points
    # Define lists to keep report organized
    mineral_list = ['Calcium', 'Magnesium', 'Phosphorus', 'Silicon', 'Sodium', 'Potassium', 
                   'Copper', 'Zinc', 'Iron', 'Manganese', 'Chromium', 'Vanadium', 'Boron', 
                   'Cobalt', 'Molybdenum', 'Iodine', 'Lithium', 'Germanium', 'Selenium', 
                   'Sulfur', 'Fluorine']
                   
    metal_list = ['Aluminum', 'Antimony', 'Silver', 'Arsenic', 'Barium', 'Beryllium', 
                 'Bismuth', 'Cadmium', 'Mercury', 'Nickel', 'Platinum', 'Lead', 
                 'Thallium', 'Thorium', 'Gadolinium', 'Tin']

    # --- PROCESS MINERALS ---
    for item in mineral_list:
        raw = data.get(item, 0.0)
        adj = raw # Default: No change
        
        # Specific Correction Rules
        if item == 'Magnesium':
            adj = raw * 1.35
            
        if item == 'Zinc':
            if skin_type == "I-II (Pale)":
                adj = raw * 0.90
            elif skin_type == "III-IV (Medium)":
                adj = raw * 1.15
            else:
                adj = raw * 1.25
                
        results[item] = round(adj, 4)

    # --- PROCESS METALS ---
    for item in metal_list:
        raw = data.get(item, 0.0)
        adj = raw
        
        # Blockage Rule: If blocked and reading is "safe" (<0.02), assume it's a false negative
        if is_blocked and raw < 0.02:
            adj = raw * 3.5 # The Projection Multiplier
            
        results[item] = round(adj, 5)

    return results, flags, status_msg, mineral_list, metal_list

# --- 4. PDF GENERATOR ---
def create_pdf(patient_name, original_data, results, flags, status_msg, mineral_list, metal_list):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    
    # Title
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, clean_text(f"Adjusted Clinical Report: {patient_name}"), ln=True, align='C')
    pdf.ln(5)
    
    # Status
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, clean_text(f"Detox Status: {status_msg}"), ln=True)
    
    if flags:
        pdf.set_font("Arial", 'I', 9)
        for flag in flags:
            pdf.cell(0, 5, clean_text(f"* {flag}"), ln=True)
    pdf.ln(10)
    
    # --- TABLE HEADER FUNCTION ---
    def print_header(title):
        pdf.set_font("Arial", 'B', 11)
        pdf.set_fill_color(200, 220, 255)
        pdf.cell(60, 8, clean_text(title), 1, 0, 'C', 1)
        pdf.cell(40, 8, "Original", 1, 0, 'C', 1)
        pdf.cell(40, 8, "Adjusted", 1, 0, 'C', 1)
        pdf.cell(50, 8, "Status", 1, 1, 'C', 1)
        pdf.set_font("Arial", size=10)

    # --- MINERALS TABLE ---
    print_header("MINERALS")
    
    for item in mineral_list:
        raw = original_data.get(item, 0.0)
        adj = results.get(item, 0.0)
        
        # Determine Status Label
        note = ""
        if item == 'Zinc': note = "Optics Adj."
        elif item == 'Magnesium': note = "Serum Corr."
        elif raw != adj: note = "Projected"
        
        # Highlight significant changes
        pdf.set_text_color(0, 0, 0)
        if raw != adj: pdf.set_font("Arial", 'B', 10)
        else: pdf.set_font("Arial", '', 10)
            
        pdf.cell(60, 7, clean_text(item), 1)
        pdf.cell(40, 7, str(raw), 1, 0, 'C')
        pdf.cell(40, 7, str(adj), 1, 0, 'C')
        pdf.cell(50, 7, clean_text(note), 1, 1, 'C')
        
    pdf.ln(10)
    
    # --- METALS TABLE ---
    print_header("HEAVY METALS")
    
    for item in metal_list:
        raw = original_data.get(item, 0.0)
        adj = results.get(item, 0.0)
        
        note = ""
        is_changed = (raw != adj)
        
        if is_changed:
            note = "Hidden/Projected"
            pdf.set_text_color(200, 0, 0) # Red text for projected metals
        else:
            pdf.set_text_color(0, 0, 0)
            
        pdf.cell(60, 7, clean_text(item), 1)
        pdf.cell(40, 7, str(raw), 1, 0, 'C')
        pdf.cell(40, 7, str(adj), 1, 0, 'C')
        pdf.cell(50, 7, clean_text(note), 1, 1, 'C')
        
    return pdf.output(dest='S').encode('latin-1', 'replace')

# --- 5. APP UI ---
with st.sidebar:
    st.header("Patient Settings")
    patient_name = st.text_input("Name", "Patient X")
    skin_type = st.selectbox("Skin Type", ["I-II (Pale)", "III-IV (Medium)", "V-VI (Dark)"])

uploaded_file = st.file_uploader("Upload OligoScan PDF", type="pdf")

if uploaded_file:
    # Run Logic
    data = extract_data_from_pdf(uploaded_file)
    results, flags, status, min_list, met_list = run_adjustment(data, skin_type, patient_name)
    
    # Display Summary
    st.subheader(f"Analysis: {status}")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Zinc (Adj)", results['Zinc'], delta=round(results['Zinc']-data['Zinc'], 2))
    col2.metric("Magnesium (Adj)", results['Magnesium'], delta=round(results['Magnesium']-data['Magnesium'], 2))
    
    # Show Lead/Mercury logic specifically
    delta_pb = round(results['Lead'] - data['Lead'], 4)
    col3.metric("Lead (Projected)", results['Lead'], delta=delta_pb, delta_color="inverse")
    
    if flags:
        st.warning(f"{flags[0]}")

    # Generate PDF
    pdf_data = create_pdf(patient_name, data, results, flags, status, min_list, met_list)
    
    st.download_button(
        "📄 Download Full Adjusted Report",
        data=pdf_data,
        file_name=f"{patient_name}_Adjusted.pdf",
        mime="application/pdf"
    )
