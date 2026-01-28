def fmt_qu_calc(dl_fac, sw, sdl, ll_fac, ll, qu_val):
    # Load: 0 decimal places for input, 2 for result if needed, but usually integer is clean for loads
    return r"""
    \begin{aligned}
    SW &= h \times 2400 = \mathbf{""" + f"{sw:.0f}" + r"""} \; kg/m^2 \\
    q_u &= """ + f"{dl_fac}(SW + SDL) + {ll_fac}(LL) \\\\" + r"""
        &= """ + f"{dl_fac}({sw:.0f} + {sdl:.0f}) + {ll_fac}({ll:.0f}) \\\\" + r"""
        &= \mathbf{""" + f"{qu_val:.0f}" + r"""} \; kg/m^2
    \end{aligned}
    """

def fmt_geometry_trace(c1_mm, c2_mm, d_mm, bo_mm, pos):
    # Shows the explicit addition for bo
    c1 = c1_mm
    c2 = c2_mm
    d = d_mm
    
    if pos == "Interior":
        formula = r"2(c_1 + d) + 2(c_2 + d)"
        sub = f"2({c1:.0f} + {d:.0f}) + 2({c2:.0f} + {d:.0f})"
    elif pos == "Edge":
        formula = r"2(c_1 + d/2) + (c_2 + d)"
        sub = f"2({c1:.0f} + {d/2:.0f}) + ({c2:.0f} + {d:.0f})"
    else: # Corner
        formula = r"(c_1 + d/2) + (c_2 + d/2)"
        sub = f"({c1:.0f} + {d/2:.0f}) + ({c2:.0f} + {d/2:.0f})"
        
    return r"""
    \begin{aligned}
    d &= h - \text{cover} - d_b/2 = \mathbf{""" + f"{d:.0f}" + r"""} \; mm \\
    b_o &= """ + formula + r""" \\
        &= """ + sub + r""" \\
        &= \mathbf{""" + f"{bo_mm:.0f}" + r"""} \; mm
    \end{aligned}
    """

def fmt_shear_capacity_sub(fc, beta, alpha, d, bo):
    # Stress: 2 decimal places
    return r"""
    \begin{aligned}
    v_{c1} &= 0.33\sqrt{""" + f"{fc:.1f}" + r"""} = \mathbf{""" + f"{0.33 * (fc**0.5):.2f}" + r"""} \; MPa \\
    v_{c2} &= 0.17(1 + \frac{2}{""" + f"{beta:.2f}" + r"""})\sqrt{""" + f"{fc:.1f}" + r"""} \\
    v_{c3} &= 0.083(2 + \frac{""" + f"{alpha} \cdot {d:.0f}" + r"""}{""" + f"{bo:.0f}" + r"""})\sqrt{""" + f"{fc:.1f}" + r"""}
    \end{aligned}
    """

def fmt_flexure_trace(strip_name, coeff, mo, mu, fy, d_cm, as_req):
    # Moment: 2 decimal places with comma
    return r"""
    \textbf{""" + strip_name + r"""} \; (C = """ + f"{coeff}" + r"""): \\
    \begin{aligned}
    M_u &= """ + f"{coeff} \\times {mo:,.2f}" + r""" = \mathbf{""" + f"{mu:,.2f}" + r"""} \; kg \cdot m \\
    A_s &= \frac{M_u}{0.9 f_y (0.9d)} = \frac{""" + f"{mu * 100:.0f}" + r"""}{0.9( """ + f"{fy:.0f}" + r""")(0.9 \cdot """ + f"{d_cm:.1f}" + r""")} \\
        &= \mathbf{""" + f"{as_req:.2f}" + r"""} \; cm^2
    \end{aligned}
    """
