import streamlit as st
import formatter

def render(data):
    i = data['inputs']
    l = data['loads']
    s = data['shear']
    f = data['flexure']
    
    st.title("🏗️ Structural Calculation Report")
    st.markdown("---")

    # --- SECTION 1: GEOMETRY & MATERIALS ---
    st.header("1. Geometry & Materials")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.write(f"**Dimensions:**")
        st.write(f"Thickness (h): {i['h']} mm")
        st.write(f"Cover (cc): {i['cover']} mm")
    with c2:
        st.write(f"**Column:**")
        st.write(f"Size: {i['c1']} x {i['c2']} mm")
        st.write(f"Position: {i['pos']}")
    with c3:
        st.write(f"**Materials:**")
        st.write(f"fc': {i['fc']} ksc")
        st.write(f"fy: {i['fy']} ksc")

    # --- SECTION 2: LOAD ANALYSIS ---
    st.header("2. Load Analysis")
    st.latex(formatter.fmt_load_trace(i['h'], i['sdl'], i['ll'], l['sw'], l['qu']))

    # --- SECTION 3: SHEAR ANALYSIS ---
    st.header("3. Punching Shear Verification")
    
    st.subheader("3.1 Effective Depth Calculation")
    # Live d update displayed here
    st.latex(formatter.fmt_d_calc(i['h'], i['cover'], (i['top_db']+i['bot_db'])/2, s['d_mm']))
    
    st.subheader("3.2 Critical Section Properties")
    st.latex(formatter.fmt_shear_geometry(i['c1'], i['c2'], s['d_mm'], s['bo'], i['pos']))
    
    st.subheader("3.3 Shear Capacity (ACI 318-19)")
    st.markdown("Checking all 3 equations to find governing $V_c$:")
    st.latex(formatter.fmt_shear_capacity(
        i['fc'] * 0.098, s['beta'], s['alpha'], s['d_mm'], s['bo'],
        s['vc1'], s['vc2'], s['vc3'], s['vc_final'], s['phi_vc_kg'] * 9.8
    ))
    
    st.subheader("3.4 Shear Check")
    st.latex(formatter.fmt_shear_check(s['vu_kg'] * 9.8, s['phi_vc_kg'] * 9.8))

    # --- SECTION 4: FLEXURAL DESIGN ---
    st.header("4. Flexural Design & Detailing")
    
    st.markdown(f"**Total Static Moment ($M_o$):** {f['mo']:,.0f} kg-m")
    
    st.subheader("4.1 Top Reinforcement (Column Strip - Negative)")
    r_top = f['top']
    st.latex(formatter.fmt_moment_calc(
        r_top[0], i['fy'], s['d_mm'], r_top[1], r_top[2], r_top[3], i['top_db'], i['top_sp'], r_top[4]
    ))
    
    st.subheader("4.2 Bottom Reinforcement (Column Strip - Positive)")
    r_bot = f['bot']
    st.latex(formatter.fmt_moment_calc(
        r_bot[0], i['fy'], s['d_mm'], r_bot[1], r_bot[2], r_bot[3], i['bot_db'], i['bot_sp'], r_bot[4]
    ))

    st.markdown("---")
    st.success("🏁 Calculation Complete. All values are explicitly derived above.")
