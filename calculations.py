import numpy as np

def calculate_stiffness(c1, c2, L1, L2, lc, h_slab, fc):
    """
    Calculate EFM Stiffness Parameters (K_slab, K_col, K_torsion, K_ec)
    Input units: cm, m (mixed as per original logic), ksc
    """
    Ec = 15100 * np.sqrt(fc) # ksc
    
    # 1. Slab Stiffness (Ks)
    # L2 is width (transverse), L1 is span (longitudinal)
    Is = (L2 * 100 * h_slab**3) / 12
    Ks = 4 * Ec * Is / (L1 * 100)
    
    # 2. Column Stiffness (Kc)
    Ic = (c2 * c1**3) / 12
    Kc = 4 * Ec * Ic / (lc * 100)
    
    # 3. Torsional Member Stiffness (Kt)
    # Based on ACI 318 Simplified Torsion
    x = min(c1, h_slab)
    y = max(c1, h_slab)
    C = (1 - 0.63 * (x / y)) * (x**3 * y) / 3
    
    # Check denominator to avoid division by zero
    denom_term = (1 - c2 / (L2 * 100))
    if denom_term <= 0: denom_term = 0.01 # Prevent error if col width = slab width
        
    denom = (L2 * 100 * denom_term**3)
    
    if denom != 0:
        Kt = 2 * (9 * Ec * C) / denom
    else:
        Kt = 0
    
    # 4. Equivalent Column Stiffness (Kec)
    sum_Kc = 2 * Kc # Assumes column above and below are same
    
    if Kt == 0 or sum_Kc == 0: 
        Kec = 0
    else: 
        Kec = 1 / (1/sum_Kc + 1/Kt)
        
    return Ks, Kc, Kt, Kec

def check_punching_shear(Vu, fc, c1, c2, d, col_type="interior"):
    """
    ACI 318 Punching Shear Check (3 Formulas)
    Input: Vu (kg), fc (ksc), c1, c2 (cm), d (cm)
    Output: Vc (kg), Ratio, Status, bo (cm)
    """
    # 1. Critical Perimeter (bo)
    b0 = 2 * (c1 + d) + 2 * (c2 + d)
    
    # 2. Parameters
    beta = max(c1, c2) / min(c1, c2) # Long side / Short side ratio
    alpha_s = 40 if col_type == "interior" else (30 if col_type == "edge" else 20)
    phi = 0.75
    
    # 3. ACI 318 Formulas (in ksc unit approx)
    # Eq 1: Effect of Geometry (Aspect Ratio)
    # Vc = 0.53 * (1 + 2/beta) * sqrt(fc) * b0 * d
    Vc1 = 0.53 * (1 + 2/beta) * np.sqrt(fc) * b0 * d
    
    # Eq 2: Effect of Large Perimeter (b0/d ratio)
    # Vc = 0.27 * (alpha_s * d / b0 + 2) * sqrt(fc) * b0 * d
    Vc2 = 0.27 * ((alpha_s * d / b0) + 2) * np.sqrt(fc) * b0 * d
    
    # Eq 3: Basic Shear Strength
    # Vc = 1.06 * sqrt(fc) * b0 * d
    Vc3 = 1.06 * np.sqrt(fc) * b0 * d
    
    # Nominal Strength (Smallest controls)
    Vn = min(Vc1, Vc2, Vc3)
    Vc_design = phi * Vn
    
    if Vc_design <= 0: return 0, 999, "FAIL", b0
    
    ratio = Vu / Vc_design
    status = "PASS" if ratio <= 1.0 else "FAIL"
    
    # Debug info: return which equation controlled could be added later
    return Vc_design, ratio, status, b0

def design_rebar_detailed(Mu_kgm, b_cm, d_cm, fc, fy):
    """
    Calculate Required Reinforcement Area (As_req)
    Input: Mu (kg-m), b (cm), d (cm), fc, fy (ksc)
    Output: As_req (cm2), rho_design, Note, Status
    """
    if Mu_kgm < 10: return 0, 0.0018, "Min Steel", "OK"
    
    Mu = Mu_kgm * 100 # Convert to kg-cm
    phi = 0.90
    
    # Check Rn
    Rn = Mu / (phi * b_cm * d_cm**2)
    
    # Rho Limits (ACI)
    rho_min = 0.0018 # Temperature steel for slabs (Grade 4000+)
    
    # Calculate Beta1
    if fc <= 280:
        beta1 = 0.85
    else:
        beta1 = max(0.65, 0.85 - 0.05 * (fc - 280) / 70)
        
    # Balanced Rho (Rho_b)
    rho_b = 0.85 * beta1 * (fc / fy) * (6120 / (6120 + fy))
    rho_max = 0.75 * rho_b # Ductility limit
    
    # Calculate Required Rho
    try:
        # From Mu = phi * As * fy * (d - a/2)
        term = 1 - (2 * Rn) / (0.85 * fc)
        if term < 0:
            return 999, rho_max, "Section Too Small (Concrete Fail)", "FAIL"
        
        rho_req = (0.85 * fc / fy) * (1 - np.sqrt(term))
    except:
        return 999, rho_max, "Calc Error", "FAIL"
    
    # Final Design Logic
    if rho_req > rho_max:
        return rho_req * b_cm * d_cm, rho_req, "Rho > Rho_max (Ductility Warning)", "FAIL"
    
    rho_design = max(rho_req, rho_min)
    As_req = rho_design * b_cm * d_cm
    
    note = "OK"
    if rho_req < rho_min:
        note = "Controlled by Min Steel"
        
    return As_req, rho_design, note, "OK"
