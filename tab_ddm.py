def render_interactive_direction(data, h_slab, d_eff, fc, fy, axis_id):
    # --- 1. PREPARE DATA ---
    L_span = data['L_span']
    L_width = data['L_width']
    
    # Calculate Required Steel (As_req) for reference
    # (คำนวณ As_req รอไว้ก่อน เพื่อเอาไปโชว์ให้ User ดูตอนเลือกเหล็ก)
    def get_as_req(M_val, b_width):
        b_cm = b_width * 100
        rho_min = 0.0018
        # Simple estimation for UI guidance
        req = (M_val * 100) / (0.9 * fy * 0.9 * d_eff) 
        min_as = rho_min * b_cm * d_eff
        return max(req, min_as)

    w_cs = min(L_span, L_width) / 2.0
    w_ms = L_width - w_cs
    
    as_req_cs_top = get_as_req(data['M_vals']['M_cs_neg'], w_cs)
    as_req_cs_bot = get_as_req(data['M_vals']['M_cs_pos'], w_cs)
    as_req_ms_top = get_as_req(data['M_vals']['M_ms_neg'], w_ms)
    as_req_ms_bot = get_as_req(data['M_vals']['M_ms_pos'], w_ms)

    # --- 2. INTERACTIVE UI (SPATIAL LAYOUT) ---
    st.markdown("### 🎛️ ปรับแต่งเหล็กเสริม (Rebar Tuning)")
    st.caption("ปรับขนาดและระยะแอดให้เหมาะสม (สังเกตค่า As ที่ต้องการด้านขวา)")

    # สร้าง container แยกโซนชัดเจน
    c_zone1, c_gap, c_zone2 = st.columns([1, 0.1, 1])
    
    # === ZONE 1: COLUMN STRIP (LEFT) ===
    with c_zone1:
        st.markdown(
            """<div style="background-color:#fff5f5; padding:10px; border-radius:5px; border-left: 5px solid #d62728;">
            <strong style="color:#d62728;">🏛️ COLUMN STRIP (ริมเสา)</strong></div>""", 
            unsafe_allow_html=True
        )
        st.write("") # Spacer
        
        # 1.1 CS TOP
        st.markdown(f"**🟥 Top Bars (Support)** <span style='font-size:0.8em; color:gray;'>(Req: {as_req_cs_top:.2f} cm²/strip)</span>", unsafe_allow_html=True)
        c1, c2 = st.columns([1, 1.5])
        with c1: d_cs_top = st.selectbox("Dia (mm)", [12, 16, 20, 25], key=f"db_cst_{axis_id}")
        with c2: s_cs_top = st.number_input("@Spacing (cm)", 5, 40, 20, step=5, key=f"sp_cst_{axis_id}")
        
        st.write("---") # Separator
        
        # 1.2 CS BOT
        st.markdown(f"**🟦 Bot Bars (Mid-span)** <span style='font-size:0.8em; color:gray;'>(Req: {as_req_cs_bot:.2f} cm²/strip)</span>", unsafe_allow_html=True)
        c1, c2 = st.columns([1, 1.5])
        with c1: d_cs_bot = st.selectbox("Dia (mm)", [12, 16, 20, 25], key=f"db_csb_{axis_id}")
        with c2: s_cs_bot = st.number_input("@Spacing (cm)", 5, 45, 25, step=5, key=f"sp_csb_{axis_id}")

    # === ZONE 2: MIDDLE STRIP (RIGHT) ===
    with c_zone2:
        st.markdown(
            """<div style="background-color:#f0f8ff; padding:10px; border-radius:5px; border-left: 5px solid #1f77b4;">
            <strong style="color:#1f77b4;">🌊 MIDDLE STRIP (กลางพื้น)</strong></div>""", 
            unsafe_allow_html=True
        )
        st.write("") # Spacer

        # 2.1 MS TOP
        st.markdown(f"**🟥 Top Bars (Support)** <span style='font-size:0.8em; color:gray;'>(Req: {as_req_ms_top:.2f} cm²/strip)</span>", unsafe_allow_html=True)
        c1, c2 = st.columns([1, 1.5])
        with c1: d_ms_top = st.selectbox("Dia (mm)", [12, 16, 20, 25], key=f"db_mst_{axis_id}", index=0)
        with c2: s_ms_top = st.number_input("@Spacing (cm)", 10, 50, 30, step=5, key=f"sp_mst_{axis_id}")
        
        st.write("---")

        # 2.2 MS BOT
        st.markdown(f"**🟦 Bot Bars (Mid-span)** <span style='font-size:0.8em; color:gray;'>(Req: {as_req_ms_bot:.2f} cm²/strip)</span>", unsafe_allow_html=True)
        c1, c2 = st.columns([1, 1.5])
        with c1: d_ms_bot = st.selectbox("Dia (mm)", [12, 16, 20, 25], key=f"db_msb_{axis_id}")
        with c2: s_ms_bot = st.number_input("@Spacing (cm)", 5, 45, 25, step=5, key=f"sp_msb_{axis_id}")

    # --- 3. CALCULATE RESULTS & DISPLAY (ส่วนแสดงผลเหมือนเดิม) ---
    # ... (ส่วนคำนวณ calc_capacity และแสดงผลกราฟด้านล่าง Copy ของเก่ามาใส่ต่อตรงนี้ได้เลย) ...
    
    # ตัวอย่างการ Pack ข้อมูลเพื่อส่งไป plot
    rebar_summary = {
        "CS_Top": f"DB{d_cs_top}@{s_cs_top}",
        "CS_Bot": f"DB{d_cs_bot}@{s_cs_bot}",
        "MS_Top": f"DB{d_ms_top}@{s_ms_top}",
        "MS_Bot": f"DB{d_ms_bot}@{s_ms_bot}"
    }
    
    # ... Call Plots ...
    st.markdown("---")
    c_draw1, c_draw2 = st.columns(2)
    with c_draw1:
        st.pyplot(ddm_plots.plot_rebar_detailing(L_span, h_slab, data['c_para'], rebar_summary))
    with c_draw2:
        st.pyplot(ddm_plots.plot_rebar_plan_view(L_span, L_width, data['c_para'], rebar_summary))
