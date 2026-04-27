import streamlit as st
import json
from fpdf import FPDF
import math
from datetime import datetime

# ================= UTIL =================
def r(x):
    return round(x, 1)

# ================= OPTIMIZACIÓN =================
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

# ================= PDF =================
def generar_pdf_ventanas(pedido):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(190, 10, "PRODUCCION LINEA 25", ln=True, align="C")

    for v in pedido:
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(190, 8, f"{v['medida']} ({v['div']} hojas)", ln=True)

        pdf.set_font("Helvetica", "", 10)
        for n, info in v["detalles"].items():
            pdf.cell(190, 6, f"{info['cant']} {n}: {r(info['medida'])}", ln=True)

        vid = v["vidrio"]
        pdf.cell(190, 6, f"{vid['cant']} vidrio: {r(vid['alto'])} x {r(vid['ancho'])}", ln=True)
        pdf.ln(4)

    return pdf.output(dest="S").encode("latin1")

def generar_pdf_optimizacion(todos):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(190, 10, "OPTIMIZACION", ln=True, align="C")

    for p, piezas in todos.items():
        if p != "VIDRIO" and piezas:
            pdf.cell(190, 8, p, ln=True)
            barras = optimizar_barras(piezas)
            for i, b in enumerate(barras, 1):
                pdf.cell(190, 6, f"Tira {i}: {[r(x) for x in b]} | sobra {r(600-sum(b))}", ln=True)
            pdf.ln(3)

    return pdf.output(dest="S").encode("latin1")

def generar_pdf_cotizacion(cliente, detalle, total):
    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Helvetica","B",16)
    pdf.cell(190,10,"COTIZACION",ln=True,align="C")

    pdf.set_font("Helvetica","",11)
    pdf.cell(190,8,f"Cliente: {cliente}",ln=True)
    pdf.cell(190,8,f"Fecha: {datetime.now().strftime('%d/%m/%Y')}",ln=True)

    for d in detalle:
        pdf.cell(190,7,d,ln=True)

    pdf.set_font("Helvetica","B",12)
    pdf.cell(190,10,f"TOTAL: {r(total)} Bs",ln=True)

    return pdf.output(dest="S").encode("latin1")

# ================= MATERIALES =================
def calcular_materiales(todos):
    resumen = {}

    for p, piezas in todos.items():
        if p != "VIDRIO" and piezas:
            resumen[p] = len(optimizar_barras(piezas))

    total_area = sum(v["ancho"]*v["alto"]*v["cant"] for v in todos["VIDRIO"])
    resumen["VIDRIO"] = math.ceil(total_area / (330*214))

    return resumen

# ================= PRECIOS =================
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

# ================= APP =================
st.set_page_config(layout="wide")
st.title("🛠️ Sistema Linea 25 PRO")

if "pedido" not in st.session_state:
    st.session_state.pedido = []

if "cot_m2" not in st.session_state:
    st.session_state.cot_m2 = []

# ================= SIDEBAR =================
with st.sidebar:
    st.header("Proyecto")

    if st.session_state.pedido:
        st.download_button("Guardar Proyecto", json.dumps(st.session_state.pedido), "proyecto.json")

    file = st.file_uploader("Abrir Proyecto", type="json")
    if file:
        st.session_state.pedido = json.load(file)

    if st.button("Nuevo Proyecto"):
        st.session_state.pedido = []
        st.rerun()

    modo = st.radio("Modo", ["Producción", "Cotización", "Cotización m²"])

# ================= COTIZACIÓN m² =================
if modo == "Cotización m²":

    st.header("Cotización m²")

    cliente = st.text_input("Cliente")
    precio = st.number_input("Precio m²", 100.0, 1000.0, 300.0)

    anc = st.number_input("Ancho", 0.0)
    alt = st.number_input("Alto", 0.0)
    hojas = st.selectbox("Hojas", [2,3,4])

    if st.button("Agregar"):
        if anc > 0 and alt > 0:
            area = (anc * alt) / 10000
            total = area * precio
            st.session_state.cot_m2.append({
                "ancho": anc,
                "alto": alt,
                "hojas": hojas,
                "total": total
            })

    total_general = 0

    for i, v in enumerate(st.session_state.cot_m2):
        st.write(f"{i+1}) {r(v['ancho'])} x {r(v['alto'])} | {v['hojas']} hojas → {r(v['total'])} Bs")
        total_general += v["total"]

    if total_general > 0:
        st.success(f"TOTAL: {r(total_general)} Bs")

    if st.button("Generar PDF"):

        pdf = FPDF()
        pdf.add_page()

        pdf.set_font("Helvetica","B",16)
        pdf.cell(190,10,"COTIZACION m2",ln=True,align="C")

        pdf.set_font("Helvetica","",11)
        pdf.cell(190,8,f"Cliente: {cliente}",ln=True)
        pdf.cell(190,8,f"Fecha: {datetime.now().strftime('%d/%m/%Y')}",ln=True)
        pdf.ln(5)

        for i, v in enumerate(st.session_state.cot_m2):

            pdf.cell(190,6,
                f"Ventana {i+1}: {r(v['ancho'])} x {r(v['alto'])} cm | {v['hojas']} hojas",
                ln=True
            )

            x = 20
            y = pdf.get_y()

            w = 60
            h = 40

            pdf.rect(x, y, w, h)

            # divisiones
            for j in range(1, v["hojas"]):
                pdf.line(x + (w/v["hojas"])*j, y, x + (w/v["hojas"])*j, y + h)

            # flecha horizontal
            pdf.line(x, y+h+2, x+w, y+h+2)
            pdf.line(x, y+h+2, x+3, y+h-1)
            pdf.line(x+w, y+h+2, x+w-3, y+h-1)

            # texto ancho
            pdf.text(x + w/2 - 10, y+h+7, f"{r(v['ancho'])} cm")

            # flecha vertical
            pdf.line(x-3, y, x-3, y+h)
            pdf.line(x-3, y, x, y+3)
            pdf.line(x-3, y+h, x, y+h-3)

            # texto alto
            pdf.text(x-15, y + h/2, f"{r(v['alto'])} cm")

            pdf.ln(45)

        pdf.cell(190,10,f"TOTAL: {r(total_general)} Bs",ln=True)

        st.download_button("Descargar PDF", pdf.output(dest="S").encode("latin1"), "cotizacion_m2.pdf")
