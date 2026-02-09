# app.py
import streamlit as st
import numpy as np
import pandas as pd

# Import Modules
try:
    from calculations import FlatSlabDesign
except ImportError:
    st.error("ไม่พบไฟล์ calculations.py")
    
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
    st.caption(f"d_eff approx: {h_slab - cover - 1.2:.1f} cm")

# --- Group 2: Geometry ---
with st.sidebar.expander("2. Geometry & Span", expanded=False):
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
        
    # --- Opening ---
    st.markdown("---")
    has_opening = st.checkbox("Add Opening near Column")
    open_w, open_dist = 0.0, 0.0
    
    if has_opening:
        st.caption("Opening affects Punching Shear Perimeter")
        c_op1, c_op2 = st.columns(2)
        open_w = c_op1.number_input("Opening Width (cm)", value=30.0, min_value=0.0)
        open_dist = c_op2.number_input("Dist. from Face (cm)", value=5.0, min_value=0.0)

# --- Group 3: Loads & Factors (UPDATED) ---
with st.sidebar.expander("3. Design Loads & Factors", expanded=False):
    st.markdown("**Load Factors:**")
    c_f1, c_f2 = st.columns(2)
    factor_dl = c_f1.number_input("Fac. DL", value=1.4, step=0.1, format="%.2f")
    factor_ll = c_f2.number_input("Fac. LL", value=1.7, step=0.1, format="%.2f")
    
    st.markdown("---")
    st.markdown("**Strength Reduction (φ):**")
    c_p1, c_p2 = st.columns(2)
    # [FIX] แยกค่า Phi Shear และ Phi Bending
    phi_shear = c_p1.number_input("φ Shear", value=0.85, step=0.05, format="%.2f", help="For Shear/Punching (0.75 or 0.85)")
    phi_bend = c_p2.number_input("φ Bend", value=0.90, step=0.05, format="%.2f", help="For Flexure/Moment (0.90)")
    
    st.markdown("---")
    SDL = st.number_input("SDL (kg/m²)", value=150.0)
    LL = st.number_input("Live Load (kg/m²)", value=300.0)

# --- Group 4: Reinforcement Detailing ---
with st.sidebar.expander("4. Reinforcement Detailing", expanded=True):
    rebar_mode = st.radio("Selection Mode:", ["Uniform (Auto)", "Custom (Manual)"], horizontal=True)
    
    bar_opts = [9, 10, 12, 16, 20, 25]
    spa_opts = [10, 15, 20, 25, 30]

    cfg = {
        'cs_top_db': 12, 'cs_top_spa': 15,
        'cs_bot_db': 12, 'cs_bot_spa': 20,
        'ms_top_db': 12, 'ms_top_spa': 20,
        'ms_bot_db': 12, 'ms_bot_spa': 25
    }

    if rebar_mode == "Uniform (Auto)":
        c_r1, c_r2 = st.columns(2)
        main_db = c_r1.selectbox("Main Bar (mm)", bar_opts, index=2) # Default DB12
        main_spa = c_r2.selectbox("Spacing (cm)", spa_opts, index=2) # Default @20
        
        for key in cfg:
            if 'db' in key: cfg[key] = main_db
            if 'spa' in key: cfg[key] = main_spa
            
    else: # Custom Manual Mode
        st.markdown("**🟥 Column Strip**")
        c1, c2 = st.columns(2)
        cfg['cs_top_db'] = c1.selectbox("Top Dia", bar_opts, index=2, key="cst_d")
        cfg['cs_top_spa'] = c2.selectbox("Top @", spa_opts, index=1, key="cst_s")
        
        c3, c4 = st.columns(2)
        cfg['cs_bot_db'] = c3.selectbox("Bot Dia", bar_opts, index=2, key="csb_d")
        cfg['cs_bot_spa'] = c4.selectbox("Bot @", spa_opts, index=2, key="csb_s")
        
        st.markdown("**🟦 Middle Strip**")
        c5, c6 = st.columns(2)
        cfg['ms_top_db'] = c5.selectbox("Top Dia", bar_opts, index=2, key="mst_d")
        cfg['ms_top_spa'] = c6.selectbox("Top @", spa_opts, index=2, key="mst_s")
        
        c7, c8 = st.columns(2)
        cfg['ms_bot_db'] = c7.selectbox("Bot Dia", bar_opts, index=2, key="msb_d")
        cfg['ms_bot_spa'] = c8.selectbox("Bot @", spa_opts, index=3, key="msb_s")

    d_bar = cfg['cs_top_db'] 

# ==========================
# 3. CONTROLLER LOGIC
# ==========================

# 3.1 Pack Inputs
user_inputs = {
    "fc": fc, "fy": fy,
    "h_slab": h_slab, "cover": cover, 
    "d_bar": d_bar,
    "rebar_cfg": cfg,
    "Lx": Lx, "Ly": Ly,
    "cx": cx, "cy": cy,
    "lc": lc, "col_type": col_type,
    "has_drop": has_drop,
    "h_drop": h_drop, "drop_w": drop_w, "drop_l": drop_l,
    "use_drop_as_support": use_drop_as_support,
    "SDL": SDL, "LL": LL,
    "open_w": open_w if has_opening else 0.0,
    "open_dist": open_dist if has_opening else 0.0,
    
    # [IMPORTANT] ส่งค่าแยกกันเพื่อความชัดเจน
    "factor_dl": factor_dl,
    "factor_ll": factor_ll,
    "phi": phi_bend,       # Key 'phi' ใช้สำหรับ Tab_DDM (Bending) ตามโค้ดเดิม
    "phi_shear": phi_shear # Key 'phi_shear' ส่งเพิ่มเผื่อไว้ใช้
}

# 3.1.2 Pack Factors for Model
load_factors = {
    'DL': factor_dl,
    'LL': factor_ll,
    'phi': phi_shear # สำหรับ Model (Punching) ให้ใช้ phi_shear เป็นหลัก
}

# 3.2 Initialize Model
# หมายเหตุ: Model จะใช้ load_factors['phi'] (ซึ่งตอนนี้คือ shear) ไปคำนวณ Punching
model = FlatSlabDesign(user_inputs, factors=load_factors)

# 3.3 Execute
results = model.run_full_analysis()

# ==========================
# 4. DASHBOARD DISPLAY
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

# Unpack results
loads_res = results['loads']
geo_res = results['geometry']
shear_res = results['shear_oneway']
punch_res = results['shear_punching']
check_res = results['checks']

col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)

with col_kpi1:
    status = punch_res.get('status', 'ERROR')
    ratio = punch_res.get('ratio', 0)
    note_txt = punch_res.get('note', '')
    # แสดงให้รู้ว่าใช้ Phi ตัวไหน
    metric_card("Punching Shear", f"{ratio:.2f}", status, f"φ={phi_shear:.2f} | {note_txt}")

with col_kpi2:
    status = shear_res['status']
    metric_card("One-Way Shear", f"{shear_res['ratio']:.2f}", status, f"φ={phi_shear:.2f} | Critical at {shear_res['critical_dir']}")

with col_kpi3:
    h_min = check_res['h_min']
    status_def = "PASS" if h_slab >= h_min else "CHECK"
    metric_card("Deflection Control", f"L/33", status_def, f"Min: {h_min:.1f} cm | Actual: {h_slab:.0f} cm")

with col_kpi4:
    subtext_factors = f"({factor_dl}D + {factor_ll}L)"
    metric_card("Factored Load (Wu)", f"{loads_res['w_u']:,.0f}", "INFO", subtext_factors)

st.markdown("<br>", unsafe_allow_html=True)

# ==========================
# 5. CONTENT TABS
# ==========================
tab1, tab2, tab3, tab4 = st.tabs(["📐 Engineering Drawings", "📊 Calculation Sheet", "📝 DDM Analysis", "🏗️ EFM Stiffness"])

# --- TAB 1: DRAWINGS ---
with tab1:
    drop_data = {"has_drop": has_drop, "width": drop_w, "length": drop_l, "depth": h_drop}
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
    # tab_ddm จะอ่านค่า 'phi' จาก user_inputs ซึ่งเรา map ไว้เป็น phi_bend แล้ว
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
