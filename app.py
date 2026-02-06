# app.py
import streamlit as st
import numpy as np
import pandas as pd

# Import Modules
from calculations import FlatSlabDesign 
import tab_ddm  
import tab_drawings 
import tab_efm
import tab_calc

# ---------------------------------------------------------
# 1. PAGE CONFIG & STYLING
# ---------------------------------------------------------
st.set_page_config(page_title="ProFlat: Structural Design Suite", layout="wide", page_icon="🏗️")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Roboto', sans-serif; }
    
    /* KPI Cards */
    .metric-card {
        background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px;
        padding: 20px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        text-align: center; transition: transform 0.2s;
    }
    .metric-card:hover { transform: translateY(-2px); }
    .metric-label { font-size: 0.85rem; color: #64748b; text-transform: uppercase; letter-spacing: 1px; font-weight: 600; }
    .metric-value { font-size: 1.8rem; font-weight: 700; color: #0f172a; margin: 5px 0; }
    .metric-status { font-size: 0.9rem; font-weight: 600; padding: 4px 12px; border-radius: 20px; display: inline-block;}
    
    .status-pass { background-color: #dcfce7; color: #166534; } 
    .status-fail { background-color: #fee2e2; color: #991b1b; } 
    .status-info { background-color: #f1f5f9; color: #334155; }
</style>
""", unsafe_allow_html=True)

# ==========================
# 2. SIDEBAR: PROJECT PARAMS (VIEW / INPUT)
# ==========================
st.sidebar.markdown("### ⚙️ Design Parameters")

# --- Group 1: Material ---
with st.sidebar.expander("1. Material Properties", expanded=True):
    c1, c2 = st.columns(2)
    fc = c1.number_input("f'c (ksc)", value=240.0, step=10.0, min_value=1.0)
    fy = c2.number_input("fy (ksc)", value=4000.0, step=100.0)
    h_slab = st.number_input("Slab Thickness (cm)", value=20.0, step=1.0, min_value=5.0)
    
    c3, c4 = st.columns(2)
    cover = c3.number_input("Cover (cm)", value=2.5)
    d_bar = c4.selectbox("Rebar (mm)", [12, 16, 20, 25], index=0)

# --- Group 2: Geometry ---
with st.sidebar.expander("2. Geometry & Span", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        Lx = st.number_input("Span Lx (m)", value=8.0, min_value=0.5)
        cx = st.number_input("Col. X (cm)", value=40.0, min_value=10.0)
    with col2:
        Ly = st.number_input("Span Ly (m)", value=6.0, min_value=0.5)
        cy = st.number_input("Col. Y (cm)", value=40.0, min_value=10.0)
    
    lc = st.number_input("Storey Height (m)", value=3.0)
    col_type = st.selectbox("Column Position", ["interior", "edge", "corner"])
    
    # --- Drop Panel ---
    st.markdown("---")
    has_drop = st.checkbox("Add Drop Panel")
    
    h_drop, drop_w, drop_l = 0.0, 0.0, 0.0
    use_drop_as_support = False
    
    if has_drop:
        h_drop = st.number_input("Drop Depth (cm)", value=10.0)
        st.info(f"Total Thk: **{h_slab+h_drop:.0f} cm**")
        d1, d2 = st.columns(2)
        drop_w = d1.number_input("Drop Width (cm)", value=250.0)
        drop_l = d2.number_input("Drop Length (cm)", value=200.0)
        use_drop_as_support = st.checkbox("Use Drop as Support?", value=False)
        
    # --- [NEW] Opening ---
    st.markdown("---")
    has_opening = st.checkbox("Add Opening near Column")
    open_w, open_dist = 0.0, 0.0
    
    if has_opening:
        st.caption("Opening affects Punching Shear Perimeter")
        c_op1, c_op2 = st.columns(2)
        open_w = c_op1.number_input("Opening Width (cm)", value=30.0, min_value=0.0)
        open_dist = c_op2.number_input("Dist. from Face (cm)", value=5.0, min_value=0.0)

# --- Group 3: Loads ---
with st.sidebar.expander("3. Design Loads", expanded=True):
    SDL = st.number_input("SDL (kg/m²)", value=150.0)
    LL = st.number_input("Live Load (kg/m²)", value=300.0)

# ==========================
# 3. CONTROLLER LOGIC (Connect UI to Model)
# ==========================

# 3.1 Pack Inputs: รวบรวมค่าจากหน้าจอใส่กล่องเดียว
user_inputs = {
    "fc": fc, "fy": fy,
    "h_slab": h_slab, "cover": cover, "d_bar": d_bar,
    "Lx": Lx, "Ly": Ly,
    "cx": cx, "cy": cy,
    "lc": lc, "col_type": col_type,
    "has_drop": has_drop,
    "h_drop": h_drop, "drop_w": drop_w, "drop_l": drop_l,
    "use_drop_as_support": use_drop_as_support,
    "SDL": SDL, "LL": LL,
    # [NEW] Opening Inputs
    "open_w": open_w if has_opening else 0.0,
    "open_dist": open_dist if has_opening else 0.0
}

# 3.2 Initialize Model: ส่งค่าเข้า Class คำนวณ
model = FlatSlabDesign(user_inputs)

# 3.3 Execute: สั่งคำนวณทุกอย่าง
results = model.run_full_analysis()

# ==========================
# 4. DASHBOARD DISPLAY (VIEW)
# ==========================
st.markdown("## 🏗️ ProFlat: Structural Analysis Dashboard")
st.markdown("---")

def metric_card(label, value, status, subtext=""):
    is_pass = status in ["OK", "PASS"]
    is_fail = status == "FAIL"
    
    color_class = "status-pass" if is_pass else ("status-fail" if is_fail else "status-info")
    icon = "✅" if is_pass else ("❌" if is_fail else "ℹ️")
    
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-status {color_class}">{icon} {status}</div>
        <div style="font-size:0.8rem; color:#94a3b8; margin-top:5px;">{subtext}</div>
    </div>
    """, unsafe_allow_html=True)

# Unpack results for Header Dashboard
loads_res = results['loads']
geo_res = results['geometry']
shear_res = results['shear_oneway']
punch_res = results['shear_punching']
check_res = results['checks']

col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)

with col_kpi1:
    status = punch_res.get('status', 'ERROR')
    ratio = punch_res.get('ratio', 0)
    # Update Subtext to warn if Opening is used
    note_txt = punch_res.get('note', '')
    metric_card("Punching Shear", f"{ratio:.2f}", status, note_txt)

with col_kpi2:
    status = shear_res['status']
    metric_card("One-Way Shear", f"{shear_res['ratio']:.2f}", status, f"Critical at {shear_res['critical_dir']}")

with col_kpi3:
    h_min = check_res['h_min']
    status_def = "PASS" if h_slab >= h_min else "CHECK"
    metric_card("Deflection Control", f"L/33", status_def, f"Min: {h_min:.1f} cm | Actual: {h_slab:.0f} cm")

with col_kpi4:
    metric_card("Factored Load (Wu)", f"{loads_res['w_u']:,.0f}", "INFO", "kg/m² (ULS)")

st.markdown("<br>", unsafe_allow_html=True)

# ==========================
# 5. CONTENT TABS
# ==========================
tab1, tab2, tab3, tab4 = st.tabs(["📐 Engineering Drawings", "📊 Calculation Sheet", "📝 DDM Analysis", "🏗️ EFM Stiffness"])

# --- TAB 1: DRAWINGS ---
with tab1:
    drop_data = {"has_drop": has_drop, "width": drop_w, "length": drop_l, "depth": h_drop}
    # ส่งค่าที่ Clean แล้วจาก Model ไปให้ module วาดรูป
    tab_drawings.render(
        L1=Lx, L2=Ly, c1_w=cx, c2_w=cy, h_slab=h_slab, lc=lc, cover=cover, 
        d_eff=geo_res['d_slab'], 
        drop_data=drop_data, 
        moment_vals=results['ddm']['x']['M_vals'], 
        mat_props=user_inputs, 
        loads=loads_res, 
        col_type=col_type  
    )

# --- TAB 2: CALCULATIONS ---
with tab2:
    tab_calc.render(
        punch_res=punch_res, 
        v_oneway_res=shear_res, 
        mat_props=user_inputs, 
        loads=loads_res,
        Lx=Lx, Ly=Ly
    )    

# --- TAB 3: DDM ---
with tab3:
    tab_ddm.render_dual(
        data_x=results['ddm']['x'], 
        data_y=results['ddm']['y'], 
        mat_props=user_inputs, 
        w_u=loads_res['w_u']
    )

# --- TAB 4: EFM ---
with tab4:
    tab_efm.render(
        c1_w=cx, c2_w=cy, L1=Lx, L2=Ly, lc=lc, h_slab=h_slab, fc=fc, 
        mat_props=user_inputs, 
        w_u=loads_res['w_u'], 
        col_type=col_type,
        h_drop=h_drop + h_slab if has_drop else h_slab,
        drop_w=drop_w/100 if has_drop else 0,
        drop_l=drop_l/100 if has_drop else 0
    )
