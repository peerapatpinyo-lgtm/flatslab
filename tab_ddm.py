import streamlit as st
import pandas as pd
import numpy as np
import ddm_plots 

def render_dual(data_x, data_y, h_slab, d_eff, fc, fy, d_bar, w_u):
    st.markdown("## 2. Interactive DDM Studio 🏗️")
    st.caption("ปรับขนาดเหล็กและระยะแอดได้ตามต้องการ ระบบจะตรวจสอบความปลอดภัยและปริมาณงานให้ทันที")
    
    tab_x, tab_y = st.tabs([
        f"➡️ Design X-Direction ({data_x['L_span']}m)", 
        f"⬆️ Design Y-Direction ({data_y['L_span']}m)"
    ])
    
    with tab_x:
        render_interactive_direction(data_x, h_slab, d_eff, fc, fy, "X")
    with tab_y:
        render_interactive_direction(data_y, h_slab, d_eff, fc, fy, "Y")

def render_interactive_direction(data, h_slab, d_eff, fc, fy, axis_id):
    # Extract Data
    L_span = data['L_span']
    L_width = data['L_width']
    c_para = data['c_para']
    ln = data['ln']
    Mo = data['Mo']
    m_vals = data['M_vals']
    
    # --- 1. Control Panel (User Inputs) ---
    st.markdown(f"### 🛠️ ปรับแต่งเหล็กเสริม (Axis {axis_id})")
    
    # เตรียมค่า Default (คำนวณเบื้องต้น)
    def get_default_spacing(M_val, width):
        # Quick estimation logic
        req_As = (M_val*100)/(0.9*fy*0.9*d_eff) 
        db_area = 1.13 # DB12 approx
        n = max(req_As/db_area, 2)
        s = min(int((width*100)/n/5)*5, 30) # Round to nearest 5cm
        return max(s, 10)

    # แบ่ง Layout เป็น 2 คอลัมน์ (ซ้าย=ปรับค่า / ขวา=ผลลัพธ์)
    col_ctrl, col_res = st.columns([1, 1.5])
    
    with col_ctrl:
        st.info("👇 **Rebar Settings:** ลองปรับค่าตรงนี้")
        
        # UI สำหรับเลือกเหล็ก (ใช้ Session State key เพื่อแยกแกน X/Y)
        # Column Strip Top
        st.markdown("**1. Column Strip (Top/Neg)**")
        d_cs_top = st.selectbox(f"Dia.", [12, 16, 20, 25], key=f"db_cs_t_{axis_id}", index=0)
        s_cs_top = st.slider(f"Spacing @ (cm)", 5, 40, 20, step=5, key=f"s_cs_t_{axis_id}")
        
        # Column Strip Bot
        st.markdown("**2. Column Strip (Bot/Pos)**")
        d_cs_bot = st.selectbox(f"Dia.", [12, 16, 20, 25], key=f"db_cs_b_{axis_id}", index=0)
        s_cs_bot = st.slider(f"Spacing @ (cm)", 5, 40, 25, step=5, key=f"s_cs_b_{axis_id}")
        
        # Middle Strip Bot
        st.markdown("**3. Middle Strip (Bot/Pos)**")
        d_ms_bot = st.selectbox(f"Dia.", [12, 16, 20, 25], key=f"db_ms_b_{axis_id}", index=0)
        s_ms_bot = st.slider(f"Spacing @ (cm)", 5, 45, 25, step=5, key=f"s_ms_b_{axis_id}")
        
        # Middle Strip Top (Optional/Min)
        st.markdown("**4. Middle Strip (Top/Neg)**")
        d_ms_top = st.selectbox(f"Dia.", [12, 16, 20, 25], key=f"db_ms_t_{axis_id}", index=0)
        s_ms_top = st.slider(f"Spacing @ (cm)", 10, 50, 30, step=5, key=f"s_ms_t_{axis_id}")

    # --- 2. Real-time Calculation ---
    # Helper เพื่อคำนวณ Capacity
    def calc_capacity(dia, spacing, b_width_m, type="Top"):
        b_cm = b_width_m * 100
        Ab = 3.1416 * (dia/10)**2 / 4
        n_bars = b_cm / spacing
        As_prov = n_bars * Ab
        
        # Phi Mn Calculation
        a = (As_prov * fy) / (0.85 * fc * b_cm)
        Mn = As_prov * fy * (d_eff - a/2)
        Phi_Mn = 0.9 * Mn / 100 # kg-m
        
        return As_prov, Phi_Mn, n_bars

    w_cs = min(L_span, L_width) / 2.0
    w_ms = L_width - w_cs
    
    # Calculate Capacities based on user input
    res_cs_top = calc_capacity(d_cs_top, s_cs_top, w_cs)
    res_cs_bot = calc_capacity(d_cs_bot, s_cs_bot, w_cs)
    res_ms_bot = calc_capacity(d_ms_bot, s_ms_bot, w_ms)
    res_ms_top = calc_capacity(d_ms_top, s_ms_top, w_ms) # Usually controlled by Min Steel

    # Mapping User Input to Results for Plotting
    rebar_summary = {
        "CS_Top": f"DB{d_cs_top}@{s_cs_top}",
        "CS_Bot": f"DB{d_cs_bot}@{s_cs_bot}",
        "MS_Bot": f"DB{d_ms_bot}@{s_ms_bot}",
        "MS_Top": f"DB{d_ms_top}@{s_ms_top}"
    }

    # --- 3. Display Results (Right Column) ---
    with col_res:
        st.markdown("### 📊 Analysis Status")
        
        # Check Safety (Compare PhiMn vs Mu)
        checks = [
            ("CS Top (-)", res_cs_top[1], m_vals['M_cs_neg']),
            ("CS Bot (+)", res_cs_bot[1], m_vals['M_cs_pos']),
            ("MS Bot (+)", res_ms_bot[1], m_vals['M_ms_pos']),
            ("MS Top (-)", res_ms_top[1], m_vals['M_ms_neg'])
        ]
        
        status_cols = st.columns(4)
        total_steel_weight = 0
        
        for i, (name, Cap, Demand) in enumerate(checks):
            ratio = Demand / Cap if Cap > 0 else 999
            is_safe = Cap >= Demand
            color = "green" if is_safe else "red"
            icon = "✅" if is_safe else "❌"
            
            with status_cols[i]:
                st.markdown(f"**{name}**")
                st.markdown(f"<span style='color:{color}; font-size:20px;'>{icon} {ratio:.2f}</span>", unsafe_allow_html=True)
                st.caption(f"Cap: {Cap:,.0f}\nReq: {Demand:,.0f}")
                
        st.markdown("---")
        
        # 4. Steel Weight Estimation (BOQ Lite)
        # Weight per meter of bar
        w_bar = lambda d: 0.00617 * d**2
        
        # Length estimation (approx)
        len_top_cs = L_span * 0.3 * 2 * res_cs_top[2] # 0.3L both sides * n_bars
        len_bot_cs = L_span * 1.0 * res_cs_bot[2]
        len_bot_ms = L_span * 1.0 * res_ms_bot[2]
        len_top_ms = L_span * 0.25 * 2 * res_ms_top[2] # Min bars at support
        
        total_w = (len_top_cs * w_bar(d_cs_top)) + \
                  (len_bot_cs * w_bar(d_cs_bot)) + \
                  (len_bot_ms * w_bar(d_ms_bot)) + \
                  (len_top_ms * w_bar(d_ms_top))
                  
        steel_density = total_w / (L_span * L_width)
        
        st.metric("🏗️ Est. Steel Weight", f"{total_w:.1f} kg", delta=f"{steel_density:.2f} kg/m²")
        if steel_density > 15:
            st.warning("⚠️ ปริมาณเหล็กค่อนข้างสูง (>15 kg/m²) ลองเพิ่มความหนาพื้นหรือลดขนาดเหล็ก")
        elif steel_density < 8:
             st.success("💰 ประหยัดมาก (High Economy)")

    # --- 5. Professional Drawings ---
    st.markdown("---")
    st.subheader("blueprint & Details")
    
    # ใช้ฟังก์ชันเดิมวาดรูป แต่ข้อมูลมาจาก User Selection
    c1, c2 = st.columns(2)
    with c1:
        # Pass override 'fail' status if any check failed? 
        # For interactive, we show drawing anyway but maybe with warning
        fig_side = ddm_plots.plot_rebar_detailing(L_span, h_slab, c_para, rebar_summary)
        st.pyplot(fig_side)
    with c2:
        fig_top = ddm_plots.plot_rebar_plan_view(L_span, L_width, c_para, rebar_summary)
        st.pyplot(fig_top)
