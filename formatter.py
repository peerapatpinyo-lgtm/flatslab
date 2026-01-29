import streamlit as st

def fmt_design_philosophy():
    return r"""
    \small
    \textbf{Design Philosophy:} \\
    \text{- Code Reference: ACI 318-19 (Building Code Requirements for Structural Concrete)} \\
    \text{- Method: Direct Design Method (DDM) for Two-Way Slabs} \\
    \text{- Safety Factors: } \phi_{shear} = 0.75, \; \phi_{flexure} = 0.90 \\
    \text{- Load Factors: } U = 1.4(DL) + 1.7(LL) \; \text{(Local Practice Adjusted)}
    """

def fmt_bo_explanation(bo_str, bo_mm, d_mm):
    return r"""
    \text{Shear Perimeter } (b_o): \\
    b_o = """ + bo_str + r""" \\
    \text{Substitute } d = """ + f"{d_mm:.0f}" + r""" \; mm \rightarrow b_o = \mathbf{""" + f"{bo_mm:.0f}" + r"""} \; mm
    """

def fmt_rebar_verification(name, coeff, mo, mu, fy, d_cm, as_req_calc, as_min, as_target, 
                           user_db, user_spacing, bar_area, as_prov, status, color, max_s):
    
    mu_sub = f"{coeff:.2f} \\times {mo:,.0f}"
    
    # Status formatting
    status_icon = r"\checkmark" if "SAFE" in status else r"\times"
    
    return r"""
    \underline{\textbf{""" + name + r"""}} \\
    \begin{aligned}
    M_u &= """ + f"{mu_sub} = {mu:,.0f}" + r""" \; kg \cdot m \\
    A_{s,req} &= \mathbf{""" + f"{as_req_calc:.2f}" + r"""} \; cm^2/m \quad \text{vs} \quad A_{s,min} = """ + f"{as_min:.2f}" + r""" \\
    \text{Try} &: \text{DB""" + f"{user_db} @ {user_spacing}" + r""" mm} \rightarrow A_{s,prov} = \mathbf{""" + f"{as_prov:.2f}" + r"""} \; cm^2/m \\
    \text{Limits} &: S_{user} \le S_{max} (""" + f"{max_s}" + r""" mm) \quad \text{and} \quad A_{s,prov} \ge A_{s,req} \\
    \text{Result} &: \textbf{\textcolor{""" + color + r"""}{""" + status + r"""}}
    \end{aligned}
    """

# Keep existing helpers
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
