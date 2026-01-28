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
    # แสดงการแทนค่าสูตร ACI ทั้ง 3 สมการ
    return r"""
    \begin{aligned}
    v_{c1} &= 0.33\sqrt{f_c'} = 0.33\sqrt{""" + f"{fc_val:.1f}" + r"""} \\\\
    v_{c2} &= 0.17(1 + \frac{2}{\beta})\sqrt{f_c'} = 0.17(1 + \frac{2}{""" + f"{beta:.2f}" + r"""})\sqrt{""" + f"{fc_val:.1f}" + r"""} \\\\
    v_{c3} &= 0.083(2 + \frac{\alpha_s d}{b_o})\sqrt{f_c'} = 0.083(2 + \frac{""" + f"{alpha_s} \cdot {d_mm:.0f}" + r"""}{""" + f"{bo_mm:.0f}" + r"""})\sqrt{""" + f"{fc_val:.1f}" + r"""}
    \end{aligned}
    """

def fmt_punching_comparison(vu_kg, phi_vc_kg, ratio, is_pass):
    # แสดงบรรทัดสรุปผลการตรวจสอบแรงเฉือน
    status_color = "green" if is_pass else "red"
    status_text = "OK" if is_pass else "FAIL"
    
    return r"""
    \begin{aligned}
    V_u &= \mathbf{""" + f"{vu_kg/1000:.2f}" + r"""} \; Tons \\\\
    \phi V_c &= \mathbf{""" + f"{phi_vc_kg/1000:.2f}" + r"""} \; Tons \\\\
    Ratio &= \frac{V_u}{\phi V_c} = \mathbf{""" + f"{ratio:.2f}" + r"""} \quad \rightarrow \quad \color{""" + status_color + r"""}{\textbf{""" + status_text + r"""}}
    \end{aligned}
    """

def fmt_rebar_calc(strip_name, coeff, mo, mu, fy, d_cm, as_req):
    # แสดงการคำนวณ As สำหรับแต่ละ Strip
    return r"""
    \textbf{""" + strip_name + r"""} \; (Coeff """ + f"{coeff}" + r"""): \\
    \begin{aligned}
    M_u &= """ + f"{coeff} M_o = {mu/1000:.2f} \; T \cdot m \\\\" + r"""
    A_s &= \frac{M_u}{0.9 f_y (0.9d)} = \frac{""" + f"{mu*100:.2f}" + r"""}{0.9 \cdot """ + f"{fy}" + r""" \cdot 0.9 \cdot """ + f"{d_cm:.2f}" + r"""} \\\\
        &= \mathbf{""" + f"{as_req:.2f}" + r"""} \; cm^2
    \end{aligned}
    """
