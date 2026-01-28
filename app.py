import streamlit as st
import numpy as np

# --- Page Config ---
st.set_page_config(page_title="Flat Slab Designer (ACI 318-19)", layout="wide")

def calculate_flat_slab():
    st.title("🏗️ Expert Flat Slab Design Tool (ACI 318-19)")
    st.markdown("---")

    # --- Sidebar: Input Data ---
    st.sidebar.header("1. ข้อมูลทางเรขาคณิต (Geometry)")
    lx = st.sidebar.number_input("Span Length X (Lx) [m]", value=6.0)
    ly = st.sidebar.number_input("Span Length Y (Ly) [m]", value=6.0)
    h = st.sidebar.number_input("Slab Thickness (h) [mm]", value=200) / 1000
    c_width = st.sidebar.number_input("Column Width [mm]", value=400) / 1000
    c_depth = st.sidebar.number_input("Column Depth [mm]", value=400) / 1000
    cover = st.sidebar.number_input("Clear Cover [mm]", value=20) / 1000

    st.sidebar.header("2. ข้อมูลวัสดุ (Material)")
    fc_prime = st.sidebar.number_input("Concrete Strength (f'c) [ksc]", value=280)
    fy = st.sidebar.number_input("Steel Yield Strength (fy) [ksc]", value=4000)

    st.sidebar.header("3. ข้อมูลน้ำหนักบรรทุก (Loading)")
    sdl = st.sidebar.number_input("Superimposed Dead Load [kg/m²]", value=150)
    ll = st.sidebar.number_input("Live Load [kg/m²]", value=300)

    # --- Calculation Logic ---
    # 1. Loading Calculation (U = 1.2DL + 1.6LL)
    sw = h * 2400  # Self-weight
    qu = (1.2 * (sw + sdl)) + (1.6 * ll)
    
    # 2. Direct Design Method (DDM)
    ln = lx - c_width  # Clear span
    mo = (qu * ly * (ln**2)) / 8
    
    # Effective depth (d)
    d = h - cover - (0.012 / 2) # Assuming 12mm bar

    # 3. Punching Shear Check (Simplified at d/2)
    # Critical perimeter bo
    bo = 2 * ((c_width + d) + (c_depth + d))
    vu = qu * (lx * ly - (c_width + d) * (c_depth + d))
    
    # Phi Vc (ACI 318-19) - simplified
    phi = 0.75
    vc = 1.1 * np.sqrt(fc_prime) * bo * d * 10 # Convert to kg
    phi_vc = phi * vc
    punching_ratio = vu / phi_vc

    # --- Display Results ---
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 ผลการวิเคราะห์น้ำหนัก (Analysis)")
        st.write(f"**น้ำหนักบรรทุกแผ่ (qu):** {qu:,.2f} kg/m²")
        st.write(f"**Total Static Moment (Mo):** {mo:,.2f} kg-m")
        
        st.info("💡 **Moment Distribution (DDM):**")
        st.write(f"- Column Strip Positive: {0.60 * 0.35 * mo:,.2f} kg-m")
        st.write(f"- Column Strip Negative: {0.75 * 0.65 * mo:,.2f} kg-m")

    with col2:
        st.subheader("🛡️ การตรวจสอบแรงเฉือนทะลุหัวเสา (Punching Shear)")
        if punching_ratio < 1.0:
            st.success(f"ผ่าน (PASS): Ratio = {punching_ratio:.3f}")
        else:
            st.error(f"ไม่ผ่าน (FAIL): Ratio = {punching_ratio:.3f}")
            st.warning("คำแนะนำ: ควรเพิ่มความหนาพื้น (h) หรือเพิ่ม Drop Panel")

    st.markdown("---")
    
    # --- Reinforcement Summary ---
    st.subheader("📋 ตารางสรุปเหล็กเสริมเบื้องต้น (Estimated Reinforcement)")
    
    # Min Steel Calculation
    as_min = 0.0018 * 100 * (h * 100) # cm2 per m
    
    data = {
        "Position": ["Column Strip (Top)", "Column Strip (Bottom)", "Middle Strip (Top)", "Middle Strip (Bottom)"],
        "Min As (cm²/m)": [f"{as_min:.2f}" for _ in range(4)],
        "Recommended": ["DB12 @ 0.15 m", "DB12 @ 0.20 m", "DB12 @ 0.20 m", "DB12 @ 0.20 m"]
    }
    st.table(data)

    # --- Engineering Notes ---
    with st.expander("📝 Engineering Notes (คำแนะนำด้านวิศวกรรม)"):
        st.write("""
        - การคำนวณนี้ใช้มาตรฐาน **ACI 318-19** โดยวิธี Direct Design Method.
        - ตรวจสอบค่า **Long-term Deflection** เสมอ เนื่องจากพื้น Flat Slab มักมีปัญหาเรื่องการตกท้องช้างในระยะยาว.
        - ระยะ **Clear Cover** ต้องสอดคล้องกับข้อกำหนดการทนไฟ (Fire Rating).
        - หากค่า Punching Shear Ratio เข้าใกล้ 1.0 ควรพิจารณาติดตั้ง **Shear Studs**.
        """)

if __name__ == "__main__":
    calculate_flat_slab()
