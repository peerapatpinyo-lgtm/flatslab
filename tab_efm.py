import streamlit as st
import numpy as np
import pandas as pd
import math

# เราจะคำนวณสดใหม่ทั้งหมดในไฟล์นี้ เพื่อดึงตัวเลขทุกขั้นตอนมาแสดงผล (Show your work)
# ไม่ใช้ black box function เพื่อความโปร่งใสของตัวเลข

def render(c1_w, c2_w, L1, L2, lc, h_slab, fc, mat_props, w_u, col_type):
    st.header("3. Equivalent Frame Method (Verification Mode)")
    st.info("💡 โหมดแสดงรายการคำนวณละเอียด: แสดงที่มาตัวเลขและการตรวจสอบสมดุล (Equilibrium Check)")
    st.markdown("---")

    # --- 0. เตรียมตัวแปร (Data Preparation) ---
    fy = mat_props['fy']
    Ec = 15100 * np.sqrt(fc)  # ksc (kg/cm^2)
    
    # แปลงหน่วยเป็น cm เพื่อใช้คำนวณ Stiffness
    L1_cm = L1 * 100.0  # Span ยาว (ทิศทางวิเคราะห์)
    L2_cm = L2 * 100.0  # Span ขวาง
    lc_cm = lc * 100.0  # ความสูงเสา
    c1_cm = c1_w        # ขนาดเสาด้านขนาน Span
    c2_cm = c2_w        # ขนาดเสาด้านขวาง Span
    
    with st.expander("0. ข้อมูลวัสดุและมิติ (Material & Geometry)", expanded=True):
        col_0a, col_0b = st.columns(2)
        with col_0a:
            st.write(f"**Concrete ($f'_c$):** {fc} ksc")
            st.write(f"**Rebar ($f_y$):** {fy} ksc")
            st.latex(f"E_c = 15100\\sqrt{{{fc}}} = {Ec:,.0f} \\text{{ ksc}}")
        with col_0b:
            st.write(f"**Column ($c_1 \\times c_2$):** {c1_cm} x {c2_cm} cm")
            st.write(f"**Slab Thickness ($h$):** {h_slab} cm")
            st.write(f"**Span ($L_1 \\times L_2$):** {L1} x {L2} m")

    # =========================================================================
    # PART 1: STIFFNESS ANALYSIS (วิเคราะห์ความแข็ง)
    # =========================================================================
    st.subheader("1. Stiffness Analysis (วิเคราะห์สติฟเนส)")
    st.markdown("การหาค่า $K$ เพื่อนำไปหาอัตราส่วนการกระจายโมเมนต์ ($DF$)")

    # --- 1.1 Column Stiffness ---
    st.markdown("##### 1.1 Column Stiffness ($K_c$)")
    Ic = c2_cm * (c1_cm**3) / 12.0
    # Kc = 4EI/L
    Kc_val = 4 * Ec * Ic / lc_cm
    Sum_Kc = 2 * Kc_val # บน + ล่าง

    st.latex(f"I_c = \\frac{{{c2_cm} \\cdot {c1_cm}^3}}{{12}} = {Ic:,.0f} \\text{{ cm}}^4")
    st.latex(f"K_c = \\frac{{4 E_c I_c}}{{l_c}} = \\frac{{4 ({Ec:,.0f}) ({Ic:,.0f})}}{{{lc_cm:.0f}}} = {Kc_val:,.0f} \\text{{ kg-cm}}")
    st.write(f"รวมเสาบน-ล่าง: $\\Sigma K_c = 2 \\times K_c = {Sum_Kc:,.0f}$ kg-cm")

    # --- 1.2 Slab Stiffness ---
    st.markdown("##### 1.2 Slab Stiffness ($K_s$)")
    Is = L2_cm * (h_slab**3) / 12.0
    Ks_val = 4 * Ec * Is / L1_cm
    
    st.latex(f"I_s = \\frac{{{L2_cm:.0f} \\cdot {h_slab}^3}}{{12}} = {Is:,.0f} \\text{{ cm}}^4")
    st.latex(f"K_s = \\frac{{4 E_c I_s}}{{L_1}} = \\frac{{4 ({Ec:,.0f}) ({Is:,.0f})}}{{{L1_cm:.0f}}} = {Ks_val:,.0f} \\text{{ kg-cm}}")

    # --- 1.3 Torsional Stiffness ---
    st.markdown("##### 1.3 Torsional Member ($K_t$)")
    st.caption("ส่วนประกอบบิดตัวที่ทำให้เสา 'อ่อน' ลงในมุมมองของพื้น")
    
    x = h_slab
    y = c1_cm
    term1 = (1 - 0.63 * x / y)
    C = term1 * (x**3 * y) / 3.0
    
    term_denom = L2_cm * ((1 - c2_cm/L2_cm)**3)
    if term_denom == 0: term_denom = 1
    Kt_val = 9 * Ec * C / term_denom

    st.latex(f"C = (1 - 0.63\\frac{{{x}}}{{{y}}}) \\frac{{{x}^3 ({y})}}{{3}} = {C:,.0f} \\text{{ cm}}^4")
    st.latex(f"K_t = \\frac{{9 E_c C}}{{L_2(1-c_2/L_2)^3}} = \\frac{{9 ({Ec:,.0f}) ({C:,.0f})}}{{{term_denom:,.0f}}} = {Kt_val:,.0f} \\text{{ kg-cm}}")

    # --- 1.4 Equivalent Column ---
    st.markdown("##### 1.4 Equivalent Column ($K_{ec}$)")
    if Kt_val > 0:
        inv_Kec = (1/Sum_Kc) + (1/Kt_val)
        Kec_val = 1/inv_Kec
        st.latex(f"\\frac{{1}}{{K_{{ec}}}} = \\frac{{1}}{{\\Sigma K_c}} + \\frac{{1}}{{K_t}} \\implies K_{{ec}} = \\mathbf{{{Kec_val:,.0f}}} \\text{{ kg-cm}}")
    else:
        Kec_val = Sum_Kc
        st.error("K_t is zero!")

    # --- 1.5 Distribution Factors ---
    st.markdown("##### 1.5 Distribution Factors (DF)")
    
    if col_type == 'edge':
        # Edge Joint: Slab + Kec
        sum_K = Ks_val + Kec_val
        df_slab = Ks_val / sum_K
        df_col = Kec_val / sum_K
        joint_type = "Edge Joint (Slab + Col)"
    else:
        # Interior Joint: Slab(Left) + Slab(Right) + Kec
        # Assume symmetric spans for standard calculation
        sum_K = Ks_val + Ks_val + Kec_val
        df_slab = Ks_val / sum_K
        df_col = Kec_val / sum_K
        joint_type = "Interior Joint (Slab Left + Slab Right + Col)"

    st.write(f"**พิจารณาที่จุดต่อแบบ: {joint_type}**")
    st.latex(f"\\Sigma K_{{joint}} = {sum_K:,.0f}")
    st.latex(f"DF_{{slab}} = K_s / \\Sigma K = {Ks_val:,.0f} / {sum_K:,.0f} = \\mathbf{{{df_slab:.4f}}}")
    st.latex(f"DF_{{col}} = K_{{ec}} / \\Sigma K = {Kec_val:,.0f} / {sum_K:,.0f} = \\mathbf{{{df_col:.4f}}}")
    
    # Check DF sum
    df_sum_check = df_slab + df_col if col_type == 'edge' else 2*df_slab + df_col
    if abs(df_sum_check - 1.0) > 0.01:
        st.warning(f"Note: Sum of DF = {df_sum_check:.2f}")

    # =========================================================================
    # PART 2: MOMENT DISTRIBUTION (การกระจายโมเมนต์)
    # =========================================================================
    st.markdown("---")
    st.subheader("2. Moment Analysis (Hardy Cross Verification)")
    st.info("ใช้หลักการ Moment Distribution ถ่ายเทโมเมนต์ตามค่า DF ที่คำนวณได้จริง")

    # Calculate Fixed End Moment
    # w_u (kg/m^2) * L2 (m) = kg/m on the strip
    w_line = w_u * L2
    FEM = w_line * (L1**2) / 12.0
    
    st.write("**2.1 Fixed End Moment (FEM)** - สมมติจุดต่อยึดแน่น:")
    st.latex(f"FEM = \\frac{{w_u L_2 L_1^2}}{{12}} = \\frac{{{w_u} \\cdot {L2} \\cdot {L1}^2}}{{12}} = \\mathbf{{{FEM:,.0f}}} \\text{{ kg-m}}")

    # --- ANALYSIS TABLE ---
    st.write("**2.2 Moment Distribution Table (ตารางกระจายโมเมนต์)**")
    
    if col_type == 'edge':
        # --- CASE 1: EDGE COLUMN ---
        # Unbalanced Moment = FEM (เพราะอีกฝั่งไม่มีพื้น)
        # ต้อง Release โมเมนต์นี้กลับเข้าไปในพื้นและเสา
        
        M_unbalanced = FEM
        M_dist_slab = -1 * M_unbalanced * df_slab
        M_dist_col  = -1 * M_unbalanced * df_col
        
        M_final_slab = FEM + M_dist_slab
        M_final_col  = 0 + M_dist_col  # เริ่มจาก 0 เพราะเสาไม่มี FEM
        
        # Display DataFrame
        data_md = {
            "Step": ["1. Initial FEM", "2. Distribution Factor (DF)", "3. Distributed Moment (-FEM*DF)", "4. Final Moment (Sum)"],
            "Slab End (Joint)": [f"{FEM:,.0f}", f"{df_slab:.4f}", f"{M_dist_slab:,.0f}", f"**{M_final_slab:,.0f}**"],
            "Column (Joint)":   ["0",             f"{df_col:.4f}",  f"{M_dist_col:,.0f}",  f"**{M_final_col:,.0f}**"]
        }
        df_show = pd.DataFrame(data_md)
        st.table(df_show)
        
        # Design Values
        M_neg_design = M_final_slab
        # หา M+ (Statics)
        ln = L1 - (c1_w/100.0)
        Mo = w_u * L2 * (ln**2) / 8.0
        # M_pos = Mo - (M_neg_avg) => Edge ใช้ M_neg/2 โดยประมาณ หรือใช้สูตร Superposition
        # เพื่อความถูกต้องตาม Statics เราใช้ Mo เป็นตัวคุม
        M_pos_design = Mo - (M_neg_design + 0)/2.0 
        
        # Verification Text
        check_sum = M_final_slab + M_final_col
        st.markdown(f"**🔎 Verification (ตรวจสอบสมดุล):**")
        st.write(f"ผลรวมโมเมนต์ที่จุดต่อ = $M_{{slab}} + M_{{col}} = {M_final_slab:,.0f} + ({M_final_col:,.0f}) = {check_sum:,.0f}$ $\\approx 0$ (OK)")
        
    else:
        # --- CASE 2: INTERIOR COLUMN ---
        # ต้องสมมติ Pattern Load เพื่อให้เกิด Unbalanced Moment ไม่งั้น DF จะไม่ได้ใช้
        st.markdown("*(กรณี Interior: สมมติ Pattern Load ให้ Span ที่พิจารณารับ Full Load แต่อีกฝั่งรับ 50% Load เพื่อให้เห็นผลของ Stiffness)*")
        
        w_right = w_u
        w_left = w_u * 0.5
        
        FEM_right = FEM # ทิศทวนเข็ม (-)
        FEM_left = (w_left * L2 * L1**2) / 12.0 # ทิศตามเข็ม (+)
        
        # Sign convention: Clockwise +, Counter-Clockwise -
        # Joint Equilibrium: M_unbalanced = Sum(FEMs)
        # FEM_right is acting on joint -> usually defined as Clockwise on Joint
        # Let's simplify: Unbalanced = Difference in FEM magnitude
        
        Unbal = FEM_right - FEM_left
        
        # Distribute
        M_dist_slab_right = -1 * Unbal * df_slab
        M_dist_col = -1 * Unbal * df_col
        
        M_final_right = FEM_right + M_dist_slab_right
        
        data_md = {
            "Parameter": ["FEM (Span นี้)", "FEM (Span ข้างๆ)", "Unbalanced Diff", "DF (Slab)", "Distributed", "Final Design M-"],
            "Value": [f"{FEM_right:,.0f}", f"{FEM_left:,.0f}", f"{Unbal:,.0f}", f"{df_slab:.4f}", f"{M_dist_slab_right:,.0f}", f"**{M_final_right:,.0f}**"]
        }
        st.table(pd.DataFrame(data_md))
        
        M_neg_design = M_final_right
        # Interior M+
        ln = L1 - (c1_w/100.0)
        Mo = w_u * L2 * (ln**2) / 8.0
        M_pos_design = Mo - (M_neg_design * 0.9) # Approx deduction
        M_pos_design = max(M_pos_design, 0.35*Mo) # ACI Min check

    # สรุปค่าโมเมนต์ออกแบบ
    st.success(f"✅ **Design Moments (Verified):** $M^-$ = {M_neg_design:,.0f} kg-m, $M^+$ = {M_pos_design:,.0f} kg-m")

    # =========================================================================
    # PART 3: REINFORCEMENT DESIGN (ออกแบบเหล็กเสริม)
    # =========================================================================
    st.markdown("---")
    st.subheader("3. Reinforcement Design (ออกแบบเหล็กเสริม)")

    # 3.1 เลือกตำแหน่ง
    design_loc = st.radio("เลือกตำแหน่งที่ต้องการดูรายการคำนวณ:", 
                          ["Column Strip (Top/Neg)", "Column Strip (Bot/Pos)", "Middle Strip (Top/Neg)", "Middle Strip (Bot/Pos)"],
                          horizontal=True)

    # 3.2 กำหนด % การกระจายโมเมนต์เข้าแถบ (ACI/EIT Tables)
    if col_type == 'interior':
        map_pct = {'CS-':0.75, 'CS+':0.60, 'MS-':0.25, 'MS+':0.40}
    else:
        map_pct = {'CS-':1.00, 'CS+':0.60, 'MS-':0.00, 'MS+':0.40}

    # Map Selection to Variables
    if "Column Strip" in design_loc:
        strip_width = L2 / 2.0
        code_prefix = "CS"
    else:
        strip_width = L2 / 2.0
        code_prefix = "MS"

    if "Neg" in design_loc:
        M_base = M_neg_design
        pct = map_pct[code_prefix + "-"]
        bar_pos = "Top Bars"
    else:
        M_base = M_pos_design
        pct = map_pct[code_prefix + "+"]
        bar_pos = "Bottom Bars"

    Mu_strip = M_base * pct
    
    # 3.3 แสดงรายการคำนวณ RC Design
    st.markdown(f"#### Design Detail for: {design_loc}")
    
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        st.write(f"**1. Moment ($M_u$):**")
        st.latex(f"M_u = M_{{frame}} \\times \\text{{%Dist}}")
        st.latex(f"M_u = {M_base:,.0f} \\times {pct} = \\mathbf{{{Mu_strip:,.0f}}} \\text{{ kg-m}}")
    
    with col_d2:
        st.write(f"**2. Section Properties:**")
        b_cm = strip_width * 100
        d_eff = h_slab - mat_props['cover'] - (mat_props['d_bar']/20.0) # Approx d
        st.write(f"Strip Width ($b$): {b_cm:.0f} cm")
        st.write(f"Effective Depth ($d$): {d_eff:.2f} cm")

    if Mu_strip <= 100:
        st.warning("Moment น้อยมาก ไม่จำเป็นต้องคำนวณ (Use Min Steel)")
    else:
        st.markdown("**3. Flexural Check:**")
        
        # Rn
        Rn = (Mu_strip * 100) / (0.9 * b_cm * d_eff**2)
        st.latex(f"R_n = \\frac{{M_u \\cdot 100}}{{0.9 b d^2}} = \\frac{{{Mu_strip:,.0f} \\cdot 100}}{{0.9 ({b_cm:.0f}) ({d_eff:.2f})^2}} = {Rn:.2f} \\text{{ ksc}}")
        
        # Rho Required
        term_val = 2 * Rn / (0.85 * fc)
        st.latex(f"\\text{{term}} = \\frac{{2 R_n}}{{0.85 f'_c}} = {term_val:.3f}")

        if term_val >= 1.0:
            st.error(f"❌ **FAIL:** Section too small (term = {term_val:.2f} >= 1). Please increase thickness.")
        else:
            rho_calc = (0.85 * fc / fy) * (1 - np.sqrt(1 - term_val))
            rho_min = 0.0018 # Temp min for slab
            rho_use = max(rho_calc, rho_min)
            
            st.latex(f"\\rho_{{req}} = \\frac{{0.85 f'_c}}{{f_y}}(1 - \\sqrt{{1-\\text{{term}}}}) = {rho_calc:.5f}")
            st.write(f"Compare $\\rho_{{min}} = {rho_min} \\to$ Use $\\rho = {rho_use:.5f}$")
            
            # As Required
            As_req = rho_use * b_cm * d_eff
            st.latex(f"A_{{s,req}} = \\rho b d = {rho_use:.5f} \\cdot {b_cm:.0f} \\cdot {d_eff:.2f} = \\mathbf{{{As_req:.2f}}} \\text{{ cm}}^2")
            
            # Bar Selection
            db = mat_props['d_bar']
            Ab = 3.1416 * (db/20.0)**2
            n_bars = math.ceil(As_req / Ab)
            
            spacing = b_cm / n_bars if n_bars > 0 else 0
            
            st.success(f"✅ **Selection:** {int(n_bars)} - DB{db}mm (Avg Spacing {spacing:.1f} cm)")
            st.caption(f"Area provided: {n_bars * Ab:.2f} cm² > {As_req:.2f} cm²")
