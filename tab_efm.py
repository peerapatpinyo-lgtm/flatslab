import streamlit as st
import numpy as np
import pandas as pd
import math
from calculations import calculate_stiffness

def render(c1_w, c2_w, L1, L2, lc, h_slab, fc, mat_props, w_u, col_type):
    st.header("3. Equivalent Frame Method (Real Frame Analysis)")
    st.info("💡 คำนวณโมเมนต์ด้วยวิธี Hardy Cross (Moment Distribution) โดยใช้ค่า Stiffness จริง")
    st.markdown("---")

    # --- 0. Setup ---
    fy = mat_props['fy']
    Ec = 15100 * np.sqrt(fc)
    
    L1_cm = L1 * 100
    L2_cm = L2 * 100
    lc_cm = lc * 100
    c1_cm = c1_w
    c2_cm = c2_w
    
    # Material Info
    with st.expander("0. Material & Geometry Data", expanded=False):
        st.write(f"Fc' = {fc} ksc, Fy = {fy} ksc, Ec = {Ec:,.0f} ksc")
        st.write(f"Column: {c1_cm}x{c2_cm} cm, Slab h: {h_slab} cm")

    # =========================================================================
    # PART 1: STIFFNESS (Calculate K & DF)
    # =========================================================================
    st.subheader("1. Stiffness & Distribution Factors")
    
    # 1.1 Calculate Stiffness
    Ic = c2_cm * (c1_cm**3) / 12.0
    Kc = 4 * Ec * Ic / lc_cm
    Sum_Kc = 2 * Kc
    
    Is = L2_cm * (h_slab**3) / 12.0
    Ks = 4 * Ec * Is / L1_cm
    
    # 1.2 Torsional Stiffness
    x = h_slab
    y = c1_cm
    C = (1 - 0.63 * x / y) * (x**3 * y) / 3.0
    denom = (L2_cm * (1 - c2_cm/L2_cm)**3)
    if denom == 0: denom = 1.0
    Kt = 9 * Ec * C / denom
    
    # 1.3 Equivalent Column
    if Kt > 0:
        Kec = 1 / ((1/Sum_Kc) + (1/Kt))
    else:
        Kec = Sum_Kc
        
    # 1.4 Distribution Factors (DF)
    # เราพิจารณา Joint ที่มี: พื้นซ้าย(สมมติ), พื้นขวา(L1), และเสา(Kec)
    # เพื่อความง่ายในการ demo เราจะคิด DF สำหรับ Node ปัจจุบัน
    # DF = K_member / Sum_K_joint
    
    if col_type == 'edge':
        # Edge Node: มีพื้นด้านเดียว (Ks) + เสา (Kec)
        sum_joint = Ks + Kec
        df_slab = Ks / sum_joint
        df_col = Kec / sum_joint
        node_name = "Edge Joint"
    else:
        # Interior Node: มีพื้นซ้าย (Ks) + พื้นขวา (Ks) + เสา (Kec)
        # สมมติ Span ซ้ายยาวเท่า Span ขวา
        sum_joint = Ks + Ks + Kec
        df_slab = Ks / sum_joint # ถ่ายเข้าพื้นฝั่งขวา
        df_col = Kec / sum_joint # ถ่ายเข้าเสา
        node_name = "Interior Joint"

    st.write(f"**Calculated Stiffness Parameters at {node_name}:**")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Slab (Ks)", f"{Ks:,.0e}")
    c2.metric("Torsion (Kt)", f"{Kt:,.0e}")
    c3.metric("Equiv Col (Kec)", f"{Kec:,.0e}")
    c4.metric("Sum K Joint", f"{sum_joint:,.0e}")
    
    st.write("**Distribution Factors (DF):**")
    st.latex(f"DF_{{slab}} = \\frac{{K_s}}{{\\Sigma K}} = \\mathbf{{{df_slab:.3f}}}, \\quad DF_{{col}} = \\frac{{K_{{ec}}}}{{\\Sigma K}} = \\mathbf{{{df_col:.3f}}}")
    if col_type == 'interior':
        st.caption("(Note: For Interior, Sum K includes Slab Left + Slab Right + Col)")

    # =========================================================================
    # PART 2: MOMENT ANALYSIS (Real EFM)
    # =========================================================================
    st.markdown("---")
    st.subheader("2. Moment Analysis (Hardy Cross Method)")
    
    # 2.1 Fixed End Moment (FEM)
    # Load w_u บนคานยึดแน่น
    FEM = w_u * L2 * (L1**2) / 12.0
    st.write(f"**Fixed End Moment (FEM):** (Assume Fixed-Fixed)")
    st.latex(f"FEM = \\frac{{w_u L_2 L_1^2}}{{12}} = {FEM:,.0f} \\text{{ kg-m}}")
    
    # 2.2 Moment Distribution Table
    st.markdown("#### 2.2 Moment Distribution (การกระจายโมเมนต์)")
    
    if col_type == 'edge':
        st.markdown("""
        **Edge Column Analysis:**
        ที่จุดรองรับริมสุด โมเมนต์ Unbalanced คือ FEM ทั้งก้อน
        ธรรมชาติของโครงสร้างจะ 'คลาย' (Release) โมเมนต์นี้กลับเข้าไปตามค่าความแข็ง (Stiffness)
        """)
        
        # Calculation
        unbalanced = FEM 
        dist_to_slab = -1 * unbalanced * df_slab # Moment ที่พื้นดูดกลับไป
        dist_to_col = -1 * unbalanced * df_col   # Moment ที่ถ่ายลงเสา
        
        # Final Moments
        M_slab_neg = FEM + dist_to_slab # นี่คือ M- ที่ปลายพื้น
        M_col = abs(dist_to_col)        # นี่คือ M ที่ถ่ายลงเสา
        
        # Display as Table
        md_data = {
            "Step": ["1. Fixed End Moment (FEM)", "2. Distribution Factors (DF)", "3. Distribute (M_dist = -FEM * DF)", "4. Final Moment (Sum)"],
            "Slab End (Joint)": [f"{FEM:,.0f}", f"{df_slab:.3f}", f"{dist_to_slab:,.0f}", f"**{M_slab_neg:,.0f}**"],
            "Column (Equiv)":   ["0", f"{df_col:.3f}", f"{dist_to_col:,.0f}", f"**{M_col:,.0f}**"]
        }
        st.table(pd.DataFrame(md_data))
        
        M_neg_design = M_slab_neg
        
        # Calculate Positive Moment
        # จาก Statics: Mo = M_neg_avg + M_pos
        ln = L1 - (c1_w/100.0)
        Mo = w_u * L2 * (ln**2) / 8.0
        M_pos_calc = Mo - (M_neg_design + 0)/2.0 # (M_left + M_right)/2, M_right=0 for edge strip approx or midspan logic
        # หรือใช้สูตร Superposition: M_pos = M_simple + M_dist_effect
        M_pos_simple = w_u * L2 * (L1**2) / 8.0
        M_pos_design = M_pos_simple - (M_neg_design / 2.0)
        
    else:
        st.markdown("""
        **Interior Column Analysis (Pattern Loading):**
        ถ้าโหลดเต็มทุกช่วง (Full Load) โมเมนต์ซ้ายขวาจะหักล้างกัน (Unbalanced = 0) ทำให้ DF ไม่มีผล
        แต่ EFM ต้องพิจารณา **Pattern Loading** (โหลดหมากรุก) เพื่อหาค่าวิกฤต
        
        *สมมติกรณี: ช่วงที่เราพิจารณา (Current Span) มี Total Load แต่อีกฝั่งมีแค่ Dead Load (50% Load)*
        """)
        
        # สมมติ Span ข้างๆ Load น้อยกว่า (Pattern Load) เพื่อให้เกิด Unbalanced Moment
        w_dead_approx = w_u * 0.5 
        FEM_curr = FEM
        FEM_adj = w_dead_approx * L2 * (L1**2) / 12.0
        
        Unbalanced = FEM_curr - FEM_adj
        
        # Distribute
        # Moment จะถูกแบ่งเข้า Slab Current, Slab Adj, และ Column
        # สนใจเฉพาะส่วนที่กระทบ Slab Current
        dist_moment = -1 * Unbalanced * df_slab
        
        M_neg_design = FEM_curr + dist_moment
        
        md_data = {
            "Parameter": ["FEM (Current Span)", "FEM (Adj Span - DL only)", "Unbalanced Moment", "DF (Slab)", "Distributed Moment", "Final Design M-"],
            "Value": [f"{FEM_curr:,.0f}", f"{FEM_adj:,.0f}", f"{Unbalanced:,.0f}", f"{df_slab:.3f}", f"{dist_moment:,.0f}", f"**{M_neg_design:,.0f}**"]
        }
        st.table(pd.DataFrame(md_data))
        
        # Static Moment check
        ln = L1 - (c1_w/100.0)
        Mo = w_u * L2 * (ln**2) / 8.0
        M_pos_design = Mo - (M_neg_design * 0.9) # Approx logic for interior
        M_pos_design = max(M_pos_design, 0.35 * Mo) # Code min check

    st.success(f"✅ **Design Moments derived from Stiffness:**")
    c_m1, c_m2 = st.columns(2)
    c_m1.metric("M- (Support)", f"{M_neg_design:,.0f} kg-m", help="Derived from FEM + Distribution")
    c_m2.metric("M+ (Midspan)", f"{M_pos_design:,.0f} kg-m", help="Derived from Static Moment balance")

    # =========================================================================
    # PART 3: REINFORCEMENT (Standard)
    # =========================================================================
    st.markdown("---")
    st.subheader("3. Reinforcement Design")
    
    # Strip Definitions
    if col_type == 'interior':
        factors = {'CS-':0.75, 'CS+':0.60, 'MS-':0.25, 'MS+':0.40}
    else:
        factors = {'CS-':1.00, 'CS+':0.60, 'MS-':0.00, 'MS+':0.40}

    design_opt = st.selectbox("Select Strip:", ["Column Strip (-)", "Column Strip (+)", "Middle Strip (-)", "Middle Strip (+)"])
    
    if "Column" in design_opt:
        width_m = L2/2.0
        code = "CS"
    else:
        width_m = L2/2.0
        code = "MS"
        
    if "(-)" in design_opt:
        Mu = M_neg_design * factors[code+"-"]
    else:
        Mu = M_pos_design * factors[code+"+"]
        
    st.write(f"**Design Moment ($M_u$) for {design_opt}:** {Mu:,.0f} kg-m")
    
    # Simple Design Block
    if Mu > 100:
        b_cm = width_m * 100
        d_eff = h_slab - mat_props['cover'] - (mat_props['d_bar']/20.0)
        Rn = (Mu * 100) / (0.9 * b_cm * d_eff**2)
        term = 2 * Rn / (0.85 * fc)
        
        if term >= 1.0:
            st.error("Section Fail (Too thin)")
        else:
            rho = (0.85 * fc / fy) * (1 - np.sqrt(1 - term))
            rho = max(rho, 0.0018)
            As = rho * b_cm * d_eff
            num_bars = math.ceil(As / (3.1416*(mat_props['d_bar']/20.0)**2))
            st.success(f"Require: {int(num_bars)} - DB{mat_props['d_bar']} (As={As:.2f} cm2)")
    else:
        st.info("Moment too small.")
