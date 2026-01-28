import matplotlib.pyplot as plt
import matplotlib.patches as patches

def plot_slab_section(h_mm, cover_mm, c1_mm, ln_m, lx_m):
    """
    วาด Cross Section แบบ Construction Drawing
    """
    # Robust conversion
    h = float(h_mm) / 1000.0
    cover = float(cover_mm) / 1000.0
    c1 = float(c1_mm) / 1000.0
    ln_val = float(ln_m)
    
    fig, ax = plt.subplots(figsize=(10, 5)) # Wide format
    
    # 1. Concrete & Column
    view_limit = 2.5
    # Slab
    slab = patches.Rectangle((-view_limit, 0), 2*view_limit, h, 
                             facecolor='#f0f0f0', edgecolor='gray', linewidth=1, label='Concrete')
    ax.add_patch(slab)
    # Column
    col = patches.Rectangle((-c1/2, -0.6), c1, 0.6, 
                            facecolor='#d0d0d0', edgecolor='black', hatch='///')
    ax.add_patch(col)
    
    # 2. Rebar Detailing
    # 2.1 Top Bar (Negative Moment) - Red, Thick
    # Length = c1 + 2 * (0.33 Ln) approx for detailing (ACI min is 0.30Ln)
    ext_len = 0.33 * ln_val
    top_bar_half_len = (c1/2) + ext_len
    y_top = h - cover
    
    ax.plot([-top_bar_half_len, top_bar_half_len], [y_top, y_top], 
            color='#d62728', linewidth=3.5, label='Top Bar (Main)')
    
    # Hook/End markers
    ax.plot([-top_bar_half_len, -top_bar_half_len], [y_top-0.03, y_top], color='#d62728', linewidth=2)
    ax.plot([top_bar_half_len, top_bar_half_len], [y_top-0.03, y_top], color='#d62728', linewidth=2)
    
    # Label for Extension
    ax.text(top_bar_half_len, y_top + 0.03, f"Ext. {ext_len:.2f} m", 
            ha='center', va='bottom', color='#d62728', fontweight='bold', fontsize=10)

    # 2.2 Bottom Bar (Positive Moment) - Blue, Continuous
    y_bot = cover
    ax.plot([-view_limit+0.2, view_limit-0.2], [y_bot, y_bot], 
            color='#1f77b4', linewidth=3, linestyle='-', label='Bottom Bar')
    ax.text(view_limit-0.5, y_bot + 0.03, "Cont. Bottom Bar", 
            ha='right', color='#1f77b4', fontsize=9)

    # 3. Dimension Lines (Professional Style)
    # H Dimension
    dim_x = -1.2
    ax.annotate(text='', xy=(dim_x, 0), xytext=(dim_x, h), arrowprops=dict(arrowstyle='<|-|>', color='black'))
    ax.text(dim_x - 0.05, h/2, f"h = {h_mm:.0f} mm", rotation=90, va='center', ha='right')

    # Cover Dimension (Zoomed logic visually)
    ax.annotate(text='', xy=(0, h), xytext=(0, h-cover), arrowprops=dict(arrowstyle='<|-', color='purple'))
    ax.text(0.1, h - cover/2, f"Cov {cover_mm} mm", color='purple', fontsize=8, va='center')

    # Center Line
    ax.axvline(0, color='black', linestyle='-.', linewidth=0.5, alpha=0.5)

    # 4. Settings
    ax.set_xlim(-view_limit, view_limit)
    ax.set_ylim(-0.2, h + 0.4)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title(f"TYPICAL SECTION: COLUMN STRIP\n(Span Ln = {ln_val:.2f} m)", fontweight='bold')
    ax.legend(loc='lower right')
    
    return fig
