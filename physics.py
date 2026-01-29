import math

CONCRETE_DENSITY = 2400 # kg/m3

def get_units():
    return {
        'ksc_to_mpa': 0.0980665,
        'grav': 9.80665
    }

# Rebar Database
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

# --- EFM Stiffness Modules ---

def get_inertia_gross(b_m, h_m):
    """Calculates Gross Moment of Inertia (m4)"""
    return (b_m * (h_m**3)) / 12.0

def get_torsional_constant_c(x, y):
    """
    Calculates Torsional Constant C per ACI (x < y)
    C = Sum [ (1 - 0.63(x/y)) * (x^3 * y) / 3 ]
    """
    term1 = 1 - 0.63 * (x / y)
    term2 = (x**3 * y) / 3.0
    return term1 * term2

def get_torsional_stiffness_kt(E, C, l2, c2):
    """
    Calculates Kt (Torsional Stiffness)
    Kt = (9 * E * C) / (l2 * (1 - c2/l2)^3)
    """
    denom = l2 * ((1 - (c2/l2))**3)
    if denom == 0: return 999999999 # Rigid if c2 approx l2
    return (9 * E * C) / denom

def get_equivalent_column_stiffness(sum_kc, kt):
    """
    Calculates Kec (Equivalent Column Stiffness)
    1/Kec = 1/Sum_Kc + 1/Kt
    """
    if sum_kc == 0: return 0
    if kt == 0: return 0 # Pinned
    
    inv_kec = (1/sum_kc) + (1/kt)
    return 1 / inv_kec

def get_moment_distribution(continuity, strip_type):
    """DDM Coefficients (Legacy Support)"""
    if continuity == "End Span (Integral w/ Beam)":
        dist_factors = (0.16, 0.57, 0.70)
    elif continuity == "End Span (Slab Only)":
        dist_factors = (0.26, 0.52, 0.70)
    else: 
        dist_factors = (0.65, 0.35, 0.65)
    
    neg_factor, pos_factor, _ = dist_factors
    
    if strip_type == "Column Strip":
        return neg_factor * 0.75, pos_factor * 0.60
    else:
        return neg_factor * 0.25, pos_factor * 0.40

def get_min_thickness_limit(ln, pos):
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
    else: 
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
    if pos == "Interior": return 1.0
    if pos == "Edge": return 1.10
    if pos == "Corner": return 1.20
    return 1.0
