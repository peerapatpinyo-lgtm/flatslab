import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.ticker as ticker
import numpy as np
import streamlit as st

def draw_span_schematic(span_type):
    """
    สร้างรูปตัดขวาง (Schematic Section) ตามประเภท Span ที่เลือก
    เพื่อให้วิศวกรเห็นภาพ Boundary Condition
    """
    fig, ax = plt.subplots(figsize=(6, 2))
    ax.set_xlim(-1, 11)
    ax.set_ylim(-1, 3)
    ax.axis('off') # ปิดแกนเลข

    # สไตล์คอนกรีต
    slab_color = '#e0e0e0' # สีเทาอ่อน
    support_color = '#404040' # สีเทาเข้ม
    line_color = 'black'

    # วาดพื้น Slab หลัก (ยาวตลอด)
    # สมมติ Span ยาวจาก x=0 ถึง x=10
    rect = patches.Rectangle((0, 1.5), 10, 0.5, linewidth=1, edgecolor=line_color, facecolor=slab_color)
    ax.add_patch(rect)
    
    # Text Properties
    font_props = {'ha': 'center', 'va': 'center', 'fontsize': 9, 'color': 'blue'}

    if "Interior" in span_type:
        # Case 1: Interior Span (ต่อเนื่องทั้งสองฝั่ง)
        # วาดเสา 3 ต้น (ซ้าย กลาง ขวา) เพื่อแสดงความต่อเนื่อง
        
        # Left Support (Continuous)
        ax.add_patch(patches.Rectangle((-0.5, 0), 1, 1.5, color=support_color))
        # Right Support (Continuous)
        ax.add_patch(patches.Rectangle((9.5, 0), 1, 1.5, color=support_color))
        
        # สัญลักษณ์ความต่อเนื่อง (Break lines)
        ax.text(-0.8, 1.75, "~", fontsize=20, ha='center') 
        ax.text(10.8, 1.75, "~", fontsize=20, ha='center')
        
        ax.text(5, 2.5, "Interior Span\n(Continuous Both Ends)", **font_props)
        ax.text(5, 0.5, "Moment Coeff: Neg 0.65 | Pos 0.35", fontsize=8, ha='center', color='gray')

    elif "Edge Beam" in span_type:
        # Case 2: End Span with Edge Beam (ขอบมีคานลึก)
        
        # Left Support (Edge Beam) - วาดให้ลึกกว่าพื้น
        # Beam size: 1x2.5
        ax.add_patch(patches.Rectangle((0, 0.5), 1, 1.0, linewidth=1, edgecolor=line_color, facecolor='#a0a0a0')) 
        ax.add_patch(patches.Rectangle((0, 0), 1, 1.5, color=support_color)) # Column under beam
        
        # Right Support (Interior Column)
        ax.add_patch(patches.Rectangle((9.5, 0), 1, 1.5, color=support_color))
        ax.text(10.8, 1.75, "~", fontsize=20, ha='center') # Continuous Right
        
        ax.text(5, 2.5, "End Span w/ Edge Beam\n(Stiff Edge)", **font_props)
        ax.text(1.5, 0.2, "Stiff Beam", fontsize=8, color='red')
        ax.text(5, 0.5, "Moment Coeff: Ext.Neg 0.30 | Pos 0.50 | Int.Neg 0.70", fontsize=8, ha='center', color='gray')

    elif "No Beam" in span_type:
        # Case 3: End Span (Flat Plate) - ไม่มีคานขอบ
        
        # Left Support (Column Only)
        ax.add_patch(patches.Rectangle((0, 0), 1, 1.5, color=support_color))
        
        # Right Support (Interior Column)
        ax.add_patch(patches.Rectangle((9.5, 0), 1, 1.5, color=support_color))
        ax.text(10.8, 1.75, "~", fontsize=20, ha='center') # Continuous Right
        
        ax.text(5, 2.5, "End Span (Flat Plate)\n(Flexible Edge)", **font_props)
        ax.text(0.5, 2.2, "Free Edge", fontsize=8, color='red', ha='center')
        ax.text(5, 0.5, "Moment Coeff: Ext.Neg 0.26 | Pos 0.52 | Int.Neg 0.70", fontsize=8, ha='center', color='gray')

    return fig
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

# Zone Colors
CLR_ZONE_CS = '#FFF0F0'  # Column Strip
CLR_ZONE_MS = '#F0F8FF'  # Middle Strip

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
    ax.annotate('', xy=(x1, y1), xytext=(x2, y2),
                arrowprops=dict(arrowstyle='<|-|>', color=color, lw=0.8))
    
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
# 1. BENDING MOMENT DIAGRAM
# ==========================================
def plot_ddm_moment(L_span, c1, m_vals):
    fig, ax = plt.subplots(figsize=(10, 4), facecolor=CLR_BG)
    
    x = np.linspace(0, L_span, 400)
    M_neg_cs, M_pos_cs = m_vals['M_cs_neg'], m_vals['M_cs_pos']
    M_neg_ms, M_pos_ms = m_vals['M_ms_neg'], m_vals['M_ms_pos']

    # Interpolation Points (Simplified Parabolic)
    pts_x = [0, L_span*0.2, L_span*0.5, L_span*0.8, L_span]
    pts_y_cs = [-M_neg_cs, 0, M_pos_cs, 0, -M_neg_cs]
    pts_y_ms = [-M_neg_ms, 0, M_pos_ms, 0, -M_neg_ms]
    
    y_cs = np.interp(x, pts_x, pts_y_cs)
    y_ms = np.interp(x, pts_x, pts_y_ms)

    ax.axhline(0, color='black', lw=0.8, zorder=1)
    ax.plot(x, y_ms, label='Middle Strip', color=CLR_BAR_BOT, lw=1.5, ls='--', alpha=0.6)
    ax.plot(x, y_cs, label='Column Strip', color=CLR_BAR_TOP, lw=2.5)

    ax.fill_between(x, y_cs, 0, where=(y_cs<0), color=CLR_BAR_TOP, alpha=0.1)
    ax.fill_between(x, y_cs, 0, where=(y_cs>0), color=CLR_BAR_BOT, alpha=0.1)

    setup_axis_labels(ax, f"BENDING MOMENT DIAGRAM (Span = {L_span:.2f} m)")
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
# 2. SECTION A-A DETAILED
# ==========================================
def plot_rebar_detailing(L_span, h_slab, c_para, rebar_results, axis_dir):
    h_m = h_slab / 100.0
    c_m = c_para / 100.0
    
    fig, ax = plt.subplots(figsize=(10, 3.5), facecolor=CLR_BG)
    ax.axis('off')

    # Concrete
    rect = patches.Rectangle((0, 0), L_span, h_m, fc=CLR_CONCRETE, ec=CLR_EDGE, lw=1.5)
    ax.add_patch(rect)
    
    # Columns
    col_h = 0.5 
    for cx in [0, L_span]:
        ax.add_patch(patches.Rectangle((cx - c_m/2, h_m), c_m, col_h, fc='white', ec=CLR_EDGE, hatch='///'))
        ax.add_patch(patches.Rectangle((cx - c_m/2, -col_h), c_m, col_h, fc='white', ec=CLR_EDGE, hatch='///'))
        ax.plot([cx, cx], [-col_h*1.2, h_m+col_h*1.2], 'k-.', lw=0.5, alpha=0.5)

    # Rebars
    cover = 0.025
    y_top = h_m - cover
    y_bot = cover
    cutoff_len = L_span / 3.0
    
    # Top Bars (Support)
    ax.plot([-c_m/2, cutoff_len], [y_top, y_top], color=CLR_BAR_TOP, lw=LW_BAR)
    ax.plot([-c_m/2, -c_m/2], [y_top, y_top - 0.15], color=CLR_BAR_TOP, lw=LW_BAR) # Hook
    
    ax.plot([L_span - cutoff_len, L_span + c_m/2], [y_top, y_top], color=CLR_BAR_TOP, lw=LW_BAR)
    ax.plot([L_span + c_m/2, L_span + c_m/2], [y_top, y_top - 0.15], color=CLR_BAR_TOP, lw=LW_BAR) # Hook

    # Bottom Bar (Continuous)
    ax.plot([0, L_span], [y_bot, y_bot], color=CLR_BAR_BOT, lw=LW_BAR)
    ax.plot([0, 0], [y_bot, y_bot + 0.10], color=CLR_BAR_BOT, lw=LW_BAR) # Hook
    ax.plot([L_span, L_span], [y_bot, y_bot + 0.10], color=CLR_BAR_BOT, lw=LW_BAR) # Hook

    # Dimensions
    draw_dimension(ax, 0, h_m + 0.1, cutoff_len, h_m + 0.1, f"L/3 = {cutoff_len:.2f} m", offset=0.1)
    draw_dimension(ax, L_span - cutoff_len, h_m + 0.1, L_span, h_m + 0.1, "L/3", offset=0.1)

    # Labels
    txt_top = rebar_results.get('CS_Top', 'DB??')
    txt_bot = rebar_results.get('CS_Bot', 'DB??')
    
    ax.annotate(f"Top: {txt_top}", xy=(cutoff_len/2, y_top), xytext=(cutoff_len/2, y_top + 0.4),
                arrowprops=dict(arrowstyle='->', color=CLR_BAR_TOP), color=CLR_BAR_TOP, fontweight='bold')
    
    ax.annotate(f"Bot: {txt_bot}", xy=(L_span/2, y_bot), xytext=(L_span/2, y_bot - 0.4),
                arrowprops=dict(arrowstyle='->', color=CLR_BAR_BOT), color=CLR_BAR_BOT, fontweight='bold')

    ax.set_title(f"SECTION A-A: REBAR DETAILING ({axis_dir})", fontsize=11, fontweight='bold', pad=20)
    ax.set_xlim(-0.5, L_span + 0.5)
    ax.set_ylim(-0.8, h_m + 1.0)
    plt.tight_layout()
    return fig

# ==========================================
# 3. PLAN VIEW DETAILED
# ==========================================
def plot_rebar_plan_view(L_span, L_width, c_para, rebar_results, axis_dir):
    fig, ax = plt.subplots(figsize=(8, 8), facecolor=CLR_BG)
    ax.axis('off')
    
    W = L_span if axis_dir == 'X' else L_width
    H = L_width if axis_dir == 'X' else L_span
    w_cs_half = min(L_span, L_width) / 4.0
    
    # Zones
    # CS Bot
    ax.add_patch(patches.Rectangle((0, 0), W, w_cs_half, fc=CLR_ZONE_CS, ec='none'))
    ax.text(W/2, w_cs_half/2, "Column Strip", color=CLR_BAR_TOP, alpha=0.1, ha='center', va='center', fontweight='bold', fontsize=15)
    # CS Top
    ax.add_patch(patches.Rectangle((0, H - w_cs_half), W, w_cs_half, fc=CLR_ZONE_CS, ec='none'))
    ax.text(W/2, H - w_cs_half/2, "Column Strip", color=CLR_BAR_TOP, alpha=0.1, ha='center', va='center', fontweight='bold', fontsize=15)
    # MS
    ax.add_patch(patches.Rectangle((0, w_cs_half), W, H - 2*w_cs_half, fc=CLR_ZONE_MS, ec='none'))
    ax.text(W/2, H/2, "Middle Strip", color=CLR_BAR_BOT, alpha=0.1, ha='center', va='center', fontweight='bold', fontsize=15)

    ax.add_patch(patches.Rectangle((0, 0), W, H, fill=False, ec='black', lw=1.5))

    # Rebar Drawing Logic
    cutoff = W / 3.0
    
    def draw_rebar_line(y_pos, type_z, is_top):
        c = CLR_BAR_TOP if is_top else CLR_BAR_BOT
        lbl = rebar_results.get(f"{type_z}_{'Top' if is_top else 'Bot'}", "?")
        
        if is_top:
            # Left & Right with Cutoff
            ax.plot([0, cutoff], [y_pos, y_pos], color=c, lw=2)
            ax.plot([cutoff], [y_pos], marker='|', color=c, ms=10)
            
            ax.plot([W-cutoff, W], [y_pos, y_pos], color=c, lw=2)
            ax.plot([W-cutoff], [y_pos], marker='|', color=c, ms=10)
            
            ax.text(cutoff/2, y_pos + 0.1, lbl, color=c, fontsize=8, fontweight='bold', ha='center')
            ax.text(W - cutoff/2, y_pos + 0.1, lbl, color=c, fontsize=8, fontweight='bold', ha='center')
        else:
            # Continuous
            ax.plot([0, W], [y_pos, y_pos], color=c, lw=2)
            ax.text(W/2, y_pos + 0.1, lbl, color=c, fontsize=8, fontweight='bold', ha='center')

    # Draw Rebars
    draw_rebar_line(w_cs_half * 0.3, 'CS', is_top=False)
    draw_rebar_line(w_cs_half * 0.7, 'CS', is_top=True)
    draw_rebar_line(H/2 - 0.3, 'MS', is_top=False)
    draw_rebar_line(H/2 + 0.3, 'MS', is_top=True)
    draw_rebar_line(H - w_cs_half * 0.7, 'CS', is_top=True)
    draw_rebar_line(H - w_cs_half * 0.3, 'CS', is_top=False)

    # Dimensions
    y_dim = H + 0.5
    draw_dimension(ax, 0, y_dim, cutoff, y_dim, "L/3", offset=0.2, color='black')
    draw_dimension(ax, W-cutoff, y_dim, W, y_dim, "L/3", offset=0.2, color='black')
    
    draw_dimension(ax, 0, -0.5, W, -0.5, f"Span = {W:.2f} m", offset=-0.4)
    draw_dimension(ax, W + 0.5, 0, W + 0.5, H, f"Width = {H:.2f} m", offset=0.4)

    ax.set_title(f"PLAN VIEW: REBAR LAYOUT ({axis_dir})", fontsize=12, fontweight='bold', pad=20)
    ax.set_xlim(-1, W + 1)
    ax.set_ylim(-2, H + 2)
    plt.tight_layout()
    return fig

# เพิ่มต่อท้ายในไฟล์ ddm_plots.py
def plot_punching_shear_geometry(c1, c2, d_avg, bo, status, ratio):
    """
    แสดงรูปแปลนจุดรองรับและแนววิกฤต Punching Shear
    """
    fig, ax = plt.subplots(figsize=(6, 6), facecolor=CLR_BG)
    
    # Scale constants
    limit = max(c1, c2) * 3 + d_avg * 2
    ax.set_xlim(-limit/2, limit/2)
    ax.set_ylim(-limit/2, limit/2)
    ax.set_aspect('equal')
    ax.axis('off')
    
    # 1. Column (Center)
    col_rect = patches.Rectangle((-c1/2, -c2/2), c1, c2, 
                                 fc='#343A40', ec='black', zorder=10)
    ax.add_patch(col_rect)
    ax.text(0, 0, "Column", color='white', ha='center', va='center', fontweight='bold')
    
    # 2. Critical Section (d/2 offset)
    crit_w = c1 + d_avg
    crit_h = c2 + d_avg
    color_crit = '#28A745' if status == "OK" else '#DC3545' # Green or Red
    
    crit_rect = patches.Rectangle((-crit_w/2, -crit_h/2), crit_w, crit_h, 
                                  fc=color_crit, ec=color_crit, alpha=0.2, ls='--', lw=2, zorder=5)
    ax.add_patch(crit_rect)
    
    # เส้นขอบเขต Critical
    crit_outline = patches.Rectangle((-crit_w/2, -crit_h/2), crit_w, crit_h, 
                                     fill=False, ec=color_crit, ls='--', lw=2, zorder=6)
    ax.add_patch(crit_outline)

    # 3. Dimensions
    # d/2 arrows
    ax.annotate("", xy=(c1/2, 0), xytext=(crit_w/2, 0), arrowprops=dict(arrowstyle='<->', color='black'))
    ax.text((c1/2 + crit_w/2)/2, 0.1 * limit, "d/2", ha='center', fontsize=9)
    
    # 4. Status Label
    ax.set_title(f"PUNCHING SHEAR CHECK: {status}\nRatio = {ratio:.2f}", 
                 color=color_crit, fontweight='bold', fontsize=12)
    
    plt.tight_layout()
    return fig
