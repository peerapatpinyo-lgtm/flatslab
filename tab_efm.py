import streamlit as st
import numpy as np
import pandas as pd
import math
from calculations import calculate_stiffness

def render(c1_w, c2_w, L1, L2, lc, h_slab, fc, mat_props, w_u, col_type):
    st.header("3. Equivalent Frame Method (Detailed Step-by-Step)")
    st.info("💡 แสดงรายการคำนวณแบบละเอียด (Substitution Method)")
    st.markdown("---")

    # --- 0. Setup Variables ---
    fy = mat_props['fy']
    Ec = 15100 * np.sqrt(fc)  # ksc
    
    # Convert dimensions to cm/kg for internal calcs
    L1_cm = L1 * 100
    L2_cm = L2 * 100
    lc_cm = lc * 100
    c1_cm = c1_w
    c2_cm = c2_w
    
    # Show Material Properties
    with st.expander("0. Material & Geometry Properties", expanded=True):
        c_A, c_B = st.columns(2)
        with c_A:
            st.markdown(f"**Concrete ($f'_c$):** {fc} ksc")
            st.markdown(f"**Modulus ($E_c$):** {Ec:,.0f} ksc")
        with c_B:
            st.markdown(f"**Column ($c_1 \\times c_2$):** {c1_cm} x {c2_cm} cm")
            st.markdown(f"**Slab Thickness ($h$):** {h_slab} cm")

    # =========================================================================
    # PART 1: STIFFNESS
    # =========================================================================
    st.subheader("1. Stiffness Calculation (คำนวณความแข็ง)")

    # --- 1.1 Column Stiffness ---
    st.markdown("#### 1.1 Column Stiffness ($K_c$)")
    
    Ic = c2_cm * (c1_cm**3) / 12.0
    Kc = 4 * Ec * Ic / lc_cm
    Sum_Kc = 2 * Kc
    
    # Note: ใช้ f-string แบบ \\ เพื่อลดโอกาส Syntax Error
    st.write("Moment of Inertia of Column ($I_c$):")
    st.latex(f"I_c = \\frac{{c_2 c_1^3}}{{12}} = \\frac{{{c2_cm} \\times {c1_cm}^3}}{{12}} = {Ic:,.0f} \\text{{ cm}}^4")
    
    st.write("Stiffness of Column ($K_c$):")
    st.latex(f"K_c = \\frac{{4 E_c I_c}}{{l_c}} = \\frac{{4 ({Ec:,.0f}) ({Ic:,.0f})}}{{{lc_cm:.0f}}} = {Kc:,.0f} \\text{{ kg-cm}}")
    
    st.write("Total Column Stiffness (Top + Bottom):")
    st.latex(f"\\Sigma K_c = 2 \\times K_c = {Sum_Kc:,.0f} \\text{{ kg-cm}}")

    # --- 1.2 Slab Stiffness ---
    st.markdown("#### 1.2 Slab Stiffness ($K_s$)")
    
    Is = L2_cm * (h_slab**3) / 12.0
    Ks = 4 * Ec * Is / L1_cm
    
    st.write("Moment of Inertia of Slab ($I_s$):")
    st.latex(f"I_s = \\frac{{L_2 h^3}}{{12}} = \\frac{{{L2_cm:.0f} \\times {h_slab}^3}}{{12}} = {Is:,.0f} \\text{{ cm}}^4")
    
    st.write("Stiffness of Slab ($K_s$):")
    st.latex(f"K_s = \\frac{{4 E_c I_s}}{{L_1}} = \\frac{{4 ({Ec:,.0f}) ({Is:,.0f})}}{{{L1_cm:.0f}}} = {Ks:,.0f} \\text{{ kg-cm}}")

    # --- 1.3 Torsional Stiffness ---
    st.markdown("#### 1.3 Torsional Member Stiffness ($K_t$)")
    
    x = h_slab
    y = c1_cm
    term_c = (1 - 0.63 * x / y)
    C = term_c * (x**3 * y) / 3.0
    
    # Prevent division by zero
    denom = (L2_cm * (1 - c2_cm/L2_cm)**3)
    if denom == 0: denom = 1.0
    Kt = 9 * Ec * C / denom
    
    st.write(f"Section Properties: $x = {x}$ cm, $y = {y}$ cm")
    st.latex(f"C = \\left(1 - 0.63 \\frac{{x}}{{y}}\\right) \\frac{{x^3 y}}{{3}} = {C:,.0f} \\text{{ cm}}^4")
    st.latex(f"K_t = \\frac{{9 E_c C}}{{L_2 (1 - c_2/L_2)^3}} = \\frac{{9 ({Ec:,.0f}) ({C:,.0f})}}{{{denom:,.0f}}} = {Kt:,.0f} \\text{{ kg-cm}}")

    # --- 1.4 Equivalent Column ---
    st.markdown("#### 1.4 Equivalent Column ($K_{ec}$)")
    
    if Kt > 0:
        inv_Kec = (1/Sum_Kc) + (1/Kt)
        Kec = 1/inv_Kec
        st.latex(f"\\frac{{1}}{{K_{{ec}}}} = \\frac{{1}}{{\\Sigma K_c}} + \\frac{{1}}{{K_t}} \\implies K_{{ec}} = {Kec:,.0f} \\text{{ kg-cm}}")
    else:
        Kec = Sum_Kc
        st.warning("Torsional stiffness is zero or invalid.")

    # --- 1.5 DF ---
    st.markdown("#### 1.5 Distribution Factors (DF)")
    sum_joint = Ks + Kec
    df_col = Kec / sum_joint if sum_joint > 0 else 0
    df_slab = Ks / sum_joint if sum_joint > 0 else 0
    
    st.latex(f"DF_{{col}} = \\frac{{K_{{ec}}}}{{K_s + K_{{ec}}}} = \\frac{{{Kec:,.0f}}}{{{sum_joint:,.0f}}} = \\mathbf{{{df_col:.4f}}}")

    # =========================================================================
    # PART 2: MOMENT
    # =========================================================================
    st.markdown("---")
    st.subheader("2. Moment Analysis")
    
    ln = L1 - (c1_w/100.0)
    Mo = w_u * L2 * (ln**2) / 8.0
    FEM = w_u * L2 * (L1**2) / 12.0
    
    st.write("Static Moment ($M_o$):")
    st.latex(f"M_o = \\frac{{w_u L_2 l_n^2}}{{8}} = \\frac{{{w_u:,.0f} \\times {L2} \\times {ln:.2f}^2}}{{8}} = \\mathbf{{{Mo:,.0f}}} \\text{{ kg-m}}")
    
    if col_type == 'interior':
        M_neg = 0.65 * Mo
        M_pos = 0.35 * Mo
        st.success("Interior Column (Standard Coeffs):")
        st.latex(f"M^- = 0.65 M_o = {M_neg:,.0f} \\text{{ kg-m}}")
        st.latex(f"M^+ = 0.35 M_o = {M_pos:,.0f} \\text{{ kg-m}}")
    else:
        st.warning(f"Edge Column (DF = {df_col:.4f}):")
        st.write(f"FEM = {FEM:,.0f} kg-m")
        M_neg = FEM * df_col
        st.latex(f"M^- (Transfer) = FEM \\times DF_{{col}} = {M_neg:,.0f} \\text{{ kg-m}}")
        
        M_pos_calc = Mo - (M_neg/2.0)
        M_pos = max(M_pos_calc, 0.50 * Mo)
        st.latex(f"M^+ = M_o - \\frac{{M^-}}{{2}} = {M_pos:,.0f} \\text{{ kg-m}}")

    # =========================================================================
    # PART 3: DESIGN
    # =========================================================================
    st.markdown("---")
    st.subheader("3. Reinforcement Design")
    
    design_opt = st.selectbox("Select Strip to View Calculation:", 
                             ["Column Strip (-)", "Column Strip (+)", "Middle Strip (-)", "Middle Strip (+)"])
    
    # Determine Width and Moment based on selection
    if col_type == 'interior':
        factors = {'CS-':0.75, 'CS+':0.60, 'MS-':0.25, 'MS+':0.40}
    else:
        factors = {'CS-':1.00, 'CS+':0.60, 'MS-':0.00, 'MS+':0.40}
        
    if "Column" in design_opt:
        width_m = L2/2.0
        code = "CS"
    else:
        width_m = L2/2.0
        code = "MS"
        
    if "(-)" in design_opt:
        moment_base = M_neg
        pct = factors[code+"-"]
    else:
        moment_base = M_pos
        pct = factors[code+"+"]
        
    Mu = moment_base * pct
    b_cm = width_m * 100
    
    st.markdown(f"**Design for: {design_opt}**")
    st.latex(f"M_u = {moment_base:,.0f} \\times {pct} = \\mathbf{{{Mu:,.0f}}} \\text{{ kg-m}}")
    
    if Mu > 100:
        d_bar = mat_props['d_bar']
        cover = mat_props['cover']
        d_eff = h_slab - cover - (d_bar/20.0)
        
        st.write("3.1 Check Section Strength ($R_n$):")
        Rn = (Mu * 100) / (0.9 * b_cm * d_eff**2)
        st.latex(f"R_n = \\frac{{M_u \\cdot 100}}{{0.9 b d^2}} = \\frac{{{Mu:,.0f} \\cdot 100}}{{0.9 ({b_cm:.0f}) ({d_eff:.2f})^2}} = {Rn:.2f} \\text{{ ksc}}")
        
        st.write("3.2 Calculate Reinforcement Ratio ($\\rho$):")
        term = 2 * Rn / (0.85 * fc)
        if term >= 1.0:
            st.error("FAIL: Section too small (Thicken slab)")
        else:
            rho_calc = (0.85 * fc / fy) * (1 - np.sqrt(1 - term))
            rho_min = 0.0018
            rho_use = max(rho_calc, rho_min)
            
            st.latex(f"\\rho_{{req}} = {rho_calc:.5f} \\quad (\\rho_{{min}} = {rho_min}) \\rightarrow \\text{{Use }} {rho_use:.5f}")
            
            As = rho_use * b_cm * d_eff
            st.write(f"3.3 Required Steel Area ($A_s$):")
            st.latex(f"A_s = \\rho b d = {As:.2f} \\text{{ cm}}^2")
            
            Ab = 3.1416 * (d_bar/20.0)**2
            num_bars = math.ceil(As/Ab)
            spacing = b_cm / num_bars if num_bars > 0 else 0
            
            st.success(f"✅ Use {int(num_bars)} - DB{d_bar} (Spacing ~ {spacing:.1f} cm)")
    else:
        st.info("Moment is negligible.")
