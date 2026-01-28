import streamlit as st
import engine
import report
import drawings

st.set_page_config(page_title="Flat Slab Design Check", layout="wide")

st.sidebar.header("🏗️ Input Parameters")
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
    h_start = st.number_input("Initial Thickness (mm)", 100, 500, 200)

# Run Engine
data = engine.run_design_cycle(lx, ly, h_start, c1, c2, fc, fy, sdl, ll, 25, pos, 1.4, 1.7)
res = data['results']

st.title("🛡️ Flat Slab Design: Verified Calculation")

# Tabs
tab1, tab2 = st.tabs(["📄 Detailed Calculation", "📐 Section Drawing"])

with tab1:
    report.render_report(data)

with tab2:
    st.pyplot(drawings.draw_section(res['h'], 25, c1, res['ln']))
