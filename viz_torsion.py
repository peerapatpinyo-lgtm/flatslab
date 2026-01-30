import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

def iso_project(x, y, z, scale=1.0):
    """แปลงพิกัด (x,y,z) เป็น (x_iso, y_iso) เพื่อวาดแบบ Isometric 30 องศา"""
    # มุม 30 องศามาตรฐานงานเขียนแบบ
    angle = np.radians(30)
    # สูตร Isometric Projection
    xi = (x - y) * np.cos(angle)
    yi = (x + y) * np.sin(angle) + z
    return xi * scale, yi * scale

def draw_iso_box(ax, origin, size, color, alpha=1.0, hatch=None, edge_color='k', zorder=1):
    """ฟังก์ชันช่วยวาดกล่อง 3D (Column, Torsion Arm)"""
    x0, y0, z0 = origin
    dx, dy, dz = size
    
    # จุดยอดต่างๆ ของกล่อง
    # Bottom Face
    p0 = iso_project(x0, y0, z0)
    p1 = iso_project(x0+dx, y0, z0)
    p2 = iso_project(x0+dx, y0+dy, z0)
    p3 = iso_project(x0, y0+dy, z0)
    
    # Top Face
    p4 = iso_project(x0, y0, z0+dz)
    p5 = iso_project(x0+dx, y0, z0+dz)
    p6 = iso_project(x0+dx, y0+dy, z0+dz)
    p7 = iso_project(x0, y0+dy, z0+dz)

    # วาดหน้าตัดที่มองเห็น (Top, Right, Left)
    # 1. Top Face
    top_poly = patches.Polygon([p4, p5, p6, p7], facecolor=color, alpha=alpha, edgecolor=edge_color, hatch=hatch, zorder=zorder+1)
    ax.add_patch(top_poly)
    
    # 2. Right Face (Front-Right)
    right_poly = patches.Polygon([p1, p2, p6, p5], facecolor=color, alpha=alpha, edgecolor=edge_color, hatch=hatch, zorder=zorder)
    # Shade right face slightly darker
    right_shade = patches.Polygon([p1, p2, p6, p5], facecolor='black', alpha=0.1, zorder=zorder) 
    ax.add_patch(right_poly)
    ax.add_patch(right_shade)

    # 3. Left Face (Front-Left)
    left_poly = patches.Polygon([p0, p1, p5, p4], facecolor=color, alpha=alpha, edgecolor=edge_color, hatch=hatch, zorder=zorder)
    # Shade left face even darker
    left_shade = patches.Polygon([p0, p1, p5, p4], facecolor='black', alpha=0.2, zorder=zorder)
    ax.add_patch(left_poly)
    ax.add_patch(left_shade)

def plot_torsion_member(col_type, c1, c2, h_slab, L1, L2):
    """
    Main function to generate the plot
    col_type: 'interior', 'edge', 'corner'
    Dimensions in relative units (e.g. meters or cm, consistent)
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Config Scaled Dimensions for nice visuals (Not 1:1 engineering scale, but Diagram scale)
    # สมมติหน่วยเทียบสัดส่วนให้สวยงาม
    s_L1 = 12.0 # Span length visual
    s_L2 = 12.0 # Width length visual
    s_c1 = 2.0  # Column size
    s_c2 = 2.0
    s_h = 1.0   # Slab thickness
    
    # Grid Setup (พื้น Grid)
    grid_step = 1.0
    
    # กำหนดขอบเขตของพื้น (Slab Boundaries)
    if col_type == 'interior':
        x_range = (-s_L1/2, s_L1/2)
        y_range = (-s_L2/2, s_L2/2)
        col_pos = (-s_c1/2, -s_c2/2, 0) # Center
        
    elif col_type == 'edge':
        x_range = (-s_L1/2, s_L1/2)
        y_range = (0, s_L2) # ตัดขอบที่ y=0
        col_pos = (-s_c1/2, 0, 0) # Column อยู่ขอบ
        
    elif col_type == 'corner':
        x_range = (0, s_L1) # ตัดขอบที่ x=0
        y_range = (0, s_L2) # ตัดขอบที่ y=0
        col_pos = (0, 0, 0) # Column อยู่มุมสุด
    
    # 1. วาดพื้น Grid (Slab Wireframe)
    # เส้นขนานแกน X
    for y in np.arange(y_range[0], y_range[1] + 0.1, grid_step):
        p_start = iso_project(x_range[0], y, 0)
        p_end = iso_project(x_range[1], y, 0)
        ax.plot([p_start[0], p_end[0]], [p_start[1], p_end[1]], color='#bdc3c7', lw=0.5, zorder=0)
        
    # เส้นขนานแกน Y
    for x in np.arange(x_range[0], x_range[1] + 0.1, grid_step):
        p_start = iso_project(x, y_range[0], 0)
        p_end = iso_project(x, y_range[1], 0)
        ax.plot([p_start[0], p_end[0]], [p_start[1], p_end[1]], color='#bdc3c7', lw=0.5, zorder=0)
        
    # วาดขอบพื้นหนาๆ
    # (Simplified Slab Box)
    slab_origin = (x_range[0], y_range[0], -s_h)
    slab_size = (x_range[1]-x_range[0], y_range[1]-y_range[0], s_h)
    # วาดเฉพาะฐานล่างบางๆ ให้ดูมีความหนา
    # draw_iso_box(ax, slab_origin, slab_size, 'white', alpha=0.1, edge_color='#bdc3c7', zorder=0)

    # 2. วาดเสา (Column)
    # ให้เสาสูงทะลุพื้นขึ้นมา
    col_h = s_h * 3 
    draw_iso_box(ax, (col_pos[0], col_pos[1], -s_h), (s_c1, s_c2, col_h), 
                 color='#7f8c8d', edge_color='k', zorder=10)

    # 3. วาด Torsional Members (Highlight สีแดง)
    t_width = s_c1 # กว้างเท่ากับ c1
    
    # Logic การวาดแขนรับแรงบิด (Arms)
    arms = []
    
    # Arm 1: ทางขวา (+X direction relative to column?) No, Torsion strip is along span usually transvers
    # ตามรูป Torsional member คือแถบข้างเสา (Transverse strip width c1)
    
    # Left Arm (-Y direction)
    if y_range[0] < col_pos[1]: 
        arm_len = col_pos[1] - y_range[0]
        # Origin (x, y, z) -> start from slab edge to column
        arm_origin = (col_pos[0], y_range[0], -s_h) 
        arm_size = (s_c1, arm_len, s_h)
        draw_iso_box(ax, arm_origin, arm_size, color='#e74c3c', alpha=0.4, hatch='///', edge_color='#c0392b', zorder=5)
        
        # Label logic
        cx, cy = iso_project(col_pos[0] + s_c1, y_range[0] + arm_len/2, 0)
        ax.text(cx, cy, "Torsional\nMember", fontsize=9, color='#c0392b', ha='left', va='center')

    # Right Arm (+Y direction)
    if y_range[1] > col_pos[1] + s_c2:
        arm_len = y_range[1] - (col_pos[1] + s_c2)
        arm_origin = (col_pos[0], col_pos[1] + s_c2, -s_h)
        arm_size = (s_c1, arm_len, s_h)
        draw_iso_box(ax, arm_origin, arm_size, color='#e74c3c', alpha=0.4, hatch='///', edge_color='#c0392b', zorder=5)
        
        # Label logic
        cx, cy = iso_project(col_pos[0] + s_c1, col_pos[1] + s_c2 + arm_len/2, 0)
        ax.text(cx, cy, "Torsional\nMember", fontsize=9, color='#c0392b', ha='left', va='center')

    # 4. Dimension Annotations (c1)
    # Project points for c1 line
    c1_p1 = iso_project(col_pos[0], col_pos[1], s_h*2.5)
    c1_p2 = iso_project(col_pos[0]+s_c1, col_pos[1], s_h*2.5)
    
    ax.annotate("", xy=c1_p1, xytext=c1_p2, arrowprops=dict(arrowstyle='<->', lw=1.5))
    ax.text((c1_p1[0]+c1_p2[0])/2, c1_p1[1]+0.5, "c1", ha='center', fontweight='bold')

    # Title & Style
    ax.set_aspect('equal')
    ax.axis('off')
    
    if col_type == 'corner':
        txt = "Corner Column (1 Arm)"
    elif col_type == 'edge':
        txt = "Edge Column (2 Arms)"
    else:
        txt = "Interior Column (2 Arms)"
        
    ax.set_title(txt, fontsize=14, fontweight='bold', y=0.95)
    
    # Set Lim to remove white space
    ax.set_xlim(-15, 15)
    ax.set_ylim(-10, 10)
    
    return fig

# Test Run (ถ้ากด Run ไฟล์นี้ตรงๆ จะโชว์รูป)
if __name__ == "__main__":
    plot_torsion_member('interior', 50, 50, 20, 5, 5)
    plt.show()
