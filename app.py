import streamlit as st
import numpy as np
import pandas as pd
from geometry_view import plot_combined_view

# ==========================================
# 1. SETUP & CONFIG
# ==========================================
st.set_page_config(page_title="Pro Flat Slab Design", layout="wide", page_icon="🏢")

# Custom CSS for Professional Look
st.markdown("""
<style>
    h1, h2, h3 { color: #2c3e50; }
    .big-metric { font-size: 24px; font-weight: bold; color: #0d6efd; }
    .success-box { background-color: #d1e7dd; padding: 15px; border-radius: 5px; border-left: 5px solid #198754; color: #0f5132; }
    .fail-box { background-color: #f8d7da; padding: 15px; border-radius: 5px; border-left: 5px solid #dc3545; color: #842029; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: #f8f9fa; border-radius: 5px 5px 0 0; }
    .stTabs [aria-selected="true"] { background-color: #fff; border-top: 3px solid #0d6efd; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. ENGINEERING FUNCTIONS
# ==========================================
def calculate_stiffness(c1, c2, L1, L2, lc, h_slab, fc):
    """Calculate EFM Stiffness Parameters"""
    Ec = 15100 * np.sqrt(fc) # ksc
    # Inertia
    Is = (L2*100 * h_slab**3)/12
    Ic = (c2 * c1**3)/12
    # Stiffness K
    Ks = 4 * Ec * Is / (L1*100)
    Kc = 4 * Ec * Ic / (lc*100)
    # Torsional Kt (Simplified ACI)
    x = min(c1, h_slab)
    y = max(c1, h_slab)
    C = (1 - 0.63*(x/y)) * (x**3 * y)/3
    Kt = 2 * (9 * Ec * C) / (L2*100 * (1 - c2/(L2*100))**3)
    # Kec
    sum_Kc = 2 * Kc # Top & Bottom cols
    if Kt == 0: Kec = 0
    else: Kec = 1 / (1/sum_Kc + 1/Kt)
    return Ks, Kc, Kt, Kec

def check_punching_shear(Vu, fc, c1, c2, d):
    """ACI 318 Punching Shear Check (Interior Col)"""
    # 1. Critical Perimeter
    b0 = 2*(c1+d) + 2*(c2+d)
    
    # 2. Capacity (Vc) - ACI Metric (Ult)
    # phi * 1.06 * sqrt(fc) * b0 * d (phi=0.75 for shear)
    phi = 0.75
    Vc_stress = 1.06 * np.sqrt(fc) # kg/cm2
    Vc = phi * Vc_stress * b0 * d
    
    ratio = Vu / Vc if Vc > 0 else 999
    status = "PASS" if ratio <= 1.0 else "FAIL"
    return Vc, ratio, status, b0

def design_rebar_detailed(Mu_kgm, b_cm, d_cm, fc, fy):
    """Calculate Rebar with Min/Max Checks"""
    if Mu_kgm < 10: return 0, 0, "None", "OK"
    
    Mu = Mu_kgm * 100 # kg-cm
    phi = 0.90
    
    # Rn
    Rn = Mu / (phi * b_cm * d_cm**2)
    
    # Rho limits
    rho_min = 0.0018 # Temp & Shrinkage
    # Rho balanced (approx for fy=4000)
    beta1 = 0.85 if fc <= 280 else max(0.65, 0.85 - 0.05*(fc-280)/70)
    rho_b = 0.85 * beta1 * (fc/fy) * (6120/(6120+fy))
    rho_max = 0.75 * rho_b # Limit for ductility
    
    # Rho req
    try:
        term = 1 - (2*Rn)/(0.85*fc)
        if term < 0: return 999, rho_max, "Section Too Small", "FAIL"
        rho_req = (0.85*fc/fy) * (1 - np.sqrt(term))
    except:
        return 999, rho_max, "Calc Error", "FAIL"
    
    # Final Design
    rho_design = max(rho_req, rho_min)
    As_req = rho_design * b_cm * d_cm
    
    status = "OK"
    note = ""
    if rho_req > rho_max: 
        status = "FAIL"
        note = "Rho > Rho_max"
    elif rho_req < rho_min:
        note = "Used Min Steel"
        
    return As_req, rho_design, note, status

# ==========================================
# 3. SIDEBAR INPUTS
# ==========================================
st.sidebar.title("🏗️ Project Params")

with st.sidebar.expander("1. Material & Slab", expanded=True):
    fc = st.number_input("f'c (ksc)", value=240.0, step=10.0)
    fy = st.number_input("fy (ksc)", value=4000.0, step=100.0)
    h_slab = st.number_input("Thickness (cm)", value=20.0, step=1.0)
    cover = st.number_input("Cover (cm)", value=2.5)
    d_bar = st.selectbox("Rebar DB (mm)", [12, 16, 20, 25], index=1)

with st.sidebar.expander("2. Geometry (Span)", expanded=True):
    L1 = st.number_input("L1: Long Span (m)", value=6.0)
    L2 = st.number_input("L2: Width (m)", value=6.0)
    lc = st.number_input("Storey Height (m)", value=3.0)
    c1_w = st.number_input("Col Width c1 (cm)", value=40.0)
    c2_w = st.number_input("Col Width c2 (cm)", value=40.0)

with st.sidebar.expander("3. Loads", expanded=True):
    SDL = st.number_input("Superimposed DL (kg/m²)", value=150.0)
    LL = st.number_input("Live Load (kg/m²)", value=300.0)

# ==========================================
# 4. MAIN CALCULATION
# ==========================================
# Derived
d_eff = h_slab - cover - (d_bar/20.0)
Ab = 3.14159 * (d_bar/10)**2 / 4
w_self = (h_slab/100)*2400
w_u = 1.2*(w_self + SDL) + 1.6*LL

# A. Safety Checks
# 1. Thickness Check (ACI Table 8.3.1.1) - Interior Panel without drop
h_min_aci = max(L1, L2)*100 / 33.0
chk_thick = "PASS" if h_slab >= h_min_aci else "WARNING"

# 2. Punching Shear
# Vu at d distance from face
c1_d = c1_w + d_eff
c2_d = c2_w + d_eff
area_crit = (c1_d/100) * (c2_d/100)
Vu_punch = w_u * (L1*L2 - area_crit)
Vc_punch, ratio_punch, status_punch, b0 = check_punching_shear(Vu_punch, fc, c1_w, c2_w, d_eff)

# ==========================================
# 5. DASHBOARD HEADER
# ==========================================
st.title("Pro Flat Slab Design: Interactive Tool")
st.markdown("---")

# Safety Dashboard
col_s1, col_s2, col_s3 = st.columns(3)
with col_s1:
    st.markdown("### 🛡️ Punching Shear")
    if status_punch == "PASS":
        st.markdown(f"<div class='success-box'>✅ <b>SAFE</b> (Ratio {ratio_punch:.2f})<br>Vu = {Vu_punch:,.0f} kg<br>φVc = {Vc_punch:,.0f} kg</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='fail-box'>❌ <b>FAILED</b> (Ratio {ratio_punch:.2f})<br>Increase h or f'c</div>", unsafe_allow_html=True)

with col_s2:
    st.markdown("### 📏 Min. Thickness (Deflection)")
    if chk_thick == "PASS":
        st.markdown(f"<div class='success-box'>✅ <b>OK</b><br>Provided: {h_slab} cm<br>Req (L/33): {h_min_aci:.1f} cm</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='fail-box'>⚠️ <b>WARNING</b><br>Provided: {h_slab} cm<br>Req (L/33): {h_min_aci:.1f} cm</div>", unsafe_allow_html=True)

with col_s3:
    st.markdown("### ⚖️ Factored Load (Wu)")
    st.metric("Total Load", f"{w_u:,.0f} kg/m²", f"DL={w_self+SDL:.0f}, LL={LL}")

st.markdown("---")

# ==========================================
# 6. TABS LOGIC
# ==========================================
tab1, tab2, tab3 = st.tabs(["1️⃣ DDM (Direct Design & Rebar)", "2️⃣ EFM (Stiffness Analysis)", "3️⃣ Drawings & Visuals"])

# --- TAB 1: DDM ---
with tab1:
    st.header("Direct Design Method (DDM)")
    
    # 1. Static Moment
    ln = L1 - c1_w/100
    Mo = (w_u * L2 * ln**2) / 8
    
    col_m1, col_m2 = st.columns([1, 2])
    with col_m1:
        st.info(f"**Total Static Moment ($M_o$):**\n# {Mo:,.2f} kg-m")
    with col_m2:
        st.caption("Assumption: Interior Panel. Moment Coefficients from ACI 318.")
    
    # 2. Distribution
    # Neg = 0.65 Mo | Pos = 0.35 Mo
    # Col Strip: 75% Neg, 60% Pos
    M_neg_total = 0.65 * Mo
    M_pos_total = 0.35 * Mo
    
    vals = {
        "M_cs_neg": M_neg_total * 0.75,
        "M_ms_neg": M_neg_total * 0.25,
        "M_cs_pos": M_pos_total * 0.60,
        "M_ms_pos": M_pos_total * 0.40
    }
    
    # 3. Rebar Schedule Table
    st.subheader("📝 Reinforcement Schedule")
    
    w_cs = min(L1, L2)/2
    w_ms = L2 - w_cs
    
    schedule_data = []
    zones = [
        ("Column Strip: Top (-)", vals["M_cs_neg"], w_cs),
        ("Column Strip: Bot (+)", vals["M_cs_pos"], w_cs),
        ("Middle Strip: Top (-)", vals["M_ms_neg"], w_ms),
        ("Middle Strip: Bot (+)", vals["M_ms_pos"], w_ms),
    ]
    
    for z_name, mom, width_m in zones:
        As_req, rho, note, status = design_rebar_detailed(mom, width_m*100, d_eff, fc, fy)
        
        # Bar Selection
        if status == "OK":
            num_bars = np.ceil(As_req / Ab)
            spacing = (width_m*100)/num_bars
            # Limit spacing to 2h or 45cm
            max_s = min(2*h_slab, 45)
            spacing = min(spacing, max_s)
            
            bar_txt = f"{int(num_bars)} - DB{d_bar}"
            spa_txt = f"@{spacing:.0f} cm"
        else:
            bar_txt = "CHECK DESIGN"
            spa_txt = "-"
            
        schedule_data.append({
            "Zone": z_name,
            "Moment (kg-m)": f"{mom:,.0f}",
            "Width (m)": f"{width_m:.2f}",
            "As Req (cm²)": f"{As_req:.2f}",
            "Selection": bar_txt,
            "Spacing": spa_txt,
            "Note": note
        })
        
    df = pd.DataFrame(schedule_data)
    st.table(df)
    

# --- TAB 2: EFM ---
with tab2:
    st.header("Equivalent Frame Method (EFM) Properties")
    st.markdown("Use these Stiffness (K) values for your Frame Analysis software.")
    
    Ks, Kc, Kt, Kec = calculate_stiffness(c1_w, c2_w, L1, L2, lc, h_slab, fc)
    
    col_k1, col_k2 = st.columns(2)
    
    with col_k1:
        st.subheader("🧮 Calculated Stiffness")
        st.latex(r"K_{slab} = " + f"{Ks:,.0f}" + r" \quad \text{kg-cm}")
        st.latex(r"K_{col} = " + f"{Kc:,.0f}" + r" \quad \text{kg-cm}")
        st.latex(r"K_{ec} = " + f"{Kec:,.0f}" + r" \quad \text{kg-cm} \; (\text{Equiv Col})")
        st.caption(f"Note: Kec combines Column ({Kc:,.0f}) and Torsion ({Kt:,.0f})")

    with col_k2:
        st.subheader("Distribution Factors (DF)")
        df_slab = Ks / (Ks + Kec)
        df_col = Kec / (Ks + Kec)
        
        st.metric("DF Slab", f"{df_slab:.3f}")
        st.metric("DF Col (Total)", f"{df_col:.3f}")
        
        st.progress(df_slab)
    
    st.markdown("---")
    st.markdown("### 📐 EFM Diagram Model")
    
    st.info("The Equivalent Frame consists of the slab-beam, columns, and torsional members. The values above account for the 'softening' effect of the slab-column connection.")

# --- TAB 3: VISUALS ---
with tab3:
    st.header("Engineering Drawings")
    # Pass moment data for visualization
    st.pyplot(plot_combined_view(L1, L2, c1_w, c2_w, h_slab, lc, vals))
    
    st.markdown("#### Detail Summary")
    st.text(f"""
    - Slab Thickness: {h_slab} cm
    - Effective Depth (d): {d_eff:.2f} cm
    - Column Size: {c1_w} x {c2_w} cm
    - Concrete Cover: {cover} cm
    """)
