import streamlit as st
from engine import calculate_detailed_slab

st.set_page_config(page_title="Professional Slab Design", layout="wide")

st.title("🏗️ Structural Design: Flat Slab Engine")
st.markdown("---")

# UI Layout
col_in, col_out = st.columns([1, 2])

with col_in:
    st.header("Input Data")
    pos = st.selectbox("Column Position", ["Interior", "Edge", "Corner"])
    lx = st.number_input("Span Lx (m)", 6.0)
    ly = st.number_input("Span Ly (m)", 6.0)
    h_init = st.number_input("Initial h (mm)", 200)
    c1 = st.number_input("Column c1 (mm)", 400)
    c2 = st.number_input("Column c2 (mm)", 400)
    fc = st.number_input("f'c (ksc)", 280)
    fy = st.number_input("fy (ksc)", 4000)

# Calculation
res = calculate_detailed_slab(lx, ly, h_init, c1, c2, fc, fy, 150, 300, 20, pos)

with col_out:
    if res['status'] != "Success":
        st.error(f"Design Alert: {res['status']}")
    
    st.subheader("1. Geometric & DDM Check")
    st.info(res['ddm_warning'])
    st.write(f"Final Slab Thickness: **{res['h_final']} mm**")
    
    st.subheader("2. Punching Shear Result")
    
    st.write(f"Critical Perimeter ($b_o$): {res['bo']:.2f} m")
    st.write(f"Ultimate Shear ($V_u$): {res['vu']:,.2f} kg")
    st.write(f"Design Strength ($\phi V_c$): {res['phi_vc']:,.2f} kg")
    st.progress(min(float(res['ratio']), 1.0))

    st.subheader("3. Reinforcement (per meter width)")
    st.write("Calculated based on $A_{s,req}$ vs $A_{s,min}$")
    
    # Table data
    rebar_data = []
    for loc, val in res['rebar'].items():
        rebar_data.append({
            "Location": loc,
            "As Required (cm2/m)": round(val['As_req'], 2),
            "As Min (cm2/m)": round(val['As_min'], 2)
        })
    st.table(rebar_data)
