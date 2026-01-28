import streamlit as st
from engine import calculate_detailed_slab

st.set_page_config(page_title="Flat Slab Expert Design", layout="wide")
st.title("🏗️ Professional Flat Slab Design (ACI 318-19)")

# Input Section
with st.sidebar:
    st.header("Slab Parameters")
    pos = st.selectbox("Column Position", ["Interior", "Edge", "Corner"])
    lx = st.number_input("Span Lx (m)", value=6.0)
    ly = st.number_input("Span Ly (m)", value=6.0)
    h_mm = st.number_input("Thickness (mm)", value=200)
    c1 = st.number_input("Col Width c1 (mm)", value=400)
    c2 = st.number_input("Col Depth c2 (mm)", value=400)
    fc = st.number_input("f'c (ksc)", value=280)
    fy = st.number_input("fy (ksc)", value=4000)
    sdl = st.number_input("SDL (kg/m2)", value=150)
    ll = st.number_input("Live Load (kg/m2)", value=300)

res = calculate_detailed_slab(lx, ly, h_mm, c1, c2, fc, fy, sdl, ll, 20, pos)

# Display Output
st.subheader(f"Position: {pos} Column")

# --- Step 1: Punching Shear ---
st.markdown("### 1. การตรวจสอบแรงเฉือนทะลุหัวเสา (Punching Shear)")


st.latex(r"v_c = \min \left[ 0.33\sqrt{f'_c}, 0.17(1+\frac{2}{\beta})\sqrt{f'_c}, 0.083(2+\frac{\alpha_s d}{b_o})\sqrt{f'_c} \right]")

col1, col2 = st.columns(2)
with col1:
    st.write(f"**แรงเฉือนที่เกิดขึ้น ($V_u$):** {res['vu']:,.2f} kg")
    st.write(f"**แรงต้านทานที่ยอมรับได้ ($\phi V_c$):** {res['phi_vc']:,.2f} kg")
with col2:
    if res['ratio'] <= 1.0:
        st.success(f"**สถานะ:** ผ่าน (Ratio: {res['ratio']:.3f})")
    else:
        st.error(f"**สถานะ:** ไม่ผ่าน (Ratio: {res['ratio']:.3f})")
        st.info(f"💡 **คำแนะนำ:** ควรใช้ความหนาพื้นอย่างน้อย **{res['recommended_h']} mm.**")

# --- Step 2: Moment Distribution ---
st.markdown("---")
st.markdown("### 2. การกระจายโมเมนต์ (Moment Distribution)")


cols = st.columns(4)
for i, (k, v) in enumerate(res['moments'].items()):
    cols[i].metric(k.replace("_", " "), f"{v:,.0f} kg-m")

# --- Step 3: Reinforcement ---
st.markdown("---")
st.markdown("### 3. การคำนวณเหล็กเสริม ($A_s$)")
# คำนวณเบื้องต้นสำหรับ Column Strip Neg
m_design = res['moments']['CS_Neg']
# สูตร: As = M / (phi * fy * (d - a/2)) -> simplified
phi_flex = 0.9
as_req = (m_design * 100) / (phi_flex * fy * (res['d'] * 100 * 0.9)) 
st.write(f"เหล็กเสริมที่ต้องการเบื้องต้นใน Column Strip (Top): **{as_req:.2f} cm²/strip**")
