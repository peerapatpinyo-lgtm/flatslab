import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

def plot_ddm_moment(L_span, c1, m_vals):
    """
    วาดกราฟ Moment Envelope (Column Strip vs Middle Strip)
    """
    fig, ax = plt.subplots(figsize=(10, 4))
    
    # สร้างแกน X (ระยะทาง)
    x = np.linspace(0, L_span, 100)
    
    # 1. สร้าง Curve จำลองสำหรับ Moment Diagram (Parabolic approximation)
    # เราทราบค่า M- (Left), M+ (Mid), M- (Right)
    # Column Strip
    M_neg_cs = m_vals['M_cs_neg']
    M_pos_cs = m_vals['M_cs_pos']
    
    # Middle Strip
    M_neg_ms = m_vals['M_ms_neg']
    M_pos_ms = m_vals['M_ms_pos']

    # Function สร้าง Parabola
    def get_moment_curve(x_arr, M_neg, M_pos, L):
        # สมการพาราโบลาแบบง่าย: y = 4*M_pos * (x/L)*(1-x/L) - M_neg * (something)
        # เพื่อความง่ายในการแสดงผล ใช้ interpolation ระหว่างจุด
        x_pts = [0, 0.15*L, 0.5*L, 0.85*L, L]
        y_pts = [-M_neg, 0, M_pos, 0, -M_neg] # Negative อยู่ข้างบน (Top Tension) ตาม convention ก่อสร้างบางที่
        # แต่เพื่อให้เข้าใจง่าย: M- (Top Steel) ให้ค่าเป็นลบ, M+ (Bot Steel) ให้ค่าเป็นบวก
        # แต่เวลา plot จะกลับแกน Y ให้ M- อยู่ด้านบน (Top Fiber Tension)
        return np.interp(x_arr, x_pts, y_pts, left=-M_neg, right=-M_neg)

    # คำนวณค่า Y
    y_cs = np.interp(x, [0, L_span*0.2, L_span*0.5, L_span*0.8, L_span], [-M_neg_cs, 0, M_pos_cs, 0, -M_neg_cs])
    y_ms = np.interp(x, [0, L_span*0.2, L_span*0.5, L_span*0.8, L_span], [-M_neg_ms, 0, M_pos_ms, 0, -M_neg_ms])

    # Plot Lines
    ax.plot(x, y_cs, label='Column Strip', color='#d62728', linewidth=2) # Red
    ax.plot(x, y_ms, label='Middle Strip', color='#1f77b4', linewidth=2, linestyle='--') # Blue Dashed
    
    # Fill Area
    ax.fill_between(x, y_cs, 0, alpha=0.1, color='#d62728')
    
    # Decorations
    ax.axhline(0, color='black', linewidth=1)
    ax.set_title(f"Moment Distribution Diagram (Span {L_span} m)", fontweight='bold')
    ax.set_xlabel("Distance (m)")
    ax.set_ylabel("Moment (kg-m)")
    
    # Invert Y เพื่อให้ M- (Top Tension) อยู่ด้านบน ตามความรู้สึกเหล็กบน
    # หรือถ้าชอบกราฟมาตรฐานคณิตศาสตร์ ให้ M+ อยู่บน (แล้วแต่ชอบ)
    # ในที่นี้ขอเอา M- (Negative) ไว้ด้านบนเพื่อให้ตรงกับตำแหน่งเหล็กบน
    ax.set_ylim(max(M_pos_cs, M_pos_ms)*1.2, -max(M_neg_cs, M_neg_ms)*1.2) 
    
    # Annotate Values
    bbox = dict(boxstyle="round", fc="white", alpha=0.8, ec="none")
    # Top Left
    ax.text(0, -M_neg_cs, f"CS M-: {M_neg_cs:,.0f}", color='#d62728', ha='left', va='top', bbox=bbox, fontweight='bold')
    # Bot Mid
    ax.text(L_span/2, M_pos_cs, f"CS M+: {M_pos_cs:,.0f}", color='#d62728', ha='center', va='bottom', bbox=bbox, fontweight='bold')
    
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend()
    
    return fig

def plot_rebar_detailing(L_span, h_slab, c_para, rebar_results):
    """
    วาดรูปหน้าตัดอาคารแสดงการเสริมเหล็ก (Schematic Profile)
    """
    fig, ax = plt.subplots(figsize=(10, 3.5))
    
    # Scale conversion (m to plotting units)
    h_m = h_slab / 100
    c_m = c_para / 100
    
    # 1. Draw Concrete Slab
    slab = patches.Rectangle((0, 0), L_span, h_m, fc='#e9ecef', ec='gray', hatch='///')
    ax.add_patch(slab)
    
    # 2. Draw Columns
    col_h = 1.0 # ความสูงเสาหลอกๆ ในรูป
    ax.add_patch(patches.Rectangle((-c_m/2, -col_h), c_m, col_h, fc='#343a40')) # Left Col Below
    ax.add_patch(patches.Rectangle((-c_m/2, h_m), c_m, col_h, fc='#343a40'))    # Left Col Above
    
    ax.add_patch(patches.Rectangle((L_span-c_m/2, -col_h), c_m, col_h, fc='#343a40')) # Right Col Below
    ax.add_patch(patches.Rectangle((L_span-c_m/2, h_m), c_m, col_h, fc='#343a40'))    # Right Col Above
    
    # 3. Draw Rebar (Schematic)
    cover = 0.03 # 3cm visual cover
    
    # --- Top Bars (Column Strip) ---
    # Draw at Supports (approx 0.3Ln length)
    bar_len = L_span * 0.3
    top_y = h_m - cover
    
    # Left Top
    ax.plot([-c_m/2, bar_len], [top_y, top_y], color='#d62728', linewidth=3, marker='|')
    ax.text(0, top_y + 0.05, f"Top (CS): {rebar_results['CS_Top']}", color='#d62728', fontweight='bold', fontsize=9)
    
    # Right Top
    ax.plot([L_span - bar_len, L_span + c_m/2], [top_y, top_y], color='#d62728', linewidth=3, marker='|')
    ax.text(L_span, top_y + 0.05, f"{rebar_results['CS_Top']}", color='#d62728', fontweight='bold', ha='right', fontsize=9)
    
    # --- Bottom Bars (Column Strip & Middle) ---
    # Continuous bottom bar for simplicity in drawing
    bot_y = cover
    ax.plot([0, L_span], [bot_y, bot_y], color='#1f77b4', linewidth=3)
    ax.text(L_span/2, bot_y - 0.15, f"Bot (CS): {rebar_results['CS_Bot']}\nBot (MS): {rebar_results['MS_Bot']}", 
            color='#1f77b4', ha='center', va='top', fontweight='bold', fontsize=9)

    # Middle Strip Top (Shown slightly lower or dashed to distinguish? Or just annotate)
    # เพื่อไม่ให้รก จะไม่วาดเส้น Middle Strip Top ทับ แต่จะเขียน Note ไว้
    ax.text(L_span/2, h_m + 0.3, f"[Note: Middle Strip Top = {rebar_results['MS_Top']}]", 
            ha='center', fontsize=8, color='gray', style='italic')

    # Settings
    ax.set_xlim(-0.5, L_span + 0.5)
    ax.set_ylim(-0.5, h_m + 0.6)
    ax.axis('off') # ปิดแกน เพื่อให้ดูเป็น Drawing
    ax.set_title(f"Reinforcement Profile (Along Span {L_span} m)", loc='left', fontweight='bold')
    
    plt.tight_layout()
    return fig
