import streamlit as st

def fmt_geometry_step(c1_mm, c2_mm, d_mm, bo_mm, acrit, pos):
    d = d_mm
    c1 = c1_mm / 1000.0
    c2 = c2_mm / 1000.0
    
    # Determine formula text based on Position
    if pos == "Interior":
        bo_eq = r"2(c_1 + d) + 2(c_2 + d)"
        ac_eq = r"(c_1 + d)(c_2 + d)"
    elif pos == "Edge":
        bo_eq = r"2(c_1 + d/2) + (c_2 + d)"
        ac_eq = r"(c_1 + d/2)(c_2 + d)"
    else: # Corner
        bo_eq = r"(c_1 + d/2) + (c_2 + d/2)"
        ac_eq = r"(c_1 + d/2)(c_2 + d/2)"

    return r"""
    \begin{aligned}
    d &= h - cov - d_b/2 = \mathbf{""" + f"{d:.0f}" + r"""} \; mm \\
    b_o &= """ + bo_eq + r""" = \mathbf{""" + f"{bo_mm:.0f}" + r"""} \; mm \\
    A_{crit} &= """ + ac_eq + r""" = \mathbf{""" + f"{acrit:.4f}" + r"""} \; m^2
    \end{aligned}
    """

def fmt_load_step(dl_fac, sw, sdl, ll_fac, ll, qu, h_final):
    # Detailed Load Calc
    h_m = h_final / 1000.0
    return r"""
    \begin{aligned}
    SW &= """ + f"{h_m:.2f}" + r""" \times 2400 = \mathbf{""" + f"{sw:.0f}" + r"""} \; kg/m^2 \\
    q_u &= """ + f"{dl_fac}({sw:.0f} + {sdl:.0f}) + {ll_fac}({ll:.0f})" + r""" \\
        &= \mathbf{""" + f"{qu:.0f}" + r"""} \; kg/m^2
    \end{aligned}
    """

def fmt_shear_detailed(qu, lx, ly, acrit, gamma, vu, phi, vc_mpa, bo, d, phi_vc, ratio):
    # 1. Vu Substitution
    area = lx * ly
    vu_sub = f"{qu:.0f} \\times ({area:.2f} - {acrit:.3f}) \\times {gamma:.2f}"
    
    # 2. PhiVc Substitution
    # phi * vc * bo * d / 9.81
    vc_sub = f"0.75 \\times {vc_mpa:.2f} \\times {bo:.0f} \\times {d:.0f}"
    
    status = "SAFE" if ratio <= 1.0 else "FAIL"
    color = "green" if ratio <= 1.0 else "red"
    
    return r"""
    \begin{aligned}
    V_u &= q_u \times (Area - A_{crit}) \times \gamma_{unb} \\
        &= """ + vu_sub + r""" \\
        &= \mathbf{""" + f"{vu:,.0f}" + r"""} \; kg \\[0.8em]
    \phi V_c &= \frac{0.75 \times v_{min} \times b_o \times d}{9.80665} \\
             &= \frac{""" + vc_sub + r"""}{9.80665} \\
             &= \mathbf{""" + f"{phi_vc:,.0f}" + r"""} \; kg \\[0.8em]
    Ratio &= \frac{V_u}{\phi V_c} = \frac{""" + f"{vu:,.0f}" + r"""}{""" + f"{phi_vc:,.0f}" + r"""} \\
          &= \mathbf{""" + f"{ratio:.2f}" + r"""} \; (\text{""" + status + r"""})
    \end{aligned}
    """

def fmt_flexure_calc(strip_name, coeff, mo, mu, fy, d_cm, as_req):
    # As = (Mu * 100) / (0.9 * fy * 0.9 * d)
    # Numerical sub for As
    denom = f"0.9 \\times {fy:.0f} \\times 0.9 \\times {d_cm:.1f}"
    
    return r"""
    \underline{\text{""" + strip_name + r"""}} \\
    \begin{aligned}
    M_u &= """ + f"{coeff}" + r""" \times M_o = \mathbf{""" + f"{mu:,.0f}" + r"""} \; kg \cdot m \\
    A_s &= \frac{M_u \times 100}{\phi f_y j d} = \frac{""" + f"{mu:,.0f}" + r""" \times 100}{""" + denom + r"""} \\
        &= \mathbf{""" + f"{as_req:.2f}" + r"""} \; cm^2
    \end{aligned}
    """
