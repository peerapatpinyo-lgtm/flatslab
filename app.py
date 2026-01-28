import streamlit as st
import pandas as pd
import math
import matplotlib.pyplot as plt
from engine import calculate_detailed_slab
from drawings import plot_slab_section

# --- Page Config ---
st.set_page_config(page_title="Flat Slab Pro 2.0", page_icon="🏗️", layout="wide")

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
    st.caption("ACI 318-19 | Metric Units")
    
    with st.expander("1. Geometry", expanded=True):
        pos = st.selectbox("Position", ["Interior", "Edge", "Corner"])
        lx = st.number_input("Span Lx (m)", 6.0, step=0.5)
        ly = st.number_input("Span Ly (m)", 6.0, step=0.5)
        h_init = st.number_input("Thickness (mm)", 200, step=10)
        c1 = st.number_input("Col Width c1 (mm)", 400)
        c2 = st.number_input("Col Depth c2 (mm)", 400)
    
    with st.expander("2. Load & Materials", expanded=True):
        fc = st.number_input("fc' (ksc)", 280)
        fy = st.number_input("fy (ksc)", 4000)
        sdl = st.number_input("SDL (kg/m²)", 150)
        ll = st.number_input("Live Load (kg/m²)", 300)
        
    with st.expander("3. Load Factors", expanded=True):
        dl_fac = st.number_input("DL Factor", 1.2, 2.0, 1.2, 0.1)
        ll_fac = st.number_input("LL Factor", 1.6, 2.0, 1.6, 0.1)

# --- Calculation ---
data = calculate_detailed_slab(lx, ly, h_init, c1, c2, fc, fy, sdl, ll, 20, pos, dl_fac, ll_fac)

# --- Main Dashboard ---
st.title("📑 Structural Design Report")

# --- VERDICT CARD ---
ratio = data['ratio']
h_final = data['h_final']
h_min = data['geo']['h_min_req']

col_verdict, col_info = st.columns([2, 1])
with col_verdict:
    if ratio <= 0.9 and data['h_warning'] == "":
        st.success(f"### 🟢 SAFE (DESIGN PASS)\n**Use Thickness: {h_final} mm** | D/C Ratio: {ratio:.2f} (Target < 0.90)")
    elif ratio <= 1.0:
        st.warning(f"### 🟡 WARNING (MARGINAL)\n**Thickness: {h_final} mm** | D/C Ratio: {ratio:.2f} | Consider increasing h for safety.")
    else:
        st.error(f"### 🔴 CRITICAL (FAILED)\n**Ratio: {ratio:.2f}** | Punching Shear Capacity Exceeded.")

with col_info:
    st.metric("Final Thickness", f"{h_final} mm")
    st.caption(f"Min Req (ACI): {h_min:.0f} mm")

# --- TABS ---
tab1, tab2, tab3 = st.tabs(["📘 Analysis Steps", "🛡️ Punching Shear", "🏗️ Detailing & Rebar"])

# --- TAB 1: Analysis ---
with tab1:
    st.subheader("1. Detailed Load Analysis")
    L = data['loading']
    
    # 1.1 Substitution for qu
    st.markdown("**1.1 Factored Load Calculation ($q_u$)**")
    st.latex(rf"""
    \begin{{aligned}}
    q_u &= {dl_fac}(SW + SDL) + {ll_fac}(LL) \\
        &= {dl_fac}({L['sw']:.0f} + {sdl}) + {ll_fac}({ll}) \\
        &= {L['dl_fact']:.2f} + {L['ll_fact']:.2f} \\
        &= \mathbf{{{L['qu']:.2f}}} \; \text{{kg/m}}^2
    \end{{aligned}}
    """)
    
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        st.info(f"""
        **Tributary Area ($A_t$):**
        พื้นที่รับน้ำหนักลงเสาต้นนี้ คิดจากระยะกึ่งกลาง Span ทั้งสองด้าน
        $A_t = L_x \\times L_y = {lx} \\times {ly} = {L['trib_area']:.2f} m^2$
        """)
    with col_t2:
        st.metric("Service Load (Unfactored)", f"{L['service_load_kg']/1000:.2f} Tons", help="Use for Foundation Design")
        st.metric("Ultimate Load (Factored)", f"{L['factored_load_kg']/1000:.2f} Tons", help="Use for Column Design", delta="Design Load")

    st.markdown("---")
    
    # 1.2 Substitution for Mo
    st.markdown("**1.2 Static Moment ($M_o$)**")
    G = data['geo']
    st.latex(rf"""
    \begin{{aligned}}
    L_n &= L_x - c_1 = {lx} - {c1/1000} = {G['ln_calc']:.2f} \; m \\
    M_o &= \frac{{q_u L_y (L_n)^2}}{{8}} \\
        &= \frac{{{L['qu']:.2f} \cdot {ly} \cdot {G['ln']:.2f}^2}}{{8}} \\
        &= \mathbf{{{data['mo']:,.2f}}} \; \text{{kg-m}}
    \end{{aligned}}
    """)

# --- TAB 2: Punching ---
with tab2:
    st.subheader("2. Punching Shear Verification")
    P = data['punching']
    
    col_p1, col_p2, col_p3 = st.columns(3)
    col_p1.metric("Vu (Design Shear)", f"{P['vu_design']/1000:.2f} Tons", help=f"Includes {data['unbalanced_factor']}x factor for Unbalanced Moment")
    col_p2.metric("Phi Vc (Capacity)", f"{P['phi_vc']/1000:.2f} Tons")
    col_p3.metric("Safety Ratio", f"{data['ratio']:.2f}", delta_color="inverse" if data['ratio'] > 0.9 else "normal")
    
    if data['unbalanced_factor'] > 1.0:
        st.warning(f"⚠️ Note: $V_u$ magnified by {data['unbalanced_factor']}x for {pos} column (Unbalanced Moment Effect).")
        
    st.table(pd.DataFrame({
        "Parameter": ["Effective Depth (d)", "Critical Perimeter (bo)", "Concrete Strength (vc)"],
        "Value": [f"{P['d']*1000:.0f} mm", f"{P['bo']*1000:.0f} mm", f"{P['vc_mpa']:.2f} MPa"]
    }))

# --- TAB 3: Detailing ---
with tab3:
    st.subheader("3. Reinforcement & Construction Drawing")
    
    col_draw, col_spec = st.columns([2, 1])
    
    with col_draw:
        # Call new drawing function
        fig = plot_slab_section(data['h_final'], 20, c1, data['geo']['ln'], lx)
        st.pyplot(fig)
        
    with col_spec:
        st.markdown("##### Rebar Schedule")
        rows = []
        for loc, val in data['rebar'].items():
            loc_name = loc.replace("CS", "Column Strip").replace("MS", "Middle Strip")
            spec = get_practical_spacing(val, data['max_spacing_cm'])
            rows.append([loc_name, spec])
        st.table(pd.DataFrame(rows, columns=["Location", "Selection"]))
        
        st.info("""
        **Construction Note:**
        * Top bars (Red) must extend according to 'Ext.' dimension.
        * Bottom bars (Blue) are continuous.
        * Cover 20mm for internal slabs.
        """)
