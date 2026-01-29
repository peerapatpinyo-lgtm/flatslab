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
    # ax.grid(True, which='both', linestyle='--', linewidth=0.5, color='gray', alpha=0.2) # Optional Grid

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
    ax.grid(True, linestyle=':', alpha=0.5)
    
    limit = max(M_pos_cs, M_neg_cs, M_pos_ms, M_neg_ms) * 1.3
    ax.set_ylim(limit, -limit) 
    
    bbox = dict(boxstyle="round,pad=0.2", fc="white", ec="#D32F2F", alpha=0.9, lw=0.5)
    ax.text(0, -M_neg_cs, f"M-: {M_neg_cs:,.0f}", color='#D32F2F', ha='left', va='top', fontsize=8, bbox=bbox)
    ax.text(L_span/2, M_pos_cs, f"M+: {M_pos_cs:,.0f}", color='#D32F2F', ha='center', va='bottom', fontsize=8, bbox=bbox)
    
    ax.set_title(f"MOMENT DISTRIBUTION DIAGRAM (Span {L_span} m)", loc='left', fontweight='bold', fontsize=10)
    ax.legend(fontsize=8, loc='upper right')
    
    plt.tight_layout()
    return fig

# ==========================================
# 2. SECTION PROFILE (เพิ่มเหล็กจุด Transverse)
# ==========================================
def plot_rebar_detailing(L_span, h_slab, c_para, rebar_results, axis_dir):
    fig, ax = plt.subplots(figsize=(10, 4))
    h_m = h_slab / 100
    c_m = c_para / 100
    
    # Concrete Structure
    slab = patches.Rectangle((0, 0), L_span, h_m, fc='#E0E0E0', ec='black', lw=0.5)
    ax.add_patch(slab)
    
    col_h = 0.6
    for x_pos in [-c_m/2, L_span-c_m/2]:
        ax.add_patch(patches.Rectangle((x_pos, -col_h), c_m, col_h, fc='white', ec='black', hatch='//', lw=0.5))
        ax.add_patch(patches.Rectangle((x_pos, h_m), c_m, col_h, fc='white', ec='black', hatch='//', lw=0.5))
    
    # --- Main Rebar (Lines) ---
    cover = 0.03
    bar_offset_layer = 0.02 # สมมติระยะห่างระหว่างชั้นเหล็ก
    
    # สมมติว่าทิศที่ออกแบบอยู่ชั้นนอก (Outer Layer)
    top_y_main = h_m - cover
    bot_y_main = cover
    
    bar_len = L_span * 0.30
    
    # Top Main (Red)
    ax.plot([-c_m/2, bar_len], [top_y_main, top_y_main], color='#D32F2F', lw=2.5, zorder=10)
    ax.plot([bar_len, bar_len], [top_y_main, top_y_main-0.08], color='#D32F2F', lw=1.5, zorder=10)
    ax.plot([L_span-bar_len, L_span+c_m/2], [top_y_main, top_y_main], color='#D32F2F', lw=2.5, zorder=10)
    ax.plot([L_span-bar_len, L_span-bar_len], [top_y_main, top_y_main-0.08], color='#D32F2F', lw=1.5, zorder=10)
    
    # Bottom Main (Blue)
    ax.plot([0, L_span], [bot_y_main, bot_y_main], color='#1976D2', lw=2.5, zorder=10)
    
    # --- Transverse Rebar (Dots) - เหล็กทิศรอง ---
    # แสดงเป็นจุด เพื่อบอกว่ามีเหล็กอีกทิศวิ่งตัด
    top_y_trans = top_y_main - bar_offset_layer
    bot_y_trans = bot_y_main + bar_offset_layer
    
    # สร้างจุดสมมติระยะแอดประมาณ 30cm เพื่อ visual
    x_dots = np.arange(0.15, L_span, 0.30) 
    
    # Top Dots (Red fill)
    ax.scatter(x_dots, [top_y_trans]*len(x_dots), s=30, facecolors='#D32F2F', edgecolors='none', zorder=5, label='Transverse Bars')
    # Bot Dots (Blue fill)
    ax.scatter(x_dots, [bot_y_trans]*len(x_dots), s=30, facecolors='#1976D2', edgecolors='none', zorder=5)

    # Dimensions & Annotations
    add_dimension(ax, 0, -0.3, L_span, -0.3, f"Span L1 = {L_span} m", offset=0.1)
    add_dimension(ax, 0, h_m+0.2, bar_len, h_m+0.2, f"0.3L1", offset=0.05, color='#D32F2F', arrow_color='#D32F2F')
    
    ax.annotate(rebar_results.get('CS_Top','?'), xy=(bar_len/2, top_y_main), xytext=(bar_len/2, top_y_main+0.5),
                arrowprops=dict(arrowstyle='->', color='#D32F2F'), color='#D32F2F', fontweight='bold', ha='center', bbox=dict(fc='white', ec='none', alpha=0.7))
    
    ax.annotate(rebar_results.get('CS_Bot','?'), xy=(L_span/2, bot_y_main), xytext=(L_span/2, -0.6),
                arrowprops=dict(arrowstyle='->', color='#1976D2'), color='#1976D2', fontweight='bold', ha='center', bbox=dict(fc='white', ec='none', alpha=0.7))

    setup_cad_style(ax, f"SECTION VIEW ({axis_dir}-DIR CUT): MAIN REBAR PROFILE")
    ax.set_xlim(-0.8, L_span + 1.2)
    ax.set_ylim(-0.8, h_m + 0.8)
    plt.tight_layout()
    return fig

# ==========================================
# 3. PLAN VIEW (วาดถูกทิศทาง X/Y)
# ==========================================
def plot_rebar_plan_view(L_span, L_width, c_para, rebar_results, axis_dir):
    fig, ax = plt.subplots(figsize=(10, 6))
    w_cs = min(L_span, L_width) / 2.0
    w_cs_half = w_cs / 2.0
    
    # Background Strips (Zones based on Width L2)
    rect_ms = patches.Rectangle((0, w_cs_half), L_span, L_width - w_cs, fc='#E3F2FD', alpha=0.5)
    ax.add_patch(rect_ms)
    rect_cs_bot = patches.Rectangle((0, 0), L_span, w_cs_half, fc='#FFEBEE', alpha=0.5)
    rect_cs_top = patches.Rectangle((0, L_width - w_cs_half), L_span, w_cs_half, fc='#FFEBEE', alpha=0.5)
    ax.add_patch(rect_cs_bot)
    ax.add_patch(rect_cs_top)
    
    # Columns
    c_m = c_para / 100
    for cx in [0, L_span]:
        for cy in [0, L_width]:
            ax.add_patch(patches.Rectangle((cx-c_m/2, cy-c_m/2), c_m, c_m, fc='#333', zorder=10))

    # --- Rebar Drawing Logic (Direction Aware) ---
    bar_len_ratio = 0.3
    bar_len = L_span * bar_len_ratio

    def draw_bars_directional(orth_pos_y, txt, color, is_top=True, label_offset_x=0):
        """
        orth_pos_y: ตำแหน่งในแกนตั้งฉาก (แกน Y ในรูป)
        """
        bbox_lbl = dict(boxstyle="round,pad=0.1", fc="white", ec=color, alpha=0.8, lw=0.5)
        
        if axis_dir == 'X':
            # --- CASE X: เหล็กวิ่งแนวนอน (ขนาน L_span) ---
            y = orth_pos_y
            if is_top:
                # เหล็กบนช่วงหัวเสา (ซ้าย-ขวา)
                ax.plot([-0.2, bar_len], [y, y], color=color, lw=2)
                ax.plot([L_span-bar_len, L_span+0.2], [y, y], color=color, lw=2)
                ax.text(bar_len/2 + label_offset_x, y, txt, color=color, fontsize=7, ha='center', va='bottom', fontweight='bold', bbox=bbox_lbl)
            else:
                # เหล็กล่างวิ่งยาวตลอด
                ax.plot([0, L_span], [y, y], color=color, lw=2)
                ax.text(L_span/2 + label_offset_x, y, txt, color=color, fontsize=7, ha='center', va='bottom', fontweight='bold', bbox=bbox_lbl)
        
        else: # axis_dir == 'Y'
            # --- CASE Y: เหล็กวิ่งแนวตั้ง (ตั้งฉาก L_span) ---
            # เราต้องวาดเส้นตั้งหลายๆ เส้นเพื่อแสดงแนวเหล็ก
            
            # กำหนดขอบเขต Y ของเส้นตั้ง
            # ถ้าอยู่ Col Strip (บน/ล่าง)
            if orth_pos_y < w_cs_half: y_start, y_end = 0, w_cs_half
            elif orth_pos_y > L_width - w_cs_half: y_start, y_end = L_width - w_cs_half, L_width
            # ถ้าอยู่ Middle Strip
            else: y_start, y_end = w_cs_half, L_width - w_cs_half
                
            if is_top:
                # เหล็กบน (แนวตั้ง) อยู่ช่วงหัวเสา (ซ้าย-ขวา ของรูป)
                # วาดตัวแทนสัก 2-3 เส้น
                for x_pos in np.linspace(0, bar_len, 3):
                     ax.plot([x_pos, x_pos], [y_start, y_end], color=color, lw=1.5)
                for x_pos in np.linspace(L_span-bar_len, L_span, 3):
                     ax.plot([x_pos, x_pos], [y_start, y_end], color=color, lw=1.5)
                
                # Label (หมุน 90 องศา)
                ax.text(bar_len/2, orth_pos_y, txt, color=color, fontsize=7, ha='center', va='center', fontweight='bold', rotation=90, bbox=bbox_lbl)
            
            else:
                # เหล็กล่าง (แนวตั้ง) วิ่งเต็มสแปน
                # วาดตัวแทนกระจายๆ
                for x_pos in np.linspace(0.2, L_span-0.2, 6):
                    ax.plot([x_pos, x_pos], [y_start, y_end], color=color, lw=1.5)
                
                # Label (หมุน 90 องศา)
                ax.text(L_span/2, orth_pos_y, txt, color=color, fontsize=7, ha='center', va='center', fontweight='bold', rotation=90, bbox=bbox_lbl)

    # Draw Rebars using the new directional function
    # CS Bot & Top (Bottom Zone)
    draw_bars_directional(w_cs_half*0.3, rebar_results.get('CS_Bot',''), '#1976D2', False)
    draw_bars_directional(w_cs_half*0.7, rebar_results.get('CS_Top',''), '#D32F2F', True)
    
    # CS Top (Top Zone)
    draw_bars_directional(L_width - w_cs_half*0.7, rebar_results.get('CS_Top',''), '#D32F2F', True)

    # MS Bot & Top (Middle Zone)
    draw_bars_directional(L_width/2 - 0.3, rebar_results.get('MS_Bot',''), '#1976D2', False)
    draw_bars_directional(L_width/2 + 0.3, rebar_results.get('MS_Top',''), '#D32F2F', True)

    # Dimensions (Widths L2)
    x_dim = L_span + 0.8
    add_dimension(ax, x_dim, 0, x_dim, w_cs_half, f"CS\n{w_cs_half:.2f}", offset=0, color='gray', arrow_color='gray')
    add_dimension(ax, x_dim, w_cs_half, x_dim, L_width-w_cs_half, f"MS\n{L_width-w_cs:.2f}", offset=0, color='gray', arrow_color='gray')
    add_dimension(ax, x_dim, L_width-w_cs_half, x_dim, L_width, f"CS", offset=0, color='gray', arrow_color='gray')
    
    # Dimension Span L1
    add_dimension(ax, 0, -0.5, L_span, -0.5, f"Span L1 = {L_span:.2f} m", offset=0.2)

    setup_cad_style(ax, f"PLAN VIEW: {axis_dir}-DIRECTION MAIN REBAR LAYOUT")
    ax.set_xlim(-1, L_span + 1.5)
    ax.set_ylim(-1, L_width + 0.5)
    plt.tight_layout()
    return fig
