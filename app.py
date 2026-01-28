import streamlit as st
import pandas as pd
import math
import matplotlib.pyplot as plt
from engine import calculate_detailed_slab
from drawings import plot_slab_section

# --- Page Config ---
st.set_page_config(page_title="Flat Slab Pro Design", page_icon="🏗️", layout="wide")

# --- Helper Functions ---
def get_practical_spacing(as_req, max_spacing_cm):
    def round_step(val): return math.floor(val / 2.5) * 2.5
    area_db12 = (math.pi * 1.2**2) / 4
    area_db16 = (math.pi * 1.6**2) / 4
    
    s12 = round_step((area_db12 * 100) / as_req)
    if s12 < 10.0:
        s16 = round_step((area_db16 * 100) / as_req)
        return f"DB16 @ {min(s16, max_spacing_cm):.1f} cm"
    return f"DB12 @ {min(s12, max_spacing_cm):.1f} cm"

# --- Sidebar ---
with st.sidebar:
    st.header("🏗️ Design Inputs")
    with st.expander("1. Geometry", expanded=True):
        pos = st.selectbox("Position", ["Interior", "Edge", "Corner"])
        lx = st.number_input("Span Lx (m)", 6.0, step=0.5)
        ly = st.number_input("Span Ly (m)", 6.0, step=0.5)
        h_init = st.number_input("Thickness (mm)", 200, step=10)
        c1 = st.number_input("Col Width c1 (mm)", 400) # ตัวแปร c1 ต้นฉบับ (int/float)
        c2 = st.number_input("Col Depth c2 (mm)", 400)
    
    with st.expander("2. Load & Materials", expanded=True):
        fc = st.number_input("fc' (ksc)", 280)
        fy = st.number_input("fy (ksc)", 4000)
        sdl = st.number_input("SDL (kg/m²)", 150)
        ll = st.number_input("Live Load (kg/m²)", 300)
        
    with st.expander("3. Load Factors (Custom)", expanded=True):
        dl_fac = st.number_input("Dead Load Factor", 1.2, 2.0, 1.2, 0.1)
        ll_fac = st.number_input("Live Load Factor", 1.6, 2.0, 1.6, 0.1)

# --- Calculation ---
data = calculate_detailed_slab(lx, ly, h_init, c1, c2, fc, fy, sdl, ll, 20, pos, dl_fac, ll_fac)

# --- Main Dashboard ---
st.title("📑 Structural Design Report")

# Verdict Box
is_pass = data['ratio'] <= 1.0 and data['h_warning'] == ""
if is_pass:
    st.success(f"✅ **PASSED** | Ratio: {data['ratio']:.2f} | Thickness: {data['h_final']} mm")
else:
    st.error(f"❌ **FAILED** | Ratio: {data['ratio']:.2f} | Warning: {data['h_warning']}")

tab1, tab2, tab3 = st.tabs(["📘 Load Summary", "🛡️ Punching Shear", "🏗️ Detailing"])

# --- TAB 1: Loads ---
with tab1:
    st.subheader("1. Load Analysis Summary")
    
    # Load Summary Table (Tons)
    L = data['loading']
    
    col_load1, col_load2 = st.columns([1, 1.5])
    with col_load1:
        st.markdown(f"**Load Factors:** $DL \\times {dl_fac}, LL \\times {ll_fac}$")
        st.metric("Tributary Area ($A_t$)", f"{L['trib_area']:.2f} m²")
        st.metric("Total Column Load ($P_u$)", f"{L['total_load_ton']:.2f} Tons", delta="Factored Load")
    
    with col_load2:
        st.markdown("##### Load Breakdown Table")
        df_load = pd.DataFrame({
            "Type": ["Self Weight (SW)", "Superimposed DL", "Live Load (LL)", "Total Factored ($q_u$)"],
            "Value (kg/m²)": [f"{L['sw']:.0f}", f"{sdl}", f"{ll}", f"**{L['qu']:.2f}**"],
            "Factor": [dl_fac, dl_fac, ll_fac, "-"],
        })
        st.table(df_load)
        st.caption(f"*Note: $M_o$ calculated based on Clear Span $L_n = {data['geo']['ln']:.2f}$ m*")

# --- TAB 2: Punching (Brief) ---
with tab2:
    st.subheader("2. Punching Shear Check")
    P = data['punching']
    
    # *** แก้ไข: เปลี่ยนชื่อตัวแปร c1, c2, c3 เป็น col_p1, col_p2, col_p3 เพื่อไม่ให้ทับตัวแปร c1 (เสา) ***
    col_p1, col_p2, col_p3 = st.columns(3) 
    
    col_p1.metric("Vu (Shear Force)", f"{P['vu']/1000:.2f} Tons")
    col_p2.metric("Phi Vc (Capacity)", f"{P['phi_vc']/1000:.2f} Tons")
    col_p3.metric("D/C Ratio", f"{data['ratio']:.2f}", delta_color="inverse" if data['ratio']>1 else "normal")
    
    st.info(f"Critical Perimeter ($b_o$): {P['bo']*1000:.0f} mm | Effective Depth ($d$): {P['d']*1000:.0f} mm")

# --- TAB 3: Detailing ---
with tab3:
    st.subheader("3. Reinforcement & Detailing")
    
    col_plot, col_table = st.columns([1.5, 1])
    
    with col_plot:
        st.markdown("##### Detailed Cross Section")
        # ตอนนี้ c1 จะเป็นตัวเลข (400) จาก Sidebar เหมือนเดิม ไม่ใช่ st.column แล้ว
        fig_section = plot_slab_section(data['h_final'], 20, c1, data['geo']['ln'], lx)
        st.pyplot(fig_section)
        st.caption("ภาพหน้าตัดแสดงระยะการวางเหล็กและระยะหุ้ม (Cover)")
        
    with col_table:
        st.markdown("##### Rebar Schedule")
        rows = []
        for loc, val in data['rebar'].items():
            loc_name = loc.replace("CS", "Column Strip").replace("MS", "Middle Strip")
            spec = get_practical_spacing(val, data['max_spacing_cm'])
            rows.append([loc_name, spec])
        st.table(pd.DataFrame(rows, columns=["Location", "Selection"]))
