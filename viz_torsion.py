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
def jagged_line(p1, p2, num_jags=4, amp=0.15): # ลดความถี่ลง (num_jags น้อยลง)
    """สร้างพิกัดเส้นหยัก (Break line) แบบ Engineering Style"""
    x1, y1 = p1
    x2, y2 = p2
    
    dx = x2 - x1
    dy = y2 - y1
    dist = np.sqrt(dx**2 + dy**2)
    ux, uy = dx/dist, dy/dist
    nx, ny = -uy, ux 
    
    points = [(x1, y1)]
    step = dist / num_jags
    
    for i in range(1, num_jags):
        bx = x1 + ux * step * i
        by = y1 + uy * step * i
        
        # Zigzag ที่คมขึ้น
        offset = amp if i % 2 != 0 else -amp
        jx = bx + nx * offset
        jy = by + ny * offset
        points.append((jx, jy))
        
    points.append((x2, y2))
    return points

def draw_prism_projected(ax, origin, size, color, alpha=1.0, 
                         edge_color='k', hatch=None, zorder=1, 
                         is_slab=False, cut_sides=[]):
    """วาดกล่อง 3D Isometric"""
    x, y, z = origin
    dx, dy, dz = size
    
    # Vertices
    b0 = iso(x, y, z)
    b1 = iso(x+dx, y, z)
    b2 = iso(x+dx, y+dy, z)
    b3 = iso(x, y+dy, z) # back corner
    
    t0 = iso(x, y, z+dz)
    t1 = iso(x+dx, y, z+dz)
    t2 = iso(x+dx, y+dy, z+dz)
    t3 = iso(x, y+dy, z+dz)
    
    # --- Draw Faces (Visible Only) ---
    poly_props = dict(facecolor=color, alpha=alpha, edgecolor=None, zorder=zorder, hatch=hatch)
    
    # Right Face (+X)
    ax.add_patch(patches.Polygon([b1, b2, t2, t1], **poly_props))
    # Shade Right
    ax.add_patch(patches.Polygon([b1, b2, t2, t1], facecolor='black', alpha=0.1, zorder=zorder))
    
    # Left Face (+Y) - Visible from Front-Left view
    ax.add_patch(patches.Polygon([b0, b1, t1, t0], **poly_props))
    # Shade Left
    ax.add_patch(patches.Polygon([b0, b1, t1, t0], facecolor='black', alpha=0.2, zorder=zorder))
    
    # Top Face
    ax.add_patch(patches.Polygon([t0, t1, t2, t3], **poly_props))
    
    # --- Draw Edges ---
    def plot_edge(p_start, p_end, side_name, lw=1.0):
        if is_slab and side_name in cut_sides:
            pts = jagged_line(p_start, p_end, num_jags=6, amp=0.12) # เส้นหยัก
            x_vals, y_vals = zip(*pts)
            ax.plot(x_vals, y_vals, color=edge_color, lw=lw, zorder=zorder+5)
        else:
            ax.plot([p_start[0], p_end[0]], [p_start[1], p_end[1]], 
                    color=edge_color, lw=lw, zorder=zorder+5)

    # Top Outline
    plot_edge(t0, t1, 'bottom')
    plot_edge(t1, t2, 'right')
    plot_edge(t2, t3, 'top')
    plot_edge(t3, t0, 'left')
    
    # Vertical Corners (Visible)
    plot_edge(t0, b0, 'vert')
    plot_edge(t1, b1, 'vert')
    plot_edge(t2, b2, 'vert') 
    
    # Bottom (Visible)
    plot_edge(b0, b1, 'bottom')
    plot_edge(b1, b2, 'right')

# --- 3. Main Plotter ---
def plot_torsion_member(col_type, c1, c2, h_slab, L1, L2):
    """Generate Professional Engineering Diagram"""
    fig, ax = plt.subplots(figsize=(10, 7))
    
    # Scale Factors (Schematic)
    V_C = 2.0        
    aspect = c2/c1 if c1!=0 else 1
    V_C2 = V_C * aspect
    if V_C2 > V_C * 1.5: V_C2 = V_C * 1.5 
    
    V_H = 0.5        
    V_L = 9.0        
    
    # Settings based on Type
    cut_sides = []
    if col_type == 'interior':
        slab_origin = (-V_L/2, -V_L/2, -V_H)
        slab_size = (V_L, V_L, V_H)
        cut_sides = ['left', 'right', 'top', 'bottom']
        title = "Interior Column (เสาภายใน)"
    elif col_type == 'edge':
        slab_origin = (-V_C/2, -V_L/2, -V_H) 
        slab_size = (V_L - V_C/2 + 1.5, V_L, V_H)
        cut_sides = ['right', 'top', 'bottom']
        title = "Edge Column (เสาขอบ)"
    elif col_type == 'corner':
        slab_origin = (-V_C/2, -V_C2/2, -V_H)
        slab_size = (V_L/1.6, V_L/1.6, V_H)
        cut_sides = ['right', 'top']
        title = "Corner Column (เสามุม)"

    # 1. Draw Slab
    draw_prism_projected(ax, slab_origin, slab_size, 
                         color='#f4f6f7', is_slab=True, cut_sides=cut_sides, zorder=0, edge_color='#7f8c8d')

    # 2. Draw Grid (Faint)
    grid_z = 0
    sx, sy, sz = slab_origin
    dx, dy, dz = slab_size
    
    for yi in np.linspace(sy, sy+dy, 7): # X-Grid
        p1 = iso(sx, yi, grid_z)
        p2 = iso(sx+dx, yi, grid_z)
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color='#bdc3c7', lw=0.4, zorder=1, alpha=0.6)
    
    for xi in np.linspace(sx, sx+dx, 7): # Y-Grid
        p1 = iso(xi, sy, grid_z)
        p2 = iso(xi, sy+dy, grid_z)
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color='#bdc3c7', lw=0.4, zorder=1, alpha=0.6)

    # 3. Draw Column
    col_h = V_H * 5.5
    col_origin = (-V_C/2, -V_C2/2, -V_H)
    draw_prism_projected(ax, col_origin, (V_C, V_C2, col_h), 
                         color='#95a5a6', edge_color='#2c3e50', zorder=10)

    # 4. Draw Torsional Members (Highlight)
    t_color = '#e74c3c'
    t_hatch = '////'
    
    def draw_arm(y_start, y_len):
        orig = (-V_C/2, y_start, -V_H)
        siz = (V_C, y_len, V_H)
        draw_prism_projected(ax, orig, siz, color=t_color, alpha=0.4, 
                             edge_color='#c0392b', hatch=t_hatch, zorder=5)
        return orig, siz

    arm_centers = [] # Store center points for annotation
    
    if col_type == 'interior' or col_type == 'edge':
        # Arm 1 (+Y)
        orig, siz = draw_arm(V_C2/2, (dy/2 - V_C2/2))
        arm_centers.append(iso(orig[0]+siz[0], orig[1]+siz[1]/2, 0)) # Point right side
        
        # Arm 2 (-Y)
        orig, siz = draw_arm(-dy/2, (dy/2 - V_C2/2))
        
    elif col_type == 'corner':
        orig, siz = draw_arm(V_C2/2, (dy - V_C2))
        arm_centers.append(iso(orig[0]+siz[0], orig[1]+siz[1]/2, 0))

    # --- 5. Professional Annotations ---
    
    # 5.1 Leader Line for Torsional Member (ดึงป้ายออกมาข้างนอก)
    if arm_centers:
        target_pt = arm_centers[0] # Point to the first arm
        text_pt = (target_pt[0] + 3, target_pt[1] + 2) # Offset position
        
        ax.annotate("Torsional Member\n(Transverse Strip)", 
                    xy=target_pt, xycoords='data',
                    xytext=text_pt, textcoords='data',
                    arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=.2", color='#c0392b', lw=1.5),
                    fontsize=10, fontweight='bold', color='#922b21',
                    bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#c0392b", alpha=0.9))

    # 5.2 Dimension c1 (Clearance improved)
    dim_h = col_h + 0.5 # Higher up
    d1 = iso(-V_C/2, -V_C2/2, dim_h)
    d2 = iso(V_C/2, -V_C2/2, dim_h)
    
    ax.annotate("", xy=d1, xytext=d2, arrowprops=dict(arrowstyle='<|-|>', lw=1.2, color='black'))
    mid_c1 = iso(0, -V_C2/2, dim_h + 0.3)
    ax.text(mid_c1[0], mid_c1[1], f"$c_1$ = {c1:.0f} cm", ha='center', va='bottom', fontweight='bold')

    # 5.3 L2 Direction (Natural placement)
    l2_y = -dy/2 + 1.5
    l2_p1 = iso(sx + 1.5, l2_y, 0)
    l2_p2 = iso(sx + dx - 1.5, l2_y, 0)
    ax.annotate("", xy=l2_p1, xytext=l2_p2, arrowprops=dict(arrowstyle='<|-|>', color='blue', lw=1.0))
    l2_mid = iso(sx + dx/2, l2_y, 0.3)
    ax.text(l2_mid[0], l2_mid[1], f"Direction $L_2$ (Span: {L2} m)", color='blue', ha='center', fontsize=9, fontstyle='italic')

    # Final Config
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title(title, fontsize=14, fontweight='bold', y=0.95)
    
    # Auto Scale
    ax.relim()
    ax.autoscale_view()
    # Padding
    ax.set_xlim(ax.get_xlim()[0]-1, ax.get_xlim()[1]+1)
    
    plt.tight_layout()
    return fig

if __name__ == "__main__":
    plot_torsion_member('interior', 40, 40, 20, 6, 6)
    plt.show()
