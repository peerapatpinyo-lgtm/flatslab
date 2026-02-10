# tab_calc.py
import streamlit as st
import pandas as pd
import numpy as np
import math
from calculations import check_min_reinforcement, check_long_term_deflection

# ==========================================
# 1. VISUAL STYLING (CSS)
# ==========================================
def inject_custom_css():
    st.markdown("""
    <style>
        .report-container { font-family: 'Segoe UI', Tahoma, sans-serif; }
        
        /* Main Container */
        .step-container {
            background-color: #ffffff;
            border-radius: 8px;
            padding: 25px;
            margin-bottom: 25px;
            border: 1px solid #e0e0e0;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        }
        
        /* Headers */
        .step-title {
            font-size: 1.15rem;
            font-weight: 700;
            color: #0277bd;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #b3e5fc;
            display: flex;
            align-items: center;
        }
        
        .step-num {
            background-color: #0277bd;
            color: white;
            width: 28px;
            height: 28px;
            border-radius: 50%;
            text-align: center;
            line-height: 28px;
            font-size: 0.9rem;
            margin-right: 12px;
        }
        
        .sub-header {
            font-weight: 600;
            color: #546e7a;
            margin-top: 15px;
            margin-bottom: 5px;
            text-decoration: underline;
            text-decoration-color: #cfd8dc;
        }

        .calc-result {
            font-weight: bold;
            color: #0d47a1;
            padding: 5px 0;
        }
        
        .verdict-box {
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            font-weight: bold;
            border: 1px solid #ddd;
        }
        .pass { background-color: #e8f5e9; color: #2e7d32; border-color: #a5d6a7; }
        .fail { background-color: #ffebee; color: #c62828; border-color: #ef9a9a; }
        
        hr { margin: 25px 0; border: 0; border-top: 1px dashed #cfd8dc; }
    </style>
    """, unsafe_allow_html=True)

def render_step_header(number, text):
    st.markdown(f'<div class="step-title"><div class="step-num">{number}</div>{text}</div>', unsafe_allow_html=True)

# ==========================================
# 2. DETAILED RENDERERS (ENGINEERING LOGIC FIXED)
# ==========================================

def render_punching_detailed(res, mat_props, loads, Lx, Ly, label):
    """
    Render detailed punching shear calculation with correct b0 re-calculation.
    """
    if not res:
        st.error(f"No data available for {label}")
        return

    st.markdown(f"#### 📍 Critical Section: {label}")
    
    # 1. Extract Basic Material & Geometry
    fc = mat_props['fc']
    h_slab = mat_props['h_slab']
    cover = mat_props['cover']
    
    # Get Column Size (Default to 50x50 if missing, strictly needed for corner/edge calc)
    c1 = mat_props.get('c1', 50) 
    c2 = mat_props.get('c2', 50)
    
    # Calculate d (Effective Depth) explicitly to be sure
    # Using 1.0 cm as approx half-bar diameter (DB20)
    d = h_slab - cover - 1.0 
    
    # 2. Extract Analysis Results
    # Note: res['b0'] from calculator might be generic, we will Recalculate it below for display accuracy
    beta = res.get('beta', max(c1,c2)/min(c1,c2))
    alpha_s = res.get('alpha_s', 40) # 40=Int, 30=Edge, 20=Corner
    gamma_v = res.get('gamma_v', 0.4)
    Munbal = res.get('Munbal', 0.0)
    
    sqrt_fc = math.sqrt(fc)
    
    # ==========================================
    # 🔴 ENGINEERING LOGIC: Recalculate b0
    # ==========================================
    # This ensures the displayed b0 matches the column position exactly
    
    if alpha_s >= 40:
        # Interior: 4 sides
        pos_text = "Interior Column (4 Sides)"
        b0_calc = 2*(c1 + d) + 2*(c2 + d)
        b0_latex_formula = r"b_0 = 2(c_1 + d) + 2(c_2 + d)"
        b0_sub = fr"2({c1} + {d:.1f}) + 2({c2} + {d:.1f})"
    elif alpha_s >= 30:
        # Edge: 3 sides
        # Assumption: Perpendicular to edge is c1 or c2? 
        # Standard conservative display for report:
        pos_text = "Edge Column (3 Sides)"
        b0_calc = 2*(c1 + d/2) + (c2 + d) # Example formula
        b0_latex_formula = r"b_0 = 2(c_{side} + d/2) + (c_{front} + d)"
        b0_sub = fr"2({c1} + {d/2:.1f}) + ({c2} + {d:.1f})"
    else:
        # Corner: 2 sides
        pos_text = "Corner Column (2 Sides)"
        b0_calc = (c1 + d/2) + (c2 + d/2)
        b0_latex_formula = r"b_0 = (c_1 + d/2) + (c_2 + d/2)"
        b0_sub = fr"({c1} + {d/2:.1f}) + ({c2} + {d/2:.1f})"
        
    # Use the recalculated b0 for consistency in this report
    b0 = b0_calc

    # --- Step 1: Geometry & Parameters ---
    with st.container():
        st.markdown('<div class="step-container">', unsafe_allow_html=True)
        render_step_header(1, "Geometry & Parameters Calculation")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<div class="sub-header">A. Effective Depth (d)</div>', unsafe_allow_html=True)
            st.latex(r"d = h_{slab} - \text{Cover} - \phi_{bar}/2")
            st.latex(fr"d = {h_slab:.0f} - {cover:.0f} - 1.0 = \mathbf{{{d:.2f}}} \text{{ cm}}")
            
            st.markdown('<div class="sub-header">B. Concrete Strength</div>', unsafe_allow_html=True)
            st.latex(fr"\sqrt{{f'_c}} = \sqrt{{{fc}}} = \mathbf{{{sqrt_fc:.2f}}} \text{{ ksc}}")

        with col2:
            st.markdown('<div class="sub-header">C. Critical Perimeter (b0)</div>', unsafe_allow_html=True)
            st.markdown(f"Position: **{pos_text}** ($\alpha_s={alpha_s}$)")
            
            st.latex(b0_latex_formula)
            st.latex(fr"= {b0_sub}")
            st.latex(fr"b_0 = \mathbf{{{b0:.2f}}} \text{{ cm}}")
            
            st.markdown('<div class="sub-header">D. Ratio Parameters</div>', unsafe_allow_html=True)
            st.latex(fr"\beta = {beta:.2f}, \quad \gamma_v = {gamma_v:.3f}")
            
        st.markdown('</div>', unsafe_allow_html=True)

    # --- Step 2: Nominal Capacity ---
    with st.container():
        st.markdown('<div class="step-container">', unsafe_allow_html=True)
        render_step_header(2, "Nominal Shear Strength (Vc)")
        st.write("Calculated based on ACI 318 / EIT Standard (Min of 3 equations):")
        
        eq1, eq2, eq3 = st.columns(3)
        
        # --- Eq 1: Rectangularity Effect ---
        with eq1:
            st.markdown("**Case 1: Shape (Beta)**")
            st.latex(r"V_{c1} = 0.53 \left(1 + \frac{2}{\beta}\right) \sqrt{f'_c} b_0 d")
            term_beta = 1 + (2/beta)
            val_vc1 = 0.53 * term_beta * sqrt_fc * b0 * d
            st.latex(fr"= 0.53 ({term_beta:.2f}) ({sqrt_fc:.2f}) ({b0:.0f}) ({d:.1f})")
            st.markdown(f"<div class='calc-result'>= {val_vc1:,.0f} kg</div>", unsafe_allow_html=True)

        # --- Eq 2: Perimeter Effect ---
        with eq2:
            st.markdown("**Case 2: Size (Alpha)**")
            st.latex(r"V_{c2} = 0.27 \left(\frac{\alpha_s d}{b_0} + 2\right) \sqrt{f'_c} b_0 d") 
            term_peri_val = (alpha_s * d / b0) + 2
            val_vc2 = 0.27 * term_peri_val * sqrt_fc * b0 * d 
            st.latex(fr"= 0.27 ({term_peri_val:.2f}) ({sqrt_fc:.2f}) ...")
            st.markdown(f"<div class='calc-result'>= {val_vc2:,.0f} kg</div>", unsafe_allow_html=True)

        # --- Eq 3: Basic Shear ---
        with eq3:
            st.markdown("**Case 3: Basic (Max)**")
            st.latex(r"V_{c3} = 1.06 \sqrt{f'_c} b_0 d")
            val_vc3 = 1.06 * sqrt_fc * b0 * d
            st.latex(fr"= 1.06 ({sqrt_fc:.2f}) ({b0:.0f}) ({d:.1f})")
            st.markdown(f"<div class='calc-result'>= {val_vc3:,.0f} kg</div>", unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

    # --- Step 3: Demand & Design Check ---
    with st.container():
        st.markdown('<div class="step-container">', unsafe_allow_html=True)
        render_step_header(3, "Design Check & Demand Calculation")
        
        # Factors
        f_dl = mat_props.get('factor_dl', 1.4)
        f_ll = mat_props.get('factor_ll', 1.7)
        
        # Determine Phi
        if 'phi_shear' in mat_props:
            phi = mat_props['phi_shear']
        elif 'phi' in mat_props:
            phi = mat_props['phi']
        else:
            phi = 0.85 # Default EIT
        
        # Load Calc for display
        h_m = h_slab / 100.0
        w_sw = h_m * 2400
        wu_display = (f_dl * (w_sw + loads['SDL'])) + (f_ll * loads['LL'])
        
        # Variables for Check
        vu = res.get('Vu', 0)
        vc_min = min(val_vc1, val_vc2, val_vc3)
        phi_vn = phi * vc_min
        
        is_stress_check = res.get("check_type") == "stress"
        
        col_L, col_R = st.columns([1.8, 1])
        
        with col_L:
            st.markdown('<div class="sub-header">A. Factored Loads</div>', unsafe_allow_html=True)
            st.latex(fr"w_u = {f_dl:.2f}(DL) + {f_ll:.2f}(LL) \approx \mathbf{{{wu_display:,.0f}}} \text{{ kg/m}}^2")
            
            if is_stress_check and Munbal > 10:
                st.warning("⚠️ **Combined Stress Check (Shear + Moment Transfer)**")
                st.latex(r"v_{u,max} = \frac{V_u}{A_c} + \frac{\gamma_v M_u c}{J_c}")
                
                v_act = res.get('stress_actual', 0)
                # Calculate Capacity in Stress Unit
                v_c_ksc = vc_min / (b0 * d)
                phi_v_c_ksc = phi * v_c_ksc
                
                st.write(f"Parameters: $V_u={vu:,.0f}$ kg, $M_{{unbal}}={Munbal:,.0f}$ kg-m")
                st.latex(fr"v_{{actual}} = \mathbf{{{v_act:.2f}}} \text{{ ksc}}")
                st.latex(fr"\phi v_c = {phi} \times {v_c_ksc:.2f} = \mathbf{{{phi_v_c_ksc:.2f}}} \text{{ ksc}}")
                
                demand_val = v_act
                capacity_val = phi_v_c_ksc
                unit = "ksc"
                
            else:
                st.markdown("For direct shear force check:")
                st.latex(r"V_u \approx w_u \times (A_{trib} - A_{critical})")
                st.latex(fr"V_u = \mathbf{{{vu:,.0f}}} \text{{ kg}}")
                
                st.markdown("---")
                st.latex(fr"\phi V_n = {phi} \times V_{{c,min}}")
                st.latex(fr"= {phi} \times {vc_min:,.0f} = \mathbf{{{phi_vn:,.0f}}} \text{{ kg}}")
                
                demand_val = vu
                capacity_val = phi_vn
                unit = "kg"

        with col_R:
            if capacity_val > 0:
                ratio = demand_val / capacity_val
            else:
                ratio = 999
            
            passed = demand_val <= capacity_val + 1.0 # Tolerance 1kg
            status_text = "PASS" if passed else "FAIL"
            cls = "pass" if passed else "fail"
            color_vu = "black" if passed else "red"
            
            st.markdown(f"""
            <div class="verdict-box {cls}">
                <div style="font-size:1rem; opacity:0.8;">Capacity Ratio</div>
                <div style="font-size:2.5rem; line-height:1.2;">{ratio:.2f}</div>
                <div style="font-size:1.2rem; margin-top:5px;">{status_text}</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.latex(fr"Demand \quad vs \quad Cap.")
            st.latex(fr"{demand_val:,.2f} \quad {'\leq' if passed else '>'} \quad \textcolor{{{color_vu}}}{{{capacity_val:,.2f}}}")
            st.caption(f"Unit: {unit}")

        st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 3. MAIN RENDERER
# ==========================================
def render(punch_res, v_oneway_res, mat_props, loads, Lx, Ly):
    inject_custom_css()
    
    st.title("📑 Detailed Calculation Report")
    
    # Check if Phi values are present to show in header
    p_shear = mat_props.get('phi_shear')
    
    ref_text = "Reference: ACI 318 / EIT Standard (WSD/SDM Adapted)"
    if p_shear:
        ref_text += f" | Factors: φ_shear={p_shear}"
    
    st.caption(ref_text)
    st.markdown("---")
    
    # -----------------------------------------------------
    # PRE-CALCULATION
    # -----------------------------------------------------
    h_slab = mat_props['h_slab']
    fc = mat_props['fc']
    w_service = loads['SDL'] + loads['LL']
    
    # Check Min Reinforcement
    res_min_rebar = check_min_reinforcement(h_slab)
    # Check Long Term Deflection
    res_deflection = check_long_term_deflection(w_service, max(Lx, Ly), h_slab, fc, res_min_rebar['As_min'])

    # --- 1. PUNCHING SHEAR ---
    st.header("1. Punching Shear Analysis")
    
    # Logic: Check if result is Dual (with Drop Panel) or Single (No Drop Panel)
    if punch_res.get('is_dual') or 'check_1' in punch_res:
        # --- DUAL CHECK (Drop Panel) ---
        tab1, tab2 = st.tabs(["Inner Section (Column Face)", "Outer Section (Drop Panel Edge)"])
        
        res_1 = punch_res.get('check_1', punch_res) # Safe get
        with tab1: 
            render_punching_detailed(res_1, mat_props, loads, Lx, Ly, "d/2 from Column Face")
        
        res_2 = punch_res.get('check_2')
        if res_2:
            with tab2: 
                render_punching_detailed(res_2, mat_props, loads, Lx, Ly, "d/2 from Drop Panel Edge")
    else:
        # --- SINGLE CHECK (Flat Plate) ---
        render_punching_detailed(punch_res, mat_props, loads, Lx, Ly, "d/2 from Column Face")

    # --- 2. ONE-WAY SHEAR (Verified) ---
    st.header("2. One-Way Shear Analysis")
    st.markdown('<div class="step-container">', unsafe_allow_html=True)
    
    if Lx >= Ly:
        ln_select = Lx
        axis_name = "X-Direction (Lx)"
    else:
        ln_select = Ly
        axis_name = "Y-Direction (Ly)"

    st.info(f"👉 **Controlling Span:** {axis_name}, $L={ln_select:.2f}$ m (Center-to-Center).")

    # Prep Data
    sqrt_fc = math.sqrt(fc)
    
    # --- ENGINEERING CALCULATION ---
    # 1. Geometry
    d_slab = h_slab - mat_props['cover'] - 1.0 # cm
    d_meter = d_slab / 100.0
    bw = 100.0 # Unit Strip
    
    # 2. Factors
    f_dl = mat_props.get('factor_dl', 1.4)
    f_ll = mat_props.get('factor_ll', 1.7)
    
    if 'phi_shear' in mat_props:
        phi_shear = mat_props['phi_shear']
    else:
        phi_shear = 0.85
    
    # 3. Calculate Wu
    h_m_one = h_slab / 100.0
    w_sw_one = h_m_one * 2400
    w_sdl_one = loads['SDL']
    w_ll_one = loads['LL']
    
    # Total Factored Load
    wu_calc = (f_dl * (w_sw_one + w_sdl_one)) + (f_ll * w_ll_one)
    
    # 4. Calculate Vu at critical section d
    # Note: Conservative use of L/2 instead of ln/2 (clear span)
    vu_one_calc = wu_calc * ((ln_select / 2) - d_meter)
    
    # 5. Capacity
    # Vc = 0.53 * sqrt(fc) * bw * d (For ksc units)
    vc_nominal = 0.53 * sqrt_fc * bw * d_slab
    phi_vc = phi_shear * vc_nominal
    
    c_cap, c_dem = st.columns(2)
    
    with c_cap:
        render_step_header("A", "Capacity (φVc)")
        st.markdown(r"Unit strip $b_w = 100$ cm")
        st.latex(r"V_c = 0.53 \sqrt{f'_c} b_w d")
        st.latex(fr"= 0.53 ({sqrt_fc:.2f}) (100) ({d_slab:.2f})")
        st.markdown(f"Nominal $V_c =$ **{vc_nominal:,.0f}** kg/m")
        st.markdown("---")
        st.latex(fr"\phi V_c = {phi_shear} \times {vc_nominal:,.0f} = \mathbf{{{phi_vc:,.0f}}} \text{{ kg/m}}")

    with c_dem:
        render_step_header("B", "Demand (Vu at d)")
        
        st.write("Load Calculation:")
        st.latex(fr"w_u = {f_dl:.2f}(DL) + {f_ll:.2f}(LL) = \mathbf{{{wu_calc:,.0f}}} \text{{ kg/m}}^2")
        
        st.write(f"Critical section at d ({d_meter:.2f} m) from support")
        st.latex(fr"V_u = w_u (L/2 - d)")
        st.latex(fr"V_u = {wu_calc:,.0f} \left(\frac{{{ln_select:.2f}}}{{2}} - {d_meter:.2f}\right)")
        
        color_vu_one = "black" if vu_one_calc <= phi_vc else "red"
        st.latex(fr"V_u = \textcolor{{{color_vu_one}}}{{\mathbf{{{vu_one_calc:,.0f}}}}} \text{{ kg/m}}")
    
    st.markdown("---")
    
    passed_one = vu_one_calc <= phi_vc
    status_one = "PASS" if passed_one else "FAIL"
    icon = "✅" if passed_one else "❌"
    
    st.markdown(f"**Conclusion:** $V_u$ ({vu_one_calc:,.0f}) {'≤' if passed_one else '>'} $\phi V_c$ ({phi_vc:,.0f}) $\\rightarrow$ {icon} **{status_one}**")
    st.markdown('</div>', unsafe_allow_html=True)

    # --- 3. DEFLECTION (Initial L/33) ---
    st.header("3. Deflection Control (Thickness)")
    st.markdown('<div class="step-container">', unsafe_allow_html=True)
    
    max_span = max(Lx, Ly)
    h_provided = h_slab
    
    col_def_1, col_def_2 = st.columns([1.5, 1])
    
    with col_def_1:
        render_step_header(1, "Minimum Thickness (ACI Table)")
        st.write("For Flat Plate without drop panels (Exterior):")
        st.latex(r"h_{min} = \frac{L_{max}}{33}")
        
        val_h_min = (max_span * 100) / 33
        st.latex(fr"h_{{min}} = \frac{{{max_span:.2f} \times 100}}{{33}} = \mathbf{{{val_h_min:.2f}}} \text{{ cm}}")
        
    with col_def_2:
        render_step_header(2, "Check")
        st.markdown(f"**Provided:** {h_provided:.0f} cm")
        
        passed_def = h_provided >= val_h_min - 0.5 # Tolerance 0.5cm
        status_def = "PASS" if passed_def else "CHECK REQ."
        cls_def = "pass" if passed_def else "fail"
        
        st.markdown(f"""
        <div class="verdict-box {cls_def}">
            <div style="font-size:0.9rem;">h_prov ≥ h_min</div>
            <div style="font-size:1.5rem; margin:10px 0;">
                {h_provided:.0f} {'≥' if passed_def else '<'} {val_h_min:.2f}
            </div>
            <div>{status_def}</div>
        </div>
        """, unsafe_allow_html=True)
            
    st.markdown('</div>', unsafe_allow_html=True)

    # --- 4. ADVANCED SERVICEABILITY ---
    st.header("4. Advanced Serviceability & Detailing")
    
    # 4.1 Long Term Deflection
    st.markdown('<div class="step-container">', unsafe_allow_html=True)
    render_step_header("A", "Long-Term Deflection (Estimated)")
    
    c_lt_1, c_lt_2 = st.columns([1.5, 1])
    with c_lt_1:
        st.write("Includes immediate deflection + creep/shrinkage effects ($\lambda = 2.0$):")
        st.latex(r"\Delta_{total} = \Delta_i + \lambda \Delta_i")
        
        d_imm = res_deflection['Delta_Immediate']
        d_long = res_deflection['Delta_LongTerm']
        d_total = res_deflection['Delta_Total']
        
        st.latex(fr"\Delta_{{total}} = {d_imm:.2f} + {d_long:.2f} = \mathbf{{{d_total:.2f}}} \text{{ cm}}")

    with c_lt_2:
        limit_240 = res_deflection['Limit_240']
        pass_lt = res_deflection['status'] == "PASS"
        cls_lt = "pass" if pass_lt else "fail"
        
        st.markdown(f"""
        <div class="verdict-box {cls_lt}">
            <div style="font-size:0.9rem;">Limit L/240 ({limit_240:.2f} cm)</div>
            <div style="font-size:1.5rem; margin:10px 0;">
                {d_total:.2f} cm
            </div>
            <div>{res_deflection['status']}</div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # 4.2 Minimum Reinforcement
    st.markdown('<div class="step-container">', unsafe_allow_html=True)
    render_step_header("B", "Minimum Reinforcement (Temp & Shrinkage)")
    
    req_as = res_min_rebar['As_min']
    bar_dia = mat_props.get('d_bar', 12.0)
    
    # Calculate suggested spacing
    area_bar = 3.1416 * (bar_dia/10/2)**2
    if req_as > 0:
        spacing = min((area_bar / req_as) * 100, 30.0) # Max 30cm spacing
    else:
        spacing = 30
        
    st.latex(r"A_{s,min} = 0.0018 b h")
    st.latex(fr"A_{{s,min}} = \mathbf{{{req_as:.2f}}} \text{{ cm}}^2/\text{{m}}")
    
    st.info(f"💡 **Detailing:** Use **DB{bar_dia:.0f} @ {math.floor(spacing):.0f} cm** (c/c) to satisfy min requirement.")
    st.markdown('</div>', unsafe_allow_html=True)
