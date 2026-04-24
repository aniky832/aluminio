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

# --- FUNCIONES ORIGINALES ---
def optimizar_barras(piezas, largo=600):
    if not piezas: return []
    piezas.sort(reverse=True)
    barras = []
    for p in piezas:
        puesto = False
        for b in barras:
            if sum(b) + p <= largo:
                b.append(p); puesto = True; break
        if not puesto: barras.append([p])
    return barras

def generar_pdf(pedido, todos):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(190, 10, "HOJA DE TRABAJO - LINEA 25", ln=True, align="C")
    pdf.ln(10)

    for v in pedido:
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(190, 10, f"VENTANA - {v['medida']} ({v['div']} hojas)", ln=True)

        pdf.set_font("Helvetica", "", 10)
        vid = v["vidrio"]
        pdf.cell(190, 7, f"Vidrios: {vid['cant']} de {vid['alto']:.1f} x {vid['ancho']:.1f} cm", ln=True)

        for n, info in v['detalles'].items():
            pdf.cell(190, 7, f"- {info['cant']} {n}: {info['medida']:.1f} cm", ln=True)

        pdf.ln(5)

    return pdf.output(dest='S').encode('latin1')

def generar_pdf_optimizacion(todos):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(190, 10, "OPTIMIZACION DE MATERIALES", ln=True, align="C")
    pdf.ln(10)

    for p, piezas in todos.items():
        if p != "VIDRIO" and piezas:
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(190, 8, f"{p}", ln=True)

            barras = optimizar_barras(piezas)
            pdf.set_font("Helvetica", "", 10)

            for i, b in enumerate(barras, 1):
                pdf.cell(190, 6, f"Tira {i}: {b} | Sobra: {600 - sum(b):.1f} cm", ln=True)

            pdf.cell(190, 6, f"TOTAL BARRAS: {len(barras)}", ln=True)
            pdf.ln(4)

    return pdf.output(dest='S').encode('latin1')

def calcular_materiales(todos):
    resumen = {}
    for p, piezas in todos.items():
        if p != "VIDRIO" and piezas:
            resumen[p] = len(optimizar_barras(piezas))

    total_area = 0
    for v in todos["VIDRIO"]:
        total_area += v["ancho"] * v["alto"] * v["cant"]

    planchas = total_area / (330 * 214)
    resumen["VIDRIO"] = math.ceil(planchas)

    return resumen

# --- APP ---
st.set_page_config(layout="wide")
st.title("🛠️ Sistema Linea 25 PRO")

tab1, tab2 = st.tabs(["Producción", "💰 Cotizar"])

# ================= PRODUCCIÓN (TU SISTEMA ORIGINAL) =================
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
        todos = {"JAMBA":[], "RIEL SUPERIOR":[], "RIEL INFERIOR":[],
                 "PIERNA":[], "GANCHO":[], "ZOCALO":[], "VIDRIO":[]}

        st.subheader("Resumen de Cortes")

        for v in st.session_state.pedido:
            for n, info in v["detalles"].items():
                todos[n] += [info["medida"]] * info["cant"]
            todos["VIDRIO"].append(v["vidrio"])

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

# ================= COTIZAR (NUEVO) =================
with tab2:

    st.subheader("💰 Cotización Real")

    color_al = st.selectbox("Color Aluminio", list(PRECIOS_ALUMINIO.keys()))
    color_vid = st.selectbox("Color Vidrio", list(PRECIOS_VIDRIO.keys()))

    anc = st.number_input("Ancho (cm)", 0.0)
    alt = st.number_input("Alto (cm)", 0.0)
    hojas = st.selectbox("Hojas", [2,3,4])

    if st.button("Calcular Cotización"):
        if anc > 0 and alt > 0:

            r = anc - 1.5

            if hojas == 2:
                z, cz, cp = (anc - 16) / 2, 4, 2
            elif hojas == 3:
                z, cz, cp = (anc - 26.5) / 3, 6, 4
            else:
                z, cz, cp = (anc - 30) / 4, 8, 6

            detalles = {
                "JAMBA": {"medida": alt, "cant": 2},
                "RIEL SUPERIOR": {"medida": r, "cant": 1},
                "RIEL INFERIOR": {"medida": r, "cant": 1},
                "PIERNA": {"medida": alt - 3.5, "cant": cp},
                "GANCHO": {"medida": alt - 3.5, "cant": 2},
                "ZOCALO": {"medida": z, "cant": cz}
            }

            total_al = 0
            st.subheader("Aluminio")

            for p, info in detalles.items():
                piezas = [info["medida"]] * info["cant"]
                barras = optimizar_barras(piezas)
                cantidad = len(barras)

                precio = PRECIOS_ALUMINIO[color_al][p]
                subtotal = cantidad * precio
                total_al += subtotal

                st.write(f"{p}: {cantidad} barras × {precio} = {subtotal} Bs")

            st.subheader("Vidrio")

            ancho_vid = z + 1.5
            alto_vid = alt - 15

            area = ancho_vid * alto_vid * hojas
            planchas = math.ceil(area / (330 * 214))

            total_vid = planchas * PRECIOS_VIDRIO[color_vid]

            st.write(f"{planchas} planchas × {PRECIOS_VIDRIO[color_vid]} = {total_vid} Bs")

            total = total_al + total_vid

            st.subheader("TOTAL")
            st.write(f"Aluminio: {total_al} Bs")
            st.write(f"Vidrio: {total_vid} Bs")
            st.success(f"TOTAL FINAL: {total} Bs")

        else:
            st.warning("Ingresa medidas válidas")
