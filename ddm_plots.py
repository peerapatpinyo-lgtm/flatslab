import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.ticker as ticker
import numpy as np

# ==========================================
# 🎨 ENGINEERING STYLE CONSTANTS
# ==========================================
CLR_BG = 'white'
CLR_CONCRETE = '#F8F9FA'
CLR_EDGE = '#343A40'
CLR_GRID = '#E9ECEF'

# Rebar Colors
CLR_BAR_TOP = '#D32F2F'  # Red for Negative Moment
CLR_BAR_BOT = '#1976D2'  # Blue for Positive Moment

# Zone Colors (Restored for tab_ddm.py compatibility)
CLR_ZONE_CS = '#FFF0F0'  # Column Strip Background
CLR_ZONE_MS = '#F0F8FF'  # Middle Strip Background

# Line Weights
LW_BAR = 2.5
LW_DIM = 0.8
LW_BORDER = 1.2

def setup_axis_labels(ax, title, xlabel="Distance (m)", ylabel="Moment (kg-m)"):
    """Standardize graph axis"""
    ax.set_title(title, loc='left', fontsize=12, fontweight='bold', pad=15)
    ax.set_xlabel(xlabel, fontsize=9, fontweight='bold')
    ax.set_ylabel(ylabel, fontsize=9, fontweight='bold')
    
    # Grid & Spines
    ax.grid(True, which='both', ls='--', lw=0.5, color=CLR_GRID, zorder=0)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_linewidth(0.5)
    ax.spines['bottom'].set_linewidth(0.5)

def draw_dimension(ax, x1, y1, x2, y2, text, offset=0.3, color='#555'):
    """Draw engineering dimension line with arrows"""
    # Main line
    ax.annotate('', xy=(x1, y1), xytext=(x2, y2),
                arrowprops=dict(arrowstyle='<|-|>', color=color, lw=0.8))
    
    # Text
    mid_x, mid_y = (x1 + x2)/2, (y1 + y2)/2
    if x1 == x2: # Vertical
        t_x, t_y = mid_x + offset, mid_y
        rot = 90
    else: # Horizontal
        t_x, t_y = mid_x, mid_y + offset
        rot = 0
        
    bbox = dict(boxstyle="round,pad=0.1", fc='white', ec='none', alpha=0.8)
    ax.text(t_x, t_y, text, ha='center', va='center', fontsize=8, 
            color=color, rotation=rot, bbox=bbox, zorder=20)

# ==========================================
# 1. BENDING MOMENT DIAGRAM (With Axis)
# ==========================================
def plot_ddm_moment(L_span, c1, m_vals):
    fig, ax = plt.subplots(figsize=(10, 4), facecolor=CLR_BG)
    
    # Data Generation
    x = np.linspace(0, L_span, 400)
    M_neg_cs, M_pos_cs = m_vals['M_cs_neg'], m_vals['M_cs_pos']
    M_neg_ms, M_pos_ms = m_vals['M_ms_neg'], m_vals['M_ms_pos']

    # Interpolation Points (Simplified parabolic shape)
    pts_x = [0, L_span*0.2, L_span*0.5, L_span*0.8, L_span]
    pts_y_cs = [-M_neg_cs, 0, M_pos_cs, 0, -M_neg_cs]
    pts_y_ms = [-M_neg_ms, 0, M_pos_ms, 0, -M_neg_ms]
    
    y_cs = np.interp(x, pts_x, pts_y_cs)
    y_ms = np.interp(x, pts_x, pts_y_ms)

    # Plot Lines
    ax.axhline(0, color='black', lw=0.8, zorder=1)
    ax.plot(x, y_ms, label='Middle Strip', color=CLR_BAR_BOT, lw=1.5, ls='--', alpha=0.6)
    ax.plot(x, y_cs, label='Column Strip', color=CLR_BAR_TOP, lw=2.5)

    # Fill Areas
    ax.fill_between(x, y_cs, 0, where=(y_cs<0), color=CLR_BAR_TOP, alpha=0.1)
    ax.fill_between(x, y_cs, 0, where=(y_cs>0), color=CLR_BAR_BOT, alpha=0.1)

    # Styling
    setup_axis_labels(ax, f"BENDING MOMENT DIAGRAM (Span = {L_span:.2f} m)")
    
    # Format Y Axis with Commas
    ax.yaxis.set_major_formatter(ticker.StrMethodFormatter('{x:,.0f}'))
    
    # Peak Value Labels
    def annotate_peak(px, py, txt, c, va):
        bbox = dict(boxstyle="round,pad=0.2", fc='white', ec=c, lw=0.5)
        ax.text(px, py, txt, color=c, fontsize=9, fontweight='bold', 
                ha='center', va=va, bbox=bbox, zorder=10)

    annotate_peak(0, -M_neg_cs, f"{M_neg_cs:,.0f}", CLR_BAR_TOP, 'top')
    annotate_peak(L_span/2, M_pos_cs, f"{M_pos_cs:,.0f}", CLR_BAR_BOT, 'bottom')

    ax.legend(loc='best', frameon=True)
    plt.tight_layout()
    return fig

# ==========================================
# 2. SECTION A-A (Correct Detailing)
# ==========================================
def plot_rebar_detailing(L_span, h_slab, c_para, rebar_results, axis_dir):
    """
    Shows longitudinal bars only.
    Top bars: Cut-off at 0.3L.
    Bottom bars: Continuous.
    """
    h_m = h_slab / 100.0
    c_m = c_para / 100.0 # Column dimension
    
    fig, ax = plt.subplots(figsize=(10, 3.5), facecolor=CLR_BG)
    ax.axis('off')

    # --- 1. Draw Concrete Outline ---
    # Slab
    rect = patches.Rectangle((0, 0), L_span, h_m, fc=CLR_CONCRETE, ec=CLR_EDGE, lw=1.5)
    ax.add_patch(rect)
    
    # Columns (Top/Bottom stubs)
    col_h = 0.5 # visual height
    for cx in [0, L_span]:
        # Top Column stub
        ax.add_patch(patches.Rectangle((cx - c_m/2, h_m), c_m, col_h, fc='white', ec=CLR_EDGE, hatch='///'))
        # Bot Column stub
        ax.add_patch(patches.Rectangle((cx - c_m/2, -col_h), c_m, col_h, fc='white', ec=CLR_EDGE, hatch='///'))
        # Center Line
        ax.plot([cx, cx], [-col_h*1.2, h_m+col_h*1.2], 'k-.', lw=0.5, alpha=0.5)

    # --- 2. Draw Rebars (Longitudinal Only) ---
    cover = 0.025
    y_top = h_m - cover
    y_bot = cover
    
    # >> Top Bars (Support Only) - Standard Cutoff ~0.3L or L/3
    cutoff_len = L_span / 3.0
    
    # Left Top Bar
    ax.plot([-c_m/2, cutoff_len], [y_top, y_top], color=CLR_BAR_TOP, lw=LW_BAR)
    ax.plot([-c_m/2, -c_m/2], [y_top, y_top - 0.15], color=CLR_BAR_TOP, lw=LW_BAR) # Hook
    
    # Right Top Bar
    ax.plot([L_span - cutoff_len, L_span + c_m/2], [y_top, y_top], color=CLR_BAR_TOP, lw=LW_BAR)
    ax.plot([L_span + c_m/2, L_span + c_m/2], [y_top, y_top - 0.15], color=CLR_BAR_TOP, lw=LW_BAR) # Hook

    # >> Bottom Bar (Continuous)
    ax.plot([0, L_span], [y_bot, y_bot], color=CLR_BAR_BOT, lw=LW_BAR)
    # Hooks for bottom bars (Optional but good practice)
    ax.plot([0, 0], [y_bot, y_bot + 0.10], color=CLR_BAR_BOT, lw=LW_BAR)
    ax.plot([L_span, L_span], [y_bot, y_bot + 0.10], color=CLR_BAR_BOT, lw=LW_BAR)

    # --- 3. Annotations & Dimensions ---
    
    # Dimension: L/3 for Top Bars
    draw_dimension(ax, 0, h_m + 0.1, cutoff_len, h_m + 0.1, f"$L/3 = {cutoff_len:.2f}$ m", offset=0.1)
    draw_dimension(ax, L_span - cutoff_len, h_m + 0.1, L_span, h_m + 0.1, f"$L/3$", offset=0.1)

    # Labels for Rebar
    txt_top = rebar_results.get('CS_Top', 'DB??')
    txt_bot = rebar_results.get('CS_Bot', 'DB??')
    
    # Top Label
    ax.annotate(f"Top: {txt_top}", xy=(cutoff_len/2, y_top), xytext=(cutoff_len/2, y_top + 0.4),
                arrowprops=dict(arrowstyle='->', color=CLR_BAR_TOP), color=CLR_BAR_TOP, fontweight='bold')
    
    # Bot Label
    ax.annotate(f"Bot: {txt_bot}", xy=(L_span/2, y_bot), xytext=(L_span/2, y_bot - 0.4),
                arrowprops=dict(arrowstyle='->', color=CLR_BAR_BOT), color=CLR_BAR_BOT, fontweight='bold')

    ax.set_title(f"SECTION A-A: LONGITUDINAL REBAR ({axis_dir}-Direction)", fontsize=11, fontweight='bold', pad=20)
    
    # Adjust Zoom
    ax.set_xlim(-0.5, L_span + 0.5)
    ax.set_ylim(-0.8, h_m + 1.0)
    plt.tight_layout()
    return fig

# ==========================================
# 3. PLAN VIEW (Correct Layout & Cutoffs)
# ==========================================
def plot_rebar_plan_view(L_span, L_width, c_para, rebar_results, axis_dir):
    """
    Plan view showing Column Strip (CS) and Middle Strip (MS).
    Top bars at edges (Supports). Bottom bars continuous.
    Includes cut-off dimensions.
    """
    fig, ax = plt.subplots(figsize=(8, 8), facecolor=CLR_BG)
    ax.axis('off')
    
    # Geometry
    W = L_span if axis_dir == 'X' else L_width
    H = L_width if axis_dir == 'X' else L_span
    
    # Strip Widths
    w_cs_half = min(L_span, L_width) / 4.0 # Half CS width at each edge
    
    # --- 1. Draw Zones (CS / MS) ---
    # Backgrounds for strips
    # Bottom Edge (CS)
    ax.add_patch(patches.Rectangle((0, 0), W, w_cs_half, fc=CLR_ZONE_CS, ec='none'))
    ax.text(W/2, w_cs_half/2, "Column Strip", color=CLR_BAR_TOP, alpha=0.1, ha='center', va='center', fontweight='bold', fontsize=15)
    
    # Top Edge (CS)
    ax.add_patch(patches.Rectangle((0, H - w_cs_half), W, w_cs_half, fc=CLR_ZONE_CS, ec='none'))
    ax.text(W/2, H - w_cs_half/2, "Column Strip", color=CLR_BAR_TOP, alpha=0.1, ha='center', va='center', fontweight='bold', fontsize=15)
    
    # Middle (MS)
    ax.add_patch(patches.Rectangle((0, w_cs_half), W, H - 2*w_cs_half, fc=CLR_ZONE_MS, ec='none'))
    ax.text(W/2, H/2, "Middle Strip", color=CLR_BAR_BOT, alpha=0.1, ha='center', va='center', fontweight='bold', fontsize=15)

    # Outline
    ax.add_patch(patches.Rectangle((0, 0), W, H, fill=False, ec='black', lw=1.5))

    # --- 2. Draw Rebars (Smart Logic) ---
    # Cutoff length for top bars
    cutoff = W / 3.0
    
    def draw_rebar_line(y_pos, type_z, is_top):
        """Draws a single line of rebar with correct cutoff logic"""
        c = CLR_BAR_TOP if is_top else CLR_BAR_BOT
        lbl = rebar_results.get(f"{type_z}_{'Top' if is_top else 'Bot'}", "?")
        
        if is_top:
            # Left/Bot Support (depending on rotation, but here Left/Right in plot coords)
            # Left Bar
            ax.plot([0, cutoff], [y_pos, y_pos], color=c, lw=2)
            ax.plot([cutoff], [y_pos], marker='|', color=c, ms=10) # End marker
            
            # Right Bar
            ax.plot([W-cutoff, W], [y_pos, y_pos], color=c, lw=2)
            ax.plot([W-cutoff], [y_pos], marker='|', color=c, ms=10) # End marker
            
            # Label
            ax.text(cutoff/2, y_pos + 0.1, lbl, color=c, fontsize=8, fontweight='bold', ha='center')
            ax.text(W - cutoff/2, y_pos + 0.1, lbl, color=c, fontsize=8, fontweight='bold', ha='center')
            
        else:
            # Continuous Bottom Bar
            ax.plot([0, W], [y_pos, y_pos], color=c, lw=2)
            ax.text(W/2, y_pos + 0.1, lbl, color=c, fontsize=8, fontweight='bold', ha='center')

    # >> Draw CS Bars (Bottom Zone)
    draw_rebar_line(w_cs_half * 0.3, 'CS', is_top=False) # Bot
    draw_rebar_line(w_cs_half * 0.7, 'CS', is_top=True)  # Top

    # >> Draw MS Bars (Middle Zone)
    draw_rebar_line(H/2 - 0.3, 'MS', is_top=False) # Bot
    draw_rebar_line(H/2 + 0.3, 'MS', is_top=True)  # Top (Usually minimum steel)

    # >> Draw CS Bars (Top Zone)
    draw_rebar_line(H - w_cs_half * 0.7, 'CS', is_top=True)  # Top
    draw_rebar_line(H - w_cs_half * 0.3, 'CS', is_top=False) # Bot

    # --- 3. Dimensions ---
    # Show Cut-off Dimension L/3
    y_dim = H + 0.5
    draw_dimension(ax, 0, y_dim, cutoff, y_dim, f"$L/3$", offset=0.2, color='black')
    draw_dimension(ax, W-cutoff, y_dim, W, y_dim, f"$L/3$", offset=0.2, color='black')
    
    # Overall Dimensions
    draw_dimension(ax, 0, -0.5, W, -0.5, f"$L_1$ (Span) = {W:.2f} m", offset=-0.4)
    draw_dimension(ax, W + 0.5, 0, W + 0.5, H, f"$L_2$ (Width) = {H:.2f} m", offset=0.4)

    # Orientation Arrow
    if axis_dir == 'Y':
        # If Y-direction, rotate view logically implies we are looking at rotated plan
        ax.text(W/2, -1.5, "(View Rotated for Y-Direction Analysis)", ha='center', fontsize=9, fontstyle='italic')

    ax.set_title(f"PLAN VIEW: REBAR LAYOUT ({axis_dir}-Direction)", fontsize=12, fontweight='bold', pad=20)
    
    ax.set_xlim(-1, W + 1)
    ax.set_ylim(-2, H + 2)
    plt.tight_layout()
    return fig
