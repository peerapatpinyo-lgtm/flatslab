import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# --- Configuration & Style ---
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams.update({'font.size': 9, 'figure.titlesize': 11})

# --- Helper Functions for "Pro" Visualization ---

def draw_dim_line(ax, start, end, y_pos, text, color='black'):
    """Helper to draw dimension lines"""
    ax.annotate('', xy=(start, y_pos), xytext=(end, y_pos),
                arrowprops=dict(arrowstyle='<->', color=color, lw=1))
    ax.text((start+end)/2, y_pos + (0.05 if y_pos >=0 else -0.1), text, 
            ha='center', va='center', color=color, fontsize=8, backgroundcolor='white')

def plot_torsional_member_pro(c1, c2, h_slab, x, y):
    """
    Shows the Torsional Member Cross Section with clear highlighting of x and y
    """
    fig, ax = plt.subplots(figsize=(6, 3))
    
    # 1. Draw Slab Outline (Ghost)
    slab_width = c2 + 3*h_slab # Visual width
    ax.add_patch(patches.Rectangle((-slab_width/2, -h_slab), slab_width, h_slab, 
                                   linewidth=1, edgecolor='gray', facecolor='#f0f0f0', alpha=0.5, label='Slab'))
    
    # 2. Draw Column Below
    ax.add_patch(patches.Rectangle((-c2/2, -h_slab-40), c2, 40, 
                                   linewidth=1.5, edgecolor='#333', facecolor='#D3D3D3', hatch='///', label='Column'))

    # 3. Highlight Torsional Member Section (The "Beam" hidden in slab)
    # Effective section is x * y (Smallest dim * Largest dim)
    # Usually y = c1 (into page), x = h_slab
    # Here we draw the face: c2 width + flange
    
    # For visual representation of the "Cross Section" participating in torsion
    # We highlight the area adjacent to column
    ax.add_patch(patches.Rectangle((-c2/2, -h_slab), c2, h_slab, 
                                   linewidth=2, edgecolor='#E74C3C', facecolor='#E74C3C', alpha=0.2))
    ax.text(0, -h_slab/2, "Connection\nArea", ha='center', va='center', fontsize=8, color='#C0392B')

    # Dimensions
    draw_dim_line(ax, -slab_width/2, -c2/2, -h_slab - 5, "Slab Flange")
    draw_dim_line(ax, c2/2, slab_width/2, -h_slab - 5, "Slab Flange")
    
    # Annotations for C calculation
    ax.annotate(f'x = {x:.0f} cm (Slab Thickness)', xy=(slab_width/2, -h_slab/2), xytext=(slab_width/2 + 10, -h_slab/2),
                arrowprops=dict(arrowstyle='->', color='blue'), color='blue')
    
    ax.text(0, 5, f"Perpendicular Dimension (into page)\n y = c1 = {y:.0f} cm", ha='center', color='blue', fontweight='bold')

    ax.set_xlim(-slab_width/2 - 20, slab_width/2 + 50)
    ax.set_ylim(-h_slab - 50, 20)
    ax.set_aspect('equal', adjustable='box')
    ax.axis('off')
    ax.set_title(f"Torsional Member Constant (C) Parameters", loc='left', fontsize=10, fontweight='bold')
    return fig

def plot_frame_model_pro(Ks, Kec, Sum_Kc, Kt, df_slab, df_col, col_type, L1, lc):
    """
    Stick model showing the Spring (Kt) concept clearly
    """
    fig, ax = plt.subplots(figsize=(8, 3.5))
    
    joint_x = 0
    L_span = L1 * 100
    L_col = lc * 100
    
    # 1. Draw Slab (Beam Element)
    ax.plot([-L_span, 0], [0, 0], color='#2980B9', lw=4, solid_capstyle='round') # Left
    ax.plot([0, L_span], [0, 0], color='#2980B9', lw=4, solid_capstyle='round') # Right
    ax.text(L_span/2, 15, f"$K_{{slab}}$\n{Ks:.1e}", ha='center', color='#2980B9', fontweight='bold')

    # 2. Draw Column (Bottom) - Offset to show spring
    spring_h = L_col * 0.2
    col_h = L_col * 0.8
    
    # The Column Part
    ax.plot([0, 0], [-spring_h, -L_col], color='#2C3E50', lw=5, solid_capstyle='round')
    ax.text(10, -L_col/2, f"$\\Sigma K_c$\n{Sum_Kc:.1e}", ha='left', va='center', color='#2C3E50')

    # 3. The Torsional Spring (Kt) - ZigZag line
    n_zig = 4
    zig_h = spring_h / n_zig
    zig_w = 10
    path_x = [0]
    path_y = [0]
    for i in range(n_zig):
        path_x.extend([zig_w, -zig_w])
        y_step = -(i * zig_h) - (zig_h/2)
        path_y.extend([y_step, y_step - zig_h/2])
    path_x.append(0)
    path_y.append(-spring_h)
    
    ax.plot(path_x, path_y, color='#E67E22', lw=2) # Orange Spring
    ax.text(15, -spring_h/2, f"Torsional Spring\n$K_t = {Kt:.1e}$", color='#E67E22', fontsize=8)

    # 4. Equivalent Column Text
    ax.annotate(f"$K_{{ec}}$\n{Kec:.1e}", xy=(-5, -spring_h), xytext=(-60, -spring_h/2),
                arrowprops=dict(arrowstyle='->', connectionstyle="arc3,rad=0.2"),
                color='red', fontweight='bold', ha='center')

    # 5. Supports
    # Far ends
    ax.plot([-L_span, -L_span], [-10, 10], 'k-', lw=1)
    ax.plot([L_span, L_span], [-10, 10], 'k-', lw=1)
    # Base
    ax.plot([-20, 20], [-L_col, -L_col], 'k-', lw=2)
    for i in range(-20, 25, 5):
        ax.plot([i, i-5], [-L_col, -L_col-5], 'k-', lw=1)

    # 6. Distribution Factors Bubbles
    bbox_props = dict(boxstyle="round,pad=0.3", fc="white", ec="b", alpha=0.9)
    ax.text(L_span*0.15, 30, f"DF Slab\n{df_slab:.3f}", ha='center', color='#2980B9', bbox=bbox_props)
    
    bbox_props_c = dict(boxstyle="round,pad=0.3", fc="white", ec="r", alpha=0.9)
    ax.text(0, -L_col-30, f"DF Col\n{df_col:.3f}", ha='center', color='#C0392B', bbox=bbox_props_c)

    ax.set_xlim(-L_span * 0.5, L_span * 1.1)
    ax.set_ylim(-L_col - 40, 60)
    ax.axis('off')
    ax.set_title("Equivalent Frame Model (Spring Analogy)", loc='left', fontweight='bold')
    return fig

def plot_moment_reduction_pro(M_cl, M_face, c1_cm, L1_m):
    """
    Shows Moment Diagram with filled reduction area
    """
    fig, ax = plt.subplots(figsize=(6, 4))
    
    # Units
    c1_m = c1_cm / 100.0
    half_span = L1_m / 2.5 # Zoom in
    x = np.linspace(-half_span, half_span, 200)
    
    # Parabola: y = k*x^2 - M_cl
    # At x=0, y = -M_cl
    k = (M_cl * 0.5) / (half_span**2) # Arbitrary curvature for visual
    y = k * x**2 - M_cl
    
    # Plot Main Curve
    ax.plot(x, y, color='#2980B9', lw=2, label='Moment Diagram')
    
    # Support Lines
    face = c1_m / 2
    ax.axvline(0, color='black', linestyle='--', lw=1, alpha=0.5) # CL
    ax.axvline(face, color='#C0392B', linestyle='-', lw=1.5) # Face R
    ax.axvline(-face, color='#C0392B', linestyle='-', lw=1.5) # Face L
    
    # Highlight Support Width
    ax.axvspan(-face, face, color='#BDC3C7', alpha=0.3, label='Column Support')
    
    # Highlight Reduction Area (Fill between Curve and M_face level within support)
    # Visual trick: Fill the tip of parabola inside support
    mask = (x >= -face) & (x <= face)
    ax.fill_between(x[mask], y[mask], -M_face, color='#E74C3C', alpha=0.3, hatch='//', label='Reduction $\Delta M$')
    
    # M_face horizontal line marker
    ax.hlines(-M_face, -face*2, face*2, color='#C0392B', linestyle=':', lw=1.5)

    # Annotations
    ax.plot(0, -M_cl, 'ko', markersize=4)
    ax.text(0, -M_cl * 1.05, f"$M_{{CL}}$\n{M_cl:,.0f}", ha='center', va='top', fontweight='bold')
    
    ax.plot(face, -M_face, 'ro', markersize=4)
    ax.text(face, -M_face * 0.9, f"$M_{{face}}$\n{M_face:,.0f}", ha='left', va='bottom', color='#C0392B', fontweight='bold')

    ax.set_title("Critical Section Moment Correction", loc='left', fontweight='bold')
    ax.set_xlabel("Distance from Column Center (m)")
    ax.set_ylabel("Moment (kg-m)")
    ax.invert_yaxis()
    ax.legend(loc='lower right', fontsize=8)
    return fig

def plot_strips_pro(L1, L2, c1_cm, c2_cm):
    """
    Plan view showing strips with distinct coloring
    """
    fig, ax = plt.subplots(figsize=(6, 4))
    
    # Dimensions
    L1_draw = 8 # Scaled width for aspect ratio
    scale = L1_draw / L1
    L2_draw = L2 * scale
    c1 = (c1_cm/100) * scale
    c2 = (c2_cm/100) * scale
    
    # 1. Main Slab
    ax.add_patch(patches.Rectangle((0,0), L1_draw, L2_draw, edgecolor='black', facecolor='white', lw=2))
    
    # 2. Strips Boundaries
    y_q1 = L2_draw * 0.25
    y_q3 = L2_draw * 0.75
    
    # 3. Fill Middle Strip (Yellow)
    ax.add_patch(patches.Rectangle((0, y_q1), L1_draw, y_q3-y_q1, 
                                   facecolor='#F1C40F', alpha=0.3, edgecolor='none'))
    ax.text(L1_draw/2, L2_draw/2, "MIDDLE STRIP\n(MS)", ha='center', va='center', 
            fontweight='bold', color='#7F8C8D')

    # 4. Fill Column Strips (Blue)
    # Bottom CS
    ax.add_patch(patches.Rectangle((0, 0), L1_draw, y_q1, 
                                   facecolor='#3498DB', alpha=0.3, edgecolor='none'))
    # Top CS
    ax.add_patch(patches.Rectangle((0, y_q3), L1_draw, L2_draw-y_q3, 
                                   facecolor='#3498DB', alpha=0.3, edgecolor='none'))
    
    ax.text(L1_draw/2, y_q1/2, "COLUMN STRIP (CS)", ha='center', va='center', 
            fontweight='bold', color='#2980B9', fontsize=8)
    
    # 5. Column
    col_x = L1_draw/2 - c1/2
    col_y = L2_draw/2 - c2/2
    ax.add_patch(patches.Rectangle((col_x, col_y), c1, c2, facecolor='#2C3E50', edgecolor='black'))
    
    # 6. Dimensions
    # L2 side
    ax.annotate('', xy=(-0.5, 0), xytext=(-0.5, L2_draw), arrowprops=dict(arrowstyle='<->'))
    ax.text(-0.8, L2_draw/2, f"$L_2={L2}$ m", rotation=90, ha='center', va='center')
    
    # L1 side
    ax.annotate('', xy=(0, -0.5), xytext=(L1_draw, -0.5), arrowprops=dict(arrowstyle='<->'))
    ax.text(L1_draw/2, -0.8, f"$L_1={L1}$ m", ha='center', va='center')
    
    # Strip widths
    ax.text(L1_draw+0.2, L2_draw/2, f"{L2/2:.2f}m", va='center', fontsize=8)
    ax.text(L1_draw+0.2, y_q1/2, f"{L2/4:.2f}m", va='center', fontsize=8)

    ax.set_xlim(-1.5, L1_draw + 1)
    ax.set_ylim(-1.5, L2_draw + 1)
    ax.axis('off')
    ax.set_title("Design Strips Layout", loc='left', fontweight='bold')
    return fig

# --- Main Render Function ---

def render(c1_w, c2_w, L1, L2, lc, h_slab, fc, mat_props, w_u, col_type):
    st.header("3. Equivalent Frame Method (Step-by-Step)")
    st.markdown("---")

    # --- 0. Data Preparation ---
    fy = mat_props['fy']
    Ec = 15100 * np.sqrt(fc)
    
    # Unit Conversion for Calc
    L1_m, L2_m, lc_m = L1, L2, lc
    L1_cm, L2_cm, lc_cm = L1*100, L2*100, lc*100
    c1_cm, c2_cm = c1_w, c2_w
    h_m = h_slab / 100.0
    
    # Moment of Inertia
    Ic = (c2_cm/100) * ((c1_cm/100)**3) / 12.0
    Is = L2_m * (h_m**3) / 12.0
    
    # Display Inputs Summary
    with st.expander("Show Design Parameters", expanded=False):
        col_i1, col_i2 = st.columns(2)
        col_i1.write(f"**Concrete:** $f'_c={fc}$ ksc, $E_c={Ec:,.0f}$ ksc")
        col_i2.write(f"**Geometry:** $L_1={L1}$m, $L_2={L2}$m, $h={h_slab}$cm")

    # =========================================================================
    # STEP 1: STIFFNESS (K)
    # =========================================================================
    st.subheader("Step 1: Stiffness Analysis ($K$)")
    
    # 1.1 & 1.2 Basic Stiffness
    E_ksm = Ec * 10000 # Convert ksc to kg/m2 for relative stiffness consistency
    Kc = 4 * E_ksm * Ic / lc_m
    Sum_Kc = 2 * Kc # Above + Below
    Ks = 4 * E_ksm * Is / L1_m
    
    c1a, c1b = st.columns(2)
    with c1a: 
        st.info(f"**Column Stiffness ($K_c$)**\n\n$I_c = {Ic:.4f}$ $m^4$\n\n$\\Sigma K_c = {Sum_Kc:,.2e}$")
    with c1b: 
        st.info(f"**Slab Stiffness ($K_s$)**\n\n$I_s = {Is:.4f}$ $m^4$\n\n$K_s = {Ks:,.2e}$")

    # 1.3 Torsional Stiffness
    st.markdown("##### Torsional Member ($K_t$)")
    x = h_slab
    y = c1_w # Approx
    
    # Plot Torsion
    st.pyplot(plot_torsional_member_pro(c1_w, c2_w, h_slab, x, y), use_container_width=True)
    
    # Calc C
    C_val = (1 - 0.63 * x / y) * (x**3 * y) / 3.0 # cm^4
    C_m4 = C_val / (100**4)
    term_denom = L2_m * ((1 - (c2_cm/100)/L2_m)**3)
    if term_denom == 0: term_denom = 1e-9
    Kt = 9 * E_ksm * C_m4 / term_denom
    
    st.latex(r"K_t = \sum \frac{9 E C}{L_2(1-c_2/L_2)^3} = " + f"{Kt:,.2e}")

    # 1.4 Equivalent Column (Kec)
    st.markdown("##### Equivalent Stiffness ($K_{ec}$)")
    
    if Kt > 0:
        Kec = 1 / ((1/Sum_Kc) + (1/Kt))
    else:
        Kec = Sum_Kc
        
    # DF
    sum_k = Ks + Kec if col_type == 'edge' else 2*Ks + Kec
    df_slab = Ks / sum_k
    df_col = Kec / sum_k
    
    # Plot Stick Model
    col_md_txt, col_md_plot = st.columns([1, 2])
    with col_md_txt:
        st.markdown(f"""
        **ผลลัพธ์การคำนวณ:**
        
        $1/K_{{ec}} = 1/\\Sigma K_c + 1/K_t$
        
        **$K_{{ec}} = {Kec:,.2e}$**
        
        **Distribution Factors:**
        * Slab: **{df_slab:.3f}**
        * Column: **{df_col:.3f}**
        """)
    with col_md_plot:
        st.pyplot(plot_frame_model_pro(Ks, Kec, Sum_Kc, Kt, df_slab, df_col, col_type, L1, lc), use_container_width=True)

    # =========================================================================
    # STEP 2-4: MOMENT DISTRIBUTION & CORRECTION
    # =========================================================================
    st.markdown("---")
    st.subheader("Step 2-4: Moment Distribution & Correction")
    
    # Calc M_CL
    w_line = w_u * L2_m
    FEM = w_line * (L1_m**2) / 12.0
    
    # Simplified Moment Dist for display
    if col_type == 'interior':
        # Unbalanced from Pattern load assumption
        Unbal = FEM # Worst case assumption for demo
        Dist = -1 * Unbal * df_slab # Approx distribution
        M_cl_neg = FEM + abs(Dist) # Conservative total
    else:
        # Edge
        M_cl_neg = FEM - (FEM * df_slab) # Release to slab
        
    # Face Correction
    Vu = w_line * L1_m / 2.0
    c1_half_m = (c1_cm/100) / 2.0
    M_red = Vu * c1_half_m - (w_line * c1_half_m**2 / 2)
    M_face = M_cl_neg - M_red
    
    col_res_m1, col_res_m2 = st.columns([1, 1.5])
    
    with col_res_m1:
        st.write("###### Moment Calculation")
        st.write(f"1. **FEM:** {FEM:,.0f} kg-m")
        st.write(f"2. **$M_{{CL}}$:** {M_cl_neg:,.0f} kg-m (After DF)")
        st.write(f"3. **Reduction ($\Delta M$):** {M_red:,.0f} kg-m")
        st.success(f"**Design $M_{{neg}}$:** {M_face:,.0f} kg-m")
        
        # Positive M approx
        M_simple = w_line * L1_m**2 / 8
        M_pos = M_simple - M_face # Simplified
        st.success(f"**Design $M_{{pos}}$:** {M_pos:,.0f} kg-m")

    with col_res_m2:
        st.pyplot(plot_moment_reduction_pro(M_cl_neg, M_face, c1_cm, L1_m), use_container_width=True)

    # =========================================================================
    # STEP 5: STRIPS
    # =========================================================================
    st.markdown("---")
    st.subheader("Step 5: Design Strips Assignment")
    
    col_s1, col_s2 = st.columns([1.5, 1])
    
    with col_s1:
        st.pyplot(plot_strips_pro(L1, L2, c1_cm, c2_cm), use_container_width=True)
        
    with col_s2:
        st.write("###### % Moment Assignment (ACI)")
        if col_type == 'interior':
            data = {
                "Strip": ["Column Strip", "Middle Strip"],
                "Negative %": ["75%", "25%"],
                "Positive %": ["60%", "40%"]
            }
        else:
            data = {
                "Strip": ["Column Strip", "Middle Strip"],
                "Negative %": ["100%", "0%"],
                "Positive %": ["60%", "40%"]
            }
        st.table(pd.DataFrame(data))
        st.caption("นำ % เหล่านี้ไปคูณกับ Design M เพื่อหาปริมาณเหล็กเสริม")
