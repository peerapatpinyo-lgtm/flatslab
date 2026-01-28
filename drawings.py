import matplotlib.pyplot as plt
import matplotlib.patches as patches

def draw_section(h_mm, cover_mm, c1_mm, ln_m, d_mm, top_rebar_str, bot_rebar_str):
    h = h_mm / 1000.0
    c1 = c1_mm / 1000.0
    cover = cover_mm / 1000.0
    
    fig, ax = plt.subplots(figsize=(10, 4.5))
    w = 2.2  # View width from center
    
    # 1. Concrete & Column
    ax.add_patch(patches.Rectangle((-w, 0), 2*w, h, facecolor='#f4f4f4', edgecolor='black'))
    ax.add_patch(patches.Rectangle((-c1/2, -0.6), c1, 0.6, hatch='///', facecolor='white', edgecolor='black'))
    
    # 2. Critical Section
    d_m = d_mm / 1000.0
    crit_dist = (c1/2) + (d_m/2)
    ax.vlines([-crit_dist, crit_dist], 0, h, colors='red', linestyles=':', alpha=0.5)
    
    # 3. Rebar Drawing
    y_top = h - cover
    y_bot = cover
    
    # 3.1 Top Bar (CS Top) - Length 0.33 Ln
    top_len = 0.33 * ln_m
    ax.plot([-top_len, top_len], [y_top, y_top], color='blue', linewidth=3, label='Top Bar')
    # Label Top Bar
    ax.text(0, y_top + 0.05, f"Top: {top_rebar_str}", color='blue', ha='center', fontweight='bold')
    
    # 3.2 Bottom Bar (CS Bot) - Continuous
    ax.plot([-w+0.1, w-0.1], [y_bot, y_bot], color='green', linewidth=3, label='Bot Bar')
    # Label Bot Bar
    ax.text(1.0, y_bot - 0.08, f"Bot: {bot_rebar_str}", color='green', ha='center', fontweight='bold')

    # 4. Dimensions & Cut-offs
    # 0.33 Ln Dimension
    ax.annotate(f"0.33 Ln = {top_len:.2f} m", xy=(-top_len, y_top), xytext=(-top_len, h+0.2),
                arrowprops=dict(arrowstyle='->', color='blue'), color='blue', ha='center')
    ax.vlines([-top_len, top_len], y_top, h+0.2, colors='blue', linestyles='--')
    
    # 0.20 Ln Marker (Required by prompt)
    len_20 = 0.20 * ln_m
    ax.plot([-len_20, len_20], [y_top-0.03, y_top-0.03], color='orange', linewidth=2, linestyle='--')
    ax.text(0, y_top - 0.08, f"Min Ext. 0.20 Ln ({len_20:.2f}m)", color='orange', ha='center', fontsize=8)

    # Height
    ax.annotate(f"h={h_mm}mm", xy=(-w+0.2, 0), xytext=(-w+0.2, h),
                arrowprops=dict(arrowstyle='<->'), rotation=90, va='center')

    ax.set_xlim(-w, w)
    ax.set_ylim(-0.7, h+0.5)
    ax.axis('off')
    ax.set_title(f"CONSTRUCTION SECTION (Ln = {ln_m:.2f} m)", loc='left', fontweight='bold')
    
    return fig
