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

    # Extension Lines
    ext_kw = dict(color=color, lw=0.6, ls='-', alpha=0.4)
    if is_vert:
        ax.plot([p1[0], x1], [p1[1], y1], **ext_kw)
        ax.plot([p2[0], x2], [p2[1], y2], **ext_kw)
    else:
        ax.plot([p1[0], x1], [p1[1], y1], **ext_kw)
        ax.plot([p2[0], x2], [p2[1], y2], **ext_kw)

    # Main Dimension Line
    arrow_style = '<|-|>'
    if style == 'clear': arrow_style = '|-|'
        
    ax.annotate('', xy=(x1, y1), xytext=(x2, y2),
                arrowprops=dict(arrowstyle=arrow_style, color=color, lw=0.8, mutation_scale=12))
    
    # Text Label (Background to hide lines underneath)
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
    
    # --- 4.1 Data Prep & Safety Defaults ---
    if drop_data is None: drop_data = {'has_drop': False, 'width': 0, 'length': 0, 'depth': 0}
    if mat_props is None: mat_props = {}
    if loads is None: loads = {}
    
    # Safety: Handle None or 0 values
    h_slab = h_slab if h_slab else 20
    cover = cover if cover else 2.5
    d_eff = d_eff if d_eff else (h_slab - cover - 1.0)
    lc = lc if lc else 3.0
    
    c1_m, c2_m = c1_w/100.0, c2_w/100.0
    Ln_x = L1 - c1_m
    Ln_y = L2 - c2_m
    
    has_drop = drop_data.get('has_drop')
    drop_w_val = drop_data.get('width', 0) # cm
    drop_l_val = drop_data.get('length', 0) # cm
    h_drop_val = drop_data.get('depth', 0) # cm (Projection)
    
    # Unit Conversions for Drawing
    drop_w_m = drop_w_val/100.0
    drop_l_m = drop_l_val/100.0
    
    fc_val = mat_props.get('fc', 0)
    wu = loads.get('w_u', 0)

    # --- 4.2 LOGIC CHECK: Is Drop Panel Structural? (ACI 318) ---
    is_structural_drop = False
    dp_status_label = ""
    dp_reason = ""
    
    if has_drop:
        # 1. Extension Check: Must extend Ln/6 from support
        ln_x_cm = Ln_x * 100.0
        ln_y_cm = Ln_y * 100.0
        
        req_ext_x = ln_x_cm / 6.0
        req_ext_y = ln_y_cm / 6.0
        
        # Total required width (assuming centered)
        req_w_total = (2 * req_ext_x) + c1_w
        req_l_total = (2 * req_ext_y) + c2_w
        
        pass_dim = (drop_w_val >= req_w_total) and (drop_l_val >= req_l_total)

        # 2. Depth Check: Projection must be >= h_slab/4
        req_depth = h_slab / 4.0
        pass_depth = (h_drop_val >= req_depth)
        
        # 3. Final Status
        is_structural_drop = pass_dim and pass_depth
        
        if not is_structural_drop:
            dp_status_label = "SHEAR CAP"
            reasons = []
            if not pass_dim: reasons.append("Too Small")
            if not pass_depth: reasons.append("Too Thin")
            dp_reason = "\n".join(reasons) # For drawing
            dp_reason_inline = ", ".join(reasons) # For table

    # --- 4.3 Styles ---
    st.markdown("""
    <style>
        .sheet-container {
            font-family: sans-serif; border: 1px solid #cfd8dc; 
            background-color: #fff; box-shadow: 0 2px 5px rgba(0,0,0,0.05);
            margin-bottom: 20px;
        }
        .sheet-header {
            background-color: #37474f; color: #fff; padding: 10px; 
            text-align: center; font-weight: bold; font-size: 1rem;
        }
        .sheet-table { width: 100%; border-collapse: collapse; }
        .sheet-footer {
            padding: 10px; background-color: #f5f5f5; border-top: 1px solid #ddd;
            font-size: 0.75rem; color: #78909c;
        }
    </style>
    """, unsafe_allow_html=True)

    # --- 4.4 Layout ---
    col_draw, col_data = st.columns([2, 1])

    # === LEFT: ENGINEERING DRAWINGS ===
    with col_draw:
        # ------------------------------------
        # A. PLAN VIEW
        # ------------------------------------
        st.markdown(f"**📐 PLAN VIEW: {col_type.upper()} PANEL**")
        fig, ax = plt.subplots(figsize=(8, 6))
        
        lbls = {"top": "CONTINUOUS", "bot": "CONTINUOUS", "left": "CONTINUOUS", "right": "CONTINUOUS"}
        # Assume design column is Top-Left (0, L2) for visualization consistency
        
        if col_type == 'edge':
            lbls["left"] = "BUILDING EDGE"
        elif col_type == 'corner':
            lbls["left"] = "BUILDING EDGE"
            lbls["top"] = "BUILDING EDGE"

        # Grid & Slab
        margin = 1.5
        ax.plot([-margin, L1+margin], [L2/2, L2/2], color='#b0bec5', ls='-.', lw=0.8) # Grid X
        ax.plot([L1/2, L1/2], [-margin, L2+margin], color='#b0bec5', ls='-.', lw=0.8) # Grid Y
        
        ax.add_patch(patches.Rectangle((0, 0), L1, L2, fc='#ffffff', ec='#263238', lw=1.5, zorder=1))

        # Columns Loop
        centers = [(0,0), (L1,0), (0,L2), (L1,L2)]
        for cx, cy in centers:
            # --- Draw Drop Panel ---
            if has_drop:
                # Style Logic
                if is_structural_drop:
                    # Pass (Blue)
                    dp_fc, dp_ec, dp_ls = '#e1f5fe', '#0288d1', '--'
                    dp_lw = 0.8
                else:
                    # Fail (Orange/Red)
                    dp_fc, dp_ec, dp_ls = '#ffccbc', '#d32f2f', '--'
                    dp_lw = 1.2

                ax.add_patch(patches.Rectangle(
                    (cx-drop_w_m/2, cy-drop_l_m/2), drop_w_m, drop_l_m, 
                    fc=dp_fc, ec=dp_ec, lw=dp_lw, ls=dp_ls, zorder=2
                ))
                
                # Special Label ONLY on Top-Left Column (Design Column)
                if cx == 0 and cy == L2:
                    # Size Text
                    label_text = f"DROP: {drop_w_val:.0f}x{drop_l_val:.0f}"
                    ax.text(cx, cy - drop_l_m/2 - 0.2, label_text, 
                            ha='center', va='top', fontsize=8, color=dp_ec, fontweight='bold',
                            bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', pad=0.5))
                    
                    # Status/Warning Text
                    if not is_structural_drop:
                        warn_text = f"({dp_status_label})\n{dp_reason}"
                        ax.text(cx, cy - drop_l_m/2 - 0.55, warn_text, 
                                ha='center', va='top', fontsize=7, color='#c62828', fontweight='bold')

            # --- Draw Column ---
            ax.add_patch(patches.Rectangle((cx-c1_m/2, cy-c2_m/2), c1_m, c2_m, 
                                         fc='#455a64', ec='black', zorder=5))

        # Revision Cloud (Targeting Top-Left)
        c_size = max(c1_m, c2_m) * 3.5
        draw_revision_cloud(ax, 0, L2, c_size, c_size)

        # Labels
        draw_boundary_label(ax, L1/2, L2 + 1.2, lbls["top"])
        draw_boundary_label(ax, L1/2, -1.2, lbls["bot"])
        draw_boundary_label(ax, -1.2, L2/2, lbls["left"], rotation=90)
        draw_boundary_label(ax, L1 + 1.2, L2/2, lbls["right"], rotation=90)

        # Dims
        draw_dim(ax, (0, L2), (L1, L2), f"{L1:.2f}m", offset=0.8)
        draw_dim(ax, (L1, 0), (L1, L2), f"{L2:.2f}m", offset=0.8, is_vert=True)
        draw_dim(ax, (c1_m/2, L2/4), (L1 - c1_m/2, L2/4), f"Ln={Ln_x:.2f}m", offset=0, color='#2e7d32', style='clear')
        
        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_xlim(-margin-0.5, L1+margin+0.5)
        ax.set_ylim(-margin-0.5, L2+margin+0.5)
        st.pyplot(fig, use_container_width=True)

        # ------------------------------------
        # B. SECTION VIEW
        # ------------------------------------
        st.markdown(f"**🏗️ SECTION A-A** (Storey H = {lc:.2f} m)")
        fig_s, ax_s = plt.subplots(figsize=(8, 4))
        
        cut_w = 250
        col_draw_h = 150
        
        # 1. Column
        ax_s.add_patch(patches.Rectangle((-c1_w/2, -col_draw_h), c1_w, col_draw_h, fc='#546e7a', ec='black', zorder=2))
        
        # 2. Slab
        ax_s.add_patch(patches.Rectangle((-cut_w/2, 0), cut_w, h_slab, fc='white', ec='black', hatch='//', zorder=3))
        
        # 3. Drop Panel
        y_bottom_slab = 0
        if has_drop:
            # Consistent Styling with Plan
            if is_structural_drop:
                dp_sec_fc, dp_sec_ec = 'white', 'black' # Standard Concrete
                dp_sec_style = '-'
                dp_sec_label = None
            else:
                dp_sec_fc, dp_sec_ec = '#ffccbc', '#d32f2f' # Warning
                dp_sec_style = '--'
                dp_sec_label = "Shear Cap Only\n(Stiffness Ignored)"

            drop_draw_w = min(cut_w * 0.7, drop_w_val)
            
            # Draw Drop
            ax_s.add_patch(patches.Rectangle(
                (-drop_draw_w/2, -h_drop_val), drop_draw_w, h_drop_val, 
                fc=dp_sec_fc, ec=dp_sec_ec, hatch='//' if is_structural_drop else None, 
                ls=dp_sec_style, zorder=3
            ))
            
            y_bottom_slab = -h_drop_val
            draw_dim(ax_s, (drop_draw_w/2 + 10, 0), (drop_draw_w/2 + 10, -h_drop_val), f"{h_drop_val}cm", is_vert=True, color='#0277bd')

            # Section Label
            if dp_sec_label:
                ax_s.annotate(
                    dp_sec_label,
                    xy=(drop_draw_w/2, -h_drop_val),
                    xytext=(drop_draw_w/2 + 30, -h_drop_val - 30),
                    arrowprops=dict(arrowstyle='->', color=dp_sec_ec, connectionstyle="arc3,rad=0.2"),
                    color=dp_sec_ec, fontsize=9, fontweight='bold', zorder=100,
                    bbox=dict(boxstyle="round,pad=0.2", fc="white", ec=dp_sec_ec, alpha=0.9)
                )

        # 4. Rebar
        eff_depth_line = h_slab - cover - 0.5
        ax_s.plot([-cut_w/2 + 10, cut_w/2 - 10], [eff_depth_line, eff_depth_line], color='#d32f2f', lw=2.5, zorder=4)
        
        # 5. Dimensions
        draw_dim(ax_s, (-cut_w/2 - 15, 0), (-cut_w/2 - 15, h_slab), f"h={h_slab:.0f}cm", is_vert=True)
        draw_dim(ax_s, (cut_w/4, eff_depth_line), (cut_w/4, y_bottom_slab), f"d={d_eff:.2f}cm", is_vert=True, color='#d32f2f')
        draw_dim(ax_s, (-c1_w/2 - 30, 0), (-c1_w/2 - 30, -col_draw_h), f"H={lc:.2f}m", is_vert=True, color='#e65100')

        ax_s.set_aspect('equal')
        ax_s.axis('off')
        ax_s.set_xlim(-cut_w/2 - 50, cut_w/2 + 50)
        ax_s.set_ylim(-col_draw_h - 20, h_slab + 30)
        
        st.pyplot(fig_s, use_container_width=True)

    # === RIGHT: DATA SHEET ===
    with col_data:
        html = ""
        html += '<div class="sheet-container">'
        html += '<div class="sheet-header">DESIGN DATA</div>'
        html += '<table class="sheet-table">'
        
        html += get_row_html("1. GEOMETRY", "", "", is_header=True)
        html += get_row_html("Panel Type", f"{col_type.upper()}", "", is_highlight=True)
        html += get_row_html("Thickness (h)", f"{h_slab:.0f}", "cm")
        html += get_row_html("Cover (c)", f"{cover:.1f}", "cm")
        html += get_row_html("Eff. Depth (d)", f"{d_eff:.2f}", "cm")
        
        html += get_row_html("2. SPANS", "", "", is_header=True)
        html += get_row_html("L1 (Center)", f"{L1:.2f}", "m")
        html += get_row_html("L2 (Center)", f"{L2:.2f}", "m")
        html += get_row_html("Ln (Clear)", f"{max(Ln_x, Ln_y):.2f}", "m")
        
        if has_drop:
            html += get_row_html("3. DROP PANEL", "", "", is_header=True)
            html += get_row_html("Size (WxL)", f"{drop_w_val:.0f}x{drop_l_val:.0f}", "cm")
            html += get_row_html("Depth (Ext)", f"{h_drop_val:.0f}", "cm")
            html += get_row_html("Total Depth", f"{h_slab+h_drop_val:.0f}", "cm")
            
            # Status Indicator in Table with Reason
            status_text = "STRUCTURAL" if is_structural_drop else "SHEAR CAP"
            status_color = "green" if is_structural_drop else "red"
            status_bg = "#e8f5e9" if is_structural_drop else "#ffebee"
            
            html += f"""
            <tr style="background-color: {status_bg}; border-bottom: 1px solid #eceff1;">
                <td style="padding: 5px 10px; color: #e65100; font-weight: bold;">STATUS</td>
                <td style="padding: 5px 10px; text-align: right; color: {status_color}; font-weight: bold;">{status_text}</td>
                <td></td>
            </tr>"""
            
            if not is_structural_drop:
                html += f"""
                <tr style="background-color: {status_bg};">
                    <td colspan="3" style="padding: 2px 10px 8px 10px; text-align: right; font-size: 0.75rem; color: #c62828;">
                        *Reason: {dp_reason_inline}
                    </td>
                </tr>"""

        html += get_row_html("4. LOADING", "", "", is_header=True)
        html += get_row_html("fc'", f"{fc_val:.0f}", "ksc")
        html += get_row_html("Load (Wu)", f"{wu:,.0f}", "kg/m²", is_highlight=True)
        
        html += '</table>'
        html += f'<div class="sheet-footer">Date: {pd.Timestamp.now().strftime("%d-%b-%Y")}</div>'
        html += '</div>'

        st.markdown(html, unsafe_allow_html=True)
