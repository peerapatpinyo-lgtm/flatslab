import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# ==========================================
# 🎨 HELPER FUNCTIONS (CAD STYLE)
# ==========================================
def add_dimension(ax, x1, y1, x2, y2, text, offset=0.5, color='black'):
    """
    ฟังก์ชันวาดเส้นบอกระยะ (Dimension Line) สไตล์ CAD
    """
    # เส้นหลัก
    ax.annotate('', xy=(x1, y1), xytext=(x2, y2),
                arrowprops=dict(arrowstyle='<->', color=color, lw=0.8))
    
    # เส้น Center (คำนวณตำแหน่งตัวหนังสือ)
    mid_x = (x1 + x2) / 2
    mid_y = (y1 + y2) / 2
    
    # วาด Background ให้ตัวหนังสือ (จะได้ไม่จม)
    bbox = dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.7)
    
    ax.text(mid_x, mid_y + offset, text, ha='center', va='center', 
            fontsize=8, color=color, bbox=bbox, fontweight='bold')

def setup_cad_style(ax, title):
    """ตั้งค่าแกนให้ดูเหมือนกระดาษเขียนแบบ"""
    ax.set_title(title, loc='left', fontsize=11, fontweight='bold', pad=15)
    ax.axis('off')
    # วาดกรอบรูป (Border)
    # ax.figure.patch.set_linewidth(1)
    # ax.figure.patch.set_edgecolor('black')

# ==========================================
# 1. MOMENT DIAGRAM
# ==========================================
def plot_ddm_moment(L_span, c1, m_vals):
    """
    Moment Envelope Diagram (Refined)
    """
    fig, ax = plt.subplots(figsize=(10, 3.5))
    
    x = np.linspace(0, L_span, 200) # เพิ่มความละเอียด
    
    M_neg_cs, M_pos_cs = m_vals['M_cs_neg'], m_vals['M_cs_pos']
    M_neg_ms, M_pos_ms = m_vals['M_ms_neg'], m_vals['M_ms_pos']

    # Interpolation Points (Smoother curve)
    # จุดดัดกลับ (Inflection points) ประมาณ 0.2L
    pts = [0, L_span*0.2, L_span*0.5, L_span*0.8, L_span]
    
    y_cs = np.interp(x, pts, [-M_neg_cs, 0, M_pos_cs, 0, -M_neg_cs])
    y_ms = np.interp(x, pts, [-M_neg_ms, 0, M_pos_ms, 0, -M_neg_ms])

    # Plotting
    ax.plot(x, y_cs, label='Column Strip', color='#D32F2F', linewidth=1.5)
    ax.plot(x, y_ms, label='Middle Strip', color='#1976D2', linewidth=1.5, linestyle='--')
    
    # Areas
    ax.fill_between(x, y_cs, 0, alpha=0.05, color='#D32F2F')
    ax.axhline(0, color='black', linewidth=0.8)
    
    # Limit & Style
    limit = max(M_pos_cs, M_neg_cs, M_pos_ms, M_neg_ms) * 1.3
    ax.set_ylim(limit, -limit) # Invert Y for Engineering Style (Optional)
    
    # Annotations
    bbox = dict(boxstyle="round,pad=0.3", fc="white", ec="#D32F2F", alpha=0.9, linewidth=0.5)
    ax.text(0, -M_neg_cs, f"M-: {M_neg_cs:,.0f}", color='#D32F2F', ha='left', va='top', fontsize=8, bbox=bbox)
    ax.text(L_span/2, M_pos_cs, f"M+: {M_pos_cs:,.0f}", color='#D32F2F', ha='center', va='bottom', fontsize=8, bbox=bbox)
    
    ax.set_title(f"MOMENT DIAGRAM (Span {L_span} m)", loc='left', fontweight='bold', fontsize=10)
    ax.set_xlabel("Distance (m)", fontsize=8)
    ax.grid(True, linestyle=':', alpha=0.5)
    ax.legend(fontsize=8, loc='upper right')
    
    plt.tight_layout()
    return fig

# ==========================================
# 2. SECTION PROFILE (IMPROVED)
# ==========================================
def plot_rebar_detailing(L_span, h_slab, c_para, rebar_results):
    fig, ax = plt.subplots(figsize=(10, 4))
    
    h_m = h_slab / 100
    c_m = c_para / 100
    
    # 1. Structure
    slab = patches.Rectangle((0, 0), L_span, h_m, fc='#E0E0E0', ec='black', lw=0.5) # Concrete Color
    ax.add_patch(slab)
    
    col_h = 0.6
    # Columns with Hatch
    for x_pos in [-c_m/2, L_span-c_m/2]:
        rect_bot = patches.Rectangle((x_pos, -col_h), c_m, col_h, fc='white', ec='black', hatch='//', lw=0.5)
        rect_top = patches.Rectangle((x_pos, h_m), c_m, col_h, fc='white', ec='black', hatch='//', lw=0.5)
        ax.add_patch(rect_bot)
        ax.add_patch(rect_top)
    
    # 2. Rebar
    cover = 0.03
    bar_len = L_span * 0.30 # ACI standard approx 0.3Ln
    
    # Top Bars (Red)
    top_y = h_m - cover
    ax.plot([-c_m/2, bar_len], [top_y, top_y], color='#D32F2F', linewidth=2.5, solid_capstyle='round')
    ax.plot([bar_len, bar_len], [top_y, top_y-0.05], color='#D32F2F', linewidth=1.5) # Hook/End
    
    ax.plot([L_span-bar_len, L_span+c_m/2], [top_y, top_y], color='#D32F2F', linewidth=2.5, solid_capstyle='round')
    ax.plot([L_span-bar_len, L_span-bar_len], [top_y, top_y-0.05], color='#D32F2F', linewidth=1.5)
    
    # Bottom Bars (Blue)
    bot_y = cover
    ax.plot([0, L_span], [bot_y, bot_y], color='#1976D2', linewidth=2.5, solid_capstyle='round')
    
    # 3. Dimensions (Smart Dimensions) ✨
    # Span Dim
    add_dimension(ax, 0, -0.4, L_span, -0.4, f"Span = {L_span} m", offset=0.1)
    # Slab Thickness Dim
    add_dimension(ax, L_span + 0.5, 0, L_span + 0.5, h_m, f"h={h_slab}cm", offset=0.0, color='black')
    # Top Bar Length Dim
    add_dimension(ax, 0, h_m + 0.3, bar_len, h_m + 0.3, f"0.3L = {bar_len:.2f}m", offset=0.05, color='#D32F2F')

    # 4. Labels (Callouts)
    # CS Top
    ax.annotate(rebar_results.get('CS_Top','?'), xy=(bar_len/2, top_y), xytext=(bar_len/2, top_y+0.6),
                arrowprops=dict(arrowstyle='->', color='#D32F2F'), color='#D32F2F', fontweight='bold', ha='center')
    
    # CS Bot
    ax.annotate(rebar_results.get('CS_Bot','?'), xy=(L_span/2, bot_y), xytext=(L_span/2, -0.7),
                arrowprops=dict(arrowstyle='->', color='#1976D2'), color='#1976D2', fontweight='bold', ha='center')

    setup_cad_style(ax, "SECTION A-A: REINFORCEMENT PROFILE")
    
    ax.set_xlim(-0.8, L_span + 1.2)
    ax.set_ylim(-1.0, h_m + 1.0)
    plt.tight_layout()
    return fig

# ==========================================
# 3. PLAN VIEW (IMPROVED)
# ==========================================
def plot_rebar_plan_view(L_span, L_width, c_para, rebar_results):
    fig, ax = plt.subplots(figsize=(10, 6))
    
    w_cs = min(L_span, L_width) / 2.0
    w_cs_half = w_cs / 2.0
    
    # 1. Background Zones with Hatching (Engineering Look)
    # Middle Strip
    rect_ms = patches.Rectangle((0, w_cs_half), L_span, L_width - w_cs, 
                                fc='#E3F2FD', ec='none', alpha=0.4, label='Middle Strip')
    ax.add_patch(rect_ms)
    
    # Column Strips (Top/Bot)
    rect_cs_bot = patches.Rectangle((0, 0), L_span, w_cs_half, 
                                    fc='#FFEBEE', ec='none', alpha=0.4, label='Col Strip')
    rect_cs_top = patches.Rectangle((0, L_width - w_cs_half), L_span, w_cs_half, 
                                    fc='#FFEBEE', ec='none', alpha=0.4)
    ax.add_patch(rect_cs_bot)
    ax.add_patch(rect_cs_top)
    
    # Grid Lines (Center Lines)
    ax.axhline(L_width/2, color='gray', linestyle='-.', linewidth=0.5) # CL Slab
    ax.axvline(0, color='gray', linestyle='-.', linewidth=0.5)         # CL Col Left
    ax.axvline(L_span, color='gray', linestyle='-.', linewidth=0.5)    # CL Col Right
    
    # 2. Columns
    c_m = c_para / 100
    for cx in [0, L_span]:
        for cy in [0, L_width]:
            ax.add_patch(patches.Rectangle((cx-c_m/2, cy-c_m/2), c_m, c_m, fc='black', zorder=10))

    # 3. Rebar Drawing (CAD Style)
    bar_len = L_span * 0.3
    
    def draw_bar_group(y_pos, txt, color, is_top=True):
        if is_top:
            # Left
            ax.plot([-0.2, bar_len], [y_pos, y_pos], color=color, lw=2)
            ax.plot([bar_len], [y_pos], marker='|', color=color, ms=10) # End mark
            # Right
            ax.plot([L_span-bar_len, L_span+0.2], [y_pos, y_pos], color=color, lw=2)
            ax.plot([L_span-bar_len], [y_pos], marker='|', color=color, ms=10)
            
            # Label Left
            ax.text(bar_len/2, y_pos + 0.15, txt, color=color, fontsize=8, ha='center', fontweight='bold')
        else:
            # Bottom (Full Span)
            ax.plot([0.1, L_span-0.1], [y_pos, y_pos], color=color, lw=2)
            ax.text(L_span/2, y_pos + 0.15, txt, color=color, fontsize=8, ha='center', fontweight='bold')

    # CS Bars
    draw_bar_group(w_cs_half/2, rebar_results.get('CS_Top',''), '#D32F2F', is_top=True)
    draw_bar_group(w_cs_half/2 - 0.3, rebar_results.get('CS_Bot',''), '#1976D2', is_top=False) # Offset Bot
    
    draw_bar_group(L_width - w_cs_half/2, rebar_results.get('CS_Top',''), '#D32F2F', is_top=True)
    
    # MS Bars
    draw_bar_group(L_width/2 + 0.3, rebar_results.get('MS_Top',''), '#D32F2F', is_top=True)
    draw_bar_group(L_width/2, rebar_results.get('MS_Bot',''), '#1976D2', is_top=False)

    # 4. Dimensions (Widths)
    add_dimension(ax, L_span+0.8, 0, L_span+0.8, w_cs_half, f"CS/2\n{w_cs_half:.2f}m", offset=0, color='gray')
    add_dimension(ax, L_span+0.8, w_cs_half, L_span+0.8, L_width-w_cs_half, f"Middle Strip\n{L_width-w_cs:.2f}m", offset=0, color='gray')
    add_dimension(ax, L_span+0.8, L_width-w_cs_half, L_span+0.8, L_width, f"CS/2", offset=0, color='gray')

    setup_cad_style(ax, f"PLAN VIEW: REBAR LAYOUT (Span {L_span}x{L_width}m)")
    ax.set_xlim(-1, L_span + 1.5)
    ax.set_ylim(-0.5, L_width + 0.5)
    plt.tight_layout()
    
    return fig
