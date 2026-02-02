# calculations.py
import numpy as np
import math

# ==========================================
# 1. PUNCHING SHEAR (Single Critical Section)
# ==========================================
def check_punching_shear(Vu, fc, c1, c2, d, col_type="interior"):
    """
    Check punching shear for a specific critical section.
    Auto-adjusts critical perimeter (b0) based on column location.
    
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
    # Note: Critical section is at d/2 from column face.
    
    if col_type == "interior":
        # 4 sides effective
        alpha_s = 40
        b0 = 2 * (c1 + d) + 2 * (c2 + d)
        
    elif col_type == "edge":
        # 3 sides effective 
        # Typically: 2 sides of (c1 + d/2) + 1 side of (c2 + d)
        alpha_s = 30
        # Simplification: Assume column is flush with edge
        b0 = 2 * (c1 + d/2.0) + (c2 + d) 
        
    elif col_type == "corner":
        # 2 sides effective
        alpha_s = 20
        # Corner: 1 side (c1 + d/2) + 1 side (c2 + d/2)
        b0 = (c1 + d/2.0) + (c2 + d/2.0)
    else:
        # Fallback to interior
        alpha_s = 40
        b0 = 2 * (c1 + d) + 2 * (c2 + d)

    # 3. Beta (Ratio of long side to short side of column)
    # Prevent division by zero if dimensions are weird
    min_c = min(c1, c2)
    beta = max(c1, c2) / min_c if min_c > 0 else 1.0
    
    # 4. Concrete Capacity (Vc) according to ACI 318 (Metric)
    # Equations return Force in kg
    sqrt_fc = np.sqrt(fc) # ksc unit
    
    # (a) Aspect Ratio Effect
    Vc1 = 0.53 * (1 + 2/beta) * sqrt_fc * b0 * d
    
    # (b) Perimeter Size Effect
    Vc2 = 0.27 * ((alpha_s * d / b0) + 2) * sqrt_fc * b0 * d
    
    # (c) Basic Shear Strength
    Vc3 = 1.06 * sqrt_fc * b0 * d
    
    # Nominal Strength (Smallest of 3 equations)
    Vc_nominal = min(Vc1, Vc2, Vc3)
    phi = 0.85 # ACI 318-19 Shear phi
    
    phi_Vc = phi * Vc_nominal
    
    # 5. Check Ratio
    if phi_Vc > 0:
        ratio = Vu / phi_Vc
    else:
        ratio = 999.0
        
    status = "OK" if ratio <= 1.0 else "FAIL"
    
    # Return full results dictionary for plotting/display
    return {
        "Vu": Vu,
        "d_avg": d, # Alias for consistency
        "d": d,
        "bo": b0,
        "beta": beta,
        "alpha_s": alpha_s,
        "Vc_formulas": [Vc1, Vc2, Vc3],
        "Vc_nominal": Vc_nominal,
        "phi_Vc": phi_Vc,
        "ratio": ratio,
        "status": status
    }

# ==========================================
# 2. PUNCHING SHEAR (Dual Case for Drop Panel)
# ==========================================
def check_punching_dual_case(w_u, Lx, Ly, fc, c1, c2, d_drop, d_slab, drop_w, drop_l, col_type):
    """
    Checks 2 critical sections:
    1. Around Column (d = d_drop) -> Checks punching through Drop Panel
    2. Around Drop Panel (d = d_slab) -> Checks punching through Slab
    """
    # Ensure floats
    w_u = float(w_u); Lx = float(Lx); Ly = float(Ly)
    
    # --- Check 1: Inner Section (Around Column) ---
    # Critical section inside Drop Panel
    # Load acts on area outside critical section
    
    # Calculate approx critical area to subtract from load
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
    # Treats the Drop Panel as a large "Column"
    # Punching through the slab thickness (d_slab)
    
    # NOTE: When checking outer section, the "column dimensions" become the "drop panel dimensions"
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
        "check_1": res1, # Inner (Drop Panel)
        "check_2": res2  # Outer (Slab)
    }

# ==========================================
# 3. EFM STIFFNESS CALCULATIONS
# ==========================================
def calculate_stiffness(c1, c2, L1, L2, lc, h_slab, fc):
    """
    Calculate K_slab, K_col, K_ec (Equivalent Column Stiffness)
    Units: cm, kg
    Note: L1 is direction of analysis, L2 is transverse width
    """
    # Ensure floats
    c1=float(c1); c2=float(c2); L1=float(L1); L2=float(L2); lc=float(lc); h_slab=float(h_slab); fc=float(fc)

    # Elastic Modulus of Concrete (ACI Metric)
    E_c = 15100 * np.sqrt(fc) # ksc
    
    # 1. Column Stiffness (Kc)
    # Assumes infinite stiffness within slab joint not modeled (Simplified)
    # Ic = Moment of inertia of column
    Ic = c2 * (c1**3) / 12.0 
    lc_cm = lc * 100.0
    
    # Kc for one column (Far end fixed assumption = 4EI/L)
    Kc = 4 * E_c * Ic / lc_cm
    
    # Sum_Kc (Columns above and below)
    Sum_Kc = 2 * Kc
    
    # 2. Slab Stiffness (Ks)
    # Gross section
    Is = (L2*100.0) * (h_slab**3) / 12.0
    L1_cm = L1 * 100.0
    Ks = 4 * E_c * Is / L1_cm
    
    # 3. Torsional Stiffness (Kt)
    # Based on ACI/EFM formula
    # Torsional member is the slab strip of width c1 and depth h_slab
    
    x = h_slab
    y = c1 
    # Torsional constant C
    C = (1 - 0.63 * x / y) * (x**3 * y) / 3.0
    
    # Kt calculation
    # L2 is transverse span length
    # c2 is transverse column width
    term = (1 - c2/(L2*100.0))
    if term <= 0: term = 0.01 # Prevent zero division or negative
    
    denom = (L2*100.0 * term**3)
    
    if denom > 0:
        Kt = 9 * E_c * C / denom
    else:
        Kt = 0 # Should not happen with check above
    
    # 4. Equivalent Column Stiffness (Kec)
    # 1/Kec = 1/Sum_Kc + 1/Kt
    if Kt > 0 and Sum_Kc > 0:
        Kec = 1 / (1/Sum_Kc + 1/Kt)
    else:
        Kec = 0
        
    return Ks, Sum_Kc, Kt, Kec

# ==========================================
# 4. ONE-WAY SHEAR CHECK (Beam Action)
# ==========================================
def check_oneway_shear(w_u, L_span, L_width, c_support, d_eff, fc):
    """
    Checks One-way shear on a 1.0m wide strip.
    """
    # Cast to float
    w_u = float(w_u)
    L_span = float(L_span)
    c_support = float(c_support)
    d_eff = float(d_eff)
    fc = float(fc)

    # Critical section at d from support face
    # c_support is column dimension parallel to span
    
    # Convert inputs to consistent units (m for length, cm for section)
    # x_crit (m) = L/2 - c/2 - d
    x_crit = (L_span / 2.0) - (c_support / 100.0 / 2.0) - (d_eff / 100.0)
    
    if x_crit < 0: x_crit = 0
    
    # Vu per meter strip (w_u is kg/m^2, so Vu is kg/m width)
    Vu_oneway = w_u * x_crit 
    
    phi = 0.75 # Shear phi
    # Vc = 0.53 * sqrt(fc) * bw * d
    Vc_stress = 0.53 * np.sqrt(fc) # ksc
    
    # bw = 100 cm (1 meter strip), d_eff in cm
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
