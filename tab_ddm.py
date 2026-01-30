import streamlit as st
import pandas as pd
from calculations import design_rebar_detailed

def render_dual(data_x, data_y, mat_props, wu):
    """
    Render DDM Calculation for both X and Y directions
    """
    st.header("2. Direct Design Method (DDM)")
    
    # Create Tabs for X and Y inside the section
    t1, t2 = st.tabs([f"↔️ {data_x['axis']}", f"↕️ {data_y['axis']}"])
    
    with t1:
        render_direction_panel(data_x, mat_props, wu)
        
    with t2:
        render_direction_panel(data_y, mat_props, wu)

def render_direction_panel(data, mat, wu):
    """
    Internal function to render one direction
    """
    # Unpack
    L_span = data['L_span']
    L_width = data['L_width']
    M_vals = data['M_vals']
    fc = mat['fc']
    fy = mat['fy']
    h_slab = mat['h_slab']
    cover = mat['cover']
    d_bar = mat['d_bar']
    
    # Calculate d for flexure (ignoring drop panel for main span)
    d_flex = h_slab - cover - (d_bar/20.0) 
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("📋 Design Params")
        st.write(f"**Span ($L_1$):** {L_span:.2f} m")
        st.write(f"**Width ($L_2$):** {L_width:.2f} m")
        st.write(f"**Total Moment ($M_o$):** {data['Mo']:,.2f} kg-m")
        st.info(f"Using d = {d_flex:.2f} cm (for Moment)")

    with col2:
        st.subheader("🏗️ Reinforcement Design")
        
        # Prepare Data for Table
        results = []
        
        # Define the strips to check
        checks = [
            ("Column Strip (-)", M_vals['M_cs_neg'], L_width/2.0),
            ("Column Strip (+)", M_vals['M_cs_pos'], L_width/2.0),
            ("Middle Strip (-)", M_vals['M_ms_neg'], L_width/2.0),
            ("Middle Strip (+)", M_vals['M_ms_pos'], L_width/2.0),
        ]
        
        for name, Mu, width_strip in checks:
            # Width of strip in cm (Column strip is roughly L2/2)
            b_strip = width_strip * 100 
            
            # Call Cycle 1 Logic
            As_req, rho, note, status = design_rebar_detailed(Mu, b_strip, d_flex, fc, fy)
            
            # Append to list
            results.append({
                "Location": name,
                "Mu (kg-m)": f"{Mu:,.0f}",
                "As Req (cm²)": f"{As_req:.2f}",
                "Status": status,
                "Note": note
            })
            
        # Display as DataFrame
        df = pd.DataFrame(results)
        
        # Custom Highlight Function
        def highlight_status(val):
            color = '#d1e7dd' if val == 'OK' else '#f8d7da' # Green / Red
            return f'background-color: {color}'

        st.dataframe(
            df.style.applymap(highlight_status, subset=['Status']),
            use_container_width=True,
            hide_index=True
        )
        
        # Guide for User
        st.markdown(f"""
        > **คำแนะนำ:** > * **As Req:** คือปริมาณเหล็กเสริมที่ต้องการในหน้าตัด (cm²)  
        > * เลือกเหล็กเสริมให้มากกว่าค่านี้ (เช่น {d_bar}mm)  
        """)
