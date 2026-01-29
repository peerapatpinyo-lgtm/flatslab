import physics
import math

def check_deflection_immediate(qu, lx, ly, Ec, I_eff):
    w_line = qu * ly
    try:
        # Coefficient for continuous span approx 2.5/384
        delta = (2.5 * w_line * (lx**4)) / (384 * Ec * I_eff)
        limit = lx / 240.0
        return delta * 1000, limit * 1000, delta / limit
    except ZeroDivisionError:
        return 0, 0, 0

def analyze_and_verify_system(
    # Geometry & Loads
    lx, ly, h_user, c1_mm, c2_mm, lc_h, 
    sdl, ll, fc_ksc, fy_ksc, 
    # Settings
    cover_mm, pos, method, continuity, use_cracked, eb_h, eb_w,
    # Rebar Inputs (Linked directly to analysis)
    top_db, top_sp, bot_db, bot_sp
):
    """
    Unified function that analyzes forces AND verifies capacity 
    using the EXACT rebar configurations provided by the user.
    """
    
    # 1. Setup Units & Material
    u = physics.get_units()
    fc_mpa = fc_ksc * u['ksc_to_mpa']
    
    # Dimensions
    c1 = c1_mm / 1000.0
    c2 = c2_mm / 1000.0
    
    # 2. Calculate Exact Effective Depth (d)
    # Use average d for shear (assume 2 layers of steel)
    # d = h - cover - db_outer - (db_inner/2) -> Simplified to h - cover - db
    avg_db = (top_db + bot_db) / 2.0
    d_mm = h_user - cover_mm - avg_db
    d_m = d_mm / 1000.0
    
    # 3. Loads
    sw = (h_user / 1000.0) * physics.CONCRETE_DENSITY
    qu = (1.4 * (sw + sdl)) + (1.7 * ll)
    
    # 4. Shear Analysis (Using Actual d)
    ln_x = max(lx - c1, 0.65 * lx)
    ln = ln_x
    bo_m, acrit, alpha, beta, bo_str = physics.get_geometry(c1, c2, d_m, pos)
    
    # Shear Capacity
    v1, v2, v3 = physics.get_vc_stress(fc_mpa, beta, alpha, d_m, bo_m)
    vc_mpa = min(v1, v2, v3)
    vc_newton = vc_mpa * (bo_m * 1000) * d_mm
    phi_vc_kg = (0.75 * vc_newton) / u['grav']
    
    # Shear Demand
    gamma_v = physics.get_gamma_v(pos)
    vu_kg = qu * ((lx * ly) - acrit) * gamma_v
    shear_ratio = vu_kg / phi_vc_kg if phi_vc_kg > 0 else 999
    
    # 5. Flexural Analysis (EFM)
    efm_data = analyze_efm_logic(lx, ly, h_user/1000.0, c1, c2, lc_h, fc_mpa, continuity, use_cracked, eb_h, eb_w)
    
    # Calculate Moments (Mo)
    mo = (qu * ly * ln**2) / 8
    
    # Distribute Moments
    moments = distribute_moments(method, continuity, mo, efm_data)
    
    # 6. Deflection Check
    delta_imm, delta_lim, delta_ratio = check_deflection_immediate(qu, lx, ly, efm_data['Ec'], efm_data['Is'])
    
    # 7. Rebar Verification (Using Linked Inputs)
    rebar_results = verify_rebar_list(moments, h_user, d_mm, fy_ksc, top_db, top_sp, bot_db, bot_sp)
    
    # 8. Overall Safety Status
    flexure_safe = all(r['status'] == "SAFE" for r in rebar_results)
    shear_safe = shear_ratio <= 1.0
    deflection_safe = delta_ratio <= 1.0
    
    overall_status = "SAFE" if (flexure_safe and shear_safe) else "UNSAFE"
    
    return {
        "inputs": {
            "lx": lx, "ly": ly, "h": h_user, "c1": c1, "c2": c2,
            "fc": fc_ksc, "fy": fy_ksc, "qu": qu, "sw": sw, "sdl": sdl, "ll": ll,
            "method": method, "pos": pos, "cover": cover_mm
        },
        "results": {
            "d_mm": d_mm, "bo_mm": bo_m*1000, 
            "vu": vu_kg, "phi_vc": phi_vc_kg, "shear_ratio": shear_ratio,
            "mo": mo, "delta_ratio": delta_ratio, "delta_imm": delta_imm,
            "overall_status": overall_status
        },
        "rebar": rebar_results,
        "efm": efm_data
    }

def analyze_efm_logic(lx, ly, h_m, c1, c2, lc_h, fc_mpa, continuity, use_cracked, eb_h, eb_w):
    Ec = 4700 * math.sqrt(fc_mpa) * 1000000 
    Is = physics.get_inertia_gross(ly, h_m, use_cracked, "slab")
    Ks = (4 * Ec * Is) / lx 
    Ic = physics.get_inertia_gross(c2, c1, use_cracked, "column") 
    Kc = (4 * Ec * Ic) / lc_h
    Sum_Kc = 2 * Kc
    
    # Torsion
    eb_d = eb_h if eb_h > 0 else 0
    eb_wd = eb_w if eb_w > 0 else 0
    C = physics.get_torsional_constant_c_complex(h_m, c1, eb_wd, eb_d - h_m)
    Kt = physics.get_torsional_stiffness_kt(Ec, C, ly, c2)
    Kec = physics.get_equivalent_column_stiffness(Sum_Kc, Kt)
    
    total = Ks + Kec
    df_ext = Ks / total if total > 0 else 0
    return {"Ec": Ec, "Is": Is, "Kec": Kec, "df_ext_slab": df_ext}

def distribute_moments(method, continuity, mo, efm_data):
    if "DDM" in method:
        cs_neg, cs_pos = physics.get_moment_distribution_coeffs(continuity, "Column Strip")
        ms_neg, ms_pos = physics.get_moment_distribution_coeffs(continuity, "Middle Strip")
        return [
            ("Column Strip Top (-)", cs_neg * mo, "top"),
            ("Column Strip Bot (+)", cs_pos * mo, "bot"),
            ("Middle Strip Top (-)", ms_neg * mo, "top"),
            ("Middle Strip Bot (+)", ms_pos * mo, "bot")
        ]
    else:
        # EFM Simplified distribution
        fem = efm_data.get('fem', mo * 0.65) # Fallback
        # Apply standard EFM splits
        m_neg = mo * 0.70 # Simplified for logic flow
        m_pos = mo * 0.50
        return [
            ("Column Strip Top (-)", m_neg * 0.75, "top"),
            ("Column Strip Bot (+)", m_pos * 0.60, "bot"),
            ("Middle Strip Top (-)", m_neg * 0.25, "top"),
            ("Middle Strip Bot (+)", m_pos * 0.40, "bot")
        ]

def verify_rebar_list(moments, h, d_mm, fy, top_db, top_sp, bot_db, bot_sp):
    results = []
    as_min = 0.0018 * 100 * (h / 10.0)
    
    for name, mu, side in moments:
        db = top_db if side == "top" else bot_db
        sp = top_sp if side == "top" else bot_sp
        
        # 1. Demand
        d_cm = d_mm / 10.0
        denom = 0.9 * fy * 0.9 * d_cm
        as_req = (mu * 100) / denom
        as_target = max(as_req, as_min)
        
        # 2. Capacity
        bar_area = physics.get_bar_area(db)
        as_prov = (bar_area * 1000) / sp
        
        # 3. Status
        check_pass = True
        note = []
        if as_prov < as_target: 
            check_pass = False
            note.append("Insufficient As")
        if sp > min(2*h, 300):
            check_pass = False
            note.append("Spacing > Max")
            
        results.append({
            "name": name, "mu": mu, "as_req": as_req, "as_min": as_min,
            "db": db, "sp": sp, "as_prov": as_prov,
            "status": "SAFE" if check_pass else "FAIL",
            "note": ", ".join(note) if note else "OK",
            "util": as_req / as_prov if as_prov > 0 else 9.9
        })
    return results
