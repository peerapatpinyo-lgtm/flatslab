import physics
import math

def run_design_cycle(lx, ly, h_init, c1_mm, c2_mm, fc_ksc, fy_ksc, sdl, ll, cover_mm, pos, dl_fac, ll_fac):
    # 1. Unit Setup & Constants
    fc_mpa = fc_ksc * 0.0980665
    c1 = c1_mm / 1000.0
    c2 = c2_mm / 1000.0
    ln = max(lx - c1, 0.65 * lx) # Clear span
    
    # 2. Minimum Thickness Requirement
    h_min_aci = physics.get_min_thickness_aci(ln, pos)
    
    # 3. Main Design Loop (Find h)
    current_h = h_init
    max_h = 600
    
    while current_h <= max_h:
        # Prep Loop Variables
        d_mm = current_h - cover_mm - 8 # assume db16/2 approx
        d_m = d_mm / 1000.0
        
        # --- Physics Calls ---
        # 3.1 Load
        sw = (current_h / 1000.0) * 2400
        qu = (dl_fac * (sw + sdl)) + (ll_fac * ll)
        
        # 3.2 Geometry & Shear
        bo_m, acrit_m2, alpha_s, beta = physics.get_geometry_properties(c1, c2, d_m, pos)
        v1, v2, v3, vc_mpa = physics.calc_aci_shear_capacity(fc_mpa, beta, alpha_s, d_m, bo_m)
        
        # 3.3 Forces Check
        phi = 0.75
        phi_vc_n = phi * vc_mpa * (bo_m * 1000) * (d_mm) # N
        phi_vc_kg = phi_vc_n / 9.80665
        
        unbalanced_factor = physics.get_unbalanced_factor(pos)
        vu_kg = qu * ((lx * ly) - acrit_m2) * unbalanced_factor
        
        ratio = vu_kg / phi_vc_kg if phi_vc_kg > 0 else 999
        
        # 3.4 Convergence Check
        # ต้องผ่านทั้ง Shear Ratio <= 1.0 (safety check) 
        # และ ความหนาต้องมากกว่า ACI Min Thickness (deflection check)
        if (ratio <= 1.0) and (current_h >= h_min_aci):
            break
        
        current_h += 10 # Step up logic
        
        if current_h > max_h:
            break # Prevent infinite loop

    # --- 4. Flexural Design (Moment & Rebar) ---
    mo = (qu * ly * ln**2) / 8
    d_cm = d_mm / 10
    
    # Define Coefficients (Approx DDM distribution for Interior Panel)
    # Total Static Moment Mo
    # CS Neg (75% of 65%) = 0.4875
    # CS Pos (60% of 35%) = 0.21
    # MS Neg (25% of 65%) = 0.1625
    # MS Pos (40% of 35%) = 0.14
    
    rebar_strips = [
        {"name": "Col. Strip Negative", "coeff": 0.4875, "loc": "Top"},
        {"name": "Col. Strip Positive", "coeff": 0.2100, "loc": "Bot"},
        {"name": "Mid. Strip Negative", "coeff": 0.1625, "loc": "Top"},
        {"name": "Mid. Strip Positive", "coeff": 0.1400, "loc": "Bot"},
    ]
    
    rebar_results = []
    for strip in rebar_strips:
        mu = strip['coeff'] * mo
        # As = Mu / (0.9 * fy * 0.9 * d)
        as_req = (mu * 100) / (0.9 * fy_ksc * 0.9 * d_cm)
        
        rebar_results.append({
            "name": strip['name'],
            "loc": strip['loc'],
            "coeff": strip['coeff'],
            "mu": mu,
            "as_req": as_req
        })

    # --- 5. Pack Results ---
    return {
        "inputs": {
            "lx": lx, "ly": ly, "ln": ln,
            "sw": sw, "sdl": sdl, "ll": ll, "dl_fac": dl_fac, "ll_fac": ll_fac,
            "fc_mpa": fc_mpa, "fy": fy_ksc
        },
        "results": {
            "h": current_h, "d_mm": d_mm, "bo_mm": bo_m*1000, 
            "qu": qu, "mo": mo, 
            "vu_kg": vu_kg, "phi_vc_kg": phi_vc_kg, "ratio": ratio,
            "v1": v1, "v2": v2, "v3": v3, "vc_mpa": vc_mpa,
            "alpha_s": alpha_s, "beta": beta,
            "unbalanced_factor": unbalanced_factor,
            "h_min_aci": h_min_aci
        },
        "rebar": rebar_results
    }
