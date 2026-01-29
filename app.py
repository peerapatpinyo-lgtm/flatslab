import streamlit as st
import numpy as np

# Import Modules
from calculations import check_punching_shear
import tab_drawings
import tab_ddm
import tab_efm

# ==========================
# 1. PAGE SETUP
# ==========================
st.set_page_config(page_title="Pro Flat Slab Design", layout="wide", page_icon="🏗️")
st.markdown("""
<style>
    .success-box { background-color: #d1e7dd; padding: 15px; border-radius: 5px; border-left: 5px solid #198754; color: #0f5132; }
    .fail-box { background-color: #f8d7da; padding: 15px; border-radius: 5px; border-left: 5px solid #dc3545; color: #842029; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ==========================
# 2. SIDEBAR INPUTS
# ==========================
st.sidebar.title("🏗️ Project Params")

with st.sidebar.expander("1. Material & Section", expanded=True):
    fc = st.number_input("f'c (ksc)", 240.0, step=10.0)
    fy = st.number_input("fy (ksc)", 4000.0, step=100.0)
    h_slab = st.number_input("Slab Thickness (cm)", 20.0, step=1.0)
    cover = st.number_input("Cover (cm)", 2.5)
    d_bar = st.selectbox("Rebar DB (mm)", [12, 16, 20, 25], index=1)

with st.sidebar.expander("2. Geometry", expanded=True):
    L1 = st.number_input("L1: Long Span (m)", 6.0)
    L2 = st.number_input("L2: Width (m)", 6.0)
    lc = st.number_input("Storey Height (m)", 3.0)
    c1_w = st.number_input("c1: Col // L1 (cm)", 40.0)
    c2_w = st.number_input("c2: Col // L2 (cm)", 40.0)

with st.sidebar.expander("3. Loads", expanded=True):
    SDL = st.number_input("SDL (kg/m²)", 150.0)
    LL = st.number_input("Live Load (kg/m²)", 300.0)

# ==========================
# 3. GLOBAL CALCULATIONS
# ==========================
# Constants
d_eff = h_slab - cover - (d_bar/20.0)
w_self = (h_slab/100)*2400
w_u = 1.2*(w_self + SDL) + 1.6*LL

# A. Safety Checks (Dashboard)
# Punching Shear
c1_d = c1_w + d_eff
c2_d = c2_w + d_eff
area_crit = (c1_d/100) * (c2_d/100)
Vu_punch = w_u * (L1*L2 - area_crit)
Vc_punch, ratio_punch, status_punch, _ = check_punching_shear(Vu_punch, fc, c1_w, c2_w, d_eff)

# Min Thickness
h_min_aci = max(L1, L2)*100 / 33.0
status_thick = "PASS" if h_slab >= h_min_aci else "WARNING"

# B. DDM Moments (Needed for both Drawing and DDM tabs)
ln = L1 - c1_w/100
Mo = (w_u * L2 * ln**2) / 8
M_neg = 0.65 * Mo
M_pos = 0.35 * Mo
moment_vals = {
    "M_cs_neg": M_neg * 0.75,
    "M_ms_neg": M_neg * 0.25,
    "M_cs_pos": M_pos * 0.60,
    "M_ms_pos": M_pos * 0.40
}

# ==========================
# 4. DASHBOARD
# ==========================
st.title("Pro Flat Slab Design System")

col_d1, col_d2, col_d3 = st.columns(3)

with col_d1: # Punching Shear
    if status_punch == "PASS":
        st.markdown(f"<div class='success-box'>✅ <b>Punching Shear: SAFE</b><br>Ratio: {ratio_punch:.2f}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='fail-box'>❌ <b>Punching Shear: FAIL</b><br>Ratio: {ratio_punch:.2f}</div>", unsafe_allow_html=True)

with col_d2: # Thickness
    if status_thick == "PASS":
        st.markdown(f"<div class='success-box'>✅ <b>Thickness: OK</b><br>Prov: {h_slab} cm > Req: {h_min_aci:.1f}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='fail-box'>⚠️ <b>Thickness: WARNING</b><br>Check Deflection!</div>", unsafe_allow_html=True)

with col_d3: # Load
    st.metric("Factored Load (Wu)", f"{w_u:,.0f} kg/m²")

st.markdown("---")

# ==========================
# 5. TABS
# ==========================
tab1, tab2, tab3 = st.tabs(["1️⃣ Drawings & Plan", "2️⃣ DDM Calculation", "3️⃣ EFM Stiffness"])

with tab1:
    tab_drawings.render(L1, L2, c1_w, c2_w, h_slab, lc, cover, d_eff, moment_vals)

with tab2:
    # --- แก้ไขจุดที่ Error ตรงนี้ครับ (เพิ่ม w_u, c1_w, ln เข้าไป) ---
    tab_ddm.render(Mo, L1, L2, h_slab, d_eff, fc, fy, d_bar, moment_vals, w_u, c1_w, ln)

with tab3:
    tab_efm.render(c1_w, c2_w, L1, L2, lc, h_slab, fc)
