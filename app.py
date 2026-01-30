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
# 1. INPUTS: GLOBAL PARAMETERS
# ==========================
st.sidebar.title("🏗️ Project Params")

# --- Group 1: Material ---
with st.sidebar.expander("1. Material & Properties", expanded=True):
    fc = st.number_input("f'c (ksc)", 240.0, step=10.0)
    fy = st.number_input("fy (ksc)", 4000.0, step=100.0)
    h_slab = st.number_input("Slab Thickness (cm)", 20.0, step=1.0)
    cover = st.number_input("Cover (cm)", 2.5)
    d_bar = st.selectbox("Rebar DB (mm)", [12, 16, 20, 25], index=0)

# --- Group 2: Geometry ---
with st.sidebar.expander("2. Geometry & Drop Panel", expanded=True):
    st.info("Span Distance (Center-to-Center)")
    col1, col2 = st.columns(2)
    with col1:
        Lx = st.number_input("Lx (m)", 8.0)
        cx = st.number_input("Col X (cm)", 40.0)
    with col2:
        Ly = st.number_input("Ly (m)", 6.0)
        cy = st.number_input("Col Y (cm)", 40.0)
    
    lc = st.number_input("Storey Height (m)", 3.0)
    
    # Drop Panel Inputs
    has_drop = st.checkbox("Has Drop Panel?")
    h_drop = 0.0
    if has_drop:
        h_drop = st.number_input("Drop Thickness (cm) - (Add to slab)", 10.0)
        st.caption(f"Total Thickness at Col = {h_slab + h_drop:.0f} cm")

# --- Group 3: Loads ---
with st.sidebar.expander("3. Loads", expanded=True):
    SDL = st.number_input("SDL (kg/m²)", 150.0)
    LL = st.number_input("Live Load (kg/m²)", 300.0)

# ==========================
# 2. DATA PACKAGING (DICTIONARIES)
# ==========================
# Organize data to pass to modules cleanly
mat_props = {
    "fc": fc, "fy": fy, "h_slab": h_slab, "cover": cover, 
    "d_bar": d_bar, "h_drop": h_drop
}

geom_props = {
    "Lx": Lx, "Ly": Ly, "cx": cx, "cy": cy, "lc": lc
}

# Load Calculation
w_self = (h_slab/100)*2400
w_u = 1.2*(w_self + SDL) + 1.6*LL

# Effective Depth
# General Slab
d_eff_slab = h_slab - cover - (d_bar/20.0)
# At Column (for Punching)
d_eff_punch = (h_slab + h_drop) - cover - (d_bar/20.0)

# ==========================
# 3. ANALYSIS LOGIC
# ==========================

# --- Moment Calculation (DDM) ---
# X-Direction
ln_x = Lx - cx/100
Mo_x = (w_u * Ly * ln_x**2) / 8
M_vals_x = {
    "M_cs_neg": 0.65 * Mo_x * 0.75, "M_ms_neg": 0.65 * Mo_x * 0.25,
    "M_cs_pos": 0.35 * Mo_x * 0.60, "M_ms_pos": 0.35 * Mo_x * 0.40
}

# Y-Direction
ln_y = Ly - cy/100
Mo_y = (w_u * Lx * ln_y**2) / 8
M_vals_y = {
    "M_cs_neg": 0.65 * Mo_y * 0.75, "M_ms_neg": 0.65 * Mo_y * 0.25,
    "M_cs_pos": 0.35 * Mo_y * 0.60, "M_ms_pos": 0.35 * Mo_y * 0.40
}

# --- Punching Shear Check ---
c1_d = cx + d_eff_punch
c2_d = cy + d_eff_punch
area_crit = (c1_d/100) * (c2_d/100)
Vu_punch = w_u * (Lx*Ly - area_crit)

# Call updated function (Cycle 1 logic)
Vc_punch, ratio_punch, status_punch, bo_punch = check_punching_shear(Vu_punch, fc, cx, cy, d_eff_punch)

# ==========================
# 4. DASHBOARD & TABS
# ==========================
st.title("Pro Flat Slab Design System (Dual-Axis)")

# Top Dashboard
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
    # Use generic generic arguments for now (we haven't updated drawing tab yet)
    tab_drawings.render(Lx, Ly, cx, cy, h_slab, lc, cover, d_eff_slab, M_vals_x)

with tab2:
    # Prepare Data Packs for DDM Tab
    data_x = {
        "axis": "X-Axis", "L_span": Lx, "L_width": Ly, "c_para": cx, 
        "ln": ln_x, "Mo": Mo_x, "M_vals": M_vals_x
    }
    data_y = {
        "axis": "Y-Axis", "L_span": Ly, "L_width": Lx, "c_para": cy, 
        "ln": ln_y, "Mo": Mo_y, "M_vals": M_vals_y
    }
    
    # Send clean dictionaries to the new Tab 2
    tab_ddm.render_dual(data_x, data_y, mat_props, w_u)

with tab3:
    # Pass individual args for EFM (haven't updated EFM tab yet)
    tab_efm.render(cx, cy, Lx, Ly, lc, h_slab, fc)
