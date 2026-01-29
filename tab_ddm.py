import streamlit as st
import pandas as pd
import numpy as np
import ddm_plots 

def render_dual(data_x, data_y, h_slab, d_eff, fc, fy, d_bar, w_u):
    # (ส่วนนี้เหมือนเดิม)
    st.header("2. Direct Design Method (DDM) - Detailed Calculation")
    tab_x, tab_y = st.tabs([
        f"➡️ Design X-Direction (Span {data_x['L_span']}m)", 
        f"⬆️ Design Y-Direction (Span {data_y['L_span']}m)"
    ])
    with tab_x:
        render_single_direction(data_x, h_slab, d_eff, fc, fy, d_bar, w_u)
    with tab_y:
        render_single_direction(data_y, h_slab, d_eff, fc, fy, d_bar, w_u)

def render_single_direction(data, h_slab, d_eff, fc, fy, d_bar, w_u):
    # Extract Data
    L_span = data['L_span']
    L_width = data['L_width']
    c_para = data['c_para']
    ln = data['ln']
    Mo = data['Mo']
    m_vals = data['M_vals']
    dir_name = data['dir']

    # --- Header ---
    st.markdown(f"""
    <div style="background-color:#f8f9fa; padding:10px; border-left:5px solid #0d6efd; margin-bottom:15px;">
        <h5 style="margin:0; color:#0d6efd;">📐 {dir_name} : Span {L_span} m</h5>
    </div>
    """, unsafe_allow_html=True)

    # --- PART 1: CALCULATION DETAILS ---
    col_left, col_right = st.columns([1, 1])
    
    rebar_summary = {} 
    
    with col_left:
        st.subheader("1. Calculation Steps")
        # 1.1 Mo
        with st.expander("🔹 Step 1: Static Moment (Mo)", expanded=False):
            st.latex(r"M_o = " + f"{Mo:,.0f} " + " kg-m")
            st.write(f"(Ln = {ln:.2f} m, Width = {L_width:.2f} m)")
        
        # 1.2 Rebar Loop
        w_cs = min(L_span, L_width) / 2.0
        w_ms = L_width - w_cs
        zones = [
            {"id": "CS_Top", "name": "Column Strip - Top (-)", "M": m_vals["M_cs_neg"], "b": w_cs},
            {"id": "CS_Bot", "name": "Column Strip - Bot (+)", "M": m_vals["M_cs_pos"], "b": w_cs},
            {"id": "MS_Top", "name": "Middle Strip - Top (-)", "M": m_vals["M_ms_neg"], "b": w_ms},
            {"id": "MS_Bot", "name": "Middle Strip - Bot (+)", "M": m_vals["M_ms_pos"], "b": w_ms},
        ]
        
        summary_table = []
        for z in zones:
            # (Logic คำนวณเหมือนเดิม)
            Mu_kgcm = z['M'] * 100
            b_cm = z['b'] * 100
            denom = 0.9 * b_cm * (d_eff**2)
            Rn = Mu_kgcm / denom if denom > 0 else 0
            try:
                term = 1 - (2*Rn)/(0.85*fc)
                if term < 0:
                    res_txt = "FAIL (Deep Check)"
                    rebar_summary[z['id']] = "FAIL"
                else:
                    rho_req = (0.85*fc/fy) * (1 - np.sqrt(term))
                    rho_design = max(rho_req, 0.0018)
                    As_req = rho_design * b_cm * d_eff
                    Ab = 3.14159 * (d_bar/10)**2 / 4
                    n = max(np.ceil(As_req/Ab), 2)
                    spacing = min(b_cm/n, 2*h_slab, 45)
                    res_txt = f"{int(n)}-DB{d_bar}@{int(spacing)}"
                    rebar_summary[z['id']] = res_txt
            except:
                res_txt = "Error"
                rebar_summary[z['id']] = "Error"
            summary_table.append({"Zone": z['name'], "Moment": f"{z['M']:,.0f}", "Reinforcement": res_txt})
        
        st.table(pd.DataFrame(summary_table).set_index("Zone"))

    # --- PART 2: VISUALIZATION ---
    with col_right:
        st.subheader("2. Diagrams")
        # Plot 1: Moment
        fig_mom = ddm_plots.plot_ddm_moment(L_span, c_para, m_vals)
        st.pyplot(fig_mom)

    st.markdown("---")
    
    # --- PART 3: DETAILING DRAWINGS (FULL WIDTH) ---
    st.subheader("3. Detailing Drawings")
    if "FAIL" not in rebar_summary.values():
        c1, c2 = st.columns(2)
        with c1:
            # Side View
            fig_side = ddm_plots.plot_rebar_detailing(L_span, h_slab, c_para, rebar_summary)
            st.pyplot(fig_side)
        with c2:
            # Top View (New!)
            fig_top = ddm_plots.plot_rebar_plan_view(L_span, L_width, c_para, rebar_summary)
            st.pyplot(fig_top)
    else:
        st.error("Cannot draw detailing due to calculation failure.")
