# app.py (Fixed Import)
import streamlit as st
import numpy as np

# Import Modules (Fixed Name Here)
from calculations import check_punching_shear, design_rebar_detailed
import tab_drawings
import tab_ddm
import tab_efm

st.set_page_config(page_title="Pro Flat Slab Design", layout="wide", page_icon="🏗️")

# CSS Styles
st.markdown("""
<style>
    .metric-card { background-color: #f0f2f6; padding: 15px; border-radius: 8px; text-align: center; }
    .success-box { background-color: #d1e7dd; padding: 10px; border-radius: 5px; color: #0f5132; border-left: 5px solid #198754; }
    .fail-box { background-color: #f8d7da; padding: 10px; border-radius: 5px; color: #842029; border-left: 5px solid #dc3545; }
</style>
""", unsafe_allow_html=True)

# ==========================
# 1. INPUTS
# ==========================
st.sidebar.header("🏗️ Project Parameters")

with st.sidebar.expander("Material Properties", expanded=True):
    fc = st.number_input("f'c (ksc)", value=240.0, step=10.0)
    fy = st.number_input("fy (ksc)", value=4000.0, step=100.0)
    
with st.sidebar.expander("Geometry (Slab & Column)", expanded=True):
    h_slab_cm = st.number_input("Slab Thickness (cm)", value=20.0)
    cover_cm = st.number_input("Concrete Cover (cm)", value=2.5)
    
    col1, col2 = st.columns(2)
    Lx = col1.number_input("Span Lx (m)", value=8.0)
    Ly = col2.number_input("Span Ly (m)", value=6.0)
    
    col3, col4 = st.columns(2)
    cx_cm = col3.number_input("Col X (cm)", value=40.0)
    cy_cm = col4.number_input("Col Y (cm)", value=60.0)
    
    lc = st.number_input("Column Height (m)", value=3.0)

with st.sidebar.expander("Loads", expanded=True):
    SDL = st.number_input("Superimposed DL (kg/m²)", value=150.0)
    LL = st.number_input("Live Load (kg/m²)", value=300.0)

# ==========================
# 2. PRE-CALCULATION (UNIT CONVERSION)
# ==========================
h = h_slab_cm / 100.0
cx = cx_cm / 100.0
cy = cy_cm / 100.0
cover = cover_cm / 100.0

# Effective Depth (Average for Punching)
db_est = 0.020 
d_avg = h - cover - db_est

# Loads
w_self = h * 2400
wu = 1.2*(w_self + SDL) + 1.6*LL

# ==========================
# 3. CORE LOGIC
# ==========================

# --- Punching Shear ---
b1 = cx + d_avg 
b2 = cy + d_avg 
Area_crit = b1 * b2

Vu = wu * (Lx * Ly - Area_crit) 

# เรียกฟังก์ชัน (สังเกตหน่วยที่ส่งไป: Vu=kg, cx=cm, cy=cm, d=cm)
punching_res = check_punching_shear(Vu, fc, cx_cm, cy_cm, d_avg*100) 

# ==========================
# 4. DASHBOARD
# ==========================
st.title("Pro Flat Slab Design System")

m1, m2, m3, m4 = st.columns(4)
m1.metric("Factored Load (Wu)", f"{wu:,.0f} kg/m²")
m2.metric("Total Load on Col", f"{Vu/1000:,.1f} tons")
m3.metric("Effective d (avg)", f"{d_avg*100:.1f} cm")

with m4:
    if punching_res[2] == "PASS":
        st.markdown(f"<div class='success-box'>✅ Punching OK<br>Ratio: {punching_res[1]:.2f}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='fail-box'>❌ Punching FAIL<br>Ratio: {punching_res[1]:.2f}</div>", unsafe_allow_html=True)

st.divider()

# Tabs
tab1, tab2, tab3 = st.tabs(["📊 1. Analysis (DDM)", "✏️ 2. Detailing & Drawings", "🧮 3. Advanced (EFM)"])

with tab1:
    project_data = {
        "Lx": Lx, "Ly": Ly, "cx": cx, "cy": cy,
        "wu": wu, "fc": fc, "fy": fy, 
        "h": h, "d_avg": d_avg
    }
    # เรียก Tab DDM
    tab_ddm.render_dual(project_data) 

with tab2:
    # เรียก Tab Drawings
    tab_drawings.render(Lx, Ly, cx_cm, cy_cm, h_slab_cm)

with tab3:
    # เรียก Tab EFM
    tab_efm.render(cx, cy, Lx, Ly, lc, h, fc)
