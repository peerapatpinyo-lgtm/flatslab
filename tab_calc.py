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
        
        /* 1. Dashboard Cards (Top Summary) */
        .metric-container {
            background-color: #ffffff;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 15px 10px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            height: 100%;
        }
        .metric-title { font-size: 0.85rem; color: #616161; font-weight: 600; text-transform: uppercase; }
        .metric-value { font-size: 1.5rem; font-weight: 800; color: #1565c0; margin: 5px 0; }
        
        /* 2. Step Containers */
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

        /* 3. Formula Box */
        .eq-box {
            background: #ffffff;
            border: 1px dashed #b0bec5;
            border-radius: 6px;
            padding: 10px;
            margin: 10px 0;
            text-align: center;
        }
        
        /* 4. Result/Verdict Box */
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

# ==========================================
# 2. HELPER COMPONENTS
# ==========================================
def render_summary_card(title, value, status, suffix=""):
    icon = "✅" if status == "PASS" else ("❌" if status == "FAIL" else "ℹ️")
    color = "#2e7d32" if status == "PASS" else ("#c62828" if status == "FAIL" else "#1565c0")
    st.markdown(f"""
    <div class="metric-container">
        <div class="metric-title">{title}</div>
        <div class="metric-value" style="color:{color}">{value}</div>
        <div style="font-size:0.8rem; color:#757575;">{icon} {status} {suffix}</div>
    </div>
    """, unsafe_allow_html=True)

def render_step_header(number, text):
    st.markdown(f'<div class="step-title"><div class="step-icon">{number}</div>{text}</div>', unsafe_allow_html=True)

# ==========================================
# 3. DETAILED RENDERERS
# ==========================================

def render_punching_detailed(res, mat_props, label):
    st.markdown(f"#### 📍 Checking: {label}")
    
    fc = mat_props['fc']
    d = res['d']
    b0 = res['b0']
    beta = res.get('beta', 2.0)
    
    with st.container():
        st.markdown('<div class="step-container">', unsafe_allow_html=True)
        render_step_header(1, "Geometry & Material Properties")
        
        # Grid Layout for Inputs
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Effective Depth (d)", f"{d:.2f} cm")
        c2.metric("Perimeter (b0)", f"{b0:.2f} cm")
        c3.metric("Beta (β)", f"{beta:.2f}")
        c4.metric("Sqrt(fc')", f"{math.sqrt(fc):.2f} ksc")
        st.markdown('</div>', unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="step-container">', unsafe_allow_html=True)
        render_step_header(2, "Shear Capacity Calculation (ACI 318)")
        st.info("The nominal shear strength ($V_c$) is the smallest of the following three equations:")
        
        # 3-Column Layout for Equations (Best for comparison)
        eq1, eq2, eq3 = st.columns(3)
        
        with eq1:
            st.markdown("**Eq. 1: Aspect Ratio**")
            st.latex(r"V_{c1} = 0.53 (1 + \frac{2}{\beta}) \sqrt{f'_c} b_0 d")
            st.caption("Substitution:")
            st.latex(f"0.53 (1 + \\frac{{2}}{{{beta:.2f}}}) ({math.sqrt(fc):.2f}) ({b0:.0f}) ({d:.0f})")
            st.markdown(f"<div class='eq-box'><b>{res['Vc1']:,.0f}</b> kg</div>", unsafe_allow_html=True)

        with eq2:
            st.markdown("**Eq. 2: Perimeter**")
            st.latex(r"V_{c2} = 0.53 (\frac{40 d}{b_0} + 2) \sqrt{f'_c} b_0 d")
            st.caption("Substitution:")
            val_term = (40*d/b0) + 2
            st.latex(f"0.53 ({val_term:.2f}) ({math.sqrt(fc):.2f}) ({b0:.0f}) ({d:.0f})")
            st.markdown(f"<div class='eq-box'><b>{res['Vc2']:,.0f}</b> kg</div>", unsafe_allow_html=True)

        with eq3:
            st.markdown("**Eq. 3: Basic**")
            st.latex(r"V_{c3} = 1.06 \sqrt{f'_c} b_0 d")
            st.caption("Substitution:")
            st.latex(f"1.06 ({math.sqrt(fc):.2f}) ({b0:.0f}) ({d:.0f})")
            st.markdown(f"<div class='eq-box'><b>{res['Vc3']:,.0f}</b> kg</div>", unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

    # Comparison Block
    with st.container():
        st.markdown('<div class="step-container">', unsafe_allow_html=True)
        render_step_header(3, "Final Check (Capacity vs Demand)")
        
        vc_min = min(res['Vc1'], res['Vc2'], res['Vc3'])
        phi_vn = 0.85 * vc_min
        vu = res['Vu']
        ratio = vu / phi_vn
        status = "PASS" if ratio <= 1.0 else "FAIL"
        
        # Left: Numbers | Right: Verdict
        res_L, res_R = st.columns([2, 1])
        
        with res_L:
            st.write(f"• Governing $V_c$ (Min) = **{vc_min:,.0f}** kg")
            st.write(f"• Design Strength $\phi V_n$ ($0.85 \\times V_c$) = **{phi_vn:,.0f}** kg")
            st.markdown(f"• Factored Load $V_u$ = <b style='color:#d32f2f'>{vu:,.0f}</b> kg", unsafe_allow_html=True)
        
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
# 4. MAIN RENDERER
# ==========================================
def render(punch_res, v_oneway_res, mat_props, loads, Lx, Ly):
    inject_custom_css()
    
    st.title("📑 Detailed Calculation Report")
    st.caption("Step-by-step verification of structural adequacy.")
    
    # --- TOP DASHBOARD ---
    c1, c2, c3, c4 = st.columns(4)
    with c1: render_summary_card("Punching Shear", f"{punch_res['ratio']:.2f}", punch_res['status'])
    with c2: render_summary_card("One-Way Shear", f"{v_oneway_res['ratio']:.2f}", v_oneway_res['status'])
    h_min = max(Lx, Ly)*100/33
    h_status = "PASS" if mat_props['h_slab'] >= h_min else "CHECK"
    with c3: render_summary_card("Deflection", f"L/33", h_status, f"Req: {h_min:.1f} cm")
    with c4: render_summary_card("Factored Load", f"{loads['w_u']:,.0f}", "INFO", "kg/m²")
    
    st.write("") # Spacer

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
    
    # Prepare Data
    fc = mat_props['fc']
    d_slab = mat_props['h_slab'] - mat_props['cover'] - 1.0 
    vc_calc = 0.53 * math.sqrt(fc) * 100 * d_slab
    phi_vc = 0.85 * vc_calc
    vu_one = v_oneway_res.get('Vu', 0)
    
    with col_cap:
        render_step_header("A", "Capacity ($\phi V_c$)")
        st.write("Consider 1m strip ($b_w=100$ cm):")
        st.latex(r"V_c = 0.53 \sqrt{f'_c} b_w d")
        st.latex(f"V_c = 0.53 ({math.sqrt(fc):.2f}) (100) ({d_slab:.2f})")
        st.markdown(f"**$V_c$ = {vc_calc:,.0f} kg/m**")
        st.markdown(f"**$\phi V_c$ = {phi_vc:,.0f} kg/m** (at $\phi=0.85$)")

    with col_dem:
        render_step_header("B", "Demand ($V_u$)")
        st.write("Shear at distance $d$ from support:")
        st.latex(r"V_u = w_u \times (L_n/2 - d)")
        st.markdown(f"<h3 style='text-align:center; color:#d32f2f'>{vu_one:,.0f} kg/m</h3>", unsafe_allow_html=True)
    
    # Verdict
    st.markdown("---")
    ratio_one = vu_one / phi_vc
    status_one = "PASS" if ratio_one <= 1.0 else "FAIL"
    st.markdown(f"**Conclusion:** Ratio = {vu_one:,.0f} / {phi_vc:,.0f} = **{ratio_one:.2f}** ({status_one})")
    st.markdown('</div>', unsafe_allow_html=True)

    # --- 3. DEFLECTION ---
    st.header("3. Deflection (Min. Thickness)")
    st.markdown('<div class="step-container">', unsafe_allow_html=True)
    
    # Layout: Timeline style
    c_d1, c_d2, c_d3 = st.columns([1, 1.5, 1])
    
    with c_d1:
        st.markdown("**1. Span Data**")
        st.write(f"$L_x$ = {Lx} m")
        st.write(f"$L_y$ = {Ly} m")
        max_span = max(Lx, Ly)
        st.write(f"$L_{{max}}$ = {max_span} m")
    
    with c_d2:
        st.markdown("**2. ACI Formula (Interior)**")
        st.latex(r"h_{min} = \frac{L_n}{33} = \frac{" + f"{max_span*100:.0f}" + r"}{33}")
        st.markdown(f"<div style='text-align:center; font-weight:bold; font-size:1.2rem;'>Req: {h_min:.2f} cm</div>", unsafe_allow_html=True)
        
    with c_d3:
        st.markdown("**3. Check**")
        h_prov = mat_props['h_slab']
        st.write(f"Provided: **{h_prov} cm**")
        if h_prov >= h_min:
            st.success("✅ OK")
        else:
            st.error("❌ Too Thin")
            
    st.markdown('</div>', unsafe_allow_html=True)

    # --- 4. LOADS ---
    st.header("4. Factored Load Analysis ($w_u$)")
    st.markdown('<div class="step-container">', unsafe_allow_html=True)
    
    # Prepare Dataframe for cleaner look
    h_m = mat_props['h_slab'] / 100.0
    wd = h_m * 2400
    sdl = loads['SDL']
    ll = loads['LL']
    
    data = [
        {"Load Type": "Slab Weight", "Details": f"{h_m:.2f}m × 2400 kg/m³", "Service Load": wd, "Factor": 1.2, "Factored Load": wd*1.2},
        {"Load Type": "Superimposed (SDL)", "Details": "User Input", "Service Load": sdl, "Factor": 1.2, "Factored Load": sdl*1.2},
        {"Load Type": "Live Load (LL)", "Details": "User Input", "Service Load": ll, "Factor": 1.6, "Factored Load": ll*1.6},
    ]
    df = pd.DataFrame(data)
    
    # Show Table
    st.table(df.style.format({
        "Service Load": "{:,.1f}", 
        "Factored Load": "{:,.1f}",
        "Factor": "{:.1f}"
    }))
    
    # Final Sum
    wu_sum = df["Factored Load"].sum()
    st.markdown(f"""
    <div style="text-align:right; padding:10px; background:#e3f2fd; border-radius:5px;">
        <span style="font-size:1.2rem; margin-right:15px;">Total Factored Load ($w_u$) =</span>
        <span style="font-size:1.8rem; font-weight:bold; color:#1565c0;">{wu_sum:,.0f} kg/m²</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
