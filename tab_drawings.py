# tab_drawings.py
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pandas as pd
import numpy as np

# ==========================================
# 1. HELPER: DIMENSIONS
# ==========================================
def draw_dim(ax, p1, p2, text, offset=0, color='#000000', is_vert=False, font_size=10, style='standard'):
    """Render architectural dimensions nicely."""
    x1, y1 = p1
    x2, y2 = p2
    
    if is_vert:
        x1 += offset; x2 += offset
        ha, va, rot = 'center', 'center', 90
        sign = 1 if offset > 0 else -1
        txt_x = x1 + (0.45 * sign) 
        txt_pos = (txt_x, (y1+y2)/2)
    else:
        y1 += offset; y2 += offset
        ha, va, rot = 'center', 'center', 0
        sign = 1 if offset > 0 else -1
        txt_y = y1 + (0.45 * sign)
        txt_pos = ((x1+x2)/2, txt_y)

    ext_kw = dict(color=color, lw=0.6, ls='-', alpha=0.4)
    if is_vert:
        ax.plot([p1[0], x1], [p1[1], y1], **ext_kw)
        ax.plot([p2[0], x2], [p2[1], y2], **ext_kw)
    else:
        ax.plot([p1[0], x1], [p1[1], y1], **ext_kw)
        ax.plot([p2[0], x2], [p2[1], y2], **ext_kw)

    arrow_style = '<|-|>'
    if style == 'clear': arrow_style = '|-|'
        
    ax.annotate('', xy=(x1, y1), xytext=(x2, y2),
                arrowprops=dict(arrowstyle=arrow_style, color=color, lw=0.8, mutation_scale=12))
    
    ax.text(txt_pos[0], txt_pos[1], text, 
            color=color, fontsize=font_size, ha=ha, va=va, rotation=rot, 
            fontfamily='monospace', fontweight='bold', zorder=20,
            bbox=dict(facecolor='white', alpha=0.9, edgecolor='none', pad=1.5))

# ==========================================
# 2. HELPER: VISUAL ANNOTATIONS
# ==========================================
def draw_boundary_label(ax, x, y, text, rotation=0):
    """Draws a tag indicating if the side is Continuous or Edge."""
    if "EDGE" in text:
        bg_col = "#ffebee" # Light Red (Warning)
        txt_col = "#c62828"
        border_col = "#ef9a9a"
        weight = "bold"
    else:
        bg_col = "#f5f5f5" # Light Grey
        txt_col = "#90a4ae"
        border_col = "#cfd8dc"
        weight = "normal"
        
    ax.text(x, y, text, ha='center', va='center', rotation=rotation,
            fontsize=8, color=txt_col, fontweight=weight,
            bbox=dict(facecolor=bg_col, edgecolor=border_col, alpha=1.0, pad=4, boxstyle="round,pad=0.4"))

def draw_revision_cloud(ax, x, y, width, height):
    """Draws a generic 'cloud' shape to highlight the design column."""
    cloud = patches.Ellipse(
        (x, y), width, height,
        ec='#ff6d00', # Bright Orange
        fc='none',    
        lw=2.5,        
        ls='-',
        zorder=15
    )
    cloud.set_sketch_params(scale=2.0, length=10.0, randomness=5.0)
    ax.add_patch(cloud)
    
    ax.annotate("DESIGN\nCOLUMN", xy=(x + width/2 * 0.7, y - height/2 * 0.7), 
                xytext=(x + width*1.2, y - height*1.2),
                arrowprops=dict(arrowstyle="->", color='#ff6d00', connectionstyle="arc3,rad=-0.2"),
                color='#e65100', fontsize=9, fontweight='bold', ha='left')

# ==========================================
# 3. HELPER: HTML TABLE RENDERER
# ==========================================
def get_row_html(label, value, unit, is_header=False, is_highlight=False):
    if is_header:
        return f"""
        <tr style="background-color: #263238; color: white;">
            <td colspan="3" style="padding: 8px 10px; font-weight: 700; font-size: 0.9rem; border-top: 2px solid #000;">{label}</td>
        </tr>"""
    
    bg = "#e8f5e9" if is_highlight else "#ffffff"
    col_val = "#1b5e20" if is_highlight else "#000000"
    w_val = "700" if is_highlight else "500"
    
    return f"""
    <tr style="background-color: {bg}; border-bottom: 1px solid #eceff1;">
        <td style="padding: 5px 10px; color: #546e7a; font-weight: 500; font-size: 0.85rem;">{label}</td>
        <td style="padding: 5px 10px; text-align: right; color: {col_val}; font-weight: {w_val}; font-family: monospace; font-size: 0.9rem;">{value}</td>
        <td style="padding: 5px 10px; color: #90a4ae; font-size: 0.75rem;">{unit}</td>
    </tr>"""

# ==========================================
# 4. MAIN RENDERER
# ==========================================
def render(L1, L2, c1_w, c2_w, h_slab, lc, cover, d_eff, 
           drop_data=None, moment_vals=None, 
           mat_props=None, loads=None, 
           col_type="interior"):
    
    if drop_data is None: drop_data = {'has_drop': False, 'width': 0, 'length': 0, 'depth': 0}
    if mat_props is None: mat_props = {}
    if loads is None: loads = {}
    
    h_slab = h_slab if h_slab else 20
    cover = cover if cover else 2.5
    d_eff = d_eff if d_eff else (h_slab - cover - 1.0)
    lc = lc if lc else 3.0
    
    c1_m, c2_m = c1_w/100.0, c2_w/100.0
    Ln_x = L1 - c1_m
    Ln_y = L2 - c2_m
    
    has_drop = drop_data.get('has_drop')
    drop_w_val = drop_data.get('width', 0)
    drop_l_val = drop_data.get('length', 0)
    h_drop_val = drop_data.get('depth', 0)
    
    drop_w_m = drop_w_val/100.0
    drop_l_m = drop_l_val/100.0
    
    fc_val = mat_props.get('fc', 0)
    wu = loads.get('w_u', 0)

    # --- LOGIC CHECK: Is Drop Panel Structural? ---
    is_structural_drop = False
    dp_status_label = ""
    dp_reason = ""
    dp_reason_inline = ""
    
    if has_drop:
        req_ext_x = (Ln_x * 100.0) / 6.0
        req_ext_y = (Ln_y * 100.0) / 6.0
        req_w_total = (2 * req_ext_x) + c1_w
        req_l_total = (2 * req_ext_y) + c2_w
        req_depth = h_slab / 4.0
        
        pass_dim = (drop_w_val >= req_w_total - 0.1) and (drop_l_val >= req_l_total - 0.1)
        pass_depth = (h_drop_val >= req_depth - 0.1)
        is_structural_drop = pass_dim and pass_depth
        
        if not is_structural_drop:
            dp_status_label = "SHEAR CAP"
            reasons = []
            if not pass_dim: reasons.append("Too Small")
            if not pass_depth: reasons.append("Too Thin")
            dp_reason = "\n".join(reasons)
            dp_reason_inline = ", ".join(reasons)

    st.markdown("""<style>.sheet-container { border: 1px solid #cfd8dc; background: #fff; margin-bottom: 20px; } 
    .sheet-header { background: #37474f; color: #fff; padding: 10px; text-align: center; font-weight: bold; }
    .sheet-table { width: 100%; border-collapse: collapse; }</style>""", unsafe_allow_html=True)

    col_draw, col_data = st.columns([2, 1])

    with col_draw:
        st.markdown(f"**📐 PLAN VIEW: {col_type.upper()} PANEL**")
        fig, ax = plt.subplots(figsize=(8, 6))
        
        # --- DYNAMIC BOUNDARY LOGIC (LINKED) ---
        lbls = {"top": "CONTINUOUS", "bot": "CONTINUOUS", "left": "CONTINUOUS", "right": "CONTINUOUS"}
        if col_type == 'edge':
            lbls["left"] = "BUILDING EDGE"
        elif col_type == 'corner':
            lbls["left"] = "BUILDING EDGE"
            lbls["top"] = "BUILDING EDGE"

        margin = 1.5
        ax.plot([-margin, L1+margin], [L2/2, L2/2], color='#b0bec5', ls='-.', lw=0.8)
        ax.plot([L1/2, L1/2], [-margin, L2+margin], color='#b0bec5', ls='-.', lw=0.8)
        ax.add_patch(patches.Rectangle((0, 0), L1, L2, fc='#ffffff', ec='#263238', lw=1.5, zorder=1))

        centers = [(0,0), (L1,0), (0,L2), (L1,L2)]
        for cx, cy in centers:
            if has_drop:
                dp_fc, dp_ec, dp_ls = ('#e1f5fe', '#0288d1', '--') if is_structural_drop else ('#ffccbc', '#d32f2f', '--')
                ax.add_patch(patches.Rectangle((cx-drop_w_m/2, cy-drop_l_m/2), drop_w_m, drop_l_m, fc=dp_fc, ec=dp_ec, lw=1.0, ls=dp_ls, zorder=2))
                if cx == 0 and cy == L2: # Design Column
                    ax.text(cx, cy - drop_l_m/2 - 0.2, f"DROP: {drop_w_val:.0f}x{drop_l_val:.0f}", ha='center', va='top', fontsize=8, color=dp_ec, fontweight='bold', bbox=dict(fc='white', alpha=0.8, ec='none'))
                    if not is_structural_drop:
                        ax.text(cx, cy - drop_l_m/2 - 0.55, f"({dp_status_label})\n{dp_reason}", ha='center', va='top', fontsize=7, color='#c62828', fontweight='bold')

            ax.add_patch(patches.Rectangle((cx-c1_m/2, cy-c2_m/2), c1_m, c2_m, fc='#455a64', ec='black', zorder=5))

        # --- REVISION CLOUD (RESTORED) ---
        c_size = max(c1_m, c2_m) * 3.5
        draw_revision_cloud(ax, 0, L2, c_size, c_size)

        draw_boundary_label(ax, L1/2, L2 + 1.2, lbls["top"])
        draw_boundary_label(ax, L1/2, -1.2, lbls["bot"])
        draw_boundary_label(ax, -1.2, L2/2, lbls["left"], rotation=90)
        draw_boundary_label(ax, L1 + 1.2, L2/2, lbls["right"], rotation=90)

        draw_dim(ax, (0, L2), (L1, L2), f"{L1:.2f}m", offset=0.8)
        draw_dim(ax, (L1, 0), (L1, L2), f"{L2:.2f}m", offset=0.8, is_vert=True)
        
        ax.set_aspect('equal')
        ax.axis('off')
        st.pyplot(fig, use_container_width=True)

        # --- SECTION VIEW ---
        st.markdown(f"**🏗️ SECTION A-A**")
        fig_s, ax_s = plt.subplots(figsize=(8, 3))
        cut_w = 250
        ax_s.add_patch(patches.Rectangle((-c1_w/2, -100), c1_w, 100+h_slab, fc='#546e7a', ec='black', zorder=2))
        ax_s.add_patch(patches.Rectangle((-cut_w/2, 0), cut_w, h_slab, fc='white', ec='black', hatch='//', zorder=3))
        
        if has_drop:
            ds_fc, ds_ec = ('white', 'black') if is_structural_drop else ('#ffccbc', '#d32f2f')
            draw_dw = min(cut_w * 0.7, drop_w_val)
            ax_s.add_patch(patches.Rectangle((-draw_dw/2, -h_drop_val), draw_dw, h_drop_val, fc=ds_fc, ec=ds_ec, hatch='//' if is_structural_drop else None, zorder=3))
            draw_dim(ax_s, (draw_dw/2 + 10, 0), (draw_dw/2 + 10, -h_drop_val), f"{h_drop_val}cm", is_vert=True, color='#0277bd')

        draw_dim(ax_s, (-cut_w/2 - 15, 0), (-cut_w/2 - 15, h_slab), f"h={h_slab:.0f}", is_vert=True)
        ax_s.set_aspect('equal')
        ax_s.axis('off')
        ax_s.set_xlim(-cut_w/2 - 50, cut_w/2 + 50)
        st.pyplot(fig_s, use_container_width=True)

    with col_data:
        html = f'<div class="sheet-container"><div class="sheet-header">DESIGN DATA</div><table class="sheet-table">'
        html += get_row_html("1. GEOMETRY", "", "", is_header=True)
        html += get_row_html("Panel Type", f"{col_type.upper()}", "", is_highlight=True)
        html += get_row_html("Thickness (h)", f"{h_slab:.0f}", "cm")
        html += get_row_html("Eff. Depth (d)", f"{d_eff:.2f}", "cm")
        
        if has_drop:
            html += get_row_html("2. DROP PANEL", "", "", is_header=True)
            html += get_row_html("Size (WxL)", f"{drop_w_val:.0f}x{drop_l_val:.0f}", "cm")
            html += get_row_html("Depth (Ext)", f"{h_drop_val:.0f}", "cm")
            st_col = "green" if is_structural_drop else "red"
            html += f'<tr style="background:#f5f5f5;"><td style="padding:5px 10px; font-weight:bold;">STATUS</td><td style="text-align:right; color:{st_col}; font-weight:bold;">{"STRUCTURAL" if is_structural_drop else "SHEAR CAP"}</td><td></td></tr>'
            if not is_structural_drop:
                html += f'<tr><td colspan="3" style="text-align:right; font-size:0.7rem; color:red; padding-right:10px;">* {dp_reason_inline}</td></tr>'

        html += get_row_html("3. LOADING", "", "", is_header=True)
        html += get_row_html("Load (Wu)", f"{wu:,.0f}", "kg/m²", is_highlight=True)
        html += '</table></div>'
        st.markdown(html, unsafe_allow_html=True)
