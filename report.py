import streamlit as st
import pandas as pd
import formatter

def render_report(data):
    inp = data['inputs']
    res = data['results']
    rebar_list = data['rebar']
    
    # --- Header ---
    st.markdown("## 1. Design Criteria")
    st.info(f"""
    **Thickness Traceability:**
    * Input Thickness: **{inp['h_init']} mm**
    * Final Design Thickness: **{res['h']} mm**
    * **Governing Condition:** {res['reason']}
    """)
    st.markdown("**Minimum Thickness Check (ACI 318):**")
    st.latex(formatter.fmt_h_min_check(res['ln'], inp['pos'], res['h_min_code'], res['h']))

    # --- Load ---
    st.markdown("## 2. Load Analysis")
    st.latex(formatter.fmt_qu_calc(
        inp['dl_fac'], inp['sw'], inp['sdl'], inp['ll_fac'], inp['ll'], res['qu'], res['h']
    ))
    
    # --- Shear Verification ---
    st.markdown("## 3. Punching Shear Verification")
    
    # 3.1 Geometric Properties
    st.markdown("#### 3.1 Geometric Properties (Critical Section)")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Effective Depth ($d$) & Perimeter ($b_o$):**")
        st.latex(formatter.fmt_geometry_trace(inp['c1_mm'], inp['c2_mm'], res['d_mm'], res['bo_mm'], inp['pos']))
    with c2:
        st.markdown("**Critical Area ($A_{crit}$):**")
        st.latex(formatter.fmt_acrit_calc(inp['c1_mm'], inp['c2_mm'], res['d_mm'], inp['pos'], res['acrit']))
    
    # 3.2 Demand
    st.markdown("#### 3.2 Shear Demand ($V_u$)")
    st.latex(formatter.fmt_vu_trace(
        res['qu'], inp['lx'], inp['ly'], res['acrit'], res['gamma_v'], res['vu_kg']
    ))
    
    # 3.3 Capacity (Stress)
    st.markdown("#### 3.3 Shear Capacity Stresses ($v_c$)")
    st.latex(formatter.fmt_shear_capacity_sub(
        inp['fc_mpa'], res['beta'], res['alpha'], res['d_mm'], res['bo_mm'],
        res['v1'], res['v2'], res['v3']
    ))
    
    # 3.4 Unit Bridge (Force Conversion)
    st.markdown("#### 3.4 Force Conversion (Unit Bridge)")
    st.latex(formatter.fmt_force_conversion(
        res['vc_gov_mpa'], res['bo_mm'], res['d_mm'], res['vc_newton'], res['phi_vc_kg']
    ))

    # Verdict
    pass_flag = res['ratio'] <= 1.0
    color = "green" if pass_flag else "red"
    st.markdown(f"### Final Ratio = {res['ratio']:.2f} (Status: :{color}[{'PASS' if pass_flag else 'FAIL'}])")

    # --- Flexure ---
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
