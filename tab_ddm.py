import streamlit as st
import pandas as pd
import numpy as np

def render_dual(data_x, data_y, h_slab, d_eff, fc, fy, d_bar, w_u):
    """
    Main Entry Point: สร้าง Tabs แยกทิศทาง X และ Y
    """
    st.header("2. Direct Design Method (DDM) - Detailed Calculation")
    
    # สร้าง Sub-Tabs สำหรับเลือกดูทิศทาง
    tab_x, tab_y = st.tabs([
        f"➡️ Design X-Direction (Span {data_x['L_span']}m)", 
        f"⬆️ Design Y-Direction (Span {data_y['L_span']}m)"
    ])
    
    with tab_x:
        render_single_direction(data_x, h_slab, d_eff, fc, fy, d_bar, w_u)
        
    with tab_y:
        render_single_direction(data_y, h_slab, d_eff, fc, fy, d_bar, w_u)

def render_single_direction(data, h_slab, d_eff, fc, fy, d_bar, w_u):
    """
    ฟังก์ชันแสดงวิธีทำละเอียด (ใช้ร่วมกันทั้ง X และ Y)
    """
    # ดึงค่าจาก Dictionary
    L_span = data['L_span']   # ช่วงคานทิศที่คำนวณ
    L_width = data['L_width'] # ความกว้างรับน้ำหนัก
    c_para = data['c_para']   # ขนาดเสาที่ขนานช่วงคาน
    ln = data['ln']           # ระยะสุทธิ
    Mo = data['Mo']           # โมเมนต์สถิต
    m_vals = data['M_vals']   # ค่าโมเมนต์ย่อย
    dir_name = data['dir']    # ชื่อทิศ (X หรือ Y)

    # Styling
    st.markdown(f"""
    <div style="background-color:#f0f2f6; padding:15px; border-radius:10px; margin-bottom:15px;">
        <h4 style="margin:0; color:#1f77b4;">📐 {dir_name} Calculation</h4>
        <ul style="margin-bottom:0;">
            <li><b>Design Span ($L_1$):</b> {L_span:.2f} m</li>
            <li><b>Transverse Width ($L_2$):</b> {L_width:.2f} m</li>
            <li><b>Column ($c_1$):</b> {c_para:.2f} cm (Parallel to Span)</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    # ==========================================
    # STEP 1: STATIC MOMENT (Mo)
    # ==========================================
    st.subheader("1. คำนวณโมเมนต์สถิตรวม ($M_o$)")
    
    with st.expander("แสดงวิธีทำ $M_o$ (Click to expand)", expanded=True):
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown("**1.1 ระยะช่วงคานสุทธิ ($l_n$)**")
            st.latex(r"l_n = L_{span} - c_{parallel}")
            st.write(f"แทนค่า: $l_n = {L_span:.2f} - {c_para/100:.2f} = {ln:.3f}$ m")
            
            st.markdown("**1.2 โมเมนต์สถิต ($M_o$)**")
            st.latex(r"M_o = \frac{w_u \cdot L_{width} \cdot (l_n)^2}{8}")
            st.write(f"แทนค่า: $M_o = \\frac{{{w_u:,.0f} \\times {L_width:.2f} \\times ({ln:.3f})^2}}{{8}}$")
        
        with col2:
            st.markdown(f"""
            <div style="text-align:center; padding:20px; border:2px solid #28a745; border-radius:10px;">
                <h3>M<sub>o</sub></h3>
                <h2 style="color:#28a745;">{Mo:,.0f}</h2>
                <p>kg-m</p>
            </div>
            """, unsafe_allow_html=True)

    # ==========================================
    # STEP 2: REBAR DESIGN (4 ZONES)
    # ==========================================
    st.subheader("2. ออกแบบเหล็กเสริม (Reinforcement Design)")
    
    # กำหนดความกว้าง Strip
    w_cs = min(L_span, L_width) / 2.0
    w_ms = L_width - w_cs
    
    zones = [
        {"name": "Zone 1: Column Strip - Top (Negative)", "M": m_vals["M_cs_neg"], "b": w_cs, "icon": "🟥"},
        {"name": "Zone 2: Column Strip - Bottom (Positive)", "M": m_vals["M_cs_pos"], "b": w_cs, "icon": "🟦"},
        {"name": "Zone 3: Middle Strip - Top (Negative)", "M": m_vals["M_ms_neg"], "b": w_ms, "icon": "⬜"},
        {"name": "Zone 4: Middle Strip - Bottom (Positive)", "M": m_vals["M_ms_pos"], "b": w_ms, "icon": "⬜"},
    ]

    for z in zones:
        with st.expander(f"{z['icon']} {z['name']} | Moment: {z['M']:,.0f} kg-m", expanded=False):
            # ตัวแปรสำหรับคำนวณ
            Mu_kgcm = z['M'] * 100
            b_cm = z['b'] * 100
            
            c1, c2 = st.columns([1.5, 1])
            
            with c1:
                st.markdown("#### 1. Check Capacity ($R_n$)")
                # แสดงค่าตัวแปร
                st.write(f"- $M_u = {Mu_kgcm:,.0f}$ kg-cm")
                st.write(f"- $b = {b_cm:.0f}$ cm (Strip Width)")
                st.write(f"- $d = {d_eff:.2f}$ cm, $\phi = 0.9$")
                
                # คำนวณ Rn
                denom = 0.9 * b_cm * (d_eff**2)
                Rn = Mu_kgcm / denom if denom > 0 else 0
                
                st.latex(r"R_n = \frac{M_u}{\phi b d^2} = " + f"\\frac{{{Mu_kgcm:,.0f}}}{{{denom:,.0f}}} = {Rn:.2f}" + r" \text{ ksc}")
                
                st.markdown("#### 2. Calculate $\\rho$")
                term = 1 - (2*Rn)/(0.85*fc)
                
                if term < 0:
                    st.error(f"❌ **FAIL:** Section too small! (Term in root is negative: {term:.3f})")
                    st.stop()
                    
                rho_req = (0.85*fc/fy) * (1 - np.sqrt(term))
                rho_min = 0.0018
                rho_design = max(rho_req, rho_min)
                
                st.write(f"- $\\rho_{{req}} = {rho_req:.5f}$")
                st.write(f"- $\\rho_{{min}} = {rho_min}$")
                st.markdown(f"👉 **Use $\\rho = {rho_design:.5f}$**")

            with c2:
                st.markdown("#### 3. Final Selection")
                As_req = rho_design * b_cm * d_eff
                st.metric("As Required", f"{As_req:.2f} cm²")
                
                # คำนวณจำนวนเหล็ก
                Ab = 3.14159 * (d_bar/10)**2 / 4
                n_bars = max(np.ceil(As_req/Ab), 2)
                
                # คำนวณ Spacing
                s_calc = b_cm / n_bars
                s_max = min(2*h_slab, 45)
                s_final = min(s_calc, s_max)
                
                st.success(f"""
                **SELECT:**
                ### {int(n_bars)} - DB{d_bar}
                **@ {int(s_final)} cm**
                """)
                st.caption(f"Actual As = {n_bars*Ab:.2f} cm²")
