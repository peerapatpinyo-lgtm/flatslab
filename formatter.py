import streamlit as st

def fmt_acrit_calc(c1_mm, c2_mm, d_mm, pos, acrit_val):
    c1 = c1_mm / 1000.0
    c2 = c2_mm / 1000.0
    d = d_mm / 1000.0
    
    if pos == "Interior":
        eq = r"(c_1 + d)(c_2 + d)"
        sub = f"({c1:.2f} + {d:.2f})({c2:.2f} + {d:.2f})"
    elif pos == "Edge":
        eq = r"(c_1 + d/2)(c_2 + d)"
        sub = f"({c1:.2f} + {d/2:.2f})({c2:.2f} + {d:.2f})"
    else: # Corner
        eq = r"(c_1 + d/2)(c_2 + d/2)"
        sub = f"({c1:.2f} + {d/2:.2f})({c2:.2f} + {d/2:.2f})"
        
    return r"""
    \begin{aligned}
    A_{crit} &= """ + eq + r""" \\
             &= """ + sub + r""" \\
             &= \mathbf{""" + f"{acrit_val:.4f}" + r"""} \; m^2
    \end{aligned}
    """

def fmt_vu_trace(qu, lx, ly, acrit, gamma_v, vu_kg):
    area_tot = lx * ly
    # Show substitution explicitly
    sub_str = f"{qu:.0f} \\times ({area_tot:.2f} - {acrit:.3f}) \\times {gamma_v:.2f}"
    
    return r"""
    \begin{aligned}
    V_u &= q_u \times (Area_{total} - A_{crit}) \times \gamma_v \\
        &= """ + sub_str + r""" \\
        &= \mathbf{""" + f"{vu_kg:,.0f}" + r"""} \; kg
    \end{aligned}
    """

def fmt_shear_capacity_sub(fc, beta, alpha, d, bo, v1, v2, v3):
    # Show sqrt substitution
    sqrt_term = r"\sqrt{" + f"{fc:.1f}" + r"}"
    
    return r"""
    \begin{aligned}
    v_{c1} &= 0.33""" + sqrt_term + r""" = \mathbf{""" + f"{v1:.2f}" + r"""} \; MPa \\
    v_{c2} &= 0.17(1 + 2/""" + f"{beta:.2f}" + r""")""" + sqrt_term + r""" = \mathbf{""" + f"{v2:.2f}" + r"""} \; MPa \\
    v_{c3} &= 0.083(2 + \frac{""" + f"{alpha:.0f}" + r""" \cdot """ + f"{d:.0f}" + r"""}{""" + f"{bo:.0f}" + r"""})""" + sqrt_term + r""" = \mathbf{""" + f"{v3:.2f}" + r"""} \; MPa
    \end{aligned}
    """

def fmt_force_conversion(vc_gov_mpa, bo_mm, d_mm, vc_newton, phi_vc_kg):
    # Unit Bridge Calculation
    return r"""
    \begin{aligned}
    \text{Governing Stress } v_c &= \mathbf{""" + f"{vc_gov_mpa:.2f}" + r"""} \; MPa \\
    V_c (Newton) &= v_c \times b_o \times d \\
    &= """ + f"{vc_gov_mpa:.2f}" + r""" \times """ + f"{bo_mm:.0f}" + r""" \times """ + f"{d_mm:.0f}" + r""" \\
    &= """ + f"{vc_newton:,.0f}" + r""" \; N \\
    \phi V_c (Capacity) &= \frac{0.75 \times V_c}{9.80665 \times 1000} \\
    &= \frac{0.75 \times """ + f"{vc_newton:,.0f}" + r"""}{9806.65} \\
    &= \mathbf{""" + f"{phi_vc_kg/1000:,.2f}" + r"""} \; \text{Tons} \approx \mathbf{""" + f"{phi_vc_kg:,.0f}" + r"""} \; kg
    \end{aligned}
    """

# --- Keep existing functions ---
def fmt_h_min_check(ln_m, pos, h_min_code, h_selected):
    denom = 33 if pos == "Interior" else 30
    ln_str = f"{ln_m:.3f}"
    return r"""
    \begin{aligned}
    \text{Code Req:} \; h_{min} &= \frac{\ell_n}{""" + str(denom) + r"""} = \frac{""" + ln_str + r""" \times 1000}{""" + str(denom) + r"""} = \mathbf{""" + f"{h_min_code:.2f}" + r"""} \; mm \\
    \text{Design Use:} \; h &= \mathbf{""" + f"{h_selected:.0f}" + r"""} \; mm
    \end{aligned}
    """

def fmt_qu_calc(dl_fac, sw, sdl, ll_fac, ll, qu_val, h_final):
    h_m = h_final / 1000.0
    sw_show = f"{h_m:.2f} \\times 2400"
    return r"""
    \begin{aligned}
    SW &= h_{final} \times 2400 = (""" + sw_show + r""") = \mathbf{""" + f"{sw:.0f}" + r"""} \; kg/m^2 \\
    q_u &= """ + f"{dl_fac}" + r"""(SW + SDL) + """ + f"{ll_fac}" + r"""(LL) = \mathbf{""" + f"{qu_val:.0f}" + r"""} \; kg/m^2
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
        &= """ + sub + r""" = \mathbf{""" + f"{bo_mm:.0f}" + r"""} \; mm
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
