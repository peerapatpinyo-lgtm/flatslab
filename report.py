import streamlit as st
import formatter
import pandas as pd

def render_report(base_data, verify_data):
    i = base_data['inputs']
    r = base_data['results']
    bars = verify_data['rebar_verified']
    as_min = verify_data['as_min']
    
    st.markdown("## 🏗️ Professional Design Calculation")
    
    # 0. Philosophy
    st.latex(formatter.fmt_design_philosophy())
    st.divider()

    # 1. Geometry
    st.markdown("### 1. Structural Parameters & Geometry")
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"Slab Thickness $h$: **{r['h']} mm**")
        st.write(f"Effective Depth $d$: **{r['d_mm']:.0f} mm**")
    with col2:
        st.write(f"Clear Span $L_{{nx}}$: **{r['ln_x']:.2f} m**")
        st.write(f"Clear Span $L_{{ny}}$: **{r['ln_y']:.2f} m**")
        st.caption("Note: $L_n$ calculated as face-to-face of columns")

    st.latex(formatter.fmt_load_trace(i['dl_fac'], i['sw'], i['sdl'], i['ll_fac'], i['ll'], r['qu']))
    
    # 2. Shear
    st.markdown("### 2. Punching Shear Verification")
    st.latex(formatter.fmt_bo_explanation(r['bo_str'], r['bo_mm'], r['d_mm']))
    st.latex(formatter.fmt_vu_detailed(r['qu'], i['lx'], i['ly'], r['acrit'], r['gamma_v'], r['vu_kg']))
    st.latex(formatter.fmt_vc_conversion_detailed(0.75, r['vc_mpa'], r['bo_mm'], r['d_mm'], r['phi_vc_kg']/1000.0))
    
    pass_flag = r['ratio'] <= 1.0
    color = "green" if pass_flag else "red"
    st.markdown(f"**Shear Ratio:** :{color}[{r['ratio']:.2f}] ({'SAFE' if pass_flag else 'FAIL'})")
    
    # 3. Flexure
    st.markdown("### 3. Flexural Design & Detailing")
    st.latex(fr"M_o = \frac{{q_u L_y L_n^2}}{{8}} = \mathbf{{{r['mo']:,.0f}}} \; kg \cdot m")
    
    # Detailed Calculations
    for idx, bar in enumerate(bars):
        if idx % 2 == 0: col = st.columns(2)
        with col[idx % 2]:
            st.latex(formatter.fmt_rebar_verification(
                bar['name'], bar['coeff'], r['mo'], bar['mu'],
                i['fy'], r['d_mm']/10.0,
                bar['as_req_calc'], bar['as_min'], bar['as_target'],
                bar['user_db'], bar['user_spacing'], bar['bar_area'],
                bar['as_provided'], bar['status'], bar['color'], bar['max_spacing']
            ))

    # 4. Summary Table (Checker Friendly)
    st.markdown("### 4. Design Summary (For Checker)")
    
    summary_data = []
    for bar in bars:
        summary_data.append({
            "Location": bar['name'],
            "Moment (kg-m)": f"{bar['mu']:,.0f}",
            "As Req (cm2)": f"{bar['as_target']:.2f}",
            "Provided": f"DB{bar['user_db']}@{bar['user_spacing']}",
            "As Prov (cm2)": f"{bar['as_provided']:.2f}",
            "Status": "PASS" if "SAFE" in bar['status'] else "FAIL"
        })
        
    df = pd.DataFrame(summary_data)
    st.dataframe(df, use_container_width=True)
