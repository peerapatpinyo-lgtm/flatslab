import physics
import math

def analyze_efm(lx, ly, h_m, c1, c2, lc_upper, lc_lower, fc_mpa, continuity):
    """
    Equivalent Frame Method (EFM) - Stiffness Calculation
    """
    # 1. Properties
    Ec = 4700 * math.sqrt(fc_mpa) * 1000000 
    
    # Slab Stiffness (Ks)
    Is = physics.get_inertia_gross(ly, h_m)
    Ks = (4 * Ec * Is) / lx 
    
    # Column Stiffness (Kc)
    Ic = physics.get_inertia_gross(c2, c1) 
    Kc_upper = (4 * Ec * Ic) / lc_upper
    Kc_lower = (4 * Ec * Ic) / lc_lower
    Sum_Kc = Kc_upper + Kc_lower
    
    # Torsional Stiffness (Kt)
    x = h_m
    y = c1 
    if x > y: x, y = y, x
    C = physics.get_torsional_constant_c(x, y)
    Kt = physics.get_torsional_stiffness_kt(Ec, C, ly, c2)
    
    # Equivalent Column (Kec)
    Kec = physics.get_equivalent_column_stiffness(Sum_Kc, Kt)
    
    # Alpha EC (Ratio of Equivalent Column to Slab Stiffness) at the joint
    # This helps engineers judge how "stiff" the column connection is.
    # For interior joint: sum(Ks) = 2*Ks approx.
    alpha_ec = Kec / (Ks * 2) if continuity == "Interior Span" else Kec / Ks
    
    # Distribution Factors (DF)
    total_stiffness_ext = Ks + Kec
    df_ext_slab = Ks / total_stiffness_ext # DF to Slab at Exterior
    
    return {
        "Ec": Ec, "Is": Is, "Ic": Ic, "Ks": Ks,
        "Kc_up": Kc_upper, "Kc_low": Kc_lower, "Sum_Kc": Sum_Kc,
        "C": C, "Kt": Kt, "Kec": Kec,
        "alpha_ec": alpha_ec,
        "df_ext_slab": df_ext_slab
    }

def analyze_structure(lx, ly, h_init, c1_mm, c2_mm, lc_up_m, lc_low_m, 
                      fc_ksc, fy_ksc, sdl, ll, cover_mm, pos, dl_fac, ll_fac, 
                      est_bar_db, continuity, method_str):
    
    u = physics.get_units()
    fc_mpa = fc_ksc * u['ksc_to_mpa']
    
    c1 = c1_mm / 1000.0
    c2 = c2_mm / 1000.0
    
    # Exact Clear Span Calculation
    ln_x = max(lx - c1, 0.65 * lx)
    ln_y = max(ly - c2, 0.65 * ly)
    ln = ln_x 
    
    # --- Thickness Loop ---
    h_min_val, h_denom = physics.get_min_thickness_limit(ln, pos)
    h_current = h_init
    max_h = 1500
    
    while h_current <= max_h:
        d_mm = h_current - cover_mm - (est_bar_db / 2.0)
        d_m = d_mm / 1000.0
        
        sw = (h_current / 1000.0) * physics.CONCRETE_DENSITY
        qu = (dl_fac * (sw + sdl)) + (ll_fac * ll)
        
        # Shear
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
    
    # --- Moment Calculation Strategy ---
    # 1. Base Static Moment
    mo = (qu * ly * ln**2) / 8
    
    # 2. EFM Calculation
    efm_data = analyze_efm(lx, ly, h_current/1000.0, c1, c2, lc_up_m, lc_low_m, fc_mpa, continuity)
    fem = (qu * ly * (lx**2)) / 12.0
    
    # Assign EFM Moments based on simple frame logic
    if continuity == "Interior Span":
        m_neg_efm = fem 
        m_pos_efm = (qu * ly * (lx**2)) / 24.0 # Approx
    else:
        # End Span
        df = efm_data['df_ext_slab']
        m_neg_ext_efm = fem * (1 - df) # Release based on stiffness
        m_neg_int_efm = fem + (0.5 * fem * df) # Carry over
        m_pos_efm = mo - ((m_neg_ext_efm + m_neg_int_efm)/2)
        
        # Save explicitly for report
        efm_data.update({
            "m_neg_ext": m_neg_ext_efm,
            "m_neg_int": m_neg_int_efm,
            "m_pos": m_pos_efm
        })

    return {
        "inputs": {
            "lx": lx, "ly": ly, "c1": c1, "c2": c2, "pos": pos,
            "sw": sw, "sdl": sdl, "ll": ll, "qu": qu,
            "fc_mpa": fc_mpa, "fy": fy_ksc, "h_denom": h_denom,
            "h_init": h_init, "dl_fac": dl_fac, "ll_fac": ll_fac,
            "cover_mm": cover_mm, "continuity": continuity,
            "lc_up": lc_up_m, "lc_low": lc_low_m,
            "method": method_str
        },
        "results": {
            "h": h_current, "h_min": h_min_val, "reason": reason,
            "d_mm": d_mm, "bo_mm": bo_m*1000, "acrit": acrit,
            "vc_mpa": vc_mpa, "phi_vc_kg": phi_vc_kg, "vu_kg": vu_kg, 
            "qu": qu, "gamma_v": gamma_v, "ratio": ratio, 
            "mo": mo, "ln": ln, "ln_x": ln_x, "ln_y": ln_y,
            "bo_str": bo_str
        },
        "efm": efm_data
    }

def verify_reinforcement(base_data, user_top_db, user_top_spacing, user_bot_db, user_bot_spacing):
    r = base_data['results']
    i = base_data['inputs']
    efm = base_data['efm']
    
    h = r['h']
    d_avg = r['d_mm']
    mo = r['mo']
    fy = i['fy']
    method = i['method']
    continuity = i['continuity']
    
    as_min = 0.0018 * 100 * (h / 10.0)
    
    # --- Logic Switch: DDM vs EFM Moments ---
    
    if "DDM" in method:
        # Use Coefficients * Mo
        cs_neg, cs_pos = physics.get_moment_distribution(continuity, "Column Strip")
        ms_neg, ms_pos = physics.get_moment_distribution(continuity, "Middle Strip")
        
        # Values
        m_cs_neg = cs_neg * mo
        m_cs_pos = cs_pos * mo
        m_ms_neg = ms_neg * mo
        m_ms_pos = ms_pos * mo
        
    else: 
        # Use EFM Moments directly (distributed to strips)
        # Simplified: CS takes 75% neg, 60% pos of Frame Moment
        
        if continuity == "Interior Span":
            m_neg_frame = efm.get('fem', mo * 0.65)
            m_pos_frame = efm.get('m_pos', mo * 0.35)
        else:
            m_neg_frame = efm.get('m_neg_int', mo * 0.70)
            m_pos_frame = efm.get('m_pos', mo * 0.50)
            
        m_cs_neg = m_neg_frame * 0.75
        m_cs_pos = m_pos_frame * 0.60
        m_ms_neg = m_neg_frame * 0.25
        m_ms_pos = m_pos_frame * 0.40

    strips_config = [
        ("Column Strip Top (-)", m_cs_neg, "top"),
        ("Column Strip Bot (+)", m_cs_pos, "bot"),
        ("Middle Strip Top (-)", m_ms_neg, "top"),
        ("Middle Strip Bot (+)", m_ms_pos, "bot")
    ]
    
    rebar_detailed = []
    
    for name, mu_val, side in strips_config:
        d_cm = d_avg / 10.0 
        denom_val = 0.9 * fy * 0.9 * d_cm
        as_req_calc = (mu_val * 100) / denom_val 
        as_target = max(as_req_calc, as_min)
        
        if side == "top":
            sel_db, sel_spacing = user_top_db, user_top_spacing
        else:
            sel_db, sel_spacing = user_bot_db, user_bot_spacing
            
        bar_area = physics.get_bar_area(sel_db)
        as_provided = (bar_area * 1000) / sel_spacing
        
        # Checks
        status_msgs = []
        is_safe = True
        if as_provided < as_target:
            status_msgs.append("FAIL: Insufficient As")
            is_safe = False
        if sel_spacing > min(2 * h, 450):
            status_msgs.append("FAIL: Spacing Limit")
            is_safe = False
            
        status = "SAFE" if is_safe else " / ".join(status_msgs)
        color = "green" if is_safe else "red"
            
        rebar_detailed.append({
            "name": name,
            "mu": mu_val,
            "as_target": as_target,
            "as_min": as_min,
            "user_db": sel_db,
            "user_spacing": sel_spacing,
            "as_provided": as_provided,
            "status": status,
            "color": color
        })
        
    return {
        "rebar_verified": rebar_detailed,
        "as_min": as_min
    }
