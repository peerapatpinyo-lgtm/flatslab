import matplotlib.pyplot as plt
import matplotlib.patches as patches

def plot_slab_section(h_mm, cover_mm, c1_mm, ln_m, lx_m):
    # Robust Conversion
    h = float(h_mm) / 1000.0
    cover = float(cover_mm) / 1000.0
    c1 = float(c1_mm) / 1000.0
    ln_val = float(ln_m)

    fig, ax = plt.subplots(figsize=(10, 5))
    
    # 1. Concrete & Column
    view_limit = 2.2
    slab = patches.Rectangle((-view_limit, 0), 2*view_limit, h, facecolor='#f5f5f5', edgecolor='gray')
    col = patches.Rectangle((-c1/2, -0.6), c1, 0.6, facecolor='#e0e0e0', edgecolor='black', hatch='///')
    ax.add_patch(slab)
    ax.add_patch(col)

    # 2. Rebar
    # Top Bar (Red)
    ext_len = 0.33 * ln_val
    top_half = (c1/2) + ext_len
    y_top = h - cover
    ax.plot([-top_half, top_half], [y_top, y_top], color='#d62728', linewidth=3, label='Top Bar')
    # Hook
    ax.plot([-top_half, -top_half], [y_top, y_top-0.03], color='#d62728', linewidth=2)
    ax.plot([top_half, top_half], [y_top, y_top-0.03], color='#d62728', linewidth=2)
    ax.text(top_half, y_top+0.02, f"Ext. {ext_len:.2f}m", ha='center', color='#d62728', fontweight='bold')

    # Bottom Bar (Blue)
    y_bot = cover
    ax.plot([-view_limit+0.2, view_limit-0.2], [y_bot, y_bot], color='#1f77b4', linewidth=3, label='Bottom Bar')

    # 3. Dimensions
    # Height
    ax.annotate('', xy=(-1.5, 0), xytext=(-1.5, h), arrowprops=dict(arrowstyle='<->'))
    ax.text(-1.6, h/2, f"h={h_mm:.0f}", rotation=90, va='center')
    # Cover
    ax.annotate('', xy=(0, h), xytext=(0, h-cover), arrowprops=dict(arrowstyle='<->', color='purple'))
    ax.text(0.1, h-cover/2, f"Cov {cover_mm}", color='purple', fontsize=8, va='center')

    ax.set_xlim(-view_limit, view_limit)
    ax.set_ylim(-0.2, h+0.3)
    ax.axis('off')
    ax.set_title(f"SECTION A-A (Ln = {ln_val:.2f} m)", loc='left', fontsize=10)
    
    return fig
