import streamlit as st
import pandas as pd
import numpy as np

# IMPORT CUSTOM MODULES
import DDM_Logic as logic
import DDM_Schematics as schem

# Optional import for plotting
try:
    import ddm_plots
    HAS_PLOTS = True
except ImportError:
    HAS_PLOTS = False

# ========================================================
# 1. HELPER: PUNCHING SHEAR CALCULATOR (CORE LOGIC)
# ========================================================
def calculate_punching_physics(c1, c2, d, col_location):
    """
    Calculate Properties of Critical Section for Punching Shear
    c1: Dimension parallel to moment axis (cm)
    c2: Dimension perpendicular to moment axis (cm)
    d: Effective depth (cm)
    col_location: 'interior', 'edge', 'corner'
    """
    props = {}
    
    # 1. Critical Section Dimensions
    if col_location == 'interior':
        # Rectangular Ring
        b1 = c1 + d
        b2 = c2 + d
        bo = 2 * (b1 + b2)
        
        # Centroid is at center
        c_AB = b1 / 2.0
        c_CD = b1 / 2.0
        
        # Jc Calculation (Interior)
        # Jc = (d*b1^3)/6 + (b1*d^3)/6 + (d*b2*b1^2)/2
        term1 = (d * b1**3) / 6.0
        term2 = (b1 * d**3) / 6.0
        term3 = (d * b2 * b1**2) / 2.0
        Jc = term1 + term2 + term3
        
        props.update({'type': 'Interior', 'b1': b1, 'b2': b2, 'bo': bo, 'Jc': Jc, 'c_AB': c_AB})

    elif col_location == 'edge':
        # U-Shaped Section (Assumes moment acts about axis perpendicular to c1)
        # Side legs = c1 + d/2 (L1)
        # Front face = c2 + d   (L2)
        
        L1 = c1 + (d / 2.0)
        L2 = c2 + d
        bo = (2 * L1) + L2
        
        # Centroid Calculation (from inner face of column)
        # Area moments about inner face (line connecting ends of legs)
        # Area_legs = 2 * (L1 * d) -> Centroid at -L1/2
        # Area_front = (L2 * d)    -> Centroid at 0
        area_legs = 2 * L1 * d
        area_front = L2 * d
        total_area = area_legs + area_front
        
        # x_bar distance from center of column face towards the span
        moment_area = (area_legs * (-L1 / 2.0)) + (area_front * 0)
        x_bar = moment_area / total_area # This will be negative (inside the span)
        
        c_AB = abs(x_bar)        # Distance to centroid from inner face
        c_CD = L1 - c_AB         # Distance to outer edge
        
        # Jc Calculation (Edge)
        # 1. Parallel to Moment Axis (Legs)
        # I_legs = 2 * [ (d*L1^3)/12 + (L1*d)*(dist_to_centroid)^2 ]
        dist_leg_center = (L1/2.0) - c_AB
        I_legs_own = (d * L1**3) / 12.0
        I_legs_shift = (L1 * d) * (dist_leg_center**2)
        J_legs = 2 * (I_legs_own + I_legs_shift)
        
        # 2. Perpendicular Face (Front)
        # I_front = (L2*d^3)/12 + (L2*d)*(c_AB)^2
        I_front_own = (L2 * d**3) / 12.0 # Generally small, often neglected but included here
        I_front_shift = (L2 * d) * (c_AB**2)
        J_front = I_front_own + I_front_shift
        
        Jc = J_legs + J_front
        
        props.update({'type': 'Edge', 'L1': L1, 'L2': L2, 'bo': bo, 'Jc': Jc, 'c_AB': c_AB, 'c_CD': c_CD})

    else: # Corner
        # L-Shaped Section
        L1 = c1 + (d/2.0)
        L2 = c2 + (d/2.0)
        bo = L1 + L2
        
        # Simplified Jc for Corner (Approx or detailed)
        # For DDM Corner usually critical in shear transfer, 
        # but simpler model: Centroid calculation
        area_1 = L1 * d
        area_2 = L2 * d
        total_area = area_1 + area_2
        
        x_bar = ((area_1 * L1/2) + (area_2 * 0)) / total_area
        c_AB = L1 - x_bar
        
        # Simplified Jc (Conservative)
        Jc = (d * L1**3)/3 + (L2 * d * x_bar**2) 
        
        props.update({'type': 'Corner', 'L1': L1, 'L2': L2, 'bo': bo, 'Jc': Jc, 'c_AB': c_AB})
        
    return props

# ========================================================
# 2. DETAILED FLEXURAL CALCULATION (EXISTING)
# ========================================================
def show_detailed_calculation(zone_name, res, inputs, coeff_pct, Mo_val):
    # Unpack Inputs
    Mu, b, h, cover, fc, fy, db, s, phi_bend = inputs
    b_cm = b * 100
    Mu_kgcm = Mu * 100
    
    st.markdown(f"""
    <div style="background-color:#f0f9ff; padding:15px; border-radius:10px; border-left: 5px solid #0369a1; margin-bottom: 20px;">
        <h4 style="margin:0; color:#0369a1;">🔍 Detailed Flexural Analysis: {zone_name}</h4>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.tabs(["1️⃣ Load & Geometry", "2️⃣ Steel Design", "3️⃣ Verification"])
    
    with c1:
        st.write("**1.1 Section Properties**")
        st.latex(f"h = {h} cm, \\quad C_c = {cover} cm, \\quad d_b = {db} mm")
        st.latex(f"d = h - C_c - d_b/2 = {res['d']:.2f} cm")
        
        st.write("**1.2 Design Moment**")
        st.latex(f"M_o = {Mo_val:,.0f} \\text{{ kg-m}}, \\quad \\text{{Coeff}} = {coeff_pct:.1f}\\%")
        st.latex(f"M_u = {Mo_val:,.0f} \\times {coeff_pct/100:.3f} = \\mathbf{{{Mu:,.0f}}} \\text{{ kg-m}}")

    with c2:
        st.write("**2.1 Required Strength ($R_n$)**")
        st.latex(r"R_n = \frac{M_u}{\phi b d^2}")
        st.latex(f"R_n = \\frac{{{Mu_kgcm:,.0f}}}{{{phi_bend} \\cdot {b_cm:.0f} \\cdot {res['d']:.2f}^2}} = \\mathbf{{{res['Rn']:.3f}}} \\text{{ ksc}}")
        
        st.write("**2.2 Reinforcement Ratio ($\\rho$)**")
        st.latex(f"\\rho_{{req}} = \\frac{{0.85 f_c'}}{{f_y}} \\left( 1 - \\sqrt{{1 - \\frac{{2 R_n}}{{0.85 f_c'}}}} \\right) = \\mathbf{{{res['rho_calc']:.5f}}}")
        
        st.write("**2.3 Steel Area ($A_s$)**")
        st.latex(f"A_{{s,req}} = \\rho b d = {res['As_req']:.2f} \\text{{ cm}}^2")

    with c3:
        st.write("**3.1 Provided Steel**")
        st.latex(f"\\text{{Use }} \\text{{DB}}{db} @ {s} \\text{{ cm}} \\rightarrow A_{{s,prov}} = \\mathbf{{{res['As_prov']:.2f}}} \\text{{ cm}}^2")
        
        st.write("**3.2 Capacity Check**")
        st.latex(f"\\phi M_n = {res['PhiMn']:,.0f} \\text{{ kg-m}}")
        if res['DC'] <= 1.0:
            st.success(f"✅ Safe (D/C = {res['DC']:.3f})")
        else:
            st.error(f"❌ Unsafe (D/C = {res['DC']:.3f})")

# ========================================================
# 3. INTERACTIVE DIRECTION CHECK (MAIN RENDERER)
# ========================================================
def render_interactive_direction(data, mat_props, axis_id, w_u, is_main_dir):
    # Unpack Props
    h_slab = float(mat_props['h_slab'])
    cover = float(mat_props['cover'])
    fc = float(mat_props['fc'])
    fy = float(mat_props['fy'])
    phi_bend = mat_props.get('phi', 0.90)        
    phi_shear = mat_props.get('phi_shear', 0.85) 
    cfg = mat_props.get('rebar_cfg', {})
    
    # Geometry from Inputs
    L_span = data['L_span']
    L_width = data.get('L_width', L_span)
    c_para = float(data['c_para']) # Dimension parallel to span
    c_perp = float(mat_props['cy']) if axis_id == "X" else float(mat_props['cx']) # Dimension perp
    
    # Adjust inputs for consistency
    # If checking X-axis: c_para = cx, c_perp = cy
    if axis_id == "X":
        c1 = float(mat_props['cx']) # Parallel to moment
        c2 = float(mat_props['cy']) # Perpendicular
    else:
        c1 = float(mat_props['cy'])
        c2 = float(mat_props['cx'])

    Mo = data['Mo']
    m_vals = data['M_vals']
    span_type_str = data.get('span_type_str', 'Interior')
    
    # Determine Column Location for Punching Logic
    # (Simplified: If interior span -> Interior Col, If End Span -> Edge Col)
    if "Interior" in span_type_str:
        col_loc_code = "interior"
    else:
        col_loc_code = "edge" # Assume Edge for end span in DDM context

    # 1. ANALYSIS HEADER
    st.markdown(f"### 1️⃣ Analysis: {axis_id}-Direction ({span_type_str})")
    with st.expander(f"📊 Load & Moment Distribution", expanded=False):
        st.write(f"**Total Static Moment ($M_o$):** {Mo:,.0f} kg-m")
        st.write(f"**Unbalanced Moment ($M_{{sc}}$):** {m_vals.get('M_unbal', 0):,.0f} kg-m")

    # 2. DETAILED PUNCHING SHEAR (THE CORE UPGRADE)
    st.markdown("---")
    st.markdown(f"### 2️⃣ Punching Shear Check (Detailed)")
    
    # A. PREPARE DATA
    d_avg = h_slab - cover - 1.6 # Average d (approx)
    
    # Calculate Properties using Helper
    p_props = calculate_punching_physics(c1, c2, d_avg, col_loc_code)
    
    # Calculate Gamma_v
    b1 = p_props.get('b1', p_props.get('L1', 0)) # Dimension parallel
    b2 = p_props.get('b2', p_props.get('L2', 0)) # Dimension perp
    
    if b1 > 0 and b2 > 0:
        gamma_f = 1.0 / (1.0 + (2.0/3.0) * (b1/b2)**0.5)
        gamma_v = 1.0 - gamma_f
    else:
        gamma_v = 0.4 # Default fallback
    
    # Loads
    area_panel = (L_span * L_width)
    area_col = (c1/100) * (c2/100)
    Vu = w_u * (area_panel - area_col) # kg
    Munbal = m_vals.get('M_unbal', 0) * 100 # kg-cm

    # B. DISPLAY CALCULATION
    col_p1, col_p2 = st.columns([1.2, 1])
    
    with col_p1:
        st.markdown("**A) Critical Section Geometry**")
        st.write(f"Column: {c1:.0f} x {c2:.0f} cm | Location: **{p_props['type']}**")
        st.write(f"Effective Depth ($d$): **{d_avg:.2f} cm**")
        
        # Display bo formula based on type
        if p_props['type'] == 'Interior':
            st.latex(r"b_o = 2(c_1 + d) + 2(c_2 + d)")
            st.latex(f"b_o = 2({c1}+{d_avg:.1f}) + 2({c2}+{d_avg:.1f}) = \\mathbf{{{p_props['bo']:.2f}}} \\; cm")
        elif p_props['type'] == 'Edge':
            st.latex(r"b_o = 2(c_1 + d/2) + (c_2 + d)")
            st.latex(f"b_o = 2({p_props['L1']:.1f}) + {p_props['L2']:.1f} = \\mathbf{{{p_props['bo']:.2f}}} \\; cm")
            
        st.markdown("**B) Section Properties ($J_c$)**")
        st.write("Polar Moment of Inertia of shear critical section:")
        st.latex(f"J_c = \\mathbf{{{p_props['Jc']:,.0f}}} \\; cm^4")
        st.latex(f"c_{{AB}} = {p_props['c_AB']:.2f} \\; cm \\quad (\\text{{Dist. to Centroid}})")
        
    with col_p2:
        st.markdown("**C) Shear Stress Calculation**")
        
        # Direct Shear
        v1 = Vu / (p_props['bo'] * d_avg)
        st.latex(r"v_{direct} = \frac{V_u}{b_o d}")
        st.latex(f"v_{{direct}} = \\frac{{{Vu:,.0f}}}{{{p_props['bo']:.1f} \\cdot {d_avg:.1f}}} = {v1:.2f} \\; ksc")
        
        # Moment Shear
        if Munbal > 0:
            st.latex(r"\gamma_v = 1 - \frac{1}{1 + \frac{2}{3}\sqrt{b_1/b_2}}")
            st.latex(f"\\gamma_v = {gamma_v:.3f}")
            
            v2 = (gamma_v * Munbal * p_props['c_AB']) / p_props['Jc']
            st.latex(r"v_{moment} = \frac{\gamma_v M_{sc} c_{AB}}{J_c}")
            st.latex(f"v_{{moment}} = \\frac{{{gamma_v:.3f} \\cdot {Munbal/100:,.0f} \\cdot 100 \\cdot {p_props['c_AB']:.1f}}}{{{p_props['Jc']:,.0f}}} = {v2:.2f} \\; ksc")
        else:
            v2 = 0
            st.info("Balanced condition: $v_{moment} \\approx 0$")

        # Total
        v_max = v1 + v2
        st.markdown("---")
        st.latex(f"v_{{max}} = {v1:.2f} + {v2:.2f} = \\mathbf{{{v_max:.2f}}} \\; ksc")

    # C. CHECK CAPACITY
    st.markdown("#### **Verification (ACI 318)**")
    
    # Capacity Formula
    phi_vc = phi_shear * 1.06 * (fc**0.5) # Basic formula
    # (Ideally should check 3 formulas, but using the governing one for slabs usually)
    
    res_col1, res_col2 = st.columns(2)
    with res_col1:
        st.write("Allowable Shear Strength ($\\phi v_c$):")
        st.latex(r"\phi v_c = \phi \cdot 1.06 \sqrt{f_c'}")
        st.latex(f"\\phi v_c = {phi_shear} \\cdot 1.06 \\cdot \\sqrt{{{fc}}} = \\mathbf{{{phi_vc:.2f}}} \\; ksc")
    
    with res_col2:
        ratio = v_max / phi_vc
        st.write(f"**D/C Ratio:** {ratio:.2f}")
        if v_max <= phi_vc:
            st.success(f"✅ **PASS** (Safe)")
        else:
            st.error(f"❌ **FAIL** (Reinforcement or Thickness Required)")
            req_thick = d_avg * (v_max/phi_vc) + cover + 1.6
            st.caption(f"Suggestion: Increase slab thickness to > {req_thick:.0f} cm")

    # 3. REINFORCEMENT
    st.markdown("---")
    st.markdown("### 3️⃣ Reinforcement Design")
    
    # Map Config
    d_cst, s_cst = cfg.get('cs_top_db', 12), cfg.get('cs_top_spa', 20)
    d_csb, s_csb = cfg.get('cs_bot_db', 12), cfg.get('cs_bot_spa', 20)
    d_mst, s_mst = cfg.get('ms_top_db', 12), cfg.get('ms_top_spa', 20)
    d_msb, s_msb = cfg.get('ms_bot_db', 12), cfg.get('ms_bot_spa', 20)
    
    zones = [
        {"Label": "Col Strip - Top (-)", "Mu": m_vals['M_cs_neg'], "b": data.get('L_width', L_span)/2, "db": d_cst, "s": s_cst},
        {"Label": "Col Strip - Bot (+)", "Mu": m_vals['M_cs_pos'], "b": data.get('L_width', L_span)/2, "db": d_csb, "s": s_csb},
        {"Label": "Mid Strip - Top (-)", "Mu": m_vals['M_ms_neg'], "b": data.get('L_width', L_span)/2, "db": d_mst, "s": s_mst},
        {"Label": "Mid Strip - Bot (+)", "Mu": m_vals['M_ms_pos'], "b": data.get('L_width', L_span)/2, "db": d_msb, "s": s_msb},
    ]
    
    results = []
    for z in zones:
        res = logic.calc_rebar_logic(
            z['Mu'], z['b'], z['db'], z['s'], 
            h_slab, cover, fc, fy, is_main_dir, phi_bend
        )
        res.update(z)
        results.append(res)
    
    df_res = pd.DataFrame(results)[["Label", "Mu", "As_req", "As_prov", "DC", "Note"]]
    st.dataframe(df_res.style.background_gradient(subset=["DC"], cmap="RdYlGn_r", vmin=0, vmax=1.2), use_container_width=True, hide_index=True)
    
    st.markdown("#### 🔍 Select Zone for Detailed Calculation")
    sel_zone = st.selectbox(f"Show details for ({axis_id}):", [z['Label'] for z in zones], key=f"sel_{axis_id}")
    
    target = next(z for z in results if z['Label'] == sel_zone)
    raw_inputs = (target['Mu'], target['b'], h_slab, cover, fc, fy, target['db'], target['s'], phi_bend)
    pct_val = (target['Mu'] / Mo * 100) if Mo > 0 else 0
    
    show_detailed_calculation(sel_zone, target, raw_inputs, pct_val, Mo)

    if HAS_PLOTS:
        st.markdown("---")
        t1, t2 = st.tabs(["📉 Moment Diagram", "🏗️ Rebar Detailing"])
        rebar_map = {
            "CS_Top": f"DB{d_cst}@{s_cst}", "CS_Bot": f"DB{d_csb}@{s_csb}",
            "MS_Top": f"DB{d_mst}@{s_mst}", "MS_Bot": f"DB{d_msb}@{s_msb}"
        }
        with t1: st.pyplot(ddm_plots.plot_ddm_moment(L_span, c_para/100, m_vals))
        with t2: st.pyplot(ddm_plots.plot_rebar_detailing(L_span, h_slab, c_para, rebar_map, axis_id))

# ========================================================
# 4. MAIN ENTRY POINT
# ========================================================
def render_dual(data_x, data_y, mat_props, w_u):
    st.markdown("## 🏗️ RC Slab Design (DDM Analysis)")
    
    # Show Config Summary
    with st.expander("⚙️ Span Continuity Settings", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            type_x = st.radio("Span Condition (X-Axis):", ["Interior Span", "End Span - Edge Beam", "End Span - No Beam"], key="sx")
            data_x = logic.update_moments_based_on_config(data_x, type_x)
        with c2:
            type_y = st.radio("Span Condition (Y-Axis):", ["Interior Span", "End Span - Edge Beam", "End Span - No Beam"], key="sy")
            data_y = logic.update_moments_based_on_config(data_y, type_y)

    tab_x, tab_y = st.tabs(["➡️ X-Direction Check", "⬆️ Y-Direction Check"])
    with tab_x: render_interactive_direction(data_x, mat_props, "X", w_u, True)
    with tab_y: render_interactive_direction(data_y, mat_props, "Y", w_u, False)
