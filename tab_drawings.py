# tab_drawings.py
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib as mpl
import pandas as pd
import numpy as np

# ==========================================
# 0. CONFIG & STYLES (CAD THEME)
# ==========================================
CAD_COLORS = {
    'bg': 'white',
    'slab_fill': '#FFFFFF',
    'slab_edge': '#37474F',
    'col_fill': '#CFD8DC',  # Lighter grey for columns to make dims pop
    'col_edge': '#263238',
    'dim': '#455A64',
    'rebar': '#C62828',
    'grid': '#ECEFF1',
    'pass_fill': '#E8F5E9', # Light Green
    'pass_edge': '#2E7D32', # Green
    'fail_fill': '#FFEBEE', # Light Red
    'fail_edge': '#C62828', # Red
    'text_main': '#263238',
    'text_sub': '#78909c'
}

mpl.rcParams['font.family'] = 'sans-serif'
mpl.rcParams['font.sans-serif'] = ['Tahoma', 'DejaVu Sans', 'Arial']

# ==========================================
# 1. UTILS: DRAWING HELPER
# ==========================================
def draw_smart_dim(ax, p1, p2, text, offset=0, is_vert=False, color=CAD_COLORS['dim'], check_pass=True):
    """Draws a professional dimension line with automatic offset handling."""
    x1, y1 = p1
    x2, y2 = p2
    
    # Text Color Logic (Red if check fails)
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

    # Extension Lines
    kw_ext = dict(color=final_color, lw=0.5, ls='-', alpha=0.4)
    if is_vert:
        ax.plot([p1[0], x1], [p1[1], y1], **kw_ext)
        ax.plot([p2[0], x2], [p2[1], y2], **kw_ext)
    else:
        ax.plot([p1[0], x1], [p1[1], y1], **kw_ext)
        ax.plot([p2[0], x2], [p2[1], y2], **kw_ext)

    # Arrow Line
    ax.annotate('', xy=(x1, y1), xytext=(x2, y2),
                arrowprops=dict(arrowstyle='<|-|>', color=final_color, lw=0.7, shrinkA=0, shrinkB=0))
    
    # Text
    ax.text(txt_pos[0], txt_pos[1], text, 
            color=final_color, fontsize=8, ha=ha, va=va, rotation=rot, 
            fontfamily='monospace', fontweight='bold', zorder=20,
            bbox=dict(facecolor='white', alpha=0.85, edgecolor='none', pad=1.0))

def draw_tag(ax, x, y, text, is_warning=False, rotation=0):
    """Draws a status tag."""
    fc = CAD_COLORS['fail_fill'] if is_warning else '#F5F5F5'
    ec = CAD_COLORS['fail_edge'] if is_warning else '#B0BEC5'
    tc = CAD_COLORS['fail_edge'] if is_warning else '#546E7A'
    
    ax.text(x, y, text, ha='center', va='center', rotation=rotation,
            fontsize=7, color=tc, fontweight='bold', zorder=25,
            bbox=dict(facecolor=fc, edgecolor=ec, alpha=1, pad=4, boxstyle="round,pad=0.3"))

# ==========================================
# 2. ENGINEERING KERNEL (CALCULATION)
# ==========================================
def calculate_aci_compliance(drop_w, drop_l, drop_h, L1, L2, c1, c2, h_slab):
    """
    Detailed ACI 318 calculation. 
    Returns a dict containing both boolean status AND specific values for the report.
    """
    # 1. Geometry
    Ln_x = L1 - (c1/100.0)
    Ln_y = L2 - (c2/100.0)
    
    # 2. Required Extension (Ln/6)
    # Convert to CM for easy comparison
    req_ext_x_cm = (Ln_x * 100) / 6.0
    req_ext_y_cm = (Ln_y * 100) / 6.0
    
    # 3. Total Required Size (assuming symmetric drop)
    # Width = Column + 2 * Extension
    req_total_w = c1 + (2 * req_ext_x_cm)
    req_total_l = c2 + (2 * req_ext_y_cm)
    
    # 4. Required Projection (h/4)
    req_proj = h_slab / 4.0
    
    # 5. Check (with 1cm tolerance)
    tol = 1.0 
    ok_w = drop_w >= (req_total_w - tol)
    ok_l = drop_l >= (req_total_l - tol)
    ok_h = drop_h >= (req_proj - 0.1)
    
    is_structural = ok_w and ok_l and ok_h
    
    return {
        'is_structural': is_structural,
        'checks': {
            'width': {'req': req_total_w, 'act': drop_w, 'ok': ok_w, 'ext_req': req_ext_x_cm},
            'length': {'req': req_total_l, 'act': drop_l, 'ok': ok_l, 'ext_req': req_ext_y_cm},
            'depth': {'req': req_proj, 'act': drop_h, 'ok': ok_h}
        },
        'ln': (Ln_x, Ln_y)
    }

# ==========================================
# 3. HTML GENERATOR (ENGINEERING TABLE)
# ==========================================
def generate_engineering_table(res, geo_data):
    """Generates a detailed HTML table showing Required vs Provided."""
    
    def status_cell(is_ok):
        color = "#2E7D32" if is_ok else "#C62828"
        icon = "✔ PASS" if is_ok else "✘ FAIL"
        bg = "#E8F5E9" if is_ok else "#FFEBEE"
        return f"<td style='color:{color}; background:{bg}; font-weight:bold; text-align:center;'>{icon}</td>"

    # Header
    html = """
    <style>
        .eng-table { width: 100%; border-collapse: collapse; font-family: sans-serif; font-size: 0.85rem; }
        .eng-table th { background: #455A64; color: white; padding: 8px; text-align: left; }
        .eng-table td { border-bottom: 1px solid #ECEFF1; padding: 6px 8px; color: #37474F; }
        .eng-val { font-family: monospace; font-weight: bold; }
        .sub-txt { font-size: 0.75rem; color: #90A4AE; display: block; }
    </style>
    """
    
    html += "<div style='border: 1px solid #CFD8DC; border-radius: 4px; overflow: hidden;'>"
    html += "<table class='eng-table'>"
    
    # Section 1: Result Summary
    main_status = "STRUCTURAL DROP PANEL" if res['is_structural'] else "SHEAR CAP ONLY"
    main_color = "#2E7D32" if res['is_structural'] else "#C62828"
    main_bg = "#E8F5E9" if res['is_structural'] else "#FFEBEE"
    
    html += f"""
    <tr style="background:{main_bg}; border-bottom: 2px solid {main_color};">
        <td colspan="4" style="padding: 12px; font-size: 1rem; color: {main_color}; font-weight: bold; text-align: center;">
            {main_status}
        </td>
    </tr>
    """
    
    # Section 2: Detailed Checks
    html += "<tr><th>Check Item (ACI 318)</th><th style='text-align:right'>Required</th><th style='text-align:right'>Provided</th><th>Status</th></tr>"
    
    # 2.1 Extension X (Width)
    cw = res['checks']['width']
    w_req_txt = f"{cw['req']:.0f} <span class='sub-txt'>(Ln/6 ext: {cw['ext_req']:.0f})</span>"
    html += f"<tr><td><b>Min Width (X)</b><br><span class='sub-txt'>Span Ln={res['ln'][0]:.2f}m</span></td>"
    html += f"<td class='eng-val' style='text-align:right'>{w_req_txt}</td>"
    html += f"<td class='eng-val' style='text-align:right'>{cw['act']:.0f}</td>"
    html += status_cell(cw['ok']) + "</tr>"
    
    # 2.2 Extension Y (Length)
    cl = res['checks']['length']
    l_req_txt = f"{cl['req']:.0f} <span class='sub-txt'>(Ln/6 ext: {cl['ext_req']:.0f})</span>"
    html += f"<tr><td><b>Min Length (Y)</b><br><span class='sub-txt'>Span Ln={res['ln'][1]:.2f}m</span></td>"
    html += f"<td class='eng-val' style='text-align:right'>{l_req_txt}</td>"
    html += f"<td class='eng-val' style='text-align:right'>{cl['act']:.0f}</td>"
    html += status_cell(cl['ok']) + "</tr>"

    # 2.3 Projection (Depth)
    cd = res['checks']['depth']
    html += f"<tr><td><b>Min Projection</b><br><span class='sub-txt'>h_slab/4 (h={geo_data['h']})</span></td>"
    html += f"<td class='eng-val' style='text-align:right'>{cd['req']:.1f}</td>"
    html += f"<td class='eng-val' style='text-align:right'>{cd['act']:.1f}</td>"
    html += status_cell(cd['ok']) + "</tr>"
    
    html += "</table></div>"
    
    # Section 3: Loads (Summary)
    html += "<div style='margin-top:10px; font-size:0.8rem; color:#546E7A;'>"
    html += f"<b>Design Data:</b> fc' = {geo_data['fc']} ksc | Wu = {geo_data['wu']:,} kg/m²"
    html += "</div>"

    return html

# ==========================================
# 4. MAIN RENDERER
# ==========================================
def render(L1, L2, c1_w, c2_w, h_slab, lc, cover, d_eff, 
           drop_data=None, moment_vals=None, mat_props=None, loads=None, col_type="interior"):
    
    # --- Data Prep ---
    if drop_data is None: drop_data = {'has_drop': False, 'width': 0, 'length': 0, 'depth': 0}
    mat_props = mat_props or {'fc': 240}
    loads = loads or {'w_u': 0}
    h_slab = h_slab or 20
    
    c1_m, c2_m = c1_w/100.0, c2_w/100.0
    
    has_drop = drop_data.get('has_drop')
    dw, dl, dh = drop_data.get('width', 0), drop_data.get('length', 0), drop_data.get('depth', 0)
    
    # --- Engineering Calculation ---
    aci_res = None
    if has_drop:
        aci_res = calculate_aci_compliance(dw, dl, dh, L1, L2, c1_w, c2_w, h_slab)
    
    # --- Layout ---
    col_draw, col_data = st.columns([0.6, 0.4], gap="medium")

    # ------------------------------------
    # LEFT: VISUALIZATION
    # ------------------------------------
    with col_draw:
        st.markdown(f"#### 📐 PLAN VIEW: {col_type.upper()}")
        
        # 1. Plan View (Fixed Scale)
        # Margin logic: Ensure enough space for external dims
        margin = max(L1, L2) * 0.25 + 0.5
        fig, ax = plt.subplots(figsize=(7, 6))
        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_xlim(-margin, L1 + margin)
        ax.set_ylim(-margin, L2 + margin)

        # Grids
        ax.plot([-margin, L1+margin], [L2/2, L2/2], color=CAD_COLORS['grid'], ls='-.', lw=1)
        ax.plot([L1/2, L1/2], [-margin, L2+margin], color=CAD_COLORS['grid'], ls='-.', lw=1)

        # Slab
        ax.add_patch(patches.Rectangle((0, 0), L1, L2, fc='white', ec=CAD_COLORS['slab_edge'], lw=1.5, zorder=1))

        # Elements
        centers = [(0,0), (L1,0), (0,L2), (L1,L2)]
        for cx, cy in centers:
            # Drop Panel
            if has_drop:
                # Determine colors based on Pass/Fail
                if aci_res['is_structural']:
                    dfc, dec = CAD_COLORS['pass_fill'], CAD_COLORS['pass_edge']
                    dls, dlw = '-', 1.0
                else:
                    dfc, dec = CAD_COLORS['fail_fill'], CAD_COLORS['fail_edge']
                    dls, dlw = '--', 1.2
                
                dm_w, dm_l = dw/100.0, dl/100.0
                ax.add_patch(patches.Rectangle((cx - dm_w/2, cy - dm_l/2), dm_w, dm_l, 
                                             fc=dfc, ec=dec, ls=dls, lw=dlw, zorder=2))
                
                # Annotation (Only on Top-Left)
                if cx == 0 and cy == L2:
                    lbl = f"DROP {dw:.0f}x{dl:.0f}"
                    ax.text(cx, cy - dm_l/2 - 0.15, lbl, ha='center', va='top', fontsize=7, 
                            color=dec, fontweight='bold', bbox=dict(fc='white', ec='none', alpha=0.7, pad=0))

            # Column
            ax.add_patch(patches.Rectangle((cx-c1_m/2, cy-c2_m/2), c1_m, c2_m, 
                                         fc=CAD_COLORS['col_fill'], ec=CAD_COLORS['col_edge'], zorder=5))

        # Dimensions
        dim_off = 0.5 + (margin * 0.1)
        draw_smart_dim(ax, (0, L2), (L1, L2), f"L1 = {L1:.2f} m", offset=dim_off)
        draw_smart_dim(ax, (L1, 0), (L1, L2), f"L2 = {L2:.2f} m", offset=dim_off, is_vert=True)
        
        # Check specific Dimension Pass/Fail for visual feedback
        pass_Ln = True # Placeholder
        draw_smart_dim(ax, (c1_m/2, L2/4), (L1-c1_m/2, L2/4), f"Ln = {aci_res['ln'][0] if aci_res else 0:.2f} m", 
                       color='#2E7D32', check_pass=pass_Ln)

        st.pyplot(fig, use_container_width=True)

        # 2. Section View (Cleaned up)
        st.markdown(f"#### 🏗️ SECTION CHECK")
        fig_s, ax_s = plt.subplots(figsize=(7, 3))
        
        # Fixed viewing window logic
        sec_w = 300 # cm
        ax_s.set_xlim(-sec_w/2 - 50, sec_w/2 + 50)
        ax_s.set_ylim(-150, h_slab + 50)
        ax_s.set_aspect('equal')
        ax_s.axis('off')

        # Column
        ax_s.add_patch(patches.Rectangle((-c1_w/2, -150), c1_w, 150+h_slab, fc=CAD_COLORS['col_fill'], ec='black', zorder=1))
        
        # Slab
        slab_p = patches.Rectangle((-sec_w/2, 0), sec_w, h_slab, fc='white', ec='black', lw=1.2, zorder=2)
        slab_p.set_hatch('...') # Concrete stipple
        ax_s.add_patch(slab_p)

        # Drop
        if has_drop:
            # Color logic
            if aci_res['is_structural']:
                ds_fc, ds_ec = 'white', 'black'
            else:
                ds_fc, ds_ec = CAD_COLORS['fail_fill'], CAD_COLORS['fail_edge']
            
            draw_dw = min(dw, sec_w * 0.7)
            dp_p = patches.Rectangle((-draw_dw/2, -dh), draw_dw, dh, fc=ds_fc, ec=ds_ec, lw=1.2, zorder=2)
            if aci_res['is_structural']: dp_p.set_hatch('...')
            ax_s.add_patch(dp_p)
            
            # Dimension Check Logic
            check_d = aci_res['checks']['depth']['ok']
            draw_smart_dim(ax_s, (draw_dw/2 + 20, 0), (draw_dw/2 + 20, -dh), f"{dh:.0f}cm", 
                           is_vert=True, check_pass=check_d)
            
            # Fail Label
            if not aci_res['is_structural']:
                ax_s.text(0, -dh-15, "DOES NOT MEET ACI 318", color=CAD_COLORS['fail_edge'], 
                          ha='center', va='top', fontsize=8, fontweight='bold')

        # Main Dimension
        draw_smart_dim(ax_s, (-sec_w/2 - 20, 0), (-sec_w/2 - 20, h_slab), f"h={h_slab:.0f}", is_vert=True)

        st.pyplot(fig_s, use_container_width=True)

    # ------------------------------------
    # RIGHT: ENGINEERING DATA
    # ------------------------------------
    with col_data:
        st.markdown("#### 📋 COMPLIANCE REPORT")
        
        if has_drop:
            geo_info = {'h': h_slab, 'fc': mat_props.get('fc', 0), 'wu': loads.get('w_u', 0)}
            html_table = generate_engineering_table(aci_res, geo_info)
            st.markdown(html_table, unsafe_allow_html=True)
            
            # Engineer's Action Plan
            if not aci_res['is_structural']:
                st.warning("**💡 Engineer's Recommendation:**")
                rec_list = []
                cw = aci_res['checks']['width']
                cl = aci_res['checks']['length']
                cd = aci_res['checks']['depth']
                
                if not cw['ok']:
                    diff = cw['req'] - cw['act']
                    rec_list.append(f"- Increase **Width** by at least **{diff:.0f} cm**")
                if not cl['ok']:
                    diff = cl['req'] - cl['act']
                    rec_list.append(f"- Increase **Length** by at least **{diff:.0f} cm**")
                if not cd['ok']:
                    diff = cd['req'] - cd['act']
                    rec_list.append(f"- Increase **Projection** by **{diff:.1f} cm**")
                
                for r in rec_list:
                    st.markdown(r)
        else:
            st.info("No Drop Panel defined.\nSlab will be designed as Flat Plate.")
