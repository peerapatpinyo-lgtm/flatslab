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
            font-size: 1.2rem;
            font-weight: 700;
            color: #1565c0; /* Darker Blue */
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #90caf9;
            display: flex;
            align-items: center;
        }
        
        .step-num {
            background-color: #1565c0;
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
            color: #455a64;
            margin-top: 20px;
            margin-bottom: 8px;
            font-size: 1rem;
            border-left: 4px solid #cfd8dc;
            padding-left: 10px;
        }

        .meaning-text {
            font-size: 0.9rem;
            color: #616161;
            font-style: italic;
            margin-bottom: 10px;
            background-color: #f5f5f5;
            padding: 8px;
            border-radius: 4px;
        }

        .calc-result-box {
            background-color: #e3f2fd;
            color: #0d47a1;
            padding: 10px;
            border-radius: 5px;
            text-align: center;
            font-weight: bold;
            font-size: 1.1rem;
            border: 1px solid #bbdefb;
            margin-top: 10px;
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
# 2. DETAILED RENDERERS (FULL EXPANSION MODE)
# ==========================================

def render_punching_detailed(res, mat_props, loads, Lx, Ly, label):
    """
    Render detailed punching shear calculation with FULL substitution steps.
    No abbreviations.
    """
    if not res:
        st.error(f"No data available for {label}")
        return

    st.markdown(f"#### 📍 Critical Section: {label}")
    
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
    gamma_v = res.get('gamma_v', 0.4)
    Munbal = res.get('Munbal', 0.0)
    sqrt_fc = math.sqrt(fc)
    
    # ==========================================
    # 🔴 LOGIC: Dynamic b0 & Detailed Formula
    # ==========================================
    if alpha_s >= 40:
        # --- INTERIOR ---
        pos_title = "Interior Column (เสากลาง)"
        pos_desc = "พื้นที่รับแรงเฉือนครบ 4 ด้าน (4 Sides Effective)"
        # Formula
        b0_latex_eq = r"b_0 = 2(c_1 + d) + 2(c_2 + d)"
        # Substitution
        b0_latex_sub = fr"b_0 = 2({c1} + {d:.1f}) + 2({c2} + {d:.1f})"
        b0_latex_step = fr"b_0 = 2({c1+d:.1f}) + 2({c2+d:.1f})"
        # Calc
        b0_calc = 2*(c1 + d) + 2*(c2 + d)
        
    elif alpha_s >= 30:
        # --- EDGE ---
        pos_title = "Edge Column (เสาขอบ)"
        pos_desc = "พื้นที่รับแรงหายไป 1 ด้าน (รับแรง 3 ด้าน: 2 ด้านตั้งฉาก + 1 ด้านขนาน)"
        # Formula
        b0_latex_eq = r"b_0 = 2(c_1 + d/2) + (c_2 + d)"
        # Substitution
        b0_latex_sub = fr"b_0 = 2({c1} + {d/2:.1f}) + ({c2} + {d:.1f})"
        b0_latex_step = fr"b_0 = 2({c1+d/2:.1f}) + ({c2+d:.1f})"
        # Calc
        b0_calc = 2*(c1 + d/2) + (c2 + d)
        
    else:
        # --- CORNER ---
        pos_title = "Corner Column (เสาเข้ามุม) - Critical Case 🔥"
        pos_desc = "พื้นที่รับแรงหายไป 2 ด้าน (รับแรงเพียง 2 ด้าน) ทำให้ความยาวรอบรูปน้อยที่สุด"
        # Formula
        b0_latex_eq = r"b_0 = (c_1 + d/2) + (c_2 + d/2)"
        # Substitution
        b0_latex_sub = fr"b_0 = ({c1} + {d/2:.1f}) + ({c2} + {d/2:.1f})"
        b0_latex_step = fr"b_0 = ({c1+d/2:.1f}) + ({c2+d/2:.1f})"
        # Calc
        b0_calc = (c1 + d/2) + (c2 + d/2)
        
    b0 = b0_calc

    # --- Step 1: Geometry & Parameters ---
    with st.container():
        st.markdown('<div class="step-container">', unsafe_allow_html=True)
        render_step_header(1, "Geometry & Parameters (ค่าพารามิเตอร์พื้นฐาน)")
        
        # Display Input Parameters first
        st.info(f"**Parameters:** $c_1={c1}$ cm, $c_2={c2}$ cm, $h={h_total}$ cm, Cover={cover} cm")

        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<div class="sub-header">A. Effective Depth (d)</div>', unsafe_allow_html=True)
            st.markdown('<div class="meaning-text">ความลึกประสิทธิผล = ความหนา - ระยะหุ้ม - รัศมีเหล็กเสริม</div>', unsafe_allow_html=True)
            st.latex(r"d = h - \text{Cover} - \phi_{bar}/2")
            st.latex(fr"d = {h_total:.0f} - {cover:.1f} - 1.0")
            st.latex(fr"d = \mathbf{{{d:.2f}}} \text{{ cm}}")
            
            st.markdown('<div class="sub-header">B. Concrete Strength</div>', unsafe_allow_html=True)
            st.latex(fr"\sqrt{{f'_c}} = \sqrt{{{fc}}} = \mathbf{{{sqrt_fc:.2f}}} \text{{ ksc}}")

        with col2:
            st.markdown('<div class="sub-header">C. Critical Perimeter (b0)</div>', unsafe_allow_html=True)
            st.markdown(f"**Position:** {pos_title} ($\alpha_s={alpha_s}$)")
            st.markdown(f"<span style='font-size:0.9rem; color:#d32f2f'>{pos_desc}</span>", unsafe_allow_html=True)
            
            # Show Full Calculation Steps
            st.latex(b0_latex_eq)
            st.latex(b0_latex_sub)
            st.latex(b0_latex_step)
            st.markdown(f"<div class='calc-result-box'>b0 = {b0:.2f} cm</div>", unsafe_allow_html=True)
            
            st.markdown('<div class="sub-header">D. Shape Factors</div>', unsafe_allow_html=True)
            st.latex(fr"\beta = \frac{{\text{{Long Side}}}}{{\text{{Short Side}}}} = \frac{{{max(c1,c2)}}}{{{min(c1,c2)}}} = {beta:.2f}")
            
        st.markdown('</div>', unsafe_allow_html=True)

    # --- Step 2: Nominal Capacity ---
    with st.container():
        st.markdown('<div class="step-container">', unsafe_allow_html=True)
        render_step_header(2, "Nominal Shear Strength ($V_c$) Calculation")
        st.write("คำนวณกำลังรับแรงเฉือนตาม ACI 318 / EIT Standard โดยเลือกค่าน้อยที่สุดจาก 3 สมการ:")
        
        eq1, eq2, eq3 = st.columns(3)
        
        # --- Eq 1: Rectangularity Effect ---
        with eq1:
            st.markdown("**Case 1: Shape Effect**")
            st.latex(r"V_{c1} = 0.53 \left(1 + \frac{2}{\beta}\right) \sqrt{f'_c} b_0 d")
            
            term_beta = 1 + (2/beta)
            val_vc1 = 0.53 * term_beta * sqrt_fc * b0 * d
            
            st.markdown("**Substitute:**")
            st.latex(fr"= 0.53 \left(1 + \frac{{2}}{{{beta:.2f}}}\right) ({sqrt_fc:.2f}) ({b0:.0f}) ({d:.1f})")
            st.latex(fr"= 0.53 ({term_beta:.2f}) ({sqrt_fc:.2f}) ({b0:.0f}) ({d:.1f})")
            st.markdown(f"<div class='calc-result-box'>{val_vc1:,.0f} kg</div>", unsafe_allow_html=True)

        # --- Eq 2: Size Effect ---
        with eq2:
            st.markdown("**Case 2: Size Effect**")
            st.latex(r"V_{c2} = 0.27 \left(\frac{\alpha_s d}{b_0} + 2\right) \sqrt{f'_c} b_0 d") 
            
            term_peri_val = (alpha_s * d / b0) + 2
            val_vc2 = 0.27 * term_peri_val * sqrt_fc * b0 * d 
            
            st.markdown("**Substitute:**")
            st.latex(fr"= 0.27 \left(\frac{{{alpha_s} \cdot {d:.1f}}}{{{b0:.0f}}} + 2\right) ({sqrt_fc:.2f}) ({b0:.0f}) ({d:.1f})")
            st.latex(fr"= 0.27 ({term_peri_val:.2f}) ({sqrt_fc:.2f}) ({b0:.0f}) ({d:.1f})")
            st.markdown(f"<div class='calc-result-box'>{val_vc2:,.0f} kg</div>", unsafe_allow_html=True)

        # --- Eq 3: Basic Shear ---
        with eq3:
            st.markdown("**Case 3: Basic Limit**")
            st.latex(r"V_{c3} = 1.06 \sqrt{f'_c} b_0 d")
            
            val_vc3 = 1.06 * sqrt_fc * b0 * d
            
            st.markdown("**Substitute:**")
            st.latex(fr"= 1.06 ({sqrt_fc:.2f}) ({b0:.0f}) ({d:.1f})")
            st.markdown(f"<div class='calc-result-box'>{val_vc3:,.0f} kg</div>", unsafe_allow_html=True)
        
        st.markdown("---")
        vc_min = min(val_vc1, val_vc2, val_vc3)
        st.success(f"📌 **Controlling Value (Minimum):** $V_c = {vc_min:,.0f}$ kg")
        st.markdown('</div>', unsafe_allow_html=True)

    # --- Step 3: Demand & Design Check ---
    with st.container():
        st.markdown('<div class="step-container">', unsafe_allow_html=True)
        render_step_header(3, "Design Check & Demand Calculation")
        
        # Factors
        f_dl = mat_props.get('factor_dl', 1.4)
        f_ll = mat_props.get('factor_ll', 1.7)
        phi = mat_props.get('phi_shear', 0.85)
        
        # Loads
        h_m = h_total / 100.0
        w_sw = h_m * 2400
        wu_display = (f_dl * (w_sw + loads['SDL'])) + (f_ll * loads['LL'])
        
        # Values
        vu = res.get('Vu', 0)
        phi_vn = phi * vc_min
        
        col_L, col_R = st.columns([1.5, 1])
        
        with col_L:
            st.markdown('<div class="sub-header">A. Factored Loads ($w_u$)</div>', unsafe_allow_html=True)
            st.latex(fr"w_u = {f_dl:.2f}(DL) + {f_ll:.2f}(LL)")
            st.latex(fr"w_u = {f_dl:.2f}({w_sw+loads['SDL']:.0f}) + {f_ll:.2f}({loads['LL']:.0f})")
            st.latex(fr"w_u = \mathbf{{{wu_display:,.0f}}} \text{{ kg/m}}^2")
            
            st.markdown('<div class="sub-header">B. Factored Shear Force ($V_u$)</div>', unsafe_allow_html=True)
            st.markdown('<div class="meaning-text">แรงเฉือนที่เกิดขึ้นจริงจากการวิเคราะห์ (Analysis Result)</div>', unsafe_allow_html=True)
            st.latex(fr"V_u = \mathbf{{{vu:,.0f}}} \text{{ kg}}")
            
            st.markdown('<div class="sub-header">C. Design Capacity ($\phi V_n$)</div>', unsafe_allow_html=True)
            st.latex(fr"\phi V_n = \phi \times V_{{c,min}}")
            st.latex(fr"= {phi} \times {vc_min:,.0f}")
            st.latex(fr"= \mathbf{{{phi_vn:,.0f}}} \text{{ kg}}")

        with col_R:
            st.markdown('<div class="sub-header">D. Conclusion</div>', unsafe_allow_html=True)
            if phi_vn > 0:
                ratio = vu / phi_vn
            else:
                ratio = 999
            
            passed = vu <= phi_vn + 1.0 # Tolerance
            status_text = "PASS (ปลอดภัย)" if passed else "FAIL (อันตราย)"
            cls = "pass" if passed else "fail"
            color_vu = "green" if passed else "red"
            
            st.markdown(f"""
            <div class="verdict-box {cls}">
                <div style="font-size:1rem; opacity:0.8;">Demand / Capacity Ratio</div>
                <div style="font-size:2.8rem; line-height:1.2;">{ratio:.2f}</div>
                <div style="font-size:1.2rem; margin-top:5px;">{status_text}</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.latex(fr"V_u \quad {'\leq' if passed else '>'} \quad \phi V_n")
            st.markdown(f"<div style='text-align:center; font-weight:bold; color:{color_vu}'>{vu:,.0f} {'≤' if passed else '>'} {phi_vn:,.0f}</div>", unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 3. MAIN RENDERER
# ==========================================
def render(punch_res, v_oneway_res, mat_props, loads, Lx, Ly):
    inject_custom_css()
    
    st.title("📑 Detailed Calculation Report (Full Breakdown)")
    
    # Check if Phi values are present to show in header
    p_shear = mat_props.get('phi_shear', 0.85)
    
    st.info(f"💡 **Design Standard:** ACI 318 / EIT Standard (WSD/SDM Adapted) | **Load Factors:** DL={mat_props.get('factor_dl')}, LL={mat_props.get('factor_ll')} | **Reduction Factor:** $\phi_v$={p_shear}")
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
    st.header("1. Punching Shear Analysis (แรงเฉือนเจาะทะลุ)")
    
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

    # --- 2. ONE-WAY SHEAR ---
    st.header("2. One-Way Shear Analysis (แรงเฉือนทางเดียว)")
    st.markdown('<div class="step-container">', unsafe_allow_html=True)
    
    if Lx >= Ly:
        ln_select = Lx
        axis_name = "X-Direction (Lx)"
    else:
        ln_select = Ly
        axis_name = "Y-Direction (Ly)"

    st.markdown(f"**Controlling Span:** {axis_name}, $L={ln_select:.2f}$ m.")

    # Prep Data
    sqrt_fc = math.sqrt(fc)
    d_slab = h_slab - mat_props.get('cover', 2.5) - 1.0 
    d_meter = d_slab / 100.0
    bw = 100.0 # Unit Strip
    f_dl = mat_props.get('factor_dl', 1.4)
    f_ll = mat_props.get('factor_ll', 1.7)
    phi_shear = mat_props.get('phi_shear', 0.85)
    
    # Load Calc
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
        st.markdown('<div class="meaning-text">คิดต่อความกว้างแถบ 1 เมตร (Unit Strip, $b_w=100$ cm)</div>', unsafe_allow_html=True)
        st.latex(r"V_c = 0.53 \sqrt{f'_c} b_w d")
        st.markdown("**Substitute:**")
        st.latex(fr"= 0.53 ({sqrt_fc:.2f}) (100) ({d_slab:.2f})")
        st.latex(fr"V_c = {vc_nominal:,.0f} \text{{ kg/m}}")
        st.markdown("---")
        st.latex(fr"\phi V_c = {phi_shear} \times {vc_nominal:,.0f} = \mathbf{{{phi_vc:,.0f}}} \text{{ kg/m}}")

    with c_dem:
        render_step_header("B", "Demand ($V_u$ at $d$)")
        st.markdown('<div class="meaning-text">แรงเฉือนที่ระยะ d จากขอบ (Critical Section)</div>', unsafe_allow_html=True)
        
        st.write("1. Ultimate Load ($w_u$):")
        st.latex(fr"w_u = {f_dl:.2f}(DL) + {f_ll:.2f}(LL) = \mathbf{{{wu_calc:,.0f}}} \text{{ kg/m}}^2")
        
        st.write(f"2. Shear Force ($V_u$):")
        st.latex(r"V_u = w_u \times (\frac{L}{2} - d_{meter})")
        st.latex(fr"= {wu_calc:,.0f} \times \left(\frac{{{ln_select:.2f}}}{{2}} - {d_meter:.3f}\right)")
        st.latex(fr"= {wu_calc:,.0f} \times ({ln_select/2:.3f} - {d_meter:.3f})")
        
        color_vu_one = "green" if vu_one_calc <= phi_vc else "red"
        st.markdown(f"<div class='calc-result-box' style='color:{color_vu_one}'>Vu = {vu_one_calc:,.0f} kg/m</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    passed_one = vu_one_calc <= phi_vc
    status_one = "PASS" if passed_one else "FAIL"
    icon = "✅" if passed_one else "❌"
    
    st.markdown(f"### Conclusion: $V_u$ ({vu_one_calc:,.0f}) {'≤' if passed_one else '>'} $\phi V_c$ ({phi_vc:,.0f}) $\\rightarrow$ {icon} **{status_one}**")
    st.markdown('</div>', unsafe_allow_html=True)

    # --- 3. DEFLECTION ---
    st.header("3. Deflection Control (Thickness)")
    st.markdown('<div class="step-container">', unsafe_allow_html=True)
    
    max_span = max(Lx, Ly)
    val_h_min = (max_span * 100) / 33
    
    col_def_1, col_def_2 = st.columns([1.5, 1])
    
    with col_def_1:
        render_step_header(1, "Minimum Thickness Check")
        st.markdown('<div class="meaning-text">ตรวจสอบความหนาขั้นต่ำตามตาราง ACI (Exterior, No Drop)</div>', unsafe_allow_html=True)
        st.latex(r"h_{min} = \frac{L_{max}}{33}")
        st.latex(fr"h_{{min}} = \frac{{{max_span:.2f} \times 100}}{{33}} = \frac{{{max_span*100:.1f}}}{{33}}")
        st.latex(fr"= \mathbf{{{val_h_min:.2f}}} \text{{ cm}}")
        
    with col_def_2:
        render_step_header(2, "Verdict")
        st.markdown(f"**Provided Thickness:** {h_slab:.0f} cm")
        
        passed_def = h_slab >= val_h_min - 0.5 
        status_def = "PASS" if passed_def else "CHECK REQ."
        cls_def = "pass" if passed_def else "fail"
        
        st.markdown(f"""
        <div class="verdict-box {cls_def}">
            <div style="font-size:0.9rem;">Comparison</div>
            <div style="font-size:1.5rem; margin:10px 0;">
                {h_slab:.0f} {'≥' if passed_def else '<'} {val_h_min:.2f}
            </div>
            <div>{status_def}</div>
        </div>
        """, unsafe_allow_html=True)
            
    st.markdown('</div>', unsafe_allow_html=True)

    # --- 4. DETAILING ---
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
    st.latex(fr"A_{{s,min}} = 0.0018 \times 100 \times {h_slab:.0f}")
    st.latex(fr"= \mathbf{{{req_as:.2f}}} \text{{ cm}}^2/\text{{m}}")
    
    st.success(f"💡 **Detailing Recommendation:** Use **DB{bar_dia:.0f} @ {math.floor(spacing):.0f} cm** (c/c)")
    st.markdown('</div>', unsafe_allow_html=True)
