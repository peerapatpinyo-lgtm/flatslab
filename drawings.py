import matplotlib.pyplot as plt
import matplotlib.patches as patches

def draw_section(h_mm, cover_mm, c1_m, span_draw_m, d_mm, top_txt, bot_txt):
    """
    Draws a schematic section of the slab/column strip.
    """
    fig, ax = plt.subplots(figsize=(10, 4))
    
    # Dimensions for plotting
    col_w = c1_m * 1000  # mm
    slab_h = h_mm        # mm
    span = span_draw_m * 1000 # mm
    
    # 1. Concrete Section (Grey)
    # Slab
    rect_slab = patches.Rectangle((0, 0), span + col_w, slab_h, linewidth=1, edgecolor='none', facecolor='#E0E0E0')
    ax.add_patch(rect_slab)
    
    # Column
    rect_col = patches.Rectangle((0, -500), col_w, 500 + slab_h, linewidth=1, edgecolor='none', facecolor='#BDBDBD')
    ax.add_patch(rect_col)
    
    # 2. Rebar (Red Lines)
    eff_d_top = h_mm - cover_mm
    eff_d_bot = cover_mm
    
    # Top Bar (Main reinforcement at column)
    ax.plot([0, span/3], [eff_d_top, eff_d_top], color='red', linewidth=3, label='Top Rebar')
    ax.text(100, eff_d_top + 20, top_txt, color='red', fontsize=10, fontweight='bold')
    
    # Bot Bar (Span reinforcement)
    ax.plot([col_w, span + col_w], [eff_d_bot, eff_d_bot], color='blue', linewidth=3, label='Bot Rebar')
    ax.text(span/2, eff_d_bot + 20, bot_txt, color='blue', fontsize=10, fontweight='bold')
    
    # 3. Dimensions & Annotations
    ax.set_xlim(-200, span + col_w + 200)
    ax.set_ylim(-600, slab_h + 300)
    ax.set_aspect('equal')
    ax.axis('off')
    
    plt.title(f"Section Detail (h={h_mm}mm, d={d_mm:.0f}mm)", fontsize=12)
    plt.tight_layout()
    
    return fig
