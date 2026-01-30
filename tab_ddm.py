# tab_ddm.py
import streamlit as st
import pandas as pd
import numpy as np
from calculations import design_rebar_detailed
import ddm_plots # เรียกใช้ไฟล์ plot ที่คุณให้มา

# ==========================================
# 1. HELPER: DESIGN BLOCK WIDGET
# ==========================================
def render_design_block(title, strip_type, Mu, b_width, h_slab, cover, fc, fy, key_suffix):
    """
    สร้าง Block สำหรับคำนวณและเลือกเหล็กเสริม 1 จุด (เช่น CS-Top)
    Return: Dictionary ข้อมูลผลลัพธ์ และ String สำหรับ Label ในรูป
    """
    # Card Styling
    color_border = "#dc3545" if "Column" in strip_type else "#0d6efd"
    bg_color = "#fff5f5" if "Column" in strip_type else "#f0f8ff"
    
    with st.container():
        st.markdown(f"""
        <div style="border-left: 5px solid {color_border}; background-color: {bg_color}; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
            <strong style="color: {color_border};">{strip_type} - {title}</strong>
        </div>
        """, unsafe_allow_html=True)
        
        c1, c2 = st.columns([1, 1.2])
        
        with c1:
            # 1. Select DB
            db_options = [10, 12, 16, 20, 25, 28]
            default_idx = 2 if "Column" in strip_type else 1 # Default DB16 for CS, DB12 for MS
            d_bar = st.selectbox(f"Rebar Ø (mm)", db_options, index=default_idx, key=f"db_{key_suffix}")
            
        with c2:
            # 2. Select Spacing
            spacing = st.slider(f"Spacing (cm)", 5.0, 35.0, 20.0, 2.5, key=f"sp_{key_suffix}")

        # --- CALCULATION LOGIC ---
        d_eff = h_slab - cover - (d_bar/20.0)/2
        
        # Call Calculation Function
        As_req, rho_req, note, status_calc = design_rebar_detailed(Mu, b_width, d_eff, fc, fy)
        
        # Calculate Provided
        area_one_bar = np.pi * (d_bar/10)**2 / 4
        As_provided = area_one_bar * (100 / spacing) * (b_width/100)
        
        # Check Status
        is_pass = As_provided >= As_req
        ratio = As_provided / As_req if As_req > 0 else 999
        status_text = "OK" if is_pass else "FAIL"
        status_color = "green" if is_pass else "red"
        
        # --- DISPLAY METRICS ---
        c_res1, c_res2, c_res3 = st.columns(3)
        c_res1.metric("Moment ($M_u$)", f"{Mu:,.0f}", "kg-m")
        c_res2.metric("Req. $A_s$", f"{As_req:.2f}", "cm²")
        c_res3.metric(f"Prov. $A_s$", f"{As_provided:.2f}", f"{ratio:.2f}x ({status_text})", delta_color="normal" if is_pass else "inverse")

        # --- EXPANDER DETAIL ---
        with st.expander(f"🔎 ดูรายการคำนวณ ({strip_type} {title})"):
            st.markdown(f"**Design Parameters:** $b={b_width:.0f}$ cm, $d={d_eff:.2f}$ cm, $\phi=0.9$")
            
            # Step 1: Rn
            Rn = (Mu * 100) / (0.9 * b_width * d_eff**2)
            st.latex(r"R_n = \frac{M_u}{\phi b d^2} = " + f"{Rn:.2f}" + r" \text{ ksc}")
            
            # Step 2: Rho
            if status_calc == "FAIL":
                st.error(f"Calculation Error: {note}")
            else:
                st.latex(r"\rho_{req} = " + f"{rho_req:.5f}" + r" \rightarrow A_{s,req} = \rho b d = " + f"{As_req:.2f}" + r" \text{ cm}^2")
                st.caption(f"Control Condition: {note}")
            
            st.markdown("---")
            st.markdown(f"**Selection:** DB{d_bar}@{spacing:.0f} cm")
            st.latex(r"A_{s,prov} = \frac{\pi d_b^2}{4} \times \frac{100}{s} \times \frac{b}{100} = " + f"{As_provided:.2f}" + r" \text{ cm}^2")

        return {
            "label": f"DB{d_bar}@{spacing:.0f}c", # For Plotting
            "status": status_text,
            "As_prov": As_provided,
            "As_req": As_req,
            "d_bar": d_bar,
            "spacing": spacing
        }

# ==========================================
# 2. MAIN TAB RENDERER
# ==========================================
def render_direction_tab(direction_name, data, mat, w_u):
    """
    Render 1 Tab (X or Y) with full engineering workflow
    1. Moment Diagram (Auto)
    2. Interactive Design (User Input)
    3. Detailing Drawings (Auto-update based on Input)
    """
    L_span = data['L_span']
    L_width = data['L_width']
    ln = data['ln']
    Mo = data['Mo']
    M_vals = data['M_vals']
    c_para = data['c_para'] # cx or cy
    
    fc, fy = mat['fc'], mat['fy']
    h_slab, cover = mat['h_slab'], mat['cover']
    
    # Calculate Strip Widths (for Calculation)
    w_cs = 0.5 * min(L_span, L_width) * 100 # Total CS Width (cm)
    w_ms = (L_width * 100) - w_cs           # Total MS Width (cm)

    st.markdown(f"### 1️⃣ Analysis: Bending Moment Diagram ({direction_name}-Axis)")
    
    # --- PLOT 1: MOMENT DIAGRAM ---
    # เรียกใช้ plot_ddm_moment จาก ddm_plots.py
    fig_moment = ddm_plots.plot_ddm_moment(L_span, c_para/100, M_vals)
    
    st.pyplot(fig_moment, use_container_width=True)
    
    st.info(f"**Total Static Moment ($M_o$):** {Mo:,.0f} kg-m | **Distribution:** CS Width = {w_cs:.0f} cm, MS Width = {w_ms:.0f} cm")
    
    st.markdown("---")
    st.markdown(f"### 2️⃣ Design: Reinforcement Selection")
    
    # Storage for Rebar Labels (to send to plots)
    rebar_map = {}
    
    # --- INTERACTIVE DESIGN SECTION ---
    col_cs, col_ms = st.columns(2)
    
    # A. COLUMN STRIP
    with col_cs:
        st.subheader("🟥 Column Strip (CS)")
        # CS Top
        res_cs_top = render_design_block("Top (Support)", "Column Strip", M_vals['M_cs_neg'], w_cs, h_slab, cover, fc, fy, f"{direction_name}_cs_top")
        rebar_map['CS_Top'] = res_cs_top['label']
        
        # CS Bot
        res_cs_bot = render_design_block("Bottom (Midspan)", "Column Strip", M_vals['M_cs_pos'], w_cs, h_slab, cover, fc, fy, f"{direction_name}_cs_bot")
        rebar_map['CS_Bot'] = res_cs_bot['label']

    # B. MIDDLE STRIP
    with col_ms:
        st.subheader("🟦 Middle Strip (MS)")
        # MS Top
        res_ms_top = render_design_block("Top (Support)", "Middle Strip", M_vals['M_ms_neg'], w_ms, h_slab, cover, fc, fy, f"{direction_name}_ms_top")
        rebar_map['MS_Top'] = res_ms_top['label']
        
        # MS Bot
        res_ms_bot = render_design_block("Bottom (Midspan)", "Middle Strip", M_vals['M_ms_pos'], w_ms, h_slab, cover, fc, fy, f"{direction_name}_ms_bot")
        rebar_map['MS_Bot'] = res_ms_bot['label']

    st.markdown("---")
    st.markdown(f"### 3️⃣ Detailing: Construction Drawings")
    st.markdown("แบบขยายเหล็กเสริม (อัปเดตตามค่าที่เลือกด้านบน)")

    # --- PLOT 2 & 3: DETAILING ---
    tab_det1, tab_det2 = st.tabs(["📐 Section A-A (Side View)", "🏗️ Plan View (Top View)"])
    
    with tab_det1:
        # เรียกใช้ plot_rebar_detailing (ส่ง rebar_map เข้าไปเพื่อให้รูป update ตาม user)
        fig_sec = ddm_plots.plot_rebar_detailing(L_span, h_slab, c_para, rebar_map, direction_name)
        
        st.pyplot(fig_sec, use_container_width=True)
        st.caption("Note: แสดงการเสริมเหล็ก Column Strip เป็นหลัก (Middle Strip ใช้รูปแบบคล้ายกัน)")
        
    with tab_det2:
        # เรียกใช้ plot_rebar_plan_view
        fig_plan = ddm_plots.plot_rebar_plan_view(L_span, L_width, c_para, rebar_map, direction_name)
        
        st.pyplot(fig_plan, use_container_width=True)

    # --- SUMMARY TABLE ---
    st.markdown("### 📋 Design Summary")
    df_sum = pd.DataFrame([
        ["Column Strip", "Top (Support)", M_vals['M_cs_neg'], res_cs_top['label'], res_cs_top['As_req'], res_cs_top['As_prov'], res_cs_top['status']],
        ["Column Strip", "Bottom (Mid)", M_vals['M_cs_pos'], res_cs_bot['label'], res_cs_bot['As_req'], res_cs_bot['As_prov'], res_cs_bot['status']],
        ["Middle Strip", "Top (Support)", M_vals['M_ms_neg'], res_ms_top['label'], res_ms_top['As_req'], res_ms_top['As_prov'], res_ms_top['status']],
        ["Middle Strip", "Bottom (Mid)", M_vals['M_ms_pos'], res_ms_bot['label'], res_ms_bot['As_req'], res_ms_bot['As_prov'], res_ms_bot['status']],
    ], columns=["Strip", "Location", "Mu (kg-m)", "Rebar Selected", "As Req", "As Prov", "Status"])
    
    st.dataframe(df_sum.style.applymap(lambda v: 'color: red; font-weight: bold' if v == 'FAIL' else 'color: green', subset=['Status']), use_container_width=True)

# ==========================================
# 3. ENTRY POINT
# ==========================================
def render_dual(data_x, data_y, mat_props, w_u):
    st.write("## 🏗️ Interactive Slab Design (DDM)")
    st.info("💡 **Workflow:** 1.ดูค่าโมเมนต์ -> 2.เลือกเหล็กเสริม (Design) -> 3.ตรวจสอบแบบขยาย (Detailing)")
    
    tab_x, tab_y = st.tabs(["➡️ X-Direction Analysis", "⬆️ Y-Direction Analysis"])
    
    with tab_x:
        render_direction_tab("X", data_x, mat_props, w_u)
        
    with tab_y:
        render_direction_tab("Y", data_y, mat_props, w_u)
