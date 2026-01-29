import streamlit as st
import pandas as pd
import numpy as np
import ddm_plots 

# ========================================================
# 1. MAIN ENTRY POINT
# ========================================================
def render_dual(data_x, data_y, h_slab, d_eff, fc, fy, d_bar, w_u):
    st.markdown("## 2. Interactive Direct Design Method")
    st.info("💡 **Design Mode:** Complete analysis according to ACI 318 / EIT Standards.")

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
    # Column Strip width = 2 * (min(L1, L2)/4) = min(L1, L2)/2
    w_cs = min(L_span, L_width) / 2.0
    w_ms = L_width - w_cs
    
    # Clear Span
    Ln = L_span - (c_para / 100.0)

    # ----------------------------------------------------
    # 📝 PART A: DETAILED CALCULATION (STEP-BY-STEP)
    # ----------------------------------------------------
    # [FIXED LINE BELOW]: Changed {axis_id-Direction} to {axis_id}-Direction
    st.markdown(f"### 📐 Detailed Calculation: {axis_id}-Direction")
    
    with st.expander("📝 Show Engineering Calculations (แสดงรายการคำนวณ)", expanded=False):
        # 1. Geometry
        st.markdown("#### 1. Geometry & Static Moment ($M_o$)")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Span ($L_1$)", f"{L_span:.2f} m")
            st.metric("Width ($L_2$)", f"{L_width:.2f} m")
        with c2:
            st.metric("Column ($c_1$)", f"{c_para/100:.2f} m")
            st.metric("Clear Span ($l_n$)", f"{Ln:.2f} m")
        with c3:
            st.metric("Load ($w_u$)", f"{w_u:,.0f} kg/m²")
        
        st.markdown("**Total Static Moment (ACI 318 Eq. 8.10.3.2):**")
        st.latex(r"M_o = \frac{w_u L_2 l_n^2}{8}")
        st.latex(f"M_o = \\frac{{{w_u:,.0f} \\times {L_width:.2f} \\times {Ln:.2f}^2}}{{8}} = \\mathbf{{{Mo:,.0f}}} \\; \\text{{kg-m}}")

        # 2. Distribution Factors
        st.markdown("#### 2. Moment Distribution Coefficients")
        st.caption("ตรวจสอบสัมประสิทธิ์การกระจายโมเมนต์ (Distribution Factors) เทียบกับมาตรฐาน ACI/วสท.")
        
        # Calculate Implicit Factors for verification
        f_neg_total = (m_vals['M_cs_neg'] + m_vals['M_ms_neg']) / Mo
        f_pos_total = (m_vals['M_cs_pos'] + m_vals['M_ms_pos']) / Mo
        
        f_cs_neg = m_vals['M_cs_neg'] / (m_vals['M_cs_neg'] + m_vals['M_ms_neg']) if (m_vals['M_cs_neg'] + m_vals['M_ms_neg']) > 0 else 0
        f_cs_pos = m_vals['M_cs_pos'] / (m_vals['M_cs_pos'] + m_vals['M_ms_pos']) if (m_vals['M_cs_pos'] + m_vals['M_ms_pos']) > 0 else 0

        # Create Verification Table
        dist_data = [
            ["Total Negative (-)", f"{f_neg_total:.2f} $M_o$", f"{Mo*f_neg_total:,.0f}", "100%", "Check ACI Table 8.10.4.2"],
            ["... Column Strip", f"{f_cs_neg:.2f} $M_{{neg}}$", f"{m_vals['M_cs_neg']:,.0f}", f"{(m_vals['M_cs_neg']/Mo)*100:.1f}%", "Typically 75%"],
            ["... Middle Strip", f"{1-f_cs_neg:.2f} $M_{{neg}}$", f"{m_vals['M_ms_neg']:,.0f}", f"{(m_vals['M_ms_neg']/Mo)*100:.1f}%", "Remainder (25%)"],
            ["Total Positive (+)", f"{f_pos_total:.2f} $M_o$", f"{Mo*f_pos_total:,.0f}", "100%", "Check ACI Table 8.10.4.2"],
            ["... Column Strip", f"{f_cs_pos:.2f} $M_{{pos}}$", f"{m_vals['M_cs_pos']:,.0f}", f"{(m_vals['M_cs_pos']/Mo)*100:.1f}%", "Typically 60%"],
            ["... Middle Strip", f"{1-f_cs_pos:.2f} $M_{{pos}}$", f"{m_vals['M_ms_pos']:,.0f}", f"{(m_vals['M_ms_pos']/Mo)*100:.1f}%", "Remainder (40%)"],
        ]
        df_dist = pd.DataFrame(dist_data, columns=["Section", "Coeff.", "Moment (kg-m)", "% of Mo", "Note"])
        st.table(df_dist)

    # ----------------------------------------------------
    # 🎛️ PART B: INTERACTIVE REBAR DESIGN
    # ----------------------------------------------------
    # Calculation Helper
    def calc_rebar_status(M_u, b_width, d_bar, s_bar):
        b_cm = b_width * 100
        h_cm = h_slab
        d_eff_local = h_cm - 3.0 # Approx cover 2.5 + 0.5 bar
        
        # 1. Provided Steel
        Ab = 3.1416*(d_bar/10)**2/4
        As_prov = (b_cm/s_bar)*Ab
        
        # 2. Strength Check (Phi Mn)
        a = (As_prov*fy)/(0.85*fc*b_cm)
        PhiMn = 0.9 * As_prov * fy * (d_eff_local - a/2) / 100
        
        # 3. Minimum Steel Check (ACI 8.6.1.1: 0.0018 Ag)
        As_min = 0.0018 * b_cm * h_cm
        
        # 4. Spacing Check (ACI 8.7.2.2: 2h)
        s_max = min(2 * h_cm, 45) # 2h or 450mm
        
        # Ratios
        dc_ratio = M_u / PhiMn if PhiMn > 0 else 999
        min_steel_ok = As_prov >= As_min
        spacing_ok = s_bar <= s_max
        
        return As_prov, PhiMn, dc_ratio, As_min, min_steel_ok, s_max, spacing_ok

    # UI Inputs
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

    # Process Results
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
        As, PhiMn, dc, As_min, ok_min, s_max, ok_space = calc_rebar_status(z['M'], z['b'], z['d'], z['s'])
        
        # Logic for Status
        # 1. Strength
        pass_str = dc <= 1.0
        # 2. Min Steel
        pass_min = ok_min
        # 3. Spacing
        pass_space = ok_space
        
        is_pass = pass_str and pass_min and pass_space
        if not is_pass: overall_safe = False
        
        status_icon = "✅ Pass" if is_pass else "❌ Fail"
        note = ""
        if not pass_str: note += "Strength Insufficient. "
        if not pass_min: note += "As < As,min. "
        if not pass_space: note += "Spacing > 2h. "
        
        res_list.append({
            "Location": f"<b>{z['name']}</b>",
            "Demand Mu": f"{z['M']:,.0f}",
            "Selection": f"DB{z['d']}@{z['s']}",
            "As Prov.": f"{As:.2f}",
            "As Min": f"{As_min:.2f}",
            "φMn Cap.": f"{PhiMn:,.0f}",
            "D/C Ratio": f"<b style='color:{'green' if pass_str else 'red'}'>{dc:.2f}</b>",
            "Max Spacing": f"{s_max} cm",
            "Status": f"<b>{status_icon}</b>",
            "Note": f"<small style='color:red'>{note}</small>" if note else "-"
        })
        
        # Save for plotting
        rebar_map[z['name'].replace("-","_")] = f"DB{z['d']}@{z['s']}"

    # Render Summary Table
    st.write("---")
    st.markdown("### 📊 Engineering Summary Table")
    df_res = pd.DataFrame(res_list)
    st.write(df_res.style.format(precision=2).to_html(escape=False, index=False), unsafe_allow_html=True)
    
    if not overall_safe:
        st.error("⚠️ warning: Please adjust rebar size or spacing to satisfy all code requirements.")

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
