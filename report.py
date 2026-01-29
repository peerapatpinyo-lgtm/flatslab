import streamlit as st
import pandas as pd
import formatter
import drawings

def render_unified_report(base_data, verify_data):
    i = base_data['inputs']
    r = base_data['results']
    efm = base_data['efm']
    bars = verify_data['rebar_verified']

    # --- Header ---
    st.markdown("## 📑 Structural Calculation Report")
    st.markdown(f"**Method:** {i['method']} | **Code:** ACI 318-19")
    st.latex(formatter.fmt_design_philosophy())
    
    st.divider()

    # --- Part 1: Design Criteria ---
    st.subheader("1. Design Criteria")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.caption("Geometry")
        st.write(f"Span Lx: **{i['lx']} m**")
        st.write(f"Span Ly: **{i['ly']} m**")
        st.write(f"Column: **{i['c1']*1000:.0f} x {i['c2']*1000:.0f} mm**")
    with col2:
        st.caption("Materials")
        st.write(f"fc': **{i['fc_mpa']/0.0980665:.0f} ksc**")
        st.write(f"fy: **{i['fy']:.0f} ksc**")
        st.write(f"LL: **{i['ll']} kg/m²**")
    with col3:
        st.caption("Loading (Ultimate)")
        st.latex(f"q_u = {r['qu']:.0f} \; kg/m^2")

    st.divider()

    # --- Part 2: Thickness & Shear Check ---
    st.subheader("2. Thickness & Punching Shear Check")
    
    # Thickness Status
    def_check = "PASS" if r['delta_ratio'] <= 1.0 else "FAIL"
    h_color = "green" if r['delta_ratio'] <= 1.0 else "red"
    st.markdown(f"**Slab Thickness Selected:** {r['h']} mm (Min Req: {r['h_min']:.0f} mm)")
    if r['delta_ratio'] > 1.0:
        st.error(f"⚠️ Immediate Deflection Warning: {r['delta_imm']:.2f} mm > L/240")
    
    # Shear Status
    shear_util = r['ratio']
    shear_status = "OK" if shear_util <= 1.0 else "FAIL"
    shear_msg = f"Shear Utilization: {shear_util:.2f} ({shear_status})"
    
    if shear_util <= 1.0:
        st.success(f"✅ **Punching Shear Passed** | {shear_msg}")
    else:
        st.error(f"❌ **Punching Shear Failed** | {shear_msg}")
        
    with st.expander("Show Shear Calculation Details"):
        st.write(f"Critical Perimeter ($b_o$): **{r['bo_mm']:.0f} mm**")
        st.write(f"Action ($V_u$): **{r['vu_kg']/1000:.2f} tons**")
        st.write(f"Capacity ($\phi V_c$): **{r['phi_vc_kg']/1000:.2f} tons**")
        st.latex(r"\phi V_c = \phi \cdot \min(0.33\sqrt{f'_c}, \dots) \cdot b_o d")

    st.divider()

    # --- Part 3: Moment Analysis ---
    st.subheader("3. Moment Analysis")
    st.latex(f"M_o = \\frac{{q_u L_2 L_n^2}}{{8}} = {r['mo']:,.0f} \; kg\\cdot m")
    
    if "EFM" in i['method']:
        st.info(f"**Stiffness Analysis:** Ext DF = {efm['df_ext_slab']:.3f} | Int DF = {efm['df_int_slab']:.3f}")
    
    # Create a clean dataframe for moments
    moment_data = {
        "Location": ["Column Strip Top (-)", "Column Strip Bot (+)", "Middle Strip Top (-)", "Middle Strip Bot (+)"],
        "Moment (kg-m)": [b['mu'] for b in bars]
    }
    st.table(pd.DataFrame(moment_data))

    st.divider()

    # --- Part 4: Reinforcement Verification ---
    st.subheader("4. Reinforcement Summary")
    
    # Use Container for Summary Cards
    for idx, bar in enumerate(bars):
        with st.container():
            col_res, col_det = st.columns([1, 3])
            with col_res:
                st.markdown(f"#### {bar['name']}")
                st.caption(f"Mu: {bar['mu']:,.0f} kg-m")
            with col_det:
                if bar['color'] == 'green':
                    st.success(f"**PROVIDED:** DB{bar['user_db']}@{bar['user_spacing']} mm (As = {bar['as_provided']:.2f} cm²)")
                else:
                    st.error(f"**FAILED:** {bar['status']}")
            
            # Detailed math in expander
            with st.expander(f"See calculation for {bar['name']}"):
                 st.latex(formatter.fmt_rebar_verification(
                    bar['name'], 0, r['mo'], bar['mu'],
                    i['fy'], r['d_mm']/10.0,
                    bar['as_target'], bar['as_min'], bar['as_target'],
                    bar['user_db'], bar['user_spacing'], 0,
                    bar['as_provided'], bar['status'], bar['color'], bar['max_s']
                ))

    st.divider()

    # --- Part 5: Construction Details ---
    st.subheader("5. Construction Detail (Schematic)")
    
    # Extract rebar text for drawing
    top_txt = f"DB{bars[0]['user_db']}@{bars[0]['user_spacing']}" # CS Top
    bot_txt = f"DB{bars[1]['user_db']}@{bars[1]['user_spacing']}" # CS Bot
    
    fig = drawings.draw_section(
        r['h'], 25, i['c1'], r['ln'], r['d_mm'], 
        top_txt, bot_txt
    )
    st.pyplot(fig)
    
    st.success("🏁 Calculation Complete. Print this page for your records.")
