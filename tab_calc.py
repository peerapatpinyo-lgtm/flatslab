# tab_calc.py
import streamlit as st
import pandas as pd
import numpy as np
import math

# ==========================================
# 1. VISUAL STYLING
# ==========================================
def inject_custom_css():
    st.markdown("""
    <style>
        .report-container { font-family: 'Sarabun', 'Segoe UI', sans-serif; }
        
        /* Main Section Container */
        .step-container {
            background-color: #ffffff;
            border-radius: 10px;
            padding: 25px;
            margin-bottom: 25px;
            border: 1px solid #e0e0e0;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        }
        
        /* Headers with Number */
        .step-header {
            display: flex;
            align-items: center;
            margin-bottom: 15px;
            border-bottom: 2px solid #0288d1;
            padding-bottom: 8px;
        }
        .step-num {
            background-color: #0288d1;
            color: white;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            text-align: center;
            line-height: 30px;
            font-weight: bold;
            margin-right: 12px;
            font-size: 1rem;
        }
        .step-title {
            font-size: 1.2rem;
            font-weight: 700;
            color: #01579b;
        }

        /* Result Highlighting */
        .result-box {
            background-color: #f1f8e9;
            border-left: 5px solid #8bc34a;
            padding: 15px;
            margin-top: 10px;
        }
        .fail-box {
            background-color: #ffebee;
            border-left: 5px solid #f44336;
            padding: 15px;
            margin-top: 10px;
        }
        
        /* Text styling */
        .calc-label { font-weight: 600; color: #555; }
        .sub-header { font-size: 1rem; font-weight: bold; color: #455a64; margin-top: 15px; text-decoration: underline;}
    </style>
    """, unsafe_allow_html=True)

def section_header(number, title):
    st.markdown(f"""
    <div class="step-header">
        <div class="step-num">{number}</div>
        <div class="step-title">{title}</div>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# 2. CALCULATION LOGIC
# ==========================================

def render_punching_detailed(res, mat_props, label):
    st.markdown(f"### 📍 Critical Section: {label}")
    
    # Variables
    fc = mat_props['fc']
    sqrt_fc = math.sqrt(fc)
    d = res['d']
    b0 = res['b0']
    beta = res.get('beta', 2.0)
    alpha_s = res.get('alpha_s', 40)
    
    # --- Part 1: Parameters ---
    with st.container():
        st.markdown('<div class="step-container">', unsafe_allow_html=True)
        section_header("1", "Design Parameters & Geometry")
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Material Properties:**")
            st.latex(fr"f'_c = {fc} \text{{ ksc}}")
            st.latex(fr"\sqrt{{f'_c}} = \sqrt{{{fc}}} = \mathbf{{{sqrt_fc:.2f}}} \text{{ ksc}}")
        with c2:
            st.markdown("**Section Geometry:**")
            st.latex(fr"d = \mathbf{{{d:.2f}}} \text{{ cm}}")
            st.latex(fr"b_0 (\text{{Perimeter}}) = \mathbf{{{b0:.2f}}} \text{{ cm}}")
            st.latex(fr"\beta (\text{{Ratio}}) = {beta:.2f}, \quad \alpha_s = {alpha_s}")
        st.markdown('</div>', unsafe_allow_html=True)

    # --- Part 2: Nominal Strength ---
    with st.container():
        st.markdown('<div class="step-container">', unsafe_allow_html=True)
        section_header("2", "Nominal Shear Strength (Vc)")
        st.markdown("According to ACI 318, $V_c$ is the smallest of:")
        
        # --- EQ 1 ---
        st.markdown('<div class="sub-header">Case 1: Effect of Geometry Shape (Rectangularity)</div>', unsafe_allow_html=True)
        st.latex(r"V_{c1} = 0.53 \left(1 + \frac{2}{\beta}\right) \sqrt{f'_c} b_0 d")
        term_beta = 1 + (2/beta)
        val_vc1 = 0.53 * term_beta * sqrt_fc * b0 * d
        st.latex(fr"= 0.53 \left(1 + \frac{{2}}{{{beta:.1f}}}\right) ({sqrt_fc:.2f}) ({b0:.0f}) ({d:.1f})")
        st.latex(fr"= 0.53 ({term_beta:.2f}) ({sqrt_fc:.2f}) ({b0:.0f}) ({d:.1f}) = \mathbf{{{val_vc1:,.0f}}} \text{{ kg}}")

        # --- EQ 2 ---
        st.markdown('<div class="sub-header">Case 2: Effect of Column Size vs. Slab Depth</div>', unsafe_allow_html=True)
        st.latex(r"V_{c2} = 0.53 \left(\frac{\alpha_s d}{b_0} + 2\right) \sqrt{f'_c} b_0 d")
        term_peri = (alpha_s * d / b0) + 2
        val_vc2 = 0.53 * term_peri * sqrt_fc * b0 * d
        st.latex(fr"= 0.53 \left(\frac{{{alpha_s:.0f} \cdot {d:.1f}}}{{{b0:.0f}}} + 2\right) ({sqrt_fc:.2f}) ({b0:.0f}) ({d:.1f})")
        st.latex(fr"= 0.53 ({term_peri:.2f}) ({sqrt_fc:.2f}) ({b0:.0f}) ({d:.1f}) = \mathbf{{{val_vc2:,.0f}}} \text{{ kg}}")

        # --- EQ 3 ---
        st.markdown('<div class="sub-header">Case 3: Basic Shear Strength</div>', unsafe_allow_html=True)
        st.latex(r"V_{c3} = 1.06 \sqrt{f'_c} b_0 d")
        val_vc3 = 1.06 * sqrt_fc * b0 * d
        st.latex(fr"= 1.06 ({sqrt_fc:.2f}) ({b0:.0f}) ({d:.1f}) = \mathbf{{{val_vc3:,.0f}}} \text{{ kg}}")
        
        # Summary Min
        vc_min = min(val_vc1, val_vc2, val_vc3)
        st.markdown("---")
        st.markdown(f"**Controlling Value ($V_{{c,min}}$):**")
        st.latex(fr"V_c = \min({val_vc1:,.0f}, {val_vc2:,.0f}, {val_vc3:,.0f}) = \mathbf{{{vc_min:,.0f}}} \text{{ kg}}")
        st.markdown('</div>', unsafe_allow_html=True)

    # --- Part 3: Design Check ---
    with st.container():
        st.markdown('<div class="step-container">', unsafe_allow_html=True)
        section_header("3", "Final Design Check")
        
        phi = 0.85
        phi_vn = phi * vc_min
        vu = res['Vu']
        
        col1, col2 = st.columns([1.5, 1])
        with col1:
            st.markdown("**1. Calculate Design Capacity ($\phi V_c$):**")
            st.latex(r"\phi = 0.85 \quad (\text{Shear})")
            st.latex(fr"\phi V_c = 0.85 \times {vc_min:,.0f} = \mathbf{{{phi_vn:,.0f}}} \text{{ kg}}")
            
            st.markdown("**2. Compare with Factored Demand ($V_u$):**")
            status = "OK" if phi_vn >= vu else "NOT OK"
            sym = r"\geq" if phi_vn >= vu else "<"
            color = "green" if phi_vn >= vu else "red"
            
            st.latex(fr"\phi V_c \quad {sym} \quad V_u")
            st.latex(fr"{phi_vn:,.0f} \quad {sym} \quad {vu:,.0f}")
        
        with col2:
            ratio = vu / phi_vn
            css_class = "result-box" if phi_vn >= vu else "fail-box"
            st.markdown(f"""
            <div class="{css_class}" style="text-align:center;">
                <h3 style="margin:0;">{status}</h3>
                <p>Ratio = {ratio:.2f}</p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 3. MAIN RENDERER
# ==========================================
def render(punch_res, v_oneway_res, mat_props, loads, Lx, Ly):
    inject_custom_css()
    
    st.title("📑 Detailed Engineering Calculation Report")
    st.markdown("Reference Standard: **ACI 318 / EIT 1008**")
    st.divider()

    # --- SECTION A: LOADS ---
    st.header("A. Load Analysis")
    st.markdown('<div class="step-container">', unsafe_allow_html=True)
    section_header("1", "Unit Load Calculation")
    
    h_slab_cm = mat_props['h_slab']
    h_m = h_slab_cm / 100.0
    w_sw = h_m * 2400
    sdl = loads['SDL']
    ll = loads['LL']
    
    # 1. Dead Load
    st.markdown("**1. Dead Load (DL)**")
    st.markdown("- Self Weight ($SW$):")
    st.latex(fr"SW = \text{{thickness}} \times \text{{density}}")
    st.latex(fr"SW = {h_m:.2f} \text{{ m}} \times 2400 \text{{ kg/m}}^3 = \mathbf{{{w_sw:.0f}}} \text{{ kg/m}}^2")
    st.markdown("- Superimposed Dead Load ($SDL$):")
    st.latex(fr"SDL = {sdl:.0f} \text{{ kg/m}}^2")
    st.latex(fr"DL_{{total}} = {w_sw:.0f} + {sdl:.0f} = \mathbf{{{w_sw+sdl:.0f}}} \text{{ kg/m}}^2")
    
    # 2. Factored Load
    st.markdown("**2. Factored Design Load ($w_u$)**")
    st.latex(r"w_u = 1.2(DL) + 1.6(LL)")
    st.latex(fr"w_u = 1.2({w_sw+sdl:.0f}) + 1.6({ll:.0f})")
    
    term_dl = 1.2 * (w_sw + sdl)
    term_ll = 1.6 * ll
    wu_total = term_dl + term_ll
    
    st.latex(fr"w_u = {term_dl:.0f} + {term_ll:.0f} = \mathbf{{{wu_total:,.0f}}} \text{{ kg/m}}^2")
    st.markdown('</div>', unsafe_allow_html=True)

    # --- SECTION B: PUNCHING SHEAR ---
    st.header("B. Punching Shear Analysis (Two-Way)")
    if punch_res.get('is_dual', False):
        tab1, tab2 = st.tabs(["Inner Section (d/2 from Col)", "Outer Section (d/2 from Drop)"])
        with tab1: render_punching_detailed(punch_res['check_1'], mat_props, "Column Face")
        with tab2: render_punching_detailed(punch_res['check_2'], mat_props, "Drop Panel Edge")
    else:
        render_punching_detailed(punch_res, mat_props, "Column Face")

    # --- SECTION C: ONE-WAY SHEAR ---
    st.header("C. One-Way Shear Analysis (Beam Action)")
    st.markdown('<div class="step-container">', unsafe_allow_html=True)
    section_header("1", "Parameters & Capacity")
    
    fc = mat_props['fc']
    sqrt_fc = math.sqrt(fc)
    d_slab = mat_props['h_slab'] - mat_props['cover'] - 1.0 # Approximate db/2
    bw = 100.0
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Analysis Strip:**")
        st.latex(r"b_w = 100 \text{ cm (Unit Width)}")
        st.latex(fr"d = {d_slab:.2f} \text{{ cm}}")
        
    with col2:
        st.markdown("**Concrete Strength:**")
        st.latex(fr"\sqrt{{f'_c}} = {sqrt_fc:.2f} \text{{ ksc}}")

    st.markdown("**Nominal Capacity ($V_c$):**")
    st.latex(r"V_c = 0.53 \sqrt{f'_c} b_w d")
    st.latex(fr"V_c = 0.53 ({sqrt_fc:.2f}) (100) ({d_slab:.2f})")
    vc_val = 0.53 * sqrt_fc * 100 * d_slab
    st.latex(fr"V_c = \mathbf{{{vc_val:,.0f}}} \text{{ kg/m}}")
    
    st.markdown("**Design Capacity ($\phi V_c$):**")
    phi_vc = 0.85 * vc_val
    st.latex(fr"\phi V_c = 0.85 \times {vc_val:,.0f} = \mathbf{{{phi_vc:,.0f}}} \text{{ kg/m}}")
    
    st.markdown("---")
    section_header("2", "Demand vs Capacity")
    vu_one = v_oneway_res.get('Vu', 0)
    
    # Back-calc for display Ln/2 - d roughly
    approx_dist = (vu_one / wu_total) if wu_total > 0 else 0
    
    st.markdown("Checking shear at distance $d$ from support:")
    st.latex(r"V_u = w_u \left(\frac{L_n}{2} - d\right)")
    st.latex(fr"V_u = \mathbf{{{vu_one:,.0f}}} \text{{ kg/m}}")
    
    # Verdict
    if vu_one <= phi_vc:
        st.success(f"✅ PASS: One-way shear demand ({vu_one:,.0f}) < Capacity ({phi_vc:,.0f})")
    else:
        st.error(f"❌ FAIL: One-way shear demand ({vu_one:,.0f}) > Capacity ({phi_vc:,.0f})")
        
    st.markdown('</div>', unsafe_allow_html=True)

    # --- SECTION D: DEFLECTION ---
    st.header("D. Deflection Control (Minimum Thickness)")
    st.markdown('<div class="step-container">', unsafe_allow_html=True)
    section_header("1", "Span & Requirement")
    
    max_span = max(Lx, Ly)
    st.markdown(f"- Longest Clear Span ($L$): **{max_span:.2f} m**")
    st.markdown("- Slab System: Flat Plate / Flat Slab without Interior Beams")
    
    st.markdown("**Minimum Thickness Calculation ($h_{min}$):**")
    st.latex(r"h_{min} = \frac{L}{33} \quad (\text{For Exterior Panel without Edge Beams})")
    
    val_h_min = (max_span * 100) / 33
    st.latex(fr"h_{{min}} = \frac{{{max_span*100:.0f}}}{{33}} = \mathbf{{{val_h_min:.2f}}} \text{{ cm}}")
    
    st.markdown("---")
    section_header("2", "Check Provided Thickness")
    h_prov = mat_props['h_slab']
    
    st.latex(fr"h_{{provided}} = \mathbf{{{h_prov:.0f}}} \text{{ cm}}")
    
    if h_prov >= val_h_min:
        st.success(f"✅ PASS: Provided ({h_prov} cm) > Required ({val_h_min:.2f} cm)")
    else:
        st.error(f"❌ WARNING: Provided ({h_prov} cm) < Required ({val_h_min:.2f} cm). Detailed deflection calculation required.")
        
    st.markdown('</div>', unsafe_allow_html=True)
