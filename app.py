import streamlit as st
from engine import calculate_detailed_slab
import math

st.set_page_config(page_title="Slab Design Report", layout="wide")

def get_rebar_spec(as_req):
    # เลือก DB12 เป็นหลัก ถ้าห่างเกินไปให้ใช้ DB16
    bar_size = 12
    area = (math.pi * (1.2**2)) / 4
    spacing = min(area / as_req, 0.30) # Max spacing 30cm
    if spacing < 0.10: # ถ้าชิดเกิน 10cm ให้เปลี่ยนเป็น DB16
        bar_size = 16
        area = (math.pi * (1.6**2)) / 4
        spacing = min(area / as_req, 0.30)
    return f"DB{bar_size} @ {spacing:.2f} m"

st.title("📑 Structural Calculation Report: Flat Slab")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("Input Design Criteria")
    pos = st.selectbox("Column Position", ["Interior", "Edge", "Corner"])
    lx = st.number_input("Span Lx (m)", 6.0)
    ly = st.number_input("Span Ly (m)", 6.0)
    h_init = st.number_input("Initial Thickness (mm)", 200)
    fc = st.number_input("Concrete Strength f'c (ksc)", 280)
    fy = st.number_input("Steel Strength fy (ksc)", 4000)

data = calculate_detailed_slab(lx, ly, h_init, 400, 400, fc, fy, 150, 300, 20, pos)

# --- Manual Calculation Style ---
with st.expander("📝 STEP 1: LOAD COMBINATIONS", expanded=True):
    st.write("น้ำหนักบรรทุกตามมาตรฐาน ACI 318:")
    st.latex(rf"W_{{u}} = 1.2(DL + SDL) + 1.6(LL)")
    st.write(f"Self-weight ($2400 \times {data['h_final']/1000}$ m) = {data['loading']['sw']:.0f} $kg/m^2$")
    st.latex(rf"q_u = 1.2({data['loading']['sw']:.0f} + 150) + 1.6(300) = {data['loading']['qu']:.2f} \text{{ kg/m}}^2")

with st.expander("📝 STEP 2: TOTAL STATIC MOMENT ($M_o$)"):
    st.write("วิเคราะห์ด้วยวิธี Direct Design Method (DDM):")
    st.latex(rf"L_n = L_x - C_1 = {data['geo']['ln']:.2f} \text{{ m}}")
    st.latex(rf"M_o = \frac{{q_u \cdot L_y \cdot L_n^2}}{{8}}")
    st.latex(rf"M_o = \frac{{{data['loading']['qu']:.2f} \cdot {ly} \cdot {data['geo']['ln']:.2f}^2}}{{8}} = {data['mo']:,.2f} \text{{ kg-m}}")

with st.expander("📝 STEP 3: PUNCHING SHEAR DETAILED CHECK"):
    p = data['punching']
    st.write(f"**ตำแหน่งเสา:** {pos} | **$\beta$:** {data['geo']['beta']:.2f}")
    
    st.write("เปรียบเทียบหน่วยแรงเฉือนคอนกรีต ($v_c$) 3 เงื่อนไข (MPa):")
    cols = st.columns(3)
    cols[0].metric("Formula 1 (Limit)", f"{p['v1']:.2f}")
    cols[1].metric("Formula 2 (Beta)", f"{p['v2']:.2f}")
    cols[2].metric("Formula 3 (Alpha)", f"{p['v3']:.2f}")
    
    st.latex(rf"v_{{c, governing}} = {p['vc_mpa']:.2f} \text{{ MPa}}")
    
    v_u_stress = (p['vu'] * 9.81) / (p['bo'] * 1000 * p['d'] * 1000)
    st.write(f"หน่วยแรงเฉือนที่เกิดขึ้น $v_u = V_u / (b_o \cdot d) = $ **{v_u_stress:.2f} MPa**")
    
    if v_u_stress <= (0.75 * p['vc_mpa']):
        st.success(f"PASS: $v_u \le \phi v_c$ ({v_u_stress:.2f} $\le$ {0.75 * p['vc_mpa']:.2f})")
    else:
        st.error("FAIL: Shear Stress exceeds capacity")

# --- Final Table ---
st.subheader("📊 Summary of Reinforcement")


summary_data = []
for loc, as_val in data['rebar'].items():
    summary_data.append({
        "Location": loc.replace("_", " "),
        "Required $A_s$ ($cm^2/m$)": f"{as_val:.2f}",
        "Min $A_s$ ($cm^2/m$)": f"{data['as_min']:.2f}",
        "Recommended Spacing": get_rebar_spec(as_val)
    })

st.table(summary_data)
