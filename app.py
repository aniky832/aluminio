import streamlit as st
import json
from fpdf import FPDF

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

# ---------------- PDF ----------------
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

            if st.session_state.get(f"edit_{i}"):

                na = st.number_input("Nuevo ancho", value=float(v["medida"].split("x")[0]), key=f"na{i}")
                nh = st.number_input("Nuevo alto", value=float(v["medida"].split("x")[1]), key=f"nh{i}")
                hj = st.selectbox("Hojas", [2,3,4], index=[2,3,4].index(v["div"]), key=f"hj{i}")

                if st.button("Guardar cambios", key=f"save{i}"):

                    if hj == 2:
                        z, cz, cp = (na-16)/2, 4, 2
                    elif hj == 3:
                        z, cz, cp = (na-26.5)/3, 6, 4
                    else:
                        z, cz, cp = (na-30)/4, 8, 6

                    st.session_state.pedido[i] = {
                        "medida": f"{na}x{nh}",
                        "div": hj,
                        "detalles": {
                            "JAMBA": {"medida": nh, "cant": 2},
                            "RIEL SUPERIOR": {"medida": na-1.5, "cant": 1},
                            "RIEL INFERIOR": {"medida": na-1.5, "cant": 1},
                            "PIERNA": {"medida": nh-3.5, "cant": cp},
                            "GANCHO": {"medida": nh-3.5, "cant": 2},
                            "ZOCALO": {"medida": z, "cant": cz}
                        },
                        "vidrio": {
                            "ancho": z+1.5,
                            "alto": nh-15,
                            "cant": hj
                        }
                    }

                    st.session_state[f"edit_{i}"] = False
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

    # ---------------- PDF ----------------
    st.divider()

    pdf1 = pdf_descuentos(st.session_state.pedido)
    st.download_button("📄 PDF Descuentos", pdf1, "descuentos.pdf")

    pdf2 = pdf_optimizacion(todos)
    st.download_button("📄 PDF Optimización", pdf2, "optimizacion.pdf")
