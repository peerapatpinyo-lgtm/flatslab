import matplotlib.pyplot as plt
import matplotlib.patches as patches

def draw_section(h_mm, cover_mm, c1_mm, ln_m):
    h = h_mm / 1000.0
    c1 = c1_mm / 1000.0
    cover = cover_mm / 1000.0
    
    fig, ax = plt.subplots(figsize=(10, 3.5))
    w = 2.0  # View width
    
    # Slab
    ax.add_patch(patches.Rectangle((-w, 0), 2*w, h, facecolor='#e0e0e0', edgecolor='black'))
    # Column
    ax.add_patch(patches.Rectangle((-c1/2, -0.5), c1, 0.5, hatch='///', facecolor='white', edgecolor='black'))
    
    # Critical Section Lines (d/2)
    d_m = (h_mm - cover_mm - 10)/1000.0
    crit_x = (c1/2) + (d_m/2)
    ax.vlines([-crit_x, crit_x], 0, h, colors='red', linestyles='--')
    ax.text(crit_x, h/2, f" d/2\n(Crit)", color='red', fontsize=8, va='center')
    
    # Rebar
    y_rebar = h - cover
    ax.plot([-w+0.1, w-0.1], [y_rebar, y_rebar], color='blue', linewidth=2)
    ax.text(0, y_rebar+0.02, f"d = {d_m*1000:.0f} mm", color='blue', ha='center')
    
    # Labels
    ax.text(-w+0.1, h/2, f"h = {h_mm} mm", rotation=90, va='center', fontweight='bold')
    
    ax.set_xlim(-w, w)
    ax.set_ylim(-0.6, h+0.2)
    ax.axis('off')
    ax.set_title(f"Section View (Ln = {ln_m:.2f} m)", loc='left')
    
    return fig
