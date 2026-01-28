import numpy as np

def calculate_detailed_slab(lx, ly, h_mm, c1_mm, c2_mm, fc_ksc, fy_ksc, sdl, ll, cover_mm, pos="Interior"):
    # --- 1. การเตรียมข้อมูลและหน่วย (Initial Setup) ---
    h = h_mm / 1000
    c1 = c1_mm / 1000  # ด้านขนาน lx
    c2 = c2_mm / 1000  # ด้านขนาน ly
    d = (h_mm - cover_mm - 12) / 1000  # Effective depth (assume DB12)
    
    # แปลงหน่วยเป็น SI สำหรับการคำนวณมาตรฐาน
    fc_mpa = fc_ksc * 0.0980665
    fy_mpa = fy_ksc * 0.0980665
    g = 9.80665

    # Check DDM Limitation
    ratio = max(lx, ly) / min(lx, ly)
    ddm_warning = "DDM Limits OK" if ratio <= 2.0 else "Ratio exceeds DDM limits (L/W > 2)"

    # --- 2. การคำนวณน้ำหนัก (Loading) ---
    sw = h * 2400
    qu = (1.2 * (sw + sdl)) + (1.6 * ll)

    # --- 3. การคำนวณโมเมนต์ (Static Moment Mo) ---
    # ตรวจสอบ ln >= 0.65lx
    ln_raw = lx - c1
    ln = max(ln_raw, 0.65 * lx)
    mo = (qu * ly * (ln**2)) / 8

    # --- 4. การคำนวณแรงเฉือนทะลุ (Punching Shear Logic) ---
    def check_punching(current_h_mm):
        curr_h = current_h_mm / 1000
        curr_d = (current_h_mm - cover_mm - 12) / 1000
        
        # กำหนด bo และ Tributary Area (Atrib) ตามตำแหน่งเสา
        if pos == "Interior":
            bo = 2 * ((c1 + curr_d) + (c2 + curr_d))
            a_crit = (c1 + curr_d) * (c2 + curr_d)
            alpha_s = 40
        elif pos == "Edge":
            # สมมติเสาอยู่ที่ขอบด้าน ly (ด้าน lx สั้นลง)
            bo = (2 * (c1 + curr_d/2)) + (c2 + curr_d)
            a_crit = (c1 + curr_d/2) * (c2 + curr_d)
            alpha_s = 30
        else: # Corner
            bo = (c1 + curr_d/2) + (c2 + curr_d/2)
            a_crit = (c1 + curr_d/2) * (c2 + curr_d/2)
            alpha_s = 20

        beta = max(c1, c2) / min(c1, c2)
        
        # คำนวณ Vc (MPa) 3 สูตรของ ACI
        f1 = 0.33 * np.sqrt(fc_mpa)
        f2 = 0.17 * (1 + 2/beta) * np.sqrt(fc_mpa)
        f3 = 0.083 * (2 + (alpha_s * curr_d / bo)) * np.sqrt(fc_mpa)
        vc_mpa = min(f1, f2, f3)
        
        # แรงเฉือนต้านทาน (kg)
        # Newton = MPa * Area(mm2) -> kg = Newton / g
        phi_vc_kg = (0.75 * vc_mpa * (bo * 1000 * curr_d * 1000)) / g
        
        # แรงเฉือนที่เกิดขึ้น Vu (kg)
        curr_qu = (1.2 * ((curr_h * 2400) + sdl)) + (1.6 * ll)
        vu_kg = curr_qu * ((lx * ly) - a_crit)
        
        return vu_kg, phi_vc_kg, bo, curr_d

    # วนลูปหาความหนาที่เหมาะสม (Iterative Design)
    current_h = h_mm
    status = "Success"
    while True:
        vu, phi_vc, bo_final, d_final = check_punching(current_h)
        if vu <= phi_vc:
            break
        current_h += 10
        if current_h > 600:
            status = "Failed (Slab too thick > 600mm)"
            break

    # --- 5. การกระจายโมเมนต์และเหล็กเสริม (Moment & Rebar) ---
    # Distribution factors
    m_neg_total = 0.65 * mo
    m_pos_total = 0.35 * mo
    
    moments = {
        "CS_Neg": 0.75 * m_neg_total,
        "MS_Neg": 0.25 * m_neg_total,
        "CS_Pos": 0.60 * m_pos_total,
        "MS_Pos": 0.40 * m_pos_total
    }

    # คำนวณ As (Required vs Min)
    # As_min = 0.0018 * b * h (cm2)
    as_min_per_m = 0.0018 * 100 * (current_h / 10) 
    
    rebar_results = {}
    phi_flex = 0.9
    for key, M in moments.items():
        # b สำหรับ strip (m) - พิจารณาเฉลี่ยต่อเมตรเพื่อความง่ายใน UI
        # As = M / (phi * fy * j * d) โดย j ประมาณ 0.9
        as_req = (M * 100) / (phi_flex * fy_ksc * (d_final * 100 * 0.9))
        rebar_results[key] = {
            "As_req": max(as_req / ly, as_min_per_m), # cm2/m
            "As_min": as_min_per_m
        }

    return {
        "status": status,
        "ddm_warning": ddm_warning,
        "qu": qu,
        "mo": mo,
        "vu": vu,
        "phi_vc": phi_vc,
        "h_final": current_h,
        "bo": bo_final,
        "rebar": rebar_results,
        "ratio": vu / phi_vc if phi_vc > 0 else 0
    }
