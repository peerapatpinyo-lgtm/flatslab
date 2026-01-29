import streamlit as st
import engine
import report

# --- PAGE SETUP ---
st.set_page_config(page_title="Pro Slab Design", layout="wide", page_icon="🏗️")

# --- SESSION STATE INITIALIZATION ---
if 'calc_results' not in st.session_state:
    st.session_state.calc_results = None

# --- SIDEBAR INPUTS (FORM) ---
with st.sidebar:
    st.title("🏗️ Design Parameters")
    
    # Use st.form to batch inputs and prevent reload on every change
    with st.form("design_input_form"):
        st.subheader("1. Geometry & Section")
        col1, col2 = st.columns(2)
        lx = col1.number_input("Span Lx (m)", 3.0, 15.0, 8.0, step=0.1)
        ly = col2.number_input("Span Ly (m)", 3.0, 15.0, 8.0, step=0.1)
        h_user = st.number_input("Slab Thickness (mm)", 100, 600, 200, step=10)
        
        col3, col4 = st.columns(2)
        c1_mm = col3.number_input("Col Width (mm)", 200, 1500, 500)
        c2_mm = col4.number_input("Col Depth (mm)", 200, 1500, 500)
        lc_h = st.number_input("Story Height (m)", 2.5, 6.0, 3.0)
        
        st.subheader("2. Loading & Materials")
        sdl = st.number_input("SDL (kg/m²)", 0, 1000, 150)
        ll = st.number_input("Live Load (kg/m²)", 0, 2000, 300)
        fc = st.number_input("fc' (ksc)", 180, 500, 280)
        fy = st.number_input("fy (ksc)", 2400, 5000, 4000)
        
        st.subheader("3. Reinforcement (Design)")
        st.info("Select rebar to verify structural capacity")
        
        st.markdown("**Top Bars (Negative)**")
        t1, t2 = st.columns(2)
        top_db = t1.selectbox("Top DB", [10, 12, 16, 20, 25], index=1)
        top_sp = t2.number_input("Top @ (mm)", 50, 400, 200, step=25)
        
        st.markdown("**Bottom Bars (Positive)**")
        b1, b2 = st.columns(2)
        bot_db = b1.selectbox("Bot DB", [10, 12, 16, 20, 25], index=1)
        bot_sp = b2.number_input("Bot @ (mm)", 50, 400, 250, step=25)
        
        st.subheader("4. Advanced Config")
        method = st.radio("Method", ["EFM", "DDM"])
        pos = st.selectbox("Position", ["Interior", "Edge", "Corner"])
        use_cracked = st.checkbox("Cracked Section Analysis", value=True)
        
        st.markdown("---")
        # SUBMIT BUTTON - The only trigger for calculation
        submit_val = st.form_submit_button("🚀 Run Analysis", type="primary")

# --- LOGIC TRIGGER ---
if submit_val:
    with st.spinner("Analyzing structure..."):
        # Call Engine -> Get COMPLETE object
        results = engine.run_full_analysis(
            lx, ly, h_user, c1_mm, c2_mm, lc_h,
            sdl, ll, fc, fy,
            25, pos, method, "Interior Span", use_cracked, 0, 0,
            top_db, top_sp, bot_db, bot_sp
        )
        # Store in Session State
        st.session_state.calc_results = results

# --- REPORT RENDERING ---
if st.session_state.calc_results is not None:
    # Pass ONLY the data object to report
    report.render_unified_report(st.session_state.calc_results)
else:
    # Landing Screen
    st.title("🛡️ Professional Flat Slab Design System")
    st.markdown("""
    ### 👋 Welcome
    This application helps you design and verify RC Flat Slabs according to ACI 318-19.
    
    **How to use:**
    1.  Open the **Sidebar** (left).
    2.  Fill in **Geometry, Loads, and Reinforcement**.
    3.  Click **'Run Analysis'**.
    
    *The report will generate securely and persist on this screen.*
    """)
