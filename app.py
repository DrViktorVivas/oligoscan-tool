import streamlit as st
import pdfplumber
import re
from fpdf import FPDF

# --- 1. CONFIGURATION & UI SETUP ---
st.set_page_config(page_title="OligoScan Adjustment Tool", layout="centered")
st.title("🧬 OligoScan Clinical Adjustment Tool")
st.markdown("""
This tool corrects OligoScan results based on **Bioavailability Logic**:
1.  **Detox Blockage:** Checks Sulfur + Methylation (B6/B12).
2.  **Skin Optics:** Adjusts Zinc/Minerals based on Fitzpatrick Scale.
""")

# --- 2. THE PARSING LOGIC (Reads your specific PDF layout) ---
def extract_data_from_pdf(pdf_file):
    data = {}
    full_text = ""
    
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            full_text += page.extract_text() + "\n"
            
    # Regex patterns to find specific values in the OligoScan text lines
    # Example raw text: "Sulphur 52.3 48.1 52.0" (Value is usually the first number)
    patterns = {
        'Sulfur': r"Sulphur\s+([\d,.]+)",
        'Zinc': r"Zinc\s+([\d,.]+)",
        'Magnesium': r"Magnesium\s+([\d,.]+)",
        'Lead': r"Lead\s+([\d,.]+)",
        'Mercury': r"Mercury\s+([\d,.]+)",
        'Cadmium': r"Cadmium\s+([\d,.]+)",
        'Aluminum': r"Aluminium\s+([\d,.]+)",
        'Gadolinium': r"Gadolinium\s+([\d,.]+)",
        'Vit_B6': r"Vitamin B6\s+(\d+)%",
        'Vit_B12': r"Vitamin B12\s+(\d+)%",
        'Vit_B9': r"Vitamin B9.*?\s+(\d+)%"
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, full_text, re.IGNORECASE)
        if match:
            # Convert "52,3" (Euro format) to "52.3" and make float
            clean_val = match.group(1).replace(',', '.')
            data[key] = float(clean_val)
        else:
            data[key] = 0.0 # Default if not found
            
    return data

# --- 3. THE ADJUSTMENT ENGINE (Your Custom Logic) ---
def run_adjustment(data, skin_type, patient_name):
    flags = []
    results = {}
    
    # Inputs
    sulfur = data.get('Sulfur', 0)
    vit_b6 = data.get('Vit_B6', 100)
    vit_b12 = data.get('Vit_B12', 100)
    
    # Blockage Logic
    methylation_failure = (vit_b6 < 60) or (vit_b12 < 60)
    sulfur_blockage = (sulfur < 48.1)
    is_blocked = methylation_failure or sulfur_blockage
    
    # Heavy Metals Logic
    metals = ['Lead', 'Mercury', 'Cadmium', 'Aluminum', 'Gadolinium']
    results['Metals_Status'] = "OPTIMAL"
    
    if is_blocked:
        results['Metals_Status'] = "⛔ BLOCKED (False Negatives Likely)"
        flags.append(f"CRITICAL: Detox is blocked (Sulfur: {sulfur}, B6: {vit_b6}%, B12: {vit_b12}%).")
        flags.append("Warning: 'Normal' heavy metal readings are likely FALSE NEGATIVES due to retention.")
        
        for metal in metals:
            val = data.get(metal, 0)
            if val < 0.02:
                results[metal] = "⚠️ HIGH RISK (Hidden)"
            else:
                results[metal] = f"{val} (Confirmed High)"
    else:
        for metal in metals:
            results[metal] = data.get(metal, 0)

    # Mineral Logic (Zinc & Magnesium)
    # Magnesium Correction (Serum correlation observed in patients)
    results['Magnesium_Adj'] = round(data.get('Magnesium', 0) * 1.35, 2)
    
    # Zinc Fitzpatrick Correction
    zinc_raw = data.get('Zinc', 0)
    if skin_type == "I-II (Pale)":
        results['Zinc_Adj'] = round(zinc_raw * 0.90, 2)
        flags.append("Zinc adjusted down (-10%) for Pale Skin reflectance.")
    elif skin_type == "III-IV (Medium)":
        results['Zinc_Adj'] = round(zinc_raw * 1.15, 2)
        flags.append("Zinc adjusted up (+15%) for Melanin/Vascular compensation.")
    else:
        results['Zinc_Adj'] = round(zinc_raw * 1.25, 2) # Darker skin
        
    return results, flags

# --- 4. PDF REPORT GENERATOR ---
def create_pdf(patient_name, original_data, results, flags):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Header
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt=f"Clinical Adjustment Report: {patient_name}", ln=True, align='C')
    pdf.line(10, 20, 200, 20)
    pdf.ln(15)
    
    # Status Section
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, f"Detox Status: {results['Metals_Status']}", ln=True)
    pdf.set_font("Arial", size=10)
    
    if "BLOCKED" in results['Metals_Status']:
        pdf.set_text_color(220, 50, 50) # Red
        pdf.multi_cell(0, 10, "NOTE: Patient lacks Methylation cofactors (B6/B12) or Sulfur needed to mobilize metals. Low scan readings are likely false negatives.")
        pdf.set_text_color(0, 0, 0)
    
    pdf.ln(5)
    
    # Heavy Metals Table
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Heavy Metal Projections:", ln=True)
    pdf.set_font("Arial", size=10)
    
    metals = ['Lead', 'Mercury', 'Cadmium', 'Aluminum', 'Gadolinium']
    for metal in metals:
        raw = original_data.get(metal, 0)
        adj = results[metal]
        pdf.cell(50, 10, f"{metal}", border=1)
        pdf.cell(50, 10, f"Scan: {raw}", border=1)
        pdf.cell(80, 10, f"Adjusted: {adj}", border=1, ln=True)

    pdf.ln(10)
    
    # Minerals Table
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Mineral Bioavailability Corrections:", ln=True)
    pdf.set_font("Arial", size=10)
    
    # Zinc
    pdf.cell(50, 10, "Zinc", border=1)
    pdf.cell(50, 10, f"Scan: {original_data.get('Zinc',0)}", border=1)
    pdf.cell(80, 10, f"Adjusted: {results['Zinc_Adj']}", border=1, ln=True)
    
    # Magnesium
    pdf.cell(50, 10, "Magnesium", border=1)
    pdf.cell(50, 10, f"Scan: {original_data.get('Magnesium',0)}", border=1)
    pdf.cell(80, 10, f"Adjusted: {results['Magnesium_Adj']}", border=1, ln=True)
    
    return pdf.output(dest='S').encode('latin-1')

# --- 5. MAIN APP INTERFACE ---
with st.sidebar:
    st.header("Patient Data")
    patient_name = st.text_input("Patient Name", "John Doe")
    skin_type = st.selectbox("Fitzpatrick Skin Type", ["I-II (Pale)", "III-IV (Medium)", "V-VI (Dark)"])

uploaded_file = st.file_uploader("Upload OligoScan PDF", type="pdf")

if uploaded_file is not None:
    st.success("PDF Uploaded Successfully!")
    
    # 1. Parse
    data = extract_data_from_pdf(uploaded_file)
    
    # 2. Process
    adjusted_results, flags = run_adjustment(data, skin_type, patient_name)
    
    # 3. Display Results on Screen
    st.divider()
    st.subheader(f"Results for {patient_name}")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Detox Status", adjusted_results['Metals_Status'])
        st.metric("Zinc (Adjusted)", adjusted_results['Zinc_Adj'], delta=round(adjusted_results['Zinc_Adj'] - data['Zinc'], 1))
    
    with col2:
        st.metric("Sulfur Level", data['Sulfur'])
        st.metric("Magnesium (Adjusted)", adjusted_results['Magnesium_Adj'])

    if flags:
        st.warning("Clinical Flags Detected:")
        for flag in flags:
            st.write(f"- {flag}")
            
    # 4. Generate Download
    pdf_bytes = create_pdf(patient_name, data, adjusted_results, flags)
    st.download_button(
        label="📄 Download Clinical Report",
        data=pdf_bytes,
        file_name=f"{patient_name}_Adjusted_OligoScan.pdf",
        mime="application/pdf"
    )