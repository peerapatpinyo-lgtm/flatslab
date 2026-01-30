# tab_ddm.py
import streamlit as st
import pandas as pd
import numpy as np

# ลองนำเข้า ddm_plots แบบปลอดภัย
try:
    import ddm_plots 
    HAS_PLOTS = True
except ImportError:
    HAS_PLOTS = False

# ========================================================
# 1. CALCULATION LOGIC (Engineering Core)
# ========================================================
def calc_rebar_logic(M_u, b_width, d_bar, s_bar, h_slab, cover, fc, fy, is_main_dir):
    """
    ฟังก์ชันคำนวณเหล็กเสริม (Engineering Logic)
    """
    b_cm = b_width * 100
    h_cm = h_slab
    
    # Effective Depth (d)
    # Layer 1 (Outer/Main): d = h - cover - db/2
    # Layer 2 (Inner/Minor): d = h - cover - db_outer - db/2 (approx -1.2cm extra)
    d_offset = 0 if is_main_dir else (d_bar/10.0)
    d_eff = h_cm - cover - (d_bar/20.0) - d_offset
    
    if M_u < 100: 
        return { "As_req": 0, "As_prov": 0, "PhiMn": 0, "DC": 0, "Status": True, "Note": "-", "d_eff": d_eff }

    # 1. Required Steel (Flexure)
    Rn = (M_u * 100) / (0.9 * b_cm * d_eff**2)
    term = 1 - (2 * Rn) / (0.85 * fc)
    
    if term < 0:
        rho_req = 999 
    else:
        rho_req = (0.85 * fc / fy) * (1 - np.sqrt(term))
        
    As_flex = rho_req * b_cm * d_eff
    
    # 2. Minimum Steel
    As_min = 0.0018 * b_cm * h_cm
    As_req_final = max(As_flex, As_min) if rho_req != 999 else 999
    
    # 3. Provided Steel
    Ab = np.pi * (d_bar/10)**2 / 4
    As_prov = (b_cm / s_bar) * Ab
    
    # 4. Capacity Check (Phi Mn)
    if rho_req == 999:
        PhiMn = 0
        dc_ratio = 999
    else:
        a = (As_prov * fy) / (0.85 * fc * b_cm)
        PhiMn = 0.9 * As_prov * fy * (d_eff - a/2) / 100
        dc_ratio = M_u / PhiMn if PhiMn > 0 else 999

    # 5. Spacing Check (ACI: 2h or 45cm)
    s_max = min(2 * h_cm, 45)
    
    # Status
    checks = []
    if dc_ratio > 1.0: checks.append("Strength")
    if As_prov < As_min: checks.append("Min Steel")
    if s_bar > s_max: checks.append(f"Spacing > {s_max}")
    
    return {
        "As_req": As_req_final,
        "As_prov": As_prov,
        "PhiMn": PhiMn,
        "DC": dc_ratio,
        "Status": len(checks) == 0,
        "Note": ", ".join(checks) if checks else "OK",
        "d_eff": d_eff
    }

# ========================================================
# 2. RENDER FUNCTION (UI Layout)
# ========================================================
def render_interactive_direction(data, h_slab, cover, fc, fy, axis_id, w_u, is_main_dir):
    L_span = data['L_span']
    L_width = data['L_width']
    c_para = data['c_para']
    Mo = data['Mo']
    m_vals = data['M_vals']
    
    # Geometry
    w_cs = min(L_span, L_width) / 2.0
    w_ms = L_width - w_cs
    
    # --- PART 1: ANALYSIS ---
    st.markdown(f"### 1️⃣ Analysis: {axis_id}-Direction Moment")
    
    # แสดงกราฟ Moment
    if HAS_PLOTS:
        st.pyplot(ddm_plots.plot_ddm_moment(L_span, c_para/100, m_vals))
    
    with st.expander("📊 ดูรายละเอียดค่าโมเมนต์ (Calculation Details)"):
        st.info(f"**Total Static Moment ($M_o$):** {Mo:,.0f} kg-m")
        st.latex(r"M_o = \frac{w_u L_2 l_n^2}{8}")
        
    # --- PART 2: DESIGN INPUTS (Side-by-Side Layout) ---
    st.markdown("---")
    st.markdown("### 2️⃣ Reinforcement Design")
    
    # Layout แยก Column Strip (CS) กับ Middle Strip (MS)
    col_cs, col_gap, col_ms = st.columns([1, 0.05, 1])
    
    # --- A. COLUMN STRIP ---
    with col_cs:
        st.markdown(f"""
        <div style="background-color:#ffebee; padding:10px; border-radius:5px; border-left:5px solid #ef5350;">
            <b style="color:#c62828;">🟥 COLUMN STRIP</b> (Width {w_cs:.2f} m)
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        
        # CS Top
        st.markdown(f"**Top (Support):** $M_u$ = {m_vals['M_cs_neg']:,.0f}")
        c1, c2 = st.columns([1, 1.2])
        d_cst = c1.selectbox("DB", [10, 12, 16, 20, 25, 28], index=2, key=f"db_cs_t_{axis_id}", label_visibility="collapsed")
        s_cst = c2.slider("Spacing (cm)", 5.0, 35.0, 20.0, 2.5, key=f"sp_cs_t_{axis_id}", label_visibility="collapsed")
        st.caption(f"👉 Use DB{d_cst}@{s_cst:.0f}cm")
        
        st.divider()
        
        # CS Bot
        st.markdown(f"**Bot (Midspan):** $M_u$ = {m_vals['M_cs_pos']:,.0f}")
        c1, c2 = st.columns([1, 1.2])
        d_csb = c1.selectbox("DB", [10, 12, 16, 20, 25, 28], index=1, key=f"db_cs_b_{axis_id}", label_visibility="collapsed")
        s_csb = c2.slider("Spacing (cm)", 5.0, 35.0, 25.0, 2.5, key=f"sp_cs_b_{axis_id}", label_visibility="collapsed")
        st.caption(f"👉 Use DB{d_csb}@{s_csb:.0f}cm")

    # --- B. MIDDLE STRIP ---
    with col_ms:
        st.markdown(f"""
        <div style="background-color:#e3f2fd; padding:10px; border-radius:5px; border-left:5px solid #42a5f5;">
            <b style="color:#1565c0;">🟦 MIDDLE STRIP</b> (Width {w_ms:.2f} m)
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        
        # MS Top
        st.markdown(f"**Top (Support):** $M_u$ = {m_vals['M_ms_neg']:,.0f}")
        c1, c2 = st.columns([1, 1.2])
        d_mst = c1.selectbox("DB", [10, 12, 16, 20, 25, 28], index=0, key=f"db_ms_t_{axis_id}", label_visibility="collapsed")
        s_mst = c2.slider("Spacing (cm)", 5.0, 35.0, 25.0, 2.5, key=f"sp_ms_t_{axis_id}", label_visibility="collapsed")
        st.caption(f"👉 Use DB{d_mst}@{s_mst:.0f}cm")
        
        st.divider()
        
        # MS Bot
        st.markdown(f"**Bot (Midspan):** $M_u$ = {m_vals['M_ms_pos']:,.0f}")
        c1, c2 = st.columns([1, 1.2])
        d_msb = c1.selectbox("DB", [10, 12, 16, 20, 25, 28], index=0, key=f"db_ms_b_{axis_id}", label_visibility="collapsed")
        s_msb = c2.slider("Spacing (cm)", 5.0, 35.0, 25.0, 2.5, key=f"sp_ms_b_{axis_id}", label_visibility="collapsed")
        st.caption(f"👉 Use DB{d_msb}@{s_msb:.0f}cm")

    # --- PROCESSING ---
    inputs = [
        ("CS_Top", m_vals['M_cs_neg'], w_cs, d_cst, s_cst),
        ("CS_Bot", m_vals['M_cs_pos'], w_cs, d_csb, s_csb),
        ("MS_Top", m_vals['M_ms_neg'], w_ms, d_mst, s_mst),
        ("MS_Bot", m_vals['M_ms_pos'], w_ms, d_msb, s_msb),
    ]
    
    results = []
    rebar_map = {}
    
    for label, Mu, b, db, sb in inputs:
        res = calc_rebar_logic(Mu, b, db, sb, h_slab, cover, fc, fy, is_main_dir)
        
        status_icon = "✅ OK" if res['Status'] else "❌ FAIL"
        rebar_map[label] = f"DB{db}@{sb:.0f}"
        
        results.append({
            "Location": label,
            "Mu (kg-m)": f"{Mu:,.0f}",
            "Selection": f"DB{db}@{sb:.0f}",
            "As Req": f"{res['As_req']:.2f}",
            "As Prov": f"{res['As_prov']:.2f}",
            "D/C": res['DC'], # Keep raw for styling
            "Status": status_icon,
            "Note": res['Note']
        })

    # --- PART 3: SUMMARY TABLE ---
    st.write("")
    st.write("#### 📋 Design Summary")
    df = pd.DataFrame(results)
    
    # Styling
    def style_status(val):
        color = 'red' if 'FAIL' in val else 'green'
        return f'color: {color}; font-weight: bold'

    st.dataframe(
        df.style.applymap(style_status, subset=['Status'])
                .format({"D/C": "{:.2f}"}),
        use_container_width=True
    )
    
    # --- PART 4: DETAILING (PLOTS) ---
    st.markdown("---")
    st.markdown("### 3️⃣ Detailing Drawings")
    if HAS_PLOTS:
        tab1, tab2 = st.tabs(["📐 Section A-A (Side)", "🏗️ Plan View (Top)"])
        with tab1:
            # Section View
            st.pyplot(ddm_plots.plot_rebar_detailing(L_span, h_slab, c_para, rebar_map, axis_id))
        with tab2:
            # Plan View
            st.pyplot(ddm_plots.plot_rebar_plan_view(L_span, L_width, c_para, rebar_map, axis_id))
    else:
        st.warning("⚠️ ไม่พบโมดูล ddm_plots.py กรุณาตรวจสอบไฟล์")


# ========================================================
# 3. MAIN ENTRY POINT (เรียกจาก app.py)
# ========================================================
def render_dual(data_x, data_y, mat_props, w_u):
    st.markdown("## 🏗️ Interactive Slab Design (DDM)")
    st.info("💡 **Instructions:** เลือกขนาดเหล็กและระยะเรียงให้ผ่านเกณฑ์ (Status = OK)")
    
    tab_x, tab_y = st.tabs([
        f"➡️ X-Direction (Span {data_x['L_span']}m)", 
        f"⬆️ Y-Direction (Span {data_y['L_span']}m)"
    ])
    
    with tab_x:
        render_interactive_direction(data_x, mat_props['h_slab'], mat_props['cover'], mat_props['fc'], mat_props['fy'], "X", w_u, is_main_dir=True)
        
    with tab_y:
        render_interactive_direction(data_y, mat_props['h_slab'], mat_props['cover'], mat_props['fc'], mat_props['fy'], "Y", w_u, is_main_dir=False)
