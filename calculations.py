# calculations.py
import numpy as np
import math

# ==========================================
# 1. PUNCHING SHEAR (ADVANCED WITH MOMENT TRANSFER)
# ==========================================
def calculate_section_properties(c1, c2, d, col_type):
    """
    Helper to calculate Ac, Jc, and gamma_v for Moment Transfer.
    """
    # Critical section dimensions
    b1 = c1 + d  # Width parallel to moment
    b2 = c2 + d  # Width perpendicular to moment (Interior)

    # Adjust based on column type (Approximate for rectangular sections)
    if col_type == "edge":
        b2 = c2 + d/2.0
    elif col_type == "corner":
        b1 = c1 + d/2.0
        b2 = c2 + d/2.0

    # 1. Perimeter (bo) & Area (Ac)
    if col_type == "interior":
        bo = 2*(b1 + b2)
    elif col_type == "edge":
        bo = 2*b1 + b2
    else: # corner
        bo = b1 + b2
    
    Ac = bo * d

    # 2. Polar Moment of Inertia (Jc)
    # Using Standard Interior Formula for robustness in this scope
    Jc = (d * b1**3)/6 + (d**3 * b1)/6 + (d * b2 * b1**2)/2

    # 3. Fraction of Moment Transferred by Shear (gamma_v)
    gamma_f = 1 / (1 + (2/3) * np.sqrt(b1/b2))
    gamma_v = 1 - gamma_f
    
    # Distance from centroid to edge (c_AB)
    c_AB = b1 / 2.0

    return Ac, Jc, gamma_v, c_AB, bo

def check_punching_shear(Vu, fc, c1, c2, d, col_type="interior", Munbal=0.0):
    """
    Check punching shear considering Direct Shear (Vu) + Unbalanced Moment (Munbal).
    """
    try:
        Vu = float(Vu); fc = float(fc); c1 = float(c1); c2 = float(c2); d = float(d); Munbal = float(Munbal)
    except ValueError:
        return {"status": "ERROR", "ratio": 999, "Note": "Invalid Input"}

    # 1. Get Section Properties
    Ac, Jc, gamma_v, c_AB, bo = calculate_section_properties(c1, c2, d, col_type)

    # 2. Determine Shear Stress (vu_max)
    # Convert Munbal from kg-m to kg-cm
    Munbal_cm = Munbal * 100.0
    
    stress_direct = Vu / Ac
    stress_moment = (gamma_v * Munbal_cm * c_AB) / Jc
    
    vu_max = stress_direct + stress_moment # ksc (kg/cm^2)

    # 3. Allowable Shear Stress (phi_vc)
    phi = 0.85 
    sqrt_fc = np.sqrt(fc)
    
    # Vc calculation (Stress units)
    vc_stress_nominal = 1.06 * sqrt_fc 
    
    # Refine Vc based on rectangularity (beta)
    beta = max(c1, c2) / min(c1, c2)
    vc_beta = 0.27 * (2 + 4/beta) * sqrt_fc
    
    # Vc based on size effect (alpha_s)
    if col_type == "interior": alpha_s = 40
    elif col_type == "edge": alpha_s = 30
    else: alpha_s = 20
    vc_size = 0.27 * ((alpha_s * d / bo) + 2) * sqrt_fc

    vc_final_stress = min(vc_stress_nominal, vc_beta, vc_size)
    phi_vc_stress = phi * vc_final_stress

    # 4. Check
    if phi_vc_stress > 0:
        ratio = vu_max / phi_vc_stress
    else:
        ratio = 999.0
        
    status = "OK" if ratio <= 1.0 else "FAIL"

    # 5. Return with Compatibility Keys (b0, phi_Vc) for tab_calc.py
    return {
        "Vu": Vu,
        "Munbal": Munbal,
        "d": d,
        "d_avg": d,
        "bo": bo,          # New key
        "b0": bo,          # !!! CRITICAL FIX: Alias for legacy tab_calc.py !!!
        "Ac": Ac,
        "beta": beta,      # Added for legacy support
        "alpha_s": alpha_s, # Added for legacy support
        "gamma_v": gamma_v,
        "stress_actual": vu_max,
        "stress_allow": phi_vc_stress,
        "phi_Vc": phi_vc_stress * Ac, # Approx Force Capacity for legacy display
        "Vc_nominal": vc_final_stress * Ac, # Approx Nominal Force
        "ratio": ratio,
        "status": status,
        "note": f"Incl. Moment: {Munbal:,.0f} kg-m",
        "check_type": "stress" # Flag to tell UI this is stress-based
    }

# ==========================================
# 2. DUAL CASE PUNCHING (DROP PANEL)
# ==========================================
def check_punching_dual_case(w_u, Lx, Ly, fc, c1, c2, d_drop, d_slab, drop_w, drop_l, col_type, Munbal=0.0):
    # Case 1: Inner (Drop Depth)
    # Load inside critical section is neglected, but simplified to full area for safety or use (Lx*Ly - Ac)
    # Conservative approximation:
    Vu1 = w_u * (Lx * Ly) * 0.95 
    res1 = check_punching_shear(Vu1, fc, c1, c2, d_drop, col_type, Munbal)
    res1["case"] = "Inside Drop (d_drop)" # Label for UI
    
    # Case 2: Outer (Slab Depth)
    # Moment transfers less to the outer perimeter, assume Munbal decays or is taken by Drop.
    Vu2 = w_u * (Lx * Ly) * 0.90 
    res2 = check_punching_shear(Vu2, fc, drop_w, drop_l, d_slab, col_type, Munbal * 0.5)
    res2["case"] = "Outside Drop (d_slab)" # Label for UI
    
    # Return the worst case
    if res1['ratio'] > res2['ratio']:
        res1['is_dual'] = True
        return res1
    else:
        res2['is_dual'] = True
        return res2

# ==========================================
# 3. REINFORCEMENT & SERVICEABILITY CHECKS
# ==========================================
def check_min_reinforcement(h_slab, b_width=100.0, fy=4000.0):
    """
    Calculate Minimum Temperature & Shrinkage Reinforcement (ACI 318).
    rho_min = 0.0018 for Deformed bars (fy=4000 ksc / Grade 60)
    """
    rho_min = 0.0018
    As_min = rho_min * b_width * h_slab # cm^2 per meter strip (if b=100)
    
    return {
        "rho_min": rho_min,
        "As_min": As_min, # cm2
        "note": "Based on ACI 318 Temp/Shrinkage (0.0018)"
    }

def check_long_term_deflection(w_service, L, h, fc, As_provided, b=100.0):
    """
    Estimate Long-Term Deflection including Creep & Shrinkage.
    """
    # 1. Material Properties
    Ec = 15100 * np.sqrt(fc) # ksc
    
    # 2. Immediate Deflection (Elastic)
    L_cm = L * 100.0
    w_line_kg_cm = (w_service * (b/100.0)) / 100.0 # kg/cm per strip
    
    Ig = b * (h**3) / 12.0
    
    # Effective Moment of Inertia (Ie) - Cracked Section approximation
    Ie = 0.4 * Ig # Avg constant for cracked flat plate
    
    # Deflection Formula (Continuous Beam Approx coeff ~1/200 range)
    # Using coefficient 5/384 * 0.5 (Continuity)
    Delta_immediate = (5 * w_line_kg_cm * (L_cm**4)) / (384 * Ec * Ie) * 0.5 
    
    # 3. Long Term Multiplier (Lambda)
    Lambda_LT = 2.0
    
    Delta_LT = Delta_immediate * Lambda_LT
    Delta_Total = Delta_immediate + Delta_LT
    
    # 4. Allowable
    Limit_240 = L_cm / 240.0
    
    status = "PASS" if Delta_Total <= Limit_240 else "FAIL"
    
    return {
        "Delta_Immediate": Delta_immediate,
        "Delta_LongTerm": Delta_LT,
        "Delta_Total": Delta_Total,
        "Limit_240": Limit_240,
        "status": status,
        "I_effective": Ie
    }

# ==========================================
# 4. EFM STIFFNESS
# ==========================================
def calculate_stiffness(c1, c2, L1, L2, lc, h_slab, fc):
    # Ensure floats
    c1=float(c1); c2=float(c2); L1=float(L1); L2=float(L2); lc=float(lc); h_slab=float(h_slab); fc=float(fc)

    E_c = 15100 * np.sqrt(fc) # ksc
    
    # 1. Column Stiffness (Kc)
    Ic = c2 * (c1**3) / 12.0 
    lc_cm = lc * 100.0
    Kc = 4 * E_c * Ic / lc_cm
    Sum_Kc = 2 * Kc
    
    # 2. Slab Stiffness (Ks)
    Is = (L2*100.0) * (h_slab**3) / 12.0
    L1_cm = L1 * 100.0
    Ks = 4 * E_c * Is / L1_cm
    
    # 3. Torsional Stiffness (Kt)
    x = h_slab
    y = c1 
    C = (1 - 0.63 * x / y) * (x**3 * y) / 3.0
    
    term = (1 - c2/(L2*100.0))
    if term <= 0: term = 0.01
    denom = (L2*100.0 * term**3)
    
    if denom > 0:
        Kt = 9 * E_c * C / denom
    else:
        Kt = 0
    
    # 4. Equivalent Column Stiffness (Kec)
    if Kt > 0 and Sum_Kc > 0:
        Kec = 1 / (1/Sum_Kc + 1/Kt)
    else:
        Kec = 0
        
    return Ks, Sum_Kc, Kt, Kec

# ==========================================
# 5. ONE-WAY SHEAR
# ==========================================
def check_oneway_shear(w_u, L_span, L_width, c_support, d_eff, fc):
    w_u = float(w_u); L_span = float(L_span); c_support = float(c_support); d_eff = float(d_eff); fc = float(fc)

    x_crit = (L_span / 2.0) - (c_support / 100.0 / 2.0) - (d_eff / 100.0)
    if x_crit < 0: x_crit = 0
    
    Vu_oneway = w_u * x_crit * L_width 
    
    phi = 0.85 
    Vc_stress = 0.53 * np.sqrt(fc) # ksc
    bw = L_width * 100.0 # Width in cm
    Vc = Vc_stress * bw * d_eff 
    phi_Vc = phi * Vc
    
    if phi_Vc > 0:
        ratio = Vu_oneway / phi_Vc
    else:
        ratio = 999.0
        
    status = "PASS" if ratio <= 1.0 else "FAIL"
    
    return {
        "Vu": Vu_oneway,
        "phi_Vc": phi_Vc,
        "ratio": ratio,
        "status": status,
        "x_crit": x_crit
    }
