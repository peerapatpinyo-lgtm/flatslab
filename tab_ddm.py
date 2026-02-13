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
    M_neg_total = coeffs['neg'] * Mo    # Interior Negative
    M_pos_total = coeffs['pos'] * Mo    # Positive
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
# 4. INTERACTIVE DIRECTION CHECK (TAB CONTENT)
# ========================================================
def render_interactive_direction(data, mat_props, axis_id, w_u, is_main_dir):
    # -----------------------------------------------------
    # 0. SETUP & UNPACKING
    # -----------------------------------------------------
    # Unpack basic props
    h_slab = float(mat_props['h_slab'])
    cover = float(mat_props['cover'])
    fc = float(mat_props['fc'])
    fy = float(mat_props['fy'])
    phi_bend = mat_props.get('phi', 0.90)        
    phi_shear = mat_props.get('phi_shear', 0.85) 
    
    # Rebar Config
    cfg = mat_props.get('rebar_cfg', {})
    
    # Data from Analysis
    L_span = data['L_span']
    L_width = data.get('L_width', L_span) # Use get to prevent key error if square
    c_para = float(data['c_para'])
    Mo = data['Mo']
    m_vals = data['M_vals']
    coeff_desc = data.get('coeffs_desc', 'Standard')
    span_type_str = data.get('span_type_str', 'Interior')
    
    # Dimension Symbols
    span_sym, width_sym = ("L_x", "L_y") if axis_id == "X" else ("L_y", "L_x")
    ln_val = L_span - (c_para/100.0)
    
    # Strip Widths (Column Strip / Middle Strip)
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
            
            # --- Unbalanced Moment Check & Note (CRITICAL SECTION) ---
            M_sc = m_vals.get('M_unbal', 0)
            
            if M_sc > 0:
                st.warning(f"⚠️ **Unbalanced Moment ($M_{{sc}}$):** {M_sc:,.0f} kg-m (Transferred to Edge Column)")
                
                # Calculate coefficient used for display
                coeff_used = M_sc / Mo if Mo > 0 else 0.30
                
                # [ENGLISH NOTE AS REQUESTED]
                st.markdown(f"""
                > 📝 **Engineering Note:** > This value is derived from **$M_{{sc}} = {coeff_used:.2f} \\times M_o$** (Exterior Negative Moment).  
                > It represents the moment transferred directly to the edge column due to the **discontinuity** at the slab edge (no adjacent slab to balance the moment).  
                > **This is the critical factor causing high punching shear stress.**
                """)
            else:
                 st.success("✅ **Balanced Span:** No significant unbalanced moment transfer (Interior Span).")

    # -----------------------------------------------------
    # -----------------------------------------------------
    # SECTION 2: PUNCHING SHEAR (VERIFIED PHYSICS MODE)
    # -----------------------------------------------------
    if HAS_CALC:
        st.markdown("---")
        st.markdown("### 2️⃣ Punching Shear Check (Verified Calculation)")
        
        # --- A. PREPARE INPUTS ---
        h_slab_val = float(h_slab)
        cover_val = float(cover)
        
        # Assumption: Bar diameter avg ~ 1.6 cm (DB12 + DB20 or similar)
        d_avg = h_slab_val - cover_val - 1.6 
        
        # Load & Dimensions
        w_u_val = float(w_u)
        c1 = float(c_para) # Dimension perpendicular to edge (Length of moment arm direction)
        c2 = float(c_para) # Dimension parallel to edge (Width) - Assuming square column input
        
        # --- B. GEOMETRY & CRITICAL SECTION ---
        st.markdown("#### **Step 1: Geometry & Critical Section Properties**")
        
        is_edge = "Interior" not in span_type_str
        
        if not is_edge:
            # === INTERIOR COLUMN (4 Sides) ===
            st.info("📍 **Type:** Interior Column (Rectangular Section)")
            
            # 1. Dimensions of Critical Section
            b1 = c1 + d_avg
            b2 = c2 + d_avg
            bo = 2 * (b1 + b2)
            
            # 2. Centroid & Jc (Symmetric)
            c_AB = b1 / 2.0  # Distance to neutral axis
            
            # Jc Formula for Box Section (ACI / MacGregor)
            term1 = (d_avg * b1**3) / 6.0
            term2 = (d_avg**3 * b1) / 6.0
            term3 = (d_avg * b2 * b1**2) / 2.0
            J_c = term1 + term2 + term3
            
            # 3. Gamma
            gamma_f = 1.0 / (1.0 + (2.0/3.0) * (b1/b2)**0.5)
            gamma_v = 1.0 - gamma_f
            
            # 4. Moment
            M_unbal = 0.0 # Typically 0 for interior in simplified DDM
            
            # Display Geometry
            st.latex(f"b_o = 2({c1}+{d_avg:.2f}) + 2({c2}+{d_avg:.2f}) = \\mathbf{{{bo:.2f}}} \\; cm")
            
        else:
            # === EDGE COLUMN (3 Sides - U Shape) ===
            # นี่คือจุดที่ละเอียดอ่อนที่สุด เช็คบรรทัดต่อบรรทัดได้เลยครับ
            st.info("📍 **Type:** Edge Column (U-Shaped Section)")
            
            

            # 1. Dimensions of Critical Section
            # Side 1 (Perpendicular to edge): c1 + d/2
            L1 = c1 + (d_avg / 2.0) 
            # Side 2 (Parallel to edge): c2 + d
            L2 = c2 + d_avg
            
            # Perimeter
            bo = (2 * L1) + L2
            
            st.write(f"**Side legs ($L_1$):** {c1} + {d_avg:.2f}/2 = {L1:.2f} cm")
            st.write(f"**Front face ($L_2$):** {c2} + {d_avg:.2f} = {L2:.2f} cm")
            st.latex(f"b_o = 2({L1:.2f}) + {L2:.2f} = \\mathbf{{{bo:.2f}}} \\; cm")

            # 2. Find Centroid (c_AB)
            # Take moment of area about the INNER FACE (Face inside the slab)
            # Area of legs = 2 * (L1 * d)
            # Area of front = L2 * d
            # Centroid of legs is at -L1/2 from inner face
            # Centroid of front is at 0 from inner face
            area_legs = 2 * L1 * d_avg
            area_front = L2 * d_avg
            total_area_shear = bo * d_avg
            
            # Moment of Area / Total Area
            # (Area_legs * (-L1/2)) / Total_Area
            x_bar = (area_legs * (-L1/2.0)) / total_area_shear
            
            # c_AB (Distance from Centroid to Inner Face - Critical Point)
            c_AB = abs(x_bar) 
            # c_CD (Distance from Centroid to Outer Edge)
            c_CD = L1 - c_AB
            
            st.write("---")
            st.write("**Finding Centroid ($c_{AB}$):**")
            st.latex(r"c_{AB} = \frac{\sum A_i x_i}{A_{total}} = \frac{2(L_1 d)(L_1/2)}{b_o d} = \frac{L_1^2}{b_o}") 
            st.latex(f"c_{{AB}} = \\frac{{{L1:.2f}^2}}{{{bo:.2f}}} = \\mathbf{{{c_AB:.2f}}} \\; cm \\; (\\text{{Inner Face}})")

            # 3. Calculate Jc (Polar Moment of Inertia) using Parallel Axis Theorem
            # Jc = Sum ( I_local + A * dist^2 ) + Sum ( I_torsion )
            
            # --- Part 1: Two Side Legs (Calculated relative to Centroid) ---
            # Inertia of leg about its own center + Area * (distance to centroid)^2
            # Distance from leg center (-L1/2) to Centroid (-c_AB) is |L1/2 - c_AB|
            dist_leg = abs((L1/2.0) - c_AB)
            I_leg_local = (d_avg * L1**3) / 12.0
            I_leg_shift = (L1 * d_avg) * (dist_leg**2)
            J_legs = 2.0 * (I_leg_local + I_leg_shift) # 2 legs
            
            # --- Part 2: Front Face (Calculated relative to Centroid) ---
            # Distance from front face (0) to Centroid (-c_AB) is c_AB
            # Inertia is thin rectangle approx + Area * shift
            I_front_local = (L2 * d_avg**3) / 12.0 # Often small but technically there
            I_front_shift = (L2 * d_avg) * (c_AB**2)
            J_front = I_front_local + I_front_shift
            
            J_c = J_legs + J_front
            
            st.write("**Calculating $J_c$:**")
            st.latex(f"J_{{legs}} = 2[\\frac{{d L_1^3}}{{12}} + (L_1 d)(x_{{leg}} - c_{{AB}})^2]")
            st.latex(f"J_{{front}} = (L_2 d)(c_{{AB}})^2")
            st.latex(f"J_c = {J_legs:,.0f} + {J_front:,.0f} = \\mathbf{{{J_c:,.0f}}} \\; cm^4")
            
            # 4. Gamma v
            gamma_f = 1.0 / (1.0 + (2.0/3.0) * (L1/L2)**0.5)
            gamma_v = 1.0 - gamma_f
            st.latex(f"\\gamma_v = 1 - \\frac{{1}}{{1 + \\frac{{2}}{{3}}\\sqrt{{{L1:.2f}/{L2:.2f}}}}} = \\mathbf{{{gamma_v:.3f}}}")
            
            M_unbal = m_vals.get('M_unbal', 0)

        # --- C. LOADS & STRESS ---
        st.markdown("#### **Step 2: Loads & Stress Calculation**")
        
        # Vu
        area_panel = (L_span * L_width)
        area_col = (c1/100) * (c2/100)
        Vu = w_u_val * (area_panel - area_col)
        
        # Stress 1: Direct Shear
        v1 = Vu / (bo * d_avg)
        
        # Stress 2: Moment Transfer
        # Critical stress is at the INNER FACE (where v1 and v2 add up)
        # Formula: v = Vu/Ac + (gamma * M * c) / Jc
        if M_unbal > 0:
            M_sc_cm = M_unbal * 100 # Convert kg-m to kg-cm
            v2 = (gamma_v * M_sc_cm * c_AB) / J_c
            sign_text = "+" 
        else:
            v2 = 0
            sign_text = ""
            
        v_total = v1 + v2
        
        col_res1, col_res2 = st.columns(2)
        with col_res1:
            st.write(f"**$V_u$:** {Vu:,.0f} kg")
            st.write(f"**$v_{{load}}$:** {v1:.2f} ksc")
        with col_res2:
            st.write(f"**$M_{{sc}}$:** {M_unbal:,.0f} kg-m")
            st.write(f"**$v_{{moment}}$:** {v2:.2f} ksc")
            
        st.latex(r"v_{max} = \frac{V_u}{b_o d} + \frac{\gamma_v M_{sc} c_{AB}}{J_c}")
        st.latex(f"v_{{max}} = {v1:.2f} {sign_text} {v2:.2f} = \\mathbf{{{v_total:.2f}}} \\; ksc")

        # --- D. CAPACITY & CONCLUSION ---
        st.markdown("#### **Step 3: Verification (ACI 318)**")
        
        # Capacity (ACI Metric)
        # 1.06 * sqrt(fc') is the standard approximation for ksc units 
        # (Derived from 0.33 sqrt(fc_MPa) or 4 sqrt(fc_psi))
        phi_vc = phi_shear * 1.06 * (fc**0.5)
        
        ratio = v_total / phi_vc
        
        st.write(f"**Capacity ($\\phi v_c$):** {phi_shear} × 1.06 × √{fc} = **{phi_vc:.2f} ksc**")
        
        if v_total <= phi_vc:
            st.success(f"✅ **PASS** (Ratio: {ratio:.2f})")
            st.progress(min(ratio, 1.0))
        else:
            st.error(f"❌ **FAIL** (Ratio: {ratio:.2f})")
            st.progress(min(ratio, 1.0))
            
            # Recommendation
            req_d = d_avg * (ratio**0.5)
            req_h = req_d + cover_val + 1.6
            st.warning(f"💡 **Fix:** Needs slab thickness approx **{req_h:.1f} cm**")
            
    # -----------------------------------------------------
    # SECTION 3: SERVICEABILITY (DEFLECTION)
    # -----------------------------------------------------
    st.markdown("---")
    st.markdown("### 3️⃣ Serviceability (Deflection)")
    
    def_res = calc_deflection_check(L_span, h_slab, w_u, fc, span_type_str)
    
    with st.container(border=True):
        c_d1, c_d2 = st.columns(2)
        
        # A) Thickness Check
        with c_d1:
            st.markdown("**A) Minimum Thickness (ACI Table 8.3.1.1)**")
            if def_res['status_h']:
                st.success(f"✅ Provided {h_slab} cm $\ge$ Min {def_res['h_min']:.2f} cm")
            else:
                st.error(f"❌ Provided {h_slab} cm < Min {def_res['h_min']:.2f} cm")
            st.caption(f"Based on $L_n / {def_res['denom']:.0f}$")

        # B) Deflection Calc
        with c_d2:
            st.markdown("**B) Estimated Deflection ($\Delta_{total}$)**")
            st.write(f"Immediate (Elastic): {def_res['delta_imm']:.2f} cm")
            # Using 3.0x as requested (Immediate + Creep/Shrinkage ~ 2.0)
            st.write(f"Long-term Multiplier: 3.0x") 
            
            val = def_res['delta_total']
            lim = def_res['limit']
            
            if val <= lim:
                st.success(f"✅ **{val:.2f} cm** (Limit L/240 = {lim:.2f} cm)")
            else:
                st.warning(f"⚠️ **{val:.2f} cm** (Exceeds Limit {lim:.2f} cm)")
    # -----------------------------------------------------
    # SECTION 4: REINFORCEMENT DESIGN
    # -----------------------------------------------------
    st.markdown("---")
    st.markdown("### 4️⃣ Reinforcement Design")
    
    # Get Rebar Settings (Diameter/Spacing) for each zone
    d_cst, s_cst = cfg.get('cs_top_db', 12), cfg.get('cs_top_spa', 20)
    d_csb, s_csb = cfg.get('cs_bot_db', 12), cfg.get('cs_bot_spa', 20)
    d_mst, s_mst = cfg.get('ms_top_db', 12), cfg.get('ms_top_spa', 20)
    d_msb, s_msb = cfg.get('ms_bot_db', 12), cfg.get('ms_bot_spa', 20)
    
    # Define Zones Data
    zones = [
        {"Label": "Col Strip - Top (-)", "Mu": m_vals['M_cs_neg'], "b": w_cs, "db": d_cst, "s": s_cst},
        {"Label": "Col Strip - Bot (+)", "Mu": m_vals['M_cs_pos'], "b": w_cs, "db": d_csb, "s": s_csb},
        {"Label": "Mid Strip - Top (-)", "Mu": m_vals['M_ms_neg'], "b": w_ms, "db": d_mst, "s": s_mst},
        {"Label": "Mid Strip - Bot (+)", "Mu": m_vals['M_ms_pos'], "b": w_ms, "db": d_msb, "s": s_msb},
    ]
    
    results = []
    # Calculate for all zones
    for z in zones:
        # Call Logic
        res = calc_rebar_logic(
            z['Mu'], z['b'], z['db'], z['s'], 
            h_slab, cover, fc, fy, is_main_dir, phi_bend
        )
        # Merge results with label info
        res.update(z)
        results.append(res)
    
    # Display Summary Table
    df_res = pd.DataFrame(results)[["Label", "Mu", "As_req", "As_prov", "DC", "Note"]]
    
    # Style the dataframe (Gradient for D/C Ratio)
    st.dataframe(
        df_res.style.format({
            "Mu": "{:,.0f}", 
            "As_req": "{:.2f}", 
            "As_prov": "{:.2f}", 
            "DC": "{:.2f}"
        })
        .background_gradient(subset=["DC"], cmap="RdYlGn_r", vmin=0, vmax=1.2),
        use_container_width=True, 
        hide_index=True
    )
    
    # --- DETAILED CALCULATION SELECTOR ---
    st.markdown("#### 🔍 Select Zone for Detailed Calculation")
    sel_zone = st.selectbox(f"Show details for ({axis_id}):", [z['Label'] for z in zones], key=f"sel_{axis_id}")
    
    # Retrieve data for selected zone
    target = next(z for z in results if z['Label'] == sel_zone)
    
    # Prepare tuple for display function
    raw_inputs = (target['Mu'], target['b'], h_slab, cover, fc, fy, target['db'], target['s'], phi_bend)
    pct_val = (target['Mu'] / Mo * 100) if Mo > 0 else 0
    
    # CALL THE DETAILED DISPLAY FUNCTION
    show_detailed_calculation(sel_zone, target, raw_inputs, pct_val, Mo)

    # --- PLOTS (Moment & Detailing) ---
    if HAS_PLOTS:
        st.markdown("---")
        t1, t2 = st.tabs(["📉 Moment Diagram", "🏗️ Rebar Detailing"])
        
        rebar_map = {
            "CS_Top": f"DB{d_cst}@{s_cst}", "CS_Bot": f"DB{d_csb}@{s_csb}",
            "MS_Top": f"DB{d_mst}@{s_mst}", "MS_Bot": f"DB{d_msb}@{s_msb}"
        }
        
        with t1: 
            st.pyplot(ddm_plots.plot_ddm_moment(L_span, c_para/100, m_vals))
        with t2: 
            st.pyplot(ddm_plots.plot_rebar_detailing(L_span, h_slab, c_para, rebar_map, axis_id))


# ========================================================
# HELPER: ENGINEERING SCHEMATIC + COEFFICIENTS (FINAL)
# ========================================================

def draw_span_schematic(span_type):
    """
    Final Refined Schematic (Fixed Overlapping Text):
    - Expanded Left Margin (xlim -4.0) to prevent Label collision.
    - Cleaned up text alignment for CS/MS strips.
    """
    fig, ax = plt.subplots(figsize=(10, 6)) 
    # ขยายแกน X ด้านซ้ายเพิ่มขึ้น เพื่อกันตัวหนังสือชนกัน
    ax.set_xlim(-4.0, 12.5)
    ax.set_ylim(-1.5, 8.0) 
    ax.axis('off')

    # --- Color Palette ---
    concrete_color = '#f5f5f5'
    
    # Column Strip (CS) - Blue Theme
    cs_band_color = '#e1f5fe'  # Light Blue Background
    cs_text_color = '#0277bd'  # Darker Blue Text for readability
    
    # Middle Strip (MS) - Orange Theme
    ms_band_color = '#fff3e0'  # Light Orange Background
    ms_text_color = '#ef6c00'  # Darker Orange Text

    # --- Helper: Draw Distribution Data ---
    def draw_data_column(x, m_total, is_flat_plate, section_type):
        """
        Draws the vertical stack of data: Total -> CS -> MS
        """
        if section_type == 'neg':
            cs_ratio = 0.75 if is_flat_plate else 0.85 
        else:
            cs_ratio = 0.60 if is_flat_plate else 0.75
            
        ms_ratio = 1.0 - cs_ratio
        
        val_cs = m_total * cs_ratio
        val_ms = m_total * ms_ratio

        # --- DRAWING THE DATA STACK ---
        
        # A. Total Moment Box (Top) - Raised slightly to y=7.0
        ax.text(x, 7.0, f"Total $M_o$\n{m_total:.2f}", 
                ha='center', va='center', weight='bold', fontsize=9, 
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="black", lw=1.2))

        # B. Connection Line
        ax.plot([x, x], [6.5, 6.0], color='#b0bec5', linestyle='-', linewidth=1.2)

        # C. Column Strip Value (Inside Blue Band)
        # Center vertically in the band (y=5.6)
        ax.text(x, 5.6, f"CS: {val_cs:.3f}", 
                ha='center', va='center', weight='bold', fontsize=9, color=cs_text_color)

        # D. Middle Strip Value (Inside Orange Band)
        # Center vertically in the band (y=4.8)
        ax.text(x, 4.8, f"MS: {val_ms:.3f}", 
                ha='center', va='center', weight='bold', fontsize=9, color=ms_text_color)
        
        # E. Leader Line to Structure
        ax.plot([x, x], [4.5, 2.8], color='#cfd8dc', linestyle=':', linewidth=1.2)

    # ---------------- DRAWING LOGIC ----------------

    # 1. BACKGROUND STRIPS (The Layers) - ขยับไปทางซ้ายสุดที่ x=-4.0
    # CS Band (Upper Layer) - Blue (y=5.2 to 6.0)
    ax.add_patch(patches.Rectangle((-4.0, 5.2), 16.5, 0.8, facecolor=cs_band_color, edgecolor='none'))
    # Label for CS - อยู่ซ้ายสุด ไม่ชนใครแน่นอน
    ax.text(-3.8, 5.6, "Column Strip\n(CS)", color=cs_text_color, fontsize=9, weight='bold', ha='left', va='center')

    # MS Band (Lower Layer) - Orange (y=4.4 to 5.2)
    ax.add_patch(patches.Rectangle((-4.0, 4.4), 16.5, 0.8, facecolor=ms_band_color, edgecolor='none'))
    # Label for MS
    ax.text(-3.8, 4.8, "Middle Strip\n(MS)", color=ms_text_color, fontsize=9, weight='bold', ha='left', va='center')

    # 2. STRUCTURAL GEOMETRY
    slab_y, slab_h = 2.0, 0.6
    col_w, col_h = 1.0, 2.2
    beam_d = 1.3
    col_style = {'facecolor': '#546e7a', 'edgecolor': 'black', 'zorder': 5}
    slab_style = {'facecolor': concrete_color, 'edgecolor': '#333', 'linewidth': 1.5}

    # Draw Columns
    ax.add_patch(patches.Rectangle((-col_w/2, slab_y-col_h), col_w, col_h, **col_style))
    ax.add_patch(patches.Rectangle((10-col_w/2, slab_y-col_h), col_w, col_h, **col_style))

    # 3. SPAN SPECIFIC DRAWING
    if "Interior" in span_type:
        ax.add_patch(patches.Rectangle((-2.5, slab_y), 15, slab_h, **slab_style))
        ax.text(-2.0, slab_y+slab_h/2, "≈", fontsize=24, rotation=90, va='center')
        ax.text(12.0, slab_y+slab_h/2, "≈", fontsize=24, rotation=90, va='center')
        
        draw_data_column(0, 0.65, True, 'neg')
        draw_data_column(5, 0.35, True, 'pos')
        draw_data_column(10, 0.65, True, 'neg')
        
        ax.text(5, 7.8, "INTERIOR SPAN DISTRIBUTION", ha='center', fontsize=12, weight='bold')

    elif "Edge Beam" in span_type:
        ax.add_patch(patches.Rectangle((-col_w/2, slab_y), 13, slab_h, **slab_style))
        ax.add_patch(patches.Rectangle((-col_w/2, slab_y-beam_d), col_w*1.5, beam_d, **slab_style)) # Beam
        ax.text(12.0, slab_y+slab_h/2, "≈", fontsize=24, rotation=90, va='center')

        draw_data_column(0, 0.30, False, 'neg')
        draw_data_column(5, 0.50, False, 'pos')
        draw_data_column(10, 0.70, False, 'neg')
        
        ax.text(5, 7.8, "END SPAN - EDGE BEAM DISTRIBUTION", ha='center', fontsize=12, weight='bold')
        ax.annotate('Stiff Edge Beam', xy=(0.8, slab_y-beam_d/2), xytext=(3, 0),
                    arrowprops=dict(arrowstyle="->", color='#d32f2f'), color='#d32f2f', weight='bold')

    elif "No Beam" in span_type:
        ax.add_patch(patches.Rectangle((-col_w/2, slab_y), 13, slab_h, **slab_style))
        ax.add_patch(patches.Rectangle((-col_w/2, slab_y-beam_d), col_w, beam_d, fc='none', ec='#d32f2f', ls='--'))
        ax.text(12.0, slab_y+slab_h/2, "≈", fontsize=24, rotation=90, va='center')

        draw_data_column(0, 0.26, True, 'neg')
        draw_data_column(5, 0.52, True, 'pos')
        draw_data_column(10, 0.70, True, 'neg')
        
        ax.text(5, 7.8, "END SPAN - FLAT PLATE DISTRIBUTION", ha='center', fontsize=12, weight='bold')
        ax.annotate('No Beam (Flexible)', xy=(0.5, slab_y), xytext=(3, 0.5),
                    arrowprops=dict(arrowstyle="->", color='#d32f2f'), color='#d32f2f', weight='bold')

    # --- Footer ---
    ax.annotate('', xy=(0, -0.5), xytext=(10, -0.5), arrowprops=dict(arrowstyle='<->', linewidth=1.2))
    ax.text(5, -0.8, "Clear Span ($L_n$)", ha='center', fontsize=10, fontstyle='italic')
    ax.text(0, -1.2, "Ext. Support", ha='center', fontsize=9)
    ax.text(10, -1.2, "Int. Support", ha='center', fontsize=9)

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
