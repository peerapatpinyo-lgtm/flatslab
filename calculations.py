# calculations.py
import numpy as np
import math

# ==========================================
# 1. PUNCHING SHEAR (Single Critical Section)
# ==========================================
def check_punching_shear(Vu, fc, c1, c2, d, col_type="interior"):
    """
    Check punching shear for a specific critical section.
    Vu: Factored Shear Force (kg) - Calculated outside based on area
    fc: f'c (ksc)
    c1, c2: Column dimensions (cm)
    d: Effective depth (cm)
    col_type: 'interior', 'edge', 'corner'
    """
    
    # 1. Critical Perimeter (bo)
    # Simplified rectangular perimeter at d/2 from face
    b0 = 2 * (c1 + d) + 2 * (c2 + d)
    
    # 2. Beta (Ratio of long side to short side of column)
    beta = max(c1, c2) / min(c1, c2)
    
    # 3. Alpha_s (Constant based on location)
    if col_type == "interior": alpha_s = 40
    elif col_type == "edge": alpha_s = 30
    else: alpha_s = 20
    
    # 4. Concrete Capacity (Vc) - ACI 318
    # We need smallest of 3 equations
    sqrt_fc = np.sqrt(fc)
    
    # Eq (a)
    Vc1 = 0.53 * (1 + 2/beta) * sqrt_fc * b0 * d
    
    # Eq (b)
    Vc2 = 0.27 * ((alpha_s * d / b0) + 2) * sqrt_fc * b0 * d
    
    # Eq (c)
    Vc3 = 1.06 * sqrt_fc * b0 * d
    
    # Nominal Strength
    Vn = min(Vc1, Vc2, Vc3)
    
    # Design Strength
    phi = 0.75
    Vc_design = phi * Vn
    
    # Check
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
    """
    Checks 2 critical sections:
    1. Inner Section: d = d_drop (Total thickness), Perimeter around Column
    2. Outer Section: d = d_slab (Slab thickness), Perimeter around Drop Panel
    """
    
    # --- Case 1: Inner Section (at d/2 from Column) ---
    # Load: Wu * (Total Area - Area inside critical section 1)
    # Approx Critical Area 1
    c1_d = c1 + d_drop
    c2_d = c2 + d_drop
    Ac1 = (c1_d/100) * (c2_d/100)
    Vu1 = w_u * (Lx*Ly - Ac1)
    
    res1 = check_punching_shear(Vu1, fc, c1, c2, d_drop, col_type)
    
    # --- Case 2: Outer Section (at d/2 from Drop Panel) ---
    # Load: Wu * (Total Area - Area inside critical section 2)
    # Critical section is around the Drop Panel
    # Dimensions of support are now drop_w and drop_l
    drop_c1_d = drop_w + d_slab
    drop_c2_d = drop_l + d_slab
    Ac2 = (drop_c1_d/100) * (drop_c2_d/100)
    Vu2 = w_u * (Lx*Ly - Ac2)
    
    # Note: For outer check, the "column" dimension is the Drop Panel dimension
    res2 = check_punching_shear(Vu2, fc, drop_w, drop_l, d_slab, col_type)
    
    # --- Combine Results ---
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
    
    # 1. Column Stiffness (Kc) - Simplified (Infinite Inertia not considered for simplicity)
    # Ic = b*h^3 / 12
    Ic = c2 * (c1**3) / 12
    # Kc = 4EI / L (Fixed-Fixed assumption for intermediate floor)
    lc_cm = lc * 100
    Kc = 4 * E_c * Ic / lc_cm
    # Total Kc (Above + Below)
    Sum_Kc = 2 * Kc
    
    # 2. Slab Stiffness (Ks)
    # Is = L2 * h^3 / 12
    Is = (L2*100) * (h_slab**3) / 12
    L1_cm = L1 * 100
    Ks = 4 * E_c * Is / L1_cm
    
    # 3. Torsional Stiffness (Kt) -> Equivalent Column (Kec)
    # This is complex. Using a simplified approximation for visual purpose.
    # C = constant for torsional member
    x = h_slab
    y = c1 # approx width of torsion arm
    C = (1 - 0.63 * x / y) * (x**3 * y) / 3
    Kt = 9 * E_c * C / (L2*100 * (1 - c2/(L2*100))**3) # Very Rough Approx
    
    # Equivalent Stiffness Kec
    # 1/Kec = 1/Sum_Kc + 1/Kt
    if Kt > 0:
        Kec = 1 / (1/Sum_Kc + 1/Kt)
    else:
        Kec = Sum_Kc # rigid connection
        
    return Ks, Sum_Kc, Kt, Kec

# ==========================================
# 4. ONE-WAY SHEAR CHECK (Beam Action) - [NEW]
# ==========================================
def check_oneway_shear(w_u, L_span, L_width, c_support, d_eff, fc):
    """
    Check One-way Shear for a 1-meter strip
    Input: 
      - w_u (kg/m2)
      - L_span (m): Span length in direction of analysis
      - c_support (cm): Support dimension (parallel to span)
      - d_eff (cm): Effective depth
      - fc (ksc)
    """
    # 1. Calculate Vu at critical section (d from support face)
    # Distance from center to critical section
    # x_crit = (L/2) - (c/2) - d
    x_crit = (L_span / 2.0) - (c_support / 100.0 / 2.0) - (d_eff / 100.0)
    
    # Check if x_crit is valid (in case span is very short)
    if x_crit < 0: x_crit = 0
    
    # Shear Force (consider 1 m strip width)
    # Vu = w_u * x_crit * 1.0 (width)
    Vu_oneway = w_u * x_crit 
    
    # 2. Capacity Phi Vn
    # Vc = 0.53 * sqrt(fc) * b * d (ACI 318 Simplified)
    # b = 100 cm (1 m strip)
    phi = 0.75 # Shear phi
    
    Vc_stress = 0.53 * np.sqrt(fc) # ksc
    Vc = Vc_stress * 100.0 * d_eff # kg per 1m strip
    
    phi_Vc = phi * Vc
    
    # 3. Result
    ratio = Vu_oneway / phi_Vc if phi_Vc > 0 else 999
    status = "PASS" if ratio <= 1.0 else "FAIL"
    
    return {
        "Vu": Vu_oneway,
        "phi_Vc": phi_Vc,
        "ratio": ratio,
        "status": status,
        "x_crit": x_crit # Distance from center used for load
    }
