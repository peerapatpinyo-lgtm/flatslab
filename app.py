import streamlit as st
import pandas as pd
import math
from engine import calculate_detailed_slab

# --- 1. System Config & Helper Functions ---
st.set_page_config(page_title="Flat Slab Expert Design", page_icon="🏗️", layout="wide")

def get_rebar_spec(as_req, max_spacing_cm):
    """เลือกเหล็กเสริม DB12 หรือ DB16 และปัดเศษระยะห่างให้ทำงานง่าย"""
    area_db12 = (math.pi * 1.2**2) / 4
    area_db16 = (math.pi * 1.6**2) / 4
    
    # Try DB12 first
    s12 = (area_db12 * 100) / as_req
    if s12 < 10: # ถ้าถี่เกินไป ให้ขยับไปใช้ DB16
        s16 = (area_db16 * 100) / as_req
        spacing = min(s16, max_spacing_cm)
        return f"DB16 @ {int(spacing)} cm"
    else:
        spacing = min(s12, max_spacing_cm)
        return f"DB12 @ {int(spacing)} cm"

def highlight_min_row(s):
    """Highlight ค่าที่ต่ำที่สุดใน Series (สำหรับหา Governing Case)"""
    is_min = s == s.min()
    return ['background-color: #d1e7dd; color: #0f5132; font-weight: bold' if v else '' for v in is_min]

# --- 2. Sidebar Input ---
with st.sidebar:
    st.header("🏗️ Design Parameters")
    st.info("ACI 318-19 (Metric Unit)")
    
    with st.expander("1. Geometry (ขนาดโครงสร้าง)", expanded=True):
        pos = st.selectbox("Column Position", ["Interior", "Edge", "Corner"])
        lx = st.number_input("Span Lx (m)", value=6.0, step=0.5)
        ly = st.number_input("Span Ly (m)", value=6.0, step=0.5)
        h_init = st.number_input("Slab Thickness (mm)", value=200, step=10)
        c1 = st.number_input("Col Width c1 (mm)", value=400)
        c2 = st.number_input("Col Depth c2 (mm)", value=400)

    with st.expander("2. Loads & Materials (วัสดุและน้ำหนัก)", expanded=True):
        fc = st.number_input("Concrete f'c (ksc)", value=280)
        fy = st.number_input("Rebar fy (ksc)", value=4000)
        sdl = st.number_input("SDL (kg/m²)", value=150)
        ll = st.number_input("Live Load (kg/m²)", value=300)
    
    st.markdown("---")
    st.caption("Engine v1.2 | Refactored for Explainability")

# --- 3. Execute Engine ---
data = calculate_detailed_slab(lx, ly, h_init, c1, c2, fc, fy, sdl, ll, 20, pos)

# --- 4. Main Report Display ---
st.title("📑 Structural Design Report: RC Flat Slab")
st.markdown(f"**Status:** {'✅ PASSED' if data['ratio'] <= 1.0 else '❌ FAILED'} | **Final Thickness:** {data['h_final']} mm")

# Warning Banner
if data['h_warning']:
    st.warning(f"⚠️ {data['h_warning']}")

tab1, tab2, tab3 = st.tabs(["📘 1. Load & Moment", "🛡️ 2. Punching Shear", "🏗️ 3. Reinforcement"])

# ==========================================
# TAB 1: Load Analysis & Static Moment
# ==========================================
with tab1:
    st.subheader("1.1 Load Analysis (การวิเคราะห์น้ำหนัก)")
    col_img1, col_calc1 = st.columns([1, 2])
    
    with col_img1:
        # Placeholder for Diagram
        st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/6/64/Slab_load_distribution.svg/300px-Slab_load_distribution.svg.png", caption="Uniform Load Distribution", use_container_width=True)
    
    with col_calc1:
        L = data['loading']
        st.markdown("##### Factored Load ($q_u$)")
        st.write("น้ำหนักบรรทุกประลัยคำนวณจาก $1.2DL + 1.6LL$:")
        
        # Detailed Substitution
        st.latex(rf"""
        \begin{{aligned}}
        q_u &= 1.2(SW + SDL) + 1.6(LL) \\
            &= 1.2({L['sw']:.0f} + {sdl}) + 1.6({ll}) \\
            &= {L['dl_fact']:.2f} + {L['ll_fact']:.2f} \\
            &= \mathbf{{{L['qu']:.2f}}} \; \text{{kg/m}}^2
        \end{{aligned}}
        """)

    st.divider()
    
    st.subheader("1.2 Static Moment ($M_o$)")
    G = data['geo']
    st.markdown("##### Direct Design Method (DDM)")
    
    st.latex(rf"L_n = L_x - c_1 = {lx} - {c1/1000} = \mathbf{{{G['ln']:.2f}}} \; \text{{m}}")
    
    st.latex(rf"""
    \begin{{aligned}}
    M_o &= \frac{{q_u L_y L_n^2}}{{8}} \\
        &= \frac{{{L['qu']:.2f} \cdot {ly} \cdot {G['ln']:.2f}^2}}{{8}} \\
        &= \mathbf{{{data['mo']:,.2f}}} \; \text{{kg-m}}
    \end{{aligned}}
    """)
    st.info("💡 $M_o$ คือโมเมนต์รวมที่จะถูกกระจายเข้าสู่ Column Strip และ Middle Strip ในขั้นตอนต่อไป")

# ==========================================
# TAB 2: Punching Shear (Detailed)
# ==========================================
with tab2:
    st.subheader("2.1 Punching Shear Check (แรงเฉือนทะลุ)")
    P = data['punching']
    
    col_vis, col_check = st.columns([1, 2])
    
    with col_vis:
        st.markdown(f"**Position: {pos}**")
        # Logic to switch images based on position
        if pos == "Interior":
            img_url = "https://www.researchgate.net/publication/283289066/figure/fig1/AS:614343542255622@1523482650829/Critical-perimeter-b-0-according-to-ACI-318-10.png"
        elif pos == "Edge":
            img_url = "https://ars.els-cdn.com/content/image/1-s2.0-S235201242030046X-gr1.jpg" # Representative
        else:
            img_url = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS_J5_T6pE3QjJ6_4_g2_qg_Ff_X5_H5_X5_Q&s" # Representative
            
        st.image(img_url, caption=f"Critical Section at d/2 ({P['d']*1000/2:.0f} mm)", use_container_width=True)
        st.metric("Critical Perimeter ($b_o$)", f"{P['bo']:.2f} m")

    with col_check:
        st.markdown("##### Step A: Compare $v_c$ Formulas (ACI 318-19)")
        st.write("เปรียบเทียบหน่วยแรงต้านทานทั้ง 3 สมการ เพื่อหาค่าที่น้อยที่สุด (Governing Case):")
        
        # Create Comparison DataFrame
        df_vc = pd.DataFrame({
            'Condition': ['1. Limit (Normal)', '2. Shape (Beta)', '3. Size (Alpha)'],
            'Formula': [r'$0.33\sqrt{f_c}$', r'$0.17(1+\frac{2}{\beta})\sqrt{f_c}$', r'$0.083(2+\frac{\alpha d}{b_o})\sqrt{f_c}$'],
            'Value (MPa)': [P['v1'], P['v2'], P['v3']]
        })
        
        # Display with Highlight
        st.dataframe(
            df_vc.style.apply(highlight_min_row, subset=['Value (MPa)'])
            .format({"Value (MPa)": "{:.2f}"}),
            use_container_width=True,
            hide_index=True
        )
        
        governing_vc = P['vc_mpa']
        st.latex(rf"\therefore v_{{c,allow}} = \mathbf{{{governing_vc:.2f}}} \; \text{{MPa}}")

    st.markdown("---")
    
    st.subheader("2.2 Final Verification")
    
    # Calculate Stresses
    vu_stress = (P['vu'] * 9.80665) / (P['bo'] * 1000 * P['d'] * 1000) # MPa
    phi_vc_stress = 0.75 * governing_vc
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Actual Stress ($v_u$)", f"{vu_stress:.2f} MPa")
    c2.metric("Design Capacity ($\phi v_c$)", f"{phi_vc_stress:.2f} MPa")
    c3.metric("Ratio ($v_u / \phi v_c$)", f"{vu_stress/phi_vc_stress:.2f}", delta_color="inverse")

    if vu_stress <= phi_vc_stress:
        st.success(f"✅ **PASS:** ความหนา {data['h_final']} mm เพียงพอรับแรงเฉือนทะลุ")
    else:
        st.error(f"❌ **FAIL:** หน้าตัดรับแรงไม่ไหว (Ratio {vu_stress/phi_vc_stress:.2f})")
        st.markdown("👉 **คำแนะนำ:** เพิ่มความหนาพื้น, เพิ่ม Drop Panel, หรือใส่เหล็กเสริมรับแรงเฉือน (Shear Studs)")

# ==========================================
# TAB 3: Reinforcement
# ==========================================
with tab3:
    st.subheader("3. Reinforcement Detail (รายละเอียดเหล็กเสริม)")
    
    col_layout, col_table = st.columns([1, 2])
    
    with col_layout:
        st.image("https://theconstructor.org/wp-content/uploads/2017/04/design-strip.jpg", caption="Column Strip vs Middle Strip", use_container_width=True)
        st.info("**Design Criteria:**\n\n* Min Steel: $0.0018bh$\n* Max Spacing: $2h$ or 30 cm")

    with col_table:
        st.write("ตารางสรุปเหล็กเสริม (คำนวณตามปริมาณที่ต้องการเทียบกับขั้นต่ำ):")
        
        rebar_data = []
        for loc, val in data['rebar'].items():
            loc_name = loc.replace("CS", "Column Strip").replace("MS", "Middle Strip").replace("_", " ")
            spec = get_rebar_spec(val, data['max_spacing_cm'])
            rebar_data.append([loc_name, f"{val:.2f}", f"{data['as_min']:.2f}", spec])
            
        df_rebar = pd.DataFrame(rebar_data, columns=["Location", "Req. As (cm²/m)", "Min As (cm²/m)", "Recommended Bar"])
        
        st.table(df_rebar)
        
    st.markdown("---")
    st.caption("Note: Top bars for negative moment supports, Bottom bars for positive moment span.")
