import streamlit as st
import pandas as pd
import drawings
import formatter

def render_unified_report(data):
    i = data['inputs']
    r = data['results']
    bars = data['rebar']
    
    # --- 1. Global Status Banner ---
    st.markdown("## 📑 Structural Calculation Sheet")
    
    status = r['overall_status']
    if status == "SAFE":
        st.success(f"✅ **DESIGN PASSED:** The structure is SAFE with the selected reinforcement.")
    else:
        st.error(f"❌ **DESIGN FAILED:** The structure is UNSAFE. Please adjust Thickness or Rebar.")
    
    st.divider()

    # --- 2. Design Criteria Table ---
    st.markdown("### 1. Design Criteria")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Span", f"{i['lx']} x {i['ly']} m")
    col2.metric("Thickness", f"{i['h']} mm")
    col3.metric("Concrete (fc')", f"{i['fc']} ksc")
    col4.metric("Steel (fy)", f"{i['fy']} ksc")
    
    st.caption(f"**Loading:** SDL = {i['sdl']} kg/m², LL = {i['ll']} kg/m² -> **Qu = {r['vu']/(i['lx']*i['ly']):.0f} kg/m²**")

    # --- 3. Shear & Deflection Section ---
    st.markdown("### 2. Serviceability & Shear Check")
    
    c_shear, c_defl = st.columns(2)
    with c_shear:
        st.markdown("**Punching Shear Check**")
        s_ratio = r['shear_ratio']
        s_color = "green" if s_ratio <= 1.0 else "red"
        st.write(f"Action $V_u$: **{r['vu']/1000:.2f} T**")
        st.write(f"Capacity $\phi V_c$: **{r['phi_vc']/1000:.2f} T**")
        st.markdown(f"Utilization: :{s_color}[**{s_ratio:.2f}**]")
        if s_ratio > 1.0: st.warning("Increase Slab Thickness or Concrete Strength")

    with c_defl:
        st.markdown("**Deflection Check (Immediate)**")
        d_ratio = r['delta_ratio']
        d_color = "green" if d_ratio <= 1.0 else "red"
        st.write(f"Deflection $\Delta$: **{r['delta_imm']:.2f} mm**")
        st.write(f"Limit $L/240$: **{i['lx']*1000/240:.2f} mm**")
        st.markdown(f"Ratio: :{d_color}[**{d_ratio:.2f}**]")

    st.divider()

    # --- 4. Flexural & Rebar Verification ---
    st.markdown("### 3. Flexural Design & Rebar Verification")
    st.info(f"Using effective depth $d \\approx {r['d_mm']:.0f}$ mm (Based on user rebar)")

    # Prepare DataFrame for Display
    table_data = []
    for b in bars:
        status_icon = "✅" if b['status'] == "SAFE" else "❌"
        row = {
            "Location": b['name'],
            "Moment (Mu)": f"{b['mu']:,.0f}",
            "As Req (cm²)": f"{max(b['as_req'], b['as_min']):.2f}",
            "User Rebar": f"DB{b['db']}@{b['sp']}",
            "As Prov (cm²)": f"{b['as_prov']:.2f}",
            "Utilization": f"{b['util']:.2f}",
            "Status": f"{status_icon} {b['note']}"
        }
        table_data.append(row)
    
    df = pd.DataFrame(table_data)
    st.dataframe(df, use_container_width=True)

    # --- 5. Detailing Visualization ---
    st.markdown("### 4. Construction Detail")
    top_txt = f"DB{bars[0]['db']}@{bars[0]['sp']}"
    bot_txt = f"DB{bars[1]['db']}@{bars[1]['sp']}"
    
    fig = drawings.draw_section(
        i['h'], i['cover'], i['c1'], r['d_mm']/1000*0.8 + i['c1'], r['d_mm'], 
        top_txt, bot_txt
    )
    st.pyplot(fig)
