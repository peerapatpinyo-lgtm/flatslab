import numpy as np

def get_unbalanced_factor(pos):
    """
    คืนค่าตัวคูณเผื่อ Unbalanced Moment (Gamma_v estimate)
    ตามข้อกำหนด User: Edge=1.15, Corner=1.20, Interior=1.00
    """
    if pos == "Edge":
        return 1.15
    elif pos == "Corner":
        return 1.20
    return 1.0

def get_geometry_properties(c1, c2, d, pos):
    """คำนวณ bo, Acrit, Alpha_s, Beta"""
    # หน่วย: เมตร
    if pos == "Interior":
        bo = 2 * ((c1 + d) + (c2 + d))
        acrit = (c1 + d) * (c2 + d)
        alpha_s = 40
        beta = max(c1, c2) / min(c1, c2)
    elif pos == "Edge":
        # สมมติ c1 ตั้งฉากกับขอบ (Perpendicular to edge)
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
    """
    คืนค่า v_c (MPa) แยก 3 กรณีตาม ACI 318
    """
    # Eq 1: Basic
    v1 = 0.33 * np.sqrt(fc_mpa)
    
    # Eq 2: Rectangularity effect
    v2 = 0.17 * (1 + 2/beta) * np.sqrt(fc_mpa)
    
    # Eq 3: Aspect ratio effect (Column size relative to d)
    # ระวัง: d และ bo ต้องหน่วยเดียวกัน (เมตร หรือ มม. ก็ได้ เพราะตัดกัน)
    # แต่ในสูตร ACI ปกติใช้หน่วย mm สำหรับค่าคงที่
    # หากส่งเข้ามาเป็นเมตร ให้ระวังเรื่องหน่วย แต่ตรงนี้ alpha_s * d / bo เป็น dimensionless
    v3 = 0.083 * (2 + (alpha_s * d / bo)) * np.sqrt(fc_mpa)
    
    vc_mpa = min(v1, v2, v3)
    
    return v1, v2, v3, vc_mpa

def get_min_thickness_aci(ln, pos):
    """
    ความหนาขั้นต่ำตาม ACI Table 8.3.1.1 (Without Drop Panels)
    Interior: Ln/33, Exterior: Ln/30
    """
    denominator = 33.0 if pos == "Interior" else 30.0
    h_min = (ln * 1000) / denominator
    return h_min
