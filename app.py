import streamlit as st
import engine
import report
import drawings

st.set_page_config(page_title="Pro Flat Slab Design", layout="wide")

# --- Sidebar Inputs ---
st.sidebar.header("🏗️ Project Inputs")
with st.sidebar:
    lx = st.number_input("Span Lx (m)", 3.0, 15.0, 8.0)
    ly = st.number_input("Span Ly (m)", 3.0, 15.0, 8.0)
    c1 = st.number_input("Col Width c1 (mm)", 200, 2000, 500)
    c2 = st.number_input("Col Depth c2 (mm)", 200, 2000, 500)
    pos = st.selectbox("Column Position", ["Interior", "Edge", "Corner"])
    st.divider()
    fc = st.number_input("fc' (ksc)", 180, 500, 280)
    fy = st.number_input("fy (ksc)", 2400, 5000, 4000)
    sdl = st.number_input("SDL (kg/m2)", 0, 1000, 150)
    ll = st.number_input("LL (kg/m2)", 0, 3000, 300)
    h_init = st.number_input("Initial Thickness (mm)", 100, 600, 200)

# --- Execution ---
data = engine.run_design_cycle(lx, ly, h_init, c1, c2, fc, fy, sdl, ll, 25, pos, 1.4, 1.7)
res = data['results']

st.title("🛡️ Professional Flat Slab Design")
st.caption("Detailed breakdown with Numerical Substitution & Unit Traceability")

# --- Status Box ---
status_color = "green" if res['ratio'] <= 1.0 else "red"
st.markdown(f"""
<div style='background-color:#f0f2f6; padding:15px; border-left:6px solid {status_color}; border-radius:5px;'>
    <h3 style='margin:0; color: #31333F;'>Final Design Thickness: {res['h']} mm</h3>
    <p style='margin:5px 0'>Shear Ratio: <b>{res['ratio']:.2f}</b> | Status: <b>{'SAFE' if res['ratio']<=1.0 else 'FAIL'}</b></p>
</div>
<br>
""", unsafe_allow_html=True)

# --- Tabs ---
tab1, tab2 = st.tabs(["📄 Detailed Report", "📐 Fabrication Drawings"])

with tab1:
    report.render_report(data)

with tab2:
    st.markdown("### Section View at Column Strip")
    fig = drawings.draw_section(res['h'], 25, c1, res['ln'], res['d_mm'])
    st.pyplot(fig)
