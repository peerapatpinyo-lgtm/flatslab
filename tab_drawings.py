# tab_drawings.py
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pandas as pd

# ==========================================
# 1. HELPER: CAD STYLING & DIMENSIONS
# ==========================================
def draw_dim(ax, p1, p2, text, offset=0, color='#000000', is_vert=False, font_size=10, is_inner=False):
    """
    Render architectural dimensions. 
    is_inner: If True, draws extension lines from the 'inside' face outwards.
    """
    x1, y1 = p1
    x2, y2 = p2
    
    # Calculate positions based on offset
    if is_vert:
        # Vertical Dimension
        x1 += offset; x2 += offset
        ha, va, rot = 'center', 'center', 90
        sign = 1 if offset > 0 else -1
        txt_x = x1 + (0.3 * sign) 
        txt_pos = (txt_x, (y1+y2)/2)
        
        # Extension Lines
        # If showing Clear Span (inner), legs go from face to dim line
        ax.plot([p1[0], x1], [p1[1], y1], color=color, lw=0.4, ls='-', alpha=0.6)
        ax.plot([p2[0], x2], [p2[1], y2], color=color, lw=0.4, ls='-', alpha=0.6)

    else:
        # Horizontal Dimension
        y1 += offset; y2 += offset
        ha, va, rot = 'center', 'center', 0
        sign = 1 if offset > 0 else -1
        txt_y = y1 + (0.3 * sign)
        txt_pos = ((x1+x2)/2, txt_y)

        # Extension Lines
        ax.plot([p1[0], x1], [p1[1], y1], color=color, lw=0.4, ls='-', alpha=0.6)
        ax.plot([p2[0], x2], [p2[1], y2], color=color, lw=0.4, ls='-', alpha=0.6)

    # Main Dimension Line
    ax.annotate('', xy=(x1, y1), xytext=(x2, y2),
                arrowprops=dict(arrowstyle='<|-|>', color=color, lw=0.7, mutation_scale=12))
    
    # Text Label
    ax.text(txt_pos[0], txt_pos[1], text, 
            color=color, fontsize=font_size, ha=ha, va=va, rotation=rot, 
            fontfamily='monospace', fontweight='bold', zorder=15,
            bbox=dict(facecolor='white', alpha=0.95, edgecolor='none', pad=1.5))

# ==========================================
# 2. HELPER: HTML ROW GENERATOR
# ==========================================
def get_row_html(label, value, unit, is_header=False, is_highlight=False):
    if is_header:
        return f'<tr style="background-color: #263238; color: white;"><td colspan="3" style="padding: 8px 10px; font-weight: bold; font-size: 0.9rem; border-top: 2px solid #000;">{label}</td></tr>'
    
    bg = "#e8f5e9" if is_highlight else "#ffffff" # Slight green tint for highlight
    col_val = "#1b5e20" if is_highlight else "#000000"
    w_val = "800" if is_highlight else "600"
    
    return f'<tr style="background-color: {bg}; border-bottom: 1px solid #ddd;"><td style="padding: 5px 10px; color: #444; font-weight: 500; font-size: 0.9rem;">{label}</td><td style="padding: 5px 10px; text-align: right; color: {col_val}; font-weight: {w_val}; font-family: monospace; font-size: 0.95rem;">{value}</td><td style="padding: 5px 10px; color: #888; font-size: 0.8rem;">[{unit}]</td></tr>'

# ==========================================
# 3. MAIN RENDER FUNCTION
# ==========================================
def render(L1, L2, c1_w, c2_w, h_slab, lc, cover, d_eff, 
           drop_data=None, moment_vals=None, 
           mat_props=None, loads=None):
    
    # --- Data Setup ---
    if drop_data is None: drop_data = {'has_drop': False, 'width': 0, 'length': 0, 'depth': 0}
    if mat_props is None: mat_props = {}
    if loads is None: loads = {}
    
    # Units conversion
    c1_m, c2_m = c1_w/100.0, c2_w/100.0
    
    # Clear Spans (Face-to-Face)
    Ln_x = L1 - c1_m
    Ln_y = L2 - c2_m
    
    has_drop = drop_data.get('has_drop')
    drop_w_m = drop_data.get('width', 0)/100.0
    drop_l_m = drop_data.get('length', 0)/100.0
    h_drop = drop_data.get('depth', 0)
    
    fc = mat_props.get('fc', 0)
    fy = mat_props.get('fy', 0)
    d_bar = mat_props.get('d_bar', 0)
    
    sdl = loads.get('SDL', 0)
    ll = loads.get('LL', 0)
    wu = loads.get('w_u', 0)
    
    # ==========================================
    # CSS STYLES
    # ==========================================
    st.markdown("""
    <style>
        .eng-sheet {
            font-family: 'Segoe UI', Tahoma, sans-serif;
            border: 2px solid #000;
            background: white;
            margin-bottom: 20px;
            box-shadow: 4px 4px 10px rgba(0,0,0,0.1);
        }
        .eng-header {
            background-color: #212121;
            color: white;
            padding: 12px;
            text-align: center;
            font-weight: 900;
            font-size: 1.2rem;
            letter-spacing: 1.5px;
            text-transform: uppercase;
        }
        .eng-table {
            width: 100%;
            border-collapse: collapse;
        }
        .eng-footer {
            padding: 12px;
            font-size: 0.75rem;
            color: #555;
            background: #f1f1f1;
            border-top: 1px solid #000;
            font-family: monospace;
        }
    </style>
    """, unsafe_allow_html=True)

    # ==========================================
    # LAYOUT
    # ==========================================
    col_gfx, col_dat = st.columns([1.8, 1])

    with col_gfx:
        st.markdown("**1. PLAN VIEW @ S-01**")
        fig, ax = plt.subplots(figsize=(10, 8)) # Increased height slightly
        
        # 1. Grid Lines (Centerlines)
        ax.plot([-1, L1+1], [L2/2, L2/2], color='#b0bec5', ls='-.', lw=0.6)
        ax.plot([L1/2, L1/2], [-1, L2+1], color='#b0bec5', ls='-.', lw=0.6)

        # 2. Slab Boundary
        ax.add_patch(patches.Rectangle((0, 0), L1, L2, fc='#fafafa', ec='#37474f', lw=1.5))

        # 3. Columns & Drop Panels
        centers = [(0,0), (L1,0), (0,L2), (L1,L2)]
        for cx, cy in centers:
            if has_drop:
                ax.add_patch(patches.Rectangle((cx-drop_w_m/2, cy-drop_l_m/2), drop_w_m, drop_l_m, 
                                               fc='#e3f2fd', ec='#1976d2', lw=1, ls='--', zorder=2))
            ax.add_patch(patches.Rectangle((cx-c1_m/2, cy-c2_m/2), c1_m, c2_m, 
                                           fc='#263238', ec='black', zorder=3))

        # ----------------------------------------------
        # 4. DIMENSIONS STRATEGY: 
        #    Top/Right = Center-to-Center (Black)
        #    Bottom/Left = Clear Span (Green)
        # ----------------------------------------------
        
        # A. Center-to-Center (Outer)
        draw_dim(ax, (0, L2), (L1, L2), f"Lx = {L1:.2f} m", offset=1.2, is_vert=False, font_size=11) # Top
        draw_dim(ax, (L1, 0), (L1, L2), f"Ly = {L2:.2f} m", offset=1.2, is_vert=True, font_size=11)  # Right
        
        # B. Clear Spans (Inner Face-to-Face) - NEW!
        # Clear Span X (Bottom)
        # Start from Right Face of Col 1 to Left Face of Col 2
        draw_dim(ax, (c1_m/2, 0), (L1 - c1_m/2, 0), f"Ln = {Ln_x:.2f} m", 
                 offset=-1.0, is_vert=False, color='#2e7d32', font_size=11)
        
        # Clear Span Y (Left)
        # Start from Top Face of Col 1 to Bottom Face of Col 3
        draw_dim(ax, (0, c2_m/2), (0, L2 - c2_m/2), f"Ln = {Ln_y:.2f} m", 
                 offset=-1.0, is_vert=True, color='#2e7d32', font_size=11)

        # C. Drop Panel Dims (Detail)
        if has_drop:
            # Drop Width (Top Support)
            draw_dim(ax, (L1 - drop_w_m/2, L2), (L1 + drop_w_m/2, L2), 
                     f"Drop: {drop_data['width']:.0f} cm", offset=0.5, color='#1565c0', font_size=9)
            # Drop Length (Right Support)
            draw_dim(ax, (L1, L2 - drop_l_m/2), (L1, L2 + drop_l_m/2), 
                     f"Drop: {drop_data['length']:.0f} cm", offset=0.5, is_vert=True, color='#1565c0', font_size=9)

        # Label S-01
        ax.text(L1/2, L2/2 - 0.3, "S-01", ha='center', fontsize=16, fontweight='bold', color='#37474f',
                bbox=dict(boxstyle="circle,pad=0.5", fc="white", ec="#37474f", alpha=1.0, zorder=5))
        
        margin = 1.5
        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_xlim(-margin, L1+margin)
        ax.set_ylim(-margin, L2+margin)
        st.pyplot(fig, use_container_width=True)

        # --- SECTION ---
        st.markdown("**2. SECTION A-A (Typical)**")
        fig_s, ax_s = plt.subplots(figsize=(10, 3))
        cut_w = 200
        
        ax_s.add_patch(patches.Rectangle((-cut_w/2, 0), cut_w, h_slab, fc='#ffffff', ec='black', hatch='///', lw=1.2))
        
        y_bot = 0
        if has_drop:
            dw = min(cut_w*0.6, drop_data['width'])
            ax_s.add_patch(patches.Rectangle((-dw/2, -h_drop), dw, h_drop, fc='#ffffff', ec='black', hatch='///', lw=1.2))
            y_bot = -h_drop
            draw_dim(ax_s, (dw/2+10, 0), (dw/2+10, -h_drop), f"{h_drop} cm", offset=0, is_vert=True, color='#1565c0')

        ax_s.add_patch(patches.Rectangle((-c1_w/2, y_bot-30), c1_w, 30, fc='#455a64', ec='black'))
        d_line = h_slab - cover - 0.6
        ax_s.plot([-cut_w/2+15, cut_w/2-15], [d_line, d_line], color='#d32f2f', lw=3)
        
        draw_dim(ax_s, (-cut_w/2-15, 0), (-cut_w/2-15, h_slab), f"h={h_slab:.0f}", offset=0, is_vert=True)
        draw_dim(ax_s, (cut_w/3, d_line), (cut_w/3, y_bot), f"d={d_eff:.2f}", offset=15, is_vert=True, color='#d32f2f')

        ax_s.set_aspect('equal')
        ax_s.axis('off')
        ax_s.set_ylim(y_bot-40, h_slab+30)
        st.pyplot(fig_s, use_container_width=True)

    with col_dat:
        html_content = ""
        html_content += '<div class="eng-sheet">'
        html_content += '<div class="eng-header">DESIGN DATA SHEET</div>'
        html_content += '<table class="eng-table">'
        
        html_content += get_row_html("1. GEOMETRY INFO", "", "", is_header=True)
        html_content += get_row_html("Slab Thickness (h)", f"{h_slab:.0f}", "cm")
        html_content += get_row_html("Effective Depth (d)", f"{d_eff:.2f}", "cm")
        html_content += get_row_html("Clear Cover", f"{cover:.1f}", "cm")
        html_content += get_row_html("Storey Height", f"{lc:.2f}", "m")
        
        html_content += get_row_html("2. DIMENSIONS", "", "", is_header=True)
        html_content += get_row_html("C-C Span X (Lx)", f"{L1:.2f}", "m")
        html_content += get_row_html("C-C Span Y (Ly)", f"{L2:.2f}", "m")
        # Add Clear Span to Data Sheet
        html_content += get_row_html("Clear Span X (Ln)", f"{Ln_x:.2f}", "m", is_highlight=True)
        html_content += get_row_html("Clear Span Y (Ln)", f"{Ln_y:.2f}", "m", is_highlight=True)
        
        html_content += get_row_html("Column Size", f"{c1_w:.0f} x {c2_w:.0f}", "cm")
        
        if has_drop:
            html_content += get_row_html("3. DROP PANEL SPEC", "", "", is_header=True)
            html_content += get_row_html("Drop Size (WxL)", f"{drop_data['width']:.0f}x{drop_data['length']:.0f}", "cm")
            html_content += get_row_html("Drop Thickness", f"+{h_drop:.0f}", "cm")

        html_content += get_row_html("4. MATERIALS", "", "", is_header=True)
        html_content += get_row_html("Concrete (fc')", f"{fc:.0f}", "ksc")
        html_content += get_row_html("Rebar (fy)", f"{fy:.0f}", "ksc")

        html_content += get_row_html("5. LOADS (ULS)", "", "", is_header=True)
        html_content += get_row_html("Live Load (LL)", f"{ll:.0f}", "kg/m²")
        html_content += get_row_html("FACTORED (Wu)", f"{wu:,.0f}", "kg/m²", is_highlight=True)
        
        html_content += '</table>'
        
        now_str = pd.Timestamp.now().strftime('%d-%b-%Y')
        html_content += f'<div class="eng-footer"><b>ENGINEER NOTES:</b><br>1. Ln = Clear span face-to-face.<br>2. Dimensions in [m] and [cm].<br>3. Date: {now_str}</div>'
        html_content += '</div>'

        st.markdown(html_content, unsafe_allow_html=True)
