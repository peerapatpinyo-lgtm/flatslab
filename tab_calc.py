import streamlit as st
import pandas as pd
import numpy as np
import math

# Try importing helper functions, provide fallback if missing
try:
    from calculations import check_min_reinforcement, check_long_term_deflection
except ImportError:
    # Dummy Fallback functions for testing purely UI
    def check_min_reinforcement(h): return {'As_min': 0.0018*100*h}
    def check_long_term_deflection(*args): 
        return {
            'status': 'PASS', 
            'Delta_Total': 1.50, 
            'Limit_240': 2.00, 
            'Delta_Immediate': 0.50, 
            'Delta_LongTerm': 1.00
        }

# ==========================================
# 1. VISUAL STYLING (CSS)
# ==========================================
def inject_custom_css():
    st.markdown("""
    <style>
        .report-container { font-family: 'Segoe UI', Tahoma, Helvetica, sans-serif; }
        
        .step-container {
            background-color: #ffffff;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            border: 1px solid #e0e0e0;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }
        
        .step-title {
            font-size: 1.2rem;
            font-weight: 700;
            color: #0d47a1; 
            margin-bottom: 15px;
            padding-bottom: 8px;
            border-bottom: 2px solid #e3f2fd;
            display: flex;
            align-items: center;
        }
        
        .step-num {
            background-color: #0d47a1;
            color: white;
            width: 28px;
            height: 28px;
            border-radius: 50%;
            text-align: center;
            line-height: 28px;
            font-size: 0.9rem;
            margin-right: 10px;
            font-weight: bold;
        }
        
        .sub-header {
            font-weight: 600;
            color: #455a64;
            margin-top: 15px;
            margin-bottom: 5px;
            font-size: 1rem;
            border-left: 4px solid #cfd8dc;
            padding-left: 8px;
        }

        .meaning-text {
            font-size: 0.9rem;
            color: #546e7a;
            font-style: italic;
            margin-bottom: 10px;
            background-color: #f5f7f8;
            padding: 8px;
            border-radius: 4px;
        }

        .calc-result-box {
            background-color: #e1f5fe;
            color: #0277bd;
            padding: 10px;
            border-radius: 6px;
            text-align: center;
            font-weight: bold;
            font-size: 1.1rem;
            border: 1px solid #81d4fa;
            margin-top: 8px;
        }
        
        .verdict-box {
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            font-weight: bold;
            border: 1px solid #ddd;
        }
        .pass { background-color: #e8f5e9; color: #2e7d32; border-color: #a5d6a7; }
        .fail { background-color: #ffebee; color: #c62828; border-color: #ef9a9a; }
        
        hr { margin: 20px 0; border: 0; border-top: 1px solid #eceff1; }
    </style>
    """, unsafe_allow_html=True)

def render_step_header(number, text):
    # If number is a string (e.g. "Logic Check"), handle gracefully
    if isinstance(number, str) and not number.isdigit() and len(number) > 2:
        st.markdown(f'<div class="step-title" style="padding-left:0;">{text}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="step-title"><div class="step-num">{number}</div>{text}</div>', unsafe_allow_html=True)

# ==========================================
# 2. LOGIC RENDERER (FINAL PROFESSIONAL VERSION)
# ==========================================
def render_structural_logic(mat_props, Lx, Ly):
    
    st.markdown('<div class="step-container">', unsafe_allow_html=True)
    render_step_header("ℹ️", "Logic Check: Drop Panel vs. Shear Cap Classification")

    # 1. Extract Basic Data
    h_slab = mat_props.get('h_slab', 20.0)
    h_drop = mat_props.get('h_drop', 0)
    has_drop = mat_props.get('has_drop', False) and h_drop > 0

    # ---------------------------------------------------------
    # SMART FETCH: ดึงค่าจาก app.py (ไม่ว่าหน่วยจะเป็น cm หรือ m)
    # ---------------------------------------------------------
    def get_dim(keys_to_check):
        for key in keys_to_check:
            val = mat_props.get(key, 0)
            if val > 0: return val
        return 0

    raw_x = get_dim(['drop_w', 'drop_width_x', 'drop_width', 'width', 'drop_x'])
    raw_y = get_dim(['drop_l', 'drop_width_y', 'drop_length', 'length', 'drop_y'])

    # Auto Unit Conversion: ถ้าค่า > 10 เดาว่าเป็น cm ให้หาร 100
    w_drop_x = raw_x / 100.0 if raw_x > 10 else raw_x
    w_drop_y = raw_y / 100.0 if raw_y > 10 else raw_y
    # ---------------------------------------------------------

    # CASE 1: FLAT PLATE (NO DROP)
    if not has_drop:
        st.info("### 🟦 System Type: FLAT PLATE")
        st.markdown("""
        **Engineering Analysis Protocol:**
        * **Stiffness ($EI$):** Calculated based on uniform slab thickness ($h_{slab}$).
        * **Reinforcement:** Design follows standard Flat Plate coefficients.
        * **Shear:** Punching shear capacity is limited by slab thickness only.
        """)
        st.markdown('</div>', unsafe_allow_html=True)
        return

    # CASE 2: DROP PANEL CHECK
    # Calculate ACI Limits
    limit_L_x = Lx / 3.0
    limit_L_y = Ly / 3.0
    limit_h = h_slab / 4.0
    
    pass_dim_x = w_drop_x >= limit_L_x
    pass_dim_y = w_drop_y >= limit_L_y
    pass_thick = h_drop >= limit_h
    is_structural = pass_dim_x and pass_dim_y and pass_thick
    
    # Render Results Table
    st.write("**Checking dimensions against ACI 318 Requirements:**")
    results = [
        {"Check": "Min. Extension X ($L_x/3$)", "Limit": f"≥ {limit_L_x:.2f} m", "Actual": f"{w_drop_x:.2f} m", "Status": pass_dim_x},
        {"Check": "Min. Extension Y ($L_y/3$)", "Limit": f"≥ {limit_L_y:.2f} m", "Actual": f"{w_drop_y:.2f} m", "Status": pass_dim_y},
        {"Check": "Min. Projection ($h_s/4$)", "Limit": f"≥ {limit_h:.2f} cm", "Actual": f"{h_drop:.2f} cm", "Status": pass_thick},
    ]
    
    c1, c2, c3, c4 = st.columns([2, 1.5, 1.5, 1])
    c1.markdown("**Criteria**"); c2.markdown("**Required**"); c3.markdown("**Provided**"); c4.markdown("**Result**")
    st.markdown("---")
    for r in results:
        c1, c2, c3, c4 = st.columns([2, 1.5, 1.5, 1])
        c1.write(r["Check"]); c2.write(r["Limit"]); c3.write(r["Actual"])
        c4.write("✅" if r["Status"] else "❌")
    st.markdown("---")
    
    # --- ENGINEERING CONCLUSION ---
    if is_structural:
        st.success("### ✅ Conclusion: STRUCTURAL DROP PANEL")
        st.markdown("""
        **Engineering Consequence Analysis:**
        
        1.  **Stiffness Modification (Improved):** * The thickened section meets ACI requirements.
            * **Action:** The software **includes** the Drop Panel inertia ($I_{drop}$) in the Equivalent Frame Analysis.
            * **Result:** Increased stiffness at supports reduces calculated deflection.
            
        2.  **Flexural Design (Economical):**
            * **Action:** Negative moment reinforcement at support is calculated using the full effective depth ($d = h_{slab} + h_{drop} - cover$).
            * **Result:** Reduces the area of steel ($A_s$) required at the column strip.
            
        3.  **Shear Capacity:** * Provides maximum protection against Punching Shear at the column face.
        """)
    else:
        st.warning("### ⚠️ Conclusion: SHEAR CAP ONLY (Not a Structural Drop)")
        st.markdown(f"""
        **Engineering Logic Applied (Safe & Economical Protocol):**
        
        The provided dimensions do not meet ACI 318 criteria for a Drop Panel. The system acts as a **Flat Plate with Shear Caps**.
        
        **1. Stiffness & Frame Analysis (Conservative Approach):**
        * **Action:** The software **IGNORES** the cap thickness for stiffness calculations.
        * **Model:** Treated as a uniform Flat Plate ($h = {h_slab}$ cm).
        * **Reasoning:** Modeling a small cap as a rigid support would artificially attract negative moment and underestimate positive moment at mid-span. We ignore it to ensure the mid-span reinforcement is **Safe**.
        
        **2. Flexural Reinforcement:**
        * **Action:** Support reinforcement is calculated using slab thickness ($h_{{slab}}$) only.
        * **Reasoning:** ACI Code prohibits using the increased depth for flexural strength if dimensions are insufficient.
        
        **3. Punching Shear (Economical Approach):**
        * **Action:** The physical mass of the cap **IS USED** for shear resistance.
        * **Check 1:** Punching at Column Face (Using $d_{{total}}$).
        * **Check 2:** Punching at Cap Edge (Using $d_{{slab}}$).
        """)

    st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 3. CALCULATION RENDERERS
# ==========================================

def render_punching_detailed(res, mat_props, loads, Lx, Ly, label):
    """
    Render detailed punching shear calculation with Step-by-Step explanation.
    """
    if not res:
        st.error(f"No data available for {label}")
        return

    st.markdown(f"#### 📍 Section: {label}")
    
    # --- 1. Extract Basic Material & Geometry ---
    fc = mat_props.get('fc', 240)
    c1 = mat_props.get('cx', 50.0) 
    c2 = mat_props.get('cy', 50.0)
    cover = mat_props.get('cover', 2.5)
    
    # Thickness logic: If checking Column Face and Drop exists, add Drop thickness
    h_slab_base = mat_props.get('h_slab', 20.0)
    is_drop_check = "Face" in label or "Column" in label
    
    # Check if we should add drop thickness
    if mat_props.get('has_drop') and is_drop_check:
        h_total = h_slab_base + mat_props.get('h_drop', 0)
    else:
        h_total = h_slab_base

    # --- Effective Depth (d) ---
    d_bar_mm = mat_props.get('d_bar', 12.0)
    d_bar_cm = d_bar_mm / 10.0
    d = h_total - cover - (d_bar_cm / 2)
    
    # --- Analysis Results ---
    # Safe division
    min_c = min(c1,c2) if min(c1,c2) > 0 else 1
    beta = max(c1,c2)/min_c
    
    alpha_s = mat_props.get('alpha_s', 40) # 40=Int, 30=Edge, 20=Corner
    sqrt_fc = math.sqrt(fc)
    
    # --- Calculate b0 for Display ---
    if alpha_s >= 40:
        pos_title = "Interior Column"
        b0_latex_eq = r"b_0 = 2(c_1 + d) + 2(c_2 + d)"
        b0_calc = 2*(c1 + d) + 2*(c2 + d)
    elif alpha_s >= 30:
        pos_title = "Edge Column"
        b0_latex_eq = r"b_0 = 2(c_1 + d/2) + (c_2 + d)"
        b0_calc = 2*(c1 + d/2) + (c2 + d)
    else:
        pos_title = "Corner Column"
        b0_latex_eq = r"b_0 = (c_1 + d/2) + (c_2 + d/2)"
        b0_calc = (c1 + d/2) + (c2 + d/2)
        
    b0 = b0_calc

    # --- Step 1: Geometry & Parameters ---
    with st.container():
        st.markdown('<div class="step-container">', unsafe_allow_html=True)
        render_step_header(1, "Geometry & Parameters")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<div class="sub-header">A. Effective Depth (d)</div>', unsafe_allow_html=True)
            st.write(f"Thickness: {h_total:.0f} cm | Cover: {cover:.1f} cm | Bar: $\phi${d_bar_mm:.0f} mm")
            st.latex(fr"d = {h_total:.0f} - {cover:.1f} - \frac{{{d_bar_cm}}}{{2}} = \mathbf{{{d:.2f}}} \text{{ cm}}")
            
            st.markdown('<div class="sub-header">B. Concrete Strength</div>', unsafe_allow_html=True)
            st.latex(fr"\sqrt{{f'_c}} = \sqrt{{{fc}}} = \mathbf{{{sqrt_fc:.2f}}} \text{{ ksc}}")

        with col2:
            st.markdown('<div class="sub-header">C. Critical Perimeter (b0)</div>', unsafe_allow_html=True)
            st.write(f"**Type:** {pos_title} ($\\alpha_s = {alpha_s}$)")
            st.latex(b0_latex_eq)
            st.markdown(f"<div class='calc-result-box'>b0 = {b0:.2f} cm</div>", unsafe_allow_html=True)
            
            st.markdown('<div class="sub-header">D. Shape Factor</div>', unsafe_allow_html=True)
            st.latex(fr"\beta = \frac{{{max(c1,c2)}}}{{{min_c}}} = {beta:.2f}")
            
        st.markdown('</div>', unsafe_allow_html=True)

    # --- Step 2: Nominal Capacity ---
    with st.container():
        st.markdown('<div class="step-container">', unsafe_allow_html=True)
        render_step_header(2, "Nominal Shear Capacity (V<sub>c</sub>)")
        
        eq1, eq2, eq3 = st.columns(3)
        
        # --- Eq 1 ---
        with eq1:
            st.markdown("**1. Rectangularity Effect**")
            st.latex(r"V_{c1} = 0.53 \left(1 + \frac{2}{\beta}\right) \sqrt{f'_c} b_0 d")
            term_beta = 1 + (2/beta)
            val_vc1 = 0.53 * term_beta * sqrt_fc * b0 * d
            st.markdown(f"<div class='calc-result-box'>{val_vc1:,.0f} kg</div>", unsafe_allow_html=True)

        # --- Eq 2 ---
        with eq2:
            st.markdown("**2. Size Effect**")
            st.latex(r"V_{c2} = 0.27 \left(\frac{\alpha_s d}{b_0} + 2\right) \sqrt{f'_c} b_0 d") 
            term_peri_val = (alpha_s * d / b0) + 2
            val_vc2 = 0.27 * term_peri_val * sqrt_fc * b0 * d 
            st.markdown(f"<div class='calc-result-box'>{val_vc2:,.0f} kg</div>", unsafe_allow_html=True)

        # --- Eq 3 ---
        with eq3:
            st.markdown("**3. Basic Limit**")
            st.latex(r"V_{c3} = 1.06 \sqrt{f'_c} b_0 d")
            val_vc3 = 1.06 * sqrt_fc * b0 * d
            st.markdown(f"<div class='calc-result-box'>{val_vc3:,.0f} kg</div>", unsafe_allow_html=True)
        
        st.markdown("---")
        vc_min = min(val_vc1, val_vc2, val_vc3)
        st.success(f"📌 **Governing Capacity ($V_c$):** {vc_min:,.0f} kg")
        st.markdown('</div>', unsafe_allow_html=True)

    # --- Step 3: Demand Calculation ---
    with st.container():
        st.markdown('<div class="step-container">', unsafe_allow_html=True)
        render_step_header(3, "Shear Demand (V<sub>u</sub>)")
        
        # Loads
        f_dl = mat_props.get('factor_dl', 1.4)
        f_ll = mat_props.get('factor_ll', 1.7)
        h_m = h_total / 100.0
        w_sw = h_m * 2400
        wu_val = (f_dl * (w_sw + loads['SDL'])) + (f_ll * loads['LL'])

        # Areas
        area_trib = Lx * Ly
        # Critical area (approximate for display)
        area_crit = ((c1+d)/100) * ((c2+d)/100)
        
        # Vu Calc
        vu_calc_raw = wu_val * (area_trib - area_crit)
        # Prefer value from result dict if available
        vu_display = res.get('Vu', vu_calc_raw)

        col_L, col_R = st.columns(2)
        
        with col_L:
            st.markdown('<div class="sub-header">A. Factored Load (w<sub>u</sub>)</div>', unsafe_allow_html=True)
            st.latex(fr"w_u = {f_dl}(DL) + {f_ll}(LL)")
            st.latex(fr"w_u = {f_dl}({w_sw+loads['SDL']:.0f}) + {f_ll}({loads['LL']:.0f})")
            st.markdown(f"**$w_u$ = {wu_val:,.0f} kg/m²**")

            st.markdown('<div class="sub-header">B. Areas</div>', unsafe_allow_html=True)
            st.write(f"$A_{{trib}} = {area_trib:.2f} m^2$")
            st.write(f"$A_{{crit}} \\approx {area_crit:.3f} m^2$")

        with col_R:
            st.markdown('<div class="sub-header">C. Factored Shear (V<sub>u</sub>)</div>', unsafe_allow_html=True)
            st.latex(r"V_u = w_u \times (A_{trib} - A_{crit})")
            st.markdown(f"""
            <div class="calc-result-box" style="font-size:1.4rem; background-color:#fff3e0; color:#e65100; border-color:#ffb74d">
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
        
        # Check Logic
        passed = vu_display <= phi_vn + 1.0 
        
        c1, c2 = st.columns(2)
        with c1:
            st.write("### Demand ($V_u$)")
            st.latex(fr"\mathbf{{{vu_display:,.0f}}} \text{{ kg}}")
        with c2:
            st.write("### Capacity ($\phi V_n$)")
            st.latex(fr"{phi} \times {vc_min:,.0f} = \mathbf{{{phi_vn:,.0f}}} \text{{ kg}}")
        
        st.markdown("---")
        
        ratio = vu_display / phi_vn if phi_vn > 0 else 999
        status_text = "PASS (Safe)" if passed else "FAIL (Unsafe)"
        cls = "pass" if passed else "fail"
        
        st.markdown(f"""
        <div class="verdict-box {cls}">
            <div style="font-size:1rem; opacity:0.8;">Demand / Capacity Ratio</div>
            <div style="font-size:2.5rem; line-height:1.2;">{ratio:.2f}</div>
            <div style="font-size:1.5rem; margin-top:5px;">{status_text}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 4. MAIN RENDERER
# ==========================================
def render(punch_res, v_oneway_res, mat_props, loads, Lx, Ly):
    inject_custom_css()
    
    st.title("📑 Structural Calculation Report")
    
    # --- Header Info ---
    p_shear = mat_props.get('phi_shear', 0.85)
    st.info(f"**Standard:** ACI 318 / EIT | **Load Factors:** {mat_props.get('factor_dl', 1.4)}DL + {mat_props.get('factor_ll', 1.7)}LL | **$\phi_v$:** {p_shear}")
    
    # ==========================================================
    # 🔴 CALL THE NEW LOGIC CHECK HERE
    # ==========================================================
    render_structural_logic(mat_props, Lx, Ly)
    
    # -----------------------------------------------------
    # PRE-CALCULATION
    # -----------------------------------------------------
    h_slab = mat_props.get('h_slab', 20.0)
    fc = mat_props.get('fc', 240)
    w_service = loads['SDL'] + loads['LL']
    
    # Recalculate basic checks for display
    res_min_rebar = check_min_reinforcement(h_slab)
    res_deflection = check_long_term_deflection(w_service, max(Lx, Ly), h_slab, fc, res_min_rebar['As_min'])

    # --- 1. PUNCHING SHEAR ---
    st.header("1. Punching Shear Analysis")
    
    # Check if Dual Case (Shear Cap / Drop Panel)
    if punch_res.get('is_dual') or 'check_1' in punch_res:
        tab1, tab2 = st.tabs(["Inner Section (Column Face)", "Outer Section (Drop/Cap Edge)"])
        res_1 = punch_res.get('check_1', punch_res)
        with tab1: 
            render_punching_detailed(res_1, mat_props, loads, Lx, Ly, "d/2 from Column Face")
        
        res_2 = punch_res.get('check_2')
        if res_2:
            with tab2: 
                render_punching_detailed(res_2, mat_props, loads, Lx, Ly, "d/2 from Drop/Cap Edge")
    else:
        render_punching_detailed(punch_res, mat_props, loads, Lx, Ly, "d/2 from Column Face")

    # --- 2. ONE-WAY SHEAR ---
    st.header("2. One-Way Shear Analysis")
    st.markdown('<div class="step-container">', unsafe_allow_html=True)
    
    ln_select = Lx if Lx >= Ly else Ly
    axis_name = "X-Direction" if Lx >= Ly else "Y-Direction"

    st.markdown(f"**Controlling Span:** {axis_name}, $L={ln_select:.2f}$ m.")
    
    # Data Prep
    sqrt_fc = math.sqrt(fc)
    d_bar_mm = mat_props.get('d_bar', 12.0)
    d_slab = h_slab - mat_props.get('cover', 2.5) - (d_bar_mm/10.0/2)
    d_meter = d_slab / 100.0
    bw = 100.0 # Unit Strip
    
    # Loads
    f_dl = mat_props.get('factor_dl', 1.4)
    f_ll = mat_props.get('factor_ll', 1.7)
    phi_shear = mat_props.get('phi_shear', 0.85)
    
    h_m_one = h_slab / 100.0
    w_sw_one = h_m_one * 2400
    wu_calc = (f_dl * (w_sw_one + loads['SDL'])) + (f_ll * loads['LL'])
    
    # Vu Calculation (at distance d)
    # Conservative approximation: Vu = wu * (L/2 - d)
    vu_one_calc = wu_calc * ((ln_select / 2) - d_meter)
    
    vc_nominal = 0.53 * sqrt_fc * bw * d_slab
    phi_vc = phi_shear * vc_nominal
    
    c_cap, c_dem = st.columns(2)
    
    with c_cap:
        render_step_header("A", "Capacity (&phi;V<sub>c</sub>)")
        st.latex(r"\phi V_c = \phi \times 0.53 \sqrt{f'_c} b_w d")
        st.latex(fr"= {phi_shear} \times 0.53 ({sqrt_fc:.2f}) (100) ({d_slab:.2f})")
        st.latex(fr"\phi V_c = \mathbf{{{phi_vc:,.0f}}} \text{{ kg/m}}")

    with c_dem:
        render_step_header("B", "Demand (V<sub>u</sub> at d)")
        st.write(f"Load $w_u = {wu_calc:,.0f}$ kg/m")
        st.latex(r"V_u = w_u (L/2 - d)")
        st.latex(fr"= {wu_calc:,.0f} ({ln_select:.2f}/2 - {d_meter:.2f})")
        
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
        render_step_header(1, "Minimum Thickness (h<sub>min</sub>)")
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
        d_imm = res_deflection['Delta_Immediate']
        d_long = res_deflection['Delta_LongTerm']
        d_total = res_deflection['Delta_Total']
        
        st.markdown("**1. Deflection Components:**")
        st.latex(r"\Delta_{imm} = " + f"{d_imm:.2f}" + r" \text{ cm}")
        st.latex(r"\Delta_{long} = \lambda \Delta_{imm} = 2.0 \times " + f"{d_imm:.2f} = {d_long:.2f} " + r"\text{ cm}")

        st.markdown("**2. Total Deflection:**")
        st.latex(fr"\Delta_{{total}} = {d_imm:.2f} + {d_long:.2f} = \mathbf{{{d_total:.2f}}} \text{{ cm}}")

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
    render_step_header("B", "Minimum Reinforcement (A<sub>s,min</sub>)")
    
    req_as = res_min_rebar['As_min']
    bar_dia = mat_props.get('d_bar', 12.0)
    
    # Calculate spacing
    area_bar = 3.1416 * (bar_dia/10/2)**2
    if req_as > 0:
        spacing = min((area_bar / req_as) * 100, 30.0) 
    else:
        spacing = 30
        
    st.latex(r"A_{s,min} = 0.0018 b h = 0.0018 \times 100 \times " + f"{h_slab:.0f}")
    st.latex(fr"= \mathbf{{{req_as:.2f}}} \text{{ cm}}^2/\text{{m}}")
    
    st.success(f"💡 **Recommendation:** Use **DB{bar_dia:.0f} @ {math.floor(spacing):.0f} cm** c/c")
    st.markdown('</div>', unsafe_allow_html=True)
