import streamlit as st
import math

# ==========================================
# 1. CONFIG & SETUP (Must be first)
# ==========================================
st.set_page_config(page_title="Transparent Slab Design", layout="wide", page_icon="📐")

# ==========================================
# 2. MODULE: FORMATTER (Show the Math)
# ==========================================
def fmt_load_trace(h_mm, sdl, ll, sw_res, qu_res):
    """Generates LaTeX for Load Trace with substitution."""
    h_m = h_mm / 1000.0
    return r"""
    \begin{aligned}
    SW &= \text{Thickness} \times 2400 = %.2f \times 2400 = %.1f \; kg/m^2 \\
    DL &= SW + SDL = %.1f + %.1f = %.1f \; kg/m^2 \\
    q_u &= 1.4(DL) + 1.7(LL) \\
        &= 1.4(%.1f) + 1.7(%.1f) \\
        &= \mathbf{%.1f} \; kg/m^2
    \end{aligned}
    """ % (h_m, sw_res, sw_res, sdl, sw_res + sdl, sw_res + sdl, ll, qu_res)

def fmt_d_calc(h, cover, db_avg, d_res):
    """Generates LaTeX for Effective Depth."""
    return r"""
    d = h - c_c - \frac{d_{b,avg}}{2} = %.0f - %.0f - %.1f = \mathbf{%.1f} \; mm
    """ % (h, cover, db_avg, d_res)

def fmt_shear_geometry(c1, c2, d, bo, method_pos):
    """Generates LaTeX for Critical Perimeter."""
    return r"""
    \begin{aligned}
    \text{Position} &: \text{%s} \\
    b_o &= 2(c_1 + d) + 2(c_2 + d) \\
        &= 2(%.0f + %.0f) + 2(%.0f + %.0f) \\
        &= \mathbf{%.0f} \; mm
    \end{aligned}
    """ % (method_pos, c1, d, c2, d, bo)

def fmt_shear_capacity(fc, beta, alpha, d, bo, vc1, vc2, vc3, vc_final, phi_vc):
    """Generates LaTeX for ACI 318 Shear Equations."""
    return r"""
    \begin{aligned}
    V_{c1} &= 0.33\sqrt{f'_c} b_o d = 0.33\sqrt{%.1f}(%.0f)(%.0f)/1000 = %.1f \; kN \\
    V_{c2} &= 0.17(1 + \frac{2}{\beta})\sqrt{f'_c} b_o d = 0.17(1 + \frac{2}{%.1f})\sqrt{%.1f}(%.0f)(%.0f)/1000 = %.1f \; kN \\
    V_{c3} &= 0.083(\frac{\alpha_s d}{b_o} + 2)\sqrt{f'_c} b_o d = 0.083(\frac{%.0f \cdot %.0f}{%.0f} + 2)\sqrt{%.1f}(%.0f)(%.0f)/1000 = %.1f \; kN \\
    \\
    V_c &= \min(V_{c1}, V_{c2}, V_{c3}) = \mathbf{%.1f} \; kN \\
    \phi V_c &= 0.75 \times V_c = \mathbf{%.1f} \; kN \quad (\approx %.1f \; tons)
    \end{aligned}
    """ % (fc, bo, d, vc1/1000, 
           beta, fc, bo, d, vc2/1000, 
           alpha, d, bo, fc, bo, d, vc3/1000,
           vc_final/1000, phi_vc/1000, phi_vc/9806.65)

def fmt_shear_check(vu, phi_vc):
    """Generates LaTeX for Pass/Fail Check."""
    ratio = vu / phi_vc
    res = "OK" if ratio <= 1.0 else "FAIL"
    color = "green" if ratio <= 1.0 else "red"
    return r"""
    \text{Check: } \frac{V_u}{\phi V_c} = \frac{%.1f}{%.1f} = \textcolor{%s}{\mathbf{%.2f}} \quad (\text{%s})
    """ % (vu/1000, phi_vc/1000, color, ratio, res)

def fmt_moment_calc(mu, fy, d, a_req, a_min, a_prov, db, s, status):
    """Generates LaTeX for Flexural Design."""
    res_text = "OK" if status == "SAFE" else "FAIL"
    col = "green" if status == "SAFE" else "red"
    return r"""
    \begin{aligned}
    M_u &= %.1f \; kg\cdot m \\
    A_{s,req} &\approx \frac{M_u}{0.9 f_y (0.9d)} = \frac{%.0f \cdot 100}{0.9(%.0f)(0.9 \cdot %.1f)} = %.2f \; cm^2 \\
    A_{s,min} &= 0.0018 b h = 0.0018(100)(%.1f) = %.2f \; cm^2 \\
    A_{s,target} &= \max(%.2f, %.2f) = \mathbf{%.2f} \; cm^2 \\
    \\
    \text{Try } \textbf{DB%d @ %.0f mm} &\rightarrow A_{s,prov} = \mathbf{%.2f} \; cm^2 \\
    \text{Status} &: \textcolor{%s}{\textbf{%s}}
    \end{aligned}
    """ % (mu, mu, fy, d/10, a_req, 
           d*10/10 + 3.0, a_min,
           a_req, a_min, max(a_req, a_min),
           db, s, a_prov, col, res_text)

# ==========================================
# 3. MODULE: ENGINE (Calculation Logic)
# ==========================================
GRAV = 9.80665
CONCRETE_DENSITY = 2400 

def run_analysis(lx, ly, h_mm, c1_mm, c2_mm, sdl, ll, fc_ksc, fy_ksc, cover_mm, pos, top_db, top_sp, bot_db, bot_sp):
    # --- 1. Unit Conversion ---
    fc_mpa = fc_ksc * 0.0980665
    
    # --- 2. Geometry & Effective Depth (d) ---
    avg_db = (top_db + bot_db) / 2.0
    d_mm = h_mm - cover_mm - avg_db
    
    # --- 3. Loads ---
    sw = (h_mm / 1000.0) * CONCRETE_DENSITY
    dl = sw + sdl
    qu = (1.4 * dl) + (1.7 * ll)
    
    # --- 4. Punching Shear Analysis ---
    b1 = c1_mm + d_mm
    b2 = c2_mm + d_mm
    
    # Critical Perimeter (bo) based on Position
    if pos == "Interior":
        bo = 2 * (b1 + b2)
        alpha_s = 40
    elif pos == "Edge":
        bo = (2 * b1) + b2
        alpha_s = 30
    else: # Corner
        bo = b1 + b2
        alpha_s = 20
        
    beta = max(c1_mm, c2_mm) / min(c1_mm, c2_mm)
    
    # Capacity Vc (Newtons) - ACI 3 Equations
    vc1 = 0.33 * math.sqrt(fc_mpa) * bo * d_mm
    vc2 = 0.17 * (1 + (2/beta)) * math.sqrt(fc_mpa) * bo * d_mm
    vc3 = 0.083 * ((alpha_s * d_mm / bo) + 2) * math.sqrt(fc_mpa) * bo * d_mm
    
    vc_n = min(vc1, vc2, vc3)
    phi_vc_kg = (0.75 * vc_n) / GRAV
    
    # Demand Vu (kg)
    area_load = (lx * ly) - ((c1_mm/1000)*(c2_mm/1000))
    vu_kg = qu * area_load
    
    # --- 5. Flexural Analysis (Simplified) ---
    ln = lx - (c1_mm/1000)
    mo = (qu * ly * ln**2) / 8
    mu_top = mo * 0.65 * 0.75
    mu_bot = mo * 0.35 * 0.60
    
    # --- 6. Rebar Verification ---
    def check_bar(mu, db, sp, d_val):
        d_cm = d_val / 10.0
        as_req = (mu * 100) / (0.9 * fy_ksc * 0.9 * d_cm)
        as_min = 0.0018 * 100 * (h_mm / 10.0)
        area_bar = (math.pi * (db/2)**2) / 100
        as_prov = (area_bar * 1000) / sp
        status = "SAFE" if (as_prov >= max(as_req, as_min)) else "FAIL"
        return mu, as_req, as_min, as_prov, status

    res_top = check_bar(mu_top, top_db, top_sp, d_mm)
    res_bot = check_bar(mu_bot, bot_db, bot_sp, d_mm)

    # --- 7. Package Results ---
    return {
        "inputs": {
            "h": h_mm, "sdl": sdl, "ll": ll, "fc": fc_ksc, "fy": fy_ksc,
            "c1": c1_mm, "c2": c2_mm, "cover": cover_mm, "pos": pos,
            "top_db": top_db, "top_sp": top_sp, "bot_db": bot_db, "bot_sp": bot_sp
        },
        "loads": { "sw": sw, "qu": qu },
        "shear": {
            "d_mm": d_mm, "bo": bo, "beta": beta, "alpha": alpha_s,
            "vc1": vc1, "vc2": vc2, "vc3": vc3, "vc_final": vc_n,
            "phi_vc_kg": phi_vc_kg, "vu_kg": vu_kg
        },
        "flexure": { "mo": mo, "top": res_top, "bot": res_bot }
    }

# ==========================================
# 4. MODULE: REPORT (UI Rendering)
# ==========================================
def render_report(data):
    i = data['inputs']
    l = data['loads']
    s = data['shear']
    f = data['flexure']
    
    st.title("🏗️ Structural Calculation Report")
    st.markdown("---")

    # Section 1: Geometry
    st.header("1. Geometry & Materials")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.write(f"**Dimensions:**")
        st.write(f"Thickness (h): {i['h']} mm")
    with c2:
        st.write(f"**Column:**")
        st.write(f"Size: {i['c1']} x {i['c2']} mm")
    with c3:
        st.write(f"**Materials:**")
        st.write(f"fc': {i['fc']} ksc")
        st.write(f"fy: {i['fy']} ksc")

    # Section 2: Loads
    st.header("2. Load Analysis")
    st.latex(fmt_load_trace(i['h'], i['sdl'], i['ll'], l['sw'], l['qu']))

    # Section 3: Shear
    st.header("3. Punching Shear Verification")
    st.subheader("3.1 Effective Depth Calculation")
    st.latex(fmt_d_calc(i['h'], i['cover'], (i['top_db']+i['bot_db'])/2, s['d_mm']))
    
    st.subheader("3.2 Critical Section")
    st.latex(fmt_shear_geometry(i['c1'], i['c2'], s['d_mm'], s['bo'], i['pos']))
    
    st.subheader("3.3 Shear Capacity")
    st.latex(fmt_shear_capacity(
        i['fc'] * 0.098, s['beta'], s['alpha'], s['d_mm'], s['bo'],
        s['vc1'], s['vc2'], s['vc3'], s['vc_final'], s['phi_vc_kg'] * 9.8
    ))
    st.subheader("3.4 Shear Check")
    st.latex(fmt_shear_check(s['vu_kg'] * 9.8, s['phi_vc_kg'] * 9.8))

    # Section 4: Flexure
    st.header("4. Flexural Design")
    st.subheader("4.1 Top Rebar")
    r_top = f['top']
    st.latex(fmt_moment_calc(r_top[0], i['fy'], s['d_mm'], r_top[1], r_top[2], r_top[3], i['top_db'], i['top_sp'], r_top[4]))
    
    st.subheader("4.2 Bottom Rebar")
    r_bot = f['bot']
    st.latex(fmt_moment_calc(r_bot[0], i['fy'], s['d_mm'], r_bot[1], r_bot[2], r_bot[3], i['bot_db'], i['bot_sp'], r_bot[4]))

# ==========================================
# 5. MAIN APP LOGIC (Controller)
# ==========================================

# --- Session State ---
if 'calc_data' not in st.session_state:
    st.session_state.calc_data = None

# --- Sidebar ---
with st.sidebar:
    st.title("⚙️ Design Parameters")
    
    with st.form("input_form"):
        st.subheader("Geometry")
        h = st.number_input("Thickness (mm)", 100, 500, 200)
        c1 = st.number_input("Col Width c1 (mm)", 200, 1000, 500)
        c2 = st.number_input("Col Depth c2 (mm)", 200, 1000, 500)
        lx = st.number_input("Span Lx (m)", 3.0, 12.0, 8.0)
        ly = st.number_input("Span Ly (m)", 3.0, 12.0, 8.0)
        
        st.subheader("Loads & Mat.")
        sdl = st.number_input("SDL (kg/m2)", 0, 500, 150)
        ll = st.number_input("LL (kg/m2)", 0, 1000, 300)
        fc = st.number_input("fc' (ksc)", 180, 500, 280)
        fy = st.number_input("fy (ksc)", 2400, 5000, 4000)
        
        st.subheader("Reinforcement Selection")
        c_top1, c_top2 = st.columns(2)
        top_db = c_top1.selectbox("Top DB", [12, 16, 20, 25], index=1)
        top_sp = c_top2.number_input("Top @ (mm)", 50, 400, 200, step=25)
        
        c_bot1, c_bot2 = st.columns(2)
        bot_db = c_bot1.selectbox("Bot DB", [12, 16, 20, 25], index=1)
        bot_sp = c_bot2.number_input("Bot @ (mm)", 50, 400, 250, step=25)
        
        pos = st.selectbox("Position", ["Interior", "Edge", "Corner"])
        
        submitted = st.form_submit_button("🚀 Calculate / Update")

# --- Execution ---
if submitted:
    # Run Engine
    data = run_analysis(
        lx, ly, h, c1, c2, 
        sdl, ll, fc, fy, 
        25, pos, top_db, top_sp, bot_db, bot_sp
    )
    # Store in Session
    st.session_state.calc_data = data

# --- Display ---
if st.session_state.calc_data:
    render_report(st.session_state.calc_data)
else:
    st.info("👈 Please enter parameters in the sidebar and click Calculate.")
