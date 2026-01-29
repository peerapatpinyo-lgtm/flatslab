import matplotlib.pyplot as plt
import matplotlib.patches as patches

def plot_geometry_detailed(L1, L2, c1, c2, h_slab, lc, Ic_val):
    """
    วาด 2 มุมมอง: Top View (Plan) และ Side View (Section)
    รับค่า:
    - L1, L2, lc (เมตร)
    - c1, c2, h_slab (เซนติเมตร -> จะถูกแปลงเป็นเมตรในฟังก์ชัน)
    - Ic_val (ค่า Inertia สำหรับแสดงโชว์)
    """
    # Create Figure with 2 Subplots (Top View ใหญ่กว่า Side View หน่อย)
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 12), gridspec_kw={'height_ratios': [2, 1]})
    
    # Common Conversions (Plotting in Meters)
    c1_m = c1 / 100.0
    c2_m = c2 / 100.0
    h_m = h_slab / 100.0
    margin_x = L1 * 0.2
    margin_y = L2 * 0.2

    # ==========================================
    # VIEW 1: TOP VIEW (PLAN) -> L1, L2, c1, c2, Ic
    # ==========================================
    ax1.set_title("TOP VIEW (Plan)", fontsize=14, fontweight='bold', pad=15)
    
    # 1. Draw Columns
    col_coords = [(0,0), (L1,0), (0,L2), (L1,L2)]
    for (cx, cy) in col_coords:
        rect = patches.Rectangle(
            (cx - c1_m/2, cy - c2_m/2), c1_m, c2_m,
            linewidth=1.5, edgecolor='black', facecolor='#6c757d', zorder=5
        )
        ax1.add_patch(rect)

    # 2. Draw Slab Outline & Strips
    ax1.add_patch(patches.Rectangle((-margin_x/2, -margin_y/2), L1+margin_x, L2+margin_y, 
                                    facecolor='#e9ecef', edgecolor='black', linestyle='--', alpha=0.5, zorder=0))
    
    # Centerlines
    ax1.axvline(x=0, color='black', linestyle='-.', alpha=0.3)
    ax1.axvline(x=L1, color='black', linestyle='-.', alpha=0.3)
    ax1.axhline(y=0, color='black', linestyle='-.', alpha=0.3)
    ax1.axhline(y=L2, color='black', linestyle='-.', alpha=0.3)

    # 3. Dimensions Helper
    def draw_dim(ax, p1, p2, text, offset_x=0, offset_y=0, color='blue'):
        ax.annotate('', xy=p1, xytext=p2, arrowprops=dict(arrowstyle='<->', color=color, lw=1.5))
        mid_x, mid_y = (p1[0]+p2[0])/2 + offset_x, (p1[1]+p2[1])/2 + offset_y
        ax.text(mid_x, mid_y, text, ha='center', va='center', color=color, fontweight='bold', 
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=color, alpha=0.8))

    # Dim L1, L2
    draw_dim(ax1, (0, -c2_m*2), (L1, -c2_m*2), f"L1 = {L1} m", offset_y=-0.3)
    draw_dim(ax1, (-c1_m*2, 0), (-c1_m*2, L2), f"L2 = {L2} m", offset_x=-0.3)

    # 4. Column Details (c1, c2, Ic)
    ax1.text(0, c2_m, f"c1 = {c1} cm", ha='center', va='bottom', fontsize=9, color='red')
    ax1.text(c1_m, 0, f"c2 = {c2} cm", ha='left', va='center', fontsize=9, color='red', rotation=90)
    
    # Ic Label
    ax1.annotate(f"Ic = {Ic_val:,.0f} cm⁴", xy=(0, 0), xytext=(L1*0.2, L2*0.2),
                 arrowprops=dict(arrowstyle='->', connectionstyle="arc3,rad=.2", color='purple', lw=1.5),
                 color='purple', fontweight='bold', fontsize=11,
                 bbox=dict(boxstyle="round,pad=0.3", fc="#f3e5f5", ec="purple"))

    ax1.set_xlim(-margin_x, L1 + margin_x)
    ax1.set_ylim(-margin_y, L2 + margin_y)
    ax1.set_aspect('equal')
    ax1.axis('off')

    # ==========================================
    # VIEW 2: SIDE VIEW (SECTION) -> h, lc
    # ==========================================
    ax2.set_title("SECTION VIEW (A-A)", fontsize=14, fontweight='bold', pad=15)
    
    # Ground Line
    ax2.axhline(y=0, color='black', linewidth=2)
    
    # Draw Columns
    col_width_view = c1_m 
    ax2.add_patch(patches.Rectangle((-col_width_view/2, 0), col_width_view, lc, 
                                    facecolor='#6c757d', edgecolor='black'))
    ax2.add_patch(patches.Rectangle((-col_width_view/2, lc), col_width_view, lc*0.3, 
                                    facecolor='#6c757d', edgecolor='black', linestyle='--'))
    
    # Draw Slab
    slab_y_bottom = lc - h_m
    ax2.add_patch(patches.Rectangle((-L1*0.5, slab_y_bottom), L1*1.5, h_m, 
                                    facecolor='#adb5bd', hatch='///', edgecolor='black'))

    # Dimensions (h, lc)
    draw_dim(ax2, (col_width_view, 0), (col_width_view, lc), f"lc = {lc} m", offset_x=0.5, color='black')
    draw_dim(ax2, (L1*0.5, slab_y_bottom), (L1*0.5, lc), f"h = {h_slab} cm", offset_x=0.6, color='red')

    ax2.set_xlim(-L1*0.2, L1*0.8) 
    ax2.set_ylim(0, lc * 1.4)
    ax2.set_aspect('equal')
    ax2.axis('off')

    plt.tight_layout()
    return fig
