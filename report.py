import streamlit as st
import formatter
import pandas as pd

def render_report(base_data, verify_data):
    i = base_data['inputs']
    r = base_data['results']
    efm = base_data['efm']
    bars = verify_data['rebar_verified']
    
    st.markdown("## 🏗️ Professional Design Report")
    st.latex(formatter.fmt_design_philosophy())
    
    # --- 1. Summary Dashboard ---
    st.markdown("### 1. Design Status Summary")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Slab Thickness", f"{r['h']} mm", f"Min: {r['h_min']:.0f} mm")
    with c2:
        ur_shear = r['ratio']
        st.metric("Shear Utilization", f"{ur_shear:.2f}", "Limit 1.0", delta_color="inverse")
    with c3:
        ur_flex = verify_data['max_flexure_util']
        st.metric("Flexure Utilization", f"{ur_flex:.2f}", "Limit 1.0", delta_color="inverse")
    with c4:
        def_ratio = r['delta_ratio']
        st.metric("Deflection (Imm)", f"{r['delta_imm']:.1f} mm", f"Lim: {r['delta_lim']:.1f} mm")

    if r['delta_ratio'] > 1.0:
        st.error(f"⚠️ Warning: Immediate Deflection exceeds L/240 ({r['delta_lim']:.1f} mm). Increase thickness or stiffness.")

    st.divider()

    # --- 2. Geometry & Analysis ---
    st.markdown("### 2. Geometry & Stiffness Analysis")
    st.latex(formatter.fmt_load_trace(i['dl_fac'], i['sw'], i['sdl'], i['ll_fac'], i['ll'], r['qu']))
    
    if "EFM" in i['method']:
        st.info("Equivalent Frame Method Calculation Details:")
        st.latex(formatter.fmt_stiffness_substitution(efm))
        col_k1, col_k2 = st.columns(2)
        col_k1.metric("DF Slab (Exterior)", f"{efm['df_ext_slab']:.3f}")
        col_k2.metric("DF Slab (Interior)", f"{efm['df_int_slab']:.3f}")

    # --- 3. Flexural Design ---
    st.markdown("### 3. Flexural Design & Detailing")
    
    for idx, bar in enumerate(bars):
        if idx % 2 == 0: col = st.columns(2)
        with col[idx % 2]:
            st.latex(formatter.fmt_rebar_verification(
                bar['name'], 0, r['mo'], bar['mu'],
                i['fy'], r['d_mm']/10.0,
                bar['as_target'], bar['as_min'], bar['as_target'],
                bar['user_db'], bar['user_spacing'], 0,
                bar['as_provided'], bar['status'], bar['color'], bar['max_s']
            ))

    # --- 4. Shear Check ---
    st.markdown("### 4. Punching Shear Verification")
    st.write(f"Shear Perimeter ($b_o$): **{r['bo_mm']:.0f} mm** | Action ($V_u$): **{r['vu_kg']/1000:.2f} T**")
    st.write(f"Capacity ($\phi V_c$): **{r['phi_vc_kg']/1000:.2f} T**")
    
    if r['ratio'] > 1.0:
        st.error("❌ PUNCHING SHEAR FAILURE: Increase slab thickness or column size.")
    else:
        st.success("✅ SHEAR CHECK PASSED")
