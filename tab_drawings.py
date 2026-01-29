import streamlit as st
from geometry_view import plot_combined_view

def render(L1, L2, c1_w, c2_w, h_slab, lc, cover, d_eff, moment_vals):
    st.header("1. Engineering Drawings & Details")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.pyplot(plot_combined_view(L1, L2, c1_w, c2_w, h_slab, lc, moment_vals))
        
    with col2:
        st.markdown("### 📋 Design Summary")
        st.info(f"""
        **Geometry:**
        - Design Span (L1): {L1} m
        - Width (L2): {L2} m
        - Thickness: {h_slab} cm
        
        **Section:**
        - Col (Parallel): {c1_w} cm
        - Col (Perp): {c2_w} cm
        - d_eff: {d_eff:.2f} cm
        """)
