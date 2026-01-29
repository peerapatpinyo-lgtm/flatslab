import streamlit as st
import engine
import report
import drawings

st.set_page_config(page_title="Interactive Flat Slab", layout="wide")

st.sidebar.header("🏗️ 1. Global Parameters")
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
    h_init = st.number_input("Start h (mm)", 100, 600, 200)

st.title("🛡️ Interactive Flat Slab Design")

# --- Phase 1: Structural Analysis ---
# We run this first to get h and moments, which helps guide the user
base_data = engine.analyze_structure(
    lx, ly, h_init, c1, c2, fc, fy, sdl, ll, 25, pos, 1.4, 1.7, 20
)
res = base_data['results']

# Show Status
status_color = "green" if res['ratio'] <= 1.0 else "red"
st.markdown(f"""
<div style='background-color:#f0f2f6; padding:15px; border-left:6px solid {status_color}; border-radius:5px;'>
    <h3 style='margin:0;'>Step 1 Analysis: h = {res['h']} mm</h3>
    <p style='margin:0;'>Shear Ratio: <b>{res['ratio']:.2f}</b></p>
</div>
""", unsafe_allow_html=True)

# --- Phase 2: User Reinforcement Selection ---
st.markdown("### 2. Reinforcement Selection (Manual Control)")
col_top, col_bot = st.columns(2)

with col_top:
    st.subheader("Top Bars (Column Strip)")
    top_db = st.selectbox("Top Bar Size", [10, 12, 16, 20, 25], index=2, key="top_db")
    top_space = st.slider("Top Spacing (mm)", 50, 350, 150, 10, key="top_sp")
    st.caption(f"Selected: DB{top_db} @ {top_space} mm")

with col_bot:
    st.subheader("Bottom Bars (Column Strip)")
    bot_db = st.selectbox("Bottom Bar Size", [10, 12, 16, 20, 25], index=1, key="bot_db")
    bot_space = st.slider("Bottom Spacing (mm)", 50, 350, 200, 10, key="bot_sp")
    st.caption(f"Selected: DB{bot_db} @ {bot_space} mm")

# --- Phase 3: Verification & Reporting ---
verify_data = engine.verify_reinforcement(base_data, top_db, top_space, bot_db, bot_space)

tab1, tab2 = st.tabs(["📄 Detailed Check", "📐 Construction Drawing"])

with tab1:
    report.render_report(base_data, verify_data)

with tab2:
    st.markdown("### Interactive Section View")
    top_lbl = f"DB{top_db} @ {top_space} mm"
    bot_lbl = f"DB{bot_db} @ {bot_space} mm"
    
    fig = drawings.draw_section(res['h'], 25, c1, res['ln'], res['d_mm'], top_lbl, bot_lbl)
    st.pyplot(fig)
