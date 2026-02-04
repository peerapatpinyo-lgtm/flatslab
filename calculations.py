import numpy as np
import math

# ==========================================
# 0. THE "BRAIN" CLASS (NEW: MVC Controller Logic)
# ==========================================
class FlatSlabDesign:
    """
    Class นี้ทำหน้าที่เป็น 'Engineering Logic Controller'
    รวบรวม Logic จาก app.py เดิม มาจัดระเบียบใหม่
    """
    def __init__(self, inputs):
        self.inputs = inputs
        # Unpack parameters commonly used
        self.Lx = inputs.get('Lx', 8.0)
        self.Ly = inputs.get('Ly', 6.0)
        self.cx = inputs.get('cx', 40.0)
        self.cy = inputs.get('cy', 40.0)
        self.h_slab = inputs.get('h_slab', 20.0)
        self.cover = inputs.get('cover', 2.5)
        self.d_bar = inputs.get('d_bar', 12)
        self.fc = inputs.get('fc', 240)
        self.has_drop = inputs.get('has_drop', False)
        self.h_drop = inputs.get('h_drop', 0.0)
        self.drop_w = inputs.get('drop_w', 0.0)
        self.drop_l = inputs.get('drop_l', 0.0)

    def _get_eff_depth(self, h_total):
        """Internal helper: Calculate d (cm)"""
        return h_total - self.cover - (self.d_bar / 10.0) / 2.0

    def _calculate_loads(self):
        """คำนวณ Wu (ULS)"""
        w_self = (self.h_slab / 100.0) * 2400
        # ใช้สูตร Load Combination เดิมของคุณ
        w_u = 1.4 * (w_self + self.inputs['SDL']) + 1.7 * self.inputs['LL']
        return w_u

    def _analyze_oneway(self, w_u, d_slab):
        """Logic หา Critical One-way Shear (ย้ายมาจาก app.py)"""
        # 1. X-Direction
        Vu_face_x = w_u * (self.Lx / 2.0) - w_u * (self.cx / 100.0 / 2.0)
        res_x = check_oneway_shear(Vu_face_x, w_u, self.Lx - self.cx/100.0, d_slab, self.fc)
        
        # 2. Y-Direction
        Vu_face_y = w_u * (self.Ly / 2.0) - w_u * (self.cy / 100.0 / 2.0)
        res_y = check_oneway_shear(Vu_face_y, w_u, self.Ly - self.cy/100.0, d_slab, self.fc)

        # 3. Compare & Return Winner
        if res_x['ratio'] > res_y['ratio']:
            res_x['critical_dir'] = "X-Axis"
            return res_x
        else:
            res_y['critical_dir'] = "Y-Axis"
            return res_y

    def _analyze_ddm_moments(self, w_u):
        """Logic คำนวณ DDM Moments (ย้ายมาจาก app.py)"""
        # Determine Effective Column for Span (ถ้าใช้ Drop เป็น Support ก็ลดระยะ ln ลง)
        use_drop = self.has_drop and self.inputs.get('use_drop_as_support', False)
        eff_cx = self.drop_w if use_drop else self.cx
        eff_cy = self.drop_l if use_drop else self.cy

        # --- X-Direction ---
        ln_x = self.Lx - eff_cx/100.0
        Mo_x = (w_u * self.Ly * ln_x**2) / 8
        M_vals_x = { 
            "M_cs_neg": 0.65 * Mo_x * 0.75, "M_ms_neg": 0.65 * Mo_x * 0.25, 
            "M_cs_pos": 0.35 * Mo_x * 0.60, "M_ms_pos": 0.35 * Mo_x * 0.40 
        }

        # --- Y-Direction ---
        ln_y = self.Ly - eff_cy/100.0
        Mo_y = (w_u * self.Lx * ln_y**2) / 8
        M_vals_y = { 
            "M_cs_neg": 0.65 * Mo_y * 0.75, "M_ms_neg": 0.65 * Mo_y * 0.25, 
            "M_cs_pos": 0.35 * Mo_y * 0.60, "M_ms_pos": 0.35 * Mo_y * 0.40 
        }

        return {
            "x": {"L_span": self.Lx, "L_width": self.Ly, "ln": ln_x, "Mo": Mo_x, "M_vals": M_vals_x},
            "y": {"L_span": self.Ly, "L_width": self.Lx, "ln": ln_y, "Mo": Mo_y, "M_vals": M_vals_y}
        }

    def run_full_analysis(self):
        """Main entry point: สั่งคำนวณทุกอย่างรวดเดียว"""
        # 1. Prep Data
        w_u = self._calculate_loads()
        d_slab = self._get_eff_depth(self.h_slab)
        d_total = self._get_eff_depth(self.h_slab + self.h_drop)

        # 2. Shear Analysis
        shear_res = self._analyze_oneway(w_u, d_slab)

        # 3. Punching Analysis
        if self.has_drop:
            punch_res = check_punching_dual_case(
                w_u, self.Lx, self.Ly, self.fc, 
                self.cx, self.cy, d_total, d_slab, 
                self.drop_w, self.drop_l, self.inputs['col_type']
            )
        else:
            c1_d = self.cx + d_slab
            c2_d = self.cy + d_slab
            area_crit = (c1_d/100.0) * (c2_d/100.0)
            Vu_punch = w_u * (self.Lx*self.Ly - area_crit)
            punch_res = check_punching_shear(
                Vu_punch, self.fc, self.cx, self.cy, d_slab, self.inputs['col_type']
            )

        # 4. Check Requirements (Min Thickness)
        h_min = max(self.Lx, self.Ly)*100 / 33.0
        
        # 5. DDM Analysis
        ddm_res = self._analyze_ddm_moments(w_u)

        # 6. Pack Results
        return {
            "loads": {"w_u": w_u, "SDL": self.inputs['SDL'], "LL": self.inputs['LL']},
            "geometry": {"d_slab": d_slab, "d_total": d_total},
            "shear_oneway": shear_res,
            "shear_punching": punch_res,
            "ddm": ddm_res,
            "checks": {"h_min": h_min}
        }

# ==========================================
# 1. PUNCHING SHEAR (ORIGINAL FUNCTIONS)
# ==========================================
def calculate_section_properties(c1, c2, d, col_type):
    """
    Helper to calculate Ac, Jc, and gamma_v for Moment Transfer.
    Geometry is based on ACI 318 Critical Section at d/2 from face.
    """
    # Critical section dimensions
    b1 = c1 + d  # Width parallel to moment (c1 direction)
    b2 = c2 + d  # Width perpendicular to moment (c2 direction)

    # Adjust based on column type (Approximate geometry)
    if col_type == "edge":
        # Assume Edge parallel to moment (3 sides)
        b2 = c2 + d/2.0
    elif col_type == "corner":
        # Corner (2 sides)
        b1 = c1 + d/2.0
        b2 = c2 + d/2.0

    # 1. Perimeter (bo) & Area (Ac)
    if col_type == "interior":
        bo = 2*(b1 + b2)
    elif col_type == "edge":
        bo = 2*b1 + b2
    else: # corner
        bo = b1 + b2
    
    Ac = bo * d

    # 2. Polar Moment of Inertia (Jc)
    # Using Standard Interior Formula (Box Section)
    Jc = (d * b1**3)/6 + (d**3 * b1)/6 + (d * b2 * b1**2)/2

    # 3. Fraction of Moment Transferred by Shear (gamma_v)
    gamma_f = 1 / (1 + (2/3) * np.sqrt(b1/b2))
    gamma_v = 1 - gamma_f
    
    # Distance from centroid to edge (c_AB)
    c_AB = b1 / 2.0

    return Ac, Jc, gamma_v, c_AB, bo

def check_punching_shear(Vu, fc, c1, c2, d, col_type="interior", Munbal=0.0):
    """
    Check punching shear considering Direct Shear (Vu) + Unbalanced Moment (Munbal).
    """
    try:
        Vu = float(Vu); fc = float(fc); c1 = float(c1); c2 = float(c2); d = float(d); Munbal = float(Munbal)
    except ValueError:
        return {"status": "ERROR", "ratio": 999, "Note": "Invalid Input"}

    # 1. Get Section Properties
    Ac, Jc, gamma_v, c_AB, bo = calculate_section_properties(c1, c2, d, col_type)

    # 2. Determine Shear Stress (vu_max)
    Munbal_cm = Munbal * 100.0
    
    # Stress from Gravity Load
    stress_direct = Vu / Ac
    
    # Stress from Unbalanced Moment
    stress_moment = (gamma_v * abs(Munbal_cm) * c_AB) / Jc
    
    # Total Stress
    vu_max = stress_direct + stress_moment # ksc (kg/cm^2)

    # 3. Allowable Shear Stress (phi_vc)
    phi = 0.85 
    sqrt_fc = np.sqrt(fc)
    
    # Vc calculation (Stress units - kg/cm^2)
    # 3.1 Basic
    vc_stress_nominal = 1.06 * sqrt_fc 
    
    # 3.2 Rectangularity effect (beta)
    beta = max(c1, c2) / min(c1, c2)
    vc_beta = 0.27 * (2 + 4/beta) * sqrt_fc
    
    # 3.3 Size effect (alpha_s)
    if col_type == "interior": alpha_s = 40
    elif col_type == "edge": alpha_s = 30
    else: alpha_s = 20
    vc_size = 0.27 * ((alpha_s * d / bo) + 2) * sqrt_fc

    # Governing Vc
    vc_final_stress = min(vc_stress_nominal, vc_beta, vc_size)
    phi_vc_stress = phi * vc_final_stress

    # 4. Check Ratio
    if phi_vc_stress > 0:
        ratio = vu_max / phi_vc_stress
    else:
        ratio = 999.0
        
    status = "OK" if ratio <= 1.0 else "FAIL"

    # 5. Return (With Legacy Keys for UI Compatibility)
    return {
        "Vu": Vu,
        "Munbal": Munbal,
        "d": d,
        "d_avg": d,
        
        # Geometry
        "bo": bo,          # New key
        "b0": bo,          # !!! COMPATIBILITY FIX: Alias for legacy tab_calc.py !!!
        "Ac": Ac,
        "beta": beta,      
        "alpha_s": alpha_s, 
        
        # Analysis
        "gamma_v": gamma_v,
        "Jc": Jc,
        "stress_actual": vu_max,       # v_u (combined)
        "stress_allow": phi_vc_stress, # phi*v_c
        
        # Force Equivalents (For Legacy UI Display)
        "phi_Vc": phi_vc_stress * Ac, # Equivalent Capacity Force
        "Vc_nominal": vc_final_stress * Ac, 
        
        # Result
        "ratio": ratio,
        "status": status,
        "note": f"Incl. Moment: {Munbal:,.0f} kg-m",
        "check_type": "stress" # Flag to tell UI this is stress-based
    }

# ==========================================
# 2. DUAL CASE PUNCHING (DROP PANEL)
# ==========================================
def check_punching_dual_case(w_u, Lx, Ly, fc, c1, c2, d_drop, d_slab, drop_w, drop_l, col_type, Munbal=0.0):
    """
    Checks two critical sections:
    1. Inside Drop Panel (using d_drop)
    2. Outside Drop Panel (using d_slab)
    """
    # Case 1: Inner (Drop Depth)
    Vu1 = w_u * (Lx * Ly) * 0.95 
    res1 = check_punching_shear(Vu1, fc, c1, c2, d_drop, col_type, Munbal)
    res1["case"] = "Inside Drop (d_drop)" 
    
    # Case 2: Outer (Slab Depth)
    Vu2 = w_u * (Lx * Ly) * 0.90 
    res2 = check_punching_shear(Vu2, fc, drop_w, drop_l, d_slab, col_type, Munbal * 0.5)
    res2["case"] = "Outside Drop (d_slab)" 
    
    # Return the governing (worst) case
    if res1['ratio'] > res2['ratio']:
        res1['is_dual'] = True
        res1['other_case'] = res2 
        return res1
    else:
        res2['is_dual'] = True
        res2['other_case'] = res1
        return res2

# ==========================================
# 3. REINFORCEMENT & SERVICEABILITY CHECKS
# ==========================================
def check_min_reinforcement(h_slab, b_width=100.0, fy=4000.0):
    """
    Calculate Minimum Temperature & Shrinkage Reinforcement (ACI 318).
    rho_min = 0.0018 for Deformed bars (fy=4000 ksc / Grade 60)
    """
    rho_min = 0.0018
    As_min = rho_min * b_width * h_slab # cm^2 per meter strip (if b=100)
    
    return {
        "rho_min": rho_min,
        "As_min": As_min, # cm2
        "note": "Based on ACI 318 Temp/Shrinkage (0.0018)"
    }

def check_long_term_deflection(w_service, L, h, fc, As_provided, b=100.0):
    """
    Estimate Long-Term Deflection including Creep & Shrinkage.
    """
    # 1. Material Properties
    Ec = 15100 * np.sqrt(fc) # ksc
    
    # 2. Immediate Deflection (Elastic)
    L_cm = L * 100.0
    w_line_kg_cm = (w_service * (b/100.0)) / 100.0 # kg/cm per strip
    
    Ig = b * (h**3) / 12.0
    
    # Effective Moment of Inertia (Ie) - Cracked Section approximation
    Ie = 0.4 * Ig # Avg constant for cracked flat plate (Simplified ACI)
    
    # Deflection Formula (Continuous Beam Approx coeff ~1/200 range)
    # Using coefficient 5/384 * 0.5 (Continuity Factor)
    Delta_immediate = (5 * w_line_kg_cm * (L_cm**4)) / (384 * Ec * Ie) * 0.5 
    
    # 3. Long Term Multiplier (Lambda)
    Lambda_LT = 2.0
    
    Delta_LT = Delta_immediate * Lambda_LT
    Delta_Total = Delta_immediate + Delta_LT
    
    # 4. Allowable
    Limit_240 = L_cm / 240.0
    
    status = "PASS" if Delta_Total <= Limit_240 else "FAIL"
    
    return {
        "Delta_Immediate": Delta_immediate,
        "Delta_LongTerm": Delta_LT,
        "Delta_Total": Delta_Total,
        "Limit_240": Limit_240,
        "status": status,
        "I_effective": Ie
    }

# ==========================================
# 4. EFM STIFFNESS
# ==========================================
def calculate_stiffness(c1, c2, L1, L2, lc, h_slab, fc, h_drop=None, drop_w=0, drop_l=0):
    """
    Calculate EFM Stiffness (Kc, Ks, Kt, Kec)
    Advanced Update: Supports Drop Panel effect on Torsional Stiffness (Kt)
    """
    # Ensure inputs are float
    c1=float(c1); c2=float(c2); L1=float(L1); L2=float(L2); lc=float(lc); h_slab=float(h_slab); fc=float(fc)
    
    # Handle Drop Panel dimensions (default to slab if no drop)
    if h_drop is None or h_drop <= h_slab or drop_w <= 0:
        h_drop = h_slab
        has_drop = False
    else:
        h_drop = float(h_drop)
        drop_w = float(drop_w) # Width of drop (perpendicular to L1 usually, check input mapping)
        has_drop = True

    E_c = 15100 * np.sqrt(fc) # ksc
    
    # ==============================
    # 1. Column Stiffness (Kc)
    # ==============================
    Ic = c2 * (c1**3) / 12.0 
    lc_cm = lc * 100.0
    Kc = 4 * E_c * Ic / lc_cm
    Sum_Kc = 2 * Kc
    
    # ==============================
    # 2. Slab Stiffness (Ks)
    # ==============================
    # Simplified: Assuming gross section of slab
    Is = (L2*100.0) * (h_slab**3) / 12.0
    L1_cm = L1 * 100.0
    Ks = 4 * E_c * Is / L1_cm
    
    # ==============================
    # 3. Torsional Stiffness (Kt)
    # ==============================
    # Helper to calc C constant
    def get_C(x, y):
        # x = thickness, y = width (c1)
        return (1 - 0.63 * x / y) * (x**3 * y) / 3.0
    
    y = c1 # Width of torsional member is column width c1
    
    # 3.1 Calculate C for Slab and Drop sections
    C_slab = get_C(h_slab, y)
    
    if has_drop:
        C_drop = get_C(h_drop, y)
        
        # Calculate Effective C using Harmonic Mean
        len_total = L2 * 100.0
        len_drop = min(drop_w * 100.0, len_total) # Drop width in cm
        len_slab = max(0, len_total - len_drop)
        
        # Inverse weighted average (1/C_eff = sum(L_i/C_i) / L_total)
        if C_drop > 0 and C_slab > 0:
            term_drop = len_drop / C_drop
            term_slab = len_slab / C_slab
            C_eff = len_total / (term_drop + term_slab)
        else:
            C_eff = C_slab
    else:
        C_eff = C_slab
        
    # 3.2 Calculate Kt
    # Kt = 9 E C / [L2 * (1 - c2/L2)^3]
    term_geom = (1 - c2/(L2*100.0))
    if term_geom <= 0: term_geom = 0.01
    denom = (L2*100.0 * term_geom**3)
    
    if denom > 0:
        Kt = 2 * 9 * E_c * C_eff / denom 
        # Note: Multiplied by 2 for both sides of the joint
    else:
        Kt = 0
    
    # ==============================
    # 4. Equivalent Stiffness (Kec)
    # ==============================
    if Kt > 0 and Sum_Kc > 0:
        Kec = 1 / (1/Sum_Kc + 1/Kt)
    else:
        Kec = 0
        
    return Ks, Sum_Kc, Kt, Kec

# ==========================================
# 5. ONE-WAY SHEAR (UPDATED FOR UNIT CONSISTENCY)
# ==========================================
def check_oneway_shear(Vu_face_kg, w_u_area, L_clear_m, d_eff_cm, fc):
    """
    ตรวจสอบแรงเฉือนแบบคาน (One-Way Shear)
    Standard: พิจารณาต่อความกว้าง 1 เมตร (1.0 m Strip)
    """
    # 1. แปลงหน่วยและเตรียมตัวแปร (คิดต่อแถบกว้าง 1 เมตร)
    d_m = d_eff_cm / 100.0  # แปลง d เป็นเมตร
    
    # 2. คำนวณ Vu ที่ระยะ d จากผิวเสา (Critical Section)
    w_line_strip = w_u_area * 1.0 
    
    Vu_critical = Vu_face_kg - (w_line_strip * d_m)
    if Vu_critical < 0: Vu_critical = 0
    
    # 3. คำนวณกำลังรับแรงเฉือนของคอนกรีต (Vc)
    Vc = 0.53 * np.sqrt(fc) * 100.0 * d_eff_cm
    
    # 4. ตรวจสอบ
    phi = 0.85
    phi_Vc = phi * Vc
    
    if phi_Vc > 0:
        ratio = Vu_critical / phi_Vc
    else:
        ratio = 999.0
        
    status = "OK" if ratio <= 1.0 else "FAIL"
    
    return {
        "Vu_face": Vu_face_kg,
        "dist_d": d_m,
        "Vu_critical": Vu_critical,
        "Vc": Vc,
        "phi_Vc": phi_Vc,
        "ratio": ratio,
        "status": status
    }
