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

        /* Result Box Style (Applied via Markdown Quote) */
        blockquote {
            background-color: #ffffff;
            border-left: 5px solid #b0bec5;
            padding: 10px;
            font-size: 1rem;
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
        
        hr { margin: 30px 0; border: 0; border-top: 1px solid #e0e0e0; }
    </style>
    """, unsafe_allow_html=True)

def render_step_header(number, text):
    # Function to render header cleanly
    st.markdown(f'<div class="step-title"><div class="step-icon">{number}</div>{text}</div>', unsafe_allow_html=True)

def render_latex_kv(key_latex, value_str):
    # Render Key-Value Pair safely
    st.markdown(f"**{key_latex}**")
    st.markdown(f"### {value_str}")

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
        render_step_header(2, "Nominal Shear Strength ($V_c$)")
        st.write("Calculated based on ACI 318 (Minimum of 3 equations):")
        
        eq1, eq2, eq3 = st.columns(3)
        
        # Note: We use st.latex for equations and st.markdown for results to ensure no $ leaks
        
        # Eq 1
        with eq1:
            st.markdown(r"**1. Aspect Ratio ($V_{c1}$)**")
            st.latex(r"V_{c1} = 0.53 \left(1 + \frac{2}{\beta}\right) \sqrt{f'_c} b_0 d")
            term_beta = 1 + (2/beta)
            val_vc1 = 0.53 * term_beta * math.sqrt(fc) * b0 * d
            # Result Display
            st.markdown(rf"> $V_{{c1}} =$ **{val_vc1:,.0f}** kg")

        # Eq 2
        with eq2:
            st.markdown(r"**2. Perimeter ($V_{c2}$)**")
            st.latex(r"V_{c2} = 0.53 \left(\frac{\alpha_s d}{b_0} + 2\right) \sqrt{f'_c} b_0 d")
            term_peri = (alpha_s * d / b0) + 2
            val_vc2 = 0.53 * term_peri * math.sqrt(fc) * b0 * d
            # Result Display
            st.markdown(rf"> $V_{{c2}} =$ **{val_vc2:,.0f}** kg")

        # Eq 3
        with eq3:
            st.markdown(r"**3. Basic ($V_{c3}$)**")
            st.latex(r"V_{c3} = 1.06 \sqrt{f'_c} b_0 d")
            val_vc3 = 1.06 * math.sqrt(fc) * b0 * d
            # Result Display
            st.markdown(rf"> $V_{{c3}} =$ **{val_vc3:,.0f}** kg")
        
        st.markdown('</div>', unsafe_allow_html=True)

    # --- Step 3: Design Check ---
    with st.container():
        st.markdown('<div class="step-container">', unsafe_allow_html=True)
        render_step_header(3, "Design Check")
        
        vc_min = min(val_vc1, val_vc2, val_vc3)
        phi = 0.85
        phi_vn = phi * vc_min
        vu = res['Vu']
        
        # Status Logic
        passed = phi_vn >= vu
        status_text = "PASS" if passed else "FAIL"
        
        # Color logic for Math (Red if fail)
        color_vu = "black" if passed else "red"
        operator = r"\geq" if passed else "<"
        
        c_left, c_right = st.columns([2, 1])
        
        with c_left:
            st.markdown("Comparing Design Capacity vs. Factored Demand:")
            
            # Main Comparison Equation (LaTeX handles color safely)
            st.latex(rf"\phi V_n \quad \text{{vs}} \quad V_u")
            st.latex(rf"{phi_vn:,.0f} \quad {operator} \quad \textcolor{{{color_vu}}}{{{vu:,.0f}}}")
            
            st.markdown("---")
            # Summary List using standard Markdown to prevent HTML issues
            st.markdown(rf"- Nominal Capacity ($V_c$): **{vc_min:,.0f}** kg")
            st.markdown(rf"- Design Capacity ($\phi V_n$): **{phi_vn:,.0f}** kg")
            # Use LaTeX color for consistent Vu rendering
            st.markdown(rf"- Factored Demand ($V_u$): $\textcolor{{{color_vu}}}{{\mathbf{{{vu:,.0f}}}}}}$ kg")
        
        with c_right:
            cls = "pass" if passed else "fail"
            ratio = vu / phi_vn
            # HTML only for the box container, no math inside
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
    
    vc_nominal_calc = 0.53 * math.sqrt(fc) * bw * d_slab
    phi = 0.85
    phi_vc = phi * vc_nominal_calc
    vu_one = v_oneway_res.get('Vu', 0)
    
    c_cap, c_dem = st.columns(2)
    
    with c_cap:
        render_step_header("A", "Capacity ($\phi V_c$)")
        st.markdown(r"Unit strip $b_w = 100$ cm")
        st.latex(r"V_c = 0.53 \sqrt{f'_c} b_w d")
        st.latex(rf"V_c = 0.53 ({math.sqrt(fc):.2f}) (100) ({d_slab:.2f})")
        st.markdown(rf"Design $\phi V_c$ = **{phi_vc:,.0f}** kg/m")

    with c_dem:
        render_step_header("B", "Demand ($V_u$)")
        st.markdown(r"At distance $d$ from support:")
        st.latex(r"V_u = w_u (L_n/2 - d)")
        
        # Color logic for One-Way
        color_vu_one = "black" if vu_one <= phi_vc else "red"
        st.latex(rf"V_u = \textcolor{{{color_vu_one}}}{{\mathbf{{{vu_one:,.0f}}}}} \text{{ kg/m}}")
    
    # Verdict
    st.markdown("---")
    passed_one = vu_one <= phi_vc
    op_one = r"\leq" if passed_one else ">"
    status_one = "PASS" if passed_one else "FAIL"
    icon = "✅" if passed_one else "❌"
    
    # Conclusion Line
    st.markdown(rf"**Conclusion:** $V_u$ ({vu_one:,.0f}) ${op_one}$ $\phi V_c$ ({phi_vc:,.0f}) $\rightarrow$ {icon} **{status_one}**")
    st.markdown('</div>', unsafe_allow_html=True)

    # --- 3. DEFLECTION ---
    st.header("3. Deflection Control")
    st.markdown('<div class="step-container">', unsafe_allow_html=True)
    
    c_d1, c_d2, c_d3 = st.columns([1, 1.5, 1])
    max_span = max(Lx, Ly)
    
    with c_d1:
        st.markdown("**1. Span Data**")
        st.markdown(rf"Longest Span ($L$): **{max_span:.2f} m**")
    
    with c_d2:
        st.markdown("**2. ACI Formula**")
        st.latex(r"h_{min} = \frac{L}{33}")
        st.latex(rf"h_{{min}} = \mathbf{{{max_span*100/33:.2f}}} \text{{ cm}}")
        
    with c_d3:
        st.markdown("**3. Check**")
        h_prov = mat_props['h_slab']
        st.markdown(rf"Provided ($h$): **{h_prov:.0f} cm**")
        if h_prov >= (max_span*100/33):
            st.success("✅ PASS")
        else:
            st.error("❌ CHECK REQ.")
            
    st.markdown('</div>', unsafe_allow_html=True)

    # --- 4. LOADS ---
    st.header("4. Factored Load ($w_u$)")
    st.markdown('<div class="step-container">', unsafe_allow_html=True)
    
    h_m = mat_props['h_slab'] / 100.0
    w_sw = h_m * 2400
    sdl = loads['SDL']
    ll = loads['LL']
    
    # Create nice DataFrame
    data = [
        {"Type": "Dead (Self-Weight)", "Service Load": w_sw, "Factor": 1.2, "Factored": w_sw*1.2},
        {"Type": "Dead (SDL)",         "Service Load": sdl,  "Factor": 1.2, "Factored": sdl*1.2},
        {"Type": "Live Load (LL)",     "Service Load": ll,   "Factor": 1.6, "Factored": ll*1.6},
    ]
    df = pd.DataFrame(data)
    wu_total = df["Factored"].sum()
    
    st.table(df.style.format({
        "Service Load": "{:,.1f}", 
        "Factored": "{:,.1f}",
        "Factor": "{:.1f}"
    }))
    
    # Total Load Summary
    st.markdown(rf"""
    <div style="text-align:right; padding:15px; background-color:#e1f5fe; border-radius:5px;">
        <span style="margin-right:20px; font-weight:bold; color:#455a64;">Total Design Load ($w_u$):</span>
        <span style="font-size:1.5rem; font-weight:800; color:#0277bd;">{wu_total:,.0f} kg/m²</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
