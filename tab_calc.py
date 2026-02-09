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
# 2. DETAILED RENDERERS
# ==========================================

def render_punching_detailed(res, mat_props, loads, Lx, Ly, label):
    """
    Render detailed punching shear calculation.
    """
    # Safety check: if res is None or empty, stop rendering
    if not res:
        st.error(f"No data available for {label}")
        return

    st.markdown(f"#### 📍 Critical Section: {label}")
    
    # Extract Variables
    fc = mat_props['fc']
    h_slab = mat_props['h_slab']
    cover = mat_props['cover']
    
    # From Result Dictionary
    d = res.get('d', 0)
    b0 = res.get('b0', res.get('bo', 0)) # Handle alias
    beta = res.get('beta', 2.0)
    alpha_s = res.get('alpha_s', 40)
    gamma_v = res.get('gamma_v', 0.4) # For moment transfer
    Munbal = res.get('Munbal', 0.0)
    
    sqrt_fc = math.sqrt(fc)
    
    # Identify Column Position for Display
    if alpha_s >= 40:
        pos_text = "Interior Column (4 Sides)"
        b0_latex = r"b_0 = 2(c_1 + d) + 2(c_2 + d)"
    elif alpha_s >= 30:
        pos_text = "Edge Column (3 Sides)"
        b0_latex = r"b_0 = 2(c_{edge} + d/2) + (c_{face} + d)"
    else:
        pos_text = "Corner Column (2 Sides)"
        b0_latex = r"b_0 = (c_1 + d/2) + (c_2 + d/2)"
    
    # --- Step 1: Geometry & Parameters ---
    with st.container():
        st.markdown('<div class="step-container">', unsafe_allow_html=True)
        render_step_header(1, "Geometry & Parameters Calculation")
        
        c1, c2 = st.columns(2)
        
        with c1:
            st.markdown('<div class="sub-header">A. Effective Depth (d)</div>', unsafe_allow_html=True)
            st.latex(r"d = h_{slab} - \text{Cover} - \phi_{bar}/2")
            st.write("Assuming average bar diameter ~20mm:")
            st.latex(fr"d \approx {h_slab:.0f} - {cover:.0f} - 1.0 = \mathbf{{{d:.2f}}} \text{{ cm}}")
            
            st.markdown('<div class="sub-header">B. Concrete Strength</div>', unsafe_allow_html=True)
            st.latex(fr"\sqrt{{f'_c}} = \sqrt{{{fc}}} = \mathbf{{{sqrt_fc:.2f}}} \text{{ ksc}}")

        with c2:
            st.markdown('<div class="sub-header">C. Critical Perimeter (b0)</div>', unsafe_allow_html=True)
            st.markdown(f"Condition: **{pos_text}**")
            st.write("Perimeter at distance $d/2$ from support:")
            
            st.latex(b0_latex)
            st.latex(fr"b_0 = \mathbf{{{b0:.2f}}} \text{{ cm}}")
            
            st.markdown('<div class="sub-header">D. Parameters</div>', unsafe_allow_html=True)
            st.latex(fr"\alpha_s = {alpha_s}, \quad \beta = {beta:.2f}")
            if Munbal > 0:
                 st.latex(fr"\gamma_v (\text{{Moment Transfer}}) = {gamma_v:.3f}")
            
        st.markdown('</div>', unsafe_allow_html=True)

    # --- Step 2: Nominal Capacity ---
    with st.container():
        st.markdown('<div class="step-container">', unsafe_allow_html=True)
        render_step_header(2, "Nominal Shear Strength (Vc)")
        st.write("Calculated based on ACI 318 (Minimum of 3 equations):")
        
        eq1, eq2, eq3 = st.columns(3)
        
        # --- Eq 1 ---
        with eq1:
            st.markdown("**Case 1: Rectangularity**")
            st.latex(r"V_{c1} = 0.53 \left(1 + \frac{2}{\beta}\right) \sqrt{f'_c} b_0 d")
            term_beta = 1 + (2/beta)
            val_vc1 = 0.53 * term_beta * sqrt_fc * b0 * d
            st.latex(fr"= 0.53 ({term_beta:.2f}) ({sqrt_fc:.2f}) ({b0:.0f}) ({d:.1f})")
            st.markdown(f"<div class='calc-result'>= {val_vc1:,.0f} kg</div>", unsafe_allow_html=True)

        # --- Eq 2 ---
        with eq2:
            st.markdown("**Case 2: Perimeter**")
            st.latex(r"V_{c2} = 0.53 \left(\frac{\alpha_s d}{b_0} + 2\right) \sqrt{f'_c} b_0 d")
            term_peri_val = (alpha_s * d / b0) + 2
            val_vc2 = 0.53 * term_peri_val * sqrt_fc * b0 * d
            st.latex(fr"= 0.53 \left(\frac{{{alpha_s} \cdot {d:.1f}}}{{{b0:.0f}}} + 2\right) ({sqrt_fc:.2f}) ({b0:.0f}) ({d:.1f})")
            st.markdown(f"<div class='calc-result'>= {val_vc2:,.0f} kg</div>", unsafe_allow_html=True)

        # --- Eq 3 ---
        with eq3:
            st.markdown("**Case 3: Basic**")
            st.latex(r"V_{c3} = 1.06 \sqrt{f'_c} b_0 d")
            val_vc3 = 1.06 * sqrt_fc * b0 * d
            st.latex(fr"= 1.06 ({sqrt_fc:.2f}) ({b0:.0f}) ({d:.1f})")
            st.markdown(f"<div class='calc-result'>= {val_vc3:,.0f} kg</div>", unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

    # --- Step 3: Demand & Design Check ---
    with st.container():
        st.markdown('<div class="step-container">', unsafe_allow_html=True)
        render_step_header(3, "Design Check & Demand Calculation")
        
        # Retrieve Factors
        f_dl = loads.get('factor_dl', 1.4)
        f_ll = loads.get('factor_ll', 1.7)
        
        # [MODIFIED] Logic to determine Phi automatically
        # If Load Factor DL < 1.3 (implied 1.2), use Phi 0.75 (Modern ACI).
        # Else (implied 1.4), use Phi 0.85 (EIT/Old ACI).
        if f_dl < 1.3:
            phi = 0.75
            std_ref = "ACI 318-05+"
        else:
            phi = 0.85
            std_ref = "EIT / ACI 318-99"

        h_m = h_slab / 100.0
        w_sw = h_m * 2400
        sdl = loads['SDL']
        ll = loads['LL']
        w_dead_total = w_sw + sdl
        
        # Note: wu_val below is recalculated for display verification, 
        # normally we should match loads['w_u'] from the model.
        wu_display = (f_dl * w_dead_total) + (f_ll * ll)
        
        # Load from Result
        vu = res.get('Vu', 0)
        vc_min = min(val_vc1, val_vc2, val_vc3)
        phi_vn = phi * vc_min
        
        # Logic Switch: Force vs Stress
        is_stress_check = res.get("check_type") == "stress"
        
        col_L, col_R = st.columns([1.8, 1])
        
        with col_L:
            st.markdown('<div class="sub-header">A. Factored Shear Demand</div>', unsafe_allow_html=True)
            st.write("Using Load Factors:")
            
            # Show formula with factors
            st.latex(fr"w_u = {f_dl:.2f}(DL) + {f_ll:.2f}(LL)")
            st.latex(fr"w_u = {f_dl:.2f}(\underbrace{{{w_sw:.0f}}}_{{SW}} + \underbrace{{{sdl}}}_{{SDL}}) + {f_ll:.2f}({ll})")
            st.latex(fr"w_u = \mathbf{{{wu_display:,.0f}}} \text{{ kg/m}}^2")
            
            if is_stress_check and Munbal > 10:
                # STRESS BASED DISPLAY (Advanced)
                st.warning("⚠️ **Moment Transfer Detected:** Checking Combined Shear Stress")
                
                st.latex(r"v_{u,max} = \frac{V_u}{A_c} + \frac{\gamma_v M_u c}{J_c}")
                
                v_act = res.get('stress_actual', 0)
                v_allow = res.get('stress_allow', 0)
                
                st.latex(fr"V_u = {vu:,.0f} \text{{ kg}}, \quad M_{{unbal}} = {Munbal:,.0f} \text{{ kg-m}}")
                st.latex(fr"v_{{actual}} = \mathbf{{{v_act:.2f}}} \text{{ ksc}}")
                
                st.markdown("---")
                st.markdown('<div class="sub-header">B. Stress Capacity</div>', unsafe_allow_html=True)
                st.write(f"Ref: {std_ref} ($\phi = {phi}$)")
                st.latex(r"\phi v_c = \phi \times \min(\text{Eq1, Eq2, Eq3})")
                st.latex(fr"\phi v_c = {phi} \times {vc_min/(b0*d):.2f} = \mathbf{{{v_allow:.2f}}} \text{{ ksc}}")
                
                # Setup vars for verdict
                demand_val = v_act
                capacity_val = v_allow
                unit = "ksc"
                
            else:
                # FORCE BASED DISPLAY (Legacy/Simple)
                st.latex(r"V_u \approx w_u \times (A_{trib} - A_{critical})")
                st.latex(fr"V_u = \mathbf{{{vu:,.0f}}} \text{{ kg}}")
                
                st.markdown("---")
                st.markdown('<div class="sub-header">B. Force Capacity</div>', unsafe_allow_html=True)
                st.write(f"Ref: {std_ref} ($\phi = {phi}$)")
                st.latex(fr"\phi V_n = {phi} \times V_{{c,min}}")
                st.latex(fr"= {phi} \times {vc_min:,.0f} = \mathbf{{{phi_vn:,.0f}}} \text{{ kg}}")
                
                # Setup vars for verdict
                demand_val = vu
                capacity_val = phi_vn
                unit = "kg"

        with col_R:
            status = res.get('status', 'N/A')
            passed = status == "OK" or status == "PASS"
            status_text = "PASS" if passed else "FAIL"
            color_vu = "black" if passed else "red"
            operator = r"\leq" if passed else ">"
            cls = "pass" if passed else "fail"
            ratio = res.get('ratio', 0)
            
            st.markdown(f"""
            <div class="verdict-box {cls}">
                <div style="font-size:1rem; opacity:0.8;">Capacity Ratio</div>
                <div style="font-size:2.5rem; line-height:1.2;">{ratio:.2f}</div>
                <div style="font-size:1.2rem; margin-top:5px;">{status_text}</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.latex(fr"\text{{Demand}} \quad \text{{vs}} \quad \text{{Cap.}}")
            st.latex(fr"{demand_val:,.2f} \quad {operator} \quad \textcolor{{{color_vu}}}{{{capacity_val:,.2f}}}")
            st.caption(f"Unit: {unit}")

        st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 3. MAIN RENDERER
# ==========================================
def render(punch_res, v_oneway_res, mat_props, loads, Lx, Ly):
    inject_custom_css()
    
    st.title("📑 Detailed Calculation Report")
    st.caption("Reference: ACI 318 / EIT Standard (Method of Limit States)")
    st.markdown("---")
    
    # -----------------------------------------------------
    # PRE-CALCULATION FOR NEW CHECKS
    # -----------------------------------------------------
    h_slab = mat_props['h_slab']
    fc = mat_props['fc']
    w_service = loads['SDL'] + loads['LL']
    
    # Check Min Reinforcement
    res_min_rebar = check_min_reinforcement(h_slab)
    # Check Long Term Deflection
    res_deflection = check_long_term_deflection(w_service, max(Lx, Ly), h_slab, fc, res_min_rebar['As_min'])

    # --- 1. PUNCHING SHEAR (FIXED KEYERROR) ---
    st.header("1. Punching Shear Analysis")
    
    # Logic: Check if result is Dual (with Drop Panel) or Single (No Drop Panel)
    if punch_res.get('is_dual') or 'check_1' in punch_res:
        # --- DUAL CHECK (Drop Panel) ---
        tab1, tab2 = st.tabs(["Inner Section (Column)", "Outer Section (Drop Panel)"])
        
        # Safe Get for Check 1
        res_1 = punch_res.get('check_1')
        if not res_1: res_1 = punch_res # Fallback
            
        with tab1: 
            render_punching_detailed(res_1, mat_props, loads, Lx, Ly, "d/2 from Column Face")
        
        # Safe Get for Check 2
        res_2 = punch_res.get('check_2')
        if res_2:
            with tab2: 
                render_punching_detailed(res_2, mat_props, loads, Lx, Ly, "d/2 from Drop Panel Edge")
    else:
        # --- SINGLE CHECK (Flat Plate) ---
        render_punching_detailed(punch_res, mat_props, loads, Lx, Ly, "d/2 from Column Face")

    # --- 2. ONE-WAY SHEAR ---
    st.header("2. One-Way Shear Analysis")
    st.markdown('<div class="step-container">', unsafe_allow_html=True)
    
    if Lx >= Ly:
        ln_select = Lx
        axis_name = "X-Direction (Lx)"
    else:
        ln_select = Ly
        axis_name = "Y-Direction (Ly)"

    st.info(f"👉 **Controlling Case:** {axis_name} is used because it has the longest span ($L={ln_select:.2f}$ m).")

    # Prep Data
    fc = mat_props['fc']
    sqrt_fc = math.sqrt(fc)
    d_slab = mat_props['h_slab'] - mat_props['cover'] - 1.0
    bw = 100.0
    
    # [MODIFIED] Link Phi to Load Factor here as well
    f_dl = loads.get('factor_dl', 1.4)
    if f_dl < 1.3:
        phi_shear = 0.75
    else:
        phi_shear = 0.85
    
    vc_nominal = 0.53 * sqrt_fc * bw * d_slab
    phi_vc = phi_shear * vc_nominal
    vu_one = v_oneway_res.get('Vu', 0)
    
    c_cap, c_dem = st.columns(2)
    
    with c_cap:
        render_step_header("A", "Capacity (φVc)")
        st.markdown(r"Unit strip $b_w = 100$ cm")
        st.latex(r"V_c = 0.53 \sqrt{f'_c} b_w d")
        st.latex(fr"= 0.53 ({sqrt_fc:.2f}) (100) ({d_slab:.2f})")
        st.markdown(f"Nominal $V_c =$ **{vc_nominal:,.0f}** kg/m")
        st.markdown("---")
        st.latex(fr"\phi V_c = {phi_shear} \times V_c")
        st.latex(fr"= {phi_shear} \times {vc_nominal:,.0f} = \mathbf{{{phi_vc:,.0f}}} \text{{ kg/m}}")

    with c_dem:
        render_step_header("B", "Demand Calculation (Vu)")
        
        # [MODIFIED] Use the real wu from loads dict to be consistent
        w_u_val = loads.get('w_u', 0)
        
        st.write(f"Using $w_u = {w_u_val:,.0f}$ kg/m²")
        st.write(f"Critical section at d ({d_slab/100:.2f} m) from support")
        st.latex(r"V_u = w_u (L_{span}/2 - d)")
        st.latex(fr"V_u = \mathbf{{{vu_one:,.0f}}} \text{{ kg/m}}")
        
        color_vu_one = "black" if vu_one <= phi_vc else "red"
        st.latex(fr"V_u = \textcolor{{{color_vu_one}}}{{\mathbf{{{vu_one:,.0f}}}}} \text{{ kg/m}}")
    
    st.markdown("---")
    
    passed_one = vu_one <= phi_vc
    op_one = r"\leq" if passed_one else ">"
    status_one = "PASS" if passed_one else "FAIL"
    icon = "✅" if passed_one else "❌"
    
    st.markdown(f"**Conclusion:** $V_u$ ({vu_one:,.0f}) ${op_one}$ $\phi V_c$ ({phi_vc:,.0f}) $\\rightarrow$ {icon} **{status_one}**")
    st.markdown('</div>', unsafe_allow_html=True)

    # --- 3. DEFLECTION (Initial L/33) ---
    st.header("3. Deflection Control (Thickness)")
    st.markdown('<div class="step-container">', unsafe_allow_html=True)
    
    max_span = max(Lx, Ly)
    h_provided = mat_props['h_slab']
    
    col_def_1, col_def_2 = st.columns([1.5, 1])
    
    with col_def_1:
        render_step_header(1, "Minimum Thickness (ACI Table 8.3.1.1)")
        
        st.write("For Flat Plate without drop panels (Exterior):")
        st.latex(r"h_{min} = \frac{L_{max}}{33}")
        
        val_h_min = (max_span * 100) / 33
        st.latex(fr"h_{{min}} = \frac{{{max_span:.2f} \times 100}}{{33}} = \mathbf{{{val_h_min:.2f}}} \text{{ cm}}")
        
    with col_def_2:
        render_step_header(2, "Check")
        
        st.markdown(f"**Provided:** {h_provided:.0f} cm")
        
        passed_def = h_provided >= val_h_min
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

    # --- 4. ADVANCED SERVICEABILITY (NEW SECTION) ---
    st.header("4. Advanced Serviceability & Detailing")
    
    # 4.1 Long Term Deflection
    st.markdown('<div class="step-container">', unsafe_allow_html=True)
    render_step_header("A", "Long-Term Deflection (Detailed)")
    
    c_lt_1, c_lt_2 = st.columns([1.5, 1])
    with c_lt_1:
        st.write("Includes immediate deflection + creep/shrinkage effects ($\lambda = 2.0$):")
        
        st.latex(r"\Delta_{total} = \Delta_i + \lambda \Delta_i")
        st.write(f"Effective Inertia ($I_e$) assumed 0.4$I_g$ (Cracked)")
        
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
    bar_dia = mat_props['d_bar']
    
    # Calculate spacing
    area_bar = 3.1416 * (bar_dia/10/2)**2
    spacing = (area_bar / req_as) * 100
    
    st.latex(r"A_{s,min} = 0.0018 b h")
    st.latex(fr"A_{{s,min}} = \mathbf{{{req_as:.2f}}} \text{{ cm}}^2/\text{{m}}")
    
    st.info(f"💡 **Detailing Suggestion:** Use **DB{bar_dia} @ {spacing:.0f} cm** (c/c) to satisfy minimum requirement.")
    st.markdown('</div>', unsafe_allow_html=True)
