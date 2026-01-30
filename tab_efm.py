import streamlit as st
import numpy as np
import pandas as pd

# ตรวจสอบการ import visualization
try:
    from viz_torsion import plot_torsion_member
except ImportError:
    def plot_torsion_member(*args): return None

# --- Main Function ---
def render(c1_w, c2_w, L1, L2, lc, h_slab, fc, mat_props, w_u, col_type, **kwargs):
    """
    Render EFM Calculation Tab (Clean Version)
    รับค่าจาก App หลักมาคำนวณและแสดงผลทันที ไม่ต้องกรอกซ้ำ
    """
    
    st.header("Equivalent Frame Method (EFM) Stiffness Analysis")
    st.markdown("---")

    # --- 1. Parameter Summary (แสดงค่าที่รับมา แทนการให้กรอกใหม่) ---
    st.subheader("1. Design Parameters (From Project Settings)")
    
    # ใช้ st.metric หรือ st.write เพื่อโชว์ค่าเฉยๆ (Read-only)
    col_info1, col_info2, col_info3 = st.columns(3)
    
    with col_info1:
        st.markdown("**🏗️ Geometry**")
        st.write(f"- Span ($L_1$): **{L1} m**")
        st.write(f"- Transverse ($L_2$): **{L2} m**")
        st.write(f"- Thickness ($h$): **{h_slab} cm**")

    with col_info2:
        st.markdown("**🏛️ Column Prop**")
        st.write(f"- Size ($c_1 \\times c_2$): **{c1_w:.0f} x {c2_w:.0f} cm**")
        st.write(f"- Height ($L_c$): **{lc} m**")
        st.write(f"- Location: **{col_type.capitalize()}**")

    with col_info3:
        st.markdown("**🧱 Material**")
        Ec = 15100 * np.sqrt(fc) # คำนวณ Ec ตรงนี้เลย
        st.write(f"- $f'_c$: **{fc} ksc**")
        st.write(f"- $E_c$: **{Ec:,.0f} ksc**")

    st.markdown("---")

    # --- 2. Calculation Core (Logic) ---
    # ใช้ตัวแปรที่รับมา (Argument) คำนวณโดยตรง ไม่ต้องผ่าน st.number_input
    
    # Unit Conversion to cm
    L1_cm = L1 * 100
    L2_cm = L2 * 100
    Lc_cm = lc * 100
    
    # 2.1 Column Stiffness (Kc)
    Ic = (c2_w * c1_w**3) / 12
    Kc = (4 * Ec * Ic) / Lc_cm
    Sum_Kc = 2 * Kc # Assume column above & below

    # 2.2 Slab Stiffness (Ks)
    Is = (L2_cm * h_slab**3) / 12
    Ks = (4 * Ec * Is) / L1_cm

    # 2.3 Torsional Member Stiffness (Kt)
    dim1 = c1_w
    dim2 = h_slab
    x = min(dim1, dim2)
    y = max(dim1, dim2)
    
    # Torsional Constant C
    C_val = (1 - 0.63 * (x/y)) * (x**3 * y) / 3
    
    # Determine arms based on location
    loc_key = col_type.lower()
    if loc_key == "interior":
        num_arms = 2 
    elif loc_key == "edge":
        num_arms = 2 
    else: # Corner
        num_arms = 1

    term_geom = L2_cm * (1 - (c2_w/L2_cm))**3
    if term_geom <= 0: term_geom = 1
    
    Kt_one_arm = (9 * Ec * C_val) / term_geom
    Kt = num_arms * Kt_one_arm

    # 2.4 Equivalent Column Stiffness (Kec)
    if Kt == 0:
        Kec = 0
    else:
        inv_Kec = (1 / Sum_Kc) + (1 / Kt)
        Kec = 1 / inv_Kec

    # 2.5 Distribution Factors (DF)
    Sum_K_joint = Ks + Kec
    if Sum_K_joint == 0:
        DF_slab, DF_col = 0, 0
    else:
        DF_slab = Ks / Sum_K_joint
        DF_col = Kec / Sum_K_joint 

    # --- 3. Display Results (Layout) ---
    
    col_res_text, col_res_viz = st.columns([1, 1.2])

    with col_res_text:
        st.subheader("2. Detailed Stiffness Calculations")
        
        # แสดงผลลัพธ์แบบ Group
        with st.container():
            st.markdown("#### Step 1: Component Stiffness")
            st.markdown(f"""
            * **Column ($K_c$):** {Kc:,.0f} $\\rightarrow$ $\sum K_c = $ **{Sum_Kc:,.0f}**
            * **Slab ($K_s$):** **{Ks:,.0f}**
            * **Torsional ($K_t$):** **{Kt:,.0f}** ($C = {C_val:,.0f}$ cm$^4$)
            """)
        
        st.markdown("---")
        
        st.markdown("#### Step 2: Equivalent Stiffness ($K_{ec}$)")
        st.latex(r"\frac{1}{K_{ec}} = \frac{1}{\sum K_c} + \frac{1}{K_t}")
        
        # ไฮไลท์ผลลัพธ์สำคัญ
        st.success(f"### $K_{{ec}}$ = {Kec:,.0f} ksc·cm")

    with col_res_viz:
        st.subheader("3. Visualization & Distribution")
        
        # Call Visualization
        try:
            fig = plot_torsion_member(loc_key, c1_w, c2_w, h_slab, L1, L2)
            if fig: st.pyplot(fig)
        except Exception: pass
        
        # Summary Table
        st.markdown("### Distribution Factors (DF)")
        df_results = pd.DataFrame({
            "Element": ["Slab ($K_s$)", "Equivalent Column ($K_{ec}$)"],
            "Stiffness": [f"{Ks:,.0f}", f"{Kec:,.0f}"],
            "Distribution Factor": [f"{DF_slab:.3f}", f"{DF_col:.3f}"],
            "% Taken": [f"{DF_slab*100:.1f}%", f"{DF_col*100:.1f}%"]
        })
        st.table(df_results)

        # Quick Interpretation
        st.info(f"**สรุป:** โมเมนต์จะถ่ายเข้าสู่เสาประมาณ **{DF_col*100:.1f}%** (ผ่าน Stiffness ของจุดต่อ $K_{{ec}}$)")
