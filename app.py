import streamlit as st
import numpy as np
import pandas as pd
from geometry_view import plot_geometry_detailed

# ==========================================
# 1. SETUP & STYLING
# ==========================================
st.set_page_config(page_title="Flat Slab Design: DDM vs EFM", layout="wide", page_icon="🏗️")
st.markdown("""
<style>
    .pass { color: #198754; font-weight: bold; }
    .fail { color: #dc3545; font-weight: bold; }
    .method-box { background-color: #e9ecef; padding: 15px; border-radius: 8px; border-left: 5px solid #0d6efd; }
</style>
""", unsafe_allow_html=True)

def math_row(label, formula, sub, result, unit):
    c1, c2, c3 = st.columns([2, 2, 1])
    with c1: st.markdown(f"**{label}**"); st.latex(formula)
    with c2: st.markdown(f"Substituting:"); st.latex(sub)
    with c3: st.markdown(f"**= {result} {unit}**")
    st.markdown("---")

# ==========================================
# 2. SIDEBAR INPUTS
# ==========================================
st.sidebar.header("1. Material & Section")
fc = st.sidebar.number_input("f'c (ksc)", 240.0)
fy = st.sidebar.number_input("fy (ksc)", 4000.0)
h_slab = st.sidebar.number_input("Slab Thickness (cm)", 20.0)
cover = st.sidebar.number_input("Cover (cm)", 2.5)
d_bar = st.sidebar.selectbox("Rebar DB (mm)", [12, 16, 20, 25], index=1)

st.sidebar.header("2. Geometry (Span)")
L1 = st.sidebar.number_input("L1 (Longitudinal) [m]", 6.0)
L2 = st.sidebar.number_input("L2 (Transverse) [m]", 5.0)
lc = st.sidebar.number_input("Storey Height [m]", 3.0)

st.sidebar.header("3. Columns")
c1 = st.sidebar.number_input("c1 (along L1) [cm]", 40.0)
c2 = st.sidebar.number_input("c2 (along L2) [cm]", 40.0)

st.sidebar.header("4. Loads")
SDL = st.sidebar.number_input("SDL (kg/m²)", 150.0)
LL = st.sidebar.number_input("Live Load (kg/m²)", 300.0)

# ==========================================
# 3. CALCULATIONS
# ==========================================
# Constants
d_eff = h_slab - cover - (d_bar/20.0) # approx
L1_cm, L2_cm, lc_cm = L1*100, L2*100, lc*100
Ec = 15100 * np.sqrt(fc)

# Loads
w_dead = (h_slab/100)*2400 + SDL
w_u = 1.2*w_dead + 1.6*LL

# --- METHOD CHECK: DDM Limitations (ACI 318) ---
limit_ratio = max(L1, L2) / min(L1, L2)
limit_load = LL / w_dead
is_3_spans = True # Assume user has 3 spans for calculation context (Common limitation)

check_1 = limit_ratio <= 2.0
check_2 = limit_load <= 2.0
# Note: ACI also requires min 3 spans, successive span diff < 1/3, etc. 
# We focus on the two most critical checks for single panel input.

can_use_ddm = check_1 and check_2

# --- METHOD 1: DDM Calculations ---
ln = L1 - c1/100 # Clear span
Mo = (w_u * L2 * ln**2) / 8 # Static Moment

# --- METHOD 2: EFM Stiffness Calculations ---
Is = (L2_cm * h_slab**3)/12
Ic = (c2 * c1**3)/12
Ks = 4*Ec*Is/L1_cm
Kc = 4*Ec*Ic/lc_cm

x, y = min(c1, h_slab), max(c1, h_slab)
C_tor = (1 - 0.63*(x/y)) * (x**3 * y)/3
Kt = 2 * (9*Ec*C_tor) / (L2_cm * (1 - c2/L2_cm)**3)
sum_kc = 2*Kc
Kec = 1 / (1/sum_kc + 1/Kt) if (sum_kc > 0 and Kt > 0) else 0
DF_slab = Ks/(Ks+Kec) if (Ks+Kec) > 0 else 0

# --- SAFETY CHECKS (Punching) ---
c1_d, c2_d = c1+d_eff, c2+d_eff
bo = 2*(c1_d + c2_d)
Vu = w_u * (L1*L2 - (c1_d/100)*(c2_d/100))
PhiVc = 0.85 * 1.06 * np.sqrt(fc) * bo * d_eff
shear_pass = PhiVc >= Vu

# ==========================================
# 4. MAIN DISPLAY
# ==========================================
st.title("🏗️ Flat Slab Design: DDM vs EFM Analysis")

tab_select, tab_ddm, tab_efm, tab_geo = st.tabs([
    "🔍 Method Selection", 
    "1️⃣ Method 1: DDM (Direct Design)", 
    "2️⃣ Method 2: EFM (Equiv. Frame)", 
    "📐 Geometry"
])

# --- TAB 1: METHOD SELECTION ---
with tab_select:
    st.header("Check ACI 318 Limitations")
    st.markdown("การจะใช้วิธี **Direct Design Method (DDM)** ต้องผ่านเงื่อนไขตามมาตรฐาน ดังนี้:")
    
    col_chk1, col_chk2 = st.columns(2)
    with col_chk1:
        st.markdown("**Check 1: Rectangular Ratio**")
        st.latex(r"\frac{L_{long}}{L_{short}} \le 2.0")
        res_1 = f"{limit_ratio:.2f}"
        if check_1:
            st.success(f"✅ Pass (Ratio = {res_1})")
        else:
            st.error(f"❌ Fail (Ratio = {res_1} > 2.0)")
            
    with col_chk2:
        st.markdown("**Check 2: Load Ratio**")
        st.latex(r"\frac{Live Load}{Unfactored Dead Load} \le 2.0")
        res_2 = f"{limit_load:.2f}"
        if check_2:
            st.success(f"✅ Pass (Ratio = {res_2})")
        else:
            st.error(f"❌ Fail (Ratio = {res_2} > 2.0)")

    st.markdown("---")
    if can_use_ddm:
        st.success("🎉 **Conclusion:** คุณสามารถใช้ **Direct Design Method (DDM)** ได้ (หรือจะใช้ EFM ก็ได้)")
        st.info("👉 ไปที่ Tab **Method 1: DDM** เพื่อดูค่าโมเมนต์")
    else:
        st.error("🚫 **Conclusion:** ไม่ผ่านเงื่อนไข DDM! ต้องใช้วิธี **Equivalent Frame Method (EFM)** เท่านั้น")
        st.warning("👉 ไปที่ Tab **Method 2: EFM** เพื่อดูค่า Stiffness สำหรับการวิเคราะห์โครงสร้าง")

    # Safety Check Summary (Always Show)
    st.subheader("🛡️ Safety Check (Punching Shear)")
    p_col1, p_col2 = st.columns(2)
    p_col1.metric("Shear Demand (Vu)", f"{Vu:,.0f} kg")
    p_col2.metric("Shear Capacity (φVc)", f"{PhiVc:,.0f} kg", 
                  delta="SAFE" if shear_pass else "FAIL", delta_color="normal" if shear_pass else "inverse")

# --- TAB 2: DDM (Direct Design Method) ---
with tab_ddm:
    if not can_use_ddm:
        st.error("⚠️ วิธีนี้ไม่แนะนำให้ใช้ เนื่องจากไม่ผ่านเงื่อนไข ACI (ดู Tab แรก)")
    
    st.header("Method 1: Direct Design Method (DDM)")
    st.markdown("เหมาะสำหรับพื้นที่มีช่วงเสาสม่ำเสมอ คำนวณหา **Total Static Moment ($M_0$)** แล้วกระจายเข้าแถบเสา/แถบกลาง")

    math_row("Total Static Moment (Mo)", 
             r"M_o = \frac{w_u L_2 l_n^2}{8}", 
             fr"\frac{{{w_u:.1f} \cdot {L2} \cdot {ln:.2f}^2}}{{8}}", 
             f"{Mo:,.2f}", "kg-m")

    st.subheader("Moment Distribution (Interior Span)")
    
    # Coefficients for Interior Span (Flat Plate)
    # Total Negative = 0.65 Mo
    # Total Positive = 0.35 Mo
    # Column Strip gets 75% of Neg, 60% of Pos
    neg_total = Mo * 0.65
    pos_total = Mo * 0.35
    
    col_neg = neg_total * 0.75
    mid_neg = neg_total * 0.25
    col_pos = pos_total * 0.60
    mid_pos = pos_total * 0.40

    df_moments = pd.DataFrame({
        "Location": ["Negative Moment (-)", "Negative Moment (-)", "Positive Moment (+)", "Positive Moment (+)"],
        "Strip": ["Column Strip (75%)", "Middle Strip (25%)", "Column Strip (60%)", "Middle Strip (40%)"],
        "Formula": ["0.65 x 0.75 x Mo", "0.65 x 0.25 x Mo", "0.35 x 0.60 x Mo", "0.35 x 0.40 x Mo"],
        "Design Moment (kg-m)": [col_neg, mid_neg, col_pos, mid_pos]
    })
    st.table(df_moments.style.format({"Design Moment (kg-m)": "{:,.2f}"}))

# --- TAB 3: EFM (Equivalent Frame Method) ---
with tab_efm:
    st.header("Method 2: Equivalent Frame Method (EFM)")
    st.markdown("""
    วิธีนี้ใช้ได้ **ทุกกรณี** (แม้ไม่ผ่านเงื่อนไข DDM) โดยหลักการคือแปลงพื้นและเสาให้เป็นโครงข้อแข็ง (Frame)
    ที่มีค่า Stiffness ($K$) และกระจายโมเมนต์ด้วยวิธี Matrix หรือ Moment Distribution
    """)

    st.info("ในที่นี้จะคำนวณค่า **Stiffness Parameters** ที่จำเป็นต้องใช้ในการวิเคราะห์โครงสร้าง:")

    with st.expander("1. Slab Stiffness (Ks)", expanded=True):
        math_row("Inertia (Is)", r"I_s = \frac{L_2 h^3}{12}", "", f"{Is:,.0f}", "cm⁴")
        math_row("Stiffness (Ks)", r"K_s = \frac{4 E_c I_s}{L_1}", "", f"{Ks:,.0f}", "kg-cm")

    with st.expander("2. Column Stiffness (Kc)", expanded=True):
        math_row("Inertia (Ic)", r"I_c = \frac{c_2 c_1^3}{12}", "", f"{Ic:,.0f}", "cm⁴")
        math_row("Stiffness (Kc)", r"K_c = \frac{4 E_c I_c}{l_c}", "", f"{Kc:,.0f}", "kg-cm")

    with st.expander("3. Equivalent Column (Kec) - *Includes Torsion*", expanded=True):
        st.write("ผลของ Torsional Member ทำให้เสาอ่อนลง (K ลดลง)")
        math_row("Torsional Stiffness (Kt)", r"K_t = \sum \frac{9 E_c C}{L_2 (1-c_2/L_2)^3}", "", f"{Kt:,.0f}", "kg-cm")
        math_row("Equiv. Stiffness (Kec)", r"\frac{1}{K_{ec}} = \frac{1}{\Sigma K_c} + \frac{1}{K_t}", "", f"{Kec:,.0f}", "kg-cm")

    st.success(f"👉 **สรุปค่าสำหรับใส่โปรแกรมวิเคราะห์:**\n- Slab Stiffness: **{Ks:,.0f}**\n- Equivalent Column Stiffness: **{Kec:,.0f}**")

# --- TAB 4: GEOMETRY ---
with tab_geo:
    st.pyplot(plot_geometry_detailed(L1, L2, c1, c2, h_slab, lc, Ic))
