import streamlit as st
import pandas as pd
import numpy as np
import ddm_plots 

def render_dual(data_x, data_y, h_slab, d_eff, fc, fy, d_bar, w_u):
    st.markdown("## 2. Direct Design Method (Detailed Report)")
    st.info("💡 รายงานการคำนวณแบบละเอียด พร้อมรูปประกอบการเสริมเหล็ก")

    tab_x, tab_y = st.tabs([
        f"📄 Design X-Direction ({data_x['L_span']}m)", 
        f"📄 Design Y-Direction ({data_y['L_span']}m)"
    ])
    
    with tab_x:
        render_detailed_direction(data_x, h_slab, d_eff, fc, fy, d_bar, w_u)
    with tab_y:
        render_detailed_direction(data_y, h_slab, d_eff, fc, fy, d_bar, w_u)

def render_detailed_direction(data, h_slab, d_eff, fc, fy, d_bar, w_u):
    # --- 1. PREPARE DATA ---
    L_span = data['L_span']
    L_width = data['L_width']
    c_para = data['c_para']
    ln = data['ln']
    Mo = data['Mo']
    m_vals = data['M_vals']
    dir_name = data['dir']

    # --- 2. HEADER & PARAMETERS ---
    st.markdown(f"### 📐 Analysis: {dir_name}-Direction")
    
    # แสดง Parameter แบบ Metric สวยๆ
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Span Length ($L_1$)", f"{L_span:.2f} m")
    c2.metric("Width ($L_2$)", f"{L_width:.2f} m")
    c3.metric("Clear Span ($l_n$)", f"{ln:.3f} m")
    c4.metric("Static Moment ($M_o$)", f"{Mo:,.0f} kg-m")
    
    # แสดงวิธีทำ Mo
    with st.expander("🔎 ดูวิธีทำ $M_o$ (Click to expand)"):
        st.latex(r"M_o = \frac{w_u \cdot L_{2} \cdot l_n^2}{8} = \frac{" + f"{w_u:,.0f} \\cdot {L_width:.2f} \\cdot {ln:.3f}^2" + r"}{8}")
        st.write(f"**Result:** $M_o = {Mo:,.0f}$ kg-m")

    st.markdown("---")

    # --- 3. REINFORCEMENT DESIGN (DETAILED TABLE) ---
    st.markdown("### 🧱 Reinforcement Calculation")
    
    w_cs = min(L_span, L_width) / 2.0
    w_ms = L_width - w_cs
    
    zones = [
        {"id": "CS_Top", "name": "Column Strip - Top (Neg)", "M": m_vals["M_cs_neg"], "b": w_cs, "type": "Top"},
        {"id": "CS_Bot", "name": "Column Strip - Bot (Pos)", "M": m_vals["M_cs_pos"], "b": w_cs, "type": "Bot"},
        {"id": "MS_Top", "name": "Middle Strip - Top (Neg)", "M": m_vals["M_ms_neg"], "b": w_ms, "type": "Top"},
        {"id": "MS_Bot", "name": "Middle Strip - Bot (Pos)", "M": m_vals["M_ms_pos"], "b": w_ms, "type": "Bot"},
    ]
    
    rebar_summary = {} # เก็บค่าไว้ส่งให้กราฟวาด
    table_rows = []

    for z in zones:
        Mu = z['M']            # kg-m
        Mu_kgcm = Mu * 100     # kg-cm
        b_cm = z['b'] * 100    # cm
        
        # 3.1 Calculate Rn
        phi = 0.9
        denom = phi * b_cm * (d_eff**2)
        Rn = Mu_kgcm / denom if denom > 0 else 0
        
        # 3.2 Calculate Rho
        # Check limit
        limit_term = 1 - (2*Rn)/(0.85*fc)
        status = "OK"
        
        if limit_term < 0:
            rho_des = 0
            As_req = 0
            select_str = "FAIL (Deep)"
            rebar_summary[z['id']] = "FAIL"
            status = "FAIL"
        else:
            rho_req = (0.85*fc/fy) * (1 - np.sqrt(limit_term))
            rho_min = 0.0018
            rho_des = max(rho_req, rho_min)
            
            # 3.3 As Required
            As_req = rho_des * b_cm * d_eff
            
            # 3.4 Select Bars
            Ab = 3.14159 * (d_bar/10)**2 / 4
            n_bars = max(np.ceil(As_req/Ab), 2) # Min 2 bars
            
            # Spacing check
            s_calc = b_cm / n_bars
            s_final = min(s_calc, 2*h_slab, 45) # Max spacing
            
            # Formatted String
            s_show = int(s_final // 5) * 5 # Round down to nearest 5
            if s_show < 5: s_show = 5
            
            # ถ้าเป็น MS Top เหล็กน้อยมากมักใส่ Min Steel
            select_str = f"{int(n_bars)}-DB{d_bar}@{s_show}c"
            rebar_summary[z['id']] = select_str
        
        # Add to table data
        table_rows.append({
            "Zone": z['name'],
            "Mu (kg-m)": f"{Mu:,.0f}",
            "Width (m)": f"{z['b']:.2f}",
            "Rn (ksc)": f"{Rn:.2f}",
            "Rho Req": f"{rho_req:.5f}" if limit_term > 0 else "N/A",
            "As Req (cm2)": f"{As_req:.2f}",
            "Selected Design": f"**{select_str}**"
        })

    # Display Table
    df_res = pd.DataFrame(table_rows)
    
    # --- FIX: เปลี่ยนจาก .to_markdown() เป็น st.table() หรือ .to_html() ---
    # st.table(df_res) # แบบธรรมดา
    # หรือแบบ HTML เพื่อให้แสดงตัวหนา (**text**) ได้ถูกต้อง
    st.markdown(df_res.to_html(escape=False, index=False), unsafe_allow_html=True)
    
    st.caption(f"*Note: Design based on d = {d_eff} cm, fc' = {fc} ksc, fy = {fy} ksc*")

    st.markdown("---")

    # --- 4. DRAWINGS (VISUALIZATION) ---
    st.markdown("### 🎨 Engineering Drawings")
    
    # 4.1 Moment Diagram
    st.markdown("**1. Moment Distribution Diagram**")
    fig_mom = ddm_plots.plot_ddm_moment(L_span, c_para, m_vals)
    st.pyplot(fig_mom)
    
    # 4.2 Rebar Drawings
    if "FAIL" not in rebar_summary.values():
        st.markdown("**2. Reinforcement Detailing**")
        c_draw1, c_draw2 = st.columns(2)
        
        with c_draw1:
            st.markdown("*(A) Section Profile*")
            fig_side = ddm_plots.plot_rebar_detailing(L_span, h_slab, c_para, rebar_summary)
            st.pyplot(fig_side)
            
        with c_draw2:
            st.markdown("*(B) Plan View Layout*")
            fig_top = ddm_plots.plot_rebar_plan_view(L_span, L_width, c_para, rebar_summary)
            st.pyplot(fig_top)
    else:
        st.error("❌ Cannot generate drawings because section failed (Check calculation above).")
