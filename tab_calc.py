# tab_calc.py
import streamlit as st
import pandas as pd
import numpy as np
import math

# ==========================================
# 1. VISUAL STYLING (CSS)
# ==========================================
def inject_custom_css():
    st.markdown("""
    <style>
        .report-container { font-family: 'Segoe UI', Tahoma, sans-serif; }
        .step-container {
            background-color: #ffffff;
            border-radius: 8px;
            padding: 25px;
            margin-bottom: 25px;
            border: 1px solid #e0e0e0;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        }
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
        .calc-result { font-weight: bold; color: #0d47a1; padding: 5px 0; }
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

# ... (Keep render_punching_detailed function as is) ...
def render_punching_detailed(res, mat_props, loads, Lx, Ly, label):
    st.markdown(f"#### 📍 Critical Section: {label}")
    fc = mat_props['fc']
    h_slab = mat_props['h_slab']
    cover = mat_props['cover']
    d = res['d']
    b0 = res['b0']
    beta = res.get('beta', 2.0)
    alpha_s = res.get('alpha_s', 40)
    sqrt_fc = math.sqrt(fc)
    
    with st.container():
        st.markdown('<div class="step-container">', unsafe_allow_html=True)
        render_step_header(1, "Geometry & Parameters Calculation")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown('**A. Effective Depth (d)**')
            st.latex(fr"d \approx {h_slab:.0f} - {cover:.0f} - 1.0 = \mathbf{{{d:.2f}}} \text{{ cm}}")
            st.markdown('**B. Concrete Strength**')
            st.latex(fr"\sqrt{{f'_c}} = \sqrt{{{fc}}} = \mathbf{{{sqrt_fc:.2f}}} \text{{ ksc}}")
        with c2:
            st.markdown('**C. Critical Perimeter (b0)**')
            st.latex(fr"b_0 = \mathbf{{{b0:.2f}}} \text{{ cm}}")
            st.markdown('**D. Parameters**')
            st.latex(fr"\beta = {beta:.2f}, \quad \alpha_s = {alpha_s}")
        st.markdown('</div>', unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="step-container">', unsafe_allow_html=True)
        render_step_header(2, "Nominal Shear Strength (Vc)")
        eq1, eq2, eq3 = st.columns(3)
        with eq1:
            st.markdown("**Case 1: Rectangularity**")
            st.latex(r"V_{c1} = 0.53 (1 + 2/\beta) \sqrt{f'_c} b_0 d")
            term_beta = 1 + (2/beta)
            val_vc1 = 0.53 * term_beta * sqrt_fc * b0 * d
            st.markdown(f"<div class='calc-result'>= {val_vc1:,.0f} kg</div>", unsafe_allow_html=True)
        with eq2:
            st.markdown("**Case 2: Perimeter**")
            st.latex(r"V_{c2} = 0.53 (\alpha_s d/b_0 + 2) \sqrt{f'_c} b_0 d")
            term_peri = (alpha_s * d / b0) + 2
            val_vc2 = 0.53 * term_peri * sqrt_fc * b0 * d
            st.markdown(f"<div class='calc-result'>= {val_vc2:,.0f} kg</div>", unsafe_allow_html=True)
        with eq3:
            st.markdown("**Case 3: Basic**")
            st.latex(r"V_{c3} = 1.06 \sqrt{f'_c} b_0 d")
            val_vc3 = 1.06 * sqrt_fc * b0 * d
            st.markdown(f"<div class='calc-result'>= {val_vc3:,.0f} kg</div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="step-container">', unsafe_allow_html=True)
        render_step_header(3, "Design Check")
        h_m = h_slab / 100.0
        w_sw = h_m * 2400
        sdl = loads['SDL']
        ll = loads['LL']
        wu_val = (1.2 * (w_sw + sdl)) + (1.6 * ll)
        vu = res['Vu']
        vc_min = min(val_vc1, val_vc2, val_vc3)
        phi_vn = 0.85 * vc_min
        
        col_L, col_R = st.columns([1.8, 1])
        with col_L:
            st.markdown('**A. Demand (Vu)**')
            st.latex(r"V_u \approx w_u (A_{trib} - A_{crit})")
            st.latex(fr"V_u = \mathbf{{{vu:,.0f}}} \text{{ kg}}")
            st.markdown('**B. Capacity (phi Vn)**')
            st.latex(fr"\phi V_n = 0.85 \times {vc_min:,.0f} = \mathbf{{{phi_vn:,.0f}}} \text{{ kg}}")
        with col_R:
            passed = phi_vn >= vu
            status = "PASS" if passed else "FAIL"
            color = "pass" if passed else "fail"
            ratio = vu / phi_vn
            st.markdown(f"""<div class="verdict-box {color}"><div>Ratio {ratio:.2f}</div><h3>{status}</h3></div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    st.divider()

# ==========================================
# MAIN RENDERER
# ==========================================
def render(punch_res, v_oneway_res, mat_props, loads, Lx, Ly):
    inject_custom_css()
    st.title("📑 Detailed Calculation Report")
    st.markdown("Reference: **ACI 318 / EIT Standard**")
    st.markdown("---")

    # 1. PUNCHING SHEAR
    st.header("1. Punching Shear Analysis")
    if punch_res.get('is_dual', False):
        tab1, tab2 = st.tabs(["Inner Section", "Outer Section"])
        with tab1: render_punching_detailed(punch_res['check_1'], mat_props, loads, Lx, Ly, "d/2 from Column Face")
        with tab2: render_punching_detailed(punch_res['check_2'], mat_props, loads, Lx, Ly, "d/2 from Drop Panel Edge")
    else:
        render_punching_detailed(punch_res, mat_props, loads, Lx, Ly, "d/2 from Column Face")

    # 2. ONE-WAY SHEAR
    st.header("2. One-Way Shear Analysis")
    st.markdown('<div class="step-container">', unsafe_allow_html=True)
    
    # Logic for controlling axis
    if Lx >= Ly:
        ln_select, axis_name = Lx, "X-Direction (Lx)"
    else:
        ln_select, axis_name = Ly, "Y-Direction (Ly)"
        
    st.info(f"👉 **Controlling Case:** {axis_name} is used because it has the longest span ($L={ln_select:.2f}$ m).")
    
    # Calculation
    fc = mat_props['fc']
    sqrt_fc = math.sqrt(fc)
    d_slab = mat_props['h_slab'] - mat_props['cover'] - 1.0
    vc_nominal = 0.53 * sqrt_fc * 100 * d_slab
    phi_vc = 0.85 * vc_nominal
    vu_one = v_oneway_res.get('Vu', 0)
    
    h_m = mat_props['h_slab'] / 100.0
    w_sw = h_m * 2400
    sdl = loads['SDL']
    ll = loads['LL']
    wu_val = (1.2*(w_sw+sdl)) + (1.6*ll)

    c1, c2 = st.columns(2)
    with c1:
        render_step_header("A", "Capacity (phi Vc)")
        st.latex(r"V_c = 0.53 \sqrt{f'_c} b_w d")
        st.latex(fr"= 0.53 ({sqrt_fc:.2f}) (100) ({d_slab:.2f}) = \mathbf{{{vc_nominal:,.0f}}} \text{{ kg/m}}")
        st.latex(fr"\phi V_c = 0.85 \times {vc_nominal:,.0f} = \mathbf{{{phi_vc:,.0f}}} \text{{ kg/m}}")
    with c2:
        render_step_header("B", "Demand (Vu)")
        st.latex(r"V_u = w_u (L_{span}/2 - d)")
        st.latex(fr"= {wu_val:,.0f} ({ln_select:.2f}/2 - {d_slab/100:.2f})")
        st.latex(fr"V_u = \mathbf{{{vu_one:,.0f}}} \text{{ kg/m}}")
    
    st.markdown("---")
    passed_one = vu_one <= phi_vc
    status_one = "PASS" if passed_one else "FAIL"
    icon = "✅" if passed_one else "❌"
    st.markdown(f"**Conclusion:** $V_u$ ({vu_one:,.0f}) vs $\phi V_c$ ({phi_vc:,.0f}) $\rightarrow$ {icon} **{status_one}**")
    st.markdown('</div>', unsafe_allow_html=True)

    # 3. DEFLECTION (UPDATED)
    st.header("3. Deflection Control")
    st.markdown('<div class="step-container">', unsafe_allow_html=True)
    
    max_span = max(Lx, Ly)
    h_provided = mat_props['h_slab']  # Get value from inputs
    
    col_def_1, col_def_2 = st.columns([1.5, 1])
    
    with col_def_1:
        render_step_header(1, "Minimum Thickness Calculation")
        
        # Explain Span Selection
        st.markdown("**1. Identify Critical Span ($L_{max}$)**")
        st.write("Deflection is controlled by the longest clear span:")
        st.latex(fr"L_{{max}} = \max({Lx}, {Ly}) = \mathbf{{{max_span:.2f}}} \text{{ m}}")
        
        # Explain Formula (ACI Table)
        st.markdown("**2. ACI 318 Criteria (Table 8.3.1.1)**")
        st.write("For Flat Plate/Slab without interior beams (Exterior Panel):")
        st.latex(r"h_{min} = \frac{L}{33}")
        
        # Explain Calculation
        st.markdown("**3. Required Thickness**")
        val_h_min = (max_span * 100) / 33
        st.latex(fr"h_{{min}} = \frac{{{max_span:.2f} \times 100}}{{33}} = \mathbf{{{val_h_min:.2f}}} \text{{ cm}}")

    with col_def_2:
        render_step_header(2, "Design Check")
        
        # Explain Source of Provided h
        st.markdown("**A. Provided Thickness ($h_{prov}$)**")
        st.caption("Value from Material Input (User Settings):")
        st.latex(fr"h_{{prov}} = \mathbf{{{h_provided:.0f}}} \text{{ cm}}")
        
        st.markdown("---")
        
        # Comparison & Verdict
        st.markdown("**B. Conclusion**")
        passed_def = h_provided >= val_h_min
        status_def = "PASS" if passed_def else "CHECK REQ."
        cls_def = "pass" if passed_def else "fail"
        
        st.markdown(f"""
        <div class="verdict-box {cls_def}">
            <div style="font-size:0.9rem;">Provided vs Required</div>
            <div style="font-size:1.5rem; margin:10px 0;">
                {h_provided:.0f} {'≥' if passed_def else '<'} {val_h_min:.2f}
            </div>
            <div>{status_def}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # 4. LOADS
    st.header("4. Factored Load (wu)")
    st.markdown('<div class="step-container">', unsafe_allow_html=True)
    total_dl = (h_m * 2400) + sdl
    st.latex(fr"DL = ({h_m:.2f} \times 2400) + {sdl:.0f} = {total_dl:,.0f} \text{{ kg/m}}^2")
    st.latex(fr"w_u = 1.2({total_dl:,.0f}) + 1.6({ll:,.0f}) = \mathbf{{{wu_val:,.0f}}} \text{{ kg/m}}^2")
    st.markdown('</div>', unsafe_allow_html=True)
