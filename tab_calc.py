# tab_calc.py
import streamlit as st
import pandas as pd
import numpy as np

# ==========================================
# 1. HELPER: CSS & CARD STYLING
# ==========================================
def inject_custom_css():
    st.markdown("""
    <style>
        /* Global Font */
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
        
        /* Metric Card Styles (Same as Dashboard) */
        .metric-card {
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            text-align: center;
            margin-bottom: 10px;
        }
        .metric-label { font-size: 0.8rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600; }
        .metric-value { font-size: 1.5rem; font-weight: 700; color: #0f172a; margin: 5px 0; }
        .metric-status { font-size: 0.8rem; font-weight: 600; padding: 2px 8px; border-radius: 12px; display: inline-block;}
        .status-pass { background-color: #dcfce7; color: #166534; }
        .status-fail { background-color: #fee2e2; color: #991b1b; }
        .status-info { background-color: #f1f5f9; color: #334155; }
        .metric-sub { font-size: 0.75rem; color: #94a3b8; margin-top: 5px; }

        /* Section Headers */
        .calc-header {
            background-color: #f8f9fa;
            border-left: 5px solid #0288d1;
            padding: 10px 15px;
            font-weight: 700;
            font-size: 1.1rem;
            color: #0277bd;
            margin-top: 25px;
            margin-bottom: 15px;
            border-radius: 0 4px 4px 0;
        }
    </style>
    """, unsafe_allow_html=True)

def metric_card(label, value, status, subtext=""):
    color_class = "status-pass" if status == "PASS" else ("status-fail" if status == "FAIL" else "status-info")
    icon = "✅" if status == "PASS" else ("❌" if status == "FAIL" else "ℹ️")
    
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-status {color_class}">{icon} {status}</div>
        <div class="metric-sub">{subtext}</div>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# 2. HELPER: RENDER PUNCHING DETAILS
# ==========================================
def render_punching_details(res, label):
    st.markdown(f"**Condition:** {label}")
    
    # Geometry
    c1, c2, c3 = st.columns(3)
    c1.metric("Effective Depth (d)", f"{res['d']:.2f} cm")
    c2.metric("Perimeter (b0)", f"{res['b0']:.2f} cm")
    beta_val = res.get('beta', 0)
    c3.metric("Ratio (β)", f"{beta_val:.2f}")

    # Formulas
    with st.expander("Show ACI Formulas"):
        st.latex(r"V_{c1} = 0.53 \left(1 + \frac{2}{\beta}\right) \sqrt{f'_c} b_0 d")
        st.latex(r"V_{c2} = 0.53 \left(\frac{\alpha_s d}{b_0} + 2\right) \sqrt{f'_c} b_0 d")
        st.latex(r"V_{c3} = 1.06 \sqrt{f'_c} b_0 d")
    
    # Table
    vc_governing = min(res['Vc1'], res['Vc2'], res['Vc3'])
    phi_vn = 0.85 * vc_governing
    
    df_cap = pd.DataFrame({
        "Mode": ["Aspect Ratio (Vc1)", "Perimeter (Vc2)", "Basic (Vc3)"],
        "Capacity (kg)": [res['Vc1'], res['Vc2'], res['Vc3']]
    })
    st.dataframe(df_cap.style.format({"Capacity (kg)": "{:,.0f}"}), use_container_width=True, hide_index=True)

    # Conclusion
    col_res1, col_res2 = st.columns([2, 1])
    with col_res1:
        st.write(f"• Governing Vc: **{vc_governing:,.0f}** kg")
        st.write(f"• Design Strength ($\phi V_n$): **{phi_vn:,.0f}** kg")
        st.write(f"• Factored Load ($V_u$): **{res['Vu']:,.0f}** kg")
    with col_res2:
        ratio = res['Vu'] / phi_vn if phi_vn > 0 else 999
        status = "PASS" if ratio <= 1 else "FAIL"
        st.caption(f"Ratio: {ratio:.2f} ({status})")
        st.progress(min(ratio, 1.0))

# ==========================================
# 3. MAIN RENDER FUNCTION
# ==========================================
def render(punch_res, v_oneway_res, mat_props, loads, Lx, Ly): # Added Lx, Ly inputs
    inject_custom_css()
    
    st.markdown("### 📑 Detailed Calculation Report")
    st.caption(f"Generated on: {pd.Timestamp.now().strftime('%d %B %Y')}")
    
    # -----------------------------------------------
    # SECTION 1: EXECUTIVE SUMMARY (THE CARDS)
    # -----------------------------------------------
    st.markdown("#### 1. Executive Summary")
    c1, c2, c3, c4 = st.columns(4)
    
    # Card 1: Punching
    with c1:
        status_punch = punch_res['status']
        metric_card("Punching Shear", f"{punch_res['ratio']:.2f}", status_punch, "Capacity Ratio")
        
    # Card 2: One-Way
    with c2:
        status_one = v_oneway_res['status']
        # Determine direction text
        dir_text = "Check Both Axes"
        # If specific direction data is available in v_oneway_res, use it (depends on implementation)
        metric_card("One-Way Shear", f"{v_oneway_res['ratio']:.2f}", status_one, "Beam Action Check")

    # Card 3: Deflection
    with c3:
        h_slab = mat_props['h_slab']
        h_min = max(Lx, Ly)*100 / 33.0
        status_def = "PASS" if h_slab >= h_min else "CHECK"
        metric_card("Deflection", f"L/33", status_def, f"Min: {h_min:.1f} cm")

    # Card 4: Load
    with c4:
        metric_card("Factored Load", f"{loads['w_u']:,.0f}", "INFO", "kg/m² (ULS)")

    st.markdown("---")

    # -----------------------------------------------
    # SECTION 2: ONE-WAY SHEAR DETAILS
    # -----------------------------------------------
    st.markdown('<div class="calc-header">2. One-Way Shear Analysis</div>', unsafe_allow_html=True)
    
    col_one1, col_one2 = st.columns([1, 1])
    with col_one1:
        st.markdown("**Concept:** Check beam shear at distance 'd' from support.")
        st.latex(r"\phi V_c = 0.85 \times 0.53 \sqrt{f'_c} b_w d")
        st.info("Critical case is taken from the axis with higher stress ratio.")
    
    with col_one2:
        vu = v_oneway_res.get('Vu', 0)
        vc = v_oneway_res.get('Vc', 0) # Assuming this is Nominal Vc
        phi_vc = vc # If your calculation already returns Design Strength, keep it. Otherwise * 0.85
        
        st.write(f"**Results:**")
        st.write(f"• Factored Shear ($V_u$): **{vu:,.0f}** kg")
        st.write(f"• Design Capacity ($\phi V_c$): **{phi_vc:,.0f}** kg")
        
        ratio = v_oneway_res['ratio']
        st.metric("Stress Ratio", f"{ratio:.2f}", delta="Safe" if ratio <=1 else "Unsafe", delta_color="inverse")

    # -----------------------------------------------
    # SECTION 3: PUNCHING SHEAR DETAILS
    # -----------------------------------------------
    st.markdown('<div class="calc-header">3. Two-Way (Punching) Shear Analysis</div>', unsafe_allow_html=True)
    
    if punch_res.get('is_dual', False):
        st.success("✅ **Dual Check Required:** Drop Panel detected.")
        t1, t2 = st.tabs(["Check 1: Column Face", "Check 2: Drop Panel Edge"])
        with t1: render_punching_details(punch_res['check_1'], "Inner Section (d/2 from Column)")
        with t2: render_punching_details(punch_res['check_2'], "Outer Section (d/2 from Drop Panel)")
    else:
        render_punching_details(punch_res, "Critical Section (d/2 from Column)")
