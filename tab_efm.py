import streamlit as st
import numpy as np
import pandas as pd
import math
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.gridspec import GridSpec

# Set Plot Style & Parameters
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.size': 10,
    'axes.labelsize': 11,
    'axes.titlesize': 12,
    'lines.linewidth': 2
})

# --- Visualization Functions (Fixed Fonts & Improved Layout) ---

def plot_torsional_concept_detailed(c1_cm, c2_cm, h_cm):
    """
    แสดงภาพ Concept Torsional Member แบบ Plan + Section
    (ใช้ภาษาอังกฤษในกราฟเพื่อแก้ปัญหาสระลอย/ภาษาต่างด้าว)
    """
    fig = plt.figure(figsize=(9, 4))
    gs = GridSpec(1, 2, width_ratios=[1, 1])

    # --- Subplot 1: Plan View ---
    ax1 = fig.add_subplot(gs[0])
    
    # Scale setup
    limit = max(c1_cm, c2_cm) * 2
    ax1.set_xlim(-limit, limit)
    ax1.set_ylim(-limit, limit)
    ax1.set_aspect('equal')
    
    # 1. Draw Column (Center)
    col_rect = patches.Rectangle((-c1_cm/2, -c2_cm/2), c1_cm, c2_cm, 
                                 facecolor='#95a5a6', edgecolor='k', lw=1.5, label='Column', zorder=5)
    ax1.add_patch(col_rect)
    
    # 2. Draw Torsional Members (Side strips)
    # Effective width y approx c1
    y_eff = c1_cm
    # Left Strip
    t_strip_left = patches.Rectangle((-c1_cm/2 - y_eff, -c2_cm/2), y_eff, c2_cm, 
                                     facecolor='#e74c3c', alpha=0.3, hatch='///', edgecolor='#c0392b')
    # Right Strip
    t_strip_right = patches.Rectangle((c1_cm/2, -c2_cm/2), y_eff, c2_cm, 
                                      facecolor='#e74c3c', alpha=0.3, hatch='///', edgecolor='#c0392b', label='Torsional Member')
    ax1.add_patch(t_strip_left)
    ax1.add_patch(t_strip_right)
    
    # 3. Slab Background (Visual Context)
    ax1.add_patch(patches.Rectangle((-limit, -c2_cm/2), 2*limit, c2_cm, facecolor='#ecf0f1', zorder=0))

    # Dimensions
    # c1 dimension
    ax1.annotate("", xy=(-c1_cm/2, c2_cm/2 + 10), xytext=(c1_cm/2, c2_cm/2 + 10), arrowprops=dict(arrowstyle='<->', lw=1))
    ax1.text(0, c2_cm/2 + 15, f"c1 = {c1_cm} cm", ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    # y dimension
    ax1.annotate("", xy=(c1_cm/2, -c2_cm/2 - 10), xytext=(c1_cm/2 + y_eff, -c2_cm/2 - 10), arrowprops=dict(arrowstyle='<->', lw=1, color='#c0392b'))
    ax1.text(c1_cm/2 + y_eff/2, -c2_cm/2 - 25, f"y (width) ~ c1", ha='center', va='top', fontsize=9, color='#c0392b')

    ax1.axis('off')
    ax1.set_title("1. Plan View (Top Down)", fontsize=12, fontweight='bold')
    ax1.legend(loc='upper right', fontsize=8, framealpha=0.9)

    # --- Subplot 2: Section View ---
    ax2 = fig.add_subplot(gs[1])
    
    x_dim = h_cm
    y_dim = c1_cm
    
    # Center the drawing
    ax2.set_xlim(-10, y_dim + 30)
    ax2.set_ylim(-10, x_dim + 20)
    ax2.set_aspect('equal')
    
    # Draw Cross Section
    section_rect = patches.Rectangle((0, 0), y_dim, x_dim, 
                                     facecolor='#e74c3c', alpha=0.5, edgecolor='k', lw=1.5, hatch='///')
    ax2.add_patch(section_rect)
    
    # Dimension x (thickness)
    ax2.annotate("", xy=(y_dim + 5, 0), xytext=(y_dim + 5, x_dim), arrowprops=dict(arrowstyle='<->', lw=1))
    ax2.text(y_dim + 8, x_dim/2, f"x = h ({h_cm} cm)", va='center', fontsize=9)
    
    # Dimension y (width)
    ax2.annotate("", xy=(0, -5), xytext=(y_dim, -5), arrowprops=dict(arrowstyle='<->', lw=1))
    ax2.text(y_dim/2, -8, f"y = c1 ({c1_cm} cm)", ha='center', va='top', fontsize=9)
    
    ax2.text(y_dim/2, x_dim/2, "Torsional Section\n(Cross-Section A-A)", ha='center', va='center', fontsize=9, color='white', fontweight='bold')
    
    ax2.axis('off')
    ax2.set_title("2. Section View (Cross-Section)", fontsize=12, fontweight='bold')
    
    plt.tight_layout()
    return fig

def plot_moment_reduction_detailed(M_cl, M_face, c1_cm, L1_m, w_u, Vu_sup):
    """
    แสดงกราฟลดค่าโมเมนต์แบบ Stacked (Physical + Diagram)
    แก้ไข Label เป็นภาษาอังกฤษเพื่อความชัดเจน
    """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6), sharex=True, gridspec_kw={'height_ratios': [1, 2], 'hspace': 0.1})
    
    c1_m = c1_cm / 100.0
    dist_face = c1_m / 2.0
    # Zoom in to 35% of span to see details
    plot_span = L1_m * 0.35
    
    # --- Subplot 1: Physical Model ---
    # 1. Beam
    ax1.plot([-dist_face*2, plot_span], [0, 0], 'k-', lw=4, color='#7f8c8d')
    
    # 2. Column Support (Visual block)
    support_rect = patches.Rectangle((-dist_face, -0.4), c1_m, 0.4, facecolor='#bdc3c7', hatch='..', edgecolor='k')
    ax1.add_patch(support_rect)
    
    # 3. Critical Lines (Vertical)
    ax1.axvline(0, color='k', linestyle='-.', lw=1, alpha=0.5) # CL
    ax1.axvline(dist_face, color='r', linestyle='--', lw=1.5) # Face
    
    # 4. Load Arrows
    arrow_spacing = plot_span / 5
    for x in np.arange(0, plot_span, arrow_spacing):
        ax1.arrow(x, 0.8, 0, -0.5, head_width=0.02*L1_m, head_length=0.2, fc='blue', ec='blue')
    ax1.text(plot_span/2, 1.0, f"Load w_u = {w_u:,.0f}", ha='center', color='blue', fontsize=9)
    
    # 5. Reaction Shear Arrow
    ax1.arrow(0, -0.8, 0, 0.6, head_width=0.03*L1_m, head_length=0.2, fc='k', ec='k', lw=2)
    ax1.text(0.02, -0.9, f"Reaction V_u\n= {Vu_sup:,.0f} kg", ha='left', va='top', fontsize=9)
    
    # Labels
    ax1.text(0, 0.2, "CL", ha='center', fontweight='bold', fontsize=9)
    ax1.text(dist_face, 0.2, "Face", ha='center', color='r', fontweight='bold', fontsize=9)
    
    ax1.set_ylim(-1.2, 1.5)
    ax1.axis('off')
    ax1.set_title("1. Physical Model & Loading", fontsize=11, fontweight='bold', loc='left')

    # --- Subplot 2: Moment Diagram ---
    # Create smooth curve
    x_vals = np.linspace(0, plot_span, 100)
    # Approx Parabola: M(x) = M_cl - Vu*x + w*x^2/2 (Standard Statics)
    # Note: This is an approximation for visualization relative to CL
    # To match M_cl and M_face exactly visually:
    # Use simple parabola form: y = a*x^2 + b*x + c
    # At x=0, y = -M_cl. At x=dist_face, y = -M_face.
    # Let's just use the M_cl curve shape: M = M_cl - (Vu*x - w*x^2/2) 
    y_vals = -1 * (M_cl - (Vu_sup * x_vals - w_u * (x_vals**2) / 2.0))

    # Plot Curve
    ax2.plot(x_vals, y_vals, color='blue', lw=2.5, label='Moment Diagram')
    
    # Critical Lines (extend from top)
    ax2.axvline(0, color='k', linestyle='-.', lw=1, alpha=0.5)
    ax2.axvline(dist_face, color='r', linestyle='--', lw=1.5)
    
    # Points
    ax2.plot(0, -M_cl, 'ko', markersize=8, zorder=5)
    ax2.text(0.02*L1_m, -M_cl, f"M_CL = {M_cl:,.0f}", va='center', ha='left', fontweight='bold', fontsize=10)
    
    ax2.plot(dist_face, -M_face, 'ro', markersize=8, zorder=5)
    ax2.text(dist_face + 0.02*L1_m, -M_face, f"M_face = {M_face:,.0f}", va='center', ha='left', color='r', fontweight='bold', fontsize=10)
    
    # Highlight Reduction Area
    # Fill between x=0 and x=dist_face
    x_fill = np.linspace(0, dist_face, 20)
    y_fill = -1 * (M_cl - (Vu_sup * x_fill - w_u * (x_fill**2) / 2.0))
    # We want to show the 'cut' from M_face level upwards? No, usually show the area under shear curve, but here showing delta M on Moment diagram
    # Let's highlight the difference vertical drop
    ax2.fill_between(x_fill, y_fill, -M_face, color='red', alpha=0.15)
    
    # Annotation arrow for reduction
    mid_x = dist_face / 2
    mid_y = (-M_cl + -M_face) / 2
    ax2.annotate(f"Reduction\n(Delta M)", xy=(mid_x, mid_y), xytext=(dist_face*2, mid_y),
                 arrowprops=dict(arrowstyle='->', color='r', lw=1.5), color='r', fontsize=9)

    ax2.set_xlim(0, plot_span)
    # Adjust Y lim to make graph look nice
    y_min = min(min(y_vals), -M_face)
    y_max = -M_cl + (M_cl * 0.1)
    ax2.set_ylim(y_min * 1.1, 0) # Negative moments usually plotted upwards in some regions, but here standard math plot (neg down)
    ax2.invert_yaxis() # Engineer convention: Negative Moment Up
    
    ax2.set_xlabel("Distance from Centerline (m)", fontsize=10)
    ax2.set_ylabel("Moment (kg-m)", fontsize=10)
    ax2.set_title("2. Moment Diagram", fontsize=11, fontweight='bold', loc='left')
    ax2.grid(True, linestyle=':', alpha=0.6)

    plt.tight_layout()
    return fig

def plot_strip_plan_simple(L1, L2):
    """
    แผนภาพ Strip Plan แบบเรียบง่าย (English Labels)
    """
    fig, ax = plt.subplots(figsize=(5, 3))
    # Slab Outline
    ax.add_patch(patches.Rectangle((0, 0), L1, L2, lw=2, ec='#34495e', fc='white'))
    
    # Strip Lines
    y1, y2 = L2/4, L2*3/4
    ax.axhline(y1, color='#3498db', ls='--', lw=1)
    ax.axhline(y2, color='#3498db', ls='--', lw=1)
    
    # Labels
    ax.text(L1/2, L2/8, "Column Strip (CS)", ha='center', va='center', color='#2980b9', fontsize=9, fontweight='bold')
    ax.text(L1/2, L2/2, "Middle Strip (MS)", ha='center', va='center', color='#2c3e50', fontsize=9, fontweight='bold')
    ax.text(L1/2, L2*7/8, "Column Strip (CS)", ha='center', va='center', color='#2980b9', fontsize=9, fontweight='bold')
    
    # Dimensions
    ax.annotate("", xy=(0, -0.1*L2), xytext=(L1, -0.1*L2), arrowprops=dict(arrowstyle='<->'))
    ax.text(L1/2, -0.2*L2, "L1 (Span)", ha='center', fontsize=9)
    
    ax.annotate("", xy=(-0.1*L1, 0), xytext=(-0.1*L1, L2), arrowprops=dict(arrowstyle='<->'))
    ax.text(-0.15*L1, L2/2, "L2 (Width)", va='center', rotation=90, fontsize=9)

    ax.set_xlim(-0.2*L1, L1+0.1*L1)
    ax.set_ylim(-0.25*L2, L2+0.1*L2)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title("Strip Layout Plan", fontsize=10, fontweight='bold')
    return fig

def plot_frame_model_compact(Ks, Kec, df_slab, df_col, col_type, L1_m):
    fig, ax = plt.subplots(figsize=(6, 2.0))
    joint_x = 0
    
    # Joint
    ax.plot(joint_x, 0, 'ko', markersize=8, zorder=5)
    
    # Beams
    if col_type == 'interior':
        ax.plot([-L1_m/3, joint_x], [0, 0], 'b-', lw=2)
        ax.text(-L1_m/6, 0.05, "Slab (Ks)", ha='center', color='b', fontsize=8)
    
    ax.plot([joint_x, L1_m/3], [0, 0], 'b-', lw=2)
    ax.text(L1_m/6, 0.05, "Slab (Ks)", ha='center', color='b', fontsize=8)

    # Column
    col_h = 0.6
    ax.plot([joint_x, joint_x], [0, -col_h], 'r-', lw=3)
    ax.text(joint_x + 0.05, -col_h/2, "Equiv. Col\n(Kec)", color='r', fontsize=8, va='center')
    
    # Support Symbol
    ax.plot([joint_x-0.15, joint_x+0.15], [-col_h, -col_h], 'k-', lw=2)
    for i in np.linspace(-0.15, 0.15, 5): 
        ax.plot([joint_x+i, joint_x+i-0.05], [-col_h, -col_h-0.05], 'k-', lw=1)

    # DF Arrows
    ax.annotate(f"DF_s={df_slab:.2f}", xy=(0.1, 0.01), xytext=(0.3, 0.2), 
                arrowprops=dict(arrowstyle="->", color='b'), color='b', fontsize=8)
    
    ax.annotate(f"DF_c={df_col:.2f}", xy=(0.01, -0.1), xytext=(0.2, -0.3), 
                arrowprops=dict(arrowstyle="->", color='r'), color='r', fontsize=8)

    ax.set_xlim(-L1_m/3 if col_type=='interior' else -0.1, L1_m/3)
    ax.set_ylim(-col_h - 0.1, 0.3)
    ax.axis('off')
    ax.set_title(f"Frame Model ({col_type.capitalize()})", fontsize=10, fontweight='bold')
    return fig

# --- Main Render Function ---

def render(c1_w, c2_w, L1, L2, lc, h_slab, fc, mat_props, w_u, col_type):
    st.header("3. Equivalent Frame Method (Visual Analysis)")
    st.info("💡 การวิเคราะห์โครงสร้างเสมือน (Advanced EFM) ตามมาตรฐาน ACI 318")
    st.markdown("---")

    # --- 0. Data Prep ---
    fy = mat_props['fy']
    Ec = 15100 * np.sqrt(fc)
    E_ksm = Ec * 10000
    L1_m, L2_m, lc_m = L1, L2, lc
    c1_cm, c2_cm, h_cm = c1_w, c2_w, h_slab
    c1_m = c1_cm/100.0
    
    Ic = (c2_cm/100) * ((c1_cm/100)**3) / 12.0
    Is = L2_m * ((h_cm/100)**3) / 12.0

    with st.expander("📋 Design Parameters (ข้อมูลออกแบบ)", expanded=False):
        st.write(f"- **Load:** $w_u = {w_u:,.2f}$ kg/m²")
        st.write(f"- **Geometry:** Span $L_1={L1_m}$ m, Width $L_2={L2_m}$ m")
        st.write(f"- **Member:** Column {c1_cm}x{c2_cm} cm, Slab $h={h_cm}$ cm")

    # =========================================================================
    # STEP 1: STIFFNESS
    # =========================================================================
    st.subheader("Step 1: Stiffness Analysis (หาค่าความแข็ง)")

    # 1.3 Torsion (Kt) - NEW DETAILED PLOT
    st.markdown("#### 1.3 Torsional Stiffness ($K_t$)")
    st.caption("พื้นที่หน้าตัดรับแรงบิด (Torsional Member) คือแถบพื้นข้างหัวเสา")
    
    # Show New Detailed Plot (English Labels to fix fonts)
    st.pyplot(plot_torsional_concept_detailed(c1_cm, c2_cm, h_cm), use_container_width=True)
    
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        st.markdown("**Dimensions:**")
        st.latex(f"x = h_{{slab}} = {h_cm} \\text{{ cm}}")
        st.latex(f"y \\approx c_1 = {c1_cm} \\text{{ cm}}")
    with col_t2:
        st.markdown("**Calculation:**")
        x, y = h_cm, c1_cm
        C_val = (1 - 0.63 * x / y) * (x**3 * y) / 3.0
        Kt = 9 * E_ksm * (C_val/1e8) / (L2_m * ((1 - (c2_cm/100)/L2_m)**3))
        st.latex(f"K_t = \\mathbf{{{Kt:,.2e}}}")

    # Other Stiffness (Compact view)
    st.markdown("---")
    Kc = 4 * E_ksm * Ic / lc_m; Sum_Kc = 2 * Kc
    Ks = 4 * E_ksm * Is / L1_m
    Kec = 1 / (1/Sum_Kc + 1/Kt) if Kt > 0 else Sum_Kc
    
    if col_type == 'edge': sum_k = Ks + Kec; df_slab = Ks/sum_k; df_col = Kec/sum_k
    else: sum_k = 2*Ks + Kec; df_slab = Ks/sum_k; df_col = Kec/sum_k

    col_df1, col_df2 = st.columns([1.2, 1])
    with col_df1:
        st.markdown("#### Summary ($K$ & $DF$)")
        st.write("ผลรวม Stiffness และการกระจายแรง:")
        st.latex(f"\\Sigma K_c = {Sum_Kc:,.2e}")
        st.latex(f"K_{{ec}} = \\mathbf{{{Kec:,.2e}}}")
        st.latex(f"DF_{{slab}} = \\mathbf{{{df_slab:.3f}}}")
    with col_df2:
        st.pyplot(plot_frame_model_compact(Ks, Kec, df_slab, df_col, col_type, L1_m), use_container_width=True)

    # =========================================================================
    # STEP 2 & 3: MOMENT DISTRIBUTION
    # =========================================================================
    st.markdown("---")
    st.subheader("Step 2 & 3: Moment Distribution")
    
    w_line = w_u * L2_m
    FEM_val = w_line * (L1_m**2) / 12.0
    
    if col_type == 'interior':
        Unbal = FEM_val - (0.5 * w_line * L1_m**2 / 12.0)
        Dist = -1 * Unbal * df_slab
        M_cl_neg = FEM_val + Dist
        data = [["FEM (Total Load)", f"{FEM_val:,.0f}"], ["FEM (Dead Load)", f"{(FEM_val*0.5):,.0f}"], ["Unbalanced", f"{Unbal:,.0f}"], ["Distribute", f"{Dist:,.0f}"], ["Final M_CL", f"**{M_cl_neg:,.0f}**"]]
    else:
        Unbal = FEM_val
        Dist = -1 * Unbal * df_slab
        M_cl_neg = FEM_val + Dist
        data = [["FEM (Fixed End)", f"{FEM_val:,.0f}"], ["Distribute", f"{Dist:,.0f}"], ["Final M_CL", f"**{M_cl_neg:,.0f}**"]]
        
    st.table(pd.DataFrame(data, columns=["Step", "Moment (kg-m)"]))

    # =========================================================================
    # STEP 4: FACE OF SUPPORT CORRECTION
    # =========================================================================
    st.markdown("---")
    st.subheader("Step 4: Face of Support Correction")
    st.caption("ลดค่าโมเมนต์จากกึ่งกลางเสา ($M_{CL}$) มาที่ขอบเสา ($M_{face}$) ตามแผนภาพ")

    # Calculation
    Vu_sup = w_line * L1_m / 2.0
    M_red = (Vu_sup * c1_m/2) - (w_line * (c1_m/2)**2 / 2.0)
    M_face = M_cl_neg - M_red
    
    # Show NEW DETAILED PLOT (English Labels)
    st.pyplot(plot_moment_reduction_detailed(M_cl_neg, M_face, c1_cm, L1_m, w_u, Vu_sup), use_container_width=True)
    
    st.latex(f"M_{{face}} = M_{{CL}} - \\Delta M = {M_cl_neg:,.0f} - {M_red:,.0f}")
    st.success(f"✅ **Design Negative Moment ($M_{{neg}}$): {M_face:,.0f} kg-m**")

    # =========================================================================
    # STEP 5: SUMMARY
    # =========================================================================
    st.markdown("---")
    st.subheader("Step 5: Design Moments Summary")
    
    M_simple = w_line * (L1_m**2) / 8.0
    M_pos = M_simple - (M_face if col_type=='interior' else (M_face+0)/2)
    
    col_s1, col_s2 = st.columns([1, 1.5])
    with col_s1:
        st.pyplot(plot_strip_plan_simple(L1_m, L2_m), use_container_width=True)
    with col_s2:
        if col_type == 'interior': pct = {'CS-':0.75, 'MS-':0.25, 'CS+':0.60, 'MS+':0.40}
        else: pct = {'CS-':1.00, 'MS-':0.00, 'CS+':0.60, 'MS+':0.40}
        
        data_res = {
            "Strip Type": ["Column Strip (CS)", "Middle Strip (MS)"],
            "M- (Design)": [f"**{M_face*pct['CS-']:,.0f}**", f"{M_face*pct['MS-']:,.0f}"],
            "M+ (Design)": [f"**{M_pos*pct['CS+']:,.0f}**", f"{M_pos*pct['MS+']:,.0f}"]
        }
        st.table(pd.DataFrame(data_res).set_index("Strip Type"))
