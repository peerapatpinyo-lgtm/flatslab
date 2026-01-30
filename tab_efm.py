import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# --- Settings ---
plt.rcParams.update({
    'font.family': 'sans-serif', 'font.size': 10,
    'axes.spines.top': False, 'axes.spines.right': False,
    'axes.grid': False, 'figure.autolayout': True
})

# ==========================================
# 1. VISUALIZATION: Plan View & Section
# ==========================================

def plot_plan_view(L1, L2, c1, c2, col_strip_width):
    """วาดแปลนพื้น แสดง Column Strip / Middle Strip"""
    fig, ax = plt.subplots(figsize=(6, 4))
    
    # Slab Boundary
    ax.add_patch(patches.Rectangle((0, 0), L1, L2, fc='#f0f0f0', ec='black', lw=2))
    
    # Columns (Corner)
    c1_m, c2_m = c1/100, c2/100
    ax.add_patch(patches.Rectangle((-c1_m/2, -c2_m/2), c1_m, c2_m, fc='black')) # Joint A
    ax.add_patch(patches.Rectangle((L1-c1_m/2, -c2_m/2), c1_m, c2_m, fc='black')) # Joint B
    
    # Column Strip Lines
    cs_w = col_strip_width
    ax.axhline(cs_w/2, color='blue', linestyle='--', alpha=0.5)
    ax.axhline(L2 - cs_w/2, color='blue', linestyle='--', alpha=0.5)
    
    # Labels
    ax.text(L1/2, L2/2, "Middle Strip", ha='center', va='center', color='green', fontweight='bold')
    ax.text(L1/2, cs_w/4, "Col Strip", ha='center', va='center', color='blue', fontsize=8)
    
    # Dimensions
    ax.annotate(f"L1 = {L1} m", xy=(L1/2, -0.5), ha='center', arrowprops=dict(arrowstyle='<->'))
    ax.annotate(f"L2 = {L2} m", xy=(-0.5, L2/2), va='center', rotation=90, arrowprops=dict(arrowstyle='<->'))
    
    ax.set_xlim(-1, L1+1); ax.set_ylim(-1, L2+1)
    ax.axis('off'); ax.set_title("Plan View: Strips & Dimensions", fontweight='bold')
    return fig

def draw_section_detail(b_cm, h_cm, num_bars, d_bar, spacing, as_req, title):
    """วาดหน้าตัดพร้อมรายละเอียด Engineering"""
    fig, ax = plt.subplots(figsize=(5, 2.5))
    
    # Concrete Section
    ax.add_patch(patches.Rectangle((0, 0), b_cm, h_cm, facecolor='#EAECEE', edgecolor='#2C3E50', lw=2))
    
    # Rebars
    cover = 3.0 # cm
    dia_cm = d_bar / 10
    y_pos = h_cm - cover - dia_cm/2 if "Top" in title else cover + dia_cm/2
    
    real_spacing = (b_cm - 2*cover - dia_cm) / (num_bars - 1) if num_bars > 1 else 0
    
    for i in range(num_bars):
        x = cover + dia_cm/2 + i*real_spacing if num_bars > 1 else b_cm/2
        ax.add_patch(patches.Circle((x, y_pos), dia_cm/2, fc='#C0392B', ec='black'))

    # Info Text
    info_text = (
        f"{title}\n"
        f"Width b = {b_cm:.0f} cm, h = {h_cm:.0f} cm\n"
        f"Req. As = {as_req:.2f} cm²\n"
        f"USE: {num_bars}-DB{d_bar} @ {spacing:.0f} cm"
    )
    ax.text(b_cm*0.05, h_cm/2, info_text, fontsize=9, va='center', bbox=dict(facecolor='white', alpha=0.8))
    
    ax.axis('equal'); ax.axis('off')
    return fig

# ==========================================
# 2. LOGIC: MOMENT DISTRIBUTION
# ==========================================
def run_moment_distribution(FEM, DF_slab, iterations=4):
    history = []
    
    # Initial State
    M_A = FEM; M_B = -FEM
    history.append({"Iter": "Start", "Step": "FEM", "Joint A": M_A, "Joint B": M_B})
    
    curr_A, curr_B = M_A, M_B
    tot_A, tot_B = M_A, M_B

    for i in range(iterations):
        # Balance
        bal_A = -1 * curr_A * DF_slab
        bal_B = -1 * curr_B * DF_slab
        tot_A += bal_A; tot_B += bal_B
        
        # Carry Over
        co_A = bal_B * 0.5
        co_B = bal_A * 0.5
        tot_A += co_A; tot_B += co_B
        
        # Save String Formatted for Display (Pre-format to avoid st.dataframe error)
        history.append({
            "Iter": f"{i+1}", "Step": "Dist & CO", 
            "Joint A": co_A, "Joint B": co_B, # Keep numeric for now
            "Balance A": bal_A, "Balance B": bal_B
        })
        
        curr_A, curr_B = co_A, co_B

    history.append({"Iter": "End", "Step": "Sum", "Joint A": tot_A, "Joint B": tot_B})
    return history, tot_A, tot_B

# ==========================================
# 3. MAIN ENGINE
# ==========================================
def render(c1_w, c2_w, L1, L2, lc, h_slab, fc, mat_props, w_u, col_type, **kwargs):
    
    st.markdown("## 🏗️ Detailed EFM Design Sheet")
    st.markdown("---")

    # --- 1. DESIGN PARAMETERS & PRE-CHECK ---
    fy = mat_props.get('fy', 4000)
    d_bar = mat_props.get('d_bar', 12)
    Ec = 15100 * np.sqrt(fc)
    
    # Strip Widths (ACI 318)
    # Column Strip width = min(L1, L2) / 2 (Total for interior) -> /2 again for side
    # But for calculation, let's use the full bay width assumption for simple strip
    # L2 is the transverse width.
    w_cs = min(L1, L2) / 2
    w_ms = L2 - w_cs
    
    with st.expander("📘 Design Parameters & Geometry Check", expanded=True):
        col1, col2 = st.columns([1, 1.5])
        with col1:
            st.write(f"**Materials:**")
            st.write(f"- $f_c'$ = {fc} ksc")
            st.write(f"- $f_y$ = {fy} ksc")
            st.write(f"- $E_c$ = {Ec:,.0f} ksc")
            st.write(f"**Geometry:**")
            st.write(f"- Slab $h$ = {h_slab} cm")
            st.write(f"- Col $c_1 \\times c_2$ = {c1_w}x{c2_w} cm")
            st.write(f"- Load $w_u$ = {w_u:,.0f} kg/m²")
        with col2:
            # Show Plan View
            st.pyplot(plot_plan_view(L1, L2, c1_w, c2_w, w_cs))

    # --- 2. STIFFNESS CALCULATION ---
    # Convert to meters for stiffness
    E_ksm = Ec * 10000 
    Ic = (c2_w * c1_w**3)/12 / 100**4
    Is = (L2*100 * h_slab**3)/12 / 100**4
    
    Kc = 4 * E_ksm * Ic / lc
    Sum_Kc = 2 * Kc # Intermediate floor assumption
    Ks = 4 * E_ksm * Is / L1
    
    # Torsion (Correct Logic: x=shorter, y=longer)
    dim1, dim2 = c1_w, h_slab
    x_t = min(dim1, dim2)
    y_t = max(dim1, dim2)
    C_val = (1 - 0.63*(x_t/y_t)) * (x_t**3 * y_t) / 3
    C_m4 = C_val / 100**4
    Kt = 2 * 9 * E_ksm * C_m4 / (L2 * (1 - (c2_w/100)/L2)**3)
    
    Kec = 1 / (1/Sum_Kc + 1/Kt)
    DF_slab = Ks / (Ks + Kec)

    # --- 3. MOMENT DISTRIBUTION & DESIGN ---
    tab1, tab2 = st.tabs(["🧮 1. Analysis & Distribution", "✅ 2. Reinforcement Design"])

    with tab1:
        st.subheader("Stiffness & Distribution Factors")
        c_k1, c_k2, c_k3 = st.columns(3)
        c_k1.metric("Slab Stiffness (Ks)", f"{Ks/1e5:.2f} E5")
        c_k2.metric("Equiv. Col (Kec)", f"{Kec/1e5:.2f} E5")
        c_k3.metric("Dist. Factor (DF)", f"{DF_slab:.3f}")
        
        st.subheader("Moment Distribution Table (Hardy Cross)")
        
        # Calculate
        w_line = w_u * L2
        FEM = w_line * L1**2 / 12
        hist_data, M_final_L, M_final_R = run_moment_distribution(FEM, DF_slab)
        
        # Clean Table for Display
        df_hist = pd.DataFrame(hist_data)
        # Format explicitly to avoid errors
        st.table(df_hist.style.format({
            "Joint A": "{:,.0f}", "Joint B": "{:,.0f}",
            "Balance A": "{:,.0f}", "Balance B": "{:,.0f}"
        }, na_rep="-"))
        
        # Face Correction
        Vu = w_line * L1 / 2
        M_red = Vu*(c1_w/200) - w_line*(c1_w/200)**2/2
        M_neg_des = abs(M_final_L) - M_red
        M_pos_des = (w_line*L1**2/8) - M_neg_des
        
        st.info(f"📌 **Design Moments (at Face):** Neg = **{M_neg_des:,.0f}** kg-m | Pos = **{M_pos_des:,.0f}** kg-m")

    with tab2:
        st.subheader("Reinforcement Calculation (ACI 318)")
        
        def design_section(Mu, b_m, strip_name):
            b_cm = b_m * 100
            d_eff = h_slab - 3.0 - d_bar/20
            
            # Strength Req
            Rn = (Mu * 100) / (0.9 * b_cm * d_eff**2) # ksc
            rho_req = (0.85*fc/fy) * (1 - np.sqrt(max(0, 1 - 2*Rn/(0.85*fc))))
            
            # Min Check
            rho_min = 0.0018 # Temp & Shrinkage
            rho_des = max(rho_req, rho_min)
            As_req = rho_des * b_cm * d_eff
            
            # Bar Selection
            A_bar = 3.1416 * (d_bar/20)**2 / 4
            num_bars = int(np.ceil(As_req / A_bar))
            
            # Spacing Check
            calc_space = (b_cm - 6.0) / num_bars
            max_space = min(2 * h_slab, 45) # ACI Limit
            
            # Override if spacing > max_space
            if calc_space > max_space:
                num_bars = int(np.ceil((b_cm - 6.0) / max_space))
                calc_space = (b_cm - 6.0) / num_bars
                status = "Governed by Spacing"
            elif rho_des == rho_min:
                status = "Governed by Min. Steel"
            else:
                status = "Governed by Strength"
                
            return {
                "Rn": Rn, "rho": rho_req, "As_req": As_req,
                "num": num_bars, "spacing": calc_space, "status": status,
                "b": b_cm
            }

        col_d1, col_d2 = st.columns(2)
        
        # --- Column Strip Design ---
        with col_d1:
            st.markdown("#### 🔴 Column Strip (Top)")
            # CS takes 75% of Neg Moment
            res = design_section(M_neg_des*0.75, w_cs, "CS Top")
            
            st.write(f"**$M_u$:** {M_neg_des*0.75:,.0f} kg-m")
            st.write(f"**Strip Width:** {res['b']} cm")
            st.caption(f"Status: {res['status']}")
            
            if res['rho'] < 0.0018:
                st.warning(f"⚠️ ใช้เหล็กขั้นต่ำ (Req $\\rho$={res['rho']:.5f})")
            
            st.success(f"**Use {res['num']}-DB{d_bar} @ {res['spacing']:.0f} cm**")
            st.pyplot(draw_section_detail(res['b'], h_slab, res['num'], d_bar, res['spacing'], res['As_req'], "CS-Top"))

        # --- Middle Strip Design ---
        with col_d2:
            st.markdown("#### 🔵 Middle Strip (Bottom)")
            # MS takes 60% of Pos Moment (simplified distribution)
            res = design_section(M_pos_des*0.60, w_ms, "MS Bot")
            
            st.write(f"**$M_u$:** {M_pos_des*0.60:,.0f} kg-m")
            st.write(f"**Strip Width:** {res['b']} cm")
            st.caption(f"Status: {res['status']}")
            
            st.success(f"**Use {res['num']}-DB{d_bar} @ {res['spacing']:.0f} cm**")
            st.pyplot(draw_section_detail(res['b'], h_slab, res['num'], d_bar, res['spacing'], res['As_req'], "MS-Bot"))

    st.markdown("---")
    st.caption("Note: Calculation based on ACI 318 Equivalent Frame Method. $\phi=0.9$ for flexure. $A_{s,min}=0.0018bh$.")
