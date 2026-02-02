# calculations.py
import numpy as np
import math

# ==========================================
# 1. PUNCHING SHEAR (Single Critical Section)
# ==========================================
def check_punching_shear(Vu, fc, c1, c2, d, col_type="interior"):
    """
    Check punching shear for a specific critical section.
    Parameters:
    - Vu: Factored shear force (kg)
    - fc: Concrete strength (ksc)
    - c1: Dimension in direction 1 (cm)
    - c2: Dimension in direction 2 (cm)
    - d: Effective depth (cm)
    - col_type: 'interior', 'edge', or 'corner'
    """
    
    # 1. Robust Input Casting (Prevent TypeError)
    try:
        Vu = float(Vu)
        fc = float(fc)
        c1 = float(c1)
        c2 = float(c2)
        d = float(d)
    except ValueError:
        return {"status": "ERROR", "ratio": 999, "Note": "Invalid Input Data"}

    # 2. Determine Alpha_s and Critical Perimeter (b0)
    if col_type == "interior":
        alpha_s = 40
        b0 = 2 * (c1 + d) + 2 * (c2 + d)
    elif col_type == "edge":
        alpha_s = 30
        b0 = 2 * (c1 + d/2.0) + (c2 + d) 
    elif col_type == "corner":
        alpha_s = 20
        b0 = (c1 + d/2.0) + (c2 + d/2.0)
    else:
        alpha_s = 40
        b0 = 2 * (c1 + d) + 2 * (c2 + d)

    # 3. Beta (Ratio of long side to short side of column)
    min_c = min(c1, c2)
    beta = max(c1, c2) / min_c if min_c > 0 else 1.0
    
    # 4. Concrete Capacity (Vc) according to ACI 318
    sqrt_fc = np.sqrt(fc) # ksc unit
    
    # (a) Aspect Ratio Effect
    Vc1 = 0.53 * (1 + 2/beta) * sqrt_fc * b0 * d
    
    # (b) Perimeter Size Effect
    Vc2 = 0.27 * ((alpha_s * d / b0) + 2) * sqrt_fc * b0 * d
    
    # (c) Basic Shear Strength
    Vc3 = 1.06 * sqrt_fc * b0 * d
    
    # Nominal Strength (Smallest of 3 equations)
    Vn = min(Vc1, Vc2, Vc3) # Rename to Vn to match legacy code
    phi = 0.85 # ACI 318-19 Shear phi (Previously 0.75 in older code, adjust if needed)
    
    Vc_design = phi * Vn # Rename to Vc_design
    
    # 5. Check Ratio
    if Vc_design > 0:
        ratio = Vu / Vc_design
    else:
        ratio = 999.0
        
    status = "OK" if ratio <= 1.0 else "FAIL"
    
    # Return dictionary with KEYS matching app.py expectations
    return {
        "Vu": Vu,
        "d": d,
        "d_avg": d,    # Alias
        "b0": b0,      # KEY FIX: Number 0 (matches app.py)
        "bo": b0,      # Alias: Letter o (just in case)
        "beta": beta,
        "alpha_s": alpha_s,
        "Vc1": Vc1,
        "Vc2": Vc2,
        "Vc3": Vc3,
        "Vn": Vn,             # Key matches legacy
        "Vc_nominal": Vn,     # Alias
        "Vc_design": Vc_design, # Key matches legacy
        "phi_Vc": Vc_design,    # Alias
        "ratio": ratio,
        "status": status
    }

# ==========================================
# 2. PUNCHING SHEAR (Dual Case for Drop Panel)
# ==========================================
def check_punching_dual_case(w_u, Lx, Ly, fc, c1, c2, d_drop, d_slab, drop_w, drop_l, col_type):
    """
    Checks 2 critical sections:
    1. Around Column (d = d_drop)
    2. Around Drop Panel (d = d_slab)
    """
    w_u = float(w_u); Lx = float(Lx); Ly = float(Ly)
    
    # --- Check 1: Inner Section (Around Column) ---
    if col_type == "interior":
        c1_crit = c1 + d_drop
        c2_crit = c2 + d_drop
    elif col_type == "edge":
        c1_crit = c1 + d_drop/2 
        c2_crit = c2 + d_drop
    else: # corner
        c1_crit = c1 + d_drop/2
        c2_crit = c2 + d_drop/2
        
    Ac1 = (c1_crit/100.0) * (c2_crit/100.0)
    Vu1 = w_u * (Lx*Ly - Ac1)
    
    res1 = check_punching_shear(Vu1, fc, c1, c2, d_drop, col_type)
    
    # --- Check 2: Outer Section (Around Drop Panel) ---
    if col_type == "interior":
        drop_c1_crit = drop_w + d_slab
        drop_c2_crit = drop_l + d_slab
    elif col_type == "edge":
        drop_c1_crit = drop_w + d_slab/2
        drop_c2_crit = drop_l + d_slab
    else:
        drop_c1_crit = drop_w + d_slab/2
        drop_c2_crit = drop_l + d_slab/2

    Ac2 = (drop_c1_crit/100.0) * (drop_c2_crit/100.0)
    Vu2 = w_u * (Lx*Ly - Ac2)
    
    res2 = check_punching_shear(Vu2, fc, drop_w, drop_l, d_slab, col_type)
    
    max_ratio = max(res1['ratio'], res2['ratio'])
    status = "OK" if max_ratio <= 1.0 else "FAIL"
    
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
# 4. ONE-WAY SHEAR CHECK (Beam Action)
# ==========================================
def check_oneway_shear(w_u, L_span, L_width, c_support, d_eff, fc):
    w_u = float(w_u)
    L_span = float(L_span)
    c_support = float(c_support)
    d_eff = float(d_eff)
    fc = float(fc)

    x_crit = (L_span / 2.0) - (c_support / 100.0 / 2.0) - (d_eff / 100.0)
    if x_crit < 0: x_crit = 0
    
    Vu_oneway = w_u * x_crit 
    
    phi = 0.85 
    Vc_stress = 0.53 * np.sqrt(fc) # ksc
    Vc = Vc_stress * 100.0 * d_eff 
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
