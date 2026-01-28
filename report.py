import streamlit as st
import formatter

def render_report(data):
    i = data['inputs']
    r = data['results']
    bars = data['rebar']
    
    st.markdown("## Detailed Calculation Report")
    
    # --- 1. Consistency Check ---
    st.markdown("### 1. Geometry & Thickness Check")
    st.info(f"Traceability: $h_{{init}} = {i['h_init']}$ mm $\\to$ $h_{{final}} = {r['h']}$ mm")
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Thickness Verification:**")
        st.latex(formatter.fmt_min_thickness(r['ln'], i['h_denom'], r['h_min'], r['h']))
    with c2:
        st.markdown("**Critical Section Properties:**")
        st.latex(fr"d = {r['d_mm']:.0f} \; mm, \quad b_o = {r['bo_mm']:.0f} \; mm")
        st.latex(fr"A_{{crit}} = {r['acrit']:.4f} \; m^2")

    # --- 2. Punching Shear ---
    st.markdown("### 2. Punching Shear (Substitution)")
    
    st.markdown("**Step 2.1: Shear Demand ($V_u$)**")
    # ใช้ r['qu'] ซึ่งตอนนี้มีอยู่ใน engine แล้ว
    st.latex(formatter.fmt_shear_demand(
        r['qu'], i['lx'], i['ly'], r['acrit'], r['gamma_v'], r['vu_kg']
    ))
    
    st.markdown("**Step 2.2: Shear Capacity ($\phi V_c$)**")
    st.caption(f"Governing Stress ($v_{{min}}$) derived from min({r['v1']:.2f}, {r['v2']:.2f}, {r['v3']:.2f}) = **{r['vc_mpa']:.2f} MPa**")
    st.latex(formatter.fmt_shear_capacity(
        0.75, r['vc_mpa'], r['bo_mm'], r['d_mm'], r['phi_vc_kg']/1000.0
    ))
    
    # Ratio
    pass_flag = r['ratio'] <= 1.0
    color = "green" if pass_flag else "red"
    st.markdown(f"#### Ratio = {r['vu_kg']:,.0f} / {r['phi_vc_kg']:,.0f} = {r['ratio']:.2f} (:{color}[{'SAFE' if pass_flag else 'FAIL'}])")

    # --- 3. Flexure ---
    st.markdown("### 3. Flexural Design (Substitution)")
    st.latex(fr"M_o = \frac{{q_u \ell_n^2}}{{8}} = \frac{{{r['qu']:.0f} \times {r['ln']:.2f}^2}}{{8}} = \mathbf{{{r['mo']:,.0f}}} \; kg \cdot m")
    
    col_a, col_b = st.columns(2)
    col_c, col_d = st.columns(2)
    cols = [col_a, col_b, col_c, col_d]
    
    for idx, bar in enumerate(bars):
        if idx < 4:
            with cols[idx]:
                st.latex(formatter.fmt_flexure_strip(
                    bar['name'], bar['coeff'], r['mo'], bar['mu'], 
                    i['fy'], r['d_mm']/10.0, bar['as_req']
                ))
