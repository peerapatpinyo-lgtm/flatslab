# tab_ddm.py
import streamlit as st
import pandas as pd
import numpy as np

# Try importing the plotting module safely
try:
    import ddm_plots 
    HAS_PLOTS = True
except ImportError:
    HAS_PLOTS = False

# ========================================================
# 1. ENGINEERING CALCULATION ENGINE
# ========================================================
def calc_rebar_logic(M_u, b_width, d_bar, s_bar, h_slab, cover, fc, fy, is_main_dir):
    """
    Perform rigorous reinforced concrete slab design checks (ACI 318 / EIT).
    """
    # Unit Conversions
    b_cm = b_width * 100.0
    h_cm = float(h_slab)
    Mu_kgcm = M_u * 100.0  # Convert kg-m to kg-cm
    
    # 1. Effective Depth (d)
    # Main Direction (Outer Layer): d = h - cover - db/2
    # Minor Direction (Inner Layer): d = h - cover - db_main - db/2
    d_offset = 0.0 if is_main_dir else 1.6 
    d_eff = h_cm - cover - (d_bar/20.0) - d_offset
    
    if M_u < 10:
        return {
            "d": d_eff, "Rn": 0, "rho_req": 0, "As_min": 0, "As_flex": 0, 
            "As_req": 0, "As_prov": 0, "a": 0, "PhiMn": 0, "DC": 0, 
            "Status": True, "Note": "Negligible Moment", "s_max": 45
        }

    # 2. Required Steel (Flexure)
    phi = 0.90
    Rn = Mu_kgcm / (phi * b_cm * d_eff**2) # ksc
    
    term_val = 1 - (2 * Rn) / (0.85 * fc)
    if term_val < 0:
        rho_req = 999 
    else:
        rho_req = (0.85 * fc / fy) * (1 - np.sqrt(term_val))
        
    As_flex = rho_req * b_cm * d_eff
    
    # 3. Minimum Steel
    As_min = 0.0018 * b_cm * h_cm
    As_req_final = max(As_flex, As_min) if rho_req != 999 else 999
    
    # 4. Provided Steel
    Ab_area = np.pi * (d_bar/10.0)**2 / 4.0
    As_prov = (b_cm / s_bar) * Ab_area
    
    # 5. Capacity Check (Phi Mn)
    if rho_req == 999:
        PhiMn = 0
        a_depth = 0
        dc_ratio = 999
    else:
        a_depth = (As_prov * fy) / (0.85 * fc * b_cm)
        Mn = As_prov * fy * (d_eff - a_depth/2.0)
        PhiMn = phi * Mn / 100.0 # Convert back to kg-m
        dc_ratio = M_u / PhiMn if PhiMn > 0 else 999

    # 6. Spacing Check
    s_max = min(2 * h_cm, 45.0)
    
    # 7. Evaluate Status
    checks = []
    if dc_ratio > 1.0: checks.append("Strength")
    if As_prov < As_min: checks.append("Min Steel")
    if s_bar > s_max: checks.append(f"Spacing > {s_max}")
    if rho_req == 999: checks.append("Section Too Small")
    
    return {
        "d": d_eff, "Rn": Rn, "rho_req": rho_req, "As_min": As_min, 
        "As_req": As_req_final, "As_prov": As_prov, "a": a_depth, 
        "PhiMn": PhiMn, "DC": dc_ratio, "Status": len(checks) == 0, 
        "Note": ", ".join(checks) if checks else "OK", "s_max": s_max
    }

# ========================================================
# 2. RENDER UI FUNCTION
# ========================================================
def render_interactive_direction(data, h_slab, cover, fc, fy, axis_id, w_u, is_main_dir):
    L_span = data['L_span']
    L_width = data['L_width']
    c_para = data['c_para']
    Mo = data['Mo']
    m_vals = data['M_vals']
    
    # --- ปรับแก้ LABEL ให้เป็นมาตรฐานวิศวกรรม (l1, l2) ---
    # l1 = Span Length (ทิศที่กำลังพิจารณา)
    # l2 = Transverse Width (ความกว้างแถบ)
    l1_val = L_span
    l2_val = L_width
    
    w_cs = min(l1_val, l2_val) / 2.0
    w_ms = l2_val - w_cs
    
    # --- PART 1: ANALYSIS & MOMENT DISTRIBUTION ---
    st.markdown(f"### 1️⃣ Analysis: {axis_id}-Direction Moment")
    
    with st.expander("📝 ดูรายการคำนวณ $M_o$ และสัมประสิทธิ์ (Details)", expanded=True):
        
        # 1. Mo Calculation (ใช้ notation l1, l2)
        ln_val = l1_val - (c_para / 100.0)
        st.markdown(f"**Step 1: คำนวณโมเมนต์สถิตรวม ($M_o$)**")
        
        c1, c2 = st.columns([1, 1.5])
        with c1:
            st.info(f"""
            **Notation (ACI 318):**
            * $l_1$ = Span Length = {l1_val:.2f} m
            * $l_2$ = Transverse Width = {l2_val:.2f} m
            * $l_n$ = Clear Span = {ln_val:.2f} m
            """)
            st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/2/23/Slab_effective_width.svg/300px-Slab_effective_width.svg.png", caption="Definition of l1 and l2", use_column_width=True)
            
        with c2:
            st.markdown("จากสูตร Direct Design Method:")
            st.latex(r"M_o = \frac{w_u l_2 l_n^2}{8}")
            st.latex(f"M_o = \\frac{{{w_u:,.0f} \\cdot {l2_val:.2f} \\cdot {ln_val:.2f}^2}}{{8}}")
            st.latex(f"M_o = \\mathbf{{{Mo:,.0f}}} \\; \\text{{kg-m}}")

        st.divider()
        
        # 2. Moment Distribution (Mu)
        st.markdown(f"**Step 2: การกระจายโมเมนต์ ($M_u$)**")
        st.markdown("""
        > **Reference:** สัมประสิทธิ์การกระจายโมเมนต์อ้างอิงจาก **ACI 318** / **มาตรฐาน วสท.** > (หมวด Direct Design Method สำหรับแผ่นพื้นไร้คาน)
        """)
        
        # Helper to calculate %
        def get_pct(val, total):
            return (val / total * 100) if total > 0 else 0

        # Create explicit table showing Source -> Distribution
        dist_data = [
            {
                "Position": "Top Support (-)", 
                "Zone": "Total Negative", 
                "% of Mo (Ref: ACI)": f"{get_pct(m_vals['M_cs_neg'] + m_vals['M_ms_neg'], Mo):.0f}%",
                "Column Strip Share": f"{get_pct(m_vals['M_cs_neg'], Mo):.1f}%", 
                "Middle Strip Share": f"{get_pct(m_vals['M_ms_neg'], Mo):.1f}%",
            },
            {
                "Position": "Midspan (+)", 
                "Zone": "Total Positive", 
                "% of Mo (Ref: ACI)": f"{get_pct(m_vals['M_cs_pos'] + m_vals['M_ms_pos'], Mo):.0f}%",
                "Column Strip Share": f"{get_pct(m_vals['M_cs_pos'], Mo):.1f}%", 
                "Middle Strip Share": f"{get_pct(m_vals['M_ms_pos'], Mo):.1f}%",
            },
        ]
        
        st.table(pd.DataFrame(dist_data))
        st.caption("*หมายเหตุ: สัดส่วนระหว่าง CS/MS ขึ้นอยู่กับค่า $\\alpha_1 l_2 / l_1$ และ $\\beta_t$ ตามตารางในมาตรฐาน")
        
    # --- PART 2: DESIGN INPUTS ---
    st.markdown("---")
    st.markdown("### 2️⃣ Reinforcement Selection")
    
    col_cs, col_gap, col_ms = st.columns([1, 0.05, 1])
    
    # COLUMN STRIP
    with col_cs:
        st.markdown(f"""<div style="background-color:#ffebee; padding:10px; border-radius:5px; border-left:5px solid #ef5350;">
            <b style="color:#c62828;">🟥 COLUMN STRIP</b> (Width {w_cs:.2f} m)</div>""", unsafe_allow_html=True)
        st.write("")
        # Top
        st.markdown(f"**Top (-):** $M_u$ = {m_vals['M_cs_neg']:,.0f}")
        c1, c2 = st.columns([1, 1.2])
        d_cst = c1.selectbox("DB", [10, 12, 16, 20, 25], index=2, key=f"d_cst_{axis_id}", label_visibility="collapsed")
        s_cst = c2.slider("Spacing", 5.0, 35.0, 20.0, 2.5, key=f"s_cst_{axis_id}", label_visibility="collapsed")
        st.caption(f"👉 Use DB{d_cst}@{s_cst:.0f}cm")
        st.divider()
        # Bot
        st.markdown(f"**Bot (+):** $M_u$ = {m_vals['M_cs_pos']:,.0f}")
        c1, c2 = st.columns([1, 1.2])
        d_csb = c1.selectbox("DB", [10, 12, 16, 20, 25], index=1, key=f"d_csb_{axis_id}", label_visibility="collapsed")
        s_csb = c2.slider("Spacing", 5.0, 35.0, 25.0, 2.5, key=f"s_csb_{axis_id}", label_visibility="collapsed")
        st.caption(f"👉 Use DB{d_csb}@{s_csb:.0f}cm")

    # MIDDLE STRIP
    with col_ms:
        st.markdown(f"""<div style="background-color:#e3f2fd; padding:10px; border-radius:5px; border-left:5px solid #42a5f5;">
            <b style="color:#1565c0;">🟦 MIDDLE STRIP</b> (Width {w_ms:.2f} m)</div>""", unsafe_allow_html=True)
        st.write("")
        # Top
        st.markdown(f"**Top (-):** $M_u$ = {m_vals['M_ms_neg']:,.0f}")
        c1, c2 = st.columns([1, 1.2])
        d_mst = c1.selectbox("DB", [10, 12, 16, 20, 25], index=0, key=f"d_mst_{axis_id}", label_visibility="collapsed")
        s_mst = c2.slider("Spacing", 5.0, 35.0, 25.0, 2.5, key=f"s_mst_{axis_id}", label_visibility="collapsed")
        st.caption(f"👉 Use DB{d_mst}@{s_mst:.0f}cm")
        st.divider()
        # Bot
        st.markdown(f"**Bot (+):** $M_u$ = {m_vals['M_ms_pos']:,.0f}")
        c1, c2 = st.columns([1, 1.2])
        d_msb = c1.selectbox("DB", [10, 12, 16, 20, 25], index=0, key=f"d_msb_{axis_id}", label_visibility="collapsed")
        s_msb = c2.slider("Spacing", 5.0, 35.0, 25.0, 2.5, key=f"s_msb_{axis_id}", label_visibility="collapsed")
        st.caption(f"👉 Use DB{d_msb}@{s_msb:.0f}cm")

    # --- CALCULATION PROCESSING ---
    inputs = [
        ("CS-Top", m_vals['M_cs_neg'], w_cs, d_cst, s_cst),
        ("CS-Bot", m_vals['M_cs_pos'], w_cs, d_csb, s_csb),
        ("MS-Top", m_vals['M_ms_neg'], w_ms, d_mst, s_mst),
        ("MS-Bot", m_vals['M_ms_pos'], w_ms, d_msb, s_msb),
    ]
    
    detailed_data = []
    
    for zone, Mu, b_zone, db, sb in inputs:
        res = calc_rebar_logic(Mu, b_zone, db, sb, h_slab, cover, fc, fy, is_main_dir)
        detailed_data.append({
            "Zone": zone,
            "Mu (kg-m)": Mu,
            "b (cm)": b_zone*100,
            "Use": f"DB{db}@{sb:.0f}",
            "d (cm)": res['d'],
            "As,min": res['As_min'],
            "As,req": res['As_req'],
            "As,prov": res['As_prov'],
            "a (cm)": res['a'],
            "φMn": res['PhiMn'],
            "D/C": res['DC'],
            "Status": "✅ PASS" if res['Status'] else "❌ " + res['Note']
        })

    # --- PART 3: DETAILED RESULTS TABLE ---
    st.write("")
    st.markdown("### 3️⃣ Detailed Engineering Verification")
    
    df_res = pd.DataFrame(detailed_data)
    st.dataframe(
        df_res.style.format({
            "Mu (kg-m)": "{:,.0f}",
            "b (cm)": "{:.0f}",
            "d (cm)": "{:.2f}",
            "As,min": "{:.2f}",
            "As,req": "{:.2f}",
            "As,prov": "{:.2f}",
            "a (cm)": "{:.2f}",
            "φMn": "{:,.0f}",
            "D/C": "{:.2f}"
        }).background_gradient(subset=["D/C"], cmap="RdYlGn_r", vmin=0.0, vmax=1.2),
        use_container_width=True
    )

    # --- PART 4: SAMPLE CALCULATION ---
    with st.expander(f"📝 View Sample Design Calculation ({detailed_data[0]['Zone']})", expanded=False):
        ex = detailed_data[0]
        st.markdown(f"**Verification for {ex['Zone']} (Critical Section):**")
        
        col_math1, col_math2 = st.columns(2)
        with col_math1:
            st.markdown("**1. Geometry & Depth**")
            st.latex(f"d = h - cover - d_b/2 = {ex['d (cm)']:.2f} \\; cm")
            
            st.markdown("**2. Required Steel**")
            st.latex(f"A_{{s,min}} = 0.0018 \\cdot b \\cdot h = {ex['As,min']:.2f} \\; cm^2")
            st.latex(f"A_{{s,req}} = {ex['As,req']:.2f} \\; cm^2")
            
        with col_math2:
            st.markdown("**3. Strength Check ($ \\phi M_n $)**")
            st.latex(f"a = \\frac{{A_s f_y}}{{0.85 f_c' b}} = {ex['a (cm)']:.2f} \\; cm")
            st.latex(f"\\phi M_n = 0.9 A_s f_y (d - a/2) = \\mathbf{{{ex['φMn']:,.0f}}} \\; kg\\cdot m")
            
            check_color = "green" if ex['D/C'] <= 1.0 else "red"
            st.markdown(f"**4. Ratio ($M_u / \\phi M_n$):**")
            st.markdown(f"<h4 style='color:{check_color}'>D/C = {ex['D/C']:.2f} {'✅ OK' if ex['D/C']<=1 else '❌ FAIL'}</h4>", unsafe_allow_html=True)

    # --- PART 5: DRAWINGS ---
    st.write("---")
    st.markdown("### 4️⃣ Drawings & Diagrams")
    
    if HAS_PLOTS:
        t1, t2, t3 = st.tabs(["📉 Moment Diagram", "📐 Section Detail", "🏗️ Plan View"])
        rebar_map = {d['Zone'].replace("-","_"): d['Use'] for d in detailed_data}
        
        with t1:
            st.pyplot(ddm_plots.plot_ddm_moment(L_span, c_para/100, m_vals))
            st.caption("Distribution of Moments in Column Strip and Middle Strip")
        with t2:
            st.pyplot(ddm_plots.plot_rebar_detailing(L_span, h_slab, c_para, rebar_map, axis_id))
            st.caption(f"Section A-A ({axis_id}-Direction)")
        with t3:
            st.pyplot(ddm_plots.plot_rebar_plan_view(L_span, L_width, c_para, rebar_map, axis_id))
            st.caption(f"Plan View Reinforcement ({axis_id}-Direction)")

# ========================================================
# 3. MAIN ENTRY POINT
# ========================================================
def render_dual(data_x, data_y, mat_props, w_u):
    st.markdown("## 🏗️ Interactive Slab Design (DDM)")
    st.info("💡 **Instructions:** Adjust reinforcement below. Calculations based on ACI 318 Direct Design Method.")
    
    # Use simple directional labels for Tabs
    tab_x, tab_y = st.tabs([
        f"➡️ X-Direction (Span {data_x['L_span']}m)", 
        f"⬆️ Y-Direction (Span {data_y['L_span']}m)"
    ])
    
    with tab_x:
        # X-Direction: Span=Lx, Width=Ly
        render_interactive_direction(data_x, mat_props['h_slab'], mat_props['cover'], mat_props['fc'], mat_props['fy'], "X", w_u, is_main_dir=True)
        
    with tab_y:
        # Y-Direction: Span=Ly, Width=Lx
        render_interactive_direction(data_y, mat_props['h_slab'], mat_props['cover'], mat_props['fc'], mat_props['fy'], "Y", w_u, is_main_dir=False)
