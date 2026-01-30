# app.py
import streamlit as st
import numpy as np
import pandas as pd

# Import Modules
# [UPDATED] Added check_oneway_shear to imports
from calculations import check_punching_shear, check_punching_dual_case, check_oneway_shear
import tab_ddm  # The interactive one
import tab_drawings # Placeholder
import tab_efm      # Placeholder

st.set_page_config(page_title="Pro Flat Slab Design", layout="wide", page_icon="🏗️")

# Custom CSS for Dashboard and Calculation Sheet
st.markdown("""
<style>
    .success-box { background-color: #d1e7dd; padding: 15px; border-radius: 5px; border-left: 5px solid #198754; color: #0f5132; }
    .fail-box { background-color: #f8d7da; padding: 15px; border-radius: 5px; border-left: 5px solid #dc3545; color: #842029; }
    div[data-testid="stMetricValue"] { font-size: 1.2rem; }
    .calc-header { font-size: 1.1rem; font-weight: bold; color: #333; margin-top: 10px; border-bottom: 2px solid #eee; padding-bottom: 5px; }
    .sub-calc { margin-left: 20px; font-family: 'Courier New', monospace; color: #444; }
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

        # [UPDATED] Option to use Drop Panel as Support Face for ln calculation
        st.markdown("---")
        use_drop_as_support = st.checkbox("Use Drop Panel as Support Face?", 
                                          help="ถ้าติ๊ก จะวัดระยะ Clear Span (ln) จากขอบ Drop Panel (Aggressive). ถ้าไม่ติ๊ก จะวัดจากขอบเสา (Conservative).")
    else:
        use_drop_as_support = False

# --- Group 3: Loads ---
with st.sidebar.expander("3. Loads", expanded=True):
    SDL = st.number_input("SDL (kg/m²)", 150.0)
    LL = st.number_input("Live Load (kg/m²)", 300.0)

# ==========================
# 2. DATA PACKAGING
# ==========================
mat_props = {
    "fc": fc, "fy": fy, "h_slab": h_slab, "cover": cover, 
    "d_bar": d_bar, "h_drop": h_drop
}

# Load Calculation
w_self = (h_slab/100)*2400
w_u = 1.2*(w_self + SDL) + 1.6*LL

# Effective Depth Calculation
d_eff_slab = h_slab - cover - (d_bar/20.0)
d_eff_total = (h_slab + h_drop) - cover - (d_bar/20.0)

# ==========================
# 3. ANALYSIS LOGIC
# ==========================

# --- [UPDATED] Determine Effective Support Dimension for Span Calculation ---
# ถ้าเลือกใช้ Drop Panel เป็น Support ให้ใช้ขนาด Drop, ถ้าไม่ ให้ใช้ขนาดเสา
eff_cx = drop_w if (has_drop and use_drop_as_support) else cx
eff_cy = drop_l if (has_drop and use_drop_as_support) else cy

# --- Moment Calculation (DDM) ---
# ใช้ eff_cx / eff_cy ในการคิด ln
ln_x = Lx - eff_cx/100
Mo_x = (w_u * Ly * ln_x**2) / 8
M_vals_x = {
    "M_cs_neg": 0.65 * Mo_x * 0.75, "M_ms_neg": 0.65 * Mo_x * 0.25,
    "M_cs_pos": 0.35 * Mo_x * 0.60, "M_ms_pos": 0.35 * Mo_x * 0.40
}

ln_y = Ly - eff_cy/100
Mo_y = (w_u * Lx * ln_y**2) / 8
M_vals_y = {
    "M_cs_neg": 0.65 * Mo_y * 0.75, "M_ms_neg": 0.65 * Mo_y * 0.25,
    "M_cs_pos": 0.35 * Mo_y * 0.60, "M_ms_pos": 0.35 * Mo_y * 0.40
}

# --- [NEW] One-Way Shear Check (Beam Action) ---
# เช็ค 2 แกน และเลือกค่าที่วิกฤตสุด (Beam Shear usually checked at d from support)
v_oneway_x = check_oneway_shear(w_u, Lx, Ly, cx, d_eff_slab, fc)
v_oneway_y = check_oneway_shear(w_u, Ly, Lx, cy, d_eff_slab, fc)

if v_oneway_x['ratio'] > v_oneway_y['ratio']:
    v_oneway_res = v_oneway_x
    v_oneway_dir = "X-Dir"
else:
    v_oneway_res = v_oneway_y
    v_oneway_dir = "Y-Dir"

# --- Punching Shear Check ---
if has_drop:
    punch_res = check_punching_dual_case(
        w_u, Lx, Ly, fc, cx, cy, 
        d_eff_total, d_eff_slab, 
        drop_w, drop_l, col_type
    )
else:
    c1_d = cx + d_eff_total
    c2_d = cy + d_eff_total
    area_crit = (c1_d/100) * (c2_d/100)
    Vu_punch = w_u * (Lx*Ly - area_crit)
    
    punch_res = check_punching_shear(Vu_punch, fc, cx, cy, d_eff_total, col_type=col_type)

# ==========================
# 4. DASHBOARD & DISPLAY
# ==========================
st.title("Pro Flat Slab Design System (Dual-Axis)")

# --- Top Dashboard [UPDATED Layout] ---
col_d1, col_d2, col_d3, col_d4 = st.columns(4) # เพิ่มเป็น 4 คอลัมน์

with col_d1:
    if punch_res['status'] == "PASS":
        st.markdown(f"<div class='success-box'>✅ <b>Punching: SAFE</b><br>Ratio: {punch_res['ratio']:.2f}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='fail-box'>❌ <b>Punching: FAIL</b><br>Ratio: {punch_res['ratio']:.2f}</div>", unsafe_allow_html=True)

# [NEW] One-Way Shear Box
with col_d2:
    if v_oneway_res['status'] == "PASS":
        st.markdown(f"<div class='success-box'>✅ <b>1-Way Shear: SAFE</b><br>Ratio: {v_oneway_res['ratio']:.2f}<br><small>({v_oneway_dir})</small></div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='fail-box'>❌ <b>1-Way Shear: FAIL</b><br>Ratio: {v_oneway_res['ratio']:.2f}<br><small>({v_oneway_dir})</small></div>", unsafe_allow_html=True)

with col_d3:
    h_min = max(Lx, Ly)*100 / 33.0
    st.info(f"Min Thick (ACI L/33): {h_min:.1f} cm\n(Actual: {h_slab:.0f} cm)")

with col_d4:
    st.metric("Factored Load (Wu)", f"{w_u:,.0f} kg/m²")

# ==========================
# 4.1 HELPER FUNCTION FOR DETAILED REPORT
# ==========================
def render_punching_details_sheet(res, title):
    """Renders a single detailed calculation sheet"""
    st.markdown(f"#### {title}")
    
    # --- Part 1: Geometry ---
    st.markdown("<div class='calc-header'>1. Geometric Parameters</div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.write(f"**Effective Depth ($d$):** {res['d']:.2f} cm")
        st.write(f"**Critical Perimeter ($b_o$):** {res['b0']:.2f} cm")
    with c2:
        st.write(f"**Column/Support Ratio ($\\beta$):** {res['beta']:.2f}")
        st.write(f"**Location Factor ($\\alpha_s$):** {res['alpha_s']}")
    
    st.markdown(f"""
    <div class='sub-calc'>
    b_o calculation (Square approx): 2 * (c1 + d) + 2 * (c2 + d) <br>
    Note: Critical section is located at d/2 from support face.
    </div>
    """, unsafe_allow_html=True)

    # --- Part 2: Load Analysis ---
    st.markdown("<div class='calc-header'>2. Load Analysis (Factored Shear)</div>", unsafe_allow_html=True)
    
    # Re-calculate Area_crit just for display (approx)
    # This is an estimation for display logic, actual calc is in logic file
    Ac_approx = (w_u * Lx * Ly - res['Vu']) / w_u
    
    st.latex(r"V_u = w_u \times (A_{total} - A_{crit})")
    st.write(f"- Total Area ($L_1 \\times L_2$): {Lx*Ly:.2f} m²")
    st.write(f"- Critical Area ($A_{{crit}}$): {Ac_approx:.4f} m² (Area inside critical section)")
    st.markdown(f"""
    <div style='background-color:#eef; padding:8px; border-radius:4px; font-weight:bold;'>
    V_u = {res['Vu']:,.0f} kg
    </div>
    """, unsafe_allow_html=True)

    # --- Part 3: Capacity ---
    st.markdown("<div class='calc-header'>3. Concrete Shear Strength ($V_c$)</div>", unsafe_allow_html=True)
    st.write("ACI 318-19 Table 22.6.5.2: Use the smallest of (a), (b), (c)")
    
    sqrt_fc = np.sqrt(fc)
    st.caption(f" Reference: $\\sqrt{{f'_c}} = \\sqrt{{{fc}}} = {sqrt_fc:.2f}$ ksc")

    # Equation A
    st.markdown("**a) Aspect Ratio Effect:**")
    st.latex(r"V_{c1} = 0.53\left(1 + \frac{2}{\beta}\right)\sqrt{f_c'} b_o d")
    st.latex(f"V_{{c1}} = 0.53(1 + \\frac{{2}}{{{res['beta']:.2f}}})({sqrt_fc:.2f})({res['b0']:.2f})({res['d']:.2f}) = \\mathbf{{{res['Vc1']:,.0f}}} \\text{{ kg}}")

    # Equation B
    st.markdown("**b) Perimeter Size Effect:**")
    st.latex(r"V_{c2} = 0.27\left(\frac{\alpha_s d}{b_o} + 2\right)\sqrt{f_c'} b_o d")
    term_b = (res['alpha_s'] * res['d'] / res['b0']) + 2
    st.latex(f"V_{{c2}} = 0.27({term_b:.2f})({sqrt_fc:.2f})({res['b0']:.2f})({res['d']:.2f}) = \\mathbf{{{res['Vc2']:,.0f}}} \\text{{ kg}}")

    # Equation C
    st.markdown("**c) Basic Shear Strength:**")
    st.latex(r"V_{c3} = 1.06\sqrt{f_c'} b_o d")
    st.latex(f"V_{{c3}} = 1.06({sqrt_fc:.2f})({res['b0']:.2f})({res['d']:.2f}) = \\mathbf{{{res['Vc3']:,.0f}}} \\text{{ kg}}")

    # --- Part 4: Conclusion ---
    st.markdown("<div class='calc-header'>4. Design Check</div>", unsafe_allow_html=True)
    
    col_res1, col_res2 = st.columns([2,1])
    with col_res1:
        st.write(f"- Nominal Strength ($V_n = \min(V_{{c1,2,3}})$): **{res['Vn']:,.0f} kg**")
        st.write(f"- Strength Reduction Factor ($\\phi$): **0.75**")
        st.write(f"- Design Strength ($\\phi V_n$): **{res['Vc_design']:,.0f} kg**")
    
    with col_res2:
        ratio = res['ratio']
        color = "green" if ratio <= 1.0 else "red"
        status_icon = "✅ OK" if ratio <= 1.0 else "❌ FAIL"
        st.markdown(f"""
        <div style='text-align:center; border: 2px solid {color}; padding: 10px; border-radius: 8px;'>
            <h3 style='color:{color}; margin:0;'>Ratio = {ratio:.2f}</h3>
            <p style='margin:0;'>{status_icon}</p>
        </div>
        """, unsafe_allow_html=True)

# ==========================
# 4.2 RENDER EXPANDER CONTENT
# ==========================
with st.expander("🔎 View Detailed Calculation Sheet (รายการคำนวณละเอียด)", expanded=False):
    
    is_dual = punch_res.get('is_dual', False)

    if is_dual:
        st.info("💡 **System Detect:** Drop Panel System (Checking 2 Critical Sections)")
        
        
        # Summary Table
        res1 = punch_res['check_1']
        res2 = punch_res['check_2']
        
        sum_data = {
            "Check Location": ["1. Inner (Column Face)", "2. Outer (Drop Panel Edge)"],
            "d (cm)": [res1['d'], res2['d']],
            "b0 (cm)": [res1['b0'], res2['b0']],
            "Vu (kg)": [res1['Vu'], res2['Vu']],
            "phi Vn (kg)": [res1['Vc_design'], res2['Vc_design']],
            "Ratio": [res1['ratio'], res2['ratio']],
            "Result": ["PASS" if res1['ratio']<=1 else "FAIL", "PASS" if res2['ratio']<=1 else "FAIL"]
        }
        df_sum = pd.DataFrame(sum_data)
        st.dataframe(df_sum.style.format({
            "d (cm)": "{:.2f}", "b0 (cm)": "{:.2f}", "Vu (kg)": "{:,.0f}", 
            "phi Vn (kg)": "{:,.0f}", "Ratio": "{:.2f}"
        }), use_container_width=True)

        # Tabs for details
        tab_inner, tab_outer = st.tabs(["📍 Check 1: Inner Section", "📍 Check 2: Outer Section"])
        
        with tab_inner:
            render_punching_details_sheet(res1, "Inner Section Calculation (Around Column)")
        with tab_outer:
            render_punching_details_sheet(res2, "Outer Section Calculation (Around Drop Panel)")
            
    else:
        st.info("💡 **System Detect:** Flat Plate (Single Critical Section)")
        
        render_punching_details_sheet(punch_res, "Punching Shear Calculation")

st.markdown("---")

# ==========================
# 5. TABS
# ==========================
tab1, tab2, tab3 = st.tabs(["1️⃣ Drawings", "2️⃣ DDM Calculation (Interactive)", "3️⃣ EFM Stiffness"])

with tab1:
    try:
        # Pass moment values for visualization
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
