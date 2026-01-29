def fmt_design_philosophy():
    return r"""
    \small
    \textbf{Design Philosophy:} \\
    \text{- Code: ACI 318-19 | Factors: } \phi_v = 0.75, \phi_m = 0.90 \\
    \text{- Load: } 1.4DL + 1.7LL \text{ (Local Practice)}
    """

def fmt_load_trace(dl_fac, sw, sdl, ll_fac, ll, qu):
    sub_str = f"{dl_fac}({sw:.0f} + {sdl:.0f}) + {ll_fac}({ll:.0f})"
    return r"""
    \begin{aligned}
    q_u &= 1.4(SW + SDL) + 1.7(LL) \\
        &= """ + sub_str + r""" = \mathbf{""" + f"{qu:.0f}" + r"""} \; kg/m^2
    \end{aligned}
    """

def fmt_stiffness_substitution(efm):
    """
    Shows step-by-step substitution for EFM stiffness.
    """
    ec = efm['Ec'] / 1e9 # GPa
    ks = efm['Ks'] / 1e6
    kc = efm['Sum_Kc'] / 1e6
    kt = efm['Kt'] / 1e6
    kec = efm['Kec'] / 1e6
    
    return r"""
    \textbf{Stiffness Calculation (Step-by-Step):} \\
    \begin{aligned}
    E_c &= 4700\sqrt{f'_c} \approx """ + f"{ec:.1f}" + r""" \times 10^9 \; Pa \\
    K_s &= \frac{4E_c I_s}{L_x} \rightarrow \mathbf{""" + f"{ks:.1f}" + r"""} \times 10^6 \; N\cdot m \\
    \Sigma K_c &= \frac{4E_c I_c}{L_{up}} + \frac{4E_c I_c}{L_{low}} \rightarrow \mathbf{""" + f"{kc:.1f}" + r"""} \times 10^6 \; N\cdot m \\
    K_t &= \frac{9E_c C}{L_2(1-c_2/L_2)^3} \rightarrow \mathbf{""" + f"{kt:.1f}" + r"""} \times 10^6 \; N\cdot m \\
    \frac{1}{K_{ec}} &= \frac{1}{\Sigma K_c} + \frac{1}{K_t} \Rightarrow K_{ec} = \mathbf{""" + f"{kec:.1f}" + r"""} \times 10^6 \; N\cdot m
    \end{aligned}
    """

def fmt_rebar_verification(name, coeff, mo, mu, fy, d_cm, as_req_calc, as_min, as_target, 
                           user_db, user_spacing, bar_area, as_prov, status, color, max_s):
    mu_sub = f"{mu:,.0f}"
    tex_color = "teal" if color == "green" else "red"
    
    return r"""
    \underline{\textbf{""" + name + r"""}} \\
    \begin{aligned}
    M_u &= """ + mu_sub + r""" \; kg \cdot m \\
    A_{s,req} &= \mathbf{""" + f"{as_req_calc:.2f}" + r"""} \; cm^2/m \quad (\text{Min } """ + f"{as_min:.2f}" + r""") \\
    \text{Try} &: \text{DB""" + f"{user_db} @ {user_spacing}" + r""" mm} \rightarrow A_{s,prov} = \mathbf{""" + f"{as_prov:.2f}" + r"""} \\
    \text{Check} &: S_{max} = """ + f"{max_s}" + r""" mm \rightarrow \textbf{\textcolor{""" + tex_color + r"""}{""" + status + r"""}}
    \end{aligned}
    """
