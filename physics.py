import math

CONCRETE_DENSITY = 2400 # kg/m3

def get_units():
    return {
        'ksc_mpa': 0.0980665, # 1 ksc = 0.098 MPa
        'grav': 9.80665       # g
    }

def get_min_thickness(ln_m, pos):
    # ACI 318 Table for Flat Plate (fy 2800-4200 approx)
    # This is simplified. Normally depends on fy.
    # Assuming fy=4000 (Grade 40) -> ln/33 (Int), ln/30 (Ext)
    if pos == "Interior":
        return (ln_m * 1000) / 33.0
    else:
        return (ln_m * 1000) / 30.0

def get_geometry_properties(c1, c2, d, pos):
    # c1, c2, d are in meters
    # Returns: bo (m), acrit (m2), alpha, beta
    
    # Critical Section Properties
    c1_d = c1 + d
    c2_d = c2 + d
    
    if pos == "Interior":
        bo = 2 * (c1_d + c2_d)
        acrit = c1_d * c2_d
        alpha = 40
    elif pos == "Edge":
        # Assume Edge parallel to c2
        bo = (2 * c1_d) + c2_d 
        # Correct ACI bo for edge is 2(c1 + d/2) + (c2 + d)
        # Let's use refined standard:
        bo = (2 * (c1 + d/2)) + (c2 + d)
        acrit = (c1 + d/2) * (c2 + d)
        alpha = 30
    else: # Corner
        bo = (c1 + d/2) + (c2 + d/2)
        acrit = (c1 + d/2) * (c2 + d/2)
        alpha = 20
        
    beta = max(c1, c2) / min(c1, c2)
    return bo, acrit, alpha, beta

def calc_aci_shear_capacity(fc_mpa, beta, alpha, d, bo):
    # Returns v1, v2, v3, vc_min (MPa)
    root_fc = math.sqrt(fc_mpa)
    
    v1 = 0.33 * root_fc
    v2 = 0.17 * (1 + (2.0/beta)) * root_fc
    v3 = 0.083 * (2 + (alpha * d / bo)) * root_fc
    
    vc = min(v1, v2, v3)
    return v1, v2, v3, vc

def get_unbalanced_factor(pos):
    # Simplified Gamma_v
    if pos == "Interior": return 1.0
    if pos == "Edge": return 1.10 # Approximation
    if pos == "Corner": return 1.20 # Approximation
    return 1.0
