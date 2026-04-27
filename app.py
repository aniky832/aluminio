import streamlit as st
import json
from fpdf import FPDF
import math

# ---------------- UTIL ----------------
def r(x): return round(x,1)

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

# ---------------- MATERIAL ----------------
def calcular_materiales(todos, pedido):
    resumen = {}

    for p, piezas in todos.items():
        if piezas:
            barras = optimizar_barras(piezas)
            resumen[p] = len(barras)

    total_area = 0
    for v in pedido:
        vid = v["vidrio"]
        total_area += vid["ancho"] * vid["alto"] * vid["cant"]

    area_plancha = 330 * 214
    resumen["VIDRIO"] = math.ceil(total_area / area_plancha)

    return resumen

# ---------------- PDF DESCUENTOS ----------------
def pdf_descuentos(pedido):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(190, 10, "DESCUENTOS - LINEA 25", ln=True, align="C")
    pdf.ln(5)

    for i, v in enumerate(pedido):
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(190, 8, f"VENTANA {i+1} - {v['medida']}", ln=True)

        pdf.set_font("Helvetica", "", 10)
        for n, info in v["detalles"].items():
            pdf.cell(190, 6, f"{info['cant']} {n}: {r(info['medida'])} cm", ln=True)

        vid = v["vidrio"]
        pdf.cell(190, 6, f"{vid['cant']} VIDRIO: {r(vid['alto'])} x {r(vid['ancho'])}", ln=True)

        pdf.ln(4)

    return pdf.output(dest='S').encode('latin1')

# ---------------- PDF OPTIMIZACION ----------------
def pdf_optimizacion(todos):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(190, 10, "OPTIMIZACION DE BARRAS", ln=True, align="C")
    pdf.ln(5)

    for p, piezas in todos.items():
        if piezas:
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(190, 8, p, ln=True)

            pdf.set_font("Helvetica", "", 10)
            barras = optimizar_barras(piezas)

            for i, b in enumerate(barras, 1):
                pdf.cell(190, 6, f"Tira {i}: {[r(x) for x in b]} | Sobra: {r(600 - sum(b))} cm", ln=True)

            pdf.cell(190, 6, f"TOTAL BARRAS: {len(barras)}", ln=True)
            pdf.ln(4)

    return pdf.output(dest='S').encode('latin1')

# ---------------- PDF COTIZACION ----------------
def pdf_cotizacion_m2(pedido, cliente, precio_m2):
    from datetime import datetime
    from fpdf import FPDF

    pdf = FPDF()
    pdf.add_page()

    def r(x): return round(x,1)

    # ---- ENCABEZADO ----
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(190, 10, "COTIZACION", ln=True, align="C")

    pdf.set_font("Helvetica", "", 10)
    pdf.cell(190, 6, f"Cliente: {cliente}", ln=True)
    pdf.cell(190, 6, f"Fecha: {datetime.now().strftime('%d/%m/%Y')}", ln=True)

    pdf.ln(5)

    def pdf_ventanas_con_cortes(pedido):
    from fpdf import FPDF

    pdf = FPDF()
    pdf.add_page()

    def r(x): return round(x,1)

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(190, 10, "PRODUCCION - VENTANAS", ln=True, align="C")
    pdf.ln(5)

    y_base = pdf.get_y()
    col = 0

    for i, v in enumerate(pedido):

        anc = float(v["medida"].split("x")[0])
        alt = float(v["medida"].split("x")[1])
        hojas = v["div"]

        x = 15 + (col * 95)
        y = y_base

        # número ventana
        pdf.set_xy(x, y)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(80, 5, f"V{i+1}", ln=False)

        y += 6
        w, h = 60, 30

        # marco
        pdf.rect(x, y, w, h)

        # divisiones
        for j in range(1, hojas):
            pdf.line(x + (w/hojas)*j, y, x + (w/hojas)*j, y + h)

        # medidas
        pdf.set_font("Helvetica", "", 8)

        pdf.line(x, y+h+2, x+w, y+h+2)
        pdf.text(x + w/2 - 10, y+h+6, f"{r(anc)}")

        pdf.line(x-3, y, x-3, y+h)
        pdf.text(x-15, y + h/2, f"{r(alt)}")

        # ---- DESCUENTOS ----
        y_texto = y + h + 10

        pdf.set_xy(x, y_texto)
        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(80, 4, "CORTES:", ln=True)

        pdf.set_font("Helvetica", "", 7)

        for n, info in v["detalles"].items():
            pdf.set_x(x)
            pdf.cell(80, 4, f"{info['cant']} {n}: {r(info['medida'])}", ln=True)

        col += 1

        if col == 2:
            col = 0
            y_base = y_texto + 30

    return pdf.output(dest='S').encode('latin1')
    # ---- DIBUJOS ----
    y_base = pdf.get_y()
    col = 0
    total_general = 0

    for i, v in enumerate(pedido):

        anc = float(v["medida"].split("x")[0])
        alt = float(v["medida"].split("x")[1])
        hojas = v["div"]

        area = (anc * alt) / 10000
        total = area * precio_m2
        total_general += total

        # posición
        x = 15 + (col * 95)
        y = y_base

        # título ventana
        pdf.set_xy(x, y)
        pdf.cell(80, 5, f"V{i+1}", ln=False)

        y += 6
        w, h = 60, 35

        # marco
        pdf.rect(x, y, w, h)

        # divisiones
        for j in range(1, hojas):
            pdf.line(x + (w/hojas)*j, y, x + (w/hojas)*j, y + h)

        # ancho (abajo)
        pdf.line(x, y+h+2, x+w, y+h+2)
        pdf.text(x + w/2 - 10, y+h+6, f"{r(anc)}")

        # alto (lado)
        pdf.line(x-3, y, x-3, y+h)
        pdf.text(x-15, y + h/2, f"{r(alt)}")

        col += 1
        if col == 2:
            col = 0
            y_base += 55

    # ---- TOTAL ----
    pdf.set_y(y_base + 5)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(190, 10, f"TOTAL: {r(total_general)} Bs", ln=True)

    return pdf.output(dest='S').encode('latin1')
    from datetime import datetime

    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(190, 10, "COTIZACION", ln=True, align="C")

    pdf.set_font("Helvetica", "", 10)
    pdf.cell(190, 6, f"Cliente: {cliente}", ln=True)
    pdf.cell(190, 6, f"Fecha: {datetime.now().strftime('%d/%m/%Y')}", ln=True)

    pdf.ln(5)

    total_general = 0

    for i, v in enumerate(pedido):
        anc = float(v["medida"].split("x")[0])
        alt = float(v["medida"].split("x")[1])

        area = (anc * alt) / 10000
        total = area * precio_m2
        total_general += total

        pdf.cell(190, 6, f"Ventana {i+1}: {r(anc)} x {r(alt)} → {r(total)} Bs", ln=True)

    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(190, 10, f"TOTAL: {r(total_general)} Bs", ln=True)

    return pdf.output(dest='S').encode('latin1')

# ---------------- APP ----------------
st.set_page_config(layout="wide")
st.title("🛠️ Producción Línea 25")

if "pedido" not in st.session_state:
    st.session_state.pedido = []

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.header("Proyecto")

    if st.session_state.pedido:
        st.download_button("💾 Guardar Proyecto", json.dumps(st.session_state.pedido), "proyecto.json")

    archivo = st.file_uploader("📂 Cargar Proyecto", type="json")
    if archivo:
        st.session_state.pedido = json.load(archivo)
        st.success("Proyecto cargado")

    if st.button("🗑 Nuevo Proyecto"):
        st.session_state.pedido = []
        st.rerun()

# ---------------- FORM ----------------
st.subheader("Agregar ventana")

c1, c2, c3 = st.columns(3)

with c1:
    anc = st.number_input("Ancho (cm)", 0.0)
with c2:
    alt = st.number_input("Alto (cm)", 0.0)
with c3:
    hojas = st.selectbox("Hojas", [2,3,4])

if st.button("➕ Agregar"):
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
            "JAMBA": {"medida": alt, "cant": 2},
            "RIEL SUPERIOR": {"medida": anc-1.5, "cant": 1},
            "RIEL INFERIOR": {"medida": anc-1.5, "cant": 1},
            "PIERNA": {"medida": alt-3.5, "cant": cp},
            "GANCHO": {"medida": alt-3.5, "cant": 2},
            "ZOCALO": {"medida": z, "cant": cz}
        },
        "vidrio": {
            "ancho": z+1.5,
            "alto": alt-15,
            "cant": hojas
        }
    })

# ---------------- LISTA ----------------
if st.session_state.pedido:

    st.divider()
    st.subheader("📋 Ventanas")

    todos = {"JAMBA":[],"RIEL SUPERIOR":[],"RIEL INFERIOR":[],"PIERNA":[],"GANCHO":[],"ZOCALO":[]}

    for i, v in enumerate(st.session_state.pedido):

        with st.expander(f"Ventana {i+1} - {v['medida']}"):

            for n, info in v["detalles"].items():
                st.write(f"{info['cant']} {n}: {r(info['medida'])}")
                todos[n] += [info["medida"]] * info["cant"]

            vid = v["vidrio"]
            st.write(f"{vid['cant']} VIDRIO: {r(vid['alto'])} x {r(vid['ancho'])}")

            col1, col2 = st.columns(2)

            if col1.button("✏️ Editar", key=f"edit{i}"):
                st.session_state[f"edit_{i}"] = True

            if col2.button("❌ Eliminar", key=f"del{i}"):
                st.session_state.pedido.pop(i)
                st.rerun()

    # ---------------- OPTIMIZAR ----------------
    if st.button("🪚 Optimizar"):
        st.subheader("Resultado de Optimización")

        for p, piezas in todos.items():
            if piezas:
                st.markdown(f"**{p}**")
                barras = optimizar_barras(piezas)

                for i, b in enumerate(barras, 1):
                    st.write(f"Tira {i}: {[r(x) for x in b]} → Sobra {r(600 - sum(b))} cm")

    # ---------------- MATERIAL ----------------
    st.divider()
    st.subheader("📦 Material a Comprar")

    resumen = calcular_materiales(todos, st.session_state.pedido)

    for k, v in resumen.items():
        if k == "VIDRIO":
            st.write(f"{k}: {v} planchas (330x214)")
        else:
            st.write(f"{k}: {v} barras")

    # ---------------- PDF ----------------
    st.divider()

    pdf1 = pdf_descuentos(st.session_state.pedido)
    st.download_button("📄 PDF Descuentos", pdf1, "descuentos.pdf")

    pdf2 = pdf_optimizacion(todos)
    st.download_button("📄 PDF Optimización", pdf2, "optimizacion.pdf")

    # ---------------- COTIZAR ----------------
    st.divider()
    st.subheader("💰 Cotizar (m²)")

    cliente = st.text_input("Nombre del cliente")
    precio_m2 = st.number_input("Precio por m² (Bs)", 100.0, 1000.0, 300.0)

    total_general = 0

    for v in st.session_state.pedido:
        anc = float(v["medida"].split("x")[0])
        alt = float(v["medida"].split("x")[1])

        area = (anc * alt) / 10000
        total = area * precio_m2
        total_general += total

    st.success(f"TOTAL: {r(total_general)} Bs")

    if st.button("📄 Generar PDF Cotización m²"):
        pdf = pdf_cotizacion_m2(st.session_state.pedido, cliente, precio_m2)

        st.download_button(
            "⬇ Descargar PDF",
            pdf,
            "cotizacion_m2.pdf",
            "application/pdf"
        )
pdf_detalle = pdf_ventanas_con_cortes(st.session_state.pedido)

st.download_button(
    "📄 PDF Producción (Ventanas + Cortes)",
    pdf_detalle,
    "produccion_visual.pdf",
    "application/pdf"
)
