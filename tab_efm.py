# tab_efm.py
import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches

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
    Visualizes how Column and Torsional member combine into Kec.
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
        M_mid_diff = M_pos - M_base # This logic is approximate for viz
        M_bump = 4 * (M_pos + (abs(M_neg_L)+abs(M_neg_R))/2) * t * (1-t) 
        M_x[i] = M_base + M_bump

    # Fill Areas
    ax.fill_between(x, M_x, 0, where=(M_x>0), color='#3498DB', alpha=0.2)
    ax.fill_between(x, M_x, 0, where=(M_x<0), color='#E74C3C', alpha=0.2)
    ax.plot(x, M_x, color='#2C3E50', lw=2)
    
    # Draw Supports
    c1_m = c1_cm / 100
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

def draw_section_detail(b_cm, h_cm, num_bars, d_bar, title):
    """
    Visualizes the cross-section with rebars.
    """
    fig, ax = plt.subplots(figsize=(5, 2.0))
    # Concrete section
    ax.add_patch(patches.Rectangle((0, 0), b_cm, h_cm, facecolor='#E0E0E0', edgecolor='#333333'))
    
    # Rebars
    cover = 2.5 
    dia_cm = d_bar / 10
    
    # Determine Y position (Top or Bot)
    if "Top" in title:
        y_pos = h_cm - cover - dia_cm/2
    else:
        y_pos = cover + dia_cm/2
        
    # Calculate spacing
    if num_bars > 1:
        space = (b_cm - 2*cover - dia_cm) / (num_bars - 1)
        xs = [cover + dia_cm/2 + i*space for i in range(num_bars)]
    else:
        xs = [b_cm/2]
        
    for x in xs:
        ax.add_patch(patches.Circle((x, y_pos), dia_cm/2, fc='red', ec='black'))
        
    ax.text(b_cm/2, h_cm/2, f"{num_bars}-DB{d_bar}", ha='center', va='center', 
            fontweight='bold', color='darkred', fontsize=12, bbox=dict(facecolor='white', alpha=0.7, edgecolor='none'))
            
    ax.set_title(title, fontsize=10)
    ax.axis('equal')
    ax.axis('off')
    return fig

# ==========================================
# 2. LOGIC: MOMENT DISTRIBUTION (CORE)
# ==========================================

def run_moment_distribution(FEM, DF_slab, iterations=4):
    """
    Simulate Hardy Cross Method:
    - Assumes a simplified single-span equivalent frame for demonstration.
    - Joint A (Left) & Joint B (Right) are interior joints.
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
        # Moment to balance = - (Unbalanced * DF)
        bal_A = -1 * curr_unbal_A * DF_slab
        bal_B = -1 * curr_unbal_B * DF_slab
        
        history.append({
            "Step": f"Iter {i+1}: Balance", 
            "Joint A": bal_A, "Joint B": bal_B,
            "Description": f"Bal = -M_unbal × {DF_slab:.3f}"
        })
        
        total_A += bal_A
        total_B += bal_B
        
        # 3. Carry Over (CO)
        # Carry over to opposite side (Factor 0.5)
        co_to_A = bal_B * 0.5
        co_to_B = bal_A * 0.5
        
        history.append({
            "Step": f"Iter {i+1}: Carry Over", 
            "Joint A": co_to_A, "Joint B": co_to_B,
            "Description": "CO = M_bal × 0.5"
        })
        
        total_A += co_to_A
        total_B += co_to_B
        
        # Update Unbalanced for next loop
        curr_unbal_A = co_to_A
        curr_unbal_B = co_to_B

    history.append({"Step": "🏁 SUM", "Joint A": total_A, "Joint B": total_B, "Description": "Total Moment"})
    return pd.DataFrame(history), total_A, total_B

# ==========================================
# 3. MAIN RENDER FUNCTION
# ==========================================
def render(c1_w, c2_w, L1, L2, lc, h_slab, fc, mat_props, w_u, col_type, **kwargs):
    
    st.markdown("### 🏗️ Full EFM Analysis: Stiffness to Design")
    st.caption("Equivalent Frame Method with Detailed Step-by-Step Calculation")
    st.markdown("---")

    # --- A. PRE-CALCULATION ---
    # Material Properties
    Ec = 15100 * np.sqrt(fc) # ksc
    E_ksm = Ec * 10000  # Convert ksc to kg/m^2 for stiffness calculation
    
    # 1. Stiffness Calculations
    
    # Column Stiffness (Kc)
    # Ic = c2 * c1^3 / 12
    Ic_cm4 = (c2_w * c1_w**3) / 12
    Ic_m4 = Ic_cm4 / (100**4)
    # Kc = 4EI/L (Assume fixed far end for simple module)
    Kc_val = 4 * E_ksm * Ic_m4 / lc
    Sum_Kc = 2 * Kc_val # Top and Bottom columns
    
    # Slab Stiffness (Ks)
    # Is = L2 * h^3 / 12
    Is_cm4 = (L2*100 * h_slab**3) / 12
    Is_m4 = Is_cm4 / (100**4)
    Ks_val = 4 * E_ksm * Is_m4 / L1
    
    # Torsional Stiffness (Kt)
    # C = (1 - 0.63 x/y) * x^3 * y / 3
    x_t = h_slab
    y_t = c1_w # Torsional member width is column width c1
    C_term = (1 - 0.63 * (x_t/y_t))
    C_val = C_term * (x_t**3 * y_t) / 3
    C_m4 = C_val / (100**4)
    
    # Kt = 9E C / [L2(1-c2/L2)^3]
    Kt_denom = L2 * (1 - (c2_w/100)/L2)**3
    if Kt_denom == 0: Kt_denom = 0.001
    Kt_val = 2 * 9 * E_ksm * C_m4 / Kt_denom # x2 for both sides of column
    
    # Equivalent Stiffness (Kec)
    # 1/Kec = 1/Sum_Kc + 1/Kt
    if Kt_val > 0:
        inv_Kec = (1/Sum_Kc) + (1/Kt_val)
        Kec_val = 1/inv_Kec
    else:
        Kec_val = 0 # Should not happen in valid geometry

    # Distribution Factor (DF)
    Total_K = Ks_val + Kec_val
    DF_slab = Ks_val / Total_K
    
    # 2. Moment Analysis
    w_line = w_u * L2 # Load per meter length of frame
    FEM = w_line * L1**2 / 12
    
    # Run Hardy Cross
    df_iter, M_final_L, M_final_R = run_moment_distribution(FEM, DF_slab)
    
    # Face Correction
    # Reduce moment from centerline to face of support
    Vu = w_line * L1 / 2
    c1_m = c1_w / 100
    M_red = Vu * (c1_m/2) - w_line*(c1_m/2)**2 / 2
    
    M_neg_design = abs(M_final_L) - M_red
    
    # Calculate Positive Moment (Statics)
    # Mo = wL^2/8
    Mo = w_line * L1**2 / 8
    # M_pos = Mo - (M_neg_L + M_neg_R)/2
    M_pos_design = Mo - M_neg_design # assuming symmetry for this module

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

    # --- C. DETAILED TABS ---
    tab1, tab2, tab3 = st.tabs(["1️⃣ Step 1: Stiffness", "2️⃣ Step 2: Moment Dist.", "3️⃣ Step 3: Design"])

    # === TAB 1: STIFFNESS ===
    with tab1:
        st.markdown("#### 1.1 Column Stiffness ($K_c$)")
        st.write("โมเมนต์ความเฉื่อยของเสา ($I_c$):")
        st.latex(rf"I_c = \frac{{c_2 c_1^3}}{{12}} = \frac{{{c2_w} \times {c1_w}^3}}{{12}} = {Ic_cm4:,.0f} \, cm^4")
        st.write("ความแข็งของเสา ($K_c$):")
        st.latex(rf"K_c = \frac{{4EI_c}}{{l_c}} = \frac{{4({E_ksm:.2e})({Ic_m4:.2e})}}{{{lc}}} = {Kc_val/1e5:.2f} \times 10^5")
        st.latex(rf"\Sigma K_c = K_{{col,top}} + K_{{col,bot}} = {Sum_Kc/1e5:.2f} \times 10^5")
        
        st.divider()
        st.markdown("#### 1.2 Slab Stiffness ($K_s$)")
        st.latex(rf"I_s = \frac{{L_2 h^3}}{{12}} = \frac{{{L2*100} \times {h_slab}^3}}{{12}} = {Is_cm4:,.0f} \, cm^4")
        st.latex(rf"K_s = \frac{{4EI_s}}{{L_1}} = {Ks_val/1e5:.2f} \times 10^5")

        st.divider()
        st.markdown("#### 1.3 Equivalent Stiffness ($K_{ec}$)")
        st.write("รวมความแข็งเสาและ Torsional Member ($K_t$):")
        st.latex(rf"K_t = {Kt_val/1e5:.2f} \times 10^5 \quad (\text{{calc from }} C = {C_val:.0f} cm^4)")
        st.latex(rf"\frac{{1}}{{K_{{ec}}}} = \frac{{1}}{{\Sigma K_c}} + \frac{{1}}{{K_t}} \Rightarrow K_{{ec}} = \mathbf{{{Kec_val/1e5:.2f} \times 10^5}}")

    # === TAB 2: MOMENT (Highlight) ===
    with tab2:
        st.markdown("#### 2.1 Fixed End Moment (FEM)")
        st.write("คำนวณโมเมนต์ปลายยึดแน่น (สมมติว่าเป็นคานยึดแน่นก่อน):")
        st.latex(rf"w = w_u \times L_2 = {w_u} \times {L2} = {w_line:,.0f} \, kg/m")
        st.latex(rf"FEM = \frac{{w L_1^2}}{{12}} = \frac{{{w_line:,.0f} \times {L1}^2}}{{12}} = \mathbf{{{FEM:,.0f}}} \, kg\cdot m")
        
        st.markdown("#### 2.2 Moment Distribution Table (Hardy Cross)")
        st.write(f"ทำการกระจายโมเมนต์ด้วยค่า **DF = {DF_slab:.3f}** (วนลูป 4 รอบ):")
        
        # Format dataframe for display
        st.dataframe(
            df_iter.style.format({
                "Joint A": "{:,.0f}", 
                "Joint B": "{:,.0f}"
            }), 
            use_container_width=True
        )

        st.markdown("#### 2.3 Face Correction (Design Moment)")
        st.write("ลดค่าโมเมนต์จาก Centerline มาที่ผิวเสา (Face of Support):")
        st.latex(rf"M_{{red}} = \frac{{V c_1}}{{2}} - \frac{{w c_1^2}}{{8}} \approx {M_red:,.0f} \, kg\cdot m")
        st.latex(rf"M_{{design}}^{{-}} = M_{{final}} - M_{{red}} = {abs(M_final_L):,.0f} - {M_red:,.0f} = \mathbf{{{M_neg_design:,.0f}}} \, kg\cdot m")
        
        st.pyplot(plot_moment_envelope(L1, -M_neg_design, -M_neg_design, M_pos_design, c1_w))

    # === TAB 3: DESIGN ===
    with tab3:
        fy = mat_props.get('fy', 4000)
        d_bar = mat_props.get('d_bar', 12)
        d_eff = h_slab - 2.5 - d_bar/20
        
        # Helper inner function for calc
        def calc_rebar_show(Mu_kgm, b_m):
            Mu = Mu_kgm * 100 # kg-cm
            Rn = Mu / (0.9 * (b_m*100) * d_eff**2)
            try:
                rho = (0.85*fc/fy)*(1 - np.sqrt(max(0, 1 - 2*Rn/(0.85*fc))))
            except:
                rho = 0.002 # Fallback
            rho = max(rho, 0.0018)
            As = rho * (b_m*100) * d_eff
            num = int(np.ceil(As / (np.pi*(d_bar/20)**2/4)))
            return Rn, rho, As, num

        st.markdown("#### 3.1 Design Parameters")
        st.write(f"**Material:** $f_c'={fc}$ ksc, $f_y={fy}$ ksc")
        st.write(f"**Depth:** $h={h_slab}$ cm, $d_{{eff}} \\approx {d_eff:.2f}$ cm")

        col_d1, col_d2 = st.columns(2)
        
        with col_d1:
            st.subheader("🔴 Column Strip (Top)")
            # CS takes 75% of Neg Moment
            Mu_cs = M_neg_design * 0.75
            b_cs = L2/2 # Approx width
            Rn, rho, As, num = calc_rebar_show(Mu_cs, b_cs)
            
            st.write(f"**Moment ($75\%$):** {Mu_cs:,.0f} kg-m")
            st.latex(rf"R_n = {Rn:.2f} \to \rho = {rho:.4f}")
            st.latex(rf"A_s = {As:.2f} \, cm^2")
            st.success(f"**Use {num}-DB{d_bar}**")
            st.pyplot(draw_section_detail(b_cs*100, h_slab, num, d_bar, "CS Top"))
            
        with col_d2:
            st.subheader("🔵 Middle Strip (Bot)")
            # MS takes 60% of Pos Moment (Approx for Interior)
            Mu_ms = M_pos_design * 0.60
            b_ms = L2/2
            Rn, rho, As, num = calc_rebar_show(Mu_ms, b_ms)
            
            st.write(f"**Moment ($60\%$):** {Mu_ms:,.0f} kg-m")
            st.latex(rf"R_n = {Rn:.2f} \to \rho = {rho:.4f}")
            st.latex(rf"A_s = {As:.2f} \, cm^2")
            st.success(f"**Use {num}-DB{d_bar}**")
            st.pyplot(draw_section_detail(b_ms*100, h_slab, num, d_bar, "MS Bot"))

    
# เพิ่มต่อท้ายในไฟล์ calculations.py
def check_punching_shear(Vu_kg, fc, h_slab, c1_cm, c2_cm, cover, d_bar_mm):
    """
    ตรวจสอบแรงเฉือนทะลุ (Punching Shear) ตามมาตรฐาน ACI 318
    Vu_kg: แรงเฉือนประลัย (kg)
    fc: กำลังคอนกรีต (ksc)
    """
    # 1. Geometry
    d_bar = d_bar_mm / 10.0 # cm
    d_avg = h_slab - cover - d_bar # Effective depth average (cm)
    
    # 2. Critical Section Perimeter (bo) at d/2
    c1_d = c1_cm + d_avg
    c2_d = c2_cm + d_avg
    bo = 2 * (c1_d + c2_d) # รอบรูปวิกฤต (cm)
    
    # 3. Parameters
    beta = max(c1_cm, c2_cm) / min(c1_cm, c2_cm)
    alpha_s = 40 # สำหรับเสาภายใน (Interior Column)
    
    # 4. Shear Capacity (Vc) - ACI 318 (3 formulas)
    # สูตรหน่วย Metric (kg/cm2) โดยประมาณ: 0.27, 0.53, 1.06 * sqrt(fc)
    # ใช้สูตรมาตรฐาน SDM ไทย (Equivalent to ACI):
    
    # Eq 1: Basic
    Vc1 = 1.06 * np.sqrt(fc) * bo * d_avg
    
    # Eq 2: Rectangularity effect
    Vc2 = 0.27 * (2 + 4/beta) * np.sqrt(fc) * bo * d_avg
    
    # Eq 3: Size effect
    Vc3 = 0.27 * (2 + (alpha_s * d_avg)/bo) * np.sqrt(fc) * bo * d_avg
    
    Vc_nominal = min(Vc1, Vc2, Vc3)
    phi = 0.85 # Strength reduction factor for shear
    phi_Vc = phi * Vc_nominal
    
    # 5. Ratio
    ratio = Vu_kg / phi_Vc
    status = "OK" if ratio <= 1.0 else "FAIL"
    
    return {
        "d_avg": d_avg,
        "bo": bo,
        "Vc_formulas": [Vc1, Vc2, Vc3],
        "Vc_nominal": Vc_nominal,
        "phi_Vc": phi_Vc,
        "Vu": Vu_kg,
        "ratio": ratio,
        "status": status,
        "critical_rect": (c1_d, c2_d) # For plotting
    }
