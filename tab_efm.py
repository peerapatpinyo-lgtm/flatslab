import streamlit as st
import numpy as np
import pandas as pd
import math

def render(c1_w, c2_w, L1, L2, lc, h_slab, fc, mat_props, w_u, col_type):
    st.header("3. Equivalent Frame Method (EFM) - Detailed Calculation")
    st.markdown("---")

    # ตัวแปร Material
    fy = mat_props['fy']
    Ec = 15100 * np.sqrt(fc)  # ksc
    
    # แปลงหน่วยเพื่อการคำนวณ (ใช้หน่วย kg, cm เป็นหลัก)
    L1_cm = L1 * 100
    L2_cm = L2 * 100
    lc_cm = lc * 100
    
    # =========================================================================
    # PART 1: STIFFNESS CALCULATION (แสดงวิธีทำหาค่า K)
    # =========================================================================
    st.subheader("1. Stiffness Calculation (คำนวณค่าความแข็ง)")
    st.info("ขั้นตอนแรก: หาความแข็งของแผ่นพื้น ($K_s$), เสา ($K_c$), และชิ้นส่วนรับแรงบิด ($K_t$) เพื่อรวมเป็น Equivalent Column ($K_{ec}$)")

    # --- 1.1 Column Stiffness (Kc) ---
    st.markdown("**1.1 Column Stiffness ($K_c$)**")
    Ic = c2_w * (c1_w**3) / 12.0
    Kc = 4 * Ec * Ic / lc_cm
    Sum_Kc = 2 * Kc  # เสาบน + เสาล่าง
    
    st.latex(r"I_c = \frac{c_2 c_1^3}{12} = \frac{" + f"{c2_w} \\times {c1_w}^3" + r"}{12} = " + f"{Ic:,.0f}" + r" \text{ cm}^4")
    st.latex(r"K_c = \frac{4 E_c I_c}{l_c} = \frac{4 (" + f"{Ec:,.0f}) ({Ic:,.0f})" + r"}{" + f"{lc_cm:.0f}" + r"} = " + f"{Kc:,.0f}" + r" \text{ kg-cm}")
    st.latex(r"\Sigma K_c = K_{c,top} + K_{c,bot} = 2 \times " + f"{Kc:,.0f} = \\mathbf{" + f"{Sum_Kc:,.0f}" + r"} \text{ kg-cm}")

    # --- 1.2 Slab Stiffness (Ks) ---
    st.markdown("**1.2 Slab Stiffness ($K_s$)**")
    Is = L2_cm * (h_slab**3) / 12.0
    Ks = 4 * Ec * Is / L1_cm
    
    st.latex(r"I_s = \frac{L_2 h^3}{12} = \frac{" + f"{L2_cm:.0f} \\times {h_slab}^3" + r"}{12} = " + f"{Is:,.0f}" + r" \text{ cm}^4")
    st.latex(r"K_s = \frac{4 E_c I_s}{L_1} = \frac{4 (" + f"{Ec:,.0f}) ({Is:,.0f})" + r"}{" + f"{L1_cm:.0f}" + r"} = \mathbf{" + f"{Ks:,.0f}" + r"} \text{ kg-cm}")

    # --- 1.3 Torsional Stiffness (Kt) ---
    st.markdown("**1.3 Torsional Member Stiffness ($K_t$)**")
    # Torsional constant C
    x = h_slab
    y = c1_w # Torsional arm width approx
    C = (1 - 0.63 * x / y) * (x**3 * y) / 3.0
    Kt = 9 * Ec * C / (L2_cm * (1 - c2_w/L2_cm)**3)
    
    st.write(f"Dimension of torsion arm: $x={x}$ cm, $y={y}$ cm")
    st.latex(r"C = \left(1 - 0.63 \frac{x}{y}\right) \frac{x^3 y}{3} = \mathbf{" + f"{C:,.0f}" + r"} \text{ cm}^4")
    st.latex(r"K_t = \frac{9 E_c C}{L_2(1 - c_2/L_2)^3} = \mathbf{" + f"{Kt:,.0f}" + r"} \text{ kg-cm}")

    # --- 1.4 Equivalent Column (Kec) ---
    st.markdown("**1.4 Equivalent Column Stiffness ($K_{ec}$)**")
    if Kt > 0:
        Kec = 1 / (1/Sum_Kc + 1/Kt)
        st.latex(r"\frac{1}{K_{ec}} = \frac{1}{\Sigma K_c} + \frac{1}{K_t} \implies K_{ec} = \mathbf{" + f"{Kec:,.0f}" + r"} \text{ kg-cm}")
    else:
        Kec = Sum_Kc
        st.write("Kt is negligible, Kec = Sum Kc")

    # --- 1.5 Distribution Factors (DF) ---
    st.markdown("**1.5 Distribution Factors (DF) at Joint**")
    Sum_K_joint = Ks + Kec
    DF_slab = Ks / Sum_K_joint
    DF_col = Kec / Sum_K_joint
    
    st.latex(r"DF_{slab} = \frac{K_s}{K_s + K_{ec}} = \frac{" + f"{Ks:,.0f}" + r"}{" + f"{Ks:,.0f} + {Kec:,.0f}" + r"} = \mathbf{" + f"{DF_slab:.3f}" + r"}")
    st.latex(r"DF_{col} = \frac{K_{ec}}{K_s + K_{ec}} = \mathbf{" + f"{DF_col:.3f}" + r"}")

    st.markdown("---")

    # =========================================================================
    # PART 2: MOMENT ANALYSIS (วิเคราะห์โมเมนต์)
    # =========================================================================
    st.subheader("2. Moment Analysis (วิเคราะห์แรงดัด)")
    
    # Static Moment
    ln = L1 - (c1_w/100.0)
    Mo = w_u * L2 * (ln**2) / 8.0
    FEM = w_u * L2 * (L1**2) / 12.0 # Fixed End Moment

    st.write(f"**Total Static Moment ($M_o$):** (Load $w_u = {w_u:,.0f}$ kg/m²)")
    st.latex(r"M_o = \frac{w_u L_2 \ell_n^2}{8} = \frac{" + f"{w_u:,.0f} \\times {L2} \\times {ln:.2f}^2" + r"}{8} = \mathbf{" + f"{Mo:,.0f}" + r"} \text{ kg-m}")

    st.write("**Determination of Design Moments:**")
    
    if col_type == 'interior':
        st.success("Case: Interior Column (สมมุติสมมาตร)")
        st.write("สำหรับเสากลาง โมเมนต์ลบจะถูกควบคุมโดย FEM และการกระจายตามสัดส่วน DDM/EFM ปกติ")
        M_neg = 0.65 * Mo # ACI DDM coeff as baseline for EFM check
        M_pos = 0.35 * Mo
        st.latex(r"M^- \approx 0.65 M_o = " + f"{M_neg:,.0f} " + r"\text{ kg-m}")
        st.latex(r"M^+ \approx 0.35 M_o = " + f"{M_pos:,.0f} " + r"\text{ kg-m}")
        
    else: # EDGE COLUMN
        st.warning(f"Case: Edge/Corner Column ($DF_{{col}} = {DF_col:.3f}$)")
        st.write("สำหรับเสาริม โมเมนต์ลบที่ถ่ายเข้าเสา (Unbalanced Moment) จะขึ้นกับค่า Stiffness ของเสาเทียบกับพื้น")
        
        # EFM Logic for Edge: Moment transfer to column approx FEM * DF_col
        # Or using ACI Equivalent Frame concepts:
        M_neg_transfer = FEM * DF_col
        
        st.latex(r"M^-_{slab} (\text{Transfer}) \approx FEM \times DF_{col}")
        st.latex(r"M^- = " + f"{FEM:,.0f} \\times {DF_col:.3f} = \\mathbf{" + f"{M_neg_transfer:,.0f}" + r"} \text{ kg-m}")
        
        # Positive moment from statics
        M_pos_calc = Mo - (M_neg_transfer / 2.0) # Approx statics
        
        # Check against minimums
        M_pos = max(M_pos_calc, 0.50 * Mo) # Don't let pos moment be too small in design
        
        st.latex(r"M^+ \approx M_o - \frac{M^-}{2} = " + f"{M_pos_calc:,.0f} " + r"\text{ kg-m}")
        st.write(f"*(Design Use $M^+$ = {M_pos:,.0f} kg-m)*")
        
        M_neg = M_neg_transfer

    # =========================================================================
    # PART 3: LATERAL DISTRIBUTION (แบ่งเข้าแถบเสา/แถบกลาง)
    # =========================================================================
    st.markdown("---")
    st.subheader("3. Lateral Distribution (กระจายเข้าแถบเสา/แถบกลาง)")
    
    # Determine Percentages based on geometry (Simple ACI Lookups)
    # L2/L1 ratio, alpha1*L2/L1 (assume beam=0 for flat plate)
    
    if col_type == 'interior':
        pct_cs_neg = 75
        pct_cs_pos = 60
    else: # Edge
        pct_cs_neg = 100 # Edge takes all moment to column
        pct_cs_pos = 60
        
    # Table Data Preparation
    col_strip_width = L2 / 2.0
    mid_strip_width = L2 / 2.0
    
    m_cs_neg = M_neg * (pct_cs_neg/100.0)
    m_ms_neg = M_neg * ((100-pct_cs_neg)/100.0)
    
    m_cs_pos = M_pos * (pct_cs_pos/100.0)
    m_ms_pos = M_pos * ((100-pct_cs_pos)/100.0)
    
    results = [
        {"Strip": "Column Strip (-)", "% Dist": f"{pct_cs_neg}%", "Mu (kg-m)": m_cs_neg, "Width (m)": col_strip_width},
        {"Strip": "Column Strip (+)", "% Dist": f"{pct_cs_pos}%", "Mu (kg-m)": m_cs_pos, "Width (m)": col_strip_width},
        {"Strip": "Middle Strip (-)", "% Dist": f"{100-pct_cs_neg}%", "Mu (kg-m)": m_ms_neg, "Width (m)": mid_strip_width},
        {"Strip": "Middle Strip (+)", "% Dist": f"{100-pct_cs_pos}%", "Mu (kg-m)": m_ms_pos, "Width (m)": mid_strip_width},
    ]
    
    st.table(pd.DataFrame(results).set_index("Strip"))

    # =========================================================================
    # PART 4: REINFORCEMENT DESIGN (คำนวณเหล็กเสริม)
    # =========================================================================
    st.markdown("---")
    st.subheader("4. Reinforcement Design (คำนวณเหล็กเสริม)")
    st.write("เลือกหนึ่งตำแหน่งเพื่อแสดงรายการคำนวณละเอียด:")
    
    selected_strip = st.selectbox("Select Strip to Design:", [r["Strip"] for r in results])
    
    # Get values for selected strip
    sel_data = next(item for item in results if item["Strip"] == selected_strip)
    Mu_design = sel_data["Mu (kg-m)"]
    b_design = sel_data["Width (m)"]
    
    if Mu_design <= 0:
        st.warning("Moment is zero or negative, minimum steel applies.")
        Mu_design = 0.1 # avoid div by zero
        
    st.markdown(f"#### 📐 Design for: {selected_strip}")
    
    # 4.1 Parameter Setup
    d_bar = mat_props['d_bar']
    cover = mat_props['cover']
    b_cm = b_design * 100
    d_eff = h_slab - cover - (d_bar/20.0)
    phi = 0.90
    
    st.markdown("**4.1 Section Parameters**")
    st.latex(r"b = " + f"{b_cm:.0f}" + r" \text{ cm}, \quad d = h - cover - \phi_{bar}/2 = " + f"{d_eff:.2f}" + r" \text{ cm}")
    
    # 4.2 Rn
    st.markdown("**4.2 Strength Parameter ($R_n$)**")
    Rn = (Mu_design * 100) / (phi * b_cm * d_eff**2)
    st.latex(r"R_n = \frac{M_u}{\phi b d^2} = \frac{" + f"{Mu_design:,.0f} \\times 100" + r"}{0.9 \times " + f"{b_cm:.0f} \\times {d_eff:.2f}^2" + r"} = \mathbf{" + f"{Rn:.2f}" + r"} \text{ ksc}")

    # 4.3 Rho
    st.markdown("**4.3 Reinforcement Ratio ($\rho$)**")
    rho_min = 0.0018
    term = 2 * Rn / (0.85 * fc)
    
    if term >= 1.0:
        st.error(f"❌ Section too small! (2Rn/0.85fc = {term:.2f} > 1.0). Increase slab thickness.")
        return
        
    rho_calc = (0.85 * fc / fy) * (1 - np.sqrt(1 - term))
    st.latex(r"\rho_{calc} = \frac{0.85 f'_c}{f_y} \left( 1 - \sqrt{1 - \frac{2 R_n}{0.85 f'_c}} \right) = \mathbf{" + f"{rho_calc:.5f}" + r"}")
    
    if rho_calc < rho_min:
        st.info(f"Note: $\\rho_{{calc}}$ ({rho_calc:.5f}) < $\\rho_{{min}}$ ({rho_min}). Use $\\rho_{{min}}$.")
        rho_use = rho_min
    else:
        rho_use = rho_calc
        
    st.latex(r"\rho_{required} = \mathbf{" + f"{rho_use:.5f}" + r"}")

    # 4.4 As & Bar Selection
    st.markdown("**4.4 Steel Area ($A_s$) & Selection**")
    As_req = rho_use * b_cm * d_eff
    st.latex(r"A_s = \rho b d = " + f"{rho_use:.5f} \\times {b_cm:.0f} \\times {d_eff:.2f} = \\mathbf{" + f"{As_req:.2f}" + r"} \text{ cm}^2")
    
    # Calculate Bars
    A_bar = 3.14159 * (d_bar/20.0)**2
    num_bars = As_req / A_bar
    spacing = b_cm / num_bars
    
    col_res1, col_res2 = st.columns(2)
    with col_res1:
        st.markdown(f"**Option A: Count Basis**")
        st.write(f"Using DB{d_bar} ($A_b = {A_bar:.2f} cm^2$)")
        st.write(f"Required = {As_req:.2f} / {A_bar:.2f} = {num_bars:.2f} bars")
        st.success(f"✅ Use **{math.ceil(num_bars)} - DB{d_bar}**")
        
    with col_res2:
        st.markdown(f"**Option B: Spacing Basis**")
        st.write(f"Theor. Spacing = {spacing:.1f} cm")
        use_spacing = math.floor(spacing / 5) * 5 # Round down to nearest 5
        if use_spacing > 30: use_spacing = 30
        if use_spacing < 10: use_spacing = 10
        st.success(f"✅ Use **DB{d_bar} @ {use_spacing/100:.2f} m**")
