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
        # กรณี Interior Span: โมเมนต์ลบซ้ายขวาเท่ากัน (ประมาณเท่ากับ FEM)
        m_neg_efm = fem 
        m_pos_efm = (qu * ly * (lx**2)) / 24.0 # Approx Midspan
        
        # --- FIX: ต้อง update ค่าลง dict ด้วย ไม่งั้น app.py จะหา key ไม่เจอ ---
        efm_data.update({
            "fem": fem,
            "m_neg_ext": m_neg_efm, # ใช้ค่าเดียวกัน
            "m_neg_int": m_neg_efm, # ใช้ค่าเดียวกัน
            "m_pos": m_pos_efm
        })
        
    else:
        # End Span
        df = efm_data['df_ext_slab']
        m_neg_ext_efm = fem * (1 - df) # Release based on stiffness
        m_neg_int_efm = fem + (0.5 * fem * df) # Carry over
        m_pos_efm = mo - ((m_neg_ext_efm + m_neg_int_efm)/2)
        
        # Save explicitly for report
        efm_data.update({
            "fem": fem,
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
