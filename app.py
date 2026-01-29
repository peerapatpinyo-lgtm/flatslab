import streamlit as st
import engine
import report
import drawings

st.set_page_config(page_title="Pro Flat Slab EFM/DDM", layout="wide", page_icon="🏗️")

st.title("🛡️ Professional Flat Slab Design System")
st.caption("Design Method: ACI 318-19 | Method: Equivalent Frame (EFM) & Direct Design (DDM)")

# --- 1. Input Section (Logical Grouping) ---
st.sidebar.markdown("### 🛠️ Design Controls")
st.sidebar.info("Adjust parameters in the main tabs.")

input_tab1, input_tab2, input_tab3 = st.tabs([
    "🏗️ 1. Geometry & Materials", 
    "⚖️ 2. Loading", 
    "⚙️ 3. Analysis Method"
])

with input_tab1:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("##### Slab Geometry")
        lx = st.number_input("Span Lx (m)", 3.0, 15.0, 8.0, step=0.1)
        ly = st.number_input("Span Ly (m)", 3.0, 15.0, 8.0, step=0.1)
        h_init = st.number_input("Initial Thickness (mm)", 100, 600, 200, step=10)
    
    with col2:
        st.markdown("##### Column & Story")
        c1 = st.number_input("Col Width c1 (Lx dir) [mm]", 200, 2000, 500)
        c2 = st.number_input("Col Depth c2 (Ly dir) [mm]", 200, 2000, 500)
        lc_upper = st.number_input("Upper Story Height (m)", 2.0, 8.0, 3.0)
        lc_lower = st.number_input("Lower Story Height (m)", 2.0, 8.0, 3.0)
        
    with col3:
        st.markdown("##### Materials")
        fc = st.number_input("fc' (ksc)", 180, 500, 280)
        fy = st.number_input("fy (ksc)", 2400, 5000, 4000)
        cover = st.number_input("Cover (mm)", 15, 50, 25)

with input_tab2:
    col_l1, col_l2 = st.columns(2)
    with col_l1:
        sdl = st.number_input("Superimposed Dead Load (SDL) [kg/m2]", 0, 1000, 150)
        ll = st.number_input("Live Load (LL) [kg/m2]", 0, 3000, 300)
    with col_l2:
        dl_fac = st.number_input("DL Factor", 1.0, 1.6, 1.4)
        ll_fac = st.number_input("LL Factor", 1.0, 2.0, 1.7)

with input_tab3:
    col_a1, col_a2 = st.columns(2)
    with col_a1:
        method = st.radio("Calculation Method", ["DDM (Direct Design Method)", "EFM (Equivalent Frame Method)"])
        continuity = st.selectbox("Span Continuity", 
                                 ["Interior Span", "End Span (Integral w/ Beam)", "End Span (Slab Only)"])
    with col_a2:
        pos = st.selectbox("Column Position", ["Interior", "Edge", "Corner"])
        st.caption("Note: EFM calculates stiffness based on slab-beam and columns.")

# --- 2. Live Warnings & Pre-Check ---
aspect_ratio = max(lx, ly) / min(lx, ly)
if aspect_ratio > 2.0:
    st.warning(f"⚠️ Warning: Aspect Ratio L/W = {aspect_ratio:.2f} > 2.0. ACI recommends using **EFM** instead of DDM.")
    if method.startswith("DDM"):
        st.error("🛑 DDM is not suitable for Aspect Ratio > 2.0. Please switch to EFM.")

# --- 3. Run Analysis ---
base_data = engine.analyze_structure(
    lx, ly, h_init, c1, c2, lc_upper, lc_lower, 
    fc, fy, sdl, ll, cover, pos, dl_fac, ll_fac, 
    20, continuity, method
)
res = base_data['results']
efm = base_data['efm']

# --- 4. Visual Feedback Dashboard ---
st.markdown("---")
dash_col1, dash_col2, dash_col3, dash_col4 = st.columns(4)

with dash_col1:
    st.metric("Design Thickness", f"{res['h']} mm", f"Min Req: {res['h_min']:.0f} mm")
    
with dash_col2:
    shear_color = "normal" if res['ratio'] <= 1.0 else "inverse"
    status_icon = "✅" if res['ratio'] <= 1.0 else "❌"
    st.metric("Shear Status", f"{status_icon} Ratio {res['ratio']:.2f}", f"Vu: {res['vu_kg']/1000:.1f} T")

with dash_col3:
    # Alpha EC (Stiffness Ratio)
    alpha_ec = efm.get('alpha_ec', 0)
    st.metric("Stiffness Ratio (α_ec)", f"{alpha_ec:.2f}", "EFM Indicator")

with dash_col4:
    moment_val = res['mo'] if "DDM" in method else efm['m_neg_int']
    st.metric("Design Moment (Neg)", f"{moment_val/1000:.1f} kNm", method.split()[0])

st.markdown("---")

# --- 5. Reinforcement & Output ---
st.subheader("🛠️ Reinforcement Selection")
r_col1, r_col2 = st.columns(2)
with r_col1:
    top_db = st.selectbox("Top Bar Size", [10, 12, 16, 20, 25], index=2)
    top_sp = st.number_input("Top Spacing (mm)", 50, 400, 150, 10)
with r_col2:
    bot_db = st.selectbox("Bottom Bar Size", [10, 12, 16, 20, 25], index=1)
    bot_sp = st.number_input("Bottom Spacing (mm)", 50, 400, 200, 10)

verify_data = engine.verify_reinforcement(base_data, top_db, top_sp, bot_db, bot_sp)

out_tab1, out_tab2 = st.tabs(["📄 Engineering Report (One-Page)", "📐 Construction Detail"])

with out_tab1:
    report.render_report(base_data, verify_data)

with out_tab2:
    top_lbl = f"DB{top_db} @ {top_sp} mm"
    bot_lbl = f"DB{bot_db} @ {bot_sp} mm"
    # Use computed Ln and d
    fig = drawings.draw_section(res['h'], cover, c1, res['ln'], res['d_mm'], top_lbl, bot_lbl)
    st.pyplot(fig)
