import numpy as np

def calculate_detailed_slab(lx, ly, h_mm, c1_mm, c2_mm, fc_ksc, fy_ksc, sdl, ll, cover_mm, pos="Interior"):
    # 1. การแปลงหน่วย (Unit Conversion)
    h = h_mm / 1000
    c1 = c1_mm / 1000  # ด้านขนานกับทิศทางพิจารณา
    c2 = c2_mm / 1000  # ด้านตั้งฉาก
    d = (h_mm - cover_mm - 12) / 1000 # assume DB12
    fc_mpa = fc_ksc * 0.0980665
    fy_mpa = fy_ksc * 0.0980665

    # 2. Loading
    sw = h * 2400
    qu = (1.2 * (sw + sdl)) + (1.6 * ll)
    
    # 3. Static Moment (DDM)
    ln = lx - c1
    mo = (qu * ly * (ln**2)) / 8

    # 4. Moment Distribution (Simplified ACI Coefficients for Flat Plate)
    # Total Negative = 0.65Mo, Total Positive = 0.35Mo
    m_neg_total = 0.65 * mo
    m_pos_total = 0.35 * mo
    
    # Distribution to Column Strip (CS) and Middle Strip (MS)
    # ตามมาตรฐาน ACI (โดยประมาณสำหรับไม่มีคานขอบ)
    results_moments = {
        "CS_Neg": 0.75 * m_neg_total,
        "MS_Neg": 0.25 * m_neg_total,
        "CS_Pos": 0.60 * m_pos_total,
        "MS_Pos": 0.40 * m_pos_total
    }

    # 5. Punching Shear Check (3 Formulas)
    # กำหนด bo และ beta ตามตำแหน่งเสา
    if pos == "Interior":
        bo = 2 * ((c1 + d) + (c2 + d))
        alpha_s = 40
    elif pos == "Edge":
        bo = (2 * (c1 + d/2)) + (c2 + d)
        alpha_s = 30
    else: # Corner
        bo = (c1 + d/2) + (c2 + d/2)
        alpha_s = 20
    
    beta = max(c1, c2) / min(c1, c2)
    
    # คำนวณ Vc (MPa) ตาม ACI 318-19 (0.33 coefficient for metric)
    vc1 = 0.33 * np.sqrt(fc_mpa)
    vc2 = 0.17 * (1 + 2/beta) * np.sqrt(fc_mpa)
    vc3 = 0.083 * (2 + (alpha_s * d / bo)) * np.sqrt(fc_mpa)
    
    vc_mpa_min = min(vc1, vc2, vc3)
    phi = 0.75
    # แปลง Vc กลับเป็น kg: (MPa * 10.197 kg/cm2) * (Area in cm2)
    phi_vc = phi * (vc_mpa_min * 10.197) * (bo * 100 * d * 100)
    
    # Vu Calculation
    vu = qu * (lx * ly - (c1 + d) * (c2 + d))
    
    # 6. Validation & Recommendation
    recommended_h = h_mm
    if vu > phi_vc:
        # ประมาณการความหนาใหม่โดยวนลูปเพิ่มทีละ 10 มม.
        temp_h = h_mm
        while True:
            temp_h += 10
            temp_d = (temp_h - cover_mm - 12) / 1000
            # คำนวณ bo ใหม่ตาม temp_d
            if pos == "Interior": temp_bo = 2*((c1+temp_d)+(c2+temp_d))
            elif pos == "Edge": temp_bo = (2*(c1+temp_d/2))+(c2+temp_d)
            else: temp_bo = (c1+temp_d/2)+(c2+temp_d/2)
            
            temp_vc = min(0.33, 0.17*(1+2/beta), 0.083*(2+(alpha_s*temp_d/temp_bo))) * np.sqrt(fc_mpa)
            temp_phi_vc = phi * (temp_vc * 10.197) * (temp_bo * 100 * temp_d * 100)
            temp_qu = (1.2 * ((temp_h/1000)*2400 + sdl)) + (1.6 * ll)
            temp_vu = temp_qu * (lx * ly - (c1 + temp_d) * (c2 + temp_d))
            
            if temp_vu <= temp_phi_vc:
                recommended_h = temp_h
                break

    return {
        "mo": mo, "moments": results_moments, "vu": vu, "phi_vc": phi_vc,
        "ratio": vu/phi_vc, "recommended_h": recommended_h, "bo": bo, "d": d
    }
