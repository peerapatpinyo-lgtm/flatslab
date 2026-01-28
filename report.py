import streamlit as st
import pandas as pd
import formatter

def render_report(data):
    inp = data['inputs']
    res = data['results']
    
    st.markdown("## 1. Load Analysis")
    st.latex(formatter.fmt_qu_calc(inp['dl_fac'], inp['sw'], inp['sdl'], inp['ll_fac'], inp['ll'], res['qu']))
    
    st.markdown("## 2. Flexural Analysis (Moment)")
    st.latex(formatter.fmt_mo_calc(res['qu'], inp['ly'], inp['ln'], res['mo']))
    
    st.markdown("## 3. Punching Shear Check")
    # Table Comparison
    st.write(f"**Critical Perimeter ($b_o$):** {res['bo_mm']:.0f} mm | **Effective Depth ($d$):** {res['d_mm']:.0f} mm")
    
    st.markdown("#### 3.1 ACI Shear Capacity Formulas (Substitution)")
    st.latex(formatter.fmt_shear_capacity_sub(inp['fc_mpa'], res['beta'], res['alpha_s'], res['d_mm'], res['bo_mm']))
    
    # Comparison Table
    df = pd.DataFrame({
        "Formula": ["Eq 1 (Basic)", "Eq 2 (Geometry)", "Eq 3 (Perimeter)"],
        "Stress Capacity (MPa)": [res['v1'], res['v2'], res['v3']],
        "Phi Vc (Tons)": [
            (0.75 * res['v1'] * res['bo_mm'] * res['d_mm'] / 9806.65),
            (0.75 * res['v2'] * res['bo_mm'] * res['d_mm'] / 9806.65),
            (0.75 * res['v3'] * res['bo_mm'] * res['d_mm'] / 9806.65)
        ]
    })
    st.table(df.style.format("{:.2f}"))
    
    col1, col2 = st.columns(2)
    col1.metric("Vu (Demand)", f"{res['vu_kg']/1000:.2f} Tons")
    col2.metric("Phi Vc (Capacity)", f"{res['phi_vc_kg']/1000:.2f} Tons", delta=f"Ratio {res['ratio']:.2f}", delta_color="inverse")

    st.markdown("## 4. Reinforcement (Sample)")
    st.markdown("**Column Strip Negative Moment:**")
    st.latex(formatter.fmt_as_req(res['mu_cs_neg'], res['d_mm']/10, inp['fy'], res['as_cs_neg']))
