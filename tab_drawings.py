# tab_drawings.py
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pandas as pd
import numpy as np

# ==========================================
# 1. CONFIGURATION & STYLES
# ==========================================
# Professional CAD Color Palette
STYLE = {
    'bg': '#ffffff',
    'grid': '#cfd8dc',       # Light Grey
    'dim': '#37474f',        # Slate Grey
    'col_fill': '#546e7a',   # Muted Blue-Grey
    'col_edge': '#263238',   # Dark Grey
    'slab_edge': '#000000',
    'pass_main': '#0277bd',  # Engineering Blue
    'pass_bg': '#e1f5fe',
    'fail_main': '#c62828',  # Alert Red
    'fail_bg': '#ffebee',
    'focus': '#ff6f00',      # Amber/Orange
    'rebar': '#d32f2f'       # Rebar Red
}

# ==========================================
# 2. HELPER FUNCTIONS
# ==========================================

def draw_smart_dim(ax, p1, p2, text, offset=0, is_vert=False, color=STYLE['dim'], style='arrow'):
    """
    Draws a dimension line with architectural ticks and background masking.
    """
    x1, y1 = p1
    x2, y2 = p2
    
    # Calculate positions
    if is_vert:
        x1 += offset; x2 += offset
        ha, va, rot = 'center', 'center', 90
        # Text position: slightly offset from line center
        txt_pos = (x1 + (0.35 if offset > 0 else -0.35), (y1+y2)/2)
    else:
        y1 += offset; y2 += offset
        ha, va, rot = 'center', 'center', 0
        txt_pos = ((x1+x2)/2, y1 + (0.35 if offset > 0 else -0.35))

    # Extension Lines (Thin, lighter)
    ext_kw = dict(color=color, lw=0.5, ls='-', alpha=0.5)
    if is_vert:
        ax.plot([p1[0], x1], [p1[1], y1], **ext_kw)
        ax.plot([p2[0], x2], [p2[1], y2], **ext_kw)
    else:
        ax.plot([p1[0], x1], [p1[1], y1], **ext_kw)
        ax.plot([p2[0], x2], [p2[1], y2], **ext_kw)

    # Dimension Line
    arrow = '<|-|>' if style == 'arrow' else '|-|'
    ax.annotate('', xy=(x1, y1), xytext=(x2, y2),
                arrowprops=dict(arrowstyle=arrow, color=color, lw=0.8, shrinkA=0, shrinkB=0))
    
    # Text with Halo (Background Mask)
    ax.text(txt_pos[0], txt_pos[1], text, color=color, fontsize=9, 
            ha=ha, va=va, rotation=rot, family='monospace', weight='bold',
            bbox=dict(facecolor='white', edgecolor='none', alpha=0.85, pad=1.5))

def draw_revision_cloud(ax, x, y, w, h):
    """
    Draws a 'sketch-style' cloud to highlight the design element.
    """
    cloud = patches.Ellipse((x, y), w, h, ec=STYLE['focus'], fc='none', lw=1.5, ls='-')
    # This creates the "hand-drawn" squiggly effect
    cloud.set_sketch_params(scale=1.5, length=10.0, randomness=4.0)
    ax.add_patch(cloud)
    
    # Annotation text
    ax.annotate("DESIGN\nCOLUMN", xy=(x + w/3, y - h/3), xytext=(x + w*0.8, y - h*0.8),
                arrowprops=dict(arrowstyle="->", color=STYLE['focus'], connectionstyle="arc3,rad=-0.2"),
                color=STYLE['focus'], fontsize=8, weight='bold')

def draw_boundary_tag(ax, x, y, text, rotation=0):
    """
    Draws tags for boundary conditions (Edge vs Continuous).
    """
    is_edge = "EDGE" in text
    
    props = dict(boxstyle='round,pad=0.3', 
                 facecolor=STYLE['fail_bg'] if is_edge else '#f5f5f5', 
                 edgecolor=STYLE['fail_main'] if is_edge else '#b0bec5',
                 alpha=1.0)
    
    ax.text(x, y, text, ha='center', va='center', rotation=rotation,
            fontsize=7, weight='bold' if is_edge else 'normal',
            color=STYLE['fail_main'] if is_edge else '#78909c',
            bbox=props, zorder=10)

def get_html_row(label, val, unit, header=False, highlight=False, status_col=None):
    """Generates a clean HTML table row."""
    if header:
        return f"""
        <tr style="background-color: #37474f; color: white;">
            <td colspan="3" style="padding: 6px 10px; font-weight: bold; border-top: 2px solid #263238;">{label}</td>
        </tr>"""
    
    bg = "#f1f8e9" if highlight else "white"
    color = status_col if status_col else ("#2e7d32" if highlight else "#263238")
    weight = "bold" if (highlight or status_col) else "normal"
    
    return f"""
    <tr style="background-color: {bg}; border-bottom: 1px solid #eceff1;">
        <td style="padding: 5px 10px; color: #546e7a; font-size: 0.85rem;">{label}</td>
        <td style="text-align: right; padding: 5px 10px; color: {color}; font-weight: {weight}; font-family: monospace; font-size: 0.9rem;">{val}</td>
        <td style="padding: 5px 10px; color: #90a4ae; font-size: 0.75rem;">{unit}</td>
    </tr>"""

# ==========================================
# 3. MAIN RENDER LOGIC
# ==========================================
def render(L1, L2, c1_w, c2_w, h_slab, lc, cover, d_eff, 
           drop_data=None, moment_vals=None, mat_props=None, loads=None, col_type="interior"):
    
    # --- Data Normalization ---
    drop_data = drop_data or {'has_drop': False, 'width': 0, 'length': 0, 'depth': 0}
    mat_props = mat_props or {'fc': 240}
    loads = loads or {'w_u': 0}
    
    # Conversions (cm to m for drawing)
    c1_m, c2_m = c1_w/100, c2_w/100
    dw, dl, dh = drop_data['width'], drop_data['length'], drop_data['depth']
    dw_m, dl_m = dw/100, dl/100
    Ln_x = L1 - c1_m
    
    # --- ACI 318 CHECK: Structural vs Shear Cap ---
    is_structural = False
    fail_reasons = []
    has_drop = drop_data['has_drop']
    
    if has_drop:
        # Check 1: Extension >= Ln/6
        req_ext = (Ln_x * 100) / 6
        req_w = c1_w + (2 * req_ext)
        req_l = c2_w + (2 * ((L2-c2_m)*100/6)) # Simplified logic for Y
        pass_dim = (dw >= req_w - 1) and (dl >= req_l - 1) # 1cm tolerance
        
        # Check 2: Depth >= h/4
        pass_depth = dh >= (h_slab/4 - 0.1)
        
        is_structural = pass_dim and pass_depth
        if not pass_dim: fail_reasons.append("Size < Ln/6")
        if not pass_depth: fail_reasons.append("Depth < h/4")

    # --- LAYOUT ---
    col_draw, col_info = st.columns([0.65, 0.35], gap="medium")

    with col_draw:
        # ==========================
        # 1. PLAN VIEW
        # ==========================
        st.markdown(f"**📐 PLAN VIEW** ({col_type.upper()} Panel)")
        
        fig, ax = plt.subplots(figsize=(8, 6.5))
        
        # Boundary Labels Logic
        lbls = {"top": "CONTINUOUS", "left": "CONTINUOUS"}
        if col_type in ['edge', 'corner']: lbls["left"] = "BUILDING EDGE"
        if col_type == 'corner': lbls["top"] = "BUILDING EDGE"

        # Grid Lines
        margin = 1.5
        ax.plot([-margin, L1+margin], [L2/2, L2/2], color=STYLE['grid'], ls='-.', lw=1, zorder=0)
        ax.plot([L1/2, L1/2], [-margin, L2+margin], color=STYLE['grid'], ls='-.', lw=1, zorder=0)

        # Slab Panel
        ax.add_patch(patches.Rectangle((0, 0), L1, L2, fc='white', ec='black', lw=1.5, zorder=1))

        # Loop Columns
        centers = [(0,0), (L1,0), (0,L2), (L1,L2)] # BL, BR, TL, TR
        for i, (cx, cy) in enumerate(centers):
            # Draw Drop Panel
            if has_drop:
                # Design Column is usually top-left or bottom-left depending on convention
                # Let's assume Top-Left (0, L2) is our target for the cloud
                is_target = (cx == 0 and cy == L2)
                
                color = STYLE['pass_main'] if is_structural else STYLE['fail_main']
                bg_col = STYLE['pass_bg'] if is_structural else STYLE['fail_bg']
                line_style = '-' if is_structural else '--'
                
                ax.add_patch(patches.Rectangle(
                    (cx - dw_m/2, cy - dl_m/2), dw_m, dl_m,
                    fc=bg_col, ec=color, ls=line_style, lw=1, zorder=2
                ))
                
                if is_target:
                    # Label for Drop Panel
                    txt = f"DROP {dw:.0f}x{dl:.0f}"
                    ax.text(cx, cy - dl_m/2 - 0.15, txt, ha='center', va='top', 
                            fontsize=8, color=color, weight='bold',
                            bbox=dict(fc='white', ec='none', alpha=0.7, pad=0))
                    
                    if not is_structural:
                        reason = ", ".join(fail_reasons)
                        ax.text(cx, cy - dl_m/2 - 0.45, f"(SHEAR CAP)\n{reason}", 
                                ha='center', va='top', fontsize=7, color=color)

            # Draw Column
            ax.add_patch(patches.Rectangle(
                (cx - c1_m/2, cy - c2_m/2), c1_m, c2_m,
                fc=STYLE['col_fill'], ec=STYLE['col_edge'], zorder=5
            ))

        # Focus Cloud (Targeting Top-Left Column)
        draw_revision_cloud(ax, 0, L2, max(c1_m, c2_m)*3.5, max(c1_m, c2_m)*3.5)

        # Boundary Tags
        draw_boundary_tag(ax, -0.8, L2/2, lbls["left"], 90)
        draw_boundary_tag(ax, L1/2, L2+0.8, lbls["top"])

        # Dimensions
        draw_smart_dim(ax, (0, L2), (L1, L2), f"L1 = {L1:.2f} m", offset=1.0)
        draw_smart_dim(ax, (L1, 0), (L1, L2), f"L2 = {L2:.2f} m", offset=1.0, is_vert=True)
        # Clear Span Dim
        draw_smart_dim(ax, (c1_m/2, L2/2 - 0.5), (L1 - c1_m/2, L2/2 - 0.5), 
                      f"Ln = {Ln_x:.2f}m", offset=0, color=STYLE['pass_main'], style='tick')

        ax.set_aspect('equal')
        ax.axis('off')
        st.pyplot(fig, use_container_width=True)

        # ==========================
        # 2. SECTION VIEW
        # ==========================
        st.markdown("**🏗️ SECTION A-A**")
        fig_s, ax_s = plt.subplots(figsize=(8, 3.5))
        
        cut_w = 2.5 # Width of section in meters to show
        scale_x = 100 # Convert m to cm for easier drawing logic
        
        # Draw Column
        ax_s.add_patch(patches.Rectangle((-c1_w/2, -150), c1_w, 150+h_slab, fc=STYLE['col_fill'], ec='black', zorder=2))
        
        # Draw Slab
        sw = 300 # Section display width
        ax_s.add_patch(patches.Rectangle((-sw/2, 0), sw, h_slab, fc='white', ec='black', lw=1.2, hatch='///', zorder=3))
        
        # Draw Drop
        if has_drop:
            d_hatch = '///' if is_structural else None
            d_fc = 'white' if is_structural else STYLE['fail_bg']
            d_ec = 'black' if is_structural else STYLE['fail_main']
            d_ls = '-' if is_structural else '--'
            
            # Limit draw width
            draw_dw = min(dw, sw*0.8)
            ax_s.add_patch(patches.Rectangle((-draw_dw/2, -dh), draw_dw, dh, 
                                           fc=d_fc, ec=d_ec, ls=d_ls, hatch=d_hatch, zorder=3))
            
            # Dim for drop depth
            draw_smart_dim(ax_s, (draw_dw/2 + 15, 0), (draw_dw/2 + 15, -dh), 
                          f"{dh:.0f}", is_vert=True, color=STYLE['pass_main'])

        # Effective Depth Line (Rebar)
        y_rebar = h_slab - cover - 0.5 # approx bar radius
        ax_s.plot([-sw/2+20, sw/2-20], [y_rebar, y_rebar], color=STYLE['rebar'], ls='--', lw=1.5, zorder=4)
        ax_s.text(sw/4, y_rebar + 2, f"d = {d_eff:.2f} cm", color=STYLE['rebar'], fontsize=8, weight='bold')

        # Main Dims
        draw_smart_dim(ax_s, (-sw/2 - 20, 0), (-sw/2 - 20, h_slab), f"h={h_slab:.0f}", is_vert=True)
        
        ax_s.set_xlim(-sw/2 - 40, sw/2 + 40)
        ax_s.set_ylim(-dh - 50 if has_drop else -50, h_slab + 40)
        ax_s.set_aspect('equal')
        ax_s.axis('off')
        st.pyplot(fig_s, use_container_width=True)

    with col_info:
        # ==========================
        # 3. DATA TABLE (HTML)
        # ==========================
        
        html = """
        <style>
            .eng-table { width: 100%; border-collapse: collapse; font-family: sans-serif; box-shadow: 0 0 10px rgba(0,0,0,0.05); }
            .eng-footer { font-size: 0.7rem; color: #b0bec5; text-align: right; padding: 5px; margin-top: 5px;}
        </style>
        <div style="border: 1px solid #cfd8dc; border-radius: 4px; overflow: hidden;">
        <table class="eng-table">
        """
        
        # Geometry Section
        html += get_html_row("GEOMETRY DATA", "", "", header=True)
        html += get_html_row("Panel Type", col_type.upper(), "", highlight=True)
        html += get_html_row("Slab Thickness (h)", f"{h_slab:.0f}", "cm")
        html += get_html_row("Eff. Depth (d)", f"{d_eff:.2f}", "cm", status_col=STYLE['rebar'])
        html += get_html_row("Clear Span (Ln)", f"{Ln_x:.2f}", "m")

        # Drop Panel Section
        if has_drop:
            html += get_html_row("DROP PANEL", "", "", header=True)
            html += get_html_row("Size", f"{dw:.0f} x {dl:.0f}", "cm")
            html += get_html_row("Projection (h_d)", f"{dh:.0f}", "cm")
            
            status_txt = "STRUCTURAL" if is_structural else "SHEAR CAP"
            status_c = STYLE['pass_main'] if is_structural else STYLE['fail_main']
            html += get_html_row("Classification", status_txt, "", status_col=status_c)
            
            if not is_structural:
                html += f"""<tr><td colspan="3" style="padding: 5px 10px; font-size: 0.75rem; color: {STYLE['fail_main']}; background: {STYLE['fail_bg']};">
                ⚠️ <b>Warning:</b> {', '.join(fail_reasons)}<br>Neglect stiffness, use for shear only.</td></tr>"""

        # Materials Section
        html += get_html_row("MATERIALS & LOADS", "", "", header=True)
        html += get_html_row("Concrete (fc')", f"{mat_props['fc']:.0f}", "ksc")
        html += get_html_row("Design Load (Wu)", f"{loads['w_u']:,.0f}", "kg/m²", highlight=True)

        html += "</table></div>"
        html += "<div class='eng-footer'>Generated by RC Slab Design Pro • ACI 318-19</div>"
        
        st.markdown(html, unsafe_allow_html=True)
