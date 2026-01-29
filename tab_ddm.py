import streamlit as st
import pandas as pd
import numpy as np

def render(Mo, L1, L2, h_slab, d_eff, fc, fy, d_bar, moment_vals, w_u, c1_w, ln):
    """
    Render DDM Tab with Full Calculation Steps
    """
    st.markdown("""
    <style>
        .calc-box { background-color: #f8f9fa; padding: 15px; border-radius: 8px; border: 1px solid #dee2e6; margin-bottom: 15px; }
        .result-text { color: #0d6efd; font-weight: bold; }
        .step-header { font-weight: bold; color: #495057; margin-top: 10px; }
        .sub-val { color: #dc3545; font-weight: bold; } /* สีแดงสำหรับตัวเลขที่แทนค่า */
    </style>
    """, unsafe_allow_html=True)

    st.header("2. Direct Design Method (DDM) - Detailed Calculation")

    # ==========================================
    # PART 1: STATIC MOMENT (Mo)
    # ==========================================
    st.subheader("1. คำนวณโมเมนต์สถิตรวม (Total Static Moment, $M_o$)")
    
    with st.container():
        st.markdown("<div class='calc-box'>", unsafe_allow_html=True)
        
        # 1.1 Clear Span (ln)
        st.markdown("**Step 1.1: ระยะช่วงคานสุทธิ ($l_n$)**")
        st.latex(r"l_n = L_1 - c_1")
        st.write(f"แทนค่า: $l_n = {L1:.2f} - {c1_w/100:.2f}$")
        st.markdown(f"👉 **$l_n = {ln:.3f}$ m**")
        
        st.markdown("---")

        # 1.2 Static Moment (Mo)
        st.markdown("**Step 1.2: โมเมนต์สถิตรวม ($M_o$)**")
        st.latex(r"M_o = \frac{w_u L_2 (l_n)^2}{8}")
        st.write(f"แทนค่า: $M_o = \\frac{{{w_u:,.0f} \\times {L2:.2f} \\times ({ln:.3f})^2}}{{8}}$")
        st.markdown(f"👉 <span class='result-text'>$M_o = {Mo:,.2f}$ kg-m</span>", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)

    # ==========================================
    # PART 2: DISTRIBUTION FACTORS
    # ==========================================
    st.subheader("2. การกระจายโมเมนต์ (Moment Distribution)")
    st.info("อ้างอิง ACI 318 สำหรับ Interior Panel (Flat Plate - No Beams)")

    col_d1, col_d2 = st.columns(2)
    
    # Longitudinal
    with col_d1:
        st.markdown("**2.1 กระจายตามยาว (Longitudinal)**")
        st.markdown("- **Negative Moment ($M^-$):** $65\%$ of $M_o$")
        st.markdown("- **Positive Moment ($M^+$):** $35\%$ of $M_o$")
        
        m_neg_total = 0.65 * Mo
        m_pos_total = 0.35 * Mo
        
        st.write(f"• Total $M^-$ = $0.65 \\times {Mo:,.0f} = {m_neg_total:,.0f}$ kg-m")
        st.write(f"• Total $M^+$ = $0.35 \\times {Mo:,.0f} = {m_pos_total:,.0f}$ kg-m")

    # Transverse
    with col_d2:
        st.markdown("**2.2 กระจายตามขวาง (Transverse)**")
        st.markdown("""
        **Column Strip (CS):**
        - รับ 75% ของ $M^-$
        - รับ 60% ของ $M^+$
        
        **Middle Strip (MS):**
        - ส่วนที่เหลือ (25% ของ $M^-$, 40% ของ $M^+$)
        """)

    # ==========================================
    # PART 3: DETAILED REBAR CALCULATION (4 ZONES)
    # ==========================================
    st.subheader("3. การออกแบบเหล็กเสริม (Reinforcement Design)")
    st.write("คำนวณละเอียดทีละโซน โดยใช้วิธี Ultimate Strength Design (USD)")

    # Data Setup
    w_cs = min(L1, L2)/2.0
    w_ms = L2 - w_cs
    zones_data = [
        {"name": "Zone 1: Column Strip - Top (Negative)", "M": moment_vals["M_cs_neg"], "b": w_cs, "type": "Top"},
        {"name": "Zone 2: Column Strip - Bottom (Positive)", "M": moment_vals["M_cs_pos"], "b": w_cs, "type": "Bot"},
        {"name": "Zone 3: Middle Strip - Top (Negative)", "M": moment_vals["M_ms_neg"], "b": w_ms, "type": "Top"},
        {"name": "Zone 4: Middle Strip - Bottom (Positive)", "M": moment_vals["M_ms_pos"], "b": w_ms, "type": "Bot"},
    ]

    for zone in zones_data:
        # Expander for each zone details
        with st.expander(f"📌 {zone['name']} | Moment: {zone['M']:,.0f} kg-m", expanded=False):
            
            Mu_kgm = zone['M']
            Mu_kgcm = Mu_kgm * 100
            b_m = zone['b']
            b_cm = b_m * 100
            
            col_calc1, col_calc2 = st.columns([1.5, 1])
            
            with col_calc1:
                st.markdown("#### 1. Parameters")
                st.write(f"- $M_u = {Mu_kgm:,.0f}$ kg-m = **{Mu_kgcm:,.0f}** kg-cm")
                st.write(f"- Width ($b$) = {b_m:.2f} m = **{b_cm:.0f}** cm")
                st.write(f"- Effective Depth ($d$) = **{d_eff:.2f}** cm")
                st.write(f"- $\phi$ (Flexure) = 0.90")

                st.markdown("#### 2. Check Capacity ($R_n$)")
                st.latex(r"R_n = \frac{M_u}{\phi b d^2}")
                
                # Rn Calc
                denom = 0.9 * b_cm * (d_eff**2)
                Rn = Mu_kgcm / denom if denom > 0 else 0
                
                st.write(f"แทนค่า: $R_n = \\frac{{{Mu_kgcm:,.0f}}}{{0.9 \\times {b_cm:.0f} \\times ({d_eff:.2f})^2}}$")
                st.write(f"ตัวหาร: {denom:,.0f}")
                st.markdown(f"👉 **$R_n = {Rn:.2f}$ ksc**")
                
                # Rho Calc
                st.markdown("#### 3. Calculate Reinforcement Ratio ($\\rho$)")
                st.latex(r"\rho_{req} = \frac{0.85 f'_c}{f_y} \left( 1 - \sqrt{1 - \frac{2 R_n}{0.85 f'_c}} \right)")
                
                term_root = 1 - (2 * Rn) / (0.85 * fc)
                
                if term_root < 0:
                    st.error(f"❌ Error: Section too small! (Term in root is negative: {term_root:.3f})")
                    st.stop()
                
                rho_req = (0.85 * fc / fy) * (1 - np.sqrt(term_root))
                
                st.write(f"พจน์ในรู้ท: $1 - \\frac{{2 \\times {Rn:.2f}}}{{0.85 \\times {fc}}} = {term_root:.4f}$")
                st.markdown(f"👉 **$\\rho_{{req}} = {rho_req:.5f}$**")

                # Check Min/Max
                rho_min = 0.0018
                st.write(f"- $\\rho_{{min}} = {rho_min}$ (Temp & Shrinkage)")
                
                rho_design = max(rho_req, rho_min)
                reason = "Calculated" if rho_req > rho_min else "Minimum"
                
                st.markdown(f"👉 **$\\rho_{{design}} = {rho_design:.5f}$** ({reason})")

            with col_calc2:
                st.markdown("#### 4. Steel Area ($A_s$)")
                st.latex(r"A_s = \rho b d")
                As = rho_design * b_cm * d_eff
                st.write(f"แทนค่า: $A_s = {rho_design:.5f} \\times {b_cm:.0f} \\times {d_eff:.2f}$")
                st.metric("As Required", f"{As:.2f} cm²")
                
                st.markdown("#### 5. Bar Selection")
                bar_area = 3.14159 * (d_bar/10)**2 / 4
                num_bars = np.ceil(As / bar_area)
                num_bars = max(num_bars, 2) # Min 2 bars
                
                calc_spacing = b_cm / num_bars
                # Max Spacing Check
                max_s = min(2*h_slab, 45)
                final_spacing = min(calc_spacing, max_s)
                
                st.write(f"- ใช้เหล็ก DB{d_bar} ($A_b={bar_area:.2f}$ cm²)")
                st.write(f"- จำนวน: $ {As:.2f} / {bar_area:.2f} = {As/bar_area:.2f} $ → **{int(num_bars)} เส้น**")
                st.write(f"- ระยะคำนวณ: ${b_cm:.0f} / {int(num_bars)} = {calc_spacing:.1f}$ cm")
                st.write(f"- ระยะ Max Allow: {max_s} cm")
                
                st.success(f"**สรุป: ใช้ {int(num_bars)} - DB{d_bar} @ {int(final_spacing)} cm**")

    # ==========================================
    # PART 4: SUMMARY TABLE
    # ==========================================
    st.subheader("4. สรุปตารางเหล็กเสริม (Summary)")
    summary_data = []
    for zone in zones_data:
         # Recalculate briefly for table (or store from loop)
         # For simplicity in display, using the same logic logic again hiddenly
         # Or better, just display the final result since user saw details above
         pass 
         # (User already saw details in Expanders, but a clean table is good)
    
    # Simple Manual Table Construction for Summary
    st.markdown("""
    | Zone | Moment (kg-m) | Width (m) | As Req (cm²) | Provide Rebar |
    |---|---|---|---|---|
    """ + "\n".join([
        f"| {z['name']} | {z['M']:,.0f} | {z['b']:.2f} | " 
        f"{(max((0.85*fc/fy)*(1-np.sqrt(1-(2*(z['M']*100/(0.9*z['b']*100*d_eff**2)))/(0.85*fc))), 0.0018) * z['b']*100 * d_eff):.2f} | " 
        "Check above details |" 
        for z in zones_data
    ]))
