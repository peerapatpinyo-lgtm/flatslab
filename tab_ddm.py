import streamlit as st
import pandas as pd
import numpy as np
import ddm_plots 

# ========================================================
# 1. MAIN ENTRY POINT
# ========================================================
def render_dual(data_x, data_y, h_slab, d_eff, fc, fy, d_bar, w_u):
    st.markdown("## 2. Interactive Direct Design Method")
    st.info("💡 **Design Mode:** Complete analysis (ACI 318 / EIT Standards). Includes detailed derivation.")

    tab_x, tab_y = st.tabs([
        f"🏗️ Design X-Dir ({data_x['L_span']}m)", 
        f"🏗️ Design Y-Dir ({data_y['L_span']}m)"
    ])
    
    with tab_x:
        render_interactive_direction(data_x, h_slab, d_eff, fc, fy, "X", w_u)
    with tab_y:
        render_interactive_direction(data_y, h_slab, d_eff, fc, fy, "Y", w_u)

# ========================================================
# 2. CALCULATION & UI
# ========================================================
def render_interactive_direction(data, h_slab, d_eff, fc, fy, axis_id, w_u):
    # Unpack Data
    L_span = data['L_span']
    L_width = data['L_width']
    c_para = data['c_para']
    Mo = data['Mo']
    m_vals = data['M_vals']
    
    # Strip Widths (ACI 318 Definition)
    w_cs = min(L_span, L_width) / 2.0
    w_ms = L_width - w_cs
    
    # Clear Span
    Ln = L_span - (c_para / 100.0)

    # ----------------------------------------------------
    # 📝 PART A: DETAILED CALCULATION (STEP-BY-STEP)
    # ----------------------------------------------------
    st.markdown(f"### 📐 Detailed Calculation: {axis_id}-Direction")
    
    with st.expander("📝 Show Engineering Calculations (แสดงรายการคำนวณละเอียด)", expanded=False):
        # --- 1. Geometry ---
        st.markdown("#### 1. Geometry & Static Moment ($M_o$)")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Span ($L_1$)", f"{L_span:.2f} m")
            st.metric("Width ($L_2$)", f"{L_width:.2f} m")
        with c2:
            st.metric("Column ($c_1$)", f"{c_para/100:.2f} m")
            st.metric("Clear Span ($l_n$)", f"{Ln:.2f} m")
        with c3:
            st.metric("Factored Load ($w_u$)", f"{w_u:,.0f} kg/m²")
        
        st.markdown("**Total Static Moment (ACI 318 Eq. 8.10.3.2):**")
        st.latex(r"M_o = \frac{w_u L_2 l_n^2}{8}")
        st.latex(f"M_o = \\frac{{{w_u:,.0f} \\times {L_width:.2f} \\times {Ln:.2f}^2}}{{8}} = \\mathbf{{{Mo:,.0f}}} \\; \\text{{kg-m}}")

        # --- 2. Distribution Factors ---
        st.markdown("---")
        st.markdown("#### 2. Moment Distribution Coefficients")
        st.caption("การกระจายโมเมนต์จาก $M_o$ ไปยัง Column Strip และ Middle Strip")
        
        # Calculate Implicit Factors for display
        f_cs_neg = m_vals['M_cs_neg'] / (m_vals['M_cs_neg'] + m_vals['M_ms_neg']) if (m_vals['M_cs_neg'] + m_vals['M_ms_neg']) > 0 else 0
        f_cs_pos = m_vals['M_cs_pos'] / (m_vals['M_cs_pos'] + m_vals['M_ms_pos']) if (m_vals['M_cs_pos'] + m_vals['M_ms_pos']) > 0 else 0
        
        # Table Data
        dist_data = [
            ["Total Negative (-)", "100%", f"{m_vals['M_cs_neg'] + m_vals['M_ms_neg']:,.0f}"],
            [f"... Column Strip ({f_cs_neg*100:.0f}%)", f"{(m_vals['M_cs_neg']/Mo)*100:.1f}% of Mo", f"{m_vals['M_cs_neg']:,.0f}"],
            [f"... Middle Strip ({100-f_cs_neg*100:.0f}%)", f"{(m_vals['M_ms_neg']/Mo)*100:.1f}% of Mo", f"{m_vals['M_ms_neg']:,.0f}"],
            ["Total Positive (+)", "100%", f"{m_vals['M_cs_pos'] + m_vals['M_ms_pos']:,.0f}"],
            [f"... Column Strip ({f_cs_pos*100:.0f}%)", f"{(m_vals['M_cs_pos']/Mo)*100:.1f}% of Mo", f"{m_vals['M_cs_pos']:,.0f}"],
            [f"... Middle Strip ({100-f_cs_pos*100:.0f}%)", f"{(m_vals['M_ms_pos']/Mo)*100:.1f}% of Mo", f"{m_vals['M_ms_pos']:,.0f}"],
        ]
        st.table(pd.DataFrame(dist_data, columns=["Zone", "% Distribution", "Moment (kg-m)"]))

        # --- 3. REBAR CALCULATION EXAMPLE (NEW!) ---
        st.markdown("---")
        st.markdown("#### 3. Flexural Reinforcement Calculation (Example)")
        st.markdown(f"**Sample Calculation for: Column Strip - Top (Negative Moment)**")
        
        # Get Sample Values
        M_u_sample = m_vals['M_cs_neg']
        b_sample_cm = w_cs * 100
        d_sample = d_eff # cm
        phi = 0.9
        
        # Step 1: Rn
        Rn_sample = (M_u_sample * 100) / (phi * b_sample_cm * d_sample**2) # ksc
        
        # Step 2: Rho
        # rho = (0.85*fc/fy) * (1 - sqrt(1 - 2Rn/(0.85fc)))
        term = 1 - (2 * Rn_sample) / (0.85 * fc)
        if term < 0:
            rho_sample = 0 # Error case (Section too small)
            txt_term = "Error (Section too small)"
        else:
            rho_sample = (0.85 * fc / fy) * (1 - np.sqrt(term))
            txt_term = f"{rho_sample:.5f}"
            
        # Step 3: As Req
        As_req_sample = rho_sample * b_sample_cm * d_sample
        As_min_sample = 0.0018 * b_sample_cm * h_slab
        As_final_sample = max(As_req_sample, As_min_sample)

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Design Parameters:**")
            st.write(f"- $M_u = {M_u_sample:,.0f}$ kg-m")
            st.write(f"- $b = {b_sample_cm:.0f}$ cm")
            st.write(f"- $d = {d_sample:.2f}$ cm")
            st.write(f"- $f_c' = {fc}$ ksc, $f_y = {fy}$ ksc")
        
        with c2:
            st.markdown("**Formulas (Strength Design):**")
            st.latex(r"R_n = \frac{M_u}{0.9 b d^2}")
            st.latex(r"\rho = \frac{0.85f_c'}{f_y}\left(1 - \sqrt{1 - \frac{2R_n}{0.85f_c'}}\right)")
            st.latex(r"A_{s,req} = \rho b d")

        st.markdown("**Substitution:**")
        st.latex(f"R_n = \\frac{{{M_u_sample:,.0f} \\times 100}}{{0.9 \\times {b_sample_cm:.0f} \\times {d_sample:.2f}^2}} = \\mathbf{{{Rn_sample:.2f}}} \\; \\text{{ksc}}")
        st.latex(f"\\rho_{{calc}} = \\mathbf{{{rho_sample:.5f}}}")
        st.latex(f"A_{{s,req}} = {rho_sample:.5f} \\times {b_sample_cm:.0f} \\times {d_sample:.2f} = \\mathbf{{{As_req_sample:.2f}}} \\; \\text{{cm}}^2")
        st.info(f"Note: Minimum steel ($A_{{s,min}} = 0.0018bh$) = {As_min_sample:.2f} cm² is also checked.")

    # ----------------------------------------------------
    # 🎛️ PART B: INTERACTIVE REBAR DESIGN
    # ----------------------------------------------------
    # Calculation Logic for ALL Zones
    def calc_rebar_logic(M_u, b_width, d_bar, s_bar):
        b_cm = b_width * 100
        h_cm = h_slab
        d_local = h_cm - 3.0 # Approx d
        
        # 1. As Required (Theoretical)
        Rn = (M_u * 100) / (0.9 * b_cm * d_local**2)
        term = 1 - (2*Rn)/(0.85*fc)
        if term < 0: 
            rho = 999 # Fail
        else:
            rho = (0.85*fc/fy) * (1 - np.sqrt(term))
        
        As_flex = rho * b_cm * d_local
        As_min = 0.0018 * b_cm * h_cm
        As_req_final = max(As_flex, As_min) if rho != 999 else 999
        
        # 2. As Provided
        Ab = 3.1416*(d_bar/10)**2/4
        As_prov = (b_cm/s_bar)*Ab
        
        # 3. Strength Check (Phi Mn)
        a = (As_prov*fy)/(0.85*fc*b_cm)
        PhiMn = 0.9 * As_prov * fy * (d_local - a/2) / 100
        
        # 4. Spacing Check (2h)
        s_max = min(2 * h_cm, 45)
        
        # Status
        dc_ratio = M_u / PhiMn if PhiMn > 0 else 999
        pass_str = dc_ratio <= 1.0
        pass_min = As_prov >= As_min
        pass_space = s_bar <= s_max
        
        is_pass = pass_str and pass_min and pass_space
        
        # Note generation
        notes = []
        if not pass_str: notes.append("Strength")
        if not pass_min: notes.append("Min Steel")
        if not pass_space: notes.append("Spacing")
        note_str = ", ".join(notes) if notes else "-"
        
        return As_req_final, As_prov, PhiMn, dc_ratio, s_max, is_pass, note_str

    # --- UI Inputs ---
    st.markdown(f"### 🎛️ Reinforcement Selection")
    
    col_cs, col_gap, col_ms = st.columns([1, 0.05, 1])
    
    # === CS INPUTS ===
    with col_cs:
        st.markdown(f"""<div style="background-color:{ddm_plots.CLR_ZONE_CS}; padding:10px; border-radius:5px; border-left:5px solid {ddm_plots.CLR_BAR_TOP};">
        <b>COLUMN STRIP</b> ({w_cs:.2f} m)</div>""", unsafe_allow_html=True)
        st.write("")
        st.caption("Top Rebar (Support)")
        c1, c2 = st.columns([1, 1.5])
        d_cs_top = c1.selectbox("DB", [12,16,20,25], key=f"dct{axis_id}")
        s_cs_top = c2.number_input("@Spacing (cm)", 5, 50, 20, 5, key=f"sct{axis_id}")
        
        st.caption("Bot Rebar (Mid-span)")
        c1, c2 = st.columns([1, 1.5])
        d_cs_bot = c1.selectbox("DB", [12,16,20,25], key=f"dcb{axis_id}")
        s_cs_bot = c2.number_input("@Spacing (cm)", 5, 50, 25, 5, key=f"scb{axis_id}")

    # === MS INPUTS ===
    with col_ms:
        st.markdown(f"""<div style="background-color:{ddm_plots.CLR_ZONE_MS}; padding:10px; border-radius:5px; border-left:5px solid {ddm_plots.CLR_BAR_BOT};">
        <b>MIDDLE STRIP</b> ({w_ms:.2f} m)</div>""", unsafe_allow_html=True)
        st.write("")
        st.caption("Top Rebar (Support)")
        c1, c2 = st.columns([1, 1.5])
        d_ms_top = c1.selectbox("DB", [12,16,20,25], index=0, key=f"dmt{axis_id}")
        s_ms_top = c2.number_input("@Spacing (cm)", 10, 50, 30, 5, key=f"smt{axis_id}")
        
        st.caption("Bot Rebar (Mid-span)")
        c1, c2 = st.columns([1, 1.5])
        d_ms_bot = c1.selectbox("DB", [12,16,20,25], key=f"dmb{axis_id}")
        s_ms_bot = c2.number_input("@Spacing (cm)", 5, 50, 25, 5, key=f"smb{axis_id}")

    # Process Results for Table
    zones = [
        {"name": "CS-Top", "M": m_vals['M_cs_neg'], "b": w_cs, "d": d_cs_top, "s": s_cs_top},
        {"name": "CS-Bot", "M": m_vals['M_cs_pos'], "b": w_cs, "d": d_cs_bot, "s": s_cs_bot},
        {"name": "MS-Top", "M": m_vals['M_ms_neg'], "b": w_ms, "d": d_ms_top, "s": s_ms_top},
        {"name": "MS-Bot", "M": m_vals['M_ms_pos'], "b": w_ms, "d": d_ms_bot, "s": s_ms_bot},
    ]

    res_list = []
    rebar_map = {}
    overall_safe = True

    for z in zones:
        As_req, As_prov, PhiMn, dc, s_max, is_pass, note = calc_rebar_logic(z['M'], z['b'], z['d'], z['s'])
        
        if not is_pass: overall_safe = False
        
        status_icon = "✅ Pass" if is_pass else "❌ Fail"
        
        res_list.append({
            "Location": f"<b>{z['name']}</b>",
            "Mu (kg-m)": f"{z['M']:,.0f}",
            "Req. As": f"<b>{As_req:.2f}</b>", # Increased Visibility
            "Selection": f"DB{z['d']}@{z['s']}",
            "Prov. As": f"{As_prov:.2f}",
            "φMn": f"{PhiMn:,.0f}",
            "D/C": f"<b style='color:{'green' if dc<=1 else 'red'}'>{dc:.2f}</b>",
            "Max @": f"{s_max}",
            "Status": f"<b>{status_icon}</b>",
            "Note": f"<small style='color:red'>{note}</small>"
        })
        rebar_map[z['name'].replace("-","_")] = f"DB{z['d']}@{z['s']}"

    # Render Summary Table
    st.write("---")
    st.markdown("### 📊 Engineering Summary Table")
    df_res = pd.DataFrame(res_list)
    # Custom CSS/HTML for table is handled by pandas style
    st.write(df_res.style.format(precision=2).to_html(escape=False, index=False), unsafe_allow_html=True)
    
    if not overall_safe:
        st.error("⚠️ warning: Please increase rebar size or reduce spacing.")

    # ----------------------------------------------------
    # 🖼️ PART C: ENGINEERING DRAWINGS
    # ----------------------------------------------------
    st.write("---")
    st.markdown("### 📐 Professional Drawings")
    
    try:
        st.pyplot(ddm_plots.plot_ddm_moment(L_span, c_para, m_vals))
    except Exception as e: st.error(f"Plot Error: {e}")
    
    c1, c2 = st.columns(2)
    with c1:
        st.pyplot(ddm_plots.plot_rebar_detailing(L_span, h_slab, c_para, rebar_map, axis_id))
    with c2:
        st.pyplot(ddm_plots.plot_rebar_plan_view(L_span, L_width, c_para, rebar_map, axis_id))
