import streamlit as st
import numpy as np
import pandas as pd
from geometry_view import plot_geometry_detailed

# ==========================================
# 1. SETUP & STYLING
# ==========================================
st.set_page_config(page_title="Pro Flat Slab Design", layout="wide", page_icon="🏗️")
st.markdown("""
<style>
    .pass { color: #198754; font-weight: bold; }
    .fail { color: #dc3545; font-weight: bold; }
    .stMetric { background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 5px; padding: 10px; }
</style>
""", unsafe_allow_html=True)

# Helper for showing formulas
def math_row(label, formula, sub, result, unit, status=None):
    c1, c2, c3 = st.columns([2, 2, 1])
    with c1: st.markdown(f"**{label}**"); st.latex(formula)
    with c2: st.markdown(f"Substituting:"); st.latex(sub)
    with c3: 
        st.markdown(f"Result ({unit})")
        st.metric("", result)
        if status == "PASS": st.markdown(":white_check_mark: <span class='pass'>PASS</span>", unsafe_allow_html=True)
        elif status == "FAIL": st.markdown(":x: <span class='fail'>FAIL</span>", unsafe_allow_html=True)
    st.markdown("---")

# ==========================================
# 2. SIDEBAR INPUTS
# ==========================================
st.sidebar.header("🏗️ Project Parameters")

with st.sidebar.expander("1. Material & Section", expanded=True):
    fc = st.number_input("f'c (ksc)", 240.0, step=10.0)
    fy = st.number_input("fy (ksc)", 4000.0, step=100.0)
    h_slab = st.number_input("Slab Thickness (cm)", 20.0, step=1.0)
    cover = st.number_input("Concrete Cover (cm)", 2.5, step=0.5)
    d_bar = st.selectbox("Main Rebar Diameter (mm)", [12, 16, 20, 25, 28], index=1)

with st.sidebar.expander("2. Geometry", expanded=True):
    L1 = st.number_input("L1: Span Length (m)", 6.0)
    L2 = st.number_input("L2: Transverse Span (m)", 6.0)
    lc = st.number_input("Storey Height (m)", 3.0)
    c1 = st.number_input("c1: Col width // L1 (cm)", 40.0)
    c2 = st.number_input("c2: Col width // L2 (cm)", 40.0)

with st.sidebar.expander("3. Loads", expanded=True):
    SDL = st.number_input("SDL (kg/m²)", 150.0)
    LL = st.number_input("Live Load (kg/m²)", 300.0)

# ==========================================
# 3. CALCULATION ENGINE
# ==========================================
# Units & Constants
d_eff = h_slab - cover - (d_bar/10.0/2.0) # Effective depth (cm)
L1_cm, L2_cm, lc_cm = L1*100, L2*100, lc*100
Ec = 15100 * np.sqrt(fc) # ksc

# Loads
w_self = (h_slab/100)*2400
w_u = 1.2*(w_self + SDL) + 1.6*LL

# A. Stiffness (EFM)
Is = (L2_cm * h_slab**3)/12
Ic = (c2 * c1**3)/12
Ks = 4*Ec*Is/L1_cm
Kc = 4*Ec*Ic/lc_cm

x, y = min(c1, h_slab), max(c1, h_slab)
C_tor = (1 - 0.63*(x/y)) * (x**3 * y)/3
Kt = 2 * (9*Ec*C_tor) / (L2_cm * (1 - c2/L2_cm)**3)
# Prevent div by zero
sum_kc = 2*Kc
Kec = 1 / (1/sum_kc + 1/Kt) if (sum_kc > 0 and Kt > 0) else 0

DF_slab = Ks/(Ks+Kec) if (Ks+Kec) > 0 else 0
DF_col = 1 - DF_slab

# B. Punching Shear (ACI 318)
# Critical Perimeter bo
c1_d = c1 + d_eff
c2_d = c2 + d_eff
bo = 2*c1_d + 2*c2_d

# Shear Demand (Vu) - Approx for interior column
area_trib = L1 * L2
area_col_crit = (c1_d/100) * (c2_d/100)
Vu = w_u * (area_trib - area_col_crit) # kg

# Shear Capacity (Vc)
phi = 0.85
Vc_basic = 1.06 * np.sqrt(fc) * bo * d_eff
PhiVc = phi * Vc_basic

# Check Status
shear_status = "PASS" if PhiVc >= Vu else "FAIL"
min_h_req = max(L1_cm, L2_cm)/33
thick_status = "PASS" if h_slab >= min_h_req else "FAIL" 

# ==========================================
# 4. MAIN DISPLAY
# ==========================================
st.title("🏗️ Professional Flat Slab Design")
st.markdown(f"**Analysis Status:** {'✅ SAFE' if shear_status=='PASS' and thick_status=='PASS' else '❌ CRITICAL'}")

tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Dashboard & Safety", 
    "📝 Detailed Calculation", 
    "📐 Geometry View",
    "📥 Summary Report"
])

# --- TAB 1: DASHBOARD ---
with tab1:
    col1, col2, col3, col4 = st.columns(4)
    
    # Calculate utilization safely
    util_percent = (Vu / PhiVc * 100) if PhiVc > 0 else 0.0

    col1.metric("Factored Load (Wu)", f"{w_u:,.0f} kg/m²")
    col2.metric("Effective Depth (d)", f"{d_eff:.2f} cm")
    
    col3.metric("Shear Capacity (φVc)", f"{PhiVc:,.0f} kg", 
                delta_color="normal" if shear_status=="PASS" else "inverse")
    
    # --- FIXED LINE HERE (รวมหน่วยไว้ใน value string) ---
    col4.metric("Shear Demand (Vu)", f"{Vu:,.0f} kg", 
                delta=f"{util_percent:.1f}% Utilized", delta_color="inverse")

    st.markdown("---")
    st.subheader("🛑 Design Checks Summary")
    chk1, chk2 = st.columns(2)
    with chk1:
        if shear_status == "PASS":
            st.success(f"**Punching Shear: PASSED**\n\nRatio {Vu/PhiVc:.2f} < 1.0")
        else:
            st.error(f"**Punching Shear: FAILED**\n\nRequires thicker slab or higher f'c")
    with chk2:
        if thick_status == "PASS":
            st.success(f"**Min. Thickness: PASSED**\n\nProvided {h_slab} cm > Limit {min_h_req:.1f} cm")
        else:
            st.warning(f"**Min. Thickness: WARNING**\n\nProvided {h_slab} cm < Limit {min_h_req:.1f} cm. Check Deflection!")

# --- TAB 2: DETAILED CALCULATION ---
with tab2:
    st.header("1. Load Analysis")
    math_row("Design Load", r"w_u = 1.2DL + 1.6LL", 
             fr"1.2({w_self+SDL:.0f}) + 1.6({LL:.0f})", f"{w_u:.1f}", "kg/m²")
    
    st.header("2. Equivalent Frame Method (Stiffness)")
    with st.expander("Show EFM Derivation", expanded=True):
        math_row("Slab Stiffness (Ks)", r"K_s = \frac{4E_c I_s}{L_1}", 
                 fr"\frac{{4 \cdot {Ec:.0f} \cdot {Is:.0f}}}{{{L1_cm}}}", f"{Ks:,.0f}", "kg-cm")
        math_row("Torsional Stiffness (Kt)", r"K_t = \sum \frac{9E_c C}{L_2(1-c_2/L_2)^3}", 
                 fr"\text{{Complex Term}}", f"{Kt:,.0f}", "kg-cm")
        math_row("Equivalent Col Stiffness (Kec)", r"\frac{1}{K_{ec}} = \frac{1}{\Sigma K_c} + \frac{1}{K_t}", 
                 fr"\text{{Series Combination}}", f"{Kec:,.0f}", "kg-cm")
        st.info(f"👉 **Distribution Factor (DF) to Slab:** {DF_slab:.4f}")

    st.header("3. Punching Shear Check (Critical)")
    st.latex(r"\phi V_c = 0.85 \cdot 1.06 \sqrt{f'_c} \cdot b_o \cdot d")
    with st.expander("Show Shear Detail", expanded=True):
        math_row("Critical Perimeter (bo)", r"b_o = 2(c_1+d) + 2(c_2+d)", 
                 fr"2({c1}+{d_eff:.1f}) + 2({c2}+{d_eff:.1f})", f"{bo:.1f}", "cm")
        math_row("Shear Strength (φVc)", r"\phi V_c", 
                 fr"0.85 \cdot 1.06 \sqrt{{{fc}}} \cdot {bo:.1f} \cdot {d_eff:.1f}", 
                 f"{PhiVc:,.0f}", "kg", shear_status)

# --- TAB 3: GEOMETRY ---
with tab3:
    st.header("Geometry Visualization")
    st.pyplot(plot_geometry_detailed(L1, L2, c1, c2, h_slab, lc, Ic))

# --- TAB 4: REPORT ---
with tab4:
    st.header("📥 Project Summary Report")
    report_text = f"""
    FLAT SLAB DESIGN REPORT
    -----------------------
    Date: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}
    
    [INPUTS]
    - Concrete (fc'): {fc} ksc
    - Steel (fy): {fy} ksc
    - Slab Thickness: {h_slab} cm (Cover {cover} cm, Bar DB{d_bar})
    - Span: {L1}m x {L2}m
    - Column: {c1}x{c2} cm
    - Load: SDL={SDL}, LL={LL} kg/m2
    
    [RESULTS]
    - Factored Load (Wu): {w_u:.2f} kg/m2
    - Slab Stiffness (Ks): {Ks:,.0f} kg-cm
    - Equiv. Col Stiffness (Kec): {Kec:,.0f} kg-cm
    - DF Slab: {DF_slab:.4f}
    
    [SAFETY CHECKS]
    - Punching Shear: {shear_status} (Demand: {Vu:,.0f} kg / Cap: {PhiVc:,.0f} kg)
    - Min Thickness: {thick_status} (Req: {min_h_req:.1f} cm)
    """
    st.text_area("Copy text below:", report_text, height=300)
    st.download_button("Download Report (.txt)", report_text, "design_report.txt")
