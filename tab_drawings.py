# tab_drawings.py
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pandas as pd

# ==========================================
# 1. HELPER: PROFESSIONAL DIMENSIONS
# ==========================================
def draw_dim(ax, p1, p2, text, offset=0, color='#000000', is_vert=False, font_size=10, style='standard'):
    """
    Render architectural dimensions.
    """
    x1, y1 = p1
    x2, y2 = p2
    
    # Configuration based on orientation
    if is_vert:
        x1 += offset; x2 += offset
        ha, va, rot = 'center', 'center', 90
        sign = 1 if offset > 0 else -1
        txt_x = x1 + (0.35 * sign) 
        txt_pos = (txt_x, (y1+y2)/2)
    else:
        y1 += offset; y2 += offset
        ha, va, rot = 'center', 'center', 0
        sign = 1 if offset > 0 else -1
        txt_y = y1 + (0.35 * sign)
        txt_pos = ((x1+x2)/2, txt_y)

    # Extension Lines
    ext_kw = dict(color=color, lw=0.5, ls='-', alpha=0.5)
    
    if is_vert:
        ax.plot([p1[0], x1], [p1[1], y1], **ext_kw)
        ax.plot([p2[0], x2], [p2[1], y2], **ext_kw)
    else:
        ax.plot([p1[0], x1], [p1[1], y1], **ext_kw)
        ax.plot([p2[0], x2], [p2[1], y2], **ext_kw)

    # Main Dimension Line
    arrow_style = '<|-|>'
    if style == 'clear': arrow_style = '|-|' # Style for clear span
        
    ax.annotate('', xy=(x1, y1), xytext=(x2, y2),
                arrowprops=dict(arrowstyle=arrow_style, color=color, lw=0.8, mutation_scale=12))
    
    # Text Label
    ax.text(txt_pos[0], txt_pos[1], text, 
            color=color, fontsize=font_size, ha=ha, va=va, rotation=rot, 
            fontfamily='monospace', fontweight='bold', zorder=20,
            bbox=dict(facecolor='white', alpha=1.0, edgecolor='none', pad=2.0))

# ==========================================
# 2. HELPER: BOUNDARY LABELS
# ==========================================
def draw_boundary_label(ax, x, y, text, align='center', rotation=0):
    """Draws text indicating continuity or edge."""
    ax.text(x, y, text, ha='center', va='center', rotation=rotation,
            fontsize=9, color='#78909c', fontweight='bold',
            bbox=dict(facecolor='#eceff1', edgecolor='none', alpha=0.7, pad=2))

# ==========================================
# 3. HELPER: HTML TABLE
# ==========================================
def get_row_html(label, value, unit, is_header=False, is_highlight=False, is_sub=False):
    if is_header:
        return f"""
        <tr style="background-color: #37474f; color: white;">
            <td colspan="3" style="padding: 10px; font-weight: 700; font-size: 0.95rem; letter-spacing: 1px; border-top: 2px solid #000;">{label}</td>
        </tr>"""
    
    bg = "#e8f5e9" if is_highlight else "#ffffff"
    col_val = "#1b5e20" if is_highlight else "#000000"
    w_val = "800" if is_highlight else "600"
    
    return f"""
    <tr style="background-color: {bg}; border-bottom: 1px solid #eceff1;">
        <td style="padding: 6px 12px; color: #455a64; font-weight: 500; font-size: 0.9rem;">{label}</td>
        <td style="padding: 6px 12px; text-align: right; color: {col_val}; font-weight: {w_val}; font-family: 'Consolas', monospace; font-size: 0.9rem;">{value}</td>
        <td style="padding: 6px 12px; color: #90a4ae; font-size: 0.8rem;">[{unit}]</td>
    </tr>"""

# ==========================================
# 4. MAIN RENDERER
# ==========================================
def render(L1, L2, c1_w, c2_w, h_slab, lc, cover, d_eff, 
           drop_data=None, moment_vals=None, 
           mat_props=None, loads=None, col_type="interior"): # Added col_type
    
    # --- 4.1 Data Prep ---
    if drop_data is None: drop_data = {'has_drop': False, 'width': 0, 'length': 0, 'depth': 0}
    if mat_props is None: mat_props = {}
    if loads is None: loads = {}
    
    c1_m, c2_m = c1_w/100.0, c2_w/100.0
    Ln_x = L1 - c1_m
    Ln_y = L2 - c2_m
    
    has_drop = drop_data.get('has_drop')
    drop_w_m = drop_data.get('width', 0)/100.0
    drop_l_m = drop_data.get('length', 0)/100.0
    h_drop = drop_data.get('depth', 0)
    
    fc = mat_props.get('fc', 0)
    fy = mat_props.get('fy', 0)
    d_bar = mat_props.get('d_bar', 0)
    sdl, ll, wu = loads.get('SDL', 0), loads.get('LL', 0), loads.get('w_u', 0)

    # --- 4.2 Styles ---
    st.markdown("""
    <style>
        .sheet-container {
            font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            border: 1px solid #cfd8dc;
            background-color: #ffffff;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            margin-bottom: 2rem;
        }
        .sheet-header {
            background-color: #263238;
            color: #ffffff;
            padding: 15px;
            text-align: center;
            font-weight: 800;
            font-size: 1.1rem;
            letter-spacing: 1.2px;
            text-transform: uppercase;
        }
        .sheet-table { width: 100%; border-collapse: collapse; }
        .sheet-footer {
            padding: 15px; background-color: #f5f5f5; border-top: 2px solid #263238;
            font-size: 0.75rem; color: #607d8b; line-height: 1.5;
        }
    </style>
    """, unsafe_allow_html=True)

    # --- 4.3 Layout ---
    col_draw, col_data = st.columns([1.8, 1])

    # === LEFT: ENGINEERING DRAWINGS ===
    with col_draw:
        # ------------------------------------
        # A. PLAN VIEW
        # ------------------------------------
        st.markdown(f"##### 📐 PLAN VIEW ({col_type.upper()} PANEL)")
        fig, ax = plt.subplots(figsize=(10, 8.5))
        
        # Grid Lines
        ax.plot([-1, L1+1], [L2/2, L2/2], color='#cfd8dc', ls='-.', lw=1.0)
        ax.plot([L1/2, L1/2], [-1, L2+1], color='#cfd8dc', ls='-.', lw=1.0)

        # Slab
        ax.add_patch(patches.Rectangle((0, 0), L1, L2, fc='#ffffff', ec='#263238', lw=2.0, zorder=1))

        # Supports
        centers = [(0,0), (L1,0), (0,L2), (L1,L2)]
        for cx, cy in centers:
            if has_drop:
                ax.add_patch(patches.Rectangle((cx-drop_w_m/2, cy-drop_l_m/2), drop_w_m, drop_l_m, 
                                               fc='#e1f5fe', ec='#039be5', lw=1.0, ls='--', zorder=2))
            ax.add_patch(patches.Rectangle((cx-c1_m/2, cy-c2_m/2), c1_m, c2_m, 
                                           fc='#37474f', ec='black', zorder=5))

        # --- BOUNDARY CONTEXT LABELS (Logic for Interior/Edge/Corner) ---
        # Assumptions: 
        # - User is designing the panel defined by Lx, Ly.
        # - We label the boundaries of this panel.
        
        lbl_top = "CONTINUOUS"
        lbl_bot = "CONTINUOUS"
        lbl_left = "CONTINUOUS"
        lbl_right = "CONTINUOUS"
        
        if col_type == 'edge':
            # Assume Left Edge is the building edge for visualization
            lbl_left = "BUILDING EDGE" 
        elif col_type == 'corner':
            # Assume Top-Left Corner
            lbl_left = "BUILDING EDGE"
            lbl_top = "BUILDING EDGE"

        # Draw Context Labels (Outside the slab)
        draw_boundary_label(ax, L1/2, L2 + 0.3, lbl_top)       # Top
        draw_boundary_label(ax, L1/2, -0.3, lbl_bot)           # Bottom
        draw_boundary_label(ax, -0.3, L2/2, lbl_left, rotation=90)  # Left
        draw_boundary_label(ax, L1 + 0.3, L2/2, lbl_right, rotation=90) # Right

        # --- DIMENSIONS ---
        # A. Center-to-Center (Black)
        draw_dim(ax, (0, L2), (L1, L2), f"Lx = {L1:.2f} m", offset=1.2, is_vert=False, font_size=11)
        draw_dim(ax, (L1, 0), (L1, L2), f"Ly = {L2:.2f} m", offset=1.2, is_vert=True, font_size=11)
        
        # B. Clear Spans (Green)
        draw_dim(ax, (c1_m/2, 0), (L1 - c1_m/2, 0), f"Ln = {Ln_x:.2f} m", 
                 offset=-1.0, is_vert=False, color='#2e7d32', font_size=11, style='clear')
        draw_dim(ax, (0, c2_m/2), (0, L2 - c2_m/2), f"Ln = {Ln_y:.2f} m", 
                 offset=-1.0, is_vert=True, color='#2e7d32', font_size=11, style='clear')

        # C. Drop Panel (Blue)
        if has_drop:
            draw_dim(ax, (L1 - drop_w_m/2, L2), (L1 + drop_w_m/2, L2), 
                     f"Drop: {drop_data['width']:.0f} cm", offset=0.5, color='#0277bd', font_size=9)
            draw_dim(ax, (L1, L2 - drop_l_m/2), (L1, L2 + drop_l_m/2), 
                     f"Drop: {drop_data['length']:.0f} cm", offset=0.5, is_vert=True, color='#0277bd', font_size=9)

        # Label S-01
        ax.text(L1/2, L2/2 - 0.4, "S-01", ha='center', fontsize=18, fontweight='bold', color='#263238',
                bbox=dict(boxstyle="circle,pad=0.4", fc="white", ec="#263238", lw=1.5, zorder=10))

        margin = 1.6
        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_xlim(-margin, L1+margin)
        ax.set_ylim(-margin, L2+margin)
        st.pyplot(fig, use_container_width=True)

        # ------------------------------------
        # B. SECTION VIEW
        # ------------------------------------
        st.markdown("##### 🏗️ SECTION A-A (STOREY HEIGHT)")
        
        # Increase figure height to accommodate Storey Height
        fig_s, ax_s = plt.subplots(figsize=(10, 5)) 
        
        # Scale Factors for Visuals
        cut_w = 220 
        col_h_draw = 180 # Arbitrary visual height for column below
        
        # 1. Slab Concrete
        ax_s.add_patch(patches.Rectangle((-cut_w/2, 0), cut_w, h_slab, 
                                       fc='#ffffff', ec='black', hatch='///', lw=1.2))
        
        # 2. Drop Panel
        y_bot = 0
        if has_drop:
            dw = min(cut_w*0.6, drop_data['width'])
            ax_s.add_patch(patches.Rectangle((-dw/2, -h_drop), dw, h_drop, 
                                           fc='#ffffff', ec='black', hatch='///', lw=1.2))
            y_bot = -h_drop
            draw_dim(ax_s, (dw/2+12, 0), (dw/2+12, -h_drop), f"{h_drop} cm", offset=0, is_vert=True, color='#0277bd')

        # 3. Column (Extended Downwards)
        # Draw column extending down to represent storey height
        ax_s.add_patch(patches.Rectangle((-c1_w/2, -col_h_draw), c1_w, col_h_draw + y_bot, 
                                         fc='#546e7a', ec='black'))
        
        # 4. Floor Line Below (Break Line)
        ax_s.plot([-c1_w, c1_w], [-col_h_draw, -col_h_draw], color='black', lw=1.5, ls='--')
        ax_s.text(0, -col_h_draw - 15, "LOWER FLOOR LEVEL", ha='center', fontsize=9, color='#455a64')

        # 5. Storey Height Dimension (lc)
        # From Top of Slab to Top of Lower Floor (approximated visually as the break line)
        # Note: lc is usually floor-to-floor.
        draw_dim(ax_s, (-c1_w/2 - 40, 0), (-c1_w/2 - 40, -col_h_draw), 
                 f"Storey Height: {lc:.2f} m", offset=0, is_vert=True, color='#e65100', font_size=11)

        # 6. Rebar
        d_line = h_slab - cover - 0.6
        ax_s.plot([-cut_w/2+20, cut_w/2-20], [d_line, d_line], color='#d32f2f', lw=3.0, label='Main Rebar')
        
        # 7. Other Dims
        draw_dim(ax_s, (-cut_w/2-20, 0), (-cut_w/2-20, h_slab), f"h={h_slab:.0f}", offset=0, is_vert=True)
        draw_dim(ax_s, (cut_w/3, d_line), (cut_w/3, y_bot), f"d={d_eff:.2f}", offset=20, is_vert=True, color='#d32f2f')

        ax_s.set_aspect('equal')
        ax_s.axis('off')
        ax_s.set_ylim(-col_h_draw - 30, h_slab + 35)
        st.pyplot(fig_s, use_container_width=True)

    # === RIGHT: DATA SHEET ===
    with col_data:
        html = ""
        html += '<div class="sheet-container">'
        html += '<div class="sheet-header">Design Data Sheet</div>'
        html += '<table class="sheet-table">'
        
        # Geometry
        html += get_row_html("1. GEOMETRY", "", "", is_header=True)
        html += get_row_html("Type", f"{col_type.upper()}", "-", is_highlight=True)
        html += get_row_html("Thickness (h)", f"{h_slab:.0f}", "cm")
        html += get_row_html("Covering", f"{cover:.1f}", "cm")
        html += get_row_html("Eff. Depth (d)", f"{d_eff:.2f}", "cm")
        html += get_row_html("Storey Height", f"{lc:.2f}", "m", is_highlight=True)
        
        # Dimensions
        html += get_row_html("2. DIMENSIONS", "", "", is_header=True)
        html += get_row_html("C-C Span X", f"{L1:.2f}", "m")
        html += get_row_html("C-C Span Y", f"{L2:.2f}", "m")
        html += get_row_html("Clear Span X (Ln)", f"{Ln_x:.2f}", "m", is_highlight=True)
        html += get_row_html("Clear Span Y (Ln)", f"{Ln_y:.2f}", "m", is_highlight=True)
        html += get_row_html("Column Size", f"{c1_w:.0f} x {c2_w:.0f}", "cm")
        
        if has_drop:
            html += get_row_html("3. DROP PANEL", "", "", is_header=True)
            html += get_row_html("Size (WxL)", f"{drop_data['width']:.0f}x{drop_data['length']:.0f}", "cm")
            html += get_row_html("Depth", f"+{h_drop:.0f}", "cm")
            html += get_row_html("Total Thick.", f"{h_slab+h_drop:.0f}", "cm")

        # Materials & Loads
        html += get_row_html("4. MATERIALS & LOADS", "", "", is_header=True)
        html += get_row_html("Concrete (fc')", f"{fc:.0f}", "ksc")
        html += get_row_html("Rebar (fy)", f"{fy:.0f}", "ksc")
        html += get_row_html("FACTORED (Wu)", f"{wu:,.0f}", "kg/m²", is_highlight=True)
        
        html += '</table>'
        
        now_str = pd.Timestamp.now().strftime('%d-%b-%Y')
        html += f"""
        <div class="sheet-footer">
            <b>📝 ENGINEER NOTES:</b><br>
            • Panel Type: <b>{col_type.upper()}</b> indicated by boundary labels.<br>
            • Ln = Clear span face-to-face.<br>
            • Date: {now_str}
        </div>
        """
        html += '</div>'

        st.markdown(html, unsafe_allow_html=True)
