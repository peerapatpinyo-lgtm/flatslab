import physics
import math

def run_design_cycle(lx, ly, h_init, c1_mm, c2_mm, fc_ksc, fy_ksc, sdl, ll, cover_mm, pos, dl_fac, ll_fac):
    # 1. Constants & Units
    u = physics.get_units()
    fc_mpa = fc_ksc * u['ksc_mpa']
    
    # 2. Geometry Setup
    c1 = c1_mm / 1000.0
    c2 = c2_mm / 1000.0
    ln = max(lx - c1, 0.65 * lx) # Clear Span
    
    # 3. Min Thickness
    h_min_exact = physics.get_min_thickness(ln, pos)
    h_min_practical = math.ceil(h_min_exact / 10.0) * 10
    
    # 4. Iteration Loop
    h_current = h_init
    max_h = 1000
    
    while h_current <= max_h:
        # 4.1 Properties
        d_mm = h_current - cover_mm - 8 # Assume db16 approx
        d_m = d_mm / 1000.0
        
        # 4.2 Loads
        sw = (h_current / 1000.0) * physics.CONCRETE_DENSITY
        qu = (dl_fac * (sw + sdl)) + (ll_fac * ll)
        
        # 4.3 Shear Physics
        bo_m, acrit, alpha, beta = physics.get_geometry_properties(c1, c2, d_m, pos)
        v1, v2, v3, vc_mpa = physics.calc_aci_shear_capacity(fc_mpa, beta, alpha, d_m, bo_m)
        
        # 4.4 Shear Check
        # Capacity in Newton -> kg
        # Force (N) = Stress(MPa) * Area(mm2)
        vc_newton = vc_mpa * (bo_m * 1000) * d_mm 
        phi = 0.75
        phi_vc_kg = (phi * vc_newton) / u['grav']
        
        # Demand
        gamma_v = physics.get_unbalanced_factor(pos)
        vu_kg = qu * ((lx * ly) - acrit) * gamma_v
        
        ratio = vu_kg / phi_vc_kg if phi_vc_kg > 0 else 999
        
        # Break Condition: Pass Shear AND Pass Min Thickness
        if (ratio <= 1.0) and (h_current >= h_min_exact):
            break
            
        h_current += 10
        
    # 5. Logic Reason
    if h_current == h_init:
        reason = "Input Satisfactory"
    elif h_current <= h_min_practical + 10 and ratio <= 1.0:
        reason = "ACI Min. Thickness Limit"
    else:
        reason = "Punching Shear Requirement"

    # 6. Flexural Design (Complete 4 Strips)
    mo = (qu * ly * ln**2) / 8 # Static Moment
    d_cm = d_mm / 10.0
    
    # Strip Coefficients (ACI Direct Design Method approx)
    strips_config = [
        ("Column Strip Top (-)", 0.49), # Approx for Int/Ext avg
        ("Column Strip Bot (+)", 0.21),
        ("Middle Strip Top (-)", 0.16),
        ("Middle Strip Bot (+)", 0.14)
    ]
    
    rebar_data = []
    for name, coeff in strips_config:
        mu = coeff * mo # kg-m
        # As = Mu / (phi * fy * j * d)
        # Mu(kg-m) * 100 -> kg-cm
        # phi=0.9, j=0.9 approx
        as_req = (mu * 100) / (0.9 * fy_ksc * 0.9 * d_cm)
        
        rebar_data.append({
            "name": name, 
            "coeff": coeff, 
            "mu": mu, 
            "as_req": as_req,
            "d_cm": d_cm
        })

    return {
        "inputs": {
            "lx": lx, "ly": ly, "c1_mm": c1_mm, "c2_mm": c2_mm, 
            "pos": pos, "sw": sw, "sdl": sdl, "ll": ll, 
            "dl_fac": dl_fac, "ll_fac": ll_fac, "fc_mpa": fc_mpa, "fy": fy_ksc, 
            "cover": cover_mm, "h_init": h_init
        },
        "results": {
            "h": h_current, "h_min_code": h_min_exact, "reason": reason,
            "d_mm": d_mm, "bo_mm": bo_m * 1000, 
            "acrit": acrit, 
            "qu": qu, "mo": mo, "ln": ln,
            "vu_kg": vu_kg, 
            "vc_gov_mpa": vc_mpa, "vc_newton": vc_newton, "phi_vc_kg": phi_vc_kg,
            "ratio": ratio,
            "v1": v1, "v2": v2, "v3": v3, "beta": beta, "alpha": alpha,
            "gamma_v": gamma_v
        },
        "rebar": rebar_data
    }
