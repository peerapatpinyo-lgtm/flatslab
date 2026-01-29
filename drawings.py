import matplotlib.pyplot as plt
import matplotlib.patches as patches

def draw_section(h_mm, cover_mm, c1_mm, ln_m):
    h = h_mm / 1000.0
    c1 = c1_mm / 1000.0
    cover = cover_mm / 1000.0
    
    fig, ax = plt.subplots(figsize=(10, 4))
    
    # Dynamic Width
    w = min(2.5, ln_m * 0.4)
    
    # 1. Slab & Column
    ax.add_patch(patches.Rectangle((-w, 0), 2*w, h, facecolor='#e6e6e6', edgecolor='black'))
    ax.add_patch(patches.Rectangle((-c1/2, -0.5), c1, 0.5, hatch='///', facecolor='white', edgecolor='black'))
    
    # 2. Rebar
    ext = 0.33 * ln_m
    top_x = (c1/2) + ext
    y_top = h - cover
    ax.plot([-top_x, top_x], [y_top, y_top], 'r-', lw=3, label='Top')
    ax.plot([-top_x, -top_x], [y_top, y_top-0.1], 'r-', lw=2)
    ax.plot([top_x, top_x], [y_top, y_top-0.1], 'r-', lw=2)
    ax.text(top_x, y_top+0.05, f"L={ext:.2f}m", color='red', ha='center')
    
    y_bot = cover
    ax.plot([-w+0.2, w-0.2], [y_bot, y_bot], 'b-', lw=3, label='Bot')
    
    # --- [NEW] Critical Section Lines (d/2 from face) ---
    d_m = (h_mm - cover_mm - 8) / 1000.0
    crit_x = (c1/2) + (d_m/2)
    
    # Draw dashed lines
    ax.vlines(x=[-crit_x, crit_x], ymin=0, ymax=h, colors='red', linestyles='--', alpha=0.6, linewidth=1)
    # Add text label
    ax.text(crit_x + 0.02, h/2, f"Crit. Sec.\n(d/2)", color='red', fontsize=8, va='center')
    # ----------------------------------------------------

    # 3. Dimensions
    ax.annotate("", xy=(-w+0.5, 0), xytext=(-w+0.5, h), arrowprops=dict(arrowstyle='<->'))
    ax.text(-w+0.4, h/2, f"h={h_mm:.0f}", rotation=90, va='center', fontweight='bold')
    
    ax.annotate("", xy=(0, h), xytext=(0, h-cover), arrowprops=dict(arrowstyle='|-|', color='purple'))
    ax.text(0.1, h-cover/2, f"cov {cover_mm}", color='purple', fontsize=8, va='center')

    ax.set_xlim(-w, w)
    ax.set_ylim(-0.6, h+0.4)
    ax.axis('off')
    ax.set_title(f"SECTION A-A (Ln = {ln_m:.2f} m)", loc='left')
    
    return fig
