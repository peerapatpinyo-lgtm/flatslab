import numpy as np

def calculate_detailed_slab(lx, ly, h_mm, c1_mm, c2_mm, fc_ksc, fy_ksc, sdl, ll, cover_mm, pos="Interior"):
    # --- 1. การเตรียมข้อมูลและหน่วย ---
    h = h_mm / 1000
    c1 = c1_mm / 1000
    c2 = c2_mm / 1000
    d = (h_mm - cover_mm - 12) / 1000
    fc_mpa = fc_ksc * 0.0980665
    g = 9.80665

    # --- 2. Loading Detailed ---
    sw = h * 2400
    w_dl_factored = 1.2 * (sw + sdl)
    w_ll_factored = 1.6 * ll
    qu = w_dl_factored + w_ll_factored

    # --- 3. Geometry & Mo ---
    ln = max(lx - c1, 0.65 * lx)
    mo = (qu * ly * (ln**2)) / 8

    # --- 4. Punching Shear Check (Governing Case) ---
    def get_punching_data(temp_h_mm):
        t_h = temp_h_mm / 1000
        t_d = (temp_h_mm - cover_mm - 12) / 1000
        
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
        # 3 Formulas in MPa
        v1 = 0.33 * np.sqrt(fc_mpa)
        v2 = 0.17 * (1 + 2/beta) * np.sqrt(fc_mpa)
        v3 = 0.083 * (2 + (alpha_s * t_d / bo)) * np.sqrt(fc_mpa)
        vc_mpa = min(v1, v2, v3)
        
        vu_kg = qu * ((lx * ly) - a_crit)
        phi_vc_kg = (0.75 * vc_mpa * (bo * 1000 * t_d * 1000)) / g
        
        return {
            "vu": vu_kg, "phi_vc": phi_vc_kg, "bo": bo, "d": t_d,
            "v1": v1, "v2": v2, "v3": v3, "vc_mpa": vc_mpa, "beta": beta
        }

    # Search for safe thickness
    current_h = h_mm
    while True:
        p = get_punching_data(current_h)
        if p['vu'] <= p['phi_vc'] or current_h >= 600:
            break
        current_h += 10

    # --- 5. Rebar Calculation ---
    as_min = 0.0018 * 100 * (current_h / 10)
    phi_flex = 0.9
    m_coeffs = {"CS_Neg": 0.75*0.65, "MS_Neg": 0.25*0.65, "CS_Pos": 0.60*0.35, "MS_Pos": 0.40*0.35}
    
    rebar_out = {}
    for key, coeff in m_coeffs.items():
        m_strip = coeff * mo
        # Simple flexure: As = M / (phi * fy * 0.9d)
        as_req = (m_strip * 100) / (phi_flex * fy_ksc * (p['d'] * 100 * 0.9))
        as_final = max(as_req / ly, as_min)
        rebar_out[key] = as_final

    return {
        "loading": {"dl_fact": w_dl_factored, "ll_fact": w_ll_factored, "qu": qu, "sw": sw},
        "geo": {"ln": ln, "beta": p['beta'], "bo": p['bo'], "d": p['d']},
        "punching": p,
        "mo": mo,
        "h_final": current_h,
        "rebar": rebar_out,
        "as_min": as_min
    }
