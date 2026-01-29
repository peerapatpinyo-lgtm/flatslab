import streamlit as st
import pandas as pd
import numpy as np
from calculations import design_rebar_detailed

def render(Mo, L1, L2, h_slab, d_eff, fc, fy, d_bar, moment_vals, w_u, c1_w, ln):
    """
    Render DDM Tab with Full Calculation Steps
    """
    st.markdown("""
    <style>
        .calc-box { background-color: #f8f9fa; padding: 15px; border-radius: 8px; border: 1px solid #dee2e6; margin-bottom: 15px; }
        .result-text { color: #0d6efd; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

    st.header("2. Direct Design Method (DDM) - Detailed Calculation")

    # PART 1: STATIC MOMENT
    st.subheader("1. คำนวณโมเมนต์สถิตรวม (Total Static Moment, $M_o$)")
    with st.container():
        st.markdown("<div class='calc-box'>", unsafe_allow_html=True)
        
        # ln
        st.markdown("**Step 1.1: ระยะช่วงคานสุทธิ ($l_n$)**")
        st.latex(r"l_n = L_1 - c_1")
        st.write(f"แทนค่า: $l_n = {L1:.2f} - {c1_w/100:.2f}$")
        st.markdown(f"👉 **$l_n = {ln:.3f}$ m**")
        st.markdown("---")
        # Mo
        st.markdown("**Step 1.2: โมเมนต์สถิตรวม ($M_o$)**")
        st.latex(r"M_o = \frac{w_u L_2 (l_n)^2}{8}")
        st.write(f"แทนค่า: $M_o = \\frac{{{w_u:,.0f} \\times {L2:.2f} \\times ({ln:.3f})^2}}{{8}}$")
        st.markdown(f"👉 <span class='result-text'>$M_o = {Mo:,.2f}$ kg-m</span>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # PART 2: DISTRIBUTION
    st.subheader("2. การกระจายโมเมนต์ (Moment Distribution)")
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        st.markdown("**2.1 กระจายตามยาว (Longitudinal)**")
        st.write(f"• Total $M^-$ (65%) = {Mo*0.65:,.0f} kg-m")
        st.write(f"• Total $M^+$ (35%) = {Mo*0.35:,.0f} kg-m")
    with col_d2:
        st.markdown("**2.2 กระจายตามขวาง (Transverse)**")
        st.write("- **Col Strip:** 75% Neg, 60% Pos")
        st.write("- **Mid Strip:** Remainder")

    # PART 3: REBAR CALCULATION
    st.subheader("3. การออกแบบเหล็กเสริม (Reinforcement Design)")
    
    w_cs = min(L1, L2)/2.0
    w_ms = L2 - w_cs
    zones_data = [
        {"name": "Zone 1: Column Strip - Top (-)", "M": moment_vals["M_cs_neg"], "b": w_cs},
        {"name": "Zone 2: Column Strip - Bot (+)", "M": moment_vals["M_cs_pos"], "b": w_cs},
        {"name": "Zone 3: Middle Strip - Top (-)", "M": moment_vals["M_ms_neg"], "b": w_ms},
        {"name": "Zone 4: Middle Strip - Bot (+)", "M": moment_vals["M_ms_pos"], "b": w_ms},
    ]

    for zone in zones_data:
        with st.expander(f"📌 {zone['name']} | Moment: {zone['M']:,.0f} kg-m", expanded=False):
            Mu_kgcm = zone['M'] * 100
            b_cm = zone['b'] * 100
            
            col_calc1, col_calc2 = st.columns([1.5, 1])
            with col_calc1:
                st.markdown("#### Parameters")
                st.write(f"- $M_u = {Mu_kgcm:,.0f}$ kg-cm")
                st.write(f"- $b = {b_cm:.0f}$ cm, $d = {d_eff:.2f}$ cm")
                
                # Rn
                denom = 0.9 * b_cm * (d_eff**2)
                Rn = Mu_kgcm / denom if denom > 0 else 0
                st.write(f"👉 $R_n = {Rn:.2f}$ ksc")
                
                # Rho
                term_root = 1 - (2 * Rn) / (0.85 * fc)
                if term_root < 0:
                    st.error("Section too small!")
                    continue
                rho_req = (0.85 * fc / fy) * (1 - np.sqrt(term_root))
                rho_min = 0.0018
                rho_design = max(rho_req, rho_min)
                st.write(f"👉 $\\rho_{{req}} = {rho_req:.5f}$ vs $\\rho_{{min}} = {rho_min}$")
                st.markdown(f"👉 **Use $\\rho = {rho_design:.5f}$**")

            with col_calc2:
                st.markdown("#### Selection")
                As = rho_design * b_cm * d_eff
                st.metric("As Required", f"{As:.2f} cm²")
                
                bar_area = 3.14159 * (d_bar/10)**2 / 4
                num_bars = max(np.ceil(As / bar_area), 2)
                spacing = min(b_cm / num_bars, 2*h_slab, 45)
                
                st.success(f"**Use {int(num_bars)} - DB{d_bar} @ {int(spacing)} cm**")
