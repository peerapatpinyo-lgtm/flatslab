import streamlit as st
import math

# ==========================================
# 1. CONFIG & SETUP
# ==========================================
st.set_page_config(page_title="Interactive Flat Slab Design", layout="wide", page_icon="🏗️")

# --- INITIALIZE SESSION STATE ---
if 'demands' not in st.session_state:
    st.session_state.demands = None

# ==========================================
# 2. MODULE: FORMATTERS (Math Display)
# ==========================================
def fmt_load_calc(h, sdl, ll, dl, qu):
    return r"""
    \begin{aligned}
    DL &= (0.0024 \times %.0f) + %.0f = %.1f \; kg/m^2 \\
    q_u &= 1.2(%.1f) + 1.6(%.0f) = \mathbf{%.1f} \; kg/m^2
    \end{aligned}
    """ % (h, sdl, dl, dl, ll, qu)

def fmt_moment_check(pos, mu, d, as_req, as_min, as_prov, status):
    color = "green" if status == "PASS" else "red"
    return r"""
    \begin{aligned}
    \text{%s Moment } (M_u) &= %.2f \; kN\cdot m \\
    \text{Eff. Depth } (d) &= %.1f \; mm \\
    A_{s,req} &= \mathbf{%.2f} \; cm^2 \quad (\text{Whitney}) \\
    A_{s,min} &= %.2f \; cm^2 \\
    A_{s,prov} &= \mathbf{%.2f} \; cm^2 \rightarrow \textcolor{%s}{\textbf{%s}}
    \end{aligned}
    """ % (pos, mu, d, as_req, as_min, as_prov, color, status)

def fmt_shear_verify(vu, phi_vc, ratio, status):
    color = "green" if status == "PASS" else "red"
    return r"""
    \begin{aligned}
    V_u &= \mathbf{%.1f} \; kN \quad (\text{Net Demand}) \\
    \phi V_c &= \mathbf{%.1f} \; kN \quad (\text{Capacity}) \\
    \text{Ratio} &= \frac{V_u}{\phi V_c} = \textcolor{%s}{\mathbf{%.2f}} \quad (\textbf{%s})
    \end{aligned}
    """ % (vu, phi_vc, color, ratio, status)

# ==========================================
# 3. MODULE: ENGINE
# ==========================================
GRAV = 9.80665

# --- Part 1: Initial Demands (Geometry & Loads) ---
def calc_general_demands(lx, ly, h_mm, c1, c2, sdl, ll, pos):
    # Loads
    sw = (h_mm / 1000.0) * 2400
    dl = sw + sdl
    qu = (1.2 * dl) + (1.6 * ll)
    
    # Static Moment (ACI Direct Design Method approximation)
    ln = lx - (c1/1000)
    mo_kgm = (qu * ly * ln**2) / 8
    mo_kNm = mo_kgm * GRAV / 1000.0
    
    # Distribute Moment (Approx Coeffs for Exterior/Interior avg)
    mu_neg = mo_kNm * 0.65 # Top
    mu_pos = mo_kNm * 0.35 # Bottom
    
    return {
        "h": h_mm, "c1": c1, "c2": c2, "lx": lx, "ly": ly,
        "qu": qu, "sw": sw, "dl": dl, 
        "mu_top": mu_neg, "mu_bot": mu_pos,
        "pos": pos
    }

# --- Part 2: Interactive Verification (Rebar dependent) ---
def verify_reinforcement(demands, fc_ksc, fy_ksc, cover, top_db, top_s, bot_db, bot_s):
    # Unpack
    d_dict = demands
    h, c1, c2 = d_dict['h'], d_dict['c1'], d_dict['c2']
    qu = d_dict['qu']
    
    fc_mpa = fc_ksc * 0.0981
    fy_mpa = fy_ksc * 0.0981
    
    # 1. Effective Depths (d)
    # Assume Top = Outer Layer, Bot = Inner Layer
    d_top = h - cover - (top_db/2)
    d_bot = h - cover - top_db - (bot_db/2)
    d_avg = (d_top + d_bot) / 2.0
    
    # 2. Flexural Check Logic
    def solve_as(mu_kNm, d_mm):
        # Whitney Stress Block Quadratic Solver
        phi = 0.9
        mu_Nmm = mu_kNm * 1e6
        alpha = (phi * fy_mpa**2) / (1.7 * fc_mpa * 1000) # b=1000
        beta = - (phi * fy_mpa * d_mm)
        gamma = mu_Nmm
        try:
            delta = beta**2 - 4*alpha*gamma
            if delta < 0: return 999.99 # Section too small
            as_mm2 = (-beta - math.sqrt(delta)) / (2*alpha)
            return as_mm2 / 100.0 # cm2
        except: return 999.99

    def get_as_prov(db, s):
        area_one = math.pi * (db/2)**2
        return (area_one / s) * 1000 / 100 # cm2
        
    # Check Top
    as_req_top = solve_as(d_dict['mu_top'], d_top)
    as_min = 0.0018 * 1000 * h / 100
    as_prov_top = get_as_prov(top_db, top_s)
    st_top = "PASS" if as_prov_top >= max(as_req_top, as_min) and top_s <= 2*h else "FAIL"
    
    # Check Bot
    as_req_bot = solve_as(d_dict['mu_bot'], d_bot)
    as_prov_bot = get_as_prov(bot_db, bot_s)
    st_bot = "PASS" if as_prov_bot >= max(as_req_bot, as_min) and bot_s <= 2*h else "FAIL"

    # 3. Punching Shear (Depends on d_avg)
    # Geometry
    pos = d_dict['pos']
    if pos == "Interior":
        b1, b2 = c1 + d_avg, c2 + d_avg
        bo = 2*(b1+b2)
        alpha_s = 40
        mag = 1.0
    elif pos == "Edge":
        b1, b2 = c1 + d_avg/2, c2 + d_avg
        bo = 2*b1 + b2
        alpha_s = 30
        mag = 1.25
    else: # Corner
        b1, b2 = c1 + d_avg/2, c2 + d_avg/2
        bo = b1 + b2
        alpha_s = 20
        mag = 1.30
        
    # Demand Vu (Net Load)
    a_inside = (b1 * b2) / 1e6
    vu_net_kN = (qu * ((d_dict['lx']*d_dict['ly']) - a_inside) * mag * GRAV) / 1000
    
    # Capacity PhiVc
    beta = max(c1,c2)/min(c1,c2)
    vc1 = 0.33 * math.sqrt(fc_mpa) * bo * d_avg
    vc2 = 0.17 * (1 + 2/beta) * math.sqrt(fc_mpa) * bo * d_avg
    vc3 = 0.083 * (alpha_s*d_avg/bo + 2) * math.sqrt(fc_mpa) * bo * d_avg
    phi_vc_kN = (0.75 * min(vc1,vc2,vc3)) / 1000
    
    st_shear = "PASS" if vu_net_kN <= phi_vc_kN else "FAIL"
    
    return {
        "d_top": d_top, "as_req_top": as_req_top, "as_prov_top": as_prov_top, "st_top": st_top,
        "d_bot": d_bot, "as_req_bot": as_req_bot, "as_prov_bot": as_prov_bot, "st_bot": st_bot,
        "as_min": as_min,
        "vu": vu_net_kN, "phi_vc": phi_vc_kN, "st_shear": st_shear, "bo": bo
    }

# ==========================================
# 4. MODULE: UI LAYOUT
# ==========================================

# --- SIDEBAR: Fixed Inputs (Geometry & Loads) ---
with st.sidebar:
    st.header("1. Project Inputs")
    with st.form("geom_form"):
        st.subheader("Geometry & Materials")
        h = st.number_input("Slab Thickness (mm)", 100, 500, 200)
        c1 = st.number_input("Col Width c1 (mm)", 200, 1000, 500)
        c2 = st.number_input("Col Depth c2 (mm)", 200, 1000, 500)
        cover = st.number_input("Cover (mm)", 15, 50, 25)
        
        st.subheader("Span & Position")
        lx = st.number_input("Span Lx (m)", 2.0, 12.0, 8.0)
        ly = st.number_input("Span Ly (m)", 2.0, 12.0, 8.0)
        pos = st.selectbox("Column Position", ["Interior", "Edge", "Corner"])
        
        st.subheader("Loads")
        sdl = st.number_input("SDL (kg/m2)", 0, 500, 150)
        ll = st.number_input("LL (kg/m2)", 0, 1000, 300)
        
        st.subheader("Material Properties")
        fc = st.number_input("fc' (ksc)", 180, 500, 280)
        fy = st.number_input("fy (ksc)", 2400, 5000, 4000)
        
        # Action Button: Calculate Demands ONLY
        calc_btn = st.form_submit_button("📊 Calculate Demands")

if calc_btn:
    st.session_state.demands = calc_general_demands(lx, ly, h, c1, c2, sdl, ll, pos)
    # Streamlit will re-run and show the main area

# --- MAIN AREA: Report & Interactive Design ---
st.title("🏗️ Interactive Flat Slab Design")
st.caption("ACI 318-19 | Metric Units")
st.markdown("---")

if st.session_state.demands:
    dm = st.session_state.demands
    
    # === SECTION 2: LOADS & GEOMETRY ===
    c1_ui, c2_ui = st.columns([1, 2])
    with c1_ui:
        st.subheader("2. Load Analysis")
        st.latex(fmt_load_calc(dm['h'], sdl, ll, dm['dl'], dm['qu']))
    with c2_ui:
        st.info(f"**Structural Context:** {dm['pos']} Column | Size {dm['c1']}x{dm['c2']} mm | Span {dm['lx']}x{dm['ly']} m")

    st.markdown("---")
    
    # === SECTION 3: REINFORCEMENT DESIGN (INTERACTIVE) ===
    st.header("3. Reinforcement Design")
    st.markdown("👉 **Adjust the rebar configuration below to satisfy demands:**")
    
    # Container for Interactive Inputs
    with st.container():
        col_top, col_bot = st.columns(2)
        
        # --- Top Rebar Input ---
        with col_top:
            st.subheader("Top Rebar (Negative Moment)")
            st.write(f"**Demand:** $M_u = {dm['mu_top']:.2f}$ kN-m")
            # User Input - Key change triggers rerun
            t_db = st.selectbox("Top Bar Size (mm)", [10,12,16,20,25], index=2, key="t_db")
            t_sp = st.number_input("Top Spacing (mm)", 50, 450, 200, step=25, key="t_sp")
        
        # --- Bottom Rebar Input ---
        with col_bot:
            st.subheader("Bottom Rebar (Positive Moment)")
            st.write(f"**Demand:** $M_u = {dm['mu_bot']:.2f}$ kN-m")
            # User Input - Key change triggers rerun
            b_db = st.selectbox("Bot Bar Size (mm)", [10,12,16,20,25], index=1, key="b_db")
            b_sp = st.number_input("Bot Spacing (mm)", 50, 450, 250, step=25, key="b_sp")

    # === REAL-TIME CALCULATION ===
    # This runs every time the user touches the widgets above
    res = verify_reinforcement(dm, fc, fy, cover, t_db, t_sp, b_db, b_sp)
    
    # Display Results immediately below inputs
    r1, r2 = st.columns(2)
    with r1:
        st.latex(fmt_moment_check("Top", dm['mu_top'], res['d_top'], res['as_req_top'], res['as_min'], res['as_prov_top'], res['st_top']))
    with r2:
        st.latex(fmt_moment_check("Bottom", dm['mu_bot'], res['d_bot'], res['as_req_bot'], res['as_min'], res['as_prov_bot'], res['st_bot']))
        
    st.markdown("---")
    
    # === SECTION 4: FINAL SHEAR VERIFICATION ===
    st.header("4. Punching Shear Verification")
    st.markdown("Computed based on actual $d_{avg}$ from selected reinforcement.")
    
    s1, s2 = st.columns([1, 1])
    with s1:
        st.write("**Critical Section parameters:**")
        st.write(f"- $d_{{avg}} = { (res['d_top']+res['d_bot'])/2:.1f}$ mm")
        st.write(f"- $b_o = {res['bo']:.0f}$ mm")
        st.latex(fmt_shear_verify(res['vu'], res['phi_vc'], res['vu']/res['phi_vc'], res['st_shear']))
    
    with s2:
        if res['st_shear'] == "FAIL":
            st.error("❌ **Shear Check Failed:** Try increasing Slab Thickness, Concrete Strength, or adding Drop Panels.")
        else:
            st.success("✅ **Shear Check Passed:** Design is adequate for Shear.")

else:
    st.info("👈 Please enter Geometry & Loads in the Sidebar and click 'Calculate Demands' to start designing.")
