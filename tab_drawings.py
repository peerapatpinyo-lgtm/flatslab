# tab_drawings.py
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# ==========================================
# 1. HELPER: CAD STYLING & DIMENSIONS
# ==========================================
def draw_dim(ax, p1, p2, text, offset=0, color='#000000', is_vert=False, font_size=11):
    """
    Draws a professional architectural dimension line.
    """
    x1, y1 = p1
    x2, y2 = p2
    
    # Calculate text and line positions with precision
    if is_vert:
        x1 += offset; x2 += offset
        ha, va, rot = 'right' if offset < 0 else 'left', 'center', 90
        # Text positioning with slight padding
        txt_x = x1 - 0.15 if offset < 0 else x1 + 0.15
        txt_pos = (txt_x, (y1+y2)/2)
    else:
        y1 += offset; y2 += offset
        ha, va, rot = 'center', 'bottom' if offset > 0 else 'top', 0
        # Text positioning with slight padding
        txt_y = y1 + 0.15 if offset > 0 else y1 - 0.15
        txt_pos = ((x1+x2)/2, txt_y)

    # 1. Main Dimension Line with Architectural Ticks
    ax.annotate('', xy=(x1, y1), xytext=(x2, y2),
                arrowprops=dict(arrowstyle='<|-|>', color=color, lw=0.8, mutation_scale=15))
    
    # 2. Extension Lines (Thin, lighter color)
    ext_style = dict(color=color, lw=0.4, ls='-', alpha=0.5)
    if is_vert:
        ax.plot([p1[0], x1], [p1[1], y1], **ext_style)
        ax.plot([p2[0], x2], [p2[1], y2], **ext_style)
    else:
        ax.plot([p1[0], x1], [p1[1], y1], **ext_style)
        ax.plot([p2[0], x2], [p2[1], y2], **ext_style)

    # 3. Text Label with High-Contrast Background (Opaque Box)
    ax.text(txt_pos[0], txt_pos[1], text, 
            color=color, fontsize=font_size, ha=ha, va=va, rotation=rot, 
            fontfamily='monospace', fontweight='bold', zorder=10,
            bbox=dict(facecolor='white', alpha=1.0, edgecolor='none', pad=2))

# ==========================================
# 2. HELPER: HTML ROW GENERATOR
# ==========================================
def cad_row(label, value, unit, is_header=False, is_highlight=False):
    """Generates a clean HTML table row."""
    if is_header:
        return f"""
        <tr style="background-color: #2c3e50; color: #ffffff;">
            <td colspan="3" style="padding: 8px 10px; font-weight: 700; text-transform: uppercase; font-size: 0.85rem; letter-spacing: 0.5px; border-top: 1px solid #000;">{label}</td>
        </tr>
        """
    
    bg_color = "#ffebee" if is_highlight else "#ffffff"
    text_color = "#b71c1c" if is_highlight else "#000000"
    weight = "800" if is_highlight else "600"
    
    return f"""
    <tr style="background-color: {bg_color}; border-bottom: 1px solid #e0e0e0;">
        <td style="padding: 6px 12px; font-weight: 500; color: #455a64; width: 55%;">{label}</td>
        <td style="padding: 6px 12px; text-align: right; font-family: 'Consolas', 'Monaco', monospace; font-weight: {weight}; color: {text_color}; width: 25%;">{value}</td>
        <td style="padding: 6px 12px; text-align: left; color: #78909c; font-size: 0.75rem; width: 20%;">[{unit}]</td>
    </tr>
    """

# ==========================================
# 3. MAIN RENDER FUNCTION
# ==========================================
def render(L1, L2, c1_w, c2_w, h_slab, lc, cover, d_eff, 
           drop_data=None, moment_vals=None, 
           mat_props=None, loads=None):
    
    # --- 1. Data Preparation ---
    if drop_data is None: drop_data = {'has_drop': False, 'width': 0, 'length': 0, 'depth': 0}
    if mat_props is None: mat_props = {}
    if loads is None: loads = {}
    
    # Geometry
    c1_m, c2_m = c1_w/100.0, c2_w/100.0
    has_drop = drop_data.get('has_drop')
    drop_w_m = drop_data.get('width', 0)/100.0
    drop_l_m = drop_data.get('length', 0)/100.0
    h_drop = drop_data.get('depth', 0)
    
    # Material & Loads
    fc = mat_props.get('fc', 0)
    fy = mat_props.get('fy', 0)
    d_bar = mat_props.get('d_bar', 0)
    sdl = loads.get('SDL', 0)
    ll = loads.get('LL', 0)
    wu = loads.get('w_u', 0)
    w_self = (h_slab/100) * 2400

    # ==========================================
    # 2. CSS STYLING (AutoCAD Sheet Look)
    # ==========================================
    st.markdown("""
    <style>
        .cad-container {
            font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            border: 2px solid #37474f;
            background-color: #ffffff;
            margin-bottom: 20px;
            box-shadow: 2px 2px 8px rgba(0,0,0,0.1);
        }
        .cad-header {
            background-color: #37474f;
            color: #ffffff;
            text-align: center;
            font-weight: 900;
            padding: 12px;
            font-size: 1.1rem;
            letter-spacing: 1.5px;
            text-transform: uppercase;
        }
        .cad-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9rem;
        }
        .cad-footer {
            padding: 10px 15px;
            font-size: 0.75rem;
            color: #546e7a;
            background-color: #fcfcfc;
            border-top: 2px solid #37474f;
            line-height: 1.4;
        }
    </style>
    """, unsafe_allow_html=True)

    # ==========================================
    # 3. LAYOUT GRID
    # ==========================================
    col_draw, col_data = st.columns([1.8, 1]) # Ratio 65% : 35%

    # ------------------------------------------
    # LEFT: ENGINEERING DRAWINGS
    # ------------------------------------------
    with col_draw:
        st.markdown("**1. PLAN VIEW (TOP)**")
        
        # --- A. PLAN PLOT ---
        fig, ax = plt.subplots(figsize=(10, 7)) # Larger Canvas
        
        # 1. Grid Lines (Centerlines)
        ax.plot([-1, L1+1], [L2/2, L2/2], color='#90a4ae', ls='-.', lw=0.6) # CL-X
        ax.plot([L1/2, L1/2], [-1, L2+1], color='#90a4ae', ls='-.', lw=0.6) # CL-Y

        # 2. Slab Boundary
        ax.add_patch(patches.Rectangle((0, 0), L1, L2, fc='#fafafa', ec='#263238', lw=2))

        # 3. Columns & Drop Panels
        centers = [(0,0), (L1,0), (0,L2), (L1,L2)]
        for cx, cy in centers:
            # Drop Panel
            if has_drop:
                ax.add_patch(patches.Rectangle(
                    (cx-drop_w_m/2, cy-drop_l_m/2), drop_w_m, drop_l_m, 
                    fc='#e1f5fe', ec='#0277bd', lw=1.0, ls='--'
                ))
            # Column (Solid Fill)
            ax.add_patch(patches.Rectangle(
                (cx-c1_m/2, cy-c2_m/2), c1_m, c2_m, 
                fc='#263238', ec='black'
            ))

        # 4. Dimensions (Clear & Large)
        # Main Spans
        draw_dim(ax, (0, L2), (L1, L2), f"Lx = {L1:.2f} m", offset=0.8, is_vert=False, font_size=12)
        draw_dim(ax, (L1, 0), (L1, L2), f"Ly = {L2:.2f} m", offset=0.8, is_vert=True, font_size=12)
        
        # Drop Panel Dims (if exists)
        if has_drop:
            # Width
            draw_dim(ax, (L1/2 - drop_w_m/2, L2/2 + drop_l_m/2 + 0.1), 
                     (L1/2 + drop_w_m/2, L2/2 + drop_l_m/2 + 0.1), 
                     f"Drop W: {drop_data['width']:.0f}", offset=0, color='#0277bd', font_size=10)
            # Length
            draw_dim(ax, (L1/2 - drop_w_m/2 - 0.1, L2/2 - drop_l_m/2), 
                     (L1/2 - drop_w_m/2 - 0.1, L2/2 + drop_l_m/2), 
                     f"Drop L: {drop_data['length']:.0f}", offset=0, is_vert=True, color='#0277bd', font_size=10)

        # Labels
        ax.text(L1/2, L2/2 - 0.5, "S-01", ha='center', fontsize=16, fontweight='bold', color='#263238',
                bbox=dict(boxstyle="circle,pad=0.3", fc="white", ec="black"))

        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_xlim(-1.5, L1+1.5)
        ax.set_ylim(-1.5, L2+1.5)
        st.pyplot(fig, use_container_width=True)

        # --- B. SECTION PLOT ---
        st.markdown("**2. SECTION A-A**")
        fig_s, ax_s = plt.subplots(figsize=(10, 3.5))
        
        cut_w = 240 # Section Width in cm
        
        # Concrete Hatching (Slab)
        ax_s.add_patch(patches.Rectangle((-cut_w/2, 0), cut_w, h_slab, 
                                       fc='white', ec='black', hatch='///', lw=1.5))
        
        # Drop Panel & Column Logic
        y_bot = 0
        if has_drop:
            dw = min(cut_w*0.7, drop_data['width'])
            ax_s.add_patch(patches.Rectangle((-dw/2, -h_drop), dw, h_drop, 
                                           fc='white', ec='black', hatch='///', lw=1.5))
            y_bot = -h_drop
            # Drop Depth Dim
            draw_dim(ax_s, (dw/2+15, 0), (dw/2+15, -h_drop), f"{h_drop} cm", offset=0, is_vert=True, color='#0277bd')

        # Column Support
        ax_s.add_patch(patches.Rectangle((-c1_w/2, y_bot-40), c1_w, 40, fc='#455a64', ec='black'))
        
        # Rebar (Red Line)
        d_line = h_slab - cover - 0.6
        ax_s.plot([-cut_w/2+20, cut_w/2-20], [d_line, d_line], color='#d32f2f', lw=2.5, label="Main Rebar")
        
        # Dimensions
        draw_dim(ax_s, (-cut_w/2-20, 0), (-cut_w/2-20, h_slab), f"h = {h_slab:.0f}", offset=0, is_vert=True, font_size=11)
        draw_dim(ax_s, (cut_w/3, d_line), (cut_w/3, y_bot), f"d = {d_eff:.2f}", offset=20, is_vert=True, color='#d32f2f', font_size=11)

        ax_s.set_aspect('equal')
        ax_s.axis('off')
        ax_s.set_ylim(y_bot-50, h_slab+30)
        st.pyplot(fig_s, use_container_width=True)

    # ------------------------------------------
    # RIGHT: DATA SHEET (Corrected Logic)
    # ------------------------------------------
    with col_data:
        # Build HTML parts as a list to prevent string format errors
        html_parts = []
        
        # 1. Container Start
        html_parts.append('<div class="cad-container">')
        html_parts.append('<div class="cad-header">DESIGN DATA SHEET</div>')
        html_parts.append('<table class="cad-table">')
        
        # 2. Geometry
        html_parts.append(cad_row("1. GEOMETRY", "", "", is_header=True))
        html_parts.append(cad_row("Slab Thickness (h)", f"{h_slab:.0f}", "cm"))
        html_parts.append(cad_row("Covering", f"{cover:.1f}", "cm"))
        html_parts.append(cad_row("Effective Depth (d)", f"{d_eff:.2f}", "cm"))
        html_parts.append(cad_row("Storey Height", f"{lc:.2f}", "m"))

        # 3. Plan Dimensions
        html_parts.append(cad_row("2. PLAN DIMENSIONS", "", "", is_header=True))
        html_parts.append(cad_row("Span X (Lx)", f"{L1:.2f}", "m"))
        html_parts.append(cad_row("Span Y (Ly)", f"{L2:.2f}", "m"))
        html_parts.append(cad_row("Column Size X", f"{c1_w:.0f}", "cm"))
        html_parts.append(cad_row("Column Size Y", f"{c2_w:.0f}", "cm"))

        # 4. Drop Panel (Conditional)
        if has_drop:
            html_parts.append(cad_row("3. DROP PANEL", "", "", is_header=True))
            html_parts.append(cad_row("Drop Depth", f"+{h_drop:.0f}", "cm"))
            html_parts.append(cad_row("Total Thickness", f"{h_slab+h_drop:.0f}", "cm"))
            html_parts.append(cad_row("Drop Width", f"{drop_data['width']:.0f}", "cm"))
            html_parts.append(cad_row("Drop Length", f"{drop_data['length']:.0f}", "cm"))

        # 5. Materials
        html_parts.append(cad_row("4. MATERIALS", "", "", is_header=True))
        html_parts.append(cad_row("Concrete (f'c)", f"{fc:.0f}", "ksc"))
        html_parts.append(cad_row("Rebar Yield (fy)", f"{fy:.0f}", "ksc"))
        html_parts.append(cad_row("Main Bar Size", f"DB{d_bar}", "mm"))

        # 6. Loads
        html_parts.append(cad_row("5. DESIGN LOADS (ULS)", "", "", is_header=True))
        html_parts.append(cad_row("Superimposed DL", f"{sdl:.0f}", "kg/m²"))
        html_parts.append(cad_row("Live Load (LL)", f"{ll:.0f}", "kg/m²"))
        html_parts.append(cad_row("Self Weight", f"{w_self:.0f}", "kg/m²"))
        html_parts.append(cad_row("FACTORED (Wu)", f"{wu:,.0f}", "kg/m²", is_highlight=True))

        # 7. Close Table & Add Footer
        html_parts.append('</table>')
        html_parts.append(f"""
        <div class="cad-footer">
            <b>👨‍💻 ENGINEER NOTES:</b><br>
            1. All dimensions are in meters unless noted.<br>
            2. Concrete strength is cylinder strength at 28 days.<br>
            3. Design Code: ACI 318-19 / EIT Standard.<br>
            4. Generated by ProFlat Design System.<br>
            5. Analysis Date: {pd.Timestamp.now().strftime('%d-%b-%Y')}
        </div>
        """)
        html_parts.append('</div>') # Close container

        # Join and Render
        final_html = "\n".join(html_parts)
        st.markdown(final_html, unsafe_allow_html=True)
