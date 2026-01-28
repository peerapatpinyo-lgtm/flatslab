import physics
import math

def run_design_cycle(lx, ly, h_init, c1_mm, c2_mm, fc_ksc, fy_ksc, sdl, ll, cover_mm, pos, dl_fac, ll_fac, main_bar_db):
    # 1. Setup
    u = physics.get_units()
    fc_mpa = fc_ksc * u['ksc_to_mpa']
    bar_area = physics.get_bar_properties(main_bar_db)
    
    c1 = c1_mm / 1000.0
    c2 = c2_mm / 1000.0
    ln = max(lx - c1, 0.65 * lx)
    
    # 2. Thickness Loop
    h_min_val, h_denom = physics.get_min_thickness_limit(ln, pos)
    h_current = h_init
    max_h = 1500
    
    while h_current <= max_h:
        # Properties
        # d depends on cover and bar size (d = h - cov - db/2)
        d_mm = h_current - cover_mm - (main_bar_db / 2.0)
        d_m = d_mm / 1000.0
        
        # Loads
        sw = (h_current / 1000.0) * physics.CONCRETE_DENSITY
        qu = (dl_fac * (sw + sdl)) + (ll_fac * ll)
        
        # Shear
        bo_m, acrit, alpha, beta = physics.get_geometry(c1, c2, d_m, pos)
        v1, v2, v3 = physics.get_vc_stress(fc_mpa, beta, alpha, d_m, bo_m)
        vc_mpa = min(v1, v2, v3)
        
        # Check
        phi = 0.75
        vc_newton = vc_mpa * (bo_m * 1000) * d_mm
        phi_vc_kg = (phi * vc_newton) / u['grav']
        
        gamma_v = physics.get_gamma_v(pos)
        vu_kg = qu * ((lx * ly) - acrit) * gamma_v
        
        ratio = vu_kg / phi_vc_kg if phi_vc_kg > 0 else 999
        
        if ratio <= 1.0 and h_current >= h_min_val:
            break
            
        h_current += 10
        
    reason = "Design Satisfied" if ratio <= 1.0 else "Shear Limit Reached"

    # 3. Flexure Design & Detailing
    mo = (qu * ly * ln**2) / 8
    
    # As Min (Temperature & Shrinkage)
    # As_min = 0.0018 * b * h (where b=100cm, h in cm)
    # Result in cm2 per meter
    as_min = 0.0018 * 100 * (h_current / 10.0)
    
    strips_config = [
        ("Column Strip Top (-)", 0.49),
        ("Column Strip Bot (+)", 0.21),
        ("Middle Strip Top (-)", 0.16),
        ("Middle Strip Bot (+)", 0.14)
    ]
    
    rebar_data = []
    d_cm = d_mm / 10.0
    
    for name, coeff in strips_config:
        mu = coeff * mo
        # As_req calculation
        denom_val = 0.9 * fy_ksc * 0.9 * d_cm
        as_req = (mu * 100) / denom_val # 100 to convert kg-m to kg-cm
        
        # Compare with Min
        as_design = max(as_req, as_min)
        
        # Spacing Calculation
        # Spacing = (100 * bar_area) / As_design
        if as_design > 0:
            theo_spacing = (100.0 * bar_area) / as_design
            # Round down to nearest 2.5 cm for construction practicality (max 30cm)
            use_spacing = math.floor(theo_spacing / 2.5) * 2.5
            use_spacing = min(use_spacing, 30.0)
            use_spacing = max(use_spacing, 5.0) # Min spacing 5cm
        else:
            theo_spacing = 30.0
            use_spacing = 30.0
            
        rebar_data.append({
            "name": name,
            "coeff": coeff,
            "mu": mu,
            "as_req": as_req,
            "as_design": as_design,
            "theo_spacing": theo_spacing,
            "use_spacing": use_spacing,
            "is_min_gov": as_min > as_req
        })

    return {
        "inputs": {
            "lx": lx, "ly": ly, "c1": c1, "c2": c2, "pos": pos,
            "sw": sw, "sdl": sdl, "ll": ll, "qu": qu,
            "fc_mpa": fc_mpa, "fy": fy_ksc, "h_denom": h_denom,
            "h_init": h_init, "main_bar_db": main_bar_db, 
            "bar_area": bar_area
        },
        "results": {
            "h": h_current, "h_min": h_min_val, "reason": reason,
            "d_mm": d_mm, "bo_mm": bo_m*1000, "acrit": acrit,
            "v1": v1, "v2": v2, "v3": v3, "vc_mpa": vc_mpa,
            "phi_vc_kg": phi_vc_kg, "vu_kg": vu_kg, 
            "qu": qu, "gamma_v": gamma_v, "ratio": ratio, 
            "mo": mo, "ln": ln, "as_min": as_min
        },
        "rebar": rebar_data
    }
