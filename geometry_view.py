import matplotlib.pyplot as plt
import matplotlib.patches as patches

def plot_geometry_detailed(L1, L2, c1, c2, h_slab, lc, Ic_val):
    """(ฟังก์ชันเดิม - วาดรูปตัดและแปลนทั่วไป)"""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 12), gridspec_kw={'height_ratios': [2, 1]})
    
    c1_m, c2_m, h_m = c1/100.0, c2/100.0, h_slab/100.0
    margin_x, margin_y = L1*0.2, L2*0.2

    # --- TOP VIEW ---
    ax1.set_title("PLAN VIEW (Top View)", fontsize=12, fontweight='bold', loc='left')
    
    # Draw Slab Outline
    ax1.add_patch(patches.Rectangle((-margin_x/2, -margin_y/2), L1+margin_x, L2+margin_y, 
                                    facecolor='#f8f9fa', edgecolor='#dee2e6', zorder=0))
    # Grid lines
    ax1.axvline(x=0, color='#adb5bd', linestyle='-.'); ax1.axvline(x=L1, color='#adb5bd', linestyle='-.')
    ax1.axhline(y=0, color='#adb5bd', linestyle='-.'); ax1.axhline(y=L2, color='#adb5bd', linestyle='-.')

    # Columns
    col_coords = [(0,0), (L1,0), (0,L2), (L1,L2)]
    for (cx, cy) in col_coords:
        ax1.add_patch(patches.Rectangle((cx - c1_m/2, cy - c2_m/2), c1_m, c2_m, fc='#343a40', ec='black', zorder=5))

    # Dims
    ax1.annotate('', xy=(0, -c2_m), xytext=(L1, -c2_m), arrowprops=dict(arrowstyle='<|-|>', color='blue'))
    ax1.text(L1/2, -c2_m*1.5, f"L1 = {L1}m", ha='center', color='blue')
    
    ax1.axis('equal'); ax1.axis('off')

    # --- SECTION VIEW ---
    ax2.set_title("SECTION VIEW", fontsize=12, fontweight='bold', loc='left')
    ax2.axhline(y=0, color='black', lw=2)
    ax2.add_patch(patches.Rectangle((-c1_m/2, 0), c1_m, lc, fc='#343a40'))
    ax2.add_patch(patches.Rectangle((-L1*0.2, lc-h_m), L1*1.4, h_m, fc='#e9ecef', hatch='///', ec='black'))
    
    ax2.annotate('', xy=(-L1*0.1, lc-h_m), xytext=(-L1*0.1, lc), arrowprops=dict(arrowstyle='<|-|>', color='red'))
    ax2.text(-L1*0.15, lc-h_m/2, f"h={h_slab}cm", va='center', color='red', rotation=90)

    ax2.axis('equal'); ax2.axis('off')
    plt.tight_layout()
    return fig

def plot_moment_map(L1, L2, c1, c2, M_col_neg, M_col_pos, M_mid_neg, M_mid_pos):
    """
    วาดแผนผังแสดงตำแหน่งโมเมนต์ (Moment Map)
    แบ่งสีโซน Col Strip vs Mid Strip และแปะค่าโมเมนต์
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Dimensions
    w_col_strip = min(L1, L2) / 2.0  # Total width of col strip (ACI: 0.25L on each side of centerline)
    half_col_strip = w_col_strip / 2.0
    
    # 1. Draw Column Strip (Darker Blue) - Centered on Y=0
    # Visualizing one full panel span L1, width L2
    
    # Zone: Column Strip (Along Line A)
    ax.add_patch(patches.Rectangle((0, -half_col_strip), L1, w_col_strip, 
                                   facecolor='#dbeafe', edgecolor='#0d6efd', alpha=0.5, label='Column Strip'))
    
    # Zone: Middle Strip (The rest)
    # Drawing top and bottom parts of middle strip to fill L2
    mid_strip_h = (L2 - w_col_strip) / 2
    if mid_strip_h > 0:
        ax.add_patch(patches.Rectangle((0, half_col_strip), L1, mid_strip_h, 
                                       facecolor='#e2e3e5', edgecolor='#adb5bd', alpha=0.5, label='Middle Strip'))
        ax.add_patch(patches.Rectangle((0, -L2/2), L1, mid_strip_h, # Simplified visualization
                                       facecolor='#e2e3e5', edgecolor='#adb5bd', alpha=0.5))

    # 2. Draw Columns
    c1_m, c2_m = c1/100, c2/100
    ax.add_patch(patches.Rectangle((-c1_m/2, -c2_m/2), c1_m, c2_m, fc='black'))
    ax.add_patch(patches.Rectangle((L1-c1_m/2, -c2_m/2), c1_m, c2_m, fc='black'))

    # 3. Add Moment Labels (The Values)
    bbox_props = dict(boxstyle="round,pad=0.3", fc="white", ec="black", alpha=0.9)
    
    # -- Column Strip Moments --
    # M- (Negative) at Column Face
    ax.text(c1_m, 0, f"M- (Col)\n{M_col_neg:,.0f}", ha='left', va='center', color='red', fontweight='bold', bbox=bbox_props)
    ax.text(L1-c1_m, 0, f"M- (Col)\n{M_col_neg:,.0f}", ha='right', va='center', color='red', fontweight='bold', bbox=bbox_props)
    # M+ (Positive) at Mid Span
    ax.text(L1/2, 0, f"M+ (Col)\n{M_col_pos:,.0f}", ha='center', va='center', color='blue', fontweight='bold', bbox=bbox_props)

    # -- Middle Strip Moments --
    # M- at Supports (Usually small)
    y_mid = half_col_strip + mid_strip_h/2
    ax.text(0, y_mid, f"M- (Mid)\n{M_mid_neg:,.0f}", ha='left', va='center', color='#6c757d', fontsize=9, bbox=bbox_props)
    # M+ at Mid Span
    ax.text(L1/2, y_mid, f"M+ (Mid)\n{M_mid_pos:,.0f}", ha='center', va='center', color='#0dcaf0', fontweight='bold', bbox=bbox_props)

    # Labels
    ax.text(L1*0.05, -half_col_strip*0.8, "COLUMN STRIP", color='#0d6efd', fontsize=10, fontweight='bold', style='italic')
    ax.text(L1*0.05, half_col_strip*1.2, "MIDDLE STRIP", color='gray', fontsize=10, fontweight='bold', style='italic')

    ax.set_title(f"MOMENT DISTRIBUTION MAP (Unit: kg-m)", fontsize=14, fontweight='bold', pad=15)
    ax.set_xlim(-L1*0.1, L1*1.1)
    ax.set_ylim(-L2/2, L2/2 + L2*0.2)
    ax.axis('off')
    
    return fig
