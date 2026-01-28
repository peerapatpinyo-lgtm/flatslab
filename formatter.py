import streamlit as st

def fmt_h_min_check(ln_m, pos, h_min_code, h_selected):
    denom = 33 if pos == "Interior" else 30
    # แยกตัวแปรออกมาคำนวณก่อนเพื่อความปลอดภัยของ Syntax
    ln_str = f"{ln_m:.3f}"
    
    return r"""
    \begin{aligned}
    \text{Code Req:} \; h_{min} &= \frac{\ell_n}{""" + str(denom) + r"""} = \frac{""" + ln_str + r""" \times 1000}{""" + str(denom) + r"""} \\
    &= \mathbf{""" + f"{h_min_code:.2f}" + r"""} \; mm \\
    \text{Design Use:} \; h &= \mathbf{""" + f"{h_selected:.0f}" + r"""} \; mm
    \end{aligned}
    """

def fmt_qu_calc(dl_fac, sw, sdl, ll_fac, ll, qu_val, h_final):
    h_m = h_final / 1000.0
    sw_show = f"{h_m:.2f} \\times 2400"
    
    return r"""
    \begin{aligned}
    SW &= h_{final} \times 2400 = (""" + sw_show + r""") = \mathbf{""" + f"{sw:.0f}" + r"""} \; kg/m^2 \\
    q_u &= """ + f"{dl_fac}" + r"""(SW + SDL) + """ + f"{ll_fac}" + r"""(LL) \\
        &= """ + f"{dl_fac}" + r"""(""" + f"{sw:.0f}" + r""" + """ + f"{sdl:.0f}" + r""") + """ + f"{ll_fac}" + r"""(""" + f"{ll:.0f}" + r""") \\
        &= \mathbf{""" + f"{qu_val:.0f}" + r"""} \; kg/m^2
    \end{aligned}
    """

def fmt_geometry_trace(c1_mm, c2_mm, d_mm, bo_mm, pos):
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
    area_tot = lx * ly
    return r"""
    \begin{aligned}
    V_u &= q_u(L_x L_y - A_{crit})\gamma_v \\
        &= """ + f"{qu:.0f}" + r"""(""" + f"{area_tot:.2f}" + r""" - """ + f"{acrit:.4f}" + r""")(""" + f"{gamma_v:.2f}" + r""") \\
        &= \mathbf{""" + f"{vu_kg:.0f}" + r"""} \; kg
    \end{aligned}
    """

def fmt_shear_capacity_sub(fc, beta, alpha, d, bo):
    v1_val = 0.33 * (fc**0.5)
    return r"""
    \begin{aligned}
    v_{c1} &= 0.33\sqrt{f_c'} = \mathbf{""" + f"{v1_val:.2f}" + r"""} \; MPa \\
    v_{c2} &= 0.17(1 + 2/\beta)\sqrt{f_c'} \\
    v_{c3} &= 0.083(2 + \alpha_s d/b_o)\sqrt{f_c'}
    \end{aligned}
    """

def fmt_flexure_trace(strip_name, coeff, mo, mu, fy, d_cm, as_req):
    return r"""
    \textbf{""" + strip_name + r"""} \; (C=""" + f"{coeff}" + r"""): \\
    \begin{aligned}
    M_u &= C M_o = \mathbf{""" + f"{mu:,.0f}" + r"""} \; kg \cdot m \\
    A_s &= \frac{M_u}{0.9 f_y (0.9d)} = \mathbf{""" + f"{as_req:.2f}" + r"""} \; cm^2
    \end{aligned}
    """
