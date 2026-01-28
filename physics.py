import math

CONCRETE_DENSITY = 2400 # kg/m3

def get_units():
    return {
        'ksc_to_mpa': 0.0980665,
        'grav': 9.80665
    }

def get_bar_properties(db_mm):
    # Standard DB areas (cm2)
    # Area = pi * (d/2)^2 / 100
    r_cm = (db_mm / 10.0) / 2.0
    area = math.pi * (r_cm**2)
    return area

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
    elif pos == "Edge":
        bo = (2 * (c1 + d/2)) + (c2 + d)
        acrit = (c1 + d/2) * (c2 + d)
        alpha = 30
    else: # Corner
        bo = (c1 + d/2) + (c2 + d/2)
        acrit = (c1 + d/2) * (c2 + d/2)
        alpha = 20
        
    beta = max(c1, c2) / min(c1, c2)
    return bo, acrit, alpha, beta

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
