import streamlit as st
from engine import calculate_slab_logic

st.set_page_config(page_title="Detailed Flat Slab Design", layout="wide")

st.title("📝 Flat Slab Design & Step-by-Step Calculation")

# --- Sidebar Inputs ---
with st.sidebar:
    st.header("Input Parameters")
    lx = st.number_input("Span Lx (m)", value=6.0)
    ly = st.number_input("Span Ly (m)", value=6.0)
    h_mm = st.number_input("Thickness h (mm)", value=200)
    c_w_mm = st.number_input("Column Width (mm)", value=400)
    c_d_mm = st.number_input("Column Depth (mm)", value=400)
    fc = st.number_input("f'c (ksc)", value=280)
    fy = st.number_input("fy (ksc)", value=4000)
    sdl = st.number_input("SDL (kg/m2)", value=150)
    ll = st.number_input("Live Load (kg/m2)", value=300)
    cover_mm = st.number_input("Cover (mm)", value=20)

# ประมวลผล
res = calculate_slab_logic(lx, ly, h_mm, c_w_mm, c_d_mm, fc, fy, sdl, ll, cover_mm)

# --- Display Section ---
tab1, tab2 = st.tabs(["📊 Summary Results", "📖 Show Calculation Steps"])

with tab1:
    st.subheader("Result Overview")
    col1, col2, col3 = st.columns(3)
    col1.metric("Ultimate Load ($q_u$)", f"{res['qu']:.2f} kg/m²")
    col2.metric("Static Moment ($M_o$)", f"{res['mo']:.2f} kg-m")
    col3.metric("Punching Ratio", f"{res['ratio']:.3f}", delta_color="inverse")

with tab2:
    st.header("Step-by-Step Calculation (Direct Design Method)")
    
    st.markdown("### Step 1: Load Analysis")
    st.write(f"น้ำหนักตัวพื้นเอง (Self-weight) = $h \\times 2400$ = ${h_mm/1000} \\times 2400$ = **{res['sw']:.2f}** kg/m²")
    st.latex(f"q_u = 1.2(DL + SDL) + 1.6(LL) = 1.2({res['sw']:.0f} + {sdl}) + 1.6({ll}) = {res['qu']:.2f} \\text{{ kg/m}}^2")

    st.markdown("---")
    st.markdown("### Step 2: Total Static Moment ($M_o$)")
    st.write(f"ระยะ Clear Span ($l_n$) = $l_x - c_{{width}}$ = ${lx} - {c_w_mm/1000}$ = **{res['ln']:.2f}** m")
    st.latex(f"M_o = \\frac{{q_u \\cdot L_y \\cdot L_n^2}}{{8}} = \\frac{{{res['qu']:.2f} \\cdot {ly} \\cdot {res['ln']:.2f}^2}}{{8}} = {res['mo']:.2f} \\text{{ kg-m}}")

    st.markdown("---")
    st.markdown("### Step 3: Punching Shear Check")
    st.write(f"Effective depth ($d$) = **{res['d']:.3f}** m")
    st.write(f"เส้นรอบรูปวิกฤต ($b_o$) ที่ระยะ $d/2$ จากขอบเสา = **{res['bo']:.2f}** m")
    
    st.latex(f"V_u = q_u \\times [ (L_x \\cdot L_y) - (c_1+d)(c_2+d) ] = {res['vu']:.2f} \\text{{ kg}}")
    st.latex(f"\\phi V_c = 0.75 \\times 1.1 \\sqrt{{f'_c}} \\cdot b_o \\cdot d")
    st.write(f"หน่วยแรงต้านทานที่ยอมรับได้ ($\\phi V_c$) = **{res['phi_vc']:.2f}** kg")
    
    if res['ratio'] < 1:
        st.success(f"**สรุป:** $V_u < \\phi V_c$ (Ratio: {res['ratio']:.3f}) → **ความหนาพื้นเพียงพอ**")
    else:
        st.error(f"**สรุป:** $V_u > \\phi V_c$ (Ratio: {res['ratio']:.3f}) → **ต้องเพิ่มความหนาพื้นหรือใส่ Drop Panel**")
