import math

CONCRETE_DENSITY = 2400 # kg/m3

def get_units():
    return {
        'ksc_to_mpa': 0.0980665,
        'grav': 9.80665
    }

# Rebar Database (Standard Thai Sizes)
DB_PROPERTIES = {
    10: 0.785,
    12: 1.131,
    16: 2.011,
    20: 3.142,
    25: 4.909,
    28: 6.158,
    32: 8.042
}

def get_bar_area(db_mm):
    return DB_PROPERTIES.get(int(db_mm), math.pi * ((db_mm/10/2)**2))

# --- EFM Stiffness Modules (Advanced) ---

def get_inertia_gross(b_m, h_m, use_cracked=False, member_type="slab"):
    """
    Calculates Moment of Inertia (m4).
    Applies ACI 318 modifiers for cracked sections if enabled.
    """
    Ig = (b_m * (h_m**3)) / 12.0
    
    if use_cracked:
        # ACI 318-19 Table 6.6.3.1.1(a)
        if member_type == "slab":
            return 0.25 * Ig
        elif member_type == "column":
            return 0.70 * Ig
        elif member_type == "beam":
            return 0.35 * Ig
            
    return Ig

def get_torsional_constant_c_complex(x1, y1, x2=0, y2=0):
    """
    Calculates Torsional Constant C per ACI (Summation of Rectangles).
    Supports Slab + Beam (L-shape or T-shape approximations).
    Formula: Sum [ (1 - 0.63(x/y)) * (x^3 * y) / 3 ] where x < y
    """
    def calc_single_rect(w, h):
        if w == 0 or h == 0: return 0
        x, y = sorted([w, h]) # Ensure x is smaller
        return (1 - 0.63 * (x / y)) * (x**3 * y) / 3.0

    c_total = calc_single_rect(x1, y1)
    if x2 > 0 and y2 > 0:
        c_total += calc_single_rect(x2, y2)
        
    return c_total

def get_torsional_stiffness_kt(E, C, l2, c2, edge_beam_exists=False):
    """
    Calculates Kt (Torsional Stiffness).
    Kt = (9 * E * C) / (l2 * (1 - c2/l2)^3)
    """
    try:
        denom = l2 * ((1 - (c2/l2))**3)
        if denom <= 0.0001: return 9.9e9 # Rigid approximation
        return (9 * E * C) / denom
    except ZeroDivisionError:
        return 9.9e9

def get_equivalent_column_stiffness(sum_kc, kt):
    """
    Calculates Kec (Equivalent Column Stiffness)
    1/Kec = 1/Sum_Kc + 1/Kt
    """
    if sum_kc == 0: return 0
    if kt == 0: return 0 # Pinned
    
    try:
        inv_kec = (1/sum_kc) + (1/kt)
        return 1 / inv_kec
    except ZeroDivisionError:
        return 0

# --- Shear & Design Logic ---

def get_moment_distribution_coeffs(continuity, strip_type):
    """
    DDM Coefficients (Legacy Support / Fallback).
    Returns (Negative Coeff, Positive Coeff)
    """
    # ACI 318 Direct Design Method Coefficients
    if continuity == "End Span (Integral w/ Beam)":
        dist_factors = (0.16, 0.57, 0.70) # Neg Ext, Pos, Neg Int
    elif continuity == "End Span (Slab Only)":
        dist_factors = (0.26, 0.52, 0.70)
    else: 
        dist_factors = (0.65, 0.35, 0.65) # Neg, Pos, Neg
    
    # Mapping to Strip Logic
    if strip_type == "Column Strip":
        # CS takes 75% of Neg, 60% of Pos
        neg_int = dist_factors[2] * 0.75
        pos = dist_factors[1] * 0.60
        return neg_int, pos
    else:
        # MS takes 25% of Neg, 40% of Pos
        neg_int = dist_factors[2] * 0.25
        pos = dist_factors[1] * 0.40
        return neg_int, pos

def get_min_thickness_limit(ln, pos):
    """ACI 318 Table 8.3.1.1"""
    denom = 33.0 if pos == "Interior" else 30.0
    return (ln * 1000) / denom, denom

def get_geometry(c1, c2, d, pos):
    c1_d = c1 + d
    c2_d = c2 + d
    
    if pos == "Interior":
        bo = 2 * (c1_d + c2_d)
        acrit = c1_d * c2_d
        alpha = 40
        bo_str = "2(c_1+d + c_2+d)"
    elif pos == "Edge":
        bo = (2 * (c1 + d/2)) + (c2 + d)
        acrit = (c1 + d/2) * (c2 + d)
        alpha = 30
        bo_str = "2(c_1+d/2) + (c_2+d)"
    else: # Corner
        bo = (c1 + d/2) + (c2 + d/2)
        acrit = (c1 + d/2) * (c2 + d/2)
        alpha = 20
        bo_str = "(c_1+d/2) + (c_2+d/2)"
        
    beta = max(c1, c2) / min(c1, c2)
    return bo, acrit, alpha, beta, bo_str

def get_vc_stress(fc_mpa, beta, alpha, d, bo):
    root_fc = math.sqrt(fc_mpa)
    v1 = 0.33 * root_fc
    v2 = 0.17 * (1 + (2.0/beta)) * root_fc
    v3 = 0.083 * (2 + (alpha * d / bo)) * root_fc
    return v1, v2, v3

def get_gamma_v(pos):
    """Unbalanced Moment Transfer Fraction (Simplified)"""
    if pos == "Interior": return 1.0
    if pos == "Edge": return 1.10
    if pos == "Corner": return 1.20 # Increased risk
    return 1.0
