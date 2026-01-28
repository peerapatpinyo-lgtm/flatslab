import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import math
from engine import calculate_detailed_slab

# --- Page Config ---
st.set_page_config(page_title="Flat Slab Expert Design", page_icon="🏗️", layout="wide")

# --- Helper Functions & Graphics (คงเดิมจากเวอร์ชันก่อน) ---
def get_practical_spacing(as_req, max_spacing_cm):
    area_db12 = (math.pi * 1.2**2) / 4
    area_db16 = (math.pi * 1.6**2) / 4
    def round_step(val): return math.floor(val / 2.5) * 2.5
    s12_raw = (area_db12 * 100) / as_req
    s12_practical = round_step(s12_raw)
    if s12_practical < 10.0:
        s16_raw = (area_db16 * 100) / as_req
        s16_practical = round_step(s16_raw)
        return f"DB16 @ {min(s16_practical, max_spacing_cm):.1f} cm"
    return f"DB12 @ {min(s12_practical, max_spacing_cm):.1f} cm"

def highlight_min_row(s):
    is_min = s == s.min()
    return ['background-color: #d1e7dd; color: #0f5132; font-weight: bold' if v else '' for v in is_min]

def plot_punching_detailed(c1, c2, d, pos):
    fig, ax = plt.subplots(figsize=(5, 5))
    margin = 0.6 + d
    ax.set_xlim(-margin, c1 + margin)
    ax.set_ylim(-margin, c2 + margin)
    ax.set_aspect('equal')
    ax.axis('off')
    col_rect = patches.Rectangle((0, 0), c1, c2, linewidth=2, edgecolor='black', facecolor='#ff9999', label='Column', zorder=5)
    ax.add_patch(col_rect)
    d_half = d / 2
    if pos == "Interior":
        crit_patch = patches.Rectangle((-d_half, -d_half), c1+d, c2+d, linewidth=2, edgecolor='blue', linestyle='--', facecolor='#fff5cc', alpha=0.6, label='Critical Area (Acrit)')
        ax.add_patch(crit_patch)
    elif pos == "Edge":
        ax.plot([-d_half, c1+d_half], [c2+d_half, c2+d_half], 'b--', linewidth=2)
        ax.plot([c1+d_half, c1+d_half], [-d_half, c2+d_half], 'b--', linewidth=2)
        ax.plot([c1+d_half, -d_half], [-d_half, -d_half], 'b--', linewidth=2)
        rect = patches.Rectangle((0, -d_half), c1+d_half, c2+d, facecolor='#fff5cc', alpha=0.6, label='Critical Area')
        ax.add_patch(rect)
    elif pos == "Corner":
        ax.plot([c1+d_half, c1+d_half], [0, c2+d_half], 'b--', linewidth=2)
        ax.plot([0, c1+d_half], [c2+d_half, c2+d_half], 'b--', linewidth=2)
        rect = patches.Rectangle((0, 0), c1+d_half, c2+d_half, facecolor='#fff5cc', alpha=0.6, label='Critical Area')
        ax.add_patch(rect)
    ax.legend(loc='upper right', fontsize='small')
    ax.set_title(f"Punching Shear Critical Section\n(Position: {pos})", fontsize=10)
    return fig

# --- Sidebar Input ---
with st.sidebar:
    st.header("🏗️ Design Parameters")
    
    with st.expander("1. Geometry Inputs", expanded=True):
        pos = st.selectbox("Column Position", ["Interior", "Edge", "Corner"])
        lx = st.number_input("Span Lx (m)", value=6.0, step=0.5)
        ly = st.number_input("Span Ly (m)", value=6.0, step=0.5)
        h_init = st.number_input("Slab Thickness (mm)", value=200, step=10)
        c1 = st.number_input("Col Width c1 (mm)", value=400)
        c2 = st.number_input("Col Depth c2 (mm)", value=400)

    with st.expander("2. Loads & Materials", expanded=True):
        fc = st.number_input("f'c (ksc)", value=280)
        fy = st.number_input("fy (ksc)", value=4000)
        sdl = st.number_input("SDL (kg/m²)", value=150)
        ll = st.number_input("Live Load (kg/m²)", value=300)
        
    # *** Update: Custom Load Factors ***
    with st.expander("3. Load Factors (Custom)", expanded=False):
        dl_fac = st.number_input("Dead Load Factor", value=1.2, step=0.1, format="%.2f")
        ll_fac = st.number_input("Live Load Factor", value=1.6, step=0.1, format="%.2f")

# --- Execute Engine ---
# ส่ง Custom Factors เข้าไปใน engine
data = calculate_detailed_slab(lx, ly, h_init, c1, c2, fc, fy, sdl, ll, 20, pos, dl_factor=dl_fac, ll_factor=ll_fac)

# --- Main Report ---
st.title("📑 รายการคำนวณออกแบบพื้นไร้คาน (Flat Slab)")

# Verdict
check_shear = data['ratio'] <= 1.0
check_thickness = data['h_warning'] == ""
if check_shear and check_thickness:
    st.success(f"✅ **DESIGN ACCEPTABLE** (Ratio: {data['ratio']:.2f}) | Thickness: {data['h_final']} mm")
elif not check_shear:
    st.error(f"❌ **FAILED: Punching Shear** (Ratio: {data['ratio']:.2f}) | Try increasing thickness or c1/c2")
else:
    st.warning(f"⚠️ **CAUTION:** {data['h_warning']}")

tab1, tab2, tab3 = st.tabs(["📘 1. Load & Moment", "🛡️ 2. Punching Shear", "🏗️ 3. Reinforcement"])

# --- TAB 1: Loads & Moment ---
with tab1:
    st.subheader("1. Load Analysis (วิเคราะห์น้ำหนัก)")
    
    col_factor, col_trib = st.columns(2)
    with col_factor:
        st.info(f"**Load Factors:** DL x {data['loading']['factors']['dl']} | LL x {data['loading']['factors']['ll']}")
        L = data['loading']
        st.latex(rf"q_u = {data['loading']['factors']['dl']}({L['sw']:.0f} + {sdl}) + {data['loading']['factors']['ll']}({ll}) = \mathbf{{{L['qu']:.2f}}} \; kg/m^2")
    
    with col_trib:
        # *** Update: Tributary Logic ***
        st.markdown(f"**Tributary Data (พื้นที่รับน้ำหนัก):**")
        st.write(f"- Tributary Area ($A_t = L_x \cdot L_y$): **{L['trib_area']:.2f} m²**")
        st.write(f"- Total Load on Column ($P_u$): **{L['total_load']:,.0f} kg**")

    st.divider()
    
    st.subheader("2. Static Moment ($M_o$) Calculation")
    G = data['geo']
    
    # *** Update: Show Ln Substitution ***
    st.markdown("##### Step A: หาความยาวช่วงสุทธิ (Clear Span, $L_n$)")
    st.write("หักลบขนาดเสาออกจากความยาวช่วง ($L_x - c_1$):")
    st.latex(rf"L_n = L_x - c_1 = {lx} - {c1/1000} = \mathbf{{{G['ln_calc']:.2f}}} \; m")
    if G['ln_calc'] < 0.65 * lx:
         st.warning(f"Note: Calculated Ln ({G['ln_calc']:.2f}) < 0.65Lx. Using 0.65Lx = {0.65*lx:.2f} m as per ACI code.")

    st.markdown("##### Step B: คำนวณโมเมนต์ตั้งต้น ($M_o$)")
    st.latex(rf"M_o = \frac{{q_u L_y (L_n)^2}}{{8}} = \frac{{{L['qu']:.2f} \cdot {ly} \cdot {G['ln']:.2f}^2}}{{8}} = \mathbf{{{data['mo']:,.2f}}} \; kg-m")

# --- TAB 2: Punching Shear ---
with tab2:
    st.subheader("2. Punching Shear Verification")
    col_vis, col_calc = st.columns([1, 1.5])
    
    with col_vis:
        fig = plot_punching_detailed(c1/1000, c2/1000, data['geo']['d'], pos)
        st.pyplot(fig)
        
        # *** Update: Education Note ***
        st.info("""
        **🎓 Education Note:**
        * **$A_{crit}$ (สีเหลือง):** คือพื้นที่หน้าตัดวิกฤต เป็นจุดที่คอนกรีตต้องรับแรงเฉือนสูงสุด
        * หากแรงเฉือนมากเกินไป พื้นจะเกิดรอยร้าวทะลุเป็นรูปกรวย (Punching Cone) บริเวณรอบๆ เส้นประสีน้ำเงิน
        """)

    with col_calc:
        P = data['punching']
        
        st.markdown(f"##### Key Parameters")
        # *** Update: Show bo Value ***
        st.write(f"1. Effective Depth ($d$): **{P['d']*1000:.0f} mm**")
        st.write(f"2. Critical Perimeter ($b_o$): **{P['bo']*1000:.0f} mm** (เส้นรอบรูปวิกฤต)")
        
        st.markdown("##### Capacity Check ($v_c$)")
        df_vc = pd.DataFrame({
            'Condition': ['Limit', 'Shape (Beta)', 'Size (Alpha)'],
            'Formula': [r'$0.33\sqrt{f_c}$', r'$0.17(1+\frac{2}{\beta})\sqrt{f_c}$', r'$0.083(2+\frac{\alpha d}{b_o})\sqrt{f_c}$'],
            'Value (MPa)': [P['v1'], P['v2'], P['v3']]
        })
        st.dataframe(df_vc.style.apply(highlight_min_row, subset=['Value (MPa)']).format({"Value (MPa)": "{:.2f}"}), use_container_width=True)
        
        vu_stress = (P['vu'] * 9.80665) / (P['bo'] * 1000 * P['d'] * 1000)
        phi_vc = 0.75 * P['vc_mpa']
        
        c1_res, c2_res = st.columns(2)
        c1_res.metric("Stress ($v_u$)", f"{vu_stress:.2f} MPa")
        c2_res.metric("Capacity ($\phi v_c$)", f"{phi_vc:.2f} MPa", delta_color="inverse" if vu_stress > phi_vc else "normal")

# --- TAB 3: Reinforcement ---
with tab3:
    st.subheader("3. Reinforcement Specification")
    
    st.info("**Spec:** Practical spacing rounded to nearest 2.5 cm step.")
    rebar_rows = []
    for loc, val in data['rebar'].items():
        loc_name = loc.replace("CS", "Column Strip").replace("MS", "Middle Strip").replace("_", " ")
        spec = get_practical_spacing(val, data['max_spacing_cm'])
        rebar_rows.append([loc_name, f"{val:.2f}", f"{data['as_min']:.2f}", spec])
    st.table(pd.DataFrame(rebar_rows, columns=["Location", "Req. As", "Min As", "Selection"]))
