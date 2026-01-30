import streamlit as st
import numpy as np
import pandas as pd
from viz_torsion import plot_torsion_member  # เรียกใช้ฟังก์ชันวาดรูปจากไฟล์ที่เราเพิ่งแก้

def render_efm_tab():
    st.header("Equivalent Frame Method (EFM) Analysis")
    st.markdown("---")

    # --- 1. Inputs Section (รับค่า) ---
    st.subheader("1. Design Parameters (กำหนดค่าออกแบบ)")
    
    col_in1, col_in2, col_in3 = st.columns(3)
    
    with col_in1:
        st.markdown("**Geometry (มิติ)**")
        L1 = st.number_input("Span Length L1 (ทิศทางวิเคราะห์) [m]", value=6.0, step=0.5)
        L2 = st.number_input("Transverse Span L2 (ความกว้างแถบ) [m]", value=6.0, step=0.5)
        h_slab = st.number_input("Slab Thickness (h) [cm]", value=20.0, step=1.0)
        
    with col_in2:
        st.markdown("**Column Dimensions (ขนาดเสา)**")
        c1 = st.number_input("Column c1 (Dimension // L1) [cm]", value=40.0, step=5.0)
        c2 = st.number_input("Column c2 (Dimension // L2) [cm]", value=40.0, step=5.0)
        col_h = st.number_input("Column Height (Lc) [m]", value=3.0, step=0.1)

    with col_in3:
        st.markdown("**Material (วัสดุ)**")
        fc = st.number_input("f'c (Concrete Strength) [ksc]", value=240.0)
        # Calculate E_c (Estimate)
        Ec = 15100 * np.sqrt(fc) # ksc unit approximation
        st.write(f"**Modulus Elasticity (Ec):** {Ec:,.0f} ksc")
        col_loc = st.selectbox("Column Location (ตำแหน่งเสา)", ["Interior", "Edge", "Corner"])

    st.markdown("---")

    # --- 2. Calculation Core (คำนวณละเอียด) ---
    
    # Unit Conversion
    L1_cm = L1 * 100
    L2_cm = L2 * 100
    Lc_cm = col_h * 100
    
    # 2.1 Column Stiffness (Kc)
    # Inertia of Column
    Ic = (c2 * c1**3) / 12
    # Stiffness Kc (Assume Fixed-Fixed for simplicity factor = 4E)
    # ACI usually considers infinite rigid arm, but here let's simplify to 4EI/L
    Kc = (4 * Ec * Ic) / Lc_cm
    # If Interior column, we have 2 columns (Above and Below), assume same size
    Sum_Kc = 2 * Kc 

    # 2.2 Slab Stiffness (Ks)
    # Inertia of Slab (Full width L2)
    Is = (L2_cm * h_slab**3) / 12
    # Stiffness Ks (4EI/L)
    Ks = (4 * Ec * Is) / L1_cm

    # 2.3 Torsional Member Stiffness (Kt) - The Critical Part
    # Torsional member is the strip of slab perpendicular to the frame.
    # Cross section: width = c1, height = h_slab
    # (Checking if beam exists? Assume flat plate -> just slab strip)
    x = min(c1, h_slab)
    y = max(c1, h_slab)
    
    # Torsional Constant C
    # Formula: C = sum( (1 - 0.63(x/y)) * (x^3 * y) / 3 )
    C_val = (1 - 0.63 * (x/y)) * (x**3 * y) / 3
    
    # Kt Formula (ACI 318)
    # Kt = sum ( 9 * Ec * C / (L2 * (1 - c2/L2)**3) )
    # Check arm count
    if col_loc == "Interior":
        num_arms = 2 # Left and Right of column
    elif col_loc == "Edge":
        num_arms = 2 # Assuming edge is along L1, so transverse still has torsion? 
        # Actually for standard Edge Column analysis (Perpendicular to edge), Kt has 2 arms (torsion sides).
        # But if analyzing Parallel to edge, it might differ. Let's assume standard 2 arms for torsion strip at edge.
        num_arms = 2 
    else: # Corner
        num_arms = 1

    term_geom = L2_cm * (1 - (c2/L2_cm))**3
    if term_geom == 0: term_geom = 1 # prevent div/0
    Kt_one_arm = (9 * Ec * C_val) / term_geom
    Kt = num_arms * Kt_one_arm

    # 2.4 Equivalent Column Stiffness (Kec)
    # Formula: 1/Kec = 1/Sum_Kc + 1/Kt
    if Kt == 0:
        Kec = 0
    else:
        inv_Kec = (1 / Sum_Kc) + (1 / Kt)
        Kec = 1 / inv_Kec

    # 2.5 Distribution Factors (DF)
    # DF_slab = Ks / (Ks + Kec)
    # DF_col = Kec / (Ks + Kec) (Distributed to equivalent column)
    Sum_K_joint = Ks + Kec
    DF_slab = Ks / Sum_K_joint
    DF_col = Kec / Sum_K_joint # This goes to the equivalent column structure

    # --- 3. Display Results (Layout จัดเต็ม) ---
    
    col_res_text, col_res_viz = st.columns([1, 1.2])

    with col_res_text:
        st.subheader("2. Detailed Calculations")
        
        # Step 1: Column
        with st.expander("Step 1: Column Stiffness ($K_c$)", expanded=True):
            st.latex(r"I_c = \frac{c_2 \cdot c_1^3}{12}")
            st.write(f"- $I_c$: {Ic:,.0f} cm⁴")
            st.write(f"- $\sum K_c$ (Above + Below): **{Sum_Kc:,.0f}** ksc·cm")

        # Step 2: Slab
        with st.expander("Step 2: Slab-Beam Stiffness ($K_s$)", expanded=True):
            st.latex(r"I_s = \frac{L_2 \cdot h^3}{12}")
            st.write(f"- $I_s$: {Is:,.0f} cm⁴")
            st.write(f"- $K_s$: **{Ks:,.0f}** ksc·cm")

        # Step 3: Torsional Member (ไฮไลท์ส่วนที่เคยหายไป)
        with st.expander("Step 3: Torsional Member ($K_t$)", expanded=True):
            st.markdown(f"Cross-section for Torsion: **{x:.0f} x {y:.0f} cm**")
            st.latex(r"C = \left(1 - 0.63 \frac{x}{y}\right) \frac{x^3 y}{3}")
            st.write(f"- Torsional Constant ($C$): **{C_val:,.0f} cm⁴**")
            st.latex(r"K_t = \sum \frac{9 E_c C}{L_2 (1 - c_2/L_2)^3}")
            st.write(f"- $K_t$ (Total): **{Kt:,.0f}** ksc·cm")

        # Step 4: Equivalent Column
        with st.expander("Step 4: Equivalent Stiffness ($K_{ec}$)", expanded=True):
            st.latex(r"\frac{1}{K_{ec}} = \frac{1}{\sum K_c} + \frac{1}{K_t}")
            st.metric("Kec (Equivalent Column)", f"{Kec:,.0f}", "ksc·cm")

    with col_res_viz:
        st.subheader("3. Visualization & Results")
        
        # Call the Improved Visualization
        col_type_key = col_loc.lower()
        fig = plot_torsion_member(col_type_key, c1, c2, h_slab, L1, L2)
        st.pyplot(fig)
        
        st.markdown("### Final Distribution Factors (DF)")
        
        # Create a nice summary table
        df_results = pd.DataFrame({
            "Component": ["Slab ($K_s$)", "Equivalent Column ($K_{ec}$)"],
            "Stiffness (ksc·cm)": [f"{Ks:,.0f}", f"{Kec:,.0f}"],
            "DF (Distribution Factor)": [f"{DF_slab:.3f}", f"{DF_col:.3f}"],
            "Ratio (%)": [f"{DF_slab*100:.1f}%", f"{DF_col*100:.1f}%"]
        })
        
        st.table(df_results)
        
        st.info("""
        **Interpretation:**
        * **High $K_{ec}$**: The connection is stiff (Moment transfers to column).
        * **Low $K_{ec}$**: The connection is flexible (More moment stays in slab).
        * $K_t$ significantly reduces the effective stiffness of the column.
        """)

# Helper to run standalone for testing
if __name__ == "__main__":
    render_efm_tab()
