import streamlit as st
import pandas as pd
import formatter

def render_report(data):
    inp = data['inputs']
    res = data['results']
    rebar_list = data['rebar']
    
    # 1. Load Analysis & Geometry
    st.markdown("## 1. Load Analysis & Geometry")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Load Calculation:**")
        st.latex(formatter.fmt_qu_calc(
            inp['dl_fac'], inp['sw'], inp['sdl'], inp['ll_fac'], inp['ll'], res['qu']
        ))
        
    with col2:
        st.markdown("**Verification Trace ($b_o$):**")
        st.latex(formatter.fmt_geometry_trace(
            inp['c1_mm'], inp['c2_mm'], res['d_mm'], res['bo_mm'], inp['pos']
        ))

    # 2. Punching Shear
    st.markdown("## 2. Punching Shear Verification")
    
    # 2.1 Demand (Vu)
    st.markdown("#### 2.1 Shear Demand ($V_u$)")
    # เรียกใช้ fmt_vu_trace ที่สร้างใหม่ใน formatter.py
    st.latex(formatter.fmt_vu_trace(
        res['qu'], inp['lx'], inp['ly'], res['acrit'], res['gamma_v'], res['vu_kg']
    ))
    
    # 2.2 Capacity (Vc)
    st.markdown("#### 2.2 Shear Capacity ($\phi V_c$)")
    st.latex(formatter.fmt_shear_capacity_sub(
        inp['fc_mpa'], res['beta'], res['alpha'], res['d_mm'], res['bo_mm']
    ))
    
    # 2.3 Table
    df = pd.DataFrame({
        "Eq": ["Eq.1 (Basic)", "Eq.2 (Rect)", "Eq.3 (Aspect)"],
        "Stress (MPa)": [res['v1'], res['v2'], res['v3']],
        "Capacity (Ton)": [
            (0.75 * v * res['bo_mm'] * res['d_mm'] / 9806.65) for v in [res['v1'], res['v2'], res['v3']]
        ]
    })
    
    st.table(df.style.format({
        "Stress (MPa)": "{:.2f}",
        "Capacity (Ton)": "{:.2f}"
    }))
    
    # 2.4 Verdict
    pass_flag = res['ratio'] <= 1.0
    color = "green" if pass_flag else "red"
    verdict = "PASS" if pass_flag else "FAIL"
    st.markdown(f"### Ratio = {res['ratio']:.2f} $\\rightarrow$ :{color}[**{verdict}**]")

    # 3. Flexural Design
    st.markdown("## 3. Flexural Design (4 Strips)")
    st.latex(r"M_o = \frac{q_u \ell_2 \ell_n^2}{8} = \mathbf{" + f"{res['mo']:,.0f}" + r"} \; kg \cdot m")
    
    # Grid Layout for 4 Rebar Strips
    c1, c2 = st.columns(2)
    c3, c4 = st.columns(2)
    cols = [c1, c2, c3, c4]
    
    # Loop แสดงผล
    for i, item in enumerate(rebar_list):
        if i < 4: # ป้องกัน Index Error
            with cols[i]:
                st.latex(formatter.fmt_flexure_trace(
                    item['name'], 
                    item['coeff'], 
                    res['mo'], 
                    item['mu'], 
                    inp['fy'], 
                    res['d_mm']/10, 
                    item['as_req']
                ))
