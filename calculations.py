import numpy as np
import math

# ==========================================
# 1. PUNCHING SHEAR (Single Critical Section)
# ==========================================
def check_punching_shear(Vu, fc, c1, c2, d, col_type="interior"):
    """
    Check punching shear for a specific critical section.
    """
    # 1. Critical Perimeter (bo)
    b0 = 2 * (c1 + d) + 2 * (c2 + d)
    
    # 2. Beta
    beta = max(c1, c2) / min(c1, c2)
    
    # 3. Alpha_s
    if col_type == "interior": alpha_s = 40
    elif col_type == "edge": alpha_s = 30
    else: alpha_s = 20
    
    # 4. Concrete Capacity (Vc)
    sqrt_fc = np.sqrt(fc)
    
    Vc1 = 0.53 * (1 + 2/beta) * sqrt_fc * b0 * d
    Vc2 = 0.27 * ((alpha_s * d / b0) + 2) * sqrt_fc * b0 * d
    Vc3 = 1.06 * sqrt_fc * b0 * d
    
    Vn = min(Vc1, Vc2, Vc3)
    phi = 0.75
    Vc_design = phi * Vn
    
    ratio = Vu / Vc_design if Vc_design > 0 else 999
    status = "PASS" if ratio <= 1.0 else "FAIL"
    
    return {
        "Vu": Vu, "d": d, "b0": b0, "beta": beta, "alpha_s": alpha_s,
        "Vc1": Vc1, "Vc2": Vc2, "Vc3": Vc3, "Vn": Vn,
        "Vc_design": Vc_design, "ratio": ratio, "status": status
    }

# ==========================================
# 2. PUNCHING SHEAR (Dual Case for Drop Panel)
# ==========================================
def check_punching_dual_case(w_u, Lx, Ly, fc, c1, c2, d_drop, d_slab, drop_w, drop_l, col_type):
    # Case 1: Inner Section
    c1_d = c1 + d_drop
    c2_d = c2 + d_drop
    Ac1 = (c1_d/100) * (c2_d/100)
    Vu1 = w_u * (Lx*Ly - Ac1)
    
    res1 = check_punching_shear(Vu1, fc, c1, c2, d_drop, col_type)
    
    # Case 2: Outer Section
    drop_c1_d = drop_w + d_slab
    drop_c2_d = drop_l + d_slab
    Ac2 = (drop_c1_d/100) * (drop_c2_d/100)
    Vu2 = w_u * (Lx*Ly - Ac2)
    
    res2 = check_punching_shear(Vu2, fc, drop_w, drop_l, d_slab, col_type)
    
    max_ratio = max(res1['ratio'], res2['ratio'])
    status = "PASS" if max_ratio <= 1.0 else "FAIL"
    
    return {
        "is_dual": True,
        "status": status,
        "ratio": max_ratio,
        "check_1": res1,
        "check_2": res2
    }

# ==========================================
# 3. EFM STIFFNESS CALCULATIONS
# ==========================================
def calculate_stiffness(c1, c2, L1, L2, lc, h_slab, fc):
    """
    Calculate K_slab, K_col, K_ec (Torsional member) for EFM
    Units: cm, kg
    """
    E_c = 15100 * np.sqrt(fc) # ksc
    
    # 1. Column Stiffness (Kc)
    Ic = c2 * (c1**3) / 12
    lc_cm = lc * 100
    Kc = 4 * E_c * Ic / lc_cm
    Sum_Kc = 2 * Kc
    
    # 2. Slab Stiffness (Ks)
    Is = (L2*100) * (h_slab**3) / 12
    L1_cm = L1 * 100
    Ks = 4 * E_c * Is / L1_cm
    
    # 3. Torsional Stiffness (Kt)
    x = h_slab
    y = c1 
    C = (1 - 0.63 * x / y) * (x**3 * y) / 3.0
    
    denom = (L2*100 * (1 - c2/(L2*100))**3)
    if denom == 0: denom = 1.0
    Kt = 9 * E_c * C / denom
    
    # Equivalent Stiffness Kec
    if Kt > 0:
        Kec = 1 / (1/Sum_Kc + 1/Kt)
    else:
        Kec = Sum_Kc 
        
    return Ks, Sum_Kc, Kt, Kec

# ==========================================
# 4. ONE-WAY SHEAR CHECK
# ==========================================
def check_oneway_shear(w_u, L_span, L_width, c_support, d_eff, fc):
    x_crit = (L_span / 2.0) - (c_support / 100.0 / 2.0) - (d_eff / 100.0)
    if x_crit < 0: x_crit = 0
    
    Vu_oneway = w_u * x_crit 
    
    phi = 0.75 
    Vc_stress = 0.53 * np.sqrt(fc)
    Vc = Vc_stress * 100.0 * d_eff 
    phi_Vc = phi * Vc
    
    ratio = Vu_oneway / phi_Vc if phi_Vc > 0 else 999
    status = "PASS" if ratio <= 1.0 else "FAIL"
    
    return {
        "Vu": Vu_oneway,
        "phi_Vc": phi_Vc,
        "ratio": ratio,
        "status": status,
        "x_crit": x_crit
    }
