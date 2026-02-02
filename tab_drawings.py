# tab_drawings.py
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pandas as pd # Import pandas for Timestamp

# ==========================================
# 1. HELPER: CAD STYLING & DIMENSIONS
# ==========================================
def draw_dim(ax, p1, p2, text, offset=0, color='#000000', is_vert=False, font_size=12):
    """
    Render architectural dimensions with high precision.
    """
    x1, y1 = p1
    x2, y2 = p2
    
    # Calculate positions
    if is_vert:
        x1 += offset; x2 += offset
        ha, va, rot = 'right' if offset < 0 else 'left', 'center', 90
        txt_x = x1 - 0.2 if offset < 0 else x1 + 0.2
        txt_pos = (txt_x, (y1+y2)/2)
    else:
        y1 += offset; y2 += offset
        ha, va, rot = 'center', 'bottom' if offset > 0 else 'top', 0
        txt_y = y1 + 0.2 if offset > 0 else y1 - 0.2
        txt_pos = ((x1+x2)/2, txt_y)

    # Dimension Line
    ax.annotate('', xy=(x1, y1), xytext=(x2, y2),
                arrowprops=dict(arrowstyle='<|-|>', color=color, lw=0.8, mutation_scale=12))
    
    # Extension Lines
    ext_style = dict(color=color, lw=0.5, ls='-', alpha=0.5)
    if is_vert:
        ax.plot([p1[0], x1], [p1[1], y1], **ext_style)
        ax.plot([p2[0], x2], [p2[1], y2], **ext_style)
    else:
        ax.plot([p1[0], x1], [p1[1], y1], **ext_style)
        ax.plot([p2[0], x2], [p2[1], y2], **ext_style)

    # Text with background
    ax.text(txt_pos[0], txt_pos[1], text, 
            color=color, fontsize=font_size, ha=ha, va=va, rotation=rot, 
            fontfamily='monospace', fontweight='bold', zorder=10,
            bbox=dict(facecolor='white', alpha=1.0, edgecolor='none', pad=1))

# ==========================================
# 2. HELPER: HTML ROW GENERATOR (FIXED)
# ==========================================
def get_row_html(label, value, unit, is_header=False, is_highlight=False):
    """Returns a single line of HTML for the table without indentation issues."""
    if is_header:
        return f'<tr style="background-color: #263238; color: white;"><td colspan="3" style="padding: 8px 10px; font-weight: bold; font-size: 0.9rem; border-top: 1px solid black;">{label}</td></tr>'
    
    bg = "#ffebee" if is_highlight else "#ffffff"
    col_val = "#b71c1c" if is_highlight else "#000000"
    w_val = "800" if is_highlight else "600"
    
    return f'<tr style="background-color: {bg}; border-bottom: 1px solid #ddd;"><td style="padding: 6px 10px; color: #444; font-weight: 500;">{label}</td><td style="padding: 6px 10px; text-align: right; color: {col_val}; font-weight: {w_val}; font-family: monospace;">{value}</td><td style="padding: 6px 10px; color: #888; font-size: 0.8rem;">[{unit}]</td></tr>'

# ==========================================
# 3. MAIN RENDER FUNCTION
# ==========================================
def render(L1, L2, c1_w, c2_w, h_slab, lc, cover, d_eff, 
           drop_data=None, moment_vals=None, 
           mat_props=None, loads=None):
    
    # --- Data Unpacking ---
    if drop_data is None: drop_data = {'has_drop': False, 'width': 0, 'length': 0, 'depth': 0}
    if mat_props is None: mat_props = {}
    if loads is None: loads = {}
    
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
    w_self = (h_slab/100) * 2400

    # ==========================================
    # CSS STYLES
    # ==========================================
    st.markdown("""
    <style>
        .eng-sheet {
            font-family: 'Segoe UI', sans-serif;
            border: 2px solid #333;
            background: white;
            margin-bottom: 20px;
        }
        .eng-header {
            background-color: #333;
            color: white;
            padding: 10px;
            text-align: center;
            font-weight: bold;
            font-size: 1.1rem;
            letter-spacing: 1px;
        }
        .eng-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9rem;
        }
        .eng-footer {
            padding: 10px;
            font-size: 0.75rem;
            color: #666;
            background: #f9f9f9;
            border-top: 1px solid #333;
        }
    </style>
    """, unsafe_allow_html=True)

    # ==========================================
    # LAYOUT
    # ==========================================
    col_gfx, col_dat = st.columns([1.8, 1])

    # --- LEFT: DRAWINGS ---
    with col_gfx:
        st.markdown("**1. PLAN VIEW (TOP)**")
        fig, ax = plt.subplots(figsize=(10, 7))
        
        # Grid & Slab
        ax.plot([-1, L1+1], [L2/2, L2/2], color='#ccc', ls='-.', lw=0.8)
        ax.plot([L1/2, L1/2], [-1, L2+1], color='#ccc', ls='-.', lw=0.8)
        ax.add_patch(patches.Rectangle((0, 0), L1, L2, fc='#fdfdfd', ec='black', lw=2))

        # Supports
        centers = [(0,0), (L1,0), (0,L2), (L1,L2)]
        for cx, cy in centers:
            if has_drop:
                ax.add_patch(patches.Rectangle((cx-drop_w_m/2, cy-drop_l_m/2), drop_w_m, drop_l_m, 
                                               fc='#e3f2fd', ec='#2196f3', lw=1, ls='--'))
            ax.add_patch(patches.Rectangle((cx-c1_m/2, cy-c2_m/2), c1_m, c2_m, fc='#333', ec='black'))

        # Dims
        draw_dim(ax, (0, L2), (L1, L2), f"Lx = {L1:.2f} m", offset=0.8, is_vert=False)
        draw_dim(ax, (L1, 0), (L1, L2), f"Ly = {L2:.2f} m", offset=0.8, is_vert=True)
        
        if has_drop:
            draw_dim(ax, (L1/2-drop_w_m/2, L2/2+drop_l_m/2), (L1/2+drop_w_m/2, L2/2+drop_l_m/2), 
                     f"Drop: {drop_data['width']:.0f}", offset=0.2, color='#1976d2', font_size=10)

        ax.text(L1/2, L2/2 - 0.5, "S-01", ha='center', fontsize=14, fontweight='bold', 
                bbox=dict(boxstyle="circle", fc="white", ec="black"))
        
        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_xlim(-1.5, L1+1.5)
        ax.set_ylim(-1.5, L2+1.5)
        st.pyplot(fig, use_container_width=True)

        # Section
        st.markdown("**2. SECTION A-A**")
        fig_s, ax_s = plt.subplots(figsize=(10, 3.5))
        cut_w = 250
        
        # Slab
        ax_s.add_patch(patches.Rectangle((-cut_w/2, 0), cut_w, h_slab, fc='white', ec='black', hatch='///'))
        
        y_bot = 0
        if has_drop:
            dw = min(cut_w*0.6, drop_data['width'])
            ax_s.add_patch(patches.Rectangle((-dw/2, -h_drop), dw, h_drop, fc='white', ec='black', hatch='///'))
            y_bot = -h_drop
            draw_dim(ax_s, (dw/2+10, 0), (dw/2+10, -h_drop), f"{h_drop}", offset=0, is_vert=True, color='blue')

        # Column
        ax_s.add_patch(patches.Rectangle((-c1_w/2, y_bot-40), c1_w, 40, fc='#444', ec='black'))
        
        # Rebar
        d_line = h_slab - cover - 0.6
        ax_s.plot([-cut_w/2+20, cut_w/2-20], [d_line, d_line], 'r-', lw=2)
        
        draw_dim(ax_s, (-cut_w/2-10, 0), (-cut_w/2-10, h_slab), f"h={h_slab:.0f}", offset=0, is_vert=True)
        draw_dim(ax_s, (cut_w/3, d_line), (cut_w/3, y_bot), f"d={d_eff:.2f}", offset=10, is_vert=True, color='red')
        
        ax_s.set_aspect('equal')
        ax_s.axis('off')
        ax_s.set_ylim(y_bot-50, h_slab+30)
        st.pyplot(fig_s, use_container_width=True)

    # --- RIGHT: DATA SHEET (HTML FIX) ---
    with col_dat:
        # Construct HTML string linearly to avoid indentation errors
        html_content = ""
        html_content += '<div class="eng-sheet">'
        html_content += '<div class="eng-header">DESIGN DATA SHEET</div>'
        html_content += '<table class="eng-table">'
        
        # Rows
        html_content += get_row_html("1. GEOMETRY", "", "", is_header=True)
        html_content += get_row_html("Slab Thickness (h)", f"{h_slab:.0f}", "cm")
        html_content += get_row_html("Covering", f"{cover:.1f}", "cm")
        html_content += get_row_html("Effective Depth (d)", f"{d_eff:.2f}", "cm")
        html_content += get_row_html("Storey Height", f"{lc:.2f}", "m")
        
        html_content += get_row_html("2. PLAN DIMENSIONS", "", "", is_header=True)
        html_content += get_row_html("Span X (Lx)", f"{L1:.2f}", "m")
        html_content += get_row_html("Span Y (Ly)", f"{L2:.2f}", "m")
        html_content += get_row_html("Column X", f"{c1_w:.0f}", "cm")
        html_content += get_row_html("Column Y", f"{c2_w:.0f}", "cm")
        
        if has_drop:
            html_content += get_row_html("3. DROP PANEL", "", "", is_header=True)
            html_content += get_row_html("Drop Depth", f"+{h_drop:.0f}", "cm")
            html_content += get_row_html("Total Thickness", f"{h_slab+h_drop:.0f}", "cm")
            html_content += get_row_html("Drop Size", f"{drop_data['width']:.0f}x{drop_data['length']:.0f}", "cm")

        html_content += get_row_html("4. MATERIALS", "", "", is_header=True)
        html_content += get_row_html("Concrete (fc')", f"{fc:.0f}", "ksc")
        html_content += get_row_html("Rebar (fy)", f"{fy:.0f}", "ksc")
        html_content += get_row_html("Main Bar", f"DB{d_bar}", "mm")

        html_content += get_row_html("5. LOADS (ULS)", "", "", is_header=True)
        html_content += get_row_html("Superimposed DL", f"{sdl:.0f}", "kg/m²")
        html_content += get_row_html("Live Load", f"{ll:.0f}", "kg/m²")
        html_content += get_row_html("FACTORED (Wu)", f"{wu:,.0f}", "kg/m²", is_highlight=True)
        
        html_content += '</table>'
        
        # Footer
        now_str = pd.Timestamp.now().strftime('%d-%b-%Y')
        html_content += f'<div class="eng-footer"><b>ENGINEER NOTES:</b><br>1. All dimensions in meters/cm.<br>2. Code: ACI 318-19.<br>3. Date: {now_str}</div>'
        html_content += '</div>'

        # RENDER
        st.markdown(html_content, unsafe_allow_html=True)
