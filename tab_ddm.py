import streamlit as st
import numpy as np
from calculations import design_rebar_detailed

def render_dual(data_x, data_y, mat_props, wu):
    """
    Render DDM Calculation for both X and Y directions
    """
    st.header("2. Direct Design Method (DDM) & Reinforcement")
    st.caption("ตรวจสอบเหล็กเสริมตามโมเมนต์ที่คำนวณได้ (User Selects Rebar)")
    
    # Create Tabs for X and Y inside the section
    t1, t2 = st.tabs([f"↔️ {data_x['axis']}", f"↕️ {data_y['axis']}"])
    
    with t1:
        render_interactive_panel(data_x, mat_props, "X")
        
    with t2:
        render_interactive_panel(data_y, mat_props, "Y")

def render_interactive_panel(data, mat, direction_label):
    """
    Interactive function: User selects spacing, Code checks capacity
    """
    # Unpack Data
    L_span = data['L_span']
    L_width = data['L_width']
    M_vals = data['M_vals']
    
    fc = mat['fc']
    fy = mat['fy']
    h_slab = mat['h_slab']
    cover = mat['cover']
    # Default bar size from global input, but can be overridden per strip
    d_bar_global = mat['d_bar'] 
    
    d_flex = h_slab - cover - (d_bar_global/20.0)
    
    # --- Summary Header ---
    c1, c2, c3 = st.columns(3)
    c1.info(f"Span: {L_span:.2f} m")
    c2.info(f"Width: {L_width:.2f} m")
    c3.info(f"Mo: {data['Mo']:,.2f} kg-m")

    st.markdown("---")

    # --- Define Strips to Design ---
    # Structure: (Label, Moment_Value, Strip_Width_m, Key_Suffix)
    strips = [
        ("Column Strip (Neg - Top)", M_vals['M_cs_neg'], L_width/2.0, "cs_neg"),
        ("Column Strip (Pos - Bot)", M_vals['M_cs_pos'], L_width/2.0, "cs_pos"),
        ("Middle Strip (Neg - Top)", M_vals['M_ms_neg'], L_width/2.0, "ms_neg"),
        ("Middle Strip (Pos - Bot)", M_vals['M_ms_pos'], L_width/2.0, "ms_pos"),
    ]

    # --- Loop Generate Rows ---
    for label, Mu, width_m, key in strips:
        with st.container():
            # Layout: 4 Columns (Info | Input Rebar | Check Result | Status)
            col_info, col_input, col_result, col_status = st.columns([1.2, 1.5, 1.2, 0.8])
            
            # 1. Info Column
            with col_info:
                st.markdown(f"**{label}**")
                st.caption(f"Mu: {Mu:,.0f} kg-m")
                
                # Calculate Required Area (Engineering Logic)
                As_req, rho, note, status_calc = design_rebar_detailed(Mu, width_m*100, d_flex, fc, fy)
                st.markdown(f"Req: **{As_req:.2f}** cm²")

            # 2. Input Column (User Interaction restored!)
            with col_input:
                # User chooses Bar Diameter & Spacing
                c_sub1, c_sub2 = st.columns(2)
                with c_sub1:
                    sel_db = st.selectbox("DB", [10,12,16,20,25], index=1, key=f"db_{direction_label}_{key}")
                with c_sub2:
                    sel_space = st.number_input("@Spacing (cm)", min_value=5.0, max_value=40.0, value=20.0, step=2.5, key=f"sp_{direction_label}_{key}")

            # 3. Calculation Check Column
            with col_result:
                # Calculate Area Provided
                # Area of 1 bar = pi * d^2 / 4
                area_one_bar = 3.1416 * (sel_db/10.0)**2 / 4
                num_bars = (width_m * 100) / sel_space
                As_provided = num_bars * area_one_bar
                
                st.markdown(f"Prov: **{As_provided:.2f}** cm²")
                st.caption(f"(Use DB{sel_db}@{sel_space:.0f})")

            # 4. Status Column (Visual Feedback)
            with col_status:
                # Compare Provided vs Required
                is_safe = As_provided >= As_req
                if is_safe:
                    st.success("✅ PASS")
                else:
                    st.error("❌ FAIL")
            
            st.divider()
