import streamlit as st
import numpy as np
import pandas as pd
import math

# เรายังคง import เพื่อความชัวร์ แต่ในไฟล์นี้เราจะคำนวณโชว์สดๆ เพื่อดึงตัวเลขมาแสดง
from calculations import calculate_stiffness

def render(c1_w, c2_w, L1, L2, lc, h_slab, fc, mat_props, w_u, col_type):
    st.header("3. Equivalent Frame Method (Detailed Calculation)")
    st.info("💡 แสดงรายการคำนวณแบบละเอียดทุกขั้นตอน (Step-by-Step Substitution)")
    st.markdown("---")

    # --- 0. เตรียมตัวแปรและแสดงค่าเริ่มต้น ---
    fy = mat_props['fy']
    Ec = 15100 * np.sqrt(fc)  # ksc
    
    # แปลงหน่วยเป็น cm เพื่อการคำนวณภายใน
    L1_cm = L1 * 100
    L2_cm = L2 * 100
    lc_cm = lc * 100
    c1_cm = c1_w
    c2_cm = c2_w
    
    with st.expander("0. Material & Geometry Properties (ค่าคงที่และมิติ)", expanded=True):
        col0_1, col0_2 = st.columns(2)
        with col0_1:
            st.markdown(f"**Concrete ($f'_c$):** {fc} ksc")
            st.markdown(f"**Steel ($f_y$):** {fy} ksc")
            st.latex(r"E_c = 15100\sqrt{f'_c} = 15100\sqrt{" + f"{fc}" + r"} = \mathbf{" + f"{Ec:,.0f}" + r"} \text{ ksc}")
        with col0_2:
            st.write(f"**Span $L_1$ (Direction of analysis):** {L1_cm:.0f} cm")
            st.write(f"**Span $L_2$ (Transverse):** {L2_cm:.0f} cm")
            st.write(f"**Column ($c_1 \times c_2$):** {c1_cm} x {c2_cm} cm")
            st.write(f"**Slab Thickness ($h$):** {h_slab} cm")

    # =========================================================================
    # PART 1: STIFFNESS (แสดงการแทนค่าละเอียด)
    # =========================================================================
    st.subheader("1. Stiffness Calculation (คำนวณความแข็ง)")

    # --- 1.1 Column Stiffness ---
    st.markdown("#### 1.1 Column Stiffness ($K_c$)")
    
    # Inertia
    Ic = c2_cm * (c1_cm**3) / 12.0
    st.write("Moment of Inertia of Column ($I_c$):")
    st.latex(r"I_c = \frac{c_2 \cdot c_1^3}{12} = \frac{" + f"{c2_cm} \cdot {c1_cm}^3" + r"}{12} = " + f"{Ic:,.0f}" + r" \text{ cm}^4")
    
    # Kc
    Kc = 4 * Ec * Ic / lc_cm
    st.write("Stiffness of one column ($K_c$):")
    st.latex(r"K_c = \frac{4 E_c I_c}{l_c} = \frac{4 \cdot " + f"{Ec:,.0f} \cdot {Ic:,.0f}" + r"}{" + f"{lc_cm:.0f}" + r"} = \mathbf{" + f"{Kc:,.0f}" + r"} \text{ kg-cm}")
    
    # Sum Kc
    Sum_Kc = 2 * Kc
    st.write("Total Column Stiffness (Top + Bottom):")
    st.latex(r"\Sigma K_c = 2 \times K_c = 2 \times " + f"{Kc:,.0f} = \mathbf{" + f"{Sum_Kc:,.0f}" + r"} \text{ kg-cm}")

    # --- 1.2 Slab Stiffness ---
    st.markdown("#### 1.2 Slab Stiffness ($K_s$)")
    
    # Inertia
    Is = L2_cm * (h_slab**3) / 12.0
    st.write("Moment of Inertia of Slab ($I_s$):")
    st.latex(r"I_s = \frac{L_2 \cdot h^3}{12} = \frac{" + f"{L2_cm:.0f} \cdot {h_slab}^3" + r"}{12} = " + f"{Is:,.0f}" + r" \text{ cm}^4")
    
    # Ks
    Ks = 4 * Ec * Is / L1_cm
    st.write("Stiffness of Slab ($K_s$):")
    st.latex(r"K_s = \frac{4 E_c I_s}{L_1} = \frac{4 \cdot " + f"{Ec:,.0f} \cdot {Is:,.0f}" + r"}{" + f"{L1_cm:.0f}" + r"} = \mathbf{" + f"{Ks:,.0f}" + r"} \text{ kg-cm}")

    # --- 1.3 Torsional Stiffness ---
    st.markdown("#### 1.3 Torsional Stiffness ($K_t$)")
    st.info("ส่วนนี้คำนวณยากที่สุด แสดงรายละเอียดค่าคงที่ C และส่วนประกอบต่างๆ")
    
    x = h_slab
    y = c1_cm
    term_c = (1 - 0.63 * x / y)
    C = term_c * (x**3 * y) / 3.0
    
    st.write(f"**Torsional section dimensions:** $x$ (shorter) = {x} cm, $y$ (longer) = {y} cm")
    st.write("Calculate Torsional Constant ($C$):")
    st.latex(r"C = \left(1 - 0.63 \frac{x}{y}\right) \frac{x^3 y}{3}")
    st.latex(r"C = \left(1 - 0.63 \frac{" + f"{x}" + r"}{" + f"{y}" + r"}\right) \frac{" + f"{x}^3 \cdot {y}" + r"}{3} = \mathbf{" + f"{C:,.0f}" + r"} \text{ cm}^4")
    
    denom_kt = (L2_cm * (1 - c2_cm/L2_cm)**3)
    if denom_kt == 0: denom_kt = 1.0 # Protect div 0
    
    Kt = 9 * Ec * C / denom_kt
    
    st.write("Calculate $K_t$:")
    st.latex(r"K_t = \frac{9 E_c C}{L_2(1 - c_2/L_2)^3}")
    st.latex(r"K_t = \frac{9 \cdot " + f"{Ec:,.0f} \cdot {C:,.0f}" + r"}{" + f"{L2_cm:.0f}(1 - {c2_cm}/{L2_cm:.0f})^3" + r"} = \mathbf{" + f"{Kt:,.0f}" + r"} \text{ kg-cm}")

    # --- 1.4 Equivalent Column ---
    st.markdown("#### 1.4 Equivalent Column ($K_{ec}$)")
    if Kt > 0:
        inv_Kec = (1/Sum_Kc) + (1/Kt)
        Kec = 1/inv_Kec
        st.latex(r"\frac{1}{K_{ec}} = \frac{1}{\Sigma K_c} + \frac{1}{K_t} = \frac{1}{" + f"{Sum_Kc:,.0f}" + r"} + \frac{1}{" + f"{Kt:,.0f}" + r"}")
        st.latex(r"K_{ec} = \mathbf{" + f"{Kec:,.0f}" + r"} \text{ kg-cm}")
    else:
        Kec = Sum_Kc
        st.error("Kt is zero, Kec = Sum Kc")

    # --- 1.5 Distribution Factors ---
    st.markdown("#### 1.5 Distribution Factors (DF)")
    sum_joint = Ks + Kec
    df_col = Kec / sum_joint
    df_slab = Ks / sum_joint
    
    st.latex(r"\Sigma K_{joint} = K_s + K_{ec} = " + f"{Ks:,.0f} + {Kec:,.0f} = {sum_joint:,.0f}")
    st.latex(r"DF_{col} = \frac{K_{ec}}{\Sigma K} = \frac{" + f"{Kec:,.0f}" + r"}{" + f"{sum_joint:,.0f}" + r"} = \mathbf{" + f"{df_col:.4f}" + r"}")
    st.latex(r"DF_{slab} = \frac{K_s}{\Sigma K} = \frac{" + f"{Ks:,.0f}" + r"}{" + f"{sum_joint:,.0f}" + r"} = \mathbf{" + f"{df_slab:.4f}" + r"}")

    st.markdown("---")

    # =========================================================================
    # PART 2: MOMENT ANALYSIS
    # =========================================================================
    st.subheader("2. Moment Analysis (วิเคราะห์โมเมนต์)")
    
    ln = L1 - (c1_w/100.0)
    Mo = w_u * L2 * (ln**2) / 8.0
    FEM = w_u * L2 * (L1**2) / 12.0
    
    st.markdown("**2.1 Static Moment ($M_o$)**")
    st.latex(r"\ell_n = L_1 - c_1 = " + f"{L1} - {c1_w/100} = {ln:.2f} m")
    st.latex(r"M_o = \frac{w_u L_2 \ell_n^2}{8} = \frac{" + f"{w_u:,.0f} \cdot {L2} \cdot {ln:.2f}^2" + r"}{8} = \mathbf{" + f"{Mo:,.0f}" + r"} \text{ kg-m}")

    st.markdown("**2.2 Design Moments (Unbalanced Moment Transfer)**")
    
    if col_type == 'interior':
        M_neg = 0.65 * Mo
        M_pos = 0.35 * Mo
        st.success(f"**Interior Column:** Using Direct Design Coefficients")
        st.latex(r"M^- = 0.65 M_o = 0.65 \times " + f"{Mo:,.0f} = \mathbf{" + f"{M_neg:,.0f}" + r"} \text{ kg-m}")
        st.latex(r"M^+ = 0.35 M_o = 0.35 \times " + f"{Mo:,.0f} = \mathbf{" + f"{M_pos:,.0f}" + r"} \text{ kg-m}")
    else:
        st.warning(f"**Edge Column:** Moment transfer depends on $DF_{{col}} = {df_col:.4f}$")
        st.write("Fixed End Moment (FEM):")
        st.latex(r"FEM = \frac{w_u L_2 L_1^2}{12} = \frac{" + f"{w_u:,.0f} \cdot {L2} \cdot {L1}^2" + r"}{12} = " + f"{FEM:,.0f} \text{ kg-m}")
        
        M_neg = FEM * df_col
        st.write("Negative Moment (Transfer to Column):")
        st.latex(r"M^- = FEM \times DF_{col} = " + f"{FEM:,.0f} \times {df_col:.4f} = \mathbf{" + f"{M_neg:,.0f}" + r"} \text{ kg-m}")
        
        M_pos_calc = Mo - (M_neg/2.0)
        M_pos = max(M_pos_calc, 0.50 * Mo)
        
        st.write("Positive Moment (Midspan):")
        st.latex(r"M^+ \approx M_o - \frac{M^-}{2} = " + f"{Mo:,.0f} - \frac{{{M_neg:,.0f}}}{{2}} = \mathbf{" + f"{M_pos:,.0f}" + r"} \text{ kg-m}")

    # =========================================================================
    # PART 3: REINFORCEMENT DESIGN
    # =========================================================================
    st.markdown("---")
    st.subheader("3. Reinforcement Calculation (คำนวณเหล็กเสริม)")
    
    # Strip Definitions
    col_strip_width = L2 / 2.0
    mid_strip_width = L2 / 2.0
    
    if col_type == 'interior':
        factors = {'CS-':0.75, 'CS+':0.60, 'MS-':0.25, 'MS+':0.40}
    else:
        factors = {'CS-':1.00, 'CS+':0.60, 'MS-':0.00, 'MS+':0.40}
        
    # User Select
    design_loc = st.selectbox("เลือกตำแหน่งเพื่อดูรายการคำนวณออกแบบ (Design Step-by-Step):", 
                              ["Column Strip (Neg)", "Column Strip (Pos)", "Middle Strip (Neg)", "Middle Strip (Pos)"])
    
    # Map selection to variables
    if "Column" in design_loc:
        width = col_strip_width
        key_prefix = "CS"
    else:
        width = mid_strip_width
        key_prefix = "MS"
        
    if "Neg" in design_loc:
        base_moment = M_neg
        pct = factors[key_prefix + "-"]
        sign = "(-)"
    else:
        base_moment = M_pos
        pct = factors[key_prefix + "+"]
        sign = "(+)"
        
    Mu_strip = base_moment * pct
    
    # Display Design Steps
    st.markdown(f"#### 📐 Design Detail: {design_loc}")
    
    st.write("**3.1 Factored Moment ($M_u$)**")
    st.latex(r"M_{total} = " + f"{base_moment:,.0f}, \quad \\text{{% Distribution}} = {pct*100}\\%")
    st.latex(r"M_u = " + f"{base_moment:,.0f} \\times {pct} = \mathbf{" + f"{Mu_strip:,.0f}" + r"} \text{ kg-m}")
    
    if Mu_strip <= 100:
        st.warning("Moment is too small for design.")
    else:
        st.write("**3.2 Section Properties**")
        b_cm = width * 100
        cover = mat_props['cover']
        d_bar = mat_props['d_bar']
        d_eff = h_slab - cover - (d_bar/20.0)
        
        st.latex(r"b = " + f"{b_cm:.0f} \text{ cm}")
        st.latex(r"d = h - cover - d_b/2 = " + f"{h_slab} - {cover} - {d_bar/20.0} = \mathbf{" + f"{d_eff:.2f}" + r"} \text{ cm}")
        
        st.write("**3.3 Flexural Resistance Factor ($R_n$)**")
        Rn = (Mu_strip * 100) / (0.9 * b_cm * d_eff**2)
        st.latex(r"R_n = \frac{M_u \times 100}{0.9 b d^2} = \frac{" + f"{Mu_strip:,.0f} \\times 100" + r"}{0.9 \cdot " + f"{b_cm:.0f} \cdot {d_eff:.2f}^2" + r"} = \mathbf{" + f"{Rn:.2f}" + r"} \text{ ksc}")
        
        st.write("**3.4 Required Reinforcement Ratio ($\rho$)**")
        rho_min = 0.0018
        term = 2 * Rn / (0.85 * fc)
        
        if term >= 1.0:
            st.error(f"❌ Section Fail! Value inside sqrt is negative ($2R_n/0.85f'_c = {term:.2f} > 1$) -> Increase Thickness")
        else:
            rho_calc = (0.85 * fc / fy) * (1 - np.sqrt(1 - term))
            
            st.latex(r"\text{term} = \frac{2 R_n}{0.85 f'_c} = \frac{2 \cdot " + f"{Rn:.2f}" + r"}{0.85 \cdot " + f"{fc}" + r"} = " + f"{term:.3f}")
            st.latex(r"\rho_{calc} = \frac{0.85 f'_c}{f_y} (1 - \sqrt{1 - \text{term}}) = \mathbf{" + f"{rho_calc:.5f}" + r"}")
            
            rho_final = max(rho_calc, rho_min)
            if rho_calc < rho_min:
                st.caption(f"(Note: $\\rho_{{calc}} < \\rho_{{min}}$, using $\\rho_{{min}} = {rho_min}$)")
            
            st.write("**3.5 Steel Area ($A_s$)**")
            As = rho_final * b_cm * d_eff
            st.latex(r"A_s = \rho b d = " + f"{rho_final:.5f} \\cdot {b_cm:.0f} \\cdot {d_eff:.2f} = \mathbf{" + f"{As:.2f}" + r"} \text{ cm}^2")
            
            st.write("**3.6 Bar Selection**")
            Ab = 3.1416 * (d_bar/20.0)**2
            num = math.ceil(As / Ab)
            
            st.latex(r"\text{Use DB}" + f"{d_bar} (A_b = {Ab:.2f} \text{ cm}^2)")
            st.latex(r"\text{Number of bars} = \frac{A_s}{A_b} = \frac{" + f"{As:.2f}" + r"}{" + f"{Ab:.2f}" + r"} \to \text{Use } \mathbf{" + f"{int(num)}" + r"} \text{ bars}")
            
            spacing = b_cm / num
            st.write(f"Average Spacing = {spacing:.1f} cm")
