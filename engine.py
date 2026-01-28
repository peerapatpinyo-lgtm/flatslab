import physics
import math

def run_design_cycle(lx, ly, h_init, c1_mm, c2_mm, fc_ksc, fy_ksc, sdl, ll, cover_mm, pos, dl_fac, ll_fac):
    # 1. Setup Units & Geometry
    u = physics.get_units()
    fc_mpa = fc_ksc * u['ksc_to_mpa']
    
    c1 = c1_mm / 1000.0
    c2 = c2_mm / 1000.0
    ln = max(lx - c1, 0.65 * lx)
    
    # 2. Minimum Thickness Requirement
    h_min_val, h_denom = physics.get_min_thickness_limit(ln, pos)
    h_min_practical = math.ceil(h_min_val / 10.0) * 10
    
    # 3. Design Loop
    h_current = h_init
    max_h = 1500
    
    while h_current <= max_h:
        # 3.1 Derived Properties
        d_mm = h_current - cover_mm - 10 
        d_m = d_mm / 1000.0
        
        # 3.2 Loads
        sw = (h_current / 1000.0) * physics.CONCRETE_DENSITY
        qu = (dl_fac * (sw + sdl)) + (ll_fac * ll)
        
        # 3.3 Shear Parameters
        bo_m, acrit, alpha, beta = physics.get_geometry(c1, c2, d_m, pos)
        v1, v2, v3 = physics.get_vc_stress(fc_mpa, beta, alpha, d_m, bo_m)
        vc_mpa = min(v1, v2, v3)
        
        # 3.4 Capacity (MPa -> Tons)
        phi = 0.75
        vc_newton = vc_mpa * (bo_m * 1000) * d_mm
        phi_vc_ton = (phi * vc_newton) / (u['grav'] * 1000)
        phi_vc_kg = phi_vc_ton * 1000
        
        # 3.5 Demand
        gamma_v = physics.get_gamma_v(pos)
        area_load = (lx * ly) - acrit
        vu_kg = qu * area_load * gamma_v
        
        ratio = vu_kg / phi_vc_kg if phi_vc_kg > 0 else 999
        
        # 3.6 Check
        if ratio <= 1.0 and h_current >= h_min_val:
            break
            
        h_current += 10
        
    # Reason
    if h_current == h_init:
        reason = "Input Satisfactory"
    elif h_current <= h_min_practical + 10 and ratio <= 1.0:
        reason = "ACI Min Thickness"
    else:
        reason = "Shear Requirement"

    # 4. Flexure
    mo = (qu * ly * ln**2) / 8
    strips = [
        ("Column Strip Top (-)", 0.49),
        ("Column Strip Bot (+)", 0.21),
        ("Middle Strip Top (-)", 0.16),
        ("Middle Strip Bot (+)", 0.14)
    ]
    
    rebar_data = []
    d_cm = d_mm / 10.0
    for name, coeff in strips:
        mu = coeff * mo
        as_req = (mu * 100000) / (0.9 * fy_ksc * 0.9 * d_cm)
        rebar_data.append({
            "name": name, "coeff": coeff, "mu": mu, "as_req": as_req
        })

    return {
        "inputs": {
            "lx": lx, "ly": ly, "c1": c1, "c2": c2, "pos": pos,
            "sw": sw, "sdl": sdl, "ll": ll, "qu": qu,
            "fc_mpa": fc_mpa, "fy": fy_ksc, "h_denom": h_denom,
            "h_init": h_init
        },
        "results": {
            "h": h_current, "h_min": h_min_val, "reason": reason,
            "d_mm": d_mm, "bo_mm": bo_m*1000, "acrit": acrit,
            "v1": v1, "v2": v2, "v3": v3, "vc_mpa": vc_mpa,
            "vc_newton": vc_newton,
            "phi_vc_kg": phi_vc_kg, "vu_kg": vu_kg, 
            "gamma_v": gamma_v, # <--- ตรวจสอบว่าบรรทัดนี้มีอยู่
            "qu": qu,           # <--- เพิ่มบรรทัดนี้เพื่อให้ report เรียกใช้ได้
            "ratio": ratio, "mo": mo, "ln": ln
        },
        "rebar": rebar_data
    }
