# calculations.py
import numpy as np
import math

# ==========================================
# HELPER: FLEXURAL DESIGN FUNCTION (NEW)
# ==========================================
def design_flexure_slab(Mu_kgm, b_cm, d_cm, h_cm, fc, fy, d_bar_mm):
    """
    คำนวณปริมาณเหล็กเสริมรับแรงดัด (Slab Flexural Design)
    Mu_kgm: Ultimate Moment (kg-m)
    b_cm: Analysis strip width (cm)
    d_cm: Effective depth (cm)
    h_cm: Slab thickness (cm)
    """
    # 1. Convert Units
    Mu_kgcm = abs(Mu_kgm) * 100.0 # Make positive for calc
    phi = 0.90 # Tension controlled for slabs

    # 2. Check Capacity (Rn)
    # Mn = Mu / phi
    # Rn = Mn / (b * d^2)
    if Mu_kgcm == 0:
        return {"As_req": 0, "rho": 0, "spacing": 0, "txt": "-"}

    Rn = Mu_kgcm / (phi * b_cm * (d_cm**2))
    
    # Check if section is too small (over reinforced limit approx)
    # rho_bal approx 0.85*beta1*fc/fy * (6120/(6120+fy)) -> simplified check
    # Let's use direct formula for rho_req
    
    term = 1 - (2 * Rn) / (0.85 * fc)
    if term < 0:
        return {
            "As_req": 999, "rho": 999, "spacing": 0, 
            "txt": "Section Too Small (Fail)", "status": "FAIL"
        }
    
    rho_req = (0.85 * fc / fy) * (1 - np.sqrt(term))
    As_req = rho_req * b_cm * d_cm

    # 3. Minimum Reinforcement (Temp & Shrinkage for Slabs)
    # ACI 318: 0.0018 * b * h
    As_min = 0.0018 * b_cm * h_cm
    
    # Design As
    As_design = max(As_req, As_min)
    
    # 4. Calculate Spacing
    # Area of 1 bar (cm2)
    A_bar = 3.1416 * (d_bar_mm/10.0)**2 / 4.0
    
    if As_design > 0:
        spacing_theoretical_cm = (A_bar / As_design) * b_cm
        # Round down to nearest 0.5 cm or 1 cm
        # Practical max spacing = 2h or 45 cm
        s_max = min(2 * h_cm, 45.0)
        s_final = min(spacing_theoretical_cm, s_max)
        
        # Format Text (e.g., DB12 @ 0.20)
        # Round spacing down to nearest 5mm (0.5cm) integer for text
        s_show_m = math.floor(s_final * 2) / 2.0 / 100.0 
        
        # If spacing is too tight (< 5cm), warn
        if s_show_m < 0.05:
            txt = f"Need > As (DB{d_bar_mm}@{s_show_m:.2f})"
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
        "spacing_cm": s_final,
        "txt": txt,
        "rho_percent": (As_design / (b_cm*d_cm)) * 100
    }


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
        self.fy = inputs.get('fy', 4000) # Added fy here
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
    
    def _calculate_service_load(self):
        """คำนวณ W (Service Load) สำหรับเช็ค Deflection"""
        w_self = (self.h_slab / 100.0) * 2400
        # Service Load: DL + LL
        w_service = (w_self + self.inputs['SDL']) + self.inputs['LL']
        return w_service

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
        """Logic คำนวณ DDM Moments และ Rebar Design"""
        # Determine Effective Column for Span
        use_drop = self.has_drop and self.inputs.get('use_drop_as_support', False)
        
        if use_drop:
            eff_cx = self.drop_w * 100.0
            eff_cy = self.drop_l * 100.0
            d_neg = self._get_eff_depth(self.h_slab + self.h_drop) # d at support (drop)
        else:
            eff_cx = self.cx
            eff_cy = self.cy
            d_neg = self._get_eff_depth(self.h_slab) # d at support (slab)
            
        d_pos = self._get_eff_depth(self.h_slab) # d at midspan is always slab thickness

        # --- Helper for processing strip design ---
        def process_strip(Mo, L_width_m, factor_cs_neg, factor_cs_pos, factor_ms_neg, factor_ms_pos):
            # Column Strip Width (approx L/2 or L_width/2)
            # Simplified: CS width = L_width / 2, MS width = L_width / 2
            b_cs = (L_width_m * 100.0) / 2.0
            b_ms = (L_width_m * 100.0) / 2.0
            
            # Moments
            M_cs_neg = 0.65 * Mo * factor_cs_neg
            M_cs_pos = 0.35 * Mo * factor_cs_pos
            M_ms_neg = 0.65 * Mo * factor_ms_neg
            M_ms_pos = 0.35 * Mo * factor_ms_pos
            
            # Design Steel
            # Note: Negative moment at support uses d_neg (could be drop), Positive uses d_pos
            h_neg = self.h_slab + self.h_drop if use_drop else self.h_slab
            
            des_cs_neg = design_flexure_slab(M_cs_neg, b_cs, d_neg, h_neg, self.fc, self.fy, self.d_bar)
            des_cs_pos = design_flexure_slab(M_cs_pos, b_cs, d_pos, self.h_slab, self.fc, self.fy, self.d_bar)
            des_ms_neg = design_flexure_slab(M_ms_neg, b_ms, d_pos, self.h_slab, self.fc, self.fy, self.d_bar) # MS usually misses drop
            des_ms_pos = design_flexure_slab(M_ms_pos, b_ms, d_pos, self.h_slab, self.fc, self.fy, self.d_bar)
            
            return {
                "M_cs_neg": M_cs_neg, "M_cs_pos": M_cs_pos,
                "M_ms_neg": M_ms_neg, "M_ms_pos": M_ms_pos,
                "design": {
                    "cs_neg": des_cs_neg, "cs_pos": des_cs_pos,
                    "ms_neg": des_ms_neg, "ms_pos": des_ms_pos
                }
            }

        # --- X-Direction ---
        ln_x = self.Lx - eff_cx/100.0
        if ln_x < 0.65 * self.Lx: ln_x = 0.65 * self.Lx
        Mo_x = (w_u * self.Ly * ln_x**2) / 8
        
        # Factors (Interior Span defaults)
        # CS Neg 0.75, CS Pos 0.60
        # MS Neg 0.25, MS Pos 0.40
        res_x = process_strip(Mo_x, self.Ly, 0.75, 0.60, 0.25, 0.40)

        # --- Y-Direction ---
        ln_y = self.Ly - eff_cy/100.0
        if ln_y < 0.65 * self.Ly: ln_y = 0.65 * self.Ly
        Mo_y = (w_u * self.Lx * ln_y**2) / 8
        
        res_y = process_strip(Mo_y, self.Lx, 0.75, 0.60, 0.25, 0.40)

        return {
            "x": {
                "L_span": self.Lx, "L_width": self.Ly, "ln": ln_x, "Mo": Mo_x, 
                "M_vals": res_x, # Contains Moments & Design
                "c_para": eff_cx/100.0, "c_perp": eff_cy/100.0
            },
            "y": {
                "L_span": self.Ly, "L_width": self.Lx, "ln": ln_y, "Mo": Mo_y, 
                "M_vals": res_y, # Contains Moments & Design
                "c_para": eff_cy/100.0, "c_perp": eff_cx/100.0
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
        w_service = self._calculate_service_load()
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

        # 4. Check Requirements
        h_min = max(self.Lx, self.Ly)*100 / 33.0
        
        # Check Deflection (Simplified)
        deflection_res = check_long_term_deflection(
            w_service, max(self.Lx, self.Ly), self.h_slab, self.fc, None
        )
        
        # 5. DDM Analysis
        ddm_res = self._analyze_ddm_moments(w_u)
        
        # 6. EFM Analysis (NEW)
        efm_res = self._analyze_efm(w_u)

        # 7. Pack Results
        return {
            "loads": {"w_u": w_u, "w_service": w_service, "SDL": self.inputs['SDL'], "LL": self.inputs['LL']},
            "geometry": {"d_slab": d_slab, "d_total": d_total},
            "shear_oneway": shear_res,
            "shear_punching": punch_res,
            "ddm": ddm_res,
            "efm": efm_res,
            "checks": {"h_min": h_min, "deflection": deflection_res}
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
    """
    Check Deflection based on ACI 318
    """
    Ec = 15100 * np.sqrt(fc) 
    L_cm = L * 100.0
    w_line_kg_cm = (w_service * (b/100.0)) / 100.0 
    
    Ig = b * (h**3) / 12.0
    Ie = 0.4 * Ig # Approximation for Cracked Moment of Inertia
    Delta_immediate = (5 * w_line_kg_cm * (L_cm**4)) / (384 * Ec * Ie) * 0.5 # Factor 0.5 for continuity
    
    Lambda_LT = 2.0
    Delta_LT = Delta_immediate * Lambda_LT
    Delta_Total = Delta_immediate + Delta_LT
    Limit_240 = L_cm / 240.0
    status = "PASS" if Delta_Total <= Limit_240 else "FAIL"
    
    return {
        "Delta_Immediate": Delta_immediate,
        "Delta_LongTerm": Delta_LT,
        "Delta_Total": Delta_Total, 
        "Limit_240": Limit_240, 
        "status": status
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
