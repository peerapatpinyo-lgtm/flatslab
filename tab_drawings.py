# tab_drawings.py
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pandas as pd

# ==========================================
# 1. HELPER: Dimension Line (CAD Style)
# ==========================================
def draw_dimension(ax, start, end, text, offset=0, color='#003366', fontsize=9, arrow_size=0.5):
    """
    วาดเส้นบอกระยะที่มีความยืดหยุ่นสูง ปรับระยะห่าง (offset) ได้
    """
    x1, y1 = start
    x2, y2 = end
    
    # ตรวจสอบว่าเป็นเส้นตั้งหรือนอน
    is_vertical = abs(x1 - x2) < 0.001
    
    if is_vertical: # Vertical Dimension
        x1 += offset
        x2 += offset
        rotation = 90
        ha = 'right' if offset < 0 else 'left'
        va = 'center'
        # Adjust text position
        txt_x = x1 - 0.1 if offset < 0 else x1 + 0.1
        txt_y = (y1 + y2) / 2
    else: # Horizontal Dimension
        y1 += offset
        y2 += offset
        rotation = 0
        ha = 'center'
        va = 'bottom' if offset > 0 else 'top'
        # Adjust text position
        txt_x = (x1 + x2) / 2
        txt_y = y1 + 0.1 if offset > 0 else y1 - 0.1

    # 1. Draw Main Line with Arrows
    ax.annotate('', xy=(x1, y1), xytext=(x2, y2),
                arrowprops=dict(arrowstyle='<->', color=color, lw=0.8, mutation_scale=10))
    
    # 2. Draw Extension Lines (เส้นฉาย)
    ext_overshoot = 0.05 # ส่วนเกินของเส้นฉาย
    if is_vertical:
        ax.plot([start[0], x1], [y1, y1], color=color, lw=0.5, linestyle=':', alpha=0.7) # Top/Bottom ext
        ax.plot([end[0], x2], [y2, y2], color=color, lw=0.5, linestyle=':', alpha=0.7)
    else:
        ax.plot([x1, x1], [start[1], y1], color=color, lw=0.5, linestyle=':', alpha=0.7) # Left/Right ext
        ax.plot([x2, x2], [end[1], y2], color=color, lw=0.5, linestyle=':', alpha=0.7)

    # 3. Draw Text with Background
    ax.text(txt_x, txt_y, text, 
            color=color, fontsize=fontsize, ha=ha, va=va, rotation=rotation,
            bbox=dict(facecolor='white', alpha=0.9, edgecolor='none', pad=1))

# ==========================================
# 2. MAIN RENDER FUNCTION
# ==========================================
def render(L1, L2, c1_w, c2_w, h_slab, lc, cover, d_eff, drop_data):
    """
    แสดงแบบแปลนและรูปตัดเพื่อตรวจสอบระยะ (Input Verification Mode)
    """
    st.header("📐 Geometry Verification (ตรวจสอบระยะโครงสร้าง)")
    st.caption("หน้านี้แสดงภาพจากค่าที่คุณกรอก เพื่อยืนยันว่าโปรแกรมเข้าใจรูปร่างโครงสร้างถูกต้อง")

    # แปลงหน่วยเพื่อการวาด (cm -> m)
    c1_m = c1_w / 100.0
    c2_m = c2_w / 100.0
    
    # ตรวจสอบ Drop Panel
    has_drop = drop_data.get('has_drop', False)
    drop_w_m = drop_data.get('width', 0) / 100.0
    drop_l_m = drop_data.get('length', 0) / 100.0
    h_drop = drop_data.get('depth', 0)

    # ==========================================
    # ส่วนที่ 1: OVERALL PLAN VIEW (แปลนรวม)
    # ==========================================
    col_plan, col_info = st.columns([3, 1])
    
    with col_plan:
        st.subheader("1. General Plan View")
        fig, ax = plt.subplots(figsize=(8, 6))
        
        # 1. Slab Outline
        slab_rect = patches.Rectangle((0, 0), L1, L2, lw=2, edgecolor='black', facecolor='#f9f9f9', label='Slab')
        ax.add_patch(slab_rect)
        
        # 2. Columns (4 Corners)
        col_style = dict(facecolor='#404040', edgecolor='black', zorder=5)
        
        # Coordinates for 4 columns
        col_coords = [
            (-c1_m/2, -c2_m/2),         # BL
            (L1 - c1_m/2, -c2_m/2),     # BR
            (-c1_m/2, L2 - c2_m/2),     # TL
            (L1 - c1_m/2, L2 - c2_m/2)  # TR
        ]
        
        for xy in col_coords:
            ax.add_patch(patches.Rectangle(xy, c1_m, c2_m, **col_style))

        # 3. Drop Panels (Optional)
        if has_drop:
            drop_style = dict(facecolor='#b0bec5', edgecolor='#546e7a', linestyle='--', alpha=0.5, zorder=3)
            # Draw Drops centered at columns
            for cx, cy in [(0,0), (L1,0), (0,L2), (L1,L2)]:
                # Drop coordinates (centered on column center)
                dx = cx - drop_w_m/2
                dy = cy - drop_l_m/2
                ax.add_patch(patches.Rectangle((dx, dy), drop_w_m, drop_l_m, **drop_style))

        # 4. Dimensions (Overall)
        draw_dimension(ax, (0, L2), (L1, L2), f"Lx = {L1} m", offset=1.0, color='blue', fontsize=11)
        draw_dimension(ax, (L1, 0), (L1, L2), f"Ly = {L2} m", offset=1.0, color='blue', fontsize=11)
        
        # Decoration
        ax.set_xlim(-1.5, L1 + 1.5)
        ax.set_ylim(-1.5, L2 + 1.5)
        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_title(f"Floor Plan Layout ({L1}x{L2}m)", fontweight='bold')
        st.pyplot(fig)

    with col_info:
        st.info("ℹ️ **Data Check**")
        df_check = pd.DataFrame({
            "Parameter": ["Lx (Span)", "Ly (Span)", "Col X (c1)", "Col Y (c2)"],
            "Value": [f"{L1} m", f"{L2} m", f"{c1_w} cm", f"{c2_w} cm"]
        })
        st.table(df_check)
        
        if has_drop:
            st.success(f"**Drop Panel Active**\n\nSize: {drop_w_m*100:.0f} x {drop_l_m*100:.0f} cm\nThick: +{h_drop} cm")
        else:
            st.warning("No Drop Panel")

    st.markdown("---")

    # ==========================================
    # ส่วนที่ 2: DETAIL ZOOM & SECTION (จุดสำคัญ)
    # ==========================================
    col_d1, col_d2 = st.columns(2)

    # --- 2.1 Column/Drop Detail (Zoom Plan) ---
    with col_d1:
        st.subheader("2. Support Detail (Plan Zoom)")
        fig2, ax2 = plt.subplots(figsize=(5, 5))
        
        # Center point (0,0)
        zoom_range = max(c1_m, c2_m) * 3 if not has_drop else max(drop_w_m, drop_l_m) * 1.5
        
        # Draw Drop
        if has_drop:
            ax2.add_patch(patches.Rectangle((-drop_w_m/2, -drop_l_m/2), drop_w_m, drop_l_m, 
                                            fc='#eceff1', ec='blue', ls='--', label='Drop Panel'))
            # Drop Dimensions
            draw_dimension(ax2, (-drop_w_m/2, drop_l_m/2), (drop_w_m/2, drop_l_m/2), 
                           f"Drop X: {drop_data['width']}cm", offset=0.2, color='blue', fontsize=8)
            draw_dimension(ax2, (-drop_w_m/2, -drop_l_m/2), (-drop_w_m/2, drop_l_m/2), 
                           f"Drop Y: {drop_data['length']}cm", offset=-0.2, color='blue', fontsize=8)
        
        # Draw Column
        ax2.add_patch(patches.Rectangle((-c1_m/2, -c2_m/2), c1_m, c2_m, fc='gray', ec='black', hatch='..'))
        
        # Column Dimensions
        draw_dimension(ax2, (-c1_m/2, -c2_m/2), (c1_m/2, -c2_m/2), f"c1: {c1_w}cm", offset=-0.1, color='red')
        draw_dimension(ax2, (c1_m/2, -c2_m/2), (c1_m/2, c2_m/2), f"c2: {c2_w}cm", offset=0.1, color='red')
        
        # Config
        ax2.set_xlim(-zoom_range/2, zoom_range/2)
        ax2.set_ylim(-zoom_range/2, zoom_range/2)
        ax2.set_aspect('equal')
        ax2.axis('off')
        ax2.set_title("Top View @ Support", fontsize=10)
        st.pyplot(fig2)

    # --- 2.2 Section View (Detailed Thickness) ---
    with col_d2:
        st.subheader("3. Section Detail (Thickness)")
        fig3, ax3 = plt.subplots(figsize=(5, 5))
        
        # Constants for plotting (cm)
        plot_w = c1_w * 4 # Width of section view
        
        # 1. Slab
        # Concrete Hatching using '///'
        ax3.add_patch(patches.Rectangle((-plot_w/2, 0), plot_w, h_slab, fc='white', ec='black', hatch='///', label='Slab'))
        
        # 2. Drop Panel
        current_y = 0
        if has_drop:
            drop_vis_w = min(plot_w * 0.8, drop_data['width']) # Limit width for visual
            ax3.add_patch(patches.Rectangle((-drop_vis_w/2, -h_drop), drop_vis_w, h_drop, 
                                            fc='white', ec='black', hatch='///'))
            current_y = -h_drop
            
            # Dim Drop
            draw_dimension(ax3, (drop_vis_w/2 + 5, 0), (drop_vis_w/2 + 5, -h_drop), 
                           f"Drop: {h_drop}cm", offset=5, color='blue')

        # 3. Column
        ax3.add_patch(patches.Rectangle((-c1_w/2, current_y - 50), c1_w, 50, fc='#606060', ec='black'))
        
        # 4. Dimensions
        # Slab H
        draw_dimension(ax3, (-plot_w/2 - 10, 0), (-plot_w/2 - 10, h_slab), f"h_slab: {h_slab}cm", offset=-5, color='black')
        
        # Total H (if drop)
        if has_drop:
            draw_dimension(ax3, (-plot_w/2 - 25, -h_drop), (-plot_w/2 - 25, h_slab), 
                           f"Total: {h_slab+h_drop}cm", offset=-5, color='red')
        
        # Cover & d
        rebar_y = h_slab - cover - 0.6
        ax3.plot([-plot_w/3, plot_w/3], [rebar_y, rebar_y], color='red', lw=3, label='Top Bar')
        draw_dimension(ax3, (plot_w/3, h_slab), (plot_w/3, rebar_y), f"Cov:{cover}", offset=5, color='green')
        
        # Config
        ax3.set_xlim(-plot_w/2 - 40, plot_w/2 + 40)
        ax3.set_ylim(current_y - 30, h_slab + 20)
        ax3.set_aspect('equal')
        ax3.axis('off')
        ax3.set_title("Section A-A (Side View)", fontsize=10)
        st.pyplot(fig3)
