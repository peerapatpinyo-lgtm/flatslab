# tab_drawings.py
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# ==========================================
# 1. HELPER: CAD STYLING & DIMENSIONS
# ==========================================
def draw_dim(ax, p1, p2, text, offset=0, color='#000000', is_vert=False, font_size=9):
    """
    Draws a technical dimension line (Architectural Tick Style).
    """
    x1, y1 = p1
    x2, y2 = p2
    
    # Calculate text and line positions
    if is_vert:
        x1 += offset; x2 += offset
        ha, va, rot = 'right' if offset < 0 else 'left', 'center', 90
        txt_x = x1 - 0.08 if offset < 0 else x1 + 0.08
        txt_pos = (txt_x, (y1+y2)/2)
    else:
        y1 += offset; y2 += offset
        ha, va, rot = 'center', 'bottom' if offset > 0 else 'top', 0
        txt_y = y1 + 0.08 if offset > 0 else y1 - 0.08
        txt_pos = ((x1+x2)/2, txt_y)

    # Main Dimension Line
    ax.annotate('', xy=(x1, y1), xytext=(x2, y2),
                arrowprops=dict(arrowstyle='<|-|>', color=color, lw=0.6, mutation_scale=10))
    
    # Extension Lines (Thin lines)
    ext_style = dict(color=color, lw=0.3, ls='-', alpha=0.6)
    if is_vert:
        ax.plot([p1[0], x1], [p1[1], y1], **ext_style)
        ax.plot([p2[0], x2], [p2[1], y2], **ext_style)
    else:
        ax.plot([p1[0], x1], [p1[1], y1], **ext_style)
        ax.plot([p2[0], x2], [p2[1], y2], **ext_style)

    # Text Label with High-Contrast Background
    ax.text(txt_pos[0], txt_pos[1], text, 
            color=color, fontsize=font_size, ha=ha, va=va, rotation=rot, 
            fontfamily='monospace', fontweight='bold',
            bbox=dict(facecolor='#ffffff', alpha=1.0, edgecolor='none', pad=1))

# ==========================================
# 2. HELPER: HTML DATA ROWS
# ==========================================
def cad_row(label, value, unit, is_header=False):
    """Generates a perfectly aligned HTML table row."""
    if is_header:
        return f"""
        <tr style="background-color: #000; color: #fff;">
            <td colspan="3" style="padding: 6px; font-weight: bold; text-transform: uppercase; font-size: 0.85rem; letter-spacing: 1px;">{label}</td>
        </tr>
        """
    else:
        return f"""
        <tr style="border-bottom: 1px solid #ccc;">
            <td style="padding: 4px 8px; font-weight: 600; color: #333; width: 50%;">{label}</td>
            <td style="padding: 4px 8px; text-align: right; font-family: 'Courier New', monospace; font-weight: 700; color: #000; width: 30%;">{value}</td>
            <td style="padding: 4px 8px; text-align: left; color: #666; font-size: 0.8rem; width: 20%;">[{unit}]</td>
        </tr>
        """

# ==========================================
# 3. MAIN RENDER FUNCTION
# ==========================================
def render(L1, L2, c1_w, c2_w, h_slab, lc, cover, d_eff, 
           drop_data=None, moment_vals=None, 
           mat_props=None, loads=None):
    
    # --- 1. Data Prep ---
    if drop_data is None: drop_data = {'has_drop': False, 'width': 0, 'length': 0, 'depth': 0}
    if mat_props is None: mat_props = {}
    if loads is None: loads = {}
    
    # Geometry Conversions
    c1_m, c2_m = c1_w/100.0, c2_w/100.0
    drop_w_m = drop_data.get('width', 0)/100.0
    drop_l_m = drop_data.get('length', 0)/100.0
    h_drop = drop_data.get('depth', 0)
    has_drop = drop_data.get('has_drop')

    # Load & Mat Values
    fc = mat_props.get('fc', 0)
    fy = mat_props.get('fy', 0)
    d_bar = mat_props.get('d_bar', 0)
    
    sdl = loads.get('SDL', 0)
    ll = loads.get('LL', 0)
    wu = loads.get('w_u', 0)

    # ==========================================
    # 2. CSS STYLING (The "CAD Title Block" Look)
    # ==========================================
    st.markdown("""
    <style>
        .cad-sheet {
            font-family: 'Segoe UI', sans-serif;
            background-color: white;
            border: 2px solid #000; /* Thick border like a drawing sheet */
            padding: 0;
            margin-bottom: 20px;
        }
        .cad-title {
            text-align: center;
            font-weight: 900;
            font-size: 1.1rem;
            padding: 10px;
            border-bottom: 2px solid #000;
            background-color: #f4f4f4;
            letter-spacing: 2px;
            text-transform: uppercase;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9rem;
        }
        .drawing-area {
            background-color: #ffffff;
            border-right: 2px solid #000;
            padding: 20px;
            text-align: center;
        }
    </style>
    """, unsafe_allow_html=True)

    # ==========================================
    # 3. LAYOUT STRUCTURE
    # ==========================================
    # Split: Left (Drawing) 65% | Right (Data Table) 35%
    col_draw, col_table = st.columns([2, 1.2])

    # ------------------------------------------
    # LEFT COLUMN: THE DRAWINGS
    # ------------------------------------------
    with col_draw:
        st.markdown("**PLAN VIEW (Top)**")
        
        # --- PLAN PLOT ---
        fig, ax = plt.subplots(figsize=(8, 6))
        
        # 1. Grid Lines (Centerlines)
        ax.axhline(L2/2, color='blue', ls='-.', lw=0.4, alpha=0.5)
        ax.axvline(L1/2, color='blue', ls='-.', lw=0.4, alpha=0.5)

        # 2. Main Slab Outline
        ax.add_patch(patches.Rectangle((0, 0), L1, L2, fc='none', ec='black', lw=2))

        # 3. Columns & Drops
        centers = [(0,0), (L1,0), (0,L2), (L1,L2)]
        for cx, cy in centers:
            # Drop Panel
            if has_drop:
                ax.add_patch(patches.Rectangle(
                    (cx-drop_w_m/2, cy-drop_l_m/2), drop_w_m, drop_l_m, 
                    fc='#e3f2fd', ec='#1565c0', lw=0.8, ls='--'
                ))
            # Column
            ax.add_patch(patches.Rectangle(
                (cx-c1_m/2, cy-c2_m/2), c1_m, c2_m, 
                fc='black', ec='black'
            ))

        # 4. Dimensions (Clean & Precise)
        draw_dim(ax, (0, L2), (L1, L2), f"{L1:.2f}", offset=0.5, is_vert=False) # Top Dim
        draw_dim(ax, (L1, 0), (L1, L2), f"{L2:.2f}", offset=0.5, is_vert=True)  # Right Dim
        
        # Internal Dims (Drop Panel)
        if has_drop:
            # Drop Width
            draw_dim(ax, (L1/2 - drop_w_m/2, L2/2 + drop_l_m/2 + 0.2), 
                     (L1/2 + drop_w_m/2, L2/2 + drop_l_m/2 + 0.2), 
                     f"Drop W: {drop_data['width']}", offset=0, color='#1565c0')
            # Drop Length
            draw_dim(ax, (L1/2 - drop_w_m/2 - 0.2, L2/2 - drop_l_m/2), 
                     (L1/2 - drop_w_m/2 - 0.2, L2/2 + drop_l_m/2), 
                     f"Drop L: {drop_data['length']}", offset=0, is_vert=True, color='#1565c0')

        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_xlim(-1, L1+1)
        ax.set_ylim(-1, L2+1)
        st.pyplot(fig, use_container_width=True)

        # --- SECTION PLOT (Below Plan) ---
        st.markdown("**SECTION A-A**")
        fig_s, ax_s = plt.subplots(figsize=(10, 3))
        
        cut_w = 200 # Visual width
        
        # Concrete Hatching
        ax_s.add_patch(patches.Rectangle((-cut_w/2, 0), cut_w, h_slab, fc='white', ec='black', hatch='///', lw=1.5))
        
        bot_y = 0
        if has_drop:
            dw = min(cut_w*0.6, drop_data['width'])
            ax_s.add_patch(patches.Rectangle((-dw/2, -h_drop), dw, h_drop, fc='white', ec='black', hatch='///'))
            bot_y = -h_drop
            draw_dim(ax_s, (dw/2+5, 0), (dw/2+5, -h_drop), f"{h_drop}", offset=5, is_vert=True, color='blue')

        # Column Support
        ax_s.add_patch(patches.Rectangle((-c1_w/2, bot_y-30), c1_w, 30, fc='#333', ec='black'))
        
        # Rebar
        d_line = h_slab - cover - 0.6
        ax_s.plot([-cut_w/2+10, cut_w/2-10], [d_line, d_line], 'r-', lw=2, label="Rebar")
        
        # Dims
        draw_dim(ax_s, (-cut_w/2-10, 0), (-cut_w/2-10, h_slab), f"h:{h_slab}", offset=-5, is_vert=True)
        draw_dim(ax_s, (cut_w/3, d_line), (cut_w/3, bot_y), f"d:{d_eff:.2f}", offset=5, is_vert=True, color='red')

        ax_s.set_aspect('equal')
        ax_s.axis('off')
        ax_s.set_ylim(bot_y-40, h_slab+20)
        st.pyplot(fig_s, use_container_width=True)

    # ------------------------------------------
    # RIGHT COLUMN: THE "TITLE BLOCK" DATA
    # ------------------------------------------
    with col_table:
        # Build the HTML Table String
        html_table = f"""
        <div class="cad-sheet">
            <div class="cad-title">DESIGN DATA SHEET</div>
            <table>
                {cad_row("1. GEOMETRY", "", "", is_header=True)}
                {cad_row("Slab Thickness (h)", f"{h_slab:.0f}", "cm")}
                {cad_row("Covering", f"{cover:.1f}", "cm")}
                {cad_row("Effective Depth (d)", f"{d_eff:.2f}", "cm")}
                {cad_row("Storey Height", f"{lc:.2f}", "m")}
                
                {cad_row("2. PLAN DIMENSIONS", "", "", is_header=True)}
                {cad_row("Span X (Lx)", f"{L1:.2f}", "m")}
                {cad_row("Span Y (Ly)", f"{L2:.2f}", "m")}
                {cad_row("Column Size X", f"{c1_w:.0f}", "cm")}
                {cad_row("Column Size Y", f"{c2_w:.0f}", "cm")}
        """
        
        if has_drop:
            html_table += f"""
                {cad_row("3. DROP PANEL", "", "", is_header=True)}
                {cad_row("Drop Thickness", f"+{h_drop:.0f}", "cm")}
                {cad_row("Total Thick.", f"{h_slab+h_drop:.0f}", "cm")}
                {cad_row("Drop Width", f"{drop_data['width']:.0f}", "cm")}
                {cad_row("Drop Length", f"{drop_data['length']:.0f}", "cm")}
            """

        html_table += f"""
                {cad_row("4. MATERIALS", "", "", is_header=True)}
                {cad_row("Concrete (f'c)", f"{fc:.0f}", "ksc")}
                {cad_row("Rebar Yield (fy)", f"{fy:.0f}", "ksc")}
                {cad_row("Rebar Diameter", f"DB{d_bar}", "mm")}
                
                {cad_row("5. DESIGN LOADS", "", "", is_header=True)}
                {cad_row("Superimposed DL", f"{sdl:.0f}", "kg/m²")}
                {cad_row("Live Load (LL)", f"{ll:.0f}", "kg/m²")}
                {cad_row("Self Weight", f"{(h_slab/100)*2400:.0f}", "kg/m²")}
                <tr style="background-color: #ffebee; border-bottom: 2px solid black;">
                    <td style="padding: 6px 8px; font-weight: bold; color: #b71c1c;">FACTORED (Wu)</td>
                    <td style="padding: 6px 8px; text-align: right; font-family: 'Courier New'; font-weight: 800; color: #b71c1c;">{wu:,.0f}</td>
                    <td style="padding: 6px 8px; color: #b71c1c;">[kg/m²]</td>
                </tr>
            </table>
            
            <div style="padding: 10px; font-size: 0.75rem; color: #555; border-top: 1px solid #000;">
                <b>ENGINEER NOTES:</b><br>
                1. All dimensions are in meters unless noted.<br>
                2. Concrete strength is cylinder strength.<br>
                3. Design Code: ACI 318-19 / EIT Standard.<br>
                4. Generated by ProFlat Design System.
            </div>
        </div>
        """
        
        st.markdown(html_table, unsafe_allow_html=True)

    st.markdown("---")
