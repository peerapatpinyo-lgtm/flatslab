# tab_calc.py
import streamlit as st
import pandas as pd

# ==========================================
# 1. HELPER: CSS STYLING
# ==========================================
def inject_custom_css():
    st.markdown("""
    <style>
        .calc-header {
            background-color: #f8f9fa;
            border-left: 5px solid #0288d1;
            padding: 10px 15px;
            font-weight: 700;
            font-size: 1.1rem;
            color: #0277bd;
            margin-top: 20px;
            margin-bottom: 10px;
            border-radius: 0 4px 4px 0;
        }
        .formula-box {
            background-color: #ffffff;
            border: 1px solid #e0e0e0;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 10px;
            text-align: center;
        }
        .result-pass {
            color: #2e7d32;
            font-weight: bold;
            background-color: #e8f5e9;
            padding: 2px 8px;
            border-radius: 4px;
        }
        .result-fail {
            color: #c62828;
            font-weight: bold;
            background-color: #ffebee;
            padding: 2px 8px;
            border-radius: 4px;
        }
        .sub-text {
            font-size: 0.85rem;
            color: #616161;
        }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. HELPER: RENDER PUNCHING CHECK
# ==========================================
def render_punching_details(res, label, title):
    """Render details for a single punching shear check."""
    
    st.markdown(f'<div class="calc-header">{title}</div>', unsafe_allow_html=True)
    st.markdown(f"**Condition:** {label}")
    
    # 1. Critical Section Geometry
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Effective Depth (d)", f"{res['d']:.2f} cm")
    with c2:
        st.metric("Perimeter (b0)", f"{res['b0']:.2f} cm")
    with c3:
        # Check if beta exists (some calculation functions might not return it if simplified)
        beta_val = res.get('beta', 0)
        st.metric("Ratio Long/Short (β)", f"{beta_val:.2f}")

    # 2. ACI Formulas
    st.markdown("**ACI 318 Shear Capacity Formulas ($V_c$):**")
    with st.container():
        st.latex(r"V_{c1} = 0.53 \left(1 + \frac{2}{\beta}\right) \sqrt{f'_c} b_0 d")
        st.latex(r"V_{c2} = 0.53 \left(\frac{\alpha_s d}{b_0} + 2\right) \sqrt{f'_c} b_0 d")
        st.latex(r"V_{c3} = 1.06 \sqrt{f'_c} b_0 d")
    
    # 3. Calculated Capacities
    df_cap = pd.DataFrame({
        "Equation": ["Vc1 (Aspect Ratio)", "Vc2 (Perimeter)", "Vc3 (Basic)"],
        "Capacity (kg)": [res['Vc1'], res['Vc2'], res['Vc3']]
    })
    # Find minimum
    vc_governing = min(res['Vc1'], res['Vc2'], res['Vc3'])
    phi_vn = 0.85 * vc_governing
    
    # Highlight the governing row
    st.dataframe(df_cap.style.format({"Capacity (kg)": "{:,.0f}"}), use_container_width=True, hide_index=True)

    # 4. Final Check
    st.markdown("---")
    col_final1, col_final2 = st.columns([2, 1])
    
    with col_final1:
        st.write(f"Governing $V_c$: **{vc_governing:,.0f}** kg")
        st.write(f"Design Strength $\phi V_n$ ($\phi=0.85$): **{phi_vn:,.0f}** kg")
        st.write(f"Factored Load $V_u$: **{res['Vu']:,.0f}** kg")
    
    with col_final2:
        ratio = res['Vu'] / phi_vn if phi_vn > 0 else 999
        status = "PASS" if ratio <= 1.0 else "FAIL"
        color_cls = "result-pass" if status == "PASS" else "result-fail"
        
        st.markdown(f"""
        <div style="text-align: center; border: 2px solid #ddd; padding: 10px; border-radius: 8px;">
            <div style="font-size: 0.9rem; color: #757575;">Demand/Capacity</div>
            <div style="font-size: 1.8rem; font-weight: bold;">{ratio:.2f}</div>
            <span class="{color_cls}">{status}</span>
        </div>
        """, unsafe_allow_html=True)

# ==========================================
# 3. MAIN RENDER FUNCTION
# ==========================================
def render(punch_res, v_oneway_res, mat_props, loads):
    inject_custom_css()
    
    st.markdown("### 📑 Structural Calculation Report")
    st.caption(f"Date: {pd.Timestamp.now().strftime('%d %B %Y')}")
    
    # --- SECTION 1: DESIGN PARAMETERS ---
    with st.expander("1. Design Parameters", expanded=False):
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Concrete (fc')", f"{mat_props['fc']:.0f} ksc")
        c2.metric("Rebar (fy)", f"{mat_props['fy']:.0f} ksc")
        c3.metric("Slab Thickness", f"{mat_props['h_slab']:.0f} cm")
        c4.metric("Factored Load (Wu)", f"{loads['w_u']:,.0f} kg/m²")

    # --- SECTION 2: ONE-WAY SHEAR ---
    st.markdown('<div class="calc-header">2. One-Way Shear Check (Beam Action)</div>', unsafe_allow_html=True)
    
    c_one1, c_one2 = st.columns([3, 2])
    with c_one1:
        st.write("Checked at distance **d** from support face.")
        st.latex(r"\phi V_c = 0.85 \times 0.53 \sqrt{f'_c} b_w d")
        
        # Display One-Way details
        vu_one = v_oneway_res.get('Vu', 0)
        vc_one = v_oneway_res.get('Vc', 0) # This is usually phi*Vc in calculations.py or needs checking
        phi_vc_one = vc_one # Assuming calculation returns design strength, if returns nominal, multiply by 0.85
        
        st.write(f"• Factored Shear ($V_u$): **{vu_one:,.0f}** kg")
        st.write(f"• Design Capacity ($\phi V_c$): **{phi_vc_one:,.0f}** kg")

    with c_one2:
        ratio_one = v_oneway_res['ratio']
        status_one = "PASS" if ratio_one <= 1.0 else "FAIL"
        color_one = "result-pass" if status_one == "PASS" else "result-fail"
        
        st.markdown(f"""
        <div style="text-align: center; background: #f1f8e9; padding: 15px; border-radius: 8px;">
            <b>Ratio: {ratio_one:.2f}</b><br>
            <span class="{color_one}">{status_one}</span>
        </div>
        """, unsafe_allow_html=True)

    # --- SECTION 3: TWO-WAY (PUNCHING) SHEAR ---
    st.markdown("---")
    
    # Check if Dual Case (Drop Panel) or Single Case
    if punch_res.get('is_dual', False):
        st.info("ℹ️ **Drop Panel Detected:** Performing two critical section checks.")
        
        tab_inner, tab_outer = st.tabs(["check 1: Column Face", "check 2: Drop Panel Face"])
        
        with tab_inner:
            render_punching_details(punch_res['check_1'], 
                                    "Critical Section at d/2 from Column Face", 
                                    "3.1 Inside Drop Panel (Punching at Column)")
            
        with tab_outer:
            render_punching_details(punch_res['check_2'], 
                                    "Critical Section at d/2 from Drop Panel Edge", 
                                    "3.2 Outside Drop Panel (Punching at Drop Edge)")
            
    else:
        render_punching_details(punch_res, 
                                "Critical Section at d/2 from Column Face", 
                                "3. Punching Shear Analysis")
