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
# 1. CORE ENGINEERING LOGIC (ACI 318 / EIT)
# ========================================================

def get_beta1(fc: float) -> float:
    """
    Calculate Beta1 factor for equivalent rectangular concrete stress distribution.
    ACI 318: 0.85 for fc <= 280 ksc (4000 psi).
    Reduces by 0.05 for every 70 ksc above 280, min 0.65.
    """
    if fc <= 280:
        return 0.85
    else:
        beta = 0.85 - 0.05 * ((fc - 280) / 70)
        return max(0.65, beta)

def calc_rebar_logic(
    M_u: float, b_width: float, d_bar: float, s_bar: float, 
    h_slab: float, cover: float, fc: float, fy: float, 
    is_main_dir: bool, phi_factor: float = 0.90
) -> Dict[str, Any]:
    """
    Perform Flexural Design with detailed intermediate steps.
    """
    # Units: kg, cm
    b_cm = b_width * 100.0
    h_cm = float(h_slab)
    Mu_kgcm = M_u * 100.0
    
    # 1. Effective Depth (d)
    # Layer 1 (Outer) or Layer 2 (Inner)
    d_offset = 0.0 if is_main_dir else (d_bar / 10.0)
    d_eff = h_cm - cover - (d_bar / 20.0) - d_offset
    
    if d_eff <= 0:
        return {"Status": False, "Note": "Depth Error", "d": 0, "As_req": 0}

    # 2. Beta 1
    beta1 = get_beta1(fc)

    # 3. Required Strength (Rn)
    # Rn = Mu / (phi * b * d^2)
    try:
        Rn = Mu_kgcm / (phi_factor * b_cm * (d_eff**2))
    except ZeroDivisionError:
        Rn = 0

    # 4. Reinforcement Ratio (rho)
    # rho = (0.85*fc/fy) * (1 - sqrt(1 - 2Rn/(0.85*fc)))
    term_inside = 1 - (2 * Rn) / (0.85 * fc)
    
    rho_calc = 0.0
    if term_inside < 0:
        rho_req = 999.0 # Section too small (Fail)
    else:
        if M_u < 100: # Negligible moment
            rho_req = 0.0
        else:
            rho_req = (0.85 * fc / fy) * (1 - np.sqrt(term_inside))
            rho_calc = rho_req

    # 5. Steel Areas
    As_flex = rho_req * b_cm * d_eff
    As_min = 0.0018 * b_cm * h_cm # Temp & Shrinkage (ACI Standard for Slabs)
    
    # Control Logic: Use Max(As_flex, As_min)
    # Even if Moment is 0 (e.g. Mid Strip Top), we need As_min for shrinkage
    As_req_final = max(As_flex, As_min) if rho_req != 999 else 999.0
    
    # 6. Provided Steel
    Ab_area = np.pi * (d_bar / 10.0)**2 / 4.0
    As_prov = (b_cm / s_bar) * Ab_area
    
    # 7. Capacity Check (Phi Mn)
    if rho_req == 999:
        PhiMn = 0; a_depth = 0; dc_ratio = 999.0
    else:
        # a = As*fy / (0.85*fc*b)
        a_depth = (As_prov * fy) / (0.85 * fc * b_cm)
        # Mn = As*fy*(d - a/2)
        Mn = As_prov * fy * (d_eff - a_depth / 2.0)
        PhiMn = phi_factor * Mn / 100.0 # kg-m
        
        # DC Ratio check (avoid div by zero)
        if M_u < 50: # Ignore check for zero moment zones
            dc_ratio = 0.0
        else:
            dc_ratio = M_u / PhiMn if PhiMn > 0 else 999.0

    s_max = min(2 * h_cm, 45.0)
    
    checks = []
    if dc_ratio > 1.0: checks.append("Strength Fail")
    if As_prov < As_min: checks.append("As < Min")
    if s_bar > s_max: checks.append("Spacing > Max")
    if rho_req == 999: checks.append("Section Too Small")
    
    status_bool = (len(checks) == 0)

    return {
        "d": d_eff, "beta1": beta1, "Rn": Rn, 
        "rho_req": rho_req, "rho_calc": rho_calc,
        "As_min": As_min, "As_flex": As_flex,
        "As_req": As_req_final, "As_prov": As_prov, 
        "a": a_depth, "PhiMn": PhiMn, "DC": dc_ratio, 
        "Status": status_bool, 
        "Note": ", ".join(checks) if checks else "OK", 
        "s_max": s_max
    }

def calc_deflection_check(L_span, h_slab, w_u, fc, span_type):
    """
    Simplified Serviceability Check.
    Note: Real deflection requires effective inertia (Ie).
    Here we use Ig with a conservative multiplier for long-term effects.
    """
    # Minimum Thickness Table (ACI 318)
    denom = 30.0 # Default
    if "Interior" in span_type: denom = 33.0
    elif "Edge" in span_type: denom = 30.0
    
    h_min = (L_span * 100) / denom
    
    # Elastic Deflection (Approximate)
    # 5wL^4 / 384EI (Simple) * Continuity Factor
    # Continuity Factor: 0.6 for interior, 0.8 for end span (Rough approx)
    k_cont = 0.6 if "Interior" in span_type else 0.8
    
    Ec = 15100 * np.sqrt(fc) # ksc
    b_design = 100.0 # Consider 1m strip width for check
    Ig = (b_design * h_slab**3) / 12.0
    
    w_service = w_u / 1.45 # Approx service load
    w_line = (w_service * 1.0) / 100.0 # kg/cm per strip width
    L_cm = L_span * 100.0
    
    delta_imm = k_cont * (5 * w_line * L_cm**4) / (384 * Ec * Ig)
    
    # Long term multiplier (Creep + Shrinkage)
    # ACI: lambda = xi / (1 + 50rho')
    # Conservative assume lambda = 2.0 -> Total = 3.0 * Immediate
    lambda_long = 2.0
    delta_total = delta_imm * (1 + lambda_long)
    
    limit = L_cm / 240.0
    
    return {
        "h_min": h_min, "status_h": h_slab >= h_min,
        "delta_imm": delta_imm, "delta_total": delta_total,
        "limit": limit, "denom": denom
    }

# ========================================================
# 2. DDM COEFFICIENT ENGINE
# ========================================================
def get_ddm_coeffs(span_type: str) -> Dict[str, float]:
    """
    Returns ACI 318 Moment Coefficients.
    Now includes 'ext_neg' for Unbalanced Moment calculation at edge.
    """
    if "Interior" in span_type:
        # Case: Interior Span
        return {'neg': 0.65, 'pos': 0.35, 'ext_neg': 0.0, 'desc': 'Interior Span'}
    
    elif "Edge Beam" in span_type:
        # Case: Exterior Span with Stiff Edge Beam
        # Ext Neg: 0.30, Pos: 0.50, Int Neg: 0.70
        return {'neg': 0.70, 'pos': 0.50, 'ext_neg': 0.30, 'desc': 'End Span (Stiff Beam)'}
    
    elif "No Beam" in span_type:
        # Case: Exterior Span (Flat Plate)
        # Ext Neg: 0.26, Pos: 0.52, Int Neg: 0.70
        return {'neg': 0.70, 'pos': 0.52, 'ext_neg': 0.26, 'desc': 'End Span (Flat Plate)'}
        
    return {'neg': 0.65, 'pos': 0.35, 'ext_neg': 0.0, 'desc': 'Default'}

def update_moments_based_on_config(data_obj: Dict, span_type: str) -> Dict:
    Mo = data_obj['Mo']
    coeffs = get_ddm_coeffs(span_type)
    
    # Total Static Moment Distribution
    M_neg_total = coeffs['neg'] * Mo    # Interior Negative
    M_pos_total = coeffs['pos'] * Mo    # Positive
    M_ext_neg_total = coeffs['ext_neg'] * Mo # Exterior Negative (Unbalanced)

    # Column Strip / Middle Strip Distribution (ACI 318)
    # Simplified assumptions for Flat Plate (Beta_t = 0 for no beam)
    # Interior Negative: 75% CS, 25% MS
    # Positive: 60% CS, 40% MS
    # Exterior Negative: 100% CS (Conservative for Flat Plate)
    
    M_cs_neg = 0.75 * M_neg_total
    M_ms_neg = 0.25 * M_neg_total
    
    M_cs_pos = 0.60 * M_pos_total
    M_ms_pos = 0.40 * M_pos_total
    
    # Store Values
    data_obj['M_vals'] = {
        'M_cs_neg': M_cs_neg,
        'M_ms_neg': M_ms_neg,
        'M_cs_pos': M_cs_pos,
        'M_ms_pos': M_ms_pos,
        'M_unbal': M_ext_neg_total # Important for Edge Column Punching
    }
    data_obj['coeffs_desc'] = coeffs['desc'] 
    data_obj['span_type_str'] = span_type
    return data_obj

# ========================================================
# 3. DETAILED CALCULATION RENDERER (THE EXPLAINER)
# ========================================================
def show_detailed_calculation(zone_name, res, inputs, coeff_pct, Mo_val):
    Mu, b, h, cover, fc, fy, db, s, phi_bend = inputs
    
    st.markdown(f"""
    <div style="background-color:#f8f9fa; padding:15px; border-radius:10px; border-left: 5px solid #3b82f6;">
        <h4 style="margin:0; color:#1e3a8a;">📐 Detailed Design Sheet: {zone_name}</h4>
        <p style="margin:5px 0 0 0; color:#64748b; font-size:0.9em;">
            Method: Strength Design (USD) per ACI 318 / EIT Standard
        </p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.tabs(["1️⃣ Moment & Geometry", "2️⃣ Reinforcement Calculation", "3️⃣ Capacity & Summary"])
    
    # --- TAB 1: MOMENT & GEOMETRY ---
    with c1:
        st.markdown("**1.1 Design Moment ($M_u$)**")
        st.write("Calculated using Direct Design Method (DDM) coefficients:")
        st.latex(f"M_o = \\text{{Total Static Moment}} = {Mo_val:,.0f} \\; \\text{{kg-m}}")
        st.latex(f"M_u = (\\text{{Coeff}} \\% ) \\times M_o = {coeff_pct/100:.3f} \\times {Mo_val:,.0f}")
        st.info(f"👉 **Design Moment ($M_u$): {Mu:,.0f} kg-m**")
        
        st.markdown("---")
        st.markdown("**1.2 Effective Depth ($d$)**")
        st.write("Distance from compression fiber to centroid of tension reinforcement.")
        st.latex(r"d = h - C_c - \frac{d_b}{2} - (\text{Layer Offset})")
        st.latex(f"d = {h} - {cover} - {db/20.0:.2f} - ...")
        
        if res['d'] < (h - cover - db/10.0):
            st.caption("ℹ️ Note: Calculation for Inner Layer (Secondary Direction)")
            
        st.success(f"**Effective Depth ($d$): {res['d']:.2f} cm**")

    # --- TAB 2: REINFORCEMENT ---
    with c2:
        st.markdown("**2.1 Determine $\\beta_1$ Factor**")
        st.write(f"For concrete strength $f_c' = {fc}$ ksc:")
        if fc <= 280:
            st.latex(r"\beta_1 = 0.85 \quad (\text{for } f_c' \le 280 \text{ ksc})")
        else:
            st.latex(r"\beta_1 = 0.85 - 0.05 \left( \frac{f_c' - 280}{70} \right) \ge 0.65")
        st.write(f"**Use $\\beta_1 = {res['beta1']:.2f}$**")

        st.markdown("---")
        st.markdown("**2.2 Required Reinforcement Area ($A_{s,req}$)**")
        
        # Step A: Rn
        st.write("**A) Flexural Resistance Factor ($R_n$)**")
        st.latex(f"R_n = \\frac{{M_u}}{{\\phi b d^2}} = \\frac{{{Mu*100:,.0f}}}{{{phi_bend} \\cdot {b*100:.0f} \\cdot {res['d']:.2f}^2}}")
        st.latex(f"R_n = \\mathbf{{{res['Rn']:.2f}}} \\; \\text{{ksc}}")

        # Step B: Rho Required
        st.write("**B) Required Ratio ($\\rho_{req}$)**")
        if res['rho_req'] == 999:
            st.error("❌ $R_n$ exceeds limit. Section is too thin or concrete too weak.")
        elif res['rho_req'] == 0:
            st.info("Moment is negligible. Theoretical $\\rho_{req} = 0$.")
        else:
            st.latex(r"\rho_{req} = \frac{0.85 f_c'}{f_y} \left( 1 - \sqrt{1 - \frac{2 R_n}{0.85 f_c'}} \right)")
            st.latex(f"\\rho_{{req}} = {res['rho_calc']:.5f}")
            st.latex(f"A_{{s,flex}} = \\rho_{{req}} b d = {res['rho_calc']:.5f} \\cdot {b*100:.0f} \\cdot {res['d']:.2f} = {res['As_flex']:.2f} \\; \\text{{cm}}^2")

        # Step C: Minimum Steel
        st.write("**C) Minimum Temperature & Shrinkage Steel ($A_{s,min}$)**")
        st.latex(r"A_{s,min} = 0.0018 \cdot b \cdot h \quad (\text{for Grade 40/60})")
        st.latex(f"A_{{s,min}} = 0.0018 \\cdot {b*100:.0f} \\cdot {h} = \\mathbf{{{res['As_min']:.2f}}} \\; \\text{{cm}}^2")

        st.markdown("---")
        st.info(f"📌 **Design Control:** $A_{{s,req}} = \\max({res['As_flex']:.2f}, {res['As_min']:.2f}) = \\mathbf{{{res['As_req']:.2f}}} \\; \\text{{cm}}^2$")

    # --- TAB 3: SUMMARY ---
    with c3:
        st.markdown("**3.1 Provided Reinforcement**")
        bar_txt = f"DB{db}" if db > 9 else f"RB{db}"
        st.markdown(f"Try: **{bar_txt} @ {s:.0f} cm**")
        
        area_one_bar = 3.1416 * (db/10)**2 / 4
        st.latex(f"A_{{s,prov}} = \\frac{{b}}{{s}} \\cdot A_{{bar}} = \\frac{{{b*100:.0f}}}{{{s:.0f}}} \\cdot {area_one_bar:.2f}")
        
        val_color = "green" if res['As_prov'] >= res['As_req'] else "red"
        st.markdown(f"<h3 style='color:{val_color}'>Provided: {res['As_prov']:.2f} cm²</h3>", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("**3.2 Moment Capacity Check**")
        st.latex(f"a = \\frac{{A_s f_y}}{{0.85 f_c' b}} = \\frac{{{res['As_prov']:.2f} \cdot {fy}}}{{0.85 \cdot {fc} \cdot {b*100:.0f}}} = {res['a']:.2f} \\; \\text{{cm}}")
        st.latex(f"\\phi M_n = \\phi A_s f_y (d - a/2) = {res['PhiMn']:,.0f} \\; \\text{{kg-m}}")
        
        dc = res['DC']
        if dc <= 1.0:
            st.success(f"✅ **PASS** (Demand/Capacity = {dc:.2f})")
        else:
            st.error(f"❌ **FAIL** (Demand/Capacity = {dc:.2f})")


# ========================================================
# 4. UI RENDERER (INTERACTIVE)
# ========================================================
def render_interactive_direction(data, mat_props, axis_id, w_u, is_main_dir):
    # Unpack basic props
    h_slab = mat_props['h_slab']
    cover = mat_props['cover']
    fc = mat_props['fc']
    fy = mat_props['fy']
    phi_bend = mat_props.get('phi', 0.90)       
    phi_shear = mat_props.get('phi_shear', 0.85) 
    
    # Rebar Config
    cfg = mat_props.get('rebar_cfg', {})
    
    L_span = data['L_span']
    L_width = data['L_width']
    c_para = data['c_para']
    Mo = data['Mo']
    m_vals = data['M_vals']
    coeff_desc = data.get('coeffs_desc', 'Standard')
    span_type_str = data.get('span_type_str', 'Interior')
    
    # Dimension Symbols
    span_sym, width_sym = ("L_x", "L_y") if axis_id == "X" else ("L_y", "L_x")
    ln_val = L_span - (c_para/100.0)
    
    # Strip Widths
    w_cs = min(L_span, L_width) / 2.0
    w_ms = L_width - w_cs
    
    # -----------------------------------------------------
    # SECTION 1: ANALYSIS & LOAD
    # -----------------------------------------------------
    st.markdown(f"### 1️⃣ Analysis: {axis_id}-Direction")
    
    with st.expander(f"📊 Load & Moment Distribution ({axis_id})", expanded=True):
        c_an1, c_an2 = st.columns([1, 1.5])
        with c_an1:
            st.info(f"**Span Configuration:** {span_type_str}")
            st.markdown(f"""
            - **Span {span_sym}:** {L_span:.2f} m
            - **Width {width_sym}:** {L_width:.2f} m
            - **Clear Span ($l_n$):** {ln_val:.2f} m
            - **Total Load ($w_u$):** {w_u:,.0f} kg/m²
            """)
        with c_an2:
            st.markdown("#### Total Static Moment ($M_o$)")
            st.latex(f"M_o = \\frac{{w_u l_2 l_n^2}}{{8}} = \\frac{{{w_u:,.0f} \\cdot {L_width:.2f} \\cdot {ln_val:.2f}^2}}{{8}}")
            st.latex(f"M_o = \\mathbf{{{Mo:,.0f}}} \\; \\text{{kg-m}}")
            
            # Show Unbalanced Moment if exists
            if m_vals.get('M_unbal', 0) > 0:
                st.warning(f"⚠️ **Unbalanced Moment ($M_{{sc}}$):** {m_vals['M_unbal']:,.0f} kg-m (Transferred to Edge Column)")

    # -----------------------------------------------------
    # SECTION 2: PUNCHING SHEAR (INTEGRATED)
    # -----------------------------------------------------
    if HAS_CALC:
        st.markdown("---")
        st.markdown("### 2️⃣ Punching Shear Check")
        
        # Geometry setup
        c_col = float(c_para)
        load_area = (L_span * L_width) - ((c_col/100)**2)
        Vu_approx = float(w_u) * load_area 
        d_eff_avg = float(h_slab) - float(cover) - 1.6
        
        # Determine Column Condition for Calculation
        if "Interior" in span_type_str:
            col_cond = "interior"
        else:
            col_cond = "edge"
        
        # Call Calculation Module
        ps_res = calc.check_punching_shear(
            Vu=Vu_approx,        
            fc=float(fc),
            c1=c_col,            
            c2=c_col,            
            d=d_eff_avg,                
            col_type=col_cond,
            open_w=mat_props.get('open_w', 0),
            open_dist=mat_props.get('open_dist', 0),
            phi=phi_shear 
        )
        
        c_ps1, c_ps2 = st.columns([1, 2])
        with c_ps1:
            if HAS_PLOTS:
                
                st.pyplot(ddm_plots.plot_punching_shear_geometry(
                    c_col, c_col, ps_res['d'], ps_res['bo'], ps_res['status'], ps_res['ratio']
                ))
            else:
                st.info("Visual module unavailable")
        
        with c_ps2:
            st.markdown(f"**Condition:** {col_cond.capitalize()} Column")
            
            # Add Unbalanced Moment Warning
            if col_cond == "edge" and m_vals.get('M_unbal', 0) > 0:
                 st.info(f"ℹ️ **Note:** Edge column check considers Moment Transfer ($M_{{sc}}$) = {m_vals['M_unbal']:,.0f} kg-m")

            if ps_res['status'] == "OK":
                st.success(f"✅ **PASSED** (Ratio: {ps_res['ratio']:.2f})")
            else:
                st.error(f"❌ **FAILED** (Ratio: {ps_res['ratio']:.2f})")
                st.write("👉 Suggestion: Increase slab thickness, column size, or add drop panel.")
            
            with st.expander("Show Punching Calculation"):
                st.latex(f"v_u = \\frac{{V_u}}{{b_o d}} + \\frac{{\\gamma_v M_{{sc}} c}}{{J_c}}")
                st.write(f"Shear Capacity ($V_c$): {ps_res['phi_Vc']:,.0f} kg")
                st.write(f"Shear Demand ($V_u$): {ps_res['Vu']:,.0f} kg")

    # -----------------------------------------------------
    # SECTION 3: DEFLECTION (SERVICEABILITY)
    # -----------------------------------------------------
    st.markdown("---")
    st.markdown("### 3️⃣ Serviceability (Deflection)")
    
    def_res = calc_deflection_check(L_span, h_slab, w_u, fc, span_type_str)
    
    with st.container(border=True):
        c_d1, c_d2 = st.columns(2)
        with c_d1:
            st.markdown("**A) Minimum Thickness (ACI Table 8.3.1.1)**")
            if def_res['status_h']:
                st.success(f"✅ Provided {h_slab} cm $\ge$ Min {def_res['h_min']:.2f} cm")
            else:
                st.error(f"❌ Provided {h_slab} cm < Min {def_res['h_min']:.2f} cm")
            st.caption(f"Based on $L_n / {def_res['denom']:.0f}$")

        with c_d2:
            st.markdown("**B) Estimated Deflection ($\Delta_{total}$)**")
            st.write(f"Immediate (Elastic): {def_res['delta_imm']:.2f} cm")
            st.write(f"Long-term Multiplier: 3.0x (Creep+Shrinkage)")
            
            val = def_res['delta_total']
            lim = def_res['limit']
            
            if val < lim:
                st.success(f"✅ **{val:.2f} cm** (Limit L/240 = {lim:.2f} cm)")
            else:
                st.warning(f"⚠️ **{val:.2f} cm** (Exceeds Limit {lim:.2f} cm)")

    # -----------------------------------------------------
    # SECTION 4: REINFORCEMENT DESIGN
    # -----------------------------------------------------
    st.markdown("---")
    st.markdown("### 4️⃣ Reinforcement Design")
    
    # Map Rebar Config
    d_cst, s_cst = cfg.get('cs_top_db', 12), cfg.get('cs_top_spa', 20)
    d_csb, s_csb = cfg.get('cs_bot_db', 12), cfg.get('cs_bot_spa', 20)
    d_mst, s_mst = cfg.get('ms_top_db', 12), cfg.get('ms_top_spa', 20)
    d_msb, s_msb = cfg.get('ms_bot_db', 12), cfg.get('ms_bot_spa', 20)
    
    # Calculate all zones
    zones = [
        {"Label": "Col Strip - Top (-)", "Mu": m_vals['M_cs_neg'], "b": w_cs, "db": d_cst, "s": s_cst},
        {"Label": "Col Strip - Bot (+)", "Mu": m_vals['M_cs_pos'], "b": w_cs, "db": d_csb, "s": s_csb},
        {"Label": "Mid Strip - Top (-)", "Mu": m_vals['M_ms_neg'], "b": w_ms, "db": d_mst, "s": s_mst},
        {"Label": "Mid Strip - Bot (+)", "Mu": m_vals['M_ms_pos'], "b": w_ms, "db": d_msb, "s": s_msb},
    ]
    
    results = []
    for z in zones:
        res = calc_rebar_logic(z['Mu'], z['b'], z['db'], z['s'], h_slab, cover, fc, fy, is_main_dir, phi_bend)
        res.update(z)
        results.append(res)
    
    # Summary Table
    df_res = pd.DataFrame(results)[["Label", "Mu", "As_req", "As_prov", "DC", "Note"]]
    st.dataframe(
        df_res.style.format({"Mu": "{:,.0f}", "As_req": "{:.2f}", "As_prov": "{:.2f}", "DC": "{:.2f}"})
        .background_gradient(subset=["DC"], cmap="RdYlGn_r", vmin=0, vmax=1.2),
        use_container_width=True, hide_index=True
    )
    
    # Detailed Calculation View
    st.markdown("#### 🔍 Select Zone for Detailed Calculation")
    sel_zone = st.selectbox(f"Show details for ({axis_id}):", [z['Label'] for z in zones])
    target = next(z for z in results if z['Label'] == sel_zone)
    
    raw_inputs = (target['Mu'], target['b'], h_slab, cover, fc, fy, target['db'], target['s'], phi_bend)
    pct_val = (target['Mu'] / Mo * 100) if Mo > 0 else 0
    
    show_detailed_calculation(sel_zone, target, raw_inputs, pct_val, Mo)

    # Drawings
    if HAS_PLOTS:
        st.markdown("---")
        t1, t2 = st.tabs(["📉 Moment Diagram", "🏗️ Rebar Detailing"])
        rebar_map = {
            "CS_Top": f"DB{d_cst}@{s_cst}", "CS_Bot": f"DB{d_csb}@{s_csb}",
            "MS_Top": f"DB{d_mst}@{s_mst}", "MS_Bot": f"DB{d_msb}@{s_msb}"
        }
        with t1: st.pyplot(ddm_plots.plot_ddm_moment(L_span, c_para/100, m_vals))
        with t2: st.pyplot(ddm_plots.plot_rebar_detailing(L_span, h_slab, c_para, rebar_map, axis_id))

# ========================================================
# MAIN ENTRY POINT
# ========================================================
def render_dual(data_x, data_y, mat_props, w_u):
    st.markdown("## 🏗️ RC Slab Design (DDM Analysis)")
    
    # Span Configuration Selectors
    with st.expander("⚙️ Span Continuity Settings", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**X-Direction ($L_x$={data_x['L_span']}m)**")
            type_x = st.selectbox("Span Type X", ["Interior Span", "End Span - Edge Beam", "End Span - No Beam"], key="sx")
            data_x = update_moments_based_on_config(data_x, type_x)
        with c2:
            st.markdown(f"**Y-Direction ($L_y$={data_y['L_span']}m)**")
            type_y = st.selectbox("Span Type Y", ["Interior Span", "End Span - Edge Beam", "End Span - No Beam"], key="sy")
            data_y = update_moments_based_on_config(data_y, type_y)

    tab_x, tab_y = st.tabs(["➡️ X-Direction Check", "⬆️ Y-Direction Check"])
    
    with tab_x:
        render_interactive_direction(data_x, mat_props, "X", w_u, True)
    with tab_y:
        render_interactive_direction(data_y, mat_props, "Y", w_u, False)
