import streamlit as st
import pandas as pd
import formatter

def render_report(data):
    inp = data['inputs']
    res = data['results']
    
    st.markdown("## 1. Load Analysis & Geometry")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Load Calculation:**")
        st.latex(formatter.fmt_qu_calc(inp['dl_fac'], inp['sw'], inp['sdl'], inp['ll_fac'], inp['ll'], res['qu']))
    with col2:
        st.markdown("**Verification Trace ($b_o$):**")
        st.latex(formatter.fmt_geometry_trace(inp['c1_mm'], inp['c2_mm'], res['d_mm'], res['bo_mm'], inp['pos']))

    st.markdown("## 2. Punching Shear Verification")
    
    # Detailed Vu Trace
    area_tot = inp['lx'] * inp['ly']
    acrit = res['acrit']
    gamma = res['gamma_v']
    st.markdown("**Shear Demand ($V_u$):**")
    st.latex(r"""
    V_u = q_u(L_x L_y - A_{crit})\gamma_v = """ + f"{res['qu']:.0f}({area_tot:.2f} - {acrit:.4f})({gamma}) = \mathbf{""" + f"{res['vu_kg']:.0f}" + r"""} \; kg
    """)
    
    # Capacity Table
    st.markdown("**Shear Capacity ($\phi V_c$):**")
    st.latex(formatter.fmt_shear_capacity_sub(inp['fc_mpa'], res['beta'], res['alpha'], res['d_mm'], res['bo_mm']))
    
    df = pd.DataFrame({
        "Eq": ["Eq.1", "Eq.2", "Eq.3"],
        "Stress (MPa)": [res['v1'], res['v2'], res['v3']],
        "Capacity (Ton)": [
            (0.75 * v * res['bo_mm'] * res['d_mm'] / 9806.65) for v in [res['v1'], res['v2'], res['v3']]
        ]
    })
    
    # Significant Figures Formatting
    st.table(df.style.format({
        "Stress (MPa)": "{:.2f}",
        "Capacity (Ton)": "{:.2f}"
    }))
    
    # Final Verdict
    pass_flag = res['ratio'] <= 1.0
    color = "green" if pass_flag else "red"
    verdict = "PASS" if pass_flag else "FAIL"
    st.markdown(f"#### Ratio = {res['ratio']:.2f} : :{color}[{verdict}]")

    st.markdown("## 3. Flexural Design (4 Strips)")
    st.latex(r"M_o = \frac{q_u \ell_2 \ell_n^2}{8} = \mathbf{" + f"{res['mo']:,.2f}" + r"} \; kg \cdot m")
    
    # 2x2 Grid for Strips
    r1c1, r1c2 = st.columns(2)
    r2c1, r2c2 = st.columns(2)
    cols = [r1c1, r1c2, r2c1, r2c2]
    
    for i, item in enumerate(data['rebar']):
        with cols[i]:
            st.latex(formatter.fmt_flexure_trace(
                item['name'], item['coeff'], res['mo'], item['mu'], inp['fy'], res['d_mm']/10, item['as_req']
            ))
