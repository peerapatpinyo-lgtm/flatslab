# tab_ddm.py
import streamlit as st
import pandas as pd
import numpy as np

# Try importing dependencies
try:
    import ddm_plots 
    HAS_PLOTS = True
except ImportError:
    HAS_PLOTS = False

try:
    import calculations as calc
    HAS_CALC = True
except ImportError:
    HAS_CALC = False

# ========================================================
# 1. CORE CALCULATION ENGINE
# ========================================================
def calc_rebar_logic(M_u, b_width, d_bar, s_bar, h_slab, cover, fc, fy, is_main_dir):
    """
    Core Logic: คำนวณเหล็กเสริมตาม ACI 318
    """
    b_cm = b_width * 100.0
    h_cm = float(h_slab)
    Mu_kgcm = M_u * 100.0
    phi = 0.90 

    # Effective Depth
    # Main Axis (Outer Layer): d = h - cover - db/2
    # Minor Axis (Inner Layer): d = h - cover - db_main - db/2 (approx offset 1.6cm)
    d_offset = 0.0 if is_main_dir else 1.6 
    d_eff = h_cm - cover - (d_bar/20.0) - d_offset
    
    # Handle negligible moment
    if M_u < 10:
        return {
            "d": d_eff, "Rn": 0, "rho_req": 0, "As_min": 0, "As_flex": 0, 
            "As_req": 0, "As_prov": 0, "a": 0, "PhiMn": 0, "DC": 0, 
            "Status": True, "Note": "M -> 0", "s_max": 45
        }

    # Strength Design
    Rn = Mu_kgcm / (phi * b_cm * d_eff**2)
    term_val = 1 - (2 * Rn) / (0.85 * fc)
    
    if term_val < 0:
        rho_req = 999 
    else:
        rho_req = (0.85 * fc / fy) * (1 - np.sqrt(term_val))
        
    As_flex = rho_req * b_cm * d_eff
    As_min = 0.0018 * b_cm * h_cm
    As_req_final = max(As_flex, As_min) if rho_req != 999 else 999
    
    # Provided
    Ab_area = np.pi * (d_bar/10.0)**2 / 4.0
    As_prov = (b_cm / s_bar) * Ab_area
    
    # Capacity Check
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
    """
    แสดงรายการคำนวณแบบละเอียดยิบ (Substitution Step-by-Step)
    """
    Mu, b, h, cover, fc, fy, db, s = inputs
    
    st.markdown(f"#### 📐 รายการคำนวณออกแบบ: {zone_name}")
    st.caption(f"Design Parameters: $f_c'={fc}$ ksc, $f_y={fy}$ ksc, $h={h}$ cm")

    step1, step2, step3 = st.tabs(["1. Moment & Depth", "2. Steel Area", "3. Capacity Check"])
    
    with step1:
        st.markdown("**1.1 Design Moment ($M_u$) Calculation**")
        st.write("หาค่าโมเมนต์ดัดออกแบบจากสัมประสิทธิ์ (Coefficient Method):")
        st.latex(f"M_u = (\\text{{Coeff}}) \\times M_o")
        st.latex(f"M_u = {coeff_pct/100:.3f} \\times {Mo_val:,.0f} = \\mathbf{{{Mu:,.0f}}} \\; \\text{{kg-m}}")
        
        st.markdown("**1.2 Effective Depth ($d$)**")
        st.latex(r"d = h - C_{over} - \frac{d_b}{2}")
        st.latex(f"d = {h} - {cover} - \\frac{{{db/10}}}{{2}} = \\mathbf{{{res['d']:.2f}}} \\; \\text{{cm}}")

    with step2:
        st.markdown("**2.1 Required Reinforcement ($A_{s,req}$)**")
        # As min
        st.latex(f"A_{{s,min}} = 0.0018 \\cdot ({b*100:.0f}) \\cdot {h} = {res['As_min']:.2f} \\; \\text{{cm}}^2")
        
        # As flexure
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
    # 🔹 DYNAMIC LABELING LOGIC (Lx/Ly Only)
    # -----------------------------------------------
    if axis_id == "X":
        # Tab X: Span is Lx, Strip Width is Ly
        span_sym = "L_x"
        width_sym = "L_y"
        span_val = L_span
        width_val = L_width
    else:
        # Tab Y: Span is Ly, Strip Width is Lx
        span_sym = "L_y"
        width_sym = "L_x"
        span_val = L_span
        width_val = L_width

    ln_val = span_val - (c_para/100.0)
    w_cs = min(span_val, width_val) / 2.0
    w_ms = width_val - w_cs
    
    # --- PART 1: Mo & DISTRIBUTION ---
    st.markdown(f"### 1️⃣ Analysis: {axis_id}-Direction")
    
    with st.expander(f"📝 ดูที่มาของ $M_o$ และ $M_u$ ({axis_id}-Direction)", expanded=True):
        col_diagram, col_calc = st.columns([1, 1.5])
        
        with col_diagram:
             # Contextual Diagram
            st.info(f"**Definitions for {axis_id}-Axis:**")
            st.markdown(f"""
            - **Span Length ({span_sym}):** {span_val:.2f} m
            - **Strip Width ({width_sym}):** {width_val:.2f} m
            - **Clear Span ($l_n$):** {ln_val:.2f} m
            """)
            st.write(f"*Note: $l_n = {span_sym} - \\text{{Column}}$")
            st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/2/23/Slab_effective_width.svg/300px-Slab_effective_width.svg.png", caption="Span Definitions (ACI)", use_container_width=True)

        with col_calc:
            st.markdown(f"#### Step 1: Total Static Moment ($M_o$)")
            st.latex(r"M_o = \frac{w_u \cdot (\text{Width}) \cdot (\text{Clear Span})^2}{8}")
            # Dynamic LaTeX formula based on Axis
            st.latex(f"M_o = \\frac{{w_u {width_sym} ({span_sym} - c)^2}}{{8}}")
            st.latex(f"M_o = \\frac{{{w_u:,.0f} \\cdot {width_val:.2f} \\cdot ({ln_val:.2f})^2}}{{8}} = \\mathbf{{{Mo:,.0f}}} \\; \\text{{kg-m}}")
        
        st.divider()
        st.markdown(f"#### Step 2: Distribution to $M_u$")
        
        # Helper for % calculation
        def get_pct(val): return (val / Mo * 100) if Mo > 0 else 0
        
        # Distribution Table
        dist_data = [
            {"Pos": "Top (-)", "Strip": "🟥 Column Strip", "% of Mo": f"{get_pct(m_vals['M_cs_neg']):.1f}%", "Mu": m_vals['M_cs_neg']},
            {"Pos": "Top (-)", "Strip": "🟦 Middle Strip", "% of Mo": f"{get_pct(m_vals['M_ms_neg']):.1f}%", "Mu": m_vals['M_ms_neg']},
            {"Pos": "Bot (+)", "Strip": "🟥 Column Strip", "% of Mo": f"{get_pct(m_vals['M_cs_pos']):.1f}%", "Mu": m_vals['M_cs_pos']},
            {"Pos": "Bot (+)", "Strip": "🟦 Middle Strip", "% of Mo": f"{get_pct(m_vals['M_ms_pos']):.1f}%", "Mu": m_vals['M_ms_pos']},
        ]
        st.dataframe(pd.DataFrame(dist_data).style.format({"Mu": "{:,.0f}"}), use_container_width=True, hide_index=True)

    # ==========================================================
    # 2️⃣ PUNCHING SHEAR CHECK (NEW ADDITION)
    # ==========================================================
    if HAS_CALC and HAS_PLOTS:
        st.markdown("---")
        st.markdown("### 2️⃣ Punching Shear Check (ตรวจสอบแรงเฉือนทะลุ)")
        
        # 1. Prepare Data for Punching Check
        # Assumption: For the DDM tab, we approximate the check using current tab's geometry
        # L1 = Span, L2 = Width, c1 = c_para, c2 = c_para (Square assumption if not provided)
        c_col = c_para # cm
        
        load_area = (span_val * width_val) - ((c_col/100) * (c_col/100))
        Vu_approx = w_u * load_area # Factored Load from Main input
        
        # 2. Perform Check
        ps_res = calc.check_punching_shear(
            Vu_kg=Vu_approx, 
            fc=fc, 
            h_slab=h_slab, 
            c1_cm=c_col, 
            c2_cm=c_col, 
            cover=cover, 
            d_bar_mm=12 # Assumption for check
        )
        
        # 3. Display Results
        col_p1, col_p2 = st.columns([1, 1.5])
        
        with col_p1:
            st.pyplot(ddm_plots.plot_punching_shear_geometry(
                c_col, c_col, ps_res['d_avg'], ps_res['bo'], ps_res['status'], ps_res['ratio']
            ))
        
        with col_p2:
            if ps_res['status'] == "OK":
                st.success(f"✅ **PASSED** (Ratio: {ps_res['ratio']:.2f})")
            else:
                st.error(f"❌ **FAILED** (Ratio: {ps_res['ratio']:.2f})")
                st.warning("⚠️ แนะนำ: เพิ่มความหนาพื้น, เพิ่มขนาดเสา, หรือใส่ Drop Panel")
            
            with st.expander("แสดงรายการคำนวณ (Calculation Details)", expanded=True):
                st.write(f"**1. Factored Shear ($V_u$):** {ps_res['Vu']:,.0f} kg")
                st.latex(r"d_{avg} = h - cover - d_b = " + f"{ps_res['d_avg']:.2f}" + " cm")
                st.latex(r"b_o = 2(c_1+d) + 2(c_2+d) = " + f"{ps_res['bo']:.2f}" + " cm")
                
                st.write("**2. Concrete Capacity ($V_c$):**")
                st.latex(r"\phi V_c = 0.85 \times " + f"{ps_res['Vc_nominal']:,.0f} = " + f"\\mathbf{{{ps_res['phi_Vc']:,.0f}}}" + " kg")
                
                st.write("**3. Check:**")
                st.latex(rf"{ps_res['Vu']:,.0f} \le {ps_res['phi_Vc']:,.0f} \rightarrow \text{{{ps_res['status']}}}")

            # Suggest Drop Panel
            if ps_res['status'] == "FAIL":
                req_Vc = ps_res['Vu'] / 0.85
                req_d = req_Vc / (1.06 * np.sqrt(fc) * ps_res['bo']) # Approximate
                req_h = req_d + cover + 1.2
                add_h = req_h - h_slab
                st.info(f"💡 **Recommendation:** Need Drop Panel thickness >= {add_h:.1f} cm (Total thickness {req_h:.1f} cm)")
                
    elif not HAS_CALC:
        st.warning("⚠️ module 'calculations.py' not found. Skipping Punching Shear Check.")

    # --- PART 3: INPUTS (Renumbered to 3) ---
    st.markdown("---")
    st.markdown("### 3️⃣ Reinforcement Selection")
    
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
    # ⚠️ KEY MAPPING: กำหนด Key ให้ตรงกับที่ ddm_plots.py ต้องการ (CS_Top, CS_Bot, MS_Top, MS_Bot)
    calc_configs = [
        {"Label": "Col Strip - Top (-)", "PlotKey": "CS_Top", "Mu": m_vals['M_cs_neg'], "b": w_cs, "db": d_cst, "s": s_cst},
        {"Label": "Col Strip - Bot (+)", "PlotKey": "CS_Bot", "Mu": m_vals['M_cs_pos'], "b": w_cs, "db": d_csb, "s": s_csb},
        {"Label": "Mid Strip - Top (-)", "PlotKey": "MS_Top", "Mu": m_vals['M_ms_neg'], "b": w_ms, "db": d_mst, "s": s_mst},
        {"Label": "Mid Strip - Bot (+)", "PlotKey": "MS_Bot", "Mu": m_vals['M_ms_pos'], "b": w_ms, "db": d_msb, "s": s_msb},
    ]

    results = []
    for cfg in calc_configs:
        res = calc_rebar_logic(cfg['Mu'], cfg['b'], cfg['db'], cfg['s'], h_slab, cover, fc, fy, is_main_dir)
        res.update(cfg) # Merge config into result
        results.append(res)

    # --- PART 4: SUMMARY ---
    st.write("")
    st.markdown("### 4️⃣ Verification Table")
    
    df_show = pd.DataFrame(results)
    st.dataframe(
        df_show[["Label", "Mu", "d", "As_req", "As_prov", "PhiMn", "DC", "Note"]].style.format({
            "Mu": "{:,.0f}", "d": "{:.2f}", "As_req": "{:.2f}", "As_prov": "{:.2f}", 
            "PhiMn": "{:,.0f}", "DC": "{:.2f}"
        }).background_gradient(subset=["DC"], cmap="RdYlGn_r", vmin=0, vmax=1.2),
        use_container_width=True
    )

    # --- PART 5: DETAILED CALCULATION SHEET ---
    st.markdown("---")
    st.markdown("### 5️⃣ Detailed Calculation Sheet")
    
    sel_label = st.selectbox(f"Select Zone to View Details ({axis_id}):", [r['Label'] for r in results])
    target = next(r for r in results if r['Label'] == sel_label)
    
    # Inputs for detailed renderer
    raw_inputs = (target['Mu'], target['b'], h_slab, cover, fc, fy, target['db'], target['s'])
    
    with st.container(border=True):
        # Calculate % for display inside the calc sheet
        pct_val = (target['Mu'] / Mo * 100) if Mo > 0 else 0
        show_detailed_calculation(sel_label, target, raw_inputs, pct_val, Mo)

    # --- DRAWINGS ---
    if HAS_PLOTS:
        st.markdown("---")
        t1, t2, t3 = st.tabs(["📉 Moment Diagram", "🏗️ Section Detail", "📐 Plan View"])
        
        # ⚠️ สร้าง Map โดยใช้ Key ที่ตรงกับ ddm_plots (CS_Top, CS_Bot, MS_Top, MS_Bot)
        rebar_map = {r['PlotKey']: f"DB{r['db']}@{r['s']:.0f}" for r in results}
        
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
