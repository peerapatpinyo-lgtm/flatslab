import streamlit as st

def render(L1, L2, c1_w, c2_w, h_slab, lc, cover, d_eff, moment_vals):
    st.markdown("## 🏗️ Construction Drawings")
    st.info("ℹ️ Module นี้กำลังอยู่ระหว่างการพัฒนา (Drawing Module is under construction)")
    
    st.markdown("""
    ### Features to come:
    - Auto-generated DXF export
    - Detailed Rebar Schedule
    - Section cuts automation
    """)
    
    # แสดงค่าที่รับมา เพื่อ Debug ว่าส่งค่ามาถูกไหม
    with st.expander("Debug: Received Parameters"):
        st.write({
            "Lx": L1, "Ly": L2, 
            "h_slab": h_slab, 
            "Moment Data": moment_vals
        })
