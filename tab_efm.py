import streamlit as st
import numpy as np
import pandas as pd
import math
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Set Plot Style for cleaner look
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams.update({'font.size': 9, 'axes.labelsize': 10, 'axes.titlesize': 11})

# --- Helper Functions for Visualization (Revised for Clarity & Compactness) ---

def plot_torsional_concept_compact(c1_cm, c2_cm, h_cm):
    """แสดงภาพตัดขวางส่วนที่รับแรงบิดแบบกระชับ"""
    fig, ax = plt.subplots(figsize=(5, 2.5)) # Reduced size
    
    # Center line
    ax.axvline(0, color='k', linestyle='--', lw=0.8)
    
    # Column
    col_w = c2_cm
    ax.add_patch(patches.Rectangle((-col_w/2, -h_cm), col_w, h_cm, facecolor='#95a5a6', edgecolor='k', label='Column'))
    
    # Slab/Torsional Member
    # Show effective width y approx c1
    eff_y = c1_cm 
    ax.add_patch(patches.Rectangle((-col_w/2 - eff_y, -h_cm), eff_y, h_cm, facecolor='#e74c3c', alpha=0.3, edgecolor='#c0392b', hatch='///', label='Torsional Member'))
    ax.add_patch(patches.Rectangle((col_w/2, -h_cm), eff_y, h_cm, facecolor='#e74c3c', alpha=0.3, edgecolor='#c0392b', hatch='///'))

    # Dimension lines
    # Dimension x (thickness)
    ax.annotate("", xy=(-col_w/2 - eff_y - 5, -h_cm), xytext=(-col_w/2 - eff_y - 5, 0), arrowprops=dict(arrowstyle='<->', lw=1))
    ax.text(-col_w/2 - eff_y - 15, -h_cm/2, f"x = h\n({h_cm:.0f} cm)", va='center', ha='center', fontsize=8)
    
    # Dimension y (effective width)
    ax.annotate("", xy=(-col_w/2 - eff_y, h_cm*0.2), xytext=(-col_w/2, h_cm*0.2), arrowprops=dict(arrowstyle='<->', lw=1))
    ax.text(-col_w/2 - eff_y/2, h_cm*0.5, f"y \u2248 c1\n({c1_cm:.0f} cm)", ha='center', va='center', fontsize=8)

    ax.set_xlim(-col_w/2 - eff_y - 30, col_w/2 + eff_y + 10)
    ax.set_ylim(-h_cm - 10, h_cm + 10)
    ax.set_aspect('equal', adjustable='box')
    ax.axis('off')
    ax.set_title("Section: Torsional Member Dimensions ($x, y$)", fontsize=10, pad=2)
    # ax.legend(loc='upper right', fontsize=7)
    return fig

def plot_frame_model_compact(Ks, Kec, df_slab, df_col, col_type, L1_m):
    """แสดงแผนภาพ Stick Model แบบมาตรฐานวิศวกรรม"""
    fig, ax = plt.subplots(figsize=(6, 2.5)) # Compact size
    
    joint_x = 0
    # Main Joint
    ax.plot(joint_x, 0, 'ko', markersize=8, zorder=5)
    
    # Slab Members
    if col_type == 'interior':
        ax.plot([-L1_m/2, joint_x], [0, 0], 'b-', lw=2) # Slab Left (partial shown)
        ax.text(-L1_m/4, 0.1, "Slab ($K_s$)", ha='center', color='b', fontsize=8)
    
    ax.plot([joint_x, L1_m/2], [0, 0], 'b-', lw=2) # Slab Right (partial)
    ax.text(L1_m/4, 0.1, "Slab ($K_s$)", ha='center', color='b', fontsize=8)

    # Equivalent Column
    col_h = 0.8
    ax.plot([joint_x, joint_x], [0, -col_h], 'r-', lw=3)
    ax.text(joint_x + 0.1, -col_h/2, "Equiv. Col\n($K_{ec}$)", color='r', fontsize=8, va='center')

    # Supports (Standard Symbols)
    # Fixed support at column base
    ax.plot([joint_x-0.2, joint_x+0.2], [-col_h, -col_h], 'k-', lw=2)
    for i in np.linspace(-0.2, 0.2, 6):
        ax.plot([joint_x+i, joint_x+i-0.05], [-col_h, -col_h-0.05], 'k-', lw=1)

    # DF Arrows (Clearer)
    ax.annotate(f"DF_s={df_slab:.2f}", xy=(0.1, 0.02), xytext=(0.4, 0.3), 
                arrowprops=dict(arrowstyle="->", color='b', lw=1.5), color='b', fontsize=9, ha='center')
    
    ax.annotate(f"DF_c={df_col:.2f}", xy=(0.02, -0.1), xytext=(0.3, -0.4), 
                arrowprops=dict(arrowstyle="->", color='r', lw=1.5), color='r', fontsize=9, ha='center')

    ax.set_xlim(-L1_m/2 - 0.1 if col_type=='interior' else -0.2, L1_m/2 + 0.1)
    ax.set_ylim(-col_h - 0.2, 0.5)
    ax.axis('off')
    ax.set_title(f"Equivalent Frame Model ({col_type.capitalize()} Joint)", fontsize=10)
    return fig

def plot_moment_reduction_clear(M_cl, M_face, c1_cm, L1_m):
    """แสดงกราฟลดค่าโมเมนต์ที่เน้นความชัดเจน"""
    fig, ax = plt.subplots(figsize=(5, 3))
    
    c1_m = c1_cm / 100.0
    x_span = np.linspace(0, L1_m/2, 50)
    # Parabolic moment curve (approx)
    y_mom = -M_cl * (1 - (x_span / (L1_m*0.6))**2) 

    # Plot curve
    ax.plot(x_span, y_mom, 'b-', lw=2, alpha=0.6)
    
    # Critical lines
    ax.axvline(0, color='k', linestyle='--', label='Centerline')
    ax.axvline(c1_m/2, color='r', lw=2, label='Face of Support')
    
    # Points
    ax.plot(0, -M_cl, 'ko')
    ax.text(0.05, -M_cl*1.02, f"$M_{{CL}}$\n{M_cl:,.0f}", ha='left', va='top', fontsize=9)
    
    ax.plot(c1_m/2, -M_face, 'ro')
    ax.text(c1_m/2 + 0.05, -M_face*0.98, f"$M_{{face}}$\n{M_face:,.0f}", color='r', ha='left', va='bottom', fontsize=9)

    # Reduction Area (Highlight)
    ax.fill_between([0, c1_m/2], [-M_cl, -M_face], [-M_face, -M_face], color='red', alpha=0.2)
    
    # Annotation for Reduction
    mid_x = c1_m/4
    mid_y = (-M_cl - M_face)/2
    ax.annotate("Reduction\n$\\Delta M = V \cdot c_1/2$", xy=(mid_x, mid_y), xytext=(c1_m, mid_y*1.2),
                arrowprops=dict(arrowstyle='->', color='r'), color='r', fontsize=8)

    ax.set_xlim(-0.1, L1_m/3)
    ax.set_ylim(min(y_mom)*1.1, 0)
    ax.invert_yaxis()
    ax.set_xlabel("Distance from Centerline (m)", fontsize=8)
    ax.set_ylabel("Negative Moment (kg-m)", fontsize=8)
    ax.set_title("Moment Reduction at Support Face", fontsize=10)
    ax.grid(True, linestyle=':', alpha=0.5)
    return fig

def plot_strip_plan_simple(L1, L2):
    """แสดงแผนภาพ Strip แบบเรียบง่ายสะอาดตา"""
    fig, ax = plt.subplots(figsize=(4, 3))
    
    # Slab outline
    ax.add_patch(patches.Rectangle((0, 0), L1, L2, linewidth=2, edgecolor='#34495e', facecolor='none'))
    
    # Strip lines
    y1 = L2/4
    y2 = L2*3/4
    ax.axhline(y1, color='#3498db', linestyle='--', lw=1)
    ax.axhline(y2, color='#3498db', linestyle='--', lw=1)
    
    # Fill & Label
    ax.text(L1/2, L2/8, "Column Strip (CS)", ha='center', va='center', color='#2980b9', fontsize=9)
    ax.text(L1/2, L2/2, "Middle Strip (MS)", ha='center', va='center', color='#2c3e50', fontsize=9)
    ax.text(L1/2, L2*7/8, "Column Strip (CS)", ha='center', va='center', color='#2980b9', fontsize=9)
    
    # Dimensions
    ax.annotate("", xy=(0, -0.2), xytext=(L1, -0.2), arrowprops=dict(arrowstyle='<->', lw=1))
    ax.text(L1/2, -0.5, f"$L_1$ (Span Direction)", ha='center', fontsize=8)
    
    ax.annotate("", xy=(-0.2, 0), xytext=(-0.2, L2), arrowprops=dict(arrowstyle='<->', lw=1))
    ax.text(-0.5, L2/2, f"$L_2$ (Transverse)", va='center', rotation=90, fontsize=8)

    ax.set_xlim(-1, L1+0.5)
    ax.set_ylim(-1, L2+0.5)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title("Plan View: Strip Definitions", fontsize=10)
    return fig

# --- Main Render Function ---

def render(c1_w, c2_w, L1, L2, lc, h_slab, fc, mat_props, w_u, col_type):
    st.header("3. Equivalent Frame Method (Detailed & Visual)")
    st.info("💡 แสดงการคำนวณละเอียดตามมาตรฐาน ACI พร้อมภาพประกอบความเข้าใจ")
    st.markdown("---")

    # --- 0. Data Prep ---
    fy = mat_props['fy']
    Ec = 15100 * np.sqrt(fc)
    E_ksm = Ec * 10000 # kg/m^2
    
    # Dimensions
    L1_m, L2_m, lc_m = L1, L2, lc
    c1_cm, c2_cm, h_cm = c1_w, c2_w, h_slab
    c1_m = c1_cm/100.0
    
    # Inertia (m^4)
    Ic = (c2_cm/100) * ((c1_cm/100)**3) / 12.0
    Is = L2_m * ((h_cm/100)**3) / 12.0

    with st.expander("📋 Design Parameters (ข้อมูลเริ่มต้น)", expanded=False):
        st.write(f"Load $w_u = {w_u}$ kg/m², Span $L_1={L1_m}$ m, $L_2={L2_m}$ m")
        st.write(f"Column {c1_cm}x{c2_cm} cm, Slab $h={h_cm}$ cm")

    # =========================================================================
    # STEP 1: STIFFNESS & DF
    # =========================================================================
    st.subheader("Step 1: Stiffness ($K$) & Distribution Factors ($DF$)")
    st.markdown("คำนวณความแข็งของชิ้นส่วนต่างๆ เพื่อหาว่าโมเมนต์จะกระจายไปทางไหนมากที่สุด")

    # --- 1.1 & 1.2 Slab & Column ---
    Kc = 4 * E_ksm * Ic / lc_m
    Sum_Kc = 2 * Kc
    Ks = 4 * E_ksm * Is / L1_m
    
    col_k1, col_k2 = st.columns(2)
    col_k1.latex(f"\\Sigma K_c (Col) = \\frac{{4EI}}{{l}} \\times 2 = {Sum_Kc:,.2e}")
    col_k2.latex(f"K_s (Slab) = \\frac{{4EI}}{{L_1}} = {Ks:,.2e}")

    # --- 1.3 Torsion (Kt) ---
    st.markdown("---")
    col_t1, col_t2 = st.columns([1.5, 1])
    with col_t1:
        st.markdown("**1.3 Torsional Stiffness ($K_t$)**")
        st.caption("ความแข็งของพื้นส่วนที่รับแรงบิดรอบหัวเสา ($x, y$)")
        # Show Torsion Diagram (Compact)
        st.pyplot(plot_torsional_concept_compact(c1_cm, c2_cm, h_cm), use_container_width=True)
        
    with col_t2:
        st.write("Calculation:")
        x, y = h_cm, c1_cm
        C_val = (1 - 0.63 * x / y) * (x**3 * y) / 3.0 # cm^4
        Kt = 9 * E_ksm * (C_val/1e8) / (L2_m * ((1 - (c2_cm/100)/L2_m)**3))
        st.latex(f"C = {C_val:,.0f} \\text{{ cm}}^4")
        st.latex(f"K_t = \\mathbf{{{Kt:,.2e}}}")
        
    # --- 1.4 Equiv Col & 1.5 DF ---
    st.markdown("---")
    Kec = 1 / (1/Sum_Kc + 1/Kt) if Kt > 0 else Sum_Kc
    
    if col_type == 'edge': sum_k = Ks + Kec; df_slab = Ks/sum_k; df_col = Kec/sum_k
    else: sum_k = 2*Ks + Kec; df_slab = Ks/sum_k; df_col = Kec/sum_k

    col_df1, col_df2 = st.columns([1, 1.5])
    with col_df1:
        st.markdown("**1.4 Equivalent Column ($K_{ec}$)**")
        st.latex(f"K_{{ec}} = (K_c^{{-1}} + K_t^{{-1}})^{{-1}}")
        st.latex(f"K_{{ec}} = \\mathbf{{{Kec:,.2e}}}")
        st.markdown("**1.5 Distribution Factors (DF)**")
        st.latex(f"DF_{{slab}} = {df_slab:.3f}, DF_{{col}} = {df_col:.3f}")
        
    with col_df2:
        # Show Frame Model Diagram (Compact)
        st.pyplot(plot_frame_model_compact(Ks, Kec, df_slab, df_col, col_type, L1_m), use_container_width=True)

    # =========================================================================
    # STEP 2 & 3: MOMENT DISTRIBUTION
    # =========================================================================
    st.markdown("---")
    st.subheader("Step 2 & 3: Moment Distribution (กระจายโมเมนต์)")
    st.caption("ใช้ Hardy Cross Method กระจายโมเมนต์จาก FEM ตามสัดส่วน DF (แสดง Cycle 1)")

    # FEM
    w_line = w_u * L2_m
    FEM_val = w_line * (L1_m**2) / 12.0
    st.latex(f"FEM = w L_2 L_1^2 / 12 = {FEM_val:,.0f} \\text{{ kg-m}}")

    # Table
    if col_type == 'interior':
        Unbal = FEM_val - (0.5 * w_line * L1_m**2 / 12.0) # Pattern load approx
        Dist = -1 * Unbal * df_slab
        M_cl_neg = FEM_val + Dist
        data = [["FEM (Initial)", f"{FEM_val:,.0f}"], ["Unbalanced (Pattern)", f"{Unbal:,.0f}"], ["Distribute (x DF)", f"{Dist:,.0f}"], ["Final M_CL", f"**{M_cl_neg:,.0f}**"]]
    else:
        Unbal = FEM_val
        Dist = -1 * Unbal * df_slab
        M_cl_neg = FEM_val + Dist
        data = [["FEM (Unbalanced)", f"{FEM_val:,.0f}"], ["Distribute to Slab", f"{Dist:,.0f}"], ["Final M_CL", f"**{M_cl_neg:,.0f}**"]]
        
    st.table(pd.DataFrame(data, columns=["Step", "Moment (kg-m)"]))

    # =========================================================================
    # STEP 4: FACE OF SUPPORT CORRECTION
    # =========================================================================
    st.markdown("---")
    st.subheader("Step 4: Face of Support Correction (ปรับแก้ที่ขอบเสา)")
    
    col_red1, col_red2 = st.columns([1.5, 1])
    with col_red1:
        # Show Moment Reduction Diagram (Clearer)
        Vu_sup = w_line * L1_m / 2.0
        M_red = (Vu_sup * c1_m/2) - (w_line * (c1_m/2)**2 / 2.0)
        M_face = M_cl_neg - M_red
        st.pyplot(plot_moment_reduction_clear(M_cl_neg, M_face, c1_cm, L1_m), use_container_width=True)
        
    with col_red2:
        st.write("Calculation:")
        st.latex(f"V_u \\approx {Vu_sup:,.0f} \\text{{ kg}}")
        st.latex(f"\\Delta M (Red.) = {M_red:,.0f}")
        st.markdown(f"**Final Negative Moment:**")
        st.latex(f"M_{{face}} = M_{{CL}} - \\Delta M")
        st.latex(f"M_{{neg}} = \\mathbf{{{M_face:,.0f}}} \\text{{ kg-m}}")

    # Positive Moment
    M_simple = w_line * (L1_m**2) / 8.0
    M_pos = M_simple - (M_face if col_type=='interior' else (M_face+0)/2)
    st.write(f"**Final Positive Moment (Statics):** $M_{{pos}} = M_{{simple}} - M_{{neg,avg}} = \\mathbf{{{M_pos:,.0f}}}$ kg-m")

    # =========================================================================
    # STEP 5: STRIP DISTRIBUTION
    # =========================================================================
    st.markdown("---")
    st.subheader("Step 5: Strip Distribution (แบ่งเข้าแถบ)")
    
    col_str1, col_str2 = st.columns([1, 1.5])
    with col_str1:
        # Show Strip Plan (Simple)
        st.pyplot(plot_strip_plan_simple(L1_m, L2_m), use_container_width=True)
        
    with col_str2:
        if col_type == 'interior': pct = {'CS-':0.75, 'MS-':0.25, 'CS+':0.60, 'MS+':0.40}
        else: pct = {'CS-':1.00, 'MS-':0.00, 'CS+':0.60, 'MS+':0.40}
        
        data_res = {
            "Strip": ["Column Strip", "Middle Strip"],
            "M- Design": [f"**{M_face*pct['CS-']:,.0f}** ({pct['CS-']*100}%)", f"{M_face*pct['MS-']:,.0f} ({pct['MS-']*100}%)"],
            "M+ Design": [f"**{M_pos*pct['CS+']:,.0f}** ({pct['CS+']*100}%)", f"{M_pos*pct['MS+']:,.0f} ({pct['MS+']*100}%)"]
        }
        st.table(pd.DataFrame(data_res).set_index("Strip"))
        st.success("✅ ค่าในช่องตัวหนาคือโมเมนต์สำหรับออกแบบเหล็กเสริม")
