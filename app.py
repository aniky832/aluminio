import streamlit as st
import json
from fpdf import FPDF
import math

# --- PRECIOS ---
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

# --- FUNCIONES ---
def optimizar_barras(piezas, largo=600):
    piezas = sorted(piezas, reverse=True)
    barras = []
    for p in piezas:
        for b in barras:
            if sum(b) + p <= largo:
                b.append(p)
                break
        else:
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

# --- UI ---
st.set_page_config(layout="wide")
st.title("🛠️ Sistema Linea 25 PRO")

tab1, tab2 = st.tabs(["Producción", "💰 Cotizar"])

# ================= PRODUCCIÓN =================
with tab1:

    if "pedido" not in st.session_state:
        st.session_state.pedido = []

    col1, col2, col3 = st.columns(3)
    anc = col1.number_input("Ancho", 0.0)
    alt = col2.number_input("Alto", 0.0)
    hojas = col3.selectbox("Hojas", [2,3,4])

    if st.button("Agregar Ventana"):
        if anc > 0 and alt > 0:
            r = anc - 1.5
            if hojas == 2:
                z, cz, cp = (anc-16)/2, 4, 2
            elif hojas == 3:
                z, cz, cp = (anc-26.5)/3, 6, 4
            else:
                z, cz, cp = (anc-30)/4, 8, 6

            st.session_state.pedido.append({
                "medida": f"{anc}x{alt}",
                "detalles": {
                    "JAMBA":{"medida":alt,"cant":2},
                    "RIEL SUPERIOR":{"medida":r,"cant":1},
                    "RIEL INFERIOR":{"medida":r,"cant":1},
                    "PIERNA":{"medida":alt-3.5,"cant":cp},
                    "GANCHO":{"medida":alt-3.5,"cant":2},
                    "ZOCALO":{"medida":z,"cant":cz}
                },
                "vidrio":{
                    "ancho":z+1.5,
                    "alto":alt-15,
                    "cant":hojas
                }
            })

    if st.session_state.pedido:
        todos = {"JAMBA":[], "RIEL SUPERIOR":[], "RIEL INFERIOR":[],
                 "PIERNA":[], "GANCHO":[], "ZOCALO":[], "VIDRIO":[]}

        st.subheader("Resumen")

        for i, v in enumerate(st.session_state.pedido):
            st.write(v["medida"])

            for n, info in v["detalles"].items():
                todos[n] += [info["medida"]] * info["cant"]

            todos["VIDRIO"].append(v["vidrio"])

            if st.button(f"Eliminar {i}", key=f"del_{i}"):
                st.session_state.pedido.pop(i)
                st.rerun()

        if st.button("Calcular Optimización"):
            for p, piezas in todos.items():
                if p != "VIDRIO" and piezas:
                    st.write(f"--- {p} ---")
                    barras = optimizar_barras(piezas)
                    for i, b in enumerate(barras, 1):
                        st.write(f"Tira {i}: {b} | sobra {600 - sum(b):.1f}")

        st.subheader("Material a Comprar")
        resumen = calcular_materiales(todos)

        for k, v in resumen.items():
            if k != "VIDRIO":
                st.write(f"{k}: {v} barras")

        st.write(f"VIDRIO: {resumen['VIDRIO']} planchas")

# ================= COTIZAR =================
with tab2:

    if "cotizacion" not in st.session_state:
        st.session_state.cotizacion = []

    st.subheader("Agregar Ventana a Cotización")

    c1, c2, c3 = st.columns(3)
    anc = c1.number_input("Ancho (cm)", 0.0, key="c_anc")
    alt = c2.number_input("Alto (cm)", 0.0, key="c_alt")
    hojas = c3.selectbox("Hojas", [2,3,4], key="c_hojas")

    if st.button("➕ Agregar"):
        if anc > 0 and alt > 0:
            r = anc - 1.5

            if hojas == 2:
                z, cz, cp = (anc - 16) / 2, 4, 2
            elif hojas == 3:
                z, cz, cp = (anc - 26.5) / 3, 6, 4
            else:
                z, cz, cp = (anc - 30) / 4, 8, 6

            st.session_state.cotizacion.append({
                "detalles": {
                    "JAMBA": {"medida": alt, "cant": 2},
                    "RIEL SUPERIOR": {"medida": r, "cant": 1},
                    "RIEL INFERIOR": {"medida": r, "cant": 1},
                    "PIERNA": {"medida": alt - 3.5, "cant": cp},
                    "GANCHO": {"medida": alt - 3.5, "cant": 2},
                    "ZOCALO": {"medida": z, "cant": cz}
                },
                "vidrio": {
                    "ancho": z + 1.5,
                    "alto": alt - 15,
                    "cant": hojas
                }
            })

    color_al = st.selectbox("Color Aluminio", list(PRECIOS_ALUMINIO.keys()))
    color_vid = st.selectbox("Color Vidrio", list(PRECIOS_VIDRIO.keys()))

    if st.session_state.cotizacion:

        todos = {"JAMBA":[], "RIEL SUPERIOR":[], "RIEL INFERIOR":[],
                 "PIERNA":[], "GANCHO":[], "ZOCALO":[], "VIDRIO":[]}

        for v in st.session_state.cotizacion:
            for n, info in v["detalles"].items():
                todos[n] += [info["medida"]] * info["cant"]
            todos["VIDRIO"].append(v["vidrio"])

        if st.button("💰 Calcular Cotización"):

            materiales = calcular_materiales(todos)

            total_al = 0
            st.subheader("Aluminio")

            for p, barras in materiales.items():
                if p != "VIDRIO":
                    precio = PRECIOS_ALUMINIO[color_al][p]
                    subtotal = barras * precio
                    total_al += subtotal
                    st.write(f"{p}: {barras} x {precio} = {subtotal} Bs")

            planchas = materiales["VIDRIO"]
            total_vid = planchas * PRECIOS_VIDRIO[color_vid]

            st.subheader("Vidrio")
            st.write(f"{planchas} planchas x {PRECIOS_VIDRIO[color_vid]} = {total_vid} Bs")

            total = total_al + total_vid

            st.divider()
            st.subheader("TOTAL")
            st.write(f"Aluminio: {total_al} Bs")
            st.write(f"Vidrio: {total_vid} Bs")
            st.success(f"TOTAL FINAL: {total} Bs")
