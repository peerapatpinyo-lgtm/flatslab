# tab_calc.py
import streamlit as st
import pandas as pd
import numpy as np

# ==========================================
# 1. HELPER: STYLING & UTILS
# ==========================================
def inject_custom_css():
    st.markdown("""
    <style>
        /* Modern Calculation Header */
        .topic-header {
            font-size: 1.2rem;
            font-weight: 700;
            color: #1565c0; /* Blue 800 */
            border-bottom: 2px solid #bbdefb;
            padding-bottom: 8px;
            margin-top: 30px;
            margin-bottom: 20px;
        }
        .topic-header span {
            background-color: #e3f2fd;
            padding: 5px 12px;
            border-radius: 5px 5px 0 0;
            border: 1px solid #bbdefb;
            border-bottom: none;
        }
        /* Subsection Box */
        .sub-box {
            background-color: #f8f9fa;
            border-left: 4px solid #546e7a;
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 15px;
        }
        /* Formula Box */
        .formula-card {
            background-color: #ffffff;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 15px;
            text-align: center;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }
        /* Status Badges */
        .badge-pass { background-color: #c8e6c9; color: #2e7d32; padding: 4px 8px; border-radius: 4px; font-weight: bold; }
        .badge-fail { background-color: #ffcdd2; color: #c62828; padding: 4px 8px; border-radius: 4px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

def render_punching_check_section(res, title_suffix=""):
    """Helper to render one punching check block"""
    
    st.markdown(f"**📍 Critical Section: {title_suffix}**")
    
    # 1. Geometry Data
    c1, c2, c3 = st.columns(3)
    c1.metric("Effective Depth (d)", f"{res['d']:.2f} cm")
    c2.metric("Perimeter (b0)", f"{res['b0']:.2f} cm")
    beta_val = res.get('beta', 0)
    c3.metric("Aspect Ratio (β)", f"{beta_val:.2f}")

    # 2. Capacity Table
    vc_governing = min(res['Vc1'], res['Vc2'], res['Vc3'])
    phi_vn = 0.85 * vc_governing
    
    with st.expander("View ACI 318 Equations & Vc Values", expanded=True):
        col_eq, col_tbl = st.columns([1.2, 1])
        with col_eq:
            st.latex(r"V_{c1} = 0.53 (1 + 2/\beta) \sqrt{f'_c} b_0 d")
            st.latex(r"V_{c2} = 0.53 (\alpha_s d/b_0 + 2) \sqrt{f'_c} b_0 d")
            st.latex(r"V_{c3} = 1.06 \sqrt{f'_c} b_0 d")
        with col_tbl:
            df_vc = pd.DataFrame({
                "Eq.": ["Vc1", "Vc2", "Vc3"],
                "Value (kg)": [res['Vc1'], res['Vc2'], res['Vc3']]
            })
            st.dataframe(df_vc.style.format({"Value (kg)": "{:,.0f}"}), use_container_width=True, hide_index=True)

    # 3. Final Compare
    c_final1, c_final2 = st.columns([2, 1])
    with c_final1:
        st.write(f"Governing $V_c$: **{vc_governing:,.0f}** kg")
        st.write(f"Design Strength $\phi V_n$ (0.85): **{phi_vn:,.0f}** kg")
        st.write(f"Factored Load $V_u$: **{res['Vu']:,.0f}** kg")
    with c_final2:
        ratio = res['Vu'] / phi_vn if phi_vn > 0 else 999
        status = "PASS" if ratio <= 1.0 else "FAIL"
        badge_cls = "badge-pass" if status == "PASS" else "badge-fail"
        
        st.markdown(f"""
        <div style="text-align:center; border:1px solid #ddd; border-radius:8px; padding:10px;">
            <div style="font-size:0.8rem; color:#666;">Capacity Ratio</div>
            <div style="font-size:1.6rem; font-weight:bold;">{ratio:.2f}</div>
            <span class="{badge_cls}">{status}</span>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()

# ==========================================
# 2. MAIN RENDERER
# ==========================================
def render(punch_res, v_oneway_res, mat_props, loads, Lx, Ly):
    inject_custom_css()
    
    st.markdown("### 📑 Detailed Calculation Report")
    
    # ==========================================
    # 1. PUNCHING SHEAR
    # ==========================================
    st.markdown('<div class="topic-header"><span>1. Punching Shear Analysis (Two-Way)</span></div>', unsafe_allow_html=True)
    
    # Check Dual Case
    if punch_res.get('is_dual', False):
        st.info("ℹ️ **Drop Panel Case:** Checking two critical sections.")
        render_punching_check_section(punch_res['check_1'], "Inside Drop Panel (d/2 from Column)")
        render_punching_check_section(punch_res['check_2'], "Outside Drop Panel (d/2 from Drop Edge)")
    else:
        render_punching_check_section(punch_res, "d/2 from Column Face")


    # ==========================================
    # 2. ONE-WAY SHEAR
    # ==========================================
    st.markdown('<div class="topic-header"><span>2. One-Way Shear Analysis (Beam Action)</span></div>', unsafe_allow_html=True)
    
    col_one_L, col_one_R = st.columns([1.5, 1])
    
    with col_one_L:
        st.markdown("**Concept:** Check shear at distance $d$ from support face.")
        st.markdown('<div class="formula-card">', unsafe_allow_html=True)
        st.latex(r"\phi V_c = \phi \times 0.53 \sqrt{f'_c} b_w d")
        st.caption("Where $\phi = 0.85$ for shear")
        st.markdown('</div>', unsafe_allow_html=True)
        
        vu_one = v_oneway_res.get('Vu', 0)
        vc_one = v_oneway_res.get('Vc', 0) # Assuming Nominal
        phi_vc_one = vc_one * 0.85 if vc_one > vu_one else vc_one # Adjust based on your calc logic
        
        st.write(f"• Section Width ($b_w$): **100** cm (Unit Strip)")
        st.write(f"• Factored Shear ($V_u$): **{vu_one:,.0f}** kg")
        st.write(f"• Design Capacity ($\phi V_c$): **{phi_vc_one:,.0f}** kg")

    with col_one_R:
        ratio_one = v_oneway_res['ratio']
        status_one = "PASS" if ratio_one <= 1.0 else "FAIL"
        badge_one = "badge-pass" if status_one == "PASS" else "badge-fail"
        
        st.markdown(f"""
        <div style="text-align:center; background:#f4f4f4; border-radius:8px; padding:20px; height:100%;">
            <h4>Shear Ratio</h4>
            <div style="font-size:2rem; font-weight:bold; margin:10px 0;">{ratio_one:.2f}</div>
            <span class="{badge_one}">{status_one}</span>
        </div>
        """, unsafe_allow_html=True)


    # ==========================================
    # 3. DEFLECTION (MIN THICKNESS)
    # ==========================================
    st.markdown('<div class="topic-header"><span>3. Deflection Control (Minimum Thickness)</span></div>', unsafe_allow_html=True)
    
    col_def1, col_def2 = st.columns([2, 1])
    
    with col_def1:
        st.markdown("**Method:** ACI 318 Table 8.3.1.1 - Minimum thickness for slabs without interior beams.")
        
        # Calculation Logic Display
        max_span = max(Lx, Ly)
        denom = 33.0 # Basic assumption for Interior Panel w/o Drop
        
        st.markdown(f"""
        * **Longest Span ($L_n$):** {max_span:.2f} m
        * **Criteria:** $L_n / {denom:.0f}$ (Interior Panel)
        * **Calculation:** $({max_span:.2f} \\times 100) / {denom:.0f}$
        """)
        
        h_min = (max_span * 100) / denom
        st.markdown(f"👉 **Required Minimum Thickness ($h_{{min}}$): {h_min:.2f} cm**")

    with col_def2:
        h_actual = mat_props['h_slab']
        status_def = "PASS" if h_actual >= h_min else "CHECK"
        bg_def = "#e8f5e9" if status_def == "PASS" else "#fff3e0"
        
        st.markdown(f"""
        <div style="background-color:{bg_def}; padding:15px; border-radius:8px; border:1px solid #ccc;">
            <strong>Actual Thickness</strong>
            <div style="font-size:1.8rem; font-weight:bold; color:#333;">{h_actual:.0f} cm</div>
            <div style="margin-top:5px; font-size:0.9rem;">vs Min: {h_min:.1f} cm</div>
            <hr style="margin:5px 0;">
            <strong style="color:{'green' if status_def=='PASS' else 'orange'};">{status_def}</strong>
        </div>
        """, unsafe_allow_html=True)


    # ==========================================
    # 4. FACTORED LOAD
    # ==========================================
    st.markdown('<div class="topic-header"><span>4. Factored Load Analysis (ULS)</span></div>', unsafe_allow_html=True)
    
    # 1. Inputs
    sdl = loads['SDL']
    ll = loads['LL']
    h_m = mat_props['h_slab'] / 100.0
    w_concrete = 2400 # kg/m3
    
    # 2. Calculation Steps
    st.markdown("calculation of Uniformly Distributed Load ($w_u$):")
    
    df_load = pd.DataFrame([
        {"Item": "Slab Self-Weight", "Calc": f"{h_m:.2f} m × 2400 kg/m³", "Value": h_m*w_concrete},
        {"Item": "Superimposed Dead Load (SDL)", "Calc": "Input", "Value": sdl},
        {"Item": "Total Dead Load (D)", "Calc": "Sum", "Value": h_m*w_concrete + sdl},
        {"Item": "Live Load (L)", "Calc": "Input", "Value": ll},
    ])
    
    st.table(df_load.style.format({"Value": "{:,.1f}"}))
    
    # 3. Final Formula
    wu = loads['w_u']
    st.markdown('<div class="sub-box">', unsafe_allow_html=True)
    st.markdown("**Load Combination (ACI 318):**")
    st.latex(r"w_u = 1.2 D + 1.6 L")
    st.latex(f"w_u = 1.2({(h_m*w_concrete + sdl):.0f}) + 1.6({ll:.0f})")
    st.markdown(f"### 👉 Total Factored Load ($w_u$) = <span style='color:#d32f2f'>{wu:,.0f} kg/m²</span>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
