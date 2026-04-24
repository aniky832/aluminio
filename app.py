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
    "Estipoly": 320
}

# --- FUNCIONES BASE ---
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

    area_total = 0
    for v in todos["VIDRIO"]:
        area_total += v["ancho"] * v["alto"] * v["cant"]

    planchas = area_total / (330 * 214)
    resumen["VIDRIO"] = math.ceil(planchas)

    return resumen

# --- FUNCION COTIZAR REAL ---
def cotizar(pedido, color_al, color_vid):
    todos = {
        "JAMBA": [], "RIEL SUPERIOR": [], "RIEL INFERIOR": [],
        "PIERNA": [], "GANCHO": [], "ZOCALO": [], "VIDRIO": []
    }

    for v in pedido:
        for n, info in v["detalles"].items():
            todos[n] += [info["medida"]] * info["cant"]
        todos["VIDRIO"].append(v["vidrio"])

    materiales = calcular_materiales(todos)

    total_aluminio = 0
    desglose = []

    for perfil, barras in materiales.items():
        if perfil != "VIDRIO":
            precio = PRECIOS_ALUMINIO[color_al][perfil]
            subtotal = barras * precio
            total_aluminio += subtotal
            desglose.append(f"{perfil}: {barras} x {precio} = {subtotal} Bs")

    planchas = materiales["VIDRIO"]
    precio_vidrio = PRECIOS_VIDRIO[color_vid]
    total_vidrio = planchas * precio_vidrio

    total = total_aluminio + total_vidrio

    return desglose, planchas, total_vidrio, total_aluminio, total


# --- UI ---
st.set_page_config(layout="wide")
st.title("🛠️ Sistema Linea 25 PRO")

tab1, tab2 = st.tabs(["Producción", "💰 Cotizar"])

# ================= PRODUCCIÓN =================
with tab1:

    if "pedido" not in st.session_state:
        st.session_state.pedido = []

    with st.form("form"):
        c1, c2, c3 = st.columns(3)
        anc = c1.number_input("Ancho", 0.0)
        alt = c2.number_input("Alto", 0.0)
        hojas = c3.selectbox("Hojas", [2,3,4])

        if st.form_submit_button("Agregar"):
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
                    "div": hojas,
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
        st.subheader("Resumen")
        for i,v in enumerate(st.session_state.pedido):
            st.write(v["medida"])

# ================= COTIZAR =================
with tab2:

    st.subheader("💰 Cotización Real")

    color_al = st.selectbox("Color Aluminio", list(PRECIOS_ALUMINIO.keys()))
    color_vid = st.selectbox("Color Vidrio", list(PRECIOS_VIDRIO.keys()))

    if st.button("Calcular Cotización"):
        if st.session_state.pedido:
            desglose, planchas, total_vidrio, total_al, total = cotizar(
                st.session_state.pedido, color_al, color_vid
            )

            st.subheader("Detalle Aluminio")
            for d in desglose:
                st.write(d)

            st.subheader("Vidrio")
            st.write(f"{planchas} planchas x {PRECIOS_VIDRIO[color_vid]} = {total_vidrio} Bs")

            st.divider()
            st.subheader("TOTAL")
            st.write(f"Aluminio: {total_al} Bs")
            st.write(f"Vidrio: {total_vidrio} Bs")
            st.success(f"TOTAL FINAL: {total} Bs")

        else:
            st.warning("Agrega ventanas en Producción primero")
