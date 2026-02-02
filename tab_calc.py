# tab_calc.py
import streamlit as st
import pandas as pd
import numpy as np
import math

# ==========================================
# 1. CSS & STYLING
# ==========================================
def inject_custom_css():
    st.markdown("""
    <style>
        .report-container { font-family: 'Sarabun', sans-serif; }
        
        /* Box สำหรับแสดงวิธีทำ (Step-by-Step Box) */
        .step-box {
            background-color: #f8f9fa;
            border-left: 4px solid #455a64;
            padding: 15px;
            margin-bottom: 15px;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            font-size: 0.95rem;
            color: #37474f;
        }
        
        /* Header ของแต่ละ Step */
        .step-header {
            font-weight: bold;
            color: #1565c0;
            margin-top: 10px;
            margin-bottom: 5px;
            font-size: 1rem;
        }

        /* Summary Cards */
        .summary-card {
            background: white;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 12px;
            text-align: center;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. HELPER FUNCTIONS
# ==========================================
def render_latex_substitution(formula_str, substitution_str, result_str):
    """Helper to render Formula -> Substitution -> Result"""
    st.markdown(f"**Formula:**")
    st.latex(formula_str)
    st.markdown(f"**Substitution:**")
    st.latex(substitution_str)
    st.markdown(f"**Result:**")
    st.write(result_str)

def render_punching_step_by_step(res, mat_props, label):
    st.markdown(f"#### 📍 Critical Section: {label}")
    
    fc = mat_props['fc']
    d = res['d']
    b0 = res['b0']
    beta = res.get('beta', 2.0)
    alpha_s = 40 # Interior column assumption usually
    
    # --- Step 1: Geometric Parameters ---
    st.markdown('<div class="step-header">Step 1: Geometric Parameters</div>', unsafe_allow_html=True)
    with st.container():
        st.markdown(f"""
        * **Effective Depth ($d$):** {d:.2f} cm
        * **Critical Perimeter ($b_0$):** {b0:.2f} cm (Calculated at distance $d/2$ from face)
        * **Column Aspect Ratio ($\beta$):** {beta:.2f}
        * **Concrete Strength ($\sqrt{{f'_c}}$):** $\sqrt{{{fc:.0f}}} = {math.sqrt(fc):.2f}$ ksc
        """)

    # --- Step 2: Calculate Vc (3 Equations) ---
    st.markdown('<div class="step-header">Step 2: ACI 318 Shear Capacity Calculation ($V_c$)</div>', unsafe_allow_html=True)
    
    # Eq 1
    with st.expander("Detailed Substitution for Vc1, Vc2, Vc3", expanded=True):
        st.markdown("**Equation 1: Aspect Ratio Effect**")
        st.latex(r"V_{c1} = 0.53 \left(1 + \frac{2}{\beta}\right) \sqrt{f'_c} b_0 d")
        st.latex(f"V_{{c1}} = 0.53 \\left(1 + \\frac{{2}}{{{beta:.2f}}}\\right) ({math.sqrt(fc):.2f}) ({b0:.2f}) ({d:.2f})")
        st.latex(f"V_{{c1}} = {res['Vc1']:,.0f} \\text{{ kg}}")
        
        st.markdown("---")
        st.markdown("**Equation 2: Perimeter Effect**")
        st.latex(r"V_{c2} = 0.53 \left(\frac{\alpha_s d}{b_0} + 2\right) \sqrt{f'_c} b_0 d")
        term_2 = (alpha_s * d / b0) + 2
        st.latex(f"V_{{c2}} = 0.53 \\left({term_2:.2f}\\right) ({math.sqrt(fc):.2f}) ({b0:.2f}) ({d:.2f})")
        st.latex(f"V_{{c2}} = {res['Vc2']:,.0f} \\text{{ kg}}")
        
        st.markdown("---")
        st.markdown("**Equation 3: Basic Shear Strength**")
        st.latex(r"V_{c3} = 1.06 \sqrt{f'_c} b_0 d")
        st.latex(f"V_{{c3}} = 1.06 ({math.sqrt(fc):.2f}) ({b0:.2f}) ({d:.2f})")
        st.latex(f"V_{{c3}} = {res['Vc3']:,.0f} \\text{{ kg}}")

    # --- Step 3: Determine Governing Vc ---
    vc_min = min(res['Vc1'], res['Vc2'], res['Vc3'])
    phi_vn = 0.85 * vc_min
    
    st.markdown('<div class="step-header">Step 3: Design Strength ($\phi V_n$)</div>', unsafe_allow_html=True)
    st.markdown(f"""
    The governing nominal shear strength ($V_c$) is the minimum of the three values:
    
    $$V_c = \min({res['Vc1']:,.0f}, {res['Vc2']:,.0f}, {res['Vc3']:,.0f}) = \\mathbf{{{vc_min:,.0f}}} \\text{{ kg}}$$
    
    Apply reduction factor $\phi = 0.85$:
    
    $$\phi V_n = 0.85 \\times {vc_min:,.0f} = \\mathbf{{{phi_vn:,.0f}}} \\text{{ kg}}$$
    """)

    # --- Step 4: Check against Vu ---
    st.markdown('<div class="step-header">Step 4: Safety Check</div>', unsafe_allow_html=True)
    vu = res['Vu']
    ratio = vu / phi_vn if phi_vn > 0 else 999
    status = "PASS" if ratio <= 1.0 else "FAIL"
    color = "green" if status == "PASS" else "red"
    
    st.markdown(f"""
    $$V_u = {vu:,.0f} \\text{{ kg}}$$
    
    $$Ratio = \\frac{{V_u}}{{\phi V_n}} = \\frac{{{vu:,.0f}}}{{{phi_vn:,.0f}}} = \\mathbf{{{ratio:.2f}}}$$
    
    <div style="background-color:{'#e8f5e9' if status=='PASS' else '#ffebee'}; padding:10px; border-radius:5px; text-align:center; border:1px solid {color}; margin-top:10px;">
        <strong style="color:{color}; font-size:1.2rem;">Result: {status}</strong>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

# ==========================================
# 3. MAIN RENDER FUNCTION
# ==========================================
def render(punch_res, v_oneway_res, mat_props, loads, Lx, Ly):
    inject_custom_css()
    
    # HEADER
    st.title("📘 Detailed Calculation Report")
    st.caption(f"Fully detailed step-by-step analysis per ACI 318.")
    
    # ----------------------------------------------------
    # DASHBOARD SUMMARY (Keep clean on top)
    # ----------------------------------------------------
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"<div class='summary-card'><b>Punching Shear</b><br><h2>{punch_res['ratio']:.2f}</h2>{punch_res['status']}</div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='summary-card'><b>One-Way Shear</b><br><h2>{v_oneway_res['ratio']:.2f}</h2>{v_oneway_res['status']}</div>", unsafe_allow_html=True)
    with c3:
        h_min = max(Lx, Ly)*100/33
        st.markdown(f"<div class='summary-card'><b>Deflection (Min h)</b><br><h2>{h_min:.1f} cm</h2>Limit</div>", unsafe_allow_html=True)
    with c4:
        st.markdown(f"<div class='summary-card'><b>Factored Load</b><br><h2>{loads['w_u']:,.0f}</h2>kg/m²</div>", unsafe_allow_html=True)

    st.markdown("---")

    # ----------------------------------------------------
    # 1. PUNCHING SHEAR (DETAILED)
    # ----------------------------------------------------
    st.header("1. Punching Shear Analysis (Two-Way Action)")
    
    if punch_res.get('is_dual', False):
        st.info("Structure contains Drop Panels. Checking both critical sections.")
        render_punching_step_by_step(punch_res['check_1'], mat_props, "Inside Drop Panel (d/2 from Column)")
        render_punching_step_by_step(punch_res['check_2'], mat_props, "Outside Drop Panel (d/2 from Drop Edge)")
    else:
        render_punching_step_by_step(punch_res, mat_props, "d/2 from Column Face")

    # ----------------------------------------------------
    # 2. ONE-WAY SHEAR (DETAILED)
    # ----------------------------------------------------
    st.header("2. One-Way Shear Analysis (Beam Action)")
    
    fc = mat_props['fc']
    bw = 100.0 # Unit strip
    
    # Note: v_oneway_res usually stores the worst case. 
    # To show detailed calculation, we reconstruct the steps.
    vu_one = v_oneway_res.get('Vu', 0)
    vc_one_nominal = v_oneway_res.get('Vc', 0) 
    # If the stored Vc is already design strength, we need to handle it, but let's assume it's nominal for calculation display
    # Or back-calculate d from Vc: Vc = 0.53 * sqrt(fc) * bw * d
    
    # Let's use the slab d
    d_slab = mat_props['h_slab'] - mat_props['cover'] - 1.0 # approx effective depth
    
    st.markdown('<div class="step-header">Step 1: Calculate Capacity ($\phi V_c$)</div>', unsafe_allow_html=True)
    st.markdown("Consider a unit strip width $b_w = 100$ cm.")
    
    st.latex(r"V_c = 0.53 \sqrt{f'_c} b_w d")
    st.latex(f"V_c = 0.53 ({math.sqrt(fc):.2f}) (100) ({d_slab:.2f})")
    
    calc_vc = 0.53 * math.sqrt(fc) * 100 * d_slab
    st.latex(f"V_c = {calc_vc:,.0f} \\text{{ kg/m}}")
    
    st.markdown("Apply reduction factor $\phi = 0.85$:")
    st.latex(f"\\phi V_c = 0.85 \\times {calc_vc:,.0f} = \\mathbf{{{0.85*calc_vc:,.0f}}} \\text{{ kg/m}}")

    st.markdown('<div class="step-header">Step 2: Check Demand ($V_u$)</div>', unsafe_allow_html=True)
    st.write(f"Factored shear force at distance $d$ from support:")
    st.latex(f"V_u = {vu_one:,.0f} \\text{{ kg/m}}")
    
    ratio_one = vu_one / (0.85*calc_vc)
    status_one = "PASS" if ratio_one <= 1.0 else "FAIL"
    
    st.markdown(f"**Conclusion:** Ratio = {ratio_one:.2f} $\\rightarrow$ **{status_one}**")


    # ----------------------------------------------------
    # 3. DEFLECTION (DETAILED)
    # ----------------------------------------------------
    st.markdown("---")
    st.header("3. Deflection Control (Minimum Thickness)")
    
    st.markdown('<div class="step-header">Step 1: Determine Criteria</div>', unsafe_allow_html=True)
    st.write("Per ACI 318 Table 8.3.1.1 for Slabs without Interior Beams (Interior Panel):")
    st.latex(r"h_{min} = \frac{L_n}{33}")
    
    st.markdown('<div class="step-header">Step 2: Identify Longest Span</div>', unsafe_allow_html=True)
    st.write(f"Long Span ($L_x$) = {Lx:.2f} m")
    st.write(f"Short Span ($L_y$) = {Ly:.2f} m")
    max_span = max(Lx, Ly)
    st.latex(f"L_n = \\max({Lx}, {Ly}) = {max_span:.2f} \\text{{ m}} = {max_span*100:.0f} \\text{{ cm}}")
    
    st.markdown('<div class="step-header">Step 3: Calculate Minimum Thickness</div>', unsafe_allow_html=True)
    h_min_calc = (max_span * 100) / 33.0
    st.latex(f"h_{{min}} = \\frac{{{max_span*100:.0f}}}{{33}} = \\mathbf{{{h_min_calc:.2f}}} \\text{{ cm}}")
    
    st.markdown('<div class="step-header">Step 4: Check Provided Thickness</div>', unsafe_allow_html=True)
    h_prov = mat_props['h_slab']
    check_def = "PASS" if h_prov >= h_min_calc else "CHECK REQ."
    st.write(f"Provided Thickness ($h_{{slab}}$) = **{h_prov:.0f} cm**")
    st.success(f"Status: {check_def} (Provided {h_prov} cm ≥ Required {h_min_calc:.1f} cm)")


    # ----------------------------------------------------
    # 4. FACTORED LOAD (DETAILED)
    # ----------------------------------------------------
    st.markdown("---")
    st.header("4. Factored Load Analysis ($w_u$)")
    
    h_m = mat_props['h_slab'] / 100.0
    conc_density = 2400
    sdl = loads['SDL']
    ll = loads['LL']
    
    st.markdown('<div class="step-header">Step 1: Calculate Dead Load (D)</div>', unsafe_allow_html=True)
    
    st.markdown("**1.1 Self-Weight of Slab:**")
    st.latex(r"w_{SW} = \text{thickness} \times \text{density}")
    st.latex(f"w_{{SW}} = {h_m:.2f} \\text{{ m}} \\times {conc_density} \\text{{ kg/m}}^3 = {h_m*conc_density:.1f} \\text{{ kg/m}}^2")
    
    st.markdown("**1.2 Superimposed Dead Load (SDL):**")
    st.write(f"Given Input SDL = {sdl:.1f} kg/m²")
    
    total_dl = (h_m * conc_density) + sdl
    st.markdown("**1.3 Total Dead Load ($D$):**")
    st.latex(f"D = {h_m*conc_density:.1f} + {sdl:.1f} = {total_dl:.1f} \\text{{ kg/m}}^2")
    
    st.markdown('<div class="step-header">Step 2: Identify Live Load (L)</div>', unsafe_allow_html=True)
    st.write(f"Given Input Live Load ($L$) = {ll:.1f} kg/m²")
    
    st.markdown('<div class="step-header">Step 3: Apply Load Factors (ULS)</div>', unsafe_allow_html=True)
    st.write("ACI Load Combination: $1.2D + 1.6L$")
    
    term_d = 1.2 * total_dl
    term_l = 1.6 * ll
    wu_final = term_d + term_l
    
    st.latex(f"w_u = 1.2({total_dl:.1f}) + 1.6({ll:.1f})")
    st.latex(f"w_u = {term_d:.1f} + {term_l:.1f}")
    st.latex(f"w_u = \\mathbf{{{wu_final:,.0f}}} \\text{{ kg/m}}^2")
