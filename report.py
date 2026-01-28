import streamlit as st
import formatter

def render_report(data):
    inp = data['inputs']
    res = data['results']
    rebar_list = data['rebar']
    
    st.markdown("## Design Calculation Report")
    
    # --- Step 1: Geometry ---
    st.markdown("### Step 1: Geometry & Traceability")
    st.info(f"Traceability: Input $h={inp['h_init']}$ mm $\\rightarrow$ Final Design $h={res['h']}$ mm (Reason: {res['reason']})")
    
    st.latex(formatter.fmt_geometry_step(
        inp['c1_mm'], inp['c2_mm'], res['d_mm'], res['bo_mm'], res['acrit'], inp['pos']
    ))
    
    # --- Step 2: Loads ---
    st.markdown("### Step 2: Load Analysis")
    st.latex(formatter.fmt_load_step(
        inp['dl_fac'], inp['sw'], inp['sdl'], inp['ll_fac'], inp['ll'], res['qu'], res['h']
    ))
    
    # --- Step 3: Punching Shear ---
    st.markdown("### Step 3: Punching Shear Check (Detailed)")
    # Show Vc components first
    st.caption(f"Shear Capacities: $v_{{c1}}={res['v1']:.2f}, v_{{c2}}={res['v2']:.2f}, v_{{c3}}={res['v3']:.2f} \\rightarrow v_{{min}} = {res['vc_gov_mpa']:.2f}$ MPa")
    
    st.latex(formatter.fmt_shear_detailed(
        res['qu'], inp['lx'], inp['ly'], res['acrit'], res['gamma_v'],
        res['vu_kg'], 0.75, res['vc_gov_mpa'], res['bo_mm'], res['d_mm'],
        res['phi_vc_kg'], res['ratio']
    ))
    
    # --- Step 4: Flexure ---
    st.markdown("### Step 4: Flexural Reinforcement")
    st.latex(r"M_o = \frac{q_u \ell_n^2}{8} = \mathbf{" + f"{res['mo']:,.0f}" + r"} \; kg \cdot m")
    
    # Display 4 Strips using Columns
    c1, c2 = st.columns(2)
    c3, c4 = st.columns(2)
    cols = [c1, c2, c3, c4]
    
    for i, item in enumerate(rebar_list):
        if i < 4:
            with cols[i]:
                st.latex(formatter.fmt_flexure_calc(
                    item['name'], item['coeff'], res['mo'], item['mu'], 
                    inp['fy'], item['d_cm'], item['as_req']
                ))
