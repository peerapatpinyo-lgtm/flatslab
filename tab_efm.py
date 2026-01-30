import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# --- Settings ---
# ตั้งค่า Font และ Style ให้กราฟดูเป็นแบบวิศวกรรม
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
# 1. VISUALIZATION FUNCTIONS (วาดสดในไฟล์นี้เลย)
# ==========================================

def plot_stick_model(Ks, Kc_sum, Kt, Kec):
    """วาด Diagram โมเดลโครงสร้าง (Stick Model)"""
    fig, ax = plt.subplots(figsize=(6, 3))
    
    # วาดเส้นแกนหลัก
    ax.axhline(0, color='black', linewidth=1) # Slab Line
    ax.plot([0, 0], [-1, 1], color='gray', linewidth=3, alpha=0.3) # Column Line
    
    # วาด Spring Torsion
    ax.plot([0.2, 0.2], [-0.2, 0.2], color='orange', lw=2, linestyle='--')
    ax.text(0.25, 0, f"Torsion ($K_t$)\n{Kt/1e5:.1f}E5", color='orange', va='center', fontsize=9)
    
    # วาด Slab Stiffness
    ax.text(-0.5, 0.1, f"Slab ($K_s$)\n{Ks/1e5:.1f}E5", ha='center', color='blue', fontsize=9)
    ax.annotate("", xy=(0, 0), xytext=(-1, 0), arrowprops=dict(arrowstyle='<->', color='blue'))
    
    # วาด Column Stiffness
    ax.text(-0.1, 0.8, f"Col Above\n{Kc_sum/2e5:.1f}E5", ha='right', color='gray', fontsize=8)
    ax.text(-0.1, -0.8, f"Col Below\n{Kc_sum/2e5:.1f}E5", ha='right', color='gray', fontsize=8)
    
    # Result Arrow
    ax.annotate(f"Joint $K_{{ec}}$\n= {Kec/1e5:.1f}E5", 
                xy=(0, 0), xytext=(0.6, 0.5),
                arrowprops=dict(facecolor='green', shrink=0.05),
                fontsize=10, fontweight='bold', color='green', ha='center')

    ax.set_xlim(-1.2, 1.2)
    ax.set_ylim(-1.2, 1.2)
    ax.axis('off')
    ax.set_title("Equivalent Frame Stick Model", fontsize=11, fontweight='bold')
    return fig

def plot_moment_envelope(L1, M_neg, M_pos, c1_cm):
    """วาดกราฟโมเมนต์ (Inverted Y)"""
    fig, ax = plt.subplots(figsize=(8, 3))
    
    x = np.linspace(0, L1, 200)
    # สร้างเส้นโค้งพาราโบลาจำลองให้ผ่านจุดที่คำนวณได้
    # เทคนิค: ใช้ Weight Blending ระหว่าง 2 พาราโบลา
    w_approx = 8 * M_pos / (L1**2) # สมมติ w เพื่อสร้างทรงกราฟ
    M_x = (w_approx * x/2 * (L1 - x)) - M_neg * (1 - np.sin(np.pi * x / L1)) # ปรับแก้ทรงกราฟให้สวยงาม
    # ดัดค่าให้ตรงจุด Peak จริง (เพื่อความแม่นยำในการแสดงผล)
    M_x = np.interp(x, [0, L1/2, L1], [-M_neg, M_pos, -M_neg]) # Linear guide
    # Smooth curve fitting (Spline or just slight curve logic for visual)
    # *ใช้แบบ Simplified Parabola blending*
    M_x = np.zeros_like(x)
    for i, xi in enumerate(x):
        parabola = 4 * M_pos * (xi/L1) * (1 - xi/L1) # Simple parabola 0 to Max to 0
        linear_neg = -M_neg + (0 - (-M_neg)) * (xi / (L1*0.2)) if xi < L1*0.2 else 0 # Decay
        # รวมกันแบบง่ายๆ เพื่อ Visualization
        if xi < L1/2:
            t = xi / (L1/2)
            M_x[i] = (1-t)*(-M_neg) + t*(M_pos) # Linear interp visual
            # ใส่ความโค้งนิดหน่อย
            M_x[i] -= 0.2 * M_pos * np.sin(np.pi*xi/L1) 
        else:
            t = (xi - L1/2) / (L1/2)
            M_x[i] = (1-t)*(M_pos) + t*(-M_neg)
            M_x[i] -= 0.2 * M_pos * np.sin(np.pi*xi/L1)

    # Plot Areas
    ax.fill_between(x, M_x, 0, where=(M_x>0), color='#3498DB', alpha=0.2)
    ax.fill_between(x, M_x, 0, where=(M_x<0), color='#E74C3C', alpha=0.2)
    ax.plot(x, M_x, color='#2C3E50', lw=2)

    # Support Pillars
    c1_m = c1_cm / 100
    ax.axvspan(-c1_m/2, c1_m/2, color='gray', alpha=0.3)
    ax.axvspan(L1-c1_m/2, L1+c1_m/2, color='gray', alpha=0.3)
    ax.axhline(0, color='black', lw=0.8)

    # Labels
    ax.text(0, -M_neg, f"{M_neg:,.0f}", ha='right', va='center', color='red', fontweight='bold')
    ax.text(L1/2, M_pos, f"{M_pos:,.0f}", ha='center', va='bottom', color='blue', fontweight='bold')
    
    ax.invert_yaxis() # สำคัญมากสำหรับโยธา
    ax.set_ylabel("Moment (kg-m)")
    ax.set_xlabel("Span (m)")
    ax.set_title("Moment Envelope Diagram", fontweight='bold')
    return fig

def draw_section_detail(b_cm, h_cm, num_bars, d_bar, title):
    """วาดหน้าตัดคาน/พื้นพร้อมเหล็กเสริม"""
    fig, ax = plt.subplots(figsize=(5, 2.5))
    
    # คอนกรีต
    rect = patches.Rectangle((0, 0), b_cm, h_cm, linewidth=2, edgecolor='#333333', facecolor='#E0E0E0')
    ax.add_patch(rect)
    
    # เหล็กเสริม
    cover = 2.5
    dia_cm = d_bar / 10
    y_pos = cover + dia_cm/2 # สมมติเหล็กล่าง (ถ้าเหล็กบนก็กลับด้านได้ แต่เพื่อความง่ายใช้อันนี้)
    
    if "Top" in title: y_pos = h_cm - y_pos # ถ้าเป็นเหล็กบน ให้วาดข้างบน
        
    space = (b_cm - 2*cover - dia_cm) / (num_bars - 1) if num_bars > 1 else 0
    
    for i in range(num_bars):
        x = cover + dia_cm/2 + i*space
        if num_bars == 1: x = b_cm/2
        circle = patches.Circle((x, y_pos), dia_cm/2, linewidth=1, edgecolor='black', facecolor='red')
        ax.add_patch(circle)
    
    # Dimension Lines
    ax.annotate(f"{b_cm:.0f} cm", xy=(b_cm/2, -2), ha='center', va='top')
    ax.annotate(f"{h_cm:.0f} cm", xy=(-2, h_cm/2), ha='right', va='center', rotation=90)
    
    # Text Label
    ax.text(b_cm/2, h_cm/2, f"{num_bars}-DB{d_bar} mm", ha='center', va='center', 
            fontsize=12, fontweight='bold', color='darkred', bbox=dict(facecolor='white', alpha=0.7))
            
    ax.set_title(title, fontsize=10, fontweight='bold')
    ax.axis('equal')
    ax.axis('off')
    return fig

# ==========================================
# 2. MAIN LOGIC
# ==========================================

def render(c1_w, c2_w, L1, L2, lc, h_slab, fc, mat_props, w_u, col_type, **kwargs):
    
    st.markdown("### 🏗️ EFM Calculation & Design Sheet")
    st.markdown("---")

    # --- INPUT PREP ---
    Ec = 15100 * np.sqrt(fc) # ksc
    E_ksm = Ec * 10000 # kg/m2 (ใช้สำหรับคำนวณ Stiffness ในหน่วย m)
    
    # --- 1. STIFFNESS CALCULATION ---
    # Column
    Ic_cm4 = (c2_w * c1_w**3) / 12
    Ic_m4 = Ic_cm4 / (100**4)
    Kc_val = 4 * E_ksm * Ic_m4 / lc # Single column
    Sum_Kc = 2 * Kc_val # Top + Bottom
    
    # Slab
    Is_cm4 = (L2*100 * h_slab**3) / 12
    Is_m4 = Is_cm4 / (100**4)
    Ks_val = 4 * E_ksm * Is_m4 / L1
    
    # Torsion
    c1 = c1_w # cm
    c2 = c2_w # cm
    x_t = h_slab
    y_t = c1
    # Constant C
    C_term1 = (1 - 0.63 * (x_t/y_t))
    C_val = C_term1 * (x_t**3 * y_t) / 3
    C_m4 = C_val / (100**4)
    # Kt
    Kt_denom = L2 * (1 - (c2/100)/L2)**3
    Kt_val = 2 * 9 * E_ksm * C_m4 / Kt_denom # Assume Interior (2 arms)

    # Equivalent Stiffness (Kec)
    inv_Kec = (1/Sum_Kc) + (1/Kt_val)
    Kec_val = 1/inv_Kec
    
    # Distribution Factor (DF)
    Total_K = Ks_val + Kec_val
    DF_col = Kec_val / Total_K
    DF_slab = Ks_val / Total_K

    # --- 2. MOMENT CALCULATION ---
    w_line = w_u * L2 # kg/m
    Ln = L1 - (c1/100)
    Mo = w_line * Ln**2 / 8
    
    # Coeffs
    coef_neg = 0.65
    coef_pos = 0.35
    M_neg = Mo * coef_neg
    M_pos = Mo * coef_pos

    # --- 3. REBAR DESIGN PREP ---
    fy = mat_props.get('fy', 4000)
    d_bar = mat_props.get('d_bar', 12)
    cover = 2.5
    d_eff = h_slab - cover - (d_bar/20) # cm
    
    # Design Logic Function
    def design_rebar(Mu_kgm, b_m):
        Mu = Mu_kgm * 100 # kg-cm
        b = b_m * 100 # cm
        Rn = Mu / (0.9 * b * d_eff**2)
        rho = (0.85*fc/fy) * (1 - np.sqrt(max(0, 1 - 2*Rn/(0.85*fc))))
        rho = max(rho, 0.0018)
        As_req = rho * b * d_eff
        As_bar = 3.1416 * (d_bar/20)**2 / 4
        num = int(np.ceil(As_req / As_bar))
        return Rn, rho, As_req, num

    # --- VISUAL DASHBOARD ---
    # แสดงรูป Stick Model ก่อนเลย เพื่อความเข้าใจ
    c_img, c_data = st.columns([1.5, 1])
    with c_img:
        st.pyplot(plot_stick_model(Ks_val, Sum_Kc, Kt_val, Kec_val))
    with c_data:
        st.info(f"**Status Analysis**")
        st.write(f"Column Stiffness: {Sum_Kc/Total_K*100:.1f}%")
        st.write(f"Slab Stiffness: {Ks_val/Total_K*100:.1f}%")
        if DF_col < 0.3: st.warning("⚠️ Low Column Stiffness")
        else: st.success("✅ Good Stiffness Ratio")

    # --- TABS FOR DETAILED CALCULATION ---
    tab1, tab2, tab3 = st.tabs(["1️⃣ Step 1: Stiffness", "2️⃣ Step 2: Moments", "3️⃣ Step 3: Rebar Design"])

    # === TAB 1: STIFFNESS ===
    with tab1:
        st.subheader("1.1 คำนวณค่า C (Torsional Constant)")
        st.latex(r"C = \left(1 - 0.63 \frac{x}{y}\right) \frac{x^3 y}{3}")
        st.markdown(f"แทนค่า: $x={x_t}, y={y_t}$")
        st.latex(rf"C = \left(1 - 0.63 \frac{{{x_t}}}{{{y_t}}}\right) \frac{{{x_t}^3 ({y_t})}}{{3}} = \mathbf{{{C_val:,.2f}}} \, cm^4")
        
        st.subheader("1.2 คำนวณความแข็ง $K_t, K_c, K_s$")
        st.markdown("**Column Stiffness ($K_c$):**")
        st.latex(rf"K_c = \frac{{4 E I}}{{L}} = \frac{{4 ({E_ksm:.0e}) ({Ic_m4:.1e})}}{{{lc}}} = {Kc_val:,.0f} \, kg\cdot m")
        
        st.markdown("**Equivalent Column ($K_{ec}$):**")
        st.latex(r"\frac{1}{K_{ec}} = \frac{1}{\Sigma K_c} + \frac{1}{K_t}")
        st.latex(rf"\frac{{1}}{{K_{{ec}}}} = \frac{{1}}{{{Sum_Kc:,.0f}}} + \frac{{1}}{{{Kt_val:,.0f}}}")
        st.success(f"📌 ผลลัพธ์ K_ec = {Kec_val:,.0f} kg-m")

    # === TAB 2: MOMENTS ===
    with tab2:
        st.subheader("2.1 Static Moment ($M_o$)")
        st.latex(r"M_o = \frac{w L_2 L_n^2}{8}")
        st.markdown(f"แทนค่า: $w={w_line:,.0f}, L_2={L2}, L_n={Ln:.2f}$")
        st.latex(rf"M_o = \frac{{{w_line:,.0f} \times {L2} \times {Ln:.2f}^2}}{{8}} = \mathbf{{{Mo:,.0f}}} \, kg\cdot m")
        
        st.subheader("2.2 Moment Envelope Diagram")
        st.pyplot(plot_moment_envelope(L1, M_neg, M_pos, c1_w))
        
        st.table(pd.DataFrame({
            "Position": ["Negative (Support)", "Positive (Midspan)"],
            "Coeff": [coef_neg, coef_pos],
            "Calculation": [f"{Mo:,.0f} x {coef_neg}", f"{Mo:,.0f} x {coef_pos}"],
            "Design Moment (kg-m)": [f"{M_neg:,.0f}", f"{M_pos:,.0f}"]
        }))

    # === TAB 3: DESIGN ===
    with tab3:
        st.subheader("3. Design Reinforcement")
        
        col_design_1, col_design_2 = st.columns(2)
        
        # --- Column Strip (Top) ---
        with col_design_1:
            st.markdown("#### 🔴 Column Strip (Top)")
            # คำนวณจริง
            b_cs = L2/2
            Mu_cs = M_neg * 0.75
            Rn, rho, As, num = design_rebar(Mu_cs, b_cs)
            
            # แสดงวิธีทำละเอียด
            st.markdown(f"**1. Moment:** $M_u = {Mu_cs:,.0f}$ kg-m")
            st.latex(rf"R_n = \frac{{M_u}}{{0.9 b d^2}} = \frac{{{Mu_cs*100:.0f}}}{{0.9({b_cs*100})({d_eff:.1f})^2}} = {Rn:.2f} ksc")
            st.latex(rf"\rho_{{req}} = {rho:.4f} \rightarrow A_s = {rho:.4f}({b_cs*100})({d_eff:.1f}) = {As:.2f} cm^2")
            st.success(f"**Select: {num} - DB{d_bar}**")
            # วาดรูปหน้าตัด
            st.pyplot(draw_section_detail(b_cs*100, h_slab, num, d_bar, "CS Top Section"))

        # --- Middle Strip (Bottom) ---
        with col_design_2:
            st.markdown("#### 🔵 Middle Strip (Bottom)")
            # คำนวณจริง
            b_ms = L2/2
            Mu_ms = M_pos * 0.60
            Rn, rho, As, num = design_rebar(Mu_ms, b_ms)
            
            # แสดงวิธีทำละเอียด
            st.markdown(f"**1. Moment:** $M_u = {Mu_ms:,.0f}$ kg-m")
            st.latex(rf"R_n = \frac{{M_u}}{{0.9 b d^2}} = \frac{{{Mu_ms*100:.0f}}}{{0.9({b_ms*100})({d_eff:.1f})^2}} = {Rn:.2f} ksc")
            st.latex(rf"\rho_{{req}} = {rho:.4f} \rightarrow A_s = {rho:.4f}({b_ms*100})({d_eff:.1f}) = {As:.2f} cm^2")
            st.success(f"**Select: {num} - DB{d_bar}**")
            # วาดรูปหน้าตัด
            st.pyplot(draw_section_detail(b_ms*100, h_slab, num, d_bar, "MS Bottom Section"))
