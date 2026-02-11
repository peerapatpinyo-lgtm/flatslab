# calculations.py
import numpy as np
import math

# ==========================================
# PART 1: HELPER FUNCTIONS (CORE LOGIC)
# ==========================================

def design_flexure_slab(Mu_kgm, b_cm, d_cm, h_cm, fc, fy, d_bar_mm, phi=0.90):
    """
    คำนวณปริมาณเหล็กเสริมรับแรงดัด (Slab Flexural Design)
    Returns: Dictionary with design results
    """
    Mu_kgcm = abs(Mu_kgm) * 100.0 

    # Case: No Moment
    if Mu_kgcm == 0:
        return {"As_req": 0, "rho": 0, "spacing": 0, "txt": "-"}

    # Case: Invalid Depth
    if d_cm <= 0:
        return {"As_req": 999, "rho": 999, "spacing": 0, "txt": "Error (d<=0)", "status": "FAIL"}

    # --- Flexural Design (USD Method) ---
    # Rn = Mu / (phi * b * d^2)
    Rn = Mu_kgcm / (phi * b_cm * (d_cm**2))
    
    term = 1 - (2 * Rn) / (0.85 * fc)
    if term < 0:
        return {
            "As_req": 999, "rho": 999, "spacing": 0, 
            "txt": "Section Too Small (Fail)", "status": "FAIL"
        }
    
    rho_req = (0.85 * fc / fy) * (1 - np.sqrt(term))
    As_req = rho_req * b_cm * d_cm

    # --- Minimum Reinforcement (Temp & Shrinkage) ---
    As_min = 0.0018 * b_cm * h_cm
    As_design = max(As_req, As_min)
    
    # --- Calculate Spacing ---
    A_bar = 3.1416 * (d_bar_mm/10.0)**2 / 4.0
    
    if As_design > 0:
        spacing_theoretical_cm = (A_bar / As_design) * b_cm
        
        # Max Spacing per ACI (2h or 45cm)
        s_max = min(2 * h_cm, 45.0)
        s_final = min(spacing_theoretical_cm, s_max)
        
        # Round spacing down to nearest 0.5cm (Practical for construction)
        # Example: 18.78 -> 18.5
        s_final_rounded = math.floor(s_final * 2) / 2.0 
        
        s_show_m = s_final_rounded / 100.0 
        
        if s_final_rounded < 5.0: # < 5 cm is too tight
            txt = f"Too Tight! (DB{d_bar_mm}@{s_show_m:.2f}m)"
        else:
            txt = f"DB{d_bar_mm} @ {s_show_m:.2f} m"
    else:
        s_final = 45.0
        txt = "Min"

    return {
        "Mu": Mu_kgm,
        "As_calc": As_req,
        "As_min": As_min,
        "As_design": As_design,
        "spacing_cm": s_final if As_design > 0 else 45.0,
        "txt": txt,
        "rho_percent": (As_design / (b_cm*d_cm)) * 100 if d_cm > 0 else 0
    }

def calculate_section_properties(c1, c2, d, col_type, open_w=0, open_dist=0):
    """
    Helper to calculate Ac, Jc, and gamma_v for Punching Shear
    Note: c1, c2, d are in cm.
    """
    # Initialize variables
    bo = 0.0
    Ac = 0.0
    Jc = 0.0
    c_AB = 0.0
    
    # --- 1. Geometry Based on Column Type ---
    if col_type == "interior":
        # 4 Sides (Symmetric)
        b1 = c1 + d 
        b2 = c2 + d
        bo = 2 * (b1 + b2)
        c_AB = b1 / 2.0
        # Jc for Interior Box
        Jc = (d * b1**3)/6.0 + (d**3 * b1)/6.0 + (d * b2 * b1**2)/2.0

    elif col_type == "edge":
        # 3 Sides (U-Shape)
        # Assume Edge is parallel to c2 (y-axis), so c1 is perpendicular direction
        b1 = c1 + d/2.0  # Side perpendicular to edge
        b2 = c2 + d      # Side parallel to edge
        bo = 2*b1 + b2
        
        # Find Centroid (x_cc) from inner face
        x_cc = (2 * b1 * (b1/2.0)) / bo
        c_AB = x_cc # Distance from centroid to inner face (Max stress point)
        
        # Jc Calculation (Parallel Axis Theorem)
        I_face = (b2 * d**3)/12.0 + (b2 * d) * (x_cc**2)
        I_sides = 2.0 * ( (b1 * d**3)/12.0 + (d * b1**3)/12.0 + (b1 * d) * ((b1/2.0 - x_cc)**2) )
        Jc = I_face + I_sides

    elif col_type == "corner":
        # 2 Sides (L-Shape)
        b1 = c1 + d/2.0
        b2 = c2 + d/2.0
        bo = b1 + b2
        
        # Find Centroid
        x_cc = (b1 * (b1/2.0)) / bo
        c_AB = x_cc
        
        # Jc (Simplified)
        I_face = (b2 * d**3)/12.0 + (b2 * d) * (x_cc**2)
        I_side = (b1 * d**3)/12.0 + (d * b1**3)/12.0 + (b1 * d) * ((b1/2.0 - x_cc)**2)
        Jc = I_face + I_side

    else:
        # Fallback to interior
        b1 = c1 + d 
        b2 = c2 + d
        bo = 2 * (b1 + b2)
        c_AB = b1 / 2.0
        Jc = (d * b1**3)/6.0 + (d**3 * b1)/6.0 + (d * b2 * b1**2)/2.0

    # --- 2. Handle Opening Deduction ---
    deduction = 0
    if open_w > 0:
        limit_dist = 4 * d
        if open_dist < limit_dist:
            # Simple deduction logic: Reduce effective bo
            deduction = min(open_w, bo * 0.30)
    
    bo_eff = bo - deduction
    Ac = bo_eff * d

    # Gamma factors
    # For Edge/Corner, b1 and b2 used for gamma should be effective widths approximation
    # Using simplified code approximation here
    gamma_f = 1 / (1 + (2/3) * np.sqrt(b1/b2))
    gamma_v = 1 - gamma_f

    return Ac, Jc, gamma_v, c_AB, bo_eff, deduction

def check_punching_shear(Vu, fc, c1, c2, d, col_type="interior", Munbal=0.0, open_w=0, open_dist=0, phi=0.85):
    """
    Calculates Punching Shear Stress vs Capacity
    """
    try:
        Vu = float(Vu); fc = float(fc); c1 = float(c1); c2 = float(c2); d = float(d); Munbal = float(Munbal)
    except ValueError:
        return {"status": "ERROR", "ratio": 999, "Note": "Invalid Input"}

    Ac, Jc, gamma_v, c_AB, bo, deduc_len = calculate_section_properties(c1, c2, d, col_type, open_w, open_dist)

    if Ac <= 0: return {"status": "FAIL", "ratio": 999, "note": "Ac <= 0 (Opening too big?)"}

    Munbal_cm = Munbal * 100.0
    
    # Stress Calculation (Direct + Moment Transfer)
    stress_direct = Vu / Ac
    
    if Jc > 0:
        stress_moment = (gamma_v * abs(Munbal_cm) * c_AB) / Jc
    else:
        stress_moment = 0
        
    vu_max = stress_direct + stress_moment 

    # Capacity
    sqrt_fc = np.sqrt(fc)
    
    vc_stress_nominal = 1.06 * sqrt_fc 
    beta = max(c1, c2) / min(c1, c2) if min(c1, c2) > 0 else 1.0
    vc_beta = 0.27 * (2 + 4/beta) * sqrt_fc
    
    if col_type == "interior": alpha_s = 40
    elif col_type == "edge": alpha_s = 30
    else: alpha_s = 20
    
    if bo > 0:
        vc_size = 0.27 * ((alpha_s * d / bo) + 2) * sqrt_fc
    else:
        vc_size = vc_stress_nominal

    vc_final_stress = min(vc_stress_nominal, vc_beta, vc_size)
    
    # Apply Phi
    phi_vc_stress = phi * vc_final_stress

    if phi_vc_stress > 0:
        ratio = vu_max / phi_vc_stress
    else:
        ratio = 999.0
        
    status = "OK" if ratio <= 1.0 else "FAIL"
    
    # Create note string
    note_txt = f"Munbal: {Munbal:,.0f} kg-m | ϕ={phi}"
    if deduc_len > 0:
        note_txt += f" | Op.Deduct: {deduc_len:.1f} cm"

    return {
        "Vu": Vu, "Munbal": Munbal, "d": d, "bo": bo, "Ac": Ac,
        "deduction": deduc_len,
        "gamma_v": gamma_v, "Jc": Jc,
        "stress_actual": vu_max, "stress_allow": phi_vc_stress,
        "phi_Vc": phi_vc_stress * Ac, "Vc_nominal": vc_final_stress * Ac, 
        "ratio": ratio, "status": status,
        "note": note_txt
    }

def check_punching_dual_case(w_u, Lx, Ly, fc, c1, c2, d_drop, d_slab, drop_w, drop_l, col_type, Munbal=0.0, phi=0.85):
    """
    Handle Drop Panel (Check 2 perimeters: Inside Drop & Outside Drop)
    """
    # Case 1: At Column Face (Inside Drop) - Uses d_drop
    Vu1 = w_u * (Lx * Ly) * 0.95 
    res1 = check_punching_shear(Vu1, fc, c1, c2, d_drop, col_type, Munbal, phi=phi) 
    res1["case"] = "Inside Drop (d_drop)" 
    
    # Case 2: At Drop Panel Edge (Outside Drop) - Uses d_slab
    # Note: Outside drop generally acts as "interior" geometry relative to the slab unless the drop is huge.
    # We maintain col_type but use drop dimensions as the "column" size.
    Vu2 = w_u * (Lx * Ly) * 0.90 
    res2 = check_punching_shear(Vu2, fc, drop_w*100, drop_l*100, d_slab, col_type, Munbal * 0.5, phi=phi)
    res2["case"] = "Outside Drop (d_slab)" 
    
    if res1['ratio'] > res2['ratio']:
        res1['is_dual'] = True; res1['other_case'] = res2 
        return res1
    else:
        res2['is_dual'] = True; res2['other_case'] = res1
        return res2

def check_oneway_shear(Vu_face_kg, w_u_area, L_clear_m, d_eff_cm, fc, phi=0.85):
    """
    Check One-Way Shear (Beam Shear)
    """
    d_m = d_eff_cm / 100.0 
    w_line_strip = w_u_area * 1.0 
    Vu_critical = Vu_face_kg - (w_line_strip * d_m)
    if Vu_critical < 0: Vu_critical = 0
    
    Vc = 0.53 * np.sqrt(fc) * 100.0 * d_eff_cm
    
    # Apply Phi
    phi_Vc = phi * Vc
    
    if phi_Vc > 0: ratio = Vu_critical / phi_Vc
    else: ratio = 999.0
        
    status = "OK" if ratio <= 1.0 else "FAIL"
    return {
        "Vu_face": Vu_face_kg, "dist_d": d_m, "Vu_critical": Vu_critical,
        "Vc": Vc, "phi_Vc": phi_Vc, "ratio": ratio, "status": status
    }

def check_min_reinforcement(h_slab, b_width=100.0, fy=4000.0):
    rho_min = 0.0018
    As_min = rho_min * b_width * h_slab 
    return {"rho_min": rho_min, "As_min": As_min, "note": "ACI 318 Temp/Shrinkage"}

def check_long_term_deflection(w_service, L, h, fc, As_provided, b=100.0):
    """
    Approximate Long Term Deflection Check
    """
    Ec = 15100 * np.sqrt(fc) 
    L_cm = L * 100.0
    w_line_kg_cm = (w_service * (b/100.0)) / 100.0 
    
    Ig = b * (h**3) / 12.0
    Ie = 0.4 * Ig # Simplified Effective Inertia
    Delta_immediate = (5 * w_line_kg_cm * (L_cm**4)) / (384 * Ec * Ie) * 0.5 
    
    Lambda_LT = 2.0
    Delta_LT = Delta_immediate * Lambda_LT
    Delta_Total = Delta_immediate + Delta_LT
    
    # General limit L/240
    Limit_240 = L_cm / 240.0
    status = "PASS" if Delta_Total <= Limit_240 else "FAIL"
    
    return {
        "Delta_Immediate": Delta_immediate,
        "Delta_LongTerm": Delta_LT,
        "Delta_Total": Delta_Total, 
        "Limit_240": Limit_240, 
        "status": status
    }

def check_ddm_limitations(L1, L2, num_spans=3, L_adjacent=None):
    """
    ตรวจสอบเงื่อนไขบังคับของ DDM ตามมาตรฐาน ACI 318
    Returns: (is_valid, warnings_list)
    """
    warnings = []
    is_valid = True

    # 1. Check Number of Spans (Must have at least 3 continuous spans)
    if num_spans < 3:
        warnings.append(f"Warning: Number of spans ({num_spans}) < 3. DDM allows only for >= 3 continuous spans.")
        # We assume valid for calculation sake but warn user
    
    # 2. Check Aspect Ratio (Long/Short <= 2.0)
    ratio = max(L1, L2) / min(L1, L2)
    if ratio > 2.0:
        warnings.append(f"Violation: Panel Aspect Ratio {ratio:.2f} > 2.0. ACI prohibits DDM (Use EFM).")
        is_valid = False

    # 3. Check Adjacent Span Difference (<= 1/3)
    # Only applicable if L_adjacent is provided
    if L_adjacent is not None and L_adjacent > 0:
        longer = max(L1, L_adjacent)
        shorter = min(L1, L_adjacent)
        diff_ratio = (longer - shorter) / longer
        if diff_ratio > 0.333: # 1/3
            warnings.append(f"Violation: Adjacent span difference {diff_ratio*100:.1f}% > 33%. ACI prohibits DDM.")
            is_valid = False

    return is_valid, warnings

# ==========================================
# PART 2: EFM STIFFNESS & ANALYSIS
# ==========================================

def calculate_stiffness(c1, c2, L1, L2, lc, h_slab, fc, h_drop=None, drop_w=0, drop_l=0):
    c1=float(c1); c2=float(c2); L1=float(L1); L2=float(L2); lc=float(lc); h_slab=float(h_slab); fc=float(fc)
    
    # Logic: h_drop passed here should be the TOTAL thickness if exists
    if h_drop is None or h_drop <= h_slab or drop_w <= 0:
        h_drop = h_slab
        has_drop = False
    else:
        h_drop = float(h_drop)
        drop_w = float(drop_w)
        has_drop = True

    E_c = 15100 * np.sqrt(fc) 
    
    # 1. Column Stiffness (Kc)
    # Ic = b * h^3 / 12 -> Here c2 is width, c1 is depth in direction of analysis
    Ic = c2 * (c1**3) / 12.0 
    lc_cm = lc * 100.0
    Kc = 4 * E_c * Ic / lc_cm
    Sum_Kc = 2 * Kc
    
    # 2. Slab Stiffness (Ks)
    Is = (L2*100.0) * (h_slab**3) / 12.0
    L1_cm = L1 * 100.0
    Ks = 4 * E_c * Is / L1_cm
    
    # 3. Torsional Stiffness (Kt)
    def get_C(x, y): return (1 - 0.63 * x / y) * (x**3 * y) / 3.0
    y = c1 
    C_slab = get_C(h_slab, y)
    
    if has_drop:
        # If Drop exists and is structural, h_drop here is Total Thickness
        C_drop = get_C(h_drop, y)
        len_total = L2 * 100.0
        len_drop = min(drop_w * 100.0, len_total)
        len_slab = max(0, len_total - len_drop)
        if C_drop > 0 and C_slab > 0:
            term_drop = len_drop / C_drop
            term_slab = len_slab / C_slab
            C_eff = len_total / (term_drop + term_slab)
        else: C_eff = C_slab
    else: C_eff = C_slab
        
    term_geom = (1 - c2/(L2*100.0))
    if term_geom <= 0: term_geom = 0.01
    denom = (L2*100.0 * term_geom**3)
    
    if denom > 0: Kt = 2 * 9 * E_c * C_eff / denom 
    else: Kt = 0
    
    # 4. Equivalent Stiffness (Kec)
    if Kt > 0 and Sum_Kc > 0:
        Kec = 1 / (1/Sum_Kc + 1/Kt)
    else: Kec = 0
        
    return Ks, Sum_Kc, Kt, Kec

def solve_efm_distribution(Kec, Ks, w_u, L_span, L_width, is_edge_span=False):
    W_total = w_u * L_width # kg/m
    FEM = (W_total * L_span**2) / 12.0 # kg-m
    
    if is_edge_span:
        # Edge Span: Exterior node connects to Col (Kec) + Slab (Ks)
        sum_K1 = Kec + Ks
        DF1_slab = Ks / sum_K1 if sum_K1 > 0 else 0
        
        # Interior node: Slab + Slab(next) + Col
        sum_K2 = Kec + 2*Ks 
        DF2_slab = Ks / sum_K2 if sum_K2 > 0 else 0
    else:
        # Interior Span: Symmetric
        sum_K = Kec + 2*Ks
        DF1_slab = Ks / sum_K if sum_K > 0 else 0
        DF2_slab = Ks / sum_K if sum_K > 0 else 0
    
    # Moment Distribution (3 Cycles)
    M12 = -FEM 
    M21 = +FEM 
    
    for i in range(3):
        # Balance
        Bal1 = -1 * (M12) * DF1_slab
        Bal2 = -1 * (M21) * DF2_slab
        
        M12 += Bal1
        M21 += Bal2
        
        # Carry Over
        CO12 = Bal2 * 0.5 
        CO21 = Bal1 * 0.5 
        
        M12 += CO12
        M21 += CO21
        
    M_neg_left = abs(M12)
    M_neg_right = abs(M21)
    
    M_simple = (W_total * L_span**2) / 8.0
    M_pos = M_simple - (M_neg_left + M_neg_right)/2.0
    
    return {
        "FEM": FEM,
        "DF_left": DF1_slab,
        "DF_right": DF2_slab,
        "M_neg_left": M_neg_left,
        "M_neg_right": M_neg_right,
        "M_pos": M_pos,
        "M_simple": M_simple
    }

# ==========================================
# PART 3: MAIN CONTROLLER CLASS (UPDATED)
# ==========================================
class FlatSlabDesign:
    """
    Class นี้ทำหน้าที่เป็น 'Engineering Logic Controller'
    รวบรวม Logic การคำนวณทั้งหมด
    """
    def __init__(self, inputs, factors=None):
        self.inputs = inputs
        
        # --- [SAFETY CRITICAL] Load Factors & Phi Configuration ---
        if factors:
            self.factors = factors
            # Auto-detect Code Standard based on Live Load Factor
            # Modern Code (ACI 318-02+): 1.6 LL -> Phi Shear = 0.75
            # Old Code (ACI 318-99/EIT): 1.7 LL -> Phi Shear = 0.85
            if self.factors.get('LL', 1.7) < 1.65:
                self.factors['phi_shear'] = 0.75
                self.factors['phi_flexure'] = 0.90
                self.factors['code_ref'] = "ACI 318 Modern (phi=0.75)"
            else:
                self.factors['phi_shear'] = 0.85
                self.factors['phi_flexure'] = 0.90
                self.factors['code_ref'] = "ACI 318-99/EIT (phi=0.85)"
        else:
            # Default fallback (Old EIT style as safety base)
            self.factors = {
                'DL': 1.4, 'LL': 1.7, 
                'phi_shear': 0.85, 'phi_flexure': 0.90,
                'code_ref': "Default"
            }

        self.Lx = inputs.get('Lx', 8.0)
        self.Ly = inputs.get('Ly', 6.0)
        self.cx = inputs.get('cx', 40.0)
        self.cy = inputs.get('cy', 40.0)
        self.lc = inputs.get('lc', 3.0) 
        self.h_slab = inputs.get('h_slab', 20.0)
        self.cover = inputs.get('cover', 2.5)
        self.d_bar = inputs.get('d_bar', 12)
        self.fc = inputs.get('fc', 240)
        self.fy = inputs.get('fy', 4000)
        
        # Drop Panel Inputs
        self.has_drop = inputs.get('has_drop', False)
        self.h_drop = inputs.get('h_drop', 0.0) # This is usually projection below slab
        self.drop_w = inputs.get('drop_w', 0.0)
        self.drop_l = inputs.get('drop_l', 0.0)

        # --- NEW: Check ACI Drop Panel Compliance ---
        self.is_structural_drop = False
        self.drop_status_msg = "No Drop"
        
        if self.has_drop:
            self._check_aci_drop_compliance()

    def _check_aci_drop_compliance(self):
        """
        [NEW] ตรวจสอบขนาด Drop Panel ตาม ACI 318
        1. ความหนายื่นลงมา (Projection) >= h_slab / 4
        2. ระยะยื่นออกจากศูนย์กลางเสา (Extension) >= L / 6 ในแต่ละทิศทาง
        """
        # 1. Check Projection (Thickness)
        min_proj = self.h_slab / 4.0
        pass_thick = self.h_drop >= min_proj

        # 2. Check Extension (Length)
        # Assuming Drop is centered: Extension = Width / 2
        # ACI: Extend L/6 from center-line of support
        min_ext_x = self.Lx / 6.0
        min_ext_y = self.Ly / 6.0
        
        actual_ext_x = self.drop_w / 2.0
        actual_ext_y = self.drop_l / 2.0
        
        pass_size = (actual_ext_x >= min_ext_x) and (actual_ext_y >= min_ext_y)

        if pass_thick and pass_size:
            self.is_structural_drop = True
            self.drop_status_msg = "OK (Structural Drop)"
        else:
            self.is_structural_drop = False
            # สร้างข้อความแจ้งเตือนว่าทำไมถึงตกเกณฑ์
            reasons = []
            if not pass_thick: reasons.append(f"Too Thin (<{min_proj:.1f}cm)")
            if not pass_size: reasons.append(f"Too Small (<L/6)")
            self.drop_status_msg = f"Acts as Shear Cap Only ({', '.join(reasons)})"

    def _get_eff_depth(self, h_total):
        d = h_total - self.cover - (self.d_bar / 10.0) / 2.0
        return max(d, 1.0) # Prevent zero or negative depth

    def _calculate_loads(self):
        w_self = (self.h_slab / 100.0) * 2400
        
        # --- Use Dynamic Factors ---
        f_dl = self.factors.get('DL', 1.4)
        f_ll = self.factors.get('LL', 1.7)
        
        w_u = f_dl * (w_self + self.inputs['SDL']) + f_ll * self.inputs['LL']
        return w_u
    

    def _calculate_service_load(self):
    # คำนวณน้ำหนักตัวเอง (Dead Load)
    w_self = (self.h_slab / 100.0) * 2400
    
    # ใช้ .get() เพื่อป้องกัน Error ถ้าไม่มีค่า SDL หรือ LL ส่งมา
    # ถ้าหาไม่เจอ จะถือว่าเป็น 0.0 โดยอัตโนมัติ
    sdl = self.inputs.get('SDL', 0.0)
    ll = self.inputs.get('LL', 0.0)
    
    w_service = (w_self + sdl) + ll
    return w_service

    def _analyze_oneway(self, w_u, d_slab):
        # Extract Correct Phi
        phi_s = self.factors.get('phi_shear', 0.85)

        # 1. X-Direction
        Vu_face_x = w_u * (self.Lx / 2.0) - w_u * (self.cx / 100.0 / 2.0)
        res_x = check_oneway_shear(Vu_face_x, w_u, self.Lx - self.cx/100.0, d_slab, self.fc, phi=phi_s)
        
        # 2. Y-Direction
        Vu_face_y = w_u * (self.Ly / 2.0) - w_u * (self.cy / 100.0 / 2.0)
        res_y = check_oneway_shear(Vu_face_y, w_u, self.Ly - self.cy/100.0, d_slab, self.fc, phi=phi_s)

        # 3. Compare & Return Winner
        if res_x['ratio'] > res_y['ratio']:
            res_x['critical_dir'] = "X-Axis"
            return res_x
        else:
            res_y['critical_dir'] = "Y-Axis"
            return res_y

    def _analyze_ddm_moments(self, w_u):
        """
        [UPDATED] คำนวณ Moment DDM โดยแยกกรณี Interior vs Exterior Span
        อ้างอิง ACI 318 Table 8.10.4.2 (Distribution of Mo)
        และ Table 8.10.5.x (Column Strip %)
        """
        phi_f = self.factors.get('phi_flexure', 0.90)

        # 1. Determine Effective Depth (d)
        # [MODIFIED] Use check result to decide effective depth
        use_drop_for_flexure = self.has_drop and self.is_structural_drop
        
        if use_drop_for_flexure:
            eff_cx = self.drop_w * 100.0
            eff_cy = self.drop_l * 100.0
            # Think of drop as T-beam web -> use full depth
            d_neg = self._get_eff_depth(self.h_slab + self.h_drop)
        else:
            # Shear Cap -> Ignore thickness for flexure
            eff_cx = self.cx
            eff_cy = self.cy
            d_neg = self._get_eff_depth(self.h_slab)
            
        d_pos = self._get_eff_depth(self.h_slab)

        # 2. Helper for Coefficients (ACI 318 Tables)
        def get_coeffs(span_type):
            """
            Return (neg_ext, pos, neg_int) fractions of Mo
            Assuming: Flat Plate (No Edge Beam) - Case C in ACI Table
            """
            if span_type == 'interior_span':
                # Typical Interior Span
                return 0.65, 0.35, 0.65
            else:
                # Exterior Span (Flat Plate / No Edge Beam)
                # Ref: ACI 318-19 Table 8.10.4.2
                # Ext Neg: 0.26 | Pos: 0.52 | Int Neg: 0.70
                return 0.26, 0.52, 0.70

        def get_cs_percent(span_type, moment_type):
            """
            Return % of Moment assigned to Column Strip
            Ref: ACI 318-19 Table 8.10.5.1, 8.10.5.2, 8.10.5.5
            """
            # Alpha_f1 * L2/L1 is assumed 0 for Flat Plate (No Beams)
            # Beta_t is assumed 0 for Flat Plate (No Edge Beams)
            
            if span_type == 'interior_span':
                if moment_type == 'neg': return 0.75 # Interior Neg
                if moment_type == 'pos': return 0.60 # Positive
            else:
                # Exterior Span
                if moment_type == 'neg_ext': return 1.00 # Exterior Edge (100% to CS for Flat Plate)
                if moment_type == 'pos': return 0.60     # Positive
                if moment_type == 'neg_int': return 0.75 # Interior Support
            
            return 0.75 # Default fallback

        # 3. Process Strip Logic
        def process_strip_smart(Mo, L_width_m, span_type):
            # Get Distribution Factors
            f_neg_ext, f_pos, f_neg_int = get_coeffs(span_type)
            
            # Calculate Total Moments
            M_total_neg_ext = Mo * f_neg_ext
            M_total_pos     = Mo * f_pos
            M_total_neg_int = Mo * f_neg_int
            
            # Get CS Percentages
            pct_cs_neg_ext = get_cs_percent(span_type, 'neg_ext')
            pct_cs_pos     = get_cs_percent(span_type, 'pos')
            pct_cs_neg_int = get_cs_percent(span_type, 'neg_int')
            
            # --- Column Strip Moments ---
            M_cs_neg_ext = M_total_neg_ext * pct_cs_neg_ext
            M_cs_pos     = M_total_pos     * pct_cs_pos
            M_cs_neg_int = M_total_neg_int * pct_cs_neg_int
            
            # --- Middle Strip Moments (Remainder) ---
            M_ms_neg_ext = M_total_neg_ext - M_cs_neg_ext
            M_ms_pos     = M_total_pos     - M_cs_pos
            M_ms_neg_int = M_total_neg_int - M_cs_neg_int
            
            # Use thickness based on compliance
            h_neg = self.h_slab + self.h_drop if use_drop_for_flexure else self.h_slab
            b_strip = (L_width_m * 100.0) / 2.0 # Half strip width for CS/MS usually
            
            # Design Reinforcement
            # Note: For Exterior Edge, check if b_cs fits within slab? 
            # (Simplified here: assume standard widths)
            
            # 1. Exterior Support (Top)
            des_cs_neg_ext = design_flexure_slab(M_cs_neg_ext, b_strip, d_neg, h_neg, self.fc, self.fy, self.d_bar, phi=phi_f)
            des_ms_neg_ext = design_flexure_slab(M_ms_neg_ext, b_strip, d_neg, self.h_slab, self.fc, self.fy, self.d_bar, phi=phi_f)
            
            # 2. Mid Span (Bottom)
            des_cs_pos = design_flexure_slab(M_cs_pos, b_strip, d_pos, self.h_slab, self.fc, self.fy, self.d_bar, phi=phi_f)
            des_ms_pos = design_flexure_slab(M_ms_pos, b_strip, d_pos, self.h_slab, self.fc, self.fy, self.d_bar, phi=phi_f)
            
            # 3. Interior Support (Top)
            des_cs_neg_int = design_flexure_slab(M_cs_neg_int, b_strip, d_neg, h_neg, self.fc, self.fy, self.d_bar, phi=phi_f)
            des_ms_neg_int = design_flexure_slab(M_ms_neg_int, b_strip, d_neg, self.h_slab, self.fc, self.fy, self.d_bar, phi=phi_f)

            return {
                "coeffs": (f_neg_ext, f_pos, f_neg_int),
                "M_total": (M_total_neg_ext, M_total_pos, M_total_neg_int),
                "design": {
                    "cs_neg_ext": des_cs_neg_ext, "ms_neg_ext": des_ms_neg_ext,
                    "cs_pos": des_cs_pos,         "ms_pos": des_ms_pos,
                    "cs_neg_int": des_cs_neg_int, "ms_neg_int": des_ms_neg_int
                }
            }

        # --- Main Execution ---
        col_type = self.inputs['col_type']

        # Determine Span Type for X and Y directions
        # Logic: If col_type is Edge/Corner, the span perpendicular to edge is "Exterior Span"
        
        # X-Direction Analysis
        ln_x = self.Lx - eff_cx/100.0
        if ln_x < 0.65 * self.Lx: ln_x = 0.65 * self.Lx
        Mo_x = (w_u * self.Ly * ln_x**2) / 8
        
        # Check if X-span is Exterior
        # Assume Edge Column is along Y-axis (Standard convention usually implies Edge means 1 side open)
        # Simplified logic: 
        # If 'edge' -> we assume it's an Exterior Span in the direction perpendicular to the edge
        # Ideally, we need to know WHICH edge, but for single panel calc:
        # We will assume WORST CASE: Treat as Exterior Span if it's an Edge/Corner column
        span_type_x = 'exterior_span' if col_type in ['edge', 'corner'] else 'interior_span'
        res_x = process_strip_smart(Mo_x, self.Ly, span_type_x)

        # Y-Direction Analysis
        ln_y = self.Ly - eff_cy/100.0
        if ln_y < 0.65 * self.Ly: ln_y = 0.65 * self.Ly
        Mo_y = (w_u * self.Lx * ln_y**2) / 8
        
        span_type_y = 'exterior_span' if col_type == 'corner' else 'interior_span'
        # Note: For 'edge' column, usually only one direction is exterior. 
        # But if user doesn't specify direction, corner is safe assumption for both, 
        # edge usually implies X is perp. Let's stick to X=Ext for Edge, Y=Int for Edge.
        if col_type == 'edge': span_type_y = 'interior_span'
            
        res_y = process_strip_smart(Mo_y, self.Lx, span_type_y)

        return {
            "x": {
                "L_span": self.Lx, "L_width": self.Ly, "ln": ln_x, "Mo": Mo_x, 
                "span_type": span_type_x,
                "M_vals": res_x, "c_para": eff_cx/100.0, "c_perp": eff_cy/100.0
            },
            "y": {
                "L_span": self.Ly, "L_width": self.Lx, "ln": ln_y, "Mo": Mo_y, 
                "span_type": span_type_y,
                "M_vals": res_y, "c_para": eff_cy/100.0, "c_perp": eff_cx/100.0
            }
        }


    
    def _analyze_efm(self, w_u):
        """Perform Equivalent Frame Method Analysis."""
        results = {}
        col_type = self.inputs['col_type'] 

        # [UPDATED] Determine dimensions to pass for Stiffness
        # If it's a Shear Cap (not structural drop), pass None/0 to ignore stiffness contribution
        if self.has_drop and self.is_structural_drop:
            # Stiffness Calc expects Total Thickness in 'h_drop' parameter
            calc_h_drop = self.h_slab + self.h_drop
            calc_drop_w = self.drop_w
            calc_drop_l = self.drop_l
        else:
            calc_h_drop = None
            calc_drop_w = 0
            calc_drop_l = 0

        # --- X-Direction EFM ---
        Ks_x, Sum_Kc_x, Kt_x, Kec_x = calculate_stiffness(
            c1=self.cx, c2=self.cy, L1=self.Lx, L2=self.Ly, 
            lc=self.lc, h_slab=self.h_slab, fc=self.fc,
            h_drop=calc_h_drop,
            drop_w=calc_drop_w
        )
        is_edge_x = True if col_type in ['edge', 'corner'] else False
        moments_x = solve_efm_distribution(Kec_x, Ks_x, w_u, self.Lx, self.Ly, is_edge_span=is_edge_x)
        results['x'] = {'stiffness': {'Kec': Kec_x}, 'moments': moments_x}

        # --- Y-Direction EFM ---
        Ks_y, Sum_Kc_y, Kt_y, Kec_y = calculate_stiffness(
            c1=self.cy, c2=self.cx, L1=self.Ly, L2=self.Lx, 
            lc=self.lc, h_slab=self.h_slab, fc=self.fc,
            h_drop=calc_h_drop,
            drop_w=calc_drop_l
        )
        is_edge_y = True if col_type == 'corner' else False
        moments_y = solve_efm_distribution(Kec_y, Ks_y, w_u, self.Ly, self.Lx, is_edge_span=is_edge_y)
        results['y'] = {'stiffness': {'Kec': Kec_y}, 'moments': moments_y}
        
        return results

    def run_full_analysis(self):
        """Main entry point: Updated Sequence to Link EFM Moment to Punching"""
        # 1. Prep Data
        w_u = self._calculate_loads()
        w_service = self._calculate_service_load()
        d_slab = self._get_eff_depth(self.h_slab)
        
        # For Punching Shear Check: ALWAYS use physical dimensions (Structural Drop OR Shear Cap)
        # Because even a Shear Cap helps punching shear.
        d_punching_total = self._get_eff_depth(self.h_slab + self.h_drop)

        # 2. DDM Limitations Check
        # Assumes valid if num_spans/L_adj are missing (simplified for single panel app)
        ddm_valid, ddm_warn = check_ddm_limitations(
            self.Lx, self.Ly, 
            num_spans=self.inputs.get('num_spans', 3), 
            L_adjacent=self.inputs.get('L_adjacent', None)
        )

        # 3. Shear Analysis (One-way)
        shear_res = self._analyze_oneway(w_u, d_slab)

        # ============================================================
        # 4. RUN EFM FIRST (Move Up) -> To Get Unbalanced Moments
        # ============================================================
        efm_res = self._analyze_efm(w_u)
        
        # Extract Munbal Logic:
        col_type = self.inputs['col_type']
        
        # X-Direction Munbal
        Munbal_x = 0
        if col_type in ['edge', 'corner']:
             Munbal_x = efm_res['x']['moments']['M_neg_left'] # Left node is exterior
        
        # Y-Direction Munbal
        Munbal_y = 0
        if col_type == 'corner':
             Munbal_y = efm_res['y']['moments']['M_neg_left']

        # Design Munbal (Max of X or Y)
        Munbal_design = max(abs(Munbal_x), abs(Munbal_y))

        # ============================================================
        # 5. PUNCHING ANALYSIS (Updated with Openings, EFM Moment & Dynamic Phi)
        # ============================================================
        # NOTE: Shear Caps (even if not Structural Drops) still help with Punching Shear
        op_w = self.inputs.get('open_w', 0.0)
        op_dist = self.inputs.get('open_dist', 0.0)
        
        # Extract Phi for Shear
        phi_s = self.factors.get('phi_shear', 0.85)

        if self.has_drop:
            # Use d_punching_total here (Physical depth)
            punch_res = check_punching_dual_case(
                w_u, self.Lx, self.Ly, self.fc, 
                self.cx, self.cy, d_punching_total, d_slab, 
                self.drop_w, self.drop_l, self.inputs['col_type'],
                Munbal=Munbal_design,
                phi=phi_s
            )
            # Add Status Note to Punching Result
            punch_res['drop_status'] = self.drop_status_msg
        else:
            c1_d = self.cx + d_slab
            c2_d = self.cy + d_slab
            area_crit = (c1_d/100.0) * (c2_d/100.0)
            Vu_punch = w_u * (self.Lx*self.Ly - area_crit)
            
            punch_res = check_punching_shear(
                Vu_punch, self.fc, self.cx, self.cy, d_slab, 
                self.inputs['col_type'], 
                Munbal=Munbal_design, 
                open_w=op_w, open_dist=op_dist,
                phi=phi_s
            )
            punch_res['drop_status'] = "No Drop"

        # 6. DDM Analysis
        # Will automatically use flat plate design if is_structural_drop is False
        ddm_res = self._analyze_ddm_moments(w_u)
        
        # 7. Deflection Check (Using estimated As from Middle Strip Positive Moment)
        # We need an estimate of As provided to check long term deflection.
        # Use Middle Strip As_design as a representative baseline.
        as_prov_est = ddm_res['x']['M_vals']['design']['ms_pos']['As_design']
        
        deflect_res = check_long_term_deflection(
            w_service, self.Lx, self.h_slab, self.fc,
            as_prov_est, 
            b=100.0
        )

        # 8. Assemble Final Result
        return {
            "inputs": self.inputs,
            "loads": {"w_u": w_u, "w_service": w_service},
            "shear": shear_res,
            "punching": punch_res,
            "efm": efm_res,
            "ddm": ddm_res,
            "deflection": deflect_res,
            "warnings": ddm_warn,
            "compliance": {
                "ddm_valid": ddm_valid,
                "drop_panel": self.drop_status_msg
            }
        }
