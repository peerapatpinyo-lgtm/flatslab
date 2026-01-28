import streamlit as st

def fmt_acrit_detailed(c1_m, c2_m, d_m, acrit, pos):
    # Prepare substitution strings based on Position
    c1_d = c1_m + d_m
    c2_d = c2_m + d_m
    
    if pos == "Interior":
        formula = r"(c_1 + d)(c_2 + d)"
        sub = f"({c1_m:.2f} + {d_m:.2f})({c2_m:.2f} + {d_m:.2f})"
        calc_step = f"{c1_d:.3f} \\times {c2_d:.3f}"
    elif pos == "Edge":
        formula = r"(c_1 + d/2)(c_2 + d)"
        sub = f"({c1_m:.2f} + {d_m/2:.2f})({c2_m:.2f} + {d_m:.2f})"
        calc_step = f"{(c1_m + d_m/2):.3f} \\times {c2_d:.3f}"
    else: # Corner
        formula = r"(c_1 + d/2)(c_2 + d/2)"
        sub = f"({c1_m:.2f} + {d_m/2:.2f})({c2_m:.2f} + {d_m/2:.2f})"
        calc_step = f"{(c1_m + d_m/2):.3f} \\times {(c2_m + d_m/2):.3f}"
        
    return r"""
    \begin{aligned}
    A_{crit} &= """ + formula + r""" \\
             &= """ + sub + r""" \\
             &= """ + calc_step + r""" \\
             &= \mathbf{""" + f"{acrit:.4f}" + r"""} \; m^2
    \end{aligned}
    """

def fmt_load_trace(dl_fac, sw, sdl, ll_fac, ll, qu):
    # Show: Formula -> Sub -> Result
    sub_str = f"{dl_fac}({sw:.0f} + {sdl:.0f}) + {ll_fac}({ll:.0f})"
    return r"""
    \begin{aligned}
    q_u &= 1.4(SW + SDL) + 1.7(LL) \\
        &= """ + sub_str + r""" \\
        &= \mathbf{""" + f"{qu:.0f}" + r"""} \; kg/m^2
    \end{aligned}
    """

def fmt_vu_detailed(qu, lx, ly, acrit, gamma, vu):
    # Show: Formula -> Sub -> Result
    area_term = f"({lx} \\times {ly} - {acrit:.4f})"
    sub_str = f"{qu:.0f} \\times {area_term} \\times {gamma:.2f}"
    
    return r"""
    \begin{aligned}
    V_u &= q_u \times (Area - A_{crit}) \times \gamma_v \\
        &= """ + sub_str + r""" \\
        &= \mathbf{""" + f"{vu:,.0f}" + r"""} \; kg
    \end{aligned}
    """

def fmt_vc_conversion_detailed(phi, vc_mpa, bo, d, phi_vc_ton):
    # Explicit conversion trace
    # Formula -> Substitution (with 9.80665) -> Result
    num = f"{phi} \\times {vc_mpa:.2f} \\times {bo:.0f} \\times {d:.0f}"
    den = r"9.80665 \times 1000"
    
    return r"""
    \begin{aligned}
    \phi V_c &= \frac{\phi \cdot v_{min} \cdot b_o \cdot d}{g \cdot 1000} \\
             &= \frac{""" + num + r"""}{""" + den + r"""} \\
             &= \mathbf{""" + f"{phi_vc_ton:,.2f}" + r"""} \; Tons
    \end{aligned}
    """

def fmt_flexure_detailed(name, coeff, mo, mu, fy, d_cm, denom_val, as_req):
    # 1. Moment Trace
    mu_sub = f"{coeff} \\times {mo:,.0f}"
    
    # 2. As Trace
    # Show explicit substitution for denominator
    den_sub = f"0.9 \\times {fy:.0f} \\times 0.9 \\times {d_cm:.1f}"
    
    return r"""
    \underline{\textbf{""" + name + r"""}} \\
    \begin{aligned}
    M_u &= C \times M_o = """ + mu_sub + r""" = \mathbf{""" + f"{mu:,.0f}" + r"""} \; kg \cdot m \\
    A_s &= \frac{M_u \times 100}{\phi f_y j d} \\
        &= \frac{""" + f"{mu:,.0f}" + r""" \times 100}{""" + den_sub + r"""} \\
        &= \mathbf{""" + f"{as_req:.2f}" + r"""} \; cm^2
    \end{aligned}
    """
