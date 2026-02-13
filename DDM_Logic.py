import numpy as np
from typing import Dict, Any

# ========================================================
# ENGINEERING LOGIC (ACI 318 / EIT)
# ========================================================

def get_beta1(fc: float) -> float:
    """Calculate Beta1 factor based on fc"""
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
    """Perform Flexural Design with detailed intermediate steps."""
    # Units: kg, cm
    b_cm = b_width * 100.0
    h_cm = float(h_slab)
    Mu_kgcm = M_u * 100.0
    
    d_offset = 0.0 if is_main_dir else (d_bar / 10.0)
    d_eff = h_cm - cover - (d_bar / 20.0) - d_offset
    
    if d_eff <= 0:
        return {"Status": False, "Note": "Depth Error (d<=0)", "d": 0, "As_req": 0}

    beta1 = get_beta1(fc)

    try:
        Rn = Mu_kgcm / (phi_factor * b_cm * (d_eff**2))
    except ZeroDivisionError:
        Rn = 0

    term_inside = 1 - (2 * Rn) / (0.85 * fc)
    
    rho_calc = 0.0
    if term_inside < 0:
        rho_req = 999.0 # Fail
    else:
        if M_u < 100: 
            rho_req = 0.0
        else:
            rho_req = (0.85 * fc / fy) * (1 - np.sqrt(term_inside))
            rho_calc = rho_req

    As_flex = rho_req * b_cm * d_eff
    As_min = 0.0018 * b_cm * h_cm 
    As_req_final = max(As_flex, As_min) if rho_req != 999 else 999.0
    
    Ab_area = np.pi * (d_bar / 10.0)**2 / 4.0
    As_prov = (b_cm / s_bar) * Ab_area
    
    if rho_req == 999:
        PhiMn = 0; a_depth = 0; dc_ratio = 999.0
    else:
        a_depth = (As_prov * fy) / (0.85 * fc * b_cm)
        Mn = As_prov * fy * (d_eff - a_depth / 2.0)
        PhiMn = phi_factor * Mn / 100.0 
        
        if M_u < 50: 
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
    """Simplified Serviceability Check."""
    denom = 30.0 
    if "Interior" in span_type: denom = 33.0
    elif "Edge" in span_type: denom = 30.0
    
    h_min = (L_span * 100) / denom
    k_cont = 0.6 if "Interior" in span_type else 0.8
    
    Ec = 15100 * np.sqrt(fc)
    b_design = 100.0
    Ig = (b_design * h_slab**3) / 12.0
    
    w_service = w_u / 1.45
    w_line = (w_service * 1.0) / 100.0
    L_cm = L_span * 100.0
    
    delta_imm = k_cont * (5 * w_line * L_cm**4) / (384 * Ec * Ig)
    lambda_long = 2.0
    delta_total = delta_imm * (1 + lambda_long)
    limit = L_cm / 240.0
    
    return {
        "h_min": h_min, "status_h": h_slab >= h_min,
        "delta_imm": delta_imm, "delta_total": delta_total,
        "limit": limit, "denom": denom
    }

def get_ddm_coeffs(span_type: str) -> Dict[str, float]:
    """Returns ACI 318 Moment Coefficients."""
    if "Interior" in span_type:
        return {'neg': 0.65, 'pos': 0.35, 'ext_neg': 0.0, 'desc': 'Interior Span'}
    elif "Edge Beam" in span_type:
        return {'neg': 0.70, 'pos': 0.50, 'ext_neg': 0.30, 'desc': 'End Span (Stiff Beam)'}
    elif "No Beam" in span_type:
        return {'neg': 0.70, 'pos': 0.52, 'ext_neg': 0.26, 'desc': 'End Span (Flat Plate)'}
    return {'neg': 0.65, 'pos': 0.35, 'ext_neg': 0.0, 'desc': 'Default'}

def update_moments_based_on_config(data_obj: Dict, span_type: str) -> Dict:
    Mo = data_obj['Mo']
    coeffs = get_ddm_coeffs(span_type)
    
    M_neg_total = coeffs['neg'] * Mo
    M_pos_total = coeffs['pos'] * Mo
    M_ext_neg_total = coeffs['ext_neg'] * Mo

    M_cs_neg = 0.75 * M_neg_total
    M_ms_neg = 0.25 * M_neg_total
    M_cs_pos = 0.60 * M_pos_total
    M_ms_pos = 0.40 * M_pos_total
    
    data_obj['M_vals'] = {
        'M_cs_neg': M_cs_neg, 'M_ms_neg': M_ms_neg,
        'M_cs_pos': M_cs_pos, 'M_ms_pos': M_ms_pos,
        'M_unbal': M_ext_neg_total
    }
    data_obj['coeffs_desc'] = coeffs['desc'] 
    data_obj['span_type_str'] = span_type
    return data_obj
