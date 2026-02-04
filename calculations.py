# calculations.py
import numpy as np
import math

# ==========================================
# 1. PUNCHING SHEAR (ADVANCED WITH MOMENT TRANSFER)
# ==========================================
def calculate_section_properties(c1, c2, d, col_type):
    """
    Helper to calculate Ac, Jc, and gamma_v for Moment Transfer.
    Geometry is based on ACI 318 Critical Section at d/2 from face.
    """
    # Critical section dimensions
    b1 = c1 + d  # Width parallel to moment (c1 direction)
    b2 = c2 + d  # Width perpendicular to moment (c2 direction)

    # Adjust based on column type (Approximate geometry)
    if col_type == "edge":
        # Assume Edge parallel to moment (3 sides)
        b2 = c2 + d/2.0
    elif col_type == "corner":
        # Corner (2 sides)
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
    # Using Standard Interior Formula (Box Section)
    # Note: For strict edge/corner, the centroid shifts, making Jc complex.
    # We use the interior formula as a conservative baseline for this tool scope.
    Jc = (d * b1**3)/6 + (d**3 * b1)/6 + (d * b2 * b1**2)/2

    # 3. Fraction of Moment Transferred by Shear (gamma_v)
    # gamma_f = 1 / (1 + (2/3)*sqrt(b1/b2))
    gamma_f = 1 / (1 + (2/3) * np.sqrt(b1/b2))
    gamma_v = 1 - gamma_f
    
    # Distance from centroid to edge (c_AB)
    # Assuming symmetry for c_AB is roughly b1/2
    c_AB = b1 / 2.0

    return Ac, Jc, gamma_v, c_AB, bo

def check_punching_shear(Vu, fc, c1, c2, d, col_type="interior", Munbal=0.0):
    """
    Check punching shear considering Direct Shear (Vu) + Unbalanced Moment (Munbal).
    Returns a dictionary with Stress-Based results but compatible with Legacy UI.
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
    
    # Stress from Gravity Load
    stress_direct = Vu / Ac
    
    # Stress from Unbalanced Moment
    stress_moment = (gamma_v * abs(Munbal_cm) * c_AB) / Jc
    
    # Total Stress
    vu_max = stress_direct + stress_moment # ksc (kg/cm^2)

    # 3. Allowable Shear Stress (phi_vc)
    phi = 0.85 
    sqrt_fc = np.sqrt(fc)
    
    # Vc calculation (Stress units - kg/cm^2)
    # 3.1 Basic
    vc_stress_nominal = 1.06 * sqrt_fc 
    
    # 3.2 Rectangularity effect (beta)
    beta = max(c1, c2) / min(c1, c2)
    vc_beta = 0.27 * (2 + 4/beta) * sqrt_fc
    
    # 3.3 Size effect (alpha_s)
    if col_type == "interior": alpha_s = 40
    elif col_type == "edge": alpha_s = 30
    else: alpha_s = 20
    vc_size = 0.27 * ((alpha_s * d / bo) + 2) * sqrt_fc

    # Governing Vc
    vc_final_stress = min(vc_stress_nominal, vc_beta, vc_size)
    phi_vc_stress = phi * vc_final_stress

    # 4. Check Ratio
    if phi_vc_stress > 0:
        ratio = vu_max / phi_vc_stress
    else:
        ratio = 999.0
        
    status = "OK" if ratio <= 1.0 else "FAIL"

    # 5. Return (With Legacy Keys for UI Compatibility)
    return {
        "Vu": Vu,
        "Munbal": Munbal,
        "d": d,
        "d_avg": d,
        
        # Geometry
        "bo": bo,          # New key
        "b0": bo,          # !!! COMPATIBILITY FIX: Alias for legacy tab_calc.py !!!
        "Ac": Ac,
        "beta": beta,      
        "alpha_s": alpha_s, 
        
        # Analysis
        "gamma_v": gamma_v,
        "Jc": Jc,
        "stress_actual": vu_max,       # v_u (combined)
        "stress_allow": phi_vc_stress, # phi*v_c
        
        # Force Equivalents (For Legacy UI Display)
        "phi_Vc": phi_vc_stress * Ac, # Equivalent Capacity Force
        "Vc_nominal": vc_final_stress * Ac, 
        
        # Result
        "ratio": ratio,
        "status": status,
        "note": f"Incl. Moment: {Munbal:,.0f} kg-m",
        "check_type": "stress" # Flag to tell UI this is stress-based
    }

# ==========================================
# 2. DUAL CASE PUNCHING (DROP PANEL)
# ==========================================
def check_punching_dual_case(w_u, Lx, Ly, fc, c1, c2, d_drop, d_slab, drop_w, drop_l, col_type, Munbal=0.0):
    """
    Checks two critical sections:
    1. Inside Drop Panel (using d_drop)
    2. Outside Drop Panel (using d_slab)
    """
    # Case 1: Inner (Drop Depth)
    # Load inside critical section is neglected approx. factor 0.95
    Vu1 = w_u * (Lx * Ly) * 0.95 
    res1 = check_punching_shear(Vu1, fc, c1, c2, d_drop, col_type, Munbal)
    res1["case"] = "Inside Drop (d_drop)" 
    
    # Case 2: Outer (Slab Depth)
    # Critical section is around the Drop Panel
    # Moment transfer decays at outer section, assume 50% effective or full for conservative
    Vu2 = w_u * (Lx * Ly) * 0.90 
    # Use drop_w, drop_l as the "column" dimensions for the outer check
    res2 = check_punching_shear(Vu2, fc, drop_w, drop_l, d_slab, col_type, Munbal * 0.5)
    res2["case"] = "Outside Drop (d_slab)" 
    
    # Return the governing (worst) case
    if res1['ratio'] > res2['ratio']:
        res1['is_dual'] = True
        res1['other_case'] = res2 # Store other case for detail viewing
        return res1
    else:
        res2['is_dual'] = True
        res2['other_case'] = res1
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
    Ie = 0.4 * Ig # Avg constant for cracked flat plate (Simplified ACI)
    
    # Deflection Formula (Continuous Beam Approx coeff ~1/200 range)
    # Using coefficient 5/384 * 0.5 (Continuity Factor)
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

    # Critical section at d from support face
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
