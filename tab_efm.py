# tab_efm.py
import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from calculations import calculate_stiffness

def render(c1_w, c2_w, L1, L2, lc, h_slab, fc, mat_props, w_u):
    st.header("3. Equivalent Frame Method & Detailed Design")
    st.markdown("---")

    # ดึงค่า Material
    fy = mat_props['fy']
    cover = mat_props['cover']
    d_bar = mat_props['d_bar']
    
    # -----------------------------------------------------------
    # PART 1: STIFFNESS CALCULATIONS (Step-by-Step)
    # -----------------------------------------------------------
    st.subheader("1. Stiffness Parameters ($K$ & Distribution Factors)")
    
    Ks, Kc_total, Kt, Kec = calculate_stiffness(c1_w, c2_w, L1, L2, lc, h_slab, fc)
    
    # คำนวณ Distribution Factors (DF)
    sum_K = Ks + Kec
    df_slab = Ks / sum_K if sum_K > 0 else 0
    df_col = Kec / sum_K if sum_K > 0 else 0

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Stiffness Values:**")
        st.latex(r"K_s (Slab) = " + f"{Ks:,.0f}" + r" \text{ kg-cm}")
        st.latex(r"K_{ec} (Equiv Col) = " + f"{Kec:,.0f}" + r" \text{ kg-cm}")
        st.caption(f"(From Kc={Kc_total:,.0f}, Kt={Kt:,.0f})")
    
    with col2:
        st.markdown("**Distribution Factors (DF):**")
        st.latex(r"DF_{slab} = \frac{K_s}{K_s + K_{ec}} = \frac{" + f"{Ks:,.0f}" + r"}{" + f"{Ks:,.0f} + {Kec:,.0f}" + r"} = \mathbf{" + f"{df_slab:.3f}" + r"}")
        st.latex(r"DF_{col} = \frac{K_{ec}}{K_s + K_{ec}} = \mathbf{" + f"{df_col:.3f}" + r"}")

    st.markdown("---")

    # -----------------------------------------------------------
    # PART 2: MOMENT ANALYSIS (Substitution)
    # -----------------------------------------------------------
    st.subheader("2. Structural Analysis (Total Static Moment)")
    
    # Calculate ln (Clear Span)
    ln = L1 - (c1_w / 100.0)
    
    st.write("การหาโมเมนต์สถิตรวม ($M_o$) ของแผงพื้น:")
    st.latex(r"M_o = \frac{w_u \ell_n^2 L_2}{8}")
    
    # Substitution string
    sub_str = r"M_o = \frac{" + f"{w_u:,.0f}" + r" \times (" + f"{ln:.2f}" + r")^2 \times " + f"{L2:.2f}" + r"}{8}"
    Mo = (w_u * (ln**2) * L2) / 8.0 # kg-m
    
    st.latex(sub_str + r" = \mathbf{" + f"{Mo:,.0f}" + r"} \text{ kg-m}")
    
    st.info(f"💡 โมเมนต์ $M_o$ นี้จะถูกกระจายเข้า Column Strip และ Middle Strip ตามสัมประสิทธิ์")

    # Define Coefficients (Simplified for Interior Panel)
    # [Loc, %Mo, Width(m)]
    strips = {
        "Col Strip (-)": [0.65 * 0.75, L2/2.0], # 65% Neg * 75% to CS
        "Col Strip (+)": [0.35 * 0.60, L2/2.0], # 35% Pos * 60% to CS
        "Mid Strip (-)": [0.65 * 0.25, L2/2.0], # 65% Neg * 25% to MS
        "Mid Strip (+)": [0.35 * 0.40, L2/2.0], # 35% Pos * 40% to MS
    }

    # -----------------------------------------------------------
    # PART 3: REINFORCEMENT DESIGN (The Core Request)
    # -----------------------------------------------------------
    st.subheader("3. Reinforcement Calculation (รายการคำนวณเหล็กเสริม)")
    
    # User Selects Strip to Design Detail
    design_loc = st.selectbox("เลือกตำแหน่งที่จะแสดงรายการคำนวณละเอียด:", list(strips.keys()))
    
    coef, b_width = strips[design_loc] # b_width is strip width in meters
    Mu = Mo * coef
    b_cm = b_width * 100.0 # cm
    
    # 3.1 Calculate d
    d_eff = h_slab - cover - (d_bar/20.0) # approx center
    
    st.markdown(f"#### 📍 Design for: {design_loc}")
    st.markdown("**Step 3.1: Determine Design Moment ($M_u$)**")
    st.latex(f"M_u = {coef:.3f} \\times M_o = {coef:.3f} \\times {Mo:,.0f} = \\mathbf{{{Mu:,.0f}}} \\text{{ kg-m}}")

    st.markdown("**Step 3.2: Check Effective Depth ($d$)**")
    st.latex(r"d = h - cover - \frac{d_{bar}}{2}")
    st.latex(f"d = {h_slab} - {cover} - {d_bar/20.0} = \\mathbf{{{d_eff:.2f}}} \\text{{ cm}}")

    # 3.3 Calculate Rn
    st.markdown("**Step 3.3: Calculate Strength Parameter ($R_n$)**")
    # Rn = Mu / (phi * b * d^2)
    # Unit conversion: Mu (kg-m) -> kg-cm (*100)
    phi = 0.90 # Flexure
    Mu_kgcm = Mu * 100.0
    Rn = Mu_kgcm / (phi * b_cm * (d_eff**2))
    
    st.latex(r"R_n = \frac{M_u}{\phi b d^2}")
    st.latex(rf"R_n = \frac{{{Mu:,.0f} \times 100}}{{0.9 \times {b_cm:.0f} \times {d_eff:.2f}^2}} = \mathbf{{{Rn:.2f}}} \text{{ ksc}}")

    # 3.4 Calculate Rho
    st.markdown("**Step 3.4: Calculate Required Reinforcement Ratio ($\\rho_{req}$)**")
    
    # Check if Rn is too high
    rho_min = 0.0018 # Temp & Shrinkage
    
    # Formula terms
    term1 = (0.85 * fc) / fy
    term2 = 2 * Rn / (0.85 * fc)
    
    if term2 >= 1.0:
        st.error("❌ Section too small! (Concrete Failure). Increase thickness.")
        rho_req = 999
    else:
        rho_calc = term1 * (1 - np.sqrt(1 - term2))
        rho_req = max(rho_calc, rho_min)

        st.latex(r"\rho = \frac{0.85f'_c}{f_y} \left[ 1 - \sqrt{1 - \frac{2R_n}{0.85f'_c}} \right]")
        
        # Substitution display
        st.write("แทนค่า:")
        st.latex(rf"\rho = \frac{{0.85({fc})}}{{{fy}}} \left[ 1 - \sqrt{{1 - \frac{{2({Rn:.2f})}}{{0.85({fc})}}}} \right]")
        st.latex(rf"\rho_{{calc}} = {rho_calc:.5f}")
        
        if rho_calc < rho_min:
            st.warning(f"⚠️ $\\rho_{{calc}}$ ({rho_calc:.5f}) < $\\rho_{{min}}$ ({rho_min})... Use $\\rho_{{min}}$")
        
        st.latex(rf"\therefore \text{{Use }} \rho_{{req}} = \mathbf{{{rho_req:.5f}}}")

    # 3.5 Calculate As
    st.markdown("**Step 3.5: Total Steel Area ($A_s$)**")
    As_req = rho_req * b_cm * d_eff
    
    st.latex(r"A_s = \rho b d")
    st.latex(rf"A_s = {rho_req:.5f} \times {b_cm:.0f} \times {d_eff:.2f} = \mathbf{{{As_req:.2f}}} \text{{ cm}}^2")
    
    st.write(f"(สำหรับความกว้างแถบ {b_width:.2f} เมตร)")

    # -----------------------------------------------------------
    # PART 4: REBAR SELECTION (Engineering Judgment)
    # -----------------------------------------------------------
    st.markdown("---")
    st.subheader("4. Rebar Selection (เลือกเหล็กเสริม)")
    
    c_sel1, c_sel2 = st.columns(2)
    with c_sel1:
        # DB Area
        db_area = 3.14159 * (d_bar/20.0)**2
        num_bars = As_req / db_area
        st.write(f"- Bar Diameter: **DB{d_bar}** (Area = {db_area:.2f} cm²)")
        st.write(f"- Number of bars needed: {As_req:.2f} / {db_area:.2f} = **{num_bars:.2f}** bars")
        
        req_num = int(np.ceil(num_bars))
        st.success(f"✅ **Require: {req_num} - DB{d_bar}** (Total width {b_width:.2f} m)")

    with c_sel2:
        # Spacing Calculation
        st.write("**Or specify by Spacing (@):**")
        spacing_calc = (b_cm / num_bars) if num_bars > 0 else 0
        st.write(f"Calculated Spacing = {spacing_calc:.1f} cm")
        
        # Practical Spacing Selection
        use_spacing = st.number_input("Select Spacing (cm)", value=min(20, int(spacing_calc)), step=5)
        
        # Check actual As provided
        num_bars_actual = b_cm / use_spacing
        As_prov = num_bars_actual * db_area
        
        if As_prov >= As_req:
             st.markdown(f"<div style='color:green; font-weight:bold; border:1px solid green; padding:10px;'>✅ OK<br>Use DB{d_bar} @ {use_spacing/100:.2f} m<br>(As_prov = {As_prov:.2f} cm²)</div>", unsafe_allow_html=True)
        else:
             st.markdown(f"<div style='color:red; font-weight:bold; border:1px solid red; padding:10px;'>❌ NOT ENOUGH<br>As_prov = {As_prov:.2f} cm² < As_req</div>", unsafe_allow_html=True)

    # -----------------------------------------------------------
    # SUMMARY TABLE
    # -----------------------------------------------------------
    st.markdown("---")
    with st.expander("📊 View Summary Table (All Strips)"):
        data = []
        for loc, params in strips.items():
            coef_val, bw = params
            mu_val = Mo * coef_val
            rn_val = (mu_val*100)/(0.9 * (bw*100) * d_eff**2)
            
            # Simple Rho Check
            term2_loop = 2*rn_val/(0.85*fc)
            if term2_loop < 1:
                rho_loop = (0.85*fc/fy)*(1 - np.sqrt(1 - term2_loop))
                rho_loop = max(rho_loop, 0.0018)
            else:
                rho_loop = 0
            
            as_loop = rho_loop * (bw*100) * d_eff
            num_db = as_loop / db_area
            
            data.append({
                "Location": loc,
                "Width (m)": bw,
                "Moment (kg-m)": f"{mu_val:,.0f}",
                "As Req (cm2)": f"{as_loop:.2f}",
                "No. Bars": f"{np.ceil(num_db):.0f}"
            })
            
        st.table(pd.DataFrame(data))
