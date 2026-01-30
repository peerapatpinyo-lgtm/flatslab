#tab_ddm.py
import streamlit as st
import pandas as pd
import numpy as np

# Try import plots, if not exists, skip gracefully
try:
    import ddm_plots 
    HAS_PLOTS = True
except ImportError:
    HAS_PLOTS = False

# ========================================================
# 1. MAIN ENTRY POINT
# ========================================================
def render_dual(data_x, data_y, mat_props, w_u):
    h_slab = mat_props['h_slab']
    fc = mat_props['fc']
    fy = mat_props['fy']
    cover = mat_props['cover']
    
    st.markdown("## 2. Interactive Direct Design Method")
    st.info("💡 **Design Mode:** Complete analysis (ACI 318 / EIT Standards).")

    tab_x, tab_y = st.tabs([
        f"↔️ Design X-Dir ({data_x['L_span']}m)", 
        f"↕️ Design Y-Dir ({data_y['L_span']}m)"
    ])
    
    with tab_x:
        render_interactive_direction(data_x, h_slab, cover, fc, fy, "X", w_u)
    with tab_y:
        render_interactive_direction(data_y, h_slab, cover, fc, fy, "Y", w_u)

# ========================================================
# 2. CALCULATION & UI
# ========================================================
def render_interactive_direction(data, h_slab, cover, fc, fy, axis_id, w_u):
    L_span, L_width, c_para, Mo, m_vals = data['L_span'], data['L_width'], data['c_para'], data['Mo'], data['M_vals']
    w_cs = min(L_span, L_width) / 2.0
    w_ms = L_width - w_cs
    Ln = L_span - (c_para / 100.0)

    # --- PART A: GEOMETRY ---
    st.markdown(f"### 📐 Design Parameters: {axis_id}-Direction")
    
    
    with st.expander("Show Geometry & Moment Distribution Factors", expanded=False):
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Span ($L_1$)", f"{L_span:.2f} m")
            st.metric("Width ($L_2$)", f"{L_width:.2f} m")
        with c2:
            st.metric("Column ($c_1$)", f"{c_para/100:.2f} m")
            st.metric("Clear Span ($l_n$)", f"{Ln:.2f} m")
        with c3:
            st.metric("Factored Load ($w_u$)", f"{w_u:,.0f} kg/m²")
        
        st.latex(f"M_o = \\frac{{w_u \\cdot L_2 \\cdot L_n^2}}{{8}} = \\mathbf{{{Mo:,.0f}}} \\; \\text{{kg-m}}")

    # --- PART B: REBAR SELECTION ---
    st.markdown("### 🎛️ Reinforcement Selection")
    
    def calc_rebar_logic(M_u, b_width, d_bar, s_bar):
        b_cm, h_cm = b_width * 100, h_slab
        d_local = h_cm - cover - (d_bar/20.0)
        
        Rn = (M_u * 100) / (0.9 * b_cm * d_local**2)
        term = 1 - (2*Rn)/(0.85*fc)
        
        if term < 0: return 999, 0, 0, 999, 45, False, "Section Fail"
        
        rho = (0.85*fc/fy) * (1 - np.sqrt(term))
        As_req = max(rho * b_cm * d_local, 0.0018 * b_cm * h_cm)
        As_prov = (b_cm / s_bar) * (3.1416 * (d_bar/10)**2 / 4)
        
        a = (As_prov * fy) / (0.85 * fc * b_cm)
        PhiMn = 0.9 * As_prov * fy * (d_local - a/2) / 100
        
        dc_ratio = M_u / PhiMn if PhiMn > 0 else 999
        is_pass = (dc_ratio <= 1.0) and (As_prov >= As_req) and (s_bar <= min(2*h_cm, 45))
        
        return As_req, As_prov, PhiMn, dc_ratio, min(2*h_cm, 45), is_pass, "-"

    col_cs, _, col_ms = st.columns([1, 0.05, 1])
    with col_cs:
        st.subheader(f"Column Strip ({w_cs:.2f}m)")
        d_cs_top = st.selectbox("Top DB", [12,16,20,25], index=1, key=f"dct{axis_id}")
        s_cs_top = st.number_input("Top @(cm)", 5.0, 45.0, 15.0, key=f"sct{axis_id}")
        d_cs_bot = st.selectbox("Bot DB", [12,16,20,25], index=0, key=f"dcb{axis_id}")
        s_cs_bot = st.number_input("Bot @(cm)", 5.0, 45.0, 20.0, key=f"scb{axis_id}")

    with col_ms:
        st.subheader(f"Middle Strip ({w_ms:.2f}m)")
        d_ms_top = st.selectbox("Top DB", [12,16,20,25], index=0, key=f"dmt{axis_id}")
        s_ms_top = st.number_input("Top @(cm)", 5.0, 45.0, 20.0, key=f"smt{axis_id}")
        d_ms_bot = st.selectbox("Bot DB", [12,16,20,25], index=0, key=f"dmb{axis_id}")
        s_ms_bot = st.number_input("Bot @(cm)", 5.0, 45.0, 20.0, key=f"smb{axis_id}")

    # --- PART C: DETAILED CALCULATION (รายการคำนวณละเอียด) ---
    st.write("---")
    st.markdown("### 🔎 รายการคำนวณออกแบบ (Sample Calculation: CS-Top)")
    
    Mu_sample = m_vals['M_cs_neg']
    b_s = w_cs * 100
    d_s = h_slab - cover - (d_cs_top/20.0)
    Rn_s = (Mu_sample * 100) / (0.9 * b_s * d_s**2)
    rho_s = (0.85*fc/fy) * (1 - np.sqrt(max(0, 1 - (2*Rn_s)/(0.85*fc))))
    As_r = rho_s * b_s * d_s
    As_m = 0.0018 * b_s * h_slab
    
    calc_col1, calc_col2 = st.columns(2)
    with calc_col1:
        st.markdown("**1. กำหนดค่าประสิทธิผลหน้าตัด**")
        st.latex(f"d = h - cover - \\frac{{d_b}}{{2}} = {h_slab} - {cover} - \\frac{{{d_cs_top/10}}}{{2}} = {d_s:.2f} \\text{{ cm}}")
        st.latex(f"A_{{s,min}} = 0.0018 \\cdot b \\cdot h = 0.0018 \\cdot {b_s:.0f} \\cdot {h_slab} = {As_m:.2f} \\text{{ cm}}^2")
    with calc_col2:
        st.markdown("**2. คำนวณปริมาณเหล็กเสริม**")
        st.latex(f"R_n = \\frac{{M_u}}{{\\phi b d^2}} = \\frac{{{Mu_sample:,.0f} \\cdot 100}}{{0.9 \\cdot {b_s:.0f} \\cdot {d_s:.2f}^2}} = {Rn_s:.2f} \\text{{ ksc}}")
        st.latex(f"A_{{s,req}} = \\max(A_{{s,flex}}, A_{{s,min}}) = \\mathbf{{{max(As_r, As_m):.2f}}} \\text{{ cm}}^2")

    # --- PART D: DRAWINGS (3 รูปหลัก) ---
    st.write("---")
    st.markdown("### 📐 Structural Detailing & Diagrams")
    
    # รูปที่ 1: แผนภูมิโมเมนต์
    st.markdown("**1. Moment Diagram (DDM Distribution)**")
    
    if HAS_PLOTS: st.pyplot(ddm_plots.plot_ddm_moment(L_span, c_para, m_vals))
    
    # รูปที่ 2 และ 3: รายละเอียดการวางเหล็ก
    draw_col1, draw_col2 = st.columns(2)
    with draw_col1:
        st.markdown("**2. Rebar Detailing (Section)**")
        
    with draw_col2:
        st.markdown("**3. Rebar Plan (Top View)**")
        

    # --- PART E: SUMMARY TABLE ---
    st.write("---")
    st.markdown("### 📊 Engineering Summary Table")
    # (โค้ดตารางสรุปเหมือนเดิมเพื่อความสมบูรณ์)
    res_list = []
    zones = [
        {"name": "CS-Top", "M": m_vals['M_cs_neg'], "b": w_cs, "d": d_cs_top, "s": s_cs_top},
        {"name": "CS-Bot", "M": m_vals['M_cs_pos'], "b": w_cs, "d": d_cs_bot, "s": s_cs_bot},
        {"name": "MS-Top", "M": m_vals['M_ms_neg'], "b": w_ms, "d": d_ms_top, "s": s_ms_top},
        {"name": "MS-Bot", "M": m_vals['M_ms_pos'], "b": w_ms, "d": d_ms_bot, "s": s_ms_bot},
    ]
    for z in zones:
        As_req, As_prov, PhiMn, dc, sm, ok, note = calc_rebar_logic(z['M'], z['b'], z['d'], z['s'])
        res_list.append({"Location": z['name'], "Mu": f"{z['M']:,.0f}", "As_req": f"{As_req:.2f}", "Selection": f"DB{z['d']}@{z['s']:.1f}", "D/C": f"{dc:.2f}", "Status": "PASS" if ok else "FAIL"})
    st.table(pd.DataFrame(res_list))
