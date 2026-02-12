# tab_drawings.py
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pandas as pd
import numpy as np

# ==========================================
# 1. CONSTANTS & THEMES (Professional Palette)
# ==========================================
CLR_PRIMARY = '#263238'   # Dark Blue Grey (Main Structure)
CLR_GRID = '#B0BEC5'      # Light Grey (Gridlines)
CLR_DIM = '#455A64'       # Slate Grey (Dimensions)
CLR_PASS = '#0288D1'      # Engineering Blue
CLR_FAIL = '#D32F2F'      # Alert Red
CLR_FOCUS = '#FF6D00'     # Vivid Orange

# ==========================================
# 2. HELPER: ARCHITECTURAL DIMENSIONS
# ==========================================
def draw_dim(ax, p1, p2, text, offset=0, color=CLR_DIM, is_vert=False):
    x1, y1 = p1
    x2, y2 = p2
    
    # Calculate text position and rotation
    if is_vert:
        x1 += offset; x2 += offset
        ha, va, rot = 'center', 'center', 90
        txt_pos = (x1 + (0.5 * (1 if offset > 0 else -1)), (y1+y2)/2)
    else:
        y1 += offset; y2 += offset
        ha, va, rot = 'center', 'center', 0
        txt_pos = ((x1+x2)/2, y1 + (0.5 * (1 if offset > 0 else -1)))

    # Extension lines
    ext_kw = dict(color=color, lw=0.6, alpha=0.3)
    ax.plot([p1[0], x1], [p1[1], y1], **ext_kw)
    ax.plot([p2[0], x2], [p2[1], y2], **ext_kw)

    # Dimension line with arrows
    ax.annotate('', xy=(x1, y1), xytext=(x2, y2),
                arrowprops=dict(arrowstyle='<|-|>', color=color, lw=0.8, mutation_scale=10))
    
    # Label with background mask
    ax.text(txt_pos[0], txt_pos[1], text, color=color, fontsize=9, 
            ha=ha, va=va, rotation=rot, fontweight='bold', family='monospace',
            bbox=dict(facecolor='white', alpha=1.0, edgecolor='none', pad=2))

# ==========================================
# 3. HELPER: ANNOTATIONS & CLOUDS
# ==========================================
def draw_boundary_label(ax, x, y, text, rotation=0):
    is_edge = "EDGE" in text
    ax.text(x, y, text, ha='center', va='center', rotation=rotation,
            fontsize=8, fontweight='bold' if is_edge else 'normal',
            color=CLR_FAIL if is_edge else '#78909C',
            bbox=dict(facecolor='#FFEBEE' if is_edge else '#F5F5F5', 
                      edgecolor=CLR_FAIL if is_edge else '#CFD8DC', 
                      alpha=1.0, pad=4, boxstyle="round,pad=0.3"))

def draw_design_focus(ax, x, y, size):
    """Draws Professional Revision Cloud around the target column."""
    cloud = patches.Ellipse((x, y), size, size, ec=CLR_FOCUS, fc='none', lw=2, ls='-', zorder=15)
    cloud.set_sketch_params(scale=1.5, length=8, randomness=2)
    ax.add_patch(cloud)
    
    ax.annotate("DESIGN\nCOLUMN", xy=(x + size/3, y - size/3), 
                xytext=(x + size*1.1, y - size*0.8),
                arrowprops=dict(arrowstyle="->", color=CLR_FOCUS, connectionstyle="arc3,rad=-0.2"),
                color=CLR_FOCUS, fontsize=9, fontweight='700')

# ==========================================
# 4. MAIN RENDERER
# ==========================================
def render(L1, L2, c1_w, c2_w, h_slab, lc, cover, d_eff, 
           drop_data=None, moment_vals=None, mat_props=None, loads=None, col_type="interior"):
    
    # Input Processing
    drop_data = drop_data or {'has_drop': False, 'width': 0, 'length': 0, 'depth': 0}
    h_slab = h_slab or 20
    c1_m, c2_m = c1_w/100, c2_w/100
    
    # ACI Compliance Logic
    has_drop = drop_data.get('has_drop')
    dw, dl, dh = drop_data.get('width', 0), drop_data.get('length', 0), drop_data.get('depth', 0)
    
    is_structural = False
    fail_reasons = []
    if has_drop:
        req_w = ((L1 - c1_m) * 100 / 6 * 2) + c1_w
        req_l = ((L2 - c2_m) * 100 / 6 * 2) + c2_w
        req_h = h_slab / 4
        
        pass_dim = (dw >= req_w - 0.5) and (dl >= req_l - 0.5)
        pass_h = (dh >= req_h - 0.1)
        is_structural = pass_dim and pass_h
        if not pass_dim: fail_reasons.append("Too Small")
        if not pass_h: fail_reasons.append("Too Thin")

    # Layout
    col_draw, col_data = st.columns([2, 1])

    with col_draw:
        st.subheader(f"📐 Engineering Drawings - {col_type.upper()}")
        
        # --- PLAN VIEW ---
        fig, ax = plt.subplots(figsize=(8, 6.5))
        margin = max(L1, L2) * 0.3
        
        # Boundary Logic Linking
        lbls = {"top": "CONTINUOUS", "left": "CONTINUOUS"}
        if col_type in ['edge', 'corner']: lbls["left"] = "BUILDING EDGE"
        if col_type == 'corner': lbls["top"] = "BUILDING EDGE"

        # Grid & Slab
        ax.plot([-margin, L1+margin], [L2/2, L2/2], color=CLR_GRID, ls='-.', lw=0.8, zorder=0)
        ax.plot([L1/2, L1/2], [-margin, L2+margin], color=CLR_GRID, ls='-.', lw=0.8, zorder=0)
        ax.add_patch(patches.Rectangle((0, 0), L1, L2, fc='white', ec=CLR_PRIMARY, lw=2, zorder=1))

        # Elements
        for cx, cy in [(0,0), (L1,0), (0,L2), (L1,L2)]:
            if has_drop:
                # Professional Styling based on ACI status
                color = CLR_PASS if is_structural else CL_FAIL
                ax.add_patch(patches.Rectangle((cx-dw/200, cy-dl/200), dw/100, dl/100,
                                             fc='#E3F2FD' if is_structural else '#FFEBEE',
                                             ec=color, lw=1.2, ls='-' if is_structural else '--', 
                                             hatch='///' if is_structural else None, zorder=2))
                if cx == 0 and cy == L2: # Design Col Label
                    ax.text(cx, cy - dl/200 - 0.2, f"DROP {dw}x{dl}", ha='center', color=color, 
                            weight='bold', fontsize=8, bbox=dict(fc='white', ec='none', pad=1))
                    if not is_structural:
                        ax.text(cx, cy - dl/200 - 0.5, f"({', '.join(fail_reasons)})", 
                                ha='center', color=CLR_FAIL, fontsize=7, weight='bold')

            ax.add_patch(patches.Rectangle((cx-c1_m/2, cy-c2_m/2), c1_m, c2_m, fc=CLR_PRIMARY, zorder=5))

        # Annotations
        draw_design_focus(ax, 0, L2, max(c1_m, c2_m)*4)
        draw_boundary_label(ax, L1/2, L2 + 1.2, lbls["top"])
        draw_boundary_label(ax, -1.2, L2/2, lbls["left"], 90)
        draw_dim(ax, (0, L2), (L1, L2), f"L1 = {L1:.2f} m", offset=1.0)
        draw_dim(ax, (L1, 0), (L1, L2), f"L2 = {L2:.2f} m", offset=1.0, is_vert=True)

        ax.set_aspect('equal')
        ax.axis('off')
        st.pyplot(fig)

        # --- SECTION VIEW ---
        fig_s, ax_s = plt.subplots(figsize=(8, 3))
        sw = 300
        ax_s.add_patch(patches.Rectangle((-c1_w/2, -100), c1_w, 100+h_slab, fc=CLR_PRIMARY, zorder=2))
        ax_s.add_patch(patches.Rectangle((-sw/2, 0), sw, h_slab, fc='white', ec='black', hatch='///', zorder=3))
        if has_drop:
            ax_s.add_patch(patches.Rectangle((-dw/2, -dh), dw, dh, 
                                           fc='white' if is_structural else '#FFEBEE', 
                                           ec='black' if is_structural else CLR_FAIL, 
                                           hatch='///' if is_structural else None, zorder=3))
        draw_dim(ax_s, (-sw/2 - 20, 0), (-sw/2 - 20, h_slab), f"h={h_slab}", is_vert=True)
        ax_s.set_aspect('equal')
        ax_s.axis('off')
        st.pyplot(fig_s)

    with col_data:
        # Professional HTML Table
        st.markdown(f"""
        <div style="border: 1px solid #CFD8DC; border-radius: 8px; overflow: hidden; font-family: sans-serif;">
            <div style="background: {CLR_PRIMARY}; color: white; padding: 12px; font-weight: bold; text-align: center;">
                DESIGN SUMMARY
            </div>
            <table style="width: 100%; border-collapse: collapse; font-size: 0.9rem;">
                <tr style="background: #F8F9FA; border-bottom: 1px solid #EEE;">
                    <td style="padding: 10px;">Panel Type</td>
                    <td style="text-align: right; padding: 10px; font-weight: bold;">{col_type.upper()}</td>
                </tr>
                <tr style="border-bottom: 1px solid #EEE;">
                    <td style="padding: 10px;">Slab Thickness</td>
                    <td style="text-align: right; padding: 10px;">{h_slab} cm</td>
                </tr>
                {"<tr style='background: " + ("#E8F5E9" if is_structural else "#FFEBEE") + ";'>" +
                  "<td style='padding: 10px; font-weight: bold;'>Drop Status</td>" +
                  "<td style='text-align: right; padding: 10px; font-weight: bold; color: " + 
                  (CLR_PASS if is_structural else CLR_FAIL) + ";'>" + 
                  ("STRUCTURAL" if is_structural else "SHEAR CAP") + "</td></tr>" if has_drop else ""}
            </table>
            <div style="padding: 10px; font-size: 0.75rem; color: #90A4AE; background: #F8F9FA;">
                Checked per ACI 318-19 Standards
            </div>
        </div>
        """, unsafe_allow_html=True)
