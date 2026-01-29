import streamlit as st
import engine
import report

st.set_page_config(page_title="Pro Flat Slab Design", layout="wide", page_icon="🏗️")

# --- ONE-STOP CONTROL SIDEBAR ---
with st.sidebar:
    st.title("🏗️ Design Controls")
    
    with st.expander("1. Geometry & Section", expanded=True):
        col1, col2 = st.columns(2)
        lx = col1.number_input("Lx (m)", 3.0, 15.0, 8.0, step=0.1)
        ly = col2.number_input("Ly (m)", 3.0, 15.0, 8.0, step=0.1)
        h_user = st.number_input("Slab Thickness (mm)", 100, 500, 200, step=10, help="User defined thickness")
        
        c1 = st.number_input("Col Width (mm)", 200, 1500, 500)
        c2 = st.number_input("Col Depth (mm)", 200, 1500, 500)
        lc_h = st.number_input("Story Height (m)", 2.5, 6.0, 3.0)

    with st.expander("2. Loads & Materials", expanded=False):
        sdl = st.number_input("SDL (kg/m²)", 0, 1000, 150)
        ll = st.number_input("LL (kg/m²)", 0, 2000, 300)
        fc = st.number_input("fc' (ksc)", 180, 500, 280)
        fy = st.number_input("fy (ksc)", 2400, 5000, 4000)

    with st.expander("3. Reinforcement (User Selection)", expanded=True):
        st.info("Select rebar to verify capacity")
        st.markdown("**Top Bars (Negative Moment)**")
        t_c1, t_c2 = st.columns(2)
        top_db = t_c1.selectbox("Top DB", [10, 12, 16, 20, 25], index=1)
        top_sp = t_c2.number_input("Top @ (mm)", 50, 400, 200, step=25)
        
        st.markdown("**Bottom Bars (Positive Moment)**")
        b_c1, b_c2 = st.columns(2)
        bot_db = b_c1.selectbox("Bot DB", [10, 12, 16, 20, 25], index=1)
        bot_sp = b_c2.number_input("Bot @ (mm)", 50, 400, 250, step=25)

    with st.expander("4. Advanced Settings", expanded=False):
        method = st.radio("Method", ["EFM", "DDM"])
        pos = st.selectbox("Position", ["Interior", "Edge", "Corner"])
        continuity = st.selectbox("Continuity", ["Interior Span", "End Span (Slab Only)", "End Span (Integral Beam)"])
        use_cracked = st.checkbox("Cracked Section", value=True)
        eb_h = st.number_input("Edge Beam H (mm)", 0, 1000, 0)
        eb_w = st.number_input("Edge Beam W (mm)", 0, 1000, 0)

    st.divider()
    btn_calc = st.button("🚀 Run Analysis & Verification", type="primary", use_container_width=True)

# --- MAIN DISPLAY ---
if btn_calc:
    with st.spinner("Processing Linked Calculation..."):
        # Call the unified engine function
        data = engine.analyze_and_verify_system(
            lx, ly, h_user, c1, c2, lc_h, 
            sdl, ll, fc, fy, 
            25, pos, method, continuity, use_cracked, eb_h, eb_w,
            top_db, top_sp, bot_db, bot_sp
        )
        st.session_state['data'] = data
        st.session_state['run'] = True

if st.session_state.get('run'):
    report.render_unified_report(st.session_state['data'])
else:
    st.markdown("## 👋 Ready to Design")
    st.info("👈 Please enter parameters in the Sidebar and click 'Run Analysis'.")
    st.markdown("""
    **System Features:**
    * **Fully Linked:** Rebar selection affects $d$ (effective depth) directly.
    * **Unified Check:** Shear, Deflection, and Flexure are checked against the *actual* user inputs.
    """)
