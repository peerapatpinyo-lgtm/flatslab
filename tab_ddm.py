import streamlit as st
import pandas as pd
import numpy as np
import ddm_plots 

# ========================================================
# 1. MAIN ENTRY POINT
# ========================================================
def render_dual(data_x, data_y, h_slab, d_eff, fc, fy, d_bar, w_u):
    st.markdown("## 2. Interactive Direct Design Method")
    st.info("💡 **Professional Mode:** กราฟิกแสดงผลตามมาตรฐานวิศวกรรม (แยกชั้นเหล็ก, แสดงจุดตัดสมจริง)")

    tab_x, tab_y = st.tabs([
        f"🏗️ Design X-Dir ({data_x['L_span']}m)", 
        f"🏗️ Design Y-Dir ({data_y['L_span']}m)"
    ])
    
    with tab_x:
        render_interactive_direction(data_x, h_slab, d_eff, fc, fy, "X")
    with tab_y:
        render_interactive_direction(data_y, h_slab, d_eff, fc, fy, "Y")

# ========================================================
# 2. LOGIC & UI
# ========================================================
def render_interactive_direction(data, h_slab, d_eff, fc, fy, axis_id):
    # Unpack Data
    L_span = data['L_span']
    L_width = data['L_width']
    c_para = data['c_para']
    Mo = data['Mo']
    m_vals = data['M_vals']
    
    w_cs = min(L_span, L_width) / 2.0
    w_ms = L_width - w_cs

    # Helper: Estimate Req Area
    def get_as_req(M_val, b_width_m):
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

    # UI Inputs (Using professional color codes from plotting file)
    c_red = ddm_plots.CLR_BAR_TOP
    c_blue = ddm_plots.CLR_BAR_BOT
    bg_cs = ddm_plots.CLR_ZONE_CS
    bg_ms = ddm_plots.CLR_ZONE_MS

    st.markdown(f"### 🎛️ Parameters: {axis_id}-Axis")
    c1, c2, c3 = st.columns(3)
    c1.metric("Span $L_1$", f"{L_span:.2f} m")
    c2.metric("Width $L_2$", f"{L_width:.2f} m")
    c3.metric("Moment $M_o$", f"{Mo:,.0f} kg-m")
    
    col_cs, col_gap, col_ms = st.columns([1, 0.05, 1])
    
    # === Column Strip Inputs ===
    with col_cs:
        st.markdown(
            f"""<div style="background-color:{bg_cs}; padding:12px; border-radius:6px; border-left: 5px solid {c_red}; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
            <b style="color:{c_red}; font-size:1.1em;">🏛️ COLUMN STRIP</b><br><small style="color:#666">Width = {w_cs:.2f} m</small></div>""", unsafe_allow_html=True
        )
        st.write("")
        st.markdown(f"**<span style='color:{c_red}'>🟥 Top (Support)</span>** <small style='color:#888'>(Req: {req_cs_top:.2f})</small>", unsafe_allow_html=True)
        c_a, c_b = st.columns([1,1.5])
        d_cs_top = c_a.selectbox("Dia", [12,16,20,25], key=f"dct{axis_id}")
        s_cs_top = c_b.number_input("@Spacing", 5, 50, 20, 5, key=f"sct{axis_id}")
        
        st.markdown(f"**<span style='color:{c_blue}'>🟦 Bot (Mid-span)</span>** <small style='color:#888'>(Req: {req_cs_bot:.2f})</small>", unsafe_allow_html=True)
        c_a, c_b = st.columns([1,1.5])
        d_cs_bot = c_a.selectbox("Dia", [12,16,20,25], key=f"dcb{axis_id}")
        s_cs_bot = c_b.number_input("@Spacing", 5, 50, 25, 5, key=f"scb{axis_id}")

    # === Middle Strip Inputs ===
    with col_ms:
        st.markdown(
            f"""<div style="background-color:{bg_ms}; padding:12px; border-radius:6px; border-left: 5px solid {c_blue}; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
            <b style="color:{c_blue}; font-size:1.1em;">🌊 MIDDLE STRIP</b><br><small style="color:#666">Width = {w_ms:.2f} m</small></div>""", unsafe_allow_html=True
        )
        st.write("")
        st.markdown(f"**<span style='color:{c_red}'>🟥 Top (Support)</span>** <small style='color:#888'>(Req: {req_ms_top:.2f})</small>", unsafe_allow_html=True)
        c_a, c_b = st.columns([1,1.5])
        d_ms_top = c_a.selectbox("Dia", [12,16,20,25], key=f"dmt{axis_id}", index=0)
        s_ms_top = c_b.number_input("@Spacing", 10, 50, 30, 5, key=f"smt{axis_id}")

        st.markdown(f"**<span style='color:{c_blue}'>🟦 Bot (Mid-span)</span>** <small style='color:#888'>(Req: {req_ms_bot:.2f})</small>", unsafe_allow_html=True)
        c_a, c_b = st.columns([1,1.5])
        d_ms_bot = c_a.selectbox("Dia", [12,16,20,25], key=f"dmb{axis_id}")
        s_ms_bot = c_b.number_input("@Spacing", 5, 50, 25, 5, key=f"smb{axis_id}")

    # Calculate & Table
    inputs = {
        "CS_Top": (d_cs_top, s_cs_top), "CS_Bot": (d_cs_bot, s_cs_bot),
        "MS_Top": (d_ms_top, s_ms_top), "MS_Bot": (d_ms_bot, s_ms_bot)
    }
    zones = [
        {"id": "CS_Top", "n": "Col Strip-Top", "M": m_vals["M_cs_neg"], "b": w_cs},
        {"id": "CS_Bot", "n": "Col Strip-Bot", "M": m_vals["M_cs_pos"], "b": w_cs},
        {"id": "MS_Top", "n": "Mid Strip-Top", "M": m_vals["M_ms_neg"], "b": w_ms},
        {"id": "MS_Bot", "n": "Mid Strip-Bot", "M": m_vals["M_ms_pos"], "b": w_ms},
    ]

    res_list = []
    rebar_map = {}
    is_safe = True
    
    for z in zones:
        Mu = z['M']
        b_cm = z['b'] * 100
        d_sel, s_sel = inputs[z['id']]
        
        Ab = 3.1416*(d_sel/10)**2/4
        As = (b_cm/s_sel)*Ab
        a = (As*fy)/(0.85*fc*b_cm)
        PhiMn = 0.9 * As * fy * (d_eff - a/2) / 100
        
        ratio = Mu/PhiMn if PhiMn>0 else 999
        if ratio > 1.0: is_safe = False
        
        # Professional HTML Table styling
        status_color = "#28a745" if ratio<=1 else "#dc3545"
        status_icon = "✅" if ratio<=1 else "❌"
        
        res_list.append({
            "Zone": f"<b>{z['n']}</b>",
            "Mu <br><small>(kg-m)</small>": f"{Mu:,.0f}", 
            "Rebar Selected": f"<b style='color:{c_red if 'Top' in z['id'] else c_blue}'>DB{d_sel}@{s_sel}</b>",
            "As Prov <br><small>(cm²)</small>": f"{As:.2f}",
            "φMn <br><small>(kg-m)</small>": f"{PhiMn:,.0f}",
            "D/C Ratio": f"<b style='color:{status_color}'>{ratio:.2f}</b>",
            "Status": f"{status_icon}"
        })
        rebar_map[z['id']] = f"DB{d_sel}@{s_sel}"

    st.write("---")
    st.markdown("### 📊 Engineering Analysis Summary")
    
    # Use Styler for better table look
    df = pd.DataFrame(res_list)
    st.write(df.style.format(precision=2).to_html(escape=False, index=False), unsafe_allow_html=True)

    if not is_safe:
        st.warning("⚠️ **Action Required:** Some sections have D/C Ratio > 1.0. Please increase rebar size or reduce spacing.")

    # PLOTS
    st.write("---")
    st.markdown("### 📐 Professional Engineering Drawings")
    
    try:
        st.pyplot(ddm_plots.plot_ddm_moment(L_span, c_para, m_vals))
    except Exception as e: st.error(f"Moment Plot Error: {e}")
    
    c1, c2 = st.columns(2)
    with c1:
        try:
            st.pyplot(ddm_plots.plot_rebar_detailing(L_span, h_slab, c_para, rebar_map, axis_id))
        except Exception as e: st.error(f"Section Plot Error: {e}")
    with c2:
        try:
            st.pyplot(ddm_plots.plot_rebar_plan_view(L_span, L_width, c_para, rebar_map, axis_id))
        except Exception as e: st.error(f"Plan Plot Error: {e}")
