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
    # Logic for colors
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
    # Create an Ellipse
    cloud = patches.Ellipse(
        (x, y), width, height,
        ec='#ff6d00', # Bright Orange
        fc='none',    
        lw=2.5,        
        ls='-',
        zorder=15
    )
    # Make it wavy (Sketch params)
    cloud.set_sketch_params(scale=2.0, length=10.0, randomness=5.0)
    ax.add_patch(cloud)
    
    # Label pointing to the cloud
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
    
    # Safety: Handle None or 0 values from main app during initialization
    h_slab = h_slab if h_slab else 20
    cover = cover if cover else 2.5
    d_eff = d_eff if d_eff else (h_slab - cover - 1.0) # Approx default
    lc = lc if lc else 3.0
    
    c1_m, c2_m = c1_w/100.0, c2_w/100.0
    Ln_x = L1 - c1_m
    Ln_y = L2 - c2_m
    
    has_drop = drop_data.get('has_drop')
    drop_w_val = drop_data.get('width', 0) # cm
    drop_l_val = drop_data.get('length', 0) # cm
    h_drop_val = drop_data.get('depth', 0) # cm
    
    # Unit Conversions for Drawing
    drop_w_m = drop_w_val/100.0
    drop_l_m = drop_l_val/100.0
    
    fc = mat_props.get('fc', 0)
    wu = loads.get('w_u', 0)

    # --- 4.2 Styles ---
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

    # --- 4.3 Layout ---
    col_draw, col_data = st.columns([2, 1])

    # === LEFT: ENGINEERING DRAWINGS ===
    with col_draw:
        # ------------------------------------
        # A. PLAN VIEW
        # ------------------------------------
        st.markdown(f"**📐 PLAN VIEW: {col_type.upper()} PANEL**")
        fig, ax = plt.subplots(figsize=(8, 6))
        
        # Determine Labels based on col_type
        # Default Interior
        lbls = {"top": "CONTINUOUS", "bot": "CONTINUOUS", "left": "CONTINUOUS", "right": "CONTINUOUS"}
        
        # Design Column is always Top-Left (0, L2) in this coord system
        target_pos = (0, L2)

        if col_type == 'edge':
            lbls["left"] = "BUILDING EDGE" # Exterior face
        elif col_type == 'corner':
            lbls["left"] = "BUILDING EDGE"
            lbls["top"] = "BUILDING EDGE"

        # Grid & Slab
        margin = 1.5
        ax.plot([-margin, L1+margin], [L2/2, L2/2], color='#b0bec5', ls='-.', lw=0.8) # Grid X
        ax.plot([L1/2, L1/2], [-margin, L2+margin], color='#b0bec5', ls='-.', lw=0.8) # Grid Y
        
        # Main Slab Panel
        ax.add_patch(patches.Rectangle((0, 0), L1, L2, fc='#ffffff', ec='#263238', lw=1.5, zorder=1))

        # Columns
        centers = [(0,0), (L1,0), (0,L2), (L1,L2)]
        for cx, cy in centers:
            # Drop Panel (Plan View - Simplified)
            if has_drop:
                ax.add_patch(patches.Rectangle((cx-drop_w_m/2, cy-drop_l_m/2), drop_w_m, drop_l_m, 
                                             fc='#e1f5fe', ec='#0288d1', lw=0.8, ls='--', zorder=2))
            # Column
            ax.add_patch(patches.Rectangle((cx-c1_m/2, cy-c2_m/2), c1_m, c2_m, 
                                         fc='#455a64', ec='black', zorder=5))

        # Revision Cloud (Focus on Top-Left)
        c_size = max(c1_m, c2_m) * 3.5
        draw_revision_cloud(ax, target_pos[0], target_pos[1], c_size, c_size)

        # Labels
        draw_boundary_label(ax, L1/2, L2 + 1.2, lbls["top"])
        draw_boundary_label(ax, L1/2, -1.2, lbls["bot"])
        draw_boundary_label(ax, -1.2, L2/2, lbls["left"], rotation=90)
        draw_boundary_label(ax, L1 + 1.2, L2/2, lbls["right"], rotation=90)

        # Dims
        draw_dim(ax, (0, L2), (L1, L2), f"{L1:.2f}m", offset=0.8)
        draw_dim(ax, (L1, 0), (L1, L2), f"{L2:.2f}m", offset=0.8, is_vert=True)
        
        # Clear Span
        draw_dim(ax, (c1_m/2, L2/4), (L1 - c1_m/2, L2/4), f"Ln={Ln_x:.2f}m", offset=0, color='#2e7d32', style='clear')
        
        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_xlim(-margin-0.5, L1+margin+0.5)
        ax.set_ylim(-margin-0.5, L2+margin+0.5)
        st.pyplot(fig, use_container_width=True)

        # ------------------------------------
        # B. SECTION VIEW (ENHANCED)
        # ------------------------------------
        st.markdown(f"**🏗️ SECTION A-A** (Storey H = {lc:.2f} m)")
        fig_s, ax_s = plt.subplots(figsize=(8, 4))
        
        cut_w = 250 # cm width of cut for drawing
        col_draw_h = 150 # cm height of column to draw
        
        # 1. Column
        ax_s.add_patch(patches.Rectangle((-c1_w/2, -col_draw_h), c1_w, col_draw_h, fc='#546e7a', ec='black', zorder=2))
        
        # 2. Slab
        ax_s.add_patch(patches.Rectangle((-cut_w/2, 0), cut_w, h_slab, fc='white', ec='black', hatch='//', zorder=3))
        
        # 3. Drop Panel Logic (Structural vs Shear Cap)
        y_bottom_slab = 0
        if has_drop:
            # === LOGIC START: Check Structural Validity ===
            # ACI: Extension >= L/6 (Total Width >= L/3) AND Projection >= h_slab/4
            req_width_cm = (L1 * 100) / 3.0  # Approx L/3 of span
            req_depth_cm = h_slab / 4.0
            
            is_structural_drop = (drop_w_val >= req_width_cm) and (h_drop_val >= req_depth_cm)

            # Determine Style
            if is_structural_drop:
                # ✅ Valid Structural Drop
                dp_style = '-'
                dp_color = 'white'
                dp_edge = 'black'
                dp_hatch = '//'
                dp_alpha = 1.0
                dp_label = None
            else:
                # ⚠️ Shear Cap / Non-Structural
                dp_style = '--'
                dp_color = '#FFF3E0' # Light Orange
                dp_edge = '#E65100'  # Dark Orange
                dp_hatch = None
                dp_alpha = 0.8
                dp_label = "Shear Cap Only\n(Stiffness Ignored)"

            # Draw Drop Panel
            drop_draw_w = min(cut_w * 0.7, drop_w_val) # Clamp for drawing width
            ax_s.add_patch(patches.Rectangle(
                (-drop_draw_w/2, -h_drop_val), drop_draw_w, h_drop_val, 
                fc=dp_color, ec=dp_edge, hatch=dp_hatch, ls=dp_style, alpha=dp_alpha, zorder=3
            ))
            
            y_bottom_slab = -h_drop_val
            draw_dim(ax_s, (drop_draw_w/2 + 10, 0), (drop_draw_w/2 + 10, -h_drop_val), f"{h_drop_val}cm", is_vert=True, color='#0277bd')

            # Add Warning Label if needed
            if dp_label:
                ax_s.annotate(
                    dp_label,
                    xy=(drop_draw_w/2, -h_drop_val/2),
                    xytext=(drop_draw_w/2 + 40, -h_drop_val - 20),
                    arrowprops=dict(arrowstyle='->', color=dp_edge, connectionstyle="arc3,rad=-0.2"),
                    color=dp_edge, fontsize=9, fontweight='bold',
                    bbox=dict(boxstyle="round,pad=0.2", fc="white", ec=dp_edge, alpha=0.9)
                )
            # === LOGIC END ===

        # 4. Rebar (Red Line)
        eff_depth_line = h_slab - cover - 0.5 # Center of bar approx
        ax_s.plot([-cut_w/2 + 10, cut_w/2 - 10], [eff_depth_line, eff_depth_line], color='#d32f2f', lw=2.5, zorder=4)
        
        # 5. Dimensions
        # Slab Thickness
        draw_dim(ax_s, (-cut_w/2 - 15, 0), (-cut_w/2 - 15, h_slab), f"h={h_slab:.0f}cm", is_vert=True)
        # Eff Depth
        draw_dim(ax_s, (cut_w/4, eff_depth_line), (cut_w/4, y_bottom_slab), f"d={d_eff:.2f}cm", is_vert=True, color='#d32f2f')
        # Storey Height
        draw_dim(ax_s, (-c1_w/2 - 30, 0), (-c1_w/2 - 30, -col_draw_h), f"H={lc:.2f}m", is_vert=True, color='#e65100')

        # [IMPORTANT FIX]: Set Limits explicitly
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
            html += get_row_html("Size", f"{drop_w_val:.0f}x{drop_l_val:.0f}", "cm")
            html += get_row_html("Total Depth", f"{h_slab+h_drop_val:.0f}", "cm")

        html += get_row_html("4. LOADING", "", "", is_header=True)
        html += get_row_html("fc'", f"{fc:.0f}", "ksc")
        html += get_row_html("Load (Wu)", f"{wu:,.0f}", "kg/m²", is_highlight=True)
        
        html += '</table>'
        html += f'<div class="sheet-footer">Date: {pd.Timestamp.now().strftime("%d-%b-%Y")}</div>'
        html += '</div>'

        st.markdown(html, unsafe_allow_html=True)
