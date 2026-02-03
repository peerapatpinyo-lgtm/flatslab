import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pandas as pd
import numpy as np

# ==========================================
# 1. HELPER: DIMENSIONS (No changes here)
# ==========================================
def draw_dim(ax, p1, p2, text, offset=0, color='#000000', is_vert=False, font_size=10, style='standard'):
    """Render architectural dimensions."""
    x1, y1 = p1
    x2, y2 = p2
    
    if is_vert:
        x1 += offset; x2 += offset
        ha, va, rot = 'center', 'center', 90
        sign = 1 if offset > 0 else -1
        txt_x = x1 + (0.35 * sign) 
        txt_pos = (txt_x, (y1+y2)/2)
    else:
        y1 += offset; y2 += offset
        ha, va, rot = 'center', 'center', 0
        sign = 1 if offset > 0 else -1
        txt_y = y1 + (0.35 * sign)
        txt_pos = ((x1+x2)/2, txt_y)

    # Extension Lines
    ext_kw = dict(color=color, lw=0.5, ls='-', alpha=0.5)
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
    
    # Text Label
    ax.text(txt_pos[0], txt_pos[1], text, 
            color=color, fontsize=font_size, ha=ha, va=va, rotation=rot, 
            fontfamily='monospace', fontweight='bold', zorder=20,
            bbox=dict(facecolor='white', alpha=1.0, edgecolor='none', pad=2.0))

# ==========================================
# 2. HELPER: VISUAL ANNOTATIONS
# ==========================================
def draw_boundary_label(ax, x, y, text, rotation=0):
    """Draws a tag indicating if the side is Continuous or Edge."""
    if "EDGE" in text:
        bg_col = "#ffebee" # Light Red
        txt_col = "#c62828"
    else:
        bg_col = "#eceff1" # Light Grey
        txt_col = "#78909c"
        
    ax.text(x, y, text, ha='center', va='center', rotation=rotation,
            fontsize=9, color=txt_col, fontweight='bold',
            bbox=dict(facecolor=bg_col, edgecolor='none', alpha=0.8, pad=3, boxstyle="round,pad=0.3"))

def draw_revision_cloud(ax, x, y, width, height):
    """
    Draws a single, circular, bubbly 'Cloud' style loop around the target column.
    """
    # 1. Create a base shape that is a simple Ellipse.
    # This ensures a perfectly round/oval base without any complex corners.
    cloud = patches.Ellipse(
        (x, y), width, height,
        ec='#ff9800', # Orange
        fc='none',    # No fill
        lw=2.0,       # Line width
        zorder=15
    )
    
    # 2. TUNED SKETCH PARAMETERS for "Bubbly Cloud" look on an ellipse
    # scale: Amplitude of the bubbles (Higher = bigger bubbles)
    # length: Length of each bubble arc (Shorter = more, tighter bubbles)
    # randomness: Variation in bubble size
    
    # These params create a tight, frequent looping pattern along the ellipse path.
    # scale=3.0 gives good bubble height.
    # length=15.0 creates frequent, short arcs.
    cloud.set_sketch_params(scale=3.0, length=15.0, randomness=5.0)
    
    ax.add_patch(cloud)
    
    # Label (Centered above the cloud)
    ax.text(x, y + height/2 + 0.6, "DESIGN COL.", 
            color='#ef6c00', fontsize=8, fontweight='bold', ha='center', va='bottom',
            fontfamily='Comic Sans MS')

# ==========================================
# 3. HELPER: HTML TABLE (No changes here)
# ==========================================
def get_row_html(label, value, unit, is_header=False, is_highlight=False):
    if is_header:
        return f"""
        <tr style="background-color: #37474f; color: white;">
            <td colspan="3" style="padding: 10px; font-weight: 700; font-size: 0.95rem; letter-spacing: 1px; border-top: 2px solid #000;">{label}</td>
        </tr>"""
    
    bg = "#e8f5e9" if is_highlight else "#ffffff"
    col_val = "#1b5e20" if is_highlight else "#000000"
    w_val = "800" if is_highlight else "600"
    
    return f"""
    <tr style="background-color: {bg}; border-bottom: 1px solid #eceff1;">
        <td style="padding: 6px 12px; color: #455a64; font-weight: 500; font-size: 0.9rem;">{label}</td>
        <td style="padding: 6px 12px; text-align: right; color: {col_val}; font-weight: {w_val}; font-family: 'Consolas', monospace; font-size: 0.9rem;">{value}</td>
        <td style="padding: 6px 12px; color: #90a4ae; font-size: 0.8rem;">[{unit}]</td>
    </tr>"""

# ==========================================
# 4. MAIN RENDERER (No changes to logic, just calling the updated function)
# ==========================================
def render(L1, L2, c1_w, c2_w, h_slab, lc, cover, d_eff, 
           drop_data=None, moment_vals=None, 
           mat_props=None, loads=None, 
           col_type="interior"):
    
    # --- 4.1 Data Prep ---
    if drop_data is None: drop_data = {'has_drop': False, 'width': 0, 'length': 0, 'depth': 0}
    if mat_props is None: mat_props = {}
    if loads is None: loads = {}
    
    c1_m, c2_m = c1_w/100.0, c2_w/100.0
    Ln_x = L1 - c1_m
    Ln_y = L2 - c2_m
    
    has_drop = drop_data.get('has_drop')
    drop_w_m = drop_data.get('width', 0)/100.0
    drop_l_m = drop_data.get('length', 0)/100.0
    h_drop = drop_data.get('depth', 0)
    
    fc = mat_props.get('fc', 0)
    fy = mat_props.get('fy', 0)
    wu = loads.get('w_u', 0)

    # --- 4.2 Styles ---
    st.markdown("""
    <style>
        .sheet-container {
            font-family: 'Segoe UI', sans-serif;
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
        .sheet-table { width: 100%; border-collapse: collapse; }
        .sheet-footer {
            padding: 15px; background-color: #f5f5f5; border-top: 2px solid #263238;
            font-size: 0.75rem; color: #607d8b; line-height: 1.5;
        }
    </style>
    """, unsafe_allow_html=True)

    # --- 4.3 Layout ---
    col_draw, col_data = st.columns([1.8, 1])

    # === LEFT: ENGINEERING DRAWINGS ===
    with col_draw:
        # ------------------------------------
        # A. PLAN VIEW
        # ------------------------------------
        st.markdown(f"##### 📐 PLAN VIEW: {col_type.upper()} PANEL")
        
        fig, ax = plt.subplots(figsize=(10, 8.5))
        
        # 1. Logic for Boundary & Cloud Position
        lbl_top = "CONTINUOUS"
        lbl_bot = "CONTINUOUS"
        lbl_left = "CONTINUOUS"
        lbl_right = "CONTINUOUS"
        
        # Determine Target Column for the Cloud (Default Top-Left (0, L2))
        target_cloud_pos = (0, L2) 
        
        if col_type == 'edge':
            lbl_left = "BUILDING EDGE" 
            # For Edge, highlight the Edge Column (Left side)
            target_cloud_pos = (0, L2) 
        elif col_type == 'corner':
            lbl_left = "BUILDING EDGE"
            lbl_top = "BUILDING EDGE"
            # For Corner, highlight the Corner Column (Top-Left)
            target_cloud_pos = (0, L2)
        else: # Interior
            # For Interior, highlight Top-Left as representative
             target_cloud_pos = (0, L2)

        # 2. Grid Lines & Slab
        ax.plot([-1, L1+1], [L2/2, L2/2], color='#cfd8dc', ls='-.', lw=1.0)
        ax.plot([L1/2, L1/2], [-1, L2+1], color='#cfd8dc', ls='-.', lw=1.0)
        
        # Main Slab
        ax.add_patch(patches.Rectangle((0, 0), L1, L2, fc='#ffffff', ec='#263238', lw=2.0, zorder=1))

        # 3. Supports (Column/Drop)
        centers = [(0,0), (L1,0), (0,L2), (L1,L2)]
        for cx, cy in centers:
            if has_drop:
                ax.add_patch(patches.Rectangle((cx-drop_w_m/2, cy-drop_l_m/2), drop_w_m, drop_l_m, 
                                               fc='#e1f5fe', ec='#039be5', lw=1.0, ls='--', zorder=2))
            ax.add_patch(patches.Rectangle((cx-c1_m/2, cy-c2_m/2), c1_m, c2_m, 
                                           fc='#37474f', ec='black', zorder=5))

        # 4. DRAW THE REVISION CLOUD (UPDATED)
        # Draw around the target column coordinate
        # Cloud size roughly 3x column size for a good clear circle
        cloud_w = max(c1_m * 3.0, 1.2) 
        cloud_h = max(c2_m * 3.0, 1.2)
        # Use a square aspect ratio for the cloud to make it circular
        cloud_size = max(cloud_w, cloud_h)
        draw_revision_cloud(ax, target_cloud_pos[0], target_cloud_pos[1], cloud_size, cloud_size)

        # 5. Draw Context Labels
        draw_boundary_label(ax, L1/2, L2 + 1.8, lbl_top)       # Top
        draw_boundary_label(ax, L1/2, -1.8, lbl_bot)           # Bottom
        draw_boundary_label(ax, -1.8, L2/2, lbl_left, rotation=90)  # Left
        draw_boundary_label(ax, L1 + 1.8, L2/2, lbl_right, rotation=90) # Right

        # 6. Dimensions
        draw_dim(ax, (0, L2), (L1, L2), f"Lx = {L1:.2f} m", offset=1.0, is_vert=False, font_size=11)
        draw_dim(ax, (L1, 0), (L1, L2), f"Ly = {L2:.2f} m", offset=1.0, is_vert=True, font_size=11)
        
        draw_dim(ax, (c1_m/2, 0), (L1 - c1_m/2, 0), f"Ln = {Ln_x:.2f} m", 
                 offset=-1.0, is_vert=False, color='#2e7d32', font_size=11, style='clear')
        draw_dim(ax, (0, c2_m/2), (0, L2 - c2_m/2), f"Ln = {Ln_y:.2f} m", 
                 offset=-1.0, is_vert=True, color='#2e7d32', font_size=11, style='clear')

        if has_drop:
            draw_dim(ax, (L1 - drop_w_m/2, L2), (L1 + drop_w_m/2, L2), 
                     f"Drop: {drop_data['width']:.0f} cm", offset=0.5, color='#0277bd', font_size=9)
            draw_dim(ax, (L1, L2 - drop_l_m/2), (L1, L2 + drop_l_m/2), 
                     f"Drop: {drop_data['length']:.0f} cm", offset=0.5, is_vert=True, color='#0277bd', font_size=9)

        # Label S-01
        ax.text(L1/2, L2/2 - 0.4, "S-01", ha='center', fontsize=18, fontweight='bold', color='#263238',
                bbox=dict(boxstyle="circle,pad=0.4", fc="white", ec="#263238", lw=1.5, zorder=10))

        margin = 2.2 
        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_xlim(-margin, L1+margin)
        ax.set_ylim(-margin, L2+margin)
        st.pyplot(fig, use_container_width=True)

        # ------------------------------------
        # B. SECTION VIEW
        # ------------------------------------
        st.markdown(f"##### 🏗️ SECTION A-A (H = {lc:.2f} m)")
        fig_s, ax_s = plt.subplots(figsize=(10, 5)) 
        
        cut_w = 220 
        col_h_draw = 180
        
        # Slab & Drop
        ax_s.add_patch(patches.Rectangle((-cut_w/2, 0), cut_w, h_slab, fc='#ffffff', ec='black', hatch='///', lw=1.2))
        y_bot = 0
        if has_drop:
            dw = min(cut_w*0.6, drop_data['width'])
            ax_s.add_patch(patches.Rectangle((-dw/2, -h_drop), dw, h_drop, fc='#ffffff', ec='black', hatch='///', lw=1.2))
            y_bot = -h_drop
            draw_dim(ax_s, (dw/2+12, 0), (dw/2+12, -h_drop), f"{h_drop} cm", offset=0, is_vert=True, color='#0277bd')

        # Column & Storey Height
        ax_s.add_patch(patches.Rectangle((-c1_w/2, -col_h_draw), c1_w, col_h_draw + y_bot, fc='#546e7a', ec='black'))
        ax_s.plot([-c1_w, c1_w], [-col_h_draw, -col_h_draw], color='black', lw=1.5, ls='--')
        ax_s.text(0, -col_h_draw - 20, "LOWER FLOOR LEVEL", ha='center', fontsize=9, color='#455a64')

        draw_dim(ax_s, (-c1_w/2 - 40, 0), (-c1_w/2 - 40, -col_h_draw), 
                 f"Storey Height: {lc:.2f} m", offset=0, is_vert=True, color='#e65100', font_size=11)

        # Rebar & Dims
        d_line = h_slab - cover - 0.6
        ax_s.plot([-cut_w/2+20, cut_w/2-20], [d_line, d_line], color='#d32f2f', lw=3.0)
        draw_dim(ax_s, (-cut_w/2-20, 0), (-cut_w/2-20, h_slab), f"h={h_slab:.0f}", offset=0, is_vert=True)
        draw_dim(ax_s, (cut_w/3, d_line), (cut_w/3, y_bot), f"d={d_eff:.2f}", offset=20, is_vert=True, color='#d32f2f')

        ax_s.set_aspect('equal')
        ax_s.axis('off')
        ax_s.set_ylim(-col_h_draw - 40, h_slab + 35)
        st.pyplot(fig_s, use_container_width=True)

    # === RIGHT: DATA SHEET ===
    with col_data:
        html = ""
        html += '<div class="sheet-container">'
        html += '<div class="sheet-header">Design Data Sheet</div>'
        html += '<table class="sheet-table">'
        
        # Highlight Panel Type
        html += get_row_html("1. GEOMETRY", "", "", is_header=True)
        html += get_row_html("Panel Type", f"{col_type.upper()}", "-", is_highlight=True)
        html += get_row_html("Thickness (h)", f"{h_slab:.0f}", "cm")
        html += get_row_html("Storey Height", f"{lc:.2f}", "m")
        
        html += get_row_html("2. DIMENSIONS", "", "", is_header=True)
        html += get_row_html("C-C Span X", f"{L1:.2f}", "m")
        html += get_row_html("C-C Span Y", f"{L2:.2f}", "m")
        html += get_row_html("Clear Span X", f"{Ln_x:.2f}", "m")
        html += get_row_html("Clear Span Y", f"{Ln_y:.2f}", "m")
        
        if has_drop:
            html += get_row_html("3. DROP PANEL", "", "", is_header=True)
            html += get_row_html("Size", f"{drop_data['width']:.0f}x{drop_data['length']:.0f}", "cm")
            html += get_row_html("Total Depth", f"{h_slab+h_drop:.0f}", "cm")

        html += get_row_html("4. MATERIALS & LOADS", "", "", is_header=True)
        html += get_row_html("Concrete (fc')", f"{fc:.0f}", "ksc")
        html += get_row_html("Factored (Wu)", f"{wu:,.0f}", "kg/m²", is_highlight=True)
        
        html += '</table>'
        
        now_str = pd.Timestamp.now().strftime('%d-%b-%Y')
        html += f"""
        <div class="sheet-footer">
            <b>📝 ENGINEER NOTES:</b><br>
            • Panel Type: <b>{col_type.upper()}</b>.<br>
            • <span style="color:#ef6c00; font-weight:bold;">Orange Cloud</span> indicates Design Column.<br>
            • Date: {now_str}
        </div>
        """
        html += '</div>'

        st.markdown(html, unsafe_allow_html=True)
