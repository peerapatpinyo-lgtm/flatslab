import streamlit as st
import engine
import report
import drawings

st.set_page_config(page_title="Pro Flat Slab", layout="wide")

st.sidebar.title("🏗️ Design Inputs")
with st.sidebar:
    lx = st.number_input("Span Lx (m)", 5.0, 15.0, 8.0)
    ly = st.number_input("Span Ly (m)", 5.0, 15.0, 8.0)
    c1 = st.number_input("Col Width c1 (mm)", 200, 1000, 500)
    c2 = st.number_input("Col Depth c2 (mm)", 200, 1000, 500)
    pos = st.selectbox("Position", ["Interior", "Edge", "Corner"])
    st.divider()
    fc = st.number_input("fc' (ksc)", 180, 500, 280)
    fy = st.number_input("fy (ksc)", 2400, 5000, 4000)
    sdl = st.number_input("SDL (kg/m2)", 0, 1000, 150)
    ll = st.number_input("LL (kg/m2)", 0, 2000, 300)
    st.divider()
    h_init = st.number_input("Start Thickness (mm)", 100, 500, 150)

# Define Cover
cover_val = 25 

# Run Engine
data = engine.run_design_cycle(lx, ly, h_init, c1, c2, fc, fy, sdl, ll, cover_val, pos, 1.2, 1.6)
res = data['results']

st.title("🛡️ Flat Slab Design: Traceability Edition")

# --- TRACEABILITY BANNER ---
# แสดงการเปลี่ยนแปลงความหนาและเหตุผลชัดเจน
banner_color = "green" if res['ratio'] <= 1.0 else "red"
h_start = data['inputs']['h_init']
h_final = res['h']

# Logic สำหรับลูกศรแสดงการเปลี่ยนแปลง
change_symbol = "->" if h_final > h_start else "="
change_text = f"{h_start} mm {change_symbol} **{h_final} mm**"

st.markdown(f"""
<div style='background-color:rgba(220,220,220,0.15); padding:20px; border-radius:10px; border-left: 8px solid {banner_color};'>
    <h3 style='margin:0'>Final Thickness: {h_final} mm</h3>
    <p style='font-size:18px; margin:5px 0;'>
        Trace: {change_text}
    </p>
    <p style='color: #555;'>
        <b>Reason for adjustment:</b> {res['reason']} <br>
        <b>Check Ratio:</b> {res['ratio']:.2f} ({'PASS' if res['ratio'] <= 1.0 else 'FAIL'})
    </p>
</div>
""", unsafe_allow_html=True)

t1, t2 = st.tabs(["📄 Detailed Report", "📐 Shop Drawing"])

with t1:
    report.render_report(data)

with t2:
    # ส่งค่า res['h'] (Final) เข้าไปวาดรูปเท่านั้น
    cover_to_draw = data['inputs'].get('cover', cover_val)
    fig = drawings.draw_section(res['h'], cover_to_draw, c1, res['ln'])
    st.pyplot(fig)
