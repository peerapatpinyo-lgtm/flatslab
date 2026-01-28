import streamlit as st
import engine
import report
import drawings

st.set_page_config(page_title="Pro Flat Slab", layout="wide")

st.sidebar.title("🏗️ Design Inputs")
with st.sidebar:
    lx = st.number_input("Span Lx (m)", 4.0, 15.0, 8.0)
    ly = st.number_input("Span Ly (m)", 4.0, 15.0, 8.0)
    c1 = st.number_input("Col Width c1 (mm)", 200, 1500, 500)
    c2 = st.number_input("Col Depth c2 (mm)", 200, 1500, 500)
    pos = st.selectbox("Position", ["Interior", "Edge", "Corner"])
    st.divider()
    fc = st.number_input("fc' (ksc)", 180, 500, 280)
    fy = st.number_input("fy (ksc)", 2400, 5000, 4000)
    sdl = st.number_input("SDL (kg/m2)", 0, 1000, 150)
    ll = st.number_input("LL (kg/m2)", 0, 3000, 300)
    h_init = st.number_input("Start Thickness (mm)", 100, 500, 200)

# Run Engine
data = engine.run_design_cycle(lx, ly, h_init, c1, c2, fc, fy, sdl, ll, 25, pos, 1.4, 1.7)
res = data['results']

st.title("🛡️ Flat Slab Design: Detailed Calculation")

# Status Banner
status_color = "green" if res['ratio'] <= 1.0 else "red"
st.markdown(f"""
<div style='background-color:rgba(200,200,200,0.2); padding:15px; border-left:6px solid {status_color}; border-radius:5px;'>
    <h3 style='margin:0'>Final Thickness: {res['h']} mm</h3>
    <p style='margin:5px 0'>Check Ratio: <b>{res['ratio']:.2f}</b> ({res['reason']})</p>
</div>
<br>
""", unsafe_allow_html=True)

t1, t2 = st.tabs(["📄 Calculation Report", "📐 Drawings"])

with t1:
    report.render_report(data)

with t2:
    fig = drawings.draw_section(res['h'], 25, c1, res['ln'])
    st.pyplot(fig)
