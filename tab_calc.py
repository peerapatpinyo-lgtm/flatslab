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
        .step-icon { margin-right: 10px; background: #37474f; color: white; width: 24px; height: 24px; text-align: center; border-radius: 50%; font-size: 0.8rem; line-height: 24px; }
        
        .eq-box {
            background: #ffffff;
            border: 1px dashed #b0bec5;
            border-radius: 6px;
            padding: 10px;
            margin: 10px 0;
            text-align: center;
        }
        
        .verdict-box {
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            font-weight: bold;
            margin-top: 15px;
        }
        .pass { background-color: #e8f5e9; color: #2e7d32; border: 1px solid #a5d6a7; }
        .fail { background-color: #ffebee; color: #c62828; border: 1px solid #ef9a9a; }
        
        /* Custom Metric to allow LaTeX */
        .custom-metric {
            text-align: center;
        }
        .custom-metric-label { font-size: 0.85rem; color: #616161; margin-bottom: 4px; }
        .custom-metric-value { font-size: 1.2rem; font-weight: 600; color: #000; }
        
        hr { margin: 30px 0; border: 0; border-top: 1px solid #e0e0e0; }
    </style>
    """, unsafe_allow_html=True)

def render_step_header(number, text):
    st.markdown(f'<div class="step-title"><div class="step-icon">{number}</div>{text}</div>', unsafe_allow_html=True)

def render_latex_metric(label_latex, value_str, sub_text=""):
    st.markdown(f"""
    <div class="custom-metric">
        <div class="custom-metric-label">{label_latex}</div>
        <div class="custom-metric-value">{value_str}</div>
        <div style="font-size:0.75rem; color:#888;">{sub_text}</div>
    </div>
    """, unsafe_allow_html=True)

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
        with c1: render_latex_metric(r"Effective Depth ($d$)", f"{d:.2f} cm")
        with c2: render_latex_metric(r"Perimeter ($b_0$)", f"{b0:.2f} cm")
        with c3: render_latex_metric(r"Aspect Ratio ($\beta$)", f"{beta:.2f}")
        with c4: render_latex_metric(r"Concrete ($\sqrt{f'_c}$)", f"{math.sqrt(fc):.2f} ksc")
        st.markdown('</div>', unsafe_allow_html=True)

    # --- Step 2: Nominal Capacity ---
    with st.container():
        st.markdown('<div class="step-container">', unsafe_allow_html=True)
        render_step_header(2, "Nominal Shear Strength ($V_c$)")
        st.write("Using ACI 318 criteria (Min of 3 equations):")
        
        eq1, eq2, eq3 = st.columns(3)
        
        # Eq 1
        with eq1:
            st.markdown(r"**1. Aspect Ratio ($V_{c1}$)**")
            st.latex(r"0.53 \left(1 + \frac{2}{\beta}\right) \sqrt{f'_c} b_0 d")
            term_beta = 1 + (2/beta)
            val_vc1 = 0.53 * term_beta * math.sqrt(fc) * b0 * d
            st.markdown(f"<div class='eq-box'>$V_{{c1}} =$ <b>{val_vc1:,.0f}</b> kg</div>", unsafe_allow_html=True)

        # Eq 2
        with eq2:
            st.markdown(r"**2. Perimeter ($V_{c2}$)**")
            st.latex(r"0.53 \left(\frac{\alpha_s d}{b_0} + 2\right) \sqrt{f'_c} b_0 d")
            term_peri = (alpha_s * d / b0) + 2
            val_vc2 = 0.53 * term_peri * math.sqrt(fc) * b0 * d
            st.markdown(f"<div class='eq-box'>$V_{{c2}} =$ <b>{val_vc2:,.0f}</b> kg</div>", unsafe_allow_html=True)

        # Eq 3
        with eq3:
            st.markdown(r"**3. Basic ($V_{c3}$)**")
            st.latex(r"1.06 \sqrt{f'_c} b_0 d")
            val_vc3 = 1.06 * math.sqrt(fc) * b0 * d
            st.markdown(f"<div class='eq-box'>$V_{{c3}} =$ <b>{val_vc3:,.0f}</b> kg</div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # --- Step 3: Design Check ---
    with st.container():
        st.markdown('<div class="step-container">', unsafe_allow_html=True)
        render_step_header(3, "Design Check")
        
        vc_min = min(val_vc1, val_vc2, val_vc3)
        phi = 0.85
        phi_vn = phi * vc_min
        vu = res['Vu']
        
        # Determine Status
        passed = phi_vn >= vu
        status_text = "PASS" if passed else "FAIL"
        operator = r"\geq" if passed else "<" # Use < if fail to emphasize inadequacy
        color_vu = "black" if passed else "#d32f2f"
        
        c_left, c_right = st.columns([2, 1])
        
        with c_left:
            st.markdown("Comparing Design Capacity vs. Factored Demand:")
            
            # Show the comparison clearly with Math
            st.latex(r"\phi V_n \quad \text{vs} \quad V_u")
            st.latex(f"{phi_vn:,.0f} \\; {operator} \\; {vu:,.0f}")
            
            st.markdown("---")
            st.markdown(f"- Nominal Capacity ($V_c$) = **{vc_min:,.0f}** kg")
            st.markdown(f"- Design Capacity ($\phi V_n$) = **{phi_vn:,.0f}** kg")
            st.markdown(f"- Factored Demand ($V_u$) = <b style='color:{color_vu}'>{vu:,.0f}</b> kg", unsafe_allow_html=True)
        
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
    
    vc_nominal_calc = 0.53 * math.sqrt(fc) * bw * d_slab
    phi = 0.85
    phi_vc = phi * vc_nominal_calc
    vu_one = v_oneway_res.get('Vu', 0)
    
    c_cap, c_dem = st.columns(2)
    
    with c_cap:
        render_step_header("A", "Capacity ($\phi V_c$)")
        st.markdown(r"Unit strip $b_w = 100$ cm")
        st.latex(r"V_c = 0.53 \sqrt{f'_c} b_w d")
        st.latex(f"V_c = 0.53 ({math.sqrt(fc):.2f}) (100) ({d_slab:.2f})")
        st.markdown(f"Design $\phi V_c$ = **{phi_vc:,.0f}** kg/m")

    with c_dem:
        render_step_header("B", "Demand ($V_u$)")
        st.markdown(r"At distance $d$ from support:")
        st.latex(r"V_u = w_u (L_n/2 - d)")
        
        # Color logic
        color_vu = "black" if vu_one <= phi_vc else "#d32f2f"
        st.markdown(f"<h3 style='text-align:center; color:{color_vu}'>$V_u =$ {vu_one:,.0f} kg/m</h3>", unsafe_allow_html=True)
    
    # Verdict
    st.markdown("---")
    passed_one = vu_one <= phi_vc
    op_one = r"\leq" if passed_one else ">"
    status_one = "PASS" if passed_one else "FAIL"
    icon = "✅" if passed_one else "❌"
    
    st.markdown(f"**Conclusion:** $V_u$ ({vu_one:,.0f}) ${op_one}$ $\phi V_c$ ({phi_vc:,.0f}) $\\rightarrow$ {icon} **{status_one}**")
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
        st.latex(f"h_{{min}} = \\mathbf{{{max_span*100/33:.2f}}} \\text{{ cm}}")
        
    with c_d3:
        st.markdown("**3. Check**")
        h_prov = mat_props['h_slab']
        st.markdown(f"Provided ($h$): **{h_prov:.0f} cm**")
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
    
    st.markdown(f"""
    <div style="text-align:right; padding:15px; background-color:#e1f5fe; border-radius:5px;">
        <span style="margin-right:20px; font-weight:bold; color:#455a64;">Total Design Load ($w_u$):</span>
        <span style="font-size:1.5rem; font-weight:800; color:#0277bd;">{wu_total:,.0f} kg/m²</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
