import streamlit as st
import json
from fpdf import FPDF
import math

# --- FUNCIONES ---
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

def generar_pdf(pedido):
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

    # BARRAS
    for p, piezas in todos.items():
        if p != "VIDRIO" and piezas:
            barras = optimizar_barras(piezas)
            resumen[p] = len(barras)

    # VIDRIO
    total_area = 0
    for v in todos["VIDRIO"]:
        total_area += v["ancho"] * v["alto"] * v["cant"]

    area_plancha = 330 * 214
    planchas = total_area / area_plancha

    resumen["VIDRIO"] = math.ceil(planchas)

    return resumen


# --- APP ---
st.set_page_config(layout="wide")
st.title("🛠️ Sistema Linea 25 PRO")

if "pedido" not in st.session_state:
    st.session_state.pedido = []

# SIDEBAR
with st.sidebar:
    if st.session_state.pedido:
        st.download_button("Guardar Proyecto", json.dumps(st.session_state.pedido), "proyecto.json")

    file = st.file_uploader("Abrir Proyecto", type="json")
    if file:
        st.session_state.pedido = json.load(file)

    if st.button("Nuevo Proyecto"):
        st.session_state.pedido = []
        st.rerun()

# FORM
with st.form("form"):
    c1, c2, c3 = st.columns(3)

    with c1:
        anc = st.number_input("Ancho", 0.0)

    with c2:
        alt = st.number_input("Alto", 0.0)

    with c3:
        hojas = st.selectbox("Hojas", [2, 3, 4])

    ok = st.form_submit_button("Agregar")

    if ok and anc > 0 and alt > 0:
        r = anc - 1.5

        if hojas == 2:
            z, cz, cp = (anc - 16) / 2, 4, 2
        elif hojas == 3:
            z, cz, cp = (anc - 26.5) / 3, 6, 4
        else:
            z, cz, cp = (anc - 30) / 4, 8, 6

        st.session_state.pedido.append({
            "medida": f"{anc}x{alt}",
            "div": hojas,
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

# RESULTADOS
if st.session_state.pedido:
    todos = {
        "JAMBA": [], "RIEL SUPERIOR": [], "RIEL INFERIOR": [],
        "PIERNA": [], "GANCHO": [], "ZOCALO": [], "VIDRIO": []
    }

    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Resumen")

        for i, v in enumerate(st.session_state.pedido):
            with st.expander(f"Ventana {i+1}"):

                for n, info in v["detalles"].items():
                    st.write(f"{info['cant']} {n}: {info['medida']:.1f}")
                    todos[n] += [info["medida"]] * info["cant"]

                vid = v["vidrio"]
                st.write(f"{vid['cant']} VIDRIO: {vid['alto']:.1f} x {vid['ancho']:.1f}")
                todos["VIDRIO"].append(vid)

                if st.button("Eliminar", key=i):
                    st.session_state.pedido.pop(i)
                    st.rerun()

        pdf = generar_pdf(st.session_state.pedido)
        st.download_button("PDF Ventanas", pdf, "ventanas.pdf")

    with c2:
        st.subheader("Optimización")

        if st.button("Calcular"):
            for p, piezas in todos.items():
                if p != "VIDRIO" and piezas:
                    st.write(f"--- {p} ---")
                    barras = optimizar_barras(piezas)
                    for i, b in enumerate(barras, 1):
                        st.write(f"Tira {i}: {b} | sobra {600 - sum(b):.1f}")

            pdf2 = generar_pdf_optimizacion(todos)
            st.download_button("PDF Optimización", pdf2, "optimizacion.pdf")

        st.divider()
        st.subheader("Material a Comprar")

        resumen = calcular_materiales(todos)

        for k, v in resumen.items():
            if k != "VIDRIO":
                st.write(f"{k}: {v} barras")

        st.write(f"VIDRIO: {resumen['VIDRIO']} planchas (330x214)")
