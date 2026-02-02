# tab_drawings.py
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pandas as pd

# ==========================================
# 1. HELPER: Dimension Line (CAD Style - High Precision)
# ==========================================
def draw_dimension(ax, start, end, text, offset=0, color='#003366', fontsize=10):
    """
    ฟังก์ชันวาดเส้นบอกระยะแบบ Engineering Drawing
    """
    x1, y1 = start
    x2, y2 = end
    
    # ตรวจสอบแนวเส้น (ตั้งหรือนอน)
    is_vertical = abs(x1 - x2) < 0.001
    
    if is_vertical: # แนวตั้ง
        x1 += offset
        x2 += offset
        rotation = 90
        ha = 'right' if offset < 0 else 'left'
        va = 'center'
        txt_x = x1 - 0.15 if offset < 0 else x1 + 0.15
        txt_y = (y1 + y2) / 2
    else: # แนวนอน
        y1 += offset
        y2 += offset
        rotation = 0
        ha = 'center'
        va = 'bottom' if offset > 0 else 'top'
        txt_x = (x1 + x2) / 2
        txt_y = y1 + 0.15 if offset > 0 else y1 - 0.15

    # 1. วาดเส้นหลัก (Main Line)
    ax.annotate('', xy=(x1, y1), xytext=(x2, y2),
                arrowprops=dict(arrowstyle='<|-|>', color=color, lw=0.8, mutation_scale=15))
    
    # 2. วาดเส้นฉาย (Extension Lines) - เส้นประ
    ext_len = 0.1
    alpha_ext = 0.6
    if is_vertical:
        ax.plot([start[0], x1], [y1, y1], color=color, lw=0.5, ls=':', alpha=alpha_ext)
        ax.plot([end[0], x2], [y2, y2], color=color, lw=0.5, ls=':', alpha=alpha_ext)
    else:
        ax.plot([x1, x1], [start[1], y1], color=color, lw=0.5, ls=':', alpha=alpha_ext)
        ax.plot([x2, x2], [end[1], y2], color=color, lw=0.5, ls=':', alpha=alpha_ext)

    # 3. ใส่ตัวเลข (Text with Background)
    ax.text(txt_x, txt_y, text, 
            color=color, fontsize=fontsize, ha=ha, va=va, rotation=rotation, fontweight='bold',
            bbox=dict(facecolor='white', alpha=0.85, edgecolor='none', pad=1.5))

# ==========================================
# 2. MAIN RENDER FUNCTION
# ==========================================
def render(L1, L2, c1_w, c2_w, h_slab, lc, cover, d_eff, drop_data=None, moment_vals=None):
    """
    [FIXED] รับ arguments ครบทุกตัวที่ app.py ส่งมา แม้จะไม่ได้ใช้บางตัว (moment_vals) 
    เพื่อป้องกัน Error 'unexpected keyword argument'
    """
    st.header("📐 Geometry Verification (ตรวจสอบระยะโครงสร้าง)")
    st.info("หน้านี้แสดงภาพจำลองจากค่า Input ของคุณ เพื่อยืนยันความถูกต้องของระยะ (Span, Column, Drop Panel)")

    # Data Preparation
    c1_m = c1_w / 100.0
    c2_m = c2_w / 100.0
    
    # Handle Drop Data (เผื่อกรณี None)
    if drop_data is None:
        drop_data = {'has_drop': False, 'width': 0, 'length': 0, 'depth': 0}
        
    has_drop = drop_data.get('has_drop', False)
    drop_w_m = drop_data.get('width', 0) / 100.0
    drop_l_m = drop_data.get('length', 0) / 100.0
    h_drop = drop_data.get('depth', 0)

    # ==========================================
    # PART 1: OVERALL PLAN (แปลนรวม)
    # ==========================================
    col_main, col_detail = st.columns([2, 1])
    
    with col_main:
        st.subheader("1. Floor Plan View (แปลนพื้น)")
        fig, ax = plt.subplots(figsize=(8, 6))
        
        # 1. Slab Outline
        ax.add_patch(patches.Rectangle((0, 0), L1, L2, lw=1.5, edgecolor='black', facecolor='#f8f9fa'))
        
        # 2. Drop Panels (ถ้ามี)
        if has_drop:
            # วาด Drop Panel ที่ 4 มุม (Center ที่เสา)
            drop_kw = dict(facecolor='#cfd8dc', edgecolor='#546e7a', linestyle='--', alpha=0.6)
            # Coordinates of column centers
            centers = [(0,0), (L1,0), (0,L2), (L1,L2)]
            for cx, cy in centers:
                ax.add_patch(patches.Rectangle((cx - drop_w_m/2, cy - drop_l_m/2), drop_w_m, drop_l_m, **drop_kw))
                
        # 3. Columns (4 มุม)
        col_kw = dict(facecolor='#37474f', edgecolor='black', zorder=10)
        # Coordinates of column bottom-left corners relative to column center at slab corner
        # แต่ใน Input โปรแกรมเรา (0,0) คือ Center เสา หรือ ขอบพื้น? 
        # *Convention ทั่วไป:* Span Lx วัด center-to-center. ดังนั้นมุมพื้น (0,0) คือ Center เสา
        # วาดเสาให้ Center อยู่ที่มุม (0,0), (L1,0) ...
        
        centers = [(0,0), (L1,0), (0,L2), (L1,L2)]
        for cx, cy in centers:
            ax.add_patch(patches.Rectangle((cx - c1_m/2, cy - c2_m/2), c1_m, c2_m, **col_kw))

        # 4. Dimensions (Span)
        draw_dimension(ax, (0, L2), (L1, L2), f"Lx = {L1} m", offset=0.8, color='blue')
        draw_dimension(ax, (L1, 0), (L1, L2), f"Ly = {L2} m", offset=0.8, color='blue')
        
        # Config Plot
        margin = 1.5
        ax.set_xlim(-margin, L1 + margin)
        ax.set_ylim(-margin, L2 + margin)
        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_title(f"Center-to-Center Layout", fontweight='bold')
        
        st.pyplot(fig)

    with col_detail:
        st.subheader("2. Support Detail (Zoom)")
        # Zoom ดูที่หัวเสา เพื่อเช็คขนาดเสา vs Drop Panel
        fig_z, ax_z = plt.subplots(figsize=(4, 4))
        
        zoom_range = max(c1_m, c2_m) * 2.5
        if has_drop: zoom_range = max(drop_w_m, drop_l_m) * 1.2
            
        # Draw Drop
        if has_drop:
            ax_z.add_patch(patches.Rectangle((-drop_w_m/2, -drop_l_m/2), drop_w_m, drop_l_m, 
                                             fc='#eceff1', ec='blue', ls='--'))
            # Dim Drop
            draw_dimension(ax_z, (-drop_w_m/2, drop_l_m/2), (drop_w_m/2, drop_l_m/2), 
                           f"Drop X: {drop_data['width']} cm", offset=0.15, color='blue', fontsize=8)
            draw_dimension(ax_z, (-drop_w_m/2, -drop_l_m/2), (-drop_w_m/2, drop_l_m/2), 
                           f"Drop Y: {drop_data['length']} cm", offset=-0.15, color='blue', fontsize=8)

        # Draw Col
        ax_z.add_patch(patches.Rectangle((-c1_m/2, -c2_m/2), c1_m, c2_m, fc='gray', ec='black', hatch='..'))
        
        # Dim Col
        draw_dimension(ax_z, (-c1_m/2, -c2_m/2), (c1_m/2, -c2_m/2), f"c1: {c1_w}", offset=-0.1, color='red', fontsize=9)
        draw_dimension(ax_z, (c1_m/2, -c2_m/2), (c1_m/2, c2_m/2), f"c2: {c2_w}", offset=0.1, color='red', fontsize=9)
        
        ax_z.set_xlim(-zoom_range/2, zoom_range/2)
        ax_z.set_ylim(-zoom_range/2, zoom_range/2)
        ax_z.axis('off')
        ax_z.set_aspect('equal')
        ax_z.set_title("Column Detail (cm)", fontsize=10)
        
        st.pyplot(fig_z)
        
        # Summary Text
        st.markdown("---")
        st.markdown("**Checklist:**")
        st.markdown(f"- Span: **{L1} x {L2}** m")
        st.markdown(f"- Column: **{c1_w} x {c2_w}** cm")
        if has_drop:
            st.markdown(f"- Drop: **{drop_data['width']} x {drop_data['length']}** cm")
            st.markdown(f"- Drop Thick: **+{h_drop}** cm")
        else:
            st.markdown("- Drop Panel: **None**")

    # ==========================================
    # PART 2: SECTION VIEW (รูปตัด)
    # ==========================================
    st.subheader("3. Section View A-A (ความหนา)")
    
    fig_s, ax_s = plt.subplots(figsize=(10, 3.5))
    
    # Scale: ใช้หน่วย cm ในการวาดรูปตัด
    
    # 1. Slab
    # วาดพื้นยาวๆ ตัดกลาง
    cut_width = 300 # cm (สมมุติกว้าง 3 เมตรในรูปตัด)
    ax_s.add_patch(patches.Rectangle((-cut_width/2, 0), cut_width, h_slab, fc='white', ec='black', hatch='///'))
    
    # 2. Drop Panel
    current_y = 0
    if has_drop:
        d_w = min(cut_width*0.6, drop_data['width'])
        ax_s.add_patch(patches.Rectangle((-d_w/2, -h_drop), d_w, h_drop, fc='white', ec='black', hatch='///'))
        current_y = -h_drop
        
        # Dim Drop
        draw_dimension(ax_s, (d_w/2 + 10, 0), (d_w/2 + 10, -h_drop), f"Drop +{h_drop}", offset=5, color='blue')
        
    # 3. Column
    ax_s.add_patch(patches.Rectangle((-c1_w/2, current_y - 40), c1_w, 40, fc='#607d8b', ec='black'))
    
    # 4. Dimensions
    # ความหนาพื้น (h)
    draw_dimension(ax_s, (-cut_width/2 - 10, 0), (-cut_width/2 - 10, h_slab), f"h = {h_slab} cm", offset=-5, color='black')
    
    # ความหนารวม (Total)
    if has_drop:
        total_h = h_slab + h_drop
        draw_dimension(ax_s, (-cut_width/2 - 30, -h_drop), (-cut_width/2 - 30, h_slab), 
                       f"Total = {total_h} cm", offset=-5, color='red')
        
    # Cover & d
    # วาดเหล็กเส้น
    rebar_y = h_slab - cover
    ax_s.plot([-50, 50], [rebar_y, rebar_y], color='red', lw=3, label='Main Bar')
    
    # Dim Cover
    draw_dimension(ax_s, (60, h_slab), (60, rebar_y), f"Cov = {cover}", offset=5, color='green')
    
    # Dim d (Effective Depth)
    draw_dimension(ax_s, (80, rebar_y), (80, current_y), f"d ≈ {d_eff:.1f} cm", offset=5, color='purple')

    # Config
    ax_s.set_xlim(-cut_width/2 - 50, cut_width/2 + 50)
    ax_s.set_ylim(current_y - 30, h_slab + 20)
    ax_s.axis('off')
    ax_s.set_aspect('equal')
    ax_s.set_title("Section View (Thickness & Depths)", fontsize=12, fontweight='bold')
    
    st.pyplot(fig_s)
