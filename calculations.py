import numpy as np

def calculate_stiffness(c1, c2, L1, L2, lc, h_slab, fc):
    """Calculate EFM Stiffness Parameters"""
    Ec = 15100 * np.sqrt(fc) # ksc
    # Inertia
    Is = (L2*100 * h_slab**3)/12
    Ic = (c2 * c1**3)/12
    # Stiffness K
    Ks = 4 * Ec * Is / (L1*100)
    Kc = 4 * Ec * Ic / (lc*100)
    # Torsional Kt (Simplified ACI)
    x = min(c1, h_slab)
    y = max(c1, h_slab)
    C = (1 - 0.63*(x/y)) * (x**3 * y)/3
    denom = (L2*100 * (1 - c2/(L2*100))**3)
    Kt = 2 * (9 * Ec * C) / denom if denom != 0 else 0
    
    # Kec
    sum_Kc = 2 * Kc # Top & Bottom cols
    if Kt == 0 or sum_Kc == 0: 
        Kec = 0
    else: 
        Kec = 1 / (1/sum_Kc + 1/Kt)
    return Ks, Kc, Kt, Kec

def check_punching_shear(Vu, fc, c1, c2, d):
    """ACI 318 Punching Shear Check (Interior Col)"""
    b0 = 2*(c1+d) + 2*(c2+d)
    phi = 0.75
    Vc_stress = 1.06 * np.sqrt(fc) # kg/cm2
    Vc = phi * Vc_stress * b0 * d
    
    if Vc <= 0: return 0, 999, "FAIL", b0
    
    ratio = Vu / Vc
    status = "PASS" if ratio <= 1.0 else "FAIL"
    return Vc, ratio, status, b0

def design_rebar_detailed(Mu_kgm, b_cm, d_cm, fc, fy):
    """Calculate Rebar with Min/Max Checks"""
    if Mu_kgm < 10: return 0, 0, "None", "OK"
    
    Mu = Mu_kgm * 100 # kg-cm
    phi = 0.90
    
    # Rn
    Rn = Mu / (phi * b_cm * d_cm**2)
    
    # Rho limits
    rho_min = 0.0018
    beta1 = 0.85 if fc <= 280 else max(0.65, 0.85 - 0.05*(fc-280)/70)
    rho_b = 0.85 * beta1 * (fc/fy) * (6120/(6120+fy))
    rho_max = 0.75 * rho_b 
    
    try:
        term = 1 - (2*Rn)/(0.85*fc)
        if term < 0: return 999, rho_max, "Section Too Small", "FAIL"
        rho_req = (0.85*fc/fy) * (1 - np.sqrt(term))
    except:
        return 999, rho_max, "Calc Error", "FAIL"
    
    rho_design = max(rho_req, rho_min)
    As_req = rho_design * b_cm * d_cm
    
    status = "OK"
    note = ""
    if rho_req > rho_max: 
        status = "FAIL"
        note = "Rho > Rho_max"
    elif rho_req < rho_min:
        note = "Used Min Steel"
        
    return As_req, rho_design, note, status
