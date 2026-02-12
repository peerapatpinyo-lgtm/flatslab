# tab_drawings.py
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pandas as pd
import numpy as np

# ==========================================
# 1. GRAPHICS ENGINE & UTILS
# ==========================================
def draw_dim(ax, p1, p2, text, offset=0, color='#263238', is_vert=False, font_size=9, style='standard', check_pass=True):
    """Render architectural dimensions with professional styling."""
    x1, y1 = p1
    x2, y2 = p2
    
    # Determine text position and rotation
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

    # Extension Lines (Light gray)
    ext_kw = dict(color=color, lw=0.5, ls='-', alpha=0.3)
    if is_vert:
        ax.plot([p1[0], x1], [p1[1], y1], **ext_kw)
        ax.plot([p2[0], x2], [p2[1], y2], **ext_kw)
    else:
        ax.plot([p1[0], x1], [p1[1], y1], **ext_kw)
        ax.plot([p2[0], x2], [p2[1], y2], **ext_kw)

    # Main Dimension Line
    arrow_style = '<|-|>' if style == 'standard' else '|-|'
    line_col = color if check_pass else '#d32f2f' # Red if dimension is critical/failed
    
    ax.annotate('', xy=(x1, y1), xytext=(x2, y2),
                arrowprops=dict(arrowstyle=arrow_style, color=line_col, lw=0.8, mutation_scale=10))
    
    # Text Label (Background to hide lines underneath)
    ax.text(txt_pos[0], txt_pos[1], text, 
            color=line_col, fontsize=font_size, ha=ha, va=va, rotation=rot, 
            fontfamily='monospace', fontweight='bold', zorder=20,
            bbox=dict(facecolor='white', alpha=0.85, edgecolor='none', pad=1.0))

def draw_boundary_tag(ax, x, y, text, rotation=0):
    """Professional boundary condition tags."""
    is_edge = "EDGE" in text
    bg_col = "#ffebee" if is_edge else "#f5f5f5"
    txt_col = "#c62828" if is_edge else "#78909c"
    border_col = "#ef9a9a" if is_edge else "#cfd8dc"
    
    ax.text(x, y, text, ha='center', va='center', rotation=rotation,
            fontsize=7, color=txt_col, fontweight='bold',
            bbox=dict(facecolor=bg_col, edgecolor=border_col, alpha=1.0, pad=3, boxstyle="round,pad=0.3"))

# ==========================================
# 2. ENGINEERING LOGIC (ACI 318)
# ==========================================
def check_aci_drop_panel(drop_w, drop_l, drop_h, L1, L2, c1, c2, h_slab):
    """
    Performs rigorous ACI 318 checks for Drop Panels.
    Returns a dictionary with status and specific required values.
    """
    # 1. Clear Spans
    Ln_x = L1 - (c1/100.0)
    Ln_y = L2 - (c2/100.0)
    
    # 2. Extension Requirements (Ln/6 from face of support)
    # Convert everything to cm for comparison
    req_ext_x = (Ln_x * 100) / 6.0
    req_ext_y = (Ln_y * 100) / 6.0
    
    # Total Required Width/Length (Assuming symmetric drop centered on column)
    req_width = c1 + (2 * req_ext_x)
    req_length = c2 + (2 * req_ext_y)
    
    # 3. Depth Requirement (h_slab/4 projection)
    req_proj = h_slab / 4.0
    
    # 4. Status Checks
    pass_width = drop_w >= req_width - 1.0 # Allow 1cm tolerance
    pass_length = drop_l >= req_length - 1.0
    pass_depth = drop_h >= req_proj - 0.1
    
    is_structural = pass_width and pass_length and pass_depth
    
    reasons = []
    if not pass_width: reasons.append(f"Width < {req_width:.0f}cm")
    if not pass_length: reasons.append(f"Length < {req_length:.0f}cm")
    if not pass_depth: reasons.append(f"Depth < {req_proj:.1f}cm")
    
    return {
        "is_structural": is_structural,
        "pass_dim": pass_width and pass_length,
        "pass_depth": pass_depth,
        "req_width": req_width,
        "req_length": req_length,
        "req_proj": req_proj,
        "reasons": reasons,
        "status_label": "STRUCTURAL DROP" if is_structural else "SHEAR CAP ONLY"
    }

# ==========================================
# 3. HTML REPORT GENERATOR
# ==========================================
def get_report_html(data_dict, aci_result):
    """Generates a professional engineering summary table."""
    
    def row(label, val, unit, style='normal', tooltip=""):
        # Styles: normal, header, subheader, highlight, alert, success
        bg, txt, w = "#fff", "#000", "normal"
        
        if style == 'header':
            bg, txt, w = "#37474f", "#fff", "bold"
            return f"<tr style='background:{bg}; color:{txt};'><td colspan='3' style='padding:6px; font-weight:{w}; border-top:2px solid #000;'>{label}</td></tr>"
        
        if style == 'highlight': bg = "#f1f8e9"
        if style == 'alert': bg, txt = "#ffebee", "#c62828"
        if style == 'success': bg, txt = "#e8f5e9", "#2e7d32"
        if style == 'subheader': bg, txt, w = "#eceff1", "#455a64", "bold"

        val_str = f"{val}"
        return f"""
        <tr style="background-color: {bg}; border-bottom: 1px solid #cfd8dc;">
            <td style="padding: 5px 8px; font-size: 0.85rem; color: #546e7a;">{label}</td>
            <td style="padding: 5px 8px; font-size: 0.9rem; font-family: monospace; text-align: right; color: {txt}; font-weight: {w if w!='normal' else 'bold'};">{val_str}</td>
            <td style="padding: 5px 8px; font-size: 0.75rem; color: #90a4ae;">{unit}</td>
        </tr>"""

    h_s = data_dict['h_slab']
    h_d = data_dict['h_drop']
    
    html = '<div style="font-family: sans-serif; border: 1px solid #cfd8dc; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">'
    
    # 1. GEOMETRY
    html += "<table style='width:100%; border-collapse:collapse;'>"
    html += row("1. GEOMETRY DATA", "", "", "header")
    html += row("Panel Type", data_dict['type'].upper(), "", "highlight")
    html += row("Slab Thickness (h)", f"{h_s:.0f}", "cm")
    html += row("Effective Depth (d)", f"{data_dict['d_eff']:.2f}", "cm")
    html += row("Clear Span (Ln)", f"{data_dict['ln']:.2f}", "m")

    # 2. DROP PANEL ANALYSIS
    if data_dict['has_drop']:
        aci = aci_result
        status_style = 'success' if aci['is_structural'] else 'alert'
        
        html += row("2. DROP PANEL CHECK (ACI 318)", "", "", "header")
        
        # Dimensions Comparison
        html += row("<b>Dimensions</b> (Actual)", f"{data_dict['drop_w']:.0f} x {data_dict['drop_l']:.0f}", "cm")
        if not aci['pass_dim']:
             html += row("<i>Required (Min)</i>", f"{aci['req_width']:.0f} x {aci['req_length']:.0f}", "cm", "alert")
        
        # Depth Comparison
        html += row("<b>Projection</b> (Actual)", f"{h_d:.0f}", "cm")
        if not aci['pass_depth']:
            html += row("<i>Required (h/4)</i>", f"{aci['req_proj']:.1f}", "cm", "alert")
        
        # Final Status
        html += row("<b>DESIGN STATUS</b>", aci['status_label'], "", status_style)
        
        if not aci['is_structural']:
             reason_str = "<br>".join([f"• {r}" for r in aci['reasons']])
             html += f"""
             <tr style="background-color: #ffebee;">
                <td colspan="3" style="padding: 8px; font-size: 0.8rem; color: #b71c1c; font-style: italic;">
                    <b>ACI Non-Compliance:</b><br>{reason_str}
                </td>
             </tr>"""
    else:
        html += row("2. DROP PANEL", "NONE", "", "header")

    # 3. LOADS
    html += row("3. MATERIAL & LOAD", "", "", "header")
    html += row("Concrete (fc')", f"{data_dict['fc']:.0f}", "ksc")
    html += row("Ultimate Load (Wu)", f"{data_dict['wu']:,.0f}", "kg/m²", "highlight")
    
    html += "</table></div>"
    return html

# ==========================================
# 4. MAIN RENDERER
# ==========================================
def render(L1, L2, c1_w, c2_w, h_slab, lc, cover, d_eff, 
           drop_data=None, moment_vals=None, 
           mat_props=None, loads=None, 
           col_type="interior"):
    
    # --- 4.1 Data Sanitization ---
    if drop_data is None: drop_data = {'has_drop': False, 'width': 0, 'length': 0, 'depth': 0}
    mat_props = mat_props or {'fc': 240}
    loads = loads or {'w_u': 0}
    
    # Safe Defaults
    h_slab = h_slab if h_slab else 20
    cover = cover if cover else 2.5
    d_eff = d_eff if d_eff else (h_slab - cover - 1.0)
    lc = lc if lc else 3.0
    
    # Geometry Prep
    c1_m, c2_m = c1_w/100.0, c2_w/100.0
    Ln_x = L1 - c1_m
    Ln_y = L2 - c2_m
    Ln_max = max(Ln_x, Ln_y)
    
    # Drop Data
    has_drop = drop_data.get('has_drop')
    drop_w = drop_data.get('width', 0)
    drop_l = drop_data.get('length', 0)
    drop_h = drop_data.get('depth', 0) # Projection
    
    # Run ACI Analysis
    aci_res = check_aci_drop_panel(drop_w, drop_l, drop_h, L1, L2, c1_w, c2_w, h_slab) if has_drop else None

    # --- 4.2 Streamlit Layout ---
    col_draw, col_info = st.columns([0.65, 0.35], gap="medium")

    with col_draw:
        # ------------------------------------------------
        # DRAWING 1: PLAN VIEW
        # ------------------------------------------------
        st.markdown(f"##### 📐 PLAN VIEW: {col_type.upper()}")
        
        # Setup Figure
        fig, ax = plt.subplots(figsize=(8, 6.5))
        margin = 1.2
        ax.set_xlim(-margin, L1 + margin)
        ax.set_ylim(-margin, L2 + margin)
        ax.axis('off')
        ax.set_aspect('equal')

        # Grid Lines
        ax.plot([-margin, L1+margin], [L2/2, L2/2], color='#cfd8dc', ls='-.', lw=0.8, zorder=0)
        ax.plot([L1/2, L1/2], [-margin, L2+margin], color='#cfd8dc', ls='-.', lw=0.8, zorder=0)

        # Slab Panel Background
        ax.add_patch(patches.Rectangle((0, 0), L1, L2, fc='white', ec='#455a64', lw=1.5, zorder=1))

        # Render Elements at 4 corners (representing continuous/edge)
        centers = [(0,0), (L1,0), (0,L2), (L1,L2)]
        for cx, cy in centers:
            # 1. Drop Panel
            if has_drop:
                # Color Logic
                if aci_res['is_structural']:
                    dp_fc, dp_ec, dp_ls = '#e3f2fd', '#0288d1', '--' # Good (Blue)
                else:
                    dp_fc, dp_ec, dp_ls = '#fff3e0', '#e65100', '--' # Warning (Orange)
                
                # Draw Drop
                dp_w_m, dp_l_m = drop_w/100.0, drop_l/100.0
                ax.add_patch(patches.Rectangle(
                    (cx - dp_w_m/2, cy - dp_l_m/2), dp_w_m, dp_l_m,
                    fc=dp_fc, ec=dp_ec, lw=1.0, ls=dp_ls, zorder=2
                ))

                # Annotation (Only on Design Column: Top-Left)
                if cx == 0 and cy == L2:
                    # Size Label
                    lbl = f"DROP: {drop_w:.0f}x{drop_l:.0f}"
                    ax.text(cx, cy - dp_l_m/2 - 0.25, lbl, ha='center', va='top', 
                            fontsize=8, color=dp_ec, fontweight='bold', 
                            bbox=dict(fc='white', ec='none', alpha=0.7, pad=0))
                    
                    # Status Label (If Fail)
                    if not aci_res['is_structural']:
                        fail_txt = "⚠️ SHEAR CAP"
                        if not aci_res['pass_dim']: fail_txt += "\n(TOO SMALL)"
                        elif not aci_res['pass_depth']: fail_txt += "\n(TOO THIN)"
                        
                        ax.text(cx, cy - dp_l_m/2 - 0.6, fail_txt, ha='center', va='top', 
                                fontsize=7, color='#d32f2f', fontweight='bold')

            # 2. Column
            ax.add_patch(patches.Rectangle((cx-c1_m/2, cy-c2_m/2), c1_m, c2_m, fc='#546e7a', ec='#263238', zorder=5))

        # Boundary Labels
        lbls = {"top": "CONTINUOUS", "bot": "CONTINUOUS", "left": "CONTINUOUS", "right": "CONTINUOUS"}
        if col_type == 'edge': lbls["left"] = "BUILDING EDGE"
        elif col_type == 'corner': lbls["left"] = "BUILDING EDGE"; lbls["top"] = "BUILDING EDGE"
        
        draw_boundary_tag(ax, -0.8, L2/2, lbls["left"], 90)
        draw_boundary_tag(ax, L1+0.8, L2/2, lbls["right"], 90)
        draw_boundary_tag(ax, L1/2, L2+0.8, lbls["top"])
        draw_boundary_tag(ax, L1/2, -0.8, lbls["bot"])

        # Dimensions
        draw_dim(ax, (0, L2), (L1, L2), f"L1 = {L1:.2f} m", offset=0.6)
        draw_dim(ax, (L1, 0), (L1, L2), f"L2 = {L2:.2f} m", offset=0.6, is_vert=True)
        draw_dim(ax, (c1_m/2, L2/3), (L1-c1_m/2, L2/3), f"Ln = {Ln_x:.2f} m", color='#2e7d32', style='clear')

        st.pyplot(fig, use_container_width=True)

        # ------------------------------------------------
        # DRAWING 2: SECTION VIEW
        # ------------------------------------------------
        st.markdown(f"##### 🏗️ SECTION A-A")
        fig_s, ax_s = plt.subplots(figsize=(8, 3.5))
        
        # Scaling params
        view_w = 250 # cm width of view
        view_h_top = h_slab + 30
        view_h_bot = -100
        
        # 1. Column
        ax_s.add_patch(patches.Rectangle((-c1_w/2, -200), c1_w, 200+h_slab, fc='#546e7a', ec='black', zorder=2))
        
        # 2. Slab
        ax_s.add_patch(patches.Rectangle((-view_w/2, 0), view_w, h_slab, fc='white', ec='black', hatch='///', lw=1.2, zorder=3))
        
        # 3. Drop Panel
        y_bot_dim = 0
        if has_drop:
            # Color logic same as plan
            if aci_res['is_structural']:
                ds_fc, ds_ec, ds_hatch = 'white', 'black', '///'
                ds_ls = '-'
            else:
                ds_fc, ds_ec, ds_hatch = '#fff3e0', '#e65100', None
                ds_ls = '--'
            
            draw_dw = min(view_w * 0.6, drop_w)
            
            # The Drop
            ax_s.add_patch(patches.Rectangle(
                (-draw_dw/2, -drop_h), draw_dw, drop_h, 
                fc=ds_fc, ec=ds_ec, hatch=ds_hatch, ls=ds_ls, zorder=3
            ))
            
            y_bot_dim = -drop_h
            # Dimension for Drop Depth
            draw_dim(ax_s, (draw_dw/2 + 15, 0), (draw_dw/2 + 15, -drop_h), f"{drop_h}cm", is_vert=True, color='#0277bd')

            # Fail Label in Section
            if not aci_res['is_structural']:
                ax_s.text(0, -drop_h - 10, "(NON-STRUCTURAL / SHEAR CAP)", ha='center', va='top', 
                          fontsize=8, color='#e65100', fontweight='bold')

        # 4. Rebar (Symbolic)
        rb_y = h_slab - cover - 0.5
        ax_s.plot([-view_w/2+10, view_w/2-10], [rb_y, rb_y], color='#d32f2f', lw=3, ls='-', zorder=4)
        ax_s.text(view_w/2-10, rb_y+2, "Main Bar", color='#d32f2f', fontsize=7, ha='right')

        # 5. Dimensions
        draw_dim(ax_s, (-view_w/2 - 10, 0), (-view_w/2 - 10, h_slab), f"h={h_slab:.0f}", is_vert=True)
        draw_dim(ax_s, (view_w/4, rb_y), (view_w/4, y_bot_dim), f"d={d_eff:.2f}", is_vert=True, color='#c62828')

        ax_s.set_xlim(-view_w/2 - 30, view_w/2 + 30)
        ax_s.set_ylim(view_h_bot, view_h_top)
        ax_s.axis('off')
        ax_s.set_aspect('equal')
        
        st.pyplot(fig_s, use_container_width=True)

    with col_info:
        # ------------------------------------------------
        # DATA REPORT
        # ------------------------------------------------
        # Pack data for report
        rpt_data = {
            'type': col_type,
            'h_slab': h_slab,
            'd_eff': d_eff,
            'ln': Ln_max,
            'has_drop': has_drop,
            'drop_w': drop_w,
            'drop_l': drop_l,
            'h_drop': drop_h,
            'fc': mat_props.get('fc', 240),
            'wu': loads.get('w_u', 0)
        }
        
        st.markdown(get_report_html(rpt_data, aci_res), unsafe_allow_html=True)
        
        if has_drop and not aci_res['is_structural']:
            st.info("""
            **💡 Engineer's Note:** To upgrade this to a **Structural Drop Panel**:
            1. Ensure extension $\ge L_n/6$ from support face.
            2. Ensure projection $\ge h_{slab}/4$.
            """, icon="👷‍♂️")
