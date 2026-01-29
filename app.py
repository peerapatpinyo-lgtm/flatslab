import streamlit as st
import numpy as np
import pandas as pd
from geometry_view import plot_geometry_detailed, plot_moment_map

# ==========================================
# 1. SETUP & STYLING
# ==========================================
st.set_page_config(page_title="Flat Slab Design Pro", layout="wide", page_icon="🏗️")
st.markdown("""
<style>
    .pass { color: #198754; font-weight: bold; }
    .fail { color: #dc3545; font-weight: bold; }
    .stMetric { background-color: #f8f9fa; border-radius: 5px; padding: 10px; border: 1px solid #dee2e6; }
</style>
""", unsafe_allow_html=True)

# --- Helper Functions ---
def design_rebar(Mu_kgm, b_cm, d_cm, fc, fy):
    """
    คำนวณเหล็กเสริมละเอียด (Ultimate Strength Design)
    Return: As_req, Number of Bars, Spacing, Status
    """
    if Mu_kgm <= 0.1: return 0, 0, 0, "No Moment"
    
    Mu_kgcm = Mu_kgm * 100
    phi = 0.9
    
    # 1. Calculate Rho required
    # Rn = Mu / (phi * b * d^2)
    Rn = Mu_kgcm / (phi * b_cm * d_cm**2)
    
    # Check Max Limit (prevent brittle failure)
    rho_balance = 0.85 * 0.85 * (fc / fy) * (6120 / (6120 + fy))
    rho_max = 0.75 * rho_balance
    
    # Calculate exact rho
    try:
        val_root = 1 - (2 * Rn) / (0.85 * fc)
        if val_root < 0: return 999, 0, 0, "FAIL (Section too small)"
        rho = (0.85 * fc / fy) * (1 - np.sqrt(val_root))
    except ValueError:
        return 999, 0, 0, "FAIL (Error)"

    # 2. Minimum Steel (Temp & Shrinkage)
    rho_min = 0.0018 # ACI slab standard
    rho_final = max(rho, rho_min)
    
    if rho > rho_max:
        return 999, 0, 0, "FAIL (Rho > Rho_max)"
    
    As_req = rho_final * b_cm * d_cm
    return As_req, rho_final, rho_max, "OK"

def get_bar_area(d_mm):
    return 3.14159 * (d_mm/10.0)**2 / 4

# ==========================================
# 2. INPUTS
# ==========================================
st.sidebar.header("1. Material & Section")
fc = st.sidebar.number_input("f'c (ksc)", 240.0)
fy = st.sidebar.number_input("fy (ksc)", 4000.0)
h_slab = st.sidebar.number_input("Slab Thickness (cm)", 20.0)
cover = st.sidebar.number_input("Cover (cm)", 2.5)
d_bar = st.sidebar.selectbox("Rebar DB (mm)", [12, 16, 20, 25], index=0)

st.sidebar.header("2. Geometry")
L1 = st.sidebar.number_input("L1 (Span) [m]", 6.0)
L2 = st.sidebar.number_input("L2 (Width) [m]", 6.0)
lc = st.sidebar.number_input("Storey Height (m) [lc]", 3.0) # เพิ่มตัวแปรนี้กลับมา
c1 = st.sidebar.number_input("c1 (cm)", 40.0)
c2 = st.sidebar.number_input("c2 (cm)", 40.0)

st.sidebar.header("3. Loads")
SDL = st.sidebar.number_input("SDL (kg/m²)", 150.0)
LL = st.sidebar.number_input("Live Load (kg/m²)", 300.0)

# ==========================================
# 3. CALCULATIONS (PREP)
# ==========================================
d_eff = h_slab - cover - (d_bar/20.0)
bar_area = get_bar_area(d_bar)
w_u = 1.2*((h_slab/100)*2400 + SDL) + 1.6*LL
ln = L1 - c1/100
Mo = (w_u * L2 * ln**2) / 8

# Strip Widths (for Reinforcement Calc)
w_cs_m = 0.5 * min(L1, L2)
w_ms_m = L2 - w_cs_m

# ==========================================
# 4. MAIN DISPLAY
# ==========================================
st.title("🏗️ Flat Slab Design & Detailing")

tab_ddm, tab_efm, tab_geo = st.tabs(["1️⃣ DDM Method (With Rebar)", "2️⃣ EFM Method", "📐 Geometry Check"])

# --- TAB 1: DDM (COMPLETE) ---
with tab_ddm:
    st.header("1. Analysis Results (Moments)")
    col1, col2 = st.columns([1, 2])
    with col1:
        st.info(f"**Total Static Moment ($M_o$):**\n# {Mo:,.2f} kg-m")
        st.markdown(f"**Strip Widths:**")
        st.write(f"- Column Strip: {w_cs_m:.2f} m")
        st.write(f"- Middle Strip: {w_ms_m:.2f} m")
    
    # Calculate Moments
    m_neg_total = 0.65 * Mo
    m_pos_total = 0.35 * Mo
    
    M_cs_neg = m_neg_total * 0.75
    M_ms_neg = m_neg_total * 0.25
    M_cs_pos = m_pos_total * 0.60
    M_ms_pos = m_pos_total * 0.40
    
    # Plot Visual Map
    with col2:
        st.pyplot(plot_moment_map(L1, L2, c1, c2, M_cs_neg, M_cs_pos, M_ms_neg, M_ms_pos))
        st.caption("แผนผังแสดงค่าโมเมนต์ในแต่ละโซน (หน่วย: kg-m)")

    st.markdown("---")
    st.header("2. Reinforcement Design (คำนวณเหล็กเสริม)")
    
    # Data Preparation for Table
    zones = [
        ("Column Strip Top (-)", M_cs_neg, w_cs_m),
        ("Column Strip Bot (+)", M_cs_pos, w_cs_m),
        ("Middle Strip Top (-)", M_ms_neg, w_ms_m),
        ("Middle Strip Bot (+)", M_ms_pos, w_ms_m)
    ]
    
    res_data = []
    for z_name, mom, width_m in zones:
        As_req, rho, rho_max, status = design_rebar(mom, width_m*100, d_eff, fc, fy)
        
        if status == "OK":
            num_bars = np.ceil(As_req / bar_area)
            if num_bars == 0: num_bars = 2 # Minimum bars usually
            spacing = (width_m * 100) / num_bars
            rebar_txt = f"{int(num_bars)} - DB{d_bar}"
            spacing_txt = f"@{spacing:.0f} cm"
            as_txt = f"{As_req:.2f}"
            status_icon = "✅"
        else:
            rebar_txt = "N/A"
            spacing_txt = "N/A"
            as_txt = f"{As_req:.2f}" if As_req != 999 else "Too High"
            status_icon = "❌ Check Size"

        res_data.append([z_name, f"{mom:,.0f}", f"{width_m*100:.0f}", as_txt, rebar_txt, spacing_txt, status_icon])
        
    df_res = pd.DataFrame(res_data, columns=["Zone", "Moment (kg-m)", "Width b (cm)", "As (cm2)", "No. of Bars", "Spacing", "Status"])
    st.dataframe(df_res, use_container_width=True)
    st.success(f"**Note:** ใช้เหล็ก DB{d_bar} (As = {bar_area:.2f} cm²/เส้น) | d_eff = {d_eff:.2f} cm")

# --- TAB 2: EFM (FLEXIBLE) ---
with tab_efm:
    st.header("Equivalent Frame Method")
    st.write("สำหรับวิธี EFM ปกติเราจะได้ค่า Moment จากโปรแกรมวิเคราะห์โครงสร้าง (Structural Analysis) เนื่องจากขึ้นอยู่กับ Stiffness")
    
    st.markdown("#### 🛠️ Input Moments from Analysis Result")
    col_inp1, col_inp2 = st.columns(2)
    with col_inp1:
        user_M_neg = st.number_input("Negative Moment (Support) [kg-m]", value=float(M_cs_neg))
    with col_inp2:
        user_M_pos = st.number_input("Positive Moment (Mid-span) [kg-m]", value=float(M_cs_pos))
        
    st.markdown("#### 🧱 Reinforcement Result")
    
    design_width = st.slider("Design Width (cm) [Ex: 100cm for per meter design]", 100, int(L2*100), 100)
    
    As_neg, _, _, st_neg = design_rebar(user_M_neg, design_width, d_eff, fc, fy)
    As_pos, _, _, st_pos = design_rebar(user_M_pos, design_width, d_eff, fc, fy)
    
    # --- แก้ไขจุดที่เกิด Error: เปลี่ยนชื่อตัวแปร layout จาก c1, c2 เป็น col_res1, col_res2 ---
    col_res1, col_res2 = st.columns(2)
    
    with col_res1:
        st.subheader("Top Reinforcement (Negative)")
        if st_neg == "OK":
            n_neg = np.ceil(As_neg/bar_area)
            if n_neg == 0: n_neg = 1
            st.metric("As Required", f"{As_neg:.2f} cm²")
            st.success(f"**Use: {int(n_neg)} - DB{d_bar}**")
            st.caption(f"Spacing approx @ {design_width/n_neg:.0f} cm")
        else:
            st.error("Section Failed / Load too high")
            
    with col_res2:
        st.subheader("Bottom Reinforcement (Positive)")
        if st_pos == "OK":
            n_pos = np.ceil(As_pos/bar_area)
            if n_pos == 0: n_pos = 1
            st.metric("As Required", f"{As_pos:.2f} cm²")
            st.success(f"**Use: {int(n_pos)} - DB{d_bar}**")
            st.caption(f"Spacing approx @ {design_width/n_pos:.0f} cm")
        else:
            st.error("Section Failed / Load too high")

# --- TAB 3: GEOMETRY ---
with tab_geo:
    # คำนวณ Inertia คร่าวๆ (ตอนนี้ c1 และ c2 คือค่า float จาก Sidebar แล้ว ไม่ใช่ Column object)
    Ic_calc = (c2 * c1**3)/12 
    st.info(f"Column Inertia (Ic) = {Ic_calc:,.0f} cm⁴ (Calculated from c1={c1}, c2={c2})")
    st.pyplot(plot_geometry_detailed(L1, L2, c1, c2, h_slab, lc, Ic_calc))
