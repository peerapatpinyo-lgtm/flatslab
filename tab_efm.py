import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# --- Settings ---
plt.style.use('default') # ใช้ Default เพื่อ Customize เองให้คมชัด
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.size': 9,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'figure.autolayout': True
})

# --- Helper Functions: Engineering Logic & Visualization ---

def interpret_stiffness(Ks, Kec):
    """วิเคราะห์ความสัมพันธ์ความแข็ง (Stiffness Ratio Analysis)"""
    total_k = Ks + Kec
    ratio_col = Kec / total_k
    
    if ratio_col < 0.20:
        status = "⚠️ Weak Column / Strong Slab"
        advice = "เสามีความแข็งน้อยมากเมื่อเทียบกับพื้น โมเมนต์ส่วนใหญ่จะถูกดึงกลับไปที่พื้น (Slab) ระวังพื้นร้าว!"
        color = "red"
    elif ratio_col > 0.60:
        status = "💪 Strong Column"
        advice = "เสาแข็งแรงมาก รับโมเมนต์ไปได้เยอะ ช่วยลดภาระของพื้นได้ดี"
        color = "green"
    else:
        status = "⚖️ Balanced Stiffness"
        advice = "สัดส่วนความแข็งของพื้นและเสาอยู่ในเกณฑ์ปกติ การถ่ายแรงสมดุลดี"
        color = "blue"
    return status, advice, color

def draw_rebar_section(width_cm, height_cm, cover_cm, num_bars, bar_dia_mm, title="Section"):
    """
    ฟังก์ชันวาดหน้าตัดคอนกรีตและเหล็กเสริม (Generative Section Drawing)
    """
    fig, ax = plt.subplots(figsize=(6, 2.5))
    
    # 1. Concrete Section
    ax.add_patch(patches.Rectangle((0, 0), width_cm, height_cm, 
                                   facecolor='#E0E0E0', edgecolor='black', lw=1.5, label='Concrete'))
    
    # 2. Rebars
    bar_dia_cm = bar_dia_mm / 10.0
    # Calculate spacing
    eff_width = width_cm - 2*cover_cm - bar_dia_cm
    if num_bars > 1:
        spacing = eff_width / (num_bars - 1)
        x_positions = [cover_cm + bar_dia_cm/2 + i*spacing for i in range(num_bars)]
    else:
        x_positions = [width_cm/2]
    
    # Draw bars (Bottom reinforcement visual assumption)
    y_pos = cover_cm + bar_dia_cm/2 
    for x in x_positions:
        circle = patches.Circle((x, y_pos), bar_dia_cm/2, facecolor='#C0392B', edgecolor='black')
        ax.add_patch(circle)
        
    # 3. Annotations
    ax.text(width_cm/2, height_cm/2, f"{title}\n{width_cm:.0f} x {height_cm:.0f} cm", 
            ha='center', va='center', color='gray', alpha=0.5, fontsize=12, fontweight='bold')
    
    ax.annotate(f"{num_bars}-DB{bar_dia_mm}", xy=(x_positions[-1], y_pos), xytext=(width_cm+5, y_pos),
                arrowprops=dict(arrowstyle='->', color='#C0392B'), color='#C0392B', fontweight='bold')

    ax.set_xlim(-5, width_cm + 20)
    ax.set_ylim(-5, height_cm + 5)
    ax.set_aspect('equal')
    ax.axis('off')
    return fig

def plot_moment_envelope(L1, M_neg, M_pos, c1_cm):
    """
    วาดแผนภาพโมเมนต์แบบ Engineering Style (Inverted Y)
    """
    fig, ax = plt.subplots(figsize=(8, 3))
    
    x = np.linspace(0, L1, 100)
    # Simulation of Moment Diagram (Simplification for visual)
    # M(x) approx parabola
    w_fake = 8 * (M_pos + M_neg/2) / L1**2 # Back calc w for visual
    M_x = (w_fake * x / 2) * (L1 - x) - M_neg # Approx curve
    
    # Plot formatting
    ax.plot(x, M_x, color='#2980B9', lw=2)
    ax.fill_between(x, M_x, 0, where=(M_x>0), color='#3498DB', alpha=0.1, label='Positive M')
    ax.fill_between(x, M_x, 0, where=(M_x<0), color='#E74C3C', alpha=0.1, label='Negative M')
    
    # Draw Zero Line
    ax.axhline(0, color='black', lw=1)
    
    # Draw Supports
    c1_m = c1_cm / 100
    ax.add_patch(patches.Rectangle((-c1_m/2, -M_neg*1.2), c1_m, M_neg*2.5, color='gray', alpha=0.3))
    ax.add_patch(patches.Rectangle((L1-c1_m/2, -M_neg*1.2), c1_m, M_neg*2.5, color='gray', alpha=0.3))

    # Labels
    ax.text(0, -M_neg, f"  $M^{{-}}_{{design}}$\n  {M_neg:,.0f}", ha='left', va='center', color='#C0392B', fontweight='bold')
    ax.text(L1/2, M_pos, f"$M^{{+}}_{{design}}$\n{M_pos:,.0f}", ha='center', va='bottom', color='#2980B9', fontweight='bold')

    # Style
    ax.invert_yaxis() # Civil Engineer Style!
    ax.set_title("Design Moment Envelope", loc='left', fontsize=10, fontweight='bold')
    ax.set_xlabel("Span Length (m)")
    ax.set_ylabel("Moment (kg-m)")
    ax.grid(True, linestyle='--', alpha=0.5)
    
    return fig

# --- Main Render ---
def render(c1_w, c2_w, L1, L2, lc, h_slab, fc, mat_props, w_u, col_type, **kwargs):
    
    st.markdown("## 🏗️ Equivalent Frame Method (Advanced Analysis)")
    st.markdown("---")

    # --- 1. Engineering Insights (The "Brain") ---
    # คำนวณเบื้องต้นแบบเงียบๆ
    Ec = 15100 * np.sqrt(fc)
    Ic = (c2_w * c1_w**3) / 12
    Is = (L2*100 * h_slab**3) / 12
    Kc = (4 * Ec * Ic) / (lc*100)
    Ks = (4 * Ec * Is) / (L1*100)
    
    # Torsional Part
    x, y = h_slab, c1_w
    C_val = (1 - 0.63 * x/y) * (x**3 * y) / 3
    Kt = (9 * Ec * C_val) / (L2*100 * (1 - c2_w/(L2*100))**3)
    
    # Kec & DF
    Sum_Kc = 2 * Kc
    inv_Kec = (1/Sum_Kc) + (1/Kt)
    Kec = 1/inv_Kec
    
    DF_slab = Ks / (Ks + Kec)
    DF_col = Kec / (Ks + Kec)
    
    # Get Advice
    status, advice, color_status = interpret_stiffness(Ks, Kec)

    # --- UI Section 1: System Behavior (Dashboard Style) ---
    col_dash1, col_dash2, col_dash3 = st.columns([1, 1, 1.5])
    
    with col_dash1:
        st.metric("Slab Stiffness ($K_s$)", f"{Ks:,.0f}", delta="Element Main")
        st.caption(f"Is: {Is:,.0f} cm⁴")
        
    with col_dash2:
        st.metric("Joint Stiffness ($K_{ec}$)", f"{Kec:,.0f}", 
                  delta=f"{DF_col*100:.1f}% Distribution", delta_color="inverse")
        st.caption(f"Kt (Torsion): {Kt:,.0f}")
        
    with col_dash3:
        st.markdown(f"#### Status: :{color_status}[{status}]")
        st.info(f"💡 **Analysis:** {advice}")

    st.markdown("---")

    # --- UI Section 2: Moment & Design (Visual & Result Oriented) ---
    st.subheader("📊 Structural Design Results")
    
    # Moment Calc (Back-end)
    w_line = w_u * L2
    Mo = (w_u * L2 * (L1 - c1_w/100)**2) / 8
    
    # Simplified Design Moment (For Demo)
    # In real app, this comes from Frame Analysis loop
    M_neg_coef = 0.65 if col_type=='interior' else 0.50 # ACI Coeff approx
    M_pos_coef = 0.35 if col_type=='interior' else 0.50
    
    M_neg_total = Mo * M_neg_coef
    M_pos_total = Mo * M_pos_coef
    
    # Reduction to Face
    Vu = w_line * L1 / 2
    M_red = Vu * (c1_w/200) - (w_line * (c1_w/200)**2 / 2)
    M_neg_design = M_neg_total - M_red
    M_pos_design = M_pos_total # Conservatively use center moment or adjust
    
    # Plot Envelope
    st.pyplot(plot_moment_envelope(L1, M_neg_design, M_pos_design, c1_w))

    # --- UI Section 3: Reinforcement Selection (The Real Answer) ---
    st.markdown("### 🛠️ Reinforcement Selection (ผลลัพธ์เหล็กเสริม)")
    
    # Design Parameters
    fy = mat_props.get('fy', 4000)
    d_bar = mat_props.get('d_bar', 12)
    cover = 2.5
    d = h_slab - cover - (d_bar/20) # cm
    
    def calculate_rebar(Mu_kgm, width_m):
        """คำนวณเหล็กเสริมแบบจบในฟังก์ชันเดียว"""
        Mu = Mu_kgm * 100 # kg-cm
        width_cm = width_m * 100
        Rn = Mu / (0.9 * width_cm * d**2)
        rho = (0.85 * fc / fy) * (1 - np.sqrt(1 - (2 * Rn) / (0.85 * fc)))
        rho = max(rho, 0.0018) # Min steel
        As = rho * width_cm * d
        As_bar = 3.1416 * (d_bar/20)**2
        num = int(np.ceil(As / As_bar))
        return num, As, rho

    # Strip Widths (ACI)
    width_cs = L2 / 2
    width_ms = L2 / 2
    
    # Calculate Steel
    # Column Strip (Top Steel - Negative)
    bars_cs_top, As_cs_top, rho_cs = calculate_rebar(M_neg_design * 0.75, width_cs)
    
    # Middle Strip (Bottom Steel - Positive)
    bars_ms_bot, As_ms_bot, rho_ms = calculate_rebar(M_pos_design * 0.40, width_ms) # 40% to MS pos (Interior)

    # Display Results in Tabs (Clean UI)
    tab1, tab2 = st.tabs(["🔴 Column Strip (Top Steel)", "🔵 Middle Strip (Bottom Steel)"])
    
    with tab1:
        c1, c2 = st.columns([1, 2])
        with c1:
            st.markdown("#### Design Logic")
            st.write(f"- **Width:** {width_cs:.2f} m")
            st.write(f"- **Moment:** {(M_neg_design*0.75):,.0f} kg-m")
            st.write(f"- **Required $A_s$:** {As_cs_top:.2f} cm²")
            st.success(f"**Selection:** {bars_cs_top} - DB{d_bar}")
        with c2:
            st.markdown("**Section Visualization:**")
            st.pyplot(draw_rebar_section(width_cs*100, h_slab, cover, bars_cs_top, d_bar, "Column Strip Section (Top)"), use_container_width=True)

    with tab2:
        c1, c2 = st.columns([1, 2])
        with c1:
            st.markdown("#### Design Logic")
            st.write(f"- **Width:** {width_ms:.2f} m")
            st.write(f"- **Moment:** {(M_pos_design*0.40):,.0f} kg-m")
            st.write(f"- **Required $A_s$:** {As_ms_bot:.2f} cm²")
            st.success(f"**Selection:** {bars_ms_bot} - DB{d_bar}")
        with c2:
            st.markdown("**Section Visualization:**")
            st.pyplot(draw_rebar_section(width_ms*100, h_slab, cover, bars_ms_bot, d_bar, "Middle Strip Section (Bottom)"), use_container_width=True)

    # --- Footer ---
    st.markdown("---")
    with st.expander("📚 ดูวิธีการคำนวณโดยละเอียด (Detailed Calculation Log)"):
        st.write(f"1. **Stiffness:** Kc={Kc:.0f}, Ks={Ks:.0f}, Kt={Kt:.0f}, Kec={Kec:.0f}")
        st.write(f"2. **Distribution Factors:** DF_slab={DF_slab:.3f}, DF_col={DF_col:.3f}")
        st.write(f"3. **Moments:** Mo={Mo:,.0f}, M_neg_face={M_neg_design:,.0f}")
        st.latex(r"A_s = \rho b d, \quad \rho \ge 0.0018")
