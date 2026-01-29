import streamlit as st
from calculations import calculate_stiffness

def render(c1_w, c2_w, L1, L2, lc, h_slab, fc):
    st.header("3. Equivalent Frame Method (EFM)")
    Ks, Kc, Kt, Kec = calculate_stiffness(c1_w, c2_w, L1, L2, lc, h_slab, fc)
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🧮 Stiffness Parameters")
        st.latex(r"K_{slab} = " + f"{Ks:,.0f}" + r" \quad \text{kg-cm}")
        st.latex(r"K_{col} = " + f"{Kc:,.0f}" + r" \quad \text{kg-cm}")
        st.latex(r"K_{ec} = " + f"{Kec:,.0f}" + r" \quad \text{kg-cm}")
    with c2:
        st.subheader("📊 Distribution Factors (DF)")
        if (Ks + Kec) > 0:
            df_slab = Ks / (Ks + Kec)
            df_col = Kec / (Ks + Kec)
        else:
            df_slab, df_col = 0, 0
        st.metric("DF Slab", f"{df_slab:.3f}")
        st.metric("DF Col", f"{df_col:.3f}")
        st.progress(df_slab)
