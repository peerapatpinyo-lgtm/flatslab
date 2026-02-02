# tab_drawings.py
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# ==========================================
# 1. DRAWING HELPER (เส้นบอกระยะ)
# ==========================================
def draw_dim(ax, p1, p2, text, offset=0, color='#003366', is_vert=False):
    x1, y1 = p1
    x2, y2 = p2
    
    if is_vert:
        x1 += offset; x2 += offset
        ha, va, rot = 'right' if offset < 0 else 'left', 'center', 90
        txt_pos = (x1 - 0.1 if offset < 0 else x1 + 0.1, (y1+y2)/2)
    else:
        y1 += offset; y2 += offset
        ha, va, rot = 'center', 'bottom' if offset > 0 else 'top', 0
        txt_pos = ((x1+x2)/2, y1 + 0.1 if offset > 0 else y1 - 0.1)

    ax.annotate('', xy=(x1, y1), xytext=(x2, y2),
                arrowprops=dict(arrowstyle='<|-|>', color=color, lw=0.8, mutation_scale=12))
    
    ax.plot([p1[0], x1], [p1[1], y1], color=color, lw=0.4, ls=':', alpha=0.5)
    ax.plot([p2[0], x2], [p2[1], y2], color=color, lw=0.4, ls=':', alpha=0.5)

    ax.text(txt_pos[0], txt_pos[1], text, color=color, fontsize=9, ha=ha, va=va, rotation=rot,
            bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', pad=1))

# ==========================================
# 2. MAIN RENDER FUNCTION
# ==========================================
def render(L1, L2, c1_w, c2_w, h_slab, lc, cover, d_eff, 
           drop_data=None, moment_vals=None, 
           mat_props=None, loads=None): # <--- รับค่า Material และ Load เพิ่มตรงนี้
    
    st.header("📐 Geometry & Design Criteria")
    
    # 1. Prepare Geometry Data
    if drop_data is None: drop_data = {'has_drop': False, 'width': 0, 'length': 0, 'depth': 0}
    c1_m, c2_m = c1_w/100.0, c2_w/100.0
    has_drop = drop_data.get('has_drop')
    drop_w_m = drop_data.get('width', 0)/100.0
    drop_l_m = drop_data.get('length', 0)/100.0
    h_drop = drop_data.get('depth', 0)

    # 2. Prepare Material & Load Data (Default values protection)
    #    ดึงค่าจาก dict ที่ส่งมาจาก app.py
    if mat_props is None: mat_props = {}
    if loads is None: loads = {}
    
    fc = mat_props.get('fc', 0)
    fy = mat_props.get('fy', 0)
    sdl = loads.get('SDL', 0)
    ll = loads.get('LL', 0)
    wu = loads.get('w_u', 0)

    # ==========================================
    # SECTION 1: PLAN VIEW + GENERAL NOTES
    # ==========================================
    
    col_draw, col_info = st.columns([2.5, 1])

    with col_draw:
        st.subheader("1. Floor Plan View")
        fig, ax = plt.subplots(figsize=(6, 4.5))
        
        # Slab Outline
        ax.add_patch(patches.Rectangle((0, 0), L1, L2, fc='#f8f9fa', ec='black', lw=1.5))
        
        # Columns & Drops
        centers = [(0,0), (L1,0), (0,L2), (L1,L2)]
        for cx, cy in centers:
            if has_drop:
                ax.add_patch(patches.Rectangle((cx-drop_w_m/2, cy-drop_l_m/2), drop_w_m, drop_l_m, fc='#cfd8dc', ec='none'))
            ax.add_patch(patches.Rectangle((cx-c1_m/2, cy-c2_m/2), c1_m, c2_m, fc='#37474f', ec='none'))

        # Dimensions
        draw_dim(ax, (0, L2), (L1, L2), f"Lx = {L1} m", offset=0.5, is_vert=False)
        draw_dim(ax, (L1, 0), (L1, L2), f"Ly = {L2} m", offset=0.5, is_vert=True)

        ax.set_xlim(-1, L1+1); ax.set_ylim(-1, L2+1)
        ax.set_aspect('equal'); ax.axis('off')
        
        st.pyplot(fig)

    with col_info:
        # แสดงผลข้อมูลที่เชื่อมโยงมาแล้ว (General Notes)
        st.markdown("### 📋 General Notes")
        
        st.markdown(f"""
        <style>
            .eng-table {{ width: 100%; border-collapse: collapse; font-family: monospace; font-size: 0.9rem; }}
            .eng-table td {{ padding: 4px; border-bottom: 1px solid #ddd; }}
            .eng-header {{ background-color: #e9ecef; font-weight: bold; padding: 5px; margin-top: 10px; border-left: 4px solid #003366; }}
            .val {{ text-align: right; font-weight: bold; color: #333; }}
            .unit {{ color: #666; font-size: 0.8rem; }}
        </style>

        <div class="eng-header">🧱 MATERIALS</div>
        <table class="eng-table">
            <tr><td>f'c</td><td class="val">{fc:,.0f}</td><td class="unit">ksc</td></tr>
            <tr><td>fy</td><td class="val">{fy:,.0f}</td><td class="unit">ksc</td></tr>
        </table>

        <div class="eng-header">⚖️ DESIGN LOADS</div>
        <table class="eng-table">
            <tr><td>SDL</td><td class="val">{sdl:,.0f}</td><td class="unit">kg/m²</td></tr>
            <tr><td>Live Load</td><td class="val">{ll:,.0f}</td><td class="unit">kg/m²</td></tr>
            <tr><td><b>Wu (Factored)</b></td><td class="val" style="color:#d32f2f;">{wu:,.0f}</td><td class="unit">kg/m²</td></tr>
        </table>
        
        <div class="eng-header">🏗️ GEOMETRY</div>
        <table class="eng-table">
            <tr><td>Slab Thk.</td><td class="val">{h_slab}</td><td class="unit">cm</td></tr>
            <tr><td>Cover</td><td class="val">{cover}</td><td class="unit">cm</td></tr>
            <tr><td>Storey H.</td><td class="val">{lc}</td><td class="unit">m</td></tr>
        </table>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # ==========================================
    # SECTION 2: DETAILS
    # ==========================================
    c_zoom, c_sect = st.columns([1, 2])
    
    with c_zoom:
        st.subheader("2. Column Detail")
        fig_z, ax_z = plt.subplots(figsize=(4, 4))
        limit = max(drop_w_m, drop_l_m)*1.2 if has_drop else max(c1_m, c2_m)*3
        
        if has_drop:
            ax_z.add_patch(patches.Rectangle((-drop_w_m/2, -drop_l_m/2), drop_w_m, drop_l_m, fc='#eceff1', ec='blue', ls='--'))
            draw_dim(ax_z, (-drop_w_m/2, drop_l_m/2), (drop_w_m/2, drop_l_m/2), f"{drop_data['width']}", offset=0.1, color='blue')
            draw_dim(ax_z, (-drop_w_m/2, -drop_l_m/2), (-drop_w_m/2, drop_l_m/2), f"{drop_data['length']}", offset=-0.1, color='blue', is_vert=True)

        ax_z.add_patch(patches.Rectangle((-c1_m/2, -c2_m/2), c1_m, c2_m, fc='gray', ec='black', hatch='..'))
        draw_dim(ax_z, (-c1_m/2, -c2_m/2), (c1_m/2, -c2_m/2), f"c1:{c1_w}", offset=-0.1, color='red')
        draw_dim(ax_z, (c1_m/2, -c2_m/2), (c1_m/2, c2_m/2), f"c2:{c2_w}", offset=0.1, color='red', is_vert=True)
        
        ax_z.set_xlim(-limit/2, limit/2); ax_z.set_ylim(-limit/2, limit/2)
        ax_z.axis('off'); ax_z.set_aspect('equal')
        st.pyplot(fig_z)

    with c_sect:
        st.subheader("3. Section A-A")
        fig_s, ax_s = plt.subplots(figsize=(8, 3))
        cut_w = 200
        
        ax_s.add_patch(patches.Rectangle((-cut_w/2, 0), cut_w, h_slab, fc='white', ec='black', hatch='///'))
        
        y_bot = 0
        if has_drop:
            dw = min(cut_w*0.6, drop_data['width'])
            ax_s.add_patch(patches.Rectangle((-dw/2, -h_drop), dw, h_drop, fc='white', ec='black', hatch='///'))
            y_bot = -h_drop
            draw_dim(ax_s, (dw/2+5, 0), (dw/2+5, -h_drop), f"+{h_drop}", offset=5, color='blue', is_vert=True)
            
        ax_s.add_patch(patches.Rectangle((-c1_w/2, y_bot-30), c1_w, 30, fc='gray', ec='black'))
        
        draw_dim(ax_s, (-cut_w/2-10, 0), (-cut_w/2-10, h_slab), f"h:{h_slab}", offset=-5, color='black', is_vert=True)
        d_line = h_slab - cover - 0.6
        ax_s.plot([-cut_w/3, cut_w/3], [d_line, d_line], 'r-', lw=2)
        draw_dim(ax_s, (cut_w/3+25, d_line), (cut_w/3+25, y_bot), f"d:{d_eff:.1f}", offset=5, color='purple', is_vert=True)

        ax_s.set_xlim(-cut_w/2-30, cut_w/2+40); ax_s.set_ylim(y_bot-20, h_slab+20)
        ax_s.axis('off'); ax_s.set_aspect('equal')
        st.pyplot(fig_s)
