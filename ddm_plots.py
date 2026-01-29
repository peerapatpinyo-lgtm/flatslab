import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# ... (ส่วน HELPER และ plot_ddm_moment, plot_rebar_detailing เหมือนเดิม ไม่ต้องแก้) ...
# แต่เพื่อความชัวร์ ผมใส่ให้ครบทั้งไฟล์เลยครับ จะได้ Copy ทีเดียวจบ

# ==========================================
# 🎨 HELPER: CAD STYLING
# ==========================================
def add_dimension(ax, x1, y1, x2, y2, text, offset=0.5, color='black', arrow_color='black', vertical=False):
    """ วาดเส้นบอกระยะ (Dimension Line) รองรับแนวตั้ง/แนวนอน """
    ax.annotate('', xy=(x1, y1), xytext=(x2, y2),
                arrowprops=dict(arrowstyle='<|-|>', color=arrow_color, lw=0.6))
    
    mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
    
    # คำนวณตำแหน่ง Text แบบ Offset
    if vertical:
        txt_x = mid_x + offset
        txt_y = mid_y
        rot = 90
    else:
        txt_x = mid_x
        txt_y = mid_y + offset
        rot = 0

    bbox = dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.8)
    ax.text(txt_x, txt_y, text, ha='center', va='center', 
            fontsize=7, color=color, bbox=bbox, fontweight='bold', rotation=rot)

def setup_cad_style(ax, title):
    ax.set_title(title, loc='left', fontsize=10, fontweight='bold', pad=10, color='#333333')
    ax.axis('off')

# ==========================================
# 1. MOMENT DIAGRAM (เหมือนเดิม)
# ==========================================
def plot_ddm_moment(L_span, c1, m_vals):
    fig, ax = plt.subplots(figsize=(10, 3.5))
    x = np.linspace(0, L_span, 200)
    
    M_neg_cs, M_pos_cs = m_vals['M_cs_neg'], m_vals['M_cs_pos']
    M_neg_ms, M_pos_ms = m_vals['M_ms_neg'], m_vals['M_ms_pos']

    pts = [0, L_span*0.2, L_span*0.5, L_span*0.8, L_span]
    y_cs = np.interp(x, pts, [-M_neg_cs, 0, M_pos_cs, 0, -M_neg_cs])
    y_ms = np.interp(x, pts, [-M_neg_ms, 0, M_pos_ms, 0, -M_neg_ms])

    ax.plot(x, y_cs, label='Column Strip', color='#D32F2F', linewidth=1.5)
    ax.plot(x, y_ms, label='Middle Strip', color='#1976D2', linewidth=1.5, linestyle='--')
    
    ax.fill_between(x, y_cs, 0, alpha=0.05, color='#D32F2F')
    ax.axhline(0, color='black', linewidth=0.8)
    
    limit = max(M_pos_cs, M_neg_cs, M_pos_ms, M_neg_ms) * 1.3
    ax.set_ylim(limit, -limit) 
    
    setup_cad_style(ax, f"MOMENT DISTRIBUTION DIAGRAM (Span {L_span} m)")
    ax.legend(fontsize=8, loc='upper right')
    plt.tight_layout()
    return fig

# ==========================================
# 2. SECTION PROFILE (เพิ่ม Dot เหล็กขวาง)
# ==========================================
def plot_rebar_detailing(L_span, h_slab, c_para, rebar_results, axis_dir):
    fig, ax = plt.subplots(figsize=(10, 4))
    h_m = h_slab / 100
    c_m = c_para / 100
    
    # Structure
    ax.add_patch(patches.Rectangle((0, 0), L_span, h_m, fc='#E0E0E0', ec='black', lw=0.5))
    for x_pos in [-c_m/2, L_span-c_m/2]:
        ax.add_patch(patches.Rectangle((x_pos, -0.5), c_m, 0.5, fc='white', ec='black', hatch='//'))
        ax.add_patch(patches.Rectangle((x_pos, h_m), c_m, 0.5, fc='white', ec='black', hatch='//'))

    # Rebar Lines (Main)
    top_y = h_m - 0.03
    bot_y = 0.03
    bar_L = L_span * 0.3
    
    # Top (Red)
    ax.plot([-c_m/2, bar_L], [top_y, top_y], color='#D32F2F', lw=2.5) # Left
    ax.plot([L_span-bar_L, L_span+c_m/2], [top_y, top_y], color='#D32F2F', lw=2.5) # Right
    # Bot (Blue)
    ax.plot([0, L_span], [bot_y, bot_y], color='#1976D2', lw=2.5)
    
    # Transverse Dots (เหล็กอีกแกน วางขวาง)
    x_dots = np.arange(0.2, L_span, 0.3)
    ax.scatter(x_dots, [top_y - 0.02]*len(x_dots), c='#D32F2F', s=20, zorder=5)
    ax.scatter(x_dots, [bot_y + 0.02]*len(x_dots), c='#1976D2', s=20, zorder=5)

    # Labels
    add_dimension(ax, 0, -0.2, L_span, -0.2, f"Span L1 ({axis_dir}) = {L_span} m", offset=0.1)
    
    ax.text(bar_L/2, top_y+0.1, rebar_results.get('CS_Top','?'), color='#D32F2F', ha='center', fontsize=8, fontweight='bold')
    ax.text(L_span/2, bot_y-0.15, rebar_results.get('CS_Bot','?'), color='#1976D2', ha='center', fontsize=8, fontweight='bold')

    setup_cad_style(ax, f"SECTION VIEW ({axis_dir}-DIR)")
    ax.set_xlim(-0.8, L_span + 0.8)
    ax.set_ylim(-0.8, h_m + 0.8)
    plt.tight_layout()
    return fig

# ==========================================
# 3. PLAN VIEW (แก้ไขใหม่: หมุนตามแกนจริง!)
# ==========================================
def plot_rebar_plan_view(L_span, L_width, c_para, rebar_results, axis_dir):
    """
    วาดแปลนพื้น:
    - ถ้า axis_dir == 'X': วาดแนวนอน (Span อยู่แกน X)
    - ถ้า axis_dir == 'Y': วาดแนวตั้ง (Span อยู่แกน Y)
    """
    
    # กำหนดขนาด Canvas ตามทิศทาง
    if axis_dir == 'X':
        plot_w, plot_h = L_span, L_width
        fig_w, fig_h = 10, 6
    else: # Y-Direction -> สลับแกนกราฟเลย
        plot_w, plot_h = L_width, L_span
        fig_w, fig_h = 6, 8  # ปรับ Aspect ratio ให้เป็นแนวตั้ง

    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    
    w_cs = min(L_span, L_width) / 2.0
    w_cs_half = w_cs / 2.0
    
    # 1. วาดโซน Column Strip / Middle Strip
    if axis_dir == 'X':
        # CS อยู่บน/ล่าง (แนวนอน)
        ax.add_patch(patches.Rectangle((0, 0), plot_w, w_cs_half, fc='#FFEBEE', alpha=0.5)) # Bot
        ax.add_patch(patches.Rectangle((0, plot_h - w_cs_half), plot_w, w_cs_half, fc='#FFEBEE', alpha=0.5)) # Top
        ax.add_patch(patches.Rectangle((0, w_cs_half), plot_w, plot_h - 2*w_cs_half, fc='#E3F2FD', alpha=0.5)) # Mid
    else: # Y-Direction
        # CS อยู่ซ้าย/ขวา (แนวตั้ง)
        ax.add_patch(patches.Rectangle((0, 0), w_cs_half, plot_h, fc='#FFEBEE', alpha=0.5)) # Left
        ax.add_patch(patches.Rectangle((plot_w - w_cs_half, 0), w_cs_half, plot_h, fc='#FFEBEE', alpha=0.5)) # Right
        ax.add_patch(patches.Rectangle((w_cs_half, 0), plot_w - 2*w_cs_half, plot_h, fc='#E3F2FD', alpha=0.5)) # Mid

    # 2. วาดเสา (Columns)
    c_m = c_para / 100
    cols = []
    if axis_dir == 'X':
        cols = [(0,0), (0, plot_h), (plot_w, 0), (plot_w, plot_h)]
    else:
        cols = [(0,0), (plot_w, 0), (0, plot_h), (plot_w, plot_h)]
        
    for (cx, cy) in cols:
        ax.add_patch(patches.Rectangle((cx-c_m/2, cy-c_m/2), c_m, c_m, fc='#333', zorder=10))

    # 3. วาดเหล็กเสริม (Rebars) - หมุนตามแกน
    def draw_bar(zone_name, align_pos, is_top, color):
        txt = rebar_results.get(zone_name, '')
        bar_len = L_span * 0.3 # ระยะหยุดเหล็กบน
        
        if axis_dir == 'X':
            # --- เหล็กแนวนอน (วิ่งซ้าย-ขวา) ---
            y = align_pos
            if is_top:
                # ซ้าย
                ax.plot([-0.2, bar_len], [y, y], color=color, lw=2)
                ax.text(bar_len/2, y, txt, color=color, fontsize=8, ha='center', va='bottom', fontweight='bold', bbox=dict(fc='white', ec='none', alpha=0.7))
                # ขวา
                ax.plot([plot_w-bar_len, plot_w+0.2], [y, y], color=color, lw=2)
            else:
                # ล่าง (ยาวตลอด)
                ax.plot([0, plot_w], [y, y], color=color, lw=2)
                ax.text(plot_w/2, y, txt, color=color, fontsize=8, ha='center', va='bottom', fontweight='bold', bbox=dict(fc='white', ec='none', alpha=0.7))
        
        else: # Y-Direction
            # --- เหล็กแนวตั้ง (วิ่งล่าง-บน) ---
            x = align_pos
            if is_top:
                # ล่าง (Support)
                ax.plot([x, x], [-0.2, bar_len], color=color, lw=2)
                ax.text(x, bar_len/2, txt, color=color, fontsize=8, ha='left', va='center', fontweight='bold', rotation=90, bbox=dict(fc='white', ec='none', alpha=0.7))
                # บน (Support)
                ax.plot([x, x], [plot_h-bar_len, plot_h+0.2], color=color, lw=2)
            else:
                # กลาง (ยาวตลอด)
                ax.plot([x, x], [0, plot_h], color=color, lw=2)
                ax.text(x, plot_h/2, txt, color=color, fontsize=8, ha='left', va='center', fontweight='bold', rotation=90, bbox=dict(fc='white', ec='none', alpha=0.7))

    # เรียกฟังก์ชันวาดตามตำแหน่ง
    if axis_dir == 'X':
        # Y-Coordinates for bars
        y_cs_bot = w_cs_half * 0.3
        y_cs_top = plot_h - (w_cs_half * 0.3)
        y_ms_bot = plot_h/2 - 0.2
        y_ms_top = plot_h/2 + 0.2
        
        draw_bar('CS_Bot', y_cs_bot, False, '#1976D2') # CS Bot (ล่างสุด)
        draw_bar('CS_Top', w_cs_half * 0.7, True, '#D32F2F') # CS Top (ล่าง)
        draw_bar('CS_Top', plot_h - (w_cs_half * 0.7), True, '#D32F2F') # CS Top (บน)
        
        draw_bar('MS_Bot', y_ms_bot, False, '#1976D2')
        draw_bar('MS_Top', y_ms_top, True, '#D32F2F')

    else: # Y-Direction (ตำแหน่งเป็น X-Coord)
        x_cs_left = w_cs_half * 0.3
        x_cs_right = plot_w - (w_cs_half * 0.3)
        x_ms_left = plot_w/2 - 0.2
        x_ms_right = plot_w/2 + 0.2
        
        draw_bar('CS_Bot', x_cs_left, False, '#1976D2')
        draw_bar('CS_Top', w_cs_half * 0.7, True, '#D32F2F')
        draw_bar('CS_Top', plot_w - (w_cs_half * 0.7), True, '#D32F2F')
        
        draw_bar('MS_Bot', x_ms_left, False, '#1976D2')
        draw_bar('MS_Top', x_ms_right, True, '#D32F2F')

    # 4. Dimensions
    if axis_dir == 'X':
        add_dimension(ax, 0, -0.5, plot_w, -0.5, f"Span X = {plot_w} m")
        add_dimension(ax, plot_w+0.5, 0, plot_w+0.5, plot_h, f"Width Y = {plot_h} m", vertical=True)
    else:
        add_dimension(ax, 0, -0.5, plot_w, -0.5, f"Width X = {plot_w} m")
        add_dimension(ax, plot_w+0.5, 0, plot_w+0.5, plot_h, f"Span Y = {plot_h} m", vertical=True)

    setup_cad_style(ax, f"PLAN VIEW: REBAR LAYOUT ({axis_dir}-DIRECTION)")
    
    # Set Limits with padding
    ax.set_xlim(-1, plot_w + 1.5)
    ax.set_ylim(-1, plot_h + 1)
    
    plt.tight_layout()
    return fig
