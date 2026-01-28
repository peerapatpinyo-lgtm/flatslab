def fmt_qu_calc(dl_fac, sw, sdl, ll_fac, ll, qu_val):
    return r"""
    \begin{aligned}
    q_u &= """ + f"{dl_fac}(SW + SDL) + {ll_fac}(LL) \\\\" + r"""
        &= """ + f"{dl_fac}({sw:.0f} + {sdl}) + {ll_fac}({ll}) \\\\" + r"""
        &= \mathbf{""" + f"{qu_val:.2f}" + r"""} \; kg/m^2
    \end{aligned}
    """

def fmt_mo_calc(qu, ly, ln, mo_val):
    return r"""
    \begin{aligned}
    M_o &= \frac{q_u \ell_2 (\ell_n)^2}{8} \\\\
        &= \frac{""" + f"{qu:.2f} \\times {ly} \\times ({ln:.2f})^2" + r"""}{8} \\\\
        &= \mathbf{""" + f"{mo_val:,.2f}" + r"""} \; kg \cdot m
    \end{aligned}
    """

def fmt_shear_capacity_sub(fc_val, beta, alpha_s, d_mm, bo_mm):
    return r"""
    \begin{aligned}
    v_{c1} &= 0.33\sqrt{f_c'} = 0.33\sqrt{""" + f"{fc_val:.1f}" + r"""} \\\\
    v_{c2} &= 0.17(1 + \frac{2}{\beta})\sqrt{f_c'} = 0.17(1 + \frac{2}{""" + f"{beta:.2f}" + r"""})\sqrt{""" + f"{fc_val:.1f}" + r"""} \\\\
    v_{c3} &= 0.083(2 + \frac{\alpha_s d}{b_o})\sqrt{f_c'} = 0.083(2 + \frac{""" + f"{alpha_s} \\cdot {d_mm:.0f}" + r"""}{""" + f"{bo_mm:.0f}" + r"""})\sqrt{""" + f"{fc_val:.1f}" + r"""}
    \end{aligned}
    """

def fmt_as_req(mu, d_cm, fy, as_val):
    return r"""
    A_s = \frac{M_u}{\phi f_y (0.9d)} = \frac{""" + f"{mu*100:.2f}" + r"""}{0.9 \times """ + f"{fy}" + r""" \times 0.9 \times """ + f"{d_cm:.2f}" + r"""} = \mathbf{""" + f"{as_val:.2f}" + r"""} \; cm^2
    """
