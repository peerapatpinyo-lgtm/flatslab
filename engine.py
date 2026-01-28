import numpy as np

def calculate_slab_logic(lx, ly, h_mm, c_w_mm, c_d_mm, fc, fy, sdl, ll, cover_mm):
    # แปลงหน่วยเป็น m และ kg
    h = h_mm / 1000
    cw = c_w_mm / 1000
    cd = c_d_mm / 1000
    cover = cover_mm / 1000
    
    # 1. Loading
    sw = h * 2400
    qu = (1.2 * (sw + sdl)) + (1.6 * ll)
    
    # 2. Geometry & Moment (DDM)
    ln = lx - cw
    mo = (qu * ly * (ln**2)) / 8
    
    # 3. Punching Shear
    d = h - cover - 0.006 # assume db=12mm
    bo = 2 * ((cw + d) + (cd + d))
    vu = qu * (lx * ly - (cw + d) * (cd + d))
    
    # ACI 318-19: Phi Vc = 0.75 * 1.1 * sqrt(f'c) * bo * d (Units converted to kg)
    phi = 0.75
    vc = 1.1 * np.sqrt(fc) * bo * d * 10 
    phi_vc = phi * vc
    punching_ratio = vu / phi_vc
    
    return {
        "qu": qu, "sw": sw, "ln": ln, "mo": mo, "d": d,
        "bo": bo, "vu": vu, "phi_vc": phi_vc, "ratio": punching_ratio
    }
