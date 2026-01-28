import matplotlib.pyplot as plt
import matplotlib.patches as patches

def plot_slab_section(h_mm, cover_mm, c1_mm, ln_m, lx_m):
    """
    วาดรูปหน้าตัดพื้น (Cross Section) บริเวณหัวเสา
    แสดงความหนา, ระยะหุ้ม, และระยะยืดเหล็กบน (0.3Ln)
    """
    h = h_mm / 1000      # แปลงเป็นเมตร
    cover = cover_mm / 1000
    c1 = c1_mm / 1000
    
    # Setup Figure
    fig, ax = plt.subplots(figsize=(8, 4))
    
    # 1. วาดคอนกรีต (Concrete Body)
    # วาดพื้นยาวตลอดช่วง (ตัด Section มาดูแค่ช่วงใกล้เสา +/- 2.5m)
    view_limit = 2.0 
    slab_rect = patches.Rectangle((-view_limit, 0), 2*view_limit, h, 
                                  facecolor='#e0e0e0', edgecolor='gray', linewidth=1, label='Concrete')
    ax.add_patch(slab_rect)
    
    # 2. วาดเสา (Column)
    col_rect = patches.Rectangle((-c1/2, -0.5), c1, 0.5, 
                                 facecolor='#d9d9d9', edgecolor='black', hatch='///')
    ax.add_patch(col_rect)
    
    # 3. เหล็กเสริม (Rebar)
    # 3.1 เหล็กบน (Top Bar) - สีน้ำเงิน (Column Strip)
    # ระยะยืด 0.3 Ln จากขอบเสา หรือ Center (ตามมาตรฐาน ACI ปกติคิดจาก Face, แต่เพื่อให้เห็นภาพรวมใช้ 0.3Ln)
    # ความยาวเหล็กบน = c1 + 2*(0.33*ln) -> ACI Min extension is 0.3Ln
    top_bar_len = (c1/2) + (0.33 * ln_m) 
    y_top = h - cover
    ax.plot([-top_bar_len, top_bar_len], [y_top, y_top], 
            color='blue', linewidth=3, label='Top Bar (Min 0.3Ln)')
    
    # Marker จุดหยุดเหล็ก
    ax.plot([-top_bar_len, -top_bar_len], [y_top-0.02, y_top+0.02], 'b|', markersize=10)
    ax.plot([top_bar_len, top_bar_len], [y_top-0.02, y_top+0.02], 'b|', markersize=10)
    
    # Text บอกระยะ
    ax.text(top_bar_len, y_top + 0.02, f"Ext. {0.33*ln_m:.2f} m", ha='center', color='blue', fontsize=9)

    # 3.2 เหล็กล่าง (Bottom Bar) - สีเขียว (Continuous)
    y_bot = cover
    ax.plot([-view_limit + 0.1, view_limit - 0.1], [y_bot, y_bot], 
            color='green', linewidth=3, linestyle='-', label='Bottom Bar')

    # 4. Dimension Lines (เส้นบอกระยะ)
    # เส้นบอกความหนา h
    x_dim = -0.8 # ตำแหน่งเส้นบอกระยะ
    ax.annotate('', xy=(x_dim, 0), xytext=(x_dim, h),
                arrowprops=dict(arrowstyle='<->', color='red'))
    ax.text(x_dim - 0.1, h/2, f"h = {h_mm} mm", color='red', rotation=90, va='center')
    
    # เส้นบอก Cover
    ax.annotate('', xy=(0, h), xytext=(0, h-cover),
                arrowprops=dict(arrowstyle='<->', color='purple'))
    ax.text(0.1, h - cover/2, f"Cover {cover_mm} mm", color='purple', fontsize=8, va='center')

    # Center Line
    ax.axvline(0, color='black', linestyle='-.', linewidth=0.5, alpha=0.5)

    # Settings
    ax.set_xlim(-view_limit, view_limit)
    ax.set_ylim(-0.2, h + 0.3)
    ax.set_aspect('equal')
    ax.axis('off') # ปิดแกนเลข
    ax.set_title(f"Detailed Cross Section (Column Strip)\nSpan Ln = {ln_m:.2f} m", fontsize=11)
    ax.legend(loc='lower right', fontsize='small')
    
    return fig
