import physics
import math

def run_design_cycle(lx, ly, h_init, c1_mm, c2_mm, fc_ksc, fy_ksc, sdl, ll, cover_mm, pos, dl_fac, ll_fac):
    # 1. Centralized Constants
    u = physics.get_units()
    
    # 2. Input Conversion
    fc_mpa = fc_ksc * u['ksc_mpa']
    c1 = c1_mm / 1000.0
    c2 = c2_mm / 1000.0
    ln = max(lx - c1, 0.65 * lx)
    
    # 3. Design Loop (Iterate h)
    h_current = h_init
    max_h = 1000
    h_min_code = physics.get_min_thickness(ln, pos)
    
    while h_current <= max_h:
        # 3.1 Derived Geometry
        d_mm = h_current - cover_mm - 8 # Assume db16 approx
        d_m = d_mm / 1000.0
        
        # 3.2 Load (Consistent h used here)
        sw = (h_current / 1000.0) * physics.CONCRETE_DENSITY
        qu = (dl_fac * (sw + sdl)) + (ll_fac * ll)
        
        # 3.3 Physics Calc
        bo_m, acrit, alpha, beta = physics.get_geometry_properties(c1, c2, d_m, pos)
        v1, v2, v3, vc_mpa = physics.calc_aci_shear_capacity(fc_mpa, beta, alpha, d_m, bo_m)
        
        # 3.4 Capacity & Demand (Force in kg)
        # Phi * Vc (Newton) -> kg
        phi = 0.75
        phi_vc_n = phi * vc_mpa * (bo_m * 1000) * (d_mm)
        phi_vc_kg = phi_vc_n / u['grav']
        
        gamma_v = physics.get_unbalanced_factor(pos)
        vu_kg = qu * ((lx * ly) - acrit) * gamma_v
        
        ratio = vu_kg / phi_vc_kg if phi_vc_kg > 0 else 999
        
        # 3.5 Check
        if (ratio <= 1.0) and (h_current >= h_min_code):
            break
            
        h_current += 10
        
    # 4. Flexural Calculation (All 4 Strips)
    mo = (qu * ly * ln**2) / 8
    d_cm = d_mm / 10.0
    
    strips_config = [
        ("Col. Strip Top (-)", 0.4875, "Top"),
        ("Col. Strip Bot (+)", 0.2100, "Bot"),
        ("Mid. Strip Top (-)", 0.1625, "Top"),
        ("Mid. Strip Bot (+)", 0.1400, "Bot")
    ]
    
    rebar_data = []
    for name, coeff, loc in strips_config:
        mu = coeff * mo
        as_req = (mu * 100) / (0.9 * fy_ksc * 0.9 * d_cm)
        rebar_data.append({
            "name": name, "coeff": coeff, "mu": mu, "as_req": as_req
        })

    # 5. Pack Data
    return {
        "inputs": {
            "lx": lx, "ly": ly, "c1_mm": c1_mm, "c2_mm": c2_mm, 
            "pos": pos, "sw": sw, "sdl": sdl, "ll": ll, 
            "dl_fac": dl_fac, "ll_fac": ll_fac, "fc_mpa": fc_mpa, "fy": fy_ksc, 
            "cover": cover_mm  # <--- จุดสำคัญ: ต้องส่งค่านี้กลับมาด้วย
        },
        "results": {
            "h": h_current, "d_mm": d_mm, "bo_mm": bo_m * 1000,
            "qu": qu, "mo": mo, "ln": ln,
            "vu_kg": vu_kg, "phi_vc_kg": phi_vc_kg, "ratio": ratio,
            "v1": v1, "v2": v2, "v3": v3, "beta": beta, "alpha": alpha,
            "acrit": acrit, "gamma_v": gamma_v
        },
        "rebar": rebar_data
    }
