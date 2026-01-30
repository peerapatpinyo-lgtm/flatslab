import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# --- Isometric Projection Helpers ---
def iso_project(x, y, z):
    """แปลงพิกัด 3D (x,y,z) เป็น 2D (x_iso, y_iso) มุม 30 องศา"""
    angle = np.radians(30)
    xi = (x - y) * np.cos(angle)
    yi = (x + y) * np.sin(angle) + z
    return xi, yi

def draw_iso_box(ax, origin, size, color, alpha=1.0, hatch=None, edge_color='k', zorder=1):
    """ฟังก์ชันวาดกล่อง Isometric"""
    x0, y0, z0 = origin
    dx, dy, dz = size
    
    # คำนวณจุดยอด (Vertices)
    # Top Face points
    p_top_1 = iso_project(x0, y0, z0+dz)
    p_top_2 = iso_project(x0+dx, y0, z0+dz)
    p_top_3 = iso_project(x0+dx, y0+dy, z0+dz)
    p_top_4 = iso_project(x0, y0+dy, z0+dz)
    
    # Side Face points (Right: +X face)
    p_right_1 = iso_project(x0+dx, y0, z0)
    p_right_2 = iso_project(x0+dx, y0+dy, z0)
    
    # Side Face points (Left: +Y face)
    p_left_1 = iso_project(x0, y0+dy, z0)

    # 1. Top Face
    top_poly = patches.Polygon([p_top_1, p_top_2, p_top_3, p_top_4], 
                               facecolor=color, alpha=alpha, edgecolor=edge_color, hatch=hatch, zorder=zorder+2)
    ax.add_patch(top_poly)
    
    # 2. Right Face (ด้านขวา แรเงาเล็กน้อย)
    right_poly = patches.Polygon([p_top_2, p_right_1, p_right_2, p_top_3], 
                                 facecolor=color, alpha=alpha, edgecolor=edge_color, hatch=hatch, zorder=zorder+1)
    ax.add_patch(right_poly)
    # Shadow layer
    right_shade = patches.Polygon([p_top_2, p_right_1, p_right_2, p_top_3], facecolor='black', alpha=0.1, zorder=zorder+1)
    ax.add_patch(right_shade)

    # 3. Left Face (ด้านซ้าย แรเงาเข้มกว่า)
    left_poly = patches.Polygon([p_top_4, p_top_3, p_right_2, p_left_1], 
                                facecolor=color, alpha=alpha, edgecolor=edge_color, hatch=hatch, zorder=zorder)
    ax.add_patch(left_poly)
    # Shadow layer
    left_shade = patches.Polygon([p_top_4, p_top_3, p_right_2, p_left_1], facecolor='black', alpha=0.2, zorder=zorder)
    ax.add_patch(left_shade)

def plot_torsion_member(col_type, c1, c2, h_slab, L1, L2):
    """
    Main function to draw Torsional Member Logic
    """
    fig, ax = plt.subplots(figsize=(8, 5))
    
    # ปรับสเกลสำหรับการวาด (ไม่ใช่สเกลจริง แต่เป็น Schematic Scale)
    s_L = 10.0  # Span length drawing unit
    s_c1 = 1.5  # Column width drawing unit
    s_c2 = 1.5
    s_h = 0.5   # Slab thickness drawing unit
    
    # กำหนดตำแหน่งเสาและขอบเขตพื้นตาม Type
    if col_type == 'interior':
        col_pos = (0, 0, 0)
        x_lim = (-s_L/2, s_L/2)
        y_lim = (-s_L/2, s_L/2)
        title_text = "Interior Column (2 Arms)"
    elif col_type == 'edge':
        col_pos = (0, 0, 0) 
        x_lim = (-s_c1/2, s_L) # พื้นหายไปด้านซ้าย
        y_lim = (-s_L/2, s_L/2)
        title_text = "Edge Column (2 Arms)"
    else: # corner
        col_pos = (0, 0, 0)
        x_lim = (-s_c1/2, s_L) # พื้นหายด้านซ้าย
        y_lim = (-s_c2/2, s_L) # พื้นหายด้านล่าง
        title_text = "Corner Column (1 Arm)"

    # --- 1. Draw Grid (Slab) ---
    grid_step = 1.0
    # X-lines
    for y in np.arange(y_lim[0], y_lim[1]+0.1, grid_step):
        p1 = iso_project(x_lim[0], y, -s_h)
        p2 = iso_project(x_lim[1], y, -s_h)
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color='#bdc3c7', lw=0.5, zorder=0)
    # Y-lines
    for x in np.arange(x_lim[0], x_lim[1]+0.1, grid_step):
        p1 = iso_project(x, y_lim[0], -s_h)
        p2 = iso_project(x, y_lim[1], -s_h)
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color='#bdc3c7', lw=0.5, zorder=0)

    # --- 2. Draw Column ---
    col_h = s_h * 4
    # Shift column to be centered at (0,0) visually
    cx = col_pos[0] - s_c1/2
    cy = col_pos[1] - s_c2/2
    draw_iso_box(ax, (cx, cy, -s_h), (s_c1, s_c2, col_h), '#95a5a6', edge_color='k', zorder=10)

    # --- 3. Draw Torsional Members (Red Strips) ---
    t_len = s_L/2 - s_c2/2 # Length of arm
    
    # Arm 1: Positive Y (Up-Right)
    if y_lim[1] > s_c2/2:
        draw_iso_box(ax, (cx, cy + s_c2, -s_h), (s_c1, t_len, s_h), 
                     color='#e74c3c', alpha=0.4, hatch='///', edge_color='#c0392b', zorder=5)
    
    # Arm 2: Negative Y (Down-Left)
    if y_lim[0] < -s_c2/2:
        draw_iso_box(ax, (cx, cy - t_len, -s_h), (s_c1, t_len, s_h), 
                     color='#e74c3c', alpha=0.4, hatch='///', edge_color='#c0392b', zorder=5)

    # --- 4. Annotations ---
    # Label "Torsional Member"
    label_pt = iso_project(cx + s_c1, cy + s_c2 + 1, 0)
    ax.text(label_pt[0], label_pt[1], "Torsional\nMember", color='#c0392b', fontsize=10, fontweight='bold')
    
    # Label "c1"
    c1_p1 = iso_project(cx, cy, col_h/2)
    c1_p2 = iso_project(cx+s_c1, cy, col_h/2)
    ax.annotate("", xy=c1_p1, xytext=c1_p2, arrowprops=dict(arrowstyle='<->'))
    ax.text((c1_p1[0]+c1_p2[0])/2, c1_p1[1]+0.2, "c1", ha='center', fontsize=9)

    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title(title_text, fontweight='bold', fontsize=12)
    
    # Set Limits to frame the drawing
    limit = 8
    ax.set_xlim(-limit, limit)
    ax.set_ylim(-limit/2, limit)
    
    return fig
