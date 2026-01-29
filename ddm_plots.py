import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# ==========================================
# 🎨 GLOBAL STYLING & COLORS (Engineering Standard)
# ==========================================
CLR_CONCRETE = '#F9F9F9'  # สีคอนกรีต (ขาวควันบุหรี่)
CLR_COL_HATCH = '#4A5568' # สีเสา (เทาเข้ม)
CLR_DIM = '#718096'       # สีเส้นบอกระยะ (Cool Gray)

# Rebar Colors
CLR_BAR_TOP = '#C53030'   # แดงเข้ม (Top / Negative)
CLR_BAR_BOT = '#2B6CB0'   # น้ำเงินเข้ม (Bot / Positive)

# Background Zones (Plan View)
CLR_ZONE_CS = '#FFF5F5'   # ชมพูจางๆ (Column Strip)
CLR_ZONE_MS = '#EBF8FF'   # ฟ้าจางๆ (Middle Strip)

def setup_cad_style(ax, title):
    """จัด Style ให้สะอาดตาเหมือนแบบก่อสร้าง"""
    ax.set_title(title, loc='left', fontsize=10, fontweight='bold', pad=15, color='#2D3748')
    ax.axis('off')
    ax.figure.patch.set_alpha(0.0)
    ax.patch.set_alpha(0.0)

def add_dim(ax, x1, y1, x2, y2, text, offset=0.5, is_vert=False):
    """วาด Dimension Line แบบมีหัวลูกศร"""
    # เส้นหลัก
    ax.annotate('', xy=(x1, y1), xytext=(x2, y2),
                arrowprops=dict(arrowstyle='<|-|>', color=CLR_DIM, lw=0.6))
    
    # คำนวณตำแหน่ง Text
    mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
    if is_vert:
        txt_x, txt_y = mid_x + offset, mid_y
        rot = 90
    else:
        txt_x, txt_y = mid_x, mid_y + offset
        rot = 0
        
    bbox = dict(boxstyle="round,pad=0.2", fc="white", ec=CLR_DIM, lw=0.5, alpha=0.9)
    ax.text(txt_x, txt_y, text, ha='center', va='center', 
            fontsize=7, color=CLR_DIM, bbox=bbox, fontweight='600', rotation=rot)

# ==========================================
# 1. MOMENT DIAGRAM
# ==========================================
def plot_ddm_moment(L_span, c1, m_vals):
    fig, ax = plt.subplots(figsize=(9, 3))
    
    x = np.linspace(0, L_span, 200)
    M_neg_cs, M_pos_cs = m_vals['M_cs_neg'], m_vals['M_cs_pos']
    M_neg_ms, M_pos_ms = m_vals['M_ms_neg'], m_vals['M_ms_pos']

    pts = [0, L_span*0.2, L_span*0.5, L_span*0.8, L_span]
    y_cs = np.interp(x, pts, [-M_neg_cs, 0, M_pos_cs, 0, -M_neg_cs])
    y_ms = np.interp(x, pts, [-M_neg_ms, 0, M_pos_ms, 0, -M_neg_ms])

    # Plot
    ax.plot(x, y_cs, label='Col Strip', color=CLR_BAR_TOP, lw=1.8)
    ax.plot(x, y_ms, label='Mid Strip', color=CLR_BAR_BOT, lw=1.8, ls='--')
    
    ax.fill_between(x, y_cs, 0, alpha=0.08, color=CLR_BAR_TOP)
    ax.axhline(0, color=CLR_DIM, lw=0.8)
    
    limit = max(abs(np.concatenate([y_cs, y_ms]))) * 1.4
    ax.set_ylim(limit, -limit) 
    
    # Value Tags
    bbox_val = dict(boxstyle="round,pad=0.1", fc=CLR_BAR_TOP, ec="none", alpha=0.1)
    ax.text(0, -M_neg_cs*1.1, f"{M_neg_cs:,.0f}", color=CLR_BAR_TOP, fontsize=7, ha='left', va='bottom', fontweight='bold', bbox=bbox_val)
    ax.text(L_span/2, M_pos_cs*1.1, f"{M_pos_cs:,.0f}", color=CLR_BAR_TOP, fontsize=7, ha='center', va='top', fontweight='bold', bbox=bbox_val)

    setup_cad_style(ax, f"BENDING MOMENT (L={L_span}m)")
    ax.legend(fontsize=7, loc='upper right')
    ax.grid(True, ls=':', color='#E2E8F0')
    
    return fig

# ==========================================
# 2. SECTION VIEW (แก้ตำแหน่ง Dots ให้สมจริง)
# ==========================================
def plot_rebar_detailing(L_span, h_slab, c_para, rebar_results, axis_dir):
    h_m = h_slab / 100.0
    c_m = c_para / 100.0
    
    # Adjust Figure Size
    fig_w = 9
    fig_h = max(3.5, fig_w * (h_m/L_span) * 5) # Scale height visually
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    
    # 2.1 Concrete Body
    ax.add_patch(patches.Rectangle((0, 0), L_span, h_m, fc=CLR_CONCRETE, ec=CLR_DIM, lw=0.8))
    
    # Columns
    col_h = 0.4
    for x_c in [-c_m/2, L_span-c_m/2]:
        # Top Col
        ax.add_patch(patches.Rectangle((x_c, h_m), c_m, col_h, fc='white', ec=CLR_DIM, hatch='///', lw=0.5))
        # Bot Col
        ax.add_patch(patches.Rectangle((x_c, -col_h), c_m, col_h, fc='white', ec=CLR_DIM, hatch='///', lw=0.5))

    # 2.2 Main Rebar (Outer Layer - เพื่อค่า d มากสุด)
    cover = 0.03
    bar_dia = 0.012 # สมมติขนาด visual
    y_top = h_m - cover - (bar_dia/2)
    y_bot = cover + (bar_dia/2)
    
    bar_len = L_span * 0.3
    
    # Top Bars (Red)
    ax.plot([-c_m/2, bar_len], [y_top, y_top], color=CLR_BAR_TOP, lw=3, solid_capstyle='round')
    ax.plot([L_span-bar_len, L_span+c_m/2], [y_top, y_top], color=CLR_BAR_TOP, lw=3, solid_capstyle='round')
    # Bot Bars (Blue)
    ax.plot([0, L_span], [y_bot, y_bot], color=CLR_BAR_BOT, lw=3, solid_capstyle='round')
    
    # 2.3 Transverse Dots (Inner Layer - อยู่ลึกกว่า)
    # ต้องวาด "ใต้" เหล็กบน และ "เหนือ" เหล็กล่าง
    y_dot_top = y_top - 0.02 # ขยับลงมา
    y_dot_bot = y_bot + 0.02 # ขยับขึ้นไป
    
    x_dots = np.arange(0.2, L_span, 0.25)
    
    # Dots Top (Red outline)
    ax.scatter(x_dots, [y_dot_top]*len(x_dots), c='white', edgecolors=CLR_BAR_TOP, s=25, zorder=4, linewidths=1.5)
    # Dots Bot (Blue outline)
    ax.scatter(x_dots, [y_dot_bot]*len(x_dots), c='white', edgecolors=CLR_BAR_BOT, s=25, zorder=4, linewidths=1.5)

    # 2.4 Text & Dim
    add_dim(ax, 0, -0.25, L_span, -0.25, f"Span L1 ({axis_dir}) = {L_span:.2f} m", offset=0.1)
    add_dim(ax, L_span+0.2, 0, L_span+0.2, h_m, f"h={h_slab}cm", is_vert=True, offset=0.1)

    t_style = dict(boxstyle="round,pad=0.1", fc="white", ec="none", alpha=0.8)
    ax.text(bar_len/2, y_top+0.12, rebar_results.get('CS_Top',''), color=CLR_BAR_TOP, fontsize=8, ha='center', fontweight='bold', bbox=t_style)
    ax.text(L_span/2, y_bot-0.12, rebar_results.get('CS_Bot',''), color=CLR_BAR_BOT, fontsize=8, ha='center', fontweight='bold', bbox=t_style)

    setup_cad_style(ax, f"SECTION A-A ({axis_dir}-DIRECTION)")
    ax.set_xlim(-0.6, L_span + 0.6)
    ax.set_ylim(-col_h-0.1, h_m+col_h+0.1)
    
    return fig

# ==========================================
# 3. PLAN VIEW (แก้ Logic การทับกัน)
# ==========================================
def plot_rebar_plan_view(L_span, L_width, c_para, rebar_results, axis_dir):
    """
    Key Fix:
    - แยกเลน (Offset) ระหว่างเหล็ก Top กับ Bot ใน Strip เดียวกัน
    - ไม่ให้เส้นทับกัน ไม่ให้ตัวหนังสือทับกัน
    """
    
    # Setup Canvas
    if axis_dir == 'X':
        plot_w, plot_h = L_span, L_width
        fig_w, fig_h = 8, 8 * (L_width/L_span)
    else:
        plot_w, plot_h = L_width, L_span
        fig_w, fig_h = 8 * (L_width/L_span), 8
        if fig_h > 10: fig_h = 10 # Limit height
        
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    
    # Draw Background Zones
    w_cs = min(L_span, L_width) / 2.0
    w_cs_half = w_cs / 2.0
    
    if axis_dir == 'X':
        rects = [
            (0, 0, plot_w, w_cs_half, CLR_ZONE_CS), # Bot CS
            (0, plot_h-w_cs_half, plot_w, w_cs_half, CLR_ZONE_CS), # Top CS
            (0, w_cs_half, plot_w, plot_h-2*w_cs_half, CLR_ZONE_MS) # Mid
        ]
    else:
        rects = [
            (0, 0, w_cs_half, plot_h, CLR_ZONE_CS), # Left CS
            (plot_w-w_cs_half, 0, w_cs_half, plot_h, CLR_ZONE_CS), # Right CS
            (w_cs_half, 0, plot_w-2*w_cs_half, plot_h, CLR_ZONE_MS) # Mid
        ]
        
    for (rx, ry, rw, rh, rc) in rects:
        ax.add_patch(patches.Rectangle((rx, ry), rw, rh, fc=rc))

    # Draw Columns
    c_m = c_para / 100.0
    for cx in [0, plot_w]:
        for cy in [0, plot_h]:
            ax.add_patch(patches.Rectangle((cx-c_m/2, cy-c_m/2), c_m, c_m, fc=CLR_COL_HATCH, zorder=10))
            
    # Draw Border
    ax.add_patch(patches.Rectangle((0,0), plot_w, plot_h, fill=False, ec=CLR_DIM, lw=1))

    # === Helper Drawing Function with OFFSET ===
    def draw_bar_offset(zone_type, is_top, color):
        """
        zone_type: 'CS_Bot', 'CS_Top', 'MS'
        Offset Logic:
         - Top Bar: Shifted +Offset from center line
         - Bot Bar: Shifted -Offset from center line
        This prevents overlapping!
        """
        key = f"{zone_type}_{'Top' if is_top else 'Bot'}"
        if 'MS' in zone_type: key = f"MS_{'Top' if is_top else 'Bot'}" # Handle naming match
        
        txt = rebar_results.get(key, '')
        bar_len = L_span * 0.3
        
        # Determine Center Line of the Strip
        centers = [] # List of (x_center, y_center, orientation)
        
        if axis_dir == 'X':
            # Orientation: Horizontal Lines
            if zone_type == 'CS_Bot':   centers = [w_cs_half / 2]
            elif zone_type == 'CS_Top': centers = [plot_h - (w_cs_half / 2)]
            elif zone_type == 'MS':     centers = [plot_h / 2]
            
            # Apply Offset (Separation)
            offset = 0.15 # meters separation
            y_pos = centers[0] + (offset if is_top else -offset)
            
            # Draw
            if is_top:
                # Left & Right Supports
                ax.plot([-0.1, bar_len], [y_pos, y_pos], color=color, lw=2)
                ax.plot([plot_w-bar_len, plot_w+0.1], [y_pos, y_pos], color=color, lw=2)
                # Label
                ax.text(bar_len/2, y_pos, txt, color=color, fontsize=7, ha='center', va='bottom', fontweight='bold', 
                        bbox=dict(fc='white', ec=color, pad=0.1, alpha=0.9))
            else:
                # Continuous Bottom
                ax.plot([0, plot_w], [y_pos, y_pos], color=color, lw=2)
                ax.text(plot_w/2, y_pos, txt, color=color, fontsize=7, ha='center', va='top', fontweight='bold',
                        bbox=dict(fc='white', ec=color, pad=0.1, alpha=0.9))

        else: # Y-Direction
            # Orientation: Vertical Lines
            if zone_type == 'CS_Bot':   centers = [w_cs_half / 2] # Use 'Bot' as Left here for loop simplicity
            elif zone_type == 'CS_Top': centers = [plot_w - (w_cs_half / 2)] # Right
            elif zone_type == 'MS':     centers = [plot_w / 2]
            
            # Apply Offset
            offset = 0.15
            x_pos = centers[0] + (offset if is_top else -offset)
            
            if is_top:
                ax.plot([x_pos, x_pos], [-0.1, bar_len], color=color, lw=2)
                ax.plot([x_pos, x_pos], [plot_h-bar_len, plot_h+0.1], color=color, lw=2)
                ax.text(x_pos, bar_len/2, txt, color=color, fontsize=7, ha='left', va='center', fontweight='bold', rotation=90,
                         bbox=dict(fc='white', ec=color, pad=0.1, alpha=0.9))
            else:
                ax.plot([x_pos, x_pos], [0, plot_h], color=color, lw=2)
                ax.text(x_pos, plot_h/2, txt, color=color, fontsize=7, ha='right', va='center', fontweight='bold', rotation=90,
                        bbox=dict(fc='white', ec=color, pad=0.1, alpha=0.9))

    # === EXECUTE DRAWING ===
    # วาดทีละ Layer เพื่อให้เห็นชัดเจน ไม่ทับกัน
    if axis_dir == 'X':
        # Column Strip Bottom
        draw_bar_offset('CS_Bot', False, CLR_BAR_BOT) # Bot Steel
        draw_bar_offset('CS_Bot', True, CLR_BAR_TOP)  # Top Steel (in same strip!)
        
        # Column Strip Top
        draw_bar_offset('CS_Top', False, CLR_BAR_BOT)
        draw_bar_offset('CS_Top', True, CLR_BAR_TOP)

        # Middle Strip
        draw_bar_offset('MS', False, CLR_BAR_BOT)
        draw_bar_offset('MS', True, CLR_BAR_TOP)
        
        # Dimensions
        add_dim(ax, 0, -0.6, plot_w, -0.6, f"Span L1 = {plot_w:.2f}m")
        add_dim(ax, plot_w+0.6, 0, plot_w+0.6, plot_h, f"Width L2 = {plot_h:.2f}m", is_vert=True)

    else: # Y-Direction
        # Left CS (Named CS_Bot in loop logic for left side)
        draw_bar_offset('CS_Bot', False, CLR_BAR_BOT)
        draw_bar_offset('CS_Bot', True, CLR_BAR_TOP)
        
        # Right CS
        draw_bar_offset('CS_Top', False, CLR_BAR_BOT)
        draw_bar_offset('CS_Top', True, CLR_BAR_TOP)
        
        # Middle
        draw_bar_offset('MS', False, CLR_BAR_BOT)
        draw_bar_offset('MS', True, CLR_BAR_TOP)

        # Dimensions
        add_dim(ax, 0, -0.6, plot_w, -0.6, f"Width L2 = {plot_w:.2f}m")
        add_dim(ax, plot_w+0.6, 0, plot_w+0.6, plot_h, f"Span L1 = {plot_h:.2f}m", is_vert=True)

    setup_cad_style(ax, f"PLAN LAYOUT ({axis_dir}-DIRECTION)")
    
    pad = 1.0
    ax.set_xlim(-pad, plot_w + pad)
    ax.set_ylim(-pad, plot_h + pad)
    
    return fig
