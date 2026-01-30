import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# --- Settings ---
plt.rcParams.update({
    'font.family': 'sans-serif', 'font.size': 10,
    'axes.spines.top': False, 'axes.spines.right': False,
    'axes.grid': True, 'grid.alpha': 0.3, 'figure.autolayout': True
})

# ==========================================
# 1. CORE LOGIC: MOMENT DISTRIBUTION
# ==========================================

def run_moment_distribution(FEM_L, FEM_R, DF_L, DF_R, iterations=4):
    """
    Simulate Hardy Cross Loop for a single span with two joints.
    Left Joint (A) -- Slab (AB) -- Right Joint (B)
    """
    # History Log
    history = []
    
    # Initial State
    M_A_slab = FEM_L  # CCW (+)
    M_B_slab = FEM_R  # CW (-)
    
    # Accumulators for final sum
    Total_MA = 0
    Total_MB = 0
    
    # Add Initial Row
    history.append({
        "Step": "1. FEM (Fixed End)",
        "Joint A (Slab)": M_A_slab,
        "Joint B (Slab)": M_B_slab,
        "Action": "Initial Load"
    })
    
    Total_MA += M_A_slab
    Total_MB += M_B_slab

    # Iterative Loop
    bal_A = 0
    bal_B = 0
    
    curr_unbal_A = M_A_slab # Simplified: Assume Col Moment is 0 initially or balanced by structure
    curr_unbal_B = M_B_slab
    
    # For a single span isolated analysis (Simplified EFM):
    # We balance the slab moment against the column stiffness.
    # Unbalanced Moment = M_slab (since column has 0 load initially)
    
    # Correction: The logic needs to handle the residual moment
    m_resid_A = M_A_slab
    m_resid_B = M_B_slab

    for i in range(iterations):
        # --- 1. BALANCE ---
        # At Joint A: Unbalanced = m_resid_A. We need to distribute -Unbal * DF_slab
        # Note: DF_slab is the portion going back into the slab.
        dist_A = -1 * m_resid_A * DF_L
        dist_B = -1 * m_resid_B * DF_R
        
        history.append({
            "Step": f"Iter {i+1}: Balance (x -DF)",
            "Joint A (Slab)": dist_A,
            "Joint B (Slab)": dist_B,
            "Action": f"Distribute: M x -DF"
        })
        
        Total_MA += dist_A
        Total_MB += dist_B
        
        # --- 2. CARRY OVER (CO) ---
        co_to_A = dist_B * 0.5
        co_to_B = dist_A * 0.5
        
        history.append({
            "Step": f"Iter {i+1}: Carry Over (CO)",
            "Joint A (Slab)": co_to_A,
            "Joint B (Slab)": co_to_B,
            "Action": "CO = M_bal x 0.5"
        })
        
        Total_MA += co_to_A
        Total_MB += co_to_B
        
        # Prepare for next loop
        m_resid_A = co_to_A
        m_resid_B = co_to_B

    # Summary Row
    history.append({
        "Step": "🏁 Final Design Moment",
        "Joint A (Slab)": Total_MA,
        "Joint B (Slab)": Total_MB,
        "Action": "Sum All"
    })
    
    return pd.DataFrame(history), Total_MA, Total_MB

# ==========================================
# 2. VISUALIZATION FUNCTIONS
# ==========================================

def plot_stick_model(Ks, Kc_sum, Kt, Kec):
    fig, ax = plt.subplots(figsize=(6, 2.5))
    ax.axhline(0, color='black', linewidth=1) 
    ax.plot([0, 0], [-1, 1], color='gray', linewidth=3, alpha=0.3)
    ax.plot([0.2, 0.2], [-0.2, 0.2], color='orange', lw=2, linestyle='--')
    ax.text(0.25, 0, f"Torsion ($K_t$)\n{Kt/1e5:.1f}E5", color='orange', va='center', fontsize=8)
    ax.text(-0.5, 0.1, f"Slab ($K_s$)\n{Ks/1e5:.1f}E5", ha='center', color='blue', fontsize=8)
    ax.text(-0.1, 0.8, f"Col\n{Kc_sum/2e5:.1f}E5", ha='right', color='gray', fontsize=8)
    ax.annotate(f"Joint $K_{{ec}}$\n= {Kec/1e5:.1f}E5", xy=(0, 0), xytext=(0.6, 0.5),
                arrowprops=dict(facecolor='green', shrink=0.05), fontsize=9, fontweight='bold', color='green', ha='center')
    ax.set_xlim(-1.2, 1.2); ax.set_ylim(-1.2, 1.2); ax.axis('off')
    return fig

def plot_moment_envelope(L1, M_neg_L, M_neg_R, M_pos, c1_cm):
    fig, ax = plt.subplots(figsize=(8, 3))
    x = np.linspace(0, L1, 200)
    # Generate simplified curve based on 3 points
    M_x = np.zeros_like(x)
    for i, xi in enumerate(x):
        # Hermite-like interpolation or simple blending
        t = xi / L1
        # Linear interp of ends
        M_base = (1-t)*(-abs(M_neg_L)) + t*(-abs(M_neg_R))
        # Add Parabola bump
        w_fake = 8 * M_pos / L1**2 # Approximate
        M_bump = 4 * (M_pos + (abs(M_neg_L)+abs(M_neg_R))/2) * t * (1-t) 
        M_x[i] = M_base + M_bump

    ax.fill_between(x, M_x, 0, where=(M_x>0), color='#3498DB', alpha=0.2)
    ax.fill_between(x, M_x, 0, where=(M_x<0), color='#E74C3C', alpha=0.2)
    ax.plot(x, M_x, color='#2C3E50', lw=2)
    
    c1_m = c1_cm / 100
    ax.axvspan(-c1_m/2, c1_m/2, color='gray', alpha=0.3)
    ax.axvspan(L1-c1_m/2, L1+c1_m/2, color='gray', alpha=0.3)
    ax.axhline(0, color='black', lw=0.8)

    ax.text(0, -abs(M_neg_L), f"{M_neg_L:,.0f}", ha='right', color='red', fontweight='bold')
    ax.text(L1, -abs(M_neg_R), f"{M_neg_R:,.0f}", ha='left', color='red', fontweight='bold')
    ax.text(L1/2, M_pos, f"{M_pos:,.0f}", ha='center', va='bottom', color='blue', fontweight='bold')
    
    ax.invert_yaxis()
    ax.set_ylabel("Moment (kg-m)"); ax.set_xlabel("Span (m)")
    ax.set_title("Resulting Moment Envelope", fontweight='bold')
    return fig

def draw_section_detail(b_cm, h_cm, num_bars, d_bar, title):
    fig, ax = plt.subplots(figsize=(5, 2.0))
    ax.add_patch(patches.Rectangle((0, 0), b_cm, h_cm, facecolor='#E0E0E0', edgecolor='#333333'))
    cover = 2.5; dia_cm = d_bar / 10
    y_pos = h_cm - cover - dia_cm/2 if "Top" in title else cover + dia_cm/2
    space = (b_cm - 2*cover - dia_cm) / (num_bars - 1) if num_bars > 1 else 0
    for i in range(num_bars):
        x = cover + dia_cm/2 + i*space if num_bars > 1 else b_cm/2
        ax.add_patch(patches.Circle((x, y_pos), dia_cm/2, fc='red', ec='black'))
    ax.text(b_cm/2, h_cm/2, f"{num_bars}-DB{d_bar}", ha='center', fontweight='bold', color='darkred', fontsize=12)
    ax.set_title(title, fontsize=10); ax.axis('equal'); ax.axis('off')
    return fig

# ==========================================
# 3. MAIN RENDER
# ==========================================
def render(c1_w, c2_w, L1, L2, lc, h_slab, fc, mat_props, w_u, col_type, **kwargs):
    
    st.markdown("### 🏗️ EFM Analysis: Moment Distribution Method")
    st.markdown("---")

    # --- CALCULATION PREP ---
    Ec = 15100 * np.sqrt(fc); E_ksm = Ec * 10000
    # 1. Stiffness
    Ic_m4 = ((c2_w/100) * (c1_w/100)**3) / 12
    Is_m4 = (L2 * (h_slab/100)**3) / 12
    Kc = 4 * E_ksm * Ic_m4 / lc; Sum_Kc = 2 * Kc
    Ks = 4 * E_ksm * Is_m4 / L1
    
    # Torsion
    x_t, y_t = h_slab, c1_w
    C_val = (1 - 0.63 * x_t/y_t) * (x_t**3 * y_t) / 3
    C_m4 = C_val / (100**4)
    Kt = 2 * 9 * E_ksm * C_m4 / (L2 * (1 - (c2_w/100)/L2)**3)
    Kec = 1 / (1/Sum_Kc + 1/Kt)
    
    # 2. Distribution Factors (DF)
    # สมมติโมเดล 2 Joints: Joint A (Left) - Joint B (Right)
    # ถ้า col_type = corner -> Joint A อาจเป็น Exterior (Stiffness น้อยกว่า)
    # แต่เพื่อ demo EFM ที่ชัดเจน สมมติว่าเป็นเสาต้นเดียวกันทั้ง 2 ฝั่งเพื่อดูสมมาตร หรือปรับตาม col_type
    
    # DF Slab at Joint A (Left)
    Sum_K_A = Ks + Kec
    DF_A_slab = Ks / Sum_K_A  # ส่วนที่เด้งกลับเข้าพื้น
    DF_A_col = Kec / Sum_K_A  # ส่วนที่ถ่ายลงเสา
    
    # DF Slab at Joint B (Right) - Assume same col for simplicity unless specified
    DF_B_slab = DF_A_slab 
    DF_B_col = DF_A_col

    # 3. FEM Calculation
    w_line = w_u * L2
    FEM = w_line * L1**2 / 12
    
    # --- UI DASHBOARD ---
    col1, col2 = st.columns([1.5, 1])
    with col1: st.pyplot(plot_stick_model(Ks, Sum_Kc, Kt, Kec))
    with col2:
        st.info("📊 **Stiffness & D.F.**")
        st.write(f"- $K_s$ (Slab): {Ks/1e5:.2f}E5")
        st.write(f"- $K_{{ec}}$ (Col+Tor): {Kec/1e5:.2f}E5")
        st.metric("Distribution Factor (DF)", f"{DF_A_slab:.3f}", help="DF ของพื้นเทียบกับจุดต่อรวม (Ks / ΣK)")

    # --- TABS ---
    t1, t2, t3 = st.tabs(["1️⃣ Moment Distribution (Loop)", "2️⃣ Diagram & Result", "3️⃣ Reinforcement"])

    # === TAB 1: MOMENT DISTRIBUTION LOOP ===
    with t1:
        st.markdown("#### 🔄 Cross Method Iteration")
        st.markdown("กระบวนการกระจายโมเมนต์จนกว่าจะสมดุล (Balancing & Carry Over)")
        
        # Explain Formulas
        c_f1, c_f2 = st.columns(2)
        with c_f1:
            st.latex(r"M_{bal} = - (M_{unbalanced} \times DF_{slab})")
            st.caption("คูณ DF แล้วกลับเครื่องหมายเพื่อต้านแรง")
        with c_f2:
            st.latex(r"M_{carry} = M_{bal} \times 0.5")
            st.caption("ส่งแรงไปปลายอีกด้าน 50% (CO)")
            
        # Run Calculation
        # FEM Left is + (CCW), Right is - (CW)
        df_dist, M_final_L, M_final_R = run_moment_distribution(FEM, -FEM, DF_A_slab, DF_B_slab)
        
        # Display Table
        st.dataframe(df_dist.style.format({
            "Joint A (Slab)": "{:,.0f}", 
            "Joint B (Slab)": "{:,.0f}"
        }), use_container_width=True)
        
        st.write(f"**Note:** FEM เริ่มต้น = {FEM:,.0f} kg-m")

    # === TAB 2: DIAGRAM ===
    with t2:
        # Face Correction
        Vu = w_line * L1 / 2
        M_red = Vu * (c1_w/200) - w_line*(c1_w/200)**2 / 2
        
        # Final Design Moments
        M_neg_L_face = abs(M_final_L) - M_red
        M_neg_R_face = abs(M_final_R) - M_red
        
        # Simple Approx for Positive Moment based on statics
        Mo = w_line * L1**2 / 8
        M_pos_mid = Mo - (M_neg_L_face + M_neg_R_face)/2 

        st.markdown("#### Final Moment Envelope")
        st.pyplot(plot_moment_envelope(L1, -M_neg_L_face, -M_neg_R_face, M_pos_mid, c1_w))
        
        st.info(f"**Design Moments (at Face):**\n\n"
                f"🔴 $M^{{-}}_{{L}}$ = {M_neg_L_face:,.0f} kg-m\n\n"
                f"🔵 $M^{{+}}_{{Mid}}$ = {M_pos_mid:,.0f} kg-m")

    # === TAB 3: DESIGN ===
    with t3:
        # Design Params
        d_eff = h_slab - 2.5 - (mat_props.get('d_bar', 12)/20)
        
        # Function
        def get_rebar(Mu_kgm, b_m):
            Mu = Mu_kgm * 100; b = b_m * 100
            Rn = Mu / (0.9 * b * d_eff**2)
            try: rho = (0.85*fc/mat_props['fy'])*(1 - np.sqrt(1 - 2*Rn/(0.85*fc)))
            except: rho = 0.002
            rho = max(rho, 0.0018)
            As = rho * b * d_eff
            num = int(np.ceil(As / (np.pi*(mat_props['d_bar']/20)**2 / 4)))
            return num, As
            
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            st.markdown("**Column Strip (Top)**")
            num, As = get_rebar(M_neg_L_face * 0.75, L2/2)
            st.write(f"Moment: {M_neg_L_face*0.75:,.0f}, As: {As:.2f}")
            st.pyplot(draw_section_detail(L2*50, h_slab, num, mat_props['d_bar'], "CS Top"))
            
        with col_d2:
            st.markdown("**Middle Strip (Bottom)**")
            num, As = get_rebar(M_pos_mid * 0.60, L2/2)
            st.write(f"Moment: {M_pos_mid*0.60:,.0f}, As: {As:.2f}")
            st.pyplot(draw_section_detail(L2*50, h_slab, num, mat_props['d_bar'], "MS Bot"))
