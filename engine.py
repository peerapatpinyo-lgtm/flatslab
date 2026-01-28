import numpy as np

def calculate_detailed_slab(lx, ly, h_mm, c1_mm, c2_mm, fc_ksc, fy_ksc, sdl, ll, cover_mm, pos="Interior", dl_factor=1.2, ll_factor=1.6):
    # --- 1. Unit Conversion & Geometry ---
    h = h_mm / 1000.0
    c1 = c1_mm / 1000.0
    c2 = c2_mm / 1000.0
    d_effective = (h_mm - cover_mm - 8) / 1000.0  # d approx
    
    fc_mpa = fc_ksc * 0.0980665
    fy_mpa = fy_ksc * 0.0980665
    
    # --- 2. Loads ---
    sw = h * 2400 
    w_dl = sw + sdl
    qu = (dl_factor * w_dl) + (ll_factor * ll)
    
    # --- 3. Moment Analysis (Static Moment Mo) ---
    ln_calc = lx - c1
    ln = max(ln_calc, 0.65 * lx)
    mo = (qu * ly * (ln**2)) / 8
    
    # --- 4. Punching Shear (Detailed ACI) ---
    unbalanced_factor = 1.15 if pos in ["Edge", "Corner"] else 1.0
    
    def analyze_punching(curr_h):
        t_d = (curr_h - cover_mm - 8) / 1000.0
        
        # Geometry Constants
        if pos == "Interior":
            bo = 2 * ((c1 + t_d) + (c2 + t_d))
            alpha_s = 40
            beta = max(c1, c2) / min(c1, c2)
        elif pos == "Edge":
            bo = (2 * (c1 + t_d/2)) + (c2 + t_d)
            alpha_s = 30
            beta = max(c1, c2) / min(c1, c2)
        else: # Corner
            bo = (c1 + t_d/2) + (c2 + t_d/2)
            alpha_s = 20
            beta = 1.0 # Simplified for corner

        # ACI 318 VC Equations (MPa)
        vc1 = 0.33 * np.sqrt(fc_mpa)
        vc2 = 0.17 * (1 + 2/beta) * np.sqrt(fc_mpa)
        vc3 = 0.083 * (2 + (alpha_s * t_d / bo)) * np.sqrt(fc_mpa)
        vc_mpa = min(vc1, vc2, vc3)
        
        # Forces
        a_crit = (c1 + t_d) * (c2 + t_d) # Approximate Area inside shear perimeter
        vu_force = qu * ((lx * ly) - a_crit) * unbalanced_factor
        
        # Stress Check (Vu / phi*bo*d) vs Vc
        phi = 0.75
        vu_stress_mpa = vu_force / (phi * bo * t_d * 1000 * 1000) * 9.81 # Adjust units carefully
        # Or simpler: Compare Force
        phi_vc_force = phi * vc_mpa * (bo * 1000 * t_d * 1000) / 9.80665
        
        ratio = vu_force / phi_vc_force
        
        return {
            "bo": bo, "d": t_d, "beta": beta, "alpha_s": alpha_s,
            "vc1": vc1, "vc2": vc2, "vc3": vc3, "vc_mpa": vc_mpa,
            "vu_force": vu_force, "phi_vc_force": phi_vc_force,
            "ratio": ratio
        }

    # Iterative Design (Safety Target 0.9)
    current_h = h_mm
    while True:
        p = analyze_punching(current_h)
        if p['ratio'] <= 0.9 or current_h >= 600:
            break
        current_h += 10

    # --- 5. Rebar Detailed Calculation ---
    as_min = 0.0018 * 100 * (current_h / 10)
    rebar_data = []
    
    # Coefficients
    strips = [
        ("Column Strip (-)", "Top", 0.4875), # 0.65 * 0.75
        ("Column Strip (+)", "Bot", 0.21),   # 0.35 * 0.60
        ("Middle Strip (-)", "Top", 0.1625), # 0.65 * 0.25
        ("Middle Strip (+)", "Bot", 0.14)    # 0.35 * 0.40
    ]
    
    d_final = (current_h - cover_mm - 8) / 1000.0
    
    for name, layer, coeff in strips:
        m_u = coeff * mo
        # As = Mu / (0.9 * fy * 0.9d)
        as_req = (m_u * 100) / (0.9 * fy_ksc * 0.9 * d_final * 100)
        as_final = max(as_req / ly, as_min) # As per meter width? No, usually total As in strip width
        # Let's standardize to Total As required in the Strip Width (ly/2 or ly/4)
        # But for simplicity in this app, we usually show As/m or Total As.
        # Let's keep existing logic: As_total / Strip Width. 
        # Actually, simpler: Show As_total for the whole strip width.
        
        rebar_data.append({
            "name": name,
            "layer": layer,
            "mu": m_u,
            "coeff": coeff,
            "as_req": as_final # This is As per meter width assuming distributed
        })

    return {
        "inputs": {"lx":lx, "ly":ly, "c1":c1, "c2":c2, "fc":fc_mpa, "fy":fy_mpa, "dl_fac":dl_factor, "ll_fac":ll_factor, "sdl":sdl, "ll":ll, "sw":sw},
        "geo": {"ln": ln, "ln_calc": ln_calc, "d": d_final, "h": current_h},
        "loads": {"qu": qu, "mo": mo},
        "punching": p,
        "rebar": rebar_data,
        "ratio": p['ratio']
    }
