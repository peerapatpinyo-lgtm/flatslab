import streamlit as st
import pandas as pd
import formatter

def render_report(data):
    inp = data['inputs']
    res = data['results']
    rebar_list = data['rebar'] # ดึง List รายการเหล็กเสริมออกมา
    
    # --- 1. Load Analysis ---
    st.markdown("## 1. Load Analysis")
    st.latex(formatter.fmt_qu_calc(inp['dl_fac'], inp['sw'], inp['sdl'], inp['ll_fac'], inp['ll'], res['qu']))
    
    # --- 2. Flexural Analysis ---
    st.markdown("## 2. Flexural Analysis (Moment)")
    st.latex(formatter.fmt_mo_calc(res['qu'], inp['ly'], inp['ln'], res['mo']))
    
    # --- 3. Punching Shear Check ---
    st.markdown("## 3. Punching Shear Check")
    st.write(f"**Critical Perimeter ($b_o$):** {res['bo_mm']:.0f} mm | **Effective Depth ($d$):** {res['d_mm']:.0f} mm")
    
    st.markdown("#### 3.1 ACI Shear Capacity Formulas")
    st.latex(formatter.fmt_shear_capacity_sub(inp['fc_mpa'], res['beta'], res['alpha_s'], res['d_mm'], res['bo_mm']))
    
    st.markdown("#### 3.2 Capacity Comparison Table")
    
    # สร้าง DataFrame สำหรับตารางเปรียบเทียบ
    df = pd.DataFrame({
        "Formula": ["Eq 1 (Basic)", "Eq 2 (Geometry)", "Eq 3 (Perimeter)"],
        "Stress Capacity (MPa)": [res['v1'], res['v2'], res['v3']],
        "Phi Vc (Tons)": [
            (0.75 * res['v1'] * res['bo_mm'] * res['d_mm'] / 9806.65),
            (0.75 * res['v2'] * res['bo_mm'] * res['d_mm'] / 9806.65),
            (0.75 * res['v3'] * res['bo_mm'] * res['d_mm'] / 9806.65)
        ]
    })
    
    # Format เฉพาะคอลัมน์ตัวเลข
    st.table(df.style.format({
        "Stress Capacity (MPa)": "{:.2f}",
        "Phi Vc (Tons)": "{:.2f}"
    }))
    
    # แสดงผลสรุป Ratio
    st.markdown("#### 3.3 Safety Verification")
    is_pass = res['ratio'] <= 1.0
    st.latex(formatter.fmt_punching_comparison(res['vu_kg'], res['phi_vc_kg'], res['ratio'], is_pass))

    # --- 4. Reinforcement Design (ส่วนที่แก้ไข) ---
    st.markdown("## 4. Reinforcement Design")
    
    # วนลูปแสดงผลเหล็กเสริมทุกตำแหน่ง (CS-, CS+, MS-, MS+)
    for item in rebar_list:
        # เรียกใช้ formatter ตัวใหม่ที่รับค่าครบถ้วน
        st.latex(formatter.fmt_rebar_calc(
            item['name'],
            item['coeff'],
            res['mo'],
            item['mu'],
            inp['fy'],
            res['d_mm']/10, # แปลง d เป็น cm
            item['as_req']
        ))
