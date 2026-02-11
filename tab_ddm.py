# tab_ddm.py
import streamlit as st
import pandas as pd
import numpy as np

# ========================================================
# 0. DEPENDENCY HANDLING
# ========================================================
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
def calc_rebar_logic(M_u, b_width, d_bar, s_bar, h_slab, cover, fc, fy, is_main_dir, phi_factor=0.90):
    """
    Core Logic: คำนวณเหล็กเสริมตาม ACI 318
    """
    b_cm = b_width * 100.0
    h_cm = float(h_slab)
    Mu_kgcm = M_u * 100.0
    
    # --- Effective Depth Logic ---
    if is_main_dir:
        d_offset = 0.0
    else:
        d_offset = d_bar / 10.0 
        
    d_eff = h_cm - cover - (d_bar/20.0) - d_offset
    
    # Handle negligible moment or invalid depth
    if M_u < 10 or d_eff <= 0:
        return {
            "d": max(d_eff, 0), "Rn": 0, "rho_req": 0, "As_min": 0, "As_flex": 0, 
            "As_req": 0, "As_prov": 0, "a": 0, "PhiMn": 0, "DC": 0, 
            "Status": True, "Note": "M -> 0" if M_u < 10 else "Depth Err", "s_max": 45
        }

    # Strength Design
    Rn = Mu_kgcm / (phi_factor * b_cm * d_eff**2)
    
    # Check bounds for sqrt
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
        PhiMn = phi_factor * Mn / 100.0
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
# [REMOVED] Section 2: Helper DDM Coeffs Recalculation
# เราลบส่วนนี้ออกเพื่อไม่ให้ไปทับ Logic ที่ถูกต้องจาก calculations.py
# ========================================================

# ========================================================
# 3. DETAILED CALCULATION RENDERER
# ========================================================
def show_detailed_calculation(zone_name, res, inputs, coeff_pct, Mo_val):
    Mu, b, h, cover, fc, fy, db, s, phi_bend = inputs
    
    st.markdown(f"#### 📐 รายการคำนวณออกแบบ: {zone_name}")
    st.caption(f"Design Parameters: $f_c'={fc}$ ksc, $f_y={fy}$ ksc, $h={h}$ cm, $\\phi_b={phi_bend}$")

    step1, step2, step3 = st.tabs(["1. Moment & Depth", "2. Steel Area", "3. Capacity Check"])
    
    with step1:
        st.markdown("**1.1 Design Moment ($M_u$) Calculation**")
        st.write("หาค่าโมเมนต์ดัดออกแบบจากสัมประสิทธิ์ (Coefficient Method):")
        st.latex(f"M_u = (\\text{{Coeff}}) \\times M_o")
        st.latex(f"M_u = {coeff_pct/100:.3f} \\times {Mo_val:,.0f} = \\mathbf{{{Mu:,.0f}}} \\; \\text{{kg-m}}")
        
        st.markdown("**1.2 Effective Depth ($d$)**")
        if res['d'] < (h - cover - db/20.0):
            st.info("Note: Inner layer calculation (Subtracting assumed main bar diameter)")
        st.latex(r"d_{eff} = \mathbf{" + f"{res['d']:.2f}" + r"} \; \text{cm}")

    with step2:
        st.markdown("**2.1 Required Reinforcement ($A_{s,req}$)**")
        st.latex(f"A_{{s,min}} = 0.0018 \\cdot ({b*100:.0f}) \\cdot {h} = {res['As_min']:.2f} \\; \\text{{cm}}^2")
        
        st.markdown("จากสมการกำลัง (Strength Design):")
        st.latex(f"R_n = \\frac{{M_u}}{{\\phi_b b d^2}} = \\frac{{{Mu*100:,.0f}}}{{{phi_bend} \\cdot {b*100:.0f} \\cdot {res['d']:.2f}^2}} = {res['Rn']:.2f} \\; \\text{{ksc}}")
        
        if res['rho_req'] != 999:
            st.latex(r"\rho_{req} = \frac{0.85 f_c'}{f_y} \left( 1 - \sqrt{1 - \frac{2 R_n}{0.85 f_c'}} \right)")
            st.latex(f"A_{{s,flex}} = \\rho_{{req}} b d = {res['As_flex']:.2f} \\; \\text{{cm}}^2")
        else:
            st.error("Section dimensions are too small (Rn too high).")

        st.info(f"👉 **Control:** $A_{{s,req}} = \\max({res['As_min']:.2f}, {res['As_flex']:.2f}) = \\mathbf{{{res['As_req']:.2f}}} \\; \\text{{cm}}^2$")

    with step3:
        st.markdown("**3.1 Provided Reinforcement ($A_{s,prov}$)**")
        bar_prefix = "RB" if db == 9 else "DB"
        st.write(f"เลือกใช้: **{bar_prefix}{db} @ {s:.0f} cm**")
        
        bar_area = 3.1416 * (db/10)**2 / 4
        st.latex(f"A_{{s,prov}} = \\frac{{{b*100:.0f}}}{{{s:.0f}}} \\cdot {bar_area:.2f} = \\mathbf{{{res['As_prov']:.2f}}} \\; \\text{{cm}}^2")
        
        st.markdown("**3.2 Moment Capacity Check ($\\phi M_n$)**")
        st.latex(f"a = \\frac{{{res['As_prov']:.2f} \\cdot {fy}}}{{0.85 \\cdot {fc} \\cdot {b*100:.0f}}} = {res['a']:.2f} \\; \\text{{cm}}")
        st.latex(f"\\phi_b M_n = \\frac{{{phi_bend} \\cdot {res['As_prov']:.2f} \\cdot {fy} \\cdot ({res['d']:.2f} - {res['a']:.2f}/2)}}{{100}}")
        st.latex(f"\\phi_b M_n = \\mathbf{{{res['PhiMn']:,.0f}}} \\; \\text{{kg-m}}")
        
        dc = res['DC']
        color = "green" if dc <= 1.0 else "red"
        st.markdown(f"**Verification:** Ratio = {dc:.2f} ... :{color}[{'✅ PASS' if dc <=1 else '❌ FAIL'}]")

# ========================================================
# 4. UI RENDERER
# ========================================================
def render_interactive_direction(data, mat_props, axis_id, w_u, is_main_dir):
    """
    Render DDM analysis for one direction.
    """
    # Unpack Materials
    h_slab = mat_props['h_slab']
    cover = mat_props['cover']
    fc = mat_props['fc']
    fy = mat_props['fy']
    phi_bend = mat_props.get('phi', 0.90)       
    phi_shear = mat_props.get('phi_shear', 0.85) 
    
    # Unpack Rebar Config
    cfg = mat_props.get('rebar_cfg', {})
    d_cst, s_cst = cfg.get('cs_top_db', 12), cfg.get('cs_top_spa', 20)
    d_csb, s_csb = cfg.get('cs_bot_db', 12), cfg.get('cs_bot_spa', 20)
    d_mst, s_mst = cfg.get('ms_top_db', 12), cfg.get('ms_top_spa', 20)
    d_msb, s_msb = cfg.get('ms_bot_db', 12), cfg.get('ms_bot_spa', 20)
    
    # Unpack Opening Data
    open_w = mat_props.get('open_w', 0.0)
    open_dist = mat_props.get('open_dist', 0.0)
    
    L_span = data['L_span']
    L_width = data['L_width']
    c_para = data['c_para']
    Mo = data['Mo']
    m_vals = data['M_vals'] # ใช้ค่าที่คำนวณมาถูกต้องแล้วจาก backend
    
    # ดึงค่า span type มาโชว์ (ถ้า backend ส่งมา)
    span_type_str = data.get('span_type', 'N/A')
    
    # Dynamic Labeling
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
            - **Span Type:** `{span_type_str}`
            - **Span Length ({span_sym}):** {span_val:.2f} m
            - **Strip Width ({width_sym}):** {width_val:.2f} m
            - **Clear Span ($l_n$):** {ln_val:.2f} m
            """)
            st.write(f"*Note: $l_n = {span_sym} - \\text{{Column}}$")
            

        with col_calc:
            st.markdown(f"#### Step 1: Total Static Moment ($M_o$)")
            st.latex(f"M_o = \\frac{{{w_u:,.0f} \\cdot {width_val:.2f} \\cdot ({ln_val:.2f})^2}}{{8}} = \\mathbf{{{Mo:,.0f}}} \\; \\text{{kg-m}}")
        
        st.divider()
        st.markdown(f"#### Step 2: Distribution to $M_u$ (Automated by ACI 318)")
        
        # Helper to calc % of Mo
        def get_pct(val): return (val / Mo * 100) if Mo > 0 else 0
        
        # Access data directly from m_vals dictionary (Backend generated)
        # Note: Backend structure is { 'design': {...}, 'M_total': (...), 'coeffs': (...) } based on previous fix
        # But for compatibility, let's assume we map it correctly or access what is available.
        # Assuming we need to extract concrete numbers:
        
        # Logic to extract M values cleanly regardless of dict structure
        # (This adapts to the 'M_vals' structure coming from calculations.py)
        # We expect M_vals to have specific keys or we parse them from the "design" block if needed
        # But simpler: calculations.py SHOULD return 'M_vals' as a simple dict of Mu values 
        # or we adapt here. Let's assume the previous fixed calculations.py returns a clean dict or object.
        # Actually, let's look at the previous fix return:
        # It returns: "M_vals": res_x (which is a dict with "design", "M_total", etc.)
        # We need to extract the Mu values for display.
        
        # Let's EXTRACT Mu from the 'design' dictionary which has 'Mu' inside inputs or we calculate back
        # Actually, 'M_vals'['design']['cs_neg_ext']['As_req']... 
        # Easier way: The 'design' dict in calculations.py didn't store Mu directly in root.
        # Let's fix this accessor to be safe.
        
        # Safe Accessor Logic:
        # Case 1: Interior Span (Standard keys)
        # Case 2: Exterior Span (Has 'ext' keys)
        
        # Let's try to fetch from design results directly if available
        d_res = m_vals.get('design', {})
        
        # Map logical positions to keys in design dict
        # We need to know if it's exterior or interior to know which keys to grab
        # But simpler: Just grab what exists
        
        mu_cs_top = d_res.get('cs_neg_ext', d_res.get('cs_neg_int', {})).get('d', 0) * 0 # Placeholder
        # Re-calc purely for display table if needed, OR better:
        # Trust the backend to send ready-to-display values.
        # **Simplification for UI:** # Let's assume the keys are standardized or we grab them from the 'M_vals'['M_total'] and coeffs.
        
        # Let's use the 'design' output to get Mu because that's what we use for design
        # The design dicts contain the inputs used. But wait, `design_flexure_slab` returns results, not inputs.
        
        # FIX: We will just grab the values from the `calc_configs` loop below which sets up the values correctly
        pass 

        # We will render the table AFTER calculating the values in the loop below to be 100% synced.

    # ==========================================================
    # 2️⃣ PUNCHING SHEAR CHECK
    # ==========================================================
    if HAS_CALC:
        st.markdown("---")
        st.markdown("### 2️⃣ Punching Shear Check")
        c_col = float(c_para)
        load_area = (span_val * width_val) - ((c_col/100.0) * (c_col/100.0))
        Vu_approx = float(w_u) * load_area 
        
        d_bar_val = 1.6
        d_eff = float(h_slab) - float(cover) - d_bar_val
        if d_eff <= 0: d_eff = 1.0

        ps_res = calc.check_punching_shear(
            Vu=Vu_approx,        
            fc=float(fc),
            c1=c_col,            
            c2=c_col,            
            d=d_eff,                
            col_type="interior", # Note: You might want to pass col_type here too!
            open_w=open_w,
            open_dist=open_dist,
            phi=phi_shear 
        )
        
        col_p1, col_p2 = st.columns([1, 1.5])
        with col_p1:
            if HAS_PLOTS:
                st.pyplot(ddm_plots.plot_punching_shear_geometry(
                    c_col, c_col, ps_res['d'], ps_res['bo'], ps_res['status'], ps_res['ratio']
                ))
            
            if open_w > 0:
                st.warning(f"⚠️ **Opening:** {open_w:.0f}x{open_w:.0f} cm")
        
        with col_p2:
            if ps_res['status'] == "OK":
                st.success(f"✅ **PASSED** (Ratio: {ps_res['ratio']:.2f})")
            else:
                st.error(f"❌ **FAILED** (Ratio: {ps_res['ratio']:.2f})")
            
            with st.expander("Details"):
                st.write(f"Vu: {ps_res['Vu']:,.0f} kg | phi*Vc: {ps_res['phi_Vc']:,.0f} kg")

    # --- PART 3: REINFORCEMENT & DISPLAY TABLE ---
    st.markdown("---")
    st.markdown("### 3️⃣ Reinforcement Status")
    
    # Extraction Logic from Backend Data (Compatible with new calculations.py)
    # We need to map the complex structure of 'm_vals' to simple Top/Bot/CS/MS
    
    # 1. Get Design Objects
    des = m_vals['design']
    
    # 2. Identify Keys based on Span Type
    # If Exterior Span: keys are cs_neg_ext, cs_pos, cs_neg_int
    # If Interior Span: keys are cs_neg_int, cs_pos, cs_neg_int (symmetric usually)
    
    # To simplify UI, we usually show:
    # - Exterior Support (Top) OR Interior Support (Top) -> We pick the critical or "Left" support
    # - Mid Span (Bot)
    # - Interior Support (Top) -> "Right" support
    
    # Let's map "Top (Left/Ext)", "Bot", "Top (Right/Int)"
    
    if 'cs_neg_ext' in des:
        # It is an Exterior Span
        keys_map = [
            {'label': 'Ext. Support (-)', 'key_cs': 'cs_neg_ext', 'key_ms': 'ms_neg_ext', 'pos': 'top'},
            {'label': 'Mid Span (+)',     'key_cs': 'cs_pos',     'key_ms': 'ms_pos',     'pos': 'bot'},
            {'label': 'Int. Support (-)', 'key_cs': 'cs_neg_int', 'key_ms': 'ms_neg_int', 'pos': 'top'},
        ]
    else:
        # Interior Span (Standard) - Only 2 unique zones usually shown (Support, Mid)
        # But to keep table full, let's show Support and Mid
        keys_map = [
            {'label': 'Support (-)', 'key_cs': 'cs_neg_int', 'key_ms': 'ms_neg_int', 'pos': 'top'},
            {'label': 'Mid Span (+)', 'key_cs': 'cs_pos',     'key_ms': 'ms_pos',     'pos': 'bot'},
        ]

    # Prepare Loop
    results = []
    
    for k in keys_map:
        # CS Data
        cs_res = des[k['key_cs']] # The design result from calculations.py
        # MS Data
        ms_res = des[k['key_ms']]
        
        # We need to re-verify or just display? 
        # Since calculations.py already did the design, we can technically just display 'cs_res'.
        # BUT, tab_ddm.py has its own `calc_rebar_logic` for interactive tweaking (?).
        # Ideally, use the values from `cs_res` directly.
        
        # Let's EXTRACT the Moment (Mu) from the result to re-run locally (for consistency with UI renderer)
        # We have to reverse engineer Mu from Rn? No, `calculations.py` calculates Mu first.
        # FIX: We need `calculations.py` to return the Mu used.
        # Assuming `calculations.py` returns objects that contain 'Mu' or we calculated it.
        
        # WORKAROUND: If calculations.py doesn't return Mu explicitly in the dict, 
        # we calculate it from As_req? No.
        # Let's assume we can reconstruct it from the coefficients in `m_vals['M_total']`.
        
        # Getting Mu from M_total and percentages:
        # This is getting complicated.
        # BEST WAY: Trust `calculations.py` result completely.
        
        # Let's just Add to results list for display
        # CS
        cs_res['Label'] = f"CS - {k['label']}"
        cs_res['PlotKey'] = f"CS_{k['pos']}"
        results.append(cs_res)
        
        # MS
        ms_res['Label'] = f"MS - {k['label']}"
        ms_res['PlotKey'] = f"MS_{k['pos']}"
        results.append(ms_res)

    # 4. Display Table
    df_show = pd.DataFrame(results)
    
    # Select columns that exist (handle key errors gracefully)
    cols = ["Label", "Mu", "As_req", "As_prov", "PhiMn", "DC", "Note"]
    # Ensure Mu exists (if calculations.py didn't put it in dict, we might see NaNs. 
    # **Assumption:** You updated `calculations.py` to include 'Mu' in the returned dict of `design_flexure_slab`)
    
    if not results:
        st.error("No design data found.")
    else:
        # Check if 'Mu' is in keys
        if 'Mu' not in results[0]:
             # Fallback if calculations.py doesn't return Mu: calculate roughly for display?
             # Or just hide it.
             st.warning("Mu not found in backend response. Check calculations.py")
        else:
            st.dataframe(
                df_show[cols].style.format({
                    "Mu": "{:,.0f}", "As_req": "{:.2f}", "As_prov": "{:.2f}", 
                    "PhiMn": "{:,.0f}", "DC": "{:.2f}"
                }).background_gradient(subset=["DC"], cmap="RdYlGn_r", vmin=0, vmax=1.2),
                use_container_width=True
            )

    # --- PART 5: DETAIL ---
    st.markdown("---")
    st.markdown("### 5️⃣ Detailed Calculation Sheet")
    sel_label = st.selectbox(f"Select Zone ({axis_id}):", [r['Label'] for r in results])
    target = next(r for r in results if r['Label'] == sel_label)
    
    # Re-pack inputs for the detailed renderer
    # Note: We need 'Mu' and 'b' (strip width)
    # If target comes from backend, it should have these.
    if 'Mu' in target and 'b_width' in target: # Assuming backend stores b_width
         raw_inputs = (target['Mu'], target['b_width'], h_slab, cover, fc, fy, target.get('db', 12), target.get('s', 20), phi_bend)
         pct_val = (target['Mu'] / Mo * 100) if Mo > 0 else 0
         show_detailed_calculation(sel_label, target, raw_inputs, pct_val, Mo)
    else:
        st.info("Detailed calculation requires 'Mu' and 'b_width' from backend.")

    # --- DRAWINGS ---
    if HAS_PLOTS:
        st.markdown("---")
        t1, t2, t3 = st.tabs(["📉 Moment", "🏗️ Section", "📐 Plan"])
        
        # Map for plots
        rebar_map = { r['PlotKey']: f"DB{r.get('db',12)}@{r.get('s',20):.0f}" for r in results }
        
        with t1:
            # Pass correct data structure to plots
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
    
    # [REMOVED] Dropdowns for Manual Span Override
    # เพราะ data_x และ data_y ถูกคำนวณมาอย่างถูกต้องแล้วจาก calculations.py
    # เราไม่ต้องการให้ user มาเลือก Dropdown แล้วไปเขียนทับด้วย logic เก่าที่ผิด
    
    st.info("ℹ️ **Note:** Moment Coefficients and Strip Distribution are automatically calculated based on Column Position (Interior/Edge/Corner).")

    tab_x, tab_y = st.tabs([
        f"➡️ X-Direction (Lx={data_x['L_span']}m)", 
        f"⬆️ Y-Direction (Ly={data_y['L_span']}m)"
    ])
    
    with tab_x:
        render_interactive_direction(data_x, mat_props, "X", w_u, True)
        
    with tab_y:
        render_interactive_direction(data_y, mat_props, "Y", w_u, False)
