import streamlit as st
import numpy as np
import pandas as pd

# ตรวจสอบการ import visualization
try:
    from viz_torsion import plot_torsion_member
except ImportError:
    def plot_torsion_member(*args): return None

# ฟังก์ชันช่วยเขียนการแทนค่าสมการ (Helper for Equation Substitution)
def show_sub(label, formula, sub_str, result, unit=""):
    st.markdown(f"**{label}**")
    st.latex(formula)
    st.markdown(f"$$ = {sub_str} $$")
    st.markdown(f"$$ = \\mathbf{{{result}}} \\text{{ {unit}}} $$")
    st.markdown("---")

# --- Main Function ---
def render(c1_w, c2_w, L1, L2, lc, h_slab, fc, mat_props, w_u, col_type, **kwargs):
    """
    EFM Analysis: Stiffness -> Moment Distribution -> Reinforcement Design
    """
    
    st.header("Equivalent Frame Method: Full Design Calculation")
    st.markdown("---")

    # --- 0. Unpack Material Properties ---
    fy = mat_props.get('fy', 4000)
    cover = mat_props.get('cover', 2.5)
    d_bar_mm = mat_props.get('d_bar', 12) # mm
    d_bar_cm = d_bar_mm / 10.0
    
    # คำนวณค่าคงที่เบื้องต้น
    Ec = 15100 * np.sqrt(fc) # ksc
    
    # -------------------------------------------------------
    # PART 1: STIFFNESS PARAMETERS (เหมือนเดิมแต่แสดงละเอียด)
    # -------------------------------------------------------
    st.subheader("1. Stiffness Analysis (วิเคราะห์สติฟเนส)")
    
    # 1.1 Column Stiffness (Kc)
    st.markdown("#### 1.1 Column Stiffness ($K_c$)")
    Ic = (c2_w * c1_w**3) / 12
    Lc_cm = lc * 100
    Kc = (4 * Ec * Ic) / Lc_cm
    Sum_Kc = 2 * Kc # Assume columns above & below
    
    with st.expander("แสดงวิธีทำ Kc", expanded=False):
        st.latex(r"I_c = \frac{c_2 \cdot c_1^3}{12}")
        st.write(f"Substitute: {c2_w:.0f} * {c1_w:.0f}^3 / 12 = {Ic:,.0f} cm^4")
        st.latex(r"K_c = \frac{4 E_c I_c}{L_c}")
        st.write(f"Substitute: 4 * {Ec:,.0f} * {Ic:,.0f} / {Lc_cm:.0f} = {Kc:,.0f} ksc-cm")
        st.write(f"**Sum Kc (Above + Below):** {Sum_Kc:,.0f} ksc-cm")

    # 1.2 Slab Stiffness (Ks)
    st.markdown("#### 1.2 Slab Stiffness ($K_s$)")
    L1_cm = L1 * 100
    L2_cm = L2 * 100
    Is = (L2_cm * h_slab**3) / 12
    Ks = (4 * Ec * Is) / L1_cm
    
    with st.expander("แสดงวิธีทำ Ks", expanded=False):
        st.latex(r"I_s = \frac{L_2 \cdot h^3}{12}")
        st.write(f"Substitute: {L2_cm:.0f} * {h_slab:.0f}^3 / 12 = {Is:,.0f} cm^4")
        st.latex(r"K_s = \frac{4 E_c I_s}{L_1}")
        st.write(f"Substitute: 4 * {Ec:,.0f} * {Is:,.0f} / {L1_cm:.0f} = {Ks:,.0f} ksc-cm")

    # 1.3 Torsional Member Stiffness (Kt)
    st.markdown("#### 1.3 Torsional Member ($K_t$)")
    x = min(c1_w, h_slab)
    y = max(c1_w, h_slab)
    C_val = (1 - 0.63 * (x/y)) * (x**3 * y) / 3
    
    # Check arms
    loc_key = col_type.lower()
    num_arms = 1 if loc_key == "corner" else 2
    
    term_geom = L2_cm * (1 - (c2_w/L2_cm))**3
    if term_geom <= 0: term_geom = 1
    Kt = num_arms * (9 * Ec * C_val) / term_geom

    with st.expander("แสดงวิธีทำ Kt", expanded=False):
        st.write(f"Section x={x:.0f}, y={y:.0f} cm")
        st.latex(r"C = \left(1 - 0.63 \frac{x}{y}\right) \frac{x^3 y}{3}")
        st.write(f"C = {C_val:,.0f} cm^4")
        st.latex(r"K_t = \sum \frac{9 E_c C}{L_2 (1 - c_2/L_2)^3}")
        st.write(f"Kt = {Kt:,.0f} ksc-cm")

    # 1.4 Equivalent Column (Kec)
    st.markdown("#### 1.4 Equivalent Stiffness ($K_{ec}$)")
    if Kt == 0: Kec = 0
    else: Kec = 1 / ((1/Sum_Kc) + (1/Kt))
    
    st.latex(r"\frac{1}{K_{ec}} = \frac{1}{\sum K_c} + \frac{1}{K_t}")
    st.write(f"1/Kec = 1/{Sum_Kc:,.0f} + 1/{Kt:,.0f}")
    st.success(f"**Kec = {Kec:,.0f} ksc-cm**")
    
    # Distribution Factors
    DF_col = Kec / (Ks + Kec)
    st.write(f"**DF (To Column):** {DF_col:.3f} ({(DF_col*100):.1f}%)")

    st.markdown("---")

    # -------------------------------------------------------
    # PART 2: MOMENT ANALYSIS (หาโมเมนต์ออกแบบ)
    # -------------------------------------------------------
    st.subheader("2. Moment Analysis (วิเคราะห์โมเมนต์)")
    
    # 2.1 Static Moment (Mo)
    ln = L1 - (c1_w/100) # Clear span (approx column face)
    Mo = (w_u * L2 * ln**2) / 8
    
    show_sub(
        "2.1 Total Static Moment ($M_o$)",
        r"M_o = \frac{w_u L_2 l_n^2}{8}",
        f"\\frac{{{w_u:,.0f} \\cdot {L2} \\cdot {ln:.2f}^2}}{{8}}",
        f"{Mo:,.0f}",
        "kg-m"
    )

    # 2.2 Distribute to Sections (ACI Coefficients)
    # หมายเหตุ: ใน EFM จริงๆ ต้อง Run Frame Analysis แต่เพื่อให้ได้คำตอบสำหรับการออกแบบเหล็ก
    # เราจะใช้ ACI Direct Design Method Coefficients เป็นตัวแทนของ Moment Envelope
    
    st.markdown("#### 2.2 Design Moments (By Strip)")
    
    # Coefficients based on location (Simplified logic for demonstration)
    if loc_key == "interior":
        coef_neg = 0.65
        coef_pos = 0.35
    else: # Edge/Corner
        coef_neg = 0.50 # Approx average for edge
        coef_pos = 0.50
    
    M_neg_total = coef_neg * Mo
    M_pos_total = coef_pos * Mo
    
    # Column Strip % (Interior: 75% Neg, 60% Pos)
    pct_cs_neg = 0.75
    pct_cs_pos = 0.60
    
    # Calculate Moments
    M_neg_cs = M_neg_total * pct_cs_neg
    M_pos_cs = M_pos_total * pct_cs_pos
    M_neg_ms = M_neg_total * (1 - pct_cs_neg)
    M_pos_ms = M_pos_total * (1 - pct_cs_pos)
    
    # Display Table
    data_moments = {
        "Position": ["Negative (Support)", "Positive (Midspan)"],
        "Total M (kg-m)": [M_neg_total, M_pos_total],
        "Column Strip (kg-m)": [M_neg_cs, M_pos_cs],
        "Middle Strip (kg-m)": [M_neg_ms, M_pos_ms]
    }
    st.table(pd.DataFrame(data_moments).set_index("Position").style.format("{:,.0f}"))
    st.info("💡 **Note:** Moments calculated using ACI Coeffs for strip assignment.")

    st.markdown("---")

    # -------------------------------------------------------
    # PART 3: REINFORCEMENT DESIGN (ออกแบบเหล็กเสริม)
    # -------------------------------------------------------
    st.subheader("3. Reinforcement Design (ออกแบบเหล็กเสริม)")
    st.markdown(f"**Design Parameters:** $f'_c = {fc}$ ksc, $f_y = {fy}$ ksc, Bar DB{d_bar_mm}")
    
    # 3.1 Effective Depth (d)
    d_eff = h_slab - cover - (d_bar_cm/2)
    show_sub(
        "3.1 Effective Depth ($d$)",
        r"d = h - cover - \frac{d_b}{2}",
        f"{h_slab} - {cover} - {d_bar_cm/2}",
        f"{d_eff:.2f}",
        "cm"
    )
    
    # Function to calculate Steel
    def design_steel(M_kgm, width_m, loc_name):
        st.markdown(f"### 📍 Design for {loc_name}")
        
        # 1. Convert M to kg-cm
        M_u = M_kgm * 100 
        width_cm = width_m * 100
        
        # 2. Rn
        phi = 0.90
        Rn = M_u / (phi * width_cm * d_eff**2)
        
        st.markdown(f"**Step A: Calculate $R_n$** ($M_u = {M_u:,.0f}$ kg-cm)")
        st.latex(r"R_n = \frac{M_u}{\phi b d^2}")
        st.write(f"$$ = \\frac{{{M_u:,.0f}}}{{0.9 \\cdot {width_cm:.0f} \\cdot {d_eff:.2f}^2}} = \\mathbf{{{Rn:.2f}}} \\text{{ ksc}} $$")
        
        # 3. Rho Required
        # Check if Rn too high
        rho_max = 0.75 * (0.85 * 0.85 * fc / fy * (6120/(6120+fy))) # Approx ACI
        
        st.markdown("**Step B: Calculate Reinforcement Ratio ($\\rho$)**")
        st.latex(r"\rho = \frac{0.85 f'_c}{f_y} \left[ 1 - \sqrt{1 - \frac{2 R_n}{0.85 f'_c}} \right]")
        
        term_sqrt = 1 - (2 * Rn) / (0.85 * fc)
        if term_sqrt < 0:
            st.error("❌ Section too small! (Concrete Failure). Increase thickness.")
            return
            
        rho_req = (0.85 * fc / fy) * (1 - np.sqrt(term_sqrt))
        st.write(f"Calculated $\\rho_{{req}} = {rho_req:.5f}$")
        
        # 4. Rho Min (Temp & Shrinkage)
        rho_min = 0.0018 # ACI for fy=4000
        st.write(f"Min $\\rho_{{min}} = {rho_min}$ (Temperature)")
        
        rho_design = max(rho_req, rho_min)
        
        # 5. As Required
        As_req = rho_design * width_cm * d_eff
        st.markdown(f"**Step C: Area of Steel ($A_s$)**")
        st.latex(r"A_s = \rho b d")
        st.write(f"$$ = {rho_design:.5f} \\cdot {width_cm:.0f} \\cdot {d_eff:.2f} = \\mathbf{{{As_req:.2f}}} \\text{{ cm}}^2 $$")
        
        # 6. Bar Selection
        A_bar = 3.1416 * (d_bar_cm/2)**2
        num_bars = As_req / A_bar
        num_bars_int = int(np.ceil(num_bars))
        
        st.success(f"✅ **Select:** Use **{num_bars_int}** - DB{d_bar_mm} (Total $A_s = {num_bars_int*A_bar:.2f}$ cm$^2$)")
        
        # Spacing Check
        spacing = width_cm / num_bars_int
        st.caption(f"Average Spacing: @ {spacing:.0f} cm")
        st.markdown("---")

    # --- Run Design for Critical Sections ---
    
    col_design1, col_design2 = st.columns(2)
    
    with col_design1:
        # Design Column Strip (Negative Moment) - Width = L2/2 (approx for CS)
        width_cs = L2 / 2.0 
        st.info(f"**Column Strip (Width = {width_cs} m)**")
        design_steel(M_neg_cs, width_cs, "Column Strip (Top Steel)")
        
    with col_design2:
        # Design Middle Strip (Positive Moment) - Width = L2/2
        width_ms = L2 / 2.0
        st.info(f"**Middle Strip (Width = {width_ms} m)**")
        design_steel(M_pos_ms, width_ms, "Middle Strip (Bottom Steel)")
