import matplotlib.pyplot as plt
import matplotlib.patches as patches

def plot_combined_view(L1, L2, c1, c2, h_slab, lc, M_data=None):
    """
    วาดรูปแปลน (Plan) และรูปตัด (Section) ในรูปเดียว
    M_data: Dictionary containing moments [Optional]
    """
    fig = plt.figure(figsize=(12, 14))
    gs = fig.add_gridspec(3, 1, height_ratios=[3, 1, 1.5])
    
    # Unit conv
    L1_m, L2_m = L1, L2
    c1_m, c2_m = c1/100, c2/100
    
    # ==========================
    # 1. PLAN VIEW (MOMENT MAP)
    # ==========================
    ax1 = fig.add_subplot(gs[0])
    ax1.set_title(f"PLAN VIEW: Column Strip vs Middle Strip (L1={L1}m x L2={L2}m)", fontsize=14, fontweight='bold')
    
    # Draw Slab
    margin = 1.0
    ax1.set_xlim(-margin, L1_m+margin)
    ax1.set_ylim(-L2_m/2 - margin, L2_m/2 + margin)
    
    # Zones
    w_cs = min(L1, L2)/2 # Total Column Strip Width
    h_cs = w_cs/2
    
    # Column Strip (Blue Zone)
    ax1.add_patch(patches.Rectangle((0, -h_cs), L1_m, w_cs, fc='#dbeafe', ec='#0d6efd', alpha=0.6, label='Column Strip'))
    
    # Middle Strip (Gray Zone) - Split top/bottom visually
    h_ms = (L2_m - w_cs)/2
    if h_ms > 0:
        ax1.add_patch(patches.Rectangle((0, h_cs), L1_m, h_ms, fc='#f8f9fa', ec='#adb5bd', hatch='..', alpha=0.6, label='Middle Strip'))
        ax1.add_patch(patches.Rectangle((0, -L2_m/2), L1_m, h_ms, fc='#f8f9fa', ec='#adb5bd', hatch='..', alpha=0.6))

    # Columns
    ax1.add_patch(patches.Rectangle((-c1_m/2, -c2_m/2), c1_m, c2_m, fc='black', zorder=10))
    ax1.add_patch(patches.Rectangle((L1_m-c1_m/2, -c2_m/2), c1_m, c2_m, fc='black', zorder=10))
    
    # Text Annotations for Moments
    if M_data:
        bbox = dict(boxstyle="round", fc="white", ec="black", alpha=0.9)
        # Col Strip
        ax1.text(c1_m*0.6, 0, f"M-\n{M_data['M_cs_neg']:,.0f}", color='red', ha='left', va='center', fontweight='bold', bbox=bbox)
        ax1.text(L1_m/2, 0, f"M+\n{M_data['M_cs_pos']:,.0f}", color='blue', ha='center', va='center', fontweight='bold', bbox=bbox)
        # Mid Strip
        ax1.text(L1_m/2, h_cs + h_ms/2, f"M+ (Mid)\n{M_data['M_ms_pos']:,.0f}", color='green', ha='center', va='center', fontsize=9, bbox=bbox)
    
    ax1.legend(loc='upper right')
    ax1.axis('off')
    
    # ==========================
    # 2. SECTION VIEW
    # ==========================
    ax2 = fig.add_subplot(gs[2])
    ax2.set_title("SECTION A-A: Longitudinal Section", fontsize=12, fontweight='bold', loc='left')
    
    h_m = h_slab/100
    ax2.set_xlim(-margin, L1_m+margin)
    ax2.set_ylim(0, lc+0.5)
    
    # Column & Slab
    ax2.add_patch(patches.Rectangle((-c1_m/2, 0), c1_m, lc, fc='#343a40')) # Col 1
    ax2.add_patch(patches.Rectangle((L1_m-c1_m/2, 0), c1_m, lc, fc='#343a40')) # Col 2
    ax2.add_patch(patches.Rectangle((-c1_m/2, lc-h_m), L1_m+c1_m, h_m, fc='#e9ecef', hatch='///', ec='black')) # Slab
    
    # Dims
    ax2.annotate(f"h={h_slab}cm", xy=(L1_m/2, lc-h_m), xytext=(L1_m/2, lc-h_m*3), 
                 arrowprops=dict(arrowstyle='->'), ha='center')
    ax2.text(L1_m/2, lc+0.1, f"Span L1 = {L1} m", ha='center', fontweight='bold')
    
    ax2.axis('off')
    
    plt.tight_layout()
    return fig
