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

# --- Visualization Functions ---

def plot_torsional_concept_final(c1_cm, c2_cm, h_cm, L1_m, L2_m, num_arms):
    """
    แสดงภาพ Torsional Member แบบมุมกว้าง + แสดงจำนวนแขน (Arms) ที่ถูกต้อง
    """
    fig = plt.figure(figsize=(10, 5))
    gs = GridSpec(1, 2, width_ratios=[1.2, 1])

    L1_cm = L1_m * 100
    L2_cm = L2_m * 100

    # --- Subplot 1: Plan View (Wider + Dynamic Arms) ---
    ax1 = fig.add_subplot(gs[0])

    # Plot limits
    plot_width = min(L1_cm, c1_cm * 6)
    plot_height = min(L2_cm, c2_cm * 6)
    ax1.set_xlim(-plot_width / 2, plot_width / 2)
    ax1.set_ylim(-plot_height / 2, plot_height / 2)
    ax1.set_aspect('equal')

    # 1. Slab Background
    ax1.add_patch(patches.Rectangle((-plot_width / 2, -plot_height / 2), plot_width, plot_height,
                                     facecolor='#f0f2f5', edgecolor='#bdc3c7', lw=1, zorder=0))

    # 2. Column (Center)
    col_rect = patches.Rectangle((-c1_cm / 2, -c2_cm / 2), c1_cm, c2_cm,
                                 facecolor='#95a5a6', edgecolor='k', lw=1.5, label='Column', zorder=5)
    ax1.add_patch(col_rect)

    # 3. Torsional Arms (Dynamic)
    y_eff = c1_cm
    
    # Right Arm (Always present in this view context mostly)
    # But let's assume if 1 arm (Corner), we show it on one side only.
    
    # Left Arm
    if num_arms == 2:
        t_strip_left = patches.Rectangle((-c1_cm / 2 - y_eff, -c2_cm / 2), y_eff, c2_cm,
                                         facecolor='#e74c3c', alpha=0.3, hatch='///', edgecolor='#c0392b')
        ax1.add_patch(t_strip_left)
    
    # Right Arm
    t_strip_right = patches.Rectangle((c1_cm / 2, -c2_cm / 2), y_eff, c2_cm,
                                      facecolor='#e74c3c', alpha=0.3, hatch='///', edgecolor='#c0392b',
                                      label='Torsional Member')
    ax1.add_patch(t_strip_right)

    # Labels based on arms
    if num_arms == 1:
        status_text = "Corner Column (1 Arm)"
    else:
        status_text = "Interior/Edge (2 Arms)"
        
    ax1.text(0, plot_height/2 * 0.9, status_text, ha='center', fontweight='bold', color='#c0392b', bbox=dict(facecolor='white', alpha=0.8, edgecolor='none'))

    # Dimensions
    # c1
    ax1.annotate("", xy=(-c1_cm / 2, c2_cm / 2 + 15), xytext=(c1_cm / 2, c2_cm / 2 + 15), arrowprops=dict(arrowstyle='<->', lw=1))
    ax1.text(0, c2_cm / 2 + 25, f"c1", ha='center', fontsize=9)

    # y (width)
    ax1.annotate("", xy=(c1_cm / 2, -c2_cm / 2 - 15), xytext=(c1_cm / 2 + y_eff, -c2_cm / 2 - 15),
                 arrowprops=dict(arrowstyle='<->', lw=1, color='#c0392b'))
    ax1.text(c1_cm / 2 + y_eff / 2, -c2_cm / 2 - 30, f"y ~ c1", ha='center', fontsize=9, color='#c0392b')

    ax1.axis('off')
    ax1.set_title("1. Plan View (Top Down)", fontsize=12, fontweight='bold')
    ax1.legend(loc='lower right', fontsize=8)

    # --- Subplot 2: Section View (Wider) ---
    ax2 = fig.add_subplot(gs[1])

    x_dim = h_cm
    y_dim = c1_cm
    section_width = y_dim * 3.5

    ax2.set_xlim(-section_width / 2, section_width / 2)
    ax2.set_ylim(-x_dim * 0.5, x_dim * 1.5)
    ax2.set_aspect('equal')

    # Slab
    ax2.add_patch(patches.Rectangle((-section_width / 2, 0), section_width, x_dim,
                                     facecolor='#f0f2f5', edgecolor='#bdc3c7', lw=1, zorder=0))

    # Torsional Section Highlight
    section_rect = patches.Rectangle((-y_dim / 2, 0), y_dim, x_dim,
                                     facecolor='#e74c3c', alpha=0.5, edgecolor='k', lw=1.5, hatch='///')
    ax2.add_patch(section_rect)
    
    # CL
    ax2.axvline(0, color='k', linestyle='-.', lw=1, alpha=0.5)

    # Dims
    ax2.text(y_dim / 2 + 10, x_dim / 2, f"x=h ({h_cm}cm)", va='center', fontsize=9)
    ax2.text(0, -x_dim * 0.3, f"y=c1 ({c1_cm}cm)", ha='center', fontsize=9)

    ax2.text(0, x_dim / 2, "Section A-A", ha='center', va='center', fontsize=9, color='white', fontweight='bold')

    ax2.axis('off')
    ax2.set_title("2. Section View (A-A)", fontsize=12, fontweight='bold')

    plt.tight_layout()
    return fig

def plot_moment_reduction_detailed(M_cl, M_face, c1_cm, L1_m, w_u, Vu_sup):
    """ แสดงกราฟลดค่าโมเมนต์แบบละเอียด (Physical + Diagram) """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6), sharex=True, gridspec_kw={'height_ratios': [1, 2], 'hspace': 0.1})
    
    c1_m = c1_cm / 100.0
    dist_face = c1_m / 2.0
    plot_span = L1_m * 0.35
    
    # --- Subplot 1: Physical ---
    ax1.plot([-dist_face*2, plot_span], [0, 0], 'k-', lw=4, color='#7f8c8d')
    support_rect = patches.Rectangle((-dist_face, -0.4), c1_m, 0.4, facecolor='#bdc3c7', hatch='..', edgecolor='k')
    ax1.add_patch(support_rect)
    ax1.axvline(0, color='k', linestyle='-.', lw=1, alpha=0.5)
    ax1.axvline(dist_face, color='r', linestyle='--', lw=1.5)
    
    # Arrows
    arrow_spacing = plot_span / 5
    for x in np.arange(0, plot_span, arrow_spacing):
        ax1.arrow(x, 0.8, 0, -0.5, head_width=0.02*L1_m, head_length=0.2, fc='blue', ec='blue')
    ax1.text(plot_span/2, 1.0, f"Load w_u", ha='center', color='blue', fontsize=9)
    
    ax1.text(0, 0.2, "CL", ha='center', fontweight='bold', fontsize=9)
    ax1.text(dist_face, 0.2, "Face", ha='center', color='r', fontweight='bold', fontsize=9)
    ax1.set_ylim(-1.2, 1.5); ax1.axis('off')
    ax1.set_title("1. Physical Model", fontsize=11, fontweight='bold', loc='left')

    # --- Subplot 2: Diagram ---
    x_vals = np.linspace(0, plot_span, 100)
    y_vals = -1 * (M_cl - (Vu_sup * x_vals - w_u * (x_vals**2) / 2.0))
    
    ax2.plot(x_vals, y_vals, color='blue', lw=2.5)
    ax2.axvline(0, color='k', linestyle='-.', lw=1, alpha=0.5)
    ax2.axvline(dist_face, color='r', linestyle='--', lw=1.5)
    
    ax2.plot(0, -M_cl, 'ko'); ax2.text(0.02*L1_m, -M_cl, f"M_CL = {M_cl:,.0f}", fontweight='bold')
    ax2.plot(dist_face, -M_face, 'ro'); ax2.text(dist_face + 0.02*L1_m, -M_face, f"M_face = {M_face:,.0f}", color='r', fontweight='bold')
    
    # Fill Reduction
    x_fill = np.linspace(0, dist_face, 20)
    y_fill = -1 * (M_cl - (Vu_sup * x_fill - w_u * (x_fill**2) / 2.0))
    ax2.fill_between(x_fill, y_fill, -M_face, color='red', alpha=0.15)
    
    ax2.annotate("Reduction", xy=(dist_face/2, (-M_cl-M_face)/2), xytext=(dist_face*2, (-M_cl-M_face)/2),
                 arrowprops=dict(arrowstyle='->', color='r'), color='r', fontsize=9)

    ax2.set_xlim(0, plot_span)
    ax2.set_ylim(min(y_vals)*1.1, 0)
    ax2.invert_yaxis()
    ax2.set_xlabel("Distance from CL (m)"); ax2.set_ylabel("Moment (kg-m)")
    ax2.set_title("2. Moment Diagram", fontsize=11, fontweight='bold', loc='left')

    plt.tight_layout()
    return fig

def plot_strip_plan_simple(L1, L2):
    fig, ax = plt.subplots(figsize=(5, 2.5))
    ax.add_patch(patches.Rectangle((0, 0), L1, L2, lw=2, ec='#34495e', fc='white'))
    y1, y2 = L2/4, L2*3/4
    ax.axhline(y1, color='#3498db', ls='--', lw=1); ax.axhline(y2, color='#3498db', ls='--', lw=1)
    ax.text(L1/2, L2/8, "Col Strip (CS)", ha='center', color='#2980b9', fontweight='bold', fontsize=9)
    ax.text(L1/2, L2/2, "Middle Strip (MS)", ha='center', color='#2c3e50', fontweight='bold', fontsize=9)
    ax.text(L1/2, L2*7/8, "Col Strip (CS)", ha='center', color='#2980b9', fontweight='bold', fontsize=9)
    ax.axis('off'); ax.set_title("Strip Layout", fontsize=10)
    return fig

def plot_frame_model_compact(Ks, Kec, df_slab, df_col, col_type, L1_m):
    fig, ax = plt.subplots(figsize=(6, 2.0))
    joint_x = 0
    ax.plot(joint_x, 0, 'ko', markersize=8)
    if col_type == 'interior':
        ax.plot([-L1_m/3, joint_x], [0, 0], 'b-', lw=2); ax.text(-L1_m/6, 0.05, "Slab", ha='center', color='b')
    ax.plot([joint_x, L1_m/3], [0, 0], 'b-', lw=2); ax.text(L1_m/6, 0.05, "Slab", ha='center', color='b')
    ax.plot([joint_x, joint_x], [0, -0.6], 'r-', lw=3); ax.text(joint_x+0.05, -0.3, "Col (Kec)", color='r')
    ax.plot([joint_x-0.15, joint_x+0.15], [-0.6, -0.6], 'k-', lw=2)
    ax.annotate(f"DFs={df_slab:.2f}", xy=(0.1, 0.01), xytext=(0.3, 0.2), arrowprops=dict(arrowstyle="->", color='b'), color='b')
    ax.annotate(f"DFc={df_col:.2f}", xy=(0.01, -0.1), xytext=(0.2, -0.3), arrowprops=dict(arrowstyle="->", color='r'), color='r')
    ax.axis('off'); ax.set_title(f"Frame Model ({col_type})", fontsize=10)
    return fig

# --- Main Render Function ---

def render(c1_w, c2_w, L1, L2, lc, h_slab, fc, mat_props, w_u, col_type):
    """
    Main EFM Calculation & Visualization
    """
    st.header("3. Equivalent Frame Method (Visual Analysis)")
    st.info("💡 การวิเคราะห์โครงสร้างเสมือนและตรวจสอบแรงบิด (Torsion)")
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

    # --- Determine Torsion Arms based on Column Type ---
    # ถ้าเป็น Corner Column คิดข้างเดียว, ถ้าเป็น Interior/Edge คิด 2 ข้าง
    if col_type.lower() == 'corner':
        num_arms = 1
        arm_desc = "1 Side (Corner Condition)"
    else:
        num_arms = 2
        arm_desc = "2 Sides (Interior/Edge Condition)"

    with st.expander("📋 Design Parameters", expanded=False):
        st.write(f"- Load: {w_u:,.0f} kg/m²")
        st.write(f"- Span: {L1_m} m x {L2_m} m")
        st.write(f"- Member: Col {c1_cm}x{c2_cm} cm, Slab {h_cm} cm")
        st.write(f"- **Torsion Check:** {col_type.capitalize()} Column -> {arm_desc}")

    # =========================================================================
    # STEP 1: STIFFNESS
    # =========================================================================
    st.subheader("Step 1: Stiffness Analysis")

    # 1.3 Torsion (Kt)
    st.markdown("#### 1.3 Torsional Stiffness ($K_t$)")
    
    # Visualization: Wider View + Correct Arm Logic
    st.pyplot(plot_torsional_concept_final(c1_cm, c2_cm, h_cm, L1_m, L2_m, num_arms), use_container_width=True)
    
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        st.write("**Cross-section (C):**")
        x, y = h_cm, c1_cm
        C_val = (1 - 0.63 * x / y) * (x**3 * y) / 3.0
        st.latex(f"C = {C_val:,.0f} \\text{{ cm}}^4")
    with col_t2:
        st.write("**Stiffness (Kt):**")
        # Kt for one arm
        Kt_one = 9 * E_ksm * (C_val/1e8) / (L2_m * ((1 - (c2_cm/100)/L2_m)**3))
        # Total Kt
        Kt_total = Kt_one * num_arms
        st.latex(f"K_{{t,total}} = {num_arms} \\times K_{{t,arm}}")
        st.latex(f"K_t = \\mathbf{{{Kt_total:,.2e}}}")

    st.markdown("---")
    
    # Other Stiffness
    Kc = 4 * E_ksm * Ic / lc_m; Sum_Kc = 2 * Kc
    Ks = 4 * E_ksm * Is / L1_m
    Kec = 1 / (1/Sum_Kc + 1/Kt_total) if Kt_total > 0 else Sum_Kc
    
    if col_type == 'edge': sum_k = Ks + Kec; df_slab = Ks/sum_k; df_col = Kec/sum_k
    else: sum_k = 2*Ks + Kec; df_slab = Ks/sum_k; df_col = Kec/sum_k # Interior

    col_df1, col_df2 = st.columns([1.2, 1])
    with col_df1:
        st.markdown("#### Summary ($K$ & $DF$)")
        st.latex(f"\\Sigma K_c = {Sum_Kc:,.2e}, K_s = {Ks:,.2e}")
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
        data = [["FEM (Total)", f"{FEM_val:,.0f}"], ["Unbalanced", f"{Unbal:,.0f}"], ["Distribute", f"{Dist:,.0f}"], ["Final M_CL", f"**{M_cl_neg:,.0f}**"]]
    else:
        Unbal = FEM_val
        Dist = -1 * Unbal * df_slab
        M_cl_neg = FEM_val + Dist
        data = [["FEM (Fixed)", f"{FEM_val:,.0f}"], ["Distribute", f"{Dist:,.0f}"], ["Final M_CL", f"**{M_cl_neg:,.0f}**"]]
        
    st.table(pd.DataFrame(data, columns=["Step", "Moment (kg-m)"]))

    # =========================================================================
    # STEP 4: FACE OF SUPPORT CORRECTION
    # =========================================================================
    st.markdown("---")
    st.subheader("Step 4: Face of Support Correction")
    
    Vu_sup = w_line * L1_m / 2.0
    M_red = (Vu_sup * c1_m/2) - (w_line * (c1_m/2)**2 / 2.0)
    M_face = M_cl_neg - M_red
    
    st.pyplot(plot_moment_reduction_detailed(M_cl_neg, M_face, c1_cm, L1_m, w_u, Vu_sup), use_container_width=True)
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
            "Strip Type": ["Column Strip", "Middle Strip"],
            "M- (Design)": [f"**{M_face*pct['CS-']:,.0f}**", f"{M_face*pct['MS-']:,.0f}"],
            "M+ (Design)": [f"**{M_pos*pct['CS+']:,.0f}**", f"{M_pos*pct['MS+']:,.0f}"]
        }
        st.table(pd.DataFrame(data_res).set_index("Strip Type"))
