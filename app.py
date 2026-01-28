import streamlit as st
import pandas as pd
import datetime
from engine import calculate_detailed_slab

# --- Page Configuration ---
st.set_page_config(page_title="Structural Calculation Report", layout="wide", page_icon="🏗️")

# --- Helper Functions ---
def get_rebar_spec(as_req, max_spacing_cm):
    import math
    area_db12 = (math.pi * 1.2**2) / 4
    area_db16 = (math.pi * 1.6**2) / 4
    
    s12 = (area_db12 * 100) / as_req
    if s12 < 10:
        s16 = (area_db16 * 100) / as_req
        spacing = min(s16, max_spacing_cm)
        return f"DB16 @ {spacing:.0f} cm" # Round to integer for cleaner site instruction
    else:
        spacing = min(s12, max_spacing_cm)
        return f"DB12 @ {spacing:.0f} cm"

def highlight_min(s):
    is_min = s == s.min()
    return ['background-color: #d4edda; color: #155724; font-weight: bold' if v else '' for v in is_min]

# --- 1. Professional Header ---
st.markdown("## 🏗️ RC Flat Slab Design Report (ACI 318-19)")
col_head1, col_head2 = st.columns([3, 1])
with col_head1:
    st.markdown("**Project:** Automated Structural Design System")
    st.markdown("**Engineer:** Computational Design Module")
with col_head2:
    st.markdown(f"**Date:** {datetime.date.today().strftime('%d %B %Y')}")
    st.markdown("**Code:** ACI 318-19 / WSD Method")
st.markdown("---")

# --- 2. Sidebar Inputs ---
with st.sidebar:
    st.header("📝 Design Parameters")
    
    with st.expander("Geometry", expanded=True):
        pos = st.selectbox("Column Position", ["Interior", "Edge", "Corner"])
        lx = st.number_input("Span Lx (m)", value=6.0, step=0.5)
        ly = st.number_input("Span Ly (m)", value=6.0, step=0.5)
        h_init = st.number_input("Slab Thickness (mm)", value=200, step=10)
        c1 = st.number_input("Col Width c1 (mm)", value=400)
        c2 = st.number_input("Col Depth c2 (mm)", value=400)

    with st.expander("Materials & Loads", expanded=True):
        fc = st.number_input("f'c (ksc)", value=280)
        fy = st.number_input("fy (ksc)", value=4000)
        sdl = st.number_input("SDL (kg/m²)", value=150)
        ll = st.number_input("Live Load (kg/m²)", value=300)

# --- Calculation Engine Call ---
data = calculate_detailed_slab(lx, ly, h_init, c1, c2, fc, fy, sdl, ll, 20, pos)

# --- 3. Body Content ---

# Tab Layout
tab1, tab2, tab3 = st.tabs(["📘 Analysis & Check", "🛡️ Punching Shear", "📋 Reinforcement & Summary"])

# --- TAB 1: Load & Moment Analysis ---
with tab1:
    st.subheader("1. Load Analysis (การวิเคราะห์น้ำหนักบรรทุก)")
    
    col_img, col_calc = st.columns([1, 2])
    with col_img:
        st.info("Load Distribution Concept")
        # Image Trigger: Generic load on slab
        st.markdown("")
        
    with col_calc:
        load = data['loading']
        st.markdown("**Factored Load Calculation ($q_u$):**")
        st.latex(rf"q_u = 1.2(DL + SDL) + 1.6(LL)")
        st.latex(rf"q_u = 1.2({load['sw']:.0f} + {sdl}) + 1.6({ll})")
        st.latex(rf"q_u = {load['dl_fact']:.2f} + {load['ll_fact']:.2f} = \mathbf{{{load['qu']:.2f}}} \; \text{{kg/m}}^2")

    st.markdown("---")
    st.subheader("2. Static Moment (โมเมนต์สถิตยศาสตร์)")
    
    geo = data['geo']
    st.write("ตรวจสอบระยะ Clear Span ($L_n$) และคำนวณ $M_o$ ตามวิธี Direct Design Method:")
    
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.latex(rf"L_n = L_x - c_1 = {lx} - {c1/1000} = {geo['ln']:.2f} \; \text{{m}}")
    with col_m2:
        st.latex(rf"M_o = \frac{{q_u L_y L_n^2}}{{8}} = \frac{{{load['qu']:.2f} \cdot {ly} \cdot {geo['ln']:.2f}^2}}{{8}}")
    
    st.success(f"📌 **Total Static Moment ($M_o$): {data['mo']:,.2f} kg-m**")

# --- TAB 2: Punching Shear (The Highlight) ---
with tab2:
    st.subheader("3. Punching Shear Verification (แรงเฉือนทะลุ)")
    
    # 3.1 Visual Context based on Position
    col_vis, col_data = st.columns([1, 2])
    
    with col_vis:
        st.warning(f"Position: **{pos} Column**")
        if pos == "Interior":
             st.markdown("")
        elif pos == "Edge":
             st.markdown("")
        else: # Corner
             st.markdown("")
        st.caption(f"Critical Perimeter ($b_o$) calculated at d/2 = {(data['geo']['d']*1000/2):.0f} mm from face.")

    with col_data:
        p = data['punching']
        
        # 3.2 Governing Case Comparison Table
        st.markdown("**Step 3A: Compare Concrete Capacity ($v_c$) Formulas**")
        
        df_vc = pd.DataFrame({
            'Formula Condition': ['Limit (0.33)', f'Shape Effect (Beta={p["beta"]:.2f})', 'Size Effect (Alpha)'],
            'Value (MPa)': [p['v1'], p['v2'], p['v3']]
        })
        
        # Highlight the minimum value (Governing Case)
        st.dataframe(df_vc.style.apply(highlight_min, subset=['Value (MPa)']), use_container_width=True)
        
        governing_vc = p['vc_mpa']
        st.latex(rf"\therefore v_{{c,allow}} = \min({p['v1']:.2f}, {p['v2']:.2f}, {p['v3']:.2f}) = \mathbf{{{governing_vc:.2f}}} \; \text{{MPa}}")

    st.markdown("---")
    
    # 3.3 Check Status
    st.markdown("**Step 3B: Final Safety Check**")
    
    # Calculate stresses for display
    # vu_stress = Vu / (bo * d) -> convert everything to Newton/mm2 (MPa)
    # Vu in kg -> * 9.81 = Newton
    # bo, d in m -> * 1000 = mm
    vu_stress = (p['vu'] * 9.80665) / (p['bo']*1000 * p['d']*1000)
    phi_vc_stress = 0.75 * governing_vc
    
    col_res1, col_res2, col_res3 = st.columns(3)
    col_res1.metric("Actual Shear ($v_u$)", f"{vu_stress:.2f} MPa")
    col_res2.metric("Design Capacity ($\phi v_c$)", f"{phi_vc_stress:.2f} MPa")
    col_res3.metric("Safety Ratio", f"{vu_stress/phi_vc_stress:.2f}", delta_color="inverse")

    if vu_stress <= phi_vc_stress:
        st.success(f"✅ **PASS:** The slab thickness ({data['h_final']} mm) is ADEQUATE.")
    else:
        st.error(f"❌ **FAIL:** Increase thickness or add shear reinforcement.")

# --- TAB 3: Summary & Rebar ---
with tab3:
    st.subheader("4. Reinforcement Design (สรุปปริมาณเหล็กเสริม)")
    
    col_draw, col_table = st.columns([1, 2])
    
    with col_draw:
        st.info("Typical Detail Reference")
        st.markdown("")
        st.caption("Note: Top bars for negative moment, Bottom bars for positive moment.")

    with col_table:
        # Prepare Data for Table
        rebar_rows = []
        for loc, val in data['rebar'].items():
            loc_clean = loc.replace("_", " ").title()
            spec = get_rebar_spec(val, data['max_spacing_cm'])
            rebar_rows.append([loc_clean, f"{val:.2f}", f"{data['as_min']:.2f}", spec])
            
        df_rebar = pd.DataFrame(rebar_rows, columns=["Location", "Req. As (cm²/m)", "Min. As (cm²/m)", "Selection"])
        
        st.table(df_rebar)

    # Engineering Note Footer
    with st.expander("📌 Engineering Notes (ข้อกำหนดการก่อสร้าง)", expanded=True):
        st.markdown(f"""
        * **Concrete Cover:** 20 mm (Internal) / 50 mm (Soil Contact)
        * **Max Spacing:** เหล็กเสริมห่างไม่เกิน {data['max_spacing_cm']:.0f} cm (2h หรือ 30cm)
        * **Lap Splice:** ระยะทาบเหล็กตามมาตรฐาน ACI (อย่างน้อย 40d)
        * **Warning:** หากใช้พื้นหนา {data['h_final']} mm แล้วยังมี Deflection ควรพิจารณา Drop Panel
        """)
