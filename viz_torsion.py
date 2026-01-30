import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# --- 1. Isometric Math Core ---
def iso(x, y, z):
    """Transform 3D (x,y,z) to 2D Isometric projection (30 deg)"""
    angle = np.radians(30)
    xi = (x - y) * np.cos(angle)
    yi = (x + y) * np.sin(angle) + z
    return xi, yi

# --- 2. Helper Functions ---
def jagged_line(p1, p2, num_jags=6, amp=0.2):
    """สร้างพิกัดเส้นหยัก (Break line) ระหว่างจุด p1 และ p2"""
    x1, y1 = p1
    x2, y2 = p2
    
    # Vector
    dx = x2 - x1
    dy = y2 - y1
    dist = np.sqrt(dx**2 + dy**2)
    ux, uy = dx/dist, dy/dist # Unit vector
    nx, ny = -uy, ux # Normal vector
    
    points = [(x1, y1)]
    step = dist / num_jags
    
    for i in range(1, num_jags):
        # Base point on the line
        bx = x1 + ux * step * i
        by = y1 + uy * step * i
        
        # Zigzag offset (สลับขึ้นลง)
        offset = amp if i % 2 != 0 else -amp
        jx = bx + nx * offset
        jy = by + ny * offset
        points.append((jx, jy))
        
    points.append((x2, y2))
    return points

def draw_prism_projected(ax, origin, size, color, alpha=1.0, 
                         edge_color='k', hatch=None, zorder=1, 
                         is_slab=False, cut_sides=[]):
    """
    วาดกล่อง 3D โดยคำนวณพิกัด Isometric แล้ววาดลง 2D
    feature พิเศษ: is_slab=True จะทำให้ขอบที่ระบุใน cut_sides เป็นเส้นหยัก
    """
    x, y, z = origin
    dx, dy, dz = size
    
    # Key Vertices (Bottom & Top)
    # 0=Origin, 1=+x, 2=+x+y, 3=+y
    b0 = iso(x, y, z)
    b1 = iso(x+dx, y, z)
    b2 = iso(x+dx, y+dy, z)
    b3 = iso(x, y+dy, z)
    
    t0 = iso(x, y, z+dz)
    t1 = iso(x+dx, y, z+dz)
    t2 = iso(x+dx, y+dy, z+dz)
    t3 = iso(x, y+dy, z+dz)
    
    # --- 1. Draw Faces (Painter's Algo: Back -> Front) ---
    
    # Style props
    poly_props = dict(facecolor=color, alpha=alpha, edgecolor=None, zorder=zorder, hatch=hatch)

    # Visible Faces for standard iso view (Top, Right, Left)
    
    # Left Face (+Y side, seen from left) -> (x, y+dy) to (x, y)
    # Actually in standard ISO: Left face is Plane X=0 (b0-b3-t3-t0) and Plane Y=0 (b0-b1-t1-t0) ?? 
    # Let's stick to "Visible" surfaces: Top (z+), Front-Right (x+), Front-Left (y+)
    
    # Front-Right Face (Plane at y=0 is not visible, Plane at x=dx is visible)
    # Let's draw sides first
    
    # Side 1: Right (+X face) -> b1-b2-t2-t1
    ax.add_patch(patches.Polygon([b1, b2, t2, t1], **poly_props))
    # Shade Right
    ax.add_patch(patches.Polygon([b1, b2, t2, t1], facecolor='black', alpha=0.1, zorder=zorder))
    
    # Side 2: Left (+Y face) -> b0-b1-t1-t0 (Front) OR b3-b2-t2-t3 (Back)?
    # Isometric view standard: We see Top, South-East, South-West.
    # South-East (Right) = Plane x+ (b1-b2-t2-t1) ? No. 
    # Let's keep it simple: We draw the faces that "stick out".
    
    # Side Left (Standard View): Plane x=x (Front-Left) -> b0-b1-t1-t0
    ax.add_patch(patches.Polygon([b0, b1, t1, t0], **poly_props))
    # Shade Left (Darker)
    ax.add_patch(patches.Polygon([b0, b1, t1, t0], facecolor='black', alpha=0.2, zorder=zorder))
    
    # Top Face: t0-t1-t2-t3
    ax.add_patch(patches.Polygon([t0, t1, t2, t3], **poly_props))
    
    # --- 2. Draw Edges (Outline) ---
    # ถ้าเป็น Slab และมี Cut Sides ให้วาดเส้นหยัก
    
    def plot_edge(p_start, p_end, side_name):
        if is_slab and side_name in cut_sides:
            # Draw Jagged
            pts = jagged_line(p_start, p_end, num_jags=8, amp=0.15)
            x_vals, y_vals = zip(*pts)
            ax.plot(x_vals, y_vals, color=edge_color, lw=0.8, zorder=zorder+5)
        else:
            # Draw Straight
            ax.plot([p_start[0], p_end[0]], [p_start[1], p_end[1]], 
                    color=edge_color, lw=0.8 if is_slab else 1.2, zorder=zorder+5)

    # Top Edges
    plot_edge(t0, t1, 'bottom') # x-axis near
    plot_edge(t1, t2, 'right')  # y-axis far
    plot_edge(t2, t3, 'top')    # x-axis far
    plot_edge(t3, t0, 'left')   # y-axis near
    
    # Vertical Edges (Corner pillars)
    # Only draw visible verticals: t0-b0, t1-b1, t3-b3 (t2-b2 is hidden behind)
    plot_edge(t0, b0, 'vert')
    plot_edge(t1, b1, 'vert')
    plot_edge(t3, b3, 'vert')
    
    # Bottom Edges (Visible ones)
    plot_edge(b0, b1, 'bottom')
    plot_edge(b0, b3, 'left')

# --- 3. Main Plotter ---
def plot_torsion_member(col_type, c1, c2, h_slab, L1, L2):
    """
    Generate High-Quality Engineering Diagram
    """
    fig, ax = plt.subplots(figsize=(10, 6.5))
    
    # --- Scale Settings (Visual Units) ---
    # ใช้สเกลสมมติเพื่อให้รูปสวย ไม่ใช่สเกลจริง 1:1
    V_C = 2.0         # Column Base Size
    aspect = c2/c1 if c1!=0 else 1
    V_C2 = V_C * aspect
    if V_C2 > V_C * 1.5: V_C2 = V_C * 1.5 # Limit aspect
    
    V_H = 0.6         # Slab Thickness (บางลงให้ดูสมจริง)
    V_L = 10.0        # Slab Width
    
    # Define Limits & Cut sides based on Type
    cut_sides = []
    
    if col_type == 'interior':
        slab_origin = (-V_L/2, -V_L/2, -V_H)
        slab_size = (V_L, V_L, V_H)
        cut_sides = ['left', 'right', 'top', 'bottom']
        title = "Interior Column (เสาภายใน)"
        arms = ['right_arm', 'left_arm'] # relative to layout
        
    elif col_type == 'edge':
        # เสาอยู่ขอบซ้าย (สมมติ)
        slab_origin = (-V_C/2, -V_L/2, -V_H) 
        slab_size = (V_L - V_C/2 + 2, V_L, V_H) # พื้นยื่นไปทางขวา
        cut_sides = ['right', 'top', 'bottom'] # Left is straight (edge)
        title = "Edge Column (เสาขอบ)"
        arms = ['right_arm', 'left_arm'] 
        
    elif col_type == 'corner':
        slab_origin = (-V_C/2, -V_C2/2, -V_H)
        slab_size = (V_L/1.5, V_L/1.5, V_H)
        cut_sides = ['right', 'top'] # Left and Bottom are edges
        title = "Corner Column (เสามุม)"
        arms = ['one_arm'] # usually strictly dependent on analysis direction, let's show the transverse one

    # --- 1. Draw Slab (Concrete) ---
    draw_prism_projected(ax, slab_origin, slab_size, 
                         color='#ecf0f1', is_slab=True, cut_sides=cut_sides, zorder=0)

    # --- 2. Draw Grid (Engineering Grid) ---
    # วาด Grid จางๆ บนผิวพื้นเพื่อให้ดูมี Scale
    grid_z = 0
    sx, sy, sz = slab_origin
    dx, dy, dz = slab_size
    
    # Grid X
    for yi in np.linspace(sy, sy+dy, 6):
        p1 = iso(sx, yi, grid_z)
        p2 = iso(sx+dx, yi, grid_z)
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color='#bdc3c7', lw=0.3, zorder=1)
    
    # Grid Y
    for xi in np.linspace(sx, sx+dx, 6):
        p1 = iso(xi, sy, grid_z)
        p2 = iso(xi, sy+dy, grid_z)
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color='#bdc3c7', lw=0.3, zorder=1)

    # --- 3. Draw Column ---
    col_h = V_H * 5
    col_origin = (-V_C/2, -V_C2/2, -V_H)
    draw_prism_projected(ax, col_origin, (V_C, V_C2, col_h), 
                         color='#95a5a6', edge_color='#2c3e50', zorder=10)

    # --- 4. Draw Torsional Members (Highlight) ---
    # Torsional Member = Strip of slab width c1 centered on column
    
    t_color = '#e74c3c' # Red
    t_hatch = '///'
    
    # Helper to draw arm
    def draw_arm(y_start, y_len):
        orig = (-V_C/2, y_start, -V_H)
        siz = (V_C, y_len, V_H)
        draw_prism_projected(ax, orig, siz, color=t_color, alpha=0.4, 
                             edge_color='#c0392b', hatch=t_hatch, zorder=5)

    if col_type == 'interior' or col_type == 'edge':
        # Arm 1 (+Y)
        draw_arm(V_C2/2, (dy/2 - V_C2/2))
        # Arm 2 (-Y)
        draw_arm(-dy/2, (dy/2 - V_C2/2))
        
    elif col_type == 'corner':
        # Arm (+Y only for example)
        draw_arm(V_C2/2, (dy - V_C2))

    # --- 5. Annotations ---
    
    # 5.1 Text Label: Torsional Member
    # หาตำแหน่งวาง Text ให้ไม่ทับรูป
    lbl_pt = iso(V_C, V_C2 + 1.5, V_H)
    ax.text(lbl_pt[0], lbl_pt[1], "Torsional Member\n(Transverse Strip)", 
            color='#c0392b', fontweight='bold', fontsize=9, va='center',
            bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', pad=1))

    # 5.2 Dimension c1 (สำคัญมาก)
    # ยกเส้น Dimension ขึ้นไปเหนือหัวเสา
    dim_h = col_h * 0.8
    d1 = iso(-V_C/2, -V_C2/2, dim_h)
    d2 = iso(V_C/2, -V_C2/2, dim_h)
    
    ax.annotate("", xy=d1, xytext=d2, arrowprops=dict(arrowstyle='<->', lw=1.2))
    mid_c1 = iso(0, -V_C2/2, dim_h + 0.5)
    ax.text(mid_c1[0], mid_c1[1], f"$c_1$ = {c1:.0f} cm", ha='center', color='black', fontweight='bold')

    # 5.3 Dimension c2 (ถ้าเป็น 3D ควรเห็น c2 ด้วย)
    d3 = iso(V_C/2, V_C2/2, dim_h)
    ax.annotate("", xy=d2, xytext=d3, arrowprops=dict(arrowstyle='<->', lw=1.2))
    mid_c2 = iso(V_C/2 + 0.5, 0, dim_h)
    ax.text(mid_c2[0], mid_c2[1], f"$c_2$", ha='left', va='center', color='black', fontsize=9)

    # 5.4 L2 Direction (วางบนพื้น)
    l2_y = -dy/2 + 1
    l2_p1 = iso(sx + 1, l2_y, 0)
    l2_p2 = iso(sx + dx - 1, l2_y, 0)
    ax.annotate("", xy=l2_p1, xytext=l2_p2, arrowprops=dict(arrowstyle='<->', color='blue', lw=1.0))
    l2_mid = iso(sx + dx/2, l2_y, 0.5)
    ax.text(l2_mid[0], l2_mid[1], f"Direction $L_2$ (Span: {L2} m)", color='blue', ha='center', fontsize=9)

    # Final Setup
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title(title, fontsize=14, fontweight='bold', y=0.95)
    
    # Zoom limits
    ax.set_xlim(-8, 8)
    ax.set_ylim(-6, 8)
    
    plt.tight_layout()
    return fig

if __name__ == "__main__":
    plot_torsion_member('interior', 40, 40, 20, 6, 6)
    plt.show()
