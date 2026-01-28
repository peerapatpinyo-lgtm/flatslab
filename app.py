import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import math
from engine import calculate_detailed_slab

# --- Page Config ---
st.set_page_config(page_title="Flat Slab Expert Design", page_icon="🏗️", layout="wide")

# --- 1. Helper Functions (Practical Engineering) ---
def get_practical_spacing(as_req, max_spacing_cm):
    """
    คำนวณระยะเรียงเหล็กแบบหน้างานจริง (Construction Friendly)
    - ปัดเศษลงเป็น Step ละ 2.5 cm (เช่น 16.8 -> 15.0, 13.5 -> 12.5)
    - เลือกขนาดเหล็กอัตโนมัติ (DB12 หรือ DB16)
    """
    area_db12 = (math.pi * 1.2**2) / 4
    area_db16 = (math.pi * 1.6**2) / 4
    
    def round_down_step(val, step=2.5):
        return math.floor(val / step) * step

    # Try DB12
    s12_raw = (area_db12 * 100) / as_req
    s12_practical = round_down_step(s12_raw)
    
    # ถ้า DB12 ถี่เกินไป (< 10 cm) หรือต้องการลดจำนวนเส้น ให้ลอง DB16
    if s12_practical < 10.0:
        s16_raw = (area_db16 * 100) / as_req
        s16_practical = round_down_step(s16_raw)
        spacing = min(s16_practical, max_spacing_cm)
        return f"DB16 @ {spacing:.1f} cm"
    else:
        spacing = min(s12_practical, max_spacing_cm)
        return f"DB12 @ {spacing:.1f} cm"

def highlight_min_row(s):
    is_min = s == s.min()
    return ['background-color: #d1e7dd; color: #0f5132; font-weight: bold' if v else '' for v in is_min]

# --- Graphics ---
def plot_punching_shear(c1, c2, d, pos, direction):
    """วาดรูป Critical Section โดยหมุนตามทิศทางที่วิเคราะห์"""
    fig, ax = plt.subplots(figsize=(5, 5))
    margin = 0.5 + d
    ax.set_xlim(-margin, c1 + margin)
    ax.set_ylim(-margin, c2 + margin)
    ax.set_aspect('equal')
    ax.axis('off')
    
    # Column
    col_rect = patches.Rectangle((0, 0), c1, c2, linewidth=2, edgecolor='black', facecolor='#ffcccc', label='Column')
    ax.add_patch(col_rect)
    
    # Critical Section d/2
    d_half = d / 2
    if pos == "Interior":
        crit_rect = patches.Rectangle((-d_half, -d_half), c1+d, c2+d, linewidth=2, edgecolor='blue', linestyle='--', fill=False)
        ax.add_patch(crit_rect)
    elif pos == "Edge":
        # Draw 3 sides (Assume edge is perpendicular to analysis direction for simplicity visualization)
        # For visualization generalized:
        ax.plot([-d_half, c1+d_half], [c2+d_half, c2+d_half], 'b--', linewidth=2)
        ax.plot([c1+d_half, c1+d_half], [-d_half, c2+d_half], 'b--', linewidth=2)
        ax.plot([c1+d_half, -d_half], [-d_half, -d_half], 'b--', linewidth=2)
    elif pos == "Corner":
        ax.plot([c1+d_half, c1+d_half], [0, c2+d_half], 'b--', linewidth=2)
        ax.plot([0, c1+d_half], [c2+d_half, c2+d_half], 'b--', linewidth=2)
        
    ax.set_title(f"Critical Section ({direction}-Direction Analysis)", fontsize=10)
    return fig

# --- 2. Sidebar Input ---
with st.sidebar:
    st.header("🏗️ Design Parameters")
    
    st.subheader("1. Analysis Direction")
    direction = st.radio("Select Direction:", ["X-Direction", "Y-Direction"], horizontal=True)
    
    with st.expander("2. Geometry Inputs", expanded=True):
        pos = st.selectbox("Column Position", ["Interior", "Edge", "Corner"])
        # รับค่าตามแกน Global (X, Y)
        input_lx = st.number_input("Span Length Lx (m)", value=6.0, step=0.5)
        input_ly = st.number_input("Span Length Ly (m)", value=6.0, step=0.5)
        input_cx = st.number_input("Col Dimension X (mm)", value=400)
        input_cy = st.number_input("Col Dimension Y (mm)", value=400)
        h_init = st.number_input("Slab Thickness (mm)", value=200, step=10)

    with st.expander("3. Materials & Loads", expanded=True):
        fc = st.number_input("f'c (ksc)", value=280)
        fy = st.number_input("fy (ksc)", value=4000)
        sdl = st.number_input("SDL (kg/m²)", value=150)
        ll = st.number_input("Live Load (kg/m²)", value=300)

    st.markdown("---")
    st.info("💡 **Principal Engineer Note:**\nFor Edge/Corner columns, unbalanced moment transfer is critical. Consider using Finite Element Method (FEM) for complex geometries.")

# --- 3. Logic: Swap Variables based on Direction ---
if direction == "X-Direction":
    # Analyze along X: Span=Lx, Width=Ly, c1=cx, c2=cy
    calc_l1, calc_l2 = input_lx, input_ly
    calc_c1, calc_c2 = input_cx, input_cy
    span_label = "Lx"
else:
    # Analyze along Y: Span=Ly, Width=Lx, c1=cy, c2=cx
    calc_l1, calc_l2 = input_ly, input_lx
    calc_c1, calc_c2 = input_cy, input_cx
    span_label = "Ly"

# Run Engine
data = calculate_detailed_slab(calc_l1, calc_l2, h_init, calc_c1, calc_c2, fc, fy, sdl, ll, 20, pos)

# --- 4. Main Dashboard ---
st.title(f"📑 Structural Design Report: {direction}")

# 4.1 Executive Summary (Verdict Box)
verdict_col1, verdict_col2 = st.columns([3, 1])
with verdict_col1:
    is_punching_pass = data['ratio'] <= 1.0
    is_thickness_pass = data['h_warning'] == ""
    
    if is_punching_pass and is_thickness_pass:
        st.success(f"✅ **DESIGN ACCEPTABLE** | Final Thickness: {data['h_final']} mm | Punching Ratio: {data['ratio']:.2f}")
    elif not is_punching_pass:
        st.error(f"❌ **DESIGN FAILED:** Punching Shear Critical (Ratio {data['ratio']:.2f}) - Increase h or check Drop Panel")
    else:
        st.warning(f"⚠️ **DESIGN CAUTION:** {data['h_warning']}")

# 4.2 Tabs
tab1, tab2, tab3 = st.tabs(["📘 Analysis & Moments", "🛡️ Punching Shear", "🏗️ Reinforcement"])

# --- TAB 1 ---
with tab1:
    st.subheader(f"1. Analysis along {direction}")
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown(f"**Configuration:**")
        st.write(f"- Main Span ($L_1$): {calc_l1:.2f} m")
        st.write(f"- Transverse Span ($L_2$): {calc_l2:.2f} m")
        st.write(f"- Col Parallel ($c_1$): {calc_c1} mm")
        st.write(f"- Col Transverse ($c_2$): {calc_c2} mm")
    with col2:
        L = data['loading']
        st.latex(rf"q_u = 1.2({L['sw']:.0f} + {sdl}) + 1.6({ll}) = \mathbf{{{L['qu']:.2f}}} \; kg/m^2")
        G = data['geo']
        st.latex(rf"M_o = \frac{{q_u L_2 (L_n)^2}}{{8}} = \frac{{{L['qu']:.2f} \cdot {calc_l2} \cdot {G['ln']:.2f}^2}}{{8}} = \mathbf{{{data['mo']:,.2f}}} \; kg-m")
        st.caption(f"Note: $L_n$ is clear span in {direction}")

# --- TAB 2 ---
with tab2:
    st.subheader("2. Punching Shear Check")
    col_vis, col_data = st.columns([1, 1.5])
    
    with col_vis:
        fig_punch = plot_punching_shear(calc_c1/1000, calc_c2/1000, data['geo']['d'], pos, direction)
        st.pyplot(fig_punch)
        st.caption(f"Check based on $d = {data['geo']['d']*1000:.0f}$ mm")

    with col_data:
        P = data['punching']
        df_vc = pd.DataFrame({
            'Condition': ['Limit', 'Shape (Beta)', 'Size (Alpha)'],
            'Formula': [r'$0.33\sqrt{f_c}$', r'$0.17(1+\frac{2}{\beta})\sqrt{f_c}$', r'$0.083(2+\frac{\alpha d}{b_o})\sqrt{f_c}$'],
            'Value (MPa)': [P['v1'], P['v2'], P['v3']]
        })
        st.dataframe(df_vc.style.apply(highlight_min_row, subset=['Value (MPa)']).format({"Value (MPa)": "{:.2f}"}), use_container_width=True)
        
        # Summary Status
        vu_stress = (P['vu'] * 9.80665) / (P['bo'] * 1000 * P['d'] * 1000)
        phi_vc = 0.75 * P['vc_mpa']
        
        c_res1, c_res2 = st.columns(2)
        c_res1.metric("Actual Stress ($v_u$)", f"{vu_stress:.2f} MPa")
        c_res2.metric("Capacity ($\phi v_c$)", f"{phi_vc:.2f} MPa", delta_color="inverse" if vu_stress > phi_vc else "normal")

# --- TAB 3 ---
with tab3:
    st.subheader("3. Reinforcement (Practical Design)")
    
    col_rebar_info, col_rebar_table = st.columns([1, 2])
    with col_rebar_info:
        st.info("""
        **Construction Note:**
        * Spacing rounded down to nearest **2.5 cm**
        * Max spacing limited to **30 cm** or **2h**
        * Top bars must extend **0.3Ln** from support
        """)
        
    with col_rebar_table:
        rebar_data = []
        for loc, val in data['rebar'].items():
            loc_name = loc.replace("CS", "Column Strip").replace("MS", "Middle Strip").replace("_", " ")
            # เรียกใช้ฟังก์ชัน Practical Spacing ใหม่
            spec = get_practical_spacing(val, data['max_spacing_cm'])
            rebar_data.append([loc_name, f"{val:.2f}", f"{data['as_min']:.2f}", spec])
            
        st.table(pd.DataFrame(rebar_data, columns=["Zone", "Req. As (cm²/m)", "Min As", "Practical Selection"]))
    
    # Senior Engineer Insight Box
    with st.expander("💡 Senior Engineer's Insight (ข้อควรระวังพิเศษ)", expanded=True):
        st.markdown(f"""
        1. **Unbalanced Moment:** ในกรณีเสาขอบ (Edge/Corner) แรงเฉือนจริงอาจสูงกว่าที่คำนวณ 15-25% เนื่องจากโมเมนต์ถ่ายเข้าเสา (Unbalanced Moment Transfer) แนะนำให้เพิ่มความหนาหรือเสริมเหล็กรับแรงเฉือน
        2. **Long-term Deflection:** หาก Span ยาวเกิน 8.0 เมตร แม้ $h > h_{{min}}$ ของ ACI ก็อาจตกท้องช้างได้ ควรตรวจสอบ Deflection โดยคำนึงถึง Creep & Shrinkage ($\lambda \Delta_{{inst}}$)
        3. **Top Bar Extension:** เหล็กเสริมบนบริเวณหัวเสา (Column Strip Top) ควรยืดออกจากศูนย์กลางเสาอย่างน้อย **0.30 x {calc_l1:.2f} m = {(0.3*calc_l1):.2f} m** เพื่อให้ครอบคลุมจุดดัดกลับ (Inflection Point)
        """)
