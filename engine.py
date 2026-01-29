import physics
import math

# สังเกตตัวแปรสุดท้ายคือ continuity
def analyze_structure(lx, ly, h_init, c1_mm, c2_mm, fc_ksc, fy_ksc, sdl, ll, cover_mm, pos, dl_fac, ll_fac, est_bar_db, continuity):
    """
    Phase 1: Structural Analysis & Geometry
    """
    u = physics.get_units()
    fc_mpa = fc_ksc * u['ksc_to_mpa']
    
    c1 = c1_mm / 1000.0
    c2 = c2_mm / 1000.0
    
    # Calculate Clear Spans
    ln_x = max(lx - c1, 0.65 * lx)
    ln_y = max(ly - c2, 0.65 * ly)
    ln = ln_x 
    
    # --- Thickness Design Loop ---
    h_min_val, h_denom = physics.get_min_thickness_limit(ln, pos)
    h_current = h_init
    max_h = 1500
    
    while h_current <= max_h:
        # Assume d based on estimated bar
        d_mm = h_current - cover_mm - (est_bar_db / 2.0)
        d_m = d_mm / 1000.0
        
        sw = (h_current / 1000.0) * physics.CONCRETE_DENSITY
        qu = (dl_fac * (sw + sdl)) + (ll_fac * ll)
        
        # Shear Check
        bo_m, acrit, alpha, beta, bo_str = physics.get_geometry(c1, c2, d_m, pos)
        v1, v2, v3 = physics.get_vc_stress(fc_mpa, beta, alpha, d_m, bo_m)
        vc_mpa = min(v1, v2, v3)
        
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
    
    # --- Base Moment Calculation ---
    mo = (qu * ly * ln**2) / 8
    
    return {
        "inputs": {
            "lx": lx, "ly": ly, "c1": c1, "c2": c2, "pos": pos,
            "sw": sw, "sdl": sdl, "ll": ll, "qu": qu,
            "fc_mpa": fc_mpa, "fy": fy_ksc, "h_denom": h_denom,
            "h_init": h_init, "dl_fac": dl_fac, "ll_fac": ll_fac,
            "cover_mm": cover_mm, "continuity": continuity
        },
        "results": {
            "h": h_current, "h_min": h_min_val, "reason": reason,
            "d_mm": d_mm, "bo_mm": bo_m*1000, "acrit": acrit,
            "v1": v1, "v2": v2, "v3": v3, "vc_mpa": vc_mpa,
            "phi_vc_kg": phi_vc_kg, "vu_kg": vu_kg, 
            "qu": qu, "gamma_v": gamma_v, "ratio": ratio, 
            "mo": mo, "ln": ln, "ln_x": ln_x, "ln_y": ln_y,
            "bo_str": bo_str
        }
    }

def verify_reinforcement(base_data, user_top_db, user_top_spacing, user_bot_db, user_bot_spacing):
    """
    Phase 2: Professional Verification (ACI 318 Checks)
    """
    r = base_data['results']
    i = base_data['inputs']
    
    h = r['h']
    d_avg = r['d_mm']
    mo = r['mo']
    fy = i['fy']
    continuity = i['continuity']
    
    # As Min (Temperature & Shrinkage)
    as_min = 0.0018 * 100 * (h / 10.0)
    
    # Get coefficients dynamically
    cs_neg, cs_pos = physics.get_moment_distribution(continuity, "Column Strip")
    ms_neg, ms_pos = physics.get_moment_distribution(continuity, "Middle Strip")
    
    strips_config = [
        ("Column Strip Top (-)", cs_neg, "top"),
        ("Column Strip Bot (+)", cs_pos, "bot"),
        ("Middle Strip Top (-)", ms_neg, "top"),
        ("Middle Strip Bot (+)", ms_pos, "bot")
    ]
    
    rebar_detailed = []
    
    for name, coeff, side in strips_config:
        # 1. Demand
        mu = coeff * mo
        d_cm = d_avg / 10.0 
        denom_val = 0.9 * fy * 0.9 * d_cm
        as_req_calc = (mu * 100) / denom_val 
        
        as_target = max(as_req_calc, as_min)
        
        # 2. User Provision
        if side == "top":
            sel_db = user_top_db
            sel_spacing = user_top_spacing
        else:
            sel_db = user_bot_db
            sel_spacing = user_bot_spacing
            
        bar_area = physics.get_bar_area(sel_db)
        as_provided = (bar_area * 1000) / sel_spacing
        
        # 3. Professional Checks
        status_msgs = []
        is_safe = True
        
        # Check A: Area
        if as_provided < as_target:
            status_msgs.append("FAIL: Insufficient As")
            is_safe = False
            
        # Check B: Max Spacing
        max_s = min(2 * h, 300) 
        if sel_spacing > max_s:
            status_msgs.append(f"FAIL: Spacing > Max ({max_s}mm)")
            is_safe = False
            
        # Check C: Congestion
        if sel_spacing < 75:
            status_msgs.append("WARN: Congested")
            
        if is_safe:
            status = "SAFE"
            color = "green"
            if "WARN" in str(status_msgs):
                status = "SAFE (Congested)"
                color = "orange"
        else:
            status = " / ".join(status_msgs)
            color = "red"
            
        rebar_detailed.append({
            "name": name,
            "coeff": coeff,
            "mu": mu,
            "as_req_calc": as_req_calc,
            "as_min": as_min,
            "as_target": as_target,
            "side": side,
            "user_db": sel_db,
            "user_spacing": sel_spacing,
            "bar_area": bar_area,
            "as_provided": as_provided,
            "status": status,
            "color": color,
            "max_spacing": max_s
        })
        
    return {
        "rebar_verified": rebar_detailed,
        "as_min": as_min
    }
