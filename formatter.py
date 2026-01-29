import streamlit as st

def fmt_rebar_verification(name, coeff, mo, mu, fy, d_cm, as_req_calc, as_min, as_target, 
                           user_db, user_spacing, bar_area, as_prov, status, color):
    
    # 1. Moment & As Required
    mu_sub = f"{coeff} \\times {mo:,.0f}"
    
    # 2. As Calculation
    req_sub = f"\\frac{{{mu:,.0f} \\times 100}}{{0.9 \\times {fy:.0f} \\times 0.9 \\times {d_cm:.1f}}}"
    
    # 3. Provided Logic
    # As_prov = (A_bar * 1000) / Spacing
    prov_sub = f"\\frac{{{bar_area:.2f} \\times 1000}}{{{user_spacing:.0f}}}"
    
    # Status Symbol
    status_icon = r"\checkmark" if "SAFE" in status else r"\times"
    check_ineq = r"\ge" if as_prov >= as_target else r"<"
    
    return r"""
    \underline{\textbf{""" + name + r"""}} \\
    \begin{aligned}
    M_u &= """ + f"{coeff} M_o = {mu:,.0f}" + r""" \; kg \cdot m \\
    A_{s,req} &= """ + req_sub + r""" = \mathbf{""" + f"{as_req_calc:.2f}" + r"""} \; cm^2/m \\
    \text{Control} &: \max(A_{s,req}, A_{s,min}) = \mathbf{""" + f"{as_target:.2f}" + r"""} \; cm^2/m \\
    \text{Try} &: \text{DB""" + f"{user_db} @ {user_spacing}" + r""" mm} \quad (A_{bar} = """ + f"{bar_area:.2f}" + r""" cm^2) \\
    A_{s,prov} &= \frac{A_{bar} \times 1000}{Spacing} = """ + prov_sub + r""" = \mathbf{""" + f"{as_prov:.2f}" + r"""} \; cm^2/m \\
    \text{Check} &: """ + f"{as_prov:.2f} {check_ineq} {as_target:.2f}" + r""" \quad \Rightarrow \quad \textbf{\textcolor{""" + color + r"""}{""" + status + r"""}}
    \end{aligned}
    """

def fmt_load_trace(dl_fac, sw, sdl, ll_fac, ll, qu):
    sub_str = f"{dl_fac}({sw:.0f} + {sdl:.0f}) + {ll_fac}({ll:.0f})"
    return r"""
    \begin{aligned}
    q_u &= 1.4(SW + SDL) + 1.7(LL) \\
        &= """ + sub_str + r""" \\
        &= \mathbf{""" + f"{qu:.0f}" + r"""} \; kg/m^2
    \end{aligned}
    """

def fmt_vu_detailed(qu, lx, ly, acrit, gamma, vu):
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
    num = f"{phi} \\times {vc_mpa:.2f} \\times {bo:.0f} \\times {d:.0f}"
    den = r"9.80665 \times 1000"
    return r"""
    \begin{aligned}
    \phi V_c &= \frac{\phi \cdot v_{min} \cdot b_o \cdot d}{g \cdot 1000} \\
             &= \frac{""" + num + r"""}{""" + den + r"""} \\
             &= \mathbf{""" + f"{phi_vc_ton:,.2f}" + r"""} \; Tons
    \end{aligned}
    """
