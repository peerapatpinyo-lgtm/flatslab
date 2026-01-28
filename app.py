import streamlit as st
import math
from engine import calculate_detailed_slab

st.set_page_config(page_title="Professional Slab Design", layout="wide")

def get_rebar_spec(as_req, max_spacing_cm):
    # คำนวณหา Spacing สำหรับ DB12 และ DB16
    area_db12 = (math.pi * 1.2**2) / 4
    area_db16 = (math.pi * 1.6**2) / 4
    
    # ลอง DB12 ก่อน
    s12 = (area_db12 * 100) / as_req
    # ถ้า Spacing ของ DB12 น้อยกว่า 10 cm ให้ขยับไปใช้ DB16
    if s12 < 10:
        s16 = (area_db16 * 100) / as_req
        spacing = min(s16, max_spacing_cm)
        return f"DB16 @ {spacing:.2f} cm"
    else:
        spacing = min(s12, max_spacing_cm)
        return f"DB12 @ {spacing:.2f} cm"

st.title("🏗️ Structural Report: Flat Slab ACI 318-19")

# --- Sidebar Inputs ---
with st.sidebar:
    st.header("1. Input Parameters")
    pos = st.selectbox("Column Position", ["Interior", "Edge", "Corner"])
    lx = st.number_input("Span Lx (m)", 6.0)
    ly = st.number_input("Span Ly (m)", 6.0)
    h_init = st.number_input("Thickness (mm)", 200)
    st.markdown("---")
    st.header("2. Loading & Material")
    sdl = st.number_input("SDL (kg/m2)", 150)
    ll = st.number_input("Live Load (kg/m2)", 300)
    fc = st.number_input("f'c (ksc)", 280)
    fy = st.number_input("fy (ksc)", 4000)

data = calculate_detailed_slab(lx, ly, h_init, 400, 400, fc, fy, sdl, ll, 20, pos)

# --- Warning & Error Display ---
if data['h_warning']:
    st.warning(data['h_warning'])

# --- Reports Section ---
tab1, tab2 = st.tabs(["Calculation Steps", "Final Specification"])

with tab1:
    st.subheader("Manual Calculation Verification")
    
    with st.expander("Step 1: Factored Load (qu)"):
        st.latex(rf"q_u = 1.2(DL + {sdl}) + 1.6({ll}) = {data['loading']['qu']:.2f} \text{{ kg/m}}^2")
    
    with st.expander("Step 2: Static Moment (Mo)"):
        st.latex(rf"M_o = \frac{{{data['loading']['qu']:.2f} \cdot {ly} \cdot {data['geo']['ln']:.2f}^2}}{{8}} = {data['mo']:,.2f} \text{{ kg-m}}")

    with st.expander("Step 3: Punching Shear Stress"):
        p = data['punching']
        v_u_stress = (p['vu'] * 9.81) / (p['bo'] * 1000 * p['d'] * 1000)
        st.write(f"Governing $v_c$: {p['vc_mpa']:.2f} MPa")
        st.write(f"Actual $v_u$: {v_u_stress:.2f} MPa")
        st.progress(min(float(v_u_stress / (0.75 * p['vc_mpa'])), 1.0))

with tab2:
    st.subheader("Summary Table & Construction Data")
    
    # Image for Reinforcement Layout
    
    
    results = []
    for loc, as_val in data['rebar'].items():
        results.append({
            "Position": loc.replace("_", " "),
            "Required As (cm2/m)": f"{as_val:.2f}",
            "Min As (cm2/m)": f"{data['as_min']:.2f}",
            "Rebar Spec": get_rebar_spec(as_val, data['max_spacing_cm'])
        })
    
    st.table(results)
    
    st.info(f"**Engineering Note:** Max spacing limited to {data['max_spacing_cm']:.1f} cm (min of 30cm or 2h)")
