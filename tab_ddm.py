import streamlit as st
import pandas as pd
import numpy as np
import ddm_plots 

# ========================================================
# 1. ENTRY POINT (MAIN FUNCTION)
# ========================================================
def render_dual(data_x, data_y, h_slab, d_eff, fc, fy, d_bar, w_u):
    st.markdown("## 2. Interactive Direct Design Method")
    st.info("💡 ปรับเลือกเหล็กเสริมด้านล่าง ผลลัพธ์และรายการคำนวณจะอัปเดตอัตโนมัติ")

    # สร้าง Tab แยกทิศทาง X และ Y
    tab_x, tab_y = st.tabs([
        f"🏗️ Design X-Direction ({data_x['L_span']}m)", 
        f"🏗️ Design Y-Direction ({data_y['L_span']}m)"
    ])
    
    with tab_x:
        render_interactive_direction(data_x, h_slab, d_eff, fc, fy, "X")
    with tab_y:
        render_interactive_direction(data_y, h_slab, d_eff, fc, fy, "Y")

# ========================================================
# 2. LOGIC & UI FOR EACH DIRECTION
# ========================================================
def render_interactive_direction(data, h_slab, d_eff, fc, fy, axis_id):
    # --- 1. PREPARE DATA ---
    L_span = data['L_span']
    L_width = data['L_width']
    c_para = data['c_para']
    Mo = data['Mo']
    m_vals = data['M_vals']
    
    # ความกว้างแถบ (Column Strip / Middle Strip)
    w_cs = min(L_span, L_width) / 2.0
    w_ms = L_width - w_cs

    # --- 2. HELPER: Estimate Required Steel (For UI Guidance) ---
    def get_as_req(M_val, b_width_m):
        b_cm = b_width_m * 100
        denom = 0.9 * b_cm * d_eff**2
        if denom == 0: return 0
        
        Rn = (M_val * 100) / denom
        limit_check = 1 - (2*Rn)/(0.85*fc)
        
        if limit_check < 0: return 999 # Fail (Section too deep)
        
        rho = (0.85*fc/fy) * (1 - np.sqrt(limit_check))
        rho = max(rho, 0.0018) # Minimum steel check
        return rho * b_cm * d_eff

    # คำนวณเหล็กที่ต้องการเบื้องต้นเพื่อโชว์ใน UI
    req_cs_top = get_as_req(m_vals['M_cs_neg'], w_cs)
    req_cs_bot = get_as_req(m_vals['M_cs_pos'], w_cs)
    req_ms_top = get_as_req(m_vals['M_ms_neg'], w_ms)
    req_ms_bot = get_as_req(m_vals['M_ms_pos'], w_ms)

    # --- 3. UI SECTION (SPATIAL LAYOUT) ---
    st.markdown(f"### 🎛️ Parameters & Rebar Selection ({axis_id}-Direction)")
    
    # แสดงค่าพารามิเตอร์หลัก
    c1, c2, c3 = st.columns(3)
    c1.metric("Span Length ($L_1$)", f"{L_span:.2f} m")
    c2.metric("Width ($L_2$)", f"{L_width:.2f} m")
    c3.metric("Static Moment ($M_o$)", f"{Mo:,.0f} kg-m")
    
    st.write("---")

    # จัดหน้าจอ Input แยกซ้ายขวา (CS | Gap | MS)
    col_cs, col_gap, col_ms = st.columns([1, 0.1, 1])
    
    # === ZONE 1: COLUMN STRIP (LEFT) ===
    with col_cs:
        st.markdown(
            """<div style="background-color:#fff5f5; padding:10px; border-radius:5px; border-left: 5px solid #d62728; margin-bottom:10px;">
            <strong style="color:#d62728;">🏛️ COLUMN STRIP (ริมเสา)</strong></div>""", 
            unsafe_allow_html=True
        )
        
        # CS Top (Negative Moment)
        st.markdown(f"**🟥 Top (Support)** <small style='color:gray'>(Req: {req_cs_top:.2f} cm²)</small>", unsafe_allow_html=True)
        c_a, c_b = st.columns([1, 1.5])
        d_cs_top = c_a.selectbox("Dia", [12, 16, 20, 25, 28], key=f"d_cst_{axis_id}")
        s_cs_top = c_b.number_input("@Spacing (cm)", 5, 40, 20, step=5, key=f"s_cst_{axis_id}")
        
        # CS Bot (Positive Moment)
        st.markdown(f"**🟦 Bot (Mid)** <small style='color:gray'>(Req: {req_cs_bot:.2f} cm²)</small>", unsafe_allow_html=True)
        c_a, c_b = st.columns([1, 1.5])
        d_cs_bot = c_a.selectbox("Dia", [12, 16, 20, 25, 28], key=f"d_csb_{axis_id}")
        s_cs_bot = c_b.number_input("@Spacing (cm)", 5, 45, 25, step=5, key=f"s_csb_{axis_id}")

    # === ZONE 2: MIDDLE STRIP (RIGHT) ===
    with col_ms:
        st.markdown(
            """<div style="background-color:#f0f8ff; padding:10px; border-radius:5px; border-left: 5px solid #1f77b4; margin-bottom:10px;">
            <strong style="color:#1f77b4;">🌊 MIDDLE STRIP (กลางพื้น)</strong></div>""", 
            unsafe_allow_html=True
        )
        
        # MS Top (Negative Moment)
        st.markdown(f"**🟥 Top (Support)** <small style='color:gray'>(Req: {req_ms_top:.2f} cm²)</small>", unsafe_allow_html=True)
        c_a, c_b = st.columns([1, 1.5])
        d_ms_top = c_a.selectbox("Dia", [12, 16, 20, 25, 28], key=f"d_mst_{axis_id}", index=0)
        s_ms_top = c_b.number_input("@Spacing (cm)", 10, 50, 30, step=5, key=f"s_mst_{axis_id}")

        # MS Bot (Positive Moment)
        st.markdown(f"**🟦 Bot (Mid)** <small style='color:gray'>(Req: {req_ms_bot:.2f} cm²)</small>", unsafe_allow_html=True)
        c_a, c_b = st.columns([1, 1.5])
        d_ms_bot = c_a.selectbox("Dia", [12, 16, 20, 25, 28], key=f"d_msb_{axis_id}")
        s_ms_bot = c_b.number_input("@Spacing (cm)", 5, 45, 25, step=5, key=f"s_msb_{axis_id}")

    # --- 4. DETAILED CALCULATION TABLE ---
    st.markdown("### 📊 Detailed Calculation")
    
    # รวบรวม Input จาก User
    user_inputs = {
        "CS_Top": (d_cs_top, s_cs_top),
        "CS_Bot": (d_cs_bot, s_cs_bot),
        "MS_Top": (d_ms_top, s_ms_top),
        "MS_Bot": (d_ms_bot, s_ms_bot)
    }
    
    # ข้อมูลแต่ละโซนเพื่อวนลูปคำนวณ
    zones = [
        {"id": "CS_Top", "name": "Column Strip - Top", "M": m_vals["M_cs_neg"], "b": w_cs},
        {"id": "CS_Bot", "name": "Column Strip - Bot", "M": m_vals["M_cs_pos"], "b": w_cs},
        {"id": "MS_Top", "name": "Middle Strip - Top", "M": m_vals["M_ms_neg"], "b": w_ms},
        {"id": "MS_Bot", "name": "Middle Strip - Bot", "M": m_vals["M_ms_pos"], "b": w_ms},
    ]

    table_data = []
    rebar_summary = {} # เก็บค่าไว้ส่งให้กราฟวาด
    is_safe_all = True
    
    for z in zones:
        Mu = z['M']
        b_cm = z['b'] * 100
        
        # 1. Retrieve User Selection
        d_sel, s_sel = user_inputs[z['id']]
        
        # 2. Calculate Capacity (Phi Mn)
        Ab = 3.1416 * (d_sel/10)**2 / 4
        As_prov = (b_cm / s_sel) * Ab
        
        a = (As_prov * fy) / (0.85 * fc * b_cm)
        Mn = As_prov * fy * (d_eff - a/2)
        PhiMn = 0.9 * Mn / 100 # Convert to kg-m
        
        # 3. Check Ratio
        if PhiMn <= 0:
            ratio = 999
        else:
            ratio = Mu / PhiMn
            
        status = "✅ OK" if ratio <= 1.0 else "❌ Fail"
        if ratio > 1.0: is_safe_all = False

        # 4. Prepare Data for Table & Plot
        rebar_str = f"DB{d_sel}@{s_sel}"
        rebar_summary[z['id']] = rebar_str
        
        # Format HTML for Colors
        ratio_html = f"<span style='color:{'green' if ratio<=1 else 'red'}'><b>{ratio:.2f}</b></span>"
        status_html = f"<span style='color:{'green' if ratio<=1 else 'red'}'>{status}</span>"
        
        table_data.append({
            "Zone": z['name'],
            "Mu (kg-m)": f"{Mu:,.0f}",
            "Design": f"<b>{rebar_str}</b>",
            "As Prov (cm2)": f"{As_prov:.2f}",
            "Phi Mn (kg-m)": f"{PhiMn:,.0f}",
            "Ratio": ratio_html,
            "Status": status_html
        })
        
    # Display Table using HTML (เพื่อเลี่ยงปัญหา tabulate และได้สีสวย)
    df = pd.DataFrame(table_data)
    st.markdown(df.to_html(escape=False, index=False), unsafe_allow_html=True)
    
    # --- 5. DRAWINGS (PLOTS) ---
    st.write("---")
    st.markdown("### 🎨 Engineering Drawings")
    
    # 5.1 Moment Diagram (จาก ddm_plots)
    fig_mom = ddm_plots.plot_ddm_moment(L_span, c_para, m_vals)
    st.pyplot(fig_mom)
    
    st.write("") # Spacer

    # 5.2 Section & Plan Views (ส่ง axis_id ไปด้วยเพื่อให้วาดถูกทิศ)
    c_draw1, c_draw2 = st.columns(2)
    
    with c_draw1:
        st.markdown(f"*(A) Section Profile ({axis_id}-Dir Cut)*")
        # เรียกกราฟรูปตัด
        fig_sec = ddm_plots.plot_rebar_detailing(L_span, h_slab, c_para, rebar_summary, axis_id)
        st.pyplot(fig_sec)
        
    with c_draw2:
        st.markdown(f"*(B) Plan View Layout (Showing {axis_id}-Bars)*")
        # เรียกกราฟแปลน
        fig_plan = ddm_plots.plot_rebar_plan_view(L_span, L_width, c_para, rebar_summary, axis_id)
        st.pyplot(fig_plan)

    # Global Warning if any section fails
    if not is_safe_all:
        st.error("⚠️ คำเตือน: มีบางหน้าตัดรับน้ำหนักไม่ไหว (Ratio > 1.0) กรุณาเพิ่มขนาดเหล็กหรือลดระยะแอด")
