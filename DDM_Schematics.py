import matplotlib.pyplot as plt
import matplotlib.patches as patches

# ========================================================
# SCHEMATIC DRAWING TOOLS
# ========================================================

def draw_span_schematic(span_type):
    """
    Draws the span schematic with moment distribution visualization.
    """
    fig, ax = plt.subplots(figsize=(10, 6)) 
    ax.set_xlim(-4.0, 12.5)
    ax.set_ylim(-1.5, 8.0) 
    ax.axis('off')

    # Colors
    concrete_color = '#f5f5f5'
    cs_band_color = '#e1f5fe'
    cs_text_color = '#0277bd'
    ms_band_color = '#fff3e0'
    ms_text_color = '#ef6c00'

    def draw_data_column(x, m_total, is_flat_plate, section_type):
        if section_type == 'neg':
            cs_ratio = 0.75 if is_flat_plate else 0.85 
        else:
            cs_ratio = 0.60 if is_flat_plate else 0.75
        
        ms_ratio = 1.0 - cs_ratio
        val_cs = m_total * cs_ratio
        val_ms = m_total * ms_ratio

        # Total Moment Box
        ax.text(x, 7.0, f"Total $M_o$\n{m_total:.2f}", 
                ha='center', va='center', weight='bold', fontsize=9, 
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="black", lw=1.2))
        ax.plot([x, x], [6.5, 6.0], color='#b0bec5', linestyle='-', linewidth=1.2)

        # Values
        ax.text(x, 5.6, f"CS: {val_cs:.3f}", ha='center', va='center', weight='bold', fontsize=9, color=cs_text_color)
        ax.text(x, 4.8, f"MS: {val_ms:.3f}", ha='center', va='center', weight='bold', fontsize=9, color=ms_text_color)
        ax.plot([x, x], [4.5, 2.8], color='#cfd8dc', linestyle=':', linewidth=1.2)

    # Background Strips
    ax.add_patch(patches.Rectangle((-4.0, 5.2), 16.5, 0.8, facecolor=cs_band_color, edgecolor='none'))
    ax.text(-3.8, 5.6, "Column Strip\n(CS)", color=cs_text_color, fontsize=9, weight='bold', ha='left', va='center')

    ax.add_patch(patches.Rectangle((-4.0, 4.4), 16.5, 0.8, facecolor=ms_band_color, edgecolor='none'))
    ax.text(-3.8, 4.8, "Middle Strip\n(MS)", color=ms_text_color, fontsize=9, weight='bold', ha='left', va='center')

    # Structural Geometry
    slab_y, slab_h = 2.0, 0.6
    col_w, col_h = 1.0, 2.2
    beam_d = 1.3
    col_style = {'facecolor': '#546e7a', 'edgecolor': 'black', 'zorder': 5}
    slab_style = {'facecolor': concrete_color, 'edgecolor': '#333', 'linewidth': 1.5}

    ax.add_patch(patches.Rectangle((-col_w/2, slab_y-col_h), col_w, col_h, **col_style))
    ax.add_patch(patches.Rectangle((10-col_w/2, slab_y-col_h), col_w, col_h, **col_style))

    if "Interior" in span_type:
        ax.add_patch(patches.Rectangle((-2.5, slab_y), 15, slab_h, **slab_style))
        ax.text(-2.0, slab_y+slab_h/2, "≈", fontsize=24, rotation=90, va='center')
        ax.text(12.0, slab_y+slab_h/2, "≈", fontsize=24, rotation=90, va='center')
        draw_data_column(0, 0.65, True, 'neg')
        draw_data_column(5, 0.35, True, 'pos')
        draw_data_column(10, 0.65, True, 'neg')
        ax.text(5, 7.8, "INTERIOR SPAN DISTRIBUTION", ha='center', fontsize=12, weight='bold')

    elif "Edge Beam" in span_type:
        ax.add_patch(patches.Rectangle((-col_w/2, slab_y), 13, slab_h, **slab_style))
        ax.add_patch(patches.Rectangle((-col_w/2, slab_y-beam_d), col_w*1.5, beam_d, **slab_style))
        ax.text(12.0, slab_y+slab_h/2, "≈", fontsize=24, rotation=90, va='center')
        draw_data_column(0, 0.30, False, 'neg')
        draw_data_column(5, 0.50, False, 'pos')
        draw_data_column(10, 0.70, False, 'neg')
        ax.text(5, 7.8, "END SPAN - EDGE BEAM DISTRIBUTION", ha='center', fontsize=12, weight='bold')
        ax.annotate('Stiff Edge Beam', xy=(0.8, slab_y-beam_d/2), xytext=(3, 0),
                    arrowprops=dict(arrowstyle="->", color='#d32f2f'), color='#d32f2f', weight='bold')

    elif "No Beam" in span_type:
        ax.add_patch(patches.Rectangle((-col_w/2, slab_y), 13, slab_h, **slab_style))
        ax.add_patch(patches.Rectangle((-col_w/2, slab_y-beam_d), col_w, beam_d, fc='none', ec='#d32f2f', ls='--'))
        ax.text(12.0, slab_y+slab_h/2, "≈", fontsize=24, rotation=90, va='center')
        draw_data_column(0, 0.26, True, 'neg')
        draw_data_column(5, 0.52, True, 'pos')
        draw_data_column(10, 0.70, True, 'neg')
        ax.text(5, 7.8, "END SPAN - FLAT PLATE DISTRIBUTION", ha='center', fontsize=12, weight='bold')
        ax.annotate('No Beam (Flexible)', xy=(0.5, slab_y), xytext=(3, 0.5),
                    arrowprops=dict(arrowstyle="->", color='#d32f2f'), color='#d32f2f', weight='bold')

    ax.annotate('', xy=(0, -0.5), xytext=(10, -0.5), arrowprops=dict(arrowstyle='<->', linewidth=1.2))
    ax.text(5, -0.8, "Clear Span ($L_n$)", ha='center', fontsize=10, fontstyle='italic')
    ax.text(0, -1.2, "Ext. Support", ha='center', fontsize=9)
    ax.text(10, -1.2, "Int. Support", ha='center', fontsize=9)

    return fig
