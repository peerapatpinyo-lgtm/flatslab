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
# 1. CORE CALCULATION ENGINE
# ========================================================
def calc_rebar_logic(M_u, b_width, d_bar, s_bar, h_slab, cover, fc, fy, is_main_dir):
    b_cm = b_width * 100.0
    h_cm = float(h_slab)
    Mu_kgcm = M_u * 100.0
    phi = 0.90 

    # Effective Depth (Outer vs Inner Layer)
    d_offset = 0.0 if is_main_dir else 1.6 
    d_eff = h_cm - cover - (d_bar/20.0) - d_offset
    
    if M_u < 10:
        return {
            "d": d_eff, "Rn": 0, "rho_req": 0, "As_min": 0, "As_flex": 0, 
            "As_req": 0, "As_prov": 0, "a": 0, "PhiMn": 0, "DC": 0, 
            "Status": True, "Note": "M -> 0", "s_max": 45
        }

    Rn = Mu_kgcm / (phi * b_cm * d_eff**2)
    term_val = 1 - (2 * Rn) / (0.85 * fc)
    
    if term_val < 0:
        rho_req = 999 
    else:
        rho_req = (0.85 * fc / fy) * (1 - np.sqrt(term_val))
        
    As_flex = rho_req * b_cm * d_eff
    As_min = 0.0018 * b_cm * h_cm
    As_req_final = max(As_flex, As_min) if rho_req != 999 else 999
    
    Ab_area = np.pi * (d_bar/10.0)**2 / 4.0
    As_prov = (b_cm / s_bar) * Ab_area
    
    if rho_req == 999:
        PhiMn = 0; a_depth = 0; dc_ratio = 999
    else:
        a_depth = (As_prov * fy) / (0.85 * fc * b_cm)
        Mn = As_prov * fy * (d_eff - a_depth/2.0)
        PhiMn = phi * Mn / 100.0
        dc_ratio = M_u / PhiMn if PhiMn > 0 else 999

    s_max = min(2 * h_cm, 45.0)
    
    checks = []
    if dc_ratio > 1.0: checks.append("Strength Fail")
    if As_prov < As_min: checks.append("As < Min")
    if s_bar > s_max: checks.append("Spacing > Max")
    if rho_req == 999: checks.append("Section Fail")
    
    return {
        "d": d_eff, "Rn": Rn, "rho_req": rho_req, "As_min": As_min, "As_flex": As_flex,
        "As_req": As_req_final, "As_prov": As_prov, "a": a_depth, 
        "PhiMn": PhiMn, "DC": dc_ratio, "Status": len(checks) == 0, 
        "Note": ", ".join(checks) if checks else "OK", "s_max": s_max
    }

# ========================================================
# 2. DETAILED CALCULATION RENDERER
# ========================================================
def show_detailed_calculation(zone_name, res, inputs, coeff_pct, Mo_val):
    Mu, b, h, cover, fc, fy, db, s = inputs
    
    st.markdown(f"#### 📐 รายการคำนวณออกแบบ: {zone_name}")
    st.caption(f"Design Parameters: $f_c'={fc}$ ksc, $f_y={fy}$ ksc, $h={h}$ cm")

    step1, step2, step3 = st.tabs(["1. Moment & Depth", "2. Steel Area", "3. Capacity Check"])
    
    with step1:
        st.markdown("**1.1 Design Moment ($M_u$) Calculation**")
        st.write("หาค่าโมเมนต์ดัดออกแบบจากสัมประสิทธิ์ (Coefficient Method):")
        st.latex(f"M_u = (\\text{{Coeff}}) \\times M_o")
        st.latex(f"M_u = {coeff_pct/100:.3f} \\times {Mo_val:,.0f} = \\mathbf{{{Mu:,.0f}}} \\; \\text{{kg-m}}")
        st.latex(r"d = h - C_{over} - \frac{d_b}{2}")
        st.latex(f"d = {h} - {cover} - \\frac{{{db/10}}}{{2}} = \\mathbf{{{res['d']:.2f}}} \\; \\text{{cm}}")

    with step2:
        st.markdown("**2.1 Required Reinforcement ($A_{s,req}$)**")
        st.latex(f"A_{{s,min}} = 0.0018 \\cdot ({b*100:.0f}) \\cdot {h} = {res['As_min']:.2f} \\; \\text{{cm}}^2")
        st.markdown("จากสมการกำลัง (Strength Design):")
        st.latex(f"R_n = \\frac{{M_u}}{{\\phi b d^2}} = \\frac{{{Mu*100:,.0f}}}{{0.9 \\cdot {b*100:.0f} \\cdot {res['d']:.2f}^2}} = {res['Rn']:.2f} \\; \\text{{ksc}}")
        
        if res['rho_req'] != 999:
            st.latex(r"\rho_{req} = \frac{0.85 f_c'}{f_y} \left( 1 - \sqrt{1 - \frac{2 R_n}{0.85 f_c'}} \right)")
            st.latex(f"A_{{s,flex}} = \\rho_{{req}} b d = {res['As_flex']:.2f} \\; \\text{{cm}}^2")
        else:
            st.error("Section dimensions are too small (Rn too high).")

        st.info(f"👉 **Control:** $A_{{s,req}} = \\max({res['As_min']:.2f}, {res['As_flex']:.2f}) = \\mathbf{{{res['As_req']:.2f}}} \\; \\text{{cm}}^2$")

    with step3:
        st.markdown("**3.1 Provided Reinforcement ($A_{s,prov}$)**")
        st.write(f"เลือกใช้: **DB{db} @ {s:.0f} cm**")
        bar_area = 3.1416 * (db/10)**2 / 4
        st.latex(f"A_{{s,prov}} = \\frac{{{b*100:.0f}}}{{{s:.0f}}} \\cdot {bar_area:.2f} = \\mathbf{{{res['As_prov']:.2f}}} \\; \\text{{cm}}^2")
        
        st.markdown("**3.2 Moment Capacity Check ($\\phi M_n$)**")
        st.latex(f"a = \\frac{{{res['As_prov']:.2f} \\cdot {fy}}}{{0.85 \\cdot {fc} \\cdot {b*100:.0f}}} = {res['a']:.2f} \\; \\text{{cm}}")
        st.latex(f"\\phi M_n = \\frac{{0.9 \\cdot {res['As_prov']:.2f} \\cdot {fy} \\cdot ({res['d']:.2f} - {res['a']:.2f}/2)}}{{100}}")
        st.latex(f"\\phi M_n = \\mathbf{{{res['PhiMn']:,.0f}}} \\; \\text{{kg-m}}")
        
        dc = res['DC']
        color = "green" if dc <= 1.0 else "red"
        st.markdown(f"**Verification:** Ratio = {dc:.2f} ... :{color}[{'✅ PASS' if dc <=1 else '❌ FAIL'}]")

# ========================================================
# 3. UI RENDERER
# ========================================================
def render_interactive_direction(data, h_slab, cover, fc, fy, axis_id, w_u, is_main_dir):
    L_span = data['L_span']
    L_width = data['L_width']
    c_para = data['c_para']
    Mo = data['Mo']
    m_vals = data['M_vals']
    
    # -----------------------------------------------
    # 🔹 DYNAMIC LABELING LOGIC
    # -----------------------------------------------
    if axis_id == "X":
        span_sym, width_sym = "L_x", "L_y"
        span_val, width_val = L_span, L_width
    else:
        span_sym, width_sym = "L_y", "L_x"
        span_val, width_val = L_span, L_width

    ln_val = span_val - (c_para/100.0)
    w_cs = min(span_val, width_val) / 2.0
    w_ms = width_val - w_cs
    
    # --- PART 1: Mo & DISTRIBUTION ---
    st.markdown(f"### 1️⃣ Analysis: {axis_id}-Direction")
    
    with st.expander(f"📝 ดูที่มาของ $M_o$ และ $M_u$ ({axis_id}-Direction)", expanded=True):
        col_diagram, col_calc = st.columns([1, 1.5])
        
        with col_diagram:
            st.info(f"**Definitions for {axis_id}-Axis:**")
            st.markdown(f"""
            - **Span Length ({span_sym}):** {span_val:.2f} m
            - **Strip Width ({width_sym}):** {width_val:.2f} m
            - **Clear Span ($l_n$):** {ln_val:.2f} m
            """)
            st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/2/23/Slab_effective_width.svg/300px-Slab_effective_width.svg.png", caption="Span Definitions (ACI)", use_container_width=True)

        with col_calc:
            st.markdown(f"#### Step 1: Total Static Moment ($M_o$)")
            st.latex(f"M_o = \\frac{{w_u {width_sym} ({span_sym} - c)^2}}{{8}}")
            st.latex(f"M_o = \\frac{{{w_u:,.0f} \\cdot {width_val:.2f} \\cdot ({ln_val:.2f})^2}}{{8}} = \\mathbf{{{Mo:,.0f}}} \\; \\text{{kg-m}}")
        
        st.divider()
        
        def get_pct(val): return (val / Mo * 100) if Mo > 0 else 0
        dist_data = [
            {"Pos": "Top (-)", "Strip": "🟥 Column Strip", "% of Mo": f"{get_pct(m_vals['M_cs_neg']):.1f}%", "Mu": m_vals['M_cs_neg']},
            {"Pos": "Top (-)", "Strip": "🟦 Middle Strip", "% of Mo": f"{get_pct(m_vals['M_ms_neg']):.1f}%", "Mu": m_vals['M_ms_neg']},
            {"Pos": "Bot (+)", "Strip": "🟥 Column Strip", "% of Mo": f"{get_pct(m_vals['M_cs_pos']):.1f}%", "Mu": m_vals['M_cs_pos']},
            {"Pos": "Bot (+)", "Strip": "🟦 Middle Strip", "% of Mo": f"{get_pct(m_vals['M_ms_pos']):.1f}%", "Mu": m_vals['M_ms_pos']},
        ]
        st.dataframe(pd.DataFrame(dist_data).style.format({"Mu": "{:,.0f}"}), use_container_width=True, hide_index=True)

    # --- PART 2: INPUTS ---
    st.markdown("---")
    st.markdown("### 2️⃣ Reinforcement Selection")
    
    col_cs, gap, col_ms = st.columns([1, 0.05, 1])
    
    # --- CS ---
    with col_cs:
        st.markdown(f"""<div style="background-color:#ffebee; padding:8px; border-radius:5px; border-left:4px solid #ef5350;">
            <b>🟥 COLUMN STRIP</b> (Width {w_cs:.2f} m)</div>""", unsafe_allow_html=True)
        # Top
        st.markdown(f"**Top ($M_u$ {m_vals['M_cs_neg']:,.0f}):**")
        c1, c2 = st.columns(2)
        d_cst = c1.selectbox("DB", [10,12,16,20,25], 2, key=f"d_cst_{axis_id}", label_visibility="collapsed")
        s_cst = c2.selectbox("@", [10,15,20,25,30], 2, key=f"s_cst_{axis_id}", label_visibility="collapsed")
        # Bot
        st.markdown(f"**Bot ($M_u$ {m_vals['M_cs_pos']:,.0f}):**")
        c1, c2 = st.columns(2)
        d_csb = c1.selectbox("DB", [10,12,16,20,25], 1, key=f"d_csb_{axis_id}", label_visibility="collapsed")
        s_csb = c2.selectbox("@", [10,15,20,25,30], 3, key=f"s_csb_{axis_id}", label_visibility="collapsed")

    # --- MS ---
    with col_ms:
        st.markdown(f"""<div style="background-color:#e3f2fd; padding:8px; border-radius:5px; border-left:4px solid #2196f3;">
            <b>🟦 MIDDLE STRIP</b> (Width {w_ms:.2f} m)</div>""", unsafe_allow_html=True)
        # Top
        st.markdown(f"**Top ($M_u$ {m_vals['M_ms_neg']:,.0f}):**")
        c1, c2 = st.columns(2)
        d_mst = c1.selectbox("DB", [10,12,16,20,25], 0, key=f"d_mst_{axis_id}", label_visibility="collapsed")
        s_mst = c2.selectbox("@", [10,15,20,25,30], 3, key=f"s_mst_{axis_id}", label_visibility="collapsed")
        # Bot
        st.markdown(f"**Bot ($M_u$ {m_vals['M_ms_pos']:,.0f}):**")
        c1, c2 = st.columns(2)
        d_msb = c1.selectbox("DB", [10,12,16,20,25], 0, key=f"d_msb_{axis_id}", label_visibility="collapsed")
        s_msb = c2.selectbox("@", [10,15,20,25,30], 3, key=f"s_msb_{axis_id}", label_visibility="collapsed")

    # --- CALCULATION ---
    # Assign 'Key' to identify zone
    calc_configs = [
        {"Label": "Col Strip - Top (-)", "Key": "cs_top", "Mu": m_vals['M_cs_neg'], "b": w_cs, "db": d_cst, "s": s_cst},
        {"Label": "Col Strip - Bot (+)", "Key": "cs_bot", "Mu": m_vals['M_cs_pos'], "b": w_cs, "db": d_csb, "s": s_csb},
        {"Label": "Mid Strip - Top (-)", "Key": "ms_top", "Mu": m_vals['M_ms_neg'], "b": w_ms, "db": d_mst, "s": s_mst},
        {"Label": "Mid Strip - Bot (+)", "Key": "ms_bot", "Mu": m_vals['M_ms_pos'], "b": w_ms, "db": d_msb, "s": s_msb},
    ]

    results = []
    for cfg in calc_configs:
        res = calc_rebar_logic(cfg['Mu'], cfg['b'], cfg['db'], cfg['s'], h_slab, cover, fc, fy, is_main_dir)
        res.update(cfg)
        results.append(res)

    # --- PART 3: SUMMARY ---
    st.write("")
    st.markdown("### 3️⃣ Verification Table")
    df_show = pd.DataFrame(results)
    st.dataframe(
        df_show[["Label", "Mu", "d", "As_req", "As_prov", "PhiMn", "DC", "Note"]].style.format({
            "Mu": "{:,.0f}", "d": "{:.2f}", "As_req": "{:.2f}", "As_prov": "{:.2f}", 
            "PhiMn": "{:,.0f}", "DC": "{:.2f}"
        }).background_gradient(subset=["DC"], cmap="RdYlGn_r", vmin=0, vmax=1.2),
        use_container_width=True
    )

    # --- PART 4: DETAILED CALCULATION SHEET ---
    st.markdown("---")
    st.markdown("### 4️⃣ Detailed Calculation Sheet")
    sel_label = st.selectbox(f"Select Zone to View Details ({axis_id}):", [r['Label'] for r in results])
    target = next(r for r in results if r['Label'] == sel_label)
    raw_inputs = (target['Mu'], target['b'], h_slab, cover, fc, fy, target['db'], target['s'])
    
    with st.container(border=True):
        pct_val = (target['Mu'] / Mo * 100) if Mo > 0 else 0
        show_detailed_calculation(sel_label, target, raw_inputs, pct_val, Mo)

    # --- PART 5: DRAWINGS (SUPER MAPPING FIX) ---
    if HAS_PLOTS:
        st.markdown("---")
        t1, t2, t3 = st.tabs(["📉 Moment Diagram", "🏗️ Section Detail", "📐 Plan View"])
        
        # ⚠️ UNIVERSAL FIX: สร้าง Map แบบครอบจักรวาล ดักทุกชื่อที่ ddm_plots อาจจะใช้
        rebar_map = {}
        for r in results:
            text = f"DB{r['db']}@{r['s']:.0f}"
            
            # 1. Map Keys ตรงตัว
            rebar_map[r['Key']] = text
            
            # 2. Map Keys แบบ Moment Definition (c_neg, c_pos)
            if r['Key'] == 'cs_top': rebar_map['c_neg'] = text; rebar_map['cst'] = text
            if r['Key'] == 'cs_bot': rebar_map['c_pos'] = text; rebar_map['csb'] = text
            if r['Key'] == 'ms_top': rebar_map['m_neg'] = text; rebar_map['mst'] = text
            if r['Key'] == 'ms_bot': rebar_map['m_pos'] = text; rebar_map['msb'] = text

        with t1:
            st.pyplot(ddm_plots.plot_ddm_moment(span_val, c_para/100, m_vals))
        with t2:
            st.pyplot(ddm_plots.plot_rebar_detailing(span_val, h_slab, c_para, rebar_map, axis_id))
        with t3:
            st.pyplot(ddm_plots.plot_rebar_plan_view(span_val, width_val, c_para, rebar_map, axis_id))

# ========================================================
# MAIN ENTRY
# ========================================================
def render_dual(data_x, data_y, mat_props, w_u):
    st.markdown("## 🏗️ RC Slab Design (DDM Method)")
    
    tab_x, tab_y = st.tabs([
        f"➡️ X-Direction (Lx={data_x['L_span']}m)", 
        f"⬆️ Y-Direction (Ly={data_y['L_span']}m)"
    ])
    
    with tab_x:
        render_interactive_direction(data_x, mat_props['h_slab'], mat_props['cover'], mat_props['fc'], mat_props['fy'], "X", w_u, True)
    with tab_y:
        render_interactive_direction(data_y, mat_props['h_slab'], mat_props['cover'], mat_props['fc'], mat_props['fy'], "Y", w_u, False)
