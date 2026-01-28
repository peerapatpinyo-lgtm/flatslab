import matplotlib.pyplot as plt
import matplotlib.patches as patches

def draw_section(h_mm, cover_mm, c1_mm, ln_m, lx_m):
    """
    วาดหน้าตัดโดยปรับสเกลตามความยาวช่วง (ln) และความหนา (h)
    """
    h = h_mm / 1000.0
    c1 = c1_mm / 1000.0
    cover = cover_mm / 1000.0
    
    # Dynamic View Limit based on Ln (Show about 1/3 of span from support)
    view_w = min(2.0, ln_m * 0.4) 
    
    fig, ax = plt.subplots(figsize=(10, 5))
    
    # 1. Concrete Slab
    # วาดพื้นสีเทาอ่อน
    ax.add_patch(patches.Rectangle((-view_w, 0), 2*view_w, h, facecolor='#f2f2f2', edgecolor='gray'))
    
    # 2. Column
    # วาดเสาลาย Hatch
    ax.add_patch(patches.Rectangle((-c1/2, -0.6), c1, 0.6, hatch='///', facecolor='white', edgecolor='black'))
    
    # 3. Rebar Detailing
    # Top Bar (Red)
    ext = 0.33 * ln_m
    top_len = (c1/2) + ext
    y_top = h - cover
    # Draw line
    ax.plot([-top_len, top_len], [y_top, y_top], color='#d62728', linewidth=3, label='Top Bar')
    # Draw Hooks
    hook_len = 0.15 # 15cm hook
    ax.plot([-top_len, -top_len], [y_top, y_top-hook_len], color='#d62728', linewidth=2)
    ax.plot([top_len, top_len], [y_top, y_top-hook_len], color='#d62728', linewidth=2)
    # Label Ext
    ax.text(top_len, y_top + 0.02, f"Ext. {ext:.2f} m", color='#d62728', ha='center', va='bottom', fontweight='bold')

    # Bottom Bar (Blue)
    y_bot = cover
    ax.plot([-view_w+0.1, view_w-0.1], [y_bot, y_bot], color='#1f77b4', linewidth=3, label='Bottom Bar')
    ax.text(view_w-0.2, y_bot + 0.02, "Cont.", color='#1f77b4', ha='right', va='bottom', fontsize=9)
    
    # 4. Dimensions & Annotations
    # H Dimension
    dim_x = -view_w + 0.3
    ax.annotate('', xy=(dim_x, 0), xytext=(dim_x, h), arrowprops=dict(arrowstyle='<->'))
    ax.text(dim_x - 0.05, h/2, f"h={h_mm:.0f} mm", rotation=90, va='center')
    
    # Clear Cover Annotation
    # Zoom in visual for cover
    ax.annotate('', xy=(0, h), xytext=(0, h-cover), arrowprops=dict(arrowstyle='|-|', color='purple', linewidth=1.5))
    ax.text(0.05, h - cover/2, f"Clear Cover {cover_mm} mm", color='purple', fontsize=9, va='center')
    
    # Center Line
    ax.axvline(0, color='black', linestyle='-.', linewidth=0.5, alpha=0.5)

    # Plot Settings
    ax.set_ylim(-0.2, h + 0.4)
    ax.set_xlim(-view_w, view_w)
    ax.axis('off')
    ax.set_title(f"SHOP DRAWING: SECTION A-A\n(Span Ln = {ln_m:.2f} m)", loc='left', fontsize=10, fontweight='bold')
    ax.legend(loc='lower right', fontsize='small')
    
    return fig
