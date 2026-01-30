import streamlit as st
import numpy as np
import pandas as pd
import viz_torsion  # <--- เรียกใช้ไฟล์วาดรูปที่เราเพิ่งสร้าง

def render(c1_w, c2_w, L1, L2, lc, h_slab, fc, mat_props, w_u, col_type):
    """
    Main EFM Calculation & Visualization
    """
    st.header("3. Equivalent Frame Method (Visual Analysis)")
    st.info("💡 การวิเคราะห์โครงสร้างเสมือนและตรวจสอบแรงบิด (Torsion)")
    st.markdown("---")

    # --- 0. Data Prep ---
    Ec = 15100 * np.sqrt(fc)
    E_ksm = Ec * 10000
    L1_m, L2_m, lc_m = L1, L2, lc
    c1_cm, c2_cm, h_cm = c1_w, c2_w, h_slab
    
    # Moment of Inertia
    Ic = (c2_cm/100) * ((c1_cm/100)**3) / 12.0
    Is = L2_m * ((h_cm/100)**3) / 12.0

    # --- Determine Torsion Arms based on Column Type ---
    # Logic: Corner = 1 Arm, Interior/Edge = 2 Arms
    if col_type.lower() == 'corner':
        num_arms = 1
        arm_desc = "1 Side (Corner Condition)"
    else:
        num_arms = 2
        arm_desc = "2 Sides (Interior/Edge Condition)"

    with st.expander("📋 Design Parameters", expanded=False):
        st.write(f"- Load: {w_u:,.0f} kg/m²")
        st.write(f"- Span: {L1_m} m x {L2_m} m")
        st.write(f"- Member: Col {c1_cm}x{c2_cm} cm, Slab {h_cm} cm")
        st.write(f"- **Torsion Condition:** {col_type.capitalize()} -> {arm_desc}")

    # =========================================================================
    # STEP 1: VISUALIZATION & STIFFNESS
    # =========================================================================
    st.subheader("Step 1: Torsional Stiffness Analysis")

    # 1. แสดงรูปภาพจากไฟล์ viz_torsion
    col_viz, col_calc = st.columns([1.5, 1])
    
    with col_viz:
        st.markdown("**Visualization:**")
        # เรียกใช้ฟังก์ชันวาดรูปจากไฟล์แยก
        fig = viz_torsion.plot_torsion_member(col_type.lower(), c1_cm, c2_cm, h_cm, L1_m, L2_m)
        st.pyplot(fig, use_container_width=True)

    with col_calc:
        st.markdown("**Calculation ($K_t$):**")
        
        # Calculate C
        x, y = h_cm, c1_cm
        C_val = (1 - 0.63 * x / y) * (x**3 * y) / 3.0
        
        # Calculate Kt (one arm)
        Kt_one = 9 * E_ksm * (C_val/1e8) / (L2_m * ((1 - (c2_cm/100)/L2_m)**3))
        
        # Calculate Total Kt
        Kt_total = Kt_one * num_arms
        
        st.latex(r"C = \left(1-0.63\frac{x}{y}\right)\frac{x^3y}{3}")
        st.write(f"- $C = {C_val:,.0f} \\text{{ cm}}^4$")
        st.write(f"- $K_{{t,arm}} = {Kt_one:,.0f}$")
        st.markdown("---")
        st.write(f"**Total Arms:** {num_arms}")
        st.latex(f"K_t = {num_arms} \\times {Kt_one:,.0f}")
        st.latex(f"K_t = \\mathbf{{{Kt_total:,.2e}}}")

    # =========================================================================
    # STEP 2: SUMMARY K & DF
    # =========================================================================
    st.markdown("---")
    st.subheader("Step 2: Distribution Factors (DF)")
    
    Kc = 4 * E_ksm * Ic / lc_m
    Sum_Kc = 2 * Kc
    Ks = 4 * E_ksm * Is / L1_m
    
    # Equivalent Column Stiffness (Kec)
    if Kt_total > 0:
        Kec = 1 / (1/Sum_Kc + 1/Kt_total)
    else:
        Kec = 0 # Should not happen in normal design
    
    # DF Calculation
    if col_type == 'edge': 
        sum_k = Ks + Kec
    else: 
        sum_k = 2*Ks + Kec # Interior
        
    df_slab = Ks/sum_k
    
    col_k1, col_k2, col_k3 = st.columns(3)
    col_k1.metric("Sum Kc", f"{Sum_Kc:,.2e}")
    col_k2.metric("Kec (Equiv)", f"{Kec:,.2e}")
    col_k3.metric("DF Slab", f"{df_slab:.3f}")

    # =========================================================================
    # STEP 3: MOMENTS
    # =========================================================================
    st.markdown("---")
    st.subheader("Step 3: Design Moments")
    
    w_line = w_u * L2_m
    FEM_val = w_line * (L1_m**2) / 12.0
    
    # Simplified Moment Distribution for one joint
    if col_type == 'interior':
        Unbal = FEM_val - (0.5 * w_line * L1_m**2 / 12.0) # Assume adjacent span 50% load diff
        Dist = -1 * Unbal * df_slab
        M_cl_neg = FEM_val + Dist
    else:
        Unbal = FEM_val
        Dist = -1 * Unbal * df_slab
        M_cl_neg = FEM_val + Dist
        
    # Face of support correction
    c1_m = c1_cm / 100.0
    Vu_sup = w_line * L1_m / 2.0
    M_red = (Vu_sup * c1_m/2) - (w_line * (c1_m/2)**2 / 2.0)
    M_face = M_cl_neg - M_red
    
    M_simple = w_line * (L1_m**2) / 8.0
    M_pos = M_simple - (M_face if col_type=='interior' else (M_face+0)/2)

    # Show Result Table
    res_data = {
        "Type": ["Negative Moment (M-)", "Positive Moment (M+)"],
        "Value at CL": [f"{M_cl_neg:,.0f}", "-"],
        "Value at Face": [f"**{M_face:,.0f}**", f"**{M_pos:,.0f}**"]
    }
    st.table(pd.DataFrame(res_data))
    st.caption("*หน่วย: kg-m")
