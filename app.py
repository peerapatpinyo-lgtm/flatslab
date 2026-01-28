import streamlit as st
import engine
import report
import drawings

st.set_page_config(page_title="Pro Flat Slab", layout="wide")

st.sidebar.title("🏗️ Design Inputs")
# Input Section
with st.sidebar:
    lx = st.number_input("Span Lx (m)", 5.0, 15.0, 8.0)
    ly = st.number_input("Span Ly (m)", 5.0, 15.0, 8.0)
    c1 = st.number_input("Col Width c1 (mm)", 200, 1000, 500)
    c2 = st.number_input("Col Depth c2 (mm)", 200, 1000, 500)
    pos = st.selectbox("Position", ["Interior", "Edge", "Corner"])
    st.divider()
    fc = st.number_input("fc' (ksc)", 180, 500, 280)
    fy = st.number_input("fy (ksc)", 2400, 5000, 4000)
    sdl = st.number_input("SDL (kg/m2)", 0, 1000, 150)
    ll = st.number_input("LL (kg/m2)", 0, 2000, 300)
    st.divider()
    h_init = st.number_input("Start h (mm)", 100, 500, 200)

# กำหนด Cover ที่นี่ (หรือรับจาก Sidebar ก็ได้)
cover_val = 25 

# Run Engine (ส่ง cover_val เข้าไป)
data = engine.run_design_cycle(lx, ly, h_init, c1, c2, fc, fy, sdl, ll, cover_val, pos, 1.2, 1.6)

# Main Dashboard
st.title("🛡️ Flat Slab Design: Numerical Integrity Edition")

# Summary Banner
res = data['results']
status_color = "green" if res['ratio'] <= 1.0 else "red"
st.markdown(f"""
<div style='background-color:rgba(200,200,200,0.1); padding:15px; border-radius:5px; border-left: 5px solid {status_color};'>
    <h3>Final Thickness: {res['h']} mm</h3>
    <p>Ratio: <b>{res['ratio']:.2f}</b> | Status: <b>{'PASS' if res['ratio'] <= 1.0 else 'FAIL'}</b></p>
</div>
""", unsafe_allow_html=True)

t1, t2 = st.tabs(["📄 Calculation Report", "📐 Detail Drawings"])

with t1:
    report.render_report(data)

with t2:
    # ใช้ .get() เพื่อป้องกัน Error หาก key หายไปในอนาคต
    cover_to_draw = data['inputs'].get('cover', cover_val)
    fig = drawings.draw_section(res['h'], cover_to_draw, c1, res['ln'])
    st.pyplot(fig)
