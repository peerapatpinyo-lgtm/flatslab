import streamlit as st
import pandas as pd
import formatter

def render_report(data):
    inp = data['inputs']
    res = data['results']
    rebar_list = data['rebar']
    
    # --- Section 0: Traceability Header ---
    st.markdown("## 1. Design Criteria & Geometry")
    
    st.info(f"""
    **Thickness Traceability:**
    * Input Thickness: **{inp['h_init']} mm**
    * Final Design Thickness: **{res['h']} mm**
    * **Governing Condition:** {res['reason']}
    """)
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**1.1 Minimum Thickness Check (ACI 318):**")
        st.latex(formatter.fmt_h_min_check(res['ln'], inp['pos'], res['h_min_code'], res['h']))
        
    with c2:
        st.markdown("**1.2 Effective Depth & Perimeter:**")
        st.latex(formatter.fmt_geometry_trace(inp['c1_mm'], inp['c2_mm'], res['d_mm'], res['bo_mm'], inp['pos']))

    # --- Section 2: Load ---
    st.markdown("## 2. Load Analysis (Using Final Thickness)")
    st.latex(formatter.fmt_qu_calc(
        inp['dl_fac'], inp['sw'], inp['sdl'], inp['ll_fac'], inp['ll'], res['qu'], res['h']
    ))
    
    # --- Section 3: Punching Shear ---
    st.markdown("## 3. Punching Shear Verification")
    
    st.markdown("**3.1 Shear Demand ($V_u$):**")
    st.latex(formatter.fmt_vu_trace(
        res['qu'], inp['lx'], inp['ly'], res['acrit'], res['gamma_v'], res['vu_kg']
    ))
    
    st.markdown("**3.2 Shear Capacity ($\phi V_c$):**")
    st.latex(formatter.fmt_shear_capacity_sub(
        inp['fc_mpa'], res['beta'], res['alpha'], res['d_mm'], res['bo_mm']
    ))
    
    # Compare Table
    df = pd.DataFrame({
        "Eq": ["Eq.1", "Eq.2", "Eq.3"],
        "Stress (MPa)": [res['v1'], res['v2'], res['v3']],
        "Capacity (Ton)": [
            (0.75 * v * res['bo_mm'] * res['d_mm'] / 9806.65) for v in [res['v1'], res['v2'], res['v3']]
        ]
    })
    
    # --- จุดที่แก้ไข: ระบุ Dict เพื่อ Format เฉพาะคอลัมน์ตัวเลข ---
    st.table(df.style.format({
        "Stress (MPa)": "{:.2f}",
        "Capacity (Ton)": "{:.2f}"
    }))
    
    # Verdict
    pass_flag = res['ratio'] <= 1.0
    color = "green" if pass_flag else "red"
    st.markdown(f"#### Ratio = {res['ratio']:.2f} (Status: :{color}[{'PASS' if pass_flag else 'FAIL'}])")

    # --- Section 4: Flexure ---
    st.markdown("## 4. Flexural Design")
    st.latex(r"M_o = \frac{q_u \ell_n^2}{8} = \mathbf{" + f"{res['mo']:,.0f}" + r"} \; kg \cdot m")
    
    c1, c2 = st.columns(2)
    c3, c4 = st.columns(2)
    cols = [c1, c2, c3, c4]
    
    for i, item in enumerate(rebar_list):
        if i < 4:
            with cols[i]:
                st.latex(formatter.fmt_flexure_trace(
                    item['name'], item['coeff'], res['mo'], item['mu'], inp['fy'], res['d_mm']/10, item['as_req']
                ))
