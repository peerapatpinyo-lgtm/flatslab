# tab_efm.py
import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# พยายาม import calculations ถ้าไม่มีให้แจ้งเตือน (เพื่อป้องกัน App Crash)
try:
    import calculations as calc  # เชื่อมต่อกับ The Brain V2.0
except ImportError:
    calc = None

# --- Settings for Professional Plots ---
plt.rcParams.update({
    'font.family': 'sans-serif', 
    'font.size': 10,
    'axes.spines.top': False, 
    'axes.spines.right': False,
    'axes.grid': True, 
    'grid.alpha': 0.3, 
    'figure.autolayout': True
})

# ==========================================
# 1. VISUALIZATION FUNCTIONS (Graphics Engine)
# ==========================================

def plot_stick_model(Ks, Sum_Kc, Kt, Kec):
    """
    Draws the Equivalent Frame Model (Spring Model).
    """
    fig, ax = plt.subplots(figsize=(6, 2.5))
    
    # Main Axes
    ax.axhline(0, color='black', linewidth=1) # Slab axis
    ax.plot([0, 0], [-1, 1], color='gray', linewidth=3, alpha=0.3) # Column axis
    
    # Torsional Spring Symbol
    ax.plot([0.2, 0.2], [-0.2, 0.2], color='orange', lw=2, linestyle='--')
    ax.text(0.25, 0, f"Torsion ($K_t$)\n{Kt/1e5:.1f}E5", color='orange', va='center', fontsize=8)
    
    # Slab Stiffness
    ax.text(-0.5, 0.1, f"Slab ($K_s$)\n{Ks/1e5:.1f}E5", ha='center', color='blue', fontsize=8)
    
    # Column Stiffness
    ax.text(-0.1, 0.8, f"Col (Sum)\n{Sum_Kc/1e5:.1f}E5", ha='right', color='gray', fontsize=8)
    
    # Kec Indicator
    ax.annotate(f"Joint $K_{{ec}}$\n= {Kec/1e5:.1f}E5", xy=(0, 0), xytext=(0.6, 0.5),
                arrowprops=dict(facecolor='green', shrink=0.05), 
                fontsize=9, fontweight='bold', color='green', ha='center')
    
    ax.set_xlim(-1.2, 1.2)
    ax.set_ylim(-1.2, 1.2)
    ax.axis('off')
    return fig

def plot_moment_envelope(L1, M_neg_L, M_neg_R, M_pos, c1_cm):
    """
    Plots the Moment Diagram for the span.
    """
    fig, ax = plt.subplots(figsize=(8, 3))
    x = np.linspace(0, L1, 200)
    
    # Simple Parabolic interpolation for visualization
    M_x = np.zeros_like(x)
    for i, xi in enumerate(x):
        t = xi / L1 if L1 > 0 else 0
        # Linear interpolation of end moments
        M_base = (1-t)*(-abs(M_neg_L)) + t*(-abs(M_neg_R))
        # Parabolic hump (approximate wL^2/8 shape added)
        # Height of bump needs to reach M_pos from the base line
        M_mid_base = (-abs(M_neg_L) - abs(M_neg_R)) / 2
        bump_height = M_pos - M_mid_base
        M_bump = 4 * bump_height * t * (1-t) 
        M_x[i] = M_base + M_bump

    # Fill Areas
    ax.fill_between(x, M_x, 0, where=(M_x>0), color='#3498DB', alpha=0.2)
    ax.fill_between(x, M_x, 0, where=(M_x<0), color='#E74C3C', alpha=0.2)
    ax.plot(x, M_x, color='#2C3E50', lw=2)
    
    # Draw Supports (Columns)
    c1_m = c1_cm / 100.0
    ax.axvspan(-c1_m/2, c1_m/2, color='gray', alpha=0.3)
    ax.axvspan(L1-c1_m/2, L1+c1_m/2, color='gray', alpha=0.3)
    ax.axhline(0, color='black', lw=0.8)

    # Labels
    ax.text(0, -abs(M_neg_L), f"{abs(M_neg_L):,.0f}", ha='right', color='red', fontweight='bold', fontsize=9)
    ax.text(L1, -abs(M_neg_R), f"{abs(M_neg_R):,.0f}", ha='left', color='red', fontweight='bold', fontsize=9)
    ax.text(L1/2, M_pos, f"{M_pos:,.0f}", ha='center', va='bottom', color='blue', fontweight='bold', fontsize=9)
    
    ax.invert_yaxis() # Moment diagram convention
    ax.set_ylabel("Moment (kg-m)")
    ax.set_xlabel("Span (m)")
    ax.set_title("Design Moment Envelope (Face of Support)", fontweight='bold')
    return fig

def draw_section_detail(b_cm, h_cm, db, spacing, title):
    """
    Visualizes the cross-section with rebars based on spacing.
    """
    fig, ax = plt.subplots(figsize=(5, 2.0))
    # Concrete section
    ax.add_patch(patches.Rectangle((0, 0), b_cm, h_cm, facecolor='#E0E0E0', edgecolor='#333333'))
    
    # Rebars
    cover = 2.5 
    dia_cm = db / 10.0
    
    # Determine Y position (Top or Bot)
    if "Top" in title:
        y_pos = h_cm - cover - dia_cm/2
    else:
        y_pos = cover + dia_cm/2
        
    # Calculate positions based on spacing
    # Approximate number of bars for visual
    if spacing > 0:
        num_bars = int((b_cm - 2*cover) / spacing) + 1
    else:
        num_bars = 2
        
    if num_bars < 2: num_bars = 2
    
    # Re-distribute strictly for visual centering
    real_span = (num_bars - 1) * spacing
    start_x = (b_cm - real_span) / 2
    
    xs = [start_x + i*spacing for i in range(num_bars)]
        
    for x in xs:
        if 0 < x < b_cm: # Draw only if inside section
            ax.add_patch(patches.Circle((x, y_pos), dia_cm/2, fc='red', ec='black'))
            
    label_text = f"DB{db}@{spacing:.0f}cm" if db >= 10 else f"RB{db}@{spacing:.0f}cm"
    ax.text(b_cm/2, h_cm/2, label_text, ha='center', va='center', 
            fontweight='bold', color='darkred', fontsize=12, bbox=dict(facecolor='white', alpha=0.7, edgecolor='none'))
            
    ax.set_title(title, fontsize=10)
    ax.axis('equal')
    ax.axis('off')
    return fig

# ==========================================
# 2. LOGIC: MOMENT DISTRIBUTION (Simplified View Logic)
# ==========================================

def run_moment_distribution(FEM, DF_slab, iterations=4):
    """
    Simulate Hardy Cross Method (Simplified for single span demo).
    """
    history = []
    
    # 1. Fixed End Moments
    M_A = FEM   # CCW (+)
    M_B = -FEM  # CW (-)
    
    history.append({"Step": "1. FEM", "Joint A": M_A, "Joint B": M_B, "Description": "Initial Load"})
    
    curr_unbal_A = M_A 
    curr_unbal_B = M_B
    
    total_A = M_A
    total_B = M_B

    for i in range(iterations):
        # 2. Balance
        bal_A = -1 * curr_unbal_A * DF_slab
        bal_B = -1 * curr_unbal_B * DF_slab
        
        history.append({
            "Step": f"Iter {i+1}: Balance", 
            "Joint A": bal_A, "Joint B": bal_B,
            "Description": f"Bal = -M_unbal x {DF_slab:.3f}"
        })
        
        total_A += bal_A
        total_B += bal_B
        
        # 3. Carry Over (CO)
        co_to_A = bal_B * 0.5
        co_to_B = bal_A * 0.5
        
        history.append({
            "Step": f"Iter {i+1}: Carry Over", 
            "Joint A": co_to_A, "Joint B": co_to_B,
            "Description": "CO = M_bal x 0.5"
        })
        
        total_A += co_to_A
        total_B += co_to_B
        
        # Update Unbalanced for next loop
        curr_unbal_A = co_to_A
        curr_unbal_B = co_to_B

    history.append({"Step": "🏁 SUM", "Joint A": total_A, "Joint B": total_B, "Description": "Total Moment"})
    return pd.DataFrame(history), total_A, total_B

# ==========================================
# 3. CORE DESIGN FUNCTION
# ==========================================
def calculate_capacity_check(Mu_kgm, b_width_m, h_slab, cover, fc, fy, db, spacing):
    """
    Calculates As_req vs As_prov and checks capacity.
    """
    # Units: cm, kg, ksc
    b_cm = b_width_m * 100
    # Effective depth d
    d_eff = h_slab - cover - (db/20.0) # db in mm -> db/2 in cm = db/20
    
    Mu_kgcm = Mu_kgm * 100.0
    phi = 0.90
    
    # 1. Required Steel
    try:
        Rn = Mu_kgcm / (phi * b_cm * d_eff**2)
    except ZeroDivisionError:
        Rn = 0
        
    rho_req = 0.0018 # Min
    
    # Check if section can handle moment
    term = 1 - (2 * Rn) / (0.85 * fc)
    
    if term >= 0:
        rho_calc = (0.85 * fc / fy) * (1 - np.sqrt(term))
        rho_req = max(rho_calc, 0.0018)
    else:
        # Section Fail (Moment too high for concrete section)
        rho_req = 999 
        rho_calc = 999
        
    As_req = rho_req * b_cm * d_eff
    
    # 2. Provided Steel
    bar_area = 3.1416 * (db/10.0)**2 / 4.0
    if spacing > 0:
        As_prov = (b_cm / spacing) * bar_area
    else:
        As_prov = 0
    
    # 3. Capacity
    a = (As_prov * fy) / (0.85 * fc * b_cm)
    Mn = As_prov * fy * (d_eff - a/2.0)
    PhiMn = 0.90 * Mn / 100.0 # Convert back to kg-m
    
    dc_ratio = Mu_kgm / PhiMn if PhiMn > 0 else 999
    
    # Return all intermediate values for display
    return {
        "d": d_eff,
        "Rn": Rn,
        "rho_calc": rho_calc,
        "rho_req": rho_req,
        "As_req": As_req,
        "As_prov": As_prov,
        "a_depth": a,
        "PhiMn": PhiMn,
        "Ratio": dc_ratio,
        "Pass": dc_ratio <= 1.0 and rho_calc != 999
    }

# ==========================================
# 4. MAIN RENDER FUNCTION
# ==========================================
def render(c1_w, c2_w, L1, L2, lc, h_slab, fc, mat_props, w_u, col_type, **kwargs):
    
    st.markdown("### 🏗️ Full EFM Analysis: Stiffness to Design")
    st.caption("Equivalent Frame Method with Detailed Step-by-Step Calculation")
    st.markdown("---")
    
    if calc is None:
        st.error("❌ Critical Error: 'calculations.py' not found. Please ensure the calculation module is available.")
        return

    # --- Extract Drop Panel Props from kwargs ---
    h_drop = kwargs.get('h_drop', h_slab)
    drop_w = kwargs.get('drop_w', 0)
    drop_l = kwargs.get('drop_l', 0)

    # --- A. PRE-CALCULATION ---
    # Material Properties
    Ec = 15100 * np.sqrt(fc) # ksc
    fy = mat_props.get('fy', 4000)
    cover = mat_props.get('cover', 2.5)
    
    # 1. Stiffness Calculations
    try:
        Ks_val, Sum_Kc, Kt_val, Kec_val = calc.calculate_stiffness(
            c1_w, c2_w, L1, L2, lc, h_slab, fc, 
            h_drop=h_drop, drop_w=drop_w, drop_l=drop_l
        )
    except AttributeError:
        st.error("❌ Error: Function 'calculate_stiffness' not found in calculations.py.")
        return
    except Exception as e:
        st.error(f"❌ Calculation Error: {e}")
        return
    
    # Distribution Factor (DF)
    Total_K = Ks_val + Kec_val
    if Total_K > 0:
        DF_slab = Ks_val / Total_K
    else:
        DF_slab = 0
    
    # 2. Moment Analysis
    w_line = w_u * L2 # Load per meter length of frame (kg/m)
    FEM = w_line * L1**2 / 12
    
    # Run Hardy Cross
    df_iter, M_final_L, M_final_R = run_moment_distribution(FEM, DF_slab)
    
    # Face Correction
    # Reduce moment from centerline to face of support
    Vu_frame = w_line * L1 / 2.0 # Total shear
    c1_m = c1_w / 100.0
    # M_face = M_center - V*c/2 + w*(c/2)^2/2
    M_correction = Vu_frame * (c1_m/2.0) - w_line*(c1_m/2.0)**2 / 2.0
    
    M_neg_design = abs(M_final_L) - M_correction
    if M_neg_design < 0: M_neg_design = 0
    
    # Calculate Positive Moment (Statics)
    # Mo = wL^2/8
    Mo = w_line * L1**2 / 8.0
    # M_pos = Mo - (M_neg_L + M_neg_R)/2
    M_pos_design = Mo - M_neg_design # assuming symmetry for this module check
    if M_pos_design < 0: M_pos_design = 0

    # --- B. DASHBOARD SUMMARY ---
    col1, col2 = st.columns([1.5, 1])
    with col1:
        st.pyplot(plot_stick_model(Ks_val, Sum_Kc, Kt_val, Kec_val))
    with col2:
        st.info("📊 **Analysis Result**")
        st.write(f"**$K_{{ec}}$ (Equiv):** {Kec_val/1e5:.2f} E5")
        st.write(f"**$K_s$ (Slab):** {Ks_val/1e5:.2f} E5")
        st.metric("Distribution Factor (DF)", f"{DF_slab:.3f}", 
                  help="Ratio of moment absorbed by Slab vs Column. DF = Ks / (Ks + Kec)")
        if h_drop > h_slab and drop_w > 0:
            st.warning(f"Drop Panel Active\n(h={h_drop}cm, w={drop_w}m)")

    # --- C. DETAILED TABS ---
    tab1, tab2, tab3 = st.tabs(["1️⃣ Step 1: Stiffness", "2️⃣ Step 2: Moment Dist.", "3️⃣ Step 3: Design"])


    # === TAB 1: STIFFNESS CALCULATIONS ===
    with tab1:
        st.subheader("1. การคำนวณค่าสติฟเนส (Stiffness Parameters)")
        st.caption("Reference: ACI 318 Equivalent Frame Method (EFM) - Elastic Analysis")
        
        # --- 1.1 Material Properties ---
        st.markdown("#### 1.1 คุณสมบัติวัสดุ (Material Properties)")
        col_mat1, col_mat2 = st.columns(2)
        with col_mat1:
            st.write(f"**Concrete Strength ($f_c'$):** {fc} ksc")
            st.write(f"**Modulus of Elasticity ($E_c$):**")
        
        # Formula for Ec (ACI 318 / EIT)
        # Ec = 15100 sqrt(fc') for ksc unit
        Ec_calc = 15100 * np.sqrt(fc)
        
        with col_mat2:
            st.latex(rf"E_c = 15,100 \sqrt{{f_c'}}")
            st.latex(rf"E_c = 15,100 \sqrt{{{fc}}} = \mathbf{{{Ec_calc:,.0f}}} \, ksc")
        
        st.divider()

        # --- 1.2 Column Stiffness (Kc) ---
        st.markdown("#### 1.2 สติฟเนสของเสา (Column Stiffness, $K_c$)")
        st.markdown(r"""
        พิจารณาโมเมนต์ความเฉื่อย ($I_c$) ของหน้าตัดเสา และความยาวเสา ($l_c$)
        โดย $K_c$ คำนวณจากสูตรพื้นฐานสำหรับปลายยึดแน่น (Far End Fixed):
        """)
        
        # Prepare variables for display
        lc_cm = lc * 100  # m to cm
        Ic_val = (c2_w * c1_w**3) / 12  # cm4 (c1 is usually the dimension in bending direction)
        
        # Display Column Section Calculation
        c_k1, c_k2 = st.columns([1, 1.5])
        with c_k1:
            st.info(f"**Column Dim:** {c1_w}x{c2_w} cm\n\n**Height ($l_c$):** {lc} m")
        with c_k2:
            st.latex(rf"I_c = \frac{{b h^3}}{{12}} = \frac{{{c2_w} \cdot {c1_w}^3}}{{12}} = {Ic_val:,.0f} \, cm^4")
            
        st.write("คำนวณค่า Stiffness ($K_c$):")
        
        # Kc Calculation Display
        # Note: The actual Sum_Kc comes from calc.calculate_stiffness which might include rigid arm effects
        # Here we show the base formula verification
        Kc_theory = (4 * Ec_calc * Ic_val) / lc_cm
        
        st.latex(rf"K_{{c,theory}} = \frac{{4 E_c I_c}}{{l_c}} = \frac{{4 \cdot {Ec_calc:,.0f} \cdot {Ic_val:,.0f}}}{{{lc_cm}}} \approx {Kc_theory:,.0f} \, kg\cdot cm")
        
        st.markdown(f"""
        > **Note:** ค่าที่ใช้จริงรวมผลรวมของเสาต้นบนและต้นล่าง ($\Sigma K_c$) 
        > และอาจมีการปรับแก้กรณี Joint มีความหนา (Rigid Arm Correction)
        """)
        st.success(f"📌 **Result:** $\Sigma K_c$ (Total) = **{Sum_Kc/1e5:.3f} $\times 10^5$** kg-cm")

        st.divider()

        # --- 1.3 Slab Stiffness (Ks) ---
        st.markdown("#### 1.3 สติฟเนสของพื้น (Slab Stiffness, $K_s$)")
        st.write(f"พิจารณาความกว้างแถบพื้น ($L_2$) และความหนา ($h$):")
        
        L1_cm = L1 * 100
        L2_cm = L2 * 100
        Is_val = (L2_cm * h_slab**3) / 12
        Ks_theory = (4 * Ec_calc * Is_val) / L1_cm
        
        s_k1, s_k2 = st.columns([1, 1.5])
        with s_k1:
            st.write(f"- Span $L_1 = {L1}$ m")
            st.write(f"- Width $L_2 = {L2}$ m")
            st.write(f"- Thickness $h = {h_slab}$ cm")
        with s_k2:
            st.latex(rf"I_s = \frac{{L_2 h^3}}{{12}} = \frac{{{L2_cm:.0f} \cdot {h_slab}^3}}{{12}} = {Is_val:,.0f} \, cm^4")
        
        st.write("แทนค่าในสูตร Stiffness ของพื้น:")
        st.latex(rf"K_s = \frac{{4 E_c I_s}}{{L_1}} = \frac{{4 \cdot {Ec_calc:,.0f} \cdot {Is_val:,.0f}}}{{{L1_cm}}} \approx {Ks_theory:,.0f} \, kg\cdot cm")
        
        st.success(f"📌 **Result:** $K_s$ (Slab) = **{Ks_val/1e5:.3f} $\times 10^5$** kg-cm")

        st.divider()

        # --- 1.4 Equivalent Stiffness (Kec) ---
        st.markdown("#### 1.4 สติฟเนสเทียบเท่า (Equivalent Stiffness, $K_{ec}$)")
        st.markdown(r"""
        ในวิธี EFM จุดต่อระหว่างพื้นและเสาไม่ได้เป็น Rigid 100% แต่มีความยืดหยุ่นจากการบิดตัว (Torsion) 
        จึงต้องรวมผลของ Torsional Member ($K_t$) เข้ากับเสา ($K_c$)
        """)
        
        # Torsional Stiffness Kt (Show Formula Only implies complexity)
        st.markdown("**1) Torsional Stiffness ($K_t$):**")
        st.caption("คำนวณโดยพิจารณาส่วนของพื้นทียื่นออกมาด้านข้างเสา (Torsional member)")
        st.latex(r"K_t = \sum \frac{9 E_{cs} C}{L_2 (1 - c_2/L_2)^3}")
        st.code(f"Calculated Kt = {Kt_val:,.0f} kg-cm", language="markdown")
        
        st.markdown("**2) Combine to Equivalent Stiffness ($K_{ec}$):**")
        st.markdown("รวมความอ่อนตัว (Flexibility) ของเสาและส่วนรับแรงบิด:")
        
        st.latex(r"\frac{1}{K_{ec}} = \frac{1}{\Sigma K_c} + \frac{1}{K_t}")
        
        # Substitution Display
        st.latex(rf"\frac{{1}}{{K_{{ec}}}} = \frac{{1}}{{{Sum_Kc:,.0f}}} + \frac{{1}}{{{Kt_val:,.0f}}}")
        
        # Final Calculation Check
        inv_Kec = (1/Sum_Kc + 1/Kt_val)
        Kec_check = 1/inv_Kec if inv_Kec > 0 else 0
        
        st.latex(rf"K_{{ec}} = \mathbf{{{Kec_val/1e5:.3f} \times 10^5}} \, kg\cdot cm")
        
        # Summary Box for Step 1
        st.info(f"""
        **สรุปค่าสำหรับนำไปกระจายโมเมนต์ (Step 2):**
        * Stiffness ของพื้น ($K_s$) = {Ks_val:,.0f} kg-cm
        * Stiffness เทียบเท่าของเสา ($K_{{ec}}$) = {Kec_val:,.0f} kg-cm
        * **Distribution Factor (DF):** {Ks_val / (Ks_val + Kec_val):.3f}
        """)

    # === TAB 2: MOMENT ===
    with tab2:
        st.subheader("2. Moment Distribution Analysis")
        st.caption("Method: Hardy Cross Method (Moment Distribution)")

        st.markdown("#### 2.1 Load & Fixed End Moments (FEM)")
        st.write("Convert Area Load ($w_u$) to Line Load ($w$) on the frame:")
        st.latex(rf"w = w_u \times L_2 = {w_u} \times {L2} = \mathbf{{{w_line:,.0f}}} \, kg/m")
        
        st.write("Fixed End Moment (assuming fixed supports initially):")
        st.latex(rf"FEM = \frac{{w L_1^2}}{{12}} = \frac{{{w_line:,.0f} \cdot {L1}^2}}{{12}} = \mathbf{{{FEM:,.0f}}} \, kg\cdot m")
        
        st.divider()
        
        st.markdown("#### 2.2 Iterative Distribution (Hardy Cross)")
        st.markdown(f"**Distribution Factor (DF):** Proportion of unbalanced moment absorbed by the slab.")
        st.latex(rf"DF_{{slab}} = \frac{{K_s}}{{K_s + K_{{ec}}}} = \frac{{{Ks_val:.0f}}}{{{Ks_val:.0f} + {Kec_val:.0f}}} = \mathbf{{{DF_slab:.3f}}}")
        
        with st.expander("Show Iteration Table"):
            st.dataframe(df_iter.style.format({"Joint A": "{:,.0f}", "Joint B": "{:,.0f}"}), use_container_width=True)
        
        st.markdown(f"**Final Centerline Moment ($M_{{cen}}$):** ${abs(M_final_L):,.0f} \, kg\cdot m$")

        st.divider()
        
        st.markdown("#### 2.3 Face Correction (Design Moment)")
        st.caption("Ref: Design moments are taken at the face of the support, not the centerline.")
        st.latex(r"M_{face} = M_{cen} - V_u \left(\frac{c_1}{2}\right) + \frac{w_u (c_1/2)^2}{2}")
        
        st.write("Where:")
        st.write(f"- Shear $V_u = w L_1 / 2 = {Vu_frame:,.0f}$ kg")
        st.write(f"- Support width $c_1 = {c1_m:.2f}$ m")
        
        st.latex(rf"\Delta M = {Vu_frame:,.0f} \left(\frac{{{c1_m}}}{{2}}\right) - \frac{{{w_line:,.0f} (0.5 \cdot {c1_m})^2}}{{2}} = {M_correction:,.0f} \, kg\cdot m")
        st.latex(rf"M_{{design}} (-) = {abs(M_final_L):,.0f} - {M_correction:,.0f} = \mathbf{{{M_neg_design:,.0f}}} \, kg\cdot m")
        
        st.pyplot(plot_moment_envelope(L1, -M_neg_design, -M_neg_design, M_pos_design, c1_w))

    # === TAB 3: DESIGN ===
    with tab3:
        st.subheader("3. Reinforcement Design (USD Method)")
        st.caption(f"Code Reference: ACI 318 / EIT Standard (SDM)")
        st.write(f"**Materials:** $f_c' = {fc}$ ksc, $f_y = {fy}$ ksc")
        
        # 1. Get Config from Mat Props (or default)
        cfg = mat_props.get('rebar_cfg', {})
        
        # 2. Define Strip Widths
        w_cs = min(L1, L2) / 2.0
        w_ms = L2 - w_cs
        st.info(f"**Strip Widths:** Column Strip = {w_cs:.2f} m | Middle Strip = {w_ms:.2f} m")
        
        # 3. Design Loop (4 Zones)
        zones = [
            {
                "Name": "Column Strip - Top (-)", 
                "Mu": M_neg_design * 0.75, "Width": w_cs, 
                "db": cfg.get('cs_top_db', 12), "spa": cfg.get('cs_top_spa', 20),
                "coeff": 0.75, "loc": "Support"
            },
            {
                "Name": "Column Strip - Bot (+)", 
                "Mu": M_pos_design * 0.60, "Width": w_cs, 
                "db": cfg.get('cs_bot_db', 12), "spa": cfg.get('cs_bot_spa', 20),
                "coeff": 0.60, "loc": "Midspan"
            },
            {
                "Name": "Middle Strip - Top (-)", 
                "Mu": M_neg_design * 0.25, "Width": w_ms, 
                "db": cfg.get('ms_top_db', 12), "spa": cfg.get('ms_top_spa', 20),
                "coeff": 0.25, "loc": "Support"
            },
            {
                "Name": "Middle Strip - Bot (+)", 
                "Mu": M_pos_design * 0.40, "Width": w_ms, 
                "db": cfg.get('ms_bot_db', 12), "spa": cfg.get('ms_bot_spa', 20),
                "coeff": 0.40, "loc": "Midspan"
            }
        ]
        
        results = []
        
        # Grid Layout for Cards
        c1, c2 = st.columns(2)
        
        for i, z in enumerate(zones):
            # Calculate Logic
            res = calculate_capacity_check(z['Mu'], z['Width'], h_slab, cover, fc, fy, z['db'], z['spa'])
            z.update(res)
            results.append(z)
            
            # Select Column
            col_curr = c1 if i % 2 == 0 else c2
            
            with col_curr:
                with st.container(border=True):
                    # Header
                    pass_status = "✅ PASS" if z['Pass'] else "❌ FAIL"
                    st.markdown(f"##### {z['Name']}")
                    st.caption(f"Design Moment $M_u = \text{{Total}} \times {z['coeff']} = {z['Mu']:,.0f}$ kg-m")
                    
                    # Visual
                    st.pyplot(draw_section_detail(z['Width']*100, h_slab, z['db'], z['spa'], z['Name']))
                    
                    # Quick Metrics
                    c_a, c_b = st.columns(2)
                    c_a.metric("Provided As", f"{z['As_prov']:.2f} cm²", f"Req: {z['As_req']:.2f}")
                    c_b.metric("D/C Ratio", f"{z['Ratio']:.2f}", pass_status, delta_color="inverse")
                    
                    # --- DETAILED CALCULATION EXPANDER ---
                    with st.expander("📝 View Detailed Calculation Steps"):
                        st.markdown("**1. Section Parameters**")
                        st.latex(rf"b = {z['Width']*100:.0f} \, cm, \quad h = {h_slab} \, cm")
                        st.latex(rf"d = h - cover - d_b/2 = {h_slab} - {cover} - {z['db']/20:.1f} = {z['d']:.2f} \, cm")
                        
                        st.markdown("**2. Required Reinforcement ($A_{s,req}$)**")
                        st.write("Calculate Strength Parameter ($R_n$):")
                        st.latex(rf"R_n = \frac{{M_u}}{{\phi b d^2}} = \frac{{{z['Mu']*100:,.0f}}}{{0.9 \cdot {z['Width']*100:.0f} \cdot {z['d']:.2f}^2}} = {z['Rn']:.2f} \, ksc")
                        
                        st.write("Calculate Reinforcement Ratio ($\rho$):")
                        if z['rho_calc'] != 999:
                            st.latex(rf"\rho_{{req}} = \frac{{0.85 f_c'}}{{f_y}} \left( 1 - \sqrt{{1 - \frac{{2 R_n}}{{0.85 f_c'}}}} \right) = {z['rho_calc']:.5f}")
                            st.write(f"Check Min $\\rho$: $0.0018$ vs {z['rho_calc']:.5f} -> Use $\\rho = {z['rho_req']:.5f}$")
                        else:
                            st.error("Section Failed (Rn too high). Concrete dimensions too small.")
                        
                        st.latex(rf"A_{{s,req}} = \rho b d = {z['rho_req']:.5f} \cdot {z['Width']*100:.0f} \cdot {z['d']:.2f} = \mathbf{{{z['As_req']:.2f} \, cm^2}}")
                        
                        st.markdown("**3. Check Capacity ($\phi M_n$)**")
                        st.write(f"Using **DB{z['db']}@{z['spa']}cm**: $A_{{s,prov}} = {z['As_prov']:.2f} \, cm^2$")
                        st.write("Depth of equivalent stress block ($a$):")
                        st.latex(rf"a = \frac{{A_s f_y}}{{0.85 f_c' b}} = \frac{{{z['As_prov']:.2f} \cdot {fy}}}{{0.85 \cdot {fc} \cdot {z['Width']*100:.0f}}} = {z['a_depth']:.2f} \, cm")
                        
                        st.write("Nominal Moment Capacity:")
                        st.latex(rf"\phi M_n = \phi A_s f_y (d - a/2)")
                        st.latex(rf"= 0.9 \cdot {z['As_prov']:.2f} \cdot {fy} \cdot ({z['d']:.2f} - {z['a_depth']:.2f}/2) \cdot 10^{{-2}}")
                        st.latex(rf"= \mathbf{{{z['PhiMn']:,.0f} \, kg\cdot m}}")
                        
                        if z['Ratio'] <= 1.0:
                            st.success(f"Check: $M_u ({z['Mu']:,.0f}) \le \phi M_n ({z['PhiMn']:,.0f})$ -> OK")
                        else:
                            st.error(f"Check: $M_u ({z['Mu']:,.0f}) > \phi M_n ({z['PhiMn']:,.0f})$ -> NOT SAFE")

        # Summary Table
        st.markdown("#### 📋 Summary Table")
        df_res = pd.DataFrame(results)[['Name', 'Mu', 'PhiMn', 'As_req', 'As_prov', 'Ratio']]
        
        st.dataframe(df_res.style.format({
            'Mu': "{:,.2f}", 
            'PhiMn': "{:,.2f}", 
            'As_req': "{:,.2f}", 
            'As_prov': "{:,.2f}", 
            'Ratio': "{:,.2f}"
        }), use_container_width=True)
