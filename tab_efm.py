import streamlit as st
import numpy as np
import pandas as pd
import math
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Set Plot Style
plt.style.use('seaborn-v0_8-whitegrid')

# --- Helper Functions for Visualization ---

def plot_torsional_member(c1, c2, h_slab):
    """แสดงภาพตัดขวางส่วนที่รับแรงบิด (Torsional Member)"""
    fig, ax = plt.subplots(figsize=(6, 3))
    
    # Draw Slab Section
    slab_rect = patches.Rectangle((-L2_cm/2, -h_slab), L2_cm, h_slab, linewidth=1, edgecolor='gray', facecolor='#e0e0e0', label='Slab')
    ax.add_patch(slab_rect)
    
    # Draw Column Section below slab
    col_rect = patches.Rectangle((-c2/2, -h_slab - 50), c2, 50, linewidth=2, edgecolor='black', facecolor='#7f8c8d', label='Column')
    ax.add_patch(col_rect)

    # Highlight Torsional Member adjacent to column
    # Dimension x (h_slab) and y (c1) - showing cross section transverse to L1
    t_width = c2 + 2*h_slab # Approx effective width for visual
    torsion_rect = patches.Rectangle((-t_width/2, -h_slab), t_width, h_slab, linewidth=2, edgecolor='#e74c3c', facecolor='none', linestyle='--', label='Torsional Member Region')
    ax.add_patch(torsion_rect)
    
    # Annotations
    ax.annotate(f'x = h = {h_slab} cm', xy=(c2/2 + h_slab/2, -h_slab/2), xytext=(c2/2 + h_slab + 20, -h_slab/2),
                arrowprops=dict(arrowstyle='->', lw=1.5))
    ax.text(0, -h_slab/2, f"Torsional Cross Section\n(Effective y approx. c1 = {c1} cm into page)", ha='center', va='center', fontsize=9)
    
    ax.set_xlim(-L2_cm/2 - 20, L2_cm/2 + 20)
    ax.set_ylim(-h_slab - 60, 10)
    ax.set_aspect('equal', adjustable='box')
    ax.axis('off')
    ax.legend(loc='upper right', fontsize=8)
    ax.set_title("Concept: Torsional Member Cross-Section", fontsize=10)
    return fig

def plot_frame_model(Ks, Kec, df_slab, df_col, col_type):
    """แสดงแผนภาพ Equivalent Frame (Stick Model) และการกระจายแรง"""
    fig, ax = plt.subplots(figsize=(8, 3))
    
    # Nodes
    joint_x = 0
    ax.plot(joint_x, 0, 'ks', markersize=10, label='Joint') # Main Joint
    
    # Members (Lines)
    # Slab Left
    if col_type == 'interior':
        ax.plot([-L1_cm, joint_x], [0, 0], 'b-', lw=3, label='Slab ($K_s$)')
        ax.text(-L1_cm/2, 10, f"$K_s = {Ks:.1e}$", ha='center', color='blue')
        
    # Slab Right
    ax.plot([joint_x, L1_cm], [0, 0], 'b-', lw=3)
    ax.text(L1_cm/2, 10, f"$K_s = {Ks:.1e}$", ha='center', color='blue')
    
    # Equivalent Column (Downwards)
    ax.plot([joint_x, joint_x], [0, -lc_cm*0.8], 'r-', lw=4, label='Equiv. Col ($K_{ec}$)')
    ax.text(joint_x + 10, -lc_cm/3, f"$K_{{ec}} = {Kec:.1e}$", color='red')

    # Supports
    ax.plot([-L1_cm, -L1_cm], [-20, 20], 'k-', lw=2) # Far end left
    ax.plot([L1_cm, L1_cm], [-20, 20], 'k-', lw=2)   # Far end right
    ax.plot([joint_x-20, joint_x+20], [-lc_cm*0.8, -lc_cm*0.8], 'k-', lw=2) # Col base

    # Distribution Arrows (Curved)
    # Arrow to Slab Right
    ax.annotate(f"DF={df_slab:.2f}", xy=(L1_cm/4, 5), xycoords='data',
                xytext=(20, 40), textcoords='offset points',
                arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=-.3", color='blue'), color='blue')
    
    # Arrow to Column
    ax.annotate(f"DF={df_col:.2f}", xy=(joint_x+5, -lc_cm/5), xycoords='data',
                xytext=(30, -30), textcoords='offset points',
                arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=.3", color='red'), color='red')

    ax.set_xlim(-L1_cm - 50 if col_type=='interior' else -50, L1_cm + 50)
    ax.set_ylim(-lc_cm, 60)
    ax.axis('off')
    ax.set_title(f"Equivalent Frame Model at {col_type.capitalize()} Joint", fontsize=11)
    ax.legend(loc='lower left', fontsize=8)
    return fig

def plot_moment_face_support(M_cl, M_face, c1, L1):
    """แสดงกราฟโมเมนต์และการลดค่าที่ขอบเสา"""
    fig, ax = plt.subplots(figsize=(6, 3.5))
    
    x = np.linspace(-L1_m/4, L1_m/4, 100) # Zoom in at support
    # Parabolic shape approx for negative moment region
    a = (M_cl) / (L1_m/2)**2 
    y_moment = -1 * (M_cl - a * x**2) # Inverted parabola peak at 0
    
    # Plot Moment Curve
    ax.plot(x, y_moment, 'b-', lw=2, label='Moment Diagram ($M(x)$)')
    
    # Centerline and Support Faces
    c1_m = c1 / 100.0
    ax.axvline(0, color='k', linestyle='--', lw=1, label='Centerline (CL)')
    ax.axvline(c1_m/2, color='r', linestyle='-', lw=2)
    ax.axvline(-c1_m/2, color='r', linestyle='-', lw=2, label='Face of Support')
    
    # Shade Column area
    ax.axvspan(-c1_m/2, c1_m/2, color='gray', alpha=0.3)
    
    # Annotate Points
    ax.plot(0, -M_cl, 'ko')
    ax.annotate(f'$M_{{CL}} = {M_cl:.0f}$', xy=(0, -M_cl), xytext=(0, -M_cl*1.2), ha='center', arrowprops=dict(arrowstyle='->'))
    
    ax.plot(c1_m/2, -M_face, 'ro')
    ax.annotate(f'$M_{{face}} = {M_face:.0f}$', xy=(c1_m/2, -M_face), xytext=(c1_m/2 + 0.5, -M_face*0.8), color='r', arrowprops=dict(arrowstyle='->', color='r'))

    # Fill reduction area (approx triangle for visual)
    ax.fill_between([0, c1_m/2], [-M_cl, -M_face], [-M_face, -M_face], color='red', alpha=0.2)
    ax.text(c1_m/4, -M_cl*0.9, "$\Delta M$ (Reduction)", color='r', fontsize=9, ha='center')

    ax.set_xlabel('Distance from Centerline (m)')
    ax.set_ylabel('Moment (kg-m)')
    ax.set_title("Critical Section: Face of Support Correction", fontsize=11)
    ax.invert_yaxis() # Moment diagram convention (neg up)
    ax.grid(True, which='both', linestyle='--')
    ax.legend()
    return fig

def plot_strip_plan(L1, L2, c1, c2):
    """แสดงแผนภาพแปลนพื้นและการแบ่ง Strip"""
    fig, ax = plt.subplots(figsize=(5, 4))
    
    # Slab Panel outline
    ax.add_patch(patches.Rectangle((0, 0), L1, L2, linewidth=2, edgecolor='black', facecolor='none'))
    
    # Column (Center)
    c1_m, c2_m = c1/100, c2/100
    ax.add_patch(patches.Rectangle((L1/2 - c1_m/2, L2/2 - c2_m/2), c1_m, c2_m, color='black'))
    
    # Strips Boundaries
    cs_width = L2 / 2.0
    ms_width = L2 / 2.0 # Total MS (L2/4 + L2/4)
    
    y1 = L2/4
    y2 = L2*3/4
    
    # Draw lines
    ax.axhline(y1, color='b', linestyle='--', lw=1)
    ax.axhline(y2, color='b', linestyle='--', lw=1)
    
    # Fill Areas
    # Middle Strip (Center)
    ax.axhspan(y1, y2, color='yellow', alpha=0.2, label='Middle Strip (MS)')
    # Column Strips (Edges in this view spanning L1)
    ax.axhspan(0, y1, color='blue', alpha=0.1, label='Column Strip (CS)')
    ax.axhspan(y2, L2, color='blue', alpha=0.1)
    
    # Dimension text
    ax.text(-0.5, L2/2, f"$L_2 = {L2}$ m", va='center', rotation=90)
    ax.text(L1/2, -0.5, f"$L_1 = {L1}$ m", ha='center')
    
    ax.text(L1*0.8, L2/2, f"MS Width\n{ms_width:.1f} m", ha='center', va='center', fontsize=9)
    ax.text(L1*0.8, L2*0.1, f"CS Width\n{cs_width/2:.1f} m", ha='center', va='center', fontsize=9, color='blue')

    ax.set_xlim(-1, L1+1)
    ax.set_ylim(-1, L2+1)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title("Plan View: Strip Definitions", fontsize=11)
    ax.legend(loc='upper right', fontsize=8)
    
    return fig

# --- Main Render Function ---

def render(c1_w, c2_w, L1, L2, lc, h_slab, fc, mat_props, w_u, col_type):
    global L1_m, L2_m, lc_m, c1_m, c2_m, h_m, L1_cm, L2_cm, lc_cm # Globals for plotting
    st.header("3. Equivalent Frame Method (Visual & Detailed)")
    st.info("💡 การวิเคราะห์โครงสร้างเสมือน พร้อมแผนภาพประกอบความเข้าใจในทุกขั้นตอน")
    st.markdown("---")

    # --- 0. เตรียมข้อมูล (Data Preparation) ---
    fy = mat_props['fy']
    Ec = 15100 * np.sqrt(fc)
    
    # Unit Conversion
    L1_m, L2_m, lc_m = L1, L2, lc
    c1_m, c2_m, h_m = c1_w/100.0, c2_w/100.0, h_slab/100.0
    L1_cm, L2_cm, lc_cm = L1*100, L2*100, lc*100
    
    # Moment of Inertia
    Ic = c2_m * (c1_m**3) / 12.0
    Is = L2_m * (h_m**3) / 12.0
    
    with st.expander("📋 ข้อมูลเริ่มต้น (Design Parameters)", expanded=False):
        c0a, c0b = st.columns(2)
        with c0a:
            st.write(f"**Material:** $f'_c={fc}$ ksc, $f_y={fy}$ ksc")
            st.write(f"**Modulus $E_c$:** {Ec:,.0f} ksc")
        with c0b:
            st.write(f"**Geometry:** $L_1\\times L_2 = {L1}\\times{L2}$ m")
            st.write(f"**Column:** $c_1\\times c_2 = {c1_w}\\times{c2_w}$ cm")
            st.write(f"**Slab:** $h = {h_slab}$ cm")

    # =========================================================================
    # STEP 1: STIFFNESS (K) & DISTRIBUTION FACTORS (DF)
    # =========================================================================
    st.subheader("Step 1: Stiffness Analysis (วิเคราะห์ความแข็ง)")
    st.markdown("หัวใจของ EFM คือการแปลงโครงสร้างจริง 3 มิติ ให้เป็น 'โครงสร้างเฟรมเสมือน 2 มิติ' โดยคำนึงถึงความแข็งของชิ้นส่วนต่างๆ")

    # 1.1 & 1.2 Column & Slab Stiffness
    st.markdown("##### 1.1 & 1.2 ความแข็งของเสา ($K_c$) และพื้น ($K_s$)")
    st.caption("คำนวณจากสูตรพื้นฐาน $K = 4EI/L$ (สมมติปลายยึดแน่น)")
    
    E_ksm = Ec * 10000 # แปลงหน่วย E เพื่อใช้กับหน่วยเมตรในการคำนวณ Relative K
    Kc = 4 * E_ksm * Ic / lc_m
    Sum_Kc = 2 * Kc # เสาบน + เสาล่าง
    Ks = 4 * E_ksm * Is / L1_m
    
    c1a, c1b = st.columns(2)
    with c1a: st.latex(f"K_c = \\frac{{4 E I_c}}{{l_c}} \\rightarrow \\Sigma K_c = {Sum_Kc:,.2e}")
    with c1b: st.latex(f"K_s = \\frac{{4 E I_s}}{{L_1}} = {Ks:,.2e}")

    # 1.3 Torsional Stiffness (Kt)
    st.markdown("##### 1.3 ความแข็งต่อการบิด ($K_t$)")
    st.markdown("""
    นี่คือส่วนที่ทำให้ EFM ต่างจากเฟรมปกติ พื้นคอนกรีตบริเวณรอบหัวเสาจะเกิดการ **บิดตัว (Torsion)** ทำให้การถ่ายโมเมนต์จากพื้นลงเสาไม่เต็ม 100% เสมือนว่ามีสปริงรับแรงบิดคั่นอยู่
    """)
    
    # Show Concept Diagram
    st.pyplot(plot_torsional_member(c1_w, c2_w, h_slab), use_container_width=True)
    
    x = h_slab
    y = c1_w
    st.write(f"**ตัวแปรหน้าตัดรับแรงบิด:** $x$ (ความหนาพื้น) = {x} cm, $y$ (ความกว้างประสิทธิผล $\\approx c_1$) = {y} cm")
    
    # Calculate C and Kt
    C_val = (1 - 0.63 * x / y) * (x**3 * y) / 3.0 # cm^4
    C_m4 = C_val / (100**4)
    term_denom = L2_m * ((1 - c2_m/L2_m)**3)
    if term_denom == 0: term_denom = 1e-9
    Kt = 9 * E_ksm * C_m4 / term_denom
    
    st.latex(f"K_t = \\frac{{9 E C}}{{L_2(1-c_2/L_2)^3}} = \\mathbf{{{Kt:,.2e}}}")

    # 1.4 Equivalent Column (Kec)
    st.markdown("##### 1.4 เสาเสมือน ($K_{ec}$)")
    st.caption("รวมความแข็งของเสาจริง ($\Sigma K_c$) และสปริงบิด ($K_t$) แบบอนุกรม")
    
    if Kt > 0:
        inv_Kec = (1/Sum_Kc) + (1/Kt)
        Kec = 1 / inv_Kec
        st.latex(r"\frac{1}{K_{ec}} = \frac{1}{\Sigma K_c} + \frac{1}{K_t} \implies K_{ec} = " + f"{Kec:,.2e}")
    else:
        Kec = Sum_Kc
        st.warning("Kt is zero, Kec = Sum Kc")

    # 1.5 Distribution Factors (DF)
    st.markdown("##### 1.5 อัตราส่วนการกระจายโมเมนต์ (DF)")
    st.caption("โมเมนต์ที่จุดต่อจะถูกแบ่งไปตามสัดส่วนความแข็งของสมาชิกที่มาต่อกัน ($DF = K_{member} / \Sigma K_{joint}$)")
    
    if col_type == 'edge':
        sum_k = Ks + Kec
        df_slab = Ks / sum_k; df_col = Kec / sum_k
    else:
        sum_k = 2*Ks + Kec # Assume symmetric
        df_slab = Ks / sum_k; df_col = Kec / sum_k

    # Show Frame Model Diagram with DF
    st.pyplot(plot_frame_model(Ks, Kec, df_slab, df_col, col_type), use_container_width=True)
    
    c1c, c1d = st.columns(2)
    c1c.metric("DF Slab (เข้าพื้น)", f"{df_slab:.3f}")
    c1d.metric("DF Column (ลงเสา)", f"{df_col:.3f}")

    # =========================================================================
    # STEP 2 & 3: MOMENT DISTRIBUTION
    # =========================================================================
    st.markdown("---")
    st.subheader("Step 2 & 3: Moment Distribution (การกระจายโมเมนต์)")
    st.markdown("""
    ใช้หลักการ **Hardy Cross Method** โดยเริ่มจากสมมติว่าจุดต่อยึดแน่น (Fixed) แล้วค่อยๆ ปล่อยให้โมเมนต์ถ่ายเทจนสมดุล
    * เราจะแสดงการคำนวณรอบแรก (Cycle 1) ให้เห็นภาพชัดเจน
    """)

    # 2.1 FEM
    w_line = w_u * L2_m
    FEM_val = w_line * (L1_m**2) / 12.0
    st.write("**1. Fixed-End Moment (FEM):** โมเมนต์เริ่มต้นถ้ายึดแน่น")
    st.latex(f"FEM = \\frac{{w L_2 L_1^2}}{{12}} = {FEM_val:,.0f} \\text{{ kg-m}}")

    # 2.2 Distribution Table (Simplified Cycle 1 for clarity)
    st.write("**2. ตารางการกระจายโมเมนต์ (Cycle 1 Demonstration):**")
    
    if col_type == 'interior':
        # Pattern Load Case for Interior
        st.caption("กรณีเสากลาง: พิจารณา Pattern Load (Span ซ้าย Dead Load, Span ขวา Full Load) เพื่อให้เกิด Unbalanced Moment")
        FEM_L = (0.5 * w_line * L1_m**2) / 12.0
        FEM_R = FEM_val
        Unbal = FEM_R - FEM_L
        Dist = -1 * Unbal * df_slab
        Final_M = FEM_R + Dist
        
        data_md = {
            "รายการ (Item)": ["FEM (Span ซ้าย - DL)", "FEM (Span ขวา - Total)", "Unbalanced Moment (ผลต่าง)", "Distribution (กระจายกลับ)", "Final Moment (M_CL)"],
            "ค่า (Value)": [f"{FEM_L:,.0f}", f"{FEM_R:,.0f}", f"{Unbal:,.0f}", f"{Dist:,.0f}", f"**{Final_M:,.0f}**"],
            "หมายเหตุ": ["สมมติ 50% Load", "100% Load", "ต้องกระจายออก", f"คูณ DF={df_slab:.2f}", "โมเมนต์ที่กึ่งกลางเสา"]
        }
        M_cl_neg = Final_M
    else:
        # Edge Case
        st.caption("กรณีเสาริม: Unbalanced Moment คือ FEM ทั้งหมด เพราะอีกฝั่งไม่มีพื้น")
        Unbal = FEM_val
        Dist_Slab = -1 * Unbal * df_slab
        Dist_Col = -1 * Unbal * df_col
        Final_M_Slab = FEM_val + Dist_Slab
        
        data_md = {
             "รายการ (Item)": ["FEM (Initial)", "Distribution to Slab", "Distribution to Col", "Final Slab Moment (M_CL)"],
             "ค่า (Value)": [f"{FEM_val:,.0f}", f"{Dist_Slab:,.0f}", f"{Dist_Col:,.0f}", f"**{Final_M_Slab:,.0f}**"],
             "หมายเหตุ": ["Unbalanced", f"คูณ DF={df_slab:.2f}", f"คูณ DF={df_col:.2f}", "โมเมนต์ที่กึ่งกลางเสา"]
        }
        M_cl_neg = Final_M_Slab

    st.table(pd.DataFrame(data_md))
    st.write(f"👉 **โมเมนต์ลบที่กึ่งกลางเสา ($M_{{CL}}$) = {M_cl_neg:,.0f} kg-m**")

    # =========================================================================
    # STEP 4: FACE OF SUPPORT CORRECTION
    # =========================================================================
    st.markdown("---")
    st.subheader("Step 4: Critical Section Correction (ปรับแก้ที่ขอบเสา)")
    st.markdown("""
    มาตรฐาน ACI อนุญาตให้ออกแบบปริมาณเหล็กเสริมโดยใช้ค่าโมเมนต์ที่ **ขอบเสา (Face of Support)** ซึ่งจะมีค่าน้อยกว่าที่กึ่งกลางเสา ($M_{CL}$) เสมอ
    """)

    # Calculation
    Vu_sup = w_line * L1_m / 2.0 # Approx Shear at support centerline
    c1_half = c1_m / 2.0
    # Reduction = Area of Shear diagram from CL to face = V_avg * distance
    # V_face = Vu_sup - w_line * c1_half
    # V_avg = (Vu_sup + V_face) / 2 = Vu_sup - w_line*c1_half/2
    # DeltaM = V_avg * c1_half = Vu_sup*c1_half - w_line*(c1_half^2)/2
    M_reduction = (Vu_sup * c1_half) - (w_line * c1_half**2 / 2.0)
    M_face_neg = M_cl_neg - M_reduction
    
    # Show Diagram
    st.pyplot(plot_moment_face_support(M_cl_neg, M_face_neg, c1_w, L1_m), use_container_width=True)
    
    st.write("**การคำนวณการลดค่าโมเมนต์ ($\Delta M$):**")
    c4a, c4b = st.columns(2)
    with c4a:
        st.latex(f"V_u \\approx w L_1 / 2 = {Vu_sup:,.0f} \\text{{ kg}}")
        st.latex(f"\\Delta M = V_u(c_1/2) - \\frac{{w(c_1/2)^2}}{{2}} = {M_reduction:,.0f} \\text{{ kg-m}}")
    with c4b:
        st.write("✅ **Negative Design Moment:**")
        st.latex(f"M_{{neg}} = M_{{CL}} - \\Delta M = {M_face_neg:,.0f} \\text{{ kg-m}}")

    # Positive Moment Calc
    M_simple = w_line * (L1_m**2) / 8.0
    if col_type == 'interior':
        M_pos_design = M_simple - M_face_neg # Simplified statics
    else:
        M_pos_design = M_simple - (M_face_neg + 0)/2.0 # Avg supports
        
    st.write("✅ **Positive Design Moment (Statics):**")
    st.latex(f"M_{{pos}} \\approx M_{{simple}} - M_{{neg,avg}} = {M_pos_design:,.0f} \\text{{ kg-m}}")

    # =========================================================================
    # STEP 5: STRIP DISTRIBUTION & SUMMARY
    # =========================================================================
    st.markdown("---")
    st.subheader("Step 5: Strip Distribution (แบ่งเข้าแถบพื้น)")
    st.markdown("ขั้นตอนสุดท้ายคือนำโมเมนต์ออกแบบ ($M_{neg}, M_{pos}$) มาแบ่งลงสู่ **Column Strip (CS)** และ **Middle Strip (MS)** ตามข้อกำหนดของ ACI")

    # Show Plan View Diagram
    st.pyplot(plot_strip_plan(L1_m, L2_m, c1_w, c2_w), use_container_width=True)

    # Define Percentages & Calculate
    if col_type == 'interior':
        pct = {'CS-':0.75, 'MS-':0.25, 'CS+':0.60, 'MS+':0.40}
    else:
        pct = {'CS-':1.00, 'MS-':0.00, 'CS+':0.60, 'MS+':0.40}
        
    res_data = {
        "Strip": ["Column Strip (CS)", "Middle Strip (MS)"],
        "Width (m)": [f"{L2_m/2:.2f}", f"{L2_m/2:.2f}"],
        "% M-": [f"{pct['CS-']*100:.0f}%", f"{pct['MS-']*100:.0f}%"],
        "M- (Design)": [f"**{M_face_neg*pct['CS-']:,.0f}**", f"{M_face_neg*pct['MS-']:,.0f}"],
        "% M+": [f"{pct['CS+']*100:.0f}%", f"{pct['MS+']*100:.0f}%"],
        "M+ (Design)": [f"**{M_pos_design*pct['CS+']:,.0f}**", f"{M_pos_design*pct['MS+']:,.0f}"]
    }
    
    st.write("### 📊 สรุปโมเมนต์สำหรับออกแบบ (Summary Table)")
    st.table(pd.DataFrame(res_data))
    st.success("นำค่าโมเมนต์ในช่อง **M- (Design)** และ **M+ (Design)** ไปคำนวณเหล็กเสริมในขั้นตอนต่อไป")
