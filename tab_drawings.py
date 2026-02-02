# tab_drawing.py
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import calculations as calc

# ==========================================
# HELPER: ฟังก์ชันวาดเส้นบอกระยะ (Dimension Line)
# ==========================================
def draw_dimension(ax, start, end, text, offset=0, color='blue', fontsize=10):
    """
    วาดเส้นบอกระยะแบบ CAD (ลูกศรหัวท้าย + ตัวหนังสือตรงกลาง)
    start, end: tuple (x, y)
    offset: ระยะห่างจากจุดวัด (เพื่อไม่ให้ทับเส้นจริง)
    """
    x1, y1 = start
    x2, y2 = end
    
    # คำนวณจุดสำหรับวาดเส้น (ขยับตาม Offset)
    if x1 == x2: # Vertical Dimension
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
                arrowprops=dict(arrowstyle='<->', color=color, lw=1.0))
    
    # 2. วาดเส้น Extension lines (เส้นฉาย) เล็กๆ
    ext_len = 0.2 if abs(offset) > 0 else 0
    if x1 == x2: # Vertical lines
        ax.plot([start[0], x1], [y1, y1], color=color, lw=0.5, linestyle=':')
        ax.plot([end[0], x2], [y2, y2], color=color, lw=0.5, linestyle=':')
    else: # Horizontal lines
        ax.plot([x1, x1], [start[1], y1], color=color, lw=0.5, linestyle=':')
        ax.plot([x2, x2], [end[1], y2], color=color, lw=0.5, linestyle=':')

    # 3. ใส่ตัวหนังสือ (Text)
    mid_x = (x1 + x2) / 2
    mid_y = (y1 + y2) / 2
    
    # ขยับ Text หนีเส้นนิดหน่อย
    text_offset_x = 0
    text_offset_y = 0
    if x1 == x2: text_offset_x = -0.1 if offset < 0 else 0.1
    else: text_offset_y = 0.1 if offset > 0 else -0.1
        
    ax.text(mid_x + text_offset_x, mid_y + text_offset_y, text, 
            color=color, fontsize=fontsize, ha=ha, va=va, rotation=rotation,
            bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=1))

# ==========================================
# MAIN RENDER FUNCTION
# ==========================================
def render_drawing_tab(data_x, data_y, mat_props, w_u):
    st.header("📐 Structural Drawings & Dimensions")
    st.info("หน้านี้แสดงตำแหน่งของค่า Input ต่างๆ เพื่อให้ท่านตรวจสอบความถูกต้องของระยะ")

    # 1. Validation
    if not data_x or not data_y:
        st.warning("กรุณากรอกข้อมูลใน Tab 'Design' ให้ครบถ้วนก่อนครับ")
        return

    # 2. Prepare Data
    Lx = data_x['span']
    Ly = data_y['span']
    # แปลงหน่วยเสาเป็นเมตรเพื่อวาดในแปลน
    c1_m = data_x['col_size'] / 100.0 
    c2_m = data_y['col_size'] / 100.0
    
    h_slab = mat_props['h_slab']   # cm
    cover = mat_props['cover']     # cm
    fc = mat_props['fc']

    # ==========================================
    # PART 1: PLAN VIEW (Top Down)
    # ==========================================
    st.subheader("1. Plan View: Span & Column Dimensions")
    st.caption(f"แสดงระยะช่วงเสา (Lx, Ly) และขนาดเสา (c1, c2)")
    
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # วาดพื้น (Slab Boundary)
    rect = patches.Rectangle((0, 0), Lx, Ly, linewidth=2, edgecolor='black', facecolor='#f0f2f6')
    ax.add_patch(rect)
    
    # วาดเสา (Columns) ที่ 4 มุม
    col_style = dict(facecolor='gray', edgecolor='black', alpha=0.7)
    # BL
    ax.add_patch(patches.Rectangle((-c1_m/2, -c2_m/2), c1_m, c2_m, **col_style))
    # BR
    ax.add_patch(patches.Rectangle((Lx-c1_m/2, -c2_m/2), c1_m, c2_m, **col_style))
    # TL
    ax.add_patch(patches.Rectangle((-c1_m/2, Ly-c2_m/2), c1_m, c2_m, **col_style))
    # TR
    ax.add_patch(patches.Rectangle((Lx-c1_m/2, Ly-c2_m/2), c1_m, c2_m, **col_style))

    # --- DIMENSIONS (จุดสำคัญที่เพิ่มเข้ามา) ---
    # 1. Span Dimensions (Lx, Ly)
    draw_dimension(ax, (0, Ly), (Lx, Ly), f"Span Lx = {Lx} m", offset=0.8, color='blue')
    draw_dimension(ax, (Lx, 0), (Lx, Ly), f"Span Ly = {Ly} m", offset=0.8, color='blue')
    
    # 2. Column Dimensions (Zoom in at Bottom Left)
    # c1 (Dimension parallel to X)
    draw_dimension(ax, (-c1_m/2, -c2_m/2), (c1_m/2, -c2_m/2), f"c1 = {data_x['col_size']} cm", offset=-0.4, color='red')
    # c2 (Dimension parallel to Y)
    draw_dimension(ax, (-c1_m/2, -c2_m/2), (-c1_m/2, c2_m/2), f"c2 = {data_y['col_size']} cm", offset=-0.4, color='red')

    # Config Plot
    ax.set_xlim(-1.5, Lx + 1.5)
    ax.set_ylim(-1.5, Ly + 1.5)
    ax.set_aspect('equal')
    ax.axis('off') # ปิดแกน XY เดิม เพื่อความสวยงาม
    ax.set_title("Plan View (Top-Down)", fontsize=14, fontweight='bold')
    
    st.pyplot(fig)

    # ==========================================
    # PART 2: SECTION VIEW (Side Cut)
    # ==========================================
    st.markdown("---")
    st.subheader("2. Section View: Thickness & Depth")
    st.caption("แสดงความหนาพื้น (h), ระยะหุ้ม (cover) และความลึกประสิทธิผล (d)")
    
    fig_sec, ax_sec = plt.subplots(figsize=(8, 4))
    
    # Scale: วาดหน่วยเป็น cm เพื่อให้ดูง่าย
    plot_w = 100 # ความกว้างพื้นในรูปตัดสมมติ
    col_w_cm = data_x['col_size'] # c1
    
    # 1. Draw Slab
    slab_rect = patches.Rectangle((-plot_w/2, 0), plot_w, h_slab, facecolor='#e0e0e0', edgecolor='black', lw=1.5)
    ax_sec.add_patch(slab_rect)
    
    # 2. Draw Column (Below)
    col_rect = patches.Rectangle((-col_w_cm/2, -40), col_w_cm, 40, facecolor='gray', edgecolor='black')
    ax_sec.add_patch(col_rect)
    
    # 3. Draw Rebar (เหล็กเสริม)
    # สมมติเหล็กบน (Top Bar)
    rebar_y = h_slab - cover - 0.6 # กึ่งกลางเหล็ก (สมมติ 12mm)
    ax_sec.plot([-plot_w/2 + 5, plot_w/2 - 5], [rebar_y, rebar_y], color='red', lw=3, label='Main Rebar')
    
    # --- DIMENSIONS ---
    # 1. Total Thickness (h) - ด้านซ้าย
    draw_dimension(ax_sec, (-plot_w/2 - 10, 0), (-plot_w/2 - 10, h_slab), f"h = {h_slab} cm", offset=-5, color='black')
    
    # 2. Cover - ด้านขวาบน
    draw_dimension(ax_sec, (plot_w/2 + 10, h_slab), (plot_w/2 + 10, h_slab-cover), f"Cov = {cover} cm", offset=5, color='green')
    
    # 3. Effective Depth (d) - ด้านขวา
    d_approx = h_slab - cover - 0.6
    draw_dimension(ax_sec, (plot_w/2 + 25, 0), (plot_w/2 + 25, d_approx), f"d ≈ {d_approx:.1f} cm", offset=5, color='blue')
    
    # 4. Column Width
    draw_dimension(ax_sec, (-col_w_cm/2, -10), (col_w_cm/2, -10), f"c1 = {col_w_cm} cm", offset=0, color='red')

    # Config Plot
    ax_sec.set_xlim(-plot_w/2 - 40, plot_w/2 + 40)
    ax_sec.set_ylim(-50, h_slab + 20)
    ax_sec.set_aspect('equal')
    ax_sec.axis('off')
    ax_sec.set_title("Section View (Cut through Slab)", fontsize=14, fontweight='bold')
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.pyplot(fig_sec)
    with col2:
        st.info("""
        **คำอธิบายตัวแปร:**
        * **h:** ความหนาพื้นทั้งหมด (Slab Thickness)
        * **Cov:** ระยะหุ้มคอนกรีต (Clear Cover)
        * **d:** ระยะจากผิวรับแรงอัดถึงกึ่งกลางเหล็กเสริม (Effective Depth)
        * **c1/c2:** ขนาดหน้าตัดเสา
        """)
