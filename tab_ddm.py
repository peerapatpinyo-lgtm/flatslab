# tab_ddm.py
import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple, Optional

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

def calc_rebar_logic(
    M_u: float, b_width: float, d_bar: float, s_bar: float, 
    h_slab: float, cover: float, fc: float, fy: float, 
    is_main_dir: bool, phi_factor: float = 0.90
) -> Dict[str, Any]:
    """
    Core Logic: Calculate Flexural Reinforcement per ACI 318.
    """
    b_cm = b_width * 100.0
    h_cm = float(h_slab)
    Mu_kgcm = M_u * 100.0
    
    # --- Effective Depth Logic ---
    # If main direction (outer layer), offset is 0. 
    # If secondary direction (inner layer), offset is approx 1 bar diameter.
    d_offset = 0.0 if is_main_dir else (d_bar / 10.0)
    d_eff = h_cm - cover - (d_bar / 20.0) - d_offset
    
    # Handle negligible moment or invalid depth
    if M_u < 10 or d_eff <= 0:
        return {
            "d": max(d_eff, 0), "Rn": 0, "rho_req": 0, "As_min": 0, "As_flex": 0, 
            "As_req": 0, "As_prov": 0, "a": 0, "PhiMn": 0, "DC": 0, 
            "Status": True, "Note": "M -> 0" if M_u < 10 else "Depth Err", "s_max": 45
        }

    # --- Strength Design ---
    Rn = Mu_kgcm / (phi_factor * b_cm * d_eff**2)
    
    term_val = 1 - (2 * Rn) / (0.85 * fc)
    
    if term_val < 0:
        rho_req = 999.0 # Fail indicator
    else:
        rho_req = (0.85 * fc / fy) * (1 - np.sqrt(term_val))
        
    As_flex = rho_req * b_cm * d_eff
    As_min = 0.0018 * b_cm * h_cm
    As_req_final = max(As_flex, As_min) if rho_req != 999 else 999.0
    
    # --- Provided Reinforcement ---
    Ab_area = np.pi * (d_bar / 10.0)**2 / 4.0
    As_prov = (b_cm / s_bar) * Ab_area
    
    # --- Capacity Check ---
    if rho_req == 999:
        PhiMn = 0; a_depth = 0; dc_ratio = 999.0
    else:
        a_depth = (As_prov * fy) / (0.85 * fc * b_cm)
        Mn = As_prov * fy * (d_eff - a_depth / 2.0)
        PhiMn = phi_factor * Mn / 100.0
        dc_ratio = M_u / PhiMn if PhiMn > 0 else 999.0

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

def calc_deflection_check(
    L_span: float, L_width: float, h_slab: float, w_u: float, 
    fc: float, fy: float, span_type: str
) -> Dict[str, Any]:
    """
    Serviceability Logic: Check Minimum Thickness (ACI Table 8.3.1.1) 
    and Estimate Elastic Deflection.
    """
    # 1. Minimum Thickness Check (ACI 318 Table 8.3.1.1)
    if "Interior" in span_type:
        denom = 33.0
    elif "Edge Beam" in span_type:
        denom = 30.0 # End span with edge beam
    elif "No Beam" in span_type:
        denom = 30.0 # End span without edge beam (Conservative)
    else:
        denom = 30.0

    # Fy modification factor logic simplified for typical grades
    h_min_req = (L_span * 100.0) / denom
    
    # Apply factor if Fy is significantly different (simplified check)
    if fy > 3000:
        pass 
        
    status_h = "OK" if h_slab >= h_min_req else "CHECK"
    
    # 2. Elastic Deflection Estimation (Simplified - Gross Inertia)
    # Note: This is a rough estimate using Gross Inertia only.
    w_service = w_u / 1.4 # Rough approximation to get service load
    w_line = w_service * L_width # kg/m
    
    Ec = 15100 * np.sqrt(fc) # ksc
    Ig = (L_width * 100 * (h_slab)**3) / 12.0 # cm4
    
    w_line_cm = w_line / 100.0
    L_cm = L_span * 100.0
    
    continuity_factor = 0.6 # Reduces deflection compared to simple span
    delta_imm = continuity_factor * (5 * w_line_cm * L_cm**4) / (384 * Ec * Ig)
    
    # Long term multiplier
    lambda_delta = 2.0
    delta_long = delta_imm * (1 + lambda_delta)
    
    limit_delta = L_cm / 240.0 # General limit
    
    return {
        "h_min": h_min_req,
        "status_h": status_h,
        "delta_imm": delta_imm,
        "delta_long": delta_long,
        "limit": limit_delta,
        "denom": denom
    }

# ========================================================
# 2. HELPER: DDM COEFFICIENT RECALCULATION
# ========================================================
def get_ddm_coeffs(span_type: str) -> Dict[str, Any]:
    """
    Return dictionaries of Moment Coefficients based on Span Type (ACI 318).
    """
    if "Interior" in span_type:
        return { 'neg': 0.65, 'pos': 0.35, 'desc': 'Interior: Neg 0.65, Pos 0.35' }
    elif "Edge Beam" in span_type:
        return { 'neg': 0.70, 'pos': 0.57, 'desc': 'End w/ Beam: IntNeg 0.70, Pos 0.57' }
    elif "No Beam" in span_type:
        return { 'neg': 0.70, 'pos': 0.52, 'desc': 'End No Beam: IntNeg 0.70, Pos 0.52' }
    return { 'neg': 0.65, 'pos': 0.35, 'desc': 'Default' }

def update_moments_based_on_config(data_obj: Dict, span_type: str) -> Dict:
    """
    Recalculate M_vals in data_obj based on the selected span type.
    """
    Mo = data_obj['Mo']
    coeffs = get_ddm_coeffs(span_type)
    
    M_neg_total = coeffs['neg'] * Mo
    M_pos_total = coeffs['pos'] * Mo
    
    # Distribution factors (ACI)
    M_cs_neg = 0.75 * M_neg_total
    M_ms_neg = 0.25 * M_neg_total
    
    M_cs_pos = 0.60 * M_pos_total
    M_ms_pos = 0.40 * M_pos_total
    
    data_obj['M_vals'] = {
        'M_cs_neg': M_cs_neg,
        'M_ms_neg': M_ms_neg,
        'M_cs_pos': M_cs_pos,
        'M_ms_pos': M_ms_pos
    }
    data_obj['coeffs_desc'] = coeffs['desc'] 
    data_obj['span_type_str'] = span_type
    return data_obj

# ========================================================
# 3. DETAILED CALCULATION RENDERER
# ========================================================
def show_detailed_calculation(zone_name, res, inputs, coeff_pct, Mo_val):
    Mu, b, h, cover, fc, fy, db, s, phi_bend = inputs
    
    st.markdown(f"#### 📐 Detailed Design Sheet: {zone_name}")
    st.caption(f"Design Parameters: $f_c'={fc}$ ksc, $f_y={fy}$ ksc, $h={h}$ cm, $\\phi_b={phi_bend}$")

    step1, step2, step3 = st.tabs(["1. Moment & Depth", "2. Steel Area", "3. Capacity Check"])
    
    with step1:
        st.markdown("**1.1 Design Moment ($M_u$) Calculation**")
        st.write("Determine design moment using Direct Design Method coefficients:")
        st.latex(f"M_u = (\\text{{Coeff}}) \\times M_o")
        st.latex(f"M_u = {coeff_pct/100:.3f} \\times {Mo_val:,.0f} = \\mathbf{{{Mu:,.0f}}} \\; \\text{{kg-m}}")
        
        st.markdown("**1.2 Effective Depth ($d$)**")
        if res['d'] < (h - cover - db/20.0):
            st.info("Note: Inner layer calculation (Subtracting assumed main bar diameter)")
        st.latex(r"d_{eff} = \mathbf{" + f"{res['d']:.2f}" + r"} \; \text{cm}")

    with step2:
        st.markdown("**2.1 Required Reinforcement ($A_{s,req}$)**")
        # As min
        st.latex(f"A_{{s,min}} = 0.0018 \\cdot ({b*100:.0f}) \\cdot {h} = {res['As_min']:.2f} \\; \\text{{cm}}^2")
        
        # As flexure
        st.markdown("Flexural strength design (ACI 318):")
        st.latex(f"R_n = \\frac{{M_u}}{{\\phi_b b d^2}} = \\frac{{{Mu*100:,.0f}}}{{{phi_bend} \\cdot {b*100:.0f} \\cdot {res['d']:.2f}^2}} = {res['Rn']:.2f} \\; \\text{{ksc}}")
        
        if res['rho_req'] != 999:
            st.latex(r"\rho_{req} = \frac{0.85 f_c'}{f_y} \left( 1 - \sqrt{1 - \frac{2 R_n}{0.85 f_c'}} \right)")
            st.latex(f"A_{{s,flex}} = \\rho_{{req}} b d = {res['As_flex']:.2f} \\; \\text{{cm}}^2")
        else:
            st.error("❌ Section dimensions are too small (Rn too high). Increase Depth.")

        st.info(f"👉 **Control:** $A_{{s,req}} = \\max({res['As_min']:.2f}, {res['As_flex']:.2f}) = \\mathbf{{{res['As_req']:.2f}}} \\; \\text{{cm}}^2$")

    with step3:
        st.markdown("**3.1 Provided Reinforcement ($A_{s,prov}$)**")
        bar_prefix = "RB" if db == 9 else "DB"
        st.write(f"Selection: **{bar_prefix}{db} @ {s:.0f} cm**")
        
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
    
    # Unpack Opening Data
    open_w = mat_props.get('open_w', 0.0)
    open_dist = mat_props.get('open_dist', 0.0)
    
    L_span = data['L_span']
    L_width = data['L_width']
    c_para = data['c_para']
    Mo = data['Mo']
    m_vals = data['M_vals']
    coeff_desc = data.get('coeffs_desc', 'Standard')
    span_type_str = data.get('span_type_str', 'Interior')
    
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
    
    # -----------------------------------------------------
    # 1. ANALYSIS & DISTRIBUTION
    # -----------------------------------------------------
    st.markdown(f"### 1️⃣ Analysis: {axis_id}-Direction")
    
    with st.expander(f"📝 Derivation of $M_o$ & $M_u$ ({axis_id}-Direction)", expanded=True):
        col_diagram, col_calc = st.columns([1, 1.5])
        
        with col_diagram:
            st.info(f"**Definitions for {axis_id}-Axis:**")
            st.markdown(f"""
            - **Span Type:** {coeff_desc}
            - **Span Length ({span_sym}):** {span_val:.2f} m
            - **Strip Width ({width_sym}):** {width_val:.2f} m
            - **Clear Span ($l_n$):** {ln_val:.2f} m
            """)
            st.caption(f"*Note: $l_n = {span_sym} - \\text{{Column}}$")
            

        with col_calc:
            st.markdown(f"#### Step 1: Total Static Moment ($M_o$)")
            st.latex(f"M_o = \\frac{{w_u {width_sym} ({span_sym} - c)^2}}{{8}}")
            st.latex(f"M_o = \\frac{{{w_u:,.0f} \\cdot {width_val:.2f} \\cdot ({ln_val:.2f})^2}}{{8}} = \\mathbf{{{Mo:,.0f}}} \\; \\text{{kg-m}}")
        
        st.divider()
        st.markdown(f"#### Step 2: Distribution to $M_u$")
        
        def get_pct(val): return (val / Mo * 100) if Mo > 0 else 0
        
        dist_data = [
            {"Pos": "Top (-)", "Strip": "🟥 Column Strip", "% of Mo": f"{get_pct(m_vals['M_cs_neg']):.1f}%", "Mu": m_vals['M_cs_neg']},
            {"Pos": "Top (-)", "Strip": "🟦 Middle Strip", "% of Mo": f"{get_pct(m_vals['M_ms_neg']):.1f}%", "Mu": m_vals['M_ms_neg']},
            {"Pos": "Bot (+)", "Strip": "🟥 Column Strip", "% of Mo": f"{get_pct(m_vals['M_cs_pos']):.1f}%", "Mu": m_vals['M_cs_pos']},
            {"Pos": "Bot (+)", "Strip": "🟦 Middle Strip", "% of Mo": f"{get_pct(m_vals['M_ms_pos']):.1f}%", "Mu": m_vals['M_ms_pos']},
        ]
        st.dataframe(pd.DataFrame(dist_data).style.format({"Mu": "{:,.0f}"}), use_container_width=True, hide_index=True)

    # -----------------------------------------------------
    # 2. PUNCHING SHEAR & DEFLECTION
    # -----------------------------------------------------
    
    # --- 2.1 PUNCHING SHEAR ---
    if HAS_CALC:
        st.markdown("---")
        st.markdown("### 2️⃣ Punching Shear Check")
        
        c_col = float(c_para)
        load_area = (span_val * width_val) - ((c_col/100.0) * (c_col/100.0))
        Vu_approx = float(w_u) * load_area 
        
        d_bar_val = 1.6 # Avg assumption
        d_eff = float(h_slab) - float(cover) - d_bar_val
        if d_eff <= 0: d_eff = 1.0

        # [UPDATED] Determine Column Type based on Span Type selection
        if "End Span" in span_type_str or "Edge Beam" in span_type_str or "No Beam" in span_type_str:
            calculated_col_type = "edge"
        else:
            calculated_col_type = "interior"

        # Call calculation with DYNAMIC col_type
        ps_res = calc.check_punching_shear(
            Vu=Vu_approx,        
            fc=float(fc),
            c1=c_col,            
            c2=c_col,            
            d=d_eff,                
            col_type=calculated_col_type, # <-- FIXED: Now dynamic
            open_w=open_w,
            open_dist=open_dist,
            phi=phi_shear 
        )
        
        col_p1, col_p2 = st.columns([1, 1.5])
        
        with col_p1:
            st.info(f"**Condition:** {calculated_col_type.capitalize()} Column") # Show User what we are checking
            if HAS_PLOTS:
                st.pyplot(ddm_plots.plot_punching_shear_geometry(
                    c_col, c_col, ps_res['d'], ps_res['bo'], ps_res['status'], ps_res['ratio']
                ))
            else:
                st.info("ℹ️ Plotting module not available.")
            
            if open_w > 0:
                st.warning(f"⚠️ **Opening Detected:** {open_w:.0f}cm x {open_w:.0f}cm")
        
        with col_p2:
            if ps_res['status'] == "OK":
                st.success(f"✅ **PASSED** (Ratio: {ps_res['ratio']:.2f})")
            else:
                st.error(f"❌ **FAILED** (Ratio: {ps_res['ratio']:.2f})")
                st.warning("⚠️ Suggestions: Increase slab thickness, column size, or add drop panel.")
            
            with st.expander("Calculation Details", expanded=False):
                st.write(f"**1. Factored Shear ($V_u$):** {ps_res['Vu']:,.0f} kg")
                
                if 'Munbal' in ps_res and ps_res['Munbal'] > 0:
                    st.info(f"ℹ️ **Combined Stress:** Includes $M_{{unbal}}$")
                
                st.write(f"**2. Perimeter ($b_o$):** {ps_res['bo']:.2f} cm")
                st.caption(f"Using Strength Reduction Factor $\phi_v = {phi_shear}$")
                
                st.latex(rf"\phi_v V_c = \mathbf{{{ps_res['phi_Vc']:,.0f}}} \text{{ kg}}")
                st.latex(rf"{ps_res['Vu']:,.0f} \le {ps_res['phi_Vc']:,.0f} \rightarrow \text{{{ps_res['status']}}}")
    
    # --- 2.2 DEFLECTION (SERVICEABILITY) ---
    st.markdown("---")
    st.markdown("### 3️⃣ Serviceability & Deflection Check")
    
    with st.container(border=True):
        def_res = calc_deflection_check(span_val, width_val, h_slab, w_u, fc, fy, span_type_str)
        
        c_def1, c_def2 = st.columns(2)
        with c_def1:
            st.markdown("**A) Minimum Thickness Check ($h_{min}$)**")
            st.caption(f"Based on ACI 318 Table 8.3.1.1 (Divisor L/{def_res['denom']:.0f})")
            
            if def_res['status_h'] == "OK":
                st.success(f"✅ $h_{{prov}} = {h_slab} \\text{{ cm}} \\ge h_{{min}} = {def_res['h_min']:.2f} \\text{{ cm}}$")
            else:
                st.error(f"❌ $h_{{prov}} = {h_slab} \\text{{ cm}} < h_{{min}} = {def_res['h_min']:.2f} \\text{{ cm}}$")
                st.caption("Warning: Detailed deflection calculation required.")

        with c_def2:
            st.markdown("**B) Elastic Deflection Est. ($\Delta$)**")
            # [UPDATED] Added explicit warning about Gross Inertia
            st.warning("⚠️ **NOTE:** This estimate uses Gross Inertia ($I_g$). Actual deflection with Cracked Section ($I_{eff}$) will be higher.")
            
            st.write(f"$\\Delta_{{imm}} \\approx {def_res['delta_imm']:.2f}$ cm")
            st.write(f"$\\Delta_{{long}} (\\lambda=2.0) \\approx \\mathbf{{{def_res['delta_long']:.2f}}}$ **cm**")
            
            is_ok_def = def_res['delta_long'] < def_res['limit']
            limit_txt = f"L/240 ({def_res['limit']:.2f} cm)"
            
            if is_ok_def:
                st.success(f"✅ Within Limit {limit_txt}")
            else:
                st.warning(f"⚠️ Exceeds Limit {limit_txt}")

    # -----------------------------------------------------
    # 4. REINFORCEMENT SELECTION
    # -----------------------------------------------------
    st.markdown("---")
    st.markdown("### 4️⃣ Reinforcement Status")
    
    # Map Config to Local Variables
    d_cst, s_cst = cfg.get('cs_top_db', 12), cfg.get('cs_top_spa', 20)
    d_csb, s_csb = cfg.get('cs_bot_db', 12), cfg.get('cs_bot_spa', 20)
    d_mst, s_mst = cfg.get('ms_top_db', 12), cfg.get('ms_top_spa', 20)
    d_msb, s_msb = cfg.get('ms_bot_db', 12), cfg.get('ms_bot_spa', 20)
    
    col_cs, gap, col_ms = st.columns([1, 0.05, 1])
    def fmt_bar(db, spa): return f"DB{db} @ {spa} cm" if db > 9 else f"RB{db} @ {spa} cm"

    with col_cs:
        st.markdown(f"""<div style="background-color:#ffebee; padding:8px; border-radius:5px; border-left:4px solid #ef5350;">
            <b>🟥 COLUMN STRIP</b> (Width {w_cs:.2f} m)</div>""", unsafe_allow_html=True)
        st.write(f"Top (-): **{fmt_bar(d_cst, s_cst)}**")
        st.write(f"Bot (+): **{fmt_bar(d_csb, s_csb)}**")

    with col_ms:
        st.markdown(f"""<div style="background-color:#e3f2fd; padding:8px; border-radius:5px; border-left:4px solid #2196f3;">
            <b>🟦 MIDDLE STRIP</b> (Width {w_ms:.2f} m)</div>""", unsafe_allow_html=True)
        st.write(f"Top (-): **{fmt_bar(d_mst, s_mst)}**")
        st.write(f"Bot (+): **{fmt_bar(d_msb, s_msb)}**")

    # --- CALCULATION LOOP ---
    calc_configs = [
        {"Label": "Col Strip - Top (-)", "PlotKey": "CS_Top", "Mu": m_vals['M_cs_neg'], "b": w_cs, "db": d_cst, "s": s_cst},
        {"Label": "Col Strip - Bot (+)", "PlotKey": "CS_Bot", "Mu": m_vals['M_cs_pos'], "b": w_cs, "db": d_csb, "s": s_csb},
        {"Label": "Mid Strip - Top (-)", "PlotKey": "MS_Top", "Mu": m_vals['M_ms_neg'], "b": w_ms, "db": d_mst, "s": s_mst},
        {"Label": "Mid Strip - Bot (+)", "PlotKey": "MS_Bot", "Mu": m_vals['M_ms_pos'], "b": w_ms, "db": d_msb, "s": s_msb},
    ]

    results = []
    for c in calc_configs:
        res = calc_rebar_logic(c['Mu'], c['b'], c['db'], c['s'], h_slab, cover, fc, fy, is_main_dir, phi_factor=phi_bend)
        res.update(c) 
        results.append(res)

    # --- SUMMARY TABLE ---
    st.write("")
    st.markdown("### 5️⃣ Verification Summary")
    
    df_show = pd.DataFrame(results)
    cols_to_show = ["Label", "Mu", "d", "As_req", "As_prov", "PhiMn", "DC", "Note"]
    
    for col in cols_to_show:
        if col not in df_show.columns: df_show[col] = 0
            
    st.dataframe(
        df_show[cols_to_show].style.format({
            "Mu": "{:,.0f}", "d": "{:.2f}", "As_req": "{:.2f}", "As_prov": "{:.2f}", 
            "PhiMn": "{:,.0f}", "DC": "{:.2f}"
        }).background_gradient(subset=["DC"], cmap="RdYlGn_r", vmin=0, vmax=1.2),
        use_container_width=True
    )

    # --- DETAILED SHEET ---
    st.markdown("---")
    st.markdown("### 6️⃣ Detailed Calculation Sheet")
    
    sel_label = st.selectbox(f"Select Zone to View Details ({axis_id}):", [r['Label'] for r in results])
    target = next(r for r in results if r['Label'] == sel_label)
    
    raw_inputs = (target['Mu'], target['b'], h_slab, cover, fc, fy, target['db'], target['s'], phi_bend)
    
    with st.container(border=True):
        pct_val = (target['Mu'] / Mo * 100) if Mo > 0 else 0
        show_detailed_calculation(sel_label, target, raw_inputs, pct_val, Mo)

    # --- DRAWINGS ---
    if HAS_PLOTS:
        st.markdown("---")
        t1, t2, t3 = st.tabs(["📉 Moment Diagram", "🏗️ Section Detail", "📐 Plan View"])
        
        rebar_map = {r['PlotKey']: f"{'RB' if r['db']==9 else 'DB'}{r['db']}@{r['s']:.0f}" for r in results}
        
        with t1: st.pyplot(ddm_plots.plot_ddm_moment(span_val, c_para/100, m_vals))
        with t2: st.pyplot(ddm_plots.plot_rebar_detailing(span_val, h_slab, c_para, rebar_map, axis_id))
        with t3: st.pyplot(ddm_plots.plot_rebar_plan_view(span_val, width_val, c_para, rebar_map, axis_id))

# ========================================================
# MAIN ENTRY
# ========================================================
def render_dual(data_x, data_y, mat_props, w_u):
    st.markdown("## 🏗️ RC Slab Design (DDM Method)")

    # ------------------------------------------------------------------------
    # CONFIGURATION
    # ------------------------------------------------------------------------
    with st.expander("⚙️ Span & Continuity Settings", expanded=True):
        st.info("💡 **Tips:** The program automatically adjusts Moment Coefficients based on the selected span type.")
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**X-Direction ($L_x$ = {data_x['L_span']} m):**")
            type_x = st.selectbox(
                "Span Type (X-Axis)",
                ["Interior Span", "End Span - Edge Beam", "End Span - No Beam"],
                index=0, key="span_type_x"
            )
            data_x = update_moments_based_on_config(data_x, type_x)

        with c2:
            st.markdown(f"**Y-Direction ($L_y$ = {data_y['L_span']} m):**")
            type_y = st.selectbox(
                "Span Type (Y-Axis)",
                ["Interior Span", "End Span - Edge Beam", "End Span - No Beam"],
                index=0, key="span_type_y"
            )
            data_y = update_moments_based_on_config(data_y, type_y)
            
    # ------------------------------------------------------------------------
    # TABS RENDERING
    # ------------------------------------------------------------------------
    tab_x, tab_y = st.tabs([
        f"➡️ X-Direction (Lx={data_x['L_span']}m)", 
        f"⬆️ Y-Direction (Ly={data_y['L_span']}m)"
    ])
    
    with tab_x:
        render_interactive_direction(data_x, mat_props, "X", w_u, True)
        
    with tab_y:
        render_interactive_direction(data_y, mat_props, "Y", w_u, False)
