import numpy as np

def get_geometry_properties(c1, c2, d, pos):
    """คำนวณ bo และ Acrit ตามตำแหน่งเสา"""
    # c1, c2, d must be in same unit (e.g., meters)
    if pos == "Interior":
        bo = 2 * ((c1 + d) + (c2 + d))
        acrit = (c1 + d) * (c2 + d)
        alpha_s = 40
        beta = max(c1, c2) / min(c1, c2)
    elif pos == "Edge":
        # Assume c1 is perpendicular to edge
        bo = (2 * (c1 + d/2)) + (c2 + d)
        acrit = (c1 + d/2) * (c2 + d)
        alpha_s = 30
        beta = max(c1, c2) / min(c1, c2)
    else: # Corner
        bo = (c1 + d/2) + (c2 + d/2)
        acrit = (c1 + d/2) * (c2 + d/2)
        alpha_s = 20
        beta = 1.0
        
    return bo, acrit, alpha_s, beta

def calc_aci_shear_capacity(fc_mpa, beta, alpha_s, d, bo):
    """คืนค่า v_c (MPa) ทั้ง 3 สูตรของ ACI"""
    # Eq 1
    v1 = 0.33 * np.sqrt(fc_mpa)
    # Eq 2
    v2 = 0.17 * (1 + 2/beta) * np.sqrt(fc_mpa)
    # Eq 3
    v3 = 0.083 * (2 + (alpha_s * d / bo)) * np.sqrt(fc_mpa)
    
    vc_mpa = min(v1, v2, v3)
    return v1, v2, v3, vc_mpa

def check_punching_shear(qu, lx, ly, acrit, bo, d, vc_mpa, unbalanced_factor=1.0):
    """ตรวจสอบ Vu vs Phi*Vc"""
    # Vu = qu * (TribArea - Acrit)
    vu_force = qu * ((lx * ly) - acrit) * unbalanced_factor
    
    # Phi Vc (Force) -> Phi = 0.75
    # Convert MPa to Force (N) then to same unit as Vu (Assume Vu is kg, so need care)
    # Let's keep physics unit agnostic, passing conversion factor if needed.
    # Here we assume inputs are standardized. 
    # But to be safe, let's return the raw Force Capacity in Newtons if inputs are SI.
    pass 
    # *Logic moved to Engine to handle Unit Conversion (kg <-> N)*
    return vu_force
