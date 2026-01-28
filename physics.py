import numpy as np

# --- Constants & Unit Conversions (Zero Hard-coding) ---
GRAVITY = 9.80665  # m/s^2
KSC_TO_MPA = 0.0980665
KG_FORCE_TO_NEWTON = GRAVITY
CONCRETE_DENSITY = 2400.0 # kg/m^3

def get_units():
    return {
        "grav": GRAVITY,
        "ksc_mpa": KSC_TO_MPA,
        "kg_n": KG_FORCE_TO_NEWTON
    }

def get_unbalanced_factor(pos):
    """Estimate Gamma_v based on position"""
    mapping = {"Interior": 1.0, "Edge": 1.15, "Corner": 1.20}
    return mapping.get(pos, 1.0)

def get_geometry_properties(c1, c2, d, pos):
    """
    Calculate critical section properties.
    All inputs in METERS.
    Returns: bo (m), acrit (m^2), alpha_s, beta
    """
    if pos == "Interior":
        bo = 2 * ((c1 + d) + (c2 + d))
        acrit = (c1 + d) * (c2 + d)
        alpha_s = 40
        beta = max(c1, c2) / min(c1, c2)
    elif pos == "Edge":
        # Assumes c1 is the side perpendicular to the edge
        bo = (2 * (c1 + d/2)) + (c2 + d)
        acrit = (c1 + d/2) * (c2 + d)
        alpha_s = 30
        beta = max(c1, c2) / min(c1, c2)
    else: # Corner
        bo = (c1 + d/2) + (c2 + d/2)
        acrit = (c1 + d/2) * (c2 + d/2)
        alpha_s = 20
        beta = 1.0
        
    return bo, acrit, alpha_s, beta

def calc_aci_shear_capacity(fc_mpa, beta, alpha_s, d, bo):
    """Calculate 3 ACI equations. Inputs: d, bo in METERS."""
    # Convert d, bo to mm for the formula constants, or adjust constants.
    # Standard ACI Metric: sqrt(fc) in MPa.
    # To act on safe side and clear units:
    # Eq 1: 0.33 * sqrt(fc)
    v1 = 0.33 * np.sqrt(fc_mpa)
    
    # Eq 2: 0.17 * (1 + 2/beta) * sqrt(fc)
    v2 = 0.17 * (1 + 2/beta) * np.sqrt(fc_mpa)
    
    # Eq 3: 0.083 * (2 + alpha * d / bo) * sqrt(fc)
    # d/bo is unitless ratio
    v3 = 0.083 * (2 + (alpha_s * d / bo)) * np.sqrt(fc_mpa)
    
    vc_mpa = min(v1, v2, v3)
    return v1, v2, v3, vc_mpa

def get_min_thickness(ln_m, pos):
    # ln in meters
    denom = 33.0 if pos == "Interior" else 30.0
    return (ln_m * 1000) / denom
