# tab_drawings.py
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib as mpl
import pandas as pd
import numpy as np

# ==========================================
# 0. CAD STYLE CONFIGURATION
# ==========================================
# Professional Engineering Palette
CAD_BG = 'white'
CAD_SLAB_EDGE = '#37474F'  # Dark Slate
CAD_SLAB_FILL = '#FFFFFF'
CAD_COL_FILL = '#546E7A'   # Blue Grey
CAD_COL_EDGE = '#263238'
CAD_DIM_COLOR = '#455A64'  # Slate Grey for dimensions
CAD_REBAR = '#C62828'      # Deep Red
CAD_GRID = '#CFD8DC'       # Light Grey

# Drop Panel States
DP_STRUCT_FILL = '#E3F2FD' # Light Blue
DP_STRUCT_EDGE = '#0288D1' # Engineer Blue
DP_FAIL_FILL = '#FFF3E0'   # Warning Orange
DP_FAIL_EDGE = '#E65100'   # Deep Orange

mpl.rcParams['font.family'] = 'sans-serif'
mpl.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']
mpl.rcParams['hatch.linewidth'] = 0.5
mpl.rcParams['hatch.color'] = '#B0BEC5' # Lighter hatch color

# ==========================================
# 1. GRAPHICS UTILS (ENHANCED)
# ==========================================
def draw_dim(ax, p1, p2, text, offset=0, color=CAD_DIM_COLOR, is_vert=False, font_size=9, style='standard'):
    """Render architectural dimensions with high-end CAD styling."""
    x1, y1 = p1
    x2, y2 = p2
    
    if is_vert:
        x1 += offset; x2 += offset
        ha, va, rot = 'center', 'center', 90
        sign = 1 if offset > 0 else -1
        txt_x = x1 + (0.4 * sign) 
        txt_pos = (txt_x, (y1+y2)/2)
        pad_box = 0.8
    else:
        y1 += offset; y2 += offset
        ha, va, rot = 'center', 'center', 0
        sign = 1 if offset > 0 else -1
        txt_y = y1 + (0.4 * sign)
        txt_pos = ((x1+x2)/2, txt_y)
        pad_box = 0.6

    # Extension Lines (Thin, precise)
    ext_kw = dict(color=color, lw=0.5, ls='-', alpha=0.5)
    if is_vert:
        ax.plot([p1[0], x1], [p1[1], y1], **ext_kw)
        ax.plot([p2[0], x2], [p2[1], y2], **ext_kw)
    else:
        ax.plot([p1[0], x1], [p1[1], y1], **ext_kw)
        ax.plot([p2[0], x2], [p2[1], y2], **ext_kw)

    # Main Dimension Line (Sharp arrows)
    arrow_style = '<|-|>' if style == 'standard' else '|-|'
    ax.annotate('', xy=(x1, y1), xytext=(x2, y2),
                arrowprops=dict(arrowstyle=arrow_style, color=color, lw=0.8, mutation_scale=12, shrinkA=0, shrinkB=0))
    
    # Text Label (Clean background)
    ax.text(txt_pos[0], txt_pos[1], text, 
            color=color, fontsize=font_size, ha=ha, va=va, rotation=rot, 
            fontfamily='monospace', fontweight='bold', zorder=20,
            bbox=dict(facecolor='white', alpha=0.9, edgecolor='none', pad=pad_box))

def draw_boundary_tag(ax, x, y, text, rotation=0):
    """Professional boundary condition tags."""
    is_edge = "EDGE" in text
    # Use cleaner colors defined in palette
    bg_col = "#FFEBEE" if is_edge else "#ECEFF1"
    txt_col = "#B71C1c" if is_edge else "#546E7A"
    border_col = "#EF9A9A" if is_edge else "#B0BEC5"
    
    ax.text(x, y, text, ha='center', va='center', rotation=rotation,
            fontsize=7.5, color=txt_col, fontweight='bold', zorder=30,
            bbox=dict(facecolor=bg_col, edgecolor=border_col, lw=0.8, alpha=1.0, pad=4, boxstyle="round,pad=0.4"))

# ==========================================
# 2. ENGINEERING LOGIC (ACI 318)
# ==========================================
def check_aci_drop_panel(drop_w, drop_l, drop_h, L1, L2, c1, c2, h_slab):
    # (Logic remains the same, it was correct)
    Ln_x = L1 - (c1/100.0)
    Ln_y = L2 - (c2/100.0)
    
    req_ext_x_cm = (Ln_x * 100) / 6.0
    req_ext_y_cm = (Ln_y * 100) / 6.0
    
    req_width = c1 + (2 * req_ext_x_cm)
    req_length = c2 + (2 * req_ext_y_cm)
    req_proj = h_slab / 4.0
    
    # Use a small tolerance for floating point comparison
    tol = 0.1 # cm
    pass_width = drop_w >= req_width - tol
    pass_length = drop_l >= req_length - tol
    pass_depth = drop_h >= req_proj - tol
    
    is_structural = pass_width and pass_length and pass_depth
    
    reasons = []
    if not pass_width: reasons.append(f"Width < {req_width:.0f}cm")
    if not pass_length: reasons.append(f"Length < {req_length:.0f}cm")
    if not pass_depth: reasons.append(f"Depth < {req_proj:.1f}cm")
    
    return {
        "is_structural": is_structural,
        "pass_dim": pass_width and pass_length,
        "pass_depth": pass_depth,
        "req_width": req_width, "req_length": req_length, "req_proj": req_proj,
        "reasons": reasons,
        "status_label": "STRUCTURAL" if is_structural else "SHEAR CAP ONLY"
    }

# ==========================================
# 3. HTML REPORT GENERATOR (CLEANER)
# ==========================================
def get_report_html(data_dict, aci_result):
    # (Slightly refined CSS for cleaner look)
    def row(label, val, unit, style='normal'):
        bg, txt, w, border = "#fff", "#263238", "normal", "#ECEFF1"
        if style == 'header': return f"<tr style='background:#455A64; color:white;'><td colspan='3' style='padding:8px; font-weight:bold; letter-spacing:0.5px;'>{label}</td></tr>"
        if style == 'highlight': bg = "#F1F8E9"
        if style == 'alert': bg, txt = "#FFEBEE", "#C62828"
        if style == 'success': bg, txt = "#E8F5E9", "#2E7D32"
        
        return f"<tr style='background:{bg}; border-bottom:1px solid {border};'><td style='padding:6px 8px; color:#546E7A; font-size:0.85rem;'>{label}</td><td style='padding:6px 8px; text-align:right; font-family:monospace; font-weight:{w}; color:{txt}; font-size:0.9rem;'>{val}</td><td style='padding:6px 8px; color:#90A4AE; font-size:0.75rem;'>{unit}</td></tr>"

    h_s, h_d = data_dict['h_slab'], data_dict['h_drop']
    html = '<div style="font-family:sans-serif; border:1px solid #B0BEC5; border-top:3px solid #455A64; box-shadow:0 1px 3px rgba(0,0,0,0.1);">'
    html += "<table style='width:100%; border-collapse:collapse;'>"
    
    # 1. Geometry
    html += row("1. PANEL GEOMETRY", "", "", "header")
    html += row("Type", data_dict['type'].upper(), "", "highlight")
    html += row("Slab Thickness (h)", f"{h_s:.0f}", "cm")
    html += row("Clear Span (Ln_max)", f"{data_dict['ln']:.2f}", "m")

    # 2. Drop Panel
    if data_dict['has_drop']:
        aci = aci_result
        st_style = 'success' if aci['is_structural'] else 'alert'
        html += row("2. DROP PANEL ANALYSIS", "", "", "header")
        html += row("Provided Size", f"{data_dict['drop_w']:.0f}x{data_dict['drop_l']:.0f}", "cm")
        html += row("Provided Projection", f"{h_d:.0f}", "cm")
        html += row("ACI 318 STATUS", aci['status_label'], "", st_style)
        if not aci['is_structural']:
             rs = "<br>• ".join(aci['reasons'])
             html += f"<tr><td colspan='3' style='padding:8px; background:#FFEBEE; color:#C62828; font-size:0.8rem;'><b>Non-Compliance Factors:</b><br>• {rs}</td></tr>"
    else:
        html += row("2. DROP PANEL", "NOT APPLICABLE", "", "header")

    # 3. Loads
    html += row("3. DESIGN LOADS", "", "", "header")
    html += row("Concrete (fc')", f"{data_dict['fc']:.0f}", "ksc")
    html += row("Ultimate Load (Wu)", f"{data_dict['wu']:,.0f}", "kg/m²", "highlight")
    
    html += "</table></div>"
    return html

# ==========================================
# 4. MAIN RENDERER (THE CORE UPGRADE)
# ==========================================
def render(L1, L2, c1_w, c2_w, h_slab, lc, cover, d_eff, 
           drop_data=None, moment_vals=None, mat_props=None, loads=None, col_type="interior"):
    
    # Data Initialization (Same as before)
    if drop_data is None: drop_data = {'has_drop': False, 'width': 0, 'length': 0, 'depth': 0}
    mat_props = mat_props or {'fc': 240}; loads = loads or {'w_u': 0}
    h_slab = h_slab if h_slab else 20; cover = cover if cover else 2.5
    d_eff = d_eff if d_eff else (h_slab - cover - 1.0); lc = lc if lc else 3.0
    c1_m, c2_m = c1_w/100.0, c2_w/100.0
    Ln_x, Ln_y = L1 - c1_m, L2 - c2_m
    
    has_drop = drop_data.get('has_drop')
    drop_w, drop_l, drop_h = drop_data.get('width', 0), drop_data.get('length', 0), drop_data.get('depth', 0)
    
    aci_res = check_aci_drop_panel(drop_w, drop_l, drop_h, L1, L2, c1_w, c2_w, h_slab) if has_drop else None

    # Layout
    col_draw, col_info = st.columns([1.8, 1], gap="large")

    with col_draw:
        # ------------------------------------------------
        # DRAWING 1: CAD PLAN VIEW
        # ------------------------------------------------
        st.markdown(f"### 📐 PLAN VIEW")
        
        # FIX: Significantly increased margin to prevent cut-off
        margin = 2.5 
        fig, ax = plt.subplots(figsize=(9, 7.5)) # Slightly larger figure
        ax.set_xlim(-margin, L1 + margin)
        ax.set_ylim(-margin, L2 + margin)
        ax.set_aspect('equal')
        ax.axis('off')

        # Grid Lines (Subtler)
        ax.plot([-margin, L1+margin], [L2/2, L2/2], color=CAD_GRID, ls='-.', lw=0.6, zorder=0)
        ax.plot([L1/2, L1/2], [-margin, L2+margin], color=CAD_GRID, ls='-.', lw=0.6, zorder=0)

        # Slab Panel (Clean Edge)
        ax.add_patch(patches.Rectangle((0, 0), L1, L2, fc=CAD_SLAB_FILL, ec=CAD_SLAB_EDGE, lw=1.8, zorder=1))

        # Elements Loop
        centers = [(0,0), (L1,0), (0,L2), (L1,L2)]
        for i, (cx, cy) in enumerate(centers):
            is_design_col = (cx == 0 and cy == L2)
            
            # Drop Panel
            if has_drop:
                if aci_res['is_structural']:
                    dp_fc, dp_ec, dp_ls, dp_lw = DP_STRUCT_FILL, DP_STRUCT_EDGE, '-', 1.0
                else:
                    dp_fc, dp_ec, dp_ls, dp_lw = DP_FAIL_FILL, DP_FAIL_EDGE, '--', 1.2
                
                dp_w_m, dp_l_m = drop_w/100.0, drop_l/100.0
                ax.add_patch(patches.Rectangle((cx - dp_w_m/2, cy - dp_l_m/2), dp_w_m, dp_l_m,
                                             fc=dp_fc, ec=dp_ec, lw=dp_lw, ls=dp_ls, zorder=2))

                # Smart Annotation on Design Column
                if is_design_col:
                    lbl_col = dp_ec
                    ax.text(cx, cy - dp_l_m/2 - 0.2, f"DROP {drop_w:.0f}x{drop_l:.0f}", 
                            ha='center', va='top', fontsize=8, color=lbl_col, fontweight='bold',
                            bbox=dict(fc='white', ec=lbl_col, lw=0.5, pad=2))
                    
                    if not aci_res['is_structural']:
                        ax.text(cx, cy - dp_l_m/2 - 0.55, "(SHEAR CAP)", 
                                ha='center', va='top', fontsize=7, color=DP_FAIL_EDGE, fontweight='bold')

            # Column
            ax.add_patch(patches.Rectangle((cx-c1_m/2, cy-c2_m/2), c1_m, c2_m, fc=CAD_COL_FILL, ec=CAD_COL_EDGE, zorder=5))

        # Boundary Tags (Now safe from cut-off due to large margin)
        lbls = {"t": "CONTINUOUS", "b": "CONTINUOUS", "l": "CONTINUOUS", "r": "CONTINUOUS"}
        if 'edge' in col_type: lbls["l"] = "BUILDING EDGE"
        if 'corner' in col_type: lbls["l"] = "BUILDING EDGE"; lbls["t"] = "BUILDING EDGE"
        
        # Position tags further out
        tag_offset = 1.2
        draw_boundary_tag(ax, -tag_offset, L2/2, lbls["l"], 90)
        draw_boundary_tag(ax, L1+tag_offset, L2/2, lbls["r"], 90)
        draw_boundary_tag(ax, L1/2, L2+tag_offset, lbls["t"])
        draw_boundary_tag(ax, L1/2, -tag_offset, lbls["b"])

        # Dimensions (Moved further out)
        dim_offset = 0.8
        draw_dim(ax, (0, L2), (L1, L2), f"L1 = {L1:.2f} m", offset=dim_offset)
        draw_dim(ax, (L1, 0), (L1, L2), f"L2 = {L2:.2f} m", offset=dim_offset, is_vert=True)
        # Clear span inside
        draw_dim(ax, (c1_m/2, L2/5), (L1-c1_m/2, L2/5), f"Ln = {Ln_x:.2f} m", color='#2E7D32', style='clear')

        # Use explicit bbox_inches to prevent clipping just in case
        st.pyplot(fig, use_container_width=True, bbox_inches='tight', pad_inches=0.1)

        # ------------------------------------------------
        # DRAWING 2: CAD SECTION VIEW
        # ------------------------------------------------
        st.markdown(f"### 🏗️ SECTION A-A")
        fig_s, ax_s = plt.subplots(figsize=(8, 4))
        
        # Scaling & Limits
        view_w = 300 # Wider view
        col_h_draw = 180
        
        # FIX: Explicit limits to prevent cut-off of side dimensions
        ax_s.set_xlim(-view_w/2 - 60, view_w/2 + 60)
        ax_s.set_ylim(-col_h_draw - 40, h_slab + 40)
        ax_s.set_aspect('equal')
        ax_s.axis('off')
        
        # 1. Column
        ax_s.add_patch(patches.Rectangle((-c1_w/2, -col_h_draw), c1_w, col_h_draw+h_slab, fc=CAD_COL_FILL, ec=CAD_COL_EDGE, zorder=2))
        
        # 2. Slab with Concrete Stipple Hatch (Circles instead of lines for realism)
        # Note: Matplotlib's default hatch is limited. Using 'ooo' or '...' for concrete look.
        slab_patch = patches.Rectangle((-view_w/2, 0), view_w, h_slab, fc='white', ec=CAD_SLAB_EDGE, lw=1.2, zorder=3)
        slab_patch.set_hatch('...') # Stipple pattern
        ax_s.add_patch(slab_patch)

        # 3. Drop Panel
        y_bot_dim = 0
        if has_drop:
            if aci_res['is_structural']:
                ds_fc, ds_ec, ds_ls = 'white', CAD_SLAB_EDGE, '-'
                ds_hatch = '...'
                ds_lbl_col = CAD_DIM_COLOR
            else:
                ds_fc, ds_ec, ds_ls = DP_FAIL_FILL, DP_FAIL_EDGE, '--'
                ds_hatch = None # No hatch for shear cap
                ds_lbl_col = DP_FAIL_EDGE
            
            draw_dw = min(view_w * 0.65, drop_w)
            drop_patch = patches.Rectangle((-draw_dw/2, -drop_h), draw_dw, drop_h, 
                                           fc=ds_fc, ec=ds_ec, ls=ds_ls, lw=1.2, zorder=3)
            if ds_hatch: drop_patch.set_hatch(ds_hatch)
            ax_s.add_patch(drop_patch)
            
            y_bot_dim = -drop_h
            # Projection Dimension
            draw_dim(ax_s, (draw_dw/2 + 20, 0), (draw_dw/2 + 20, -drop_h), f"Proj. {drop_h:.0f}cm", is_vert=True, color=ds_lbl_col)

            if not aci_res['is_structural']:
                ax_s.text(0, -drop_h - 15, "(SHEAR CAP ONLY)", ha='center', va='top', 
                          fontsize=8, color=DP_FAIL_EDGE, fontweight='bold')

        # 4. Rebar (Clearer representation)
        rb_y = h_slab - cover - 0.5
        ax_s.plot([-view_w/2+20, view_w/2-20], [rb_y, rb_y], color=CAD_REBAR, lw=3, ls='-', zorder=4)
        ax_s.plot([-view_w/2+20], [rb_y], marker='|', color=CAD_REBAR, ms=12, zorder=4) # End hooks marker
        ax_s.plot([view_w/2-20], [rb_y], marker='|', color=CAD_REBAR, ms=12, zorder=4)
        
        # 5. Dimensions (Moved further out)
        draw_dim(ax_s, (-view_w/2 - 30, 0), (-view_w/2 - 30, h_slab), f"h={h_slab:.0f}", is_vert=True)
        draw_dim(ax_s, (-c1_w/2 - 50, 0), (-c1_w/2 - 50, -col_h_draw), f"H={lc:.2f}m", is_vert=True, color='#E65100')

        st.pyplot(fig_s, use_container_width=True, bbox_inches='tight', pad_inches=0.1)

    with col_info:
        # ------------------------------------------------
        # ENGINEER'S SUMMARY
        # ------------------------------------------------
        st.markdown("### 📋 ENGINEER'S SUMMARY")
        rpt_data = {
            'type': col_type, 'h_slab': h_slab, 'd_eff': d_eff, 'ln': max(Ln_x, Ln_y),
            'has_drop': has_drop, 'drop_w': drop_w, 'drop_l': drop_l, 'h_drop': drop_h,
            'fc': mat_props.get('fc', 240), 'wu': loads.get('w_u', 0)
        }
        st.markdown(get_report_html(rpt_data, aci_res), unsafe_allow_html=True)
