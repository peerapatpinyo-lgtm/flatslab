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
        .report-container { font-family: 'Segoe UI', Tahoma, sans-serif; }
        
        /* Containers */
        .step-container {
            background-color: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            border: 1px solid #eceff1;
        }
        
        /* Headers */
        .step-title {
            font-size: 1.1rem;
            font-weight: 700;
            color: #37474f;
            margin-bottom: 15px;
            border-bottom: 2px solid #cfd8dc;
            padding-bottom: 5px;
            display: flex;
            align-items: center;
        }
        .step-icon { 
            margin-right: 10px; 
            background: #37474f; 
            color: white; 
            width: 24px; 
            height: 24px; 
            text-align: center; 
            border-radius: 50%; 
            font-size: 0.8rem; 
            line-height: 24px; 
        }

        /* Verdict Box */
        .verdict-box {
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            font-weight: bold;
            margin-top: 15px;
            border: 1px solid #ddd;
        }
        .pass { background-color: #e8f5e9; color: #2e7d32; border-color: #a5d6a7; }
        .fail { background-color: #ffebee; color: #c62828; border-color: #ef9a9a; }
        
        /* Sub-labels for equations */
        .eq-label {
            font-size: 0.85rem;
            color: #546e7a;
            font-weight: 600;
            margin-bottom: 5px;
            min-height: 40px; /* align heights */
        }
        
        hr { margin: 30px 0; border: 0; border-top: 1px solid #e0e0e0; }
        
        .calc-result {
            font-weight: bold;
            color: #0d47a1;
            margin-top: 5px;
        }
    </style>
    """, unsafe_allow_html=True)

def render_step_header(number, text):
    st.markdown(f'<div class="step-title"><div class="step-icon">{number}</div>{text}</div>', unsafe_allow_html=True)

# ==========================================
# 2. DETAILED RENDERERS
# ==========================================

def render_punching_detailed(res, mat_props, label):
    st.markdown(f"#### 📍 Critical Section: {label}")
    
    # Extract Variables
    fc = mat_props['fc']
    d = res['d']
    b0 = res['b0']
    beta = res.get('beta', 2.0)
    alpha_s = res.get('alpha_s', 40)
    sqrt_fc = math.sqrt(fc)
    
    # --- Step 1: Geometry ---
    with st.container():
        st.markdown('<div class="step-container">', unsafe_allow_html=True)
        render_step_header(1, "Geometry & Parameters")
        
        c1, c2, c3, c4 = st.columns(4)
        with c1: 
            st.markdown(r"Effective Depth ($d$)")
            st.markdown(f"**{d:.2f}** cm")
        with c2: 
            st.markdown(r"Perimeter ($b_0$)")
            st.markdown(f"**{b0:.2f}** cm")
        with c3: 
            st.markdown(r"Aspect Ratio ($\beta$)")
            st.markdown(f"**{beta:.2f}**")
        with c4: 
            st.markdown(r"Concrete ($\sqrt{f'_c}$)")
            st.markdown(f"**{sqrt_fc:.2f}** ksc")
        st.markdown('</div>', unsafe_allow_html=True)

    # --- Step 2: Nominal Capacity ---
    with st.container():
        st.markdown('<div class="step-container">', unsafe_allow_html=True)
        render_step_header(2, "Nominal Shear Strength (Vc)")
        st.write("Calculated based on ACI 318 (Minimum of 3 equations):")
        
        eq1, eq2, eq3 = st.columns(3)
        
        # --- Eq 1 ---
        with eq1:
            st.markdown('<div class="eq-label">1. Effect of Geometry Shape (Rectangularity)</div>', unsafe_allow_html=True)
            # Formula
            st.latex(r"V_{c1} = 0.53 \left(1 + \frac{2}{\beta}\right) \sqrt{f'_c} b_0 d")
            # Substitution
            term_beta = 1 + (2/beta)
            val_vc1 = 0.53 * term_beta * sqrt_fc * b0 * d
            st.latex(fr"= 0.53 \left(1 + \frac{{2}}{{{beta:.1f}}}\right) ({sqrt_fc:.2f}) ({b0:.0f}) ({d:.1f})")
            # Result
            st.markdown(f"<div class='calc-result'>= {val_vc1:,.0f} kg</div>", unsafe_allow_html=True)

        # --- Eq 2 ---
        with eq2:
            st.markdown('<div class="eq-label">2. Effect of Column Size vs Slab Depth</div>', unsafe_allow_html=True)
            # Formula
            st.latex(r"V_{c2} = 0.53 \left(\frac{\alpha_s d}{b_0} + 2\right) \sqrt{f'_c} b_0 d")
            # Substitution
            term_peri = (alpha_s * d / b0) + 2
            val_vc2 = 0.53 * term_peri * sqrt_fc * b0 * d
            st.latex(fr"= 0.53 \left(\frac{{{alpha_s:.0f} \cdot {d:.1f}}}{{{b0:.0f}}} + 2\right) ({sqrt_fc:.2f}) ({b0:.0f}) ({d:.1f})")
            # Result
            st.markdown(f"<div class='calc-result'>= {val_vc2:,.0f} kg</div>", unsafe_allow_html=True)

        # --- Eq 3 ---
        with eq3:
            st.markdown('<div class="eq-label">3. Basic Shear Strength (Minimum)</div>', unsafe_allow_html=True)
            # Formula
            st.latex(r"V_{c3} = 1.06 \sqrt{f'_c} b_0 d")
            # Substitution
            val_vc3 = 1.06 * sqrt_fc * b0 * d
            st.latex(fr"= 1.06 ({sqrt_fc:.2f}) ({b0:.0f}) ({d:.1f})")
            # Result
            st.markdown(f"<div class='calc-result'>= {val_vc3:,.0f} kg</div>", unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

    # --- Step 3: Design Check ---
    with st.container():
        st.markdown('<div class="step-container">', unsafe_allow_html=True)
        render_step_header(3, "Design Check")
        
        vc_min = min(val_vc1, val_vc2, val_vc3)
        phi = 0.85
        phi_vn = phi * vc_min
        vu = res['Vu']
        
        passed = phi_vn >= vu
        status_text = "PASS" if passed else "FAIL"
        color_vu = "black" if passed else "red"
        operator = r"\geq" if passed else "<"
        
        c_left, c_right = st.columns([2, 1])
        
        with c_left:
            st.markdown("Comparing Design Capacity vs. Factored Demand:")
            
            # Show calculation
            st.latex(r"\phi V_n = 0.85 \times V_{c,min}")
            st.latex(fr"= 0.85 \times {vc_min:,.0f} = \mathbf{{{phi_vn:,.0f}}} \text{{ kg}}")
            
            st.markdown("---")
            st.latex(r"\phi V_n \quad \text{vs} \quad V_u")
            st.latex(fr"{phi_vn:,.0f} \quad {operator} \quad \textcolor{{{color_vu}}}{{{vu:,.0f}}}")
        
        with c_right:
            cls = "pass" if passed else "fail"
            ratio = vu / phi_vn
            st.markdown(f"""
            <div class="verdict-box {cls}">
                <div style="font-size:0.9rem;">Demand/Capacity</div>
                <div style="font-size:2rem;">{ratio:.2f}</div>
                <div>{status_text}</div>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown('</div>', unsafe_allow_html=True)
    st.divider()

# ==========================================
# 3. MAIN RENDERER
# ==========================================
def render(punch_res, v_oneway_res, mat_props, loads, Lx, Ly):
    inject_custom_css()
    
    st.title("📑 Detailed Calculation Report")
    st.caption("Reference: ACI 318 / EIT Standard (Method of Limit States)")
    st.markdown("---")

    # --- 1. PUNCHING SHEAR ---
    st.header("1. Punching Shear Analysis")
    if punch_res.get('is_dual', False):
        tab1, tab2 = st.tabs(["Inner Section (Column)", "Outer Section (Drop Panel)"])
        with tab1: render_punching_detailed(punch_res['check_1'], mat_props, "d/2 from Column Face")
        with tab2: render_punching_detailed(punch_res['check_2'], mat_props, "d/2 from Drop Panel Edge")
    else:
        render_punching_detailed(punch_res, mat_props, "d/2 from Column Face")

    # --- 2. ONE-WAY SHEAR ---
    st.header("2. One-Way Shear Analysis")
    st.markdown('<div class="step-container">', unsafe_allow_html=True)
    
    # Calculate values
    fc = mat_props['fc']
    sqrt_fc = math.sqrt(fc)
    d_slab = mat_props['h_slab'] - mat_props['cover'] - 1.0
    bw = 100.0
    
    vc_nominal_calc = 0.53 * sqrt_fc * bw * d_slab
    phi = 0.85
    phi_vc = phi * vc_nominal_calc
    vu_one = v_oneway_res.get('Vu', 0)
    
    c_cap, c_dem = st.columns(2)
    
    with c_cap:
        render_step_header("A", "Capacity (φVc)")
        st.markdown(r"Unit strip $b_w = 100$ cm")
        # Formula
        st.latex(r"V_c = 0.53 \sqrt{f'_c} b_w d")
        # Substitution
        st.latex(fr"= 0.53 ({sqrt_fc:.2f}) (100) ({d_slab:.2f})")
        st.markdown(f"Nominal $V_c =$ **{vc_nominal_calc:,.0f}** kg/m")
        st.markdown("---")
        st.latex(r"\phi V_c = 0.85 \times V_c")
        st.latex(fr"= 0.85 \times {vc_nominal_calc:,.0f} = \mathbf{{{phi_vc:,.0f}}} \text{{ kg/m}}")

    with c_dem:
        render_step_header("B", "Demand (Vu)")
        
        # Load params for showing work
        h_m = mat_props['h_slab'] / 100.0
        w_sw = h_m * 2400
        sdl = loads['SDL']
        ll = loads['LL']
        wu_val = (1.2 * (w_sw + sdl)) + (1.6 * ll)
        
        st.markdown(r"At distance $d$ from support:")
        st.latex(r"V_u = w_u (L_n/2 - d)")
        # Show substitution using calculated wu
        st.latex(fr"= {wu_val:,.0f} (L_n/2 - {d_slab/100:.2f})")
        
        color_vu_one = "black" if vu_one <= phi_vc else "red"
        st.latex(fr"V_u = \textcolor{{{color_vu_one}}}{{\mathbf{{{vu_one:,.0f}}}}} \text{{ kg/m}}")
    
    st.markdown("---")
    # Verdict
    passed_one = vu_one <= phi_vc
    op_one = r"\leq" if passed_one else ">"
    status_one = "PASS" if passed_one else "FAIL"
    icon = "✅" if passed_one else "❌"
    
    st.markdown(f"**Conclusion:** $V_u$ ({vu_one:,.0f}) ${op_one}$ $\phi V_c$ ({phi_vc:,.0f}) $\rightarrow$ {icon} **{status_one}**")
    st.markdown('</div>', unsafe_allow_html=True)

    # --- 3. DEFLECTION ---
    st.header("3. Deflection Control")
    st.markdown('<div class="step-container">', unsafe_allow_html=True)
    
    c_d1, c_d2, c_d3 = st.columns([1, 1.5, 1])
    max_span = max(Lx, Ly)
    
    with c_d1:
        st.markdown("**1. Span Data**")
        st.markdown(f"Longest Span ($L$): **{max_span:.2f} m**")
    
    with c_d2:
        st.markdown("**2. ACI Formula**")
        st.latex(r"h_{min} = \frac{L}{33}")
        val_h_min = max_span*100/33
        # Detailed Substitution
        st.latex(fr"= \frac{{{max_span*100:.0f}}}{{33}} = \mathbf{{{val_h_min:.2f}}} \text{{ cm}}")
        
    with c_d3:
        st.markdown("**3. Check**")
        h_prov = mat_props['h_slab']
        st.markdown(f"Provided ($h$): **{h_prov:.0f} cm**")
        if h_prov >= val_h_min:
            st.success("✅ PASS")
        else:
            st.error("❌ CHECK REQ.")
            
    st.markdown('</div>', unsafe_allow_html=True)

    # --- 4. LOADS ---
    st.header("4. Factored Load (wu)")
    st.markdown('<div class="step-container">', unsafe_allow_html=True)
    
    h_m = mat_props['h_slab'] / 100.0
    w_sw = h_m * 2400
    sdl = loads['SDL']
    ll = loads['LL']
    
    # Detailed Load Calc
    st.markdown("#### Calculation Details:")
    
    # Dead Load
    st.markdown(r"**1. Dead Load ($DL$)**")
    st.latex(fr"DL = ({h_m:.2f} \times 2400) + {sdl:.0f} (\text{{SDL}}) = {w_sw + sdl:,.0f} \text{{ kg/m}}^2")
    
    # Live Load
    st.markdown(r"**2. Live Load ($LL$)**")
    st.latex(fr"LL = {ll:,.0f} \text{{ kg/m}}^2")
    
    # Factored Load
    st.markdown(r"**3. Factored Load ($w_u$)**")
    st.latex(r"w_u = 1.2(DL) + 1.6(LL)")
    
    total_dl = w_sw + sdl
    wu_total = 1.2 * total_dl + 1.6 * ll
    
    st.latex(fr"w_u = 1.2({total_dl:,.0f}) + 1.6({ll:,.0f}) = \mathbf{{{wu_total:,.0f}}} \text{{ kg/m}}^2")
    
    # Summary Box
    st.markdown(f"""
    <div style="text-align:right; margin-top:15px; padding:15px; background-color:#e1f5fe; border-radius:5px;">
        <span style="margin-right:20px; font-weight:bold; color:#455a64;">Total Design Load (wu):</span>
        <span style="font-size:1.5rem; font-weight:800; color:#0277bd;">{wu_total:,.0f} kg/m²</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
