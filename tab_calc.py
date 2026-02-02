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
        .step-container {
            background-color: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            border: 1px solid #eceff1;
        }
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
        hr { margin: 30px 0; border: 0; border-top: 1px solid #e0e0e0; }
        
        /* Highlight result value */
        .calc-result {
            font-weight: bold;
            color: #0d47a1;
        }
    </style>
    """, unsafe_allow_html=True)

def render_step_header(number, text):
    st.markdown(f'<div class="step-title"><div class="step-icon">{number}</div>{text}</div>', unsafe_allow_html=True)

# ==========================================
# 2. CALCULATION RENDERERS
# ==========================================

def render_punching_detailed(res, mat_props, label):
    st.markdown(f"#### 📍 Critical Section: {label}")
    
    # Extract Variables
    fc = mat_props['fc']
    d = res['d']
    b0 = res['b0']
    beta = res.get('beta', 2.0)
    alpha_s = res.get('alpha_s', 40)
    
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
            st.markdown(f"**{math.sqrt(fc):.2f}** ksc")
        st.markdown('</div>', unsafe_allow_html=True)

    # --- Step 2: Nominal Capacity ---
    with st.container():
        st.markdown('<div class="step-container">', unsafe_allow_html=True)
        render_step_header(2, "Nominal Shear Strength (Vc)")
        st.write("Calculated based on ACI 318 (Min of 3 equations):")
        
        # Prepare strings for safe LaTeX injection
        sqrt_fc_val = math.sqrt(fc)
        
        eq1, eq2, eq3 = st.columns(3)
        
        # --- EQ 1 ---
        with eq1:
            st.markdown(r"**1. Aspect Ratio ($V_{c1}$)**")
            # Formula
            st.latex(r"V_{c1} = 0.53 \left(1 + \frac{2}{\beta}\right) \sqrt{f'_c} b_0 d")
            # Substitution
            term_beta = 1 + (2/beta)
            val_vc1 = 0.53 * term_beta * sqrt_fc_val * b0 * d
            st.latex(fr"= 0.53 \left(1 + \frac{{2}}{{{beta:.1f}}}\right) ({sqrt_fc_val:.2f}) ({b0:.0f}) ({d:.1f})")
            # Result
            st.markdown(f"<div class='calc-result'>= {val_vc1:,.0f} kg</div>", unsafe_allow_html=True)

        # --- EQ 2 ---
        with eq2:
            st.markdown(r"**2. Perimeter ($V_{c2}$)**")
            # Formula
            st.latex(r"V_{c2} = 0.53 \left(\frac{\alpha_s d}{b_0} + 2\right) \sqrt{f'_c} b_0 d")
            # Substitution
            term_peri = (alpha_s * d / b0) + 2
            val_vc2 = 0.53 * term_peri * sqrt_fc_val * b0 * d
            st.latex(fr"= 0.53 \left(\frac{{{alpha_s:.0f} \cdot {d:.1f}}}{{{b0:.0f}}} + 2\right) ({sqrt_fc_val:.2f}) ({b0:.0f}) ({d:.1f})")
            # Result
            st.markdown(f"<div class='calc-result'>= {val_vc2:,.0f} kg</div>", unsafe_allow_html=True)

        # --- EQ 3 ---
        with eq3:
            st.markdown(r"**3. Basic ($V_{c3}$)**")
            # Formula
            st.latex(r"V_{c3} = 1.06 \sqrt{f'_c} b_0 d")
            # Substitution
            val_vc3 = 1.06 * sqrt_fc_val * b0 * d
            st.latex(fr"= 1.06 ({sqrt_fc_val:.2f}) ({b0:.0f}) ({d:.1f})")
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
            
            # Show the calculation for phi Vn
            st.latex(r"\phi V_n = \phi \times V_{c,min}")
            st.latex(fr"= 0.85 \times {vc_min:,.0f} = \mathbf{{{phi_vn:,.0f}}} \text{{ kg}}")
            
            st.markdown("---")
            # Comparison
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
    d_slab = mat_props['h_slab'] - mat_props['cover'] - 1.0
    bw = 100.0
    
    # Nominal Vc
    vc_nominal_calc = 0.53 * math.sqrt(fc) * bw * d_slab
    phi = 0.85
    phi_vc = phi * vc_nominal_calc
    
    # Vu Demand (Assume coming from logic, we calculate backward for display if needed)
    vu_one = v_oneway_res.get('Vu', 0)
    
    c_cap, c_dem = st.columns(2)
    
    with c_cap:
        render_step_header("A", "Capacity (φVc)")
        st.markdown(r"Unit strip $b_w = 100$ cm")
        # Formula
        st.latex(r"V_c = 0.53 \sqrt{f'_c} b_w d")
        # Substitution
        st.latex(fr"= 0.53 ({math.sqrt(fc):.2f}) (100) ({d_slab:.2f})")
        # Result Vc
        st.markdown(f"> $V_c =$ **{vc_nominal_calc:,.0f}** kg/m")
        st.markdown("---")
        # Design Capacity
        st.latex(r"\phi V_c = 0.85 \times V_c")
        st.latex(fr"= 0.85 \times {vc_nominal_calc:,.0f} = \mathbf{{{phi_vc:,.0f}}} \text{{ kg/m}}")

    with c_dem:
        render_step_header("B", "Demand (Vu)")
        st.markdown(r"At distance $d$ from support:")
        
        # Assuming simplified Vu = wu * (Ln/2 - d) for display purpose
        # We need wu (factored load)
        h_m = mat_props['h_slab'] / 100.0
        w_sw = h_m * 2400
        sdl = loads['SDL']
        ll = loads['LL']
        wu_val = (1.2 * (w_sw + sdl)) + (1.6 * ll)
        
        # Back-calculate Ln/2 roughly for display, or use variables passed
        # This is just for "Show your work" visualization
        ln_approx = (vu_one / wu_val) + (d_slab/100) # approximate
        
        st.latex(r"V_u = w_u \left(\frac{L_n}{2} - d\right)")
        # Substitution
        d_m = d_slab / 100.0
        st.latex(fr"= {wu_val:,.0f} \left( \text{{span}} - {d_m:.2f} \right)")
        
        color_vu_one = "black" if vu_one <= phi_vc else "red"
        st.latex(fr"V_u = \textcolor{{{color_vu_one}}}{{\mathbf{{{vu_one:,.0f}}}}} \text{{ kg/m}}")
    
    st.markdown("---")
    # Conclusion
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
        # Substitution
        val_h_min = max_span*100/33
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
    
    # Calculation Steps for Total Load
    st.markdown("#### Calculation of Factored Load:")
    
    # Dead Load Calc
    st.markdown(r"**1. Dead Load ($DL$)**")
    st.latex(r"DL = \text{Self Weight} + \text{SDL}")
    st.latex(fr"DL = ({h_m:.2f} \times 2400) + {sdl:.0f} = {w_sw:.0f} + {sdl:.0f} = {w_sw + sdl:,.0f} \text{{ kg/m}}^2")
    
    # Live Load
    st.markdown(r"**2. Live Load ($LL$)**")
    st.latex(fr"LL = {ll:,.0f} \text{{ kg/m}}^2")
    
    # Factored Load
    st.markdown(r"**3. Total Factored Load ($w_u$)**")
    st.latex(r"w_u = 1.2(DL) + 1.6(LL)")
    # Substitution
    total_dl = w_sw + sdl
    wu_total = 1.2 * total_dl + 1.6 * ll
    st.latex(fr"w_u = 1.2({total_dl:.0f}) + 1.6({ll:.0f})")
    # Result
    st.latex(fr"w_u = {1.2*total_dl:,.0f} + {1.6*ll:,.0f} = \mathbf{{{wu_total:,.0f}}} \text{{ kg/m}}^2")
    
    # Summary Table (Optional now, but good for quick look)
    st.markdown("---")
    st.caption("Load Summary Table")
    data = [
        {"Type": "Dead (SW+SDL)", "Service": total_dl, "Factor": 1.2, "Factored": total_dl*1.2},
        {"Type": "Live (LL)",     "Service": ll,       "Factor": 1.6, "Factored": ll*1.6},
    ]
    df = pd.DataFrame(data)
    st.table(df.style.format({"Service": "{:,.0f}", "Factored": "{:,.0f}", "Factor": "{:.1f}"}))
    
    st.markdown('</div>', unsafe_allow_html=True)
