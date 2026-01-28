import matplotlib.pyplot as plt
import matplotlib.patches as patches

def draw_section(h_mm, cover_mm, c1_mm, ln_m, d_mm):
    h = h_mm / 1000.0
    c1 = c1_mm / 1000.0
    cover = cover_mm / 1000.0
    
    fig, ax = plt.subplots(figsize=(10, 4))
    w = 2.0  # View width
    
    # 1. Concrete Slab
    ax.add_patch(patches.Rectangle((-w, 0), 2*w, h, facecolor='#f0f0f0', edgecolor='black'))
    # 2. Column
    ax.add_patch(patches.Rectangle((-c1/2, -0.5), c1, 0.5, hatch='///', facecolor='white', edgecolor='black'))
    
    # 3. Critical Section (d/2 from face)
    d_m = d_mm / 1000.0
    crit_dist = (c1/2) + (d_m/2)
    ax.vlines([-crit_dist, crit_dist], 0, h, colors='red', linestyles='--')
    ax.text(crit_dist, h/2, f" Crit. Sec\n d/2", color='red', fontsize=9, va='center')
    
    # 4. Top Rebar Zone (0.33 Ln)
    top_bar_len = 0.33 * ln_m
    y_rebar = h - cover
    ax.plot([-top_bar_len, top_bar_len], [y_rebar, y_rebar], color='blue', linewidth=3, label='Top Rebar')
    
    # Dimension Line for 0.33Ln
    ax.annotate(f"{top_bar_len:.2f} m", xy=(0, y_rebar + 0.05), xytext=(top_bar_len/2, y_rebar + 0.15),
                arrowprops=dict(arrowstyle='<->', color='blue'), color='blue', ha='center')
    ax.text(0, y_rebar + 0.20, r"$0.33 \ell_n$", color='blue', ha='center', fontsize=9)
    
    # 5. Height Dimension
    ax.annotate(f"h = {h_mm} mm", xy=(-w+0.2, 0), xytext=(-w+0.2, h),
                arrowprops=dict(arrowstyle='<->'), rotation=90, va='center')

    ax.set_xlim(-w, w)
    ax.set_ylim(-0.6, h+0.4)
    ax.axis('off')
    ax.set_title(f"SECTION DETAILS (Ln = {ln_m:.2f} m)", loc='left', fontweight='bold')
    
    return fig
