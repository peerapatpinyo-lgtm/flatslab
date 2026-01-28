import streamlit as st

def fmt_qu_calc(dl_fac, sw, sdl, ll_fac, ll, qu_val):
    # แสดงที่มาของ Load
    return r"""
    \begin{aligned}
    SW &= h \times 2400 = \mathbf{""" + f"{sw:.0f}" + r"""} \; kg/m^2 \\
    q_u &= """ + f"{dl_fac}(SW + SDL) + {ll_fac}(LL) \\\\" + r"""
        &= """ + f"{dl_fac}({sw:.0f} + {sdl:.0f}) + {ll_fac}({ll:.0f}) \\\\" + r"""
        &= \mathbf{""" + f"{qu_val:.0f}" + r"""} \; kg/m^2
    \end{aligned}
    """

def fmt_geometry_trace(c1_mm, c2_mm, d_mm, bo_mm, pos):
    # แสดงที่มาของ bo (Critical Perimeter)
    d = d_mm
    
    if pos == "Interior":
        formula = r"2(c_1 + d) + 2(c_2 + d)"
        sub = f"2({c1_mm:.0f} + {d:.0f}) + 2({c2_mm:.0f} + {d:.0f})"
    elif pos == "Edge":
        formula = r"2(c_1 + d/2) + (c_2 + d)"
        sub = f"2({c1_mm:.0f} + {d/2:.0f}) + ({c2_mm:.0f} + {d:.0f})"
    else: # Corner
        formula = r"(c_1 + d/2) + (c_2 + d/2)"
        sub = f"({c1_mm:.0f} + {d/2:.0f}) + ({c2_mm:.0f} + {d/2:.0f})"
        
    return r"""
    \begin{aligned}
    d &= h - \text{cover} - d_b/2 = \mathbf{""" + f"{d:.0f}" + r"""} \; mm \\
    b_o &= """ + formula + r""" \\
        &= """ + sub + r""" \\
        &= \mathbf{""" + f"{bo_mm:.0f}" + r"""} \; mm
    \end{aligned}
    """

def fmt_vu_trace(qu, lx, ly, acrit, gamma_v, vu_kg):
    # [NEW] ย้ายสูตร Vu มาไว้ที่นี่เพื่อลดโอกาสเกิด Syntax Error ใน report.py
    area_tot = lx * ly
    return r"""
    \begin{aligned}
    Area_{total} &= """ + f"{lx} \\times {ly} = {area_tot:.2f} \; m^2 \\\\" + r"""
    A_{crit} &= \text{Critical Area} \approx """ + f"{acrit:.4f} \; m^2 \\\\" + r"""
    \gamma_v &= """ + f"{gamma_v:.2f} \\\\" + r"""
    V_u &= q_u(Area_{total} - A_{crit})\gamma_v \\\\
        &= """ + f"{qu:.0f}({area_tot:.2f} - {acrit:.4f})({gamma_v}) \\\\" + r"""
        &= \mathbf{""" + f"{vu_kg:.0f}" + r"""} \; kg
    \end{aligned}
    """

def fmt_shear_capacity_sub(fc, beta, alpha, d, bo):
    # แสดงการแทนค่า v_c ทั้ง 3 สูตร
    v1_val = 0.33 * (fc**0.5)
    return r"""
    \begin{aligned}
    v_{c1} &= 0.33\sqrt{f_c'} = 0.33\sqrt{""" + f"{fc:.1f}" + r"""} = \mathbf{""" + f"{v1_val:.2f}" + r"""} \; MPa \\
    v_{c2} &= 0.17(1 + \frac{2}{\beta})\sqrt{f_c'} = 0.17(1 + \frac{2}{""" + f"{beta:.2f}" + r"""})\sqrt{""" + f"{fc:.1f}" + r"""} \\
    v_{c3} &= 0.083(2 + \frac{\alpha_s d}{b_o})\sqrt{f_c'} = 0.083(2 + \frac{""" + f"{alpha} \cdot {d:.0f}" + r"""}{""" + f"{bo:.0f}" + r"""})\sqrt{""" + f"{fc:.1f}" + r"""}
    \end{aligned}
    """

def fmt_flexure_trace(strip_name, coeff, mo, mu, fy, d_cm, as_req):
    # แสดงการคำนวณเหล็กเสริม
    return r"""
    \textbf{""" + strip_name + r"""} \; (C = """ + f"{coeff}" + r"""): \\
    \begin{aligned}
    M_u &= C \times M_o = """ + f"{coeff} \\times {mo:,.0f}" + r""" = \mathbf{""" + f"{mu:,.0f}" + r"""} \; kg \cdot m \\
    A_s &= \frac{M_u}{0.9 f_y (0.9d)} = \frac{""" + f"{mu * 100:.0f}" + r"""}{0.9(""" + f"{fy:.0f}" + r""")(0.9 \cdot """ + f"{d_cm:.1f}" + r""")} \\
        &= \mathbf{""" + f"{as_req:.2f}" + r"""} \; cm^2
    \end{aligned}
    """
