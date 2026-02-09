# tab_efm.py
import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import calculations as calc  # เชื่อมต่อกับ The Brain V2.0

# --- Settings for Professional Plots ---
plt.rcParams.update({
    'font.family': 'sans-serif', 'font.size': 10,
    'axes.spines.top': False, 'axes.spines.right': False,
    'axes.grid': True, 'grid.alpha': 0.3, 'figure.autolayout': True
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
        t = xi / L1
        # Linear interpolation of end moments
        M_base = (1-t)*(-abs(M_neg_L)) + t*(-abs(M_neg_R))
        # Parabolic hump (approximate wL^2/8 shape added)
        M_mid_diff = M_pos - M_base 
        M_bump = 4 * (M_pos + (abs(M_neg_L)+abs(M_neg_R))/2) * t * (1-t) 
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
    num_bars = int((b_cm - 2*cover) / spacing) + 1
    if num_bars < 2: num_bars = 2
    
    # Re-distribute strictly for visual centering
    real_span = (num_bars - 1) * spacing
    start_x = (b_cm - real_span) / 2
    
    xs = [start_x + i*spacing for i in range(num_bars)]
        
    for x in xs:
        if 0 < x < b_cm: # Draw only if inside section
            ax.add_patch(patches.Circle((x, y_pos), dia_cm/2, fc='red', ec='black'))
            
    label_text = f"DB{db}@{spacing:.0f}cm" if db > 9 else f"RB{db}@{spacing:.0f}cm"
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
    d_eff = h_slab - cover - (db/20.0) # Assumed outer layer for simplicity or avg
    Mu_kgcm = Mu_kgm * 100.0
    phi = 0.90
    
    # 1. Required Steel
    Rn = Mu_kgcm / (phi * b_cm * d_eff**2)
    rho_req = 0.0018 # Min
    
    term = 1 - (2 * Rn) / (0.85 * fc)
    if term >= 0:
        rho_calc = (0.85 * fc / fy) * (1 - np.sqrt(term))
        rho_req = max(rho_calc, 0.0018)
    else:
        rho_req = 999 # Fail section
        
    As_req = rho_req * b_cm * d_eff
    
    # 2. Provided Steel
    bar_area = 3.1416 * (db/10.0)**2 / 4.0
    As_prov = (b_cm / spacing) * bar_area
    
    # 3. Capacity
    a = (As_prov * fy) / (0.85 * fc * b_cm)
    Mn = As_prov * fy * (d_eff - a/2.0)
    PhiMn = 0.90 * Mn / 100.0 # kg-m
    
    dc_ratio = Mu_kgm / PhiMn if PhiMn > 0 else 999
    
    return {
        "d": d_eff,
        "As_req": As_req,
        "As_prov": As_prov,
        "PhiMn": PhiMn,
        "Ratio": dc_ratio,
        "Pass": dc_ratio <= 1.0
    }

# ==========================================
# 4. MAIN RENDER FUNCTION
# ==========================================
def render(c1_w, c2_w, L1, L2, lc, h_slab, fc, mat_props, w_u, col_type, **kwargs):
    
    st.markdown("### 🏗️ Full EFM Analysis: Stiffness to Design")
    st.caption("Equivalent Frame Method with Detailed Step-by-Step Calculation")
    st.markdown("---")

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
        st.error("Cannot find 'calculate_stiffness' in calculations.py. Please ensure the file is updated.")
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
    M_red = Vu_frame * (c1_m/2.0) - w_line*(c1_m/2.0)**2 / 2.0
    
    M_neg_design = abs(M_final_L) - M_red
    
    # Calculate Positive Moment (Statics)
    # Mo = wL^2/8
    Mo = w_line * L1**2 / 8.0
    # M_pos = Mo - (M_neg_L + M_neg_R)/2
    M_pos_design = Mo - M_neg_design # assuming symmetry for this module check

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

    # === TAB 1: STIFFNESS ===
    with tab1:
        st.markdown("#### 1.1 Column Stiffness ($K_c$)")
        Ic_cm4 = (c2_w * c1_w**3) / 12
        st.write(f"Column Moment of Inertia $I_c = {Ic_cm4:,.0f} \, cm^4$")
        st.latex(rf"K_c = \frac{{4EI_c}}{{l_c}}")
        st.latex(rf"\Sigma K_c = {Sum_Kc/1e5:.2f} \times 10^5 \quad (Top + Bot)")
        
        st.divider()
        st.markdown("#### 1.2 Slab Stiffness ($K_s$)")
        Is_cm4 = (L2*100 * h_slab**3) / 12
        st.write(f"Slab Moment of Inertia $I_s = {Is_cm4:,.0f} \, cm^4$")
        st.latex(rf"K_s = \frac{{4EI_s}}{{L_1}} = {Ks_val/1e5:.2f} \times 10^5")

        st.divider()
        st.markdown("#### 1.3 Equivalent Stiffness ($K_{ec}$)")
        st.write("Torsional Stiffness Calculation ($K_t$):")
        st.latex(rf"K_t = {Kt_val/1e5:.2f} \times 10^5")
        st.write("Equivalent Column Stiffness ($K_{ec}$):")
        st.latex(rf"\frac{{1}}{{K_{{ec}}}} = \frac{{1}}{{\Sigma K_c}} + \frac{{1}}{{K_t}} \Rightarrow K_{{ec}} = \mathbf{{{Kec_val/1e5:.2f} \times 10^5}}")

    # === TAB 2: MOMENT ===
    with tab2:
        st.markdown("#### 2.1 Fixed End Moment (FEM)")
        st.latex(rf"w = {w_line:,.0f} \, kg/m")
        st.latex(rf"FEM = \frac{{w L_1^2}}{{12}} = \mathbf{{{FEM:,.0f}}} \, kg\cdot m")
        
        st.markdown("#### 2.2 Moment Distribution Table (Hardy Cross)")
        st.dataframe(df_iter.style.format({"Joint A": "{:,.0f}", "Joint B": "{:,.0f}"}), use_container_width=True)

        st.markdown("#### 2.3 Design Moment Envelope")
        st.write("Face Correction Moment:")
        st.latex(rf"M_{{design}} = {abs(M_final_L):,.0f} - {M_red:,.0f} = \mathbf{{{M_neg_design:,.0f}}} \, kg\cdot m")
        st.pyplot(plot_moment_envelope(L1, -M_neg_design, -M_neg_design, M_pos_design, c1_w))

    # === TAB 3: DESIGN ===
    with tab3:
        st.markdown("#### 🛡️ Reinforcement Design Check")
        st.caption(f"Using materials: fc'={fc} ksc, fy={fy} ksc")
        
        # 1. Get Config from Mat Props (or default)
        cfg = mat_props.get('rebar_cfg', {})
        
        # 2. Define Strip Widths
        w_cs = min(L1, L2) / 2.0
        w_ms = L2 - w_cs
        
        # 3. Design Loop (4 Zones)
        zones = [
            {
                "Name": "Column Strip - Top (-)", 
                "Mu": M_neg_design * 0.75, "Width": w_cs, 
                "db": cfg.get('cs_top_db', 12), "spa": cfg.get('cs_top_spa', 20)
            },
            {
                "Name": "Column Strip - Bot (+)", 
                "Mu": M_pos_design * 0.60, "Width": w_cs, 
                "db": cfg.get('cs_bot_db', 12), "spa": cfg.get('cs_bot_spa', 20)
            },
            {
                "Name": "Middle Strip - Top (-)", 
                "Mu": M_neg_design * 0.25, "Width": w_ms, 
                "db": cfg.get('ms_top_db', 12), "spa": cfg.get('ms_top_spa', 20)
            },
            {
                "Name": "Middle Strip - Bot (+)", 
                "Mu": M_pos_design * 0.40, "Width": w_ms, 
                "db": cfg.get('ms_bot_db', 12), "spa": cfg.get('ms_bot_spa', 20)
            }
        ]
        
        # 4. Process and Display
        results = []
        for z in zones:
            res = calculate_capacity_check(z['Mu'], z['Width'], h_slab, cover, fc, fy, z['db'], z['spa'])
            z.update(res)
            results.append(z)
            
        # Display as Grid
        c1, c2 = st.columns(2)
        
        for i, z in enumerate(results):
            # Select Column
            with (c1 if i % 2 == 0 else c2):
                # Status Color
                color = "green" if z['Pass'] else "red"
                icon = "✅" if z['Pass'] else "❌"
                
                st.markdown(f"**{z['Name']}**")
                st.info(f"Using: **DB{z['db']}@{z['spa']}cm**")
                
                # Plot Section
                st.pyplot(draw_section_detail(z['Width']*100, h_slab, z['db'], z['spa'], z['Name']))
                
                # Metrics
                m1, m2 = st.columns(2)
                m1.write(f"$M_u$: {z['Mu']:,.0f}")
                m2.write(f"$\\phi M_n$: {z['PhiMn']:,.0f}")
                
                # Check
                st.write(f"Required $A_s$: {z['As_req']:.2f} cm² | Provided: {z['As_prov']:.2f} cm²")
                st.markdown(f"Ratio: {z['Ratio']:.2f} ... :{color}[**{icon} { 'PASS' if z['Pass'] else 'FAIL' }**]")
                st.divider()

        # Summary Table
        st.markdown("#### 📋 Summary Table")
        df_res = pd.DataFrame(results)[['Name', 'Mu', 'PhiMn', 'As_req', 'As_prov', 'Ratio']]
        
        # Updated: Format specific columns only to avoid String error
        st.dataframe(df_res.style.format({
            'Mu': "{:,.2f}", 
            'PhiMn': "{:,.2f}", 
            'As_req': "{:,.2f}", 
            'As_prov': "{:,.2f}", 
            'Ratio': "{:,.2f}"
        }), use_container_width=True)
