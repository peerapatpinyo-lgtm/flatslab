import physics
import math

def analyze_efm(lx, ly, h_m, c1, c2, lc_upper, lc_lower, fc_mpa, continuity):
    """
    Equivalent Frame Method (EFM) Analysis
    Considers Slab-Beam + Torsional Member + Columns
    """
    # 1. Properties
    Ec = 4700 * math.sqrt(fc_mpa) * 1000000 # Pa (approx for normal weight)
    
    # Slab Stiffness (Ks) - Assume Prism for Flat Plate
    # Width of slab beam is ly (designing for lx span)
    Is = physics.get_inertia_gross(ly, h_m)
    Ks = (4 * Ec * Is) / lx # Stiffness of slab
    
    # Column Stiffness (Kc)
    Ic = physics.get_inertia_gross(c1, c2) # c1 is width, c2 is depth in bending direction? 
    # Usually for Span Lx, bending axis is parallel to Ly. So width is c2, depth is c1.
    # Correct Interpretation: Bending along Lx. Column dimension parallel to Lx is c1.
    Ic = physics.get_inertia_gross(c2, c1) 
    
    Kc_upper = (4 * Ec * Ic) / lc_upper
    Kc_lower = (4 * Ec * Ic) / lc_lower
    Sum_Kc = Kc_upper + Kc_lower
    
    # Torsional Member Stiffness (Kt)
    # Torsional member is the slab strip of width c1 + h (or just c1)
    # ACI: Cross section is c1 x h
    x = h_m
    y = c1 # dimension perpendicular to span
    # ensure x < y for formula
    if x > y: x, y = y, x
        
    C = physics.get_torsional_constant_c(x, y)
    Kt = physics.get_torsional_stiffness_kt(Ec, C, ly, c2) # ly = l2, c2 = dimension parallel to span
    
    # Equivalent Column Stiffness (Kec)
    Kec = physics.get_equivalent_column_stiffness(Sum_Kc, Kt)
    
    # 2. Distribution Factors (DF)
    # At Exterior Joint (Node 1)
    # DF_slab = Ks / (Ks + Kec) -> Not usually used directly, we find moment
    # DF_col = Kec / (Ks + Kec)
    
    total_stiffness_ext = Ks + Kec
    df_ext_col = Kec / total_stiffness_ext
    df_ext_slab = Ks / total_stiffness_ext
    
    # At Interior Joint (Node 2) - Assume symmetric adjacent span
    # Stiffness = Ks (left) + Ks (right) + Kec
    total_stiffness_int = (2 * Ks) + Kec
    df_int_slab = Ks / total_stiffness_int
    
    # 3. Moment Analysis (Simplified Frame)
    # Fixed End Moment (FEM)
    # Use qu from parent function (passed implicitly? No, need calc)
    # Return stiffness data first, calc moments in main loop using qu
    
    return {
        "Ec": Ec, "Is": Is, "Ic": Ic, "Ks": Ks,
        "Kc_up": Kc_upper, "Kc_low": Kc_lower, "Sum_Kc": Sum_Kc,
        "C": C, "Kt": Kt, "Kec": Kec,
        "df_ext_slab": df_ext_slab,
        "df_int_slab": df_int_slab
    }

def analyze_structure(lx, ly, h_init, c1_mm, c2_mm, lc_up_m, lc_low_m, fc_ksc, fy_ksc, sdl, ll, cover_mm, pos, dl_fac, ll_fac, est_bar_db, continuity):
    u = physics.get_units()
    fc_mpa = fc_ksc * u['ksc_to_mpa']
    
    c1 = c1_mm / 1000.0
    c2 = c2_mm / 1000.0
    
    ln_x = max(lx - c1, 0.65 * lx)
    ln_y = max(ly - c2, 0.65 * ly)
    ln = ln_x 
    
    # --- Thickness Design Loop ---
    h_min_val, h_denom = physics.get_min_thickness_limit(ln, pos)
    h_current = h_init
    max_h = 1500
    
    while h_current <= max_h:
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
    
    # --- EFM Analysis ---
    efm_data = analyze_efm(lx, ly, h_current/1000.0, c1, c2, lc_up_m, lc_low_m, fc_mpa, continuity)
    
    # Calculate EFM Moments (Simplified Distribution)
    # FEM = qu * ly * lx^2 / 12 (Fixed End Moment)
    fem = (qu * ly * (lx**2)) / 12.0
    
    if continuity == "Interior Span":
        # Balanced Moments
        m_neg_efm = fem # Approx fixed
        m_pos_efm = (qu * ly * (lx**2)) / 24.0 # Approx midspan
    else:
        # End Span Analysis (Single Step Distribution)
        # Joint Ext (Release) -> Joint Int (Continuous)
        df_ext = efm_data['df_ext_slab'] # Distribution to slab
        
        # Moment at Exterior Face
        m_neg_ext_efm = fem * (1 - df_ext) # If DF=1 (Pinned), M=0. If DF=0 (Fixed), M=FEM.
        
        # Moment at Interior Face (Carry over approx 0.5)
        m_neg_int_efm = fem + (0.5 * fem * df_ext) 
        
        # Positive Moment (Static Balance)
        mo_static = (qu * ly * ln**2) / 8
        m_pos_efm = mo_static - ((m_neg_ext_efm + m_neg_int_efm)/2)
        
        # Store for report
        efm_data.update({
            "fem": fem,
            "m_neg_ext": m_neg_ext_efm,
            "m_neg_int": m_neg_int_efm,
            "m_pos": m_pos_efm
        })

    # --- Base Moment (DDM) ---
    mo = (qu * ly * ln**2) / 8
    
    return {
        "inputs": {
            "lx": lx, "ly": ly, "c1": c1, "c2": c2, "pos": pos,
            "sw": sw, "sdl": sdl, "ll": ll, "qu": qu,
            "fc_mpa": fc_mpa, "fy": fy_ksc, "h_denom": h_denom,
            "h_init": h_init, "dl_fac": dl_fac, "ll_fac": ll_fac,
            "cover_mm": cover_mm, "continuity": continuity,
            "lc_up": lc_up_m, "lc_low": lc_low_m
        },
        "results": {
            "h": h_current, "h_min": h_min_val, "reason": reason,
            "d_mm": d_mm, "bo_mm": bo_m*1000, "acrit": acrit,
            "v1": v1, "v2": v2, "v3": v3, "vc_mpa": vc_mpa,
            "phi_vc_kg": phi_vc_kg, "vu_kg": vu_kg, 
            "qu": qu, "gamma_v": gamma_v, "ratio": ratio, 
            "mo": mo, "ln": ln, "ln_x": ln_x, "ln_y": ln_y,
            "bo_str": bo_str
        },
        "efm": efm_data
    }

def verify_reinforcement(base_data, user_top_db, user_top_spacing, user_bot_db, user_bot_spacing):
    r = base_data['results']
    i = base_data['inputs']
    
    h = r['h']
    d_avg = r['d_mm']
    mo = r['mo']
    fy = i['fy']
    continuity = i['continuity']
    
    as_min = 0.0018 * 100 * (h / 10.0)
    
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
        mu = coeff * mo
        d_cm = d_avg / 10.0 
        denom_val = 0.9 * fy * 0.9 * d_cm
        as_req_calc = (mu * 100) / denom_val 
        
        as_target = max(as_req_calc, as_min)
        
        if side == "top":
            sel_db = user_top_db
            sel_spacing = user_top_spacing
        else:
            sel_db = user_bot_db
            sel_spacing = user_bot_spacing
            
        bar_area = physics.get_bar_area(sel_db)
        as_provided = (bar_area * 1000) / sel_spacing
        
        status_msgs = []
        is_safe = True
        
        if as_provided < as_target:
            status_msgs.append("FAIL: Insufficient As")
            is_safe = False
            
        max_s = min(2 * h, 300) 
        if sel_spacing > max_s:
            status_msgs.append(f"FAIL: Spacing > Max ({max_s}mm)")
            is_safe = False
            
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
