import streamlit as st
import formatter

def render_report(data):
    i = data['inputs']
    r = data['results']
    bars = data['rebar']
    
    st.markdown("## 🏗️ Detailed Construction Calculation")
    
    # 1. Geometry & Load
    st.markdown("### 1. Design Parameters")
    st.info(f"Final Thickness: **{r['h']} mm** | Effective Depth d: **{r['d_mm']:.1f} mm**")
    st.latex(formatter.fmt_load_trace(i['dl_fac'], i['sw'], i['sdl'], i['ll_fac'], i['ll'], r['qu']))
    
    # 2. Shear
    st.markdown("### 2. Punching Shear Check")
    st.latex(formatter.fmt_vu_detailed(r['qu'], i['lx'], i['ly'], r['acrit'], r['gamma_v'], r['vu_kg']))
    st.latex(formatter.fmt_vc_conversion_detailed(0.75, r['vc_mpa'], r['bo_mm'], r['d_mm'], r['phi_vc_kg']/1000.0))
    
    pass_flag = r['ratio'] <= 1.0
    st.markdown(f"**Ratio:** {r['ratio']:.2f} ({'SAFE' if pass_flag else 'FAIL'})")
    
    # 3. Flexural Design
    st.markdown("### 3. Flexural Design & Detailing")
    
    # 3.1 As Min Check
    st.markdown("**3.1 Minimum Reinforcement ($A_{s,min}$)**")
    st.latex(formatter.fmt_as_min_calc(100, r['h']/10.0, r['as_min']))
    st.caption("Standard: ACI 318 Temperature & Shrinkage Reinforcement")
    
    # 3.2 Strips Calculation
    st.markdown("**3.2 Strip Design (Moment $\\rightarrow$ Spacing)**")
    st.latex(fr"M_o = \mathbf{{{r['mo']:,.0f}}} \; kg \cdot m \quad (\text{{Static Moment}})")
    
    c1, c2 = st.columns(2)
    c3, c4 = st.columns(2)
    cols = [c1, c2, c3, c4]
    
    for idx, bar in enumerate(bars):
        if idx < 4:
            with cols[idx]:
                st.latex(formatter.fmt_flexure_design(
                    bar['name'], bar['coeff'], r['mo'], bar['mu'], 
                    i['fy'], r['d_mm']/10.0, 
                    bar['as_req'], r['as_min'], bar['as_design'],
                    i['bar_area'], bar['theo_spacing'], bar['use_spacing'],
                    int(i['main_bar_db'])
                ))
