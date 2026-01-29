import matplotlib.pyplot as plt
import matplotlib.patches as patches

def draw_section(h_mm, cover_mm, c1_mm, ln_m, d_mm, top_label, bot_label):
    h = h_mm / 1000.0
    c1 = c1_mm / 1000.0
    cover = cover_mm / 1000.0
    
    fig, ax = plt.subplots(figsize=(10, 5))
    w = 2.5  # View width
    
    # 1. Concrete Structure
    # Column
    ax.add_patch(patches.Rectangle((-c1/2, -0.6), c1, 0.6, hatch='///', facecolor='white', edgecolor='black'))
    # Slab
    ax.add_patch(patches.Rectangle((-w, 0), 2*w, h, facecolor='#f4f4f4', edgecolor='black'))
    
    # 2. Rebar Drawing
    y_top = h - cover
    y_bot = cover
    
    # 2.1 Top Bar (Cut-off at 0.30 Ln per ACI/Standard practice)
    cutoff_ratio = 0.30
    top_len = cutoff_ratio * ln_m
    ax.plot([-top_len, top_len], [y_top, y_top], color='blue', linewidth=3, label='Top Bar')
    ax.text(0, y_top + 0.05, f"Top: {top_label}", color='blue', ha='center', fontweight='bold', fontsize=9)
    
    # 2.2 Bottom Bar (Must extend into support >= 150mm)
    embedment = 0.15 # 150mm
    # Draw from left edge of view to right edge of view, but technically anchored at supports
    ax.plot([-w+0.1, w-0.1], [y_bot, y_bot], color='green', linewidth=3, label='Bot Bar')
    ax.text(1.0, y_bot - 0.08, f"Bot: {bot_label}", color='green', ha='center', fontweight='bold', fontsize=9)
    
    # Show Embedment
    ax.plot([c1/2 - 0.05, c1/2 + embedment], [y_bot, y_bot], color='red', linewidth=4, alpha=0.6)
    ax.text(c1/2 + 0.1, y_bot + 0.02, "Min Embed 150mm", color='red', fontsize=8)

    # 3. Dimensions
    # Cutoff Dimension
    ax.annotate(f"{cutoff_ratio} Ln = {top_len:.2f} m", xy=(-top_len, y_top), xytext=(-top_len, h+0.25),
                arrowprops=dict(arrowstyle='->', color='blue'), color='blue', ha='center', fontsize=9)
    ax.vlines([-top_len, top_len], y_top, h+0.25, colors='blue', linestyles=':', alpha=0.5)

    # Clear Span Indication
    ax.annotate(f"Face of Support", xy=(c1/2, 0), xytext=(c1/2, -0.2),
                arrowprops=dict(arrowstyle='->'), ha='left', fontsize=8)
    
    # Depth
    ax.annotate(f"h={h_mm}mm", xy=(-w+0.2, 0), xytext=(-w+0.2, h),
                arrowprops=dict(arrowstyle='<->'), rotation=90, va='center')
    
    # Effective Depth
    ax.annotate(f"d={d_mm:.0f}", xy=(-w+0.4, y_top), xytext=(-w+0.4, 0),
                arrowprops=dict(arrowstyle='<->', color='red'), color='red', va='center')

    ax.set_xlim(-w, w)
    ax.set_ylim(-0.7, h+0.6)
    ax.axis('off')
    ax.set_title(f"CONSTRUCTION DETAIL (Ln = {ln_m:.2f} m)", loc='left', fontweight='bold')
    
    return fig
