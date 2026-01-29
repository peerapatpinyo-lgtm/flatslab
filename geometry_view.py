import matplotlib.pyplot as plt
import matplotlib.patches as patches
import streamlit as st

def plot_flat_slab_plan(L1, L2, c1, c2):
    """
    L1, L2: Span lengths in meters
    c1, c2: Column dimensions in cm (will be converted to m)
    """
    # Convert column dims to meters
    c1_m = c1 / 100.0
    c2_m = c2 / 100.0
    
    # Setup Figure
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # 1. Draw Columns (At 4 corners of the panel)
    # Coordinates of column centers: (0,0), (L1,0), (0,L2), (L1,L2)
    col_centers = [(0, 0), (L1, 0), (0, L2), (L1, L2)]
    
    for (cx, cy) in col_centers:
        # Create Rectangle (xy is bottom-left corner)
        rect = patches.Rectangle(
            (cx - c1_m/2, cy - c2_m/2), c1_m, c2_m, 
            linewidth=1.5, edgecolor='black', facecolor='#404040', zorder=5
        )
        ax.add_patch(rect)

    # 2. Draw Slab Outline (The Panel)
    # Extend slightly beyond columns for visual context
    margin = 1.0 # meters
    ax.set_xlim(-margin, L1 + margin)
    ax.set_ylim(-margin, L2 + margin)
    
    # 3. Draw Centerlines (Grid Lines)
    ax.axvline(x=0, color='black', linestyle='-.', linewidth=0.8, alpha=0.5)
    ax.axvline(x=L1, color='black', linestyle='-.', linewidth=0.8, alpha=0.5)
    ax.axhline(y=0, color='black', linestyle='-.', linewidth=0.8, alpha=0.5)
    ax.axhline(y=L2, color='black', linestyle='-.', linewidth=0.8, alpha=0.5)

    # 4. Draw Strips (Column Strip vs Middle Strip)
    # Definition: Column Strip width is 0.25 * min(L1, L2) on each side of centerline
    min_span = min(L1, L2)
    cs_width_side = 0.25 * min_span
    
    # Draw Column Strip Zones (Horizontal Flow)
    # Bottom CS
    ax.add_patch(patches.Rectangle((-margin, -cs_width_side), L1 + 2*margin, 2*cs_width_side, 
                                   color='blue', alpha=0.1, label='Column Strip'))
    # Top CS
    ax.add_patch(patches.Rectangle((-margin, L2-cs_width_side), L1 + 2*margin, 2*cs_width_side, 
                                   color='blue', alpha=0.1))
    
    # Middle Strip
    ax.add_patch(patches.Rectangle((-margin, cs_width_side), L1 + 2*margin, L2 - 2*cs_width_side, 
                                   color='green', alpha=0.1, label='Middle Strip'))

    # Dashed lines separating strips
    ax.hlines(y=[cs_width_side, L2-cs_width_side], xmin=-margin, xmax=L1+margin, 
              colors='blue', linestyles='--', linewidth=1)

    # 5. Dimension Lines (Annotations)
    
    def draw_dim(p1, p2, text, offset, is_vertical=False):
        """Helper to draw dimension lines with arrows"""
        if is_vertical:
            x = p1[0] + offset
            y_mid = (p1[1] + p2[1]) / 2
            ax.annotate('', xy=(x, p1[1]), xytext=(x, p2[1]),
                        arrowprops=dict(arrowstyle='<->', color='black'))
            ax.text(x + 0.1, y_mid, text, rotation=90, va='center', ha='left', fontsize=10, fontweight='bold')
            # Witness lines
            ax.plot([p1[0], x], [p1[1], p1[1]], 'k-', linewidth=0.5)
            ax.plot([p2[0], x], [p2[1], p2[1]], 'k-', linewidth=0.5)
        else:
            y = p1[1] + offset
            x_mid = (p1[0] + p2[0]) / 2
            ax.annotate('', xy=(p1[0], y), xytext=(p2[0], y),
                        arrowprops=dict(arrowstyle='<->', color='black'))
            ax.text(x_mid, y + 0.1, text, va='bottom', ha='center', fontsize=10, fontweight='bold')
            # Witness lines
            ax.plot([p1[0], p1[0]], [p1[1], y], 'k-', linewidth=0.5)
            ax.plot([p2[0], p2[0]], [p2[1], y], 'k-', linewidth=0.5)

    # Dimension L1 (Span)
    draw_dim((0, -c2_m), (L1, -c2_m), f"L1 = {L1} m", offset=-0.5)
    
    # Dimension L2 (Span)
    draw_dim((-c1_m, 0), (-c1_m, L2), f"L2 = {L2} m", offset=-0.5, is_vertical=True)
    
    # Dimension c1, c2 (Detail on bottom-left column)
    # Zoomed text for column size
    ax.text(0, 0, f"Col\n{c1}x{c2}cm", ha='center', va='center', color='white', fontsize=8, fontweight='bold')
    
    # Label Strips
    ax.text(L1/2, 0, "Column Strip", ha='center', va='center', color='blue', fontsize=9, fontweight='bold', alpha=0.6)
    ax.text(L1/2, L2/2, "Middle Strip", ha='center', va='center', color='green', fontsize=9, fontweight='bold', alpha=0.6)
    ax.text(L1/2, L2, "Column Strip", ha='center', va='center', color='blue', fontsize=9, fontweight='bold', alpha=0.6)

    # Final Settings
    ax.set_aspect('equal')
    ax.set_title(f"Flat Slab Top View (L1={L1}m, L2={L2}m)", fontsize=14)
    ax.axis('off') # Hide axis ticks
    
    return fig
