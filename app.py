import streamlit as st
import engine
import report
import drawings

st.set_page_config(page_title="Pro Flat Slab Design", layout="wide")

st.sidebar.header("🏗️ Pro Design Inputs")
with st.sidebar:
    st.subheader("1. Geometry")
    lx = st.number_input("Span Lx (m)", 3.0, 15.0, 8.0)
    ly = st.number_input("Span Ly (m)", 3.0, 15.0, 8.0)
    continuity = st.selectbox("Span Continuity", 
                             ["Interior Span", "End Span (Integral w/ Beam)", "End Span (Slab Only)"])
    
    st.subheader("2. Columns & Story")
    c1 = st.number_input("Col Width c1 (mm)", 200, 2000, 500)
    c2 = st.number_input("Col Depth c2 (mm)", 200, 2000, 500)
    lc_upper = st.number_input("Upper Story Height (m)", 2.0, 6.0, 3.0)
    lc_lower = st.number_input("Lower Story Height (m)", 2.0, 6.0, 3.0)
    pos = st.selectbox("Position", ["Interior", "Edge", "Corner"])
    
    st.subheader("3. Material & Load")
    fc = st.number_input("fc' (ksc)", 180, 500, 280)
    fy = st.number_input("fy (ksc)", 2400, 5000, 4000)
    sdl = st.number_input("SDL (kg/m2)", 0, 1000, 150)
    ll = st.number_input("LL (kg/m2)", 0, 3000, 300)
    h_init = st.number_input("Start h (mm)", 100, 600, 200)

st.title("🛡️ Professional Flat Slab Design System")
st.caption(f"Design Code: ACI 318-19 | Method: EFM & DDM | Continuity: {continuity}")

# --- Phase 1: Structural Analysis ---
base_data = engine.analyze_structure(
    lx, ly, h_init, c1, c2, lc_upper, lc_lower, fc, fy, sdl, ll, 25, pos, 1.4, 1.7, 20, continuity
)
res = base_data['results']

# Quick Dashboard
c_dash1, c_dash2, c_dash3 = st.columns(3)
with c_dash1:
    status_color = "green" if res['ratio'] <= 1.0 else "red"
    st.markdown(f"**Thickness:** {res['h']} mm")
    st.markdown(f"**Shear Ratio:** :{status_color}[{res['ratio']:.2f}]")
with c_dash2:
    st.markdown(f"**Clear Span X:** {res['ln_x']:.2f} m")
    st.markdown(f"**Clear Span Y:** {res['ln_y']:.2f} m")
with c_dash3:
    st.markdown(f"**Static Moment:** {res['mo']:,.0f} kg-m")
    
# Show EFM Quick Data
with st.expander("Show EFM Stiffness Data"):
    col_k1, col_k2, col_k3 = st.columns(3)
    efm = base_data['efm']
    col_k1.metric("K_slab", f"{efm['Ks']:.2e}")
    col_k2.metric("K_ec", f"{efm['Kec']:.2e}")
    col_k3.metric("DF (Ext)", f"{efm['df_ext_slab']:.3f}")

st.divider()

# --- Phase 2: User Reinforcement Selection ---
st.markdown("### 🛠️ Reinforcement Detailing")
col_top, col_bot = st.columns(2)

with col_top:
    st.subheader("Top Bars (Support)")
    top_db = st.selectbox("Size", [10, 12, 16, 20, 25], index=2, key="top_db")
    top_space = st.number_input("Spacing (mm)", 50, 450, 150, 10, key="top_sp")

with col_bot:
    st.subheader("Bottom Bars (Mid-span)")
    bot_db = st.selectbox("Size", [10, 12, 16, 20, 25], index=1, key="bot_db")
    bot_space = st.number_input("Spacing (mm)", 50, 450, 200, 10, key="bot_sp")

# --- Phase 3: Verification & Reporting ---
verify_data = engine.verify_reinforcement(base_data, top_db, top_space, bot_db, bot_space)

tab1, tab2 = st.tabs(["📄 Engineering Report", "📐 Construction Detail"])

with tab1:
    report.render_report(base_data, verify_data)

with tab2:
    top_lbl = f"DB{top_db} @ {top_space} mm"
    bot_lbl = f"DB{bot_db} @ {bot_space} mm"
    fig = drawings.draw_section(res['h'], 25, c1, res['ln'], res['d_mm'], top_lbl, bot_lbl)
    st.pyplot(fig)
