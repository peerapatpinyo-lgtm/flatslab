import streamlit as st
import pandas as pd
import numpy as np

# ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="Flat Slab Design Analysis", layout="wide")

st.title("🏗️ Flat Slab Design: DDM & EFM Analysis")
st.markdown("โปรแกรมคำนวณพื้นไร้คานแบบละเอียด แสดงที่มาของตัวเลขทุกขั้นตอน")

# --- 1. SIDEBAR INPUTS ---
st.sidebar.header("1. Input Parameters")

# Material Properties
st.sidebar.subheader("Material Properties")
fc = st.sidebar.number_input("Concrete Strength, f'c (ksc)", value=240.0)
fy = st.sidebar.number_input("Steel Yield Strength, fy (ksc)", value=4000.0)
Ec = 15100 * (fc**0.5) # ACI Formula estimate (ksc)

# Geometry
st.sidebar.subheader("Geometry")
L1 = st.sidebar.number_input("Span Length L1 (Direction of Analysis) (m)", value=6.0)
L2 = st.sidebar.number_input("Transverse Span Length L2 (m)", value=5.0)
h_slab = st.sidebar.number_input("Slab Thickness (cm)", value=20.0)
l_c = st.sidebar.number_input("Storey Height (m)", value=3.0)

st.sidebar.subheader("Column Dimensions")
c1 = st.sidebar.number_input("Column Dimension c1 (Parallel to L1) (cm)", value=40.0)
c2 = st.sidebar.number_input("Column Dimension c2 (Transverse) (cm)", value=40.0)

# Loads
st.sidebar.subheader("Loads")
SDL = st.sidebar.number_input("Superimposed Dead Load (kg/m^2)", value=100.0)
LL = st.sidebar.number_input("Live Load (kg/m^2)", value=300.0)

# --- 2. CALCULATION FUNCTIONS ---

def calculate_loads(h_slab, SDL, LL):
    # Density of concrete approx 2400 kg/m3
    w_self = (h_slab / 100) * 2400
    w_dead = w_self + SDL
    w_u = 1.2 * w_dead + 1.6 * LL
    return w_self, w_dead, w_u

def ddm_analysis(L1, L2, w_u, c1, ln):
    # Total Static Moment
    Mo = (w_u * L2 * (ln**2)) / 8
    
    # Simplified Distribution (Interior Span)
    # Note: These percentages depend on constraints (beam presence etc.)
    # Assuming flat plate (no beams)
    res = {
        "Mo": Mo,
        "Neg_M": Mo * 0.65,
        "Pos_M": Mo * 0.35,
        "Col_Strip_Neg": (Mo * 0.65) * 0.75,
        "Mid_Strip_Neg": (Mo * 0.65) * 0.25,
        "Col_Strip_Pos": (Mo * 0.35) * 0.60,
        "Mid_Strip_Pos": (Mo * 0.35) * 0.40
    }
    return res

def efm_stiffness(c1, c2, L1, L2, h_slab, l_c, Ec):
    # Units conversion to meters/kg where needed, but keeping consistent helps
    # Inputs in cm need conversion for Inertia calculations
    
    # 1. Slab Moment of Inertia (Is)
    # Gross section
    Is = (L2 * 100 * (h_slab**3)) / 12  # cm^4
    
    # 2. Column Moment of Inertia (Ic)
    Ic = (c2 * (c1**3)) / 12 # cm^4
    
    # 3. Slab Stiffness (Ks) - Simplified for Interior
    # Using coefficient 4EI/L
    Ks = (4 * Ec * Is) / (L1 * 100) # kg-cm
    
    # 4. Column Stiffness (Kc)
    Kc = (4 * Ec * Ic) / (l_c * 100) # kg-cm (Assume fixed far end for simplicity of demo)
    # Note: In real EFM, Kc involves infinite stiffness at joint
    
    # 5. Torsional Member Stiffness (Kt)
    # Based on ACI Code
    x = min(c1, h_slab)
    y = max(c1, h_slab) # Approximation for rect section
    # C = constant for torsion
    C = (1 - 0.63 * (x/y)) * (x**3 * y) / 3
    
    # Kt formula: Kt = sum(9 * Ec * C / (L2 * (1 - c2/L2)**3))
    # This is a complex derivation, showing simplified version for demo
    Kt = (9 * Ec * C) / ((L2 * 100) * (1 - (c2/(L2*100)))**3) * 2 # *2 for both sides of column
    
    # 6. Equivalent Column Stiffness (Kec)
    # Formula: 1/Kec = 1/Sigma(Kc) + 1/Kt
    Sum_Kc = 2 * Kc # Upper and Lower columns
    inv_Kec = (1 / Sum_Kc) + (1 / Kt)
    Kec = 1 / inv_Kec
    
    # 7. Distribution Factor (DF)
    # DF = Ks / (Ks + Kec)
    DF = Ks / (Ks + Kec)
    
    return {
        "Is": Is, "Ic": Ic, "Ks": Ks, "Kc": Kc, 
        "C": C, "Kt": Kt, "Sum_Kc": Sum_Kc, "Kec": Kec, "DF": DF
    }

# --- 3. MAIN DISPLAY LOGIC ---

# Preliminary Calcs
ln = L1 - (c1/100) # Clear span
w_self, w_dead, w_u = calculate_loads(h_slab, SDL, LL)

st.header("2. Analysis Results")

# Display Loads
st.subheader("Step 1: Load Calculation")
col1, col2, col3 = st.columns(3)
col1.metric("Self Weight", f"{w_self:.2f} kg/m²")
col2.metric("Total Dead Load", f"{w_dead:.2f} kg/m²")
col3.metric("Factored Load (Wu)", f"{w_u:.2f} kg/m²")

st.latex(r"w_u = 1.2(DL) + 1.6(LL)")

# Check DDM Suitability
st.subheader("Step 2: Method Selection Check (ACI 318)")
limit_ratio = 2.0
ratio = max(L1, L2) / min(L1, L2)
st.write(f"- Span Ratio ($L_{{long}}/L_{{short}}$): **{ratio:.2f}** (Limit: {limit_ratio})")

use_ddm = True
if ratio > limit_ratio:
    st.error("⚠️ Span ratio exceeds 2.0. DDM is NOT allowed. Must use EFM.")
    use_ddm = False
else:
    st.success("✅ Geometry fits DDM criteria.")

method = st.radio("Select Method to View Details:", ["Direct Design Method (DDM)", "Equivalent Frame Method (EFM)"])

st.markdown("---")

if method == "Direct Design Method (DDM)":
    if not use_ddm:
        st.warning("Showing DDM calculations strictly for educational purposes (Code Violation).")
    
    st.header("Direct Design Method Calculation")
    
    ddm_res = ddm_analysis(L1, L2, w_u, c1, ln)
    
    st.markdown("### 3.1 Total Static Moment ($M_o$)")
    st.latex(r"M_o = \frac{w_u L_2 l_n^2}{8}")
    st.write(f"แทนค่า: $M_o = \\frac{{{w_u:.2f} \\times {L2} \\times {ln:.2f}^2}}{{8}}$")
    st.info(f"**Total Static Moment ($M_o$) = {ddm_res['Mo']:.2f} kg-m**")
    
    st.markdown("### 3.2 Longitudinal Distribution (Interior Span)")
    st.write("กระจายโมเมนต์รวมไปยัง Negative และ Positive Moment (ACI Table)")
    
    df_ddm = pd.DataFrame({
        "Location": ["Negative Moment (65%)", "Positive Moment (35%)"],
        "Total Moment (kg-m)": [ddm_res['Neg_M'], ddm_res['Pos_M']]
    })
    st.table(df_ddm)
    
    st.markdown("### 3.3 Transverse Distribution (Column vs Middle Strip)")
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**Negative Moment Distribution**")
        st.write(f"- Column Strip (75%): **{ddm_res['Col_Strip_Neg']:.2f} kg-m**")
        st.write(f"- Middle Strip (25%): **{ddm_res['Mid_Strip_Neg']:.2f} kg-m**")
    with col_b:
        st.markdown("**Positive Moment Distribution**")
        st.write(f"- Column Strip (60%): **{ddm_res['Col_Strip_Pos']:.2f} kg-m**")
        st.write(f"- Middle Strip (40%): **{ddm_res['Mid_Strip_Pos']:.2f} kg-m**")

elif method == "Equivalent Frame Method (EFM)":
    
    st.header("Equivalent Frame Method Calculation")
    st.markdown("ในวิธี EFM เราจะแปลงโครงสร้างพื้นและเสาให้เป็น **Equivalent Frame** เพื่อหาค่า Stiffness")
    
    efm_res = efm_stiffness(c1, c2, L1, L2, h_slab, l_c, Ec)
    
    # 1. Slab Stiffness
    st.subheader("1. Slab Stiffness ($K_s$)")
    st.latex(r"I_s = \frac{L_2 h^3}{12}")
    st.write(f"Inertia Slab ($I_s$): {efm_res['Is']:,.2f} $cm^4$")
    st.latex(r"K_s = \frac{4E_c I_s}{L_1}")
    st.write(f"Stiffness Slab ($K_s$): **{efm_res['Ks']:,.2f}** kg-cm")
    
    # 2. Column Stiffness
    st.subheader("2. Column Stiffness ($K_c$)")
    st.latex(r"I_c = \frac{c_2 c_1^3}{12}")
    st.write(f"Inertia Column ($I_c$): {efm_res['Ic']:,.2f} $cm^4$")
    st.write(f"Stiffness Column ($K_c$): **{efm_res['Kc']:,.2f}** kg-cm")
    
    # 3. Torsional Member
    st.subheader("3. Torsional Member Stiffness ($K_t$)")
    st.markdown("ส่วนที่รับแรงบิด (Torsion) บริเวณหัวเสาที่เชื่อมต่อกับพื้น")
    st.latex(r"K_t = \sum \frac{9 E_c C}{L_2 (1 - c_2/L_2)^3}")
    st.write(f"Torsional Constant ($C$): {efm_res['C']:,.2f} $cm^4$")
    st.write(f"Torsional Stiffness ($K_t$): **{efm_res['Kt']:,.2f}** kg-cm")
    
    # 4. Equivalent Column
    st.subheader("4. Equivalent Column Stiffness ($K_{ec}$)")
    st.markdown("เป็นการรวมความแข็งของเสา ($K_c$) และส่วนรับแรงบิด ($K_t$) เข้าด้วยกัน")
    st.latex(r"\frac{1}{K_{ec}} = \frac{1}{\sum K_c} + \frac{1}{K_t}")
    st.write(f"Sum Columns ($2 \\times K_c$): {efm_res['Sum_Kc']:,.2f}")
    st.success(f"**Equivalent Column Stiffness ($K_{{ec}}$): {efm_res['Kec']:,.2f} kg-cm**")
    
    # 5. Distribution Factors
    st.subheader("5. Distribution Factors (DF) at Joint")
    st.markdown("ปัจจัยการกระจายโมเมนต์เข้าสู่พื้นและเสาเทียบเท่า")
    st.latex(r"DF_{slab} = \frac{K_s}{K_s + K_{ec}}")
    
    df_val = efm_res['DF']
    st.metric("Distribution Factor to Slab", f"{df_val:.4f}")
    st.metric("Distribution Factor to Column (Equivalent)", f"{1 - df_val:.4f}")
    
    st.info("💡 Next Step: ค่า DF นี้จะถูกนำไปใช้ในกระบวนการ Moment Distribution Method (Hardy Cross) เพื่อกระจาย Fixed End Moment (FEM) จนสมดุล")
