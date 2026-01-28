import streamlit as st
import engine
import report
import drawings
import io

st.set_page_config(page_title="Flat Slab Expert 2024", layout="wide", page_icon="🏗️")

# --- Sidebar Inputs ---
with st.sidebar:
    st.title("🏗️ Design Parameters")
    
    with st.expander("Geometry", expanded=True):
        lx = st.number_input("Span Lx (m)", value=6.0, step=0.1)
        ly = st.number_input("Span Ly (m)", value=6.0, step=0.1)
        c1 = st.number_input("Col Width (mm)", value=400)
        c2 = st.number_input("Col Depth (mm)", value=400)
        pos = st.selectbox("Column Position", ["Interior", "Edge", "Corner"])
        h_init = st.number_input("Initial Thickness (mm)", value=150, step=10)

    with st.expander("Materials & Loads", expanded=True):
        fc = st.number_input("fc' (ksc)", 280)
        fy = st.number_input("fy (ksc)", 4000)
        sdl = st.number_input("SDL (kg/m2)", 150)
        ll = st.number_input("LL (kg/m2)", 300)
        dl_fac = st.number_input("DL Factor", 1.2)
        ll_fac = st.number_input("LL Factor", 1.6)

# --- Execute Design Engine ---
data = engine.run_design_cycle(lx, ly, h_init, c1, c2, fc, fy, sdl, ll, 20, pos, dl_fac, ll_fac)
res = data['results']

# --- Main Interface ---
st.title("🏗️ Structural Design Report: Flat Slab")

# 1. Design Verdict Banner
verdict_container = st.container()
with verdict_container:
    is_pass = res['ratio'] <= 1.0
    h_final = res['h']
    
    if is_pass:
        st.success(f"✅ **DESIGN PASSED** | Final Thickness: **{h_final} mm** | Ratio: **{res['ratio']:.2f}**")
    else:
        st.error(f"❌ **DESIGN FAILED** | Ratio: **{res['ratio']:.2f}** | Please increase Column Size or Concrete Strength.")

# 2. Tabs
tab1, tab2 = st.tabs(["📄 Detailed Calculation", "📐 Shop Drawing"])

with tab1:
    report.render_report(data)
    
    # Download Button Logic
    report_text = f"""
    FLAT SLAB DESIGN REPORT
    =======================
    Project: Flat Slab Analysis
    Status: {'PASS' if is_pass else 'FAIL'}
    
    [GEOMETRY]
    Span Lx: {lx} m
    Span Ly: {ly} m
    Column: {c1}x{c2} mm
    Thickness: {h_final} mm
    
    [RESULTS]
    Vu (Demand): {res['vu_kg']:.2f} kg
    Phi Vc (Capacity): {res['phi_vc_kg']:.2f} kg
    Ratio: {res['ratio']:.2f}
    """
    
    st.download_button(
        label="📥 Download Summary (TXT)",
        data=report_text,
        file_name="flatslab_design_summary.txt",
        mime="text/plain"
    )

with tab2:
    st.markdown("### Cross Section Detail")
    fig = drawings.draw_section(res['h'], 20, c1, data['inputs']['ln'], lx)
    st.pyplot(fig)
    st.info(f"**Drawing Note:** Top bar extension is calculated as 0.33Ln = {0.33*data['inputs']['ln']:.2f} m.")
