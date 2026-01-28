import numpy as np

# เพิ่ม dl_factor=1.2, ll_factor=1.6 ในบรรทัดนี้ เพื่อให้รับค่าจาก app.py ได้
def calculate_detailed_slab(lx, ly, h_mm, c1_mm, c2_mm, fc_ksc, fy_ksc, sdl, ll, cover_mm, pos="Interior", dl_factor=1.2, ll_factor=1.6):
    
    # --- 1. การเตรียมข้อมูลและหน่วย ---
    h = h_mm / 1000
    c1 = c1_mm / 1000
    c2 = c2_mm / 1000
    d = (h_mm - cover_mm - 12) / 1000
    fc_mpa = fc_ksc * 0.0980665
    g = 9.80665

    # --- 2. ACI Minimum Thickness Check ---
    # ใช้ค่า ln ในการเช็ค (โดยประมาณ)
    ln_check = max(lx, ly) - (c1_mm/1000)
    h_min_req = (ln_check * 1000) / 30 if pos != "Interior" else (ln_check * 1000) / 33
    h_warning = ""
    if h_mm < h_min_req:
        h_warning = f"Warning: Thickness ({h_mm}mm) is less than ACI min recommendation ({h_min_req:.0f}mm)."

    # --- 3. Loading Detailed (ใช้ Custom Factors) ---
    sw = h * 2400
    # ใช้ตัวแปร dl_factor และ ll_factor ที่รับเข้ามา
    w_dl_factored = dl_factor * (sw + sdl)
    w_ll_factored = ll_factor * ll
    qu = w_dl_factored + w_ll_factored
    
    # *** New: Tributary Logic ***
    tributary_area = lx * ly
    total_load_kg = qu * tributary_area

    # --- 4. Geometry & Mo ---
    # ln (Clear Span) calculation
    ln_calc = lx - c1
    ln = max(ln_calc, 0.65 * lx)
    mo = (qu * ly * (ln**2)) / 8

    # --- 5. Punching Shear Check ---
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
        v1 = 0.33 * np.sqrt(fc_mpa)
        v2 = 0.17 * (1 + 2/beta) * np.sqrt(fc_mpa)
        v3 = 0.083 * (2 + (alpha_s * t_d / bo)) * np.sqrt(fc_mpa)
        vc_mpa = min(v1, v2, v3)
        
        # Vu คำนวณจากน้ำหนักทั้งหมด ลบด้วยน้ำหนักที่ลงในพื้นที่ A_crit (แรงที่ถ่ายเข้าเสาโดยตรง)
        vu_kg = qu * ((lx * ly) - a_crit)
        phi_vc_kg = (0.75 * vc_mpa * (bo * 1000 * t_d * 1000)) / g
        
        return {
            "vu": vu_kg, 
            "phi_vc": phi_vc_kg, 
            "bo": bo, 
            "d": t_d, 
            "vc_mpa": vc_mpa, 
            "v1":v1, "v2":v2, "v3":v3,
            "beta": beta,
            "acrit": a_crit
        }

    current_h = h_mm
    while True:
        p = get_punching_data(current_h)
        if p['vu'] <= p['phi_vc'] or current_h >= 600:
            break
        current_h += 10

    # --- 6. Rebar Calculation ---
    as_min = 0.0018 * 100 * (current_h / 10)
    phi_flex = 0.9
    m_coeffs = {"CS_Neg": 0.4875, "MS_Neg": 0.1625, "CS_Pos": 0.21, "MS_Pos": 0.14}
    
    rebar_out = {}
    max_spacing_mm = min(300, 2 * current_h)
    
    for key, coeff in m_coeffs.items():
        m_strip = coeff * mo
        as_req = (m_strip * 100) / (phi_flex * fy_ksc * (p['d'] * 100 * 0.9))
        as_final = max(as_req / ly, as_min)
        rebar_out[key] = as_final

    final_ratio = p['vu'] / p['phi_vc'] if p['phi_vc'] > 0 else 0

    return {
        "loading": {
            "qu": qu, "sw": sw, "dl_fact": w_dl_factored, "ll_fact": w_ll_factored,
            "trib_area": tributary_area, "total_load": total_load_kg,
            "factors": {"dl": dl_factor, "ll": ll_factor} # ส่งค่า Factor กลับไปโชว์ที่ UI
        },
        "geo": {"ln": ln, "ln_calc": ln_calc, "c1": c1, "bo": p['bo'], "d": p['d'], "h_min_req": h_min_req},
        "punching": p,
        "mo": mo,
        "h_final": current_h,
        "h_warning": h_warning,
        "rebar": rebar_out,
        "as_min": as_min,
        "max_spacing_cm": max_spacing_mm / 10,
        "ratio": final_ratio
    }
