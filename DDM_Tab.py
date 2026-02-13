import streamlit as st
import pandas as pd
import numpy as np

# IMPORT CUSTOM MODULES
import DDM_Logic as logic
import DDM_Schematics as schem

# Optional import for plotting if you have ddm_plots.py
try:
    import ddm_plots
    HAS_PLOTS = True
except ImportError:
    HAS_PLOTS = False

# ========================================================
# 3. DETAILED CALCULATION RENDERER (ULTRA DETAILED)
# ========================================================
def show_detailed_calculation(zone_name, res, inputs, coeff_pct, Mo_val):
    # Unpack Inputs
    Mu, b, h, cover, fc, fy, db, s, phi_bend = inputs
    
    # Unit Conversions for display
    b_cm = b * 100
    Mu_kgcm = Mu * 100
    
    st.markdown(f"""
    <div style="background-color:#f0f9ff; padding:15px; border-radius:10px; border-left: 5px solid #0369a1;">
        <h4 style="margin:0; color:#0369a1;">🔍 Detailed Analysis: {zone_name}</h4>
        <p style="margin:5px 0 0 0; color:#475569; font-size:0.9em;">
            Comprehensive Step-by-Step Derivation & Verification
        </p>
    </div>
    """, unsafe_allow_html=True)
    

    c1, c2, c3 = st.tabs(["1️⃣ Load & Geometry", "2️⃣ Flexural Design", "3️⃣ Verification"])
    
    # --- TAB 1: MOMENT & GEOMETRY ---
    with c1:
        st.markdown("### 1.1 Geometry & Material Properties")
        st.write("Starting with section dimensions and material properties:")
        st.markdown(f"""
        - **Slab Thickness ($h$):** {h} cm
        - **Concrete Cover ($C_c$):** {cover} cm
        - **Bar Diameter ($d_b$):** {db} mm ({db/10:.1f} cm)
        - **Strip Width ($b$):** {b:.2f} m ({b_cm:.0f} cm)
        - **Material:** $f_c'={fc}$ ksc, $f_y={fy}$ ksc
        """)

        st.markdown("---")
        st.markdown("### 1.2 Effective Depth Calculation ($d$)")
        st.write("The effective depth is the distance from the extreme compression fiber to the centroid of the longitudinal tension reinforcement.")
        
        # Explicit check for layer offset
        layer_offset = 0.0
        standard_d = h - cover - (db/20.0)
        if res['d'] < (standard_d - 0.01):
             layer_offset = db/10.0
             st.info(f"ℹ️ **Note:** This is an **Inner Layer** reinforcement. We subtract the outer layer bar diameter ({layer_offset} cm).")

        st.write("**Formula:**")
        st.latex(r"d = h - C_c - \frac{d_b}{2} - \text{Layer Offset}")
        
        st.write("**Substitution:**")
        st.latex(f"d = {h} - {cover} - \\frac{{{db/10:.1f}}}{{2}} - {layer_offset}")
        
        st.write("**Result:**")
        st.latex(f"d = \\mathbf{{{res['d']:.2f}}} \\; \\text{{cm}}")
        
        st.markdown("---")
        st.markdown("### 1.3 Design Moment Calculation ($M_u$)")
        st.write("The design moment is derived from the Total Static Moment ($M_o$) distributed by the Direct Design Method (DDM) coefficients.")
        
        st.write("**Given:**")
        st.latex(f"M_o = \\mathbf{{{Mo_val:,.0f}}} \\; \\text{{kg-m}}")
        st.latex(f"\\text{{DDM Coefficient}} = {coeff_pct/100:.3f} \\; ({coeff_pct:.1f}\%)")
        
        st.write("**Calculation:**")
        st.latex(f"M_u = \\text{{Coeff}} \\times M_o")
        st.latex(f"M_u = {coeff_pct/100:.3f} \\times {Mo_val:,.0f} = \\mathbf{{{Mu:,.0f}}} \\; \\text{{kg-m}}")
        st.latex(f"M_u (converted) = {Mu:,.0f} \\times 100 = \\mathbf{{{Mu_kgcm:,.0f}}} \\; \\text{{kg-cm}}")

    # --- TAB 2: REINFORCEMENT ---
    with c2:
        st.markdown("### 2.1 Strength Reduction Factor")
        st.write(f"Using **$\\phi = {phi_bend}$** for tension-controlled sections (Flexure) as per ACI 318.")

        st.markdown("---")
        st.markdown("### 2.2 Nominal Strength Requirement ($R_n$)")
        st.write("First, we determine the required nominal strength coefficient $R_n$ to design the reinforcement ratio.")
        
        st.write("**Formula:**")
        st.latex(r"R_n = \frac{M_u}{\phi b d^2}")
        
        st.write("**Substitution:**")
        st.latex(f"R_n = \\frac{{{Mu_kgcm:,.0f}}}{{{phi_bend} \\cdot {b_cm:.0f} \\cdot ({res['d']:.2f})^2}}")
        
        denominator = phi_bend * b_cm * (res['d']**2)
        st.latex(f"R_n = \\frac{{{Mu_kgcm:,.0f}}}{{{denominator:,.0f}}}")
        
        st.write("**Result:**")
        st.latex(f"R_n = \\mathbf{{{res['Rn']:.3f}}} \\; \\text{{ksc}}")

        st.markdown("---")
        st.markdown("### 2.3 Required Reinforcement Ratio ($\\rho_{req}$)")
        
        # Explain Beta 1
        st.write(f"**Step A: Determine $\\beta_1$ Factor**")
        st.write(f"For concrete strength $f_c' = {fc}$ ksc:")
        if fc <= 280:
            st.latex(r"\beta_1 = 0.85 \quad (\because f_c' \le 280 \text{ ksc})")
        else:
            st.latex(r"\beta_1 = 0.85 - 0.05\frac{f_c' - 280}{70} \ge 0.65")
            st.latex(f"\\beta_1 = {res['beta1']:.3f}")

        st.write("**Step B: Calculate $\\rho_{req}$**")
        
        if res['rho_req'] == 0:
            st.info("Since $M_u$ is negligible, assume $\\rho_{req} \\approx 0$. Design will be governed by Minimum Steel ($A_{s,min}$).")
        elif res['rho_req'] == 999:
            st.error("❌ **CRITICAL FAILURE:** The section is too small. $R_n$ exceeds the maximum capacity allowed by the concrete. Increase slab thickness or concrete strength.")
        else:
            st.write("**Formula:**")
            st.latex(r"\rho_{req} = \frac{0.85 f_c'}{f_y} \left( 1 - \sqrt{1 - \frac{2 R_n}{0.85 f_c'}} \right)")
            
            term_inside_sqrt = 1 - (2 * res['Rn']) / (0.85 * fc)
            
            st.write("**Substitution:**")
            st.latex(f"\\rho_{{req}} = \\frac{{0.85({fc})}}{{{fy}}} \\left( 1 - \\sqrt{{1 - \\frac{{2({res['Rn']:.3f})}}{{0.85({fc})}}}} \\right)")
            st.latex(f"\\text{{Inside Sqrt}} = {term_inside_sqrt:.4f}")
            
            st.write("**Result:**")
            st.latex(f"\\rho_{{req}} = \\mathbf{{{res['rho_calc']:.5f}}}")

        st.markdown("---")
        st.markdown("### 2.4 Required Steel Area ($A_s$)")
        
        st.write("**1) Required Flexural Steel ($A_{s,flex}$):**")
        st.latex(f"A_{{s,flex}} = \\rho_{{req}} b d = {res['rho_calc']:.5f} \\cdot {b_cm:.0f} \\cdot {res['d']:.2f}")
        st.latex(f"A_{{s,flex}} = \\mathbf{{{res['As_flex']:.2f}}} \\; \\text{{cm}}^2")
        
        st.write("**2) Minimum Steel for Shrinkage & Temperature ($A_{s,min}$):**")
        st.latex(r"A_{s,min} = 0.0018 \cdot b \cdot h")
        st.latex(f"A_{{s,min}} = 0.0018 \\cdot {b_cm:.0f} \\cdot {h} = \\mathbf{{{res['As_min']:.2f}}} \\; \\text{{cm}}^2")
        
        st.write("**3) Final Design Area ($A_{s,req}$):**")
        condition = "As_flex > As_min" if res['As_flex'] > res['As_min'] else "As_min > As_flex"
        st.info(f"👉 **Control Case:** {condition}")
        st.latex(f"A_{{s,req}} = \\max(A_{{s,flex}}, A_{{s,min}}) = \\mathbf{{{res['As_req']:.2f}}} \\; \\text{{cm}}^2")

    # --- TAB 3: VERIFICATION ---
    with c3:
        st.markdown("### 3.1 Provided Reinforcement")
        st.write(f"**Selection:** DB{db} spaced at {s:.0f} cm")
        
        area_one_bar = np.pi * (db/10.0)**2 / 4.0
        
        st.write("**Area of one bar ($A_{bar}$):**")
        st.latex(f"A_{{bar}} = {area_one_bar:.2f} \\; \\text{{cm}}^2")
        
        st.write("**Total Provided Area ($A_{s,prov}$):**")
        st.latex(r"A_{s,prov} = \frac{b}{s} \times A_{bar}")
        st.latex(f"A_{{s,prov}} = \\frac{{{b_cm:.0f}}}{{{s:.0f}}} \\times {area_one_bar:.2f} = \\mathbf{{{res['As_prov']:.2f}}} \\; \\text{{cm}}^2")
        
        if res['As_prov'] >= res['As_req']:
            st.success(f"✅ **PASS:** Provided ({res['As_prov']:.2f}) $\ge$ Required ({res['As_req']:.2f})")
        else:
            diff = res['As_req'] - res['As_prov']
            st.error(f"❌ **FAIL:** Deficient by {diff:.2f} cm².")

        st.markdown("---")
        st.markdown("### 3.2 Moment Capacity Verification ($\\phi M_n$)")
        
        st.write("**A) Equivalent Stress Block Depth ($a$):**")
        st.latex(r"a = \frac{A_{s,prov} f_y}{0.85 f_c' b}")
        st.latex(f"a = \\mathbf{{{res['a']:.2f}}} \\; \\text{{cm}}")
        
        st.write("**B) Nominal Moment Capacity ($M_n$):**")
        st.latex(r"M_n = A_{s,prov} f_y (d - a/2)")
        
        Mn_val_kgcm = res['As_prov'] * fy * (res['d'] - res['a']/2)
        st.latex(f"M_n = {Mn_val_kgcm:,.0f} \\; \\text{{kg-cm}}")
        
        st.write("**C) Design Moment Capacity ($\\phi M_n$):**")
        st.latex(f"\\phi M_n = {res['PhiMn']*100:,.0f} \\; \\text{{kg-cm}} = \\mathbf{{{res['PhiMn']:,.0f}}} \\; \\text{{kg-m}}")
        
        st.markdown("---")
        st.markdown("### 3.3 Demand / Capacity Ratio (D/C)")
        
        d_c = res['DC']
        color = "green" if d_c <= 1.0 else "red"
        status_text = "SAFE" if d_c <= 1.0 else "UNSAFE"
        
        st.latex(f"D/C = \\frac{{M_u}}{{\\phi M_n}} = \\frac{{{Mu:,.0f}}}{{{res['PhiMn']:,.0f}}}")
        st.markdown(f"$$ D/C = \\color{{{color}}}{{\\mathbf{{{d_c:.3f}}}}} \\quad (\\text{{{status_text}}}) $$")
    return

# ========================================================
# 4. INTERACTIVE DIRECTION CHECK (TAB CONTENT)
# ========================================================
def render_interactive_direction(data, mat_props, axis_id, w_u, is_main_dir):
    # Unpack Props
    h_slab = float(mat_props['h_slab'])
    cover = float(mat_props['cover'])
    fc = float(mat_props['fc'])
    fy = float(mat_props['fy'])
    phi_bend = mat_props.get('phi', 0.90)        
    phi_shear = mat_props.get('phi_shear', 0.85) 
    cfg = mat_props.get('rebar_cfg', {})
    
    L_span = data['L_span']
    L_width = data.get('L_width', L_span)
    c_para = float(data['c_para'])
    Mo = data['Mo']
    m_vals = data['M_vals']
    span_type_str = data.get('span_type_str', 'Interior')
    
    span_sym, width_sym = ("L_x", "L_y") if axis_id == "X" else ("L_y", "L_x")
    ln_val = L_span - (c_para/100.0)
    w_cs = min(L_span, L_width) / 2.0
    w_ms = L_width - w_cs
    
    # 1. ANALYSIS
    st.markdown(f"### 1️⃣ Analysis: {axis_id}-Direction")
    with st.expander(f"📊 Load & Moment Distribution ({axis_id})", expanded=True):
        c_an1, c_an2 = st.columns([1, 1.5])
        with c_an1:
            st.info(f"**Span Configuration:** {span_type_str}")
            st.markdown(f"""
            - **Span {span_sym}:** {L_span:.2f} m
            - **Width {width_sym}:** {L_width:.2f} m
            - **Clear Span ($l_n$):** {ln_val:.2f} m
            - **Total Load ($w_u$):** {w_u:,.0f} kg/m²
            """)
        with c_an2:
            st.markdown("#### Total Static Moment ($M_o$)")
            st.latex(f"M_o = \\frac{{w_u l_2 l_n^2}}{{8}} = \\frac{{{w_u:,.0f} \\cdot {L_width:.2f} \\cdot {ln_val:.2f}^2}}{{8}}")
            st.latex(f"M_o = \\mathbf{{{Mo:,.0f}}} \\; \\text{{kg-m}}")
            
            M_sc = m_vals.get('M_unbal', 0)
            if M_sc > 0:
                st.warning(f"⚠️ **Unbalanced Moment ($M_{{sc}}$):** {M_sc:,.0f} kg-m")
                coeff_used = M_sc / Mo if Mo > 0 else 0.30
                st.markdown(f"> **Note:** This value is derived from **$M_{{sc}} = {coeff_used:.2f} \\times M_o$**.")
            else:
                 st.success("✅ **Balanced Span:** No significant unbalanced moment transfer.")

    # 2. PUNCHING SHEAR (VERIFIED PHYSICS MODE)
    st.markdown("---")
    st.markdown("### 2️⃣ Punching Shear Check (Verified Calculation)")
    
    # --- A. PREPARE INPUTS ---
    h_slab_val = float(h_slab)
    cover_val = float(cover)
    d_avg = h_slab_val - cover_val - 1.6 
    w_u_val = float(w_u)
    c1 = float(c_para)
    c2 = float(c_para)
    
    # --- B. GEOMETRY & CRITICAL SECTION ---
    st.markdown("#### **Step 1: Geometry & Critical Section Properties**")
    is_edge = "Interior" not in span_type_str
    
    if not is_edge:
        # === INTERIOR COLUMN ===
        st.info("📍 **Type:** Interior Column (Rectangular Section)")
        b1 = c1 + d_avg
        b2 = c2 + d_avg
        bo = 2 * (b1 + b2)
        c_AB = b1 / 2.0
        
        term1 = (d_avg * b1**3) / 6.0
        term2 = (d_avg**3 * b1) / 6.0
        term3 = (d_avg * b2 * b1**2) / 2.0
        J_c = term1 + term2 + term3
        
        gamma_f = 1.0 / (1.0 + (2.0/3.0) * (b1/b2)**0.5)
        gamma_v = 1.0 - gamma_f
        M_unbal = 0.0
        st.latex(f"b_o = 2({c1}+{d_avg:.2f}) + 2({c2}+{d_avg:.2f}) = \\mathbf{{{bo:.2f}}} \\; cm")
        
    else:
        # === EDGE COLUMN ===
        st.info("📍 **Type:** Edge Column (U-Shaped Section)")
        L1 = c1 + (d_avg / 2.0) 
        L2 = c2 + d_avg
        bo = (2 * L1) + L2
        
        st.write(f"**Side legs ($L_1$):** {c1} + {d_avg:.2f}/2 = {L1:.2f} cm")
        st.write(f"**Front face ($L_2$):** {c2} + {d_avg:.2f} = {L2:.2f} cm")
        st.latex(f"b_o = 2({L1:.2f}) + {L2:.2f} = \\mathbf{{{bo:.2f}}} \\; cm")

        area_legs = 2 * L1 * d_avg
        area_front = L2 * d_avg
        total_area_shear = bo * d_avg
        x_bar = (area_legs * (-L1/2.0)) / total_area_shear
        c_AB = abs(x_bar) 
        
        st.write("**Finding Centroid ($c_{AB}$):**")
        st.latex(f"c_{{AB}} = \\frac{{{L1:.2f}^2}}{{{bo:.2f}}} = \\mathbf{{{c_AB:.2f}}} \\; cm \\; (\\text{{Inner Face}})")

        dist_leg = abs((L1/2.0) - c_AB)
        I_leg_local = (d_avg * L1**3) / 12.0
        I_leg_shift = (L1 * d_avg) * (dist_leg**2)
        J_legs = 2.0 * (I_leg_local + I_leg_shift)
        
        I_front_local = (L2 * d_avg**3) / 12.0
        I_front_shift = (L2 * d_avg) * (c_AB**2)
        J_front = I_front_local + I_front_shift
        J_c = J_legs + J_front
        
        st.write("**Calculating $J_c$:**")
        st.latex(f"J_c = {J_legs:,.0f} + {J_front:,.0f} = \\mathbf{{{J_c:,.0f}}} \\; cm^4")
        
        gamma_f = 1.0 / (1.0 + (2.0/3.0) * (L1/L2)**0.5)
        gamma_v = 1.0 - gamma_f
        st.latex(f"\\gamma_v = 1 - \\frac{{1}}{{1 + \\frac{{2}}{{3}}\\sqrt{{{L1:.2f}/{L2:.2f}}}}} = \\mathbf{{{gamma_v:.3f}}}")
        M_unbal = m_vals.get('M_unbal', 0)

    # --- C. LOADS & STRESS ---
    st.markdown("#### **Step 2: Loads & Stress Calculation**")
    area_panel = (L_span * L_width)
    area_col = (c1/100) * (c2/100)
    Vu = w_u_val * (area_panel - area_col)
    
    v1 = Vu / (bo * d_avg)
    if M_unbal > 0:
        M_sc_cm = M_unbal * 100
        v2 = (gamma_v * M_sc_cm * c_AB) / J_c
        sign_text = "+" 
    else:
        v2 = 0
        sign_text = ""
        
    v_total = v1 + v2
    
    col_res1, col_res2 = st.columns(2)
    with col_res1:
        st.write(f"**$V_u$:** {Vu:,.0f} kg")
        st.write(f"**$v_{{load}}$:** {v1:.2f} ksc")
    with col_res2:
        st.write(f"**$M_{{sc}}$:** {M_unbal:,.0f} kg-m")
        st.write(f"**$v_{{moment}}$:** {v2:.2f} ksc")
        
    st.latex(r"v_{max} = \frac{V_u}{b_o d} + \frac{\gamma_v M_{sc} c_{AB}}{J_c}")
    st.latex(f"v_{{max}} = {v1:.2f} {sign_text} {v2:.2f} = \\mathbf{{{v_total:.2f}}} \\; ksc")

    # --- D. CAPACITY & CONCLUSION ---
    st.markdown("#### **Step 3: Verification (ACI 318)**")
    phi_vc = phi_shear * 1.06 * (fc**0.5)
    ratio = v_total / phi_vc
    
    st.write(f"**Capacity ($\\phi v_c$):** {phi_shear} × 1.06 × √{fc} = **{phi_vc:.2f} ksc**")
    
    if v_total <= phi_vc:
        st.success(f"✅ **PASS** (Ratio: {ratio:.2f})")
        st.progress(min(ratio, 1.0))
    else:
        st.error(f"❌ **FAIL** (Ratio: {ratio:.2f})")
        st.progress(min(ratio, 1.0))
        req_d = d_avg * (ratio**0.5)
        st.warning(f"💡 **Fix:** Needs slab thickness approx **{req_d + cover_val + 1.6:.1f} cm**")

    # 3. SERVICEABILITY
    st.markdown("---")
    st.markdown("### 3️⃣ Serviceability (Deflection)")
    def_res = logic.calc_deflection_check(L_span, h_slab, w_u, fc, span_type_str)
    
    with st.container(border=True):
        c_d1, c_d2 = st.columns(2)
        with c_d1:
            st.markdown("**A) Minimum Thickness**")
            if def_res['status_h']:
                st.success(f"✅ Provided {h_slab} cm $\ge$ Min {def_res['h_min']:.2f} cm")
            else:
                st.error(f"❌ Provided {h_slab} cm < Min {def_res['h_min']:.2f} cm")
        with c_d2:
            st.markdown("**B) Estimated Deflection**")
            val, lim = def_res['delta_total'], def_res['limit']
            if val <= lim:
                st.success(f"✅ **{val:.2f} cm** (Limit {lim:.2f} cm)")
            else:
                st.warning(f"⚠️ **{val:.2f} cm** (Exceeds Limit {lim:.2f} cm)")

    # 4. REINFORCEMENT
    st.markdown("---")
    st.markdown("### 4️⃣ Reinforcement Design")
    
    d_cst, s_cst = cfg.get('cs_top_db', 12), cfg.get('cs_top_spa', 20)
    d_csb, s_csb = cfg.get('cs_bot_db', 12), cfg.get('cs_bot_spa', 20)
    d_mst, s_mst = cfg.get('ms_top_db', 12), cfg.get('ms_top_spa', 20)
    d_msb, s_msb = cfg.get('ms_bot_db', 12), cfg.get('ms_bot_spa', 20)
    
    zones = [
        {"Label": "Col Strip - Top (-)", "Mu": m_vals['M_cs_neg'], "b": w_cs, "db": d_cst, "s": s_cst},
        {"Label": "Col Strip - Bot (+)", "Mu": m_vals['M_cs_pos'], "b": w_cs, "db": d_csb, "s": s_csb},
        {"Label": "Mid Strip - Top (-)", "Mu": m_vals['M_ms_neg'], "b": w_ms, "db": d_mst, "s": s_mst},
        {"Label": "Mid Strip - Bot (+)", "Mu": m_vals['M_ms_pos'], "b": w_ms, "db": d_msb, "s": s_msb},
    ]
    
    results = []
    for z in zones:
        res = logic.calc_rebar_logic(
            z['Mu'], z['b'], z['db'], z['s'], 
            h_slab, cover, fc, fy, is_main_dir, phi_bend
        )
        res.update(z)
        results.append(res)
    
    df_res = pd.DataFrame(results)[["Label", "Mu", "As_req", "As_prov", "DC", "Note"]]
    st.dataframe(df_res.style.background_gradient(subset=["DC"], cmap="RdYlGn_r", vmin=0, vmax=1.2), use_container_width=True, hide_index=True)
    
    st.markdown("#### 🔍 Select Zone for Detailed Calculation")
    sel_zone = st.selectbox(f"Show details for ({axis_id}):", [z['Label'] for z in zones], key=f"sel_{axis_id}")
    
    target = next(z for z in results if z['Label'] == sel_zone)
    raw_inputs = (target['Mu'], target['b'], h_slab, cover, fc, fy, target['db'], target['s'], phi_bend)
    pct_val = (target['Mu'] / Mo * 100) if Mo > 0 else 0
    
    show_detailed_calculation(sel_zone, target, raw_inputs, pct_val, Mo)

    if HAS_PLOTS:
        st.markdown("---")
        t1, t2 = st.tabs(["📉 Moment Diagram", "🏗️ Rebar Detailing"])
        rebar_map = {
            "CS_Top": f"DB{d_cst}@{s_cst}", "CS_Bot": f"DB{d_csb}@{s_csb}",
            "MS_Top": f"DB{d_mst}@{s_mst}", "MS_Bot": f"DB{d_msb}@{s_msb}"
        }
        with t1: st.pyplot(ddm_plots.plot_ddm_moment(L_span, c_para/100, m_vals))
        with t2: st.pyplot(ddm_plots.plot_rebar_detailing(L_span, h_slab, c_para, rebar_map, axis_id))

def render_dual(data_x, data_y, mat_props, w_u):
    st.markdown("## 🏗️ RC Slab Design (DDM Analysis)")
    
    with st.expander("⚙️ Span Continuity Settings & Diagrams", expanded=True):
        c1, c2 = st.columns([1, 2])
        with c1:
            type_x = st.radio("Select Span Condition (X-Axis):", ["Interior Span", "End Span - Edge Beam", "End Span - No Beam"], key="sx")
            data_x = logic.update_moments_based_on_config(data_x, type_x)
        with c2:
            st.pyplot(schem.draw_span_schematic(type_x), use_container_width=False)

        st.markdown("---")
        c3, c4 = st.columns([1, 2])
        with c3:
            type_y = st.radio("Select Span Condition (Y-Axis):", ["Interior Span", "End Span - Edge Beam", "End Span - No Beam"], key="sy")
            data_y = logic.update_moments_based_on_config(data_y, type_y)
        with c4:
            st.pyplot(schem.draw_span_schematic(type_y), use_container_width=False)

    tab_x, tab_y = st.tabs(["➡️ X-Direction Check", "⬆️ Y-Direction Check"])
    with tab_x: render_interactive_direction(data_x, mat_props, "X", w_u, True)
    with tab_y: render_interactive_direction(data_y, mat_props, "Y", w_u, False)
แก้มาครบนะ เอาให้ละเอียดแล้วข้อมูลเดิมห้ามหาย
