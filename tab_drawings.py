# tab_drawings.py
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# ==========================================
# HELPER: ฟังก์ชันวาดเส้นบอกระยะ (Dimension Line)
# ==========================================
def draw_dimension(ax, start, end, text, offset=0, color='blue', fontsize=9):
    """
    วาดเส้นบอกระยะแบบ CAD (ลูกศรหัวท้าย + ตัวหนังสือตรงกลาง)
    start, end: tuple (x, y)
    offset: ระยะห่างจากจุดวัด
    """
    x1, y1 = start
    x2, y2 = end
    
    # คำนวณจุดสำหรับวาดเส้น (ขยับตาม Offset)
    if abs(x1 - x2) < 0.001: # Vertical Dimension
        x1 += offset
        x2 += offset
        rotation = 90
        ha = 'right' if offset < 0 else 'left'
        va = 'center'
    else: # Horizontal Dimension
        y1 += offset
        y2 += offset
        rotation = 0
        ha = 'center'
        va = 'bottom' if offset > 0 else 'top'

    # 1. วาดเส้นลูกศร (Arrow Line)
    ax.annotate('', xy=(x1, y1), xytext=(x2, y2),
                arrowprops=dict(arrowstyle='<->', color=color, lw=0.8))
    
    # 2. วาดเส้น Extension lines (เส้นฉาย)
    if abs(x1 - x2) < 0.001: # Vertical lines
        ax.plot([start[0], x1], [y1, y1], color=color, lw=0.5, linestyle=':')
        ax.plot([end[0], x2], [y2, y2], color=color, lw=0.5, linestyle=':')
    else: # Horizontal lines
        ax.plot([x1, x1], [start[1], y1], color=color, lw=0.5, linestyle=':')
        ax.plot([x2, x2], [end[1], y2], color=color, lw=0.5, linestyle=':')

    # 3. ใส่ตัวหนังสือ (Text) พร้อมพื้นหลังขาว
    mid_x = (x1 + x2) / 2
    mid_y = (y1 + y2) / 2
    
    # ปรับตำแหน่ง Text เล็กน้อยเพื่อไม่ให้ทับเส้น
    t_off_x = 0
    t_off_y = 0
    if abs(x1 - x2) < 0.001: t_off_x = -0.05 if offset < 0 else 0.05
    else: t_off_y = 0.05 if offset > 0 else -0.05

    ax.text(mid_x + t_off_x, mid_y + t_off_y, text, 
            color=color, fontsize=fontsize, ha=ha, va=va, rotation=rotation,
            bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', pad=1))

# ==========================================
# MAIN RENDER FUNCTION
# ==========================================
def render(L1, L2, c1_w, c2_w, h_slab, lc, cover, d_eff, moment_vals):
    """
    Parameters รับค่าตรงกับที่ส่งมาจาก app.py:
    - L1, L2: Span (m)
    - c1_w, c2_w: Column sizes (cm)
    - h_slab, cover, d_eff: Slab properties (cm)
    - lc: Storey Height (m)
    - moment_vals: Dict of moments (kg-m)
    """
    
    st.header("📐 Structural Drawings & Details")

    # แปลงหน่วยเสาเป็นเมตรเพื่อวาดใน Plan View (m)
    c1_m = c1_w / 100.0
    c2_m = c2_w / 100.0
    
    # คำนวณความกว้าง Strip ตามมาตรฐาน DDM (L_min / 4)
    L_min = min(L1, L2)
    strip_w = L_min / 4.0

    # ==========================================
    # PART 1: PLAN VIEW & STRIPS
    # ==========================================
    st.subheader(f"1. Plan View: Column Strip & Middle Strip")
    st.caption("แสดงขอบเขตของ Column Strip (แถบเสา) และ Middle Strip (แถบกลาง) สำหรับการคำนวณโมเมนต์")
    
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # 1. วาดพื้น (Slab)
    rect = patches.Rectangle((0, 0), L1, L2, linewidth=2, edgecolor='black', facecolor='white')
    ax.add_patch(rect)
    
    # 2. วาดโซน Column Strip (สีฟ้าจางๆ)
    # แนวนอน (Along L1)
    ax.add_patch(patches.Rectangle((0, 0), L1, strip_w, facecolor='blue', alpha=0.1, label='Column Strip'))
    ax.add_patch(patches.Rectangle((0, L2-strip_w), L1, strip_w, facecolor='blue', alpha=0.1))
    
    # 3. วาดเสา (Columns) - 4 มุม
    col_kws = dict(facecolor='gray', edgecolor='black', zorder=5)
    ax.add_patch(patches.Rectangle((-c1_m/2, -c2_m/2), c1_m, c2_m, **col_kws)) # BL
    ax.add_patch(patches.Rectangle((L1-c1_m/2, -c2_m/2), c1_m, c2_m, **col_kws)) # BR
    ax.add_patch(patches.Rectangle((-c1_m/2, L2-c2_m/2), c1_m, c2_m, **col_kws)) # TL
    ax.add_patch(patches.Rectangle((L1-c1_m/2, L2-c2_m/2), c1_m, c2_m, **col_kws)) # TR

    # 4. Dimensions (Dimensions)
    # Span Dimensions
    draw_dimension(ax, (0, L2), (L1, L2), f"Lx = {L1} m", offset=0.8, color='black')
    draw_dimension(ax, (L1, 0), (L1, L2), f"Ly = {L2} m", offset=0.8, color='black')
    
    # Strip Dimensions
    draw_dimension(ax, (L1+0.5, 0), (L1+0.5, strip_w), f"CS: {strip_w:.2f}m", offset=0.2, color='blue')
    draw_dimension(ax, (L1+0.5, strip_w), (L1+0.5, L2-strip_w), f"MS: {L2 - 2*strip_w:.2f}m", offset=0.2, color='green')
    
    # Column Detail Zoom
    draw_dimension(ax, (-c1_m/2, -0.5), (c1_m/2, -0.5), f"c1: {c1_w}cm", offset=-0.1, color='red')
    
    ax.set_xlim(-1, L1 + 1.5)
    ax.set_ylim(-1, L2 + 1.5)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05))
    ax.set_title(f"Plan View (Lmin/4 = {strip_w:.2f} m)", fontweight='bold')
    
    st.pyplot(fig)
    
    # ==========================================
    # PART 2: SECTION VIEW
    # ==========================================
    st.markdown("---")
    st.subheader("2. Section View (Typical)")
    
    fig2, ax2 = plt.subplots(figsize=(8, 4))
    
    # Draw logic (Scale: cm everywhere for section detail)
    # Convert m to cm for plotting relative to slab thickness
    lc_cm = lc * 100 
    
    # 1. Slab
    ax2.add_patch(patches.Rectangle((-50, lc_cm), 100, h_slab, facecolor='#e0e0e0', edgecolor='black'))
    
    # 2. Column (Bottom)
    ax2.add_patch(patches.Rectangle((-c1_w/2, 0), c1_w, lc_cm, facecolor='gray', alpha=0.5, edgecolor='black'))
    
    # 3. Column (Top - Stub)
    ax2.add_patch(patches.Rectangle((-c1_w/2, lc_cm+h_slab), c1_w, 30, facecolor='gray', alpha=0.5, edgecolor='black', linestyle='--'))
    
    # 4. Rebar (Top & Bottom)
    # Top Bar
    ax2.plot([-40, 40], [lc_cm + h_slab - cover, lc_cm + h_slab - cover], color='blue', lw=2, label='Top Bar')
    # Bottom Bar
    ax2.plot([-40, 40], [lc_cm + cover, lc_cm + cover], color='green', lw=2, label='Bottom Bar')
    
    # Dimensions
    # Storey Height
    draw_dimension(ax2, (-60, 0), (-60, lc_cm), f"Storey H = {lc} m", offset=-10, color='black')
    
    # Slab Thickness
    draw_dimension(ax2, (60, lc_cm), (60, lc_cm+h_slab), f"h = {h_slab} cm", offset=10, color='black')
    
    # Effective Depth (d)
    d_loc = lc_cm + h_slab - cover - 0.6 # approx
    draw_dimension(ax2, (80, lc_cm), (80, d_loc), f"d = {d_eff:.1f} cm", offset=5, color='red')

    ax2.set_xlim(-100, 100)
    ax2.set_ylim(-20, lc_cm + h_slab + 50)
    ax2.axis('off')
    ax2.set_aspect('equal')
    ax2.legend(loc='lower right')
    ax2.set_title("Section A-A: Support Detail")
    
    st.pyplot(fig2)

    # ==========================================
    # PART 3: MOMENT DIAGRAM SCHEMATIC
    # ==========================================
    st.markdown("---")
    st.subheader("3. Moment Distribution Schematic (Concept)")
    
    # ดึงค่าโมเมนต์มาแสดง
    M_neg = moment_vals.get('M_cs_neg', 0)
    M_pos = moment_vals.get('M_cs_pos', 0)
    
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.info(f"**Column Strip Moments (Calculated):**\n\n"
                f"🔴 Negative (Support): {M_neg:,.0f} kg-m\n\n"
                f"🔵 Positive (Midspan): {M_pos:,.0f} kg-m")
        
    with col_m2:
        # Simple schematic of moment diagram
        fig3, ax3 = plt.subplots(figsize=(5, 2))
        x = [0, 0.2, 0.5, 0.8, 1.0]
        y = [-1, 0, 0.6, 0, -1] # Normalize shape
        
        ax3.plot(x, y, 'r-', lw=2)
        ax3.axhline(0, color='black', lw=0.5)
        ax3.fill_between(x, y, 0, where=[i>0 for i in y], color='blue', alpha=0.3)
        ax3.fill_between(x, y, 0, where=[i<0 for i in y], color='red', alpha=0.3)
        
        ax3.text(0, -1.2, "Support (-)", ha='center', fontsize=8, color='red')
        ax3.text(0.5, 0.8, "Midspan (+)", ha='center', fontsize=8, color='blue')
        ax3.text(1.0, -1.2, "Support (-)", ha='center', fontsize=8, color='red')
        
        ax3.axis('off')
        ax3.set_title("Typical Moment Diagram")
        st.pyplot(fig3)
