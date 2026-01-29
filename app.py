import streamlit as st
import engine
import report

# --- Page Configuration ---
st.set_page_config(
    page_title="Pro Flat Slab Design", 
    layout="wide", 
    page_icon="🏗️",
    initial_sidebar_state="expanded"
)

# --- Sidebar: Input Section ---
with st.sidebar:
    st.title("⚙️ Design Parameters")
    
    st.markdown("### 1. Geometry & Material")
    with st.expander("Dimensions", expanded=True):
        lx = st.number_input("Span Lx (m)", 3.0, 15.0, 8.0, step=0.1)
        ly = st.number_input("Span Ly (m)", 3.0, 15.0, 8.0, step=0.1)
        h_init = st.number_input("Trial Thickness (mm)", 100, 600, 200, step=10)
        
        c1 = st.number_input("Col Width c1 (mm)", 200, 1500, 500)
        c2 = st.number_input("Col Depth c2 (mm)", 200, 1500, 500)
        lc_h = st.number_input("Story Height (m)", 2.5, 6.0, 3.0)

    with st.expander("Materials & Loads"):
        sdl = st.number_input("SDL (kg/m2)", 0, 1000, 150)
        ll = st.number_input("Live Load (kg/m2)", 0, 2000, 300)
        fc = st.number_input("fc' (ksc)", 180, 500, 280)
        fy = st.number_input("fy (ksc)", 2400, 5000, 4000)

    st.markdown("### 2. Analysis Settings")
    method = st.radio("Method", ["EFM (Equivalent Frame)", "DDM (Direct Design)"])
    continuity = st.selectbox("Continuity", ["Interior Span", "End Span (Slab Only)", "End Span (Integral Beam)"])
    pos = st.selectbox("Position (Shear)", ["Interior", "Edge", "Corner"])
    
    use_cracked = st.checkbox("Cracked Section (ACI)", value=True)
    include_edge_beam = st.checkbox("Include Edge Beam", value=False)
    eb_h, eb_w = 0, 0
    if include_edge_beam:
        eb_h = st.number_input("Edge Beam Depth (mm)", 300, 1000, 500)
        eb_w = st.number_input("Edge Beam Width (mm)", 200, 800, 300)

    st.markdown("### 3. Reinforcement (Design)")
    r_col1, r_col2 = st.columns(2)
    with r_col1:
        top_db = st.selectbox("Top Bar", [12, 16, 20, 25], index=1)
        top_sp = st.number_input("Top @ (mm)", 50, 450, 200, step=25)
    with r_col2:
        bot_db = st.selectbox("Bot Bar", [12, 16, 20, 25], index=0)
        bot_sp = st.number_input("Bot @ (mm)", 50, 450, 250, step=25)

    st.divider()
    # --- Trigger Button ---
    btn_calc = st.button("🚀 Calculate & Generate Report", type="primary", use_container_width=True)

# --- Main Logic ---

if btn_calc:
    with st.spinner("Analyzing Structure & Verifying Code Compliance..."):
        # 1. Run Analysis
        base_data = engine.analyze_structure(
            lx, ly, h_init, c1, c2, lc_h, lc_h, 
            fc, fy, sdl, ll, 25, pos, 1.4, 1.7, 
            20, continuity, method, use_cracked, eb_h, eb_w
        )
        
        # 2. Run Verification
        verify_data = engine.verify_reinforcement(base_data, top_db, top_sp, bot_db, bot_sp)
        
        # 3. Store in Session State
        st.session_state['report_data'] = (base_data, verify_data)
        st.session_state['has_run'] = True

# --- Display Logic ---

if 'has_run' in st.session_state and st.session_state['has_run']:
    # Retrieve data
    base_data, verify_data = st.session_state['report_data']
    
    # Render Unified Report
    report.render_unified_report(base_data, verify_data)

else:
    # Landing Page State
    st.title("🛡️ Professional Flat Slab Design System")
    st.markdown("""
    ### Welcome to the Design Suite
    
    Please configure your structural parameters in the **Sidebar** to the left.
    
    **Workflow:**
    1.  Define **Geometry** (Spans, Columns, Thickness)
    2.  Set **Loads & Materials** (SDL, LL, fc', fy)
    3.  Select **Analysis Method** (EFM/DDM)
    4.  Choose **Reinforcement** intent
    5.  Click **"Calculate"** to generate the full engineering report.
    
    ---
    *Compliance: ACI 318-19 | Metric Units*
    """)
