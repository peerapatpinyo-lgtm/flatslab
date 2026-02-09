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
        st.subheader("1. Stiffness Matrix Calculations")
        st.caption("Methodology: ACI 318-19 Equivalent Frame Method (EFM) & Elastic Analysis")
        
        # --- 1.1 Material Properties ---
        st.markdown("#### 1.1 Material Properties")
        st.markdown("**Reference:** ACI 318-19 Section 19.2.2 (Modulus of Elasticity)")
        
        col_mat1, col_mat2 = st.columns([1, 2])
        
        # Calculation
        Ec_calc = 15100 * np.sqrt(fc) # ksc unit
        
        with col_mat1:
            st.write(f"**Concrete Strength ($f_c'$):**")
            st.write(f"**Modulus ($E_c$):**")
        with col_mat2:
            st.write(f"{fc} ksc")
            st.latex(rf"E_c = 15,100 \sqrt{{f_c'}} = 15,100 \sqrt{{{fc}}} = \mathbf{{{Ec_calc:,.0f}}} \, ksc")
        
        st.divider()

        # --- 1.2 Column Stiffness (Kc) ---
        st.markdown("#### 1.2 Column Stiffness ($K_c$)")
        st.markdown("**Reference:** ACI 318-19 Section 8.11.3 (Column Moments) / Mechanics of Materials")
        st.write("Stiffness of the column member assuming fixed far ends (standard frame assumption).")
        
        # Variables
        lc_cm = lc * 100
        Ic_val = (c2_w * c1_w**3) / 12  
        Kc_theory = (4 * Ec_calc * Ic_val) / lc_cm
        
        c_k1, c_k2 = st.columns([1, 1.5])
        with c_k1:
            st.info(f"**Geometry:**\n- Width ($c_2$): {c2_w} cm\n- Depth ($c_1$): {c1_w} cm\n- Height ($l_c$): {lc_cm} cm")
        with c_k2:
            st.markdown("**A) Moment of Inertia ($I_c$):**")
            st.latex(rf"I_c = \frac{{c_2 c_1^3}}{{12}} = \frac{{{c2_w} \cdot {c1_w}^3}}{{12}} = {Ic_val:,.0f} \, cm^4")
            
            st.markdown("**B) Stiffness ($K_c$):**")
            st.latex(rf"K_c = \frac{{4 E_c I_c}}{{l_c}} = \frac{{4 \cdot {Ec_calc:,.0f} \cdot {Ic_val:,.0f}}}{{{lc_cm}}} \approx {Kc_theory:,.0f} \, kg\cdot cm")

        st.warning(f"👉 **Total Column Stiffness ($\Sigma K_c$):** Sum of stiffnesses for columns above and below the slab.")
        st.latex(rf"\Sigma K_c = \mathbf{{{Sum_Kc/1e5:.3f} \times 10^5}} \, kg\cdot cm")

        st.divider()

        # --- 1.3 Slab Stiffness (Ks) ---
        st.markdown("#### 1.3 Slab Stiffness ($K_s$)")
        st.markdown("**Reference:** ACI 318-19 Section 8.11.4 (Slab Moment of Inertia)")
        st.write("Stiffness of the slab-beam element based on gross section properties.")
        
        # Variables
        L1_cm = L1 * 100
        L2_cm = L2 * 100
        Is_val = (L2_cm * h_slab**3) / 12
        Ks_theory = (4 * Ec_calc * Is_val) / L1_cm
        
        s_k1, s_k2 = st.columns([1, 1.5])
        with s_k1:
            st.info(f"**Geometry:**\n- Span ($L_1$): {L1_cm} cm\n- Width ($L_2$): {L2_cm} cm\n- Thickness ($h$): {h_slab} cm")
        with s_k2:
            st.markdown("**A) Moment of Inertia ($I_s$):**")
            st.latex(rf"I_s = \frac{{L_2 h^3}}{{12}} = \frac{{{L2_cm:.0f} \cdot {h_slab}^3}}{{12}} = {Is_val:,.0f} \, cm^4")
            
            st.markdown("**B) Stiffness ($K_s$):**")
            st.latex(rf"K_s = \frac{{4 E_c I_s}}{{L_1}} = \frac{{4 \cdot {Ec_calc:,.0f} \cdot {Is_val:,.0f}}}{{{L1_cm}}} \approx {Ks_theory:,.0f} \, kg\cdot cm")
        
        st.success(f"📌 **Result:** $K_s$ (Slab) = **{Ks_val/1e5:.3f} $\times 10^5$** kg-cm")

        st.divider()

        # --- 1.4 Equivalent Stiffness (Kec) ---
        st.markdown("#### 1.4 Equivalent Stiffness ($K_{ec}$)")
        st.markdown("**Reference:** ACI 318-19 Section 8.11.5 (Equivalent Column)")
        st.markdown("""
        In the Equivalent Frame Method, the column stiffness is reduced to account for the torsional flexibility 
        of the slab-to-column connection.
        """)
        
        
        # Torsional Stiffness Kt
        st.markdown("**1) Torsional Stiffness ($K_t$):**")
        st.caption("Represents the torsional resistance of the slab strip attached to the column.")
        st.latex(r"K_t = \sum \frac{9 E_{cs} C}{L_2 (1 - c_2/L_2)^3} \quad \text{[ACI 318 Eq. 8.11.5]}")
        st.code(f"Calculated Kt = {Kt_val:,.0f} kg-cm (Computed internally)", language="markdown")
        
        # Equivalent Stiffness Kec
        st.markdown("**2) Combine to Equivalent Stiffness ($K_{ec}$):**")
        st.write("Series combination of Column Stiffness ($\Sigma K_c$) and Torsional Stiffness ($K_t$):")
        
        # Formula
        st.latex(r"\frac{1}{K_{ec}} = \frac{1}{\Sigma K_c} + \frac{1}{K_t}")
        
        # Substitution
        st.latex(rf"\frac{{1}}{{K_{{ec}}}} = \frac{{1}}{{{Sum_Kc:,.0f}}} + \frac{{1}}{{{Kt_val:,.0f}}}")
        
        # Result
        st.latex(rf"K_{{ec}} = \mathbf{{{Kec_val/1e5:.3f} \times 10^5}} \, kg\cdot cm")
        
        # --- Summary for Next Step ---
        st.markdown("---")
        st.markdown("#### 🏁 Final Distribution Factors (DF)")
        st.caption("These factors determine how the unbalanced moment is distributed between Slab and Column.")
        
        df_calc_disp = Ks_val / (Ks_val + Kec_val)
        
        col_res1, col_res2 = st.columns(2)
        with col_res1:
            st.latex(r"DF_{slab} = \frac{K_s}{K_s + K_{ec}}")
        with col_res2:
            st.latex(rf"DF_{{slab}} = \frac{{{Ks_val:.0f}}}{{{Ks_val:.0f} + {Kec_val:.0f}}} = \mathbf{{{df_calc_disp:.3f}}}")

    
    # === TAB 2: MOMENT DISTRIBUTION ===
    with tab2:
        st.subheader("2. Moment Distribution Analysis")
        st.caption("Methodology: Hardy Cross Method & ACI 318-19 Design Moment Corrections")
        
        # --- 2.1 Fixed End Moments (FEM) ---
        st.markdown("#### 2.1 Factored Load & Fixed End Moments (FEM)")
        st.markdown("**Reference:** Mechanics of Materials / Structural Analysis (Prismatic Beam Formulas)")
        st.write("First, convert the area load ($q_u$) into a line load ($w_u$) acting on the equivalent frame.")

        col_load1, col_load2 = st.columns([1, 1.5])
        
        # 1. Line Load Calc
        w_line_val = w_u * L2  # kg/m
        
        with col_load1:
            st.info(f"**Load Parameters:**\n- Area Load ($q_u$): {w_u} kg/m²\n- Frame Width ($l_2$): {L2} m\n- Span ($l_1$): {L1} m")
        with col_load2:
            st.markdown("**A) Factored Line Load ($w_u$):**")
            st.latex(rf"w_u = q_u \times l_2 = {w_u} \times {L2} = \mathbf{{{w_line_val:,.0f}}} \, kg/m")

        # 2. FEM Calc
        fem_val = (w_line_val * L1**2) / 12.0
        
        st.markdown("**B) Fixed End Moment (FEM):**")
        st.write("Assuming both ends are initially fixed:")
        
        st.latex(rf"FEM = \frac{{w_u l_1^2}}{{12}} = \frac{{{w_line_val:,.0f} \cdot {L1}^2}}{{12}} = \mathbf{{{fem_val:,.0f}}} \, kg\cdot m")
        
        st.divider()

        # --- 2.2 Hardy Cross Method ---
        st.markdown("#### 2.2 Moment Distribution (Hardy Cross Method)")
        st.markdown("**Reference:** Cross, H. (1930). *Analysis of Continuous Frames by Distributing Fixed-End Moments.*")
        st.write("Iterative process to balance moments at joints based on stiffness.")

        # Display Distribution Factor
        st.markdown("**Distribution Factor (DF):**")
        st.latex(rf"DF = \frac{{K_{{member}}}}{{\Sigma K_{{joint}}}} \Rightarrow DF_{{slab}} = \mathbf{{{DF_slab:.3f}}}")
        
        st.markdown("**Iteration Table:**")
        st.caption("Sign Convention: Counter-Clockwise (CCW) is Positive (+).")
        
        # Show the dataframe created in the main logic
        st.dataframe(
            df_iter.style.format({
                "Joint A": "{:,.0f}", 
                "Joint B": "{:,.0f}"
            }), 
            use_container_width=True
        )

        # Result from distribution
        st.success(f"📌 **Centerline Moment ($M_{{cen}}$):** {abs(M_final_L):,.0f} kg-m")
        
        st.divider()

        # --- 2.3 Face of Support Correction ---
        st.markdown("#### 2.3 Design Moment Correction (Face of Support)")
        st.markdown("**Reference:** ACI 318-19 Section 8.11.6 (Moments at face of support)")
        st.markdown("""
        Code permits the design moment to be taken at the face of the support (column) rather than the centerline.
        This reduction is critical for economical design.
        """)
        
        
        # Variables for Correction
        c1_m = c1_w / 100.0  # Support width in direction of analysis
        Vu_val = w_line_val * L1 / 2.0  # Shear at support
        M_correction_val = Vu_val * (c1_m / 2.0) - (w_line_val * (c1_m / 2.0)**2) / 2.0
        
        c_cor1, c_cor2 = st.columns([1, 1.5])
        
        with c_cor1:
            st.info(f"**Support Geometry:**\n- Column Width ($c_1$): {c1_m:.2f} m\n- Distance to Face ($c_1/2$): {c1_m/2.0:.3f} m")
            st.metric("Shear Force ($V_u$)", f"{Vu_val:,.0f} kg")
        
        with c_cor2:
            st.markdown("**Correction Formula:**")
            st.latex(r"M_{face} = M_{cen} - V_u \left(\frac{c_1}{2}\right) + \frac{w_u (c_1/2)^2}{2}")
            
            st.markdown("**Calculation:**")
            st.latex(rf"\Delta M = {Vu_val:,.0f}({c1_m/2:.2f}) - \frac{{{w_line_val:,.0f}({c1_m/2:.2f})^2}}{{2}}")
            st.latex(rf"\Delta M = \mathbf{{{M_correction_val:,.0f}}} \, kg\cdot m")

        # Final Negative Moment
        M_neg_final = abs(M_final_L) - M_correction_val
        st.error(f"🔴 **Design Negative Moment ($M_{{u,neg}}$):** {abs(M_final_L):,.0f} - {M_correction_val:,.0f} = **{M_neg_final:,.0f}** kg-m")

        st.divider()
        
        # --- 2.4 Positive Moment ---
        st.markdown("#### 2.4 Positive Moment Calculation")
        st.markdown("**Reference:** Static Equilibrium ($M_o = wL^2/8$)")
        st.write("The positive moment is derived by subtracting the average negative moment from the simple span moment.")
        
        # Simple Span Moment
        Mo_val = (w_line_val * L1**2) / 8.0
        
        # Pos Moment Calculation
        # M_pos = Mo - (M_neg_avg)
        # Using the design negative moment for the envelope
        M_pos_calc = Mo_val - M_neg_final 
        
        col_pos1, col_pos2 = st.columns(2)
        with col_pos1:
            st.markdown("**Static Moment ($M_o$):**")
            st.latex(rf"M_o = \frac{{w_u l_1^2}}{{8}} = \mathbf{{{Mo_val:,.0f}}} \, kg\cdot m")
        
        with col_pos2:
            st.markdown("**Design Positive Moment ($M_{u,pos}$):**")
            st.latex(r"M_{pos} = M_o - M_{neg,face}")
            st.latex(rf"M_{{pos}} = {Mo_val:,.0f} - {M_neg_final:,.0f} = \mathbf{{{M_pos_calc:,.0f}}} \, kg\cdot m")
            
        st.info(f"🔵 **Design Positive Moment ($M_{{u,pos}}$):** **{M_pos_calc:,.0f}** kg-m")
        
        # Final Visual
        st.markdown("---")
        st.pyplot(plot_moment_envelope(L1, -M_neg_final, -M_neg_final, M_pos_calc, c1_w))
 

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
