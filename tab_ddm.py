#tab_ddm.py
import streamlit as st
import pandas as pd
import numpy as np
# Try import plots, if not exists, skip gracefully
try:
    import ddm_plots 
    HAS_PLOTS = True
except ImportError:
    HAS_PLOTS = False

# ========================================================
# 1. MAIN ENTRY POINT
# ========================================================
def render_dual(data_x, data_y, mat_props, w_u):
    """
    Main function called from app.py
    Unpacks material properties and renders tabs
    """
    # Unpack Material Props for general usage
    h_slab = mat_props['h_slab']
    fc = mat_props['fc']
    fy = mat_props['fy']
    cover = mat_props['cover']
    
    st.markdown("## 2. Interactive Direct Design Method")
    st.info("💡 **Design Mode:** Complete analysis (ACI 318 / EIT Standards).")

    tab_x, tab_y = st.tabs([
        f"↔️ Design X-Dir ({data_x['L_span']}m)", 
        f"↕️ Design Y-Dir ({data_y['L_span']}m)"
    ])
    
    with tab_x:
        render_interactive_direction(data_x, h_slab, cover, fc, fy, "X", w_u)
    with tab_y:
        render_interactive_direction(data_y, h_slab, cover, fc, fy, "Y", w_u)

# ========================================================
# 2. CALCULATION & UI
# ========================================================
def render_interactive_direction(data, h_slab, cover, fc, fy, axis_id, w_u):
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
    # 📝 PART A: GEOMETRY & MOMENT DISTRIBUTION
    # ----------------------------------------------------
    st.markdown(f"### 📐 Design Parameters: {axis_id}-Direction")
    
    with st.expander("Show Geometry & Moment Distribution Factors", expanded=False):
        # 1. Geometry
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Span ($L_1$)", f"{L_span:.2f} m")
            st.metric("Width ($L_2$)", f"{L_width:.2f} m")
        with c2:
            st.metric("Column ($c_1$)", f"{c_para/100:.2f} m")
            st.metric("Clear Span ($l_n$)", f"{Ln:.2f} m")
        with c3:
            st.metric("Factored Load ($w_u$)", f"{w_u:,.0f} kg/m²")
        
        st.markdown("**Total Static Moment ($M_o$):**")
        st.latex(f"M_o = \\frac{{{w_u:,.0f} \\times {L_width:.2f} \\times {Ln:.2f}^2}}{{8}} = \\mathbf{{{Mo:,.0f}}} \\; \\text{{kg-m}}")

        # 2. Distribution Table
        st.markdown("**Moment Distribution Coefficients:**")
        sum_neg = m_vals['M_cs_neg'] + m_vals['M_ms_neg']
        sum_pos = m_vals['M_cs_pos'] + m_vals['M_ms_pos']
        
        f_cs_neg = m_vals['M_cs_neg'] / sum_neg if sum_neg > 0 else 0
        f_cs_pos = m_vals['M_cs_pos'] / sum_pos if sum_pos > 0 else 0
        
        dist_data = [
            ["Negative (-)", f"CS ({f_cs_neg*100:.0f}%)", f"{m_vals['M_cs_neg']:,.0f}"],
            ["Negative (-)", f"MS ({100-f_cs_neg*100:.0f}%)", f"{m_vals['M_ms_neg']:,.0f}"],
            ["Positive (+)", f"CS ({f_cs_pos*100:.0f}%)", f"{m_vals['M_cs_pos']:,.0f}"],
            ["Positive (+)", f"MS ({100-f_cs_pos*100:.0f}%)", f"{m_vals['M_ms_pos']:,.0f}"],
        ]
        st.table(pd.DataFrame(dist_data, columns=["Zone", "% Dist.", "Moment (kg-m)"]))

    # ----------------------------------------------------
    # 🎛️ PART B: INTERACTIVE REBAR SELECTION
    # ----------------------------------------------------
    
    # Internal Logic for this Tab
    def calc_rebar_logic(M_u, b_width, d_bar, s_bar):
        b_cm = b_width * 100
        h_cm = h_slab
        # Exact d calculation based on selection
        d_local = h_cm - cover - (d_bar/20.0) 
        
        # 1. As Required
        if M_u < 100: 
            return 0, 0, 0, 0, 45, True, "No Moment"

        Rn = (M_u * 100) / (0.9 * b_cm * d_local**2)
        term = 1 - (2*Rn)/(0.85*fc)
        
        if term < 0: 
            rho = 999 
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
        
        notes = []
        if not pass_str: notes.append("Strength")
        if not pass_min: notes.append("Min Steel")
        if not pass_space: notes.append("Spacing")
        note_str = ", ".join(notes) if notes else "-"
        
        return As_req_final, As_prov, PhiMn, dc_ratio, s_max, is_pass, note_str

    # --- UI Inputs ---
    st.markdown(f"### 🎛️ Reinforcement Selection")
    
    # Define Colors if not using ddm_plots constants
    CLR_CS = "#e3f2fd"
    CLR_MS = "#fff3e0"
    
    col_cs, col_gap, col_ms = st.columns([1, 0.05, 1])
    
    # === CS INPUTS ===
    with col_cs:
        st.markdown(f"""<div style="background-color:{CLR_CS}; padding:10px; border-radius:5px; border-left:5px solid #2196f3;">
        <b>COLUMN STRIP</b> ({w_cs:.2f} m)</div>""", unsafe_allow_html=True)
        st.write("")
        c1, c2 = st.columns([1, 1.5])
        d_cs_top = c1.selectbox("Top DB", [12,16,20,25], key=f"dct{axis_id}")
        s_cs_top = c2.number_input("Top @(cm)", 5.0, 50.0, 20.0, 2.5, key=f"sct{axis_id}")
        c1, c2 = st.columns([1, 1.5])
        d_cs_bot = c1.selectbox("Bot DB", [12,16,20,25], key=f"dcb{axis_id}")
        s_cs_bot = c2.number_input("Bot @(cm)", 5.0, 50.0, 25.0, 2.5, key=f"scb{axis_id}")

    # === MS INPUTS ===
    with col_ms:
        st.markdown(f"""<div style="background-color:{CLR_MS}; padding:10px; border-radius:5px; border-left:5px solid #ff9800;">
        <b>MIDDLE STRIP</b> ({w_ms:.2f} m)</div>""", unsafe_allow_html=True)
        st.write("")
        c1, c2 = st.columns([1, 1.5])
        d_ms_top = c1.selectbox("Top DB", [12,16,20,25], index=0, key=f"dmt{axis_id}")
        s_ms_top = c2.number_input("Top @(cm)", 5.0, 50.0, 30.0, 2.5, key=f"smt{axis_id}")
        c1, c2 = st.columns([1, 1.5])
        d_ms_bot = c1.selectbox("Bot DB", [12,16,20,25], key=f"dmb{axis_id}")
        s_ms_bot = c2.number_input("Bot @(cm)", 5.0, 50.0, 25.0, 2.5, key=f"smb{axis_id}")

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
        As_req, As_prov, PhiMn, dc, s_max, is_pass, note = calc_rebar_logic(z['M'], z['b'], z['d'], z['s'])
        if not is_pass: overall_safe = False
        
        status_icon = "✅ Pass" if is_pass else "❌ Fail"
        res_list.append({
            "Location": f"<b>{z['name']}</b>",
            "Mu (kg-m)": f"{z['M']:,.0f}",
            "Req. As": f"<b>{As_req:.2f}</b>",
            "Selection": f"DB{z['d']}@{z['s']:.0f}",
            "Prov. As": f"{As_prov:.2f}",
            "φMn": f"{PhiMn:,.0f}",
            "D/C": f"<b style='color:{'green' if dc<=1 else 'red'}'>{dc:.2f}</b>",
            "Status": f"<b>{status_icon}</b>",
            "Note": f"<small style='color:red'>{note}</small>"
        })
        rebar_map[z['name'].replace("-","_")] = f"DB{z['d']}@{z['s']:.0f}"

    # Render Table
    st.write("---")
    st.markdown("### 📊 Engineering Summary Table")
    df_res = pd.DataFrame(res_list)
    st.write(df_res.style.format(precision=2).to_html(escape=False, index=False), unsafe_allow_html=True)
    
    if not overall_safe:
        st.error("⚠️ Warning: Design does not meet all ACI 318 requirements.")

    # ----------------------------------------------------
    # 📝 PART C: DETAILED CALCULATION VERIFICATION
    # ----------------------------------------------------
    with st.expander("🔎 View Sample Calculation (รายการคำนวณออกแบบอย่างละเอียด)", expanded=True):
        st.markdown("#### 3. Verification: Column Strip - Top Reinforcement")
        
        # Define Variables for Sample (CS-Top)
        Mu_sample = m_vals['M_cs_neg']
        b_sample_cm = w_cs * 100
        d_sample_cm = h_slab - cover - (d_cs_top/20.0) 
        
        # Recalculate just for display
        Rn_val = (Mu_sample * 100) / (0.9 * b_sample_cm * d_sample_cm**2)
        term = 1 - (2 * Rn_val) / (0.85 * fc)
        rho_val = (0.85 * fc / fy) * (1 - np.sqrt(term)) if term >=0 else 0
        As_req_val = rho_val * b_sample_cm * d_sample_cm
        As_min_val = 0.0018 * b_sample_cm * h_slab
        
        c_left, c_right = st.columns([1, 1.2])
        
        with c_left:
            st.markdown("**Design Parameters:**")
            st.latex(f"M_u = {Mu_sample:,.0f} \\; \\text{{kg-m}}")
            st.latex(f"b = {w_cs:.2f} \\text{{ m}} = {b_sample_cm:.0f} \\text{{ cm}}")
            st.latex(f"d = {d_sample_cm:.2f} \\text{{ cm}}")
            
        with c_right:
            st.markdown("**Calculation Steps:**")
            st.latex(r"R_n = \frac{M_u}{0.9 b d^2} = " + f"{Rn_val:.2f} \\text{{ ksc}}")
            st.latex(f"\\rho_{{req}} = {rho_val:.5f}")
            st.latex(f"A_{{s,req}} = {As_req_val:.2f} \\text{{ cm}}^2, \\; A_{{s,min}} = {As_min_val:.2f} \\text{{ cm}}^2")

    # ----------------------------------------------------
    # 🖼️ PART D: DRAWINGS (Safe Mode)
    # ----------------------------------------------------
    st.write("---")
    st.markdown("### 📐 Professional Drawings")
    
    if HAS_PLOTS:
        try:
            st.pyplot(ddm_plots.plot_ddm_moment(L_span, c_para, m_vals))
            c1, c2 = st.columns(2)
            with c1: st.pyplot(ddm_plots.plot_rebar_detailing(L_span, h_slab, c_para, rebar_map, axis_id))
            with c2: st.pyplot(ddm_plots.plot_rebar_plan_view(L_span, L_width, c_para, rebar_map, axis_id))
        except Exception as e:
            st.warning(f"Plotting Error: {e}")
    else:
        st.info("ℹ️ `ddm_plots.py` not found or drawing module disabled. (Focus on Calc)")
