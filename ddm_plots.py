import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# ==========================================
# 🎨 GLOBAL STYLING & COLORS (Professional Palette)
# ==========================================
# โทนสีวิศวกรรมที่ดูทันสมัย สบายตา
CLR_CONCRETE = '#F0F2F5'  # สีคอนกรีตเทาอ่อน
CLR_COL_HATCH = '#E0E0E0' # สีแรเงาเสา
CLR_DIM = '#666666'       # สีเส้นบอกระยะ (เทาเข้ม ไม่ดำสนิท)

# สีเหล็กเสริม (ใช้โทนที่เข้มและชัดเจน)
CLR_BAR_TOP = '#C0392B'   # สีแดงเข้ม (Negative Moment)
CLR_BAR_BOT = '#2980B9'   # สีน้ำเงินเข้ม (Positive Moment)

# สีพื้นหลังโซนใน Plan View (พาสเทลอ่อนๆ)
CLR_ZONE_CS = '#FDEDEC'   # แดงอ่อนมาก
CLR_ZONE_MS = '#EBF5FB'   # ฟ้าอ่อนมาก

def setup_cad_style(ax, title):
    """จัด Style ให้เหมือนแบบวิศวกรรม"""
    ax.set_title(title, loc='left', fontsize=11, fontweight='bold', pad=12, color='#2C3E50')
    ax.axis('off')
    # ทำให้พื้นหลัง plot โปร่งใสเล็กน้อยเพื่อให้เข้ากับเว็บ
    ax.figure.patch.set_alpha(0.0)
    ax.patch.set_alpha(0.0)

def add_dim(ax, x1, y1, x2, y2, text, offset=0.5, is_vert=False):
    """วาดเส้นบอกระยะ Dimension Line (เส้นบาง สีสุภาพ)"""
    # เส้นหลัก (บางลง)
    ax.annotate('', xy=(x1, y1), xytext=(x2, y2),
                arrowprops=dict(arrowstyle='<|-|>', color=CLR_DIM, lw=0.5))
    
    # ตำแหน่งข้อความ
    mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
    if is_vert:
        txt_x, txt_y = mid_x + offset, mid_y
        rot = 90
    else:
        txt_x, txt_y = mid_x, mid_y + offset
        rot = 0
        
    bbox = dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.85)
    ax.text(txt_x, txt_y, text, ha='center', va='center', 
            fontsize=8, color=CLR_DIM, bbox=bbox, fontweight='600', rotation=rot)

# ==========================================
# 1. MOMENT DIAGRAM (ปรับสีและ Fill)
# ==========================================
def plot_ddm_moment(L_span, c1, m_vals):
    fig, ax = plt.subplots(figsize=(9, 3.5)) # ปรับขนาดตั้งต้น
    
    x = np.linspace(0, L_span, 200)
    M_neg_cs, M_pos_cs = m_vals['M_cs_neg'], m_vals['M_cs_pos']
    M_neg_ms, M_pos_ms = m_vals['M_ms_neg'], m_vals['M_ms_pos']

    pts = [0, L_span*0.2, L_span*0.5, L_span*0.8, L_span]
    y_cs = np.interp(x, pts, [-M_neg_cs, 0, M_pos_cs, 0, -M_neg_cs])
    y_ms = np.interp(x, pts, [-M_neg_ms, 0, M_pos_ms, 0, -M_neg_ms])

    # Plot Lines (หนาขึ้นเล็กน้อย)
    ax.plot(x, y_cs, label='Column Strip', color=CLR_BAR_TOP, lw=2)
    ax.plot(x, y_ms, label='Middle Strip', color=CLR_BAR_BOT, lw=2, ls='--')
    
    # Fill Area (สีนุ่มนวล)
    ax.fill_between(x, y_cs, 0, alpha=0.1, color=CLR_BAR_TOP)
    ax.axhline(0, color=CLR_DIM, lw=0.8)
    
    # Limits & Text
    limit = max(abs(np.concatenate([y_cs, y_ms]))) * 1.35
    ax.set_ylim(limit, -limit) 
    
    bbox_val = dict(boxstyle="round,pad=0.15", fc=CLR_BAR_TOP, ec="none", alpha=0.1)
    ax.text(0, -M_neg_cs*1.05, f" {M_neg_cs:,.0f} ", color=CLR_BAR_TOP, fontsize=8, ha='left', va='bottom', fontweight='bold', bbox=bbox_val)
    ax.text(L_span/2, M_pos_cs*1.05, f" {M_pos_cs:,.0f} ", color=CLR_BAR_TOP, fontsize=8, ha='center', va='top', fontweight='bold', bbox=bbox_val)

    setup_cad_style(ax, f"BENDING MOMENT DIAGRAM (Span L = {L_span:.2f} m)")
    ax.legend(fontsize=8, loc='upper right', frameon=True, framealpha=0.9)
    ax.grid(True, ls=':', color=CLR_DIM, alpha=0.3)
    
    plt.tight_layout()
    return fig

# ==========================================
# 2. SECTION VIEW (ปรับสัดส่วน + สัญลักษณ์)
# ==========================================
def plot_rebar_detailing(L_span, h_slab, c_para, rebar_results, axis_dir):
    h_m = h_slab / 100.0
    c_m = c_para / 100.0
    
    # --- Dynamic Aspect Ratio ---
    # คำนวณสัดส่วนจริง กว้าง/สูง
    actual_ratio = L_span / (h_m + 1.2) # +1.2 เผื่อที่ว่างบนล่างสำหรับ dimension
    # กำหนดความกว้างฐาน 10 นิ้ว ความสูงปรับตาม ratio แต่ไม่เกิน 5 นิ้ว
    fig_w = 10
    fig_h = min(fig_w / actual_ratio, 5.0) 
    fig_h = max(fig_h, 3.5) # สูงขั้นต่ำ

    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    
    # 2.1 Concrete Body
    ax.add_patch(patches.Rectangle((0, 0), L_span, h_m, fc=CLR_CONCRETE, ec=CLR_DIM, lw=0.8))
    
    # Columns (Hatch สีเทาอ่อน)
    col_h = 0.5 # ความสูงเสาในรูป
    for x_c in [-c_m/2, L_span-c_m/2]:
        ax.add_patch(patches.Rectangle((x_c, -col_h), c_m, col_h, fc='white', ec=CLR_DIM, hatch='////', lw=0.5, edgecolor=CLR_COL_HATCH))
        ax.add_patch(patches.Rectangle((x_c, h_m), c_m, col_h, fc='white', ec=CLR_DIM, hatch='////', lw=0.5, edgecolor=CLR_COL_HATCH))

    # 2.2 Main Rebar (เส้นหนา สีชัด)
    cover = 0.03
    y_top = h_m - cover
    y_bot = cover
    bar_len = L_span * 0.3
    
    # Top Bars
    ax.plot([-c_m/2, bar_len], [y_top, y_top], color=CLR_BAR_TOP, lw=3.5, solid_capstyle='round')
    ax.plot([L_span-bar_len, L_span+c_m/2], [y_top, y_top], color=CLR_BAR_TOP, lw=3.5, solid_capstyle='round')
    # Bot Bars
    ax.plot([0, L_span], [y_bot, y_bot], color=CLR_BAR_BOT, lw=3.5, solid_capstyle='round')
    
    # 2.3 Transverse Dots (ขนาดพอดีๆ)
    x_dots = np.arange(0.25, L_span, 0.3)
    y_dot_top = y_top - 0.025
    y_dot_bot = y_bot + 0.025
    
    ax.scatter(x_dots, [y_dot_top]*len(x_dots), c=CLR_BAR_TOP, s=40, zorder=5, edgecolors='none')
    ax.scatter(x_dots, [y_dot_bot]*len(x_dots), c=CLR_BAR_BOT, s=40, zorder=5, edgecolors='none')

    # 2.4 Labels & Dimensions
    add_dim(ax, 0, -0.3, L_span, -0.3, f"Span L1 ({axis_dir}) = {L_span:.2f} m", offset=0.15)
    add_dim(ax, L_span+0.3, 0, L_span+0.3, h_m, f"h = {h_slab:.0f} cm", offset=0.15, is_vert=True)

    # Rebar Callouts
    t_style_top = dict(boxstyle="round,pad=0.2", fc=CLR_BAR_TOP, ec="none", alpha=0.1)
    t_style_bot = dict(boxstyle="round,pad=0.2", fc=CLR_BAR_BOT, ec="none", alpha=0.1)

    ax.text(bar_len/2, y_top+0.25, rebar_results.get('CS_Top',''), color=CLR_BAR_TOP, fontsize=9, ha='center', fontweight='bold', bbox=t_style_top)
    ax.text(L_span/2, y_bot-0.25, rebar_results.get('CS_Bot',''), color=CLR_BAR_BOT, fontsize=9, ha='center', fontweight='bold', bbox=t_style_bot)

    setup_cad_style(ax, f"SECTION A-A ({axis_dir}-DIRECTION PROFILE)")
    
    # Set limits based on content plus padding
    ax.set_xlim(-0.8, L_span + 0.8)
    ax.set_ylim(-col_h - 0.2, h_m + col_h + 0.2)
    
    return fig

# ==========================================
# 3. PLAN VIEW (ปรับสัดส่วน + สีโซน)
# ==========================================
def plot_rebar_plan_view(L_span, L_width, c_para, rebar_results, axis_dir):
    # 3.1 Setup Dynamic Canvas
    if axis_dir == 'X':
        plot_w, plot_h = L_span, L_width
        base_w = 10
        aspect = plot_h / plot_w
    else:
        plot_w, plot_h = L_width, L_span
        base_w = 7 # แนวตั้งให้ฐานแคบลงหน่อย
        aspect = plot_h / plot_w

    fig_w = base_w
    fig_h = fig_w * aspect
    # จำกัดความสูงไม่ให้ยาวเกินไปจนดูยาก
    if fig_h > 10: 
        fig_h = 10
        fig_w = fig_h / aspect # ปรับความกว้างตาม

    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    
    w_cs = min(L_span, L_width) / 2.0
    w_cs_half = w_cs / 2.0
    
    # 3.2 Draw Zones (ใช้สีพาสเทลใหม่)
    if axis_dir == 'X':
        ax.add_patch(patches.Rectangle((0, 0), plot_w, w_cs_half, fc=CLR_ZONE_CS))
        ax.add_patch(patches.Rectangle((0, plot_h-w_cs_half), plot_w, w_cs_half, fc=CLR_ZONE_CS))
        ax.add_patch(patches.Rectangle((0, w_cs_half), plot_w, plot_h-2*w_cs_half, fc=CLR_ZONE_MS))
    else:
        ax.add_patch(patches.Rectangle((0, 0), w_cs_half, plot_h, fc=CLR_ZONE_CS))
        ax.add_patch(patches.Rectangle((plot_w-w_cs_half, 0), w_cs_half, plot_h, fc=CLR_ZONE_CS))
        ax.add_patch(patches.Rectangle((w_cs_half, 0), plot_w-2*w_cs_half, plot_h, fc=CLR_ZONE_MS))

    # 3.3 Draw Columns (เข้มขึ้น)
    c_m = c_para / 100.0
    col_coords = [(0,0), (plot_w,0), (0,plot_h), (plot_w,plot_h)]
    for (cx, cy) in col_coords:
        rect = patches.Rectangle((cx-c_m/2, cy-c_m/2), c_m, c_m, fc='#34495E', zorder=10)
        ax.add_patch(rect)
    
    # Draw Border
    ax.add_patch(patches.Rectangle((0,0), plot_w, plot_h, fill=False, ec=CLR_DIM, lw=1))

    # 3.4 Helper Function วาดเหล็ก (ปรับ Font และ Bbox)
    def draw_bar_line(zone_key, pos_ratio, is_top, color):
        txt = rebar_results.get(zone_key, '')
        bar_len = L_span * 0.3
        lw_bar = 2.5
        
        bbox_lbl = dict(boxstyle="round,pad=0.15", fc="white", ec=color, alpha=0.9, lw=0.5)
        font_s = 8

        if axis_dir == 'X':
            y = w_cs_half * pos_ratio if zone_key.startswith('CS') else plot_h/2 + (0.3 if is_top else -0.3)
            if zone_key == 'CS_Top' and pos_ratio > 1: y = plot_h - (w_cs_half * 0.5) 
            if zone_key == 'CS_Top' and pos_ratio < 1: y = w_cs_half * 0.5 

            if is_top:
                ax.plot([-0.2, bar_len], [y, y], color=color, lw=lw_bar)
                ax.plot([plot_w-bar_len, plot_w+0.2], [y, y], color=color, lw=lw_bar)
                ax.text(bar_len/2, y, txt, color=color, fontsize=font_s, ha='center', va='bottom', fontweight='bold', bbox=bbox_lbl)
            else:
                ax.plot([0, plot_w], [y, y], color=color, lw=lw_bar)
                ax.text(plot_w/2, y, txt, color=color, fontsize=font_s, ha='center', va='bottom', fontweight='bold', bbox=bbox_lbl)
                
        else: # Y-Direction
            if zone_key.startswith('CS'):
                x = w_cs_half * 0.5
                if pos_ratio > 1: x = plot_w - (w_cs_half * 0.5)
            else:
                x = plot_w/2 + (0.3 if is_top else -0.3)

            if is_top:
                ax.plot([x, x], [-0.2, bar_len], color=color, lw=lw_bar)
                ax.plot([x, x], [plot_h-bar_len, plot_h+0.2], color=color, lw=lw_bar)
                ax.text(x, bar_len/2, txt, color=color, fontsize=font_s, ha='left', va='center', fontweight='bold', rotation=90, bbox=bbox_lbl)
            else:
                ax.plot([x, x], [0, plot_h], color=color, lw=lw_bar)
                ax.text(x, plot_h/2, txt, color=color, fontsize=font_s, ha='left', va='center', fontweight='bold', rotation=90, bbox=bbox_lbl)

    # 3.5 Execute Drawing
    if axis_dir == 'X':
        draw_bar_line('CS_Bot', 0.5, False, CLR_BAR_BOT)
        draw_bar_line('CS_Top', 0.5, True, CLR_BAR_TOP)
        draw_bar_line('CS_Top', 1.5, True, CLR_BAR_TOP)
        draw_bar_line('MS_Bot', 0, False, CLR_BAR_BOT)
        draw_bar_line('MS_Top', 0, True, CLR_BAR_TOP)
        
        add_dim(ax, 0, -0.6, plot_w, -0.6, f"Span L1 = {plot_w:.2f}m")
        add_dim(ax, plot_w+0.6, 0, plot_w+0.6, plot_h, f"Width L2 = {plot_h:.2f}m", is_vert=True)

    else:
        draw_bar_line('CS_Bot', 0.5, False, CLR_BAR_BOT)
        draw_bar_line('CS_Top', 0.5, True, CLR_BAR_TOP)
        draw_bar_line('CS_Top', 1.5, True, CLR_BAR_TOP)
        draw_bar_line('MS_Bot', 0, False, CLR_BAR_BOT)
        draw_bar_line('MS_Top', 0, True, CLR_BAR_TOP)

        add_dim(ax, 0, -0.6, plot_w, -0.6, f"Width L2 = {plot_w:.2f}m")
        add_dim(ax, plot_w+0.6, 0, plot_w+0.6, plot_h, f"Span L1 = {plot_h:.2f}m", is_vert=True)

    setup_cad_style(ax, f"PLAN LAYOUT ({axis_dir}-DIRECTION)")
    
    # Set Limits with padding proportional to size
    pad_x = plot_w * 0.15
    pad_y = plot_h * 0.15
    ax.set_xlim(-pad_x, plot_w + pad_x)
    ax.set_ylim(-pad_y, plot_h + pad_y)

    return fig
