import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# ... (Keep existing plot_ddm_moment function) ...
def plot_ddm_moment(L_span, c1, m_vals):
    # (ใช้โค้ดเดิมจากรอบที่แล้วได้เลยครับ หรือ Copy ทั้งไฟล์ด้านล่างนี้ไปทับก็ได้)
    fig, ax = plt.subplots(figsize=(10, 4))
    x = np.linspace(0, L_span, 100)
    
    M_neg_cs = m_vals['M_cs_neg']
    M_pos_cs = m_vals['M_cs_pos']
    M_neg_ms = m_vals['M_ms_neg']
    M_pos_ms = m_vals['M_ms_pos']

    y_cs = np.interp(x, [0, L_span*0.2, L_span*0.5, L_span*0.8, L_span], [-M_neg_cs, 0, M_pos_cs, 0, -M_neg_cs])
    y_ms = np.interp(x, [0, L_span*0.2, L_span*0.5, L_span*0.8, L_span], [-M_neg_ms, 0, M_pos_ms, 0, -M_neg_ms])

    ax.plot(x, y_cs, label='Column Strip', color='#d62728', linewidth=2)
    ax.plot(x, y_ms, label='Middle Strip', color='#1f77b4', linewidth=2, linestyle='--')
    ax.fill_between(x, y_cs, 0, alpha=0.1, color='#d62728')
    
    ax.axhline(0, color='black', linewidth=1)
    ax.set_title(f"Moment Distribution Diagram (Span {L_span} m)", fontweight='bold')
    ax.set_xlabel("Distance (m)")
    ax.set_ylabel("Moment (kg-m)")
    ax.set_ylim(max(M_pos_cs, M_pos_ms)*1.2, -max(M_neg_cs, M_neg_ms)*1.2) 
    
    bbox = dict(boxstyle="round", fc="white", alpha=0.8, ec="none")
    ax.text(0, -M_neg_cs, f"CS M-: {M_neg_cs:,.0f}", color='#d62728', ha='left', va='top', bbox=bbox, fontweight='bold')
    ax.text(L_span/2, M_pos_cs, f"CS M+: {M_pos_cs:,.0f}", color='#d62728', ha='center', va='bottom', bbox=bbox, fontweight='bold')
    
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend()
    return fig

# ... (Keep existing plot_rebar_detailing function) ...
def plot_rebar_detailing(L_span, h_slab, c_para, rebar_results):
    fig, ax = plt.subplots(figsize=(10, 3.0)) # ปรับความสูงนิดหน่อยให้กระชับ
    h_m = h_slab / 100
    c_m = c_para / 100
    
    slab = patches.Rectangle((0, 0), L_span, h_m, fc='#e9ecef', ec='gray', hatch='///')
    ax.add_patch(slab)
    
    col_h = 0.8
    ax.add_patch(patches.Rectangle((-c_m/2, -col_h), c_m, col_h, fc='#343a40'))
    ax.add_patch(patches.Rectangle((-c_m/2, h_m), c_m, col_h, fc='#343a40'))
    ax.add_patch(patches.Rectangle((L_span-c_m/2, -col_h), c_m, col_h, fc='#343a40'))
    ax.add_patch(patches.Rectangle((L_span-c_m/2, h_m), c_m, col_h, fc='#343a40'))
    
    cover = 0.03
    bar_len = L_span * 0.3
    top_y = h_m - cover
    
    # Top Bars (Red)
    ax.plot([-c_m/2, bar_len], [top_y, top_y], color='#d62728', linewidth=3, marker='|')
    ax.text(0, top_y + 0.05, f"Top (CS): {rebar_results.get('CS_Top','?')}", color='#d62728', fontweight='bold', fontsize=9)
    
    ax.plot([L_span - bar_len, L_span + c_m/2], [top_y, top_y], color='#d62728', linewidth=3, marker='|')
    
    # Bot Bars (Blue)
    bot_y = cover
    ax.plot([0, L_span], [bot_y, bot_y], color='#1f77b4', linewidth=3)
    ax.text(L_span/2, bot_y - 0.15, f"Bot (CS): {rebar_results.get('CS_Bot','?')}\nBot (MS): {rebar_results.get('MS_Bot','?')}", 
            color='#1f77b4', ha='center', va='top', fontweight='bold', fontsize=9)
            
    ax.text(L_span/2, h_m + 0.3, f"[Note: Middle Strip Top = {rebar_results.get('MS_Top','?')}]", 
            ha='center', fontsize=8, color='gray', style='italic')

    ax.set_xlim(-0.5, L_span + 0.5)
    ax.set_ylim(-0.5, h_m + 0.6)
    ax.axis('off')
    ax.set_title(f"A. Side View (Profile)", loc='left', fontweight='bold')
    plt.tight_layout()
    return fig

# ==========================================
# 🆕 NEW FUNCTION: TOP VIEW (PLAN)
# ==========================================
def plot_rebar_plan_view(L_span, L_width, c_para, rebar_results):
    """
    วาด Plan View แสดงตำแหน่งเหล็กใน Column Strip และ Middle Strip
    """
    fig, ax = plt.subplots(figsize=(10, 5))
    
    # Setup Geometry
    margin = 0.5
    ax.set_xlim(-margin, L_span + margin)
    ax.set_ylim(-margin, L_width + margin)
    
    # Zones Dimensions
    w_cs_total = min(L_span, L_width) / 2.0
    w_cs_half = w_cs_total / 2.0 # CS แบ่งครึ่งอยู่ขอบบนและล่าง
    
    # 1. Background Zones
    # Column Strip (Top & Bottom Edges)
    rect_cs_bot = patches.Rectangle((0, 0), L_span, w_cs_half, fc='#fff5f5', ec='none') # Light Red tint
    rect_cs_top = patches.Rectangle((0, L_width - w_cs_half), L_span, w_cs_half, fc='#fff5f5', ec='none')
    ax.add_patch(rect_cs_bot)
    ax.add_patch(rect_cs_top)
    
    # Middle Strip (Center)
    h_ms = L_width - w_cs_total
    rect_ms = patches.Rectangle((0, w_cs_half), L_span, h_ms, fc='#f0f8ff', ec='none') # Light Blue tint
    ax.add_patch(rect_ms)
    
    # 2. Draw Columns (Corners)
    c_m = c_para / 100
    cols = [
        (0 - c_m/2, 0 - c_m/2),         # Bot-Left
        (L_span - c_m/2, 0 - c_m/2),    # Bot-Right
        (0 - c_m/2, L_width - c_m/2),   # Top-Left
        (L_span - c_m/2, L_width - c_m/2) # Top-Right
    ]
    for (cx, cy) in cols:
        ax.add_patch(patches.Rectangle((cx, cy), c_m, c_m, fc='#343a40', zorder=5))
        
    # 3. Draw Rebar (Schematic)
    # Style Config
    style_top = dict(color='#d62728', linewidth=2, linestyle='-') # Red Solid
    style_bot = dict(color='#1f77b4', linewidth=2, linestyle='-') # Blue Solid
    
    # --- Column Strip Rebar (Draw at Top and Bottom edges) ---
    # Top Bars (Red) - Short bars at supports
    bar_len = L_span * 0.25
    y_locs_cs = [w_cs_half/2, L_width - w_cs_half/2] # Center of CS strips
    
    for y in y_locs_cs:
        # Left Support
        ax.plot([-0.2, bar_len], [y, y], **style_top)
        # Right Support
        ax.plot([L_span-bar_len, L_span+0.2], [y, y], **style_top)
        # Bot Bar (Full Span)
        ax.plot([0, L_span], [y-0.1, y-0.1], **style_bot) # Shift slightly

    # --- Middle Strip Rebar (Center) ---
    y_ms_center = L_width / 2
    # Top Bars (Red) - At edges (Supports)
    ax.plot([0, bar_len], [y_ms_center + 0.2, y_ms_center + 0.2], **style_top) # Left
    ax.plot([L_span-bar_len, L_span], [y_ms_center + 0.2, y_ms_center + 0.2], **style_top) # Right
    
    # Bot Bar (Blue) - Full Span
    ax.plot([0, L_span], [y_ms_center, y_ms_center], **style_bot)
    
    # 4. Annotations (Labels)
    bbox_red = dict(boxstyle="round", fc="white", ec="#d62728", alpha=0.9)
    bbox_blue = dict(boxstyle="round", fc="white", ec="#1f77b4", alpha=0.9)
    
    # Label CS
    ax.text(bar_len/2, L_width - w_cs_half/2, f"Top: {rebar_results.get('CS_Top','')}", 
            color='#d62728', fontsize=8, ha='center', va='bottom', bbox=bbox_red)
    ax.text(L_span/2, w_cs_half/2 - 0.1, f"Bot: {rebar_results.get('CS_Bot','')}", 
            color='#1f77b4', fontsize=8, ha='center', va='top', bbox=bbox_blue)
            
    # Label MS
    ax.text(L_span/2, y_ms_center, f"Bot (MS): {rebar_results.get('MS_Bot','')}", 
            color='#1f77b4', fontsize=8, ha='center', va='bottom', bbox=bbox_blue)
    ax.text(bar_len, y_ms_center + 0.2, f"Top (MS): {rebar_results.get('MS_Top','')}", 
            color='#d62728', fontsize=8, ha='left', va='center', bbox=bbox_red)

    # Zone Labels
    ax.text(L_span*0.8, w_cs_half/2, "Column Strip", color='gray', alpha=0.5, ha='center', fontsize=10, fontweight='bold')
    ax.text(L_span*0.8, L_width - w_cs_half/2, "Column Strip", color='gray', alpha=0.5, ha='center', fontsize=10, fontweight='bold')
    ax.text(L_span*0.8, y_ms_center, "Middle Strip", color='gray', alpha=0.5, ha='center', fontsize=10, fontweight='bold')

    # Borders & Finalize
    ax.add_patch(patches.Rectangle((0,0), L_span, L_width, fill=False, edgecolor='black', linewidth=1))
    ax.set_title(f"B. Top View (Rebar Plan) - {L_span}x{L_width}m", loc='left', fontweight='bold')
    ax.axis('off')
    plt.tight_layout()
    
    return fig
