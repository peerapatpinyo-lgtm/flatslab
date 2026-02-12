# tab_drawings.py
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib as mpl

# ==========================================
# 0. CONFIG & STYLES (CAD THEME)
# ==========================================
CAD_COLORS = {
    'bg': 'white',
    'slab_fill': '#FFFFFF',
    'slab_edge': '#37474F',
    'col_fill': '#CFD8DC',  
    'col_edge': '#263238',
    'dim': '#455A64',
    'rebar': '#C62828',
    'grid': '#ECEFF1',
    'pass_fill': '#E8F5E9', 'pass_edge': '#2E7D32',
    'fail_fill': '#FFEBEE', 'fail_edge': '#C62828',
    'focus': '#FF6D00' # Orange for Focus Circle
}

mpl.rcParams['font.family'] = 'sans-serif'
mpl.rcParams['font.sans-serif'] = ['Tahoma', 'DejaVu Sans', 'Arial']

# ==========================================
# 1. UTILS: DRAWING HELPERS
# ==========================================
def draw_smart_dim(ax, p1, p2, text, offset=0, is_vert=False, color=CAD_COLORS['dim'], check_pass=True):
    """Draws a professional dimension line."""
    x1, y1 = p1
    x2, y2 = p2
    final_color = color if check_pass else CAD_COLORS['fail_edge']
    
    if is_vert:
        x1 += offset; x2 += offset
        ha, va, rot = 'center', 'center', 90
        sign = 1 if offset > 0 else -1
        txt_pos = (x1 + (0.35 * sign), (y1+y2)/2)
    else:
        y1 += offset; y2 += offset
        ha, va, rot = 'center', 'center', 0
        sign = 1 if offset > 0 else -1
        txt_pos = ((x1+x2)/2, y1 + (0.35 * sign))

    kw_ext = dict(color=final_color, lw=0.5, ls='-', alpha=0.4)
    # Extension Lines
    if is_vert:
        ax.plot([p1[0], x1], [p1[1], y1], **kw_ext)
        ax.plot([p2[0], x2], [p2[1], y2], **kw_ext)
    else:
        ax.plot([p1[0], x1], [p1[1], y1], **kw_ext)
        ax.plot([p2[0], x2], [p2[1], y2], **kw_ext)

    # Arrow Line
    ax.annotate('', xy=(x1, y1), xytext=(x2, y2),
                arrowprops=dict(arrowstyle='<|-|>', color=final_color, lw=0.7, shrinkA=0, shrinkB=0))
    
    # Text Label
    ax.text(txt_pos[0], txt_pos[1], text, 
            color=final_color, fontsize=8, ha=ha, va=va, rotation=rot, 
            fontfamily='monospace', fontweight='bold', zorder=20,
            bbox=dict(facecolor='white', alpha=0.85, edgecolor='none', pad=1.0))

def draw_boundary_tag(ax, x, y, text, rotation=0):
    """Draws boundary condition tags (Edge vs Continuous)."""
    is_edge = "EDGE" in text
    fc = '#FFEBEE' if is_edge else '#F5F5F5' 
    ec = '#EF9A9A' if is_edge else '#B0BEC5'
    tc = '#C62828' if is_edge else '#546E7A'
    weight = 'bold' if is_edge else 'normal'
    
    ax.text(x, y, text, ha='center', va='center', rotation=rotation,
            fontsize=7, color=tc, fontweight=weight, zorder=25,
            bbox=dict(facecolor=fc, edgecolor=ec, alpha=1, pad=4, boxstyle="round,pad=0.3"))

def draw_focus_circle(ax, x, y, r):
    """Draws the FOCUS CIRCLE around the Design Column."""
    # Circle
    circle = patches.Circle((x, y), r, fill=False, edgecolor=CAD_COLORS['focus'], 
                            linestyle='--', linewidth=1.5, zorder=10)
    ax.add_patch(circle)
    
    # Label
    ax.annotate("DESIGN\nCOLUMN", xy=(x + r*0.7, y - r*0.7), xytext=(x + r*1.5, y - r*1.5),
                arrowprops=dict(arrowstyle="->", color=CAD_COLORS['focus'], connectionstyle="arc3,rad=0.2"),
                color=CAD_COLORS['focus'], fontsize=8, fontweight='bold', ha='left')

# ==========================================
# 2. ENGINEERING KERNEL (ACI 318 CHECK)
# ==========================================
def calculate_aci_compliance(drop_w, drop_l, drop_h, L1, L2, c1, c2, h_slab):
    Ln_x = L1 - (c1/100.0)
    Ln_y = L2 - (c2/100.0)
    
    # Required Extension (Ln/6)
    req_ext_x_cm = (Ln_x * 100) / 6.0
    req_ext_y_cm = (Ln_y * 100) / 6.0
    
    # Total Required Size
    req_total_w = c1 + (2 * req_ext_x_cm)
    req_total_l = c2 + (2 * req_ext_y_cm)
    req_proj = h_slab / 4.0
    
    tol = 1.0 
    ok_w = drop_w >= (req_total_w - tol)
    ok_l = drop_l >= (req_total_l - tol)
    ok_h = drop_h >= (req_proj - 0.1)
    
    is_structural = ok_w and ok_l and ok_h
    
    return {
        'is_structural': is_structural,
        'checks': {
            'width': {'req': req_total_w, 'act': drop_w, 'ok': ok_w},
            'length': {'req': req_total_l, 'act': drop_l, 'ok': ok_l},
            'depth': {'req': req_proj, 'act': drop_h, 'ok': ok_h}
        },
        'ln': (Ln_x, Ln_y)
    }

# ==========================================
# 3. HTML REPORT GENERATOR
# ==========================================
def generate_engineering_table(res, geo_data):
    def status_cell(is_ok):
        color = "#2E7D32" if is_ok else "#C62828"
        icon = "✔ PASS" if is_ok else "✘ FAIL"
        bg = "#E8F5E9" if is_ok else "#FFEBEE"
        return f"<td style='color:{color}; background:{bg}; font-weight:bold; text-align:center;'>{icon}</td>"

    html = """
    <style>
        .eng-table { width: 100%; border-collapse: collapse; font-family: sans-serif; font-size: 0.85rem; }
        .eng-table th { background: #455A64; color: white; padding: 8px; text-align: left; }
        .eng-table td { border-bottom: 1px solid #ECEFF1; padding: 6px 8px; color: #37474F; }
        .eng-val { font-family: monospace; font-weight: bold; }
        .sub-txt { font-size: 0.75rem; color: #90A4AE; }
    </style>
    """
    html += "<div style='border: 1px solid #CFD8DC; border-radius: 4px; overflow: hidden;'><table class='eng-table'>"
    
    main_status = "STRUCTURAL DROP PANEL" if res['is_structural'] else "SHEAR CAP ONLY"
    main_color = "#2E7D32" if res['is_structural'] else "#C62828"
    main_bg = "#E8F5E9" if res['is_structural'] else "#FFEBEE"
    
    html += f"<tr style='background:{main_bg}; border-bottom: 2px solid {main_color};'><td colspan='4' style='padding:10px; font-size:1rem; color:{main_color}; font-weight:bold; text-align:center;'>{main_status}</td></tr>"
    html += "<tr><th>Item (ACI 318)</th><th style='text-align:right'>Required</th><th style='text-align:right'>Provided</th><th>Status</th></tr>"
    
    cw = res['checks']['width']
    html += f"<tr><td><b>Width (X)</b><br><span class='sub-txt'>Min = Col + 2(Ln/6)</span></td><td class='eng-val' style='text-align:right'>{cw['req']:.0f}</td><td class='eng-val' style='text-align:right'>{cw['act']:.0f}</td>{status_cell(cw['ok'])}</tr>"
    
    cl = res['checks']['length']
    html += f"<tr><td><b>Length (Y)</b><br><span class='sub-txt'>Min = Col + 2(Ln/6)</span></td><td class='eng-val' style='text-align:right'>{cl['req']:.0f}</td><td class='eng-val' style='text-align:right'>{cl['act']:.0f}</td>{status_cell(cl['ok'])}</tr>"

    cd = res['checks']['depth']
    html += f"<tr><td><b>Projection</b><br><span class='sub-txt'>Min = h_slab/4</span></td><td class='eng-val' style='text-align:right'>{cd['req']:.1f}</td><td class='eng-val' style='text-align:right'>{cd['act']:.1f}</td>{status_cell(cd['ok'])}</tr>"
    
    html += "</table></div>"
    return html

# ==========================================
# 4. MAIN RENDERER (FULL FUNCTIONALITY)
# ==========================================
def render(L1, L2, c1_w, c2_w, h_slab, lc, cover, d_eff, 
           drop_data=None, moment_vals=None, mat_props=None, loads=None, col_type="interior"):
    
    # Defaults & Safety
    if drop_data is None: drop_data = {'has_drop': False, 'width': 0, 'length': 0, 'depth': 0}
    mat_props = mat_props or {'fc': 240}
    loads = loads or {'w_u': 0}
    h_slab = h_slab or 20
    
    c1_m, c2_m = c1_w/100.0, c2_w/100.0
    dw, dl, dh = drop_data.get('width', 0), drop_data.get('length', 0), drop_data.get('depth', 0)
    has_drop = drop_data.get('has_drop')
    
    # Calculate ACI Compliance
    aci_res = calculate_aci_compliance(dw, dl, dh, L1, L2, c1_w, c2_w, h_slab) if has_drop else None

    # Layout
    col_draw, col_data = st.columns([0.65, 0.35], gap="medium")

    with col_draw:
        # ------------------------------------
        # DRAWING 1: PLAN VIEW
        # ------------------------------------
        st.markdown(f"#### 📐 PLAN VIEW")
        
        # Setup Figure with good margins
        margin = max(L1, L2) * 0.35 
        fig, ax = plt.subplots(figsize=(7, 6))
        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_xlim(-margin, L1 + margin)
        ax.set_ylim(-margin, L2 + margin)

        # Grids
        ax.plot([-margin, L1+margin], [L2/2, L2/2], color=CAD_COLORS['grid'], ls='-.', lw=1)
        ax.plot([L1/2, L1/2], [-margin, L2+margin], color=CAD_COLORS['grid'], ls='-.', lw=1)

        # Slab Panel
        ax.add_patch(patches.Rectangle((0, 0), L1, L2, fc='white', ec=CAD_COLORS['slab_edge'], lw=1.5, zorder=1))

        # --- DYNAMIC BOUNDARY LOGIC (LINKED TO DROPDOWN) ---
        # Note: We treat Top-Left (0, L2) as the Design Column
        lbl_left = "CONTINUOUS"
        lbl_top = "CONTINUOUS"
        
        if col_type == 'edge':
            # Edge Column: Top edge is building boundary
            lbl_top = "BUILDING EDGE"
        elif col_type == 'corner':
            # Corner Column: Top and Left are building boundaries
            lbl_top = "BUILDING EDGE"
            lbl_left = "BUILDING EDGE"

        # Render Labels
        draw_boundary_tag(ax, -0.6, L2/2, lbl_left, rotation=90)
        draw_boundary_tag(ax, L1/2, L2+0.6, lbl_top)
        draw_boundary_tag(ax, L1+0.6, L2/2, "CONTINUOUS", rotation=90)
        draw_boundary_tag(ax, L1/2, -0.6, "CONTINUOUS")

        # Draw Elements
        centers = [(0,0), (L1,0), (0,L2), (L1,L2)]
        for cx, cy in centers:
            # Drop Panel
            if has_drop:
                # Color based on Status
                if aci_res['is_structural']:
                    dfc, dec, dls = CAD_COLORS['pass_fill'], CAD_COLORS['pass_edge'], '-'
                else:
                    dfc, dec, dls = CAD_COLORS['fail_fill'], CAD_COLORS['fail_edge'], '--'
                
                dm_w, dm_l = dw/100.0, dl/100.0
                ax.add_patch(patches.Rectangle((cx - dm_w/2, cy - dm_l/2), dm_w, dm_l, 
                                             fc=dfc, ec=dec, ls=dls, lw=1.0, zorder=2))
                
                # Text (Only on Design Column)
                if cx == 0 and cy == L2:
                    ax.text(cx, cy - dm_l/2 - 0.15, f"DROP {dw:.0f}x{dl:.0f}", ha='center', va='top', fontsize=7, 
                            color=dec, fontweight='bold', bbox=dict(fc='white', ec='none', alpha=0.7, pad=0))

            # Column
            ax.add_patch(patches.Rectangle((cx-c1_m/2, cy-c2_m/2), c1_m, c2_m, 
                                         fc=CAD_COLORS['col_fill'], ec=CAD_COLORS['col_edge'], zorder=5))

        # --- FOCUS CIRCLE (RESTORED) ---
        # Draw around Top-Left (Design Column)
        draw_focus_circle(ax, 0, L2, r=max(c1_m, c2_m)*2.5)

        # Dimensions
        draw_smart_dim(ax, (0, L2), (L1, L2), f"L1 = {L1:.2f} m", offset=0.8)
        draw_smart_dim(ax, (L1, 0), (L1, L2), f"L2 = {L2:.2f} m", offset=0.8, is_vert=True)
        
        st.pyplot(fig, use_container_width=True)

        # ------------------------------------
        # DRAWING 2: SECTION VIEW
        # ------------------------------------
        st.markdown(f"#### 🏗️ SECTION VIEW")
        fig_s, ax_s = plt.subplots(figsize=(7, 3))
        sec_w = 300
        ax_s.set_xlim(-sec_w/2 - 50, sec_w/2 + 50)
        ax_s.set_ylim(-120, h_slab + 40)
        ax_s.set_aspect('equal')
        ax_s.axis('off')

        # Draw Section Elements
        ax_s.add_patch(patches.Rectangle((-c1_w/2, -120), c1_w, 120+h_slab, fc=CAD_COLORS['col_fill'], ec='black', zorder=1))
        
        slab_p = patches.Rectangle((-sec_w/2, 0), sec_w, h_slab, fc='white', ec='black', lw=1.2, zorder=2)
        slab_p.set_hatch('...')
        ax_s.add_patch(slab_p)

        if has_drop:
            # Section Drop Colors
            if aci_res['is_structural']:
                ds_fc, ds_ec = 'white', 'black'
            else:
                ds_fc, ds_ec = CAD_COLORS['fail_fill'], CAD_COLORS['fail_edge']
            
            draw_dw = min(dw, sec_w * 0.7)
            dp_p = patches.Rectangle((-draw_dw/2, -dh), draw_dw, dh, fc=ds_fc, ec=ds_ec, lw=1.2, zorder=3)
            if aci_res['is_structural']: dp_p.set_hatch('...')
            ax_s.add_patch(dp_p)
            
            # Smart Dimension (Red if fail)
            draw_smart_dim(ax_s, (draw_dw/2 + 15, 0), (draw_dw/2 + 15, -dh), f"{dh:.0f}cm", is_vert=True, check_pass=aci_res['checks']['depth']['ok'])
        
        draw_smart_dim(ax_s, (-sec_w/2 - 15, 0), (-sec_w/2 - 15, h_slab), f"h={h_slab:.0f}", is_vert=True)
        st.pyplot(fig_s, use_container_width=True)

    # ------------------------------------
    # DATA PANEL
    # ------------------------------------
    with col_data:
        st.markdown(f"#### 📋 DESIGN CHECK: {col_type.upper()}")
        if has_drop:
            geo_info = {'h': h_slab, 'fc': mat_props.get('fc', 0), 'wu': loads.get('w_u', 0)}
            st.markdown(generate_engineering_table(aci_res, geo_info), unsafe_allow_html=True)
        else:
            st.info("No Drop Panel defined.")
