import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# --- Settings ---
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
# 1. VISUALIZATION FUNCTIONS (ดึงรูปกลับมาครบถ้วน)
# ==========================================

def plot_stick_model(Ks, Sum_Kc, Kt, Kec):
    """วาด Diagram โมเดลโครงสร้าง (Stick Model)"""
    fig, ax = plt.subplots(figsize=(6, 2.5))
    ax.axhline(0, color='black', linewidth=1) 
    ax.plot([0, 0], [-1, 1], color='gray', linewidth=3, alpha=0.3)
    ax.plot([0.2, 0.2], [-0.2, 0.2], color='orange', lw=2, linestyle='--')
    ax.text(0.25, 0, f"Torsion ($K_t$)\n{Kt/1e5:.1f}E5", color='orange', va='center', fontsize=8)
    ax.text(-0.5, 0.1, f"Slab ($K_s$)\n{Ks/1e5:.1f}E5", ha='center', color='blue', fontsize=8)
    ax.text(-0.1, 0.8, f"Col (Sum)\n{Sum_Kc/1e5:.1f}E5", ha='right', color='gray', fontsize=8)
    ax.annotate(f"Joint $K_{{ec}}$\n= {Kec/1e5:.1f}E5", xy=(0, 0), xytext=(0.6, 0.5),
                arrowprops=dict(facecolor='green', shrink=0.05), fontsize=9, fontweight='bold', color='green', ha='center')
    ax.set_xlim(-1.2, 1.2); ax.set_ylim(-1.2, 1.2); ax.axis('off')
    return fig

def plot_moment_envelope(L1, M_neg_L, M_neg_R, M_pos, c1_cm):
    """วาดกราฟโมเมนต์"""
    fig, ax = plt.subplots(figsize=(8, 3))
    x = np.linspace(0, L1, 200)
    M_x = np.zeros_like(x)
    for i, xi in enumerate(x):
        # เทคนิค Blending สร้างกราฟให้สมจริง
        t = xi / L1
        M_base = (1-t)*(-abs(M_neg_L)) + t*(-abs(M_neg_R))
        M_bump = 4 * (M_pos + (abs(M_neg_L)+abs(M_neg_R))/2) * t * (1-t) 
        M_x[i] = M_base + M_bump

    ax.fill_between(x, M_x, 0, where=(M_x>0), color='#3498DB', alpha=0.2)
    ax.fill_between(x, M_x, 0, where=(M_x<0), color='#E74C3C', alpha=0.2)
    ax.plot(x, M_x, color='#2C3E50', lw=2)
    
    c1_m = c1_cm / 100
    ax.axvspan(-c1_m/2, c1_m/2, color='gray', alpha=0.3)
    ax.axvspan(L1-c1_m/2, L1+c1_m/2, color='gray', alpha=0.3)
    ax.axhline(0, color='black', lw=0.8)

    ax.text(0, -abs(M_neg_L), f"{M_neg_L:,.0f}", ha='right', color='red', fontweight='bold', fontsize=9)
    ax.text(L1, -abs(M_neg_R), f"{M_neg_R:,.0f}", ha='left', color='red', fontweight='bold', fontsize=9)
    ax.text(L1/2, M_pos, f"{M_pos:,.0f}", ha='center', va='bottom', color='blue', fontweight='bold', fontsize=9)
    
    ax.invert_yaxis()
    ax.set_ylabel("Moment (kg-m)"); ax.set_xlabel("Span (m)")
    ax.set_title("Moment Envelope", fontweight='bold')
    return fig

def draw_section_detail(b_cm, h_cm, num_bars, d_bar, title):
    """วาดหน้าตัดคาน"""
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
# 2. LOGIC: MOMENT DISTRIBUTION
# ==========================================

def run_moment_distribution(FEM, DF_slab, iterations=4):
    """
    วนลูปกระจายโมเมนต์ (Hardy Cross)
    """
    history = []
    
    # Init
    M_A = FEM   # CCW (+)
    M_B = -FEM  # CW (-)
    
    history.append({"Step": "1. FEM", "Joint A": M_A, "Joint B": M_B, "Action": "Load"})
    
    curr_unbal_A = M_A 
    curr_unbal_B = M_B
    
    total_A = M_A
    total_B = M_B

    for i in range(iterations):
        # Balance
        bal_A = -1 * curr_unbal_A * DF_slab
        bal_B = -1 * curr_unbal_B * DF_slab
        
        history.append({
            "Step": f"Iter {i+1} Bal", 
            "Joint A": bal_A, "Joint B": bal_B,
            "Action": "Distribute"
        })
        
        total_A += bal_A
        total_B += bal_B
        
        # Carry Over
        co_to_A = bal_B * 0.5
        co_to_B = bal_A * 0.5
        
        history.append({
            "Step": f"Iter {i+1} CO", 
            "Joint A": co_to_A, "Joint B": co_to_B,
            "Action": "Carry Over"
        })
        
        total_A += co_to_A
        total_B += co_to_B
        
        curr_unbal_A = co_to_A
        curr_unbal_B = co_to_B

    history.append({"Step": "🏁 Final", "Joint A": total_A, "Joint B": total_B, "Action": "Sum"})
    return pd.DataFrame(history), total_A, total_B

# ==========================================
# 3. MAIN RENDER FUNCTION
# ==========================================
def render(c1_w, c2_w, L1, L2, lc, h_slab, fc, mat_props, w_u, col_type, **kwargs):
    
    st.markdown("### 🏗️ Full EFM Analysis: Stiffness to Design")
    st.markdown("---")

    # --- A. PRE-CALCULATION ---
    Ec = 15100 * np.sqrt(fc) # ksc
    E_ksm = Ec * 10000 
    
    # 1. Column Stiffness
    Ic_cm4 = (c2_w * c1_w**3) / 12
    Ic_m4 = Ic_cm4 / (100**4)
    Kc_val = 4 * E_ksm * Ic_m4 / lc
    Sum_Kc = 2 * Kc_val 
    
    # 2. Slab Stiffness
    Is_cm4 = (L2*100 * h_slab**3) / 12
    Is_m4 = Is_cm4 / (100**4)
    Ks_val = 4 * E_ksm * Is_m4 / L1
    
    # 3. Torsion Stiffness
    x_t, y_t = h_slab, c1_w
    C_term = (1 - 0.63 * (x_t/y_t))
    C_val = C_term * (x_t**3 * y_t) / 3
    C_m4 = C_val / (100**4)
    Kt_denom = L2 * (1 - (c2_w/100)/L2)**3
    Kt_val = 2 * 9 * E_ksm * C_m4 / Kt_denom 

    # 4. Equivalent Column & DF
    inv_Kec = (1/Sum_Kc) + (1/Kt_val)
    Kec_val = 1/inv_Kec
    Total_K = Ks_val + Kec_val
    DF_slab = Ks_val / Total_K
    
    # 5. FEM & Distribution
    w_line = w_u * L2 
    FEM = w_line * L1**2 / 12
    
    df_iter, M_final_L, M_final_R = run_moment_distribution(FEM, DF_slab)
    
    # 6. Face Correction
    Vu = w_line * L1 / 2
    c1_m = c1_w / 100
    M_red = Vu * (c1_m/2) - w_line*(c1_m/2)**2 / 2
    
    M_neg_design = abs(M_final_L) - M_red
    Mo = w_line * L1**2 / 8
    M_pos_design = Mo - M_neg_design 

    # --- B. DASHBOARD ---
    col1, col2 = st.columns([1.2, 1])
    with col1:
        st.pyplot(plot_stick_model(Ks_val, Sum_Kc, Kt_val, Kec_val))
    with col2:
        st.info("📊 **Analysis Summary**")
        st.write(f"**Slab Stiffness:** {Ks_val/1e5:.2f} E5")
        st.write(f"**Equiv. Column:** {Kec_val/1e5:.2f} E5")
        st.metric("Slab Distribution Factor ($DF$)", f"{DF_slab:.3f}")

    # --- C. TABS ---
    tab1, tab2, tab3 = st.tabs(["1️⃣ Step 1: Stiffness", "2️⃣ Step 2: Moment Dist.", "3️⃣ Step 3: Design"])

    # === TAB 1: STIFFNESS ===
    with tab1:
        st.markdown("#### 1.1 Stiffness Calculation")
        st.latex(rf"I_c = {Ic_cm4:,.0f} \, cm^4, \quad \Sigma K_c = {Sum_Kc/1e5:.2f}E5")
        st.latex(rf"I_s = {Is_cm4:,.0f} \, cm^4, \quad K_s = {Ks_val/1e5:.2f}E5")
        st.latex(rf"C = {C_val:,.0f} \, cm^4, \quad K_t = {Kt_val/1e5:.2f}E5")
        st.success(f"📌 Equivalent Stiffness $K_{{ec}}$ = {Kec_val/1e5:.2f} E5")

    # === TAB 2: MOMENT (FIXED HERE) ===
    with tab2:
        st.markdown("#### 2.1 Iteration Table")
        st.markdown("ตารางแสดงการกระจายโมเมนต์ในแต่ละรอบ:")
        
        # --- FIX: Apply format only to numeric columns ---
        st.dataframe(
            df_iter.style.format({
                "Joint A": "{:,.0f}", 
                "Joint B": "{:,.0f}"
            }), 
            use_container_width=True
        )
        # -----------------------------------------------
        
        st.markdown("#### 2.2 Design Moment (Face Correction)")
        st.latex(rf"M_{{design}} = {abs(M_final_L):,.0f} - {M_red:,.0f} = \mathbf{{{M_neg_design:,.0f}}} \, kg\cdot m")
        st.pyplot(plot_moment_envelope(L1, -M_neg_design, -M_neg_design, M_pos_design, c1_w))

    # === TAB 3: DESIGN ===
    with tab3:
        fy = mat_props.get('fy', 4000)
        d_bar = mat_props.get('d_bar', 12)
        d_eff = h_slab - 2.5 - d_bar/20
        
        def calc_rebar_show(Mu_kgm, b_m):
            Mu = Mu_kgm * 100
            Rn = Mu / (0.9 * (b_m*100) * d_eff**2)
            try: rho = (0.85*fc/fy)*(1 - np.sqrt(max(0, 1 - 2*Rn/(0.85*fc))))
            except: rho = 0.002
            rho = max(rho, 0.0018)
            As = rho * (b_m*100) * d_eff
            num = int(np.ceil(As / (np.pi*(d_bar/20)**2/4)))
            return Rn, rho, As, num

        col_d1, col_d2 = st.columns(2)
        
        with col_d1:
            st.subheader("🔴 Col Strip (Top)")
            Rn, rho, As, num = calc_rebar_show(M_neg_design*0.75, L2/2)
            st.write(f"M: {M_neg_design*0.75:,.0f}, As: {As:.2f}")
            st.pyplot(draw_section_detail(L2*50, h_slab, num, d_bar, "CS Top"))
            
        with col_d2:
            st.subheader("🔵 Mid Strip (Bot)")
            Rn, rho, As, num = calc_rebar_show(M_pos_design*0.60, L2/2)
            st.write(f"M: {M_pos_design*0.60:,.0f}, As: {As:.2f}")
            st.pyplot(draw_section_detail(L2*50, h_slab, num, d_bar, "MS Bot"))
