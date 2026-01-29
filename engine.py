import math

GRAV = 9.80665
CONCRETE_DENSITY = 2400 

def run_analysis(lx, ly, h_mm, c1_mm, c2_mm, sdl, ll, fc_ksc, fy_ksc, cover_mm, pos, top_db, top_sp, bot_db, bot_sp):
    # 1. Units
    fc_mpa = fc_ksc * 0.0980665
    
    # 2. Geometry & d
    avg_db = (top_db + bot_db) / 2.0
    d_mm = h_mm - cover_mm - avg_db
    
    # 3. Loads
    sw = (h_mm / 1000.0) * CONCRETE_DENSITY
    dl = sw + sdl
    qu = (1.4 * dl) + (1.7 * ll)
    
    # 4. Shear
    b1 = c1_mm + d_mm
    b2 = c2_mm + d_mm
    
    if pos == "Interior":
        bo = 2 * (b1 + b2)
        alpha_s = 40
    elif pos == "Edge":
        bo = (2 * b1) + b2
        alpha_s = 30
    else: # Corner
        bo = b1 + b2
        alpha_s = 20
        
    beta = max(c1_mm, c2_mm) / min(c1_mm, c2_mm)
    
    # Vc (Newtons)
    vc1 = 0.33 * math.sqrt(fc_mpa) * bo * d_mm
    vc2 = 0.17 * (1 + (2/beta)) * math.sqrt(fc_mpa) * bo * d_mm
    vc3 = 0.083 * ((alpha_s * d_mm / bo) + 2) * math.sqrt(fc_mpa) * bo * d_mm
    
    vc_n = min(vc1, vc2, vc3)
    phi_vc_kg = (0.75 * vc_n) / GRAV
    
    # Vu (kg)
    area_load = (lx * ly) - ((c1_mm/1000)*(c2_mm/1000))
    vu_kg = qu * area_load
    
    # 5. Flexure (Simplified for Demo)
    ln = lx - (c1_mm/1000)
    mo = (qu * ly * ln**2) / 8
    mu_top = mo * 0.65 * 0.75
    mu_bot = mo * 0.35 * 0.60
    
    # 6. Rebar Check Logic
    def check_bar(mu, db, sp, d_val):
        d_cm = d_val / 10.0
        as_req = (mu * 100) / (0.9 * fy_ksc * 0.9 * d_cm)
        as_min = 0.0018 * 100 * (h_mm / 10.0)
        area_bar = (math.pi * (db/2)**2) / 100
        as_prov = (area_bar * 1000) / sp
        status = "SAFE" if (as_prov >= max(as_req, as_min)) else "FAIL"
        return mu, as_req, as_min, as_prov, status

    res_top = check_bar(mu_top, top_db, top_sp, d_mm)
    res_bot = check_bar(mu_bot, bot_db, bot_sp, d_mm)

    return {
        "inputs": {
            "h": h_mm, "sdl": sdl, "ll": ll, "fc": fc_ksc, "fy": fy_ksc,
            "c1": c1_mm, "c2": c2_mm, "cover": cover_mm, "pos": pos,
            "top_db": top_db, "top_sp": top_sp, "bot_db": bot_db, "bot_sp": bot_sp
        },
        "loads": { "sw": sw, "qu": qu },
        "shear": {
            "d_mm": d_mm, "bo": bo, "beta": beta, "alpha": alpha_s,
            "vc1": vc1, "vc2": vc2, "vc3": vc3, "vc_final": vc_n,
            "phi_vc_kg": phi_vc_kg, "vu_kg": vu_kg
        },
        "flexure": { "mo": mo, "top": res_top, "bot": res_bot }
    }
