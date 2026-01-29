import streamlit as st
import engine
import report

st.set_page_config(page_title="Transparent Slab Design", layout="wide", page_icon="📐")

# --- STATE MANAGEMENT ---
if 'calc_data' not in st.session_state:
    st.session_state.calc_data = None

# --- SIDEBAR FORM ---
with st.sidebar:
    st.title("⚙️ Design Parameters")
    
    with st.form("input_form"):
        st.subheader("Geometry")
        h = st.number_input("Thickness (mm)", 100, 500, 200)
        c1 = st.number_input("Col Width c1 (mm)", 200, 1000, 500)
        c2 = st.number_input("Col Depth c2 (mm)", 200, 1000, 500)
        lx = st.number_input("Span Lx (m)", 3.0, 12.0, 8.0)
        ly = st.number_input("Span Ly (m)", 3.0, 12.0, 8.0)
        
        st.subheader("Loads & Mat.")
        sdl = st.number_input("SDL (kg/m2)", 0, 500, 150)
        ll = st.number_input("LL (kg/m2)", 0, 1000, 300)
        fc = st.number_input("fc' (ksc)", 180, 500, 280)
        fy = st.number_input("fy (ksc)", 2400, 5000, 4000)
        
        st.subheader("Reinforcement Selection")
        c_top1, c_top2 = st.columns(2)
        top_db = c_top1.selectbox("Top DB", [12, 16, 20, 25], index=1)
        top_sp = c_top2.number_input("Top @ (mm)", 50, 400, 200, step=25)
        
        c_bot1, c_bot2 = st.columns(2)
        bot_db = c_bot1.selectbox("Bot DB", [12, 16, 20, 25], index=1)
        bot_sp = c_bot2.number_input("Bot @ (mm)", 50, 400, 250, step=25)
        
        pos = st.selectbox("Position", ["Interior", "Edge", "Corner"])
        
        submitted = st.form_submit_button("🚀 Calculate / Update")

# --- PROCESS ---
if submitted:
    # เรียก Engine คำนวณ
    data = engine.run_analysis(
        lx, ly, h, c1, c2, 
        sdl, ll, fc, fy, 
        25, pos, top_db, top_sp, bot_db, bot_sp
    )
    # เก็บลง Session State
    st.session_state.calc_data = data

# --- DISPLAY REPORT ---
if st.session_state.calc_data:
    # เรียก Report ให้ Render (จุดที่เคย Error แก้แล้วตรงนี้)
    report.render(st.session_state.calc_data)
else:
    st.info("👈 Please enter parameters and click Calculate.")
