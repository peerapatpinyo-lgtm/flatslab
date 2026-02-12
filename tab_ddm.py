# tab_ddm.py
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt     
import matplotlib.patches as patches
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
        return {"Status": False, "Note": "Depth Error (d<=0)", "d": 0, "As_req": 0}

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
# 3. DETAILED CALCULATION RENDERER (ULTRA DETAILED)
# ========================================================
def show_detailed_calculation(zone_name, res, inputs, coeff_pct, Mo_val):
    # Unpack Inputs
    Mu, b, h, cover, fc, fy, db, s, phi_bend = inputs
    
    # Unit Conversions for display
    b_cm = b * 100
    Mu_kgcm = Mu * 100
    
    st.markdown(f"""
    <div style="background-color:#f0f9ff; padding:15px; border-radius:10px; border-left: 5px solid #0369a1;">
        <h4 style="margin:0; color:#0369a1;">🔍 Detailed Analysis: {zone_name}</h4>
        <p style="margin:5px 0 0 0; color:#475569; font-size:0.9em;">
            Comprehensive Step-by-Step Derivation & Verification
        </p>
    </div>
    """, unsafe_allow_html=True)
    

    c1, c2, c3 = st.tabs(["1️⃣ Load & Geometry", "2️⃣ Flexural Design", "3️⃣ Verification"])
    
    # --- TAB 1: MOMENT & GEOMETRY ---
    with c1:
        st.markdown("### 1.1 Geometry & Material Properties")
        st.write("Starting with section dimensions and material properties:")
        st.markdown(f"""
        - **Slab Thickness ($h$):** {h} cm
        - **Concrete Cover ($C_c$):** {cover} cm
        - **Bar Diameter ($d_b$):** {db} mm ({db/10:.1f} cm)
        - **Strip Width ($b$):** {b:.2f} m ({b_cm:.0f} cm)
        - **Material:** $f_c'={fc}$ ksc, $f_y={fy}$ ksc
        """)

        st.markdown("---")
        st.markdown("### 1.2 Effective Depth Calculation ($d$)")
        st.write("The effective depth is the distance from the extreme compression fiber to the centroid of the longitudinal tension reinforcement.")
        
        # Explicit check for layer offset
        layer_offset = 0.0
        # If the calculated d is less than standard d, it means we applied an offset for inner layers
        standard_d = h - cover - (db/20.0)
        if res['d'] < (standard_d - 0.01): # Use small epsilon for float comparison
             layer_offset = db/10.0
             st.info(f"ℹ️ **Note:** This is an **Inner Layer** reinforcement. We subtract the outer layer bar diameter ({layer_offset} cm).")

        st.write("**Formula:**")
        st.latex(r"d = h - C_c - \frac{d_b}{2} - \text{Layer Offset}")
        
        st.write("**Substitution:**")
        st.latex(f"d = {h} - {cover} - \\frac{{{db/10:.1f}}}{{2}} - {layer_offset}")
        
        st.write("**Result:**")
        st.latex(f"d = \\mathbf{{{res['d']:.2f}}} \\; \\text{{cm}}")
        
        st.markdown("---")
        st.markdown("### 1.3 Design Moment Calculation ($M_u$)")
        st.write("The design moment is derived from the Total Static Moment ($M_o$) distributed by the Direct Design Method (DDM) coefficients.")
        
        st.write("**Given:**")
        st.latex(f"M_o = \\mathbf{{{Mo_val:,.0f}}} \\; \\text{{kg-m}}")
        st.latex(f"\\text{{DDM Coefficient}} = {coeff_pct/100:.3f} \\; ({coeff_pct:.1f}\%)")
        
        st.write("**Calculation:**")
        st.latex(f"M_u = \\text{{Coeff}} \\times M_o")
        st.latex(f"M_u = {coeff_pct/100:.3f} \\times {Mo_val:,.0f} = \\mathbf{{{Mu:,.0f}}} \\; \\text{{kg-m}}")
        st.latex(f"M_u (converted) = {Mu:,.0f} \\times 100 = \\mathbf{{{Mu_kgcm:,.0f}}} \\; \\text{{kg-cm}}")

    # --- TAB 2: REINFORCEMENT ---
    with c2:
        st.markdown("### 2.1 Strength Reduction Factor")
        st.write(f"Using **$\\phi = {phi_bend}$** for tension-controlled sections (Flexure) as per ACI 318.")

        st.markdown("---")
        st.markdown("### 2.2 Nominal Strength Requirement ($R_n$)")
        st.write("First, we determine the required nominal strength coefficient $R_n$ to design the reinforcement ratio.")
        
        st.write("**Formula:**")
        st.latex(r"R_n = \frac{M_u}{\phi b d^2}")
        
        st.write("**Substitution:**")
        st.latex(f"R_n = \\frac{{{Mu_kgcm:,.0f}}}{{{phi_bend} \\cdot {b_cm:.0f} \\cdot ({res['d']:.2f})^2}}")
        
        denominator = phi_bend * b_cm * (res['d']**2)
        st.latex(f"R_n = \\frac{{{Mu_kgcm:,.0f}}}{{{denominator:,.0f}}}")
        
        st.write("**Result:**")
        st.latex(f"R_n = \\mathbf{{{res['Rn']:.3f}}} \\; \\text{{ksc}}")

        st.markdown("---")
        st.markdown("### 2.3 Required Reinforcement Ratio ($\\rho_{req}$)")
        
        # Explain Beta 1
        st.write(f"**Step A: Determine $\\beta_1$ Factor**")
        st.write(f"For concrete strength $f_c' = {fc}$ ksc:")
        if fc <= 280:
            st.latex(r"\beta_1 = 0.85 \quad (\because f_c' \le 280 \text{ ksc})")
        else:
            st.latex(r"\beta_1 = 0.85 - 0.05\frac{f_c' - 280}{70} \ge 0.65")
            st.latex(f"\\beta_1 = {res['beta1']:.3f}")

        st.write("**Step B: Calculate $\\rho_{req}$**")
        
        if res['rho_req'] == 0:
            st.info("Since $M_u$ is negligible, assume $\\rho_{req} \\approx 0$. Design will be governed by Minimum Steel ($A_{s,min}$).")
        elif res['rho_req'] == 999:
            st.error("❌ **CRITICAL FAILURE:** The section is too small. $R_n$ exceeds the maximum capacity allowed by the concrete. Increase slab thickness or concrete strength.")
        else:
            st.write("**Formula:**")
            st.latex(r"\rho_{req} = \frac{0.85 f_c'}{f_y} \left( 1 - \sqrt{1 - \frac{2 R_n}{0.85 f_c'}} \right)")
            
            # Show the term inside sqrt for clarity
            term_inside_sqrt = 1 - (2 * res['Rn']) / (0.85 * fc)
            
            st.write("**Substitution:**")
            st.latex(f"\\rho_{{req}} = \\frac{{0.85({fc})}}{{{fy}}} \\left( 1 - \\sqrt{{1 - \\frac{{2({res['Rn']:.3f})}}{{0.85({fc})}}}} \\right)")
            
            st.write("**Intermediate Calculation:**")
            st.latex(f"\\text{{Inside Sqrt}} = 1 - { (2 * res['Rn']) / (0.85 * fc) :.4f} = {term_inside_sqrt:.4f}")
            
            st.write("**Result:**")
            st.latex(f"\\rho_{{req}} = {0.85*fc/fy:.5f} \\times (1 - {np.sqrt(term_inside_sqrt):.4f}) = \\mathbf{{{res['rho_calc']:.5f}}}")

        st.markdown("---")
        st.markdown("### 2.4 Required Steel Area ($A_s$)")
        
        st.write("**1) Required Flexural Steel ($A_{s,flex}$):**")
        st.latex(f"A_{{s,flex}} = \\rho_{{req}} b d = {res['rho_calc']:.5f} \\cdot {b_cm:.0f} \\cdot {res['d']:.2f}")
        st.latex(f"A_{{s,flex}} = \\mathbf{{{res['As_flex']:.2f}}} \\; \\text{{cm}}^2")
        
        st.write("**2) Minimum Steel for Shrinkage & Temperature ($A_{s,min}$):**")
        st.write("According to ACI 318 for slabs using Deformed Bars ($f_y \ge 4000$ psi):")
        st.latex(r"A_{s,min} = 0.0018 \cdot b \cdot h")
        st.latex(f"A_{{s,min}} = 0.0018 \\cdot {b_cm:.0f} \\cdot {h} = \\mathbf{{{res['As_min']:.2f}}} \\; \\text{{cm}}^2")
        
        st.write("**3) Final Design Area ($A_{s,req}$):**")
        condition = "As_flex > As_min" if res['As_flex'] > res['As_min'] else "As_min > As_flex"
        st.info(f"👉 **Control Case:** {condition}")
        st.latex(f"A_{{s,req}} = \\max(A_{{s,flex}}, A_{{s,min}}) = \\max({res['As_flex']:.2f}, {res['As_min']:.2f})")
        st.latex(f"A_{{s,req}} = \\mathbf{{{res['As_req']:.2f}}} \\; \\text{{cm}}^2")

    # --- TAB 3: VERIFICATION ---
    with c3:
        st.markdown("### 3.1 Provided Reinforcement")
        st.write(f"**Selection:** DB{db} spaced at {s:.0f} cm")
        
        area_one_bar = np.pi * (db/10.0)**2 / 4.0
        
        st.write("**Area of one bar ($A_{bar}$):**")
        st.latex(f"A_{{bar}} = \\frac{{\\pi \cdot ({db/10.0})^2}}{{4}} = {area_one_bar:.2f} \\; \\text{{cm}}^2")
        
        st.write("**Total Provided Area ($A_{s,prov}$):**")
        st.latex(r"A_{s,prov} = \frac{b}{s} \times A_{bar}")
        st.latex(f"A_{{s,prov}} = \\frac{{{b_cm:.0f}}}{{{s:.0f}}} \\times {area_one_bar:.2f} = {b_cm/s:.2f} \\times {area_one_bar:.2f}")
        st.latex(f"A_{{s,prov}} = \\mathbf{{{res['As_prov']:.2f}}} \\; \\text{{cm}}^2")
        
        # Check Area
        if res['As_prov'] >= res['As_req']:
            st.success(f"✅ **PASS:** Provided Steel ({res['As_prov']:.2f}) $\ge$ Required Steel ({res['As_req']:.2f})")
        else:
            diff = res['As_req'] - res['As_prov']
            st.error(f"❌ **FAIL:** Deficient by {diff:.2f} cm². Decrease spacing or increase bar size.")

        st.markdown("---")
        st.markdown("### 3.2 Moment Capacity Verification ($\\phi M_n$)")
        st.write("We perform a reverse calculation to determine the actual capacity of the selected reinforcement.")
        
        st.write("**A) Equivalent Stress Block Depth ($a$):**")
        st.latex(r"a = \frac{A_{s,prov} f_y}{0.85 f_c' b}")
        st.latex(f"a = \\frac{{{res['As_prov']:.2f} \\cdot {fy}}}{{0.85 \\cdot {fc} \\cdot {b_cm:.0f}}}")
        st.latex(f"a = \\mathbf{{{res['a']:.2f}}} \\; \\text{{cm}}")
        
        st.write("**B) Nominal Moment Capacity ($M_n$):**")
        st.latex(r"M_n = A_{s,prov} f_y (d - a/2)")
        st.latex(f"M_n = {res['As_prov']:.2f} \\cdot {fy} \\cdot ({res['d']:.2f} - {res['a']:.2f}/2)")
        
        Mn_val_kgcm = res['As_prov'] * fy * (res['d'] - res['a']/2)
        st.latex(f"M_n = {Mn_val_kgcm:,.0f} \\; \\text{{kg-cm}}")
        
        st.write("**C) Design Moment Capacity ($\\phi M_n$):**")
        st.latex(f"\\phi M_n = {phi_bend} \\cdot M_n = {phi_bend} \\cdot {Mn_val_kgcm:,.0f}")
        st.latex(f"\\phi M_n = {res['PhiMn']*100:,.0f} \\; \\text{{kg-cm}} = \\mathbf{{{res['PhiMn']:,.0f}}} \\; \\text{{kg-m}}")
        
        st.markdown("---")
        st.markdown("### 3.3 Demand / Capacity Ratio (D/C)")
        
        d_c = res['DC']
        color = "green" if d_c <= 1.0 else "red"
        status_text = "SAFE" if d_c <= 1.0 else "UNSAFE"
        
        st.write("The ratio of Load ($M_u$) to Capacity ($\\phi M_n$):")
        st.latex(f"D/C = \\frac{{M_u}}{{\\phi M_n}} = \\frac{{{Mu:,.0f}}}{{{res['PhiMn']:,.0f}}}")
        st.markdown(f"$$ D/C = \\color{{{color}}}{{\\mathbf{{{d_c:.3f}}}}} \\quad (\\text{{{status_text}}}) $$")

    return

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
            
            if m_vals.get('M_unbal', 0) > 0:
                st.warning(f"⚠️ **Unbalanced Moment ($M_{{sc}}$):** {m_vals['M_unbal']:,.0f} kg-m (Transferred to Edge Column)")

    # -----------------------------------------------------
    # SECTION 2: PUNCHING SHEAR (INTEGRATED)
    # -----------------------------------------------------
    if HAS_CALC:
        st.markdown("---")
        st.markdown("### 2️⃣ Punching Shear Check")
        
        
        c_col = float(c_para)
        load_area = (L_span * L_width) - ((c_col/100)**2)
        Vu_approx = float(w_u) * load_area 
        d_eff_avg = float(h_slab) - float(cover) - 1.6
        
        if "Interior" in span_type_str:
            col_cond = "interior"
        else:
            col_cond = "edge"
        
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
    # SECTION 3: DEFLECTION
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
    
    d_cst, s_cst = cfg.get('cs_top_db', 12), cfg.get('cs_top_spa', 20)
    d_csb, s_csb = cfg.get('cs_bot_db', 12), cfg.get('cs_bot_spa', 20)
    d_mst, s_mst = cfg.get('ms_top_db', 12), cfg.get('ms_top_spa', 20)
    d_msb, s_msb = cfg.get('ms_bot_db', 12), cfg.get('ms_bot_spa', 20)
    
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
    
    df_res = pd.DataFrame(results)[["Label", "Mu", "As_req", "As_prov", "DC", "Note"]]
    st.dataframe(
        df_res.style.format({"Mu": "{:,.0f}", "As_req": "{:.2f}", "As_prov": "{:.2f}", "DC": "{:.2f}"})
        .background_gradient(subset=["DC"], cmap="RdYlGn_r", vmin=0, vmax=1.2),
        use_container_width=True, hide_index=True
    )
    
    # --- IMPORTANT: THIS IS THE TRIGGER FOR THE DETAILED VIEW ---
    st.markdown("#### 🔍 Select Zone for Detailed Calculation")
    sel_zone = st.selectbox(f"Show details for ({axis_id}):", [z['Label'] for z in zones], key=f"sel_{axis_id}")
    target = next(z for z in results if z['Label'] == sel_zone)
    
    raw_inputs = (target['Mu'], target['b'], h_slab, cover, fc, fy, target['db'], target['s'], phi_bend)
    pct_val = (target['Mu'] / Mo * 100) if Mo > 0 else 0
    
    # CALL THE FUNCTION
    show_detailed_calculation(sel_zone, target, raw_inputs, pct_val, Mo)

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
# HELPER: ENGINEERING SCHEMATIC + COEFFICIENTS (FINAL)
# ========================================================

def draw_span_schematic(span_type):
    """
    Ultimate Engineering Schematic:
    - Integrates Structural Geometry, ACI 318 Coefficients, and Strip Distribution (CS/MS).
    - clear visualization of moment apportionment.
    """
    fig, ax = plt.subplots(figsize=(10, 5.5)) 
    ax.set_xlim(-2.5, 12.5)
    ax.set_ylim(-2.0, 7.5) # Space for detailed breakdown
    ax.axis('off')

    # --- Styles ---
    concrete_color = '#f5f5f5'
    cs_color = '#e3f2fd' # Light Blue for Column Strip
    ms_color = '#fff3e0' # Light Orange for Middle Strip
    line_style = {'edgecolor': '#333', 'linewidth': 1.5}
    
    # Styles for Text & Boxes
    box_total = dict(boxstyle="round,pad=0.3", fc="white", ec="black", lw=1.5)
    text_cs = dict(fontsize=8.5, weight='bold', color='#0277bd', ha='center')
    text_ms = dict(fontsize=8.5, weight='bold', color='#ef6c00', ha='center')

    # --- Helper: Draw Strip Distribution Table ---
    def draw_distribution(ext_c, pos_c, int_c, is_flat_plate=False):
        """
        Draws the moment breakdown (Total -> CS -> MS) at critical sections.
        Note: CS/MS splits are illustrative typical values for visualization.
        """
        # Typical factors for visualization (User should rely on actual calcs for exact reinforcement)
        if is_flat_plate:
            cs_ratio_neg, cs_ratio_pos = 0.75, 0.60
        else: # Beam
            cs_ratio_neg, cs_ratio_pos = 0.85, 0.75

        sections = [0, 5, 10]
        coeffs = [ext_c, pos_c, int_c]
        
        for x, c_total in zip(sections, coeffs):
            # Determine CS ratio for this section (Neg or Pos)
            is_pos = (x == 5)
            ratio = cs_ratio_pos if is_pos else cs_ratio_neg
            
            val_cs = c_total * ratio
            val_ms = c_total * (1 - ratio)

            # 1. Total Moment Box
            ax.text(x, 6.2, f"Total $M_o$\n{c_total:.2f}", ha='center', weight='bold', fontsize=10, bbox=box_total)
            
            # 2. Breakdown Text
            ax.text(x, 5.3, f"CS: {val_cs:.2f}", **text_cs)
            ax.text(x, 4.9, f"MS: {val_ms:.2f}", **text_ms)
            
            # 3. Leader Lines
            ax.plot([x, x], [4.5, 2.8], color='#90a4ae', linestyle=':', linewidth=1)

    # ---------------- Main Drawing Logic ----------------
    
    # 1. Background Strips (Plan View Logic)
    ax.add_patch(patches.Rectangle((-2.5, 4.8), 15, 0.6, facecolor=cs_color, alpha=0.6)) # CS Band
    ax.add_patch(patches.Rectangle((-2.5, 4.2), 15, 0.6, facecolor=ms_color, alpha=0.6)) # MS Band
    ax.text(-2.4, 5.1, "Column Strip (CS)", color='#0277bd', fontsize=8, weight='bold', ha='left')
    ax.text(-2.4, 4.4, "Middle Strip (MS)", color='#ef6c00', fontsize=8, weight='bold', ha='left')

    # 2. Structural Geometry Setup
    slab_y, slab_h = 2.0, 0.6
    col_w, col_h = 1.0, 2.2
    beam_d = 1.3

    # Common Columns
    ax.add_patch(patches.Rectangle((-col_w/2, slab_y-col_h), col_w, col_h, fc='#546e7a', ec='black', zorder=5)) # Left
    ax.add_patch(patches.Rectangle((10-col_w/2, slab_y-col_h), col_w, col_h, fc='#546e7a', ec='black', zorder=5)) # Right

    if "Interior" in span_type:
        # === INTERIOR SPAN ===
        ax.add_patch(patches.Rectangle((-2.5, slab_y), 15, slab_h, fc=concrete_color, **line_style))
        
        # Continuity
        ax.text(-2.0, slab_y+slab_h/2, "≈", fontsize=24, rotation=90, va='center')
        ax.text(12.0, slab_y+slab_h/2, "≈", fontsize=24, rotation=90, va='center')
        
        # Data
        draw_distribution(0.65, 0.35, 0.65, is_flat_plate=True)
        ax.text(5, 7.2, "INTERIOR SPAN DISTRIBUTION", ha='center', fontsize=12, weight='extrabold')
        ax.text(0, -1.0, "Interior Col", ha='center', fontsize=9)
        ax.text(10, -1.0, "Interior Col", ha='center', fontsize=9)

    elif "Edge Beam" in span_type:
        # === END SPAN w/ BEAM ===
        ax.add_patch(patches.Rectangle((-col_w/2, slab_y), 13, slab_h, fc=concrete_color, **line_style))
        ax.add_patch(patches.Rectangle((-col_w/2, slab_y-beam_d), col_w*1.5, beam_d, fc=concrete_color, **line_style)) # Beam
        
        # Continuity
        ax.text(12.0, slab_y+slab_h/2, "≈", fontsize=24, rotation=90, va='center')
        
        # Data
        draw_distribution(0.30, 0.50, 0.70, is_flat_plate=False)
        ax.text(5, 7.2, "END SPAN - EDGE BEAM DISTRIBUTION", ha='center', fontsize=12, weight='extrabold')
        
        # Annotation
        ax.annotate('Stiff Beam', xy=(0.8, slab_y-beam_d/2), xytext=(3, 0),
                    arrowprops=dict(arrowstyle="->", color='#c62828'), color='#c62828', weight='bold')
        ax.text(0, -1.0, "Exterior Col", ha='center', fontsize=9, weight='bold')

    elif "No Beam" in span_type:
        # === FLAT PLATE (NO BEAM) ===
        ax.add_patch(patches.Rectangle((-col_w/2, slab_y), 13, slab_h, fc=concrete_color, **line_style))
        # Phantom Beam
        ax.add_patch(patches.Rectangle((-col_w/2, slab_y-beam_d), col_w, beam_d, fc='none', ec='#d32f2f', ls='--')) 
        
        # Continuity
        ax.text(12.0, slab_y+slab_h/2, "≈", fontsize=24, rotation=90, va='center')
        
        # Data (Using 0.26 / 0.52 / 0.70)
        draw_distribution(0.26, 0.52, 0.70, is_flat_plate=True)
        ax.text(5, 7.2, "END SPAN - FLAT PLATE DISTRIBUTION", ha='center', fontsize=12, weight='extrabold')
        
        # Annotation
        ax.annotate('No Beam\n(Flexible)', xy=(0.5, slab_y), xytext=(3, 0.5),
                    arrowprops=dict(arrowstyle="->", color='#d32f2f'), color='#d32f2f', weight='bold')
        ax.text(0, -1.0, "Exterior Col", ha='center', fontsize=9, weight='bold')

    # --- Footer ---
    ax.annotate('', xy=(0, -0.5), xytext=(10, -0.5), arrowprops=dict(arrowstyle='<->', linewidth=1.2))
    ax.text(5, -0.8, "Clear Span ($L_n$)", ha='center', fontsize=10, fontstyle='italic')

    return fig
# ========================================================
# MAIN ENTRY POINT
# ========================================================
def render_dual(data_x, data_y, mat_props, w_u):
    st.markdown("## 🏗️ RC Slab Design (DDM Analysis)")
    
    # ------------------------------------------------------------------
    # ส่วนแก้ไข: Span Continuity Settings พร้อมรูปภาพประกอบ
    # ------------------------------------------------------------------
    with st.expander("⚙️ Span Continuity Settings & Diagrams", expanded=True):
        st.info("💡 **Tips:** เลือกประเภทของช่วงพาด (Span Type) ให้ตรงกับตำแหน่งของแผ่นพื้นจริง เพื่อให้โปรแกรมเลือกสัมประสิทธิ์โมเมนต์ (Moment Coefficients) ตามมาตรฐาน ACI 318 ได้ถูกต้อง")
        
        # --- X-Direction ---
        st.markdown(f"### ➡️ X-Direction Analysis ($L_x$={data_x['L_span']}m)")
        c1_x, c2_x = st.columns([1, 2]) # แบ่งสัดส่วน 1:2 (เมนู : รูปภาพ)
        
        with c1_x:
            # Dropdown Selection
            type_x = st.radio(
                "Select Span Condition (X-Axis):", 
                ["Interior Span", "End Span - Edge Beam", "End Span - No Beam"], 
                key="sx",
                help="Interior: ต่อเนื่อง 2 ฝั่ง / End Span: อยู่ริมอาคาร"
            )
            # อัปเดตข้อมูลโมเมนต์ทันที
            data_x = update_moments_based_on_config(data_x, type_x)
            
        with c2_x:
            # แสดงรูป Schematic ทันที
            st.pyplot(draw_span_schematic(type_x), use_container_width=False)

        st.markdown("---") # เส้นคั่นแนวนอน

        # --- Y-Direction ---
        st.markdown(f"### ⬆️ Y-Direction Analysis ($L_y$={data_y['L_span']}m)")
        c1_y, c2_y = st.columns([1, 2])
        
        with c1_y:
            type_y = st.radio(
                "Select Span Condition (Y-Axis):", 
                ["Interior Span", "End Span - Edge Beam", "End Span - No Beam"], 
                key="sy"
            )
            data_y = update_moments_based_on_config(data_y, type_y)
            
        with c2_y:
            st.pyplot(draw_span_schematic(type_y), use_container_width=False)
            
    # ------------------------------------------------------------------
    # จบส่วนแก้ไข
    # ------------------------------------------------------------------

    tab_x, tab_y = st.tabs(["➡️ X-Direction Check", "⬆️ Y-Direction Check"])
    
    with tab_x:
        render_interactive_direction(data_x, mat_props, "X", w_u, True)
    with tab_y:
        render_interactive_direction(data_y, mat_props, "Y", w_u, False)
