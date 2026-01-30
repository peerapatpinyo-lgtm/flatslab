import streamlit as st
import numpy as np

# Import Modules
from calculations import check_punching_shear
import tab_drawings
import tab_ddm # (This uses the file we restored in previous cycle)
import tab_efm

st.set_page_config(page_title="Pro Flat Slab Design", layout="wide", page_icon="🏗️")

# Custom CSS for Dashboard
st.markdown("""
<style>
    .success-box { background-color: #d1e7dd; padding: 15px; border-radius: 5px; border-left: 5px solid #198754; color: #0f5132; }
    .fail-box { background-color: #f8d7da; padding: 15px; border-radius: 5px; border-left: 5px solid #dc3545; color: #842029; }
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
    st.markdown("---")
    has_drop = st.checkbox("Has Drop Panel? (เพิ่มแป้นหัวเสา)")
    h_drop = 0.0
    if has_drop:
        h_drop = st.number_input("Drop Thickness (cm)", 10.0)
        st.caption(f"ℹ️ Total Thickness at Column = {h_slab:.0f} + {h_drop:.0f} = **{h_slab+h_drop:.0f} cm**")

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
# 1. For Mid-Span (Flexure)
d_eff_slab = h_slab - cover - (d_bar/20.0)
# 2. For Punching Shear (Include Drop Panel if any)
d_eff_punch = (h_slab + h_drop) - cover - (d_bar/20.0)

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

# --- Punching Shear Check ---
c1_d = cx + d_eff_punch
c2_d = cy + d_eff_punch
area_crit = (c1_d/100) * (c2_d/100)
Vu_punch = w_u * (Lx*Ly - area_crit) # Total Load - Area inside critical perimeter

# Call Updated Function
punch_res = check_punching_shear(Vu_punch, fc, cx, cy, d_eff_punch)

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
    st.info(f"Min Thick (ACI L/33): {h_min:.1f} cm")

with col_d3:
    st.metric("Factored Load (Wu)", f"{w_u:,.0f} kg/m²")

# --- 🔎 DETAILED CALCULATION EXPANDER ---
with st.expander("🔎 View Punching Shear Calculation Details (รายการคำนวณ)", expanded=False):
    st.markdown("#### รายการคำนวณแรงเฉือนทะลุ (Punching Shear Calculation)")
    
    c1, c2 = st.columns([1, 1.2])
    
    with c1:
        st.markdown("**1. Design Parameters**")
        st.write(f"- Column Size: {cx:.0f} x {cy:.0f} cm")
        st.write(f"- Drop Panel: {'Yes' if has_drop else 'No'} (+{h_drop} cm)")
        st.write(f"- Effective Depth ($d$): **{d_eff_punch:.2f} cm**")
        st.write(f"- Critical Perimeter ($b_o$): **{punch_res['b0']:.2f} cm**")
        
        
    with c2:
        st.markdown("**2. Factored Shear Force ($V_u$)**")
        st.latex(r"V_u = w_u \times (L_1 L_2 - A_{crit})")
        st.latex(f"V_u = {w_u:,.0f} \\times ({Lx}\\times{Ly} - {area_crit:.2f}) = \\mathbf{{{punch_res['Vu']:,.0f}}} \\text{{ kg}}")

    st.markdown("---")
    st.markdown("**3. Concrete Shear Strength ($V_c$) per ACI 318**")
    st.caption("ต้องตรวจสอบทั้ง 3 สมการ แล้วใช้ค่าน้อยที่สุด (Governing Value)")
    
    col_eq1, col_eq2, col_eq3 = st.columns(3)
    
    with col_eq1:
        st.markdown("Equation 1 (Aspect Ratio)")
        st.latex(r"V_{c1} = 0.53(1 + \frac{2}{\beta})\sqrt{f_c'} b_o d")
        st.latex(f"V_{{c1}} = {punch_res['Vc1']:,.0f} \\text{{ kg}}")

    with col_eq2:
        st.markdown("Equation 2 (Large Perimeter)")
        st.latex(r"V_{c2} = 0.27(\frac{\alpha_s d}{b_o} + 2)\sqrt{f_c'} b_o d")
        st.latex(f"V_{{c2}} = {punch_res['Vc2']:,.0f} \\text{{ kg}}")
        
    with col_eq3:
        st.markdown("Equation 3 (Basic)")
        st.latex(r"V_{c3} = 1.06\sqrt{f_c'} b_o d")
        st.latex(f"V_{{c3}} = {punch_res['Vc3']:,.0f} \\text{{ kg}}")
        
    st.markdown(f"**Governing Nominal Strength ($V_n$):** $\min(V_{{c1}}, V_{{c2}}, V_{{c3}}) = \\mathbf{{{punch_res['Vn']:,.0f}}}$ kg")
    st.markdown(f"**Design Strength ($\phi V_c$):** $0.75 \\times {punch_res['Vn']:,.0f} = \\mathbf{{{punch_res['Vc_design']:,.0f}}}$ kg")
    
    # Conclusion
    color = "green" if punch_res['status'] == "PASS" else "red"
    st.markdown(f"""
    <div style='background-color:#f0f2f6; padding:10px; border-radius:5px;'>
    <b>Conclusion:</b> <br>
    Ratio = $V_u / \phi V_c$ = {punch_res['Vu']:,.0f} / {punch_res['Vc_design']:,.0f} = <b style='color:{color}'>{punch_res['ratio']:.2f}</b> ({punch_res['status']})
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ==========================
# 5. TABS
# ==========================
tab1, tab2, tab3 = st.tabs(["1️⃣ Drawings", "2️⃣ DDM Calculation (Interactive)", "3️⃣ EFM Stiffness"])

with tab1:
    # Use generic arguments (Tab Drawings logic remains same)
    tab_drawings.render(Lx, Ly, cx, cy, h_slab, lc, cover, d_eff_slab, M_vals_x)

with tab2:
    # Prepare Data Packs for DDM Tab
    data_x = {
        "L_span": Lx, "L_width": Ly, "c_para": cx, 
        "ln": ln_x, "Mo": Mo_x, "M_vals": M_vals_x
    }
    data_y = {
        "L_span": Ly, "L_width": Lx, "c_para": cy, 
        "ln": ln_y, "Mo": Mo_y, "M_vals": M_vals_y
    }
    # Pass mat_props explicitly to handle inputs correctly
    tab_ddm.render_dual(data_x, data_y, mat_props, w_u)

with tab3:
    tab_efm.render(cx, cy, Lx, Ly, lc, h_slab, fc)
