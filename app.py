import streamlit as st
import numpy as np
import pandas as pd
# ---------------------------------------------------------
# IMPORT ฟังก์ชันวาดรูปจากไฟล์ geometry_view.py
# ---------------------------------------------------------
from geometry_view import plot_geometry_detailed 

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================
st.set_page_config(page_title="Advanced Flat Slab Design", layout="wide")

# Custom CSS
st.markdown("""
<style>
    .stMetric { background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 5px; }
</style>
""", unsafe_allow_html=True)

# Helper Function
def show_step(title, latex_eq, sub_eq, result, unit, note=None):
    st.markdown(f"#### {title}")
    if note: st.caption(f"ℹ️ *{note}*")
    st.latex(latex_eq)
    c1, c2 = st.columns([3, 1])
    c1.markdown("**Substitution:**"); c1.latex(sub_eq)
    c2.markdown("**Result:**"); c2.metric(unit, result)
    st.markdown("---")

# ==========================================
# 2. SIDEBAR INPUTS
# ==========================================
st.sidebar.title("🛠️ Parameters")
with st.sidebar.expander("1. Material", expanded=True):
    fc = st.number_input("f'c (ksc)", value=240.0)
    fy = st.number_input("fy (ksc)", value=4000.0)

with st.sidebar.expander("2. Geometry", expanded=True):
    L1 = st.number_input("L1 (Span) [m]", value=6.0)
    L2 = st.number_input("L2 (Width) [m]", value=5.0)
    h_slab = st.number_input("h (Slab Thickness) [cm]", value=20.0)
    l_c = st.number_input("lc (Storey Height) [m]", value=3.0)

with st.sidebar.expander("3. Columns", expanded=True):
    c1 = st.number_input("c1 (Parallel L1) [cm]", value=40.0)
    c2 = st.number_input("c2 (Transverse) [cm]", value=40.0)

with st.sidebar.expander("4. Loads", expanded=True):
    SDL = st.number_input("SDL [kg/m²]", value=100.0)
    LL = st.number_input("Live Load [kg/m²]", value=300.0)

# ==========================================
# 3. CALCULATIONS (Engine)
# ==========================================
L1_cm, L2_cm, lc_cm = L1*100, L2*100, l_c*100
Ec = 15100 * np.sqrt(fc)

# Loads
w_self = (h_slab/100) * 2400
w_u = 1.2 * (w_self + SDL) + 1.6 * LL

# Stiffness
Is = (L2_cm * h_slab**3) / 12
Ks = (4 * Ec * Is) / L1_cm
Ic = (c2 * c1**3) / 12  
Kc = (4 * Ec * Ic) / lc_cm

# Torsion
x, y = min(c1, h_slab), max(c1, h_slab)
C = (1 - 0.63*(x/y)) * (x**3 * y) / 3
Kt = 2 * (9 * Ec * C) / (L2_cm * (1 - c2/L2_cm)**3)

# Equivalent & DF
Kec = 1 / (1/(2*Kc) + 1/Kt)
DF_slab = Ks / (Ks + Kec)

# DDM Moment
ln = L1 - c1/100
Mo = (w_u * L2 * ln**2) / 8

# ==========================================
# 4. MAIN LAYOUT
# ==========================================
st.title("🏗️ Flat Slab Analyzer: DDM & EFM")

tab_calc, tab_view = st.tabs(["📝 Calculation Details", "📐 Geometry Visualization"])

# --- TAB 1: Calculation ---
with tab_calc:
    st.header("1. Load & Stiffness Summary")
    c1_ui, c2_ui, c3_ui = st.columns(3)
    c1_ui.metric("Factored Load (Wu)", f"{w_u:.1f} kg/m²")
    c2_ui.metric("Slab Stiffness (Ks)", f"{Ks:,.0f} kg-cm")
    c3_ui.metric("Col. Stiffness (Kc)", f"{Kc:,.0f} kg-cm")

    st.header("2. Detailed Steps")
    with st.expander("Show Detailed EFM Calculation", expanded=True):
        show_step("Column Inertia (Ic)", r"I_c = \frac{c_2 c_1^3}{12}", 
                 fr"I_c = \frac{{{c2:.0f} \cdot {c1:.0f}^3}}{{12}}", f"{Ic:,.2f}", "cm⁴")
        show_step("Equivalent Stiffness (Kec)", r"\frac{1}{K_{ec}} = \frac{1}{\Sigma K_c} + \frac{1}{K_t}", 
                 fr"K_{{ec}} (Calculated)", f"{Kec:,.2f}", "kg-cm")

    st.header("3. Design Moments (DDM)")
    df_m = pd.DataFrame({
        "Zone": ["Col Strip (-)", "Mid Strip (-)", "Col Strip (+)", "Mid Strip (+)"],
        "Moment (kg-m)": [Mo*0.65*0.75, Mo*0.65*0.25, Mo*0.35*0.60, Mo*0.35*0.40]
    })
    st.table(df_m)

# --- TAB 2: Visualization ---
with tab_view:
    st.header("Geometry & Structural Parameters")
    st.markdown("แสดงค่าตัวแปร $h, I_c, L_1, L_2, c_1, c_2$ ในตำแหน่งจริง")
    
    # เรียกใช้ฟังก์ชันจากไฟล์ geometry_view.py
    fig = plot_geometry_detailed(L1, L2, c1, c2, h_slab, l_c, Ic)
    
    st.pyplot(fig)
    st.success("✅ **Tip:** ลองปรับค่า h หรือ L1 ใน Sidebar แล้วกดดูรูปใหม่ กราฟิกจะขยับตามทันที")
