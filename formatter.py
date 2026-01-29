def fmt_header(title):
    return f"\\textbf{{{title}}}"

def fmt_load_trace(h_mm, sdl, ll, sw_res, qu_res):
    h_m = h_mm / 1000.0
    return r"""
    \begin{aligned}
    SW &= \text{Thickness} \times 2400 = %.2f \times 2400 = %.1f \; kg/m^2 \\
    DL &= SW + SDL = %.1f + %.1f = %.1f \; kg/m^2 \\
    q_u &= 1.4(DL) + 1.7(LL) \\
        &= 1.4(%.1f) + 1.7(%.1f) \\
        &= \mathbf{%.1f} \; kg/m^2
    \end{aligned}
    """ % (h_m, sw_res, sw_res, sdl, sw_res + sdl, sw_res + sdl, ll, qu_res)

def fmt_d_calc(h, cover, db_avg, d_res):
    return r"""
    d = h - c_c - \frac{d_{b,avg}}{2} = %.0f - %.0f - %.1f = \mathbf{%.1f} \; mm
    """ % (h, cover, db_avg, d_res)

def fmt_shear_geometry(c1, c2, d, bo, method_pos):
    return r"""
    \begin{aligned}
    \text{Position} &: \text{%s} \\
    b_o &= 2(c_1 + d) + 2(c_2 + d) \\
        &= 2(%.0f + %.0f) + 2(%.0f + %.0f) \\
        &= \mathbf{%.0f} \; mm
    \end{aligned}
    """ % (method_pos, c1, d, c2, d, bo)

def fmt_shear_capacity(fc, beta, alpha, d, bo, vc1, vc2, vc3, vc_final, phi_vc):
    return r"""
    \begin{aligned}
    V_{c1} &= 0.33\sqrt{f'_c} b_o d = 0.33\sqrt{%.1f}(%.0f)(%.0f)/1000 = %.1f \; kN \\
    V_{c2} &= 0.17(1 + \frac{2}{\beta})\sqrt{f'_c} b_o d = 0.17(1 + \frac{2}{%.1f})\sqrt{%.1f}(%.0f)(%.0f)/1000 = %.1f \; kN \\
    V_{c3} &= 0.083(\frac{\alpha_s d}{b_o} + 2)\sqrt{f'_c} b_o d = 0.083(\frac{%.0f \cdot %.0f}{%.0f} + 2)\sqrt{%.1f}(%.0f)(%.0f)/1000 = %.1f \; kN \\
    \\
    V_c &= \min(V_{c1}, V_{c2}, V_{c3}) = \mathbf{%.1f} \; kN \\
    \phi V_c &= 0.75 \times V_c = \mathbf{%.1f} \; kN \quad (\approx %.1f \; tons)
    \end{aligned}
    """ % (fc, bo, d, vc1/1000, 
           beta, fc, bo, d, vc2/1000, 
           alpha, d, bo, fc, bo, d, vc3/1000,
           vc_final/1000, phi_vc/1000, phi_vc/9806.65)

def fmt_shear_check(vu, phi_vc):
    ratio = vu / phi_vc
    res = "OK" if ratio <= 1.0 else "FAIL"
    color = "green" if ratio <= 1.0 else "red"
    return r"""
    \text{Check: } \frac{V_u}{\phi V_c} = \frac{%.1f}{%.1f} = \textcolor{%s}{\mathbf{%.2f}} \quad (\text{%s})
    """ % (vu/1000, phi_vc/1000, color, ratio, res)

def fmt_moment_calc(mu, fy, d, a_req, a_min, a_prov, db, s, status):
    res_text = "OK" if status == "SAFE" else "FAIL"
    col = "green" if status == "SAFE" else "red"
    return r"""
    \begin{aligned}
    M_u &= %.1f \; kg\cdot m \\
    A_{s,req} &\approx \frac{M_u}{0.9 f_y (0.9d)} = \frac{%.0f \cdot 100}{0.9(%.0f)(0.9 \cdot %.1f)} = %.2f \; cm^2 \\
    A_{s,min} &= 0.0018 b h = 0.0018(100)(%.1f) = %.2f \; cm^2 \\
    A_{s,target} &= \max(%.2f, %.2f) = \mathbf{%.2f} \; cm^2 \\
    \\
    \text{Try } \textbf{DB%d @ %.0f mm} &\rightarrow A_{s,prov} = \mathbf{%.2f} \; cm^2 \\
    \text{Status} &: \textcolor{%s}{\textbf{%s}}
    \end{aligned}
    """ % (mu, mu, fy, d/10, a_req, 
           d*10/10 + 3.0, a_min,
           a_req, a_min, max(a_req, a_min),
           db, s, a_prov, col, res_text)
