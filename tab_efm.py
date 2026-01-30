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
# 1. VISUALIZATION & HELPER FUNCTIONS
# ==========================================

def interpret_stiffness(Ks, Kec):
    """วิเคราะห์ความสัมพันธ์ความแข็ง"""
    total_k = Ks + Kec
    if total_k == 0: return "N/A", "N/A", "gray"
    ratio_col = Kec / total_k
    
    if ratio_col < 0.25:
        return "⚠️ Flexible Connection (Slab dominant)", "จุดต่อมีความอ่อนตัวสูง โมเมนต์ส่วนใหญ่จะถ่ายเข้าพื้น (Slab) ควรตรวจสอบการแอ่นตัวและรอยร้าวในพื้น", "orange"
    elif ratio_col > 0.65:
        return "💪 Rigid Connection (Column dominant)", "จุดต่อมีความแข็งเกร็งสูง โมเมนต์ถ่ายเข้าเสาได้ดี ช่วยลดภาระพื้น", "green"
    else:
        return "⚖️ Balanced Stiffness", "สัดส่วนความแข็งเหมาะสม การถ่ายแรงสมดุลดี", "blue"

def plot_moment_envelope_with_values(L1, M_neg_L, M_neg_R, M_pos, c1_cm):
    """วาดกราฟโมเมนต์แบบวิศวกรรม (Inverted Y) พร้อมค่ากำกับ"""
    fig, ax = plt.subplots(figsize=(8, 3.5))
    x = np.linspace(0, L1, 150)
    
    # Simulate a moment curve
    M_x = np.zeros_like(x)
    for i, xi in enumerate(x):
        if xi < L1/2:
            factor = (xi / (L1/2))**2
            M_x[i] = -M_neg_L * (1-factor) + M_pos * factor
        else:
            factor = ((L1-xi) / (L1/2))**2
            M_x[i] = -M_neg_R * (1-factor) + M_pos * factor

    # Plot Area & Line
    ax.fill_between(x, M_x, 0, where=(M_x>0), color='#3498DB', alpha=0.2)
    ax.fill_between(x, M_x, 0, where=(M_x<0), color='#E74C3C', alpha=0.2)
    ax.plot(x, M_x, color='#2C3E50', lw=2)
    
    # Supports
    c1_m = c1_cm / 100
    ax.axvspan(-c1_m/2, c1_m/2, color='gray', alpha=0.3)
    ax.axvspan(L1-c1_m/2, L1+c1_m/2, color='gray', alpha=0.3)
    ax.axhline(0, color='black', lw=1)

    # Labels
    ax.text(c1_m/2, -M_neg_L, f"  $M^{{-}}_{{face}}$\n  {M_neg_L:,.0f}", ha='left', va='center', color='#C0392B', fontweight='bold')
    ax.text(L1/2, M_pos, f"$M^{{+}}_{{mid}}$\n{M_pos:,.0f}", ha='center', va='bottom', color='#2980B9', fontweight='bold')

    ax.invert_yaxis()
    ax.set_title("Design Moment Envelope (Diagram)", loc='left', fontweight='bold')
    ax.set_xlabel("Span Length (m)")
    ax.set_ylabel("Moment (kg-m)")
    ax.set_xlim(-c1_m, L1+c1_m)
    return fig

def draw_rebar_section(width_cm, height_cm, cover_cm, num_bars, bar_dia_mm, title):
    """วาดหน้าตัดคอนกรีตและเหล็กเสริมจริง"""
    fig, ax = plt.subplots(figsize=(6, 2.5))
    # Concrete
    ax.add_patch(patches.Rectangle((0, 0), width_cm, height_cm, facecolor='#ECF0F1', edgecolor='#7F8C8D', lw=2))
    # Rebars
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
        
    # Labels
    ax.text(width_cm/2, height_cm*1.1, title, ha='center', fontweight='bold')
    ax.text(width_cm/2, height_cm/2, f"{width_cm:.0f}x{height_cm:.0f} cm", ha='center', color='gray', alpha=0.5)
    if num_bars > 0:
        ax.text(width_cm/2, y_pos-bar_dia_cm*1.5, f"{num_bars}-DB{bar_dia_mm}", ha='center', color='#C0392B', fontweight='bold')
        if num_bars > 1:
             ax.text(width_cm/2, y_pos-bar_dia_cm*3, f"@ {spacing:.0f} cm c/c", ha='center', fontsize=8)

    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_ylim(-height_cm*0.2, height_cm*1.3)
    return fig

# --- Original Concept Plots ---
def plot_concept_torsion(c1, c2, h):
    fig, ax = plt.subplots(figsize=(4, 2.5))
    ax.add_patch(patches.Rectangle((-c2/2-h*2, -h), c2+h*4, h, fc='lightgray', ec='gray', label='Slab'))
    ax.add_patch(patches.Rectangle((-c2/2, -h-20), c2, 20, fc='gray', ec='k', label='Column'))
    # Torsion Member
    ax.add_patch(patches.Rectangle((-c2/2, -h), c2, h, fc='#E74C3C', alpha=0.5, hatch='///'))
    ax.text(0, -h/2, f"Torsional Member\nSection $c_1 \\times h$", ha='center', va='center', fontsize=8, color='white')
    ax.axis('equal'); ax.axis('off'); ax.set_title("Concept: Torsional Section", fontsize=9)
    return fig

def plot_concept_stick_model(Ks, Kec, Kt):
    fig, ax = plt.subplots(figsize=(4, 2))
    ax.plot([-1, 0], [0, 0], 'b-', lw=2); ax.plot([0, 1], [0, 0], 'b-', lw=2)
    ax.text(0.5, 0.1, f"$K_s$", ha='center', color='b')
    # Spring & Col
    ax.plot([0, 0], [0, -0.3], 'r-', lw=2)
    ax.plot([0.05, -0.05, 0.05, -0.05, 0], [-0.3, -0.4, -0.5, -0.6, -0.7], 'orange', lw=1.5) # Spring
    ax.text(0.2, -0.5, f"$K_t$", color='orange', va='center')
    ax.plot([0, 0], [-0.7, -1.0], 'r-', lw=2)
    ax.text(0.2, -0.85, f"$\\Sigma K_c$", color='r', va='center')
    # Equivalent
    ax.annotate(f"$K_{{ec}}$", xy=(-0.1, -0.5), xytext=(-0.8, -0.5), arrowprops=dict(arrowstyle='->', color='r'), color='r')
    ax.axis('equal'); ax.axis('off'); ax.set_xlim(-1, 1); ax.set_ylim(-1.1, 0.2)
    ax.set_title("Concept: Equivalent Frame", fontsize=9)
    return fig

# ==========================================
# 2. MAIN RENDER FUNCTION
# ==========================================
def render(c1_w, c2_w, L1, L2, lc, h_slab, fc, mat_props, w_u, col_type, **kwargs):
    
    st.markdown("### 🏗️ Equivalent Frame Method (EFM) Analysis & Design")
    st.markdown("---")

    # --- 0. Perform Calculations (Back-end) ---
    Ec = 15100 * np.sqrt(fc)
    E_ksm = Ec * 10000
    
    # Stiffness
    Ic = (c2_w/100) * (c1_w/100)**3 / 12
    Is = L2 * (h_slab/100)**3 / 12
    Kc_abs = 4 * E_ksm * Ic / lc; Sum_Kc = 2 * Kc_abs
    Ks_abs = 4 * E_ksm * Is / L1

    x, y = h_slab, c1_w
    C_val = (1 - 0.63 * x/y) * (x**3 * y) / 3
    C_m4 = C_val / (100**4)
    num_arms = 1 if col_type == 'corner' else 2
    Kt_abs = num_arms * 9 * E_ksm * C_m4 / (L2 * (1 - (c2_w/100)/L2)**3)

    if Kt_abs > 0: Kec_abs = 1 / (1/Sum_Kc + 1/Kt_abs)
    else: Kec_abs = Sum_Kc

    Sum_K_joint = Ks_abs + Kec_abs
    DF_col = Kec_abs / Sum_K_joint if Sum_K_joint > 0 else 0
    
    # Moments
    w_line = w_u * L2
    Mo = w_line * L1**2 / 8
    # Simplified ACI Coeffs for Demo
    coef_neg = 0.65 if col_type=='interior' else 0.5
    coef_pos = 0.35 if col_type=='interior' else 0.5
    M_neg_CL = Mo * coef_neg
    M_pos_mid = Mo * coef_pos
    # Reduction
    Vu = w_line * L1 / 2
    c1_m = c1_w / 100
    M_red = Vu*(c1_m/2) - w_line*(c1_m/2)**2 / 2
    
    # --- FIXED VARIABLE NAME HERE ---
    M_neg_face = M_neg_CL - M_red 

    # Reinforcement Prep
    fy = mat_props.get('fy', 4000)
    d_bar = mat_props.get('d_bar', 12)
    cover = mat_props.get('cover', 2.5)
    d_eff = h_slab - cover - (d_bar/20)

    # --- 1. DASHBOARD OVERVIEW ---
    status, advice, color = interpret_stiffness(Ks_abs, Kec_abs)
    
    col_d1, col_d2, col_d3 = st.columns([1, 1, 1.5])
    with col_d1:
        st.metric("Joint Stiffness ($K_{ec}$)", f"{Kec_abs:,.0e}", help="ความแข็งเสมือนของจุดต่อเสา")
    with col_d2:
        st.metric("Moment to Column", f"{DF_col*100:.1f}%", help="% โมเมนต์ที่ถ่ายเข้าเสา (DF_col)")
    with col_d3:
        st.markdown(f"**Status:** :{color}[{status}]")
        st.caption(advice)

    # Show Moment Envelope
    st.pyplot(plot_moment_envelope_with_values(L1, M_neg_face, M_neg_face, M_pos_mid, c1_w))

    st.markdown("---")

    # --- 2. DEEP DIVE TABS ---
    tab_stiff, tab_moment, tab_design = st.tabs(["1️⃣ Stiffness Analysis", "2️⃣ Moment Distribution", "3️⃣ Reinforcement Design"])

    # ======================= TAB 1: STIFFNESS =======================
    with tab_stiff:
        st.markdown("#### Summary of Stiffness Values")
        df_stiff = pd.DataFrame({
            "Component": ["Column ($\Sigma K_c$)", "Slab ($K_s$)", "Torsion ($K_t$)", "**Equiv. Column ($K_{ec}$)**"],
            "Value (ksc·cm)": [Sum_Kc/100, Ks_abs/100, Kt_abs/100, Kec_abs/100], 
            "Note": ["2x (Above+Below)", "Span L1", f"{num_arms} arm(s)", "Combined Series"]
        })
        st.table(df_stiff.style.format({"Value (ksc·cm)": "{:,.0f}"}))

        with st.expander("📐 ดูวิธีทำละเอียด และรูปคอนเซปต์"):
            c_c1, c_c2 = st.columns(2)
            with c_c1:
                st.markdown("**Concept 1: Torsional Member**")
                st.pyplot(plot_concept_torsion(c1_w, c2_w, h_slab))
                st.markdown("**Concept 2: Stick Model**")
                st.pyplot(plot_concept_stick_model(Ks_abs, Kec_abs, Kt_abs))
            
            with c_c2:
                st.markdown("**Calculation Steps:**")
                st.latex(r"1. I_c = \frac{c_2 c_1^3}{12}, \quad I_s = \frac{L_2 h^3}{12}")
                st.latex(r"2. K = \frac{4EI}{L} \implies K_c, K_s")
                st.latex(r"3. C = (1 - 0.63\frac{x}{y})\frac{x^3y}{3}")
                st.latex(r"4. K_t = \sum \frac{9E C}{L_2(1-c_2/L_2)^3}")
                st.latex(r"5. \frac{1}{K_{ec}} = \frac{1}{\Sigma K_c} + \frac{1}{K_t}")
                st.latex(r"6. DF_{col} = \frac{K_{ec}}{K_s + K_{ec}}")
            
            st.write(f"**Calculated C:** {C_val:,.0f} cm⁴ (Section {x:.0f}x{y:.0f} cm)")

    # ======================= TAB 2: MOMENTS =======================
    with tab_moment:
        st.markdown("#### Summary of Design Moments")
        st.write(f"**Total Static Moment ($M_o$):** {Mo:,.0f} kg-m")
        
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.metric("Negative Moment ($M^-_{face}$)", f"{M_neg_face:,.0f}", "kg-m")
        with col_m2:
            st.metric("Positive Moment ($M^+_{mid}$)", f"{M_pos_mid:,.0f}", "kg-m")
            
        with st.expander("🔢 ดูวิธีทำละเอียด การลดค่าโมเมนต์ที่ขอบเสา (Face Correction)"):
            st.markdown("การลดค่าโมเมนต์จากกึ่งกลางเสา ($M_{CL}$) มาที่ขอบเสา ($M_{face}$)")
            st.latex(r"M_{face} = M_{CL} - V_u(\frac{c_1}{2}) + \frac{w(c_1/2)^2}{2}")
            st.write(f"- $M_{{CL}}$ (Negative): {M_neg_CL:,.0f} kg-m")
            st.write(f"- Shear $V_u \approx$: {Vu:,.0f} kg")
            st.write(f"- Reduction $\Delta M$: {M_red:,.0f} kg-m")
            # --- FIXED VARIABLE NAME HERE TOO ---
            st.write(f"- **Final $M_{{face}}$: {M_neg_face:,.0f} kg-m**")

    # ======================= TAB 3: DESIGN =======================
    with tab_design:
        st.markdown("#### Reinforcement Selection Results")
        st.caption(f"Design Parameters: $f'_c={fc}, f_y={fy}, d={d_eff:.1f}cm$")

        # Design Function
        def solve_rebar(Mu_kgm, b_m):
            Mu = Mu_kgm * 100
            b = b_m * 100
            Rn = Mu / (0.9 * b * d_eff**2)
            try:
                rho = (0.85*fc/fy) * (1 - np.sqrt(1 - 2*Rn/(0.85*fc)))
            except: rho = 0.0018 # Fail safe
            rho = max(rho, 0.0018)
            As = rho * b * d_eff
            Ab = np.pi * (d_bar/20)**2
            num = int(np.ceil(As/Ab))
            return num, As, rho

        # Simplified Strip Widths
        b_cs = L2 / 2
        b_ms = L2 / 2
        
        # Calc
        num_cs, As_cs, rho_cs = solve_rebar(M_neg_face * 0.75, b_cs)
        num_ms, As_ms, rho_ms = solve_rebar(M_pos_mid * 0.60, b_ms)

        # Display Results
        c_d1, c_d2 = st.columns(2)
        
        with c_d1:
            st.markdown("**🔴 Column Strip (Top Steel)**")
            st.write(f"Moment: {(M_neg_face*0.75):,.0f} kg-m")
            st.write(f"Req. $A_s$: {As_cs:.2f} cm² ($\rho={rho_cs:.4f}$)")
            st.pyplot(draw_rebar_section(b_cs*100, h_slab, cover, num_cs, d_bar, "CS Top Section"), use_container_width=True)

        with c_d2:
            st.markdown("**🔵 Middle Strip (Bottom Steel)**")
            st.write(f"Moment: {(M_pos_mid*0.60):,.0f} kg-m")
            st.write(f"Req. $A_s$: {As_ms:.2f} cm² ($\rho={rho_ms:.4f}$)")
            st.pyplot(draw_rebar_section(b_ms*100, h_slab, cover, num_ms, d_bar, "MS Bottom Section"), use_container_width=True)

        with st.expander("📝 ดูวิธีทำละเอียด การออกแบบเหล็กเสริม"):
            st.markdown("ขั้นตอนการคำนวณหาพื้นที่หน้าตัดเหล็กเสริม ($A_s$)")
            st.latex(r"1. R_n = \frac{M_u}{\phi b d^2}")
            st.latex(r"2. \rho = \frac{0.85f'_c}{f_y}\left(1 - \sqrt{1 - \frac{2R_n}{0.85f'_c}}\right) \ge \rho_{min}")
            st.latex(r"3. A_s = \rho b d")
            st.latex(r"4. \text{Number of bars} = \lceil A_s / A_{bar} \rceil")
