import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import math
from engine import calculate_detailed_slab

# --- Page Config ---
st.set_page_config(page_title="Flat Slab Design for Engineers", page_icon="👷‍♂️", layout="wide")

# --- 1. Helper Functions (วิศวกรรมหน้างาน) ---
def get_practical_spacing(as_req, max_spacing_cm):
    """
    คำนวณระยะเรียงเหล็กแบบหน้างาน (Construction Friendly)
    - สูตร: math.floor(val / 2.5) * 2.5
    - ผลลัพธ์จะเป็นสเต็ป: 10.0, 12.5, 15.0, 17.5, 20.0...
    """
    area_db12 = (math.pi * 1.2**2) / 4
    area_db16 = (math.pi * 1.6**2) / 4
    
    def round_step(val):
        # ปัดลงทีละ 2.5 cm เพื่อความปลอดภัยและวัดง่าย
        return math.floor(val / 2.5) * 2.5

    # ลองใช้ DB12 ก่อน
    s12_raw = (area_db12 * 100) / as_req
    s12_practical = round_step(s12_raw)
    
    # ถ้า DB12 ถี่เกินไป (< 10 cm) ให้ขยับไปใช้ DB16
    if s12_practical < 10.0:
        s16_raw = (area_db16 * 100) / as_req
        s16_practical = round_step(s16_raw)
        spacing = min(s16_practical, max_spacing_cm)
        return f"DB16 @ {spacing:.1f} cm"
    else:
        spacing = min(s12_practical, max_spacing_cm)
        return f"DB12 @ {spacing:.1f} cm"

def highlight_min_row(s):
    is_min = s == s.min()
    return ['background-color: #d1e7dd; color: #0f5132; font-weight: bold' if v else '' for v in is_min]

# --- 2. Visualization (กราฟิกเพื่อความเข้าใจ) ---
def plot_punching_detailed(c1, c2, d, pos):
    """
    วาดรูป Punching Shear แบบละเอียด
    - สีแดง: ตอม่อ (Column)
    - สีเหลืองอ่อน: พื้นที่วิกฤต (Critical Area) ที่แรงถ่ายลงเสาโดยตรง
    - เส้นประ: เส้นรอบรูปวิกฤต (Critical Perimeter)
    """
    fig, ax = plt.subplots(figsize=(5, 5))
    margin = 0.6 + d
    ax.set_xlim(-margin, c1 + margin)
    ax.set_ylim(-margin, c2 + margin)
    ax.set_aspect('equal')
    ax.axis('off')
    
    # 1. วาดตอม่อ (Column)
    col_rect = patches.Rectangle((0, 0), c1, c2, linewidth=2, edgecolor='black', facecolor='#ff9999', label='Column', zorder=5)
    ax.add_patch(col_rect)
    
    # 2. คำนวณระยะขอบเขตวิกฤต (d/2)
    d_half = d / 2
    
    # 3. วาด Critical Area ตามตำแหน่งเสา
    if pos == "Interior":
        # พื้นที่รอบเสาทุกด้าน
        crit_patch = patches.Rectangle((-d_half, -d_half), c1+d, c2+d, 
                                     linewidth=2, edgecolor='blue', linestyle='--', 
                                     facecolor='#fff5cc', alpha=0.6, label='Critical Area (Ac)')
        ax.add_patch(crit_patch)
        
    elif pos == "Edge":
        # สมมติขอบอยู่ด้านซ้าย (x=0)
        # วาด Polygon แทน Rectangle เพื่อความยืดหยุ่น
        coords = [
            (-d_half, -d_half),           # ล่างซ้าย (เลยขอบมา) -> ตัดที่ x=0 ในความเป็นจริง แต่วาดให้เห็น Concept
            (c1+d_half, -d_half),         # ล่างขวา
            (c1+d_half, c2+d_half),       # บนขวา
            (-d_half, c2+d_half)          # บนซ้าย
        ]
        # ในทางปฏิบัติ ACI ตัดที่ขอบเสา แต่เพื่อให้เห็นภาพ Perimeter
        # เราจะวาดเส้นรอบรูปเฉพาะด้านที่อยู่ในเนื้อคอนกรีต
        ax.plot([-d_half, c1+d_half], [c2+d_half, c2+d_half], 'b--', linewidth=2) # บน
        ax.plot([c1+d_half, c1+d_half], [-d_half, c2+d_half], 'b--', linewidth=2) # ขวา
        ax.plot([c1+d_half, -d_half], [-d_half, -d_half], 'b--', linewidth=2) # ล่าง
        
        # Fill Area
        rect = patches.Rectangle((0, -d_half), c1+d_half, c2+d, facecolor='#fff5cc', alpha=0.6, label='Critical Area')
        ax.add_patch(rect)

    elif pos == "Corner":
        # สมมติมุมซ้ายล่าง
        ax.plot([c1+d_half, c1+d_half], [0, c2+d_half], 'b--', linewidth=2) # ขวา
        ax.plot([0, c1+d_half], [c2+d_half, c2+d_half], 'b--', linewidth=2) # บน
        
        # Fill Area
        rect = patches.Rectangle((0, 0), c1+d_half, c2+d_half, facecolor='#fff5cc', alpha=0.6, label='Critical Area')
        ax.add_patch(rect)
        
    ax.legend(loc='upper right', fontsize='small')
    ax.set_title(f"Punching Shear Critical Section\n(Position: {pos})", fontsize=10)
    return fig

# --- 3. Sidebar Input ---
with st.sidebar:
    st.header("🏗️ Design Parameters")
    
    with st.expander("1. ข้อมูลรูปทรง (Geometry)", expanded=True):
        pos = st.selectbox("ตำแหน่งเสา (Column Position)", ["Interior", "Edge", "Corner"])
        lx = st.number_input("ความยาวช่วง Lx (m)", value=6.0, step=0.5)
        ly = st.number_input("ความยาวช่วง Ly (m)", value=6.0, step=0.5)
        h_init = st.number_input("ความหนาพื้นเบื้องต้น (mm)", value=200, step=10)
        c1 = st.number_input("ขนาดเสาด้าน c1 (mm)", value=400)
        c2 = st.number_input("ขนาดเสาด้าน c2 (mm)", value=400)

    with st.expander("2. วัสดุและน้ำหนักบรรทุก", expanded=True):
        fc = st.number_input("กำลังคอนกรีต fc' (ksc)", value=280)
        fy = st.number_input("กำลังเหล็กเสริม fy (ksc)", value=4000)
        sdl = st.number_input("Superimposed DL (kg/m²)", value=150, help="น้ำหนักวัสดุปูผิว, งานระบบ, ฝ้าเพดาน")
        ll = st.number_input("Live Load (kg/m²)", value=300, help="น้ำหนักจรตามประเภทอาคาร")

# --- Execute Engine ---
# เรียกใช้ Engine (ตรวจสอบว่าไฟล์ engine.py อยู่ใน folder เดียวกัน)
data = calculate_detailed_slab(lx, ly, h_init, c1, c2, fc, fy, sdl, ll, 20, pos)

# --- 4. Main Report (Design Verdict) ---
st.title("📑 รายการคำนวณออกแบบพื้นไร้คาน (Flat Slab)")

# สรุปผลการออกแบบ (Design Verdict)
verdict_container = st.container()
with verdict_container:
    # Logic การตรวจสอบ
    check_shear = data['ratio'] <= 1.0
    check_thickness = data['h_warning'] == ""
    
    if check_shear and check_thickness:
        st.success(f"""
        ### ✅ สรุปผล: ผ่านเกณฑ์มาตรฐาน ACI 318
        * **ความหนาพื้น:** {data['h_final']} mm (เหมาะสม)
        * **อัตราส่วนแรงเฉือน (Ratio):** {data['ratio']:.2f} (< 1.00 ปลอดภัย)
        """)
    elif not check_shear:
        st.error(f"""
        ### ❌ สรุปผล: ไม่ผ่านเรื่องแรงเฉือนทะลุ (Punching Shear)
        * **Ratio:** {data['ratio']:.2f} (เกิน 1.00 อันตราย!)
        * **คำแนะนำ:** กรุณาเพิ่มความหนาพื้น, ขยายขนาดเสา, หรือใส่ Drop Panel
        """)
    else:
        st.warning(f"""
        ### ⚠️ สรุปผล: ผ่านแบบมีเงื่อนไข
        * {data['h_warning']} (อาจมีปัญหาการแอ่นตัวในระยะยาว)
        """)

# --- Tabs ---
tab1, tab2, tab3 = st.tabs(["📘 1. วิเคราะห์น้ำหนัก", "🛡️ 2. แรงเฉือนทะลุ", "🏗️ 3. เหล็กเสริม"])

# --- TAB 1: Loads ---
with tab1:
    st.subheader("1. วิเคราะห์น้ำหนักและโมเมนต์ (Load & Moment)")
    st.caption("💡 ขั้นตอนนี้เพื่อหาว่าพื้นต้องรับน้ำหนักจริงเท่าไหร่ และเกิดโมเมนต์ดัดเท่าไหร่เพื่อนำไปคำนวณเหล็กเสริม")
    
    col_load1, col_load2 = st.columns([1, 2])
    with col_load1:
         st.info("Factor ตามกฎหมาย:\n* Dead Load x 1.2\n* Live Load x 1.6")
    
    with col_load2:
        L = data['loading']
        st.markdown("**1.1 น้ำหนักบรรทุกประลัย ($q_u$)**")
        st.latex(rf"q_u = 1.2(SW + SDL) + 1.6(LL)")
        st.latex(rf"q_u = 1.2({L['sw']:.0f} + {sdl}) + 1.6({ll}) = \mathbf{{{L['qu']:.2f}}} \; kg/m^2")
        
        st.markdown("**1.2 โมเมนต์สถิตยศาสตร์รวม ($M_o$)**")
        G = data['geo']
        st.latex(rf"M_o = \frac{{q_u L_2 L_n^2}}{{8}} = \mathbf{{{data['mo']:,.2f}}} \; kg-m")
        st.caption(f"*ใช้ค่า Clear Span ($L_n$) = {G['ln']:.2f} m ในการคำนวณ")

# --- TAB 2: Punching Shear ---
with tab2:
    st.subheader("2. ตรวจสอบแรงเฉือนทะลุ (Punching Shear)")
    st.caption("💡 หัวใจสำคัญของ Flat Slab คือต้องเช็คว่า 'เสาจะทะลุพื้น' หรือไม่ โดยดูที่หน้าตัดวิกฤตระยะ d/2 จากขอบเสา")
    
    col_vis, col_calc = st.columns([1, 1.5])
    
    with col_vis:
        # แสดงรูปกราฟิกที่วาดขึ้นเอง
        fig = plot_punching_detailed(c1/1000, c2/1000, data['geo']['d'], pos)
        st.pyplot(fig)
        st.caption("พื้นที่สีเหลืองคือ Critical Area ($A_{crit}$) ภายในเส้นประ")

    with col_calc:
        P = data['punching']
        
        st.markdown("##### 2.1 เปรียบเทียบกำลังรับแรงของคอนกรีต ($v_c$)")
        st.write("เลือกค่าที่น้อยที่สุดจาก 3 สูตรของ ACI (Governing Case):")
        
        df_vc = pd.DataFrame({
            'เงื่อนไข (Condition)': ['Limit (ปกติ)', 'Shape Effect (รูปร่างเสา)', 'Size Effect (ขนาด)'],
            'สูตรคำนวณ': [r'$0.33\sqrt{f_c}$', r'$0.17(1+\frac{2}{\beta})\sqrt{f_c}$', r'$0.083(2+\frac{\alpha d}{b_o})\sqrt{f_c}$'],
            'ค่าที่ได้ (MPa)': [P['v1'], P['v2'], P['v3']]
        })
        st.dataframe(df_vc.style.apply(highlight_min_row, subset=['ค่าที่ได้ (MPa)']).format({"ค่าที่ได้ (MPa)": "{:.2f}"}), use_container_width=True)
        
        st.markdown("##### 2.2 ตรวจสอบความปลอดภัย")
        vu_stress = (P['vu'] * 9.80665) / (P['bo'] * 1000 * P['d'] * 1000)
        phi_vc = 0.75 * P['vc_mpa']
        
        c1_res, c2_res = st.columns(2)
        c1_res.metric("แรงเฉือนที่เกิดขึ้น ($v_u$)", f"{vu_stress:.2f} MPa")
        c2_res.metric("กำลังที่รับได้ ($\phi v_c$)", f"{phi_vc:.2f} MPa", 
                      delta="ปลอดภัย" if vu_stress <= phi_vc else "อันตราย", 
                      delta_color="normal" if vu_stress <= phi_vc else "inverse")

# --- TAB 3: Reinforcement ---
with tab3:
    st.subheader("3. ออกแบบเหล็กเสริม (Reinforcement)")
    st.caption("💡 ปริมาณเหล็กเสริมคำนวณตามโมเมนต์ในแต่ละแถบ (Strip) และปัดเศษระยะห่างให้หน้างานทำงานง่าย")
    
    col_img_rebar, col_table_rebar = st.columns([1, 2])
    
    with col_img_rebar:
        
        st.info("""
        **ข้อกำหนดหน้างาน:**
        * ระยะห่าง (Spacing) ปัดเศษทีละ 2.5 cm
        * เหล็กบน (Top Bar) ต้องยืดปลายตามมาตรฐาน
        * ระยะหุ้ม (Cover) 20 mm (ภายใน)
        """)
        
    with col_table_rebar:
        rebar_rows = []
        for loc, val in data['rebar'].items():
            loc_name = loc.replace("CS", "Column Strip").replace("MS", "Middle Strip").replace("_", " ")
            # ใช้ฟังก์ชัน Practical Rounding
            spec = get_practical_spacing(val, data['max_spacing_cm'])
            rebar_rows.append([loc_name, f"{val:.2f}", f"{data['as_min']:.2f}", spec])
            
        df_rebar = pd.DataFrame(rebar_rows, columns=["ตำแหน่ง (Location)", "As ต้องการ (cm²)", "As ขั้นต่ำ", "แนะนำ (Construction Spec)"])
        st.table(df_rebar)
