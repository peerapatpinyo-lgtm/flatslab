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
    """
     คำนวณออกแบบเหล็กเสริม (RC Slab Design) ตาม ACI 318 / WSD/SDM
     Return: Dictionary ค่าตัวแปรทั้งหมดเพื่อนำไปแสดงผล
    """
    # 1. Unit Conversions & Constants
    b_cm = b_width * 100.0
    h_cm = float(h_slab)
    Mu_kgcm = M_u * 100.0  # kg-m -> kg-cm
    phi = 0.90 # Flexure factor

    # 2. Effective Depth (d)
    # Main Axis: d = h - cover - db/2
    # Minor Axis: d = h - cover - db_main - db/2 (Assuming db_main ~ 1.6cm)
    d_offset = 0.0 if is_main_dir else 1.6 
    d_eff = h_cm - cover - (d_bar/20.0) - d_offset
    
    # Handle negligible moment
    if M_u < 10:
        return {
            "d": d_eff, "Rn": 0, "rho_req": 0, "As_min": 0, "As_flex": 0, 
            "As_req": 0, "As_prov": 0, "a": 0, "PhiMn": 0, "DC": 0, 
            "Status": True, "Note": "M -> 0", "s_max": 45
        }

    # 3. Required Steel (Strength Design)
    # Rn = Mu / (phi * b * d^2)
    Rn = Mu_kgcm / (phi * b_cm * d_eff**2) # ksc
    
    # Check Ductility Limit (0.85 fc')
    term_val = 1 - (2 * Rn) / (0.85 * fc)
    if term_val < 0:
        rho_req = 999 # Section too small
    else:
        rho_req = (0.85 * fc / fy) * (1 - np.sqrt(term_val))
        
    As_flex = rho_req * b_cm * d_eff
    
    # 4. Minimum Steel (Temp & Shrinkage)
    As_min = 0.0018 * b_cm * h_cm
    
    # Final As Required
    As_req_final = max(As_flex, As_min) if rho_req != 999 else 999
    
    # 5. Provided Steel
    Ab_area = np.pi * (d_bar/10.0)**2 / 4.0
    As_prov = (b_cm / s_bar) * Ab_area
    
    # 6. Capacity Check (Phi Mn)
    if rho_req == 999:
        PhiMn = 0; a_depth = 0; dc_ratio = 999
    else:
        # a = (As * fy) / (0.85 * fc * b)
        a_depth = (As_prov * fy) / (0.85 * fc * b_cm)
        # Mn = As * fy * (d - a/2)
        Mn = As_prov * fy * (d_eff - a_depth/2.0)
        PhiMn = phi * Mn / 100.0 # Convert kg-cm -> kg-m
        dc_ratio = M_u / PhiMn if PhiMn > 0 else 999

    # 7. Code Checks
    s_max = min(2 * h_cm, 45.0)
    
    checks = []
    if dc_ratio > 1.0: checks.append("Insuff. Strength")
    if As_prov < As_min: checks.append("As < As,min")
    if s_bar > s_max: checks.append("Spacing > Max")
    if rho_req == 999: checks.append("Section Fail")
    
    return {
        "d": d_eff, "Rn": Rn, "rho_req": rho_req, "As_min": As_min, "As_flex": As_flex,
        "As_req": As_req_final, "As_prov": As_prov, "a": a_depth, 
        "PhiMn": PhiMn, "DC": dc_ratio, "Status": len(checks) == 0, 
        "Note": ", ".join(checks) if checks else "OK", "s_max": s_max
    }

# ========================================================
# 2. HELPER: DETAILED MATH RENDERER
# ========================================================
def show_detailed_calculation(zone_name, res, inputs, mat):
    """
    แสดงรายการคำนวณแบบละเอียด (Substitution) สำหรับ Zone ที่เลือก
    """
    Mu, b, h, cover, fc, fy, db, s = inputs
    
    st.markdown(f"#### 📐 รายการคำนวณออกแบบ: {zone_name}")
    st.caption(f"Design Parameters: $f_c'={fc}$ ksc, $f_y={fy}$ ksc, Slab Thickness $h={h}$ cm")

    # TABS FOR STEPS
    step1, step2, step3 = st.tabs(["1. Geometry & Loads", "2. Steel Calculation", "3. Capacity Check"])
    
    with step1:
        st.markdown("**1.1 Design Moment ($M_u$)**")
        st.latex(f"M_u = \\mathbf{{{Mu:,.0f}}} \\; \\text{{kg-m}}")
        
        st.markdown("**1.2 Effective Depth ($d$)**")
        st.write(f"สมมติเหล็กเสริม {db}mm หุ้มคอนกรีต {cover}cm")
        # Determine explanation for d calculation based on value
        # Simple rendering of the formula used in logic
        st.latex(r"d = h - C_{over} - \frac{d_b}{2} - (\text{Layer Offset})")
        st.latex(f"d = {h} - {cover} - \\frac{{{db/10}}}{{2}} - ... = \\mathbf{{{res['d']:.2f}}} \\; \\text{{cm}}")

    with step2:
        st.markdown("**2.1 Required Reinforcement ($A_{s,req}$)**")
        # Show As_min
        st.latex(r"A_{s,min} = 0.0018 \cdot b \cdot h")
        st.latex(f"A_{{s,min}} = 0.0018 \\cdot {b*100:.0f} \\cdot {h} = \\mathbf{{{res['As_min']:.2f}}} \\; \\text{{cm}}^2")
        
        # Show Flexural As (Conceptual)
        st.markdown("คำนวณ $A_{s,flex}$ จากสมการกำลัง ($M_u$):")
        st.latex(f"R_n = \\frac{{M_u}}{{\\phi b d^2}} = {res['Rn']:.2f} \\; \\text{{ksc}}")
        st.latex(f"\\rho_{{req}} = \\frac{{0.85 f_c'}}{{f_y}} \\left( 1 - \\sqrt{{1 - \\frac{{2 R_n}}{{0.85 f_c'}}}} \\right) \\rightarrow A_{{s,flex}} = {res['As_flex']:.2f} \\; \\text{{cm}}^2")
        
        st.markdown(f"**Conclusion:** $A_{{s,req}} = \\max({res['As_min']:.2f}, {res['As_flex']:.2f}) = \\mathbf{{{res['As_req']:.2f}}} \\; \\text{{cm}}^2$")

    with step3:
        st.markdown("**3.1 Provided Reinforcement ($A_{s,prov}$)**")
        st.write(f"เลือกใช้เหล็ก: **DB{db} @ {s:.0f} cm**")
        st.latex(r"A_{s,prov} = \frac{b}{s} \cdot A_{bar}")
        bar_area = 3.1416 * (db/10)**2 / 4
        st.latex(f"A_{{s,prov}} = \\frac{{{b*100:.0f}}}{{{s:.0f}}} \\cdot {bar_area:.2f} = \\mathbf{{{res['As_prov']:.2f}}} \\; \\text{{cm}}^2")
        
        st.markdown("**3.2 Moment Capacity ($\\phi M_n$)**")
        st.latex(r"a = \frac{A_{s,prov} f_y}{0.85 f_c' b}")
        st.latex(f"a = \\frac{{{res['As_prov']:.2f} \\cdot {fy}}}{{0.85 \\cdot {fc} \\cdot {b*100:.0f}}} = \\mathbf{{{res['a']:.2f}}} \\; \\text{{cm}}")
        
        st.latex(r"\phi M_n = \phi A_s f_y (d - a/2)")
        st.latex(f"\\phi M_n = 0.9 \\cdot {res['As_prov']:.2f} \\cdot {fy} \\cdot ({res['d']:.2f} - {res['a']:.2f}/2) / 100")
        st.latex(f"\\phi M_n = \\mathbf{{{res['PhiMn']:,.0f}}} \\; \\text{{kg-m}}")
        
        # Check
        result_color = "green" if res['DC'] <= 1.0 else "red"
        status_icon = "✅ OK" if res['DC'] <= 1.0 else "❌ NOT SAFE"
        st.markdown(f"### Result: $M_u / \\phi M_n = {res['DC']:.2f}$ ... :{result_color}[{status_icon}]")

# ========================================================
# 3. RENDER UI FUNCTION
# ========================================================
def render_interactive_direction(data, h_slab, cover, fc, fy, axis_id, w_u, is_main_dir):
    L_span = data['L_span']
    L_width = data['L_width']
    c_para = data['c_para']
    Mo = data['Mo']
    m_vals = data['M_vals']
    
    # Notation Map
    l1 = L_span  # Span Length
    l2 = L_width # Transverse Width
    ln = l1 - (c_para/100.0)

    # Calculate Strip Widths
    w_cs = min(l1, l2) / 2.0
    w_ms = l2 - w_cs
    
    # --- PART 1: MOMENT ANALYSIS ---
    st.markdown(f"### 1️⃣ Analysis: {axis_id}-Direction")
    
    # 1.1 Mo Calculation
    with st.expander("📝 1. Static Moment Calculation ($M_o$)", expanded=False):
        c1, c2 = st.columns([1, 1.5])
        with c1:
            st.info(f"**Parameters:**\n- $l_1$ (Span) = {l1} m\n- $l_2$ (Width) = {l2} m\n- $l_n$ (Clear) = {ln:.2f} m")
            st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/2/23/Slab_effective_width.svg/300px-Slab_effective_width.svg.png", use_column_width=True)
        with c2:
            st.markdown("**Calculation:**")
            st.latex(r"M_o = \frac{w_u l_2 l_n^2}{8}")
            st.latex(f"M_o = \\frac{{{w_u:,.0f} \\cdot {l2:.2f} \\cdot {ln:.2f}^2}}{{8}} = \\mathbf{{{Mo:,.0f}}} \\; \\text{{kg-m}}")

    # 1.2 Moment Distribution Table
    with st.expander("📊 2. Moment Distribution Coefficients (ACI 318)", expanded=False):
        st.write("ตารางแสดงสัมประสิทธิ์ที่ใช้แปลงค่า $M_o$ เป็น $M_u$ ในแต่ละตำแหน่ง")
        
        # Helper to get Coeff
        def get_coeff(mu, mo): return mu/mo if mo > 0 else 0
        
        dist_data = [
            {"Zone": "Column Strip - Neg (Sup)", "Mu": m_vals['M_cs_neg'], "Coeff": get_coeff(m_vals['M_cs_neg'], Mo)},
            {"Zone": "Column Strip - Pos (Mid)", "Mu": m_vals['M_cs_pos'], "Coeff": get_coeff(m_vals['M_cs_pos'], Mo)},
            {"Zone": "Middle Strip - Neg (Sup)", "Mu": m_vals['M_ms_neg'], "Coeff": get_coeff(m_vals['M_ms_neg'], Mo)},
            {"Zone": "Middle Strip - Pos (Mid)", "Mu": m_vals['M_ms_pos'], "Coeff": get_coeff(m_vals['M_ms_pos'], Mo)},
        ]
        df_dist = pd.DataFrame(dist_data)
        df_dist["% of Mo"] = df_dist["Coeff"].apply(lambda x: f"{x*100:.1f}%")
        df_dist["Mu (kg-m)"] = df_dist["Mu"].apply(lambda x: f"{x:,.0f}")
        st.table(df_dist[["Zone", "% of Mo", "Mu (kg-m)"]])

    # --- PART 2: REBAR SELECTION (INPUTS) ---
    st.markdown("---")
    st.markdown("### 2️⃣ Reinforcement Design")
    
    col_cs, col_gap, col_ms = st.columns([1, 0.05, 1])
    
    # --- LEFT: COLUMN STRIP ---
    with col_cs:
        st.markdown(f"""<div style="text-align:center; background-color:#ffebee; padding:5px; border-radius:5px; border:1px solid #ffcdd2;">
            <b style="color:#c62828;">🟥 COLUMN STRIP</b><br><small>b = {w_cs*100:.0f} cm</small></div>""", unsafe_allow_html=True)
        
        st.markdown(f"**Top ($M_u$={m_vals['M_cs_neg']:,.0f}):**")
        c1, c2 = st.columns([1,1])
        d_cst = c1.selectbox("DB", [10,12,16,20,25], 2, key=f"d_cst_{axis_id}", label_visibility="collapsed")
        s_cst = c2.selectbox("@", [10,15,20,25,30], 2, key=f"s_cst_{axis_id}", label_visibility="collapsed")
        
        st.markdown(f"**Bot ($M_u$={m_vals['M_cs_pos']:,.0f}):**")
        c1, c2 = st.columns([1,1])
        d_csb = c1.selectbox("DB", [10,12,16,20,25], 1, key=f"d_csb_{axis_id}", label_visibility="collapsed")
        s_csb = c2.selectbox("@", [10,15,20,25,30], 3, key=f"s_csb_{axis_id}", label_visibility="collapsed")

    # --- RIGHT: MIDDLE STRIP ---
    with col_ms:
        st.markdown(f"""<div style="text-align:center; background-color:#e3f2fd; padding:5px; border-radius:5px; border:1px solid #bbdefb;">
            <b style="color:#1565c0;">🟦 MIDDLE STRIP</b><br><small>b = {w_ms*100:.0f} cm</small></div>""", unsafe_allow_html=True)
        
        st.markdown(f"**Top ($M_u$={m_vals['M_ms_neg']:,.0f}):**")
        c1, c2 = st.columns([1,1])
        d_mst = c1.selectbox("DB", [10,12,16,20,25], 0, key=f"d_mst_{axis_id}", label_visibility="collapsed")
        s_mst = c2.selectbox("@", [10,15,20,25,30], 3, key=f"s_mst_{axis_id}", label_visibility="collapsed")
        
        st.markdown(f"**Bot ($M_u$={m_vals['M_ms_pos']:,.0f}):**")
        c1, c2 = st.columns([1,1])
        d_msb = c1.selectbox("DB", [10,12,16,20,25], 0, key=f"d_msb_{axis_id}", label_visibility="collapsed")
        s_msb = c2.selectbox("@", [10,15,20,25,30], 3, key=f"s_msb_{axis_id}", label_visibility="collapsed")

    # --- PROCESS CALCULATIONS ---
    inputs_map = [
        ("CS-Top", m_vals['M_cs_neg'], w_cs, d_cst, s_cst),
        ("CS-Bot", m_vals['M_cs_pos'], w_cs, d_csb, s_csb),
        ("MS-Top", m_vals['M_ms_neg'], w_ms, d_mst, s_mst),
        ("MS-Bot", m_vals['M_ms_pos'], w_ms, d_msb, s_msb),
    ]
    
    results = []
    for label, mu, bw, db, s in inputs_map:
        res = calc_rebar_logic(mu, bw, db, s, h_slab, cover, fc, fy, is_main_dir)
        res['Label'] = label
        res['Input_Raw'] = (mu, bw, h_slab, cover, fc, fy, db, s) # Keep for detailed calc
        results.append(res)
    
    # --- PART 3: SUMMARY TABLE ---
    st.write("")
    st.markdown("### 3️⃣ Verification Summary")
    df = pd.DataFrame(results)
    
    # Create Display DF
    df_show = pd.DataFrame({
        "Zone": df['Label'],
        "Mu (kg-m)": df['Input_Raw'].apply(lambda x: f"{x[0]:,.0f}"),
        "Use": df.apply(lambda r: f"DB{r['Input_Raw'][6]}@{r['Input_Raw'][7]:.0f}", axis=1),
        "d (cm)": df['d'],
        "As,req": df['As_req'],
        "As,prov": df['As_prov'],
        "φMn (kg-m)": df['PhiMn'],
        "D/C Ratio": df['DC']
    })
    
    st.dataframe(
        df_show.style.format({
            "d (cm)": "{:.2f}", "As,req": "{:.2f}", "As,prov": "{:.2f}", 
            "φMn (kg-m)": "{:,.0f}", "D/C Ratio": "{:.2f}"
        }).background_gradient(subset=["D/C Ratio"], cmap="RdYlGn_r", vmin=0, vmax=1.2),
        use_container_width=True
    )

    # --- PART 4: DEEP DIVE CALCULATION ---
    st.markdown("---")
    st.markdown("### 4️⃣ Detailed Calculation Sheet")
    
    # Dropdown to choose which zone to inspect
    zone_options = [r['Label'] for r in results]
    selected_zone = st.selectbox("เลือกดูรายการคำนวณของ (Select Zone):", zone_options)
    
    # Find data for selected zone
    target_res = next(r for r in results if r['Label'] == selected_zone)
    
    # Render the detailed Math
    with st.container(border=True):
        show_detailed_calculation(selected_zone, target_res, target_res['Input_Raw'], None)

    # --- PART 5: DRAWINGS ---
    if HAS_PLOTS:
        st.markdown("---")
        st.markdown("### 5️⃣ Drawings")
        t1, t2 = st.tabs(["Moment Diagram", "Rebar Detailing"])
        with t1:
            st.pyplot(ddm_plots.plot_ddm_moment(l1, c_para/100, m_vals))
        with t2:
            rebar_map = {r['Label'].replace("-","_"): f"DB{r['Input_Raw'][6]}@{r['Input_Raw'][7]:.0f}" for r in results}
            st.pyplot(ddm_plots.plot_rebar_detailing(l1, h_slab, c_para, rebar_map, axis_id))

# ========================================================
# MAIN APP ENTRY
# ========================================================
def render_dual(data_x, data_y, mat_props, w_u):
    st.markdown("## 🏗️ RC Slab Design (DDM Method)")
    st.info("Input reinforcement data below. Calculations utilize ACI 318 / EIT Standard.")

    tab_x, tab_y = st.tabs([
        f"➡️ X-Direction (Span {data_x['L_span']} m)", 
        f"⬆️ Y-Direction (Span {data_y['L_span']} m)"
    ])
    
    with tab_x:
        render_interactive_direction(data_x, mat_props['h_slab'], mat_props['cover'], mat_props['fc'], mat_props['fy'], "X", w_u, True)
    
    with tab_y:
        render_interactive_direction(data_y, mat_props['h_slab'], mat_props['cover'], mat_props['fc'], mat_props['fy'], "Y", w_u, False)
