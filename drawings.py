import matplotlib.pyplot as plt
import matplotlib.patches as patches

def draw_section(h_mm, cover_mm, c1_m, ln_m, d_mm, top_txt, bot_txt):
    """
    Draws a proportional section of the slab with reinforcement cut-off points.
    """
    fig, ax = plt.subplots(figsize=(10, 4))
    
    # Dimensions (scaled for visualization)
    col_w = c1_m * 1000
    span = ln_m * 1000
    total_w = col_w + span + col_w
    slab_h = h_mm
    
    # 1. Concrete Geometry
    # Left Column
    ax.add_patch(patches.Rectangle((-col_w, -1000), col_w, 1000+slab_h, facecolor='#D3D3D3', edgecolor='black'))
    # Right Column
    ax.add_patch(patches.Rectangle((span, -1000), col_w, 1000+slab_h, facecolor='#D3D3D3', edgecolor='black'))
    # Slab
    ax.add_patch(patches.Rectangle((0, 0), span, slab_h, facecolor='#F0F0F0', edgecolor='black'))
    
    # 2. Rebar Drawing
    # Top Bar (Negative Moment) - Extends 0.30 Ln
    cutoff_len = 0.30 * span
    top_y = slab_h - cover_mm
    ax.plot([-col_w/2, cutoff_len], [top_y, top_y], 'r-', linewidth=3, label='Top Bar')
    ax.plot([span - cutoff_len, span + col_w/2], [top_y, top_y], 'r-', linewidth=3)
    
    # Bottom Bar (Positive Moment) - Continuous
    bot_y = cover_mm
    ax.plot([0 + 50, span - 50], [bot_y, bot_y], 'b-', linewidth=3, label='Bot Bar')
    
    # 3. Annotations
    ax.text(cutoff_len, top_y + 20, f"Cut-off: 0.30Ln ({cutoff_len/1000:.2f}m)", ha='center', fontsize=9, color='red')
    ax.text(span/2, top_y + 60, top_txt, ha='center', fontsize=10, weight='bold', color='darkred')
    ax.text(span/2, bot_y - 40, bot_txt, ha='center', fontsize=10, weight='bold', color='blue')
    
    # Dimensions
    ax.annotate(f"Ln = {ln_m:.2f} m", xy=(span/2, slab_h/2), ha='center', va='center')
    ax.annotate(f"h = {h_mm} mm", xy=(-20, slab_h/2), ha='right', va='center', rotation=90)
    
    # Settings
    ax.set_xlim(-col_w - 200, span + col_w + 200)
    ax.set_ylim(-500, slab_h + 300)
    ax.set_aspect('auto') # Auto aspect to fit slab and span
    ax.axis('off')
    ax.set_title("Reinforcement Detail (Schematic)", fontsize=12)
    
    return fig
