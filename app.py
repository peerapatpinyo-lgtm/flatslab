import streamlit as st
import engine
import report
import drawings

st.set_page_config(page_title="Flat Slab Pro 3.0", layout="wide")

with st.sidebar:
    st.title("🏗️ Design Input")
    lx = st.number_input("Lx (m)", 6.0)
    ly = st.number_input("Ly (m)", 6.0)
    c1 = st.number_input("Col Width (mm)", 400)
    c2 = st.number_input("Col Depth (mm)", 400)
    pos = st.selectbox("Column Position", ["Interior", "Edge", "Corner"])
    
    st.subheader("Materials")
    fc = st.number_input("fc' (ksc)", 240)
    fy = st.number_input("fy (ksc)", 4000)
    
    st.subheader("Loads")
    sdl = st.number_input("SDL (kg/m2)", 150)
    ll = st.number_input("LL (kg/m2)", 300)
    dl_fac = st.number_input("DL Factor", 1.2)
    ll_fac = st.number_input("LL Factor", 1.6)

# Execute Engine
data = engine.run_design_cycle(lx, ly, 150, c1, c2, fc, fy, sdl, ll, 20, pos, dl_fac, ll_fac)

# Layout
st.title("Flat Slab Design Report")
tab1, tab2 = st.tabs(["📄 Calculation Report", "📐 Detail Drawings"])

with tab1:
    report.render_report(data)

with tab2:
    st.pyplot(drawings.draw_section(data['results']['h'], 20, c1, data['inputs']['ln']))
