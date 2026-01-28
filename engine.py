import numpy as np

def calculate_detailed_slab(lx, ly, h_mm, c1_mm, c2_mm, fc_ksc, fy_ksc, sdl, ll, cover_mm, pos="Interior", dl_factor=1.2, ll_factor=1.6):
    # --- 1. Prepare Data & Unit Conversion ---
    h = h_mm / 1000.0
    c1 = c1_mm / 1000.0
    c2 = c2_mm / 1000.0
    # Effective depth (d) estimation: h - cover - 1/2 bar diameter (assume DB16 ~ 0.016m)
    d_est = (h_mm - cover_mm - 8) / 1000.0 
    
    fc_mpa = fc_ksc * 0.0980665
    g = 9.80665

    # --- 2. Minimum Thickness Check (ACI 318) ---
    ln_long = max(lx, ly) - c1
    # ACI Table 8.3.1.1
    if pos == "Interior":
        h_min_req = (ln_long * 1000) / 33
    else:
        h_min_req = (ln_long * 1000) / 30 # Conservative for Edge/Corner
        
    h_warning = ""
    if h_mm < h_min_req:
        h_warning = f"Warning: Thickness {h_mm} mm < ACI Min ({h_min_req:.0f} mm). Risk of Deflection."

    # --- 3. Load Logic (Service vs Ultimate) ---
    sw = h * 2400 # Concrete Density
    
    # 3.1 Service Load (Unfactored) - For Foundation & Deflection check
    w_service = (sw + sdl) + ll
    total_service_load_kg = w_service * (lx * ly)
    
    # 3.2 Factored Load (Ultimate) - For Strength Design
    w_dl_factored = dl_factor * (sw + sdl)
    w_ll_factored = ll_factor * ll
    qu = w_dl_factored + w_ll_factored
    
    tributary_area = lx * ly
    total_factored_load_kg = qu * tributary_area

    # --- 4. Moment Analysis (DDM) ---
    ln_calc = lx - c1
    ln = max(ln_calc, 0.65 * lx)
    mo = (qu * ly * (ln**2)) / 8

    # --- 5. Punching Shear Loop (Safety Oriented) ---
    # Unbalanced Moment Factor: Edge/Corner columns take more shear stress
    unbalanced_factor = 1.15 if pos in ["Edge", "Corner"] else 1.0
    
    def get_punching_data(temp_h_mm):
        t_h = temp_h_mm / 1000.0
        t_d = (temp_h_mm - cover_mm - 8) / 1000.0 # d average
        
        # Geometry Logic
        if pos == "Interior":
            bo = 2 * ((c1 + t_d) + (c2 + t_d))
            a_crit = (c1 + t_d) * (c2 + t_d)
            alpha_s = 40
        elif pos == "Edge":
            bo = (2 * (c1 + t_d/2)) + (c2 + t_d)
            a_crit = (c1 + t_d/2) * (c2 + t_d)
            alpha_s = 30
        else: # Corner
            bo = (c1 + t_d/2) + (c2 + t_d/2)
            a_crit = (c1 + t_d/2) * (c2 + t_d/2)
            alpha_s = 20

        beta = max(c1, c2) / min(c1, c2)
        
        # ACI Vc Formulas (MPa)
        v1 = 0.33 * np.sqrt(fc_mpa)
        v2 = 0.17 * (1 + 2/beta) * np.sqrt(fc_mpa)
        v3 = 0.083 * (2 + (alpha_s * t_d / bo)) * np.sqrt(fc_mpa)
        vc_mpa = min(v1, v2, v3)
        
        # Vu Calculation with Unbalanced Moment Magnification
        # Vu = qu * (TribArea - Acrit)
        vu_direct = qu * ((lx * ly) - a_crit)
        vu_design = vu_direct * unbalanced_factor # Magnified Shear
        
        # Phi Vc (kg)
        phi_vc_kg = (0.75 * vc_mpa * (bo * 1000 * t_d * 1000)) / g
        
        ratio = vu_design / phi_vc_kg if phi_vc_kg > 0 else 999
        
        return {
            "vu_direct": vu_direct, "vu_design": vu_design, "phi_vc": phi_vc_kg, 
            "bo": bo, "d": t_d, "vc_mpa": vc_mpa, "ratio": ratio,
            "v1":v1, "v2":v2, "v3":v3, "beta": beta, "acrit": a_crit
        }

    # Iterative Design: Target Ratio <= 0.90 for Safety Buffer
    current_h = h_mm
    while True:
        p = get_punching_data(current_h)
        if p['ratio'] <= 0.90 or current_h >= 600:
            break
        current_h += 10 # Increase step

    # --- 6. Rebar Calculation ---
    as_min = 0.0018 * 100 * (current_h / 10) # Temp & Shrinkage
    rebar_out = {}
    m_coeffs = {"CS_Neg": 0.4875, "MS_Neg": 0.1625, "CS_Pos": 0.21, "MS_Pos": 0.14}
    max_spacing_mm = min(300, 2 * current_h)
    
    # Using final d for rebar calc
    d_final = (current_h - cover_mm - 8) / 1000.0
    
    for key, coeff in m_coeffs.items():
        m_strip = coeff * mo
        # As = M / (phi * fy * 0.9d)
        as_req = (m_strip * 100) / (0.9 * fy_ksc * (d_final * 100 * 0.9))
        rebar_out[key] = max(as_req / ly, as_min)

    return {
        "loading": {
            "qu": qu, "sw": sw, "dl_fact": w_dl_factored, "ll_fact": w_ll_factored,
            "trib_area": tributary_area, 
            "service_load_kg": total_service_load_kg,
            "factored_load_kg": total_factored_load_kg,
            "factors": {"dl": dl_factor, "ll": ll_factor}
        },
        "geo": {"ln": ln, "ln_calc": ln_calc, "c1": c1, "bo": p['bo'], "d": p['d'], "h_min_req": h_min_req},
        "punching": p,
        "mo": mo,
        "h_final": current_h,
        "h_warning": h_warning,
        "rebar": rebar_out,
        "as_min": as_min,
        "max_spacing_cm": max_spacing_mm / 10,
        "ratio": p['ratio'],
        "unbalanced_factor": unbalanced_factor
    }
