import streamlit as st
import pandas as pd
import math
from engine import calculate_detailed_slab
from drawings import plot_slab_section

st.set_page_config(page_title="Structure Calc", layout="wide")

# --- Helper ---
def get_rebar_text(as_req):
    # Simple selection logic
    db12_area = 1.13 # cm2
    spacing = int((db12_area / as_req) * 100) # cm
    spacing = min(30, max(10, (spacing // 2) * 2)) # Step 2cm
    return f"DB12@{spacing}cm"

# --- Sidebar ---
with st.sidebar:
    st.header("Input Parameters")
    lx = st.number_input("Lx (m)", 6.0)
    ly = st.number_input("Ly (m)", 6.0)
    c1 = st.number_input("Col Width (mm)", 400)
    c2 = st.number_input("Col Depth (mm)", 400)
    h_init = st.number_input("Init Thickness (mm)", 200, step=10)
    fc = st.number_input("fc' (ksc)", 280)
    fy = st.number_input("fy (ksc)", 4000)
    sdl = st.number_input("SDL (kg/m2)", 150)
    ll = st.number_input("LL (kg/m2)", 300)
    dl_fac = st.number_input("DL Factor", 1.2)
    ll_fac = st.number_input("LL Factor", 1.6)

# --- Compute ---
res = calculate_detailed_slab(lx, ly, h_init, c1, c2, fc, fy, sdl, ll, 20, "Interior", dl_fac, ll_fac)

# --- Header ---
st.title("📄 Structural Calculation Report")
st.markdown("---")

# --- Verdict ---
r = res['ratio']
status = "PASS" if r <= 1.0 else "FAIL"
color = "green" if r <= 0.9 else "orange" if r <= 1.0 else "red"
st.markdown(f"### Verification Status: :{color}[{status}] (Ratio = {r:.2f})")
st.caption(f"Final Thickness Selected: **{res['geo']['h']} mm**")

# --- TABS ---
t1, t2, t3 = st.tabs(["1. Load & Moments", "2. Punching Shear", "3. Reinforcement"])

# --- TAB 1: Load Analysis ---
with t1:
    st.markdown("#### 1.1 Factored Load Calculation ($q_u$)")
    inp = res['inputs']
    
    # Mathematical Substitution
    st.latex(r"""
    \begin{aligned} 
    SW &= h \times 2400 = """ + f"{res['geo']['h']/1000} \\times 2400 = {inp['sw']:.0f} \; kg/m^2 \\\\" + r"""
    q_u &= """ + f"{inp['dl_fac']}(SW + SDL) + {inp['ll_fac']}(LL) \\\\" + r"""
        &= """ + f"{inp['dl_fac']}({inp['sw']:.0f} + {inp['sdl']}) + {inp['ll_fac']}({inp['ll']}) \\\\" + r"""
        &= \mathbf{""" + f"{res['loads']['qu']:.2f}" + r"""} \; kg/m^2
    \end{aligned}
    """)

    st.markdown("#### 1.2 Static Moment ($M_o$)")
    ln = res['geo']['ln']
    st.latex(r"""
    \begin{aligned}
    L_n &= L_x - c_1 = """ + f"{lx} - {c1/1000} = {res['geo']['ln_calc']:.2f} \; m \\\\" + r"""
    M_o &= \frac{q_u L_y (L_n)^2}{8} \\\\
        &= \frac{""" + f"{res['loads']['qu']:.2f} \\times {ly} \\times ({ln:.2f})^2" + r"""}{8} \\\\
        &= \mathbf{""" + f"{res['loads']['mo']/1000:.2f}" + r"""} \; ton \cdot m
    \end{aligned}
    """)

# --- TAB 2: Punching Shear ---
with t2:
    p = res['punching']
    st.markdown("#### 2.1 Critical Section Properties")
    st.latex(r"""
    \begin{aligned}
    d &= h - cover - d_b/2 = """ + f"{res['geo']['d']*1000:.0f} \; mm \\\\" + r"""
    b_o &= 2(c_1 + d) + 2(c_2 + d) \\\\
        &= 2(""" + f"{inp['c1']*1000:.0f} + {p['d']*1000:.0f}) + 2({inp['c2']*1000:.0f} + {p['d']*1000:.0f}) \\\\" + r"""
        &= \mathbf{""" + f"{p['bo']*1000:.0f}" + r"""} \; mm
    \end{aligned}
    """)

    st.markdown("#### 2.2 Shear Capacity ($v_c$) vs Demand")
    
    # Table Comparison
    df_shear = pd.DataFrame({
        "Parameter": ["Eq. (a) 0.33sqrt(fc)", "Eq. (b) 0.17(1+2/B)...", "Eq. (c) 0.083(2+as d/bo)..."],
        "Stress (MPa)": [p['vc1'], p['vc2'], p['vc3']],
        "Verdict": ["", "", ""]
    })
    df_shear['Verdict'] = df_shear['Stress (MPa)'].apply(lambda x: "Governs" if x == p['vc_mpa'] else "")
    st.table(df_shear.style.format({"Stress (MPa)": "{:.2f}"}))
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**Shear Force ($V_u$)**")
        st.latex(f"V_u = {p['vu_force']/1000:.2f} \; Tons")
    with col_b:
        st.markdown("**Capacity ($\phi V_c$)**")
        st.latex(f"\\phi V_c = {p['phi_vc_force']/1000:.2f} \; Tons")

# --- TAB 3: Reinforcement ---
with t3:
    st.markdown("#### 3.1 Flexural Design ($A_s$ Calculation)")
    
    for row in res['rebar']:
        with st.expander(f"{row['name']} ({row['layer']})", expanded=True):
            st.latex(r"""
            \begin{aligned}
            M_u &= """ + f"{row['coeff']} M_o = {row['mu']/1000:.2f} \; T \cdot m \\\\" + r"""
            A_s &= \frac{M_u}{\phi f_y (0.9d)} = \frac{""" + f"{row['mu']*100:.2f}" + r"""}{0.9 \times """ + f"{inp['fy']}" + r""" \times 0.9 \times """ + f"{res['geo']['d']*100:.2f}" + r"""} \\\\
                &= \mathbf{""" + f"{row['as_req']:.2f}" + r"""} \; cm^2/m
            \end{aligned}
            """)
            st.caption(f"Selected: **{get_rebar_text(row['as_req'])}**")

    st.markdown("#### 3.2 Detailing Section")
    fig = plot_slab_section(res['geo']['h'], 20, c1, ln, lx)
    st.pyplot(fig)
