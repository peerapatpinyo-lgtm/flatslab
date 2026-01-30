# tab_ddm.py
import streamlit as st
import pandas as pd
import numpy as np

# Try importing the plotting module
try:
    import ddm_plots 
    HAS_PLOTS = True
except ImportError:
    HAS_PLOTS = False

# ========================================================
# 1. CALCULATION ENGINE
# ========================================================
def calc_rebar_detailed(M_u, b_width, d_bar, s_bar, h_slab, cover, fc, fy, is_main_dir):
    """
    Perform detailed reinforced concrete design checks.
    """
    b_cm = b_width * 100
    h_cm = h_slab
    
    # 1. Effective Depth (d)
    # Layer 1 (Outer/Main): d = h - cover - db/2
    # Layer 2 (Inner/Minor): d = h - cover - db_outer - db/2 (approx -1.2cm extra)
    d_offset = 0 if is_main_dir else (d_bar/10.0)
    d_eff = h_cm - cover - (d_bar/20.0) - d_offset
    
    if M_u < 100: 
        return {
            "As_req": 0, "As_prov": 0, "PhiMn": 0, "DC": 0, 
            "Status": True, "Note": "Negligible Moment", "d_eff": d_eff, "rho": 0
        }

    # 2. Required Steel (Flexure)
    Rn = (M_u * 100) / (0.9 * b_cm * d_eff**2)
    term = 1 - (2 * Rn) / (0.85 * fc)
    
    if term < 0:
        rho_req = 999 # Section too small
    else:
        rho_req = (0.85 * fc / fy) * (1 - np.sqrt(term))
        
    As_flex = rho_req * b_cm * d_eff
    
    # 3. Minimum Steel (Temp & Shrinkage)
    As_min = 0.0018 * b_cm * h_cm
    As_req_final = max(As_flex, As_min) if rho_req != 999 else 999
    
    # 4. Provided Steel
    Ab = np.pi * (d_bar/10)**2 / 4
    As_prov = (b_cm / s_bar) * Ab
    
    # 5. Capacity Check (Phi Mn)
    if rho_req == 999:
        PhiMn = 0
        dc_ratio = 999
    else:
        a = (As_prov * fy) / (0.85 * fc * b_cm)
        PhiMn = 0.9 * As_prov * fy * (d_eff - a/2) / 100
        dc_ratio = M_u / PhiMn if PhiMn > 0 else 999

    # 6. Spacing Check (ACI: 2h or 45cm)
    s_max = min(2 * h_cm, 45)
    
    # 7. Final Status
    checks = []
    if dc_ratio > 1.0: checks.append("Strength")
    if As_prov < As_min: checks.append("Min Steel")
    if s_bar > s_max: checks.append(f"Spacing > {s_max}cm")
    
    is_pass = len(checks) == 0
    note_str = ", ".join(checks) if checks else "OK"
    
    return {
        "As_req": As_req_final,
        "As_prov": As_prov,
        "PhiMn": PhiMn,
        "DC": dc_ratio,
        "Status": is_pass,
        "Note": note_str,
        "d_eff": d_eff,
        "rho": rho_req,
        "As_min": As_min
    }

# ========================================================
# 2. UI COMPONENTS
# ========================================================
def render_zone_selector(label, col, M_val, axis_id, key_suffix):
    """Render a unified selection block for one zone"""
    with col:
        st.markdown(f"**{label}**")
        st.caption(f"Moment: {M_val:,.0f} kg-m")
        c1, c2 = st.columns([1, 1.2])
        d_sel = c1.selectbox("DB", [10, 12, 16, 20, 25, 28], index=1, key=f"d_{axis_id}_{key_suffix}", label_visibility="collapsed")
        s_sel = c2.slider("Spacing", 5.0, 35.0, 20.0, 2.5, key=f"s_{axis_id}_{key_suffix}", label_visibility="collapsed")
        st.write(f"👉 Use DB{d_sel}@{s_sel:.0f}cm")
        return d_sel, s_sel

def render_interactive_direction(data, h_slab, cover, fc, fy, axis_id, w_u, is_main_dir):
    L_span = data['L_span']
    L_width = data['L_width']
    c_para = data['c_para']
    Mo = data['Mo']
    m_vals = data['M_vals']
    
    # Geometry
    w_cs = min(L_span, L_width) / 2.0
    w_ms = L_width - w_cs
    
    # ----------------------------------------------------
    # PART A: ANALYSIS & MOMENT DIAGRAM
    # ----------------------------------------------------
    st.markdown(f"### 1️⃣ Analysis Results ({axis_id}-Direction)")
    
    # Plot Moment Diagram immediately to visualize the forces
    if HAS_PLOTS:
         
        st.pyplot(ddm_plots.plot_ddm_moment(L_span, c_para/100, m_vals))
    
    with st.expander("📊 View Moment Calculation Details", expanded=False):
        c1, c2, c3 = st.columns(3)
        c1.metric("Span Length", f"{L_span:.2f} m")
        c2.metric("Total Width", f"{L_width:.2f} m")
        c3.metric("Static Moment (Mo)", f"{Mo:,.0f} kg-m")
        
        st.write("**Moment Distribution Table:**")
        dist_data = [
            ["Negative (-)", f"{m_vals['M_cs_neg']:,.0f}", f"{m_vals['M_ms_neg']:,.0f}"],
            ["Positive (+)", f"{m_vals['M_cs_pos']:,.0f}", f"{m_vals['M_ms_pos']:,.0f}"]
        ]
        st.table(pd.DataFrame(dist_data, columns=["Zone", f"Column Strip ({w_cs:.2f}m)", f"Middle Strip ({w_ms:.2f}m)"]))

    # ----------------------------------------------------
    # PART B: REINFORCEMENT DESIGN
    # ----------------------------------------------------
    st.markdown("---")
    st.markdown(f"### 2️⃣ Reinforcement Design")
    
    # Create Layout: Left = Column Strip (Red), Right = Middle Strip (Blue/Orange)
    c_cs, c_gap, c_ms = st.columns([1, 0.1, 1])
    
    # --- COLUMN STRIP ---
    with c_cs:
        st.error(f"🟥 **COLUMN STRIP** (Width = {w_cs:.2f} m)")
        # CS Top
        d_cst, s_cst = render_zone_selector("Top (Support -)", st, m_vals['M_cs_neg'], axis_id, "cst")
        st.divider()
        # CS Bot
        d_csb, s_csb = render_zone_selector("Bot (Midspan +)", st, m_vals['M_cs_pos'], axis_id, "csb")

    # --- MIDDLE STRIP ---
    with c_ms:
        st.info(f"🟦 **MIDDLE STRIP** (Width = {w_ms:.2f} m)")
        # MS Top
        d_mst, s_mst = render_zone_selector("Top (Support -)", st, m_vals['M_ms_neg'], axis_id, "mst")
        st.divider()
        # MS Bot
        d_msb, s_msb = render_zone_selector("Bot (Midspan +)", st, m_vals['M_ms_pos'], axis_id, "msb")

    # --- CALCULATION LOOP ---
    inputs = [
        ("CS_Top", m_vals['M_cs_neg'], w_cs, d_cst, s_cst),
        ("CS_Bot", m_vals['M_cs_pos'], w_cs, d_csb, s_csb),
        ("MS_Top", m_vals['M_ms_neg'], w_ms, d_mst, s_mst),
        ("MS_Bot", m_vals['M_ms_pos'], w_ms, d_msb, s_msb),
    ]
    
    results = []
    rebar_map = {}
    
    for label, Mu, b, db, sb in inputs:
        res = calc_rebar_detailed(Mu, b, db, sb, h_slab, cover, fc, fy, is_main_dir)
        
        status_icon = "✅ OK" if res['Status'] else "❌ FAIL"
        
        results.append({
            "Location": label,
            "Mu": f"{Mu:,.0f}",
            "Rebar": f"DB{db}@{sb:.0f}",
            "As Req": f"{res['As_req']:.2f}",
            "As Prov": f"{res['As_prov']:.2f}",
            "D/C Ratio": res['DC'], # Store raw for styling
            "Status": status_icon,
            "Note": res['Note']
        })
        rebar_map[label] = f"DB{db}@{sb:.0f}"

    # --- SUMMARY TABLE ---
    st.write("#### 📋 Design Summary Check")
    df = pd.DataFrame(results)
    
    # Apply styling using Pandas Styler
    def color_status(val):
        color = 'red' if 'FAIL' in val else 'green'
        return f'color: {color}; font-weight: bold'
    
    def highlight_dc(val):
        return 'background-color: #ffcccc' if val > 1.0 else ''

    st.dataframe(
        df.style.applymap(color_status, subset=['Status'])
                .applymap(highlight_dc, subset=['D/C Ratio'])
                .format({"D/C Ratio": "{:.2f}"}),
        use_container_width=True
    )

    # ----------------------------------------------------
    # PART C: DETAILING & SAMPLE CALCULATION
    # ----------------------------------------------------
    st.markdown("---")
    c_det, c_calc = st.columns([1.5, 1])
    
    with c_det:
        st.markdown(f"### 3️⃣ Detailing Drawings")
        if HAS_PLOTS:
            tab1, tab2 = st.tabs(["📐 Section View", "🏗️ Plan View"])
            with tab1:
                
                st.pyplot(ddm_plots.plot_rebar_detailing(L_span, h_slab, c_para, rebar_map, axis_id))
            with tab2:
                
                st.pyplot(ddm_plots.plot_rebar_plan_view(L_span, L_width, c_para, rebar_map, axis_id))
        else:
            st.warning("Plotting module not found.")

    with c_calc:
        st.markdown("### 📝 Sample Calc (CS-Top)")
        # Show calculation for the first item (CS Top)
        ex_res = calc_rebar_detailed(inputs[0][1], inputs[0][2], inputs[0][3], inputs[0][4], h_slab, cover, fc, fy, is_main_dir)
        
        with st.container():
            st.markdown(f"""
            <div style="background-color:#f8f9fa; padding:15px; border-radius:5px; font-size:0.9em;">
            <b>Input:</b> M={inputs[0][1]:,.0f}, b={inputs[0][2]*100:.0f}, d={ex_res['d_eff']:.2f}<br>
            <b>1. Flexure:</b><br>
            $R_n = { (inputs[0][1]*100)/(0.9 * inputs[0][2]*100 * ex_res['d_eff']**2) :.2f}$ ksc<br>
            $\Rightarrow A_{{s,flex}} = {ex_res['As_req']:.2f}$ cm²<br>
            <b>2. Min Steel:</b><br>
            $A_{{s,min}} = 0.0018 b h = {ex_res['As_min']:.2f}$ cm²<br>
            <b>3. Capacity:</b><br>
            $\phi M_n = {ex_res['PhiMn']:,.0f}$ kg-m (Ratio: {ex_res['DC']:.2f})
            </div>
            """, unsafe_allow_html=True)


# ========================================================
# 3. MAIN ENTRY POINT
# ========================================================
def render_dual(data_x, data_y, mat_props, w_u):
    st.markdown("## 🏗️ Interactive Direct Design Method")
    st.info("💡 **Workflow:** โปรแกรมจะคำนวณโมเมนต์ให้อัตโนมัติ ท่านสามารถปรับขนาดและระยะห่างเหล็กเสริมได้ตามความเหมาะสม")
    
    tab_x, tab_y = st.tabs([f"➡️ X-Direction ({data_x['L_span']}m)", f"⬆️ Y-Direction ({data_y['L_span']}m)"])
    
    with tab_x:
        render_interactive_direction(data_x, mat_props['h_slab'], mat_props['cover'], mat_props['fc'], mat_props['fy'], "X", w_u, is_main_dir=True)
        
    with tab_y:
        render_interactive_direction(data_y, mat_props['h_slab'], mat_props['cover'], mat_props['fc'], mat_props['fy'], "Y", w_u, is_main_dir=False)
