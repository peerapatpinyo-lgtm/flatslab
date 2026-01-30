#app.py
import streamlit as st
import numpy as np

# Import Modules
from calculations import check_punching_shear, check_punching_dual_case
import tab_ddm  # The interactive one
import tab_drawings # Placeholder
import tab_efm      # Placeholder

st.set_page_config(page_title="Pro Flat Slab Design", layout="wide", page_icon="🏗️")

# Custom CSS for Dashboard
st.markdown("""
<style>
    .success-box { background-color: #d1e7dd; padding: 15px; border-radius: 5px; border-left: 5px solid #198754; color: #0f5132; }
    .fail-box { background-color: #f8d7da; padding: 15px; border-radius: 5px; border-left: 5px solid #dc3545; color: #842029; }
    div[data-testid="stMetricValue"] { font-size: 1.2rem; }
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
    
    # Column Location for Punching Shear calculation
    col_type = st.selectbox("Column Location", ["interior", "edge", "corner"], help="Select column position for Alpha_s parameter")
    
    # Drop Panel Inputs
    st.markdown("---")
    has_drop = st.checkbox("Has Drop Panel? (เพิ่มแป้นหัวเสา)")
    
    # Init variables
    h_drop, drop_w, drop_l = 0.0, 0.0, 0.0
    
    if has_drop:
        h_drop = st.number_input("Drop Thickness (cm)", 10.0, help="ความหนาที่เพิ่มขึ้นมา (ไม่รวมพื้น)")
        st.caption(f"ℹ️ Total Thickness at Column = {h_slab:.0f} + {h_drop:.0f} = **{h_slab+h_drop:.0f} cm**")
        
        c_d1, c_d2 = st.columns(2)
        drop_w = c_d1.number_input("Drop Width X (cm)", 250.0, help="Dimension parallel to Lx")
        drop_l = c_d2.number_input("Drop Length Y (cm)", 200.0, help="Dimension parallel to Ly")

# --- Group 3: Loads ---
with st.sidebar.expander("3. Loads", expanded=True):
    SDL = st.number_input("SDL (kg/m²)", 150.0)
    LL = st.number_input("Live Load (kg/m²)", 300.0)

# ==========================
# 2. DATA PACKAGING
# ==========================
# Bundle materials to pass to other files easily
mat_props = {
    "fc": fc, "fy": fy, "h_slab": h_slab, "cover": cover, 
    "d_bar": d_bar, "h_drop": h_drop
}

# Load Calculation
w_self = (h_slab/100)*2400
w_u = 1.2*(w_self + SDL) + 1.6*LL

# Effective Depth Calculation
# 1. For Mid-Span (Flexure) & Outer Punching Check -> Slab only
d_eff_slab = h_slab - cover - (d_bar/20.0)
# 2. For Inner Punching Check -> Slab + Drop Panel
d_eff_total = (h_slab + h_drop) - cover - (d_bar/20.0)

# ==========================
# 3. ANALYSIS LOGIC
# ==========================

# --- Moment Calculation (DDM) ---
ln_x = Lx - cx/100
Mo_x = (w_u * Ly * ln_x**2) / 8
M_vals_x = {
    "M_cs_neg": 0.65 * Mo_x * 0.75, "M_ms_neg": 0.65 * Mo_x * 0.25,
    "M_cs_pos": 0.35 * Mo_x * 0.60, "M_ms_pos": 0.35 * Mo_x * 0.40
}

ln_y = Ly - cy/100
Mo_y = (w_u * Lx * ln_y**2) / 8
M_vals_y = {
    "M_cs_neg": 0.65 * Mo_y * 0.75, "M_ms_neg": 0.65 * Mo_y * 0.25,
    "M_cs_pos": 0.35 * Mo_y * 0.60, "M_ms_pos": 0.35 * Mo_y * 0.40
}

# --- Punching Shear Check (SMART SWITCH) ---
if has_drop:
    # Use the new DUAL CHECK logic
    punch_res = check_punching_dual_case(
        w_u, Lx, Ly, fc, cx, cy, 
        d_eff_total, d_eff_slab, 
        drop_w, drop_l, col_type
    )
else:
    # Use the LEGACY SINGLE CHECK logic
    # Need to calculate Vu manually for this function
    c1_d = cx + d_eff_total
    c2_d = cy + d_eff_total
    area_crit = (c1_d/100) * (c2_d/100)
    Vu_punch = w_u * (Lx*Ly - area_crit)
    
    punch_res = check_punching_shear(Vu_punch, fc, cx, cy, d_eff_total, col_type=col_type)

# ==========================
# 4. DASHBOARD & DISPLAY
# ==========================
st.title("Pro Flat Slab Design System (Dual-Axis)")

# --- Top Dashboard ---
col_d1, col_d2, col_d3 = st.columns(3)
with col_d1:
    if punch_res['status'] == "PASS":
        st.markdown(f"<div class='success-box'>✅ <b>Punching: SAFE</b><br>Ratio: {punch_res['ratio']:.2f}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='fail-box'>❌ <b>Punching: FAIL</b><br>Ratio: {punch_res['ratio']:.2f}</div>", unsafe_allow_html=True)

with col_d2:
    h_min = max(Lx, Ly)*100 / 33.0
    status_h = "OK" if h_slab >= h_min else "CHECK"
    st.info(f"Min Thick (ACI L/33): {h_min:.1f} cm (Current: {h_slab:.0f} cm)")

with col_d3:
    st.metric("Factored Load (Wu)", f"{w_u:,.0f} kg/m²")

# --- 🔎 DETAILED CALCULATION EXPANDER ---
with st.expander("🔎 View Punching Shear Calculation Details (รายการคำนวณ)", expanded=False):
    st.markdown("#### รายการคำนวณแรงเฉือนทะลุ (Punching Shear Calculation)")
    
    # Display logic depends on whether it's Dual or Single check
    is_dual = punch_res.get('is_dual', False)
    
    if is_dual:
        st.warning(f"⚠️ **Drop Panel System Detected:** Performing 2-step check.")
        st.markdown(f"**Governing Case:** {punch_res['note']}")
        
        # Comparison Table
        res1 = punch_res['check_1']
        res2 = punch_res['check_2']
        
        comp_data = {
            "Check Location": ["1. Inner (Column Face)", "2. Outer (Drop Edge)"],
            "d (cm)": [f"{res1['d']:.2f}", f"{res2['d']:.2f}"],
            "b0 (cm)": [f"{res1['b0']:.2f}", f"{res2['b0']:.2f}"],
            "Vu (kg)": [f"{res1['Vu']:,.0f}", f"{res2['Vu']:,.0f}"],
            "phi Vc (kg)": [f"{res1['Vc_design']:,.0f}", f"{res2['Vc_design']:,.0f}"],
            "Ratio": [f"{res1['ratio']:.2f}", f"{res2['ratio']:.2f}"],
            "Status": [res1['status'], res2['status']]
        }
        st.table(comp_data)
        
    else:
        st.info("ℹ️ Single Check (No Drop Panel or Flat Plate)")

    # Show Details of the GOVERNING case
    st.markdown("---")
    st.markdown("### 📝 Detailed Check for Governing Case")
    
    c1, c2 = st.columns([1, 1.2])
    with c1:
        st.markdown("**Design Parameters**")
        st.write(f"- $b_o$: **{punch_res['b0']:.2f} cm**")
        st.write(f"- $d$: **{punch_res['d']:.2f} cm**")
        st.write(f"- $\\alpha_s$: **{punch_res['alpha_s']}** ({col_type})")
        
    with c2:
        st.markdown("**Forces**")
        st.latex(f"V_u = \\mathbf{{{punch_res['Vu']:,.0f}}} \\text{{ kg}}")
        st.latex(f"\\phi V_c = \\mathbf{{{punch_res['Vc_design']:,.0f}}} \\text{{ kg}}")

    st.markdown("**ACI 318 Strength Equations (ksc units):**")
    col_eq1, col_eq2, col_eq3 = st.columns(3)
    with col_eq1:
        st.markdown("Eq. 1 (Aspect)")
        st.latex(f"V_{{c1}} = {punch_res['Vc1']:,.0f}")
    with col_eq2:
        st.markdown(f"Eq. 2 (Alpha)")
        st.latex(f"V_{{c2}} = {punch_res['Vc2']:,.0f}") 
    with col_eq3:
        st.markdown("Eq. 3 (Basic)")
        st.latex(f"V_{{c3}} = {punch_res['Vc3']:,.0f}")
        
    st.caption(f"*Governing Vc is min(Vc1, Vc2, Vc3)*")

st.markdown("---")

# ==========================
# 5. TABS
# ==========================
tab1, tab2, tab3 = st.tabs(["1️⃣ Drawings", "2️⃣ DDM Calculation (Interactive)", "3️⃣ EFM Stiffness"])

with tab1:
    try:
        # Update plotting if Drop Panel exists (Optional future improvement: visualize drop panel)
        tab_drawings.render(L1=Lx, L2=Ly, c1_w=cx, c2_w=cy, h_slab=h_slab, lc=lc, cover=cover, d_eff=d_eff_slab, moment_vals=M_vals_x)
    except Exception as e:
        st.info(f"Drawing module error: {e}")

with tab2:
    data_x = {
        "L_span": Lx, "L_width": Ly, "c_para": cx, 
        "ln": ln_x, "Mo": Mo_x, "M_vals": M_vals_x
    }
    data_y = {
        "L_span": Ly, "L_width": Lx, "c_para": cy, 
        "ln": ln_y, "Mo": Mo_y, "M_vals": M_vals_y
    }
    tab_ddm.render_dual(data_x, data_y, mat_props, w_u)

with tab3:
    try:
        tab_efm.render(c1_w=cx, c2_w=cy, L1=Lx, L2=Ly, lc=lc, h_slab=h_slab, fc=fc)
    except Exception as e:
        st.info(f"EFM module error: {e}")
