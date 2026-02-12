# app.py
import streamlit as st
import numpy as np
import pandas as pd

# ---------------------------------------------------------
# 1. SETUP & CONFIGURATION
# ---------------------------------------------------------
st.set_page_config(
    page_title="ProFlat: Structural Design Suite", 
    layout="wide", 
    page_icon="🏗️"
)

# Custom CSS for Engineering Dashboard
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Roboto', sans-serif; }
    
    .metric-card {
        background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px;
        padding: 20px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        text-align: center; transition: transform 0.2s;
    }
    .metric-card:hover { transform: translateY(-2px); }
    .metric-label { font-size: 0.85rem; color: #64748b; text-transform: uppercase; letter-spacing: 1px; font-weight: 600; }
    .metric-value { font-size: 1.8rem; font-weight: 700; color: #0f172a; margin: 5px 0; }
    
    /* Status Colors */
    .status-pass { background-color: #dcfce7; color: #166534; padding: 4px 12px; border-radius: 20px; font-weight: 600; font-size: 0.9rem;} 
    .status-fail { background-color: #fee2e2; color: #991b1b; padding: 4px 12px; border-radius: 20px; font-weight: 600; font-size: 0.9rem;} 
    .status-info { background-color: #f1f5f9; color: #334155; padding: 4px 12px; border-radius: 20px; font-weight: 600; font-size: 0.9rem;}
</style>
""", unsafe_allow_html=True)

# Import Modules with Error Handling
try:
    from calculations import FlatSlabDesign
except ImportError:
    st.error("🚨 CRITICAL ERROR: ไม่พบไฟล์ 'calculations.py' กรุณาตรวจสอบไฟล์ในโฟลเดอร์")
    st.stop()
    
# Import Tabs (Assuming these exist)
try:
    import tab_ddm  
    import tab_drawings 
    import tab_efm
    import tab_calc
except ImportError as e:
    st.warning(f"⚠️ Warning: Module not found - {e}")

# =========================================================
# 2. SIDEBAR INPUTS (ENGINEERING CONTROL)
# =========================================================
st.sidebar.title("🏗️ Design Parameters")

# --- Section 1: Location & Geometry (CRITICAL FIX) ---
st.sidebar.header("1. Column & Span Location")
with st.sidebar.expander("📍 Column Position & Boundaries", expanded=True):
    # นี่คือส่วนที่คุณถามหา: เลือกตำแหน่งเสาเพื่อกำหนด Behavior
    col_type_options = {
        "Interior Column (ใน)": "interior",
        "Edge Column (ขอบ)": "edge",
        "Corner Column (มุม)": "corner"
    }
    
    col_display = st.selectbox(
        "Select Column Location:", 
        list(col_type_options.keys()),
        index=0,
        help="มีผลต่อค่า Alpha_s (Punching) และ Moment Distribution"
    )
    col_type = col_type_options[col_display]

    # [Engineer Logic] Show Alpha_s immediately
    if col_type == "interior":
        alpha_s = 40
        st.info(f"✅ Interior: αs = {alpha_s} (4 Sides)")
    elif col_type == "edge":
        alpha_s = 30
        st.info(f"⚠️ Edge: αs = {alpha_s} (3 Sides)")
    else: # corner
        alpha_s = 20
        st.warning(f"🔥 Corner: αs = {alpha_s} (2 Sides)")

    # [Addition] Edge Beam Check for DDM
    has_edge_beam = False
    if col_type != "interior":
        has_edge_beam = st.checkbox("Has Edge Beam?", value=False, help="Affects DDM Coefficients (αf)")

    st.markdown("---")
    c_geo1, c_geo2 = st.columns(2)
    Lx = c_geo1.number_input("Span Lx (m)", value=8.0, min_value=1.0)
    Ly = c_geo2.number_input("Span Ly (m)", value=6.0, min_value=1.0)
    
    c_dim1, c_dim2 = st.columns(2)
    cx = c_dim1.number_input("Col. Width Cx (cm)", value=40.0, min_value=15.0)
    cy = c_dim2.number_input("Col. Depth Cy (cm)", value=40.0, min_value=15.0)
    
    lc = st.number_input("Storey Height (m)", value=3.0)

# --- Section 2: Material & Section ---
with st.sidebar.expander("2. Material & Slab Thickness", expanded=False):
    c_mat1, c_mat2 = st.columns(2)
    fc = c_mat1.number_input("f'c (ksc)", value=240.0, step=10.0)
    fy = c_mat2.number_input("fy (ksc)", value=4000.0, step=100.0)
    
    h_slab = st.number_input("Slab Thickness (cm)", value=20.0, step=1.0)
    cover = st.number_input("Cover (cm)", value=2.5)
    
    # Drop Panel Logic
    has_drop = st.checkbox("Add Drop Panel")
    h_drop, drop_w, drop_l = 0.0, 0.0, 0.0
    use_drop_as_support = False
    
    if has_drop:
        st.markdown("waiting for dimensions...")
        c_drop1, c_drop2 = st.columns(2)
        h_drop = c_drop1.number_input("Drop Depth (cm)", value=10.0)
        st.success(f"Total Thickness @ Support: **{h_slab + h_drop:.0f} cm**")
        
        c_drop3, c_drop4 = st.columns(2)
        drop_w = c_drop3.number_input("Drop Width (cm)", value=250.0)
        drop_l = c_drop4.number_input("Drop Length (cm)", value=200.0)
        use_drop_as_support = st.checkbox("Use Drop as Support for Clear Span?", value=False)

# --- Section 3: Loads ---
with st.sidebar.expander("3. Loads & Factors", expanded=False):
    c_load1, c_load2 = st.columns(2)
    SDL = c_load1.number_input("SDL (kg/m²)", value=150.0)
    LL = c_load2.number_input("Live Load (kg/m²)", value=300.0)
    
    st.caption("Load Factors & Phi")
    c_fac1, c_fac2 = st.columns(2)
    factor_dl = c_fac1.number_input("Factored DL", value=1.4)
    factor_ll = c_fac2.number_input("Factored LL", value=1.7)
    
    c_phi1, c_phi2 = st.columns(2)
    phi_shear = c_phi1.number_input("φ Shear", value=0.85)
    phi_bend = c_phi2.number_input("φ Bending", value=0.90)


# --- Section 4: Reinforcement (FIXED) ---
with st.sidebar.expander("4. Reinforcement", expanded=False):
    st.markdown("### 🛠️ Rebar Configuration")
    
    # Checkbox เพื่อเปิดโหมดละเอียด
    use_detailed_rebar = st.checkbox("🔧 Advanced/Zone Control", value=False, help="กำหนดขนาดเหล็กและระยะเรียงแยกตามโซน (Column/Middle Strip)")

    if not use_detailed_rebar:
        # --- SIMPLE MODE ---
        st.caption("🔹 Global Settings (Apply to All)")
        base_db = st.selectbox("Main Bar Diameter (mm)", [10, 12, 16, 20, 25, 28, 32], index=1)
        base_spa = st.number_input("Typical Spacing (cm)", value=20.0, step=5.0)

        # [FIX] กำหนดค่า rebar_db เพื่อให้บรรทัด 233 ไม่ Error
        rebar_db = base_db 

        rebar_cfg = {
            'cs_top_db': base_db, 'cs_top_spa': base_spa,
            'cs_bot_db': base_db, 'cs_bot_spa': base_spa,
            'ms_top_db': base_db, 'ms_top_spa': base_spa,
            'ms_bot_db': base_db, 'ms_bot_spa': base_spa
        }
        
        st.info(f"Setting: DB{base_db}@{base_spa:.0f}cm (All Zones)")

    else:
        # --- ADVANCED MODE ---
        st.markdown("---")
        st.caption("📍 **Column Strip (แถบเสา)**")
        c_cs1, c_cs2 = st.columns(2)
        with c_cs1:
            st.markdown("Top (-)")
            cs_top_db = st.selectbox("Dia.", [10, 12, 16, 20, 25], index=2, key="cs_t_d")
            cs_top_spa = st.number_input("Spa.", value=15.0, step=2.5, key="cs_t_s")
        with c_cs2:
            st.markdown("Bot (+)")
            cs_bot_db = st.selectbox("Dia.", [10, 12, 16, 20, 25], index=1, key="cs_b_d")
            cs_bot_spa = st.number_input("Spa.", value=20.0, step=2.5, key="cs_b_s")

        st.markdown("---")
        st.caption("📍 **Middle Strip (แถบกลาง)**")
        c_ms1, c_ms2 = st.columns(2)
        with c_ms1:
            st.markdown("Top (-)")
            ms_top_db = st.selectbox("Dia.", [10, 12, 16, 20, 25], index=1, key="ms_t_d")
            ms_top_spa = st.number_input("Spa.", value=20.0, step=2.5, key="ms_t_s")
        with c_ms2:
            st.markdown("Bot (+)")
            ms_bot_db = st.selectbox("Dia.", [10, 12, 16, 20, 25], index=1, key="ms_b_d")
            ms_bot_spa = st.number_input("Spa.", value=25.0, step=2.5, key="ms_b_s")

        # [FIX] ใช้ค่า Top Column Strip เป็นตัวแทนหลักไปก่อน (เพื่อกัน Error)
        rebar_db = cs_top_db 

        rebar_cfg = {
            'cs_top_db': cs_top_db, 'cs_top_spa': cs_top_spa,
            'cs_bot_db': cs_bot_db, 'cs_bot_spa': cs_bot_spa,
            'ms_top_db': ms_top_db, 'ms_top_spa': ms_top_spa,
            'ms_bot_db': ms_bot_db, 'ms_bot_spa': ms_bot_spa
        }


# =========================================================
# 3. CONTROLLER & ANALYSIS
# =========================================================

# 3.1 Pack User Inputs
user_inputs = {
    # Material
    "fc": fc, "fy": fy,
    "h_slab": h_slab, "cover": cover,
    
    # Geometry
    "Lx": Lx, "Ly": Ly,
    "cx": cx, "cy": cy,
    "lc": lc,
    
    # Logic Keys (Fixed)
    "col_type": col_type,       # interior, edge, corner
    "alpha_s": alpha_s,         # 40, 30, 20 passed explicitly
    "has_edge_beam": has_edge_beam,
    
    # Components
    "has_drop": has_drop,
    "h_drop": h_drop, "drop_w": drop_w, "drop_l": drop_l,
    "use_drop_as_support": use_drop_as_support,
    
    # Loads
    "SDL": SDL, "LL": LL,
    "factor_dl": factor_dl, "factor_ll": factor_ll,
    "phi": phi_bend,          # For Flexure
    "phi_shear": phi_shear,   # For Shear
    
    # Rebar
    "d_bar": rebar_db,
    "rebar_cfg": rebar_cfg,
    
    # Openings (Default 0 for now)
    "open_w": 0.0, "open_dist": 0.0
}

# 3.2 Initialize & Run Model
# Load Factors Dictionary
factors = {'DL': factor_dl, 'LL': factor_ll, 'phi': phi_shear}

try:
    model = FlatSlabDesign(user_inputs, factors=factors)
    results = model.run_full_analysis()
    
    # Unpack Results safely
    loads_res = results.get('loads', {})
    geo_res = results.get('geometry', {})
    shear_res = results.get('shear_oneway', {})
    punch_res = results.get('shear_punching', {})
    check_res = results.get('checks', {})
    ddm_res = results.get('ddm', {'x': {}, 'y': {}})

except Exception as e:
    st.error(f"❌ Calculation Error: {str(e)}")
    st.stop()

# =========================================================
# 4. MAIN DASHBOARD UI
# =========================================================

# Title Section
c_title1, c_title2 = st.columns([3, 1])
with c_title1:
    st.title("🏗️ ProFlat: Structural Dashboard")
    st.caption(f"Design Code: ACI 318 / EIT | Concrete: {fc} ksc | Steel: {fy} ksc")
with c_title2:
    # Quick Status Badge
    overall_status = "PASS" if (punch_res.get('status') == "OK" and shear_res.get('status') == "OK") else "CHECK"
    color = "green" if overall_status == "PASS" else "red"
    st.markdown(f"<h2 style='text-align:right; color:{color}; border: 2px solid {color}; padding: 5px; border-radius: 10px;'>{overall_status}</h2>", unsafe_allow_html=True)

st.markdown("---")

# *** NOTE: Removed KPI Cards Row (Punching Shear, One-way Shear, Thickness, Loads) as requested ***

# =========================================================
# 5. DETAILED TABS
# =========================================================
t1, t2, t3, t4 = st.tabs(["📐 Drawings & Geom", "📝 Calculation Detail", "📊 Moment (DDM)", "🏗️ Stiffness (EFM)"])

with t1:
    # Pass Data to Drawing Module
    if 'tab_drawings' in globals():
        drop_data = {"has_drop": has_drop, "width": drop_w, "length": drop_l, "depth": h_drop}
        tab_drawings.render(
            L1=Lx, L2=Ly, c1_w=cx, c2_w=cy, h_slab=h_slab, lc=lc, cover=cover,
            d_eff=geo_res.get('d_slab', h_slab-3),
            drop_data=drop_data,
            moment_vals=ddm_res['x'].get('M_vals', {}), # Mock passing
            mat_props=user_inputs,
            loads=loads_res,
            col_type=col_type
        )
    else:
        st.info("Module 'tab_drawings' loaded (Placeholder)")

with t2:
    if 'tab_calc' in globals():
        tab_calc.render(
            punch_res=punch_res,
            v_oneway_res=shear_res,
            mat_props=user_inputs,
            loads=loads_res,
            Lx=Lx, Ly=Ly
        )

with t3:
    if 'tab_ddm' in globals():
        tab_ddm.render_dual(
            data_x=ddm_res['x'],
            data_y=ddm_res['y'],
            mat_props=user_inputs,
            w_u=wu
        )

with t4:
    if 'tab_efm' in globals():
        tab_efm.render(
            c1_w=cx, c2_w=cy, L1=Lx, L2=Ly, lc=lc, h_slab=h_slab, fc=fc,
            mat_props=user_inputs,
            w_u=wu,
            col_type=col_type,
            h_drop=h_drop + h_slab if has_drop else h_slab,
            drop_w=drop_w/100 if has_drop else 0,
            drop_l=drop_l/100 if has_drop else 0
        )
