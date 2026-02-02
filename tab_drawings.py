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
    style: 'standard' (arrows), 'clear' (face-to-face dots/ticks)
    """
    x1, y1 = p1
    x2, y2 = p2
    
    # Configuration based on orientation
    if is_vert:
        x1 += offset; x2 += offset
        ha, va, rot = 'center', 'center', 90
        # Text positioning
        sign = 1 if offset > 0 else -1
        txt_x = x1 + (0.35 * sign) 
        txt_pos = (txt_x, (y1+y2)/2)
    else:
        y1 += offset; y2 += offset
        ha, va, rot = 'center', 'center', 0
        # Text positioning
        sign = 1 if offset > 0 else -1
        txt_y = y1 + (0.35 * sign)
        txt_pos = ((x1+x2)/2, txt_y)

    # Extension Lines (The "Legs")
    # Make them slightly faint to not distract
    ext_kw = dict(color=color, lw=0.5, ls='-', alpha=0.5)
    
    # Draw legs from origin point to dimension line
    if is_vert:
        ax.plot([p1[0], x1], [p1[1], y1], **ext_kw)
        ax.plot([p2[0], x2], [p2[1], y2], **ext_kw)
    else:
        ax.plot([p1[0], x1], [p1[1], y1], **ext_kw)
        ax.plot([p2[0], x2], [p2[1], y2], **ext_kw)

    # Main Dimension Line
    arrow_style = '<|-|>' # Standard Architectural Tick
    if style == 'clear': 
        arrow_style = '|-|' # Butt ends for clear span
        
    ax.annotate('', xy=(x1, y1), xytext=(x2, y2),
                arrowprops=dict(arrowstyle=arrow_style, color=color, lw=0.8, mutation_scale=12))
    
    # Text Label with high-contrast background
    ax.text(txt_pos[0], txt_pos[1], text, 
            color=color, fontsize=font_size, ha=ha, va=va, rotation=rot, 
            fontfamily='monospace', fontweight='bold', zorder=20,
            bbox=dict(facecolor='white', alpha=1.0, edgecolor='none', pad=2.0))

# ==========================================
# 2. HELPER: HTML TABLE GENERATOR
# ==========================================
def get_row_html(label, value, unit, is_header=False, is_highlight=False, is_sub=False):
    """Generates a clean HTML row."""
    if is_header:
        return f"""
        <tr style="background-color: #37474f; color: white;">
            <td colspan="3" style="padding: 10px; font-weight: 700; font-size: 0.95rem; letter-spacing: 1px; border-top: 2px solid #000;">{label}</td>
        </tr>"""
    
    # Styling logic
    bg = "#e8f5e9" if is_highlight else "#ffffff" # Green tint for highlights
    if is_sub: bg = "#fafafa" # Grey tint for sub-items
    
    col_val = "#1b5e20" if is_highlight else "#000000"
    w_val = "800" if is_highlight else "600"
    font_size = "0.9rem"
    
    return f"""
    <tr style="background-color: {bg}; border-bottom: 1px solid #eceff1;">
        <td style="padding: 6px 12px; color: #455a64; font-weight: 500; font-size: {font_size};">{label}</td>
        <td style="padding: 6px 12px; text-align: right; color: {col_val}; font-weight: {w_val}; font-family: 'Consolas', monospace; font-size: {font_size};">{value}</td>
        <td style="padding: 6px 12px; color: #90a4ae; font-size: 0.8rem;">[{unit}]</td>
    </tr>"""

# ==========================================
# 3. MAIN RENDERER
# ==========================================
def render(L1, L2, c1_w, c2_w, h_slab, lc, cover, d_eff, 
           drop_data=None, moment_vals=None, 
           mat_props=None, loads=None):
    
    # --- 3.1 Data Preparation ---
    if drop_data is None: drop_data = {'has_drop': False, 'width': 0, 'length': 0, 'depth': 0}
    if mat_props is None: mat_props = {}
    if loads is None: loads = {}
    
    # Units: cm -> m
    c1_m, c2_m = c1_w/100.0, c2_w/100.0
    
    # Calculate Clear Spans (Ln)
    Ln_x = L1 - c1_m
    Ln_y = L2 - c2_m
    
    # Drop Data
    has_drop = drop_data.get('has_drop')
    drop_w_m = drop_data.get('width', 0)/100.0
    drop_l_m = drop_data.get('length', 0)/100.0
    h_drop = drop_data.get('depth', 0)
    
    # Props
    fc = mat_props.get('fc', 0)
    fy = mat_props.get('fy', 0)
    d_bar = mat_props.get('d_bar', 0)
    
    # Loads
    sdl = loads.get('SDL', 0)
    ll = loads.get('LL', 0)
    wu = loads.get('w_u', 0)

    # ==========================================
    # 3.2 CSS STYLING
    # ==========================================
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
        .sheet-table {
            width: 100%;
            border-collapse: collapse;
        }
        .sheet-footer {
            padding: 15px;
            background-color: #f5f5f5;
            border-top: 2px solid #263238;
            font-size: 0.75rem;
            color: #607d8b;
            line-height: 1.5;
        }
    </style>
    """, unsafe_allow_html=True)

    # ==========================================
    # 3.3 PLOTTING LAYOUT
    # ==========================================
    col_draw, col_data = st.columns([1.8, 1])

    # --- LEFT: ENGINEERING DRAWINGS ---
    with col_draw:
        st.markdown("##### 📐 PLAN VIEW (TOP)")
        
        # Setup Figure
        fig, ax = plt.subplots(figsize=(10, 8.5))
        
        # 1. Grid Lines (Faint Grey)
        ax.plot([-1, L1+1], [L2/2, L2/2], color='#cfd8dc', ls='-.', lw=1.0, zorder=0) # CL-X
        ax.plot([L1/2, L1/2], [-1, L2+1], color='#cfd8dc', ls='-.', lw=1.0, zorder=0) # CL-Y

        # 2. Slab Boundary (Main Object)
        ax.add_patch(patches.Rectangle((0, 0), L1, L2, fc='#ffffff', ec='#263238', lw=2.0, zorder=1))

        # 3. Columns & Drop Panels
        centers = [(0,0), (L1,0), (0,L2), (L1,L2)]
        for cx, cy in centers:
            # Drop Panel (Light Blue)
            if has_drop:
                ax.add_patch(patches.Rectangle((cx-drop_w_m/2, cy-drop_l_m/2), drop_w_m, drop_l_m, 
                                               fc='#e1f5fe', ec='#039be5', lw=1.0, ls='--', zorder=2))
            # Column (Dark Grey Solid)
            ax.add_patch(patches.Rectangle((cx-c1_m/2, cy-c2_m/2), c1_m, c2_m, 
                                           fc='#37474f', ec='black', zorder=5))

        # 4. DIMENSIONS
        
        # A. Center-to-Center (Outer Layer - Black)
        draw_dim(ax, (0, L2), (L1, L2), f"Lx = {L1:.2f} m", offset=1.2, is_vert=False, font_size=11)
        draw_dim(ax, (L1, 0), (L1, L2), f"Ly = {L2:.2f} m", offset=1.2, is_vert=True, font_size=11)
        
        # B. Clear Spans (Inner Layer - Face-to-Face - Green)
        # Note: Offsets are negative to put them "inside" or opposite side
        draw_dim(ax, (c1_m/2, 0), (L1 - c1_m/2, 0), f"Ln = {Ln_x:.2f} m", 
                 offset=-1.0, is_vert=False, color='#2e7d32', font_size=11, style='clear')
        draw_dim(ax, (0, c2_m/2), (0, L2 - c2_m/2), f"Ln = {Ln_y:.2f} m", 
                 offset=-1.0, is_vert=True, color='#2e7d32', font_size=11, style='clear')

        # C. Drop Panel Dimensions (Detail - Blue)
        if has_drop:
            # Tell dimensions at the top-right corner support
            # Drop Width
            draw_dim(ax, (L1 - drop_w_m/2, L2), (L1 + drop_w_m/2, L2), 
                     f"Drop: {drop_data['width']:.0f} cm", offset=0.5, color='#0277bd', font_size=9)
            # Drop Length
            draw_dim(ax, (L1, L2 - drop_l_m/2), (L1, L2 + drop_l_m/2), 
                     f"Drop: {drop_data['length']:.0f} cm", offset=0.5, is_vert=True, color='#0277bd', font_size=9)

        # 5. Label S-01
        ax.text(L1/2, L2/2 - 0.4, "S-01", ha='center', fontsize=18, fontweight='bold', color='#263238',
                bbox=dict(boxstyle="circle,pad=0.4", fc="white", ec="#263238", lw=1.5, zorder=10))

        # View Settings
        margin = 1.6
        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_xlim(-margin, L1+margin)
        ax.set_ylim(-margin, L2+margin)
        st.pyplot(fig, use_container_width=True)

        # --- SECTION VIEW ---
        st.markdown("##### 🏗️ SECTION A-A (TYPICAL)")
        fig_s, ax_s = plt.subplots(figsize=(10, 3.5))
        cut_w = 220 # Visual width in cm
        
        # Slab Concrete (Hatched)
        ax_s.add_patch(patches.Rectangle((-cut_w/2, 0), cut_w, h_slab, 
                                       fc='#ffffff', ec='black', hatch='///', lw=1.2))
        
        y_bot = 0
        if has_drop:
            dw = min(cut_w*0.6, drop_data['width'])
            # Drop Concrete
            ax_s.add_patch(patches.Rectangle((-dw/2, -h_drop), dw, h_drop, 
                                           fc='#ffffff', ec='black', hatch='///', lw=1.2))
            y_bot = -h_drop
            # Drop Dim
            draw_dim(ax_s, (dw/2+12, 0), (dw/2+12, -h_drop), f"{h_drop} cm", offset=0, is_vert=True, color='#0277bd')

        # Column
        ax_s.add_patch(patches.Rectangle((-c1_w/2, y_bot-35), c1_w, 35, fc='#546e7a', ec='black'))
        
        # Main Rebar (Red)
        d_line = h_slab - cover - 0.6
        ax_s.plot([-cut_w/2+20, cut_w/2-20], [d_line, d_line], color='#d32f2f', lw=3.0, label='Main Rebar')
        
        # Vertical Dimensions
        draw_dim(ax_s, (-cut_w/2-20, 0), (-cut_w/2-20, h_slab), f"h={h_slab:.0f}", offset=0, is_vert=True)
        draw_dim(ax_s, (cut_w/3, d_line), (cut_w/3, y_bot), f"d={d_eff:.2f}", offset=20, is_vert=True, color='#d32f2f')

        ax_s.set_aspect('equal')
        ax_s.axis('off')
        ax_s.set_ylim(y_bot-45, h_slab+35)
        st.pyplot(fig_s, use_container_width=True)

    # --- RIGHT: DATA SHEET ---
    with col_data:
        # Construct HTML
        html = ""
        html += '<div class="sheet-container">'
        html += '<div class="sheet-header">Design Data Sheet</div>'
        html += '<table class="sheet-table">'
        
        # 1. Geometry
        html += get_row_html("1. GEOMETRY", "", "", is_header=True)
        html += get_row_html("Thickness (h)", f"{h_slab:.0f}", "cm")
        html += get_row_html("Covering", f"{cover:.1f}", "cm")
        html += get_row_html("Eff. Depth (d)", f"{d_eff:.2f}", "cm")
        html += get_row_html("Storey Height", f"{lc:.2f}", "m")
        
        # 2. Dimensions
        html += get_row_html("2. PLAN DIMENSIONS", "", "", is_header=True)
        html += get_row_html("C-C Span X", f"{L1:.2f}", "m")
        html += get_row_html("C-C Span Y", f"{L2:.2f}", "m")
        html += get_row_html("Clear Span X (Ln)", f"{Ln_x:.2f}", "m", is_highlight=True)
        html += get_row_html("Clear Span Y (Ln)", f"{Ln_y:.2f}", "m", is_highlight=True)
        html += get_row_html("Column Size", f"{c1_w:.0f} x {c2_w:.0f}", "cm")
        
        # 3. Drop Panel
        if has_drop:
            html += get_row_html("3. DROP PANEL", "", "", is_header=True)
            html += get_row_html("Size (WxL)", f"{drop_data['width']:.0f}x{drop_data['length']:.0f}", "cm")
            html += get_row_html("Depth", f"+{h_drop:.0f}", "cm")
            html += get_row_html("Total Thick.", f"{h_slab+h_drop:.0f}", "cm")

        # 4. Materials
        html += get_row_html("4. MATERIALS", "", "", is_header=True)
        html += get_row_html("Concrete (fc')", f"{fc:.0f}", "ksc")
        html += get_row_html("Rebar (fy)", f"{fy:.0f}", "ksc")
        html += get_row_html("Main Bar", f"DB{d_bar}", "mm")

        # 5. Loads
        html += get_row_html("5. LOADS (ULS)", "", "", is_header=True)
        html += get_row_html("SDL + Self", f"{sdl + (h_slab/100*2400):.0f}", "kg/m²")
        html += get_row_html("Live Load", f"{ll:.0f}", "kg/m²")
        html += get_row_html("FACTORED (Wu)", f"{wu:,.0f}", "kg/m²", is_highlight=True)
        
        html += '</table>'
        
        # Footer
        now_str = pd.Timestamp.now().strftime('%d-%b-%Y')
        html += f"""
        <div class="sheet-footer">
            <b>📝 ENGINEER NOTES:</b><br>
            • All dimensions are in meters [m] unless noted as [cm].<br>
            • Ln = Clear span (face-to-face of supports).<br>
            • Design based on ACI 318-19 / EIT Standard.<br>
            • Date: {now_str}
        </div>
        """
        html += '</div>'

        st.markdown(html, unsafe_allow_html=True)
