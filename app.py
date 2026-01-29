import streamlit as st
import engine
import report
import drawings

st.set_page_config(page_title="Pro Slab Design ACI318", layout="wide", page_icon="🏗️")

st.title("🛡️ Professional Flat Slab Design System")
st.caption("ACI 318-19 Compliant | Equivalent Frame Method (EFM) | Automated Detailing")

# --- Sidebar Controls ---
st.sidebar.header("⚙️ Design Configuration")
use_cracked = st.sidebar.checkbox("Consider Cracked Section", value=True, help="Use 0.25Ig for Slab, 0.70Ig for Col")
include_edge_beam = st.sidebar.checkbox("Include Edge Beam", value=False)
eb_h, eb_w = 0, 0
if include_edge_beam:
    st.sidebar.markdown("---")
    eb_h = st.sidebar.number_input("Edge Beam Depth (mm)", 300, 1000, 500)
    eb_w = st.sidebar.number_input("Edge Beam Width (mm)", 200, 800, 300)

# --- Main Inputs ---
tab_geo, tab_load, tab_method = st.tabs(["🏗️ Geometry", "⚖️ Loading", "⚙️ Analysis"])

with tab_geo:
    c1, c2, c3 = st.columns(3)
    lx = c1.number_input("Span Lx (m)", 3.0, 15.0, 8.0, step=0.1)
    ly = c2.number_input("Span Ly (m)", 3.0, 15.0, 8.0, step=0.1)
    h_init = c3.number_input("Initial h (mm)", 100, 500, 200, step=10)
    
    c4, c5, c6 = st.columns(3)
    col_w = c4.number_input("Col Width c1 (mm)", 200, 1500, 500)
    col_d = c5.number_input("Col Depth c2 (mm)", 200, 1500, 500)
    lc_h = c6.number_input("Story Height (m)", 2.5, 6.0, 3.0)

with tab_load:
    l1, l2 = st.columns(2)
    sdl = l1.number_input("SDL (kg/m2)", 0, 1000, 150)
    ll = l2.number_input("Live Load (kg/m2)", 0, 2000, 300)
    
    m1, m2 = st.columns(2)
    fc = m1.number_input("fc' (ksc)", 180, 500, 280)
    fy = m2.number_input("fy (ksc)", 2400, 5000, 4000)

with tab_method:
    method = st.radio("Calculation Method", ["EFM (Equivalent Frame)", "DDM (Direct Design)"])
    continuity = st.selectbox("Span Continuity", ["Interior Span", "End Span (Slab Only)", "End Span (Integral Beam)"])
    pos = st.selectbox("Column Position (Shear)", ["Interior", "Edge", "Corner"])

# --- Analysis Execution ---
base_data = engine.analyze_structure(
    lx, ly, h_init, col_w, col_d, lc_h, lc_h, 
    fc, fy, sdl, ll, 25, pos, 1.4, 1.7, 
    20, continuity, method, use_cracked, eb_h, eb_w
)

# --- Results Section ---
st.markdown("---")
st.subheader("🛠️ Reinforcement Selection")

r_col1, r_col2 = st.columns(2)
with r_col1:
    top_db = st.selectbox("Top Bar Size", [12, 16, 20, 25], index=1)
    top_sp = st.slider("Top Spacing (mm)", 50, 450, 200, 25)
with r_col2:
    bot_db = st.selectbox("Bot Bar Size", [12, 16, 20, 25], index=0)
    bot_sp = st.slider("Bot Spacing (mm)", 50, 450, 250, 25)

verify_data = engine.verify_reinforcement(base_data, top_db, top_sp, bot_db, bot_sp)

# --- Reporting Tabs ---
out_tab1, out_tab2 = st.tabs(["📄 Calculation Report", "📐 Detailing View"])

with out_tab1:
    report.render_report(base_data, verify_data)

with out_tab2:
    res = base_data['results']
    st.info("Visual representation of reinforcement cut-offs and slab geometry.")
    fig = drawings.draw_section(
        res['h'], 25, col_w/1000.0, res['ln'], res['d_mm'], 
        f"DB{top_db}@{top_sp}", f"DB{bot_db}@{bot_sp}"
    )
    st.pyplot(fig)
