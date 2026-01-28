import streamlit as st
import engine
import report
import drawings

st.set_page_config(page_title="Flat Slab Construction Design", layout="wide")

# Sidebar
st.sidebar.header("🏗️ Input Parameters")
with st.sidebar:
    lx = st.number_input("Span Lx (m)", 3.0, 15.0, 8.0)
    ly = st.number_input("Span Ly (m)", 3.0, 15.0, 8.0)
    c1 = st.number_input("Col Width c1 (mm)", 200, 2000, 500)
    c2 = st.number_input("Col Depth c2 (mm)", 200, 2000, 500)
    pos = st.selectbox("Position", ["Interior", "Edge", "Corner"])
    st.divider()
    fc = st.number_input("fc' (ksc)", 180, 500, 280)
    fy = st.number_input("fy (ksc)", 2400, 5000, 4000)
    sdl = st.number_input("SDL (kg/m2)", 0, 1000, 150)
    ll = st.number_input("LL (kg/m2)", 0, 3000, 300)
    h_init = st.number_input("Start Thickness (mm)", 100, 600, 200)
    st.divider()
    # Bar Selection
    bar_size = st.selectbox("Rebar Size (Main)", [12, 16, 20, 25], index=1)

# Run Engine
data = engine.run_design_cycle(lx, ly, h_init, c1, c2, fc, fy, sdl, ll, 25, pos, 1.4, 1.7, bar_size)
res = data['results']
bars = data['rebar']

st.title("🛡️ Flat Slab Construction Design")
st.caption("Detailed Calculation with Rebar Spacing & Min/Max Checks")

# Status
status_color = "green" if res['ratio'] <= 1.0 else "red"
st.markdown(f"""
<div style='background-color:#f8f9fa; padding:15px; border-left:6px solid {status_color}; border-radius:5px;'>
    <h3 style='margin:0; color:#333;'>Final Design: h = {res['h']} mm</h3>
    <p style='margin:5px 0'>Shear Ratio: <b>{res['ratio']:.2f}</b> | Main Rebar: <b>DB{bar_size}</b></p>
</div>
<br>
""", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["📄 Calculation Report", "📐 Construction Drawing"])

with tab1:
    report.render_report(data)

with tab2:
    st.markdown("### Typical Section (Column Strip)")
    # Extract CS Top and CS Bot strings for drawing
    top_str = f"DB{bar_size} @ {bars[0]['use_spacing']/100:.2f}m" # CS Top
    bot_str = f"DB{bar_size} @ {bars[1]['use_spacing']/100:.2f}m" # CS Bot
    
    fig = drawings.draw_section(res['h'], 25, c1, res['ln'], res['d_mm'], top_str, bot_str)
    st.pyplot(fig)
