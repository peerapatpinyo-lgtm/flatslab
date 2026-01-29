import streamlit as st
import math

# ==========================================
# 1. CONFIG & SETUP
# ==========================================
st.set_page_config(page_title="Flat Slab ACI 318-19 Design", layout="wide", page_icon="🏢")

# ==========================================
# 2. MODULE: FORMATTER (Show the Math)
# ==========================================
def fmt_header(text):
    return r"\textbf{" + text + "}"

def fmt_load_analysis(h_mm, sdl, ll, sw, dl, qu):
    return r"""
    \begin{aligned}
    SW &= \text{Thickness} \times 2400 = \frac{%.0f}{1000} \times 2400 = %.1f \; kg/m^2 \\
    DL &= SW + SDL = %.1f + %.1f = %.1f \; kg/m^2 \\
    q_u &= 1.2(DL) + 1.6(LL) \quad (\text{ACI 318-19}) \\
        &= 1.2(%.1f) + 1.6(%.1f) \\
        &= \mathbf{%.1f} \; kg/m^2
    \end{aligned}
    """ % (h_mm, sw, sw, sdl, dl, dl, ll, qu)

def fmt_punching_geometry(pos, c1, c2, d, b1, b2, bo, gamma_v):
    return r"""
    \begin{aligned}
    \text{Location} &: \textbf{%s} \\
    d_{avg} &= %.1f \; mm \\
    b_1 &= c_1 + d/.. = %.1f \; mm \quad (\text{Dim along moment axis}) \\
    b_2 &= c_2 + d/.. = %.1f \; mm \quad (\text{Dim perp to moment axis}) \\
    b_o &= \mathbf{%.0f} \; mm \quad (\text{Critical Perimeter}) \\
    \gamma_v &= 1 - \frac{1}{1 + \frac{2}{3}\sqrt{b_1/b_2}} = 1 - \frac{1}{1 + 0.67\sqrt{%.0f/%.0f}} = \mathbf{%.2f}
    \end{aligned}
    """ % (pos, d, b1, b2, bo, b1, b2, gamma_v)

def fmt_vu_calc(qu, lx, ly, a_inside, vu):
    return r"""
    \begin{aligned}
    A_{total} &= L_x \times L_y = %.2f \times %.2f = %.2f \; m^2 \\
    A_{inside} &= \text{Area inside } b_o = %.4f \; m^2 \\
    V_u &= q_u(A_{total} - A_{inside}) \\
        &= %.1f(%.2f - %.4f) \\
        &= \mathbf{%.1f} \; kg \quad (\approx %.1f \; kN)
    \end{aligned}
    """ % (lx, ly, lx*ly, a_inside, qu, lx*ly, a_inside, vu, vu*9.81/1000)

def fmt_shear_check(vu_design, phi_vc, ratio, status):
    color = "green" if status == "PASS" else "red"
    return r"""
    \begin{aligned}
    V_{u,design} &= V_u \times \text{Mag.Factor} \approx \mathbf{%.1f} \; kN \\
    \phi V_c &= \mathbf{%.1f} \; kN \\
    \text{D/C Ratio} &= \frac{%.1f}{%.1f} = \textcolor{%s}{\mathbf{%.2f}} \quad (\textbf{%s})
    \end{aligned}
    """ % (vu_design/1000*9.81, phi_vc/1000*9.81, 
           vu_design/1000*9.81, phi_vc/1000*9.81, color, ratio, status)

def fmt_flexure_design(layer, mu, d, a_req, a_prov, db, s, rho_chk, h_chk):
    c_res = "green" if rho_chk == "OK" else "red"
    h_res = "green" if h_chk == "OK" else "red"
    
    # Quadratic solution display for 'a'
    return r"""
    \begin{aligned}
    \text{Layer} &: \text{%s} \quad (d = %.1f mm) \\
    M_u &= %.1f \; kN \cdot m \\
    A_{s,req} &= \text{Whitney Eq.} \rightarrow \mathbf{%.2f} \; cm^2 \\
    \text{Try} &: \text{DB%d @ %.0f mm} \rightarrow A_{s,prov} = \mathbf{%.2f} \; cm^2 \\
    \text{Checks} &: \text{Min/Max Rebar} \to \textcolor{%s}{\textbf{%s}}, \quad \text{Spacing} \to \textcolor{%s}{\textbf{%s}}
    \end{aligned}
    """ % (layer, d, mu, a_req, db, s, a_prov, c_res, rho_chk, h_res, h_chk)

# ==========================================
# 3. MODULE: ENGINE (ACI 318-19 Logic)
# ==========================================
GRAV = 9.80665
CONCRETE_DENSITY = 2400

def solve_whitney(mu_kNm, fc_mpa, fy_mpa, b_mm, d_mm):
    """
    Solves Quadratic Equation for As required based on Whitney Stress Block
    Mu = phi * As * fy * (d - a/2)
    a = (As * fy) / (0.85 * fc * b)
    Returns: As_req (cm2)
    """
    phi = 0.9
    mu_Nmm = mu_kNm * 1e6
    
    # Coefficients for A_s^2 * (const) - A_s * (const) + Mu = 0
    # Derived from Mu = phi*As*fy*(d - (As*fy)/(1.7*fc*b))
    
    alpha = (phi * fy_mpa**2) / (1.7 * fc_mpa * b_mm)
    beta = - (phi * fy_mpa * d_mm)
    gamma = mu_Nmm
    
    # Quadratic Formula: x = [-b +/- sqrt(b^2 - 4ac)] / 2a
    # Here x is As (mm2)
    
    try:
        delta = beta**2 - 4 * alpha * gamma
        if delta < 0: return 9999.9 # Impossible to reinforce (Section too small)
        
        as_mm2 = (-beta - math.sqrt(delta)) / (2 * alpha)
        return as_mm2 / 100.0 # Convert to cm2
    except:
        return 9999.9

def run_analysis(lx, ly, h_mm, c1_mm, c2_mm, sdl, ll, fc_ksc, fy_ksc, cover_mm, pos, top_db, top_sp, bot_db, bot_sp):
    # --- 1. Material & Geometry ---
    fc_mpa = fc_ksc * 0.0980665
    fy_mpa = fy_ksc * 0.0980665
    
    # Different d for layers (Outer = Lx direction assumed)
    d_outer = h_mm - cover_mm - (top_db/2) # Long direction
    d_inner = h_mm - cover_mm - top_db - (top_db/2) # Short direction
    d_avg = (d_outer + d_inner) / 2.0
    
    # --- 2. Load Analysis (ACI 318-19) ---
    sw = (h_mm / 1000.0) * CONCRETE_DENSITY
    dl = sw + sdl
    qu = (1.2 * dl) + (1.6 * ll) # Changed to 1.2D + 1.6L
    
    # --- 3. Punching Shear (Advanced) ---
    # 3.1 Critical Perimeter (bo) & Gamma_v
    # c1 = dimension parallel to moment, c2 = perpendicular
    
    if pos == "Interior":
        # 4 sides
        b1 = c1_mm + d_avg
        b2 = c2_mm + d_avg
        bo = 2 * (b1 + b2)
        a_inside = (b1 * b2) / 1e6 # m2
        alpha_s = 40
        mag_factor = 1.0 # Negligible transfer
        
    elif pos == "Edge":
        # 3 sides (Assume c1 is perpendicular to edge for worst case usually, 
        # but here we assume c1 is the column depth relative to moment)
        # Standard Edge: 2 sides of c1+d/2, 1 side of c2+d
        b1 = c1_mm + (d_avg/2) 
        b2 = c2_mm + d_avg
        bo = (2 * b1) + b2 
        a_inside = (b1 * b2) / 1e6
        alpha_s = 30
        mag_factor = 1.25 # Simplified stress magnification for edge
        
    else: # Corner
        # 2 sides
        b1 = c1_mm + (d_avg/2)
        b2 = c2_mm + (d_avg/2)
        bo = b1 + b2
        a_inside = (b1 * b2) / 1e6
        alpha_s = 20
        mag_factor = 1.30 # Simplified stress magnification for corner
    
    # Unbalanced Moment Factor gamma_v (ACI Eq)
    gamma_v = 1 - (1 / (1 + (2/3) * math.sqrt(b1/b2)))

    # 3.2 Demand (Vu)
    # Deduct area inside critical perimeter
    area_total = lx * ly
    vu_kg = qu * (area_total - a_inside)
    
    # Apply magnification for check (Simplified approach for app)
    # Real design would calc Jc and Munbal. Here we use factor.
    vu_design_kg = vu_kg * mag_factor
    
    # 3.3 Capacity (Phi Vc)
    beta = max(c1_mm, c2_mm) / min(c1_mm, c2_mm)
    
    vc1 = 0.33 * math.sqrt(fc_mpa) * bo * d_avg
    vc2 = 0.17 * (1 + (2/beta)) * math.sqrt(fc_mpa) * bo * d_avg
    vc3 = 0.083 * ((alpha_s * d_avg / bo) + 2) * math.sqrt(fc_mpa) * bo * d_avg
    
    vc_n = min(vc1, vc2, vc3) # Newtons
    phi_vc_kg = (0.75 * vc_n) / GRAV
    
    shear_ratio = vu_design_kg / phi_vc_kg
    shear_status = "PASS" if shear_ratio <= 1.0 else "FAIL"

    # --- 4. Flexural Design (Whitney) ---
    # Simplified Strip Method Moment Coeffs (ACI Approx)
    ln = lx - (c1_mm/1000)
    mo = (qu * ly * ln**2) / 8 # Static Moment
    mu_top_kNm = (mo * 0.65) * 9.81 / 1000 # Negative Moment (approx)
    mu_bot_kNm = (mo * 0.35) * 9.81 / 1000 # Positive Moment (approx)
    
    def check_flexure(mu_val, d_val, db, sp):
        # 1. As Required (Whitney)
        as_req = solve_whitney(mu_val, fc_mpa, fy_mpa, 1000, d_val)
        
        # 2. As Provided
        area_bar = (math.pi * (db/2)**2) / 100
        as_prov = (area_bar * 1000) / sp
        
        # 3. Constraints Check
        # Min Steel (ACI 0.0018bh)
        as_min = 0.0018 * 1000 * h_mm / 100 # cm2/m
        
        # Max Spacing (2h or 450)
        max_s = min(2 * h_mm, 450)
        s_status = "OK" if sp <= max_s else "FAIL (> 2h)"
        
        # Strain/Max Steel Check (Roughly rho < 0.02 for slabs)
        rho = as_prov / (100 * d_val/10)
        rho_status = "OK" if (as_prov >= as_min and rho < 0.02) else "FAIL"
        
        return {
            "mu": mu_val, "d": d_val, 
            "as_req": as_req, "as_prov": as_prov, 
            "rho_chk": rho_status, "sp_chk": s_status
        }

    # Top (Outer Layer assumption)
    flex_top = check_flexure(mu_top_kNm, d_outer, top_db, top_sp)
    # Bot (Inner Layer assumption)
    flex_bot = check_flexure(mu_bot_kNm, d_inner, bot_db, bot_sp)
    
    # 5. Serviceability (h min)
    # ACI Table 8.3.1.1 (Fy=420 -> ln/30 roughly for exterior w/o drop)
    h_min = (ln * 1000) / 30 
    h_chk = "OK" if h_mm >= h_min else f"FAIL (Rec > {h_min:.0f})"

    return {
        "i": locals(), # Inputs
        "res": {
            "sw": sw, "dl": dl, "qu": qu,
            "b1": b1, "b2": b2, "bo": bo, "gamma_v": gamma_v, "a_inside": a_inside,
            "vu": vu_kg, "vu_des": vu_design_kg, "phi_vc": phi_vc_kg,
            "shear_ratio": shear_ratio, "shear_status": shear_status,
            "flex_top": flex_top, "flex_bot": flex_bot, "h_chk": h_chk, "h_min": h_min
        }
    }

# ==========================================
# 4. MODULE: REPORT (Rendering)
# ==========================================
def render_report(data):
    i = data['i'] # inputs
    r = data['res'] # results
    
    st.title("🏗️ Structural Calculation Report (ACI 318-19)")
    st.markdown("---")
    
    #  
    # (Optional visual placeholder for user context)

    # 1. Geometry
    st.header("1. Geometry & Materials")
    c1, c2, c3 = st.columns(3)
    with c1: 
        st.info(f"**Slab:** h = {i['h_mm']} mm (Min Req: {r['h_min']:.0f} mm -> {r['h_chk']})")
    with c2: 
        st.info(f"**Column:** {i['c1_mm']} x {i['c2_mm']} mm ({i['pos']})")
    with c3: 
        st.info(f"**Mat:** fc'={i['fc_ksc']} ksc, fy={i['fy_ksc']} ksc")

    # 2. Loads
    st.header("2. Load Analysis")
    st.latex(fmt_load_analysis(i['h_mm'], i['sdl'], i['ll'], r['sw'], r['dl'], r['qu']))

    # 3. Punching Shear
    st.header("3. Punching Shear Design")
    
    st.subheader("3.1 Critical Section Properties")
    st.latex(fmt_punching_geometry(i['pos'], i['c1_mm'], i['c2_mm'], r['flex_top']['d'], r['b1'], r['b2'], r['bo'], r['gamma_v']))
    
    st.subheader("3.2 Shear Demand (Vu)")
    st.latex(fmt_vu_calc(r['qu'], i['lx'], i['ly'], r['a_inside'], r['vu']))
    
    st.subheader("3.3 Capacity Check")
    # 
    st.latex(fmt_shear_check(r['vu_des'], r['phi_vc'], r['shear_ratio'], r['shear_status']))
    
    if r['shear_status'] == "FAIL":
        st.error("⚠️ Punching Shear Failed! Consider increasing slab thickness, concrete strength, or adding drop panels.")

    # 4. Flexural Design
    st.header("4. Flexural Design (Whitney Method)")
    
    st.subheader("4.1 Top Reinforcement (Negative Moment)")
    ft = r['flex_top']
    st.latex(fmt_flexure_design("Top (Outer)", ft['mu'], ft['d'], ft['as_req'], ft['as_prov'], i['top_db'], i['top_sp'], ft['rho_chk'], ft['sp_chk']))
    
    st.subheader("4.2 Bottom Reinforcement (Positive Moment)")
    fb = r['flex_bot']
    st.latex(fmt_flexure_design("Bot (Inner)", fb['mu'], fb['d'], fb['as_req'], fb['as_prov'], i['bot_db'], i['bot_sp'], fb['rho_chk'], fb['sp_chk']))

    # 
    
    st.success("Analysis Complete.")

# ==========================================
# 5. MAIN APP CONTROLLER
# ==========================================
if 'calc_data' not in st.session_state:
    st.session_state.calc_data = None

with st.sidebar:
    st.title("⚙️ Design Inputs")
    with st.form("main_form"):
        st.subheader("Geometry")
        h = st.number_input("Slab Thickness (mm)", 100, 1000, 200)
        cover = st.number_input("Cover (mm)", 15, 50, 25)
        c1 = st.number_input("Col Width c1 (mm)", 200, 2000, 500)
        c2 = st.number_input("Col Depth c2 (mm)", 200, 2000, 500)
        lx = st.number_input("Span Lx (m)", 2.0, 15.0, 8.0)
        ly = st.number_input("Span Ly (m)", 2.0, 15.0, 8.0)
        
        st.subheader("Loads & Mat")
        sdl = st.number_input("SDL (kg/m2)", 0, 1000, 150)
        ll = st.number_input("LL (kg/m2)", 0, 2000, 300)
        fc = st.number_input("fc' (ksc)", 180, 500, 280)
        fy = st.number_input("fy (ksc)", 2400, 5000, 4000)
        
        st.subheader("Reinforcement")
        c_top1, c_top2 = st.columns(2)
        top_db = c_top1.selectbox("Top DB", [10,12,16,20,25], index=2)
        top_sp = c_top2.number_input("Top @ (mm)", 50, 450, 200, step=25)
        
        c_bot1, c_bot2 = st.columns(2)
        bot_db = c_bot1.selectbox("Bot DB", [10,12,16,20,25], index=1)
        bot_sp = c_bot2.number_input("Bot @ (mm)", 50, 450, 250, step=25)
        
        pos = st.selectbox("Column Position", ["Interior", "Edge", "Corner"])
        
        submitted = st.form_submit_button("🚀 Run Analysis")

if submitted:
    data = run_analysis(lx, ly, h, c1, c2, sdl, ll, fc, fy, cover, pos, top_db, top_sp, bot_db, bot_sp)
    st.session_state.calc_data = data

if st.session_state.calc_data:
    render_report(st.session_state.calc_data)
else:
    st.info("👈 Please define parameters and Calculate.")
