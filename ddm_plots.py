import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# ==========================================
# 🎨 HELPER: CAD STYLING
# ==========================================
def add_dimension(ax, x1, y1, x2, y2, text, offset=0.5, color='black', arrow_color='black'):
    """ วาดเส้นบอกระยะ (Dimension Line) """
    ax.annotate('', xy=(x1, y1), xytext=(x2, y2),
                arrowprops=dict(arrowstyle='<|-|>', color=arrow_color, lw=0.6))
    
    mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
    bbox = dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.8)
    ax.text(mid_x, mid_y + offset, text, ha='center', va='center', 
            fontsize=7, color=color, bbox=bbox, fontweight='bold')

def setup_cad_style(ax, title):
    """ จัดธีมให้เหมือนกระดาษเขียนแบบ """
    ax.set_title(title, loc='left', fontsize=10, fontweight='bold', pad=10, color='#333333')
    ax.axis('off')

# ==========================================
# 1. MOMENT DIAGRAM
# ==========================================
def plot_ddm_moment(L_span, c1, m_vals):
    fig, ax = plt.subplots(figsize=(10, 3.5))
    x = np.linspace(0, L_span, 200)
    
    M_neg_cs, M_pos_cs = m_vals['M_cs_neg'], m_vals['M_cs_pos']
    M_neg_ms, M_pos_ms = m_vals['M_ms_neg'], m_vals['M_ms_pos']

    # สร้าง Curve สวยๆ
    pts = [0, L_span*0.2, L_span*0.5, L_span*0.8, L_span]
    y_cs = np.interp(x, pts, [-M_neg_cs, 0, M_pos_cs, 0, -M_neg_cs])
    y_ms = np.interp(x, pts, [-M_neg_ms, 0, M_pos_ms, 0, -M_neg_ms])

    # Plot Lines
    ax.plot(x, y_cs, label='Column Strip', color='#D32F2F', linewidth=1.5)
    ax.plot(x, y_ms, label='Middle Strip', color='#1976D2', linewidth=1.5, linestyle='--')
    
    # Fill & Grid
    ax.fill_between(x, y_cs, 0, alpha=0.05, color='#D32F2F')
    ax.axhline(0, color='black', linewidth=0.8)
    ax.grid(True, linestyle=':', alpha=0.5)
    
    # Invert Y (Engineering Standard: Negative Moment Top)
    limit = max(M_pos_cs, M_neg_cs, M_pos_ms, M_neg_ms) * 1.3
    ax.set_ylim(limit, -limit) 
    
    # Labels
    bbox = dict(boxstyle="round,pad=0.2", fc="white", ec="#D32F2F", alpha=0.9, lw=0.5)
    ax.text(0, -M_neg_cs, f"M-: {M_neg_cs:,.0f}", color='#D32F2F', ha='left', va='top', fontsize=8, bbox=bbox)
    ax.text(L_span/2, M_pos_cs, f"M+: {M_pos_cs:,.0f}", color='#D32F2F', ha='center', va='bottom', fontsize=8, bbox=bbox)
    
    ax.set_title(f"MOMENT DISTRIBUTION DIAGRAM (Span {L_span} m)", loc='left', fontweight='bold', fontsize=10)
    ax.legend(fontsize=8, loc='upper right')
    
    return fig

# ==========================================
# 2. SECTION PROFILE (SIDE VIEW)
# ==========================================
def plot_rebar_detailing(L_span, h_slab, c_para, rebar_results):
    fig, ax = plt.subplots(figsize=(10, 4))
    h_m = h_slab / 100
    c_m = c_para / 100
    
    # Concrete Structure
    slab = patches.Rectangle((0, 0), L_span, h_m, fc='#E0E0E0', ec='black', lw=0.5)
    ax.add_patch(slab)
    
    # Columns (Hatched)
    col_h = 0.6
    for x_pos in [-c_m/2, L_span-c_m/2]:
        ax.add_patch(patches.Rectangle((x_pos, -col_h), c_m, col_h, fc='white', ec='black', hatch='//', lw=0.5))
        ax.add_patch(patches.Rectangle((x_pos, h_m), c_m, col_h, fc='white', ec='black', hatch='//', lw=0.5))
    
    # Rebar
    cover = 0.03
    bar_len = L_span * 0.30
    top_y = h_m - cover
    bot_y = cover
    
    # Top Bars (Red)
    ax.plot([-c_m/2, bar_len], [top_y, top_y], color='#D32F2F', lw=2.5) # Left
    ax.plot([bar_len, bar_len], [top_y, top_y-0.08], color='#D32F2F', lw=1.5) # Hook
    ax.plot([L_span-bar_len, L_span+c_m/2], [top_y, top_y], color='#D32F2F', lw=2.5) # Right
    ax.plot([L_span-bar_len, L_span-bar_len], [top_y, top_y-0.08], color='#D32F2F', lw=1.5) # Hook
    
    # Bottom Bars (Blue)
    ax.plot([0, L_span], [bot_y, bot_y], color='#1976D2', lw=2.5)
    
    # Dimensions
    add_dimension(ax, 0, -0.3, L_span, -0.3, f"Span = {L_span} m", offset=0.1)
    add_dimension(ax, 0, h_m+0.2, bar_len, h_m+0.2, f"0.3L = {bar_len:.2f}m", offset=0.05, color='#D32F2F', arrow_color='#D32F2F')
    
    # Annotations
    ax.annotate(rebar_results.get('CS_Top','?'), xy=(bar_len/2, top_y), xytext=(bar_len/2, top_y+0.5),
                arrowprops=dict(arrowstyle='->', color='#D32F2F'), color='#D32F2F', fontweight='bold', ha='center')
    
    ax.annotate(rebar_results.get('CS_Bot','?'), xy=(L_span/2, bot_y), xytext=(L_span/2, -0.6),
                arrowprops=dict(arrowstyle='->', color='#1976D2'), color='#1976D2', fontweight='bold', ha='center')

    setup_cad_style(ax, "SECTION A-A: REINFORCEMENT PROFILE")
    ax.set_xlim(-0.8, L_span + 1.2)
    ax.set_ylim(-0.8, h_m + 0.8)
    plt.tight_layout()
    return fig

# ==========================================
# 3. PLAN VIEW (TOP VIEW)
# ==========================================
def plot_rebar_plan_view(L_span, L_width, c_para, rebar_results):
    fig, ax = plt.subplots(figsize=(10, 5))
    w_cs = min(L_span, L_width) / 2.0
    w_cs_half = w_cs / 2.0
    
    # Background Strips
    rect_ms = patches.Rectangle((0, w_cs_half), L_span, L_width - w_cs, fc='#E3F2FD', alpha=0.5, label='Middle Strip')
    ax.add_patch(rect_ms)
    rect_cs_bot = patches.Rectangle((0, 0), L_span, w_cs_half, fc='#FFEBEE', alpha=0.5, label='Col Strip')
    rect_cs_top = patches.Rectangle((0, L_width - w_cs_half), L_span, w_cs_half, fc='#FFEBEE', alpha=0.5)
    ax.add_patch(rect_cs_bot)
    ax.add_patch(rect_cs_top)
    
    # Columns
    c_m = c_para / 100
    for cx in [0, L_span]:
        for cy in [0, L_width]:
            ax.add_patch(patches.Rectangle((cx-c_m/2, cy-c_m/2), c_m, c_m, fc='#333', zorder=10))

    # Rebar Drawing Helper
    bar_len = L_span * 0.3
    def draw_bars(y, txt, color, is_top=True):
        if is_top:
            ax.plot([-0.2, bar_len], [y, y], color=color, lw=2) # Left
            ax.plot([L_span-bar_len, L_span+0.2], [y, y], color=color, lw=2) # Right
            ax.text(bar_len/2, y+0.1, txt, color=color, fontsize=8, ha='center', fontweight='bold')
        else:
            ax.plot([0, L_span], [y, y], color=color, lw=2)
            ax.text(L_span/2, y+0.1, txt, color=color, fontsize=8, ha='center', fontweight='bold')

    # Draw Rebars
    draw_bars(w_cs_half/2, rebar_results.get('CS_Top',''), '#D32F2F', True)
    draw_bars(w_cs_half/2 - 0.25, rebar_results.get('CS_Bot',''), '#1976D2', False)
    
    draw_bars(L_width/2 + 0.25, rebar_results.get('MS_Top',''), '#D32F2F', True)
    draw_bars(L_width/2, rebar_results.get('MS_Bot',''), '#1976D2', False)

    # Dimensions (Widths)
    x_dim = L_span + 0.6
    add_dimension(ax, x_dim, 0, x_dim, w_cs_half, f"CS/2\n{w_cs_half:.2f}", offset=0, color='gray', arrow_color='gray')
    add_dimension(ax, x_dim, w_cs_half, x_dim, L_width-w_cs_half, f"Middle\n{L_width-w_cs:.2f}", offset=0, color='gray', arrow_color='gray')

    setup_cad_style(ax, f"PLAN VIEW: REBAR LAYOUT (Span {L_span}x{L_width}m)")
    ax.set_xlim(-0.5, L_span + 1.2)
    ax.set_ylim(-0.5, L_width + 0.5)
    plt.tight_layout()
    return fig
