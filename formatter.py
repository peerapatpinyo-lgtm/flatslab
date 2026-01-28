import streamlit as st

def fmt_min_thickness(ln, denom, h_min, h_actual):
    return r"""
    \begin{aligned}
    h_{min} &= \frac{\ell_n}{""" + f"{denom:.0f}" + r"""} = \frac{""" + f"{ln*1000:.0f}" + r"""}{""" + f"{denom:.0f}" + r"""} = \mathbf{""" + f"{h_min:.1f}" + r"""} \; mm \\
    h_{use} &= \mathbf{""" + f"{h_actual:.0f}" + r"""} \; mm \quad (\text{Selected})
    \end{aligned}
    """

def fmt_shear_demand(qu, lx, ly, acrit, gamma, vu):
    # Substitution string
    area_calc = f"({lx} \\times {ly} - {acrit:.3f})"
    sub_line = f"{qu:.0f} \\times {area_calc} \\times {gamma:.1f}"
    
    return r"""
    \begin{aligned}
    V_u &= q_u \times (L_x L_y - A_{crit}) \times \gamma_{unb} \\
        &= """ + sub_line + r""" \\
        &= \mathbf{""" + f"{vu:,.0f}" + r"""} \; kg
    \end{aligned}
    """

def fmt_shear_capacity(phi, vc_mpa, bo_mm, d_mm, phi_vc_ton):
    # Substitution string for Unit Conversion
    # (0.75 * vc * bo * d) / (9.81 * 1000)
    numerator = f"{phi} \\times {vc_mpa:.2f} \\times {bo_mm:.0f} \\times {d_mm:.0f}"
    denominator = r"9.80665 \times 1000"
    
    return r"""
    \begin{aligned}
    \phi V_c &= \frac{\phi \cdot v_{min} \cdot b_o \cdot d}{g \cdot 1000} \\
             &= \frac{""" + numerator + r"""}{""" + denominator + r"""} \\
             &= \mathbf{""" + f"{phi_vc_ton:,.2f}" + r"""} \; Tons \approx \mathbf{""" + f"{phi_vc_ton*1000:,.0f}" + r"""} \; kg
    \end{aligned}
    """

def fmt_flexure_strip(name, coeff, mo, mu, fy, d_cm, as_req):
    # 1. Moment Sub
    mu_sub = f"{coeff} \\times {mo:,.0f}"
    
    # 2. As Sub
    # As = (Mu * 10^5) / (0.9 * fy * 0.9 * d)
    num = f"{mu:,.0f} \\times 10^5"
    den = f"0.9 \\times {fy:.0f} \\times 0.9 \\times {d_cm:.1f}"
    
    return r"""
    \textbf{""" + name + r"""} \\
    \begin{aligned}
    M_{strip} &= C \times M_o = """ + mu_sub + r""" = \mathbf{""" + f"{mu:,.0f}" + r"""} \; kg \cdot m \\
    A_s &= \frac{M_{strip} \times 10^5}{0.9 f_y (0.9 d)} = \frac{""" + num + r"""}{""" + den + r"""} \\
        &= \mathbf{""" + f"{as_req:.2f}" + r"""} \; cm^2
    \end{aligned}
    """
