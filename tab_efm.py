import streamlit as st
import numpy as np
import pandas as pd
import math
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.gridspec import GridSpec

# Set Plot Style
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.size': 9,
    'axes.labelsize': 10,
    'axes.titlesize': 11,
    'lines.linewidth': 2
})

# --- Revised Visualization Functions (Clearer & Detailed) ---

def plot_torsional_concept_detailed(c1_cm, c2_cm, h_cm):
    """แสดงภาพ Concept Torsional Member แบบ Plan + Section"""
    fig = plt.figure(figsize=(8, 3.5))
    gs = GridSpec(1, 2, width_ratios=[1, 1.2])

    # --- Subplot 1: Plan View ---
    ax1 = fig.add_subplot(gs[0])
    
    # Slab area
    ax1.set_xlim(-c1_cm*1.5, c1_cm*1.5)
    ax1.set_ylim(-c2_cm*1.5, c2_cm*1.5)
    ax1.set_aspect('equal')
    
    # Column
    col_rect = patches.Rectangle((-c1_cm/2, -c2_cm/2), c1_cm, c2_cm, facecolor='#95a5a6', edgecolor='k', label='Column')
    ax1.add_patch(col_rect)
    
    # Torsional Members (Side strips)
    # Effective width y approx c1
    y_eff = c1_cm
    t_strip_left = patches.Rectangle((-c1_cm/2 - y_eff, -c2_cm/2), y_eff, c2_cm, facecolor='#e74c3c', alpha=0.4, hatch='///')
    t_strip_right = patches.Rectangle((c1_cm/2, -c2_cm/2), y_eff, c2_cm, facecolor='#e74c3c', alpha=0.4, hatch='///', label='Torsional Member')
    ax1.add_patch(t_strip_left)
    ax1.add_patch(t_strip_right)
    
    # Dimensions on Plan
    ax1.annotate("", xy=(-c1_cm/2, c2_cm/2 + 10), xytext=(c1_cm/2, c2_cm/2 + 10), arrowprops=dict(arrowstyle='<->', lw=1))
    ax1.text(0, c2_cm/2 + 15, f"c1 = {c1_cm:.0f}", ha='center', fontsize=9)
    
    ax1.annotate("", xy=(c1_cm/2, -c2_cm/2 - 10), xytext=(c1_cm/2 + y_eff, -c2_cm/2 - 10), arrowprops=dict(arrowstyle='<->', lw=1))
    ax1.text(c1_cm/2 + y_eff/2, -c2_cm/2 - 20, f"y \u2248 c1", ha='center', fontsize=9, color='#c0392b')

    ax1.axis('off')
    ax1.set_title("1. Plan View (มุมมองจากด้านบน)", fontsize=10)
    ax1.legend(loc='lower center', fontsize=8, frameon=True)

    # --- Subplot 2: Section View ---
    ax2 = fig.add_subplot(gs[1])
    
    # Cross section dimensions
    x_dim = h_cm
    y_dim = c1_cm
    
    ax2.set_xlim(-5, y_dim + 20)
    ax2.set_ylim(-5, x_dim + 10)
    ax2.set_aspect('equal')
    
    # Draw Cross Section Rectangle
    section_rect = patches.Rectangle((0, 0), y_dim, x_dim, facecolor='#e74c3c', alpha=0.6, edgecolor='k', hatch='///')
    ax2.add_patch(section_rect)
    
    # Dimension x (thickness)
    ax2.annotate("", xy=(y_dim + 5, 0), xytext=(y_dim + 5, x_dim), arrowprops=dict(arrowstyle='<->', lw=1))
    ax2.text(y_dim + 15, x_dim/2, f"x = h\n({h_cm:.0f} cm)", va='center', fontsize=9)
    
    # Dimension y (width)
    ax2.annotate("", xy=(0, -5), xytext=(y_dim, -5), arrowprops=dict(arrowstyle='<->', lw=1))
    ax2.text(y_dim/2, -15, f"y \u2248 c1 ({c1_cm:.0f} cm)", ha='center', fontsize=9)
    
    ax2.axis('off')
    ax2.set_title("2. Cross-Section A-A (หน้าตัดส่วนรับแรงบิด)", fontsize=10)
    
    plt.tight_layout()
    return fig

def plot_moment_reduction_detailed(M_cl, M_face, c1_cm, L1_m, w_u, Vu_sup):
    """แสดงกราฟลดค่าโมเมนต์แบบละเอียด (Physical + Moment Diagram)"""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7, 5), sharex=True, gridspec_kw={'height_ratios': [1, 1.5]})
    
    c1_m = c1_cm / 100.0
    dist_face = c1_m / 2.0
    plot_span = L1_m / 3.0
    
    # --- Subplot 1: Physical Model & Loading ---
    # Beam line
    ax1.plot([-dist_face*0.5, plot_span], [0, 0], 'k-', lw=3, color='#7f8c8d')
    
    # Support
    support_rect = patches.Rectangle((-dist_face, -0.2), c1_m, 0.4, facecolor='#bdc3c7', hatch='..')
    ax1.add_patch(support_rect)
    ax1.text(0, -0.3, "Column Support", ha='center', fontsize=9)
    
    # Centerline
    ax1.axvline(0, color='k', linestyle='-.', lw=1)
    ax1.text(0, 0.5, "Centerline\n(CL)", ha='center', fontsize=9)
    
    # Face of support line
    ax1.axvline(dist_face, color='r', linestyle='--', lw=1)
    ax1.text(dist_face, 0.3, "Face of\nSupport", ha='center', color='r', fontsize=9)
    
    # Load w_u (Arrows)
    for x in np.linspace(0, plot_span, 8):
        ax1.arrow(x, 0.8, 0, -0.6, head_width=0.05, head_length=0.1, fc='b', ec='b')
    ax1.text(plot_span/2, 0.9, f"Load $w_u = {w_u:,.0f}$ kg/m²", ha='center', color='b')
    
    # Shear Reaction Vu (Arrow)
    ax1.arrow(0, -0.8, 0, 0.6, head_width=0.08, head_length=0.15, fc='k', ec='k', lw=2)
    ax1.text(0.05, -0.7, f"Reaction Shear\n$V_u \\approx {Vu_sup:,.0f}$ kg", ha='left', fontsize=9)
    
    # Dimension distance
    ax1.annotate("", xy=(0, -0.1), xytext=(dist_face, -0.1), arrowprops=dict(arrowstyle='<->'))
    ax1.text(dist_face/2, -0.25, f"Dist = $c_1/2$\n({dist_face*100:.0f} cm)", ha='center', fontsize=9)

    ax1.set_ylim(-1, 1.2)
    ax1.axis('off')
    ax1.set_title("1. Physical Model & Loading (แบบจำลองและแรงกระทำ)", fontsize=10)

    # --- Subplot 2: Moment Diagram ---
    x_span_arr = np.linspace(0, plot_span, 100)
    # Parabolic approximation M(x) = M_cl - Vu*x + w*x^2/2
    # Simplified parabola fitting the two points for visualization
    y_mom = -M_cl * (1 - (x_span_arr / (L1_m*0.55))**2)

    # Plot Curve
    ax2.plot(x_span_arr, y_mom, 'b-', lw=2)
    
    # Critical lines corresponding to above
    ax2.axvline(0, color='k', linestyle='-.', lw=1)
    ax2.axvline(dist_face, color='r', linestyle='--', lw=1)
    
    # Points & Labels
    ax2.plot(0, -M_cl, 'ko', markersize=8)
    ax2.annotate(f"$M_{{CL}} = {M_cl:,.0f}$", xy=(0, -M_cl), xytext=(0.05, -M_cl), 
                 arrowprops=dict(arrowstyle='->'), ha='left', fontsize=10, fontweight='bold')
    
    ax2.plot(dist_face, -M_face, 'ro', markersize=8)
    ax2.annotate(f"$M_{{face}} = {M_face:,.0f}$", xy=(dist_face, -M_face), xytext=(dist_face + 0.05, -M_face*0.95), 
                 arrowprops=dict(arrowstyle='->', color='r'), ha='left', color='r', fontsize=10, fontweight='bold')

    # Highlight Reduction
    ax2.fill_between([0, dist_face], [-M_cl, -M_face], [-M_face, -M_face], color='red', alpha=0.2)
    
    mid_y = (-M_cl - M_face)/2
    ax2.annotate(f"Reduction $\\Delta M$\nเนื่องจากระยะ $c_1/2$", xy=(dist_face/2, mid_y), xytext=(dist_face*1.2, mid_y*1.1),
                 arrowprops=dict(arrowstyle='->', color='r'), color='r', fontsize=9)

    ax2.set_xlim(0, plot_span*0.8)
    ax2.set_ylim(min(y_mom)*1.05, 0)
    ax2.invert_yaxis()
    ax2.set_xlabel("Distance from Centerline (m)")
    ax2.set_ylabel("Negative Moment (kg-m)")
    ax2.set_title("2. Moment Diagram (แผนภาพโมเมนต์ดัด)", fontsize=10)
    ax2.grid(True, linestyle=':', alpha=0.5)

    plt.tight_layout()
    return fig

# --- Standard Compact Plots (Kept from previous version as they were okay) ---
def plot_frame_model_compact(Ks, Kec, df_slab, df_col, col_type, L1_m):
    fig, ax = plt.subplots(figsize=(6, 2.0))
    joint_x = 0
    ax.plot(joint_x, 0, 'ko', markersize=8, zorder=5)
    if col_type == 'interior':
        ax.plot([-L1_m/3, joint_x], [0, 0], 'b-', lw=2)
        ax.text(-L1_m/6, 0.05, "Slab ($K_s$)", ha='center', color='b', fontsize=8)
    ax.plot([joint_x, L1_m/3], [0, 0], 'b-', lw=2)
    ax.text(L1_m/6, 0.05, "Slab ($K_s$)", ha='center', color='b', fontsize=8)
    col_h = 0.6
    ax.plot([joint_x, joint_x], [0, -col_h], 'r-', lw=3)
    ax.text(joint_x + 0.05, -col_h/2, "Equiv. Col\n($K_{ec}$)", color='r', fontsize=8, va='center')
    ax.plot([joint_x-0.15, joint_x+0.15], [-col_h, -col_h], 'k-', lw=2)
    for i in np.linspace(-0.15, 0.15, 5): ax.plot([joint_x+i, joint_x+i-0.05], [-col_h, -col_h-0.05], 'k-', lw=1)
    ax.annotate(f"DF_s={df_slab:.2f}", xy=(0.1, 0.01), xytext=(0.3, 0.2), arrowprops=dict(arrowstyle="->", color='b'), color='b', fontsize=8)
    ax.annotate(f"DF_c={df_col:.2f}", xy=(0.01, -0.1), xytext=(0.2, -0.3), arrowprops=dict(arrowstyle="->", color='r'), color='r', fontsize=8)
    ax.set_xlim(-L1_m/3 if col_type=='interior' else -0.1, L1_m/3)
    ax.set_ylim(-col_h - 0.1, 0.3)
    ax.axis('off')
    ax.set_title(f"Frame Model ({col_type.capitalize()})", fontsize=10)
    return fig

def plot_strip_plan_simple(L1, L2):
    fig, ax = plt.subplots(figsize=(4, 2.5))
    ax.add_patch(patches.Rectangle((0, 0), L1, L2, lw=1.5, ec='#2c3e50', fc='none'))
    y1, y2 = L2/4, L2*3/4
    ax.axhline(y1, color='#3498db', ls='--', lw=1); ax.axhline(y2, color='#3498db', ls='--', lw=1)
    ax.text(L1/2, L2/8, "CS", ha='center', va='center', color='#2980b9', fontsize=9)
    ax.text(L1/2, L2/2, "Middle Strip (MS)", ha='center', va='center', color='#2c3e50', fontsize=9)
    ax.text(L1/2, L2*7/8, "CS", ha='center', va='center', color='#2980b9', fontsize=9)
    ax.annotate("", xy=(0, -0.1), xytext=(L1, -0.1), arrowprops=dict(arrowstyle='<->'))
    ax.text(L1/2, -0.3, f"$L_1$ (Span)", ha='center', fontsize=8)
    ax.annotate("", xy=(-0.1, 0), xytext=(-0.1, L2), arrowprops=dict(arrowstyle='<->'))
    ax.text(-0.3, L2/2, f"$L_2$ (Transverse)", va='center', rotation=90, fontsize=8)
    ax.set_xlim(-0.5, L1+0.5); ax.set_ylim(-0.5, L2+0.5); ax.set_aspect('equal'); ax.axis('off')
    ax.set_title("Strip Plan", fontsize=10)
    return fig

# --- Main Render Function ---

def render(c1_w, c2_w, L1, L2, lc, h_slab, fc, mat_props, w_u, col_type):
    st.header("3. Equivalent Frame Method (Detailed & Clear Visuals)")
    st.info("💡 แสดงการคำนวณละเอียดพร้อมภาพประกอบที่ปรับปรุงให้เข้าใจง่ายขึ้น")
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

    with st.expander("📋 Design Parameters", expanded=False):
        st.write(f"$w_u = {w_u}$ kg/m², $L_1={L1_m}$ m, $L_2={L2_m}$ m")
        st.write(f"Col {c1_cm}x{c2_cm} cm, Slab $h={h_cm}$ cm")

    # =========================================================================
    # STEP 1: STIFFNESS
    # =========================================================================
    st.subheader("Step 1: Stiffness Analysis")

    # 1.3 Torsion (Kt) - NEW DETAILED PLOT
    st.markdown("**1.3 Torsional Stiffness ($K_t$)**")
    st.caption("แสดงมิติของส่วนรับแรงบิด (Torsional Member) ทั้งในมุมมองแปลนและรูปตัด")
    # Show New Detailed Plot
    st.pyplot(plot_torsional_concept_detailed(c1_cm, c2_cm, h_cm), use_container_width=True)
    
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        st.write(f"**Dimensions:** $x=h={h_cm}$ cm, $y \\approx c_1={c1_cm}$ cm")
    with col_t2:
        x, y = h_cm, c1_cm
        C_val = (1 - 0.63 * x / y) * (x**3 * y) / 3.0
        Kt = 9 * E_ksm * (C_val/1e8) / (L2_m * ((1 - (c2_cm/100)/L2_m)**3))
        st.latex(f"K_t = \\frac{{9 E C}}{{L_2(1-c_2/L_2)^3}} = \\mathbf{{{Kt:,.2e}}}")

    # Other Stiffness (Compact view)
    st.markdown("---")
    Kc = 4 * E_ksm * Ic / lc_m; Sum_Kc = 2 * Kc
    Ks = 4 * E_ksm * Is / L1_m
    Kec = 1 / (1/Sum_Kc + 1/Kt) if Kt > 0 else Sum_Kc
    
    if col_type == 'edge': sum_k = Ks + Kec; df_slab = Ks/sum_k; df_col = Kec/sum_k
    else: sum_k = 2*Ks + Kec; df_slab = Ks/sum_k; df_col = Kec/sum_k

    col_df1, col_df2 = st.columns([1.2, 1])
    with col_df1:
        st.markdown("**Summary ($K$ & $DF$)**")
        st.latex(f"\\Sigma K_c = {Sum_Kc:,.2e}, K_s = {Ks:,.2e}")
        st.latex(f"K_{{ec}} = (\\Sigma K_c^{{-1}} + K_t^{{-1}})^{{-1}} = \\mathbf{{{Kec:,.2e}}}")
        st.latex(f"DF_{{slab}} = {df_slab:.3f}, DF_{{col}} = {df_col:.3f}")
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
        data = [["FEM (Total)", f"{FEM_val:,.0f}"], ["FEM (DL-Left)", f"{(FEM_val*0.5):,.0f}"], ["Unbalanced", f"{Unbal:,.0f}"], ["Distribute", f"{Dist:,.0f}"], ["Final M_CL", f"**{M_cl_neg:,.0f}**"]]
    else:
        Unbal = FEM_val
        Dist = -1 * Unbal * df_slab
        M_cl_neg = FEM_val + Dist
        data = [["FEM", f"{FEM_val:,.0f}"], ["Distribute", f"{Dist:,.0f}"], ["Final M_CL", f"**{M_cl_neg:,.0f}**"]]
        
    st.table(pd.DataFrame(data, columns=["Step", "Moment (kg-m)"]))

    # =========================================================================
    # STEP 4: FACE OF SUPPORT CORRECTION
    # =========================================================================
    st.markdown("---")
    st.subheader("Step 4: Face of Support Correction")
    st.caption("แสดงเหตุผลทางกายภาพที่ทำให้โมเมนต์ที่ขอบเสาลดลงจากกึ่งกลาง")

    # Calculation
    Vu_sup = w_line * L1_m / 2.0
    M_red = (Vu_sup * c1_m/2) - (w_line * (c1_m/2)**2 / 2.0)
    M_face = M_cl_neg - M_red
    
    # Show NEW DETAILED PLOT
    st.pyplot(plot_moment_reduction_detailed(M_cl_neg, M_face, c1_cm, L1_m, w_u, Vu_sup), use_container_width=True)
    
    st.write("**Calculation Detail:**")
    st.latex(f"M_{{face}} = M_{{CL}} - (V_u \\cdot \\frac{{c_1}}{{2}} - \\frac{{w (c_1/2)^2}}{{2}})")
    st.latex(f"M_{{face}} = {M_cl_neg:,.0f} - {M_red:,.0f} = \\mathbf{{{M_face:,.0f}}} \\text{{ kg-m}}")

    # =========================================================================
    # STEP 5: SUMMARY
    # =========================================================================
    st.markdown("---")
    st.subheader("Step 5: Design Moments Summary")
    
    M_simple = w_line * (L1_m**2) / 8.0
    M_pos = M_simple - (M_face if col_type=='interior' else (M_face+0)/2)
    
    col_s1, col_s2 = st.columns([1, 2])
    with col_s1:
        st.pyplot(plot_strip_plan_simple(L1_m, L2_m), use_container_width=True)
    with col_s2:
        if col_type == 'interior': pct = {'CS-':0.75, 'MS-':0.25, 'CS+':0.60, 'MS+':0.40}
        else: pct = {'CS-':1.00, 'MS-':0.00, 'CS+':0.60, 'MS+':0.40}
        
        data_res = {
            "Strip": ["Column Strip", "Middle Strip"],
            "M- (Design)": [f"**{M_face*pct['CS-']:,.0f}**", f"{M_face*pct['MS-']:,.0f}"],
            "M+ (Design)": [f"**{M_pos*pct['CS+']:,.0f}**", f"{M_pos*pct['MS+']:,.0f}"]
        }
        st.table(pd.DataFrame(data_res).set_index("Strip"))
