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
        /* Main Container Font */
        .report-container { font-family: 'Segoe UI', Tahoma, sans-serif; }
        
        /* Step Containers */
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

        /* Formula Box */
        .eq-box {
            background: #ffffff;
            border: 1px dashed #b0bec5;
            border-radius: 6px;
            padding: 10px;
            margin: 10px 0;
            text-align: center;
        }
        
        /* Result/Verdict Box */
        .verdict-box {
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            font-weight: bold;
            margin-top: 15px;
        }
        .pass { background-color: #e8f5e9; color: #2e7d32; border: 1px solid #a5d6a7; }
        .fail { background-color: #ffebee; color: #c62828; border: 1px solid #ef9a9a; }
        
        /* Custom Divider */
        hr { margin: 30px 0; border: 0; border-top: 1px solid #e0e0e0; }
    </style>
    """, unsafe_allow_html=True)

def render_step_header(number, text):
    st.markdown(f'<div class="step-title"><div class="step-icon">{number}</div>{text}</div>', unsafe_allow_html=True)

# ==========================================
# 2. DETAILED RENDERERS
# ==========================================

def render_punching_detailed(res, mat_props, label):
    st.markdown(f"#### 📍 Checking: {label}")
    
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
        c1.metric("Eff. Depth (d)", f"{d:.2f} cm")
        c2.metric("Perimeter (b0)", f"{b0:.2f} cm")
        c3.metric("Beta (β)", f"{beta:.2f}")
        c4.metric("Alpha (αs)", f"{alpha_s}")
        st.caption(f"*Note: $b_0$ is critical perimeter at $d/2$ from support face. $\\sqrt{{f'_c}} = {math.sqrt(fc):.2f}$ ksc*")
        st.markdown('</div>', unsafe_allow_html=True)

    # --- Step 2: Capacity Vc ---
    with st.container():
        st.markdown('<div class="step-container">', unsafe_allow_html=True)
        render_step_header(2, "Shear Capacity Calculation ($V_c$)")
        st.info("The nominal shear strength ($V_c$) is the **minimum** of the following three ACI 318 equations:")
        
        eq1, eq2, eq3 = st.columns(3)
        
        # Equation 1
        with eq1:
            st.markdown("**Eq. 1: Aspect Ratio**")
            st.latex(r"V_{c1} = 0.53 \left(1 + \frac{2}{\beta}\right) \sqrt{f'_c} b_0 d")
            term_beta = 1 + (2/beta)
            val_vc1 = 0.53 * term_beta * math.sqrt(fc) * b0 * d
            st.caption("Substitution:")
            st.latex(f"0.53 ({term_beta:.2f}) ({math.sqrt(fc):.2f}) ({b0:.0f}) ({d:.0f})")
            st.markdown(f"<div class='eq-box'><b>{val_vc1:,.0f}</b> kg</div>", unsafe_allow_html=True)

        # Equation 2
        with eq2:
            st.markdown("**Eq. 2: Perimeter**")
            st.latex(r"V_{c2} = 0.53 \left(\frac{\alpha_s d}{b_0} + 2\right) \sqrt{f'_c} b_0 d")
            term_peri = (alpha_s * d / b0) + 2
            val_vc2 = 0.53 * term_peri * math.sqrt(fc) * b0 * d
            st.caption("Substitution:")
            st.latex(f"0.53 ({term_peri:.2f}) ({math.sqrt(fc):.2f}) ({b0:.0f}) ({d:.0f})")
            st.markdown(f"<div class='eq-box'><b>{val_vc2:,.0f}</b> kg</div>", unsafe_allow_html=True)

        # Equation 3
        with eq3:
            st.markdown("**Eq. 3: Basic**")
            st.latex(r"V_{c3} = 1.06 \sqrt{f'_c} b_0 d")
            val_vc3 = 1.06 * math.sqrt(fc) * b0 * d
            st.caption("Substitution:")
            st.latex(f"1.06 ({math.sqrt(fc):.2f}) ({b0:.0f}) ({d:.0f})")
            st.markdown(f"<div class='eq-box'><b>{val_vc3:,.0f}</b> kg</div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # --- Step 3: Verdict (Check) ---
    with st.container():
        st.markdown('<div class="step-container">', unsafe_allow_html=True)
        # แก้ไข Title ให้ชัดเจน
        render_step_header(3, r"Design Check ($\phi V_n \geq V_u$)")
        
        # Logic
        vc_min = min(val_vc1, val_vc2, val_vc3)
        phi = 0.85
        phi_vn = phi * vc_min
        vu = res['Vu']
        ratio = vu / phi_vn
        status = "PASS" if ratio <= 1.0 else "FAIL"
        
        # Display Logic
        res_L, res_R = st.columns([2, 1])
        
        with res_L:
            # Color logic for Vu: Red only if Fail
            vu_color = "#d32f2f" if status == "FAIL" else "#333333"
            
            st.write("Comparing Design Capacity vs. Factored Demand:")
            st.latex(r"\phi V_n \geq V_u")
            
            # แสดงการเปรียบเทียบตัวเลขจริง
            st.latex(f"{phi_vn:,.0f} \\geq {vu:,.0f}")
            
            st.markdown("---")
            st.write(f"• Governing $V_c$ (Min): **{vc_min:,.0f}** kg")
            st.write(f"• Design Capacity ($\phi V_n$): **{phi_vn:,.0f}** kg")
            st.markdown(f"• Factored Demand ($V_u$): <b style='color:{vu_color}'>{vu:,.0f}</b> kg", unsafe_allow_html=True)
        
        with res_R:
            cls = "pass" if status == "PASS" else "fail"
            st.markdown(f"""
            <div class="verdict-box {cls}">
                <div style="font-size:0.9rem;">Capacity Ratio</div>
                <div style="font-size:2rem;">{ratio:.2f}</div>
                <div>{status}</div>
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
    st.caption(f"Reference: ACI 318 / EIT Standard (Method of Limit States)")
    st.markdown("---")

    # --- 1. PUNCHING SHEAR ---
    st.header("1. Punching Shear Analysis")
    if punch_res.get('is_dual', False):
        tab1, tab2 = st.tabs(["Inner Section (Column Face)", "Outer Section (Drop Panel)"])
        with tab1: render_punching_detailed(punch_res['check_1'], mat_props, "d/2 from Column Face")
        with tab2: render_punching_detailed(punch_res['check_2'], mat_props, "d/2 from Drop Panel Edge")
    else:
        render_punching_detailed(punch_res, mat_props, "d/2 from Column Face")

    # --- 2. ONE-WAY SHEAR ---
    st.header("2. One-Way Shear Analysis")
    st.markdown('<div class="step-container">', unsafe_allow_html=True)
    
    col_cap, col_dem = st.columns(2)
    
    fc = mat_props['fc']
    d_slab = mat_props['h_slab'] - mat_props['cover'] - 1.0
    bw = 100.0
    
    vc_nominal_calc = 0.53 * math.sqrt(fc) * bw * d_slab
    phi = 0.85
    phi_vc = phi * vc_nominal_calc
    vu_one = v_oneway_res.get('Vu', 0)
    
    with col_cap:
        render_step_header("A", "Capacity ($\phi V_c$)")
        st.write("Unit strip width $b_w=100$ cm")
        st.latex(r"V_c = 0.53 \sqrt{f'_c} b_w d")
        st.latex(f"V_c = 0.53 ({math.sqrt(fc):.2f}) (100) ({d_slab:.2f})")
        st.markdown(f"**Design $\phi V_c$** = **{phi_vc:,.0f}** kg/m")

    with col_dem:
        render_step_header("B", "Demand ($V_u$)")
        st.write("Critical section at distance $d$ from support.")
        st.latex(r"V_u = w_u (L_{clear}/2 - d)")
        # สี Vu เปลี่ยนตามสถานะ
        vu_color_one = "#d32f2f" if vu_one > phi_vc else "#333"
        st.markdown(f"<h3 style='text-align:center; color:{vu_color_one}'>{vu_one:,.0f} kg/m</h3>", unsafe_allow_html=True)
    
    # Verdict
    st.markdown("---")
    ratio_one = vu_one / phi_vc
    status_one = "PASS" if ratio_one <= 1.0 else "FAIL"
    icon = "✅" if status_one == "PASS" else "❌"
    
    st.markdown(f"**Conclusion:** Ratio = {vu_one:,.0f} / {phi_vc:,.0f} = **{ratio_one:.2f}** {icon} **{status_one}**")
    st.markdown('</div>', unsafe_allow_html=True)

    # --- 3. DEFLECTION ---
    st.header("3. Deflection Control")
    st.markdown('<div class="step-container">', unsafe_allow_html=True)
    
    c_d1, c_d2, c_d3 = st.columns([1, 1.5, 1])
    
    with c_d1:
        st.markdown("**1. Span Data**")
        max_span = max(Lx, Ly)
        st.write(f"Longest Span ($L$): **{max_span:.2f} m**")
    
    with c_d2:
        st.markdown("**2. Minimum Thickness**")
        st.latex(r"h_{min} = L/33")
        st.latex(f"h_{{min}} = {max_span*100:.0f}/33 = \\mathbf{{{max_span*100/33:.2f}}} \\text{{ cm}}")
        
    with c_d3:
        st.markdown("**3. Check**")
        h_prov = mat_props['h_slab']
        status_def = "PASS" if h_prov >= (max_span*100/33) else "CHECK REQ."
        st.write(f"Provided: **{h_prov:.0f} cm**")
        if status_def == "PASS":
            st.success("✅ PASS")
        else:
            st.error("❌ CHECK REQ.")
            
    st.markdown('</div>', unsafe_allow_html=True)

    # --- 4. LOADS ---
    st.header("4. Factored Load Analysis")
    st.markdown('<div class="step-container">', unsafe_allow_html=True)
    
    h_m = mat_props['h_slab'] / 100.0
    w_sw = h_m * 2400
    sdl = loads['SDL']
    ll = loads['LL']
    
    data = [
        {"Load Case": "Dead Load (Self-Weight)", "Calculation": f"{h_m:.2f}m × 2400", "Service Load": w_sw, "Factor": 1.2, "Factored Load": w_sw*1.2},
        {"Load Case": "Dead Load (SDL)", "Calculation": "User Input", "Service Load": sdl, "Factor": 1.2, "Factored Load": sdl*1.2},
        {"Load Case": "Live Load (LL)", "Calculation": "User Input", "Service Load": ll, "Factor": 1.6, "Factored Load": ll*1.6},
    ]
    df = pd.DataFrame(data)
    wu_total = df["Factored Load"].sum()
    
    st.table(df.style.format({
        "Service Load": "{:,.1f}", 
        "Factored Load": "{:,.1f}",
        "Factor": "{:.1f}"
    }))
    
    st.markdown(f"""
    <div style="text-align:right; padding:15px; background-color:#e1f5fe; border-radius:5px;">
        <span style="margin-right:20px; font-weight:bold; color:#455a64;">Total Design Load ($w_u$):</span>
        <span style="font-size:1.5rem; font-weight:800; color:#0277bd;">{wu_total:,.0f} kg/m²</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
