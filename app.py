# app.py
import streamlit as st
import numpy as np
import pandas as pd

# Import Modules
from calculations import check_punching_shear, check_punching_dual_case, check_oneway_shear
import tab_ddm  
import tab_drawings 
import tab_efm      

# ---------------------------------------------------------
# 1. PAGE CONFIG & WORLD-CLASS STYLING
# ---------------------------------------------------------
st.set_page_config(page_title="ProFlat: Structural Design Suite", layout="wide", page_icon="🏗️")

st.markdown("""
<style>
    /* Global Font & Theme */
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Roboto', sans-serif;
    }
    
    /* Headings */
    h1, h2, h3 { color: #0f172a; font-weight: 700; letter-spacing: -0.5px; }
    
    /* Result Cards (KPIs) */
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        text-align: center;
        transition: transform 0.2s;
    }
    .metric-card:hover { transform: translateY(-2px); }
    .metric-label { font-size: 0.85rem; color: #64748b; text-transform: uppercase; letter-spacing: 1px; font-weight: 600; }
    .metric-value { font-size: 1.8rem; font-weight: 700; color: #0f172a; margin: 5px 0; }
    .metric-status { font-size: 0.9rem; font-weight: 600; padding: 4px 12px; border-radius: 20px; display: inline-block;}
    
    .status-pass { background-color: #dcfce7; color: #166534; } /* Green */
    .status-fail { background-color: #fee2e2; color: #991b1b; } /* Red */
    .status-info { background-color: #f1f5f9; color: #334155; } /* Grey */

    /* Custom Tables */
    .stDataFrame { border: 1px solid #e2e8f0; border-radius: 5px; }
</style>
""", unsafe_allow_html=True)

# ==========================
# 2. SIDEBAR: PROJECT PARAMS
# ==========================
st.sidebar.markdown("### ⚙️ Design Parameters")

# --- Group 1: Material ---
with st.sidebar.expander("1. Material Properties", expanded=True):
    c1, c2 = st.columns(2)
    fc = c1.number_input("f'c (ksc)", 240.0, step=10.0)
    fy = c2.number_input("fy (ksc)", 4000.0, step=100.0)
    h_slab = st.number_input("Slab Thickness (cm)", 20.0, step=1.0)
    
    c3, c4 = st.columns(2)
    cover = c3.number_input("Cover (cm)", 2.5)
    d_bar = c4.selectbox("Rebar (mm)", [12, 16, 20, 25], index=0)

# --- Group 2: Geometry ---
with st.sidebar.expander("2. Geometry & Span", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        Lx = st.number_input("Span Lx (m)", 8.0)
        cx = st.number_input("Col. X (cm)", 40.0)
    with col2:
        Ly = st.number_input("Span Ly (m)", 6.0)
        cy = st.number_input("Col. Y (cm)", 40.0)
    
    lc = st.number_input("Storey Height (m)", 3.0)
    col_type = st.selectbox("Column Position", ["interior", "edge", "corner"])
    
    st.markdown("---")
    has_drop = st.checkbox("Add Drop Panel")
    
    h_drop, drop_w, drop_l = 0.0, 0.0, 0.0
    use_drop_as_support = False
    
    if has_drop:
        h_drop = st.number_input("Drop Depth (cm)", 10.0)
        st.info(f"Total Thk: **{h_slab+h_drop:.0f} cm**")
        d1, d2 = st.columns(2)
        drop_w = d1.number_input("Drop Width (cm)", 250.0)
        drop_l = d2.number_input("Drop Length (cm)", 200.0)
        st.markdown("---")
        use_drop_as_support = st.checkbox("Use Drop as Support?", value=False)

# --- Group 3: Loads ---
with st.sidebar.expander("3. Design Loads", expanded=True):
    SDL = st.number_input("SDL (kg/m²)", 150.0)
    LL = st.number_input("Live Load (kg/m²)", 300.0)

# ==========================
# 3. CALCULATIONS CORE
# ==========================
# Data Packaging
mat_props = {"fc": fc, "fy": fy, "h_slab": h_slab, "cover": cover, "d_bar": d_bar, "h_drop": h_drop}
w_self = (h_slab/100)*2400
w_u = 1.2*(w_self + SDL) + 1.6*LL
load_props = {"SDL": SDL, "LL": LL, "w_u": w_u}

d_eff_slab = h_slab - cover - (d_bar/20.0)
d_eff_total = (h_slab + h_drop) - cover - (d_bar/20.0)

# Effective Geometry
eff_cx = drop_w if (has_drop and use_drop_as_support) else cx
eff_cy = drop_l if (has_drop and use_drop_as_support) else cy

# DDM Moments
ln_x = Lx - eff_cx/100
Mo_x = (w_u * Ly * ln_x**2) / 8
M_vals_x = { "M_cs_neg": 0.65 * Mo_x * 0.75, "M_ms_neg": 0.65 * Mo_x * 0.25, "M_cs_pos": 0.35 * Mo_x * 0.60, "M_ms_pos": 0.35 * Mo_x * 0.40 }

ln_y = Ly - eff_cy/100
Mo_y = (w_u * Lx * ln_y**2) / 8
M_vals_y = { "M_cs_neg": 0.65 * Mo_y * 0.75, "M_ms_neg": 0.65 * Mo_y * 0.25, "M_cs_pos": 0.35 * Mo_y * 0.60, "M_ms_pos": 0.35 * Mo_y * 0.40 }

# Shear Analysis
v_oneway_x = check_oneway_shear(w_u, Lx, Ly, cx, d_eff_slab, fc)
v_oneway_y = check_oneway_shear(w_u, Ly, Lx, cy, d_eff_slab, fc)
v_oneway_res = v_oneway_x if v_oneway_x['ratio'] > v_oneway_y['ratio'] else v_oneway_y
v_oneway_dir = "X-Axis" if v_oneway_x['ratio'] > v_oneway_y['ratio'] else "Y-Axis"

if has_drop:
    punch_res = check_punching_dual_case(w_u, Lx, Ly, fc, cx, cy, d_eff_total, d_eff_slab, drop_w, drop_l, col_type)
else:
    c1_d = cx + d_eff_total
    c2_d = cy + d_eff_total
    area_crit = (c1_d/100) * (c2_d/100)
    Vu_punch = w_u * (Lx*Ly - area_crit)
    punch_res = check_punching_shear(Vu_punch, fc, cx, cy, d_eff_total, col_type=col_type)

# ==========================
# 4. DASHBOARD HEADER
# ==========================
st.markdown("## 🏗️ ProFlat: Structural Analysis Dashboard")
st.markdown("---")

# Metric Card Helper Function
def metric_card(label, value, status, subtext=""):
    color_class = "status-pass" if status == "PASS" else ("status-fail" if status == "FAIL" else "status-info")
    icon = "✅" if status == "PASS" else ("❌" if status == "FAIL" else "ℹ️")
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-status {color_class}">{icon} {status}</div>
        <div style="font-size:0.8rem; color:#94a3b8; margin-top:5px;">{subtext}</div>
    </div>
    """, unsafe_allow_html=True)

# Dashboard Columns
col1, col2, col3, col4 = st.columns(4)

with col1:
    status = punch_res['status']
    metric_card("Punching Shear", f"{punch_res['ratio']:.2f}", status, "Capacity Ratio")

with col2:
    status = v_oneway_res['status']
    metric_card("One-Way Shear", f"{v_oneway_res['ratio']:.2f}", status, f"Critical at {v_oneway_dir}")

with col3:
    h_min = max(Lx, Ly)*100 / 33.0
    status = "PASS" if h_slab >= h_min else "CHECK"
    metric_card("Deflection Control", f"L/33", status, f"Min: {h_min:.1f} cm | Actual: {h_slab:.0f} cm")

with col4:
    metric_card("Factored Load (Wu)", f"{w_u:,.0f}", "INFO", "kg/m² (ULS)")

st.markdown("<br>", unsafe_allow_html=True)

# ==========================
# 5. CONTENT TABS
# ==========================
tab1, tab2, tab3, tab4 = st.tabs(["📐 Engineering Drawings", "📊 Calculation Sheet", "📝 DDM Analysis", "🏗️ EFM Stiffness"])

# --- TAB 1: DRAWINGS ---
with tab1:
    drop_data = {"has_drop": has_drop, "width": drop_w, "length": drop_l, "depth": h_drop}
    # Pass all critical data to the drawing module
    tab_drawings.render(
        L1=Lx, L2=Ly, c1_w=cx, c2_w=cy, h_slab=h_slab, lc=lc, cover=cover, 
        d_eff=d_eff_slab, drop_data=drop_data, moment_vals=M_vals_x,
        mat_props=mat_props, loads=load_props
        col_type=col_type  
    )

# --- TAB 2: CALC SHEET (Refactored for Cleanliness) ---
with tab2:
    st.markdown("### 📑 Detailed Calculation Report")
    
    def render_calc_section(res, label):
        with st.container():
            st.markdown(f"#### {label}")
            # Use columns for a structured layout
            c_a, c_b, c_c = st.columns([1, 1, 2])
            with c_a:
                st.markdown("**Geometric Params**")
                st.latex(f"d = {res['d']:.2f} \\text{{ cm}}")
                st.latex(f"b_0 = {res['b0']:.2f} \\text{{ cm}}")
            with c_b:
                st.markdown("**Coefficients**")
                st.latex(f"\\beta = {res['beta']:.2f}")
                st.latex(f"\\alpha_s = {res['alpha_s']}")
            with c_c:
                st.markdown("**Shear Capacity ($V_c$)**")
                st.write(f"V_c1 (Aspect): **{res['Vc1']:,.0f}** kg")
                st.write(f"V_c2 (Peri): **{res['Vc2']:,.0f}** kg")
                st.write(f"V_c3 (Basic): **{res['Vc3']:,.0f}** kg")
            
            st.divider()
            c_final1, c_final2 = st.columns([3, 1])
            with c_final1:
                st.info(f"Design Strength $\phi V_n$: **{res['Vc_design']:,.0f} kg** vs Factored Load $V_u$: **{res['Vu']:,.0f} kg**")
            with c_final2:
                st.metric("Ratio", f"{res['ratio']:.2f}", delta="-Safe" if res['ratio']<=1 else "+Fail", delta_color="inverse")

    if punch_res.get('is_dual', False):
        t1, t2 = st.tabs(["Inner Section (Column)", "Outer Section (Drop Panel)"])
        with t1: render_calc_section(punch_res['check_1'], "Critical Section 1: d/2 from Column Face")
        with t2: render_calc_section(punch_res['check_2'], "Critical Section 2: d/2 from Drop Panel")
    else:
        render_calc_section(punch_res, "Critical Section: d/2 from Column Face")

# --- TAB 3: DDM ---
with tab3:
    data_x = {"L_span": Lx, "L_width": Ly, "c_para": cx, "ln": ln_x, "Mo": Mo_x, "M_vals": M_vals_x}
    data_y = {"L_span": Ly, "L_width": Lx, "c_para": cy, "ln": ln_y, "Mo": Mo_y, "M_vals": M_vals_y}
    tab_ddm.render_dual(data_x, data_y, mat_props, w_u)

# --- TAB 4: EFM ---
with tab4:
    tab_efm.render(c1_w=cx, c2_w=cy, L1=Lx, L2=Ly, lc=lc, h_slab=h_slab, fc=fc, mat_props=mat_props, w_u=w_u, col_type=col_type)
