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

        st.markdown("**Moment Distribution Coefficients:**")
        sum_neg = m_vals['M_cs_neg'] + m_vals['M_ms_neg']
        sum_pos = m_vals['M_cs_pos'] + m_vals['M_ms_pos']
        
        f_cs_neg = (m_vals['M_cs_neg'] / sum_neg * 100) if sum_neg > 0 else 0
        f_cs_pos = (m_vals['M_cs_pos'] / sum_pos * 100) if sum_pos > 0 else 0
        
        dist_data = [
            ["Negative (-)", f"CS ({f_cs_neg:.0f}%)", f"{m_vals['M_cs_neg']:,.0f}"],
            ["Negative (-)", f"MS ({100-f_cs_neg:.0f}%)", f"{m_vals['M_ms_neg']:,.0f}"],
            ["Positive (+)", f"CS ({f_cs_pos:.0f}%)", f"{m_vals['M_cs_pos']:,.0f}"],
            ["Positive (+)", f"MS ({100-f_cs_pos:.0f}%)", f"{m_vals['M_ms_pos']:,.0f}"],
        ]
        st.table(pd.DataFrame(dist_data, columns=["Zone", "% Dist.", "Moment (kg-m)"]))

    # ----------------------------------------------------
    # 🎛️ PART B: INTERACTIVE REBAR SELECTION
    # ----------------------------------------------------
    def calc_rebar_logic(M_u, b_width, d_bar, s_bar):
        b_cm = b_width * 100
        h_cm = h_slab
        d_local = h_cm - cover - (d_bar/20.0) 
        
        if M_u < 10: 
            return 0, 0, 0.1, 0, 45, True, "No Moment"

        Rn = (M_u * 100) / (0.9 * b_cm * d_local**2)
        term = 1 - (2*Rn)/(0.85*fc)
        
        if term < 0:
            rho = 999 
            As_req_final = 999
        else:
            rho = (0.85*fc/fy) * (1 - np.sqrt(term))
            As_flex = rho * b_cm * d_local
            As_min = 0.0018 * b_cm * h_cm
            As_req_final = max(As_flex, As_min)
        
        Ab = 3.1416 * (d_bar/10)**2 / 4
        As_prov = (b_cm / s_bar) * Ab
        
        # Strength Check
        a = (As_prov * fy) / (0.85 * fc * b_cm)
        PhiMn = 0.9 * As_prov * fy * (d_local - a/2) / 100
        
        s_max = min(2 * h_cm, 45)
        dc_ratio = M_u / PhiMn if PhiMn > 0 else 999
        
        is_pass = (dc_ratio <= 1.0) and (As_prov >= (0.0018 * b_cm * h_cm)) and (s_bar <= s_max)
        
        notes = []
        if rho == 999: notes.append("Section Thin")
        elif dc_ratio > 1.0: notes.append("Strength")
        if As_prov < (0.0018 * b_cm * h_cm): notes.append("Min Steel")
        if s_bar > s_max: notes.append("Spacing")
        
        return As_req_final, As_prov, PhiMn, dc_ratio, s_max, is_pass, (", ".join(notes) if notes else "-")

    st.markdown(f"### 🎛️ Reinforcement Selection")
    
    CLR_CS, CLR_MS = "#e3f2fd", "#fff3e0"
    col_cs, _, col_ms = st.columns([1, 0.05, 1])
    
    with col_cs:
        st.markdown(f"""<div style="background-color:{CLR_CS}; padding:10px; border-radius:5px; border-left:5px solid #2196f3;">
        <b>COLUMN STRIP</b> ({w_cs:.2f} m)</div>""", unsafe_allow_html=True)
        st.write("")
        d_cs_top = st.selectbox("Top DB", [12,16,20,25], index=1, key=f"dct{axis_id}")
        s_cs_top = st.number_input("Top @(cm)", 5.0, 50.0, 15.0, 2.5, key=f"sct{axis_id}")
        d_cs_bot = st.selectbox("Bot DB", [12,16,20,25], index=0, key=f"dcb{axis_id}")
        s_cs_bot = st.number_input("Bot @(cm)", 5.0, 50.0, 20.0, 2.5, key=f"scb{axis_id}")

    with col_ms:
        st.markdown(f"""<div style="background-color:{CLR_MS}; padding:10px; border-radius:5px; border-left:5px solid #ff9800;">
        <b>MIDDLE STRIP</b> ({w_ms:.2f} m)</div>""", unsafe_allow_html=True)
        st.write("")
        d_ms_top = st.selectbox("Top DB", [12,16,20,25], index=0, key=f"dmt{axis_id}")
        s_ms_top = st.number_input("Top @(cm)", 5.0, 50.0, 20.0, 2.5, key=f"smt{axis_id}")
        d_ms_bot = st.selectbox("Bot DB", [12,16,20,25], index=0, key=f"dmb{axis_id}")
        s_ms_bot = st.number_input("Bot @(cm)", 5.0, 50.0, 20.0, 2.5, key=f"smb{axis_id}")

    zones = [
        {"name": "CS-Top", "M": m_vals['M_cs_neg'], "b": w_cs, "d": d_cs_top, "s": s_cs_top},
        {"name": "CS-Bot", "M": m_vals['M_cs_pos'], "b": w_cs, "d": d_cs_bot, "s": s_cs_bot},
        {"name": "MS-Top", "M": m_vals['M_ms_neg'], "b": w_ms, "d": d_ms_top, "s": s_ms_top},
        {"name": "MS-Bot", "M": m_vals['M_ms_pos'], "b": w_ms, "d": d_ms_bot, "s": s_ms_bot},
    ]

    res_list, rebar_map, overall_safe = [], {}, True
    for z in zones:
        As_req, As_prov, PhiMn, dc, s_max, is_pass, note = calc_rebar_logic(z['M'], z['b'], z['d'], z['s'])
        if not is_pass: overall_safe = False
        
        res_list.append({
            "Location": f"<b>{z['name']}</b>",
            "Mu (kg-m)": f"{z['M']:,.0f}",
            "Req. As": f"<b>{As_req:.2f}</b>" if As_req != 999 else "FAILED",
            "Selection": f"DB{z['d']}@{z['s']:.1f}",
            "Prov. As": f"{As_prov:.2f}",
            "φMn": f"{PhiMn:,.0f}",
            "D/C": f"<b style='color:{'green' if (dc<=1.0 and is_pass) else 'red'}'>{dc:.2f}</b>",
            "Status": "✅ Pass" if is_pass else "❌ Fail",
            "Note": f"<small style='color:red'>{note}</small>"
        })
        rebar_map[z['name'].replace("-","_")] = f"DB{z['d']}@{z['s']:.1f}"

    st.write("---")
    st.markdown("### 📊 Engineering Summary Table")
    st.write(pd.DataFrame(res_list).to_html(escape=False, index=False), unsafe_allow_html=True)
    
    if not overall_safe:
        st.error("⚠️ Warning: Design does not meet all ACI 318 requirements. Please adjust rebar or thickness.")

    # ----------------------------------------------------
    # 📝 PART C: DETAILED CALCULATION VERIFICATION
    # ----------------------------------------------------
    
    with st.expander("🔎 View Sample Calculation (CS-Top)", expanded=False):
        Mu_sample = m_vals['M_cs_neg']
        b_sample_cm = w_cs * 100
        d_sample_cm = h_slab - cover - (d_cs_top/20.0) 
        Rn_val = (Mu_sample * 100) / (0.9 * b_sample_cm * d_sample_cm**2)
        
        st.markdown("#### Verification: Column Strip - Top Reinforcement")
        c_left, c_right = st.columns(2)
        with c_left:
            st.latex(f"M_u = {Mu_sample:,.0f} \\text{{ kg-m}}")
            st.latex(f"b = {b_sample_cm:.0f} \\text{{ cm}}, d = {d_sample_cm:.2f} \\text{{ cm}}")
        with c_right:
            st.latex(r"R_n = \frac{M_u}{\phi b d^2} = " + f"{Rn_val:.2f} \\text{{ ksc}}")
            st.latex(f"A_{{s,min}} = {0.0018 * b_sample_cm * h_slab:.2f} \\text{{ cm}}^2")

    # ----------------------------------------------------
    # 🖼️ PART D: DRAWINGS
    # ----------------------------------------------------
    if HAS_PLOTS:
        st.write("---")
        st.markdown("### 📐 Professional Drawings")
        try:
            st.pyplot(ddm_plots.plot_ddm_moment(L_span, c_para, m_vals))
        except Exception as e:
            st.warning(f"Plotting Error: {e}")
