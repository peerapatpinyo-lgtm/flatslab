import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="Advanced Flat Slab Design",
    page_icon="🏗️",
    layout="wide"
)

# Custom CSS for better readability
st.markdown("""
<style>
    .reportview-container {
        background: #f0f2f6
    }
    .stMetric {
        background-color: #ffffff;
        padding: 10px;
        border-radius: 5px;
        border: 1px solid #e0e0e0;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. HELPER FUNCTIONS
# ==========================================

def show_step(title, latex_eq, sub_eq, result, unit, note=None):
    """
    ฟังก์ชันช่วยแสดงผลการคำนวณ: สูตร -> แทนค่า -> คำตอบ
    """
    st.markdown(f"#### {title}")
    if note:
        st.caption(f"ℹ️ *{note}*")
    
    # แสดงสูตร
    st.latex(latex_eq)
    
    # แสดงการแทนค่าและผลลัพธ์
    col_a, col_b = st.columns([3, 1])
    with col_a:
        st.markdown("**Substitution:**")
        st.latex(sub_eq)
    with col_b:
        st.markdown("**Result:**")
        st.metric(label=unit, value=result)
    st.markdown("---")

def plot_geometry(L1, L2, c1, c2):
    """
    ฟังก์ชันวาดรูป Top View แบบ Engineering Drawing
    """
    # Convert inputs
    c1_m = c1 / 100.0
    c2_m = c2 / 100.0
    
    # Create Figure
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # 1. Draw Columns (4 corners)
    col_coords = [(0,0), (L1,0), (0,L2), (L1,L2)]
    for (cx, cy) in col_coords:
        rect = patches.Rectangle(
            (cx - c1_m/2, cy - c2_m/2), c1_m, c2_m,
            linewidth=1.5, edgecolor='black', facecolor='#555555', zorder=10
        )
        ax.add_patch(rect)
        
    # 2. Draw Grid Lines
    margin = max(L1, L2) * 0.2
    ax.axvline(x=0, color='black', linestyle='-.', alpha=0.5, linewidth=0.8)
    ax.axvline(x=L1, color='black', linestyle='-.', alpha=0.5, linewidth=0.8)
    ax.axhline(y=0, color='black', linestyle='-.', alpha=0.5, linewidth=0.8)
    ax.axhline(y=L2, color='black', linestyle='-.', alpha=0.5, linewidth=0.8)
    
    # 3. Draw Strips Zones
    min_span = min(L1, L2)
    cs_width = 0.25 * min_span # width per side of centerline
    
    # Column Strips (Blue) - Horizontal
    ax.add_patch(patches.Rectangle((-margin, -cs_width), L1+2*margin, 2*cs_width, color='#3b82f6', alpha=0.15))
    ax.add_patch(patches.Rectangle((-margin, L2-cs_width), L1+2*margin, 2*cs_width, color='#3b82f6', alpha=0.15))
    
    # Middle Strip (Green)
    ms_height = L2 - 2*cs_width
    if ms_height > 0:
        ax.add_patch(patches.Rectangle((-margin, cs_width), L1+2*margin, ms_height, color='#22c55e', alpha=0.15))
        # Text Label Middle Strip
        ax.text(L1/2, L2/2, "MIDDLE STRIP", ha='center', va='center', 
                color='green', fontsize=10, fontweight='bold', alpha=0.7)
    
    # Text Label Column Strip
    ax.text(L1/2, 0, "COLUMN STRIP", ha='center', va='center', 
            color='blue', fontsize=10, fontweight='bold', alpha=0.7)

    # 4. Dimensions
    def draw_dim_line(x1, y1, x2, y2, text, offset_x=0, offset_y=0):
        ax.annotate('', xy=(x1, y1), xytext=(x2, y2), arrowprops=dict(arrowstyle='<->', lw=1))
        mid_x, mid_y = (x1+x2)/2 + offset_x, (y1+y2)/2 + offset_y
        ax.text(mid_x, mid_y, text, ha='center', va='center', fontsize=9, backgroundcolor='white')

    # Dim L1
    draw_dim_line(0, -margin/2, L1, -margin/2, f"L1 = {L1} m")
    # Dim L2
    draw_dim_line(-margin/2, 0, -margin/2, L2, f"L2 = {L2} m")
    
    # Set Plot Limits
    ax.set_xlim(-margin, L1 + margin)
    ax.set_ylim(-margin, L2 + margin)
    ax.set_aspect('equal')
    ax.axis('off')
    plt.tight_layout()
    
    return fig

# ==========================================
# 3. SIDEBAR INPUTS
# ==========================================
st.sidebar.title("🛠️ Design Parameters")

with st.sidebar.expander("1. Material Properties", expanded=True):
    fc = st.number_input("Concrete Strength (fc') [ksc]", value=240.0, step=10.0)
    fy = st.number_input("Steel Yield Strength (fy) [ksc]", value=4000.0, step=100.0)

with st.sidebar.expander("2. Geometry (Span & Slab)", expanded=True):
    L1 = st.number_input("L1: Span Length (Analysis Dir) [m]", value=6.0, step=0.5)
    L2 = st.number_input("L2: Transverse Span [m]", value=5.0, step=0.5)
    h_slab = st.number_input("Slab Thickness (h) [cm]", value=20.0, step=1.0)
    l_c = st.number_input("Storey Height (lc) [m]", value=3.0, step=0.1)

with st.sidebar.expander("3. Column Dimensions", expanded=True):
    c1 = st.number_input("c1 (Parallel to L1) [cm]", value=40.0, step=5.0)
    c2 = st.number_input("c2 (Transverse) [cm]", value=40.0, step=5.0)

with st.sidebar.expander("4. Loads", expanded=True):
    SDL = st.number_input("Superimposed Dead Load (SDL) [kg/m²]", value=100.0, step=10.0)
    LL = st.number_input("Live Load (LL) [kg/m²]", value=300.0, step=10.0)

# ==========================================
# 4. MAIN CALCULATION LOGIC
# ==========================================

# --- Unit Conversion & Constants ---
L1_cm = L1 * 100
L2_cm = L2 * 100
lc_cm = l_c * 100
Ec = 15100 * np.sqrt(fc) # ksc

# --- Load Calculation ---
w_self = (h_slab / 100) * 2400 # kg/m2 (Conc Density ~2400)
w_dead = w_self + SDL
w_u = 1.2 * w_dead + 1.6 * LL # Factored Load

# --- EFM Stiffness Calculations ---
# 1. Slab
Is = (L2_cm * h_slab**3) / 12
Ks = (4 * Ec * Is) / L1_cm

# 2. Column
Ic = (c2 * c1**3) / 12
Kc = (4 * Ec * Ic) / lc_cm

# 3. Torsion
x = min(c1, h_slab)
y = max(c1, h_slab)
C = (1 - 0.63 * (x/y)) * (x**3 * y) / 3
term_denom = L2_cm * (1 - (c2/L2_cm))**3
Kt = 2 * (9 * Ec * C) / term_denom # Multiplied by 2 for both sides of column

# 4. Equivalent Column
Sum_Kc = 2 * Kc # Top and Bottom columns
Kec = 1 / ((1/Sum_Kc) + (1/Kt))

# 5. Distribution Factors
DF_slab = Ks / (Ks + Kec)
DF_col = 1 - DF_slab

# --- DDM Moment Calculations ---
ln = L1 - (c1/100) # Clear span in meters
Mo = (w_u * L2 * ln**2) / 8

# ==========================================
# 5. APP LAYOUT & TABS
# ==========================================

st.title("🏗️ Flat Slab Design Analyzer")
st.markdown("โปรแกรมวิเคราะห์พื้นไร้คาน : **Equivalent Frame Method (Stiffness)** & **Direct Design Method (Moments)**")

# Create Tabs
tab_calc, tab_view = st.tabs(["📝 Detailed Calculation", "📐 Geometry View (Top View)"])

# ------------------------------------------
# TAB 1: CALCULATION
# ------------------------------------------
with tab_calc:
    # --- Section: Loads ---
    st.header("1. Load Analysis")
    col1, col2, col3 = st.columns(3)
    col1.metric("Self Weight", f"{w_self:.1f} kg/m²")
    col2.metric("Total Dead Load", f"{w_dead:.1f} kg/m²")
    col3.metric("Factored Load (Wu)", f"{w_u:.1f} kg/m²", delta="Design Load")
    
    st.latex(r"w_u = 1.2(DL) + 1.6(LL)")
    
    # --- Section: EFM Stiffness ---
    st.header("2. Stiffness Calculation (EFM)")
    st.info("การคำนวณ Stiffness ของชิ้นส่วนต่างๆ เพื่อหา Equivalent Frame Properties")

    # 2.1 Slab
    with st.expander("2.1 Slab Stiffness (Ks)", expanded=False):
        show_step(
            "Moment of Inertia (Is)",
            r"I_s = \frac{L_2 h^3}{12}",
            fr"I_s = \frac{{{L2_cm:.0f} \cdot {h_slab:.0f}^3}}{{12}}",
            f"{Is:,.2f}", "cm⁴"
        )
        show_step(
            "Stiffness (Ks)",
            r"K_s = \frac{4 E_c I_s}{L_1}",
            fr"K_s = \frac{{4 \cdot {Ec:,.2f} \cdot {Is:,.2f}}}{{{L1_cm:.0f}}}",
            f"{Ks:,.2f}", "kg-cm"
        )

    # 2.2 Column
    with st.expander("2.2 Column Stiffness (Kc)", expanded=False):
        show_step(
            "Moment of Inertia (Ic)",
            r"I_c = \frac{c_2 c_1^3}{12}",
            fr"I_c = \frac{{{c2:.0f} \cdot {c1:.0f}^3}}{{12}}",
            f"{Ic:,.2f}", "cm⁴"
        )
        show_step(
            "Stiffness (Kc)",
            r"K_c = \frac{4 E_c I_c}{l_c}",
            fr"K_c = \frac{{4 \cdot {Ec:,.2f} \cdot {Ic:,.2f}}}{{{lc_cm:.0f}}}",
            f"{Kc:,.2f}", "kg-cm"
        )

    # 2.3 Torsion & Equivalent Column
    with st.expander("2.3 Equivalent Column Stiffness (Kec) - *Complex Part*", expanded=True):
        st.write("ส่วนนี้คำนวณผลของ Torsion member ที่ลดทอนความแข็งของเสา")
        
        # C calculation
        st.markdown(f"**Torsional Constant (C):** ใช้หน้าตัด $x={x} cm, y={y} cm$")
        st.latex(r"C = (1 - 0.63 \frac{x}{y}) \frac{x^3 y}{3}")
        st.write(f"Result **C = {C:,.2f} cm⁴**")
        
        # Kt calculation
        st.markdown("**Torsional Stiffness (Kt):**")
        st.latex(r"K_t = \sum \frac{9 E_c C}{L_2 (1 - c_2/L_2)^3}")
        st.write(f"Result **Kt = {Kt:,.2f} kg-cm**")
        
        # Kec calculation
        show_step(
            "Equivalent Stiffness (Kec)",
            r"\frac{1}{K_{ec}} = \frac{1}{\Sigma K_c} + \frac{1}{K_t}",
            fr"\frac{{1}}{{K_{{ec}}}} = \frac{{1}}{{{Sum_Kc:,.2f}}} + \frac{{1}}{{{Kt:,.2f}}}",
            f"{Kec:,.2f}", "kg-cm",
            note="Kec คือค่าความแข็งจริงของเสาที่พื้น 'รู้สึก' ได้"
        )

    # 2.4 DF Summary
    st.subheader("Results: Distribution Factors (DF)")
    c_df1, c_df2 = st.columns(2)
    c_df1.success(f"**DF Slab:** {DF_slab:.4f}")
    c_df2.warning(f"**DF Column:** {DF_col:.4f}")

    # --- Section: DDM Moments ---
    st.header("3. Direct Design Method Moments")
    
    # Static Moment
    show_step(
        "Total Static Moment (Mo)",
        r"M_o = \frac{w_u L_2 l_n^2}{8}",
        fr"M_o = \frac{{{w_u:.2f} \cdot {L2} \cdot {ln:.2f}^2}}{{8}}",
        f"{Mo:,.2f}", "kg-m"
    )

    # Moment Table
    st.subheader("Moment Distribution Table (Interior Span)")
    
    # Calculate moments
    m_neg = Mo * 0.65
    m_pos = Mo * 0.35
    
    # Create DataFrame for display
    df_moments = pd.DataFrame([
        ["Negative (-)", "Column Strip (75%)", f"{m_neg * 0.75:,.2f}"],
        ["Negative (-)", "Middle Strip (25%)", f"{m_neg * 0.25:,.2f}"],
        ["Positive (+)", "Column Strip (60%)", f"{m_pos * 0.60:,.2f}"],
        ["Positive (+)", "Middle Strip (40%)", f"{m_pos * 0.40:,.2f}"],
    ], columns=["Moment Type", "Strip Zone", "Design Moment (kg-m)"])
    
    st.table(df_moments)

# ------------------------------------------
# TAB 2: GEOMETRY VIEW
# ------------------------------------------
with tab_view:
    st.header("Generated Geometry Plan")
    st.markdown("แสดงสัดส่วนจริงของพื้นและเสา (Top View)")
    
    # Call Plotting Function
    fig = plot_geometry(L1, L2, c1, c2)
    st.pyplot(fig)
    
    st.info("""
    **Legend:**
    - 🟦 **สีฟ้า (Column Strip):** พื้นที่รับแรงหลักบริเวณแนวเสา
    - 🟩 **สีเขียว (Middle Strip):** พื้นที่ช่วงกลางแผ่นพื้น
    - ⬛ **สี่เหลี่ยมดำ:** ขนาดเสาจริง
    """)

# Footer
st.markdown("---")
st.caption("Developed for Structural Engineering Analysis | Based on ACI 318")
