# tab_drawings.py
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# ==========================================
# 1. ARCHITECTURAL DIMENSION HELPER
# ==========================================
def draw_dim(ax, p1, p2, text, offset=0, color='#2c3e50', is_vert=False, font_size=10):
    """
    Renders architectural-style dimensions with high precision.
    """
    x1, y1 = p1
    x2, y2 = p2
    
    # Calculate offset positions
    if is_vert:
        x1 += offset; x2 += offset
        # Text alignment
        ha, va, rot = 'right' if offset < 0 else 'left', 'center', 90
        # Text position gap
        txt_x = x1 - 0.1 if offset < 0 else x1 + 0.1
        txt_pos = (txt_x, (y1+y2)/2)
    else:
        y1 += offset; y2 += offset
        # Text alignment
        ha, va, rot = 'center', 'bottom' if offset > 0 else 'top', 0
        # Text position gap
        txt_y = y1 + 0.1 if offset > 0 else y1 - 0.1
        txt_pos = ((x1+x2)/2, txt_y)

    # 1. Main Dimension Line (With Architectural Arrows)
    ax.annotate('', xy=(x1, y1), xytext=(x2, y2),
                arrowprops=dict(arrowstyle='<|-|>', color=color, lw=0.8, mutation_scale=15))
    
    # 2. Extension Lines (Connecting to object)
    # Draw faint lines from object to dimension line
    ext_style = dict(color=color, lw=0.5, ls=':', alpha=0.5)
    if is_vert:
        ax.plot([p1[0], x1], [p1[1], y1], **ext_style)
        ax.plot([p2[0], x2], [p2[1], y2], **ext_style)
    else:
        ax.plot([p1[0], x1], [p1[1], y1], **ext_style)
        ax.plot([p2[0], x2], [p2[1], y2], **ext_style)

    # 3. Text Label (With background for clarity)
    ax.text(txt_pos[0], txt_pos[1], text, 
            color=color, fontsize=font_size, ha=ha, va=va, rotation=rot, fontweight='bold', family='sans-serif',
            bbox=dict(facecolor='white', alpha=0.85, edgecolor='none', pad=1.5))

# ==========================================
# 2. MAIN RENDER FUNCTION
# ==========================================
def render(L1, L2, c1_w, c2_w, h_slab, lc, cover, d_eff, 
           drop_data=None, moment_vals=None, 
           mat_props=None, loads=None):
    
    # --- Data Unpacking & Safety Checks ---
    if drop_data is None: drop_data = {'has_drop': False, 'width': 0, 'length': 0, 'depth': 0}
    if mat_props is None: mat_props = {}
    if loads is None: loads = {}
    
    # Convert Units
    c1_m, c2_m = c1_w/100.0, c2_w/100.0
    has_drop = drop_data.get('has_drop')
    drop_w_m = drop_data.get('width', 0)/100.0
    drop_l_m = drop_data.get('length', 0)/100.0
    h_drop = drop_data.get('depth', 0)
    
    # Key Values
    fc, fy = mat_props.get('fc', 0), mat_props.get('fy', 0)
    sdl, ll, wu = loads.get('SDL', 0), loads.get('LL', 0), loads.get('w_u', 0)

    # ==========================================
    # STYLE: CSS FOR TITLE BLOCK
    # ==========================================
    st.markdown("""
    <style>
        .dwg-container {
            font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            border: 2px solid #333;
            background-color: white;
            padding: 0;
            margin-bottom: 20px;
        }
        .dwg-header {
            background-color: #2c3e50;
            color: white;
            padding: 10px;
            text-align: center;
            font-weight: bold;
            font-size: 1.1rem;
            letter-spacing: 1px;
            text-transform: uppercase;
        }
        .dwg-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.95rem;
        }
        .dwg-table td {
            padding: 8px 12px;
            border-bottom: 1px solid #eee;
        }
        .dwg-label {
            color: #7f8c8d;
            font-weight: 600;
            width: 40%;
        }
        .dwg-val {
            color: #2c3e50;
            font-weight: 700;
            text-align: right;
        }
        .dwg-subhead {
            background-color: #f8f9fa;
            color: #34495e;
            font-size: 0.85rem;
            font-weight: 800;
            padding: 5px 10px;
            border-top: 1px solid #ddd;
            border-bottom: 1px solid #ddd;
            text-transform: uppercase;
        }
        .highlight-red { color: #c0392b !important; }
    </style>
    """, unsafe_allow_html=True)

    # ==========================================
    # LAYOUT: SPLIT VIEW
    # ==========================================
    st.markdown("### 📐 Structural Plan & Schedule")
    
    col_graphics, col_data = st.columns([2.2, 1])

    # ------------------------------------------
    # LEFT: PLAN VIEW (Top View)
    # ------------------------------------------
    with col_graphics:
        fig, ax = plt.subplots(figsize=(8, 6.5)) # Optimized aspect ratio
        
        # 1. Background (Slab)
        ax.add_patch(patches.Rectangle((0, 0), L1, L2, fc='#ffffff', ec='#2c3e50', lw=2))
        
        # 2. Engineering Grids (Center Lines)
        ax.plot([-0.5, L1+0.5], [L2/2, L2/2], color='#bdc3c7', ls='-.', lw=0.8, alpha=0.8) # CL-X
        ax.plot([L1/2, L1/2], [-0.5, L2+0.5], color='#bdc3c7', ls='-.', lw=0.8, alpha=0.8) # CL-Y
        
        # 3. Column & Drop Rendering
        centers = [(0,0), (L1,0), (0,L2), (L1,L2)]
        for cx, cy in centers:
            # Drop Panel (Dashed Line)
            if has_drop:
                ax.add_patch(patches.Rectangle(
                    (cx-drop_w_m/2, cy-drop_l_m/2), drop_w_m, drop_l_m, 
                    fc='#ecf0f1', ec='#7f8c8d', lw=1, ls='--'
                ))
            
            # Column (Solid Hatch)
            col_rect = patches.Rectangle(
                (cx-c1_m/2, cy-c2_m/2), c1_m, c2_m, 
                fc='#34495e', ec='black', lw=0, alpha=0.9
            )
            ax.add_patch(col_rect)

        # 4. Dimensions (Clean & Crisp)
        # Horizontal
        draw_dim(ax, (0, L2), (L1, L2), f"Lx = {L1:.2f} m", offset=0.6, is_vert=False, font_size=11)
        # Vertical
        draw_dim(ax, (L1, 0), (L1, L2), f"Ly = {L2:.2f} m", offset=0.6, is_vert=True, font_size=11)
        
        # Drop Panel Dims (Only if exists)
        if has_drop:
             draw_dim(ax, (L1/2 - drop_w_m/2, L2/2 + drop_l_m/2), (L1/2 + drop_w_m/2, L2/2 + drop_l_m/2), 
                      f"Drop: {drop_data['width']} cm", offset=0.2, color='#7f8c8d', font_size=9)

        # 5. Annotation / Tag
        ax.text(L1/2, L2/2 - 0.5, "S-01", ha='center', fontsize=16, fontweight='bold', color='#2c3e50',
                bbox=dict(boxstyle="circle,pad=0.4", fc="white", ec="#2c3e50", lw=1.5))

        # View Settings
        ax.set_xlim(-1.0, L1+1.0)
        ax.set_ylim(-1.0, L2+1.0)
        ax.set_aspect('equal')
        ax.axis('off')
        
        st.pyplot(fig, use_container_width=True)

    # ------------------------------------------
    # RIGHT: ENGINEERING SCHEDULE (Title Block)
    # ------------------------------------------
    with col_data:
        # Using HTML Table for Pixel-Perfect Layout
        st.markdown(f"""
        <div class="dwg-container">
            <div class="dwg-header">General Notes Schedule</div>
            
            <div class="dwg-subhead">🧱 Material Specifications</div>
            <table class="dwg-table">
                <tr><td class="dwg-label">Concrete (fc')</td><td class="dwg-val">{fc:,.0f} ksc</td></tr>
                <tr><td class="dwg-label">Rebar (fy)</td><td class="dwg-val">{fy:,.0f} ksc</td></tr>
                <tr><td class="dwg-label">Size</td><td class="dwg-val">DB{mat_props.get('d_bar')}</td></tr>
            </table>

            <div class="dwg-subhead">⚖️ Design Loads (ULS)</div>
            <table class="dwg-table">
                <tr><td class="dwg-label">Superimposed DL</td><td class="dwg-val">{sdl:,.0f} kg/m²</td></tr>
                <tr><td class="dwg-label">Live Load</td><td class="dwg-val">{ll:,.0f} kg/m²</td></tr>
                <tr><td class="dwg-label highlight-red">Factored (Wu)</td><td class="dwg-val highlight-red">{wu:,.0f} kg/m²</td></tr>
            </table>

            <div class="dwg-subhead">📐 Geometric Data</div>
            <table class="dwg-table">
                <tr><td class="dwg-label">Slab Thick (h)</td><td class="dwg-val">{h_slab:.0f} cm</td></tr>
                <tr><td class="dwg-label">Covering</td><td class="dwg-val">{cover} cm</td></tr>
                <tr><td class="dwg-label">Storey Height</td><td class="dwg-val">{lc} m</td></tr>
            </table>
        </div>
        """, unsafe_allow_html=True)
        
        st.info("💡 Note: All dimensions are in meters unless otherwise specified. Reinforcement details per ACI 318-19.")

    st.divider()

    # ------------------------------------------
    # BOTTOM: SECTION DETAIL (CAD Style)
    # ------------------------------------------
    st.markdown("### ✂️ Section A-A: Critical Detail")
    
    # Wide layout for Section
    fig_s, ax_s = plt.subplots(figsize=(12, 4))
    
    # Parameters
    cut_w = 250 # Width of the cut view in cm
    y_slab_top = h_slab
    y_slab_bot = 0
    y_drop_bot = -h_drop if has_drop else 0
    
    # 1. Concrete Slab Pattern (Hatching)
    slab_patch = patches.Rectangle((-cut_w/2, 0), cut_w, h_slab, 
                                   fc='white', ec='black', hatch='///', lw=1.5)
    ax_s.add_patch(slab_patch)
    
    # 2. Drop Panel (if any)
    if has_drop:
        dw = min(cut_w*0.6, drop_data['width'])
        drop_patch = patches.Rectangle((-dw/2, -h_drop), dw, h_drop, 
                                       fc='white', ec='black', hatch='///', lw=1.5)
        ax_s.add_patch(drop_patch)
        
        # Drop Dimension
        draw_dim(ax_s, (dw/2 + 5, 0), (dw/2 + 5, -h_drop), f"+{h_drop}cm", offset=10, is_vert=True, color='#2980b9')

    # 3. Column (Cut Section)
    col_w_draw = c1_w
    col_patch = patches.Rectangle((-col_w_draw/2, y_drop_bot - 40), col_w_draw, 40, 
                                  fc='#bdc3c7', ec='black', hatch='..')
    ax_s.add_patch(col_patch)
    
    # 4. Rebar Placement (Visualizing d)
    d_line_y = h_slab - cover - 0.6 # Center of bar approx
    ax_s.plot([-cut_w/3, cut_w/3], [d_line_y, d_line_y], color='#c0392b', lw=3, label='Main Rebar')
    
    # 5. Critical Dimensions
    # Slab Thickness
    draw_dim(ax_s, (-cut_w/2 - 10, 0), (-cut_w/2 - 10, h_slab), 
             f"h = {h_slab:.0f} cm", offset=-10, is_vert=True, color='black', font_size=11)
    
    # Effective Depth (The most important engineering value)
    draw_dim(ax_s, (cut_w/3 + 15, d_line_y), (cut_w/3 + 15, y_drop_bot), 
             f"d_eff = {d_eff:.2f} cm", offset=10, is_vert=True, color='#8e44ad', font_size=11)

    # 6. Labels
    ax_s.text(0, y_drop_bot - 20, "Column Support", ha='center', fontsize=10, color='white', 
              bbox=dict(facecolor='black', alpha=0.6))

    # Plot Settings
    ax_s.set_xlim(-cut_w/2 - 30, cut_w/2 + 30)
    ax_s.set_ylim(y_drop_bot - 50, h_slab + 20)
    ax_s.axis('off')
    
    st.pyplot(fig_s, use_container_width=True)
