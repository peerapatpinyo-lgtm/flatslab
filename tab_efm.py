import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.gridspec import GridSpec

# Set Plot Style
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams.update({'font.family': 'sans-serif', 'font.size': 10})

# --- Helper Functions ---

def plot_torsional_arms_dynamic(c1_cm, c2_cm, h_cm, col_location):
    """
    แสดงภาพ Torsional Member ตามตำแหน่งเสา (มีแขน 1 ข้าง หรือ 2 ข้าง)
    """
    fig = plt.figure(figsize=(8, 4))
    gs = GridSpec(1, 2, width_ratios=[1.2, 1])

    # --- 1. PLAN VIEW ---
    ax1 = fig.add_subplot(gs[0])
    limit = max(c1_cm, c2_cm) * 3
    ax1.set_xlim(-limit, limit)
    ax1.set_ylim(-limit, limit)
    ax1.set_aspect('equal')

    # Draw Column
    ax1.add_patch(patches.Rectangle((-c1_cm/2, -c2_cm/2), c1_cm, c2_cm, facecolor='#95a5a6', edgecolor='k', zorder=5, label='Column'))

    # Configuration for Arms
    y_eff = c1_cm
    
    # Logic: Determine Arms based on location
    has_left_arm = True
    has_right_arm = True
    
    if col_location == 'Corner (เสาเข้ามุม)':
        # สมมติเป็นมุมซ้ายบน -> มีแขนขวาอย่างเดียว (ในบริบทนี้)
        has_left_arm = False
        desc = "1 Arm (One Side)"
    else:
        # Interior or Edge (Normal case)
        desc = "2 Arms (Both Sides)"

    # Draw Left Arm
    if has_left_arm:
        ax1.add_patch(patches.Rectangle((-c1_cm/2 - y_eff, -c2_cm/2), y_eff, c2_cm, 
                                        facecolor='#e74c3c', alpha=0.4, hatch='///', edgecolor='#c0392b', label='Torsional Arm (Left)'))
        ax1.text(-c1_cm/2 - y_eff/2, c2_cm, "Arm 1", ha='center', color='#c0392b', fontweight='bold')

    # Draw Right Arm
    if has_right_arm:
        ax1.add_patch(patches.Rectangle((c1_cm/2, -c2_cm/2), y_eff, c2_cm, 
                                        facecolor='#e74c3c', alpha=0.4, hatch='///', edgecolor='#c0392b', label='Torsional Arm (Right)'))
        ax1.text(c1_cm/2 + y_eff/2, c2_cm, "Arm 2", ha='center', color='#c0392b', fontweight='bold')

    # Dimensions & Annotations
    ax1.annotate("", xy=(-c1_cm/2, -c2_cm/2 - 20), xytext=(c1_cm/2, -c2_cm/2 - 20), arrowprops=dict(arrowstyle='<->'))
    ax1.text(0, -c2_cm/2 - 35, f"c1", ha='center')
    
    ax1.axis('off')
    ax1.set_title(f"Plan View: {desc}", fontweight='bold')
    ax1.legend(loc='lower center', fontsize=8)

    # --- 2. LOGIC VISUALIZATION ---
    ax2 = fig.add_subplot(gs[1])
    ax2.axis('off')
    ax2.set_title("Stiffness Calculation Logic", fontweight='bold')
    
    # Text explanation
    y_pos = 0.8
    ax2.text(0.1, y_pos, "Formula (ACI):", fontweight='bold'); y_pos -= 0.15
    ax2.text(0.1, y_pos, r"$K_t = \sum \frac{9EC}{L_2(1-c_2/L_2)^3}$", fontsize=12); y_pos -= 0.2
    
    ax2.text(0.1, y_pos, f"Condition: {col_location}", color='b'); y_pos -= 0.15
    if col_location == 'Corner (เสาเข้ามุม)':
        ax2.text(0.1, y_pos, "• Torsion occurs on 1 side", fontsize=10)
        ax2.text(0.1, y_pos-0.1, r"• $K_{t,total} = K_{t,arm}$", fontsize=11, color='r')
    else:
        ax2.text(0.1, y_pos, "• Torsion occurs on 2 sides", fontsize=10)
        ax2.text(0.1, y_pos-0.1, r"• $K_{t,total} = 2 \times K_{t,arm}$", fontsize=11, color='r')

    plt.tight_layout()
    return fig

# --- Main Render ---

def render(c1_w, c2_w, L1, L2, lc, h_slab, fc, mat_props, w_u, col_type_input):
    st.header("3. Equivalent Frame Method (Torsion Check)")
    
    # --- UI for Torsion Specifics ---
    st.info("ℹ️ Torsion (การบิด) จะเกิดขึ้นที่แถบพื้นข้างหัวเสาที่ตั้งฉากกับทิศทางที่เราคำนวณ")
    
    # Toggle for user to see the difference
    col_location = st.radio(
        "📍 เลือกตำแหน่งเสาเพื่อดูพฤติกรรม Torsion:",
        ["Interior/Edge (เสากลาง/ริม)", "Corner (เสาเข้ามุม)"],
        horizontal=True
    )

    # Data Prep
    c1_cm, c2_cm, h_cm = c1_w, c2_w, h_slab
    L2_m = L2
    Ec = 15100 * np.sqrt(fc)
    E_ksm = Ec * 10000

    # --- Visualization ---
    st.pyplot(plot_torsional_arms_dynamic(c1_cm, c2_cm, h_cm, col_location))

    # --- Calculation ---
    # 1. Calculate C (Cross-section constant)
    x, y = h_cm, c1_cm # x is shorter dim, y is longer dim usually, but for torsion member y=c1 approx
    # Check simple Rectangular C
    C_val = (1 - 0.63 * x / y) * (x**3 * y) / 3.0
    
    # 2. Calculate Kt for ONE arm
    Kt_one_arm = 9 * E_ksm * (C_val/1e8) / (L2_m * ((1 - (c2_cm/100)/L2_m)**3))
    
    # 3. Summation based on location
    if col_location == "Corner (เสาเข้ามุม)":
        num_arms = 1
        Kt_total = Kt_one_arm * 1
    else:
        num_arms = 2
        Kt_total = Kt_one_arm * 2
        
    # --- Display Results ---
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Cross-section Constant ($C$):**")
        st.latex(f"C = {C_val:,.0f} \\text{{ cm}}^4")
        st.write(f"($x={x}, y={y}$)")
        
    with col2:
        st.write(f"**Torsional Stiffness ($K_t$):**")
        st.write(f"- Arms count: **{num_arms}** sides")
        st.latex(f"K_{{t,total}} = {num_arms} \\times {Kt_one_arm:,.0f}")
        st.latex(f"K_{{t}} = \\mathbf{{{Kt_total:,.2e}}}")

    st.markdown("---")
    st.caption("หมายเหตุ: ปกติโปรแกรมจะคำนวณแบบ 2 ด้าน (Interior) เป็นค่า Default นอกจากจะระบุว่าเป็น Corner")
