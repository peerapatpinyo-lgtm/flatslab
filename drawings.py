import matplotlib.pyplot as plt
import matplotlib.patches as patches

def draw_section(h_mm, cover_mm, c1_mm, ln_m):
    # Setup
    h = h_mm / 1000.0
    c1 = c1_mm / 1000.0
    cover = cover_mm / 1000.0
    d_m = (h_mm - cover_mm - 8) / 1000.0 # Calculate d for Critical Section
    
    fig, ax = plt.subplots(figsize=(10, 4))
    w = min(2.5, ln_m * 0.4) # View Width
    
    # 1. Concrete Body
    ax.add_patch(patches.Rectangle((-w, 0), 2*w, h, facecolor='#f0f0f0', edgecolor='black'))
    # Column
    ax.add_patch(patches.Rectangle((-c1/2, -0.6), c1, 0.6, hatch='///', facecolor='white', edgecolor='black'))
    
    # 2. Critical Section (Dashed Line at d/2)
    crit_dist = (c1/2) + (d_m/2)
    ax.vlines([-crit_dist, crit_dist], 0, h, colors='red', linestyles='--', alpha=0.7)
    ax.text(crit_dist, h/2, f"  Crit. Sec\n  d/2", color='red', fontsize=9, va='center')

    # 3. Rebar (Symbolic)
    y_top = h - cover
    ax.plot([-w+0.2, w-0.2], [y_top, y_top], 'r-', lw=2, label='Top Rebar')
    
    # 4. Dimensions
    ax.text(-w+0.2, h/2, f"h={h_mm}mm", rotation=90, va='center', fontweight='bold')
    
    ax.set_xlim(-w, w)
    ax.set_ylim(-0.7, h+0.3)
    ax.axis('off')
    ax.set_title(f"SECTION DETAILS (Ln = {ln_m:.2f} m)", loc='left')
    
    return fig
