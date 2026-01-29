import streamlit as st
import pandas as pd
import numpy as np
import ddm_plots 

# ========================================================
# 1. MAIN ENTRY POINT
# ========================================================
def render_dual(data_x, data_y, h_slab, d_eff, fc, fy, d_bar, w_u):
    st.markdown("## 2. Interactive Direct Design Method")
    st.info("💡 เลือกขนาดเหล็กเสริมให้ผ่านทุกหน้าตัด (Ratio <= 1.0)")

    tab_x, tab_y = st.tabs([
        f"🏗️ Design X-Direction (Span {data_x['L_span']}m)", 
        f"🏗️ Design Y-Direction (Span {data_y['L_span']}m)"
    ])
    
    with tab_x:
        render_interactive_direction(data_x, h_slab, d_eff, fc, fy, "X")
    with tab_y:
        render_interactive_direction(data_y, h_slab, d_eff, fc, fy, "Y")

# ========================================================
# 2. LOGIC & UI FOR EACH DIRECTION
# ========================================================
def render_interactive_direction(data, h_slab, d_eff, fc, fy, axis_id):
    
    # 1. Unpack Data
    L_span = data['L_span']
    L_width = data['L_width']
    c_para = data['c_para']
    Mo = data['Mo']
    m_vals = data['M_vals']
    
    w_cs = min(L_span, L_width) / 2.0
    w_ms = L_width - w_cs

    # 2. Helper: Estimate Required Steel
    def get_as_req(M_val, b_width_m):
        if b_width_m <= 0: return 0
        b_cm = b_width_m * 100
        denom = 0.9 * b_cm * d_eff**2
        if denom == 0: return 0
        
        Rn = (M_val * 100) / denom
        limit = 1 - (2*Rn)/(0.85*fc)
        
        if limit < 0: return 999.99
        
        rho = (0.85*fc/fy) * (1 - np.sqrt(limit))
        rho = max(rho, 0.0018)
        return rho * b_cm * d_eff

    req_cs_top = get_as_req(m_vals['M_cs_neg'], w_cs)
    req_cs_bot = get_as_req(m_vals['M_cs_pos'], w_cs)
    req_ms_top = get_as_req(m_vals['M_ms_neg'], w_ms)
    req_ms_bot = get_as_req(m_vals['M_ms_pos'], w_ms)

    # 3. UI Inputs (Updated Colors)
    st.markdown(f"### 🎛️ Rebar Selection: {axis_id}-Axis")
    c_info1, c_info2, c_info3 = st.columns(3)
    c_info1.metric(f"Span ($L_1$)", f"{L_span:.2f} m")
    c_info2.metric(f"Width ($L_2$)", f"{L_width:.2f} m")
    c_info3.metric(f"Moment ($M_o$)", f"{Mo:,.0f} kg-m")
    st.write("")

    col_cs, col_gap, col_ms = st.columns([1, 0.05, 1])
    
    # --- CS INPUTS (ใช้สีใหม่จาก ddm_plots) ---
    with col_cs:
        # ใช้สีพื้นหลังเดียวกับในกราฟ (CLR_ZONE_CS = #FDEDEC)
        st.markdown(
            """<div style="background-color:#FDEDEC; padding:12px; border-radius:8px; border-left: 6px solid #C0392B;">
            <strong style="color:#C0392B; font-size:1.1em;">🏛️ COLUMN STRIP</strong><br>
            <small style="color:#555;">Width = """ + f"{w_cs:.2f} m</small></div>", 
            unsafe_allow_html=True
        )
        st.write("")
        
        # CS Top
        st.markdown(f"**🟥 Top (Support)** <small style='color:#777'>(Req: {req_cs_top:.2f})</small>", unsafe_allow_html=True)
        c1, c2 = st.columns([1, 1.5])
        d_cs_t = c1.selectbox("Dia", [12,16,20,25,28], key=f"d_cst_{axis_id}")
        s_cs_t = c2.number_input("@Spacing", 5, 40, 20, 5, key=f"s_cst_{axis_id}")
        
        st.write("---")

        # CS Bot
        st.markdown(f"**🟦 Bot (Mid)** <small style='color:#777'>(Req: {req_cs_bot:.2f})</small>", unsafe_allow_html=True)
        c1, c2 = st.columns([1, 1.5])
        d_cs_b = c1.selectbox("Dia", [12,16,20,25,28], key=f"d_csb_{axis_id}")
        s_cs_b = c2.number_input("@Spacing", 5, 45, 25, 5, key=f"s_csb_{axis_id}")

    # --- MS INPUTS (ใช้สีใหม่จาก ddm_plots) ---
    with col_ms:
        # ใช้สีพื้นหลังเดียวกับในกราฟ (CLR_ZONE_MS = #EBF5FB)
        st.markdown(
            """<div style="background-color:#EBF5FB; padding:12px; border-radius:8px; border-left: 6px solid #2980B9;">
            <strong style="color:#2980B9; font-size:1.1em;">🌊 MIDDLE STRIP</strong><br>
            <small style="color:#555;">Width = """ + f"{w_ms:.2f} m</small></div>", 
            unsafe_allow_html=True
        )
        st.write("")
        
        # MS Top
        st.markdown(f"**🟥 Top (Support)** <small style='color:#777'>(Req: {req_ms_top:.2f})</small>", unsafe_allow_html=True)
        c1, c2 = st.columns([1, 1.5])
        d_ms_t = c1.selectbox("Dia", [12,16,20,25,28], key=f"d_mst_{axis_id}", index=0)
        s_ms_t = c2.number_input("@Spacing", 10, 50, 30, 5, key=f"s_mst_{axis_id}")

        st.write("---")

        # MS Bot
        st.markdown(f"**Bot (Mid)** <small style='color:#777'>(Req: {req_ms_bot:.2f})</small>", unsafe_allow_html=True)
        c1, c2 = st.columns([1, 1.5])
        d_ms_b = c1.selectbox("Dia", [12,16,20,25,28], key=f"d_msb_{axis_id}")
        s_ms_b = c2.number_input("@Spacing", 5, 45, 25, 5, key=f"s_msb_{axis_id}")

    # 4. Calculation Logic
    user_inputs = {
        "CS_Top": (d_cs_t, s_cs_t), "CS_Bot": (d_cs_b, s_cs_b),
        "MS_Top": (d_ms_t, s_ms_t), "MS_Bot": (d_ms_b, s_ms_b)
    }
    
    zones = [
        {"id": "CS_Top", "name": "Column Strip-Top", "M": m_vals["M_cs_neg"], "b": w_cs},
        {"id": "CS_Bot", "name": "Column Strip-Bot", "M": m_vals["M_cs_pos"], "b": w_cs},
        {"id": "MS_Top", "name": "Middle Strip-Top", "M": m_vals["M_ms_neg"], "b": w_ms},
        {"id": "MS_Bot", "name": "Middle Strip-Bot", "M": m_vals["M_ms_pos"], "b": w_ms},
    ]

    table_data = []
    rebar_summary = {}
    is_safe = True
    
    for z in zones:
        Mu = z['M']
        b_cm = z['b'] * 100
        d_sel, s_sel = user_inputs[z['id']]
        
        Ab = 3.1416 * (d_sel/10)**2 / 4
        As_prov = (b_cm / s_sel) * Ab
        
        a = (As_prov * fy) / (0.85 * fc * b_cm)
        Mn = As_prov * fy * (d_eff - a/2)
        PhiMn = 0.9 * Mn / 100
        
        ratio = Mu/PhiMn if PhiMn > 0 else 999
        status = "OK" if ratio <= 1.0 else "FAIL"
        if ratio > 1.0: is_safe = False
        
        rebar_str = f"DB{d_sel}@{s_sel}"
        rebar_summary[z['id']] = rebar_str
        
        # HTML Formatting (ใช้สีเข้มขึ้น)
        color = "#27AE60" if ratio <= 1.0 else "#C0392B" # Green / Red
        table_data.append({
            "Location": z['name'],
            "Mu (kg-m)": f"{Mu:,.0f}",
            "Rebar": f"<b>{rebar_str}</b>",
            "As (cm2)": f"{As_prov:.2f}",
            "PhiMn": f"{PhiMn:,.0f}",
            "Ratio": f"<span style='color:{color}'><b>{ratio:.2f}</b></span>",
            "Check": f"<span style='color:{color}'>{status}</span>"
        })

    # Show Table
    st.write("---")
    st.markdown("### 📊 Calculation Summary")
    df = pd.DataFrame(table_data)
    st.markdown(df.to_html(escape=False, index=False), unsafe_allow_html=True)
    
    if not is_safe:
        st.error("⚠️ Warning: Some sections are failing (Ratio > 1.0)")

    # 5. DRAWINGS
    st.write("---")
    st.markdown("### 🎨 Engineer Drawings")
    
    try:
        fig_mom = ddm_plots.plot_ddm_moment(L_span, c_para, m_vals)
        st.pyplot(fig_mom)
    except Exception as e:
        st.error(f"Plot Error (Moment): {e}")

    c_draw1, c_draw2 = st.columns(2)
    
    with c_draw1:
        try:
            fig_sec = ddm_plots.plot_rebar_detailing(L_span, h_slab, c_para, rebar_summary, axis_id)
            st.pyplot(fig_sec)
        except Exception as e:
            st.error(f"Plot Error (Section): {e}")
            
    with c_draw2:
        try:
            fig_plan = ddm_plots.plot_rebar_plan_view(L_span, L_width, c_para, rebar_summary, axis_id)
            st.pyplot(fig_plan)
        except Exception as e:
            st.error(f"Plot Error (Plan): {e}")
