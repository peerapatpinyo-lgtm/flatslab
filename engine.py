import physics
import math

def check_deflection_immediate(qu, lx, ly, Ec, I_eff):
    """
    Estimates immediate deflection using simplified elastic beam theory.
    Delta = (coefficient) * w * L^4 / (E * I)
    """
    # Use conservative coefficient for continuous span (approx 3/384 to 5/384)
    # Using 5/384 (0.013) is for simply supported, continuous is closer to 1/384 (0.0026) for fixed ends.
    # We use a mid-range value for "Design Strip" estimation: ~2.5/384
    
    w_line = qu * ly # Load per meter on the strip
    
    try:
        delta = (2.5 * w_line * (lx**4)) / (384 * Ec * I_eff)
        limit = lx / 240.0 # ACI basic limit
        ratio = delta / limit
        return delta * 1000, limit * 1000, ratio # Return in mm
    except ZeroDivisionError:
        return 0, 0, 0

def analyze_efm(lx, ly, h_m, c1, c2, lc_upper, lc_lower, fc_mpa, continuity, use_cracked, edge_beam_h=0, edge_beam_w=0):
    """
    Equivalent Frame Method (EFM) - Advanced Stiffness Calculation
    """
    # 1. Properties
    Ec = 4700 * math.sqrt(fc_mpa) * 1000000 
    
    # Slab Stiffness (Ks)
    Is_gross = physics.get_inertia_gross(ly, h_m) # Use ly as width of frame
    Is = physics.get_inertia_gross(ly, h_m, use_cracked, "slab")
    Ks = (4 * Ec * Is) / lx 
    
    # Column Stiffness (Kc)
    Ic = physics.get_inertia_gross(c2, c1, use_cracked, "column") 
    Kc_upper = (4 * Ec * Ic) / lc_upper
    Kc_lower = (4 * Ec * Ic) / lc_lower
    Sum_Kc = Kc_upper + Kc_lower
    
    # Torsional Stiffness (Kt)
    # If Edge Beam exists, C is sum of rect parts
    x1 = h_m
    y1 = c1
    
    # Check Edge Beam
    x2 = 0
    y2 = 0
    if edge_beam_h > h_m:
        x2 = edge_beam_w
        y2 = edge_beam_h - h_m # The protruding part
        
    C = physics.get_torsional_constant_c_complex(x1, y1, x2, y2)
    Kt = physics.get_torsional_stiffness_kt(Ec, C, ly, c2)
    
    # Equivalent Column (Kec)
    Kec = physics.get_equivalent_column_stiffness(Sum_Kc, Kt)
    
    # Distribution Factors (DF)
    # DF = Stiffness / Sum of Stiffness at Joint
    total_stiffness_ext = Ks + Kec
    df_ext_slab = Ks / total_stiffness_ext # At Exterior Joint
    
    # Interior Joint (Symmetric assumption: Ks_left = Ks_right)
    total_stiffness_int = (2 * Ks) + Kec
    df_int_slab = Ks / total_stiffness_int 
    
    return {
        "Ec": Ec, "Is": Is, "Ic": Ic, "Ks": Ks,
        "Kc_up": Kc_upper, "Kc_low": Kc_lower, "Sum_Kc": Sum_Kc,
        "C": C, "Kt": Kt, "Kec": Kec,
        "df_ext_slab": df_ext_slab,
        "df_int_slab": df_int_slab
    }

def analyze_structure(lx, ly, h_init, c1_mm, c2_mm, lc_up_m, lc_low_m, 
                      fc_ksc, fy_ksc, sdl, ll, cover_mm, pos, dl_fac, ll_fac, 
                      est_bar_db, continuity, method_str, use_cracked, 
                      edge_beam_h_mm=0, edge_beam_w_mm=0):
    
    u = physics.get_units()
    fc_mpa = fc_ksc * u['ksc_to_mpa']
    
    c1 = c1_mm / 1000.0
    c2 = c2_mm / 1000.0
    eb_h = edge_beam_h_mm / 1000.0
    eb_w = edge_beam_w_mm / 1000.0
    
    # Exact Clear Span
    ln_x = max(lx - c1, 0.65 * lx)
    ln_y = max(ly - c2, 0.65 * ly)
    ln = ln_x 
    
    # --- Thickness Iteration ---
    h_min_val, h_denom = physics.get_min_thickness_limit(ln, pos)
    h_current = h_init
    max_h = 1500
    
    final_results = {}
    
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
        
    # --- EFM Analysis ---
    efm_data = analyze_efm(lx, ly, h_current/1000.0, c1, c2, lc_up_m, lc_low_m, fc_mpa, 
                          continuity, use_cracked, eb_h, eb_w)
    
    fem = (qu * ly * (lx**2)) / 12.0
    
    # Moment Distribution using Calculated DFs
    if continuity == "Interior Span":
        # Balanced
        m_neg_calc = fem # Fixed
        m_pos_calc = (qu * ly * (lx**2)) / 24.0 # Approx Mid
        
        efm_data.update({
            "fem": fem,
            "m_neg_ext": m_neg_calc,
            "m_neg_int": m_neg_calc,
            "m_pos": m_pos_calc
        })
    else:
        # End Span
        df = efm_data['df_ext_slab']
        
        # Moment Distribution Method (Simplified Single Step)
        # Exterior Joint is released based on Kec
        m_neg_ext_calc = fem * (1 - df) 
        
        # Carry Over Factor = 0.5 to interior
        m_neg_int_calc = fem + (0.5 * fem * df)
        
        # Static Moment Balance
        mo_static = (qu * ly * ln**2) / 8
        m_pos_calc = max(mo_static - ((m_neg_ext_calc + m_neg_int_calc)/2), 0)
        
        efm_data.update({
            "fem": fem,
            "m_neg_ext": m_neg_ext_calc,
            "m_neg_int": m_neg_int_calc,
            "m_pos": m_pos_calc
        })

    # --- Deflection Pre-check ---
    delta_imm, delta_lim, delta_ratio = check_deflection_immediate(
        qu, lx, ly, efm_data['Ec'], efm_data['Is']
    )

    return {
        "inputs": {
            "lx": lx, "ly": ly, "c1": c1, "c2": c2, "pos": pos,
            "sw": sw, "sdl": sdl, "ll": ll, "qu": qu,
            "fc_mpa": fc_mpa, "fy": fy_ksc, "h_denom": h_denom,
            "h_init": h_init, "dl_fac": dl_fac, "ll_fac": ll_fac,
            "cover_mm": cover_mm, "continuity": continuity,
            "lc_up": lc_up_m, "lc_low": lc_low_m,
            "method": method_str, "use_cracked": use_cracked
        },
        "results": {
            "h": h_current, "h_min": h_min_val,
            "d_mm": d_mm, "bo_mm": bo_m*1000, "acrit": acrit,
            "vc_mpa": vc_mpa, "phi_vc_kg": phi_vc_kg, "vu_kg": vu_kg, 
            "qu": qu, "gamma_v": gamma_v, "ratio": ratio, 
            "mo": (qu * ly * ln**2) / 8, 
            "ln": ln, "ln_x": ln_x, "ln_y": ln_y,
            "bo_str": bo_str,
            "delta_imm": delta_imm, "delta_lim": delta_lim, "delta_ratio": delta_ratio
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
        cs_neg, cs_pos = physics.get_moment_distribution_coeffs(continuity, "Column Strip")
        ms_neg, ms_pos = physics.get_moment_distribution_coeffs(continuity, "Middle Strip")
        
        m_cs_neg = cs_neg * mo
        m_cs_pos = cs_pos * mo
        m_ms_neg = ms_neg * mo
        m_ms_pos = ms_pos * mo
        
    else: 
        # Use EFM Moments directly (Distributed to Strips)
        # ACI Rules: CS takes 75% Neg, 60% Pos
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
    max_utilization = 0
    
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
        
        # 1. Area Check
        if as_provided < as_target:
            status_msgs.append("Insufficient As")
            is_safe = False
        
        # 2. Spacing Check (Strict 2h or 300mm)
        max_s_limit = min(2 * h, 300)
        if sel_spacing > max_s_limit:
            status_msgs.append(f"Spacing > {max_s_limit}mm")
            is_safe = False
        
        # Calculate Utilization (As_req / As_prov)
        util = as_req_calc / as_provided if as_provided > 0 else 9.9
        if util > max_utilization: max_utilization = util
            
        status = "SAFE" if is_safe else "FAIL: " + ", ".join(status_msgs)
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
            "color": color,
            "utilization": util,
            "max_s": max_s_limit
        })
        
    return {
        "rebar_verified": rebar_detailed,
        "as_min": as_min,
        "max_flexure_util": max_utilization
    }
