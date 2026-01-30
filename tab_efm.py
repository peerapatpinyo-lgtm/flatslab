import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# --- Settings & Styles ---
plt.style.use('default')
plt.rcParams.update({
    'font.family': 'sans-serif', 'font.size': 9,
    'axes.spines.top': False, 'axes.spines.right': False,
    'figure.autolayout': True, 'axes.grid': True, 'grid.alpha': 0.3
})

# ==========================================
# 1. VISUALIZATION FUNCTIONS (คงเดิมที่สวยแล้ว)
# ==========================================

def interpret_stiffness(Ks, Kec):
    total_k = Ks + Kec
    if total_k == 0: return "N/A", "N/A", "gray"
    ratio_col = Kec / total_k
    if ratio_col < 0.25:
        return "⚠️ Slab Dominant", "เสาอ่อน/พื้นแข็ง: โมเมนต์ถ่ายเข้าพื้นเยอะ ระวัง Punching Shear", "orange"
    elif ratio_col > 0.65:
        return "💪 Column Dominant", "เสาแข็ง: รับโมเมนต์ได้ดี ช่วยลดการแอ่นตัวของพื้น", "green"
    else:
        return "⚖️ Balanced", "สัดส่วนความแข็งสมดุลดี", "blue"

def plot_moment_envelope_with_values(L1, M_neg_L, M_neg_R, M_pos, c1_cm):
    fig, ax = plt.subplots(figsize=(8, 3))
    x = np.linspace(0, L1, 150)
    M_x = np.zeros_like(x)
    for i, xi in enumerate(x):
        if xi < L1/2:
            factor = (xi / (L1/2))**2
            M_x[i] = -M_neg_L * (1-factor) + M_pos * factor
        else:
            factor = ((L1-xi) / (L1/2))**2
            M_x[i] = -M_neg_R * (1-factor) + M_pos * factor

    ax.fill_between(x, M_x, 0, where=(M_x>0), color='#3498DB', alpha=0.2)
    ax.fill_between(x, M_x, 0, where=(M_x<0), color='#E74C3C', alpha=0.2)
    ax.plot(x, M_x, color='#2C3E50', lw=2)
    
    c1_m = c1_cm / 100
    ax.axvspan(-c1_m/2, c1_m/2, color='gray', alpha=0.3)
    ax.axvspan(L1-c1_m/2, L1+c1_m/2, color='gray', alpha=0.3)
    ax.axhline(0, color='black', lw=1)

    ax.text(c1_m/2, -M_neg_L, f"  {M_neg_L:,.0f}", ha='left', va='center', color='#C0392B', fontweight='bold', fontsize=8)
    ax.text(L1/2, M_pos, f"{M_pos:,.0f}", ha='center', va='bottom', color='#2980B9', fontweight='bold', fontsize=8)

    ax.invert_yaxis()
    ax.set_title("Moment Envelope (kg-m)", loc='left', fontweight='bold', fontsize=10)
    ax.set_xlabel("Span (m)")
    ax.set_xlim(-c1_m, L1+c1_m)
    return fig

def draw_rebar_section(width_cm, height_cm, cover_cm, num_bars, bar_dia_mm, title):
    fig, ax = plt.subplots(figsize=(6, 2.0))
    ax.add_patch(patches.Rectangle((0, 0), width_cm, height_cm, facecolor='#ECF0F1', edgecolor='#7F8C8D', lw=1.5))
    
    bar_dia_cm = bar_dia_mm / 10.0
    eff_width_bars = width_cm - 2*cover_cm - bar_dia_cm
    if num_bars > 1:
        spacing = eff_width_bars / (num_bars - 1)
        x_pos = [cover_cm + bar_dia_cm/2 + i*spacing for i in range(num_bars)]
    elif num_bars == 1:
        x_pos = [width_cm/2]
    else:
        x_pos = []

    y_pos = cover_cm + bar_dia_cm/2 
    for x in x_pos:
        ax.add_patch(patches.Circle((x, y_pos), bar_dia_cm/2, facecolor='#C0392B', edgecolor='black'))
        
    ax.text(width_cm/2, height_cm*1.15, title, ha='center', fontweight='bold', fontsize=10)
    if num_bars > 0:
        ax.text(width_cm/2, y_pos-bar_dia_cm*2, f"{num_bars}-DB{bar_dia_mm}", ha='center', color='#C0392B', fontweight='bold')

    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_ylim(-height_cm*0.3, height_cm*1.4)
    return fig

# ==========================================
# 2. MAIN RENDER FUNCTION
# ==========================================
def render(c1_w, c2_w, L1, L2, lc, h_slab, fc, mat_props, w_u, col_type, **kwargs):
    
    st.markdown("### 🏗️ Equivalent Frame Method (Detailed Analysis)")
    st.markdown("---")

    # --- Calculation Prep ---
    Ec = 15100 * np.sqrt(fc) # ksc
    E_ksm = Ec * 10000 # kg/m2 (for stiffness calc in m units)
    
    # 1. Stiffness Parameters
    # Column
    Ic_cm4 = (c2_w * c1_w**3) / 12
    Ic_m4 = Ic_cm4 / (100**4)
    Kc_abs = 4 * E_ksm * Ic_m4 / lc
    Sum_Kc = 2 * Kc_abs # Above + Below
    
    # Slab
    Is_cm4 = (L2*100 * h_slab**3) / 12
    Is_m4 = Is_cm4 / (100**4)
    Ks_abs = 4 * E_ksm * Is_m4 / L1
    
    # Torsion
    x = min(c1_w, h_slab) # rough approx for rectangular part
    y = max(c1_w, h_slab) # actually should be based on section logic, simplfied here
    # Refine x,y for torsion member (c1 x h)
    x_t, y_t = h_slab, c1_w 
    C_val = (1 - 0.63 * x_t/y_t) * (x_t**3 * y_t) / 3
    C_m4 = C_val / (100**4)
    num_arms = 1 if col_type == 'corner' else 2
    Kt_abs = num_arms * 9 * E_ksm * C_m4 / (L2 * (1 - (c2_w/100)/L2)**3)

    # Equiv Column
    if Kt_abs > 0: Kec_abs = 1 / (1/Sum_Kc + 1/Kt_abs)
    else: Kec_abs = Sum_Kc
    
    # DF
    Sum_K_joint = Ks_abs + Kec_abs
    DF_col = Kec_abs / Sum_K_joint if Sum_K_joint > 0 else 0

    # 2. Moment Design
    w_line = w_u * L2
    Mo = w_line * L1**2 / 8
    
    # Coefficients
    coef_neg = 0.65 if col_type=='interior' else 0.50
    coef_pos = 0.35
    M_neg_CL = Mo * coef_neg
    M_pos_mid = Mo * coef_pos
    
    # Face Correction
    Vu = w_line * L1 / 2
    c1_m = c1_w / 100
    M_red = Vu*(c1_m/2) - w_line*(c1_m/2)**2 / 2
    M_neg_face = M_neg_CL - M_red
    
    # 3. Rebar Prep
    fy = mat_props.get('fy', 4000)
    d_bar = mat_props.get('d_bar', 12)
    cover = mat_props.get('cover', 2.5)
    d_eff = h_slab - cover - (d_bar/20)

    # --- PART 1: DASHBOARD (Clean Visuals) ---
    status, advice, color = interpret_stiffness(Ks_abs, Kec_abs)
    
    c1, c2, c3 = st.columns([1, 1, 1.5])
    with c1: st.metric("Joint Stiffness ($K_{ec}$)", f"{Kec_abs:,.0e}")
    with c2: st.metric("DF Column", f"{DF_col*100:.1f}%")
    with c3: 
        st.markdown(f"**Status:** :{color}[{status}]")
        st.caption(advice)

    st.pyplot(plot_moment_envelope_with_values(L1, M_neg_face, M_neg_face, M_pos_mid, c1_w))
    st.markdown("---")

    # --- PART 2: DETAILED CALCULATION TABS ---
    tab_stiff, tab_moment, tab_design = st.tabs(["1️⃣ Stiffness Calculation", "2️⃣ Moment Analysis", "3️⃣ RC Design"])

    # --- TAB 1: STIFFNESS DETAILS ---
    with tab_stiff:
        st.markdown("#### 1.1 Column Stiffness ($K_c$)")
        col_s1, col_s2 = st.columns([1, 1])
        with col_s1:
            st.latex(rf"I_c = \frac{{c_2 c_1^3}}{{12}} = \frac{{{c2_w:.0f} \times {c1_w:.0f}^3}}{{12}} = {Ic_cm4:,.0f} \, cm^4")
        with col_s2:
            st.latex(rf"K_c = \frac{{4EI_c}}{{l_c}} = {Kc_abs/1e5:.2f} \times 10^5")
            st.caption(f"Note: Sum Kc (Top+Bot) = {Sum_Kc/1e5:.2f}E5")

        st.markdown("#### 1.2 Slab Stiffness ($K_s$)")
        st.latex(rf"I_s = \frac{{L_2 h^3}}{{12}} = \frac{{{L2*100:.0f} \times {h_slab:.0f}^3}}{{12}} = {Is_cm4:,.0f} \, cm^4")
        st.latex(rf"K_s = \frac{{4EI_s}}{{L_1}} = {Ks_abs/1e5:.2f} \times 10^5")

        st.markdown("#### 1.3 Torsional Member ($K_t$)")
        st.latex(rf"C = \left(1 - 0.63\frac{{{x_t}}}{{{y_t}}}\right)\frac{{{x_t}^3 {y_t}}}{{3}} = {C_val:,.0f} \, cm^4")
        st.latex(rf"K_t = \sum \frac{{9EC}}{{L_2(1-c_2/L_2)^3}} = {Kt_abs/1e5:.2f} \times 10^5")

        st.markdown("#### 1.4 Equivalent Column ($K_{ec}$)")
        st.info("สมการรวมความแข็ง (Series Combination of Col & Torsion)")
        st.latex(rf"\frac{{1}}{{K_{{ec}}}} = \frac{{1}}{{\Sigma K_c}} + \frac{{1}}{{K_t}} \rightarrow K_{{ec}} = {Kec_abs:,.0f}")

    # --- TAB 2: MOMENT DETAILS ---
    with tab_moment:
        st.markdown("#### 2.1 Static Moment ($M_o$)")
        st.latex(rf"M_o = \frac{{w_u L_2 L_n^2}}{{8}}")
        st.write(f"- $w_u = {w_u:,.0f}$ kg/m²")
        st.write(f"- $L_2 = {L2:.2f}$ m (Transverse width)")
        st.write(f"- $L_n = L_1 - c_1 = {L1 - c1_w/100:.2f}$ m (Clear span)")
        st.success(f"**Total Static Moment $M_o$ = {Mo:,.0f} kg-m**")
        
        st.markdown("#### 2.2 Face of Support Correction")
        st.markdown("การลดค่าโมเมนต์จาก Center Line ($M_{CL}$) มาที่ผิวเสา ($M_{face}$)")
        st.latex(rf"M_{{face}} = M_{{CL}} - \frac{{V_u c_1}}{{2}} + \frac{{w c_1^2}}{{8}}")
        
        df_mom = pd.DataFrame({
            "Location": ["Negative (Interior)", "Positive (Midspan)"],
            "Coeff (ACI)": [coef_neg, coef_pos],
            "M_CL (kg-m)": [M_neg_CL, M_pos_mid],
            "Correction": [f"- {M_red:,.0f}", "0"],
            "M_Design (kg-m)": [M_neg_face, M_pos_mid]
        })
        st.table(df_mom)

    # --- TAB 3: DESIGN DETAILS ---
    with tab_design:
        # Helper for display
        def get_design_latex(Mu_val, b_val, d_val, Rn_val, rho_val, As_req, As_prov):
            return [
                rf"1. M_u = {Mu_val:,.0f} \, kg \cdot m",
                rf"2. R_n = \frac{{{Mu_val*100:.0f}}}{{0.9 \cdot {b_val*100:.0f} \cdot {d_val:.1f}^2}} = {Rn_val:.2f} \, ksc",
                rf"3. \rho_{{req}} = {rho_val:.4f} \quad (\rho_{{min}}=0.0018)",
                rf"4. A_{{s,req}} = {rho_val:.4f} \cdot {b_val*100:.0f} \cdot {d_val:.1f} = {As_req:.2f} \, cm^2"
            ]

        # Calculate Logic
        b_cs = L2/2
        b_ms = L2/2
        
        # CS Top Calculation
        Mu_cs = M_neg_face * 0.75
        Rn_cs = (Mu_cs*100) / (0.9 * (b_cs*100) * d_eff**2)
        try: rho_cs = (0.85*fc/fy)*(1 - np.sqrt(1 - 2*Rn_cs/(0.85*fc)))
        except: rho_cs = 0.0020
        rho_cs = max(rho_cs, 0.0018)
        As_cs = rho_cs * (b_cs*100) * d_eff
        num_cs = int(np.ceil(As_cs / (np.pi*(d_bar/20)**2)))
        
        # MS Bot Calculation
        Mu_ms = M_pos_mid * 0.60
        Rn_ms = (Mu_ms*100) / (0.9 * (b_ms*100) * d_eff**2)
        try: rho_ms = (0.85*fc/fy)*(1 - np.sqrt(1 - 2*Rn_ms/(0.85*fc)))
        except: rho_ms = 0.0020
        rho_ms = max(rho_ms, 0.0018)
        As_ms = rho_ms * (b_ms*100) * d_eff
        num_ms = int(np.ceil(As_ms / (np.pi*(d_bar/20)**2)))

        # --- Display Section ---
        c_des1, c_des2 = st.columns(2)
        
        with c_des1:
            st.subheader("🔴 Column Strip (Top)")
            st.pyplot(draw_rebar_section(b_cs*100, h_slab, cover, num_cs, d_bar, "CS Top"), use_container_width=True)
            with st.expander("Show Calculation Steps", expanded=True):
                steps = get_design_latex(Mu_cs, b_cs, d_eff, Rn_cs, rho_cs, As_cs, 0)
                for s in steps: st.latex(s)
                st.success(f"Use {num_cs}-DB{d_bar}")

        with c_des2:
            st.subheader("🔵 Middle Strip (Bottom)")
            st.pyplot(draw_rebar_section(b_ms*100, h_slab, cover, num_ms, d_bar, "MS Bottom"), use_container_width=True)
            with st.expander("Show Calculation Steps", expanded=True):
                steps = get_design_latex(Mu_ms, b_ms, d_eff, Rn_ms, rho_ms, As_ms, 0)
                for s in steps: st.latex(s)
                st.success(f"Use {num_ms}-DB{d_bar}")
