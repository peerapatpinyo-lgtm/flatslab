# tab_calc.py
import streamlit as st
import pandas as pd
import numpy as np

# ==========================================
# 1. HELPER: VISUAL STYLING (CSS)
# ==========================================
def inject_custom_css():
    st.markdown("""
    <style>
        /* Main Report Container */
        .report-container {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            color: #333;
        }

        /* 1. Executive Summary Cards */
        .summary-box {
            background-color: #ffffff;
            border: 1px solid #e0e0e0;
            border-radius: 10px;
            padding: 15px;
            text-align: center;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
            transition: transform 0.2s;
        }
        .summary-box:hover { transform: translateY(-2px); }
        .summary-label { font-size: 0.85rem; color: #757575; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
        .summary-val { font-size: 1.6rem; font-weight: 800; color: #1a237e; margin: 8px 0; }
        
        /* Status Badges */
        .badge { padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 700; display: inline-block; }
        .badge-pass { background-color: #e8f5e9; color: #2e7d32; border: 1px solid #c8e6c9; }
        .badge-fail { background-color: #ffebee; color: #c62828; border: 1px solid #ffcdd2; }
        .badge-info { background-color: #e3f2fd; color: #1565c0; border: 1px solid #bbdefb; }

        /* 2. Topic Headers */
        .topic-header {
            margin-top: 35px;
            margin-bottom: 20px;
            border-bottom: 2px solid #eeeeee;
            padding-bottom: 10px;
            display: flex;
            align-items: center;
        }
        .topic-number {
            background-color: #1a237e;
            color: white;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            text-align: center;
            line-height: 30px;
            font-weight: bold;
            margin-right: 15px;
        }
        .topic-title { font-size: 1.3rem; font-weight: 700; color: #37474f; }

        /* 3. Sub-components */
        .calc-card {
            background-color: #f8f9fa;
            border-left: 4px solid #3949ab;
            padding: 15px 20px;
            border-radius: 4px;
            margin-bottom: 15px;
        }
        .formula-box {
            text-align: center;
            background: #ffffff;
            border: 1px dashed #bdbdbd;
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
        }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. HELPER: COMPONENT RENDERERS
# ==========================================

def card_metric(label, value, status, subtext=""):
    """Renders a single summary card"""
    if status == "PASS":
        badge_cls = "badge-pass"
        icon = "✅ PASS"
    elif status == "FAIL":
        badge_cls = "badge-fail"
        icon = "❌ FAIL"
    else:
        badge_cls = "badge-info"
        icon = f"ℹ️ {status}"

    st.markdown(f"""
    <div class="summary-box">
        <div class="summary-label">{label}</div>
        <div class="summary-val">{value}</div>
        <div class="badge {badge_cls}">{icon}</div>
        <div style="margin-top:8px; font-size:0.75rem; color:#9e9e9e;">{subtext}</div>
    </div>
    """, unsafe_allow_html=True)

def render_punching_details(res, sub_title):
    """Renders details for one punching shear critical section"""
    st.markdown(f"**📍 Location:** {sub_title}")
    
    # 1. Geometric Properties
    c1, c2, c3 = st.columns(3)
    c1.metric("Effective Depth (d)", f"{res['d']:.2f} cm")
    c2.metric("Perimeter (b0)", f"{res['b0']:.2f} cm")
    c3.metric("Beta (β)", f"{res.get('beta', 0):.2f}")
    
    # 2. Formulas & Table
    with st.expander("Show Calculation Details (ACI 318)", expanded=True):
        col_f, col_t = st.columns([1, 1])
        with col_f:
            st.caption("Shear Capacity Formulas ($V_c$):")
            st.latex(r"V_{c1} = 0.53 (1 + 2/\beta) \sqrt{f'_c} b_0 d")
            st.latex(r"V_{c2} = 0.53 (\alpha_s d/b_0 + 2) \sqrt{f'_c} b_0 d")
            st.latex(r"V_{c3} = 1.06 \sqrt{f'_c} b_0 d")
        with col_t:
            df_vc = pd.DataFrame({
                "Criteria": ["Aspect Ratio", "Perimeter", "Basic"],
                "Vc Value (kg)": [res['Vc1'], res['Vc2'], res['Vc3']]
            })
            st.dataframe(df_vc.style.format({"Vc Value (kg)": "{:,.0f}"}), use_container_width=True, hide_index=True)
            
    # 3. Final Check
    vc_governing = min(res['Vc1'], res['Vc2'], res['Vc3'])
    phi_vn = 0.85 * vc_governing
    ratio = res['Vu'] / phi_vn if phi_vn > 0 else 999.0
    status = "PASS" if ratio <= 1.0 else "FAIL"
    
    result_col1, result_col2 = st.columns([3, 1.5])
    with result_col1:
        st.markdown(f"""
        <div class="calc-card">
            <div>🔹 Governing Vc: <b>{vc_governing:,.0f} kg</b></div>
            <div>🔹 Design Strength (ϕVn): <b>{phi_vn:,.0f} kg</b> (ϕ=0.85)</div>
            <div style="color:#d32f2f">🔸 Factored Load (Vu): <b>{res['Vu']:,.0f} kg</b></div>
        </div>
        """, unsafe_allow_html=True)
    with result_col2:
        st.metric("Stress Ratio", f"{ratio:.2f}", delta="Safe" if status=="PASS" else "Fail", delta_color="inverse")
    
    st.divider()

# ==========================================
# 3. MAIN RENDER FUNCTION
# ==========================================
def render(punch_res, v_oneway_res, mat_props, loads, Lx, Ly):
    inject_custom_css()
    
    # Header
    st.title("📑 Structural Calculation Report")
    st.caption(f"Project Code: ProFlat-001 | Date: {pd.Timestamp.now().strftime('%d %b %Y')}")
    st.markdown("---")

    # ----------------------------------------------------
    # SECTION 0: EXECUTIVE SUMMARY (DASHBOARD CARDS)
    # ----------------------------------------------------
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        card_metric("Punching Shear", f"{punch_res['ratio']:.2f}", punch_res['status'], "Capacity Ratio")
    with c2:
        card_metric("One-Way Shear", f"{v_oneway_res['ratio']:.2f}", v_oneway_res['status'], "Beam Action")
    with c3:
        h_min = max(Lx, Ly)*100 / 33.0
        s_def = "PASS" if mat_props['h_slab'] >= h_min else "CHECK"
        card_metric("Deflection", f"L/33", s_def, f"Min Thk: {h_min:.1f} cm")
    with c4:
        card_metric("Factored Load", f"{loads['w_u']:,.0f}", "INFO", "kg/m² (ULS)")

    # ----------------------------------------------------
    # SECTION 1: PUNCHING SHEAR
    # ----------------------------------------------------
    st.markdown('<div class="topic-header"><div class="topic-number">1</div><div class="topic-title">Punching Shear Analysis</div></div>', unsafe_allow_html=True)
    
    if punch_res.get('is_dual', False):
        st.info("ℹ️ **Configuration:** Slab with Drop Panel (Checking 2 Critical Sections)")
        render_punching_details(punch_res['check_1'], "Inside Drop Panel (d/2 from Column Face)")
        render_punching_details(punch_res['check_2'], "Outside Drop Panel (d/2 from Drop Panel Edge)")
    else:
        render_punching_details(punch_res, "d/2 from Column Face")

    # ----------------------------------------------------
    # SECTION 2: ONE-WAY SHEAR
    # ----------------------------------------------------
    st.markdown('<div class="topic-header"><div class="topic-number">2</div><div class="topic-title">One-Way Shear Analysis</div></div>', unsafe_allow_html=True)
    
    c_one_L, c_one_R = st.columns([2, 1])
    
    with c_one_L:
        st.write("Checking beam-action shear at distance **d** from support face.")
        st.markdown('<div class="formula-box">', unsafe_allow_html=True)
        st.latex(r"\phi V_n = \phi \cdot 0.53 \sqrt{f'_c} b_w d")
        st.caption("Assuming Unit Width bw = 100 cm")
        st.markdown('</div>', unsafe_allow_html=True)
        
        vu = v_oneway_res.get('Vu', 0)
        vc = v_oneway_res.get('Vc', 0) # Assuming this is Nominal Vc
        phi_vc = vc * 0.85 # Applying phi here if Vc is nominal
        if phi_vc < vc: phi_vc = vc # Guard clause: if input was already design strength, don't reduce again (depends on your calc logic)
        
        st.markdown(f"""
        <div class="calc-card">
            <ul>
                <li>Factored Shear Force ($V_u$): <b>{vu:,.0f} kg</b></li>
                <li>Design Shear Capacity ($\phi V_c$): <b>{phi_vc:,.0f} kg</b></li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with c_one_R:
        ratio = v_oneway_res['ratio']
        status = "PASS" if ratio <= 1.0 else "FAIL"
        color = "green" if status == "PASS" else "red"
        st.markdown(f"""
        <div style="text-align:center; padding:20px; border:2px solid {color}; border-radius:10px;">
            <h3 style="color:{color}">{status}</h3>
            <div style="font-size:2rem; font-weight:bold;">{ratio:.2f}</div>
            <div>Stress Ratio</div>
        </div>
        """, unsafe_allow_html=True)

    # ----------------------------------------------------
    # SECTION 3: DEFLECTION
    # ----------------------------------------------------
    st.markdown('<div class="topic-header"><div class="topic-number">3</div><div class="topic-title">Deflection Control</div></div>', unsafe_allow_html=True)
    
    c_def1, c_def2 = st.columns([1.5, 1])
    with c_def1:
        st.markdown("**Criteria:** ACI 318 Table 8.3.1.1 (Min Thickness for Slabs without Interior Beams)")
        max_span = max(Lx, Ly)
        st.latex(r"h_{min} = \frac{L_n}{33} \quad \text{(for Interior Panels)}")
        
        st.write(f"• Longest Span ($L$): **{max_span:.2f} m**")
        st.write(f"• Required Thickness ($h_{{min}}$): **{h_min:.2f} cm**")
    
    with c_def2:
        h_actual = mat_props['h_slab']
        delta = h_actual - h_min
        icon = "✅" if delta >= 0 else "⚠️"
        st.markdown(f"""
        <div style="background:#f1f8e9; padding:15px; border-radius:8px;">
            <strong>Actual Slab Thickness:</strong>
            <div style="font-size:24px; font-weight:bold; color:#2e7d32;">{h_actual:.0f} cm</div>
            <hr>
            <div>{icon} Margin: {delta:+.1f} cm</div>
        </div>
        """, unsafe_allow_html=True)

    # ----------------------------------------------------
    # SECTION 4: FACTORED LOAD
    # ----------------------------------------------------
    st.markdown('<div class="topic-header"><div class="topic-number">4</div><div class="topic-title">Factored Load Analysis (ULS)</div></div>', unsafe_allow_html=True)
    
    # Data Prep
    h_m = mat_props['h_slab'] / 100.0
    w_self = h_m * 2400
    sdl = loads['SDL']
    ll = loads['LL']
    dl_total = w_self + sdl
    wu_calc = 1.2*dl_total + 1.6*ll
    
    st.markdown("load Combination: **$w_u = 1.2D + 1.6L$**")
    
    # Table Styling
    load_data = [
        ["Self-Weight (D1)", f"{h_m:.2f}m × 2400", f"{w_self:.1f}", "1.2", f"{1.2*w_self:.1f}"],
        ["Superimposed (D2)", "SDL Input", f"{sdl:.1f}", "1.2", f"{1.2*sdl:.1f}"],
        ["Live Load (L)", "LL Input", f"{ll:.1f}", "1.6", f"{1.6*ll:.1f}"],
        ["<b>TOTAL (ULS)</b>", "-", f"<b>{dl_total+ll:,.1f}</b>", "-", f"<b>{wu_calc:,.1f}</b>"]
    ]
    
    df_load = pd.DataFrame(load_data, columns=["Load Type", "Calculation", "Service (kg/m²)", "Factor", "Factored (kg/m²)"])
    
    # Use HTML table for better control over bold text
    st.markdown(df_load.to_html(escape=False, index=False, justify='center', border=0, classes='table'), unsafe_allow_html=True)
    
    st.markdown(f"""
    <div style="margin-top:15px; text-align:right; font-size:1.1rem;">
        Total Design Load ($w_u$) = <b style="color:#d32f2f; font-size:1.4rem;">{wu_calc:,.0f} kg/m²</b>
    </div>
    """, unsafe_allow_html=True)
