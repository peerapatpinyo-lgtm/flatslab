# calculations.py
import numpy as np
import math

# ==========================================
# 1. PUNCHING SHEAR (ADVANCED WITH MOMENT TRANSFER)
# ==========================================
def calculate_section_properties(c1, c2, d, col_type):
    """
    Helper to calculate Ac, Jc, and gamma_v for Moment Transfer.
    c1: dimension parallel to moment
    c2: dimension perpendicular to moment
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

    # 1. Area of concrete (Ac)
    # Ac = Perimeter * d
    if col_type == "interior":
        bo = 2*(b1 + b2)
        Ac = bo * d
    elif col_type == "edge":
        bo = 2*b1 + b2
        Ac = bo * d
    else: # corner
        bo = b1 + b2
        Ac = bo * d

    # 2. Polar Moment of Inertia (Jc) - Simplified for Interior Case primarily
    # Note: Exact Jc for Edge/Corner is complex geometrically. 
    # We use ACI approximate formulation or conservative Interior model for Jc base.
    # Jc = d * (b1^3/6 + b1*d^2/6) + (b1*d)*b2^2/2 ... (Simplified)
    
    # Using Standard Interior Formula for robustness in this scope:
    # Jc = (d * b1**3)/6 + (d**3 * b1)/6 + (d * b2 * b1**2)/2
    Jc = (d * b1**3)/6 + (d**3 * b1)/6 + (d * b2 * b1**2)/2

    # 3. Fraction of Moment Transferred by Shear (gamma_v)
    # gamma_f = 1 / (1 + (2/3) * sqrt(b1/b2))
    # gamma_v = 1 - gamma_f
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
    # vu = (Vu / Ac) + (gamma_v * Munbal * c_AB) / Jc
    # Convert Munbal from kg-m to kg-cm
    Munbal_cm = Munbal * 100.0
    
    stress_direct = Vu / Ac
    stress_moment = (gamma_v * Munbal_cm * c_AB) / Jc
    
    vu_max = stress_direct + stress_moment # ksc (kg/cm^2)

    # 3. Allowable Shear Stress (phi_vc)
    # ACI 318: phi = 0.85 (for shear) * older codes or 0.75 newer. Using 0.85 for consistency.
    phi = 0.85 
    sqrt_fc = np.sqrt(fc)
    
    # Vc calculation (Stress units)
    # min of (1.06, ...) * sqrt(fc)
    # Let's use the governing equation for most slabs: 1.06 * sqrt(fc) (ksc units approx 0.33sqrt(fc') MPa)
    # Or conservative 0.53 (shear) ? Punching is usually 1.06 (4*sqrt(fc') psi)
    vc_stress_nominal = 1.06 * sqrt_fc 
    
    # Refine Vc based on rectangularity (beta)
    beta = max(c1, c2) / min(c1, c2)
    vc_beta = 0.27 * (2 + 4/beta) * sqrt_fc
    
    vc_final = min(vc_stress_nominal, vc_beta)
    
    phi_vc_stress = phi * vc_final

    # 4. Check
    ratio = vu_max / phi_vc_stress
    status = "OK" if ratio <= 1.0 else "FAIL"

    return {
        "Vu": Vu,
        "Munbal": Munbal,
        "d": d,
        "bo": bo,
        "Ac": Ac,
        "gamma_v": gamma_v,
        "stress_actual": vu_max,
        "stress_allow": phi_vc_stress,
        "ratio": ratio,
        "status": status,
        "note": f"Incl. Moment: {Munbal:,.0f} kg-m"
    }

# ==========================================
# 2. DUAL CASE PUNCHING (DROP PANEL)
# ==========================================
def check_punching_dual_case(w_u, Lx, Ly, fc, c1, c2, d_drop, d_slab, drop_w, drop_l, col_type, Munbal=0.0):
    # Case 1: Inner (Drop Depth)
    # Load inside critical section is neglected, but simplified to full area for safety or use (Lx*Ly - Ac)
    Vu1 = w_u * (Lx * Ly) * 0.95 # Approx reduction for critical area
    res1 = check_punching_shear(Vu1, fc, c1, c2, d_drop, col_type, Munbal)
    
    # Case 2: Outer (Slab Depth) - Moment transfers less to the outer perimeter, assume Munbal decays or is taken by Drop.
    # Conservative: Use same Munbal or 50%
    Vu2 = w_u * (Lx * Ly) * 0.90 
    res2 = check_punching_shear(Vu2, fc, drop_w, drop_l, d_slab, col_type, Munbal * 0.5)
    
    if res1['ratio'] > res2['ratio']:
        return res1
    else:
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
    Using ACI Multiplier Method.
    Parameters:
    - w_service: Service Load (SDL + LL) kg/m2
    - L: Span length (m)
    - h: Slab thickness (cm)
    - As_provided: Area of steel in tension zone (cm2) (Approximate)
    """
    # 1. Material Properties
    Ec = 15100 * np.sqrt(fc) # ksc
    
    # 2. Immediate Deflection (Elastic)
    # Using simplified coefficient for Flat Plate (Approx 5/384 factor equivalent or FEM based)
    # Delta_i = k * w * L^4 / (E * I)
    # For Flat Plate interior span, k is approx 0.065 (Coefficient Method)
    # Let's use a standard approximation for fixed-fixed/continuous strip
    
    L_cm = L * 100.0
    w_line_kg_cm = (w_service * (b/100.0)) / 100.0 # kg/cm per strip
    
    Ig = b * (h**3) / 12.0
    
    # Effective Moment of Inertia (Ie)
    # For service loads, slab is likely cracked. Assume Ie = 0.35 * Ig to 0.5 * Ig (R-Value equivalent)
    # ACI 318-19 Table 6.6.3.1.1(a) suggests 0.25Ig for Flat Plates in analysis, 
    # but for deflection we can be slightly more optimistic or use Branson.
    # Let's use I_effective = 0.4 * Ig for a balanced estimation.
    Ie = 0.4 * Ig
    
    # Deflection Formula (Continuous Beam Approx): 1/384 is too stiff, 5/384 is pinned.
    # Continuous span midspan deflection coeff is roughly 1/150 to 1/200 range
    # Standard approx: Delta = (w L^4) / (384 EI) * coeff
    # Let's use: Delta = (w L^4) / (48 * EI) * (1/10) roughly -> 0.002
    # More accurate for Flat Slab: Delta_max approx L/360 to L/480 range check.
    # Let's use the classic calculation: Delta = (5 * w * L^4) / (384 * E * Ie) * 0.4 (continuity factor)
    
    Delta_immediate = (5 * w_line_kg_cm * (L_cm**4)) / (384 * Ec * Ie) * 0.5 
    
    # 3. Long Term Multiplier (Lambda)
    # Lambda = Xi / (1 + 50*rho')
    # Xi (Time factor) > 5 years = 2.0
    # rho' (Compression steel) = 0 for typical slab
    Lambda_LT = 2.0
    
    Delta_LT = Delta_immediate * Lambda_LT
    Delta_Total = Delta_immediate + Delta_LT
    
    # 4. Allowable (L/240 or L/480)
    # L/240 for roof/floor not supporting non-structural elements likely to be damaged
    # L/480 for sensitive partitions
    Limit_240 = L_cm / 240.0
    Limit_480 = L_cm / 480.0
    
    status = "PASS" if Delta_Total <= Limit_240 else "FAIL"
    
    return {
        "Delta_Immediate": Delta_immediate,
        "Delta_LongTerm": Delta_LT,
        "Delta_Total": Delta_Total,
        "Limit_240": Limit_240,
        "Limit_480": Limit_480,
        "status": status,
        "I_effective": Ie
    }

# ==========================================
# 4. EFM STIFFNESS (Unchanged but ensuring imports)
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
    
    Vu_oneway = w_u * x_crit * L_width # Load on the strip width (L_width)
    
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
