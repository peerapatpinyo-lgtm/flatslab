import streamlit as st
import pandas as pd
import numpy as np
import math

# Try importing helper functions, provide fallback if missing
try:
    from calculations import check_min_reinforcement, check_long_term_deflection
except ImportError:
    # Dummy Fallback functions to prevent crash if file is missing
    def check_min_reinforcement(h): return {'As_min': 0.0018*100*h}
    def check_long_term_deflection(*args): return {'status': 'N/A', 'Delta_Total': 0.0, 'Limit_240': 0.0, 'Delta_Immediate':0, 'Delta_LongTerm':0}

# ==========================================
# 1. VISUAL STYLING (CSS)
# ==========================================
def inject_custom_css():
    st.markdown("""
    <style>
        .report-container { font-family: 'Segoe UI', Tahoma, Helvetica, sans-serif; }
        
        /* Main Container */
        .step-container {
            background-color: #ffffff;
            border-radius: 8px;
            padding: 25px;
            margin-bottom: 25px;
            border: 1px solid #e0e0e0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        
        /* Headers */
        .step-title {
            font-size: 1.3rem;
            font-weight: 700;
            color: #0d47a1; /* Strong Blue */
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e3f2fd;
            display: flex;
            align-items: center;
        }
        
        .step-num {
            background-color: #0d47a1;
            color: white;
            width: 32px;
            height: 32px;
            border-radius: 50%;
            text-align: center;
            line-height: 32px;
            font-size: 1rem;
            margin-right: 12px;
            font-weight: bold;
        }
        
        .sub-header {
            font-weight: 700;
            color: #37474f;
            margin-top: 20px;
            margin-bottom: 8px;
            font-size: 1rem;
            border-left: 4px solid #b0bec5;
            padding-left: 10px;
        }

        .meaning-text {
            font-size: 0.95rem;
            color: #546e7a;
            font-style: italic;
            margin-bottom: 15px;
            background-color: #eceff1;
            padding: 10px;
            border-radius: 4px;
            border-left: 3px solid #b0bec5;
        }

        .calc-result-box {
            background-color: #e1f5fe;
            color: #01579b;
            padding: 12px;
            border-radius: 6px;
            text-align: center;
            font-weight: bold;
            font-size: 1.1rem;
            border: 1px solid #81d4fa;
            margin-top: 10px;
        }
        
        .verdict-box {
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            font-weight: bold;
            border: 1px solid #ddd;
        }
        .pass { background-color: #e8f5e9; color: #1b5e20; border-color: #a5d6a7; }
        .fail { background-color: #ffebee; color: #b71c1c; border-color: #ef9a9a; }
        
        hr { margin: 25px 0; border: 0; border-top: 1px solid #eceff1; }
    </style>
    """, unsafe_allow_html=True)

def render_step_header(number, text):
    st.markdown(f'<div class="step-title"><div class="step-num">{number}</div>{text}</div>', unsafe_allow_html=True)

# ==========================================
# 2. DETAILED RENDERERS (ENGLISH ONLY)
# ==========================================

def render_punching_detailed(res, mat_props, loads, Lx, Ly, label):
    """
    Render detailed punching shear calculation with FULL English explanation and math.
    """
    if not res:
        st.error(f"No data available for {label}")
        return

    st.markdown(f"#### 📍 Section: {label}")
    
    # --- 1. Extract Basic Material & Geometry ---
    fc = mat_props['fc']
    c1 = mat_props.get('cx', 50.0) 
    c2 = mat_props.get('cy', 50.0)
    cover = mat_props.get('cover', 2.5)
    
    # Thickness logic
    h_slab_base = mat_props['h_slab']
    is_drop_check = "Drop" in label or "Face" in label
    if mat_props.get('has_drop') and is_drop_check and "Panel Edge" not in label:
        h_total = h_slab_base + mat_props.get('h_drop', 0)
    else:
        h_total = h_slab_base

    # Effective Depth (d)
    d = h_total - cover - 1.0 
    
    # --- 2. Extract Analysis Results & Alpha ---
    beta = max(c1,c2)/min(c1,c2)
    alpha_s = mat_props.get('alpha_s', 40) # 40=Int, 30=Edge, 20=Corner
    sqrt_fc = math.sqrt(fc)
    
    # ==========================================
    # 🔴 LOGIC: Dynamic b0 & English Explanation
    # ==========================================
    if alpha_s >= 40:
        # --- INTERIOR ---
        pos_title = "Interior Column Condition"
        pos_desc = "The critical section is continuous on all 4 sides."
        b0_latex_eq = r"b_0 = 2(c_1 + d) + 2(c_2 + d)"
        b0_latex_sub = fr"b_0 = 2({c1} + {d:.1f}) + 2({c2} + {d:.1f})"
        b0_calc = 2*(c1 + d) + 2*(c2 + d)
        
    elif alpha_s >= 30:
        # --- EDGE ---
        pos_title = "Edge Column Condition"
        pos_desc = "Shear resistance is effective on 3 sides only (1 side is exterior)."
        b0_latex_eq = r"b_0 = 2(c_1 + d/2) + (c_2 + d)"
        b0_latex_sub = fr"b_0 = 2({c1} + {d/2:.1f}) + ({c2} + {d:.1f})"
        b0_calc = 2*(c1 + d/2) + (c2 + d)
        
    else:
        # --- CORNER ---
        pos_title = "Corner Column Condition"
        pos_desc = "At the corner, the slab exists only on the inner sides. Thus, shear resistance is limited to **2 sides** (L-shape). The outer sides have no concrete."
        b0_latex_eq = r"b_0 = (c_1 + d/2) + (c_2 + d/2)"
        b0_latex_sub = fr"b_0 = ({c1} + {d/2:.1f}) + ({c2} + {d/2:.1f})"
        b0_calc = (c1 + d/2) + (c2 + d/2)
        
    b0 = b0_calc

    # --- Step 1: Geometry & Parameters ---
    with st.container():
        st.markdown('<div class="step-container">', unsafe_allow_html=True)
        render_step_header(1, "Geometry & Parameters")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<div class="sub-header">A. Effective Depth (d)</div>', unsafe_allow_html=True)
            st.write("Depth from compression face to reinforcement centroid.")
            st.latex(r"d = h - \text{Cover} - \phi_{bar}/2")
            st.latex(fr"d = {h_total:.0f} - {cover:.1f} - 1.0 = \mathbf{{{d:.2f}}} \text{{ cm}}")
            
            st.markdown('<div class="sub-header">B. Concrete Strength</div>', unsafe_allow_html=True)
            st.latex(fr"\sqrt{{f'_c}} = \sqrt{{{fc}}} = \mathbf{{{sqrt_fc:.2f}}} \text{{ ksc}}")

        with col2:
            st.markdown('<div class="sub-header">C. Critical Perimeter (b0)</div>', unsafe_allow_html=True)
            st.write(f"**Type:** {pos_title} ($\alpha_s={alpha_s}$)")
            st.info(f"ℹ️ {pos_desc}")
            
            st.latex(b0_latex_eq)
            st.latex(b0_latex_sub)
            st.markdown(f"<div class='calc-result-box'>b0 = {b0:.2f} cm</div>", unsafe_allow_html=True)
            
            st.markdown('<div class="sub-header">D. Shape Factor</div>', unsafe_allow_html=True)
            st.latex(fr"\beta = \frac{{\text{{Long Side}}}}{{\text{{Short Side}}}} = \frac{{{max(c1,c2)}}}{{{min(c1,c2)}}} = {beta:.2f}")
            
        st.markdown('</div>', unsafe_allow_html=True)

    # --- Step 2: Nominal Capacity ---
    with st.container():
        st.markdown('<div class="step-container">', unsafe_allow_html=True)
        render_step_header(2, "Nominal Shear Capacity ($V_c$)")
        st.write("The capacity is governed by the minimum of the three ACI/EIT formulas:")
        
        eq1, eq2, eq3 = st.columns(3)
        
        # --- Eq 1 ---
        with eq1:
            st.markdown("**1. Rectangularity Effect**")
            st.latex(r"V_{c1} = 0.53 \left(1 + \frac{2}{\beta}\right) \sqrt{f'_c} b_0 d")
            term_beta = 1 + (2/beta)
            val_vc1 = 0.53 * term_beta * sqrt_fc * b0 * d
            st.latex(fr"= 0.53 ({term_beta:.2f}) ({sqrt_fc:.2f}) ({b0:.0f}) ({d:.1f})")
            st.markdown(f"<div class='calc-result-box'>{val_vc1:,.0f} kg</div>", unsafe_allow_html=True)

        # --- Eq 2 ---
        with eq2:
            st.markdown("**2. Size Effect**")
            st.latex(r"V_{c2} = 0.27 \left(\frac{\alpha_s d}{b_0} + 2\right) \sqrt{f'_c} b_0 d") 
            term_peri_val = (alpha_s * d / b0) + 2
            val_vc2 = 0.27 * term_peri_val * sqrt_fc * b0 * d 
            st.latex(fr"= 0.27 ({term_peri_val:.2f}) ({sqrt_fc:.2f}) ({b0:.0f}) ({d:.1f})")
            st.markdown(f"<div class='calc-result-box'>{val_vc2:,.0f} kg</div>", unsafe_allow_html=True)

        # --- Eq 3 ---
        with eq3:
            st.markdown("**3. Basic Limit**")
            st.latex(r"V_{c3} = 1.06 \sqrt{f'_c} b_0 d")
            val_vc3 = 1.06 * sqrt_fc * b0 * d
            st.latex(fr"= 1.06 ({sqrt_fc:.2f}) ({b0:.0f}) ({d:.1f})")
            st.markdown(f"<div class='calc-result-box'>{val_vc3:,.0f} kg</div>", unsafe_allow_html=True)
        
        st.markdown("---")
        vc_min = min(val_vc1, val_vc2, val_vc3)
        st.success(f"📌 **Governing Capacity ($V_c$):** {vc_min:,.0f} kg")
        st.markdown('</div>', unsafe_allow_html=True)

    # --- Step 3: Demand Calculation (Detailed Vu) ---
    with st.container():
        st.markdown('<div class="step-container">', unsafe_allow_html=True)
        render_step_header(3, "Shear Demand Calculation ($V_u$)")
        st.markdown("""
        <div class="meaning-text">
        This section demonstrates how <b>Vu</b> is derived using the <b>Tributary Area Method</b>.
        <br>Formula: Total Factored Load on the tributary area minus the load inside the critical perimeter.
        </div>
        """, unsafe_allow_html=True)

        # 1. Loads
        f_dl = mat_props.get('factor_dl', 1.4)
        f_ll = mat_props.get('factor_ll', 1.7)
        h_m = h_total / 100.0
        w_sw = h_m * 2400
        
        # 2. Factored Load (wu)
        wu_val = (f_dl * (w_sw + loads['SDL'])) + (f_ll * loads['LL'])

        # 3. Areas
        area_trib = Lx * Ly
        # Critical area approximation: (c1+d)(c2+d) converted to m2
        b1_m = (c1 + d) / 100.0
        b2_m = (c2 + d) / 100.0
        area_crit = b1_m * b2_m 
        
        # 4. Vu Calculation
        vu_calc = wu_val * (area_trib - area_crit)
        
        # Use value from result if available (to match exact input), otherwise use calc
        vu_display = res.get('Vu', vu_calc)

        col_L, col_R = st.columns(2)
        
        with col_L:
            st.markdown('<div class="sub-header">A. Factored Load ($w_u$)</div>', unsafe_allow_html=True)
            st.latex(fr"w_u = {f_dl:.1f}(DL) + {f_ll:.1f}(LL)")
            st.latex(fr"w_u = {f_dl:.1f}({w_sw+loads['SDL']:.0f}) + {f_ll:.1f}({loads['LL']:.0f})")
            st.markdown(f"<div class='calc-result-box'>wu = {wu_val:,.0f} kg/m²</div>", unsafe_allow_html=True)

            st.markdown('<div class="sub-header">B. Areas</div>', unsafe_allow_html=True)
            st.write(f"**Tributary Area ($A_{{trib}}$):** $L_x \\times L_y$")
            st.latex(fr"= {Lx:.2f} \times {Ly:.2f} = {area_trib:.2f} \text{{ m}}^2")
            st.write(f"**Critical Area ($A_{{crit}}$):** $(c_1+d)(c_2+d)$")
            st.latex(fr"= {b1_m:.2f} \times {b2_m:.2f} = {area_crit:.3f} \text{{ m}}^2")

        with col_R:
            st.markdown('<div class="sub-header">C. Factored Shear Force ($V_u$)</div>', unsafe_allow_html=True)
            st.write("**Calculation Formula:**")
            st.latex(r"V_u = w_u \times (A_{trib} - A_{crit})")
            
            st.write("**Substitute:**")
            st.latex(fr"V_u = {wu_val:,.0f} \times ({area_trib:.2f} - {area_crit:.3f})")
            st.latex(fr"V_u = {wu_val:,.0f} \times {area_trib - area_crit:.2f}")
            
            st.markdown(f"""
            <div class="calc-result-box" style="font-size:1.6rem; background-color:#fff8e1; color:#ff6f00; border-color:#ffe082">
            Vu = {vu_display:,.0f} kg
            </div>
            """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    # --- Step 4: Design Check ---
    with st.container():
        st.markdown('<div class="step-container">', unsafe_allow_html=True)
        render_step_header(4, "Design Verdict")
        
        phi = mat_props.get('phi_shear', 0.85)
        phi_vn = phi * vc_min
        
        passed = vu_display <= phi_vn + 1.0 # Tolerance
        
        c1, c2 = st.columns(2)
        with c1:
            st.write("### Demand")
            st.latex(fr"V_u = \mathbf{{{vu_display:,.0f}}} \text{{ kg}}")
        with c2:
            st.write("### Capacity")
            st.latex(fr"\phi V_n = {phi} \times {vc_min:,.0f} = \mathbf{{{phi_vn:,.0f}}} \text{{ kg}}")
        
        st.markdown("---")
        
        ratio = vu_display / phi_vn if phi_vn > 0 else 999
        status_text = "PASS (Safe)" if passed else "FAIL (Unsafe)"
        cls = "pass" if passed else "fail"
        
        st.markdown(f"""
        <div class="verdict-box {cls}">
            <div style="font-size:1rem; opacity:0.8;">Demand / Capacity Ratio</div>
            <div style="font-size:3rem; line-height:1.2;">{ratio:.2f}</div>
            <div style="font-size:1.5rem; margin-top:5px;">{status_text}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 3. MAIN RENDERER
# ==========================================
def render(punch_res, v_oneway_res, mat_props, loads, Lx, Ly):
    inject_custom_css()
    
    st.title("📑 Structural Calculation Report")
    
    # Header Info
    p_shear = mat_props.get('phi_shear', 0.85)
    st.info(f"**Standard:** ACI 318 / EIT | **Load Factors:** 1.4DL + 1.7LL | **Reduction Factor:** $\phi_v$={p_shear}")
    
    # -----------------------------------------------------
    # PRE-CALCULATION
    # -----------------------------------------------------
    h_slab = mat_props['h_slab']
    fc = mat_props['fc']
    w_service = loads['SDL'] + loads['LL']
    
    res_min_rebar = check_min_reinforcement(h_slab)
    res_deflection = check_long_term_deflection(w_service, max(Lx, Ly), h_slab, fc, res_min_rebar['As_min'])

    # --- 1. PUNCHING SHEAR ---
    st.header("1. Punching Shear Analysis")
    
    if punch_res.get('is_dual') or 'check_1' in punch_res:
        tab1, tab2 = st.tabs(["Inner Section (Column Face)", "Outer Section (Drop Panel)"])
        res_1 = punch_res.get('check_1', punch_res)
        with tab1: 
            render_punching_detailed(res_1, mat_props, loads, Lx, Ly, "d/2 from Column Face")
        res_2 = punch_res.get('check_2')
        if res_2:
            with tab2: 
                render_punching_detailed(res_2, mat_props, loads, Lx, Ly, "d/2 from Drop Panel Edge")
    else:
        render_punching_detailed(punch_res, mat_props, loads, Lx, Ly, "d/2 from Column Face")

    # --- 2. ONE-WAY SHEAR ---
    st.header("2. One-Way Shear Analysis")
    st.markdown('<div class="step-container">', unsafe_allow_html=True)
    
    ln_select = Lx if Lx >= Ly else Ly
    axis_name = "X-Direction" if Lx >= Ly else "Y-Direction"

    st.markdown(f"**Controlling Span:** {axis_name}, $L={ln_select:.2f}$ m.")

    # Prep Data
    sqrt_fc = math.sqrt(fc)
    d_slab = h_slab - mat_props.get('cover', 2.5) - 1.0 
    d_meter = d_slab / 100.0
    bw = 100.0 # Unit Strip
    
    # Load Calc
    f_dl = mat_props.get('factor_dl', 1.4)
    f_ll = mat_props.get('factor_ll', 1.7)
    phi_shear = mat_props.get('phi_shear', 0.85)
    
    h_m_one = h_slab / 100.0
    w_sw_one = h_m_one * 2400
    wu_calc = (f_dl * (w_sw_one + loads['SDL'])) + (f_ll * loads['LL'])
    
    # Vu Calculation logic
    dist_critical = (ln_select / 2) - d_meter
    vu_one_calc = wu_calc * dist_critical
    
    vc_nominal = 0.53 * sqrt_fc * bw * d_slab
    phi_vc = phi_shear * vc_nominal
    
    c_cap, c_dem = st.columns(2)
    
    with c_cap:
        render_step_header("A", "Capacity ($\phi V_c$)")
        st.markdown('<div class="meaning-text">Per 1.0 m strip width.</div>', unsafe_allow_html=True)
        st.latex(r"V_c = 0.53 \sqrt{f'_c} b_w d")
        st.write("**Substitute:**")
        st.latex(fr"= 0.53 ({sqrt_fc:.2f}) (100) ({d_slab:.2f})")
        st.latex(fr"V_c = {vc_nominal:,.0f} \text{{ kg/m}}")
        st.markdown("---")
        st.latex(fr"\phi V_c = {phi_shear} \times {vc_nominal:,.0f} = \mathbf{{{phi_vc:,.0f}}} \text{{ kg/m}}")

    with c_dem:
        render_step_header("B", "Demand ($V_u$ at $d$)")
        st.markdown('<div class="meaning-text">Shear at distance d from support.</div>', unsafe_allow_html=True)
        
        st.latex(fr"w_u = \mathbf{{{wu_calc:,.0f}}} \text{{ kg/m}}^2")
        st.write("**Calculation:**")
        st.latex(r"V_u = w_u \times (L/2 - d)")
        st.latex(fr"= {wu_calc:,.0f} \times ({ln_select:.2f}/2 - {d_meter:.2f})")
        
        color_vu_one = "green" if vu_one_calc <= phi_vc else "red"
        st.markdown(f"<div class='calc-result-box' style='color:{color_vu_one}'>Vu = {vu_one_calc:,.0f} kg/m</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    passed_one = vu_one_calc <= phi_vc
    status_one = "PASS" if passed_one else "FAIL"
    icon = "✅" if passed_one else "❌"
    
    st.markdown(f"### Verdict: $V_u$ ({vu_one_calc:,.0f}) {'≤' if passed_one else '>'} $\phi V_c$ ({phi_vc:,.0f}) $\\rightarrow$ {icon} **{status_one}**")
    st.markdown('</div>', unsafe_allow_html=True)

    # --- 3. DEFLECTION ---
    st.header("3. Deflection Check")
    st.markdown('<div class="step-container">', unsafe_allow_html=True)
    
    max_span = max(Lx, Ly)
    val_h_min = (max_span * 100) / 33
    
    col_def_1, col_def_2 = st.columns([1.5, 1])
    
    with col_def_1:
        render_step_header(1, "Minimum Thickness ($h_{min}$)")
        st.markdown('<div class="meaning-text">ACI Table for Exterior Panel (No Drop).</div>', unsafe_allow_html=True)
        st.latex(r"h_{min} = L_{max} / 33")
        st.latex(fr"h_{{min}} = ({max_span:.2f} \times 100) / 33 = \mathbf{{{val_h_min:.2f}}} \text{{ cm}}")
        
    with col_def_2:
        render_step_header(2, "Status")
        passed_def = h_slab >= val_h_min - 0.5 
        status_def = "PASS" if passed_def else "CHECK REQ."
        cls_def = "pass" if passed_def else "fail"
        
        st.markdown(f"""
        <div class="verdict-box {cls_def}">
            <div style="font-size:0.9rem;">Provided vs Required</div>
            <div style="font-size:1.5rem; margin:10px 0;">
                {h_slab:.0f} {'≥' if passed_def else '<'} {val_h_min:.2f} cm
            </div>
            <div>{status_def}</div>
        </div>
        """, unsafe_allow_html=True)
            
    st.markdown('</div>', unsafe_allow_html=True)

    # --- 4. DETAILING ---
    st.header("4. Detailing & Recommendations")
    
    # 4.1 Long Term Deflection
    st.markdown('<div class="step-container">', unsafe_allow_html=True)
    render_step_header("A", "Long-Term Deflection")
    
    c_lt_1, c_lt_2 = st.columns([1.5, 1])
    with c_lt_1:
        st.write("Immediate + Long-term (Creep/Shrinkage, $\lambda=2.0$):")
        
        d_imm = res_deflection['Delta_Immediate']
        d_long = res_deflection['Delta_LongTerm']
        d_total = res_deflection['Delta_Total']
        
        st.latex(fr"\Delta_{{total}} = {d_imm:.2f} (\text{{Imm}}) + {d_long:.2f} (\text{{Long}}) = \mathbf{{{d_total:.2f}}} \text{{ cm}}")

    with c_lt_2:
        limit_240 = res_deflection['Limit_240']
        pass_lt = res_deflection.get('status', 'N/A') == "PASS"
        cls_lt = "pass" if pass_lt else "fail"
        
        st.markdown(f"""
        <div class="verdict-box {cls_lt}">
            <div style="font-size:0.9rem;">Limit L/240 ({limit_240:.2f} cm)</div>
            <div style="font-size:1.5rem; margin:10px 0;">
                {d_total:.2f} cm
            </div>
            <div>{res_deflection.get('status', 'N/A')}</div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # 4.2 Minimum Reinforcement
    st.markdown('<div class="step-container">', unsafe_allow_html=True)
    render_step_header("B", "Minimum Reinforcement ($A_{s,min}$)")
    
    req_as = res_min_rebar['As_min']
    bar_dia = mat_props.get('d_bar', 12.0)
    
    # Calculate suggested spacing
    area_bar = 3.1416 * (bar_dia/10/2)**2
    if req_as > 0:
        spacing = min((area_bar / req_as) * 100, 30.0) 
    else:
        spacing = 30
        
    st.latex(r"A_{s,min} = 0.0018 b h")
    st.latex(fr"= 0.0018 \times 100 \times {h_slab:.0f} = \mathbf{{{req_as:.2f}}} \text{{ cm}}^2/\text{{m}}")
    
    st.success(f"💡 **Recommendation:** Use **DB{bar_dia:.0f} @ {math.floor(spacing):.0f} cm** c/c")
    st.markdown('</div>', unsafe_allow_html=True)
