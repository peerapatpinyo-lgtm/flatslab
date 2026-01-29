import physics
import math

def run_full_analysis(
    lx, ly, h_user, c1_mm, c2_mm, lc_h, 
    sdl, ll, fc_ksc, fy_ksc, 
    cover_mm, pos, method, continuity, use_cracked, eb_h, eb_w,
    top_db, top_sp, bot_db, bot_sp
):
    """
    Master function that runs the entire engineering logic in one pass.
    """
    
    # --- 1. PREPARE INPUTS & UNITS ---
    u = physics.get_units()
    fc_mpa = fc_ksc * u['ksc_to_mpa']
    
    c1 = c1_mm / 1000.0
    c2 = c2_mm / 1000.0
    
    # --- 2. DETERMINE EFFECTIVE DEPTH (d) FROM USER REBAR ---
    # Logic: d is calculated immediately from the user's selected rebar
    avg_db = (top_db + bot_db) / 2.0
    d_mm = h_user - cover_mm - avg_db
    d_m = d_mm / 1000.0
    
    # --- 3. LOAD ANALYSIS ---
    sw = (h_user / 1000.0) * physics.CONCRETE_DENSITY
    qu = (1.4 * (sw + sdl)) + (1.7 * ll)
    
    # --- 4. SHEAR ANALYSIS (Punching) ---
    # Uses the ACTUAL d derived from user rebar
    ln_x = max(lx - c1, 0.65 * lx)
    ln = ln_x
    bo_m, acrit, alpha, beta, bo_str = physics.get_geometry(c1, c2, d_m, pos)
    
    # Capacity
    v1, v2, v3 = physics.get_vc_stress(fc_mpa, beta, alpha, d_m, bo_m)
    vc_mpa = min(v1, v2, v3)
    vc_newton = vc_mpa * (bo_m * 1000) * d_mm
    phi_vc_kg = (0.75 * vc_newton) / u['grav']
    
    # Demand
    gamma_v = physics.get_gamma_v(pos)
    vu_kg = qu * ((lx * ly) - acrit) * gamma_v
    shear_ratio = vu_kg / phi_vc_kg if phi_vc_kg > 0 else 999
    
    # --- 5. FLEXURAL ANALYSIS (EFM/DDM) ---
    # Stiffness
    Ec = 4700 * math.sqrt(fc_mpa) * 1000000 
    Is = physics.get_inertia_gross(ly, h_user/1000.0, use_cracked, "slab")
    Ks = (4 * Ec * Is) / lx 
    Ic = physics.get_inertia_gross(c2, c1, use_cracked, "column") 
    Kc = (4 * Ec * Ic) / lc_h
    Sum_Kc = 2 * Kc
    
    # Torsion
    eb_d = eb_h/1000.0 if eb_h > 0 else 0
    eb_wd = eb_w/1000.0 if eb_w > 0 else 0
    C = physics.get_torsional_constant_c_complex(h_user/1000.0, c1, eb_wd, eb_d - (h_user/1000.0))
    Kt = physics.get_torsional_stiffness_kt(Ec, C, ly, c2)
    Kec = physics.get_equivalent_column_stiffness(Sum_Kc, Kt)
    
    # Moments
    mo = (qu * ly * ln**2) / 8
    
    # Distribution Logic
    moments_data = []
    if "DDM" in method:
        coeffs = physics.get_moment_distribution_coeffs(continuity, "Column Strip") # Simplified for demo
        # In real app, call for both CS and MS. Here we focus on CS critical
        cs_neg_fac, cs_pos_fac = coeffs
        moments_data = [
            ("Column Strip Top (-)", cs_neg_fac * mo, "top"),
            ("Column Strip Bot (+)", cs_pos_fac * mo, "bot")
        ]
    else:
        # EFM Simplified
        m_neg = mo * 0.70
        m_pos = mo * 0.50
        moments_data = [
            ("Column Strip Top (-)", m_neg * 0.75, "top"),
            ("Column Strip Bot (+)", m_pos * 0.60, "bot")
        ]

    # --- 6. REBAR VERIFICATION ---
    rebar_results = []
    as_min = 0.0018 * 100 * (h_user / 10.0)
    
    for name, mu, side in moments_data:
        db = top_db if side == "top" else bot_db
        sp = top_sp if side == "top" else bot_sp
        
        # Flexural Demand
        d_cm = d_mm / 10.0
        denom = 0.9 * fy_ksc * 0.9 * d_cm
        as_req = (mu * 100) / denom
        as_target = max(as_req, as_min)
        
        # Capacity
        bar_area = physics.get_bar_area(db)
        as_prov = (bar_area * 1000) / sp
        
        # Checks
        status = "SAFE"
        reasons = []
        if as_prov < as_target:
            status = "FAIL"
            reasons.append("As < Req")
        if sp > 300: # Max spacing rule
            status = "FAIL"
            reasons.append("Spacing > 300")
            
        rebar_results.append({
            "location": name,
            "mu": mu,
            "as_req": as_req,
            "as_min": as_min,
            "user_db": db,
            "user_sp": sp,
            "as_prov": as_prov,
            "utilization": as_req / as_prov if as_prov > 0 else 9.9,
            "status": status,
            "note": ", ".join(reasons) if reasons else "OK"
        })

    # --- 7. DEFLECTION ---
    delta_imm, delta_lim, delta_ratio = 0, 0, 0
    try:
        w_line = qu * ly
        delta_imm = (2.5 * w_line * (lx**4)) / (384 * Ec * Is) * 1000 # mm
        delta_lim = lx * 1000 / 240.0
        delta_ratio = delta_imm / delta_lim
    except: pass

    # --- 8. FINAL PACKAGE ---
    # Determine Global Status
    shear_pass = shear_ratio <= 1.0
    flex_pass = all(r['status'] == "SAFE" for r in rebar_results)
    defl_pass = delta_ratio <= 1.0
    global_status = "SAFE" if (shear_pass and flex_pass and defl_pass) else "UNSAFE"

    return {
        "meta": {
            "lx": lx, "ly": ly, "h": h_user, "fc": fc_ksc, "fy": fy_ksc,
            "sdl": sdl, "ll": ll, "qu_area": qu / (lx*ly) if lx*ly > 0 else 0
        },
        "shear": {
            "d_mm": d_mm, "bo_mm": bo_m*1000, "vu": vu_kg, "phi_vc": phi_vc_kg, 
            "ratio": shear_ratio, "status": "PASS" if shear_pass else "FAIL"
        },
        "flexure": {
            "mo": mo, "results": rebar_results
        },
        "deflection": {
            "val": delta_imm, "lim": delta_lim, "ratio": delta_ratio, 
            "status": "PASS" if defl_pass else "FAIL"
        },
        "geometry": {
            "c1": c1, "cover": cover_mm
        },
        "global_status": global_status
    }
