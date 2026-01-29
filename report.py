import streamlit as st
import formatter

def render_report(base_data, verify_data):
    i = base_data['inputs']
    r = base_data['results']
    bars = verify_data['rebar_verified']
    as_min = verify_data['as_min']
    
    st.markdown("## 🏗️ Interactive Design Report")
    
    # 1. Structure
    st.markdown("### 1. Structural Analysis")
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"Final Thickness $h$: **{r['h']} mm**")
        st.latex(fr"d \approx {r['d_mm']:.0f} \; mm")
    with col2:
        pass_flag = r['ratio'] <= 1.0
        color = "green" if pass_flag else "red"
        st.markdown(f"**Shear Status:** :{color}[{'SAFE' if pass_flag else 'FAIL'}]")
        st.markdown(f"Ratio: {r['ratio']:.2f}")

    # Loads
    st.latex(formatter.fmt_load_trace(i['dl_fac'], i['sw'], i['sdl'], i['ll_fac'], i['ll'], r['qu']))
    
    # 2. Punching Shear
    st.markdown("### 2. Punching Shear Check")
    st.latex(formatter.fmt_vu_detailed(r['qu'], i['lx'], i['ly'], r['acrit'], r['gamma_v'], r['vu_kg']))
    st.latex(formatter.fmt_vc_conversion_detailed(0.75, r['vc_mpa'], r['bo_mm'], r['d_mm'], r['phi_vc_kg']/1000.0))
    
    # 3. Flexural Verification
    st.markdown("### 3. Flexural Reinforcement Verification")
    st.caption("Verifying User Selected Bars vs Requirements")
    
    st.markdown("**3.1 Minimum Reinforcement ($A_{s,min}$)**")
    st.latex(fr"A_{{s,min}} = 0.0018 \times 100 \times {r['h']/10:.1f} = \mathbf{{{as_min:.2f}}} \; cm^2/m")
    
    st.markdown("**3.2 Strip Verification**")
    st.latex(fr"M_o = \mathbf{{{r['mo']:,.0f}}} \; kg \cdot m")
    
    c1, c2 = st.columns(2)
    c3, c4 = st.columns(2)
    cols = [c1, c2, c3, c4]
    
    for idx, bar in enumerate(bars):
        if idx < 4:
            with cols[idx]:
                st.latex(formatter.fmt_rebar_verification(
                    bar['name'], bar['coeff'], r['mo'], bar['mu'],
                    i['fy'], r['d_mm']/10.0,
                    bar['as_req_calc'], bar['as_min'], bar['as_target'],
                    bar['user_db'], bar['user_spacing'], bar['bar_area'],
                    bar['as_provided'], bar['status'], bar['color']
                ))
