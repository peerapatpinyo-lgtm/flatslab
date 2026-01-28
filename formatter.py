import streamlit as st

def fmt_flexure_design(name, coeff, mo, mu, fy, d_cm, as_req, as_min, as_design, bar_area, theo_spacing, use_spacing, db_size):
    # 1. Moment
    mu_sub = f"{coeff} \\times {mo:,.0f}"
    
    # 2. As Req Substitution
    # As = (Mu * 100) / (0.9 * fy * 0.9 * d)
    num_sub = f"{mu:,.0f} \\times 10^5"
    den_sub = f"0.9 \\times {fy:.0f} \\times 0.9 \\times {d_cm:.1f}"
    
    # 3. As Min Substitution
    # Shown only once per block for clarity, but derived here
    # As_min check text
    check_logic = r"\mathbf{>}" if as_req > as_min else r"\mathbf{<}"
    gov_text = "Req" if as_req > as_min else "Min"
    
    # 4. Spacing Substitution
    # S = (100 * ab) / as
    spacing_sub = f"\\frac{{100 \\times {bar_area:.2f}}}{{{as_design:.2f}}}"
    
    return r"""
    \underline{\textbf{""" + name + r"""}} \\
    \begin{aligned}
    M_{strip} &= C_s \times M_o = """ + mu_sub + r""" = \mathbf{""" + f"{mu:,.0f}" + r"""} \; kg \cdot m \\
    A_{s,req} &= \frac{M_{strip} \times 10^5}{0.9 f_y (0.9d)} = \frac{""" + num_sub + r"""}{""" + den_sub + r"""} = \mathbf{""" + f"{as_req:.2f}" + r"""} \; cm^2/m \\
    \text{Check} &: A_{s,req} \; """ + check_logic + r""" \; A_{s,min} \quad \rightarrow \text{Use } \mathbf{""" + f"{as_design:.2f}" + r"""} \; cm^2/m \\
    \text{Spacing} &= \frac{100 \times A_{bar}}{A_{s,use}} = """ + spacing_sub + r""" = """ + f"{theo_spacing:.1f}" + r""" \; cm \\
    \therefore \text{Use} &: \mathbf{DB""" + f"{db_size} @ {use_spacing:.2f}" + r"""} \; m \quad (\text{Round down})
    \end{aligned}
    """

def fmt_as_min_calc(b, h_cm, as_min):
    sub = f"0.0018 \\times {b:.0f} \\times {h_cm:.0f}"
    return r"""
    \begin{aligned}
    A_{s,min} &= 0.0018 \times b \times h \\
              &= """ + sub + r""" \\
              &= \mathbf{""" + f"{as_min:.2f}" + r"""} \; cm^2/m
    \end{aligned}
    """

# Keep existing helpers for shear/geom
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
