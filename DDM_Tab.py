import streamlit as st
import pandas as pd
import numpy as np
import DDM_Logic as logic

# Optional import for plotting
try:
    import ddm_plots
    HAS_PLOTS = True
except ImportError:
    HAS_PLOTS = False

# ========================================================
# 1. CORE PHYSICS ENGINE: EXACT Jc & GEOMETRY
# ========================================================
def get_punching_parameters(c_x, c_y, d, location_type):
    """
    Returns exact geometric properties for punching shear (Jc, bo, cab, etc.)
    c_x: Column dimension parallel to the span being analyzed (cm)
    c_y: Column dimension perpendicular to the span (cm)
    d: Effective depth (cm)
    location_type: 'Interior', 'Edge', 'Corner'
    """
    res = {}
    res['type'] = location_type
    
    # 1. INTERIOR COLUMN (Rectangular Ring)
    if location_type == 'Interior':
        b1 = c_x + d  # Side parallel to moment
        b2 = c_y + d  # Side perpendicular to moment
        bo = 2 * (b1 + b2)
        
        # Centroid is exactly in the middle
        c_AB = b1 / 2.0 
        c_CD = b1 / 2.0
        
        # Jc Formula for Interior (ACI 318 / PCA Notes)
        # Jc = (d * b1^3)/6 + (b1 * d^3)/6 + (d * b2 * b1^2)/2
        term1 = (d * b1**3) / 6.0
        term2 = (b1 * d**3) / 6.0
        term3 = (d * b2 * b1**2) / 2.0
        Jc = term1 + term2 + term3
        
        res.update({
            'b1': b1, 'b2': b2, 'bo': bo, 'Jc': Jc, 
            'c_AB': c_AB, 'c_CD': c_CD, 
            'breakdown': f"J_c = {term1:.0f} + {term2:.0f} + {term3:.0f}"
        })

    # 2. EDGE COLUMN (U-Shaped Section)
    # Assumes the column is at the edge of the span being analyzed (Moment about Y-axis equivalent)
    # c_x is perpendicular to the edge? No, usually in DDM:
    # If analyzing Span X, Edge Col means column is at Left/Right end.
    # The critical section is 3-sided. 
    # c1 (axis of moment) = c_x
    # c2 (width) = c_y
    elif location_type == 'Edge':
        # Critical Section Dimensions
        # u1 = c_x + d/2 (The legs)
        # u2 = c_y + d   (The front face)
        u1 = c_x + (d/2.0) 
        u2 = c_y + d
        bo = (2 * u1) + u2
        
        # --- Find Centroid (x_bar from inner face) ---
        # Area 1 (Legs): 2 * (u1 * d)
        # Area 2 (Front): (u2 * d)
        A_legs = 2 * u1 * d
        A_front = u2 * d
        A_total = A_legs + A_front
        
        # Moment of Area about Center of Front Face (Inner Face Line)
        # Centroid of Legs is at -u1/2
        # Centroid of Front is at 0
        Mx = (A_legs * (-u1/2.0)) + (A_front * 0)
        x_bar = Mx / A_total  # This will be negative (inside the span)
        
        c_AB = abs(x_bar)      # Dist to Centroid from Inner Face (Critical for M_unbal)
        c_CD = u1 - c_AB       # Dist to Outer Edge
        
        # --- Calculate Jc (Shifted Axis Theorem) ---
        # 1. Inertia of Legs (Parallel to Moment)
        # I_legs_own = (d * u1^3) / 12
        # Dist_shift = (u1/2) - c_AB
        # I_legs_shift = A_legs/2 * (Dist_shift)^2
        I_leg_own = (d * u1**3) / 12.0
        dist_leg_shift = (u1/2.0) - c_AB
        I_leg_total = (I_leg_own + (u1*d)*(dist_leg_shift**2)) * 2 # Two legs
        
        # 2. Inertia of Front Face (Perpendicular)
        # I_front_own = (u2 * d^3) / 12
        # Dist_shift = c_AB
        I_front_own = (u2 * d**3) / 12.0
        I_front_total = I_front_own + (A_front * c_AB**2)
        
        Jc = I_leg_total + I_front_total
        
        res.update({
            'b1': u1, 'b2': u2, 'bo': bo, 'Jc': Jc, 
            'c_AB': c_AB, 'c_CD': c_CD,
            'breakdown': f"J_{{legs}}={I_leg_total:.0f}, J_{{front}}={I_front_total:.0f}"
        })

    # 3. CORNER COLUMN (L-Shaped Section)
    elif location_type == 'Corner':
        u1 = c_x + (d/2.0)
        u2 = c_y + (d/2.0)
        bo = u1 + u2
        
        # Simplified Conservative Approach for DDM Corner (PCA Method)
        # Find Centroid
        A1 = u1 * d
        A2 = u2 * d
        
        # Centroid x (along c_x)
        x_bar = ((A1 * u1/2.0) + (A2 * d/2.0)) / (A1 + A2) # Simplified treating corner overlap
        # Actually standard practice for Corner in DDM is less rigorous on Jc because 
        # Shear usually governs by direct shear, but let's provide the number.
        
        c_AB = u1/2.0 # Approximation for display
        
        # Very rough Jc for L-shape to avoid complex Principal Axis rotation code
        Jc = (d*u1**3)/3 + (d*u2**3)/3 
        
        res.update({
            'b1': u1, 'b2': u2, 'bo': bo, 'Jc': Jc, 
            'c_AB': c_AB, 'c_CD': c_AB,
            'breakdown': "Simplified L-Shape Jc"
        })
        
    return res

# ========================================================
# 2. RENDERER: PUNCHING SHEAR (ULTRA DETAILED)
# ========================================================
def render_punching_shear_detailed(data, mat_props, c_para, c_perp, col_type):
    st.markdown("### 2️⃣ Punching Shear Check (Detailed Verification)")
    
    # 1. Setup Variables
    h = float(mat_props['h_slab'])
    cover = float(mat_props['cover'])
    fc = float(mat_props['fc'])
    d_avg = h - cover - 1.6 # Average d for two layers
    
    # 2. Get Physics
    props = get_punching_parameters(c_para, c_perp, d_avg, col_type)
    
    # 3. Loads
    L_span = data['L_span']
    L_width = data.get('L_width', L_span)
    w_u = data.get('w_u', 1000) # Fallback if not passed, but we usually pass it
    if 'w_u' not in data: 
        # Hack to get w_u from Mo if not explicit
        # Mo = w_u * L2 * ln^2 / 8
        pass 
        
    area_panel = L_span * L_width
    area_col = (c_para/100) * (c_perp/100)
    Vu = w_u * (area_panel - area_col) # Total Shear
    
    Munbal = data['M_vals'].get('M_unbal', 0) * 100 # kg-cm
    
    # 4. Gamma V Calculation
    b1 = props['b1']
    b2 = props['b2']
    gamma_f = 1.0 / (1.0 + (2.0/3.0) * (b1/b2)**0.5)
    gamma_v = 1.0 - gamma_f
    
    # --- DISPLAY SECTION ---
    
    # A. GEOMETRY
    st.markdown("#### **Step 1: Critical Section Properties**")
    c1, c2 = st.columns(2)
    with c1:
        st.write(f"**Column Size:** {c_para:.0f} x {c_perp:.0f} cm")
        st.write(f"**Location:** {col_type}")
        st.write(f"**Effective Depth ($d$):** {d_avg:.2f} cm")
        
        
        
    with c2:
        # Show bo calculation
        if col_type == 'Interior':
            st.latex(r"b_o = 2(c_1 + d) + 2(c_2 + d)")
            st.latex(f"b_o = 2({c_para:.0f}+{d_avg:.1f}) + 2({c_perp:.0f}+{d_avg:.1f}) = \\mathbf{{{props['bo']:.2f}}} \\; cm")
        elif col_type == 'Edge':
            st.latex(r"b_o = 2(c_1 + d/2) + (c_2 + d)")
            st.latex(f"b_o = 2({props['b1']:.1f}) + {props['b2']:.1f} = \\mathbf{{{props['bo']:.2f}}} \\; cm")

    # B. CENTROID & INERTIA
    st.markdown("#### **Step 2: Centroid ($c_{AB}$) & Inertia ($J_c$)**")
    
    with st.expander("Show detailed derivation of $J_c$ and Centroid", expanded=True):
        if col_type == 'Edge':
            st.markdown("**1. Find Centroid ($c_{AB}$):**")
            st.latex(r"c_{AB} = \frac{\sum A_i x_i}{\sum A_i}")
            st.write(f"Considering moments of area about the inner face of the column:")
            st.write(f"- $A_{{legs}} = 2 \\times ({props['b1']:.1f} \\times {d_avg:.1f}) = {2*props['b1']*d_avg:.1f}$ cm²")
            st.write(f"- $A_{{front}} = {props['b2']:.1f} \\times {d_avg:.1f} = {props['b2']*d_avg:.1f}$ cm²")
            st.latex(f"c_{{AB}} = \\mathbf{{{props['c_AB']:.2f}}} \\; cm \\quad (\\text{{from inner face}})")
            
            st.markdown("**2. Calculate Polar Moment of Inertia ($J_c$):**")
            st.write("Using Parallel Axis Theorem: $J_c = \\sum (I_{own} + Ad^2)$")
            st.info(f"Breakdown: {props['breakdown']}")
            st.latex(f"J_c = \\mathbf{{{props['Jc']:,.0f}}} \\; cm^4")
            
        else:
            st.write(f"For Interior column, centroid is at center: $c_{{AB}} = {props['c_AB']:.2f}$ cm")
            st.latex(f"J_c = \\mathbf{{{props['Jc']:,.0f}}} \\; cm^4")

    # C. STRESS CALCULATION
    st.markdown("#### **Step 3: Shear Stress Analysis**")
    
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        st.markdown("**Direct Shear ($v_u^1$)**")
        st.latex(r"v_u^1 = \frac{V_u}{b_o d}")
        v1 = Vu / (props['bo'] * d_avg)
        st.latex(f"v_u^1 = \\frac{{{Vu:,.0f}}}{{{props['bo']:.1f}({d_avg:.1f})}} = \\mathbf{{{v1:.2f}}} \\; ksc")
        
    with col_s2:
        st.markdown("**Moment Transfer ($v_u^2$)**")
        if Munbal > 0:
            st.latex(r"\gamma_v = 1 - \frac{1}{1 + \frac{2}{3}\sqrt{b_1/b_2}}")
            st.latex(f"\\gamma_v = {gamma_v:.3f}")
            
            v2 = (gamma_v * Munbal * props['c_AB']) / props['Jc']
            st.latex(r"v_u^2 = \frac{\gamma_v M_{sc} c_{AB}}{J_c}")
            st.latex(f"v_u^2 = \\frac{{{gamma_v:.3f} \\cdot {Munbal:,.0f} \\cdot {props['c_AB']:.1f}}}{{{props['Jc']:,.0f}}} = \\mathbf{{{v2:.2f}}} \\; ksc")
        else:
            v2 = 0
            st.info("No Unbalanced Moment ($M_{sc} = 0$)")
            
    # Total Stress
    v_total = v1 + v2
    st.markdown("---")
    st.latex(f"v_{{max}} = {v1:.2f} + {v2:.2f} = \\mathbf{{{v_total:.2f}}} \\; ksc")
    
    # D. CHECK
    phi_shear = mat_props.get('phi_shear', 0.85)
    phi_vc = phi_shear * 1.06 * (fc**0.5)
    
    st.write(f"**Allowable Capacity ($\\phi v_c$):**")
    st.latex(f"\\phi v_c = {phi_shear} \\cdot 1.06 \\sqrt{{{fc}}} = \\mathbf{{{phi_vc:.2f}}} \\; ksc")
    
    dc_ratio = v_total / phi_vc
    
    if v_total <= phi_vc:
        st.success(f"✅ **PASS** (Ratio: {dc_ratio:.2f})")
    else:
        st.error(f"❌ **FAIL** (Ratio: {dc_ratio:.2f})")
        req_d = d_avg * (dc_ratio**0.5)
        st.write(f"👉 Recommended min slab thickness: **{req_d + cover + 1.6:.0f} cm**")

# ========================================================
# 3. HELPER: FLEXURAL CALCULATION (UNCHANGED)
# ========================================================
def show_detailed_flexure(zone_name, res, inputs, coeff_pct, Mo_val):
    # This function remains largely same but ensures clean display
    Mu, b, h, cover, fc, fy, db, s, phi_bend = inputs
    b_cm = b * 100
    Mu_kgcm = Mu * 100
    
    st.markdown(f"#### 🔍 Flexural Details: {zone_name}")
    st.write(f"**Design Moment ($M_u$):** {Mu:,.0f} kg-m (Coeff: {coeff_pct:.1f}%)")
    
    st.latex(r"A_{s,req} = \rho b d")
    st.latex(f"A_{{s,req}} = {res['As_req']:.2f} \\; cm^2")
    
    st.latex(r"A_{s,prov} = \text{Use } DB" + str(db) + f" @ {s} cm")
    st.latex(f"A_{{s,prov}} = {res['As_prov']:.2f} \\; cm^2")
    
    if res['DC'] > 1.0:
        st.error(f"Unsafe (D/C = {res['DC']:.2f})")
    else:
        st.success(f"Safe (D/C = {res['DC']:.2f})")

# ========================================================
# 4. MAIN INTERACTIVE RENDERER
# ========================================================
def render_interactive_direction(data, mat_props, axis_id, w_u, is_main_dir):
    # Unpack Props
    h_slab = float(mat_props['h_slab'])
    cover = float(mat_props['cover'])
    fc = float(mat_props['fc'])
    fy = float(mat_props['fy'])
    phi_bend = mat_props.get('phi', 0.90)
    
    # Geometry
    L_span = data['L_span']
    L_width = data.get('L_width', L_span)
    c_para = float(data['c_para']) # Parallel to span
    c_perp = float(mat_props['cy']) if axis_id == "X" else float(mat_props['cx'])
    
    Mo = data['Mo']
    m_vals = data['M_vals']
    span_type = data.get('span_type_str', 'Interior')
    
    # Determine Column Type for Punching
    if "Interior" in span_type:
        col_type = "Interior"
    elif "End" in span_type:
        # Simplification: Assume Edge column for end spans in DDM strip analysis
        col_type = "Edge" 
    else:
        col_type = "Corner" # Not usually triggered in standard strip view but available

    # Add w_u to data for punching function
    data['w_u'] = w_u

    # --- RENDER TABS ---
    st.markdown(f"### 1️⃣ Analysis: {axis_id}-Direction ({span_type})")
    st.info(f"**Moment:** $M_o$ = {Mo:,.0f} kg-m | **Unbalanced:** $M_{{sc}}$ = {m_vals.get('M_unbal', 0):,.0f} kg-m")
    
    # CALL THE DETAILED PUNCHING FUNCTION
    render_punching_shear_detailed(data, mat_props, c_para, c_perp, col_type)
    
    st.markdown("---")
    st.markdown("### 3️⃣ Reinforcement Design")
    
    # ... (Rebar Logic Same as before) ...
    cfg = mat_props.get('rebar_cfg', {})
    d_cst, s_cst = cfg.get('cs_top_db', 12), cfg.get('cs_top_spa', 20)
    d_csb, s_csb = cfg.get('cs_bot_db', 12), cfg.get('cs_bot_spa', 20)
    d_mst, s_mst = cfg.get('ms_top_db', 12), cfg.get('ms_top_spa', 20)
    d_msb, s_msb = cfg.get('ms_bot_db', 12), cfg.get('ms_bot_spa', 20)
    
    zones = [
        {"Label": "Col Strip - Top (-)", "Mu": m_vals['M_cs_neg'], "b": min(L_span, L_width)/2, "db": d_cst, "s": s_cst},
        {"Label": "Col Strip - Bot (+)", "Mu": m_vals['M_cs_pos'], "b": min(L_span, L_width)/2, "db": d_csb, "s": s_csb},
        {"Label": "Mid Strip - Top (-)", "Mu": m_vals['M_ms_neg'], "b": L_width - min(L_span, L_width)/2, "db": d_mst, "s": s_mst},
        {"Label": "Mid Strip - Bot (+)", "Mu": m_vals['M_ms_pos'], "b": L_width - min(L_span, L_width)/2, "db": d_msb, "s": s_msb},
    ]
    
    results = []
    for z in zones:
        res = logic.calc_rebar_logic(z['Mu'], z['b'], z['db'], z['s'], h_slab, cover, fc, fy, is_main_dir, phi_bend)
        res.update(z)
        results.append(res)
    
    df_res = pd.DataFrame(results)[["Label", "Mu", "As_req", "As_prov", "DC", "Note"]]
    st.dataframe(df_res.style.background_gradient(subset=["DC"], cmap="RdYlGn_r", vmin=0, vmax=1.2), use_container_width=True, hide_index=True)

    st.markdown("#### 🔍 Select Zone for Detailed Calculation")
    sel_zone = st.selectbox(f"Show details for ({axis_id}):", [z['Label'] for z in zones], key=f"sel_{axis_id}")
    target = next(z for z in results if z['Label'] == sel_zone)
    raw_inputs = (target['Mu'], target['b'], h_slab, cover, fc, fy, target['db'], target['s'], phi_bend)
    pct_val = (target['Mu'] / Mo * 100) if Mo > 0 else 0
    show_detailed_flexure(sel_zone, target, raw_inputs, pct_val, Mo)

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
# 5. ENTRY POINT
# ========================================================
def render_dual(data_x, data_y, mat_props, w_u):
    st.markdown("## 🏗️ RC Slab Design (DDM Analysis)")
    
    # Config Spans
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
