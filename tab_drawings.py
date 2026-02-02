# tab_drawings.py
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pandas as pd

# ==========================================
# 1. HELPER: CAD STYLING & DIMENSIONS
# ==========================================
def draw_dim(ax, p1, p2, text, offset=0, color='#000000', is_vert=False, font_size=10):
    """
    Render architectural dimensions with units and precision.
    """
    x1, y1 = p1
    x2, y2 = p2
    
    # Calculate positions based on offset
    if is_vert:
        # Vertical Dimension (e.g., Ly)
        x1 += offset; x2 += offset
        ha, va, rot = 'center', 'center', 90
        # Text position: Shifted slightly "outward" based on offset direction
        sign = 1 if offset > 0 else -1
        txt_x = x1 + (0.25 * sign) 
        txt_pos = (txt_x, (y1+y2)/2)
        
        # Extension Lines (Legs)
        ax.plot([p1[0], x1], [p1[1], y1], color=color, lw=0.4, ls='-', alpha=0.6) # Leg 1
        ax.plot([p2[0], x2], [p2[1], y2], color=color, lw=0.4, ls='-', alpha=0.6) # Leg 2

    else:
        # Horizontal Dimension (e.g., Lx)
        y1 += offset; y2 += offset
        ha, va, rot = 'center', 'center', 0
        # Text position: Shifted slightly "up/down"
        sign = 1 if offset > 0 else -1
        txt_y = y1 + (0.25 * sign)
        txt_pos = ((x1+x2)/2, txt_y)

        # Extension Lines (Legs)
        ax.plot([p1[0], x1], [p1[1], y1], color=color, lw=0.4, ls='-', alpha=0.6) # Leg 1
        ax.plot([p2[0], x2], [p2[1], y2], color=color, lw=0.4, ls='-', alpha=0.6) # Leg 2

    # Main Dimension Line with Arrowheads
    ax.annotate('', xy=(x1, y1), xytext=(x2, y2),
                arrowprops=dict(arrowstyle='<|-|>', color=color, lw=0.7, mutation_scale=12))
    
    # Text with Background (Prevent Overlapping)
    ax.text(txt_pos[0], txt_pos[1], text, 
            color=color, fontsize=font_size, ha=ha, va=va, rotation=rot, 
            fontfamily='monospace', fontweight='bold', zorder=15,
            bbox=dict(facecolor='white', alpha=0.9, edgecolor='none', pad=1.5))

# ==========================================
# 2. HELPER: HTML ROW GENERATOR
# ==========================================
def get_row_html(label, value, unit, is_header=False, is_highlight=False):
    """Returns a single line of HTML for the table."""
    if is_header:
        return f'<tr style="background-color: #263238; color: white;"><td colspan="3" style="padding: 8px 10px; font-weight: bold; font-size: 0.9rem; border-top: 2px solid #000;">{label}</td></tr>'
    
    bg = "#ffebee" if is_highlight else "#ffffff"
    col_val = "#b71c1c" if is_highlight else "#000000"
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
    
    # Convert Units
    c1_m, c2_m = c1_w/100.0, c2_w/100.0
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

    # ------------------------------------------
    # LEFT COLUMN: ENGINEERING DRAWINGS
    # ------------------------------------------
    with col_gfx:
        st.markdown("**1. PLAN VIEW @ S-01**")
        fig, ax = plt.subplots(figsize=(10, 7.5))
        
        # 1. Grid Lines (Centerlines)
        ax.plot([-1, L1+1], [L2/2, L2/2], color='#b0bec5', ls='-.', lw=0.6) # X-CL
        ax.plot([L1/2, L1/2], [-1, L2+1], color='#b0bec5', ls='-.', lw=0.6) # Y-CL

        # 2. Slab Boundary (Span Lx, Ly)
        ax.add_patch(patches.Rectangle((0, 0), L1, L2, fc='#fafafa', ec='#37474f', lw=1.5))

        # 3. Columns & Drop Panels (Draw at all 4 corners)
        centers = [(0,0), (L1,0), (0,L2), (L1,L2)]
        for cx, cy in centers:
            # Draw Drop Panel
            if has_drop:
                ax.add_patch(patches.Rectangle((cx-drop_w_m/2, cy-drop_l_m/2), drop_w_m, drop_l_m, 
                                               fc='#e3f2fd', ec='#1976d2', lw=1, ls='--', zorder=2))
            # Draw Column
            ax.add_patch(patches.Rectangle((cx-c1_m/2, cy-c2_m/2), c1_m, c2_m, 
                                           fc='#263238', ec='black', zorder=3))

        # 4. DIMENSIONS (Units Included)
        # Main Spans (Outer Layer)
        draw_dim(ax, (0, L2), (L1, L2), f"Lx = {L1:.2f} m", offset=1.2, is_vert=False, font_size=12) # Top
        draw_dim(ax, (L1, 0), (L1, L2), f"Ly = {L2:.2f} m", offset=1.2, is_vert=True, font_size=12)  # Right
        
        # Drop Panel Dimensions (Inner Layer - At Top-Right Corner Support)
        if has_drop:
            # Drop Width (Horizontal) -> Tell near the support
            # Use offset closer than the main span (e.g. 0.6)
            draw_dim(ax, (L1 - drop_w_m/2, L2), (L1 + drop_w_m/2, L2), 
                     f"Drop W: {drop_data['width']:.0f} cm", offset=0.6, color='#1565c0', font_size=9)
            
            # Drop Length (Vertical) -> Tell near the support
            draw_dim(ax, (L1, L2 - drop_l_m/2), (L1, L2 + drop_l_m/2), 
                     f"Drop L: {drop_data['length']:.0f} cm", offset=0.6, is_vert=True, color='#1565c0', font_size=9)

        # 5. Label S-01 (Center)
        ax.text(L1/2, L2/2 - 0.3, "S-01", ha='center', fontsize=16, fontweight='bold', color='#37474f',
                bbox=dict(boxstyle="circle,pad=0.5", fc="white", ec="#37474f", alpha=1.0, zorder=5))
        
        # View Settings
        margin = 1.5
        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_xlim(-margin, L1+margin)
        ax.set_ylim(-margin, L2+margin)
        st.pyplot(fig, use_container_width=True)

        # --- SECTION A-A ---
        st.markdown("**2. SECTION A-A (Typical)**")
        fig_s, ax_s = plt.subplots(figsize=(10, 3))
        cut_w = 200 # Width of section graphic (cm)
        
        # Slab Concrete
        ax_s.add_patch(patches.Rectangle((-cut_w/2, 0), cut_w, h_slab, 
                                       fc='#ffffff', ec='black', hatch='///', lw=1.2))
        
        # Drop Panel & Column
        y_bot = 0
        if has_drop:
            dw = min(cut_w*0.6, drop_data['width'])
            # Drop Concrete
            ax_s.add_patch(patches.Rectangle((-dw/2, -h_drop), dw, h_drop, 
                                           fc='#ffffff', ec='black', hatch='///', lw=1.2))
            y_bot = -h_drop
            # Drop Depth Dimension
            draw_dim(ax_s, (dw/2+10, 0), (dw/2+10, -h_drop), f"{h_drop} cm", offset=0, is_vert=True, color='#1565c0')

        # Column Support
        ax_s.add_patch(patches.Rectangle((-c1_w/2, y_bot-30), c1_w, 30, fc='#455a64', ec='black'))
        
        # Rebar Line
        d_line = h_slab - cover - 0.6
        ax_s.plot([-cut_w/2+15, cut_w/2-15], [d_line, d_line], color='#d32f2f', lw=3, label='Main Rebar')
        
        # Vertical Dimensions
        draw_dim(ax_s, (-cut_w/2-15, 0), (-cut_w/2-15, h_slab), f"h={h_slab:.0f} cm", offset=0, is_vert=True)
        draw_dim(ax_s, (cut_w/3, d_line), (cut_w/3, y_bot), f"d={d_eff:.2f} cm", offset=15, is_vert=True, color='#d32f2f')

        ax_s.set_aspect('equal')
        ax_s.axis('off')
        ax_s.set_ylim(y_bot-40, h_slab+30)
        st.pyplot(fig_s, use_container_width=True)

    # ------------------------------------------
    # RIGHT COLUMN: SPECIFICATION SHEET
    # ------------------------------------------
    with col_dat:
        html_content = ""
        html_content += '<div class="eng-sheet">'
        html_content += '<div class="eng-header">DESIGN DATA SHEET</div>'
        html_content += '<table class="eng-table">'
        
        # 1. Geometry
        html_content += get_row_html("1. GEOMETRY INFO", "", "", is_header=True)
        html_content += get_row_html("Slab Thickness (h)", f"{h_slab:.0f}", "cm")
        html_content += get_row_html("Clear Cover", f"{cover:.1f}", "cm")
        html_content += get_row_html("Effective Depth (d)", f"{d_eff:.2f}", "cm")
        html_content += get_row_html("Storey Height", f"{lc:.2f}", "m")
        
        # 2. Dimensions
        html_content += get_row_html("2. PLAN DIMENSIONS", "", "", is_header=True)
        html_content += get_row_html("Span Length (Lx)", f"{L1:.2f}", "m")
        html_content += get_row_html("Span Length (Ly)", f"{L2:.2f}", "m")
        html_content += get_row_html("Column Size X", f"{c1_w:.0f}", "cm")
        html_content += get_row_html("Column Size Y", f"{c2_w:.0f}", "cm")
        
        # 3. Drop Panel
        if has_drop:
            html_content += get_row_html("3. DROP PANEL SPEC", "", "", is_header=True)
            html_content += get_row_html("Drop Depth", f"+{h_drop:.0f}", "cm")
            html_content += get_row_html("Total Thick.", f"{h_slab+h_drop:.0f}", "cm")
            html_content += get_row_html("Drop Size (WxL)", f"{drop_data['width']:.0f}x{drop_data['length']:.0f}", "cm")

        # 4. Materials
        html_content += get_row_html("4. MATERIAL PROPS", "", "", is_header=True)
        html_content += get_row_html("Concrete (fc')", f"{fc:.0f}", "ksc")
        html_content += get_row_html("Rebar Yield (fy)", f"{fy:.0f}", "ksc")
        html_content += get_row_html("Bar Diameter", f"DB{d_bar}", "mm")

        # 5. Loads
        html_content += get_row_html("5. DESIGN LOADS (ULS)", "", "", is_header=True)
        html_content += get_row_html("Superimposed DL", f"{sdl:.0f}", "kg/m²")
        html_content += get_row_html("Live Load (LL)", f"{ll:.0f}", "kg/m²")
        w_self = (h_slab/100)*2400
        html_content += get_row_html("Self Weight", f"{w_self:.0f}", "kg/m²")
        html_content += get_row_html("FACTORED (Wu)", f"{wu:,.0f}", "kg/m²", is_highlight=True)
        
        html_content += '</table>'
        
        # Footer
        now_str = pd.Timestamp.now().strftime('%d-%b-%Y %H:%M')
        html_content += f"""
        <div class="eng-footer">
            <b>📝 ENGINEER NOTES:</b><br>
            1. Dimensions in [m] for spans, [cm] for sections.<br>
            2. Concrete strength is cylinder strength.<br>
            3. Reference Code: ACI 318-19 / EIT Standard.<br>
            4. Generated Date: {now_str}
        </div>
        """
        html_content += '</div>'

        st.markdown(html_content, unsafe_allow_html=True)
