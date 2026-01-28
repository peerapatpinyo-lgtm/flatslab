import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import math
from engine import calculate_detailed_slab

# --- Page Config ---
st.set_page_config(page_title="Flat Slab Expert Design", page_icon="🏗️", layout="wide")

# --- Helper: Dynamic Plotting Functions ---
def plot_punching_shear(c1, c2, d, pos):
    """วาดรูป Critical Section ตามขนาดจริง"""
    fig, ax = plt.subplots(figsize=(5, 5))
    
    # Setup dimensions
    margin = 0.5 + d
    ax.set_xlim(-margin, c1 + margin)
    ax.set_ylim(-margin, c2 + margin)
    ax.set_aspect('equal')
    ax.axis('off') # ปิดแกน
    
    # Draw Column (Solid Red)
    col_rect = patches.Rectangle((0, 0), c1, c2, linewidth=2, edgecolor='black', facecolor='#ffcccc', label='Column')
    ax.add_patch(col_rect)
    
    # Draw Critical Section (Dashed Blue) at d/2
    d_half = d / 2
    
    if pos == "Interior":
        crit_rect = patches.Rectangle((-d_half, -d_half), c1+d, c2+d, linewidth=2, edgecolor='blue', linestyle='--', fill=False, label='Critical Section (d/2)')
        ax.add_patch(crit_rect)
    elif pos == "Edge":
        # วาด 3 ด้าน (สมมติขอบอยู่ด้านซ้าย x=0)
        # เส้นบน
        ax.plot([-d_half, c1+d_half], [c2+d_half, c2+d_half], 'b--', linewidth=2)
        # เส้นขวา
        ax.plot([c1+d_half, c1+d_half], [-d_half, c2+d_half], 'b--', linewidth=2)
        # เส้นล่าง
        ax.plot([c1+d_half, -d_half], [-d_half, -d_half], 'b--', linewidth=2, label='Critical Section (d/2)')
    elif pos == "Corner":
        # วาด 2 ด้าน (สมมติมุมซ้ายล่าง)
        ax.plot([c1+d_half, c1+d_half], [0, c2+d_half], 'b--', linewidth=2) # ขวา
        ax.plot([0, c1+d_half], [c2+d_half, c2+d_half], 'b--', linewidth=2, label='Critical Section (d/2)')
        
    ax.legend(loc='upper right', fontsize='small')
    ax.set_title(f"{pos} Column Punching Check", fontsize=10)
    return fig

def plot_strip_layout(lx, ly, strip_width):
    """วาดรูปการแบ่ง Column Strip / Middle Strip"""
    fig, ax = plt.subplots(figsize=(6, 4))
    
    # Draw Slab Panel
    ax.set_xlim(0, lx)
    ax.set_ylim(0, ly)
    ax.set_aspect('equal')
    ax.set_xlabel("Span Lx (m)")
    ax.set_ylabel("Span Ly (m)")
    
    # Color Zones
    # Column Strip (Left & Right)
    cs_color = '#e6f2ff' # Light Blue
    ms_color = '#ffffff' # White
    
    # Left CS
    ax.add_patch(patches.Rectangle((0, 0), strip_width, ly, facecolor=cs_color, edgecolor='gray', alpha=0.5))
    # Right CS
    ax.add_patch(patches.Rectangle((lx-strip_width, 0), strip_width, ly, facecolor=cs_color, edgecolor='gray', alpha=0.5))
    # Middle Strip
    ax.add_patch(patches.Rectangle((strip_width, 0), lx - 2*strip_width, ly, facecolor=ms_color, edgecolor='gray', alpha=0.5))
    
    # Text Labels
    ax.text(strip_width/2, ly/2, "Column\nStrip", ha='center', va='center', fontsize=8, color='blue')
    ax.text(lx - strip_width/2, ly/2, "Column\nStrip", ha='center', va='center', fontsize=8, color='blue')
    ax.text(lx/2, ly/2, "Middle Strip", ha='center', va='center', fontsize=10, fontweight='bold')
    
    ax.set_title(f"Strip Distribution (CS Width = {strip_width:.2f} m)", fontsize=10)
    return fig

def get_rebar_spec(as_req, max_spacing_cm):
    area_db12 = (math.pi * 1.2**2) / 4
    area_db16 = (math.pi * 1.6**2) / 4
    s12 = (area_db12 * 100) / as_req
    if s12 < 10:
        s16 = (area_db16 * 100) / as_req
        return f"DB16 @ {int(min(s16, max_spacing_cm))} cm"
    return f"DB12 @ {int(min(s12, max_spacing_cm))} cm"

def highlight_min_row(s):
    is_min = s == s.min()
    return ['background-color: #d1e7dd; color: #0f5132; font-weight: bold' if v else '' for v in is_min]

# --- Sidebar ---
with st.sidebar:
    st.header("🏗️ Design Parameters")
    with st.expander("1. Geometry", expanded=True):
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

# --- Calculation ---
data = calculate_detailed_slab(lx, ly, h_init, c1, c2, fc, fy, sdl, ll, 20, pos)

# --- Main Report ---
st.title("📑 Structural Design Report: RC Flat Slab")
st.markdown(f"**Status:** {'✅ PASSED' if data['ratio'] <= 1.0 else '❌ FAILED'} | **Final Thickness:** {data['h_final']} mm")

if data['h_warning']:
    st.warning(f"⚠️ {data['h_warning']}")

tab1, tab2, tab3 = st.tabs(["📘 1. Load & Moment", "🛡️ 2. Punching Shear", "🏗️ 3. Reinforcement"])

# --- TAB 1 ---
with tab1:
    st.subheader("1. Load Analysis")
    col1, col2 = st.columns([1, 2])
    with col1:
        st.info("Concept: Load -> Moment -> Strip")
    with col2:
        L = data['loading']
        st.latex(rf"q_u = 1.2({L['sw']:.0f} + {sdl}) + 1.6({ll}) = \mathbf{{{L['qu']:.2f}}} \; kg/m^2")
        G = data['geo']
        st.latex(rf"M_o = \frac{{{L['qu']:.2f} \cdot {ly} \cdot {G['ln']:.2f}^2}}{{8}} = \mathbf{{{data['mo']:,.2f}}} \; kg-m")

# --- TAB 2 ---
with tab2:
    st.subheader("2. Punching Shear Verification")
    col_vis, col_data = st.columns([1, 1.5])
    
    with col_vis:
        # ** เรียกใช้ฟังก์ชันวาดกราฟิกที่นี่ **
        fig_punch = plot_punching_shear(c1/1000, c2/1000, data['geo']['d'], pos)
        st.pyplot(fig_punch)
        st.caption(f"Critical Perimeter at d/2 = {data['geo']['d']*1000/2:.0f} mm")

    with col_data:
        P = data['punching']
        df_vc = pd.DataFrame({
            'Condition': ['Limit', 'Shape (Beta)', 'Size (Alpha)'],
            'Formula': [r'$0.33\sqrt{f_c}$', r'$0.17(1+\frac{2}{\beta})\sqrt{f_c}$', r'$0.083(2+\frac{\alpha d}{b_o})\sqrt{f_c}$'],
            'Value (MPa)': [P['v1'], P['v2'], P['v3']]
        })
        st.dataframe(df_vc.style.apply(highlight_min_row, subset=['Value (MPa)']).format({"Value (MPa)": "{:.2f}"}), use_container_width=True)
        
        vu_stress = (P['vu'] * 9.80665) / (P['bo'] * 1000 * P['d'] * 1000)
        phi_vc = 0.75 * P['vc_mpa']
        
        c1, c2 = st.columns(2)
        c1.metric("Actual Stress ($v_u$)", f"{vu_stress:.2f} MPa")
        c2.metric("Capacity ($\phi v_c$)", f"{phi_vc:.2f} MPa", delta_color="normal" if vu_stress<=phi_vc else "inverse")

# --- TAB 3 ---
with tab3:
    st.subheader("3. Reinforcement Layout")
    col_plot, col_tab = st.columns([1, 1.5])
    
    with col_plot:
        # ** เรียกใช้ฟังก์ชันวาดกราฟิก Strip **
        strip_w = min(lx, ly) / 4
        fig_strip = plot_strip_layout(lx, ly, strip_w)
        st.pyplot(fig_strip)
        
    with col_tab:
        rebar_data = []
        for loc, val in data['rebar'].items():
            loc_name = loc.replace("CS", "Column Strip").replace("MS", "Middle Strip").replace("_", " ")
            spec = get_rebar_spec(val, data['max_spacing_cm'])
            rebar_data.append([loc_name, f"{val:.2f}", f"{data['as_min']:.2f}", spec])
        st.table(pd.DataFrame(rebar_data, columns=["Zone", "Req. As", "Min As", "Selection"]))
