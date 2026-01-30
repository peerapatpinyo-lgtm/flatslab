# tab_efm.py
import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from calculations import calculate_stiffness

def render(c1_w, c2_w, L1, L2, lc, h_slab, fc):
    st.header("3. Equivalent Frame Method (EFM) Stiffness")
    st.markdown("""
    ในวิธี EFM โครงสร้างจะถูกแปลงเป็น **Equivalent Frame** โดยจุดต่อระหว่างพื้นและเสา 
    จะถูกพิจารณาผ่าน **Equivalent Column ($K_{ec}$)** ซึ่งรวมผลของเสาจริง ($K_c$) และ Torsional Member ($K_t$)
    """)

    # 1. Calculate
    # Note: calculate_stiffness returns (Ks, Sum_Kc, Kt, Kec)
    Ks, Kc_total, Kt, Kec = calculate_stiffness(c1_w, c2_w, L1, L2, lc, h_slab, fc)

    # 2. Layout
    col_main1, col_main2 = st.columns([1, 1.5])

    # --- LEFT COLUMN: Numerical Results ---
    with col_main1:
        st.subheader("🔢 Stiffness Values")
        
        # Display Slab Stiffness
        st.markdown("**1. Slab Stiffness ($K_s$)**")
        st.latex(r"K_s = \frac{4E I_{slab}}{L_1}")
        st.metric("Ks (Slab)", f"{Ks:,.2e} kg-cm", delta_color="normal")
        
        st.markdown("---")

        # Display Column Stiffness
        st.markdown("**2. Column Stiffness ($\Sigma K_c$)**")
        st.caption("รวมความแข็งเสาบนและเสาล่าง (Assuming Fixed Far Ends)")
        st.latex(r"\Sigma K_c = 2 \times \frac{4E I_{col}}{l_c}")
        st.metric("Kc (Total Columns)", f"{Kc_total:,.2e} kg-cm")
        
        st.markdown("---")
        
        # Display Torsional Stiffness
        st.markdown("**3. Torsional Member ($K_t$)**")
        st.caption("ความแข็งของการบิดตัวด้านข้างเสา (Torsional Arm)")
        st.metric("Kt (Torsion)", f"{Kt:,.2e} kg-cm", help="ถ้าค่านี้น้อย แสดงว่าจุดต่อถ่ายโมเมนต์เข้าเสาได้น้อย")

        st.markdown("---")

        # Display Equivalent Column
        st.markdown("**4. Equivalent Column ($K_{ec}$)**")
        st.latex(r"\frac{1}{K_{ec}} = \frac{1}{\Sigma K_c} + \frac{1}{K_t}")
        st.info(f"K_ec = {Kec:,.2e} kg-cm")

    # --- RIGHT COLUMN: Visualization ---
    with col_main2:
        st.subheader("📊 Stiffness Comparison")
        
        # A. Distribution Factors
        if (Ks + Kec) > 0:
            df_slab = Ks / (Ks + Kec)
            df_col = Kec / (Ks + Kec) # Moment distributed to the Equivalent Column
        else:
            df_slab, df_col = 0, 0
            
        st.write("#### Distribution Factors (DF)")
        st.markdown("สัดส่วนการกระจายโมเมนต์ที่จุดต่อ (Joint):")
        
        col_df1, col_df2 = st.columns(2)
        col_df1.metric("DF Slab ->", f"{df_slab:.3f}", f"{df_slab*100:.1f}%")
        col_df2.metric("DF Column (Equiv) ->", f"{df_col:.3f}", f"{df_col*100:.1f}%")
        
        st.progress(df_slab)
        st.caption(f"Moment จะถูกดึงไปที่พื้น {df_slab*100:.0f}% และลงเสา {df_col*100:.0f}%")

        # B. Bar Chart Comparison
        st.write("#### Stiffness Breakdown")
        
        fig, ax = plt.subplots(figsize=(6, 4))
        
        # Data
        labels = ['K_slab', 'Sum K_col', 'K_torsion', 'K_equiv (Kec)']
        values = [Ks, Kc_total, Kt, Kec]
        colors = ['#3498db', '#95a5a6', '#f1c40f', '#e74c3c']
        
        # Plot
        bars = ax.bar(labels, values, color=colors, edgecolor='black', alpha=0.8)
        
        # Value Labels on top
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1e}',
                    ha='center', va='bottom', fontsize=9)
            
        ax.set_ylabel('Stiffness (kg-cm)')
        ax.set_title('Stiffness Comparison')
        ax.grid(axis='y', linestyle='--', alpha=0.5)
        
        st.pyplot(fig)
        
        st.warning("""
        **Note:** - ถ้า **Kt** (สีเหลือง) ต่ำมากๆ มันจะฉุดให้ **Kec** (สีแดง) ต่ำตามไปด้วย (แม้ว่าเสาจริงจะใหญ่ก็ตาม)
        - นี่คือเหตุผลที่ EFM มักให้ผลโมเมนต์ลบที่หัวเสาน้อยกว่าวิธีอื่น เพราะคิดผลของการบิดตัว (Torsion)
        """)
