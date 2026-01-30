# tab_efm.py
import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from calculations import calculate_stiffness

def render(c1_w, c2_w, L1, L2, lc, h_slab, fc, mat_props, w_u, col_type):
    st.header("3. Equivalent Frame Method (EFM) - Full Analysis")
    st.info("💡 ในวิธี EFM ค่า Stiffness และ DF จะถูกนำมาใช้เพื่อวิเคราะห์หาโมเมนต์ที่หัวเสา (Negative Moment) แทนที่จะใช้สัมประสิทธิ์ตายตัวแบบ DDM")

    # Parameters
    fy = mat_props['fy']
    cover = mat_props['cover']
    d_bar = mat_props['d_bar']
    
    # ===========================================================
    # STEP 1: STIFFNESS & DF (หาความแข็งและการกระจายแรง)
    # ===========================================================
    st.subheader("Step 1: Stiffness & Distribution Factors")
    
    Ks, Kc_total, Kt, Kec = calculate_stiffness(c1_w, c2_w, L1, L2, lc, h_slab, fc)
    
    # Calculate Distribution Factors (DF) at the Joint
    sum_K = Ks + Kec
    df_col = Kec / sum_K if sum_K > 0 else 0  # DF เข้าเสา (รวม Torsion)
    df_slab = Ks / sum_K if sum_K > 0 else 0  # DF เข้าพื้น
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Slab Stiffness (Ks)", f"{Ks:,.0f}")
    c2.metric("Equiv Col Stiffness (Kec)", f"{Kec:,.0f}")
    c3.metric("DF Column (เข้าเสา)", f"{df_col:.3f}", help="ตัวเลขนี้จะถูกนำไปคูณหาโมเมนต์ลบที่ถ่ายเข้าเสา")

    # ===========================================================
    # STEP 2: MOMENT ANALYSIS (จุดที่นำ K มาคำนวณต่อ)
    # ===========================================================
    st.markdown("---")
    st.subheader("Step 2: Moment Analysis (วิเคราะห์โมเมนต์ด้วย EFM)")
    
    # 2.1 Fixed End Moment (FEM)
    # สมมุติเป็น Uniform Load เต็ม Floor
    ln = L1 - (c1_w/100)
    FEM = (w_u * L2 * L1**2) / 12.0
    
    st.write("เริ่มจากหา Fixed End Moment (FEM) ของคานช่วงเดี่ยวก่อน:")
    st.latex(r"FEM = \frac{w_u L_2 L_1^2}{12} = " + f"{FEM:,.0f}" + r" \text{ kg-m}")
    
    # 2.2 Determine Actual Moments based on Column Type & DF
    st.markdown(f"**วิเคราะห์การถ่ายแรงกรณี: {col_type.upper()} Column**")
    
    if col_type == 'interior':
        st.write("กรณีเสากลาง (Interior): เนื่องจากสมมาตร โมเมนต์สองฝั่งมักจะสมดุลกัน")
        st.write("แต่เพื่อความปลอดภัย (Conservative) และตามพฤติกรรม EFM จะใช้ค่า FEM เป็นโมเมนต์ลบหลัก")
        M_neg_total = FEM 
        # Note: ใน EFM จริงๆ ถ้า Load ไม่เท่ากันจะเกิด Unbalanced Moment กระจายด้วย DF แต่ที่นี้คิด Gravity ทั่วไป
        
    else: # Edge or Corner
        st.markdown("""
        กรณีเสาริม (Edge/Corner): เกิด **Unbalanced Moment** ที่จุดต่อ
        โมเมนต์ลบที่ถ่ายจากพื้นเข้าเสา จะขึ้นอยู่กับความแข็งของเสา ($DF_{col}$)
        """)
        st.latex(r"M_{neg} \approx FEM \times DF_{col}")
        
        M_neg_total = FEM * df_col
        
        st.write(f"แทนค่า: {FEM:,.0f} x {df_col:.3f}")
        st.latex(r"M_{neg, total} = \mathbf{" + f"{M_neg_total:,.0f}" + r"} \text{ kg-m}")
        
        if df_col < 0.3:
            st.warning(f"⚠️ เสา/จุดต่อมีความแข็งน้อย (DF={df_col:.2f}) ทำให้โมเมนต์ถ่ายเข้าเสาน้อย และโมเมนต์บวกกลางช่วงจะเพิ่มขึ้นมาก")

    # 2.3 Calculate Positive Moment (Static Balance)
    # Mo_static = wu * L2 * ln^2 / 8  (คิดแบบ Simple Beam หรือ DDM reference)
    # แต่ใน EFM: M_pos = (Simple Span Moment) - (Average End Moments)
    M_simple = (w_u * L2 * L1**2) / 8.0
    M_pos_total = M_simple - M_neg_total # (คิดแบบหยาบว่าอีกฝั่งสมมาตร หรือเป็น 0 ถ้าปลายอีกด้าน Pin)
    
    # ปรับแก้ M_pos ให้ไม่ต่ำเกินไป (ACI Rule check)
    if M_pos_total < M_simple * 0.35: M_pos_total = M_simple * 0.35 

    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.markdown(f"#### $M^{{-}}_{{slab}}$ (Negative)")
        st.metric("Total Neg Moment", f"{M_neg_total:,.0f} kg-m")
    with col_m2:
        st.markdown(f"#### $M^{{+}}_{{slab}}$ (Positive)")
        st.metric("Total Pos Moment", f"{M_pos_total:,.0f} kg-m")
        st.caption(f"(Derived from Statics: M_simple - M_neg)")

    # ===========================================================
    # STEP 3: DISTRIBUTE TO STRIPS & DESIGN
    # ===========================================================
    st.markdown("---")
    st.subheader("Step 3: Distribute to Strips & Design")
    st.write("กระจายโมเมนต์รวมเข้าสู่ Column Strip (CS) และ Middle Strip (MS) ตามเปอร์เซ็นต์มาตรฐาน")

    # Define Distribution Percentages (Approx ACI)
    # Interior: 75% Neg to CS, 60% Pos to CS
    # Edge: 100% Neg to CS (Load transfer to support), 60% Pos to CS
    if col_type == 'interior':
        pct_cs_neg, pct_cs_pos = 0.75, 0.60
    else:
        pct_cs_neg, pct_cs_pos = 1.00, 0.60 # Edge takes full moment into column strip
    
    strips_data = {
        "Col Strip (-)": [M_neg_total * pct_cs_neg, L2/2.0],
        "Col Strip (+)": [M_pos_total * pct_cs_pos, L2/2.0],
        "Mid Strip (-)": [M_neg_total * (1-pct_cs_neg), L2/2.0],
        "Mid Strip (+)": [M_pos_total * (1-pct_cs_pos), L2/2.0],
    }

    # Display Design Table
    design_data = []
    d_eff = h_slab - cover - (d_bar/20.0)
    db_area = 3.14159 * (d_bar/20.0)**2
    
    for loc, val in strips_data.items():
        M_u, b_w = val
        if M_u <= 0: continue
        
        # --- Rebar Logic ---
        b_cm = b_w * 100
        Rn = (M_u * 100) / (0.9 * b_cm * d_eff**2)
        
        rho_min = 0.0018
        term = 2 * Rn / (0.85 * fc)
        if term < 1.0:
            rho = (0.85*fc/fy) * (1 - np.sqrt(1 - term))
            rho = max(rho, rho_min)
        else:
            rho = 999 # Fail
            
        As_req = rho * b_cm * d_eff
        num_bars = As_req / db_area
        
        design_data.append({
            "Location": loc,
            "Design Moment (Mu)": f"{M_u:,.0f}",
            "Strip Width": f"{b_w:.2f} m",
            "As Req": f"{As_req:.2f} cm²",
            "Rebar Suggestion": f"{int(np.ceil(num_bars))} - DB{d_bar}"
        })

    st.table(pd.DataFrame(design_data))
    
    st.info(f"💡 สังเกตว่าถ้าจุดต่อเป็น Edge และ Stiffness เสาต่ำ ($K_{{ec}}$ น้อย) โมเมนต์ลบจะน้อยลง แต่โมเมนต์บวกจะเพิ่มขึ้น ซึ่งนี่คือสิ่งที่ EFM จำลองพฤติกรรมจริงได้ดีกว่า DDM")
