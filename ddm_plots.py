import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# ==========================================
# 🎨 PROFESSIONAL ENGINEERING STYLING
# ==========================================
# Color Palette (Technical & Clean)
CLR_BG = 'white'
CLR_CONCRETE_FILL = '#F8F9FA'
CLR_CONCRETE_EDGE = '#495057'
CLR_HATCH = '#ADB5BD'
CLR_DIM_LINE = '#6C757D'
CLR_DIM_TEXT = '#343A40'

# Rebar Colors (High Contrast)
CLR_BAR_TOP = '#C0392B'  # Engineering Red (Negative Moment)
CLR_BAR_BOT = '#0056b3'  # Engineering Blue (Positive Moment)

# Plan View Zones (Subtle pastel)
CLR_ZONE_CS = '#FFF0F0'
CLR_ZONE_MS = '#F0F8FF'

# Line Weights
LW_BAR_MAIN = 3.0
LW_BAR_TRANS = 1.5
LW_DIM = 0.8
LW_EDGE = 1.0

def setup_pro_style(ax, title):
    """ตั้งค่า Style กราฟให้เป็นแบบมืออาชีพ"""
    ax.set_title(title, loc='left', fontsize=11, fontweight='700', pad=15, color='#212529')
    ax.axis('off')
    # Ensure crisp edges
    for spine in ax.spines.values():
        spine.set_visible(False)

def add_pro_dim(ax, x1, y1, x2, y2, text, offset=0.5, is_vert=False):
    """วาดเส้นบอกระยะ Dimension Line แบบมืออาชีพ"""
    # Arrow style
    arrow = dict(arrowstyle='<|-|>', color=CLR_DIM_LINE, lw=LW_DIM, shrinkA=0, shrinkB=0)
    ax.annotate('', xy=(x1, y1), xytext=(x2, y2), arrowprops=arrow)
    
    mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
    
    if is_vert:
        txt_x, txt_y = mid_x + offset, mid_y
        rot = 90
        va, ha = 'center', 'center'
    else:
        txt_x, txt_y = mid_x, mid_y + offset
        rot = 0
        va, ha = 'center', 'center'
        
    # Text box with background to prevent overlapping
    bbox = dict(boxstyle="round,pad=0.25", fc=CLR_BG, ec=CLR_DIM_LINE, lw=0.5, alpha=0.95)
    ax.text(txt_x, txt_y, text, ha=ha, va=va, fontsize=8, color=CLR_DIM_TEXT, 
            bbox=bbox, fontweight='600', rotation=rot, zorder=20)

# ==========================================
# 1. MOMENT DIAGRAM (Improved)
# ==========================================
def plot_ddm_moment(L_span, c1, m_vals):
    fig, ax = plt.subplots(figsize=(10, 3.5), facecolor=CLR_BG)
    
    x = np.linspace(0, L_span, 300)
    M_neg_cs, M_pos_cs = m_vals['M_cs_neg'], m_vals['M_cs_pos']
    M_neg_ms, M_pos_ms = m_vals['M_ms_neg'], m_vals['M_ms_pos']

    # Smooth Curve Interpolation
    pts_x = [0, L_span*0.15, L_span*0.5, L_span*0.85, L_span]
    pts_y_cs = [-M_neg_cs, 0, M_pos_cs, 0, -M_neg_cs]
    pts_y_ms = [-M_neg_ms, 0, M_pos_ms, 0, -M_neg_ms]
    
    from scipy.interpolate import make_interp_spline
    spl_cs = make_interp_spline(pts_x, pts_y_cs, k=3)
    spl_ms = make_interp_spline(pts_x, pts_y_ms, k=3)
    y_cs = spl_cs(x)
    y_ms = spl_ms(x)

    # Plotting with hierarchy
    ax.axhline(0, color=CLR_CONCRETE_EDGE, lw=1.0, zorder=1)
    
    # Middle Strip (Secondary)
    ax.plot(x, y_ms, label='Middle Strip', color=CLR_BAR_BOT, lw=2, ls='--', alpha=0.7, zorder=2)
    
    # Column Strip (Primary)
    ax.plot(x, y_cs, label='Column Strip', color=CLR_BAR_TOP, lw=2.5, zorder=3)
    ax.fill_between(x, y_cs, 0, where=(y_cs<0), alpha=0.1, color=CLR_BAR_TOP, zorder=0)
    ax.fill_between(x, y_cs, 0, where=(y_cs>0), alpha=0.1, color=CLR_BAR_BOT, zorder=0)
    
    # Peak Annotations
    limit = max(abs(np.concatenate([y_cs, y_ms]))) * 1.3
    ax.set_ylim(limit, -limit) # Standard engineering convention (Neg moment top)
    
    bbox_peak = dict(boxstyle="round,pad=0.2", fc=CLR_BG, ec="none", alpha=0.9)
    ax.text(0, -M_neg_cs*1.05, f"M- (CS)\n{M_neg_cs:,.0f}", color=CLR_BAR_TOP, fontsize=8, ha='left', va='bottom', fontweight='bold', bbox=bbox_peak, zorder=10)
    ax.text(L_span/2, M_pos_cs*1.05, f"M+ (CS)\n{M_pos_cs:,.0f}", color=CLR_BAR_BOT, fontsize=8, ha='center', va='top', fontweight='bold', bbox=bbox_peak, zorder=10)

    setup_pro_style(ax, f"BENDING MOMENT DIAGRAM (Span L = {L_span:.2f}m)")
    ax.legend(fontsize=9, loc='upper right', frameon=True, framealpha=1.0, edgecolor=CLR_DIM_LINE)
    ax.grid(True, ls=':', color=CLR_DIM_LINE, alpha=0.3, zorder=0)
    
    plt.tight_layout()
    return fig

# ==========================================
# 2. SECTION VIEW (Professional Layering)
# ==========================================
def plot_rebar_detailing(L_span, h_slab, c_para, rebar_results, axis_dir):
    h_m = h_slab / 100.0
    c_m = c_para / 100.0
    
    # Dynamic Figure Size based on aspect ratio
    aspect = L_span / h_m
    fig_w = 10
    fig_h = max(4, fig_w / aspect * 2) # Ensure enough height for details
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), facecolor=CLR_BG)
    
    # 2.1 Concrete & Supports
    # Slab
    ax.add_patch(patches.Rectangle((0, 0), L_span, h_m, fc=CLR_CONCRETE_FILL, ec=CLR_CONCRETE_EDGE, lw=LW_EDGE, zorder=0))
    # Columns (Hatched)
    col_h = h_m * 0.6 # Proportional column stub height
    hatch_style = dict(hatch='////', fc='white', ec=CLR_HATCH, lw=0.5, zorder=1)
    for x_c in [-c_m/2, L_span-c_m/2]:
        ax.add_patch(patches.Rectangle((x_c, h_m), c_m, col_h, edgecolor=CLR_CONCRETE_EDGE, **hatch_style)) # Top
        ax.add_patch(patches.Rectangle((x_c, -col_h), c_m, col_h, edgecolor=CLR_CONCRETE_EDGE, **hatch_style)) # Bot

    # 2.2 Rebar Positioning Logic (Crucial for realism)
    cover = 0.025 # 25mm cover standard
    db_main_est = 0.020 # Estimate 20mm main bar
    db_trans_est = 0.012 # Estimate 12mm transverse bar
    
    # Main Bars (Outer Layer)
    y_main_top = h_m - cover - db_main_est/2
    y_main_bot = cover + db_main_est/2
    
    # Transverse Bars (Inner Layer)
    y_trans_top = y_main_top - db_main_est/2 - db_trans_est/2
    y_trans_bot = y_main_bot + db_main_est/2 + db_trans_est/2

    # 2.3 Draw Main Rebar (Lines)
    bar_len_top = L_span * 0.3
    bar_style = dict(lw=LW_BAR_MAIN, solid_capstyle='round', zorder=10)
    
    # Top Main (Red)
    ax.plot([-c_m/2, bar_len_top], [y_main_top, y_main_top], color=CLR_BAR_TOP, **bar_style)
    ax.plot([L_span-bar_len_top, L_span+c_m/2], [y_main_top, y_main_top], color=CLR_BAR_TOP, **bar_style)
    # Hook ends for top bars
    hook_len = 0.15 * h_m
    ax.plot([bar_len_top, bar_len_top], [y_main_top, y_main_top-hook_len], color=CLR_BAR_TOP, lw=LW_BAR_MAIN*0.7, zorder=9)
    ax.plot([L_span-bar_len_top, L_span-bar_len_top], [y_main_top, y_main_top-hook_len], color=CLR_BAR_TOP, lw=LW_BAR_MAIN*0.7, zorder=9)

    # Bot Main (Blue)
    ax.plot([0, L_span], [y_main_bot, y_main_bot], color=CLR_BAR_BOT, **bar_style)

    # 2.4 Draw Transverse Rebar (Hollow Dots - Inner Layer)
    x_dots = np.arange(0.15, L_span, 0.25)
    dot_style = dict(s=50, facecolors=CLR_BG, lw=LW_BAR_TRANS, zorder=5)
    
    ax.scatter(x_dots, [y_trans_top]*len(x_dots), edgecolors=CLR_BAR_TOP, **dot_style) # Top inner
    ax.scatter(x_dots, [y_trans_bot]*len(x_dots), edgecolors=CLR_BAR_BOT, **dot_style) # Bot inner

    # 2.5 Dimensions & Labels
    pad_dim = h_m * 0.3
    add_pro_dim(ax, 0, -pad_dim, L_span, -pad_dim, f"Span $L_1$ ({axis_dir}) = {L_span:.2f} m", offset=pad_dim/2)
    add_pro_dim(ax, L_span+pad_dim, 0, L_span+pad_dim, h_m, f"$h$={h_slab}cm", is_vert=True, offset=pad_dim/2)

    # Rebar Callouts with clear leaders
    bbox_lbl = dict(boxstyle="round,pad=0.2", fc=CLR_BG, ec=CLR_DIM_LINE, lw=0.5, alpha=1.0)
    
    # CS Top Label
    txt_top = rebar_results.get('CS_Top', '?')
    ax.annotate(txt_top, xy=(bar_len_top/2, y_main_top), xytext=(bar_len_top/2, h_m + col_h*0.5),
                arrowprops=dict(arrowstyle='->', color=CLR_BAR_TOP, connectionstyle="arc3,rad=0.2"),
                color=CLR_BAR_TOP, fontweight='bold', fontsize=9, ha='center', bbox=bbox_lbl, zorder=20)

    # CS Bot Label
    txt_bot = rebar_results.get('CS_Bot', '?')
    ax.annotate(txt_bot, xy=(L_span/2, y_main_bot), xytext=(L_span/2, -col_h*0.5),
                arrowprops=dict(arrowstyle='->', color=CLR_BAR_BOT, connectionstyle="arc3,rad=-0.2"),
                color=CLR_BAR_BOT, fontweight='bold', fontsize=9, ha='center', bbox=bbox_lbl, zorder=20)

    setup_pro_style(ax, f"SECTION A-A: REBAR PROFILE ({axis_dir}-DIR)")
    
    margin_x = L_span * 0.1 + c_m
    margin_y = col_h * 1.2
    ax.set_xlim(-margin_x, L_span + margin_x)
    ax.set_ylim(-margin_y, h_m + margin_y)
    
    plt.tight_layout()
    return fig

# ==========================================
# 3. PLAN VIEW (Professional Layout with No Overlaps)
# ==========================================
def plot_rebar_plan_view(L_span, L_width, c_para, rebar_results, axis_dir):
    """
    Professional Plan View:
    - Uses clear offsets to separate top and bottom bars.
    - Distinct markers for bar ends.
    - Clear zoning and dimensions.
    """
    # Dynamic Canvas Size based on orientation
    if axis_dir == 'X':
        plot_w, plot_h = L_span, L_width
        base = 10
        aspect = plot_h / plot_w
        fig_w, fig_h = base, base * aspect
    else:
        plot_w, plot_h = L_width, L_span
        base = 8 # Slightly narrower base for vertical layout
        aspect = plot_h / plot_w
        fig_w, fig_h = base, base * aspect
        
    # Limit extreme aspect ratios
    if fig_h > 12: fig_h = 12; fig_w = fig_h / aspect
    if fig_w > 12: fig_w = 12; fig_h = fig_w * aspect

    fig, ax = plt.subplots(figsize=(fig_w, fig_h), facecolor=CLR_BG)
    
    # 3.1 Draw Zones & Columns
    w_cs = min(L_span, L_width) / 2.0
    w_cs_half = w_cs / 2.0
    c_m = c_para / 100.0

    # Zones
    zone_patches = []
    if axis_dir == 'X':
        zone_patches = [
            (0, 0, plot_w, w_cs_half, CLR_ZONE_CS, 'CS Bot'),
            (0, plot_h-w_cs_half, plot_w, w_cs_half, CLR_ZONE_CS, 'CS Top'),
            (0, w_cs_half, plot_w, plot_h-2*w_cs_half, CLR_ZONE_MS, 'MS')
        ]
    else:
        zone_patches = [
            (0, 0, w_cs_half, plot_h, CLR_ZONE_CS, 'CS Left'),
            (plot_w-w_cs_half, 0, w_cs_half, plot_h, CLR_ZONE_CS, 'CS Right'),
            (w_cs_half, 0, plot_w-2*w_cs_half, plot_h, CLR_ZONE_MS, 'MS')
        ]
        
    for (rx, ry, rw, rh, rc, lbl) in zone_patches:
        ax.add_patch(patches.Rectangle((rx, ry), rw, rh, fc=rc, ec='none', zorder=0))
        # Subtle zone labels
        ax.text(rx + rw/2, ry + rh/2, lbl, color=CLR_DIM_TEXT, alpha=0.15, 
                ha='center', va='center', fontweight='bold', fontsize=12, zorder=1)

    # Columns
    for cx in [0, plot_w]:
        for cy in [0, plot_h]:
            rect = patches.Rectangle((cx-c_m/2, cy-c_m/2), c_m, c_m, 
                                     fc=CLR_CONCRETE_EDGE, ec=CLR_CONCRETE_EDGE, zorder=15)
            ax.add_patch(rect)
            
    # Slab Border
    ax.add_patch(patches.Rectangle((0,0), plot_w, plot_h, fill=False, ec=CLR_CONCRETE_EDGE, lw=1.5, zorder=5))

    # 3.2 Smart Rebar Drawing Function (The Core Fix)
    def draw_smart_bar(zone_type, is_top, color):
        key = f"{zone_type}_{'Top' if is_top else 'Bot'}"
        if 'MS' in zone_type: key = f"MS_{'Top' if is_top else 'Bot'}"
        txt = rebar_results.get(key, '?')
        
        bar_len = L_span * 0.3
        bar_style = dict(color=color, lw=LW_BAR_MAIN, solid_capstyle='round', zorder=10)
        
        # Offset Logic: Standard separation distance
        offset_dist = 0.20 # meters
        
        # Determine centerline and apply offset
        if axis_dir == 'X': # Horizontal Bars
            if zone_type == 'CS_Bot': center = w_cs_half / 2
            elif zone_type == 'CS_Top': center = plot_h - (w_cs_half / 2)
            elif zone_type == 'MS': center = plot_h / 2
            
            # Top shifts UP (+), Bot shifts DOWN (-)
            y = center + (offset_dist if is_top else -offset_dist)
            
            if is_top:
                # Supports with hooks
                ax.plot([-c_m/2, bar_len], [y, y], **bar_style) # Left
                ax.scatter([bar_len], [y], marker='|', s=100, color=color, zorder=11) # End marker
                ax.plot([plot_w-bar_len, plot_w+c_m/2], [y, y], **bar_style) # Right
                ax.scatter([plot_w-bar_len], [y], marker='|', s=100, color=color, zorder=11)
                lbl_x, lbl_ha, lbl_va = bar_len/2, 'center', 'bottom'
            else:
                # Continuous
                ax.plot([0, plot_w], [y, y], **bar_style)
                lbl_x, lbl_ha, lbl_va = plot_w/2, 'center', 'top'
                
            lbl_y = y + (0.05 if is_top else -0.05)
            rot = 0

        else: # Y-Direction: Vertical Bars
            # Use 'CS_Bot' key for Left, 'CS_Top' for Right strip logic
            if zone_type == 'CS_Bot': center = w_cs_half / 2 
            elif zone_type == 'CS_Top': center = plot_w - (w_cs_half / 2)
            elif zone_type == 'MS': center = plot_w / 2
            
            # Top shifts RIGHT (+), Bot shifts LEFT (-) relative to center
            x = center + (offset_dist if is_top else -offset_dist)
            
            if is_top:
                # Supports with hooks
                ax.plot([x, x], [-c_m/2, bar_len], **bar_style) # Bot support
                ax.scatter([x], [bar_len], marker='_', s=100, color=color, zorder=11)
                ax.plot([x, x], [plot_h-bar_len, plot_h+c_m/2], **bar_style) # Top support
                ax.scatter([x], [plot_h-bar_len], marker='_', s=100, color=color, zorder=11)
                lbl_y, lbl_ha, lbl_va = bar_len/2, 'left', 'center'
            else:
                # Continuous
                ax.plot([x, x], [0, plot_h], **bar_style)
                lbl_y, lbl_ha, lbl_va = plot_h/2, 'right', 'center'
                
            lbl_x = x + (0.05 if is_top else -0.05)
            rot = 90

        # Professional Labeling
        bbox_lbl = dict(boxstyle="round,pad=0.2", fc=CLR_BG, ec=color, lw=0.5, alpha=0.95)
        ax.text(lbl_x, lbl_y, txt, color=color, fontsize=9, ha=lbl_ha, va=lbl_va, 
                fontweight='bold', rotation=rot, bbox=bbox_lbl, zorder=20)

    # 3.3 Execute Drawing (Layered)
    zones_to_draw = [('CS_Bot', CLR_BAR_BOT), ('CS_Top', CLR_BAR_TOP), ('MS', CLR_BAR_BOT), ('MS', CLR_BAR_TOP)]
    if axis_dir == 'Y':
         # For Y, we use CS_Bot for Left, CS_Top for Right
         zones_to_draw = [('CS_Bot', CLR_BAR_BOT), ('CS_Bot', CLR_BAR_TOP), 
                          ('CS_Top', CLR_BAR_BOT), ('CS_Top', CLR_BAR_TOP),
                          ('MS', CLR_BAR_BOT), ('MS', CLR_BAR_TOP)]

    for z_type, color in zones_to_draw:
        is_top = (color == CLR_BAR_TOP)
        draw_smart_bar(z_type, is_top, color)

    # 3.4 Dimensions
    pad_dim = min(plot_w, plot_h) * 0.15
    if axis_dir == 'X':
        add_pro_dim(ax, 0, -pad_dim, plot_w, -pad_dim, f"Span $L_1$ = {plot_w:.2f} m", offset=pad_dim*0.4)
        add_pro_dim(ax, plot_w+pad_dim, 0, plot_w+pad_dim, plot_h, f"Width $L_2$ = {plot_h:.2f} m", is_vert=True, offset=pad_dim*0.4)
    else:
        add_pro_dim(ax, 0, -pad_dim, plot_w, -pad_dim, f"Width $L_2$ = {plot_w:.2f} m", offset=pad_dim*0.4)
        add_pro_dim(ax, plot_w+pad_dim, 0, plot_w+pad_dim, plot_h, f"Span $L_1$ = {plot_h:.2f} m", is_vert=True, offset=pad_dim*0.4)

    setup_pro_style(ax, f"PLAN VIEW: REBAR LAYOUT ({axis_dir}-DIR)")
    
    margin_x = pad_dim * 1.5
    margin_y = pad_dim * 1.5
    ax.set_xlim(-margin_x, plot_w + margin_x)
    ax.set_ylim(-margin_y, plot_h + margin_y)
    
    plt.tight_layout()
    return fig
