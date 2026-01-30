import streamlit as st
import numpy as np
import pandas as pd
import math
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.gridspec import GridSpec
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

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

def plot_torsional_concept_3d_isometric(col_type, c1_cm, c2_cm, h_cm, L1_m, L2_m):
    """
    สร้างภาพ 3D Isometric แสดง Torsional Member ตามประเภทเสา (Interior, Edge, Corner)
    คล้ายกับรูปภาพอ้างอิงที่ผู้ใช้ต้องการ
    """
    fig = plt.figure(figsize=(10, 6))
    ax = fig.add_subplot(111, projection='3d')

    # Dimensions for plotting
    L1_plot = L1_m * 100
    L2_plot = L2_m * 100
    c1_plot = c1_cm
    c2_plot = c2_cm
    h_plot = h_cm
    
    # Scaling for better visualization
    scale_factor = 0.1
    L1_plot *= scale_factor
    L2_plot *= scale_factor
    c1_plot *= scale_factor
    c2_plot *= scale_factor
    h_plot *= scale_factor
    
    # Define Slab and Column positions based on col_type
    if col_type == 'interior':
        col_x = 0
        col_y = 0
        slab_x_range = (-L1_plot/2, L1_plot/2)
        slab_y_range = (-L2_plot/2, L2_plot/2)
        title = "Interior Column"
        arms = 2
    elif col_type == 'edge':
        col_x = -L1_plot/2 + c1_plot/2
        col_y = 0
        slab_x_range = (-L1_plot/2, L1_plot/2)
        slab_y_range = (-L2_plot/2, L2_plot/2)
        title = "Edge Column"
        arms = 2
    elif col_type == 'corner':
        col_x = -L1_plot/2 + c1_plot/2
        col_y = -L2_plot/2 + c2_plot/2
        slab_x_range = (-L1_plot/2, L1_plot/2)
        slab_y_range = (-L2_plot/2, L2_plot/2)
        title = "Corner Column"
        arms = 1

    # --- Draw Slab (Grid) ---
    # Grid lines
    x = np.linspace(slab_x_range[0], slab_x_range[1], 10)
    y = np.linspace(slab_y_range[0], slab_y_range[1], 10)
    X, Y = np.meshgrid(x, y)
    Z = np.zeros_like(X)
    ax.plot_wireframe(X, Y, Z, color='gray', alpha=0.5, linewidth=0.5)
    
    # Slab Bottom Face for shading
    slab_verts = [
        [(slab_x_range[0], slab_y_range[0], 0), (slab_x_range[1], slab_y_range[0], 0),
         (slab_x_range[1], slab_y_range[1], 0), (slab_x_range[0], slab_y_range[1], 0)]
    ]
    slab_poly = Poly3DCollection(slab_verts, facecolor='#f0f2f5', edgecolor='gray', alpha=0.3)
    ax.add_collection3d(slab_poly)

    # --- Draw Column ---
    col_z_base = 0
    col_z_top = h_plot * 2 # Make column taller than slab
    
    col_verts = [
        # Bottom
        [(col_x-c1_plot/2, col_y-c2_plot/2, col_z_base), (col_x+c1_plot/2, col_y-c2_plot/2, col_z_base),
         (col_x+c1_plot/2, col_y+c2_plot/2, col_z_base), (col_x-c1_plot/2, col_y+c2_plot/2, col_z_base)],
        # Top
        [(col_x-c1_plot/2, col_y-c2_plot/2, col_z_top), (col_x+c1_plot/2, col_y-c2_plot/2, col_z_top),
         (col_x+c1_plot/2, col_y+c2_plot/2, col_z_top), (col_x-c1_plot/2, col_y+c2_plot/2, col_z_top)],
        # Sides
        [(col_x-c1_plot/2, col_y-c2_plot/2, col_z_base), (col_x+c1_plot/2, col_y-c2_plot/2, col_z_base),
         (col_x+c1_plot/2, col_y-c2_plot/2, col_z_top), (col_x-c1_plot/2, col_y-c2_plot/2, col_z_top)],
        
        [(col_x+c1_plot/2, col_y-c2_plot/2, col_z_base), (col_x+c1_plot/2, col_y+c2_plot/2, col_z_base),
         (col_x+c1_plot/2, col_y+c2_plot/2, col_z_top), (col_x+c1_plot/2, col_y-c2_plot/2, col_z_top)],
        
        [(col_x+c1_plot/2, col_y+c2_plot/2, col_z_base), (col_x-c1_plot/2, col_y+c2_plot/2, col_z_base),
         (col_x-c1_plot/2, col_y+c2_plot/2, col_z_top), (col_x+c1_plot/2, col_y+c2_plot/2, col_z_top)],
        
        [(col_x-c1_plot/2, col_y+c2_plot/2, col_z_base), (col_x-c1_plot/2, col_y-c2_plot/2, col_z_base),
         (col_x-c1_plot/2, col_y-c2_plot/2, col_z_top), (col_x-c1_plot/2, col_y+c2_plot/2, col_z_top)],
    ]
    col_poly = Poly3DCollection(col_verts, facecolor='#95a5a6', edgecolor='k', alpha=0.8)
    ax.add_collection3d(col_poly)

    # --- Draw Torsional Members (Red, Hatched) ---
    arm_width = c1_plot # Effective width y approx c1
    arm_height = h_plot # Thickness x = h
    
    torsion_verts = []
    
    # Right Arm (+y direction)
    if col_type in ['interior', 'edge', 'corner']:
        # Define arm geometry
        y_start = col_y + c2_plot/2
        y_end = slab_y_range[1]
        x_start = col_x - arm_width/2
        x_end = col_x + arm_width/2
        
        arm_verts = [
            [(x_start, y_start, 0), (x_end, y_start, 0), (x_end, y_end, 0), (x_start, y_end, 0)], # Bottom
            [(x_start, y_start, arm_height), (x_end, y_start, arm_height), (x_end, y_end, arm_height), (x_start, y_end, arm_height)], # Top
            [(x_start, y_start, 0), (x_end, y_start, 0), (x_end, y_start, arm_height), (x_start, y_start, arm_height)], # Front
            [(x_end, y_end, 0), (x_start, y_end, 0), (x_start, y_end, arm_height), (x_end, y_end, arm_height)], # Back
            [(x_start, y_end, 0), (x_start, y_start, 0), (x_start, y_start, arm_height), (x_start, y_end, arm_height)], # Left
            [(x_end, y_start, 0), (x_end, y_end, 0), (x_end, y_end, arm_height), (x_end, y_start, arm_height)], # Right
        ]
        torsion_verts.extend(arm_verts)

    # Left Arm (-y direction)
    if col_type in ['interior', 'edge']:
        y_start = slab_y_range[0]
        y_end = col_y - c2_plot/2
        x_start = col_x - arm_width/2
        x_end = col_x + arm_width/2
        
        arm_verts = [
            [(x_start, y_start, 0), (x_end, y_start, 0), (x_end, y_end, 0), (x_start, y_end, 0)], # Bottom
            [(x_start, y_start, arm_height), (x_end, y_start, arm_height), (x_end, y_end, arm_height), (x_start, y_end, arm_height)], # Top
            [(x_start, y_start, 0), (x_end, y_start, 0), (x_end, y_start, arm_height), (x_start, y_start, arm_height)], # Front
            [(x_end, y_end, 0), (x_start, y_end, 0), (x_start, y_end, arm_height), (x_end, y_end, arm_height)], # Back
            [(x_start, y_end, 0), (x_start, y_start, 0), (x_start, y_start, arm_height), (x_start, y_end, arm_height)], # Left
            [(x_end, y_start, 0), (x_end, y_end, 0), (x_end, y_end, arm_height), (x_end, y_start, arm_height)], # Right
        ]
        torsion_verts.extend(arm_verts)
        
    if torsion_verts:
        # Create Poly3DCollection for torsional members
        # Note: Hatching in 3D is not directly supported in the same way as 2D patches.
        # We use color and alpha to represent it.
        torsion_poly = Poly3DCollection(torsion_verts, facecolor='#e74c3c', edgecolor='#c0392b', alpha=0.4)
        ax.add_collection3d(torsion_poly)

    # --- Labels & Dimensions ---
    # Title
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    
    # Torsional Member Label
    label_x = col_x + c1_plot
    label_y = col_y + c2_plot + L2_plot*0.1
    label_z = h_plot * 1.5
    
    if col_type == 'corner':
        label_text = "Torsional Member (1 Arm)"
    else:
        label_text = "Torsional Member (2 Arms)"
        
    ax.text(label_x, label_y, label_z, label_text, color='#c0392b', fontweight='bold')
    
    # Draw arrow to Torsional Member
    if col_type != 'corner' or (col_type == 'corner' and arms > 0):
        arrow_start = (label_x, label_y, label_z)
        arrow_end = (col_x, col_y + c2_plot, h_plot/2)
        ax.quiver(arrow_start[0], arrow_start[1], arrow_start[2], 
                  arrow_end[0]-arrow_start[0], arrow_end[1]-arrow_start[1], arrow_end[2]-arrow_start[2],
                  color='#c0392b', arrow_length_ratio=0.1, lw=1.5)

    # c1 Dimension
    dim_y = slab_y_range[1] + L2_plot*0.1
    dim_z = 0
    
    ax.plot([col_x-c1_plot/2, col_x+c1_plot/2], [dim_y, dim_y], [dim_z, dim_z], color='k', lw=1) # Main line
    ax.plot([col_x-c1_plot/2, col_x-c1_plot/2], [dim_y-L2_plot*0.02, dim_y+L2_plot*0.02], [dim_z, dim_z], color='k', lw=1) # Tick left
    ax.plot([col_x+c1_plot/2, col_x+c1_plot/2], [dim_y-L2_plot*0.02, dim_y+L2_plot*0.02], [dim_z, dim_z], color='k', lw=1) # Tick right
    ax.text(col_x, dim_y + L2_plot*0.05, dim_z, "c1", ha='center')

    # --- Final Plot Adjustments ---
    ax.set_xlim(slab_x_range[0]*1.2, slab_x_range[1]*1.2)
    ax.set_ylim(slab_y_range[0]*1.2, slab_y_range[1]*1.2)
    ax.set_zlim(0, h_plot*3)
    ax.set_box_aspect((4, 4, 1)) # Adjust aspect ratio for isometric-like view
    ax.view_init(elev=30, azim=-60) # Isometric view
    ax.set_axis_off() # Hide axes
    
    return fig

# --- Main Render Function ---

def render(c1_w, c2_w, L1, L2, lc, h_slab, fc, mat_props, w_u, col_type):
    """
    Main EFM Calculation & Visualization
    """
    st.header("3. Equivalent Frame Method (Visual Analysis)")
    st.info("💡 การวิเคราะห์โครงสร้างเสมือนและตรวจสอบแรงบิด (Torsion) ด้วยภาพ 3D")
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
    st.markdown("#### 1.3 Torsional Stiffness ($K_t$) - 3D Visual Concept")
    st.caption("แสดงพื้นที่หน้าตัดรับแรงบิด (Torsional Member) ในรูปแบบ 3D Isometric")
    
    # Visualization: 3D Isometric Views for all three types
    st.pyplot(plot_torsional_concept_3d_isometric('interior', c1_cm, c2_cm, h_cm, L1_m, L2_m), use_container_width=True)
    st.pyplot(plot_torsional_concept_3d_isometric('edge', c1_cm, c2_cm, h_cm, L1_m, L2_m), use_container_width=True)
    st.pyplot(plot_torsional_concept_3d_isometric('corner', c1_cm, c2_cm, h_cm, L1_m, L2_m), use_container_width=True)
    
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        st.write("**Cross-section (C):**")
        x, y = h_cm, c1_cm
        C_val = (1 - 0.63 * x / y) * (x**3 * y) / 3.0
        st.latex(f"C = {C_val:,.0f} \\text{{ cm}}^4")
    with col_t2:
        st.write("**Stiffness (Kt) for current selection:**")
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
    # with col_df2:
    #     st.pyplot(plot_frame_model_compact(Ks, Kec, df_slab, df_col, col_type, L1_m), use_container_width=True)

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
    
    # st.pyplot(plot_moment_reduction_detailed(M_cl_neg, M_face, c1_cm, L1_m, w_u, Vu_sup), use_container_width=True)
    st.success(f"✅ **Design Negative Moment ($M_{{neg}}$): {M_face:,.0f} kg-m**")

    # =========================================================================
    # STEP 5: SUMMARY
    # =========================================================================
    st.markdown("---")
    st.subheader("Step 5: Design Moments Summary")
    
    M_simple = w_line * (L1_m**2) / 8.0
    M_pos = M_simple - (M_face if col_type=='interior' else (M_face+0)/2)
    
    col_s1, col_s2 = st.columns([1, 1.5])
    # with col_s1:
    #     st.pyplot(plot_strip_plan_simple(L1_m, L2_m), use_container_width=True)
    with col_s2:
        if col_type == 'interior': pct = {'CS-':0.75, 'MS-':0.25, 'CS+':0.60, 'MS+':0.40}
        else: pct = {'CS-':1.00, 'MS-':0.00, 'CS+':0.60, 'MS+':0.40}
        
        data_res = {
            "Strip Type": ["Column Strip", "Middle Strip"],
            "M- (Design)": [f"**{M_face*pct['CS-']:,.0f}**", f"{M_face*pct['MS-']:,.0f}"],
            "M+ (Design)": [f"**{M_pos*pct['CS+']:,.0f}**", f"{M_pos*pct['MS+']:,.0f}"]
        }
        st.table(pd.DataFrame(data_res).set_index("Strip Type"))
