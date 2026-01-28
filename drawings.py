import matplotlib.pyplot as plt
import matplotlib.patches as patches

def draw_section(h_mm, cover_mm, c1_mm, ln_m):
    h = h_mm / 1000.0
    c1 = c1_mm / 1000.0
    cover = cover_mm / 1000.0
    
    fig, ax = plt.subplots(figsize=(10, 4))
    
    # Concrete
    ax.add_patch(patches.Rectangle((-2.0, 0), 4.0, h, facecolor='#f0f0f0', edgecolor='gray'))
    # Column
    ax.add_patch(patches.Rectangle((-c1/2, -0.5), c1, 0.5, hatch='///', facecolor='white', edgecolor='black'))
    
    # Rebar Top (Red)
    ext = 0.33 * ln_m
    top_len = (c1/2) + ext
    y_top = h - cover
    ax.plot([-top_len, top_len], [y_top, y_top], color='red', linewidth=3)
    ax.text(top_len, y_top+0.02, f"Ext. {ext:.2f} m", color='red', ha='center')
    
    # Rebar Bot (Blue)
    y_bot = cover
    ax.plot([-1.8, 1.8], [y_bot, y_bot], color='blue', linewidth=3)
    
    # Dimensions (Explicit Values)
    ax.annotate('', xy=(-1.5, 0), xytext=(-1.5, h), arrowprops=dict(arrowstyle='<->'))
    ax.text(-1.6, h/2, f"h={h_mm:.0f}mm", rotation=90, va='center')
    
    ax.set_ylim(-0.2, h+0.3)
    ax.set_xlim(-2.0, 2.0)
    ax.axis('off')
    ax.set_title("Cross Section A-A (Construction Detail)")
    
    return fig
