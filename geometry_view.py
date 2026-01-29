import matplotlib.pyplot as plt
import matplotlib.patches as patches

def plot_geometry_detailed(L1, L2, c1, c2, h_slab, lc, Ic_val):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 12), gridspec_kw={'height_ratios': [2, 1]})
    
    # Conversions
    c1_m, c2_m, h_m = c1/100, c2/100, h_slab/100
    margin_x, margin_y = L1*0.2, L2*0.2

    # --- TOP VIEW ---
    ax1.set_title("PLAN VIEW (Top View)", fontsize=12, fontweight='bold', loc='left', pad=10)
    col_coords = [(0,0), (L1,0), (0,L2), (L1,L2)]
    
    # Draw Slab & Strips
    ax1.add_patch(patches.Rectangle((-margin_x/2, -margin_y/2), L1+margin_x, L2+margin_y, 
                                    facecolor='#f8f9fa', edgecolor='#dee2e6', zorder=0))
    # Grid lines
    for x in [0, L1]: ax1.axvline(x=x, color='#adb5bd', linestyle='-.', lw=0.8)
    for y in [0, L2]: ax1.axhline(y=y, color='#adb5bd', linestyle='-.', lw=0.8)

    # Columns
    for (cx, cy) in col_coords:
        ax1.add_patch(patches.Rectangle((cx - c1_m/2, cy - c2_m/2), c1_m, c2_m,
                                        linewidth=1, edgecolor='black', facecolor='#343a40', zorder=5))

    # Dimensions
    def draw_dim(ax, p1, p2, text, off_x=0, off_y=0):
        ax.annotate('', xy=p1, xytext=p2, arrowprops=dict(arrowstyle='<|-|>', color='#0d6efd', lw=1))
        mx, my = (p1[0]+p2[0])/2 + off_x, (p1[1]+p2[1])/2 + off_y
        ax.text(mx, my, text, ha='center', va='center', color='#0d6efd', fontweight='bold', fontsize=9,
                bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.8))

    draw_dim(ax1, (0, -c2_m*1.5), (L1, -c2_m*1.5), f"L1 = {L1} m", off_y=-0.2)
    draw_dim(ax1, (-c1_m*1.5, 0), (-c1_m*1.5, L2), f"L2 = {L2} m", off_x=-0.2)

    # Annotation
    ax1.annotate(f"Column\n{c1}x{c2} cm\nIc={Ic_val:,.0f} cm4", xy=(0,0), xytext=(L1*0.15, L2*0.15),
                 arrowprops=dict(arrowstyle='->', color='#dc3545'), color='#dc3545', fontweight='bold')

    ax1.axis('equal'); ax1.axis('off')

    # --- SECTION VIEW ---
    ax2.set_title("SECTION A-A", fontsize=12, fontweight='bold', loc='left')
    ax2.axhline(y=0, color='black', lw=2) # Ground
    
    # Column & Slab
    ax2.add_patch(patches.Rectangle((-c1_m/2, 0), c1_m, lc, fc='#343a40', ec='black'))
    ax2.add_patch(patches.Rectangle((-L1*0.3, lc-h_m), L1*1.0, h_m, fc='#e9ecef', hatch='///', ec='#adb5bd'))
    
    # Dims
    draw_dim(ax2, (c1_m*1.5, 0), (c1_m*1.5, lc), f"lc = {lc} m", off_x=0.3)
    draw_dim(ax2, (-L1*0.2, lc-h_m), (-L1*0.2, lc), f"h = {h_slab} cm", off_x=-0.3)
    
    ax2.axis('equal'); ax2.axis('off')
    plt.tight_layout()
    return fig
