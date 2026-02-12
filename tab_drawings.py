# tab_drawings.py
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pandas as pd
import numpy as np

# ==========================================
# 1. CONFIG & STYLES (CAD THEME)
# ==========================================
CAD_COLORS = {
    'bg': 'white',
    'slab_fill': '#FFFFFF',
    'slab_edge': '#263238',
    'col_fill': '#546E7A',  
    'col_edge': '#263238',
    'dim': '#455A64',
    'grid': '#CFD8DC',
    'pass_fill': '#E3F2FD', 'pass_edge': '#0277BD', # Structural Drop (Blue)
    'fail_fill': '#FFEBEE', 'fail_edge': '#C62828', # Shear Cap (Red)
    'focus': '#FF6D00' # Orange for Revision Cloud
}

# ==========================================
# 2. UTILS: DRAWING HELPERS
# ==========================================
def draw_smart_dim(ax, p1, p2, text, offset=0, is_vert=False, color=CAD_COLORS['dim']):
    """Draws a professional dimension line with background masking."""
    x1, y1 = p1
    x2, y2 = p2
    
    if is_vert:
        x1 += offset; x2 += offset
        ha, va, rot = 'center', 'center', 90
        sign = 1 if offset > 0 else -1
        txt_pos = (x1 + (0.4 * sign), (y1+y2)/2)
    else:
        y1 += offset; y2 += offset
        ha, va, rot = 'center', 'center', 0
        sign = 1 if offset > 0 else -1
        txt_pos = ((x1+x2)/2, y1 + (0.4 * sign))

    kw_ext = dict(color=color, lw=0.5, ls='-', alpha=0.5)
    # Extension Lines
    if is_vert:
        ax.plot([p1[0], x1], [p1[1], y1], **kw_ext)
        ax.plot([p2[0], x2], [p2[1], y2], **kw_ext)
    else:
        ax.plot([p1[0], x1], [p1[1], y1], **kw_ext)
        ax.plot([p2[0], x2], [p2[1], y2], **kw_ext)

    # Arrow Line
    ax.annotate('', xy=(x1, y1), xytext=(x2, y2),
                arrowprops=dict(arrowstyle='<|-|>', color=color, lw=0.7, shrinkA=0, shrinkB=0))
    
    # Text Label with Background Mask (Important for readability)
    ax.text(txt_pos[0], txt_pos[1], text, 
            color=color, fontsize=9, ha=ha, va=va, rotation=rot, 
            fontfamily='monospace', fontweight='bold', zorder=20,
            bbox=dict(facecolor='white', alpha=0.9, edgecolor='none', pad=1.5))

def draw_boundary_tag(ax, x, y, text, rotation=0):
    """Draws boundary condition tags (Edge vs Continuous)."""
    is_edge = "EDGE" in text
    fc = '#FFEBEE' if is_edge else '#F5F5F5' 
    ec = '#EF9A9A' if is_edge else '#B0BEC5'
    tc = '#C62828' if is_edge else '#78909C'
    weight = 'bold' if is_edge else 'normal'
    
    ax.text(x, y, text, ha='center', va='center', rotation=rotation,
            fontsize=7, color=tc, fontweight=weight, zorder=25,
            bbox=dict(facecolor=fc, edgecolor=ec, alpha=1, pad=4, boxstyle="round,pad=0.4"))

def draw_revision_cloud(ax, x, y, width, height):
    """Draws the sketch-style cloud to focus on the design column."""
    cloud = patches.Ellipse((x, y), width, height, 
                            ec=CAD_COLORS['focus'], fc='none', 
                            lw=2, ls='-', zorder=15)
    # The 'sketch_params' gives it the hand-drawn look
    cloud.set_sketch_params(scale=1.5, length=10.0, randomness=3.0)
    ax.add_patch(cloud)
    
    # Arrow and Text
    ax.annotate("DESIGN\nCOLUMN", xy=(x + width/3, y - height/3), xytext=(x + width, y - height),
                arrowprops=dict(arrowstyle="->", color=CAD_COLORS['focus'], connectionstyle="arc3,rad=0.2"),
                color=CAD_COLORS['focus'], fontsize=9, fontweight='bold', ha='left')

# ==========================================
# 3. HTML TABLE GENERATOR (RESTORED)
# ==========================================
def get_row_html(label, value, unit, is_header=False, is_highlight=False, status_color=None):
    if is_header:
        return f"""
        <tr style="background-color: #37474F; color: white;">
            <td colspan="3" style="padding: 8px 10px; font-weight: bold; font-size: 0.9rem; border-top: 1px solid #000;">{label}</td>
        </tr>"""
    
    bg = "#E8F5E9" if is_highlight else "#ffffff"
    col_val = status_color if status_color else ("#1b5e20" if is_highlight else "#000000")
    w_val = "bold" if (is_highlight or status_color) else "normal"
    
    return f"""
    <tr style="background-color: {bg}; border-bottom: 1px solid #ECEFF1;">
        <td style="padding: 6px 10px; color: #546E7A; font-weight: 500; font-size: 0.85rem;">{label}</td>
        <td style="padding: 6px 10px; text-align: right; color: {col_val}; font-weight: {w_val}; font-family: monospace; font-size: 0.9rem;">{value}</td>
        <td style="padding: 6px 10px; color: #90A4AE; font-size: 0.75rem;">{unit}</td>
    </tr>"""

# ==========================================
# 4. MAIN RENDERER (FULL FUNCTIONALITY)
# ==========================================
def render(L1, L2, c1_w, c2_w, h_slab, lc, cover, d_eff, 
           drop_data=None, moment_vals=None, mat_props=None, loads=None, col_type="interior"):
    
    # --- 1. Data Preparation & Defaults ---
    if drop_data is None: drop_data = {'has_drop': False, 'width': 0, 'length': 0, 'depth': 0}
    mat_props = mat_props or {'fc': 240}
    loads = loads or {'w_u': 0}
    h_slab = h_slab or 20
    
    c1_m, c2_m = c1_w/100.0, c2_w/100.0
    Ln_x = L1 - c1_m
    Ln_y = L2 - c2_m
    
    has_drop = drop_data.get('has_drop')
    dw, dl, dh = drop_data.get('width', 0), drop_data.get('length', 0), drop_data.get('depth', 0) # cm
    
    # --- 2. ACI 318 CHECK ---
    is_structural = False
    fail_reasons = []
    
    if has_drop:
        # Check 1: Extensions (Ln/6)
        req_ext_x = (Ln_x * 100) / 6.0
        req_ext_y = (Ln_y * 100) / 6.0
        req_w_total = c1_w + (2 * req_ext_x)
        req_l_total = c2_w + (2 * req_ext_y)
        
        # Check 2: Depth (h/4)
        req_depth = h_slab / 4.0
        
        pass_dim = (dw >= req_w_total - 1.0) and (dl >= req_l_total - 1.0) # 1cm tolerance
        pass_depth = (dh >= req_depth - 0.1)
        
        is_structural = pass_dim and pass_depth
        
        if not pass_dim: fail_reasons.append("Too Small")
        if not pass_depth: fail_reasons.append("Too Thin")

    # --- 3. Layout ---
    col_draw, col_info = st.columns([0.65, 0.35], gap="large")

    with col_draw:
        # =================================
        # DRAWING 1: PLAN VIEW
        # =================================
        st.markdown(f"#### 📐 PLAN VIEW: {col_type.upper()} PANEL")
        
        fig, ax = plt.subplots(figsize=(8, 6.5))
        margin = max(L1, L2) * 0.3
        
        # Grid System
        ax.plot([-margin, L1+margin], [L2/2, L2/2], color=CAD_COLORS['grid'], ls='-.', lw=1)
        ax.plot([L1/2, L1/2], [-margin, L2+margin], color=CAD_COLORS['grid'], ls='-.', lw=1)
        
        # Slab Panel
        ax.add_patch(patches.Rectangle((0, 0), L1, L2, fc='white', ec=CAD_COLORS['slab_edge'], lw=1.5, zorder=1))

        # Dynamic Labels
        lbl_top = "CONTINUOUS"
        lbl_left = "CONTINUOUS"
        if col_type == 'edge':
            lbl_top = "BUILDING EDGE" # Assuming Edge column means top edge is exterior
        elif col_type == 'corner':
            lbl_top = "BUILDING EDGE"
            lbl_left = "BUILDING EDGE"
            
        draw_boundary_tag(ax, -0.8, L2/2, lbl_left, rotation=90)
        draw_boundary_tag(ax, L1/2, L2+0.8, lbl_top)
        draw_boundary_tag(ax, L1+0.8, L2/2, "CONTINUOUS", rotation=90)
        draw_boundary_tag(ax, L1/2, -0.8, "CONTINUOUS")

        # Draw Columns & Drops
        centers = [(0,0), (L1,0), (0,L2), (L1,L2)]
        for cx, cy in centers:
            # Drop Panel
            if has_drop:
                if is_structural:
                    col_d_fill, col_d_edge, d_style = CAD_COLORS['pass_fill'], CAD_COLORS['pass_edge'], '-'
                else:
                    col_d_fill, col_d_edge, d_style = CAD_COLORS['fail_fill'], CAD_COLORS['fail_edge'], '--'
                
                ax.add_patch(patches.Rectangle((cx - dw/200, cy - dl/200), dw/100, dl/100, 
                                             fc=col_d_fill, ec=col_d_edge, ls=d_style, lw=1.2, zorder=2))
                
                # Label only on Design Column (Top-Left 0, L2)
                if cx == 0 and cy == L2:
                    ax.text(cx, cy - dl/200 - 0.2, f"DROP {dw:.0f}x{dl:.0f}", 
                            ha='center', va='top', fontsize=8, color=col_d_edge, fontweight='bold',
                            bbox=dict(fc='white', ec='none', alpha=0.7, pad=0))
                    
                    if not is_structural:
                        fail_text = "\n".join(fail_reasons)
                        ax.text(cx, cy - dl/200 - 0.6, f"(SHEAR CAP)\n{fail_text}", 
                                ha='center', va='top', fontsize=7, color=CAD_COLORS['fail_edge'], fontweight='bold')

            # Column
            ax.add_patch(patches.Rectangle((cx-c1_m/2, cy-c2_m/2), c1_m, c2_m, 
                                         fc=CAD_COLORS['col_fill'], ec=CAD_COLORS['col_edge'], zorder=5))

        # Focus Cloud (Top-Left)
        draw_revision_cloud(ax, 0, L2, max(c1_m, c2_m)*4, max(c1_m, c2_m)*4)

        # Dimensions
        draw_smart_dim(ax, (0, L2), (L1, L2), f"{L1:.2f} m", offset=1.2)
        draw_smart_dim(ax, (L1, 0), (L1, L2), f"{L2:.2f} m", offset=1.2, is_vert=True)

        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_xlim(-margin, L1 + margin)
        ax.set_ylim(-margin, L2 + margin)
        st.pyplot(fig, use_container_width=True)

        # =================================
        # DRAWING 2: SECTION VIEW
        # =================================
        st.markdown(f"#### 🏗️ SECTION VIEW")
        fig_s, ax_s = plt.subplots(figsize=(8, 3))
        
        sw = 300 # Section width
        
        # Column
        ax_s.add_patch(patches.Rectangle((-c1_w/2, -120), c1_w, 120+h_slab, fc=CAD_COLORS['col_fill'], ec='black', zorder=1))
        
        # Slab
        ax_s.add_patch(patches.Rectangle((-sw/2, 0), sw, h_slab, fc='white', ec='black', lw=1.2, hatch='//', zorder=2))
        
        # Drop Panel Section
        if has_drop:
            # Only hatch if structural
            s_hatch = '//' if is_structural else None
            s_fc = 'white' if is_structural else CAD_COLORS['fail_fill']
            s_ec = 'black' if is_structural else CAD_COLORS['fail_edge']
            
            draw_dw = min(dw, sw * 0.8)
            ax_s.add_patch(patches.Rectangle((-draw_dw/2, -dh), draw_dw, dh, 
                                           fc=s_fc, ec=s_ec, hatch=s_hatch, lw=1.2, zorder=3))
            
            draw_smart_dim(ax_s, (draw_dw/2 + 20, 0), (draw_dw/2 + 20, -dh), f"{dh:.0f}cm", is_vert=True, color='#1565C0')

        # Dimensions
        draw_smart_dim(ax_s, (-sw/2 - 20, 0), (-sw/2 - 20, h_slab), f"h={h_slab:.0f}", is_vert=True)
        
        ax_s.set_xlim(-sw/2 - 50, sw/2 + 50)
        ax_s.set_ylim(-130, h_slab + 40)
        ax_s.set_aspect('equal')
        ax_s.axis('off')
        st.pyplot(fig_s, use_container_width=True)

    with col_info:
        # =================================
        # DATA SHEET (HTML TABLE)
        # =================================
        html = """
        <style>
            .sheet-container { border: 1px solid #CFD8DC; background-color: #fff; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
            .sheet-table { width: 100%; border-collapse: collapse; font-family: sans-serif; }
            .sheet-footer { padding: 10px; background-color: #F5F5F5; border-top: 1px solid #ddd; font-size: 0.7rem; color: #78909C; text-align: right; }
        </style>
        <div class="sheet-container">
        <table class="sheet-table">
        """
        
        html += get_row_html("1. GEOMETRY", "", "", is_header=True)
        html += get_row_html("Panel Type", f"{col_type.upper()}", "", is_highlight=True)
        html += get_row_html("Thickness (h)", f"{h_slab:.0f}", "cm")
        html += get_row_html("Cover (c)", f"{cover:.1f}", "cm")
        html += get_row_html("Eff. Depth (d)", f"{d_eff:.2f}", "cm")
        
        if has_drop:
            html += get_row_html("2. DROP PANEL", "", "", is_header=True)
            html += get_row_html("Size (WxL)", f"{dw:.0f}x{dl:.0f}", "cm")
            html += get_row_html("Depth (Ext)", f"{dh:.0f}", "cm")
            
            status_txt = "STRUCTURAL" if is_structural else "SHEAR CAP"
            status_col = "#2E7D32" if is_structural else "#C62828"
            html += get_row_html("Status", status_txt, "", status_color=status_col)
            
            if not is_structural:
                 html += f"""<tr style="background-color: #FFEBEE;"><td colspan="3" style="padding: 5px 10px; font-size: 0.75rem; color: #C62828;">* Reason: {', '.join(fail_reasons)}</td></tr>"""
        
        html += get_row_html("3. LOADING", "", "", is_header=True)
        html += get_row_html("fc'", f"{mat_props.get('fc', 0):.0f}", "ksc")
        html += get_row_html("Load (Wu)", f"{loads.get('w_u', 0):,.0f}", "kg/m²", is_highlight=True)
        
        html += "</table>"
        html += f'<div class="sheet-footer">ACI 318-19 • Auto-Generated</div></div>'
        
        st.markdown(html, unsafe_allow_html=True)
