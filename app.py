import streamlit as st
import numpy as np

# Import Modules
from calculations import check_punching_shear
import tab_drawings
import tab_ddm
import tab_efm

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
# INPUTS: GLOBAL GEOMETRY
# ==========================
st.sidebar.title("🏗️ Project Params")

with st.sidebar.expander("1. Material & Section", expanded=True):
    fc = st.number_input("f'c (ksc)", 240.0, step=10.0)
    fy = st.number_input("fy (ksc)", 4000.0, step=100.0)
    h_slab = st.number_input("Slab Thickness (cm)", 20.0, step=1.0)
    cover = st.number_input("Cover (cm)", 2.5)
    d_bar = st.selectbox("Rebar DB (mm)", [12, 16, 20, 25], index=1)

with st.sidebar.expander("2. Geometry (Plan View)", expanded=True):
    st.info("ระบุขนาดจริงตามแกน X และ Y")
    Lx = st.number_input("Lx: Span along X (m)", 8.0)
    Ly = st.number_input("Ly: Span along Y (m)", 6.0)
    lc = st.number_input("Storey Height (m)", 3.0)
    
    st.write("--- Column Size ---")
    cx = st.number_input("cx: Dimension // X (cm)", 40.0)
    cy = st.number_input("cy: Dimension // Y (cm)", 60.0)

with st.sidebar.expander("3. Loads", expanded=True):
    SDL = st.number_input("SDL (kg/m²)", 150.0)
    LL = st.number_input("Live Load (kg/m²)", 300.0)

# ==========================
# CALCULATION LOGIC (DUAL AXIS)
# ==========================
# Constants
d_eff = h_slab - cover - (d_bar/20.0)
w_self = (h_slab/100)*2400
w_u = 1.2*(w_self + SDL) + 1.6*LL

# --- Direction X Calculation ---
# Design Span = Lx, Width = Ly, Col Parallel = cx
ln_x = Lx - cx/100
Mo_x = (w_u * Ly * ln_x**2) / 8

# Moment Distribution (ACI Direct Design Method)
# 
M_vals_x = {
    "M_cs_neg": 0.65 * Mo_x * 0.75, "M_ms_neg": 0.65 * Mo_x * 0.25,
    "M_cs_pos": 0.35 * Mo_x * 0.60, "M_ms_pos": 0.35 * Mo_x * 0.40
}

# --- Direction Y Calculation ---
# Design Span = Ly, Width = Lx, Col Parallel = cy
ln_y = Ly - cy/100
Mo_y = (w_u * Lx * ln_y**2) / 8
M_vals_y = {
    "M_cs_neg": 0.65 * Mo_y * 0.75, "M_ms_neg": 0.65 * Mo_y * 0.25,
    "M_cs_pos": 0.35 * Mo_y * 0.60, "M_ms_pos": 0.35 * Mo_y * 0.40
}

# Punching Shear Check
# 
c1_d = cx + d_eff
c2_d = cy + d_eff
area_crit = (c1_d/100) * (c2_d/100)
Vu_punch = w_u * (Lx*Ly - area_crit)
Vc_punch, ratio_punch, status_punch, _ = check_punching_shear(Vu_punch, fc, cx, cy, d_eff)

# ==========================
# DASHBOARD & TABS
# ==========================
st.title("Pro Flat Slab Design System (Dual-Axis)")

# Dashboard (Punching Shear is mostly independent of direction)
col_d1, col_d2, col_d3 = st.columns(3)
with col_d1:
    if status_punch == "PASS":
        st.markdown(f"<div class='success-box'>✅ <b>Punching: SAFE</b><br>Ratio: {ratio_punch:.2f}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='fail-box'>❌ <b>Punching: FAIL</b><br>Ratio: {ratio_punch:.2f}</div>", unsafe_allow_html=True)
with col_d2:
    h_min = max(Lx, Ly)*100 / 33.0
    status_h = "OK" if h_slab >= h_min else "CHECK"
    st.info(f"Min Thick (ACI): {h_min:.1f} cm")
with col_d3:
    st.metric("Factored Load (Wu)", f"{w_u:,.0f} kg/m²")

st.markdown("---")

tab1, tab2, tab3 = st.tabs(["1️⃣ Drawings", "2️⃣ DDM Calculation (X & Y)", "3️⃣ EFM Stiffness"])

with tab1:
    # Use X geometry for drawing (Generic)
    tab_drawings.render(Lx, Ly, cx, cy, h_slab, lc, cover, d_eff, M_vals_x)

with tab2:
    # Send BOTH X and Y data to Tab 2
    data_x = {"L_span": Lx, "L_width": Ly, "c_para": cx, "ln": ln_x, "Mo": Mo_x, "M_vals": M_vals_x, "dir": "X-Direction"}
    data_y = {"L_span": Ly, "L_width": Lx, "c_para": cy, "ln": ln_y, "Mo": Mo_y, "M_vals": M_vals_y, "dir": "Y-Direction"}
    
    tab_ddm.render_dual(data_x, data_y, h_slab, d_eff, fc, fy, d_bar, w_u)

with tab3:
    tab_efm.render(cx, cy, Lx, Ly, lc, h_slab, fc)
