import streamlit as st
import numpy as np
import pandas as pd
import math
# เรียกใช้ฟังก์ชันจาก calculations.py
from calculations import calculate_stiffness 

def render(c1_w, c2_w, L1, L2, lc, h_slab, fc, mat_props, w_u, col_type):
    st.header("3. Equivalent Frame Method (EFM) - Detailed Calculation")
    st.markdown("---")

    # Parameters Setup
    fy = mat_props['fy']
    cover = mat_props['cover']
    d_bar = mat_props['d_bar']
    
    # =========================================================================
    # PART 1: STIFFNESS (เรียกใช้ function ของคุณ)
    # =========================================================================
    st.subheader("1. Stiffness Calculation")

    # เรียก Function: calculate_stiffness
    # Return 4 values: Ks, Sum_Kc, Kt, Kec
    try:
        Ks, Sum_Kc, Kt, Kec = calculate_stiffness(c1_w, c2_w, L1, L2, lc, h_slab, fc)
    except Exception as e:
        st.error(f"Error calling calculations.py: {e}")
        return

    # แสดงผลลัพธ์ Stiffness
    st.write(f"**Calculated Stiffness Parameters:**")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Slab (Ks)", f"{Ks:,.0f}")
    c2.metric("Cols (ΣKc)", f"{Sum_Kc:,.0f}")
    c3.metric("Torsion (Kt)", f"{Kt:,.0f}")
    c4.metric("Equiv Col (Kec)", f"{Kec:,.0f}")

    # คำนวณ Distribution Factors (DF) ต่อในนี้เลย
    st.markdown("**Distribution Factors (DF)**")
    sum_joint = Ks + Kec
    if sum_joint > 0:
        df_slab = Ks / sum_joint
        df_col = Kec / sum_joint
    else:
        df_slab, df_col = 0, 0
    
    st.latex(r"DF_{col} = \frac{K_{ec}}{K_s + K_{ec}} = \frac{" + f"{Kec:,.0f}" + r"}{" + f"{sum_joint:,.0f}" + r"} = \mathbf{" + f"{df_col:.3f}" + r"}")
    
    # =========================================================================
    # PART 2: MOMENT ANALYSIS
    # =========================================================================
    st.markdown("---")
    st.subheader("2. Moment Analysis")
    
    ln = L1 - (c1_w/100.0)
    Mo = w_u * L2 * (ln**2) / 8.0
    FEM = w_u * L2 * (L1**2) / 12.0
    
    st.write(f"Static Moment ($M_o$) = {Mo:,.0f} kg-m")
    
    if col_type == 'interior':
        M_neg = 0.65 * Mo
        M_pos = 0.35 * Mo
        st.success("Case: Interior Column (Standard Distribution)")
    else:
        st.warning(f"Case: Edge Column (Moment transfer via DF = {df_col:.3f})")
        # EFM for Edge: Transfer Moment = FEM * DF_col
        M_neg = FEM * df_col
        M_pos_calc = Mo - (M_neg/2.0)
        M_pos = max(M_pos_calc, 0.50 * Mo) # Minimum pos moment check
    
    col_m1, col_m2 = st.columns(2)
    col_m1.metric("Design M- (Neg)", f"{M_neg:,.0f} kg-m")
    col_m2.metric("Design M+ (Pos)", f"{M_pos:,.0f} kg-m")

    # =========================================================================
    # PART 3: REINFORCEMENT DESIGN
    # =========================================================================
    st.markdown("---")
    st.subheader("3. Reinforcement Design")
    
    # Percentage Distribution Map
    if col_type == 'interior':
        dist_map = {'CS-':0.75, 'CS+':0.60, 'MS-':0.25, 'MS+':0.40}
    else: # Edge
        dist_map = {'CS-':1.00, 'CS+':0.60, 'MS-':0.00, 'MS+':0.40}
        
    rows = []
    strip_w = L2/2.0 
    
    # Loop create table rows
    strips_data = [
        ("Col Strip (-)", M_neg, dist_map['CS-']),
        ("Col Strip (+)", M_pos, dist_map['CS+']),
        ("Mid Strip (-)", M_neg, dist_map['MS-']),
        ("Mid Strip (+)", M_pos, dist_map['MS+'])
    ]
    
    for name, m_base, pct in strips_data:
        Mu = m_base * pct
        if Mu <= 100: 
            sel_text = "-"
        else:
            # Design Calculation
            b_cm = strip_w * 100
            d_eff = h_slab - cover - (d_bar/20.0)
            Rn = (Mu*100)/(0.9 * b_cm * d_eff**2)
            
            rho_min = 0.0018
            term = 2*Rn/(0.85*fc)
            
            if term >= 1.0:
                sel_text = "Thick. Fail"
            else:
                rho = (0.85*fc/fy)*(1 - np.sqrt(1-term))
                rho = max(rho, rho_min)
                As = rho * b_cm * d_eff
                
                db_area = 3.1416 * (d_bar/20.0)**2
                n_bars = math.ceil(As/db_area)
                if n_bars == 0: n_bars = 1
                
                spacing = b_cm / n_bars
                use_spacing = math.floor(spacing/5)*5
                if use_spacing > 30: use_spacing = 30
                if use_spacing < 10: use_spacing = 10
                
                sel_text = f"DB{d_bar} @ {use_spacing/100:.2f} m"
        
        rows.append({
            "Location": name,
            "Moment (Mu)": f"{Mu:,.0f}",
            "Selection": sel_text
        })
        
    st.table(pd.DataFrame(rows))
