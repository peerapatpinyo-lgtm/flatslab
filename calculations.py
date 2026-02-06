# calculations.py
import numpy as np
import math

# ==========================================
# 0. THE "BRAIN" CLASS (MVC Controller Logic)
# ==========================================
class FlatSlabDesign:
    """
    Class นี้ทำหน้าที่เป็น 'Engineering Logic Controller'
    รวบรวม Logic การคำนวณทั้งหมด รวมถึง DDM และ EFM (Updated)
    """
    def __init__(self, inputs):
        self.inputs = inputs
        # Unpack parameters commonly used
        self.Lx = inputs.get('Lx', 8.0)
        self.Ly = inputs.get('Ly', 6.0)
        self.cx = inputs.get('cx', 40.0)
        self.cy = inputs.get('cy', 40.0)
        self.lc = inputs.get('lc', 3.0)  # Storey Height
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
        # Load Combination: 1.4DL + 1.7LL
        w_u = 1.4 * (w_self + self.inputs['SDL']) + 1.7 * self.inputs['LL']
        return w_u

    def _analyze_oneway(self, w_u, d_slab):
        """Logic หา Critical One-way Shear"""
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
        """Logic คำนวณ DDM Moments"""
        # Determine Effective Column for Span
        use_drop = self.has_drop and self.inputs.get('use_drop_as_support', False)
        eff_cx = self.drop_w * 100 if use_drop else self.cx # Convert m to cm if drop is used logic needs check, usually inputs are mixed units. 
        # Note: drop_w is usually in m, cx is in cm. Let's standardize to cm for this calculation logic block if needed, 
        # but the inputs say: cx (cm), drop_w (m).
        
        # Let's fix unit consistency:
        # eff_cx should be in cm to match cx
        if use_drop:
            eff_cx = self.drop_w * 100.0
            eff_cy = self.drop_l * 100.0
        else:
            eff_cx = self.cx
            eff_cy = self.cy

        # --- X-Direction ---
        ln_x = self.Lx - eff_cx/100.0
        if ln_x < 0.65 * self.Lx: ln_x = 0.65 * self.Lx # ACI Limit
        
        Mo_x = (w_u * self.Ly * ln_x**2) / 8
        M_vals_x = { 
            "M_cs_neg": 0.65 * Mo_x * 0.75, "M_ms_neg": 0.65 * Mo_x * 0.25, 
            "M_cs_pos": 0.35 * Mo_x * 0.60, "M_ms_pos": 0.35 * Mo_x * 0.40 
        }

        # --- Y-Direction ---
        ln_y = self.Ly - eff_cy/100.0
        if ln_y < 0.65 * self.Ly: ln_y = 0.65 * self.Ly
        
        Mo_y = (w_u * self.Lx * ln_y**2) / 8
        M_vals_y = { 
            "M_cs_neg": 0.65 * Mo_y * 0.75, "M_ms_neg": 0.65 * Mo_y * 0.25, 
            "M_cs_pos": 0.35 * Mo_y * 0.60, "M_ms_pos": 0.35 * Mo_y * 0.40 
        }

        return {
            "x": {
                "L_span": self.Lx, 
                "L_width": self.Ly, 
                "ln": ln_x, 
                "Mo": Mo_x, 
                "M_vals": M_vals_x,
                "c_para": eff_cx/100.0, # FIXED: Added for View
                "c_perp": eff_cy/100.0  # FIXED: Added for View
            },
            "y": {
                "L_span": self.Ly, 
                "L_width": self.Lx, 
                "ln": ln_y, 
                "Mo": Mo_y, 
                "M_vals": M_vals_y,
                "c_para": eff_cy/100.0, # FIXED: Added for View
                "c_perp": eff_cx/100.0  # FIXED: Added for View
            }
        }

    def _analyze_efm(self, w_u):
        """
        [NEW] Perform Equivalent Frame Method Analysis (Moment Distribution).
        Calculates Moments using Hardy Cross Method.
        """
        results = {}
        col_type = self.inputs['col_type'] # interior, edge, corner

        # --- X-Direction EFM ---
        # Calculate Stiffness
        Ks_x, Sum_Kc_x, Kt_x, Kec_x = calculate_stiffness(
            c1=self.cx, c2=self.cy, L1=self.Lx, L2=self.Ly, 
            lc=self.lc, h_slab=self.h_slab, fc=self.fc,
            h_drop=self.h_slab+self.h_drop if self.has_drop else None,
            drop_w=self.drop_w if self.has_drop else 0
        )
        
        # Determine Frame Condition based on col_type
        # If 'edge', we assume X direction is the critical edge span (Exterior -> Interior)
        # If 'interior', we assume symmetric interior span
        is_edge_x = True if col_type in ['edge', 'corner'] else False
        
        # Run Distribution
        moments_x = solve_efm_distribution(Kec_x, Ks_x, w_u, self.Lx, self.Ly, is_edge_span=is_edge_x)
        
        results['x'] = {
            'stiffness': {'Kec': Kec_x, 'Ks': Ks_x, 'Kt': Kt_x, 'Kc': Sum_Kc_x},
            'moments': moments_x
        }

        # --- Y-Direction EFM ---
        Ks_y, Sum_Kc_y, Kt_y, Kec_y = calculate_stiffness(
            c1=self.cy, c2=self.cx, L1=self.Ly, L2=self.Lx, 
            lc=self.lc, h_slab=self.h_slab, fc=self.fc,
            h_drop=self.h_slab+self.h_drop if self.has_drop else None,
            drop_w=self.drop_l if self.has_drop else 0
        )
        
        # If 'corner', Y is also edge. If 'edge', usually only one dir is edge (assume X).
        is_edge_y = True if col_type == 'corner' else False
        
        moments_y = solve_efm_distribution(Kec_y, Ks_y, w_u, self.Ly, self.Lx, is_edge_span=is_edge_y)
        
        results['y'] = {
            'stiffness': {'Kec': Kec_y, 'Ks': Ks_y, 'Kt': Kt_y, 'Kc': Sum_Kc_y},
            'moments': moments_y
        }
        
        return results

    def run_full_analysis(self):
        """Main entry point: สั่งคำนวณทุกอย่างรวดเดียว"""
        # 1. Prep Data
        w_u = self._calculate_loads()
        d_slab = self._get_eff_depth(self.h_slab)
        d_total = self._get_eff_depth(self.h_slab + self.h_drop)

        # 2. Shear Analysis
        shear_res = self._analyze_oneway(w_u, d_slab)

        # 3. Punching Analysis
        # Use EFM Unbalanced Moment if available? 
        # For now, let's keep it independent or user input, but we prepare for linkage.
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

        # 4. Check Requirements
        h_min = max(self.Lx, self.Ly)*100 / 33.0
        
        # 5. DDM Analysis
        ddm_res = self._analyze_ddm_moments(w_u)
        
        # 6. EFM Analysis (NEW)
        efm_res = self._analyze_efm(w_u)

        # 7. Pack Results
        return {
            "loads": {"w_u": w_u, "SDL": self.inputs['SDL'], "LL": self.inputs['LL']},
            "geometry": {"d_slab": d_slab, "d_total": d_total},
            "shear_oneway": shear_res,
            "shear_punching": punch_res,
            "ddm": ddm_res,
            "efm": efm_res, # Included new EFM results
            "checks": {"h_min": h_min}
        }

# ==========================================
# 1. PUNCHING SHEAR 
# ==========================================
def calculate_section_properties(c1, c2, d, col_type):
    """Helper to calculate Ac, Jc, and gamma_v"""
    b1 = c1 + d 
    b2 = c2 + d 

    if col_type == "edge":
        b2 = c2 + d/2.0
    elif col_type == "corner":
        b1 = c1 + d/2.0
        b2 = c2 + d/2.0

    if col_type == "interior": bo = 2*(b1 + b2)
    elif col_type == "edge": bo = 2*b1 + b2
    else: bo = b1 + b2
    
    Ac = bo * d
    # Jc simplified approximation
    Jc = (d * b1**3)/6 + (d**3 * b1)/6 + (d * b2 * b1**2)/2

    gamma_f = 1 / (1 + (2/3) * np.sqrt(b1/b2))
    gamma_v = 1 - gamma_f
    c_AB = b1 / 2.0

    return Ac, Jc, gamma_v, c_AB, bo

def check_punching_shear(Vu, fc, c1, c2, d, col_type="interior", Munbal=0.0):
    try:
        Vu = float(Vu); fc = float(fc); c1 = float(c1); c2 = float(c2); d = float(d); Munbal = float(Munbal)
    except ValueError:
        return {"status": "ERROR", "ratio": 999, "Note": "Invalid Input"}

    Ac, Jc, gamma_v, c_AB, bo = calculate_section_properties(c1, c2, d, col_type)

    Munbal_cm = Munbal * 100.0
    stress_direct = Vu / Ac
    stress_moment = (gamma_v * abs(Munbal_cm) * c_AB) / Jc
    vu_max = stress_direct + stress_moment 

    phi = 0.85 
    sqrt_fc = np.sqrt(fc)
    
    vc_stress_nominal = 1.06 * sqrt_fc 
    beta = max(c1, c2) / min(c1, c2)
    vc_beta = 0.27 * (2 + 4/beta) * sqrt_fc
    
    if col_type == "interior": alpha_s = 40
    elif col_type == "edge": alpha_s = 30
    else: alpha_s = 20
    vc_size = 0.27 * ((alpha_s * d / bo) + 2) * sqrt_fc

    vc_final_stress = min(vc_stress_nominal, vc_beta, vc_size)
    phi_vc_stress = phi * vc_final_stress

    if phi_vc_stress > 0:
        ratio = vu_max / phi_vc_stress
    else:
        ratio = 999.0
        
    status = "OK" if ratio <= 1.0 else "FAIL"

    return {
        "Vu": Vu, "Munbal": Munbal, "d": d, "bo": bo, "b0": bo, "Ac": Ac,
        "gamma_v": gamma_v, "Jc": Jc,
        "stress_actual": vu_max, "stress_allow": phi_vc_stress,
        "phi_Vc": phi_vc_stress * Ac, "Vc_nominal": vc_final_stress * Ac, 
        "ratio": ratio, "status": status,
        "note": f"Incl. Moment: {Munbal:,.0f} kg-m"
    }

# ==========================================
# 2. DUAL CASE PUNCHING
# ==========================================
def check_punching_dual_case(w_u, Lx, Ly, fc, c1, c2, d_drop, d_slab, drop_w, drop_l, col_type, Munbal=0.0):
    Vu1 = w_u * (Lx * Ly) * 0.95 
    res1 = check_punching_shear(Vu1, fc, c1, c2, d_drop, col_type, Munbal)
    res1["case"] = "Inside Drop (d_drop)" 
    
    Vu2 = w_u * (Lx * Ly) * 0.90 
    res2 = check_punching_shear(Vu2, fc, drop_w, drop_l, d_slab, col_type, Munbal * 0.5)
    res2["case"] = "Outside Drop (d_slab)" 
    
    if res1['ratio'] > res2['ratio']:
        res1['is_dual'] = True; res1['other_case'] = res2 
        return res1
    else:
        res2['is_dual'] = True; res2['other_case'] = res1
        return res2

# ==========================================
# 3. SERVICEABILITY CHECKS
# ==========================================
def check_min_reinforcement(h_slab, b_width=100.0, fy=4000.0):
    rho_min = 0.0018
    As_min = rho_min * b_width * h_slab 
    return {"rho_min": rho_min, "As_min": As_min, "note": "ACI 318 Temp/Shrinkage"}

def check_long_term_deflection(w_service, L, h, fc, As_provided, b=100.0):
    Ec = 15100 * np.sqrt(fc) 
    L_cm = L * 100.0
    w_line_kg_cm = (w_service * (b/100.0)) / 100.0 
    
    Ig = b * (h**3) / 12.0
    Ie = 0.4 * Ig 
    Delta_immediate = (5 * w_line_kg_cm * (L_cm**4)) / (384 * Ec * Ie) * 0.5 
    
    Lambda_LT = 2.0
    Delta_LT = Delta_immediate * Lambda_LT
    Delta_Total = Delta_immediate + Delta_LT
    Limit_240 = L_cm / 240.0
    status = "PASS" if Delta_Total <= Limit_240 else "FAIL"
    
    return {
        "Delta_Total": Delta_Total, "Limit_240": Limit_240, "status": status
    }

# ==========================================
# 4. EFM STIFFNESS & ANALYSIS (UPDATED)
# ==========================================
def calculate_stiffness(c1, c2, L1, L2, lc, h_slab, fc, h_drop=None, drop_w=0, drop_l=0):
    """
    Calculate EFM Stiffness (Kc, Ks, Kt, Kec)
    """
    c1=float(c1); c2=float(c2); L1=float(L1); L2=float(L2); lc=float(lc); h_slab=float(h_slab); fc=float(fc)
    
    if h_drop is None or h_drop <= h_slab or drop_w <= 0:
        h_drop = h_slab
        has_drop = False
    else:
        h_drop = float(h_drop)
        drop_w = float(drop_w)
        has_drop = True

    E_c = 15100 * np.sqrt(fc) 
    
    # 1. Column Stiffness (Kc)
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
    """
    [NEW] Perform simplified Moment Distribution Method (Hardy Cross).
    Analyzes a single span frame substitute.
    
    Args:
        Kec: Equivalent Column Stiffness
        Ks: Slab Stiffness
        w_u: Load (kg/m2)
        L_span: Span length (m)
        L_width: Width of frame (m)
        is_edge_span: Boolean, if True assumes Left=Exterior, Right=Interior.
                      if False assumes Interior (Symmetric).
    """
    # 1. Fixed End Moments (FEM)
    # Load on span W = w_u * L_width * L_span
    # FEM = w * L^2 / 12
    W_total = w_u * L_width # kg/m
    FEM = (W_total * L_span**2) / 12.0 # kg-m
    
    # 2. Distribution Factors (DF)
    # Node Left (1) and Node Right (2)
    
    if is_edge_span:
        # CASE: Edge Span (Exterior Panel)
        # Left Node (Exterior): Connects to Col (Kec) and Slab (Ks)
        sum_K1 = Kec + Ks
        DF1_slab = Ks / sum_K1
        
        # Right Node (Interior): Connects to Slab (Ks), Slab Next (Ks), Col (Kec)
        # Simplified: Assume symmetric next span -> 2*Ks + Kec
        sum_K2 = Kec + 2*Ks 
        DF2_slab = Ks / sum_K2
        
    else:
        # CASE: Interior Span (Symmetric)
        # Left & Right Nodes are identical Interior Joints
        sum_K = Kec + 2*Ks
        DF1_slab = Ks / sum_K
        DF2_slab = Ks / sum_K
    
    # 3. Moment Distribution Loop (3 Cycles)
    # Sign Convention: Clockwise +, Counter-Clockwise -
    M12 = -FEM # Left End
    M21 = +FEM # Right End
    
    for i in range(3):
        # Balance
        Bal1 = -1 * (M12) * DF1_slab
        Bal2 = -1 * (M21) * DF2_slab
        
        M12 += Bal1
        M21 += Bal2
        
        # Carry Over (Factor = 0.5)
        CO12 = Bal2 * 0.5 # Carry from 2 to 1
        CO21 = Bal1 * 0.5 # Carry from 1 to 2
        
        M12 += CO12
        M21 += CO21
        
    # 4. Result Processing
    M_neg_left = abs(M12)
    M_neg_right = abs(M21)
    
    # M_pos (Approximate by superimposing simple span moment)
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
# 5. ONE-WAY SHEAR
# ==========================================
def check_oneway_shear(Vu_face_kg, w_u_area, L_clear_m, d_eff_cm, fc):
    d_m = d_eff_cm / 100.0 
    w_line_strip = w_u_area * 1.0 
    Vu_critical = Vu_face_kg - (w_line_strip * d_m)
    if Vu_critical < 0: Vu_critical = 0
    Vc = 0.53 * np.sqrt(fc) * 100.0 * d_eff_cm
    phi = 0.85
    phi_Vc = phi * Vc
    
    if phi_Vc > 0: ratio = Vu_critical / phi_Vc
    else: ratio = 999.0
        
    status = "OK" if ratio <= 1.0 else "FAIL"
    return {
        "Vu_face": Vu_face_kg, "dist_d": d_m, "Vu_critical": Vu_critical,
        "Vc": Vc, "phi_Vc": phi_Vc, "ratio": ratio, "status": status
    }
