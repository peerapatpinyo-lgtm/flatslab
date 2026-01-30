# tab_ddm.py
import streamlit as st
import pandas as pd
import numpy as np
from calculations import design_rebar_detailed

def render_rebar_selector(label, default_spacing, key_suffix):
    """Helper to create consistent rebar selectors"""
    c1, c2 = st.columns([2, 1])
    with c1:
        spacing = st.slider(f"Spacing @ {label} (cm)", 10.0, 30.0, default_spacing, 2.5, key=f"sp_{key_suffix}")
    with c2:
        # Just visualization of the selection
        st.write(f"👉 Use DB-@ {spacing:.1f} cm")
    return spacing

def render_calculation_step(title, Mu, b, d, fc, fy, spacing, d_bar):
    """
    Renders a highly detailed, step-by-step calculation block for one strip.
    """
    # 1. Calculate Required Steel
    As_req, rho_req, note, status_calc = design_rebar_detailed(Mu, b, d, fc, fy)
    
    # 2. Calculate Provided Steel
    As_provided = (np.pi * (d_bar/10)**2 / 4) * (100 / spacing) * (b/100) # Total As in width b
    
    # 3. Design Check
    dc_status = "OK" if As_provided >= As_req else "FAIL"
    dc_color = "green" if dc_status == "OK" else "red"
    
    # --- RENDER DISPLAY ---
    st.markdown(f"**{title}**")
    
    # A. Load Info
    st.markdown(f"""
    - Moment ($M_u$): **{Mu:,.0f} kg-m**
    - Strip Width ($b$): {b:.0f} cm
    - Effective Depth ($d$): {d:.2f} cm
    """)
    
    # B. Detailed Math (Expandable)
    with st.expander(f"📝 ดูรายการคำนวณละเอียด ({title})"):
        st.markdown("##### 1. Flexural Design Parameters")
        st.latex(r"R_n = \frac{M_u}{\phi b d^2}")
        
        # Calculate Rn for display
        phi = 0.90
        Rn = (Mu * 100) / (phi * b * d**2)
        st.latex(f"R_n = \\frac{{{Mu*100:,.0f}}}{{0.9 \\times {b:.0f} \\times {d:.2f}^2}} = {Rn:.2f} \\text{{ ksc}}")
        
        st.markdown("##### 2. Reinforcement Ratio ($\\rho$)")
        st.latex(r"\rho_{req} = \frac{0.85 f_c'}{f_y} \left( 1 - \sqrt{1 - \frac{2 R_n}{0.85 f_c'}} \right)")
        
        if status_calc == "FAIL":
            st.error(f"Calculation Error: {note}")
        else:
            st.write(f"Calculated $\\rho_{{req}}$ = {rho_req:.5f}")
            st.write(f"*(Note: Controls by {note})*")
            
            st.markdown("##### 3. Required Steel Area ($A_s$)")
            st.latex(r"A_{s,req} = \rho b d")
            st.latex(f"A_{{s,req}} = {rho_req:.5f} \\times {b:.0f} \\times {d:.2f} = \\mathbf{{{As_req:.2f}}} \\text{{ cm}}^2")

    # C. Conclusion & User Selection Check
    st.markdown(f"""
    <div style='background-color: #f8f9fa; padding: 10px; border-radius: 5px; border-left: 4px solid {dc_color};'>
        <div style='display: flex; justify-content: space-between;'>
            <span>Required $A_s$: <b>{As_req:.2f}</b> cm²</span>
            <span>Provided $A_s$ (DB{d_bar}@{spacing}): <b>{As_provided:.2f}</b> cm²</span>
        </div>
        <div style='margin-top: 5px; font-weight: bold; color: {dc_color};'>
            Status: {dc_status} (Ratio: {As_provided/As_req if As_req > 0 else 99:.2f})
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    return {
        "Location": title,
        "Mu (kg-m)": Mu,
        "As Req (cm2)": As_req,
        "As Prov (cm2)": As_provided,
        "Status": dc_status
    }

def render_direction_tab(direction_name, data, mat, w_u):
    """
    Renders the complete design page for one direction (X or Y)
    """
    # Unpack Data
    L_span = data['L_span']
    L_width = data['L_width']
    ln = data['ln']
    Mo = data['Mo']
    M_vals = data['M_vals']
    
    fc, fy = mat['fc'], mat['fy']
    h_slab, cover = mat['h_slab'], mat['cover']
    d_bar = mat['d_bar']
    
    d_eff = h_slab - cover - (d_bar/20)/2 # One layer assumption
    
    st.header(f"📐 Design Direction: {direction_name}-Axis")
    
    # ==========================================
    # STEP 1: MOMENT CALCULATION
    # ==========================================
    st.markdown("### Step 1: Total Static Moment ($M_o$)")
    col_m1, col_m2 = st.columns([1, 1.5])
    with col_m1:
        st.info(f"""
        **Input Parameters:**
        - $L_2$ (Width) = {L_width:.2f} m
        - $l_n$ (Clear Span) = {ln:.2f} m
        - $w_u$ (Load) = {w_u:,.0f} kg/m²
        """)
    with col_m2:
        st.latex(r"M_o = \frac{w_u L_2 l_n^2}{8}")
        st.latex(f"M_o = \\frac{{{w_u:,.0f} \\times {L_width} \\times {ln:.2f}^2}}{{8}} = \\mathbf{{{Mo:,.0f}}} \\text{{ kg-m}}")

    st.markdown("---")

    # ==========================================
    # STEP 2: STRIP WIDTHS & INTERACTIVE DESIGN
    # ==========================================
    st.markdown("### Step 2: Strip Design & Reinforcement")
    
    # Calculate Strip Widths
    # Column Strip width is min(L1, L2)/2 per side (assuming interior for simplicity or full width logic)
    # Simplified: CS Width = min(L_span, L_width)/2 (Total CS width)
    # Actually standard is: 2 * (0.25 * min(L1, L2)) = 0.5 * min
    w_cs = 0.5 * min(L_span, L_width) * 100 # cm
    w_ms = (L_width * 100) - w_cs           # cm
    
    st.caption(f"💡 Column Strip Width = {w_cs:.0f} cm | Middle Strip Width = {w_ms:.0f} cm")

    # Layout: 2 Columns (CS vs MS)
    col_cs, col_ms = st.columns(2)
    
    # --- A. COLUMN STRIP (CS) ---
    with col_cs:
        st.subheader("🅰️ Column Strip (CS)")
        st.markdown(f"width $b$ = {w_cs:.0f} cm")
        
        # Selector
        st.markdown("**Select Rebar:**")
        s_cs_top = render_rebar_selector("Top (Neg)", 15.0, f"{direction_name}_cs_top")
        s_cs_bot = render_rebar_selector("Bot (Pos)", 20.0, f"{direction_name}_cs_bot")
        
        st.markdown("#### Detailed Checks")
        # Calc Top
        res_cs_neg = render_calculation_step(
            "CS-Top (Negative)", M_vals['M_cs_neg'], w_cs, d_eff, fc, fy, s_cs_top, d_bar
        )
        st.write("") # Spacer
        # Calc Bot
        res_cs_pos = render_calculation_step(
            "CS-Bottom (Positive)", M_vals['M_cs_pos'], w_cs, d_eff, fc, fy, s_cs_bot, d_bar
        )

    # --- B. MIDDLE STRIP (MS) ---
    with col_ms:
        st.subheader("🅱️ Middle Strip (MS)")
        st.markdown(f"width $b$ = {w_ms:.0f} cm")
        
        # Selector
        st.markdown("**Select Rebar:**")
        s_ms_top = render_rebar_selector("Top (Neg)", 20.0, f"{direction_name}_ms_top")
        s_ms_bot = render_rebar_selector("Bot (Pos)", 20.0, f"{direction_name}_ms_bot")
        
        st.markdown("#### Detailed Checks")
        # Calc Top
        res_ms_neg = render_calculation_step(
            "MS-Top (Negative)", M_vals['M_ms_neg'], w_ms, d_eff, fc, fy, s_ms_top, d_bar
        )
        st.write("") # Spacer
        # Calc Bot
        res_ms_pos = render_calculation_step(
            "MS-Bottom (Positive)", M_vals['M_ms_pos'], w_ms, d_eff, fc, fy, s_ms_bot, d_bar
        )

    # ==========================================
    # STEP 3: SUMMARY TABLE (SCHEDULE)
    # ==========================================
    st.markdown("---")
    st.markdown("### 📋 Design Summary (Rebar Schedule)")
    
    summary_data = [
        ["Column Strip", "Top (Support)", f"{M_vals['M_cs_neg']:,.0f}", f"DB{d_bar} @ {s_cs_top:.0f}", res_cs_neg['Status']],
        ["Column Strip", "Bottom (Mid)", f"{M_vals['M_cs_pos']:,.0f}", f"DB{d_bar} @ {s_cs_bot:.0f}", res_cs_pos['Status']],
        ["Middle Strip", "Top (Support)", f"{M_vals['M_ms_neg']:,.0f}", f"DB{d_bar} @ {s_ms_top:.0f}", res_ms_neg['Status']],
        ["Middle Strip", "Bottom (Mid)", f"{M_vals['M_ms_pos']:,.0f}", f"DB{d_bar} @ {s_ms_bot:.0f}", res_ms_pos['Status']],
    ]
    
    df = pd.DataFrame(summary_data, columns=["Strip", "Location", "Mu (kg-m)", "Selected Rebar", "Status"])
    
    # Custom highlighting for DataFrame
    def highlight_status(val):
        color = '#d1e7dd' if val == 'OK' else '#f8d7da'
        return f'background-color: {color}'

    st.dataframe(df.style.applymap(highlight_status, subset=['Status']), use_container_width=True)


def render_dual(data_x, data_y, mat_props, w_u):
    """
    Main entry point for the DDM Tab. 
    Handles switching between X and Y directions.
    """
    
    st.write("### 🏗️ Direct Design Method (Interactive Rebar Design)")
    st.info("💡 Adjust the **Spacing (Slider)** to find the optimal reinforcement. The system checks strength ($M_n$) and Minimum Steel ($A_{s,min}$) automatically.")
    
    tab_x, tab_y = st.tabs(["➡️ X-Direction Analysis", "⬆️ Y-Direction Analysis"])
    
    with tab_x:
        render_direction_tab("X", data_x, mat_props, w_u)
        
    with tab_y:
        render_direction_tab("Y", data_y, mat_props, w_u)
