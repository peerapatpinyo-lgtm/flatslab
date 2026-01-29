import streamlit as st
import pandas as pd
import numpy as np
import ddm_plots 

# ========================================================
# 1. ENTRY POINT
# ========================================================
def render_dual(data_x, data_y, h_slab, d_eff, fc, fy, d_bar, w_u):
    st.markdown("## 2. Interactive Direct Design Method")
    st.info("💡 **Tips:** ปรับเหล็กเสริมด้านล่าง กราฟิกจะแสดงตำแหน่งเหล็กบน(แดง) และเหล็กล่าง(น้ำเงิน) แยกกันชัดเจน")

    tab_x, tab_y = st.tabs([
        f"🏗️ Design X-Direction ({data_x['L_span']}m)", 
        f"🏗️ Design Y-Direction ({data_y['L_span']}m)"
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

    # UI Inputs
    st.markdown(f"### 🎛️ Parameters: {axis_id}-Axis")
    c1, c2, c3 = st.columns(3)
    c1.metric("Span L1", f"{L_span:.2f} m")
    c2.metric("Width L2", f"{L_width:.2f} m")
    c3.metric("Moment Mo", f"{Mo:,.0f} kg-m")
    
    col_cs, col_gap, col_ms = st.columns([1, 0.05, 1])
    
    # === Column Strip Inputs ===
    with col_cs:
        st.markdown(
            f"""<div style="background-color:#FFF5F5; padding:10px; border-radius:5px; border-left: 5px solid #C53030;">
            <b style="color:#C53030">🏛️ COLUMN STRIP (w={w_cs:.2f}m)</b></div>""", unsafe_allow_html=True
        )
        st.write("")
        st.markdown(f"**Top (Sup)** <small style='color:gray'>Req: {req_cs_top:.2f}</small>", unsafe_allow_html=True)
        c_a, c_b = st.columns([1,1.5])
        d_cs_top = c_a.selectbox("Dia", [12,16,20,25], key=f"dct{axis_id}")
        s_cs_top = c_b.number_input("@Spacing", 5, 40, 20, 5, key=f"sct{axis_id}")
        
        st.markdown(f"**Bot (Mid)** <small style='color:gray'>Req: {req_cs_bot:.2f}</small>", unsafe_allow_html=True)
        c_a, c_b = st.columns([1,1.5])
        d_cs_bot = c_a.selectbox("Dia", [12,16,20,25], key=f"dcb{axis_id}")
        s_cs_bot = c_b.number_input("@Spacing", 5, 40, 25, 5, key=f"scb{axis_id}")

    # === Middle Strip Inputs ===
    with col_ms:
        st.markdown(
            f"""<div style="background-color:#EBF8FF; padding:10px; border-radius:5px; border-left: 5px solid #2B6CB0;">
            <b style="color:#2B6CB0">🌊 MIDDLE STRIP (w={w_ms:.2f}m)</b></div>""", unsafe_allow_html=True
        )
        st.write("")
        st.markdown(f"**Top (Sup)** <small style='color:gray'>Req: {req_ms_top:.2f}</small>", unsafe_allow_html=True)
        c_a, c_b = st.columns([1,1.5])
        d_ms_top = c_a.selectbox("Dia", [12,16,20,25], key=f"dmt{axis_id}")
        s_ms_top = c_b.number_input("@Spacing", 10, 50, 30, 5, key=f"smt{axis_id}")

        st.markdown(f"**Bot (Mid)** <small style='color:gray'>Req: {req_ms_bot:.2f}</small>", unsafe_allow_html=True)
        c_a, c_b = st.columns([1,1.5])
        d_ms_bot = c_a.selectbox("Dia", [12,16,20,25], key=f"dmb{axis_id}")
        s_ms_bot = c_b.number_input("@Spacing", 5, 40, 25, 5, key=f"smb{axis_id}")

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
    
    for z in zones:
        Mu = z['M']
        b_cm = z['b'] * 100
        d_sel, s_sel = inputs[z['id']]
        
        Ab = 3.1416*(d_sel/10)**2/4
        As = (b_cm/s_sel)*Ab
        a = (As*fy)/(0.85*fc*b_cm)
        PhiMn = 0.9 * As * fy * (d_eff - a/2) / 100
        
        ratio = Mu/PhiMn if PhiMn>0 else 999
        res_list.append({
            "Zone": z['n'], "Mu": f"{Mu:,.0f}", 
            "Design": f"<b>DB{d_sel}@{s_sel}</b>",
            "PhiMn": f"{PhiMn:,.0f}",
            "Ratio": f"<b style='color:{'green' if ratio<=1 else 'red'}'>{ratio:.2f}</b>"
        })
        rebar_map[z['id']] = f"DB{d_sel}@{s_sel}"

    st.write("---")
    st.markdown("### 📊 Check Capacity")
    st.markdown(pd.DataFrame(res_list).to_html(escape=False, index=False), unsafe_allow_html=True)
    
    # PLOTS
    st.write("---")
    st.markdown("### 📐 Engineering Drawings")
    
    try:
        st.pyplot(ddm_plots.plot_ddm_moment(L_span, c_para, m_vals))
    except: pass
    
    c1, c2 = st.columns(2)
    with c1:
        try:
            st.pyplot(ddm_plots.plot_rebar_detailing(L_span, h_slab, c_para, rebar_map, axis_id))
        except Exception as e: st.error(f"Sec Error: {e}")
    with c2:
        try:
            st.pyplot(ddm_plots.plot_rebar_plan_view(L_span, L_width, c_para, rebar_map, axis_id))
        except Exception as e: st.error(f"Plan Error: {e}")
