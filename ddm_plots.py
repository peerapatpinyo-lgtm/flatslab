import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# ==========================================
# 🎨 HELPER: CAD STYLING
# ==========================================
def setup_cad_style(ax, title):
    """จัด Style ให้เหมือนแบบวิศวกรรม"""
    ax.set_title(title, loc='left', fontsize=10, fontweight='bold', pad=10, color='#333333')
    ax.axis('off')
    # กำหนด Aspect Ratio ให้สมจริง ไม่เบี้ยว
    ax.set_aspect('equal', adjustable='box')

def add_dim(ax, x1, y1, x2, y2, text, offset=0.5, color='black', is_vert=False):
    """วาดเส้นบอกระยะ Dimension Line"""
    # เส้นหลัก
    ax.annotate('', xy=(x1, y1), xytext=(x2, y2),
                arrowprops=dict(arrowstyle='<|-|>', color=color, lw=0.6))
    
    # ตำแหน่งข้อความ
    mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
    if is_vert:
        txt_x, txt_y = mid_x + offset, mid_y
        rot = 90
    else:
        txt_x, txt_y = mid_x, mid_y + offset
        rot = 0
        
    bbox = dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.8)
    ax.text(txt_x, txt_y, text, ha='center', va='center', 
            fontsize=7, color=color, bbox=bbox, fontweight='bold', rotation=rot)

# ==========================================
# 1. MOMENT DIAGRAM
# ==========================================
def plot_ddm_moment(L_span, c1, m_vals):
    # ปรับขนาดภาพให้กว้างพอ
    fig, ax = plt.subplots(figsize=(8, 3))
    
    x = np.linspace(0, L_span, 200)
    M_neg_cs, M_pos_cs = m_vals['M_cs_neg'], m_vals['M_cs_pos']
    M_neg_ms, M_pos_ms = m_vals['M_ms_neg'], m_vals['M_ms_pos']

    # Interpolate Moment Shape
    pts = [0, L_span*0.2, L_span*0.5, L_span*0.8, L_span]
    y_cs = np.interp(x, pts, [-M_neg_cs, 0, M_pos_cs, 0, -M_neg_cs])
    y_ms = np.interp(x, pts, [-M_neg_ms, 0, M_pos_ms, 0, -M_neg_ms])

    ax.plot(x, y_cs, label='Col Strip', color='#D32F2F', lw=1.5)
    ax.plot(x, y_ms, label='Mid Strip', color='#1976D2', lw=1.5, ls='--')
    
    # Fill & Line zero
    ax.fill_between(x, y_cs, 0, alpha=0.05, color='#D32F2F')
    ax.axhline(0, color='black', lw=0.5)
    
    # Text Annotation (ค่า Max)
    limit = max(abs(np.concatenate([y_cs, y_ms]))) * 1.4
    ax.set_ylim(limit, -limit) # Invert Y for Moment
    
    ax.text(0, -M_neg_cs, f"{M_neg_cs:.0f}", color='#D32F2F', fontsize=7, ha='left', va='top')
    ax.text(L_span/2, M_pos_cs, f"{M_pos_cs:.0f}", color='#D32F2F', fontsize=7, ha='center', va='bottom')

    ax.set_title(f"BENDING MOMENT DIAGRAM (L={L_span}m)", loc='left', fontsize=9, fontweight='bold')
    ax.legend(fontsize=7, loc='upper right')
    ax.grid(True, ls=':', alpha=0.3)
    
    plt.tight_layout()
    return fig

# ==========================================
# 2. SECTION VIEW (รูปตัด)
# ==========================================
def plot_rebar_detailing(L_span, h_slab, c_para, rebar_results, axis_dir):
    fig, ax = plt.subplots(figsize=(8, 3))
    
    h_m = h_slab / 100.0
    c_m = c_para / 100.0
    
    # 2.1 Concrete Body
    ax.add_patch(patches.Rectangle((0, 0), L_span, h_m, fc='#E0E0E0', ec='black', lw=0.5))
    
    # Columns (Support)
    for x_c in [-c_m/2, L_span-c_m/2]:
        ax.add_patch(patches.Rectangle((x_c, -0.4), c_m, 0.4, fc='white', ec='black', hatch='///'))
        ax.add_patch(patches.Rectangle((x_c, h_m), c_m, 0.4, fc='white', ec='black', hatch='///'))

    # 2.2 Rebar (Longitudinal) - เส้นยาว
    cover = 0.03
    y_top = h_m - cover
    y_bot = cover
    bar_len = L_span * 0.3
    
    # Top Bars (Red)
    ax.plot([-c_m/2, bar_len], [y_top, y_top], 'r-', lw=2)
    ax.plot([L_span-bar_len, L_span+c_m/2], [y_top, y_top], 'r-', lw=2)
    # Bot Bars (Blue)
    ax.plot([0, L_span], [y_bot, y_bot], 'b-', lw=2)
    
    # 2.3 Rebar (Transverse) - จุดเหล็กขวาง
    # ต้องมีเพื่อความสมจริงทางวิศวกรรม
    x_dots = np.arange(0.2, L_span, 0.25)
    y_dot_top = y_top - 0.02 # อยู่ใต้เหล็กบน
    y_dot_bot = y_bot + 0.02 # อยู่บนเหล็กล่าง
    
    ax.scatter(x_dots, [y_dot_top]*len(x_dots), c='r', s=15, zorder=5) # จุดแดง
    ax.scatter(x_dots, [y_dot_bot]*len(x_dots), c='b', s=15, zorder=5) # จุดน้ำเงิน

    # 2.4 Labels
    add_dim(ax, 0, -0.2, L_span, -0.2, f"Span L1 ({axis_dir}) = {L_span}m", offset=0.15)
    
    # Text Tags
    t_style = dict(boxstyle="round,pad=0.1", fc="white", ec="none", alpha=0.7)
    ax.text(bar_len/2, y_top+0.1, rebar_results.get('CS_Top',''), color='r', fontsize=7, ha='center', bbox=t_style)
    ax.text(L_span/2, y_bot-0.1, rebar_results.get('CS_Bot',''), color='b', fontsize=7, ha='center', bbox=t_style)

    setup_cad_style(ax, f"SECTION A-A ({axis_dir}-DIRECTION)")
    ax.set_xlim(-0.6, L_span + 0.6)
    ax.set_ylim(-0.6, h_m + 0.6)
    
    return fig

# ==========================================
# 3. PLAN VIEW (แปลนวางเหล็ก)
# ==========================================
def plot_rebar_plan_view(L_span, L_width, c_para, rebar_results, axis_dir):
    """
    Logic:
    - ถ้า Axis X: พื้นวางนอน (กว้าง L_span, สูง L_width) -> เหล็กวิ่งนอน
    - ถ้า Axis Y: พื้นวางตั้ง (กว้าง L_width, สูง L_span) -> เหล็กวิ่งตั้ง
    """
    
    # 3.1 Setup Canvas Dimension
    if axis_dir == 'X':
        plot_w, plot_h = L_span, L_width
        fig_size = (8, 5) # แนวนอน
    else:
        plot_w, plot_h = L_width, L_span
        fig_size = (5, 8) # แนวตั้ง

    fig, ax = plt.subplots(figsize=fig_size)
    
    # 3.2 Draw Zones (Stripes)
    # คำนวณความกว้างแถบ CS
    w_cs = min(L_span, L_width) / 2.0
    w_cs_half = w_cs / 2.0
    
    # วาดพื้นหลังแยกโซน
    if axis_dir == 'X':
        # CS อยู่บน/ล่าง
        ax.add_patch(patches.Rectangle((0, 0), plot_w, w_cs_half, fc='#FFE0E0', alpha=0.3)) # CS Bot
        ax.add_patch(patches.Rectangle((0, plot_h-w_cs_half), plot_w, w_cs_half, fc='#FFE0E0', alpha=0.3)) # CS Top
        ax.add_patch(patches.Rectangle((0, w_cs_half), plot_w, plot_h-2*w_cs_half, fc='#E0F0FF', alpha=0.3)) # MS
    else:
        # CS อยู่ซ้าย/ขวา
        ax.add_patch(patches.Rectangle((0, 0), w_cs_half, plot_h, fc='#FFE0E0', alpha=0.3)) # CS Left
        ax.add_patch(patches.Rectangle((plot_w-w_cs_half, 0), w_cs_half, plot_h, fc='#FFE0E0', alpha=0.3)) # CS Right
        ax.add_patch(patches.Rectangle((w_cs_half, 0), plot_w-2*w_cs_half, plot_h, fc='#E0F0FF', alpha=0.3)) # MS

    # 3.3 Draw Columns
    c_m = c_para / 100.0
    col_coords = [(0,0), (plot_w,0), (0,plot_h), (plot_w,plot_h)]
    for (cx, cy) in col_coords:
        rect = patches.Rectangle((cx-c_m/2, cy-c_m/2), c_m, c_m, fc='#444444', zorder=10)
        ax.add_patch(rect)

    # 3.4 Helper Function วาดเหล็ก
    def draw_bar_line(zone_key, pos_ratio, is_top, color):
        txt = rebar_results.get(zone_key, '')
        bar_len = L_span * 0.3 # ระยะหยุดเหล็กบน
        
        if axis_dir == 'X':
            # --- เหล็กแนวนอน ---
            y = w_cs_half * pos_ratio if zone_key.startswith('CS') else plot_h/2 + (0.3 if is_top else -0.3)
            # ปรับตำแหน่ง Y ให้ CS Top (โซนบน)
            if zone_key == 'CS_Top' and pos_ratio > 1: y = plot_h - (w_cs_half * 0.5) 
            if zone_key == 'CS_Top' and pos_ratio < 1: y = w_cs_half * 0.5 

            if is_top:
                # ซ้าย
                ax.plot([-0.2, bar_len], [y, y], color=color, lw=2)
                # ขวา
                ax.plot([plot_w-bar_len, plot_w+0.2], [y, y], color=color, lw=2)
                ax.text(bar_len/2, y, txt, color=color, fontsize=8, ha='center', va='bottom', fontweight='bold')
            else:
                # ยาวตลอด
                ax.plot([0, plot_w], [y, y], color=color, lw=2)
                ax.text(plot_w/2, y, txt, color=color, fontsize=8, ha='center', va='bottom', fontweight='bold')
                
        else: # Y-Direction
            # --- เหล็กแนวตั้ง ---
            # Mapping ตำแหน่ง X
            if zone_key.startswith('CS'):
                x = w_cs_half * 0.5 # Left CS
                if pos_ratio > 1: x = plot_w - (w_cs_half * 0.5) # Right CS
            else:
                x = plot_w/2 + (0.3 if is_top else -0.3)

            if is_top:
                # ล่าง
                ax.plot([x, x], [-0.2, bar_len], color=color, lw=2)
                # บน
                ax.plot([x, x], [plot_h-bar_len, plot_h+0.2], color=color, lw=2)
                ax.text(x, bar_len/2, txt, color=color, fontsize=8, ha='left', va='center', fontweight='bold', rotation=90)
            else:
                # ยาวตลอด
                ax.plot([x, x], [0, plot_h], color=color, lw=2)
                ax.text(x, plot_h/2, txt, color=color, fontsize=8, ha='left', va='center', fontweight='bold', rotation=90)

    # 3.5 Execute Drawing
    if axis_dir == 'X':
        # วาดเหล็ก X (แนวนอน)
        draw_bar_line('CS_Bot', 0.5, False, 'blue')
        draw_bar_line('CS_Top', 0.5, True, 'red') # ล่าง
        draw_bar_line('CS_Top', 1.5, True, 'red') # บน
        
        draw_bar_line('MS_Bot', 0, False, 'blue')
        draw_bar_line('MS_Top', 0, True, 'red')
        
        # Dimension
        add_dim(ax, 0, -0.8, plot_w, -0.8, f"Span L1 = {plot_w}m")
        add_dim(ax, plot_w+0.8, 0, plot_w+0.8, plot_h, f"Width L2 = {plot_h}m", is_vert=True)

    else:
        # วาดเหล็ก Y (แนวตั้ง)
        draw_bar_line('CS_Bot', 0.5, False, 'blue') # Left
        draw_bar_line('CS_Top', 0.5, True, 'red')  # Left
        draw_bar_line('CS_Top', 1.5, True, 'red')  # Right
        
        draw_bar_line('MS_Bot', 0, False, 'blue')
        draw_bar_line('MS_Top', 0, True, 'red')

        # Dimension
        add_dim(ax, 0, -0.8, plot_w, -0.8, f"Width L2 = {plot_w}m")
        add_dim(ax, plot_w+0.8, 0, plot_w+0.8, plot_h, f"Span L1 = {plot_h}m", is_vert=True)

    setup_cad_style(ax, f"PLAN LAYOUT ({axis_dir}-DIRECTION REBARS)")
    ax.set_xlim(-1, plot_w + 1.5)
    ax.set_ylim(-1, plot_h + 1)

    return fig
