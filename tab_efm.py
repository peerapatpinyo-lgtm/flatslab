import streamlit as st
import numpy as np
import pandas as pd
import math

def render(c1_w, c2_w, L1, L2, lc, h_slab, fc, mat_props, w_u, col_type):
    st.header("3. Equivalent Frame Method (Step-by-Step Calculation)")
    st.info("💡 แสดงรายการคำนวณละเอียด: สูตร -> แทนค่า -> ผลลัพธ์")
    st.markdown("---")

    # --- 0. ข้อมูลเบื้องต้น ---
    fy = mat_props['fy']
    Ec = 15100 * np.sqrt(fc)
    
    L1_cm = L1 * 100.0
    L2_cm = L2 * 100.0
    lc_cm = lc * 100.0
    c1_cm = c1_w
    c2_cm = c2_w
    
    # แสดง Parameters
    with st.expander("0. ข้อมูลการออกแบบ (Design Data)", expanded=True):
        st.write(f"**Load ($w_u$):** {w_u} kg/m²")
        st.write(f"**Dimensions:** Span {L1}x{L2} m, Slab {h_slab} cm")
        st.write(f"**Column:** {c1_cm}x{c2_cm} cm, Height {lc} m")

    # =========================================================================
    # PART 1: STIFFNESS (เก็บไว้เหมือนเดิม แต่ย่อให้กระชับเพื่อเน้น Part 2)
    # =========================================================================
    st.subheader("1. Stiffness & Distribution Factors")
    
    # 1.1 Column
    Ic = c2_cm * (c1_cm**3) / 12.0
    Kc_val = 4 * Ec * Ic / lc_cm
    Sum_Kc = 2 * Kc_val
    
    # 1.2 Slab
    Is = L2_cm * (h_slab**3) / 12.0
    Ks_val = 4 * Ec * Is / L1_cm
    
    # 1.3 Torsion & Kec
    x = h_slab; y = c1_cm
    C = (1 - 0.63 * x / y) * (x**3 * y) / 3.0
    denom = L2_cm * ((1 - c2_cm/L2_cm)**3)
    if denom == 0: denom = 1
    Kt_val = 9 * Ec * C / denom
    
    if Kt_val > 0:
        Kec_val = 1 / ((1/Sum_Kc) + (1/Kt_val))
    else:
        Kec_val = Sum_Kc

    # 1.4 DF
    if col_type == 'edge':
        sum_K = Ks_val + Kec_val
        df_slab = Ks_val / sum_K
        df_col = Kec_val / sum_K
        st.write("**Edge Joint DF:**")
    else:
        sum_K = Ks_val + Ks_val + Kec_val
        df_slab = Ks_val / sum_K
        df_col = Kec_val / sum_K
        st.write("**Interior Joint DF:**")
    
    st.latex(f"K_s = {Ks_val:,.0f}, \\quad K_{{ec}} = {Kec_val:,.0f}")
    st.latex(f"DF_{{slab}} = \\frac{{{Ks_val:,.0f}}}{{{sum_K:,.0f}}} = \\mathbf{{{df_slab:.4f}}}")
    st.latex(f"DF_{{col}} = \\frac{{{Kec_val:,.0f}}}{{{sum_K:,.0f}}} = \\mathbf{{{df_col:.4f}}}")

    # =========================================================================
    # PART 2: MOMENT ANALYSIS (ละเอียด ยิบๆ)
    # =========================================================================
    st.markdown("---")
    st.subheader("2. Moment Analysis (แสดงวิธีทำอย่างละเอียด)")
    
    # --- Step 2.1 Calculate FEM ---
    st.markdown("#### 2.1 Fixed End Moment (FEM)")
    st.write("คำนวณโมเมนต์ดัดปลายยึดแน่น (สมมติว่าจุดต่อไม่หมุนเลย)")
    
    FEM = w_u * L2 * (L1**2) / 12.0
    
    st.latex(r"FEM = \frac{w_u L_2 L_1^2}{12}")
    st.latex(f"FEM = \\frac{{{w_u} \\cdot {L2} \\cdot {L1}^2}}{{12}} = \\mathbf{{{FEM:,.0f}}} \\text{{ kg-m}}")
    
    # --- Step 2.2 Unbalanced Moment ---
    st.markdown("#### 2.2 Unbalanced Moment ($M_{unbal}$)")
    
    if col_type == 'edge':
        st.write("**กรณีเสาริม (Edge Column):**")
        st.write("มีโมเมนต์จากพื้นด้านในเพียงด้านเดียว ดังนั้นโมเมนต์ที่ไม่สมดุลคือ FEM ทั้งก้อน")
        
        M_unbal = FEM
        st.latex(f"M_{{unbal}} = FEM = {FEM:,.0f} \\text{{ kg-m}}")
        
        # --- Step 2.3 Distribution ---
        st.markdown("#### 2.3 Distribute Moment (กระจายโมเมนต์)")
        st.write("กระจายโมเมนต์กลับเข้าสู่ชิ้นส่วนต่างๆ ตามค่า $DF$ (เครื่องหมายตรงข้ามกับ Unbalanced)")
        
        M_dist_slab = -1 * M_unbal * df_slab
        M_dist_col  = -1 * M_unbal * df_col
        
        st.write("**(a) กระจายเข้าสู่พื้น (Slab):**")
        st.latex(f"M_{{dist,slab}} = - M_{{unbal}} \\times DF_{{slab}}")
        st.latex(f"M_{{dist,slab}} = - ({M_unbal:,.0f}) \\times {df_slab:.4f} = \\mathbf{{{M_dist_slab:,.0f}}} \\text{{ kg-m}}")
        
        st.write("**(b) กระจายเข้าสู่เสา (Column):**")
        st.latex(f"M_{{dist,col}} = - M_{{unbal}} \\times DF_{{col}}")
        st.latex(f"M_{{dist,col}} = - ({M_unbal:,.0f}) \\times {df_col:.4f} = \\mathbf{{{M_dist_col:,.0f}}} \\text{{ kg-m}}")
        
        # --- Step 2.4 Final Moment ---
        st.markdown("#### 2.4 Final Design Moment ($M_{final}$)")
        
        M_final_slab = FEM + M_dist_slab
        
        st.write("รวมโมเมนต์เริ่มต้น (FEM) กับโมเมนต์ที่กระจายมา (Distributed):")
        st.latex(f"M^{{-}}_{{slab}} = FEM + M_{{dist,slab}}")
        st.latex(f"M^{{-}}_{{slab}} = {FEM:,.0f} + ({M_dist_slab:,.0f}) = \\mathbf{{{M_final_slab:,.0f}}} \\text{{ kg-m}}")
        
        M_neg_design = M_final_slab

    else:
        st.write("**กรณีเสากลาง (Interior Column) - Pattern Loading:**")
        st.write("พิจารณากรณี Span ซ้ายรับ Dead Load (50%) และ Span ขวารับ Full Load (100%) เพื่อให้เกิด Unbalanced Moment")
        
        w_DL = w_u * 0.5
        FEM_left = (w_DL * L2 * L1**2) / 12.0
        FEM_right = FEM
        
        st.latex(f"FEM_{{left}} (DL) = \\frac{{{w_DL:.0f} \\cdot {L2} \\cdot {L1}^2}}{{12}} = {FEM_left:,.0f}")
        st.latex(f"FEM_{{right}} (Total) = {FEM_right:,.0f}")
        
        st.write("หาผลต่างโมเมนต์ (Unbalanced Moment):")
        M_unbal = FEM_right - FEM_left
        st.latex(f"M_{{unbal}} = {FEM_right:,.0f} - {FEM_left:,.0f} = {M_unbal:,.0f} \\text{{ kg-m}}")
        
        st.markdown("#### 2.3 Distribute Moment")
        st.write("กระจายโมเมนต์เข้าสู่พื้น (Span ขวาที่เรากำลังพิจารณาออกแบบ):")
        
        M_dist = -1 * M_unbal * df_slab
        st.latex(f"M_{{dist}} = - M_{{unbal}} \\times DF_{{slab}}")
        st.latex(f"M_{{dist}} = - ({M_unbal:,.0f}) \\times {df_slab:.4f} = \\mathbf{{{M_dist:,.0f}}} \\text{{ kg-m}}")
        
        st.markdown("#### 2.4 Final Design Moment")
        M_final = FEM_right + M_dist
        st.latex(f"M^{{-}}_{{slab}} = FEM_{{right}} + M_{{dist}}")
        st.latex(f"M^{{-}}_{{slab}} = {FEM_right:,.0f} + ({M_dist:,.0f}) = \\mathbf{{{M_final:,.0f}}} \\text{{ kg-m}}")
        
        M_neg_design = M_final

    # --- Step 2.5 Positive Moment ---
    st.markdown("#### 2.5 Positive Moment Calculation ($M^+$)")
    st.write("หาโมเมนต์บวกกลางช่วงคาน (Midspan) จากสมดุลสถิตยศาสตร์ (Static Moment)")
    
    ln = L1 - (c1_w/100.0)
    Mo = w_u * L2 * (ln**2) / 8.0
    
    st.write("1. คำนวณ Static Moment ($M_o$):")
    st.latex(f"M_o = \\frac{{w_u L_2 l_n^2}}{{8}} = \\frac{{{w_u} \\cdot {L2} \\cdot {ln:.2f}^2}}{{8}} = {Mo:,.0f} \\text{{ kg-m}}")
    
    st.write("2. หักลบโมเมนต์ลบที่หัวเสา เพื่อหาโมเมนต์บวก:")
    if col_type == 'edge':
        st.write("*(ใช้ค่าเฉลี่ยโมเมนต์ลบซ้ายขวา สำหรับ Edge ปลายอีกด้านเป็น 0)*")
        M_pos_design = Mo - (M_neg_design + 0)/2.0
        st.latex(f"M^+ = M_o - \\frac{{M^{{-}} + 0}}{{2}} = {Mo:,.0f} - \\frac{{{M_neg_design:,.0f}}}{{2}} = \\mathbf{{{M_pos_design:,.0f}}} \\text{{ kg-m}}")
    else:
        st.write("*(สำหรับ Interior ใช้ 0.65 Mo หรือคำนวณจากสมดุล)*")
        M_pos_calc = Mo - (M_neg_design * 0.9) # Approx
        M_pos_min = 0.35 * Mo
        M_pos_design = max(M_pos_calc, M_pos_min)
        st.latex(f"M^+ \\approx M_o - M^{{-}}_{{avg}} = \\mathbf{{{M_pos_design:,.0f}}} \\text{{ kg-m}}")

    # =========================================================================
    # PART 3: DESIGN (คงเดิม แต่เพิ่มความชัดเจน)
    # =========================================================================
    st.markdown("---")
    st.subheader("3. Reinforcement Design")
    
    design_loc = st.radio("เลือกตำแหน่งออกแบบ:", 
                          ["Column Strip (-)", "Column Strip (+)", "Middle Strip (-)", "Middle Strip (+)"],
                          horizontal=True)
    
    # Map factors
    if col_type == 'interior':
        map_pct = {'CS-':0.75, 'CS+':0.60, 'MS-':0.25, 'MS+':0.40}
    else:
        map_pct = {'CS-':1.00, 'CS+':0.60, 'MS-':0.00, 'MS+':0.40}

    # Identify selection
    if "Column" in design_loc:
        strip_code = "CS"
        b_width = L2/2.0
    else:
        strip_code = "MS"
        b_width = L2/2.0
        
    if "(-)" in design_loc:
        sign = "-"
        M_base = M_neg_design
    else:
        sign = "+"
        M_base = M_pos_design
        
    pct = map_pct[strip_code + sign]
    Mu = M_base * pct
    
    st.markdown(f"**รายการคำนวณเหล็กเสริมสำหรับ {design_loc}:**")
    st.write("1. แปลงโมเมนต์เฟรม ($M_{frame}$) เป็นโมเมนต์แถบ ($M_{strip}$)")
    st.latex(f"M_u = M_{{frame}} \\times \\text{{Percent}} = {M_base:,.0f} \\times {pct} = \\mathbf{{{Mu:,.0f}}} \\text{{ kg-m}}")
    
    if Mu > 100:
        b_cm = b_width * 100
        d_eff = h_slab - mat_props['cover'] - (mat_props['d_bar']/20.0)
        
        st.write("2. ตรวจสอบหน้าตัด ($R_n$):")
        Rn = (Mu * 100) / (0.9 * b_cm * d_eff**2)
        st.latex(f"R_n = \\frac{{M_u \\cdot 100}}{{0.9 b d^2}} = \\frac{{{Mu:,.0f} \\cdot 100}}{{0.9 ({b_cm:.0f}) ({d_eff:.2f})^2}} = {Rn:.2f} \\text{{ ksc}}")
        
        st.write("3. คำนวณปริมาณเหล็ก ($\;\\rho\;$):")
        term = 2 * Rn / (0.85 * fc)
        rho = (0.85 * fc / fy) * (1 - np.sqrt(1 - term))
        rho = max(rho, 0.0018)
        
        st.latex(f"\\rho_{{req}} = {rho:.5f}")
        
        As = rho * b_cm * d_eff
        st.write("4. พื้นที่เหล็กที่ต้องการ ($A_s$):")
        st.latex(f"A_s = \\rho b d = {rho:.5f} \\cdot {b_cm:.0f} \\cdot {d_eff:.2f} = \\mathbf{{{As:.2f}}} \\text{{ cm}}^2")
        
        # Bar selection
        db = mat_props['d_bar']
        Ab = 3.1416 * (db/20.0)**2
        num = math.ceil(As/Ab)
        spacing = b_cm / num
        st.success(f"✅ สรุปใช้เหล็ก: {int(num)} เส้น - DB{db}mm (ระยะห่าง @ {spacing:.0f} cm)")
    else:
        st.info("โมเมนต์น้อยมาก ให้ใช้เหล็กขั้นต่ำ (Min Reinforcement)")
