import streamlit as st
import pandas as pd
import numpy as np
from calculations import design_rebar_detailed

def render(Mo, L1, L2, h_slab, d_eff, fc, fy, d_bar, moment_vals):
    st.header("2. Direct Design Method (DDM) & Reinforcement")
    
    # 1. Info Section
    col_m1, col_m2 = st.columns([1, 2])
    with col_m1:
        st.metric("Total Static Moment (Mo)", f"{Mo:,.2f} kg-m")
    with col_m2:
        st.caption("Distribution based on ACI 318 for Interior Panel (Flat Plate)")

    # 2. Rebar Schedule Calculation
    st.subheader("📝 Reinforcement Schedule")
    
    w_cs = min(L1, L2)/2
    w_ms = L2 - w_cs
    Ab = 3.14159 * (d_bar/10)**2 / 4
    
    zones = [
        ("Column Strip: Top (-)", moment_vals["M_cs_neg"], w_cs),
        ("Column Strip: Bot (+)", moment_vals["M_cs_pos"], w_cs),
        ("Middle Strip: Top (-)", moment_vals["M_ms_neg"], w_ms),
        ("Middle Strip: Bot (+)", moment_vals["M_ms_pos"], w_ms),
    ]
    
    schedule_data = []
    
    for z_name, mom, width_m in zones:
        As_req, rho, note, status = design_rebar_detailed(mom, width_m*100, d_eff, fc, fy)
        
        if status == "OK":
            num_bars = np.ceil(As_req / Ab)
            # Minimum 2 bars
            num_bars = max(num_bars, 2)
            spacing = (width_m*100)/num_bars
            
            # Max spacing check (2h or 45cm)
            max_s = min(2*h_slab, 45)
            spacing = min(spacing, max_s)
            
            bar_txt = f"{int(num_bars)} - DB{d_bar}"
            spa_txt = f"@{spacing:.0f} cm"
            icon = "✅"
        else:
            bar_txt = "CHECK DESIGN"
            spa_txt = "-"
            icon = "❌"
            
        schedule_data.append({
            "Status": icon,
            "Zone": z_name,
            "Moment (kg-m)": f"{mom:,.0f}",
            "Strip Width": f"{width_m:.2f} m",
            "As Req": f"{As_req:.2f}",
            "Selection": bar_txt,
            "Spacing": spa_txt,
            "Note": note
        })
        
    df = pd.DataFrame(schedule_data)
    st.dataframe(df, use_container_width=True)
    
    st.markdown(f"**Note:** Calculated using DB{d_bar} (As={Ab:.2f} cm²)")
