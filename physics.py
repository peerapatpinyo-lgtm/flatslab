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

def get_moment_distribution(continuity, strip_type):
    """
    Returns coefficients [Neg_Ext, Pos, Neg_Int] based on continuity.
    Simplified ACI Direct Design Method coefficients.
    """
    # 1. Total Static Moment Distribution (Neg Ext, Pos, Neg Int)
    if continuity == "End Span (Integral w/ Beam)":
        # Case: Slab with beams between all supports
        dist_factors = (0.16, 0.57, 0.70)
    elif continuity == "End Span (Slab Only)":
        # Case: Flat Plate without edge beam
        dist_factors = (0.26, 0.52, 0.70)
    else: 
        # Interior Span (Default)
        dist_factors = (0.65, 0.35, 0.65) # Symetric Neg
    
    # 2. Lateral Distribution (Col Strip vs Middle Strip)
    # This is a simplification. Real ACI depends on alpha1 * l2 / l1
    # Assuming alpha = 0 (Flat Plate)
    
    neg_factor, pos_factor, _ = dist_factors
    
    if strip_type == "Column Strip":
        # CS takes ~75% of Neg, ~60% of Pos
        return neg_factor * 0.75, pos_factor * 0.60
    else:
        # MS takes ~25% of Neg, ~40% of Pos
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
    if pos == "Interior": return 1.0
    if pos == "Edge": return 1.10
    if pos == "Corner": return 1.20
    return 1.0
