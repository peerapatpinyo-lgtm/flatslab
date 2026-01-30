#calculations.py
import numpy as np

# ==========================================
# 1. EFM STIFFNESS CALCULATION (Original)
# ==========================================
def calculate_stiffness(c1, c2, L1, L2, lc, h_slab, fc):
    """
    Calculate EFM Stiffness Parameters
    c1, c2: Column dimension (cm) -> c1 is parallel to moment
    L1, L2: Span length (m) -> L1 is parallel to moment
    lc: Storey height (m)
    """
    Ec = 15100 * np.sqrt(fc) # ksc
    
    # Inertia (Use Gross Section)
    Is = (L2*100 * h_slab**3)/12
    Ic = (c2 * c1**3)/12
    
    # Stiffness K (Simplified)
    Ks = 4 * Ec * Is / (L1*100)
    Kc = 4 * Ec * Ic / (lc*100)
    
    # Torsional Kt (Simplified ACI)
    x = min(c1, h_slab)
    y = max(c1, h_slab)
    
    # Torsional Constant C
    term1 = (1 - 0.63*(x/y))
    C = term1 * (x**3 * y)/3
    
    # Kt Calculation
    denom = (L2*100 * (1 - c2/(L2*100))**3)
    if denom <= 0: denom = 0.01 # Prevent div by zero
    Kt = 2 * (9 * Ec * C) / denom if denom != 0 else 0
    
    # Equivalent Stiffness (Kec)
    sum_Kc = 2 * Kc # Assuming columns above and below
    
    if Kt == 0 or sum_Kc == 0: 
        Kec = 0
    else: 
        Kec = 1 / (1/sum_Kc + 1/Kt)
        
    return Ks, Kc, Kt, Kec

# ==========================================
# 2. PUNCHING SHEAR (Original Check Single)
# ==========================================
def check_punching_shear(Vu, fc, c1, c2, d, col_type="interior"):
    """
    ACI 318 Punching Shear Check (Returns Detailed Dictionary)
    Input: Vu (kg), fc (ksc), c1, c2 (cm), d (cm)
    """
    # 1. Critical Perimeter (bo)
    b0 = 2*(c1+d) + 2*(c2+d)
    
    # 2. Parameters
    beta = max(c1, c2) / min(c1, c2) if min(c1, c2) > 0 else 1.0
    
    # Mapping alpha_s based on ACI 318 (40 for interior, 30 for edge, 20 for corner)
    alpha_s = 40 if col_type == "interior" else (30 if col_type == "edge" else 20)
    
    phi = 0.75
    
    # 3. ACI 318 Formulas (in ksc unit approx)
    # Eq 1: Geometry Effect (Aspect Ratio)
    Vc1_stress = 0.53 * (1 + 2/beta) * np.sqrt(fc)
    Vc1 = Vc1_stress * b0 * d
    
    # Eq 2: Large Perimeter Effect (Alpha_s)
    Vc2_stress = 0.27 * ((alpha_s * d / b0) + 2) * np.sqrt(fc)
    Vc2 = Vc2_stress * b0 * d
    
    # Eq 3: Basic Strength
    Vc3_stress = 1.06 * np.sqrt(fc)
    Vc3 = Vc3_stress * b0 * d
    
    # Nominal Strength (Smallest controls)
    Vn = min(Vc1, Vc2, Vc3)
    Vc_design = phi * Vn
    
    if Vc_design <= 0: 
        ratio = 999
        status = "FAIL"
    else:
        ratio = Vu / Vc_design
        status = "PASS" if ratio <= 1.0 else "FAIL"
    
    # Return Dictionary for Detailed Report (Keep all keys, added alpha_s for UI)
    return {
        "status": status,
        "ratio": ratio,
        "Vu": Vu,
        "Vc_design": Vc_design,
        "Vn": Vn,
        "Vc1": Vc1,
        "Vc2": Vc2,
        "Vc3": Vc3,
        "b0": b0,
        "phi": phi,
        "d": d,
        "beta": beta,
        "alpha_s": alpha_s # Added this for explicit display in app.py
    }

# ==========================================
# 2.1 NEW: DUAL PUNCHING CHECK (For Drop Panel) 
# ==========================================
def check_punching_dual_case(w_u, Lx, Ly, fc, cx, cy, d_col, d_slab, drop_w, drop_l, col_type):
    """
    Perform 2-step Punching Shear Check for Drop Panel System:
    1. Critical Section at Column Face (using d_col = slab + drop)
    2. Critical Section at Drop Panel Edge (using d_slab = slab only)
    
    Returns the Governing (Worst) Case Dictionary with nested details.
    """
    # --- Check 1: At Column Face (Thick Section) ---
    c1_d = cx + d_col
    c2_d = cy + d_col
    area_crit_1 = (c1_d/100) * (c2_d/100)
    Vu_1 = w_u * (Lx*Ly - area_crit_1)

    res_1 = check_punching_shear(Vu_1, fc, cx, cy, d_col, col_type)
    res_1['location'] = "Face of Column (Inner)"
    res_1['b0_desc'] = f"{res_1['b0']:.2f} cm (d={d_col:.2f})"

    # --- Check 2: At Drop Panel Edge (Thin Section) ---
    # Treat the Drop Panel as a "Large Column"
    c1_d_2 = drop_w + d_slab
    c2_d_2 = drop_l + d_slab
    area_crit_2 = (c1_d_2/100) * (c2_d_2/100)
    Vu_2 = w_u * (Lx*Ly - area_crit_2)

    res_2 = check_punching_shear(Vu_2, fc, drop_w, drop_l, d_slab, col_type)
    res_2['location'] = "Face of Drop Panel (Outer)"
    res_2['b0_desc'] = f"{res_2['b0']:.2f} cm (d={d_slab:.2f})"

    # --- Compare & Return Governing Case ---
    if res_1['ratio'] >= res_2['ratio']:
        governing = res_1
        note = "Critical at Column Face"
    else:
        governing = res_2
        note = "Critical at Drop Panel Edge"

    # Attach detailed checks to the return object for UI inspection
    governing['check_1'] = res_1
    governing['check_2'] = res_2
    governing['note'] = note
    governing['is_dual'] = True
    
    return governing

# ==========================================
# 3. REBAR DESIGN (Original)
# ==========================================
def design_rebar_detailed(Mu_kgm, b_cm, d_cm, fc, fy):
    """
    Calculate Rebar with Min/Max Checks (Used by tab_ddm.py internal logic)
    Returns: As_req, rho, note, status
    """
    # Min steel for slab (Shrinkage/Temperature rebar base on gross area)
    rho_min = 0.0018
    # Use approx h = d + 3.0 for min steel check area base
    h_est = d_cm + 3.0 
    As_min = rho_min * b_cm * h_est
    
    if Mu_kgm < 50: 
        return As_min, rho_min, "Min Steel", "OK"
    
    Mu = Mu_kgm * 100 # kg-cm
    phi = 0.90
    
    # Rn
    Rn = Mu / (phi * b_cm * d_cm**2)
    
    # Rho limits (ACI 318)
    # Determine beta1 for different concrete strengths
    if fc <= 280:
        beta1 = 0.85
    else:
        beta1 = max(0.65, 0.85 - 0.05 * (fc - 280) / 70)
        
    rho_b = 0.85 * beta1 * (fc/fy) * (6120/(6120+fy))
    rho_max = 0.75 * rho_b 
    
    try:
        term = 1 - (2*Rn)/(0.85*fc)
        if term < 0: 
            return 999, rho_max, "Section Too Small", "FAIL"
        rho_req = (0.85*fc/fy) * (1 - np.sqrt(term))
    except:
        return 999, rho_max, "Calc Error", "FAIL"
    
    # Compare with Min
    if rho_req < rho_min:
        rho_design = rho_min
        note = "Controls (Min Steel)"
    else:
        rho_design = rho_req
        note = "Controls (Flexure)"

    As_req = rho_design * b_cm * d_cm
    
    status = "OK"
    if rho_req > rho_max: 
        status = "FAIL"
        note = "Rho > Rho_max"
        
    return As_req, rho_design, note, status
