import streamlit as st
import numpy as np

# Set page layout
st.set_page_config(page_title="Detailed Flat Slab Calculation", layout="wide")

# --- Helper Function สำหรับแสดงการคำนวณแบบละเอียด ---
def show_calculation_step(title, latex_formula, substitution_str, result_str, unit, note=""):
    """
    ฟังก์ชันสำหรับแสดงผลลัพธ์ทีละขั้นตอน: สูตร -> การแทนค่า -> คำตอบ
    """
    st.markdown(f"#### {title}")
    if note:
        st.caption(f"*{note}*")
    
    # 1. แสดงสูตร (Symbolic)
    st.latex(latex_formula)
    
    # 2. แสดงการแทนค่า (Substitution)
    # ใช้ text ธรรมดาหรือ latex ก็ได้ แต่ latex จะสวยกว่า
    st.markdown(f"**แทนค่า:**")
    st.latex(substitution_str)
    
    # 3. แสดงผลลัพธ์
    st.success(f"**= {result_str} {unit}**")
    st.markdown("---")

st.title("🏗️ Detailed Flat Slab Analysis (ACI 318)")
st.markdown("ระบบคำนวณพื้นไร้คาน แสดงวิธีทำละเอียดทุกขั้นตอน (Formula -> Substitution -> Result)")

# ==========================================
# 1. INPUT SECTION
# ==========================================
with st.sidebar:
    st.header("1. Design Parameters")
    
    st.subheader("Material Properties")
    fc = st.number_input("f'c (ksc)", value=240.0, step=10.0)
    fy = st.number_input("fy (ksc)", value=4000.0, step=100.0)
    
    st.subheader("Geometry (Dimensions)")
    L1 = st.number_input("L1: Span Length (ทิศทางที่คิด) (m)", value=6.0, step=0.1)
    L2 = st.number_input("L2: Transverse Span (ทิศทางขวาง) (m)", value=5.0, step=0.1)
    h_slab = st.number_input("Slab Thickness (cm)", value=20.0, step=1.0)
    l_c = st.number_input("Storey Height (m)", value=3.0, step=0.1)
    
    st.subheader("Column Size")
    c1 = st.number_input("c1 (Parallel to L1) (cm)", value=40.0, step=5.0)
    c2 = st.number_input("c2 (Transverse) (cm)", value=40.0, step=5.0)
    
    st.subheader("Loads")
    SDL = st.number_input("Superimposed Dead Load (kg/m²)", value=100.0)
    LL = st.number_input("Live Load (kg/m²)", value=300.0)

# ==========================================
# 2. PRE-CALCULATION (Internal Logic)
# ==========================================
# Convert units for calculation (Everything to kg, cm)
L1_cm = L1 * 100
L2_cm = L2 * 100
lc_cm = l_c * 100
Ec = 15100 * np.sqrt(fc) # ksc

# Load Calcs
w_self = (h_slab / 100) * 2400 # kg/m2
w_dead = w_self + SDL
w_u = 1.2 * w_dead + 1.6 * LL # kg/m2

# ==========================================
# 3. DISPLAY: LOAD & MATERIAL
# ==========================================
st.header("Step 1: Material & Load Properties")

col1, col2 = st.columns(2)

with col1:
    show_calculation_step(
        "Modulus of Elasticity (Ec)",
        r"E_c = 15,100 \sqrt{f'_c}",
        fr"E_c = 15,100 \times \sqrt{{{fc:.0f}}}",
        f"{Ec:,.2f}",
        "ksc"
    )

with col2:
    # Load combination detail
    show_calculation_step(
        "Factored Load (Wu)",
        r"w_u = 1.2(DL_{self} + SDL) + 1.6(LL)",
        fr"w_u = 1.2({w_self:.1f} + {SDL}) + 1.6({LL})",
        f"{w_u:,.2f}",
        "kg/m²"
    )

# ==========================================
# 4. EQUIVALENT FRAME METHOD (DETAILED)
# ==========================================
st.header("Step 2: Equivalent Frame Method (EFM) Stiffness Calculation")
st.info("ส่วนนี้จะคำนวณ Stiffness ของจุดต่อ (Joint) อย่างละเอียด เพื่อหา Distribution Factor (DF)")

# --- 2.1 Slab Stiffness (Ks) ---
Is = (L2_cm * (h_slab**3)) / 12
Ks = (4 * Ec * Is) / L1_cm

st.subheader("2.1 Slab Stiffness ($K_s$)")
with st.expander("ดูวิธีทำละเอียด Ks", expanded=True):
    # Inertia
    show_calculation_step(
        "Slab Moment of Inertia (Is)",
        r"I_s = \frac{L_2 \cdot h^3}{12}",
        fr"I_s = \frac{{{L2_cm:.0f} \cdot {h_slab:.0f}^3}}{{12}}",
        f"{Is:,.2f}",
        "cm⁴",
        note="คิดเต็มหน้าตัด (Gross Section)"
    )
    # Stiffness
    show_calculation_step(
        "Slab Stiffness (Ks)",
        r"K_s = \frac{4 E_c I_s}{L_1}",
        fr"K_s = \frac{{4 \cdot {Ec:,.2f} \cdot {Is:,.2f}}}{{{L1_cm:.0f}}}",
        f"{Ks:,.2f}",
        "kg-cm"
    )

# --- 2.2 Column Stiffness (Kc) ---
Ic = (c2 * (c1**3)) / 12
Kc = (4 * Ec * Ic) / lc_cm

st.subheader("2.2 Column Stiffness ($K_c$)")
with st.expander("ดูวิธีทำละเอียด Kc", expanded=True):
    show_calculation_step(
        "Column Moment of Inertia (Ic)",
        r"I_c = \frac{c_2 \cdot c_1^3}{12}",
        fr"I_c = \frac{{{c2:.0f} \cdot {c1:.0f}^3}}{{12}}",
        f"{Ic:,.2f}",
        "cm⁴"
    )
    show_calculation_step(
        "Column Stiffness (Kc)",
        r"K_c = \frac{4 E_c I_c}{l_c}",
        fr"K_c = \frac{{4 \cdot {Ec:,.2f} \cdot {Ic:,.2f}}}{{{lc_cm:.0f}}}",
        f"{Kc:,.2f}",
        "kg-cm",
        note="สมมติปลายอีกด้านเป็น Fixed (Far end fixed)"
    )

# --- 2.3 Torsional Stiffness (Kt) ---
st.subheader("2.3 Torsional Member Stiffness ($K_t$)")
st.markdown("ส่วนที่ยากที่สุดของ EFM คือการหาค่าความแข็งของการบิดตัว (Torsion) ด้านข้างเสา")

# Calculate C (Torsional Constant)
x = min(c1, h_slab)
y = max(c1, h_slab) # Note: For Rectangular section approx
term1 = (1 - 0.63 * (x/y))
term2 = (x**3 * y) / 3
C = term1 * term2

# Calculate Kt
# Formula: Kt = sum( 9EcC / [ L2(1 - c2/L2)^3 ] )
# สมมติมี Torsional member 2 ด้าน (ซ้ายขวาของเสา) -> คูณ 2
denominator_part = (1 - (c2/L2_cm))**3
Kt_one_side = (9 * Ec * C) / (L2_cm * denominator_part)
Kt = 2 * Kt_one_side 

with st.expander("ดูวิธีทำละเอียด Kt (Complex)", expanded=True):
    st.write(f"**พิจารณาหน้าตัดรับแรงบิด:** x (ด้านสั้น) = {x} cm, y (ด้านยาว) = {y} cm")
    
    # Show C Calculation
    show_calculation_step(
        "Torsional Constant (C)",
        r"C = \left(1 - 0.63 \frac{x}{y}\right) \frac{x^3 y}{3}",
        fr"C = \left(1 - 0.63 \frac{{{x}}}{{{y}}}\right) \frac{{{x}^3 \cdot {y}}}{{3}}",
        f"{C:,.2f}",
        "cm⁴"
    )
    
    # Show Kt Calculation
    st.markdown("#### Torsional Stiffness ($K_t$)")
    st.latex(r"K_t = \sum \frac{9 E_c C}{L_2 (1 - \frac{c_2}{L_2})^3}")
    st.markdown("**แทนค่า (คิด 2 ด้าน ซ้าย-ขวา):**")
    
    # Generate substitution string for Kt
    sub_kt = fr"K_t = 2 \times \frac{{9 \cdot {Ec:,.2f} \cdot {C:,.2f}}}{{{L2_cm:.0f} (1 - \frac{{{c2}}}{{{L2_cm}}})^3}}"
    st.latex(sub_kt)
    st.success(f"**= {Kt:,.2f} kg-cm**")

# --- 2.4 Equivalent Column Stiffness (Kec) ---
st.subheader("2.4 Equivalent Column Stiffness ($K_{ec}$)")
Sum_Kc = 2 * Kc # เสาบน + เสาล่าง
inv_Kec = (1/Sum_Kc) + (1/Kt)
Kec = 1/inv_Kec

with st.expander("ดูวิธีทำละเอียด Kec", expanded=True):
    st.markdown(f"**Sum of Columns ($\Sigma K_c$):** เสาบน + เสาล่าง = {Kc:,.2f} + {Kc:,.2f} = **{Sum_Kc:,.2f}** kg-cm")
    
    show_calculation_step(
        "Equivalent Stiffness Formula",
        r"\frac{1}{K_{ec}} = \frac{1}{\Sigma K_c} + \frac{1}{K_t}",
        fr"\frac{{1}}{{K_{{ec}}}} = \frac{{1}}{{{Sum_Kc:,.2f}}} + \frac{{1}}{{{Kt:,.2f}}}",
        f"{Kec:,.2f}",
        "kg-cm",
        note="Kec จะมีค่าน้อยกว่า Sum Kc เสมอ เพราะถูกลดทอนด้วย Kt"
    )

# ==========================================
# 5. DISTRIBUTION FACTORS (DF)
# ==========================================
st.header("Step 3: Distribution Factors (DF)")
st.markdown("คำนวณสัดส่วนการกระจายโมเมนต์ที่จุดต่อ (Interior Joint)")

DF_slab = Ks / (Ks + Kec)
DF_col = Kec / (Ks + Kec) # This goes to the equivalent column

col_df1, col_df2 = st.columns(2)

with col_df1:
    show_calculation_step(
        "DF Slab (ถ่ายเข้าพื้น)",
        r"DF_{slab} = \frac{K_s}{K_s + K_{ec}}",
        fr"DF_{{slab}} = \frac{{{Ks:,.2f}}}{{{Ks:,.2f} + {Kec:,.2f}}}",
        f"{DF_slab:.4f}",
        "(-)"
    )

with col_df2:
    show_calculation_step(
        "DF Column (ถ่ายเข้าเสา)",
        r"DF_{col} = \frac{K_{ec}}{K_s + K_{ec}}",
        fr"DF_{{col}} = \frac{{{Kec:,.2f}}}{{{Ks:,.2f} + {Kec:,.2f}}}",
        f"{DF_col:.4f}",
        "(-)"
    )

st.warning(f"Note: ผลรวม DF ต้องเท่ากับ 1.00 -> ({DF_slab:.4f} + {DF_col:.4f} = {DF_slab+DF_col:.4f}) ✅")

# ==========================================
# 6. DIRECT DESIGN METHOD (MOMENT DISTRIBUTION)
# ==========================================
st.header("Step 4: Design Moments (Direct Design Method Check)")
ln = L1 - (c1/100)
Mo = (w_u * L2 * ln**2) / 8

st.subheader("4.1 Total Static Moment ($M_o$)")
show_calculation_step(
    "Static Moment",
    r"M_o = \frac{w_u L_2 l_n^2}{8}",
    fr"M_o = \frac{{{w_u:.2f} \cdot {L2} \cdot ({L1}-{c1/100})^2}}{{8}}",
    f"{Mo:,.2f}",
    "kg-m"
)

st.subheader("4.2 Moment Distribution Table")
st.markdown("ตารางกระจายโมเมนต์เข้าแถบเสา (Column Strip) และแถบกลาง (Middle Strip)")

# Coefficients (Simplified for Interior Span, Flat Plate)
# Negative Moment
neg_m = Mo * 0.65
neg_cs_ratio = 0.75
neg_ms_ratio = 0.25
# Positive Moment
pos_m = Mo * 0.35
pos_cs_ratio = 0.60
pos_ms_ratio = 0.40

data = {
    "Section": ["Negative Moment (-)", "Negative Moment (-)", "Positive Moment (+)", "Positive Moment (+)"],
    "Strip Type": ["Column Strip", "Middle Strip", "Column Strip", "Middle Strip"],
    "Total Moment Portion": [f"0.65 Mo = {neg_m:,.2f}", f"0.65 Mo = {neg_m:,.2f}", f"0.35 Mo = {pos_m:,.2f}", f"0.35 Mo = {pos_m:,.2f}"],
    "% Distribution": [f"{neg_cs_ratio*100}%", f"{neg_ms_ratio*100}%", f"{pos_cs_ratio*100}%", f"{pos_ms_ratio*100}%"],
    "Calculation": [
        f"{neg_m:,.2f} * {neg_cs_ratio}",
        f"{neg_m:,.2f} * {neg_ms_ratio}",
        f"{pos_m:,.2f} * {pos_cs_ratio}",
        f"{pos_m:,.2f} * {pos_ms_ratio}"
    ],
    "Design Moment (kg-m)": [
        neg_m * neg_cs_ratio,
        neg_m * neg_ms_ratio,
        pos_m * pos_cs_ratio,
        pos_m * pos_ms_ratio
    ]
}

df_res = st.dataframe(data)

st.success("🏁 การคำนวณเสร็จสิ้น: คุณสามารถนำค่า Design Moment ในตารางไปคำนวณเหล็กเสริม (As) ต่อได้เลย")
