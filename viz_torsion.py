import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.path as mpath
import numpy as np

# --- 1. Isometric Math Core ---
def iso(x, y, z):
    """Transform 3D (x,y,z) to 2D Isometric projection"""
    # Angle 30 degrees standard isometric
    angle = np.radians(30)
    # Isometric equations
    xi = (x - y) * np.cos(angle)
    yi = (x + y) * np.sin(angle) + z
    return xi, yi

# --- 2. Drawing Primitives ---
def draw_poly(ax, points, color, alpha=1.0, edge_color='k', lw=1.0, zorder=1, hatch=None, ls='-'):
    """Helper to draw a polygon"""
    poly = patches.Polygon(points, facecolor=color, alpha=alpha, 
                           edgecolor=edge_color, linewidth=lw, zorder=zorder, hatch=hatch, linestyle=ls)
    ax.add_patch(poly)

def draw_prism(ax, origin, size, color, alpha=1.0, edge_color='k', hatch=None, zorder=1, hidden_lines=False):
    """Draw a 3D box (Prism)"""
    x, y, z = origin
    dx, dy, dz = size
    
    # Vertices
    # Bottom
    b1 = iso(x, y, z)
    b2 = iso(x+dx, y, z)
    b3 = iso(x+dx, y+dy, z)
    b4 = iso(x, y+dy, z)
    # Top
    t1 = iso(x, y, z+dz)
    t2 = iso(x+dx, y, z+dz)
    t3 = iso(x+dx, y+dy, z+dz)
    t4 = iso(x, y+dy, z+dz)

    # Surfaces (Draw order: Back -> Front for Painter's Algorithm basic)
    # But usually we just draw visible faces: Top, Right (+x), Left (+y)
    
    # Left Face (+Y side from x perspective) -> visible if looking from corner
    draw_poly(ax, [b4, b3, t3, t4], color, alpha, edge_color, zorder=zorder, hatch=hatch) # Back-Left
    draw_poly(ax, [b1, b2, t2, t1], color, alpha, edge_color, zorder=zorder+1, hatch=hatch) # Front-Right
    draw_poly(ax, [b1, b4, t4, t1], color, alpha, edge_color, zorder=zorder+1, hatch=hatch) # Front-Left

    # Top Face
    draw_poly(ax, [t1, t2, t3, t4], color, alpha, edge_color, zorder=zorder+2, hatch=hatch)
    
    # Shading (Fake Light from Top-Left)
    # Right face darker
    draw_poly(ax, [b2, b3, t3, t2], 'black', 0.1, None, zorder=zorder+1) 
    # Left face darker
    draw_poly(ax, [b1, b4, t4, t1], 'black', 0.2, None, zorder=zorder+1)

def draw_slab_outline(ax, x_range, y_range, z, h, color='#ecf0f1'):
    """Draws the main slab plate"""
    x0, x1 = x_range
    y0, y1 = y_range
    
    # Draw bottom plate (faint)
    draw_prism(ax, (x0, y0, z), (x1-x0, y1-y0, h), color, alpha=0.8, edge_color='#bdc3c7', zorder=0)

# --- 3. Main Plotter ---
def plot_torsion_member(col_type, c1, c2, h_slab, L1, L2):
    """
    Generate High-Quality Diagram
    """
    fig, ax = plt.subplots(figsize=(10, 7))
    
    # --- Visual Parameters (Schematic Scale) ---
    # Convert inputs to visual units to keep diagram proportional
    # S = Scale factor
    S_Col = 2.0  # Visual column size
    S_H   = 0.8  # Visual slab thickness
    S_L   = 8.0  # Visual span length to show context
    
    # Calculate visual proportions
    # Assume c1/c2 ratio is kept, but scaled to S_Col
    aspect = c1/c2 if c2 != 0 else 1
    v_c1 = S_Col
    v_c2 = S_Col / aspect if aspect > 1 else S_Col 
    # Limit extreme aspect ratios for drawing
    if v_c2 < 1.0: v_c2 = 1.0
    
    v_h = S_H
    
    # Origins
    cx, cy = 0, 0 # Center of column
    
    # Setup Slab Limits (The "Cut-out")
    if col_type == 'interior':
        slab_x = (-S_L/2, S_L/2)
        slab_y = (-S_L/2, S_L/2)
        title = "Interior Column: Torsional Member (2 Sides)"
        arms = ['top', 'bottom']
        
    elif col_type == 'edge':
        slab_x = (-v_c1/2, S_L/2) # Cut at column face (Edge)
        slab_y = (-S_L/2, S_L/2)
        title = "Edge Column: Torsional Member (2 Sides)"
        arms = ['top', 'bottom']
        
    elif col_type == 'corner':
        slab_x = (-v_c1/2, S_L/2)
        slab_y = (-v_c2/2, S_L/2)
        title = "Corner Column: Torsional Member (1 Side)"
        arms = ['top'] # Usually checks the one connected to the main frame or weak axis
    
    # --- DRAWING ---
    
    # 1. SLAB (Base Context)
    draw_prism(ax, 
               (slab_x[0], slab_y[0], -v_h), 
               (slab_x[1]-slab_x[0], slab_y[1]-slab_y[0], v_h), 
               color='#f7f9f9', alpha=0.9, edge_color='#bdc3c7', zorder=0)
    
    # 2. SLAB GRID (Engineering Look)
    grid_spacing = 1.0
    # X-Direction Grid
    for y_line in np.arange(int(slab_y[0]), int(slab_y[1])+1, grid_spacing):
        p1 = iso(slab_x[0], y_line, 0)
        p2 = iso(slab_x[1], y_line, 0)
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color='#bdc3c7', lw=0.5, zorder=1)
    # Y-Direction Grid
    for x_line in np.arange(int(slab_x[0]), int(slab_x[1])+1, grid_spacing):
        p1 = iso(x_line, slab_y[0], 0)
        p2 = iso(x_line, slab_y[1], 0)
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color='#bdc3c7', lw=0.5, zorder=1)

    # 3. COLUMN (Structure)
    col_height = v_h * 4
    col_origin = (-v_c1/2, -v_c2/2, -v_h)
    draw_prism(ax, col_origin, (v_c1, v_c2, col_height), 
               color='#7f8c8d', edge_color='#2c3e50', zorder=10)

    # 4. TORSIONAL MEMBERS (The Hero)
    # This is the strip of width c1 extending from the column
    t_color = '#e74c3c' # Alizarin Red
    t_hatch = '////'
    
    for arm in arms:
        if arm == 'top': # +Y direction
            # Calculate length to edge of slab
            arm_len = slab_y[1] - (v_c2/2)
            if arm_len > 0:
                origin = (-v_c1/2, v_c2/2, -v_h)
                size = (v_c1, arm_len, v_h)
                draw_prism(ax, origin, size, color=t_color, alpha=0.5, 
                           edge_color='#c0392b', hatch=t_hatch, zorder=5)
                
                # Label
                lx, ly = iso(0, v_c2/2 + arm_len/2, 0)
                ax.text(lx, ly, "Torsional\nMember", color='#922b21', 
                        fontweight='bold', fontsize=9, ha='center', va='center',
                        bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=1))

        elif arm == 'bottom': # -Y direction
            arm_len = abs(slab_y[0] - (-v_c2/2))
            if arm_len > 0:
                origin = (-v_c1/2, -v_c2/2 - arm_len, -v_h)
                size = (v_c1, arm_len, v_h)
                draw_prism(ax, origin, size, color=t_color, alpha=0.5, 
                           edge_color='#c0392b', hatch=t_hatch, zorder=5)

    # 5. DIMENSIONS & ANNOTATIONS
    
    # c1 Dimension (Width of Torsional Member)
    # Draw dimension line above the column
    dim_h = col_height * 0.7
    d1 = iso(-v_c1/2, -v_c2/2, dim_h)
    d2 = iso(v_c1/2, -v_c2/2, dim_h)
    
    # Arrow line
    ax.annotate("", xy=d1, xytext=d2, arrowprops=dict(arrowstyle='<->', lw=1.5))
    # Text
    tmpx, tmpy = iso(0, -v_c2/2, dim_h + 0.5)
    ax.text(tmpx, tmpy, f"$c_1$ (Width)", ha='center', fontweight='bold')
    
    # L2 Direction Arrow (Transverse)
    # Place it on the slab
    l2_start = iso(S_L/3, 0, 0)
    l2_end   = iso(S_L/3, S_L/3, 0)
    ax.annotate("", xy=l2_start, xytext=l2_end, arrowprops=dict(arrowstyle='<-', color='blue', lw=1.5))
    l2_txt = iso(S_L/3, S_L/6, 0.2)
    ax.text(l2_txt[0], l2_txt[1], "Transverse ($L_2$)", color='blue', fontsize=8, rotation=-30)

    # --- FINAL SETTINGS ---
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    
    # Zoom/Crop
    limit = 6
    ax.set_xlim(-limit, limit)
    ax.set_ylim(-limit/2, limit)
    
    plt.tight_layout()
    return fig

if __name__ == "__main__":
    plot_torsion_member('interior', 40, 40, 20, 5, 5)
    plt.show()
