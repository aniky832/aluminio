import streamlit as st
import json
from fpdf import FPDF
import math
from datetime import datetime

# ---------- UTIL ----------
def r(x):
    return round(x, 1)

# ---------- FUNCIONES ----------
def optimizar_barras(piezas, largo=600):
    piezas = sorted(piezas, reverse=True)
    barras = []
    for p in piezas:
        colocado = False
        for b in barras:
            if sum(b) + p <= largo:
                b.append(p)
                colocado = True
                break
        if not colocado:
            barras.append([p])
    return barras

def calcular_materiales(todos):
    resumen = {}
    for p, piezas in todos.items():
        if p != "VIDRIO" and piezas:
            resumen[p] = len(optimizar_barras(piezas))

    total_area = sum(v["ancho"] * v["alto"] * v["cant"] for v in todos["VIDRIO"])
    resumen["VIDRIO"] = math.ceil(total_area / (330 * 214))
    return resumen

# ---------- PRECIOS ----------
PRECIOS_ALUMINIO = {
    "MT": {"RIEL SUPERIOR":187,"RIEL INFERIOR":187,"ZOCALO":177,"GANCHO":171,"JAMBA":159,"PIERNA":171},
    "CH": {"RIEL SUPERIOR":191,"RIEL INFERIOR":191,"ZOCALO":180,"GANCHO":171,"JAMBA":160,"PIERNA":171},
    "BR": {"RIEL SUPERIOR":192,"RIEL INFERIOR":192,"ZOCALO":183,"GANCHO":171,"JAMBA":167,"PIERNA":171},
    "CH.O": {"RIEL SUPERIOR":191,"RIEL INFERIOR":191,"ZOCALO":172,"GANCHO":169,"JAMBA":166,"PIERNA":169},
    "MD": {"RIEL SUPERIOR":215,"RIEL INFERIOR":215,"ZOCALO":192,"GANCHO":173,"JAMBA":177,"PIERNA":173}
}

PRECIOS_VIDRIO = {
    "Bronce": 500,
    "Incoloro": 490,
    "Gris": 780,
    "Estipoly Incoloro": 320
}

# ---------- APP ----------
st.set_page_config(layout="wide")
st.title("🛠️ Sistema Linea 25 PRO")

# SESSION
if "pedido" not in st.session_state:
    st.session_state.pedido = []

if "cotizacion" not in st.session_state:
    st.session_state.cotizacion = []

if "cot_m2" not in st.session_state:
    st.session_state.cot_m2 = []

# ---------- SIDEBAR ----------
with st.sidebar:
    st.header("📂 Proyecto")

    if st.session_state.pedido:
        st.download_button("Guardar Proyecto", json.dumps(st.session_state.pedido), "proyecto.json")

    file = st.file_uploader("Abrir Proyecto", type="json")
    if file:
        st.session_state.pedido = json.load(file)
        st.success("Proyecto cargado")

    if st.button("Nuevo Proyecto"):
        st.session_state.pedido = []
        st.rerun()

    modo = st.radio("Modo", ["Producción línea 25", "Cotización", "Cotización m²"])

# ================= PRODUCCIÓN =================
if modo == "Producción línea 25":

    st.header("Producción línea 25")

    anc = st.number_input("Ancho", 0.0, key="prod_a")
    alt = st.number_input("Alto", 0.0, key="prod_h")
    hojas = st.selectbox("Hojas", [2,3,4], key="prod_hojas")

    if st.button("Agregar"):
        if hojas == 2:
            z, cz, cp = (anc - 16)/2, 4, 2
        elif hojas == 3:
            z, cz, cp = (anc - 26.5)/3, 6, 4
        else:
            z, cz, cp = (anc - 30)/4, 8, 6

        st.session_state.pedido.append({
            "medida": f"{anc}x{alt}",
            "div": hojas,
            "detalles": {
                "JAMBA": {"medida": alt, "cant": 2},
                "RIEL SUPERIOR": {"medida": anc-1.5, "cant": 1},
                "RIEL INFERIOR": {"medida": anc-1.5, "cant": 1},
                "PIERNA": {"medida": alt-3.5, "cant": cp},
                "GANCHO": {"medida": alt-3.5, "cant": 2},
                "ZOCALO": {"medida": z, "cant": cz}
            },
            "vidrio": {"ancho": z+1.5, "alto": alt-15, "cant": hojas}
        })

    if st.session_state.pedido:
        st.subheader("Ventanas")
        for v in st.session_state.pedido:
            st.write(v["medida"])

# ================= COTIZACIÓN =================
elif modo == "Cotización":

    st.header("Cotización completa")

    color_al = st.selectbox("Color aluminio", list(PRECIOS_ALUMINIO.keys()))
    color_vid = st.selectbox("Color vidrio", list(PRECIOS_VIDRIO.keys()))
    ganancia = st.number_input("Ganancia %", 0.0, 100.0, 30.0)

    anc = st.number_input("Ancho", 0.0, key="cot_a")
    alt = st.number_input("Alto", 0.0, key="cot_h")
    hojas = st.selectbox("Hojas", [2,3,4], key="cot_hojas")

    if st.button("Cotizar"):
        if hojas == 2:
            z, cz, cp = (anc - 16)/2, 4, 2
        elif hojas == 3:
            z, cz, cp = (anc - 26.5)/3, 6, 4
        else:
            z, cz, cp = (anc - 30)/4, 8, 6

        todos = {"JAMBA":[alt]*2,"RIEL SUPERIOR":[anc-1.5],"RIEL INFERIOR":[anc-1.5],
                 "PIERNA":[alt-3.5]*cp,"GANCHO":[alt-3.5]*2,"ZOCALO":[z]*cz,
                 "VIDRIO":[{"ancho":z+1.5,"alto":alt-15,"cant":hojas}]}

        mat = calcular_materiales(todos)

        total = 0

        for p,b in mat.items():
            if p!="VIDRIO":
                total += b * PRECIOS_ALUMINIO[color_al][p]

        total += mat["VIDRIO"] * PRECIOS_VIDRIO[color_vid]
        total_final = total + (total * ganancia/100)

        st.success(f"Total: {r(total_final)} Bs")

# ================= COTIZACIÓN m² =================
elif modo == "Cotización m²":

    st.header("Cotización m²")

    precio = st.number_input("Precio m²", 100.0, 1000.0, 300.0, key="m2_precio")

    anc = st.number_input("Ancho", 0.0, key="m2_a")
    alt = st.number_input("Alto", 0.0, key="m2_h")

    if st.button("Agregar m2"):
        if anc > 0 and alt > 0:
            area = (anc * alt) / 10000
            total = area * precio
            st.session_state.cot_m2.append((anc, alt, total))

    total_general = 0

    for a,h,t in st.session_state.cot_m2:
        st.write(f"{r(a)} x {r(h)} = {r(t)} Bs")
        total_general += t

    if total_general > 0:
        st.success(f"TOTAL: {r(total_general)} Bs")
