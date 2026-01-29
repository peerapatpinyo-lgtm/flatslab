import streamlit as st
import pandas as pd
import drawings

def render_unified_report(data):
    """
    Renders the full report using ONLY data passed from engine.
    No calculations allowed here.
    """
    
    # Unpack for easier access (Read-Only)
    meta = data['meta']
    shear = data['shear']
    flex = data['flexure']
    defl = data['deflection']
    geo = data['geometry']
    status = data['global_status']

    # --- 1. HEADER & STATUS ---
    st.markdown("## 📑 Structural Calculation Report")
    
    if status == "SAFE":
        st.success(f"✅ **DESIGN PASSED:** The structure is SAFE under defined loads.")
    else:
        st.error(f"❌ **DESIGN FAILED:** Please review Shear or Reinforcement.")
        
    st.divider()

    # --- 2. INPUT SUMMARY ---
    st.markdown("### 1. Input Summary")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Span (Lx x Ly)", f"{meta['lx']} x {meta['ly']} m")
    c2.metric("Thickness", f"{meta['h']} mm")
    c3.metric("Concrete (fc')", f"{meta['fc']} ksc")
    c4.metric("Steel (fy)", f"{meta['fy']} ksc")
    
    st.caption(f"**Loads:** SDL = {meta['sdl']}, LL = {meta['ll']} kg/m²")

    # --- 3. SHEAR CHECK ---
    st.markdown("### 2. Punching Shear Check")
    col_s1, col_s2 = st.columns([1, 2])
    
    with col_s1:
        s_color = "green" if shear['status'] == "PASS" else "red"
        st.markdown(f"Status: :{s_color}[**{shear['status']}**]")
        st.metric("Utilization Ratio", f"{shear['ratio']:.2f}")
    
    with col_s2:
        st.write(f"Effective Depth ($d$): **{shear['d_mm']:.0f} mm**")
        st.write(f"Critical Perimeter ($b_o$): **{shear['bo_mm']:.0f} mm**")
        st.write(f"Shear Demand ($V_u$): **{shear['vu']/1000:.2f} tons**")
        st.write(f"Shear Capacity ($\phi V_c$): **{shear['phi_vc']/1000:.2f} tons**")

    st.divider()

    # --- 4. FLEXURE & REBAR ---
    st.markdown("### 3. Flexural Verification")
    st.write(f"Total Static Moment ($M_o$): **{flex['mo']:,.0f} kg-m**")
    
    # Prepare DataFrame from prepared list
    df_rows = []
    for r in flex['results']:
        df_rows.append({
            "Location": r['location'],
            "Moment (Mu)": f"{r['mu']:,.0f}",
            "Rebar": f"DB{r['user_db']}@{r['user_sp']}",
            "As Prov": f"{r['as_prov']:.2f}",
            "As Req": f"{max(r['as_req'], r['as_min']):.2f}",
            "Util": f"{r['utilization']:.2f}",
            "Status": r['status']
        })
    
    st.dataframe(pd.DataFrame(df_rows), use_container_width=True)

    # --- 5. DEFLECTION ---
    st.markdown("### 4. Deflection Check (Immediate)")
    d_col = "green" if defl['status'] == "PASS" else "red"
    st.markdown(f"Delta: **{defl['val']:.2f} mm** vs Limit: **{defl['lim']:.2f} mm** (:{d_col}[**{defl['status']}**])")

    st.divider()

    # --- 6. DRAWING ---
    st.markdown("### 5. Construction Detail")
    try:
        # Extract rebar strings for drawing
        # Assumes index 0 is Top, index 1 is Bot from engine list
        top_str = f"DB{flex['results'][0]['user_db']}@{flex['results'][0]['user_sp']}"
        bot_str = f"DB{flex['results'][1]['user_db']}@{flex['results'][1]['user_sp']}"
        
        fig = drawings.draw_section(
            meta['h'], geo['cover'], geo['c1'], 
            meta['lx']/2, shear['d_mm'], 
            top_str, bot_str
        )
        st.pyplot(fig)
    except Exception as e:
        st.warning(f"Drawing unavailable: {e}")
