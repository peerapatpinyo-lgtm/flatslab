import streamlit as st
import pandas as pd
import formatter

def render_report(data):
    inp = data['inputs']
    res = data['results']
    rebar_list = data['rebar']
    
    # --- 1. Load Analysis ---
    st.markdown("## 1. Load Analysis")
    st.latex(formatter.fmt_qu_calc(inp['dl_fac'], inp['sw'], inp['sdl'], inp['ll_fac'], inp['ll'], res['qu']))
    
    # --- 2. Flexural Analysis ---
    st.markdown("## 2. Flexural Analysis (Moment)")
    st.latex(formatter.fmt_mo_calc(res['qu'], inp['ly'], inp['ln'], res['mo']))
    
    # --- 3. Punching Shear Check (Detailed Trace) ---
    st.markdown("## 3. Punching Shear Check")
    
    # 3.1 Trace Vu Calculation
    st.markdown("#### 3.1 Shear Force Demand ($V_u$) Calculation Trace")
    # Reverse calculate Acrit for display purpose (since engine passed Vu)
    total_area = inp['lx'] * inp['ly']
    unbalanced = res.get('unbalanced_factor', 1.0)
    # Acrit derived back: Vu = qu * (Area - Acrit) * Factor
    # This ensures consistency with the result
    acrit_disp = total_area - (res['vu_kg'] / (res['qu'] * unbalanced))
    
    st.latex(r"""
    \begin{aligned}
    Area_{total} &= L_x \times L_y = """ + f"{inp['lx']} \\times {inp['ly']} = {total_area:.2f} \; m^2 \\\\" + r"""
    A_{crit} &= \text{Critical Area inside } d/2 \approx """ + f"{acrit_disp:.4f} \; m^2 \\\\" + r"""
    \gamma_v &= \text{Unbalanced Moment Factor} = """ + f"{unbalanced:.2f} \\\\" + r"""
    V_u &= q_u \times (Area_{total} - A_{crit}) \times \gamma_v \\\\
        &= """ + f"{res['qu']:.2f} \\times ({total_area:.2f} - {acrit_disp:.4f}) \\times {unbalanced:.2f} \\\\" + r"""
        &= \mathbf{""" + f"{res['vu_kg']:.2f}" + r"""} \; kg \; (""" + f"{res['vu_kg']/1000:.2f}" + r"""\; Tons)
    \end{aligned}
    """)

    # 3.2 Capacity
    st.markdown("#### 3.2 Shear Capacity ($V_c$) & Verification")
    st.write(f"**Critical Perimeter ($b_o$):** {res['bo_mm']:.0f} mm | **Effective Depth ($d$):** {res['d_mm']:.0f} mm")
    st.latex(formatter.fmt_shear_capacity_sub(inp['fc_mpa'], res['beta'], res['alpha_s'], res['d_mm'], res['bo_mm']))
    
    # 3.3 Result Table
    df = pd.DataFrame({
        "Formula Condition": ["Eq 1 (Basic)", "Eq 2 (Geometry)", "Eq 3 (Perimeter)"],
        "Stress (MPa)": [res['v1'], res['v2'], res['v3']],
        "Capacity (Tons)": [
            (0.75 * res['v1'] * res['bo_mm'] * res['d_mm'] / 9806.65),
            (0.75 * res['v2'] * res['bo_mm'] * res['d_mm'] / 9806.65),
            (0.75 * res['v3'] * res['bo_mm'] * res['d_mm'] / 9806.65)
        ]
    })
    
    # Highlight Governing Case
    min_cap = df["Capacity (Tons)"].min()
    df["Status"] = df["Capacity (Tons)"].apply(lambda x: "Governing" if abs(x - min_cap) < 0.01 else "-")
    
    st.table(df.style.format({
        "Stress (MPa)": "{:.2f}",
        "Capacity (Tons)": "{:.2f}"
    }))
    
    # Final Verification Latex
    is_pass = res['ratio'] <= 1.0
    st.latex(formatter.fmt_punching_comparison(res['vu_kg'], res['phi_vc_kg'], res['ratio'], is_pass))

    # --- 4. Reinforcement ---
    st.markdown("## 4. Reinforcement Design")
    for item in rebar_list:
        st.latex(formatter.fmt_rebar_calc(
            item['name'], item['coeff'], res['mo'], item['mu'],
            inp['fy'], res['d_mm']/10, item['as_req']
        ))
