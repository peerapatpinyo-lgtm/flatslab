import physics
import math

def run_design_cycle(lx, ly, h_init, c1_mm, c2_mm, fc_ksc, fy_ksc, sdl, ll, cover_mm, pos, dl_fac, ll_fac):
    # 1. Unit Setup
    fc_mpa = fc_ksc * 0.0980665
    c1 = c1_mm / 1000.0
    c2 = c2_mm / 1000.0
    
    # 2. Load Loop (Iterate h until pass or limit)
    current_h = h_init
    max_h = 600
    
    while current_h <= max_h:
        # Prep
        d_mm = current_h - cover_mm - 8 # assume db16/2
        d_m = d_mm / 1000.0
        
        # Physics: Geometry
        bo_m, acrit_m2, alpha_s, beta = physics.get_geometry_properties(c1, c2, d_m, pos)
        
        # Physics: Loads
        sw = (current_h / 1000.0) * 2400
        qu = (dl_fac * (sw + sdl)) + (ll_fac * ll)
        
        # Physics: Capacities (MPa)
        v1, v2, v3, vc_mpa = physics.calc_aci_shear_capacity(fc_mpa, beta, alpha_s, d_m, bo_m)
        
        # Forces (Convert MPa to kg force for comparison)
        # Phi * Vc (N) = 0.75 * Vc(MPa) * bo(mm) * d(mm)
        phi_vc_newton = 0.75 * vc_mpa * (bo_m * 1000) * (d_mm)
        phi_vc_kg = phi_vc_newton / 9.80665
        
        # Demand (Vu)
        unbalanced = 1.15 if pos in ["Edge", "Corner"] else 1.0
        vu_kg = qu * ((lx * ly) - acrit_m2) * unbalanced
        
        ratio = vu_kg / phi_vc_kg
        
        if ratio <= 0.95 or current_h >= max_h:
            # Found result
            break
        
        current_h += 10 # Step up

    # 3. Flexure (Mo)
    ln = max(lx - c1, 0.65 * lx)
    mo = (qu * ly * ln**2) / 8
    
    # 4. Rebar (Sample CS Negative)
    mu_cs_neg = 0.4875 * mo
    # As = Mu / (0.9 fy 0.9 d)
    d_cm = d_mm / 10
    as_req = (mu_cs_neg * 100) / (0.9 * fy_ksc * 0.9 * d_cm)
    
    return {
        "inputs": {"sw": sw, "sdl": sdl, "ll": ll, "dl_fac": dl_fac, "ll_fac": ll_fac, "fc_mpa": fc_mpa, "fy": fy_ksc, "lx": lx, "ly": ly, "ln": ln},
        "results": {
            "h": current_h, "d_mm": d_mm, "bo_mm": bo_m*1000, "qu": qu, "mo": mo, 
            "vu_kg": vu_kg, "phi_vc_kg": phi_vc_kg, "ratio": ratio,
            "v1": v1, "v2": v2, "v3": v3, "vc_mpa": vc_mpa,
            "alpha_s": alpha_s, "beta": beta,
            "mu_cs_neg": mu_cs_neg, "as_cs_neg": as_req
        }
    }
