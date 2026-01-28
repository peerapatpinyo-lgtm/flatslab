import physics
import math

def run_design_cycle(lx, ly, h_init, c1_mm, c2_mm, fc_ksc, fy_ksc, sdl, ll, cover_mm, pos, dl_fac, ll_fac):
    # 1. Constants
    u = physics.get_units()
    
    # 2. Input Conversion
    fc_mpa = fc_ksc * u['ksc_mpa']
    c1 = c1_mm / 1000.0
    c2 = c2_mm / 1000.0
    ln = max(lx - c1, 0.65 * lx)
    
    # 3. Determine Min Thickness Code Requirement
    # ln is in meters, returns mm
    h_min_exact = physics.get_min_thickness(ln, pos) 
    
    # Round h_min_exact to nearest 10mm ceiling for practical construction
    h_min_practical = math.ceil(h_min_exact / 10.0) * 10
    
    # Start loop at max(h_init, h_min_practical) to save iterations
    # But we need to trace *why* it increases, so let's start at h_init and check.
    h_current = h_init
    max_h = 1000
    
    while h_current <= max_h:
        # 3.1 Derived Geometry
        d_mm = h_current - cover_mm - 8 # Assume db16 approx
        d_m = d_mm / 1000.0
        
        # 3.2 Load (Recalculate SW with current h)
        sw = (h_current / 1000.0) * physics.CONCRETE_DENSITY
        qu = (dl_fac * (sw + sdl)) + (ll_fac * ll)
        
        # 3.3 Physics Calc
        bo_m, acrit, alpha, beta = physics.get_geometry_properties(c1, c2, d_m, pos)
        v1, v2, v3, vc_mpa = physics.calc_aci_shear_capacity(fc_mpa, beta, alpha, d_m, bo_m)
        
        # 3.4 Capacity & Demand
        phi = 0.75
        phi_vc_n = phi * vc_mpa * (bo_m * 1000) * (d_mm)
        phi_vc_kg = phi_vc_n / u['grav']
        
        gamma_v = physics.get_unbalanced_factor(pos)
        vu_kg = qu * ((lx * ly) - acrit) * gamma_v
        
        ratio = vu_kg / phi_vc_kg if phi_vc_kg > 0 else 999
        
        # 3.5 Check Logic
        # Condition A: Punching Shear Pass?
        shear_pass = ratio <= 1.0
        # Condition B: Min Thickness Pass?
        min_h_pass = h_current >= h_min_exact
        
        if shear_pass and min_h_pass:
            break
            
        h_current += 10
        
    # 4. Determine Governing Reason (Traceability)
    if h_current == h_init:
        reason = "Input Satisfactory"
    elif h_current == h_min_practical:
         # If it stopped exactly at code min (and implies it passed shear)
        reason = "ACI Min. Thickness Limit"
    else:
        # If it went beyond code min, it must be Shear
        reason = "Punching Shear Requirement"

    # 5. Flexural Calculation
    mo = (qu * ly * ln**2) / 8
    d_cm = d_mm / 10.0
    
    strips_config = [
        ("Col. Strip Top (-)", 0.4875),
        ("Col. Strip Bot (+)", 0.2100),
        ("Mid. Strip Top (-)", 0.1625),
        ("Mid. Strip Bot (+)", 0.1400)
    ]
    
    rebar_data = []
    for name, coeff in strips_config:
        mu = coeff * mo
        as_req = (mu * 100) / (0.9 * fy_ksc * 0.9 * d_cm)
        rebar_data.append({
            "name": name, "coeff": coeff, "mu": mu, "as_req": as_req
        })

    return {
        "inputs": {
            "lx": lx, "ly": ly, "c1_mm": c1_mm, "c2_mm": c2_mm, 
            "pos": pos, "sw": sw, "sdl": sdl, "ll": ll, 
            "dl_fac": dl_fac, "ll_fac": ll_fac, "fc_mpa": fc_mpa, "fy": fy_ksc, 
            "cover": cover_mm, "h_init": h_init
        },
        "results": {
            "h": h_current, # <--- Final Design Thickness
            "h_min_code": h_min_exact,
            "reason": reason,
            "d_mm": d_mm, "bo_mm": bo_m * 1000,
            "qu": qu, "mo": mo, "ln": ln,
            "vu_kg": vu_kg, "phi_vc_kg": phi_vc_kg, "ratio": ratio,
            "v1": v1, "v2": v2, "v3": v3, "beta": beta, "alpha": alpha,
            "acrit": acrit, "gamma_v": gamma_v
        },
        "rebar": rebar_data
    }
