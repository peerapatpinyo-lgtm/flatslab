import streamlit as st
import numpy as np
import pandas as pd

# ตรวจสอบการ import visualization
try:
    from viz_torsion import plot_torsion_member
except ImportError:
    # Fallback กรณีไม่เจอไฟล์
    def plot_torsion_member(*args): return None

# --- Main Function: รับ Parameters ตรงกับที่ app.py ส่งมา ---
def render(c1_w, c2_w, L1, L2, lc, h_slab, fc, mat_props, w_u, col_type, **kwargs):
    """
    Render EFM Calculation Tab
    Parameters received from app.py:
    - c1_w: Column dimension parallel to L1 (cm)
    - c2_w: Column dimension transverse to L1 (cm)
    - L1: Span length (m)
    - L2: Transverse span (m)
    - lc: Column height (m)
    - h_slab: Slab thickness (cm)
    - fc: Concrete strength (ksc)
    - col_type: 'interior', 'edge', 'corner'
    """
    
    st.header("Equivalent Frame Method (EFM) Stiffness Analysis")
    st.markdown("---")

    # --- 1. Inputs Section (รับค่า / แก้ไขค่า) ---
    # เราจะใช้ค่าที่ส่งมาจาก app.py เป็นค่าเริ่มต้น (value)
    
    st.subheader("1. Design Parameters")
    
    col_in1, col_in2, col_in3 = st.columns(3)
    
    with col_in1:
        st.markdown("**Geometry (มิติ)**")
        # ใช้ค่า L1, L2, h_slab จาก app.py
        in_L1 = st.number_input("Span Length L1 (ทิศทางวิเคราะห์) [m]", value=float(L1), step=0.5)
        in_L2 = st.number_input("Transverse Span L2 (ความกว้างแถบ) [m]", value=float(L2), step=0.5)
        in_h_slab = st.number_input("Slab Thickness (h) [cm]", value=float(h_slab), step=1.0)
        
    with col_in2:
        st.markdown("**Column Dimensions (ขนาดเสา)**")
        # ใช้ค่า c1_w, c2_w, lc จาก app.py
        in_c1 = st.number_input("Column c1 (Dimension // L1) [cm]", value=float(c1_w), step=5.0)
        in_c2 = st.number_input("Column c2 (Dimension // L2) [cm]", value=float(c2_w), step=5.0)
        in_lc = st.number_input("Column Height (Lc) [m]", value=float(lc), step=0.1)

    with col_in3:
        st.markdown("**Material & Location**")
        in_fc = st.number_input("f'c (Concrete Strength) [ksc]", value=float(fc))
        
        # Mapping col_type (str) -> Selectbox Index
        type_options = ["Interior", "Edge", "Corner"]
        try:
            # แปลง input เช่น 'interior' -> index 0
            default_idx = type_options.index(col_type.capitalize())
        except ValueError:
            default_idx = 0
            
        in_col_loc = st.selectbox("Column Location", type_options, index=default_idx)

        # Calculate Ec
        Ec = 15100 * np.sqrt(in_fc)
        st.caption(f"**Modulus Elasticity ($E_c$):** {Ec:,.0f} ksc")

    st.markdown("---")

    # --- 2. Calculation Core (Logic) ---
    
    # Unit Conversion to cm
    L1_cm = in_L1 * 100
    L2_cm = in_L2 * 100
    Lc_cm = in_lc * 100
    
    # 2.1 Column Stiffness (Kc)
    # Inertia of Column
    Ic = (in_c2 * in_c1**3) / 12
    # Stiffness Kc (Assume Fixed-Fixed for simplicity factor = 4E, can be intricate in full EFM)
    # ACI 318 allows simplifying column stiffness for standard frames
    Kc = (4 * Ec * Ic) / Lc_cm
    
    # Sum Kc (Above + Below)
    # If Interior/Edge usually has columns above & below. Assume typical floor.
    Sum_Kc = 2 * Kc 

    # 2.2 Slab Stiffness (Ks)
    # Inertia of Slab (Full width L2)
    Is = (L2_cm * in_h_slab**3) / 12
    # Stiffness Ks (4EI/L)
    Ks = (4 * Ec * Is) / L1_cm

    # 2.3 Torsional Member Stiffness (Kt)
    # Section of torsional member (transverse strip)
    # x = shorter side, y = longer side of the rect section (c1 x h) or (c1 + small flange)
    # For slab system, usually implies section c1 x h
    dim1 = in_c1
    dim2 = in_h_slab
    x = min(dim1, dim2)
    y = max(dim1, dim2)
    
    # Torsional Constant C
    # Formula: C = sum( (1 - 0.63(x/y)) * (x^3 * y) / 3 )
    C_val = (1 - 0.63 * (x/y)) * (x**3 * y) / 3
    
    # Kt Formula (ACI 318)
    # Kt = sum ( 9 * Ec * C / (L2 * (1 - c2/L2)**3) )
    
    # Determine arms based on location
    loc_key = in_col_loc.lower() # interior, edge, corner
    if loc_key == "interior":
        num_arms = 2 # Left and Right torsional members
    elif loc_key == "edge":
        # If edge column is being analyzed for moment perp to edge -> 2 arms (torsion runs along edge)
        # If analyzed parallel to edge -> 1 arm? 
        # Usually standard EFM assumes frame analysis perpendicular to support line.
        # For an Edge column (support), the torsional member is the edge beam/slab.
        num_arms = 2 
    else: # Corner
        num_arms = 1

    term_geom = L2_cm * (1 - (in_c2/L2_cm))**3
    if term_geom <= 0: term_geom = 1 # Safety
    
    Kt_one_arm = (9 * Ec * C_val) / term_geom
    Kt = num_arms * Kt_one_arm

    # 2.4 Equivalent Column Stiffness (Kec)
    # Formula: 1/Kec = 1/Sum_Kc + 1/Kt
    if Kt == 0:
        Kec = 0
        df_col_pct = 0.0
    else:
        inv_Kec = (1 / Sum_Kc) + (1 / Kt)
        Kec = 1 / inv_Kec

    # 2.5 Distribution Factors (DF) at Joint
    Sum_K_joint = Ks + Kec
    if Sum_K_joint == 0:
        DF_slab = 0
        DF_col = 0
    else:
        DF_slab = Ks / Sum_K_joint
        DF_col = Kec / Sum_K_joint 

    # --- 3. Display Results (Layout) ---
    
    col_res_text, col_res_viz = st.columns([1, 1.2])

    with col_res_text:
        st.subheader("2. Detailed Calculations")
        
        # Step 1: Column
        with st.expander("Step 1: Column Stiffness ($K_c$)", expanded=True):
            st.latex(r"I_c = \frac{c_2 \cdot c_1^3}{12}")
            st.write(f"- $I_c$: {Ic:,.0f} cm⁴")
            st.write(f"- $K_c$ (4EI/L): {Kc:,.0f}")
            st.write(f"- $\sum K_c$ (Above+Below): **{Sum_Kc:,.0f}** ksc·cm")

        # Step 2: Slab
        with st.expander("Step 2: Slab Stiffness ($K_s$)", expanded=True):
            st.latex(r"I_s = \frac{L_2 \cdot h^3}{12}")
            st.write(f"- $I_s$: {Is:,.0f} cm⁴")
            st.write(f"- $K_s$ (4EI/L): **{Ks:,.0f}** ksc·cm")

        # Step 3: Torsional Member
        with st.expander("Step 3: Torsional Member ($K_t$)", expanded=True):
            st.markdown(f"Torsion Section ($x \\times y$): **{x:.0f} x {y:.0f} cm**")
            st.latex(r"C = \left(1 - 0.63 \frac{x}{y}\right) \frac{x^3 y}{3}")
            st.write(f"- Constant $C$: **{C_val:,.0f} cm⁴**")
            st.write(f"- Arms: {num_arms} side(s)")
            st.write(f"- $K_t$ (Total): **{Kt:,.0f}** ksc·cm")

        # Step 4: Equivalent Column
        with st.expander("Step 4: Equivalent Stiffness ($K_{ec}$)", expanded=True):
            st.latex(r"\frac{1}{K_{ec}} = \frac{1}{\sum K_c} + \frac{1}{K_t}")
            st.metric("Kec (Equivalent Column)", f"{Kec:,.0f}", "ksc·cm")

    with col_res_viz:
        st.subheader("3. Visualization & Results")
        
        # Call Visualization (using viz_torsion.py)
        try:
            fig = plot_torsion_member(loc_key, in_c1, in_c2, in_h_slab, in_L1, in_L2)
            if fig:
                st.pyplot(fig)
        except Exception as e:
            st.warning(f"Unable to render visualization: {e}")
        
        st.markdown("### Distribution Factors (DF)")
        
        # Summary Table
        df_results = pd.DataFrame({
            "Element": ["Slab ($K_s$)", "Equivalent Column ($K_{ec}$)"],
            "Stiffness (ksc·cm)": [f"{Ks:,.0f}", f"{Kec:,.0f}"],
            "DF Ratio": [f"{DF_slab:.3f}", f"{DF_col:.3f}"],
            "Percentage": [f"{DF_slab*100:.1f}%", f"{DF_col*100:.1f}%"]
        })
        
        st.table(df_results)
        
        # Interpretation
        if DF_col > 0.4:
            msg = "Strong Connection: Significant moment transfer to columns."
            style = "info"
        else:
            msg = "Flexible Connection: Most moment stays in the slab."
            style = "warning"
            
        st.markdown(f"""
        <div style='padding:10px; border-radius:5px; background-color:#f0f2f6; border-left:4px solid #555;'>
        <small><b>Interpretation:</b> {msg}<br>
        $K_t$ reduces the effective column stiffness. If $K_t$ is low (thin slab/small c1), $K_{{ec}}$ drops significantly.</small>
        </div>
        """, unsafe_allow_html=True)
