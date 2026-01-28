import streamlit as st
import formatter

def render_report(data):
    i = data['inputs']
    r = data['results']
    bars = data['rebar']
    
    st.markdown("## 🏗️ Detailed Calculation Report")
    
    # --- Check Traceability (Start vs Final h) ---
    st.markdown("### 1. Thickness Verification ($h$)")
    if i['h_init'] != r['h']:
        st.warning(f"⚠️ **Thickness Increased:** Start {i['h_init']} mm $\\rightarrow$ Final {r['h']} mm")
        st.caption(f"Reason: **{r['reason']}** (Calculated loop adjusted thickness automatically)")
    else:
        st.success(f"✅ **Thickness OK:** Designed at {r['h']} mm matches input.")

    st.latex(fr"d = h - cov - d_b/2 = {r['d_mm']:.0f} \; mm")
    
    # --- Step 2: Loads ---
    st.markdown("### 2. Load Analysis ($q_u$)")
    st.latex(formatter.fmt_load_trace(
        i['dl_fac'], i['sw'], i['sdl'], i['ll_fac'], i['ll'], r['qu']
    ))
    
    # --- Step 3: Punching Shear ---
    st.markdown("### 3. Punching Shear Analysis")
    
    st.markdown("**3.1 Critical Section Geometry ($A_{crit}$)**")
    st.latex(formatter.fmt_acrit_detailed(
        i['c1'], i['c2'], r['d_mm']/1000.0, r['acrit'], i['pos']
    ))
    
    st.markdown("**3.2 Shear Demand ($V_u$)**")
    st.latex(formatter.fmt_vu_detailed(
        r['qu'], i['lx'], i['ly'], r['acrit'], r['gamma_v'], r['vu_kg']
    ))
    
    st.markdown("**3.3 Shear Capacity ($\phi V_c$)**")
    st.markdown("First, determine governing stress ($v_c$):")
    st.latex(fr"v_c = \min({r['v1']:.2f}, {r['v2']:.2f}, {r['v3']:.2f}) = \mathbf{{{r['vc_mpa']:.2f}}} \; MPa")
    
    st.markdown("Then, convert stress to force (Tons):")
    st.latex(formatter.fmt_vc_conversion_detailed(
        0.75, r['vc_mpa'], r['bo_mm'], r['d_mm'], r['phi_vc_kg']/1000.0
    ))
    
    # Ratio Verdict
    pass_flag = r['ratio'] <= 1.0
    status_color = "green" if pass_flag else "red"
    st.markdown(f"#### Ratio = $V_u / \phi V_c$ = {r['ratio']:.2f} (:{status_color}[{'SAFE' if pass_flag else 'FAIL'}])")

    # --- Step 4: Flexure ---
    st.markdown("### 4. Flexural Design ($A_s$)")
    st.latex(fr"M_o = \frac{{q_u \ell_n^2}}{{8}} = \frac{{{r['qu']:.0f} \times {r['ln']:.2f}^2}}{{8}} = \mathbf{{{r['mo']:,.0f}}} \; kg \cdot m")
    
    c1, c2 = st.columns(2)
    c3, c4 = st.columns(2)
    cols = [c1, c2, c3, c4]
    
    for idx, bar in enumerate(bars):
        if idx < 4:
            with cols[idx]:
                st.latex(formatter.fmt_flexure_detailed(
                    bar['name'], bar['coeff'], r['mo'], bar['mu'], 
                    i['fy'], r['d_mm']/10.0, bar['denom_val'], bar['as_req']
                ))
