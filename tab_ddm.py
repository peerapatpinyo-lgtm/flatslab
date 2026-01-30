# tab_ddm.py
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from calculations import design_rebar_detailed

# ==========================================
# 1. HELPER: DYNAMIC STRIP DIAGRAM
# ==========================================
def plot_strips_overview(L_width, w_cs_cm, w_ms_cm, title="Strip Layout"):
    """
    Draws a cross-section or plan view showing Column Strip vs Middle Strip
    L_width (m), w_cs (cm), w_ms (cm)
    """
    total_w = L_width * 100 # cm
    cs_half = w_cs_cm / 2
    
    fig, ax = plt.subplots(figsize=(8, 2))
    
    # Background
    ax.set_xlim(0, total_w)
    ax.set_ylim(0, 10)
    ax.set_yticks([])
    ax.set_xlabel("Width (cm)")
    ax.set_title(title, fontsize=10)
    
    # Draw Strips
    # Left Column Strip (Half)
    rect_cs1 = patches.Rectangle((0, 2), cs_half, 6, linewidth=1, edgecolor='none', facecolor='#FF9999', alpha=0.8)
    ax.add_patch(rect_cs1)
    ax.text(cs_half/2, 5, f"CS\n{cs_half:.0f}", ha='center', va='center', fontsize=8, color='white', fontweight='bold')
    
    # Middle Strip
    rect_ms = patches.Rectangle((cs_half, 2), w_ms_cm, 6, linewidth=1, edgecolor='none', facecolor='#99CCFF', alpha=0.8)
    ax.add_patch(rect_ms)
    ax.text(cs_half + w_ms_cm/2, 5, f"Middle Strip\n{w_ms_cm:.0f} cm", ha='center', va='center', fontsize=9, color='white', fontweight='bold')
    
    # Right Column Strip (Half)
    rect_cs2 = patches.Rectangle((cs_half + w_ms_cm, 2), cs_half, 6, linewidth=1, edgecolor='none', facecolor='#FF9999', alpha=0.8)
    ax.add_patch(rect_cs2)
    ax.text(cs_half + w_ms_cm + cs_half/2, 5, f"CS\n{cs_half:.0f}", ha='center', va='center', fontsize=8, color='white', fontweight='bold')
    
    # Decoration
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    
    return fig

# ==========================================
# 2. HELPER: INPUT & CALCULATION WIDGET
# ==========================================
def render_design_block(title, strip_type, Mu, b_width, h_slab, cover, fc, fy, key_suffix):
    """
    Renders a complete design block with:
    - Independent Rebar Selection (DB & Spacing)
    - Real-time Calculation
    - Visual Pass/Fail Indicator
    """
    st.markdown(f"**{title}**")
    
    # --- A. INPUTS (Side by Side) ---
    c1, c2, c3 = st.columns([1.2, 1.5, 1])
    
    with c1:
        # Select Rebar Diameter Independently
        db_options = [10, 12, 16, 20, 25, 28]
        d_bar = st.selectbox(f"Rebar Ø", db_options, index=1, key=f"db_{key_suffix}", help="Select diameter for this strip only")
    
    with c2:
        # Select Spacing
        spacing = st.slider(f"Spacing @ (cm)", 5.0, 35.0, 20.0, 2.5, key=f"sp_{key_suffix}")
        
    # Recalculate Effective Depth based on local d_bar
    d_eff = h_slab - cover - (d_bar/20.0)/2 # Assume single layer
    
    # --- B. CALCULATION ---
    # 1. Required Steel
    As_req, rho_req, note, status_calc = design_rebar_detailed(Mu, b_width, d_eff, fc, fy)
    
    # 2. Provided Steel
    area_one_bar = np.pi * (d_bar/10)**2 / 4
    As_provided = area_one_bar * (100 / spacing) * (b_width/100)
    
    # 3. Status
    is_pass = As_provided >= As_req
    ratio = As_provided / As_req if As_req > 0 else 999
    color_status = "green" if is_pass else "red"
    icon = "✅" if is_pass else "❌"

    with c3:
        st.markdown(f"<div style='text-align:center; padding-top:10px;'><b>Status</b><br><span style='color:{color_status}; font-size:1.2em;'>{icon}</span></div>", unsafe_allow_html=True)

    # --- C. DISPLAY RESULTS ---
    # Use a clean Metric style
    m1, m2, m3 = st.columns(3)
    m1.metric("Mu (kg-m)", f"{Mu:,.0f}")
    m2.metric("Req. As (cm²)", f"{As_req:.2f}", delta_color="off")
    m3.metric(f"Use DB{d_bar}@{spacing:.0f}", f"{As_provided:.2f} cm²", delta=f"{ratio:.2f}x", delta_color="normal" if is_pass else "inverse")

    # --- D. EXPANDER FOR MATH GEEKS ---
    with st.expander(f"📐 รายการคำนวณละเอียด ({title})"):
        st.write(f"- $b = {b_width:.0f}$ cm, $d = {d_eff:.2f}$ cm (using DB{d_bar})")
        st.latex(r"R_n = \frac{M_u}{\phi b d^2} = " + f"{Mu*100:,.0f} / (0.9 \\cdot {b_width} \\cdot {d_eff:.2f}^2) = {(Mu*100)/(0.9*b_width*d_eff**2):.2f}")
        
        if status_calc == "FAIL":
            st.error(f"Error: {note}")
        else:
            st.latex(r"\rho_{req} = " + f"{rho_req:.5f} \\rightarrow A_{{s,req}} = {As_req:.2f} \\text{{ cm}}^2")
            st.caption(f"Note: {note}")

    return {
        "Strip": strip_type,
        "Location": title.split(" ")[-1], # Extract Pos/Neg
        "Mu": Mu,
        "Rebar": f"DB{d_bar}@{spacing:.0f}",
        "As_req": As_req,
        "As_prov": As_provided,
        "Status": "OK" if is_pass else "FAIL"
    }

# ==========================================
# 3. MAIN RENDER FUNCTION
# ==========================================
def render_direction_tab(direction_name, data, mat, w_u):
    L_span = data['L_span']
    L_width = data['L_width'] # Width perpendicular to span
    ln = data['ln']
    Mo = data['Mo']
    M_vals = data['M_vals']
    
    fc, fy = mat['fc'], mat['fy']
    h_slab, cover = mat['h_slab'], mat['cover']
    
    # 1. VISUALIZE STRIPS
    # Calculate widths
    w_cs = 0.5 * min(L_span, L_width) * 100 # cm (Total CS Width)
    w_ms = (L_width * 100) - w_cs           # cm (Total MS Width)
    
    st.markdown(f"### 📍 {direction_name}-Direction Layout")
    
    col_vis1, col_vis2 = st.columns([2, 1])
    with col_vis1:
        # Generate and show the dynamic plot
        fig = plot_strips_overview(L_width, w_cs, w_ms, title=f"Strip Distribution (Width L2 = {L_width} m)")
        st.pyplot(fig, use_container_width=True)
        
    with col_vis2:
        st.info(f"""
        **Moment ($M_o$):** {Mo:,.0f} kg-m
        
        - **Column Strip:** {w_cs/100:.2f} m ({w_cs:.0f} cm)
        - **Middle Strip:** {w_ms/100:.2f} m ({w_ms:.0f} cm)
        """)

    st.markdown("---")

    # 2. DESIGN ZONES
    # Create two distinct visual columns
    c_cs, c_ms = st.columns(2)
    
    results = []
    
    # --- COLUMN STRIP ---
    with c_cs:
        st.markdown("""<div style='background-color:#ffe6e6; padding:10px; border-radius:5px; border-left:5px solid #ff4d4d;'>
        <h4 style='color:#b30000; margin:0;'>🟥 Column Strip (CS)</h4>
        <small>Zone รับโมเมนต์สูง (High Moment)</small>
        </div>""", unsafe_allow_html=True)
        st.write("")
        
        # Negative Moment (Top Steel)
        r1 = render_design_block("Top Steel (Support -)", "Column Strip", M_vals['M_cs_neg'], w_cs, h_slab, cover, fc, fy, f"{direction_name}_cs_n")
        results.append(r1)
        
        st.divider()
        
        # Positive Moment (Bottom Steel)
        r2 = render_design_block("Bottom Steel (Midspan +)", "Column Strip", M_vals['M_cs_pos'], w_cs, h_slab, cover, fc, fy, f"{direction_name}_cs_p")
        results.append(r2)

    # --- MIDDLE STRIP ---
    with c_ms:
        st.markdown("""<div style='background-color:#e6f2ff; padding:10px; border-radius:5px; border-left:5px solid #0066cc;'>
        <h4 style='color:#004080; margin:0;'>🟦 Middle Strip (MS)</h4>
        <small>Zone รับโมเมนต์ปานกลาง (Moderate Moment)</small>
        </div>""", unsafe_allow_html=True)
        st.write("")
        
        # Negative Moment (Top Steel)
        r3 = render_design_block("Top Steel (Support -)", "Middle Strip", M_vals['M_ms_neg'], w_ms, h_slab, cover, fc, fy, f"{direction_name}_ms_n")
        results.append(r3)
        
        st.divider()
        
        # Positive Moment (Bottom Steel)
        r4 = render_design_block("Bottom Steel (Midspan +)", "Middle Strip", M_vals['M_ms_pos'], w_ms, h_slab, cover, fc, fy, f"{direction_name}_ms_p")
        results.append(r4)

    # 3. SUMMARY
    return results

def render_dual(data_x, data_y, mat_props, w_u):
    st.markdown("## 🏗️ Interactive Slab Reinforcement Design")
    
    tab_x, tab_y = st.tabs(["➡️ X-Direction", "⬆️ Y-Direction"])
    
    with tab_x:
        res_x = render_direction_tab("X", data_x, mat_props, w_u)
        st.markdown("### 📝 Design Summary (X-Axis)")
        df_x = pd.DataFrame(res_x)
        st.dataframe(df_x.style.applymap(lambda v: 'color: red; font-weight: bold' if v == 'FAIL' else 'color: green; font-weight: bold', subset=['Status']), use_container_width=True)

    with tab_y:
        res_y = render_direction_tab("Y", data_y, mat_props, w_u)
        st.markdown("### 📝 Design Summary (Y-Axis)")
        df_y = pd.DataFrame(res_y)
        st.dataframe(df_y.style.applymap(lambda v: 'color: red; font-weight: bold' if v == 'FAIL' else 'color: green; font-weight: bold', subset=['Status']), use_container_width=True)
