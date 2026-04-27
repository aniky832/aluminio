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

def generar_pdf(pedido):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(190, 10, "PRODUCCION", ln=True, align="C")
    pdf.ln(10)

    for v in pedido:
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(190, 10, f"VENTANA - {v['medida']} ({v['div']} hojas)", ln=True)

        pdf.set_font("Helvetica", "", 10)
        vid = v["vidrio"]
        pdf.cell(190, 7, f"Vidrios: {vid['cant']} de {r(vid['alto'])} x {r(vid['ancho'])}", ln=True)

        for n, info in v['detalles'].items():
            pdf.cell(190, 7, f"- {info['cant']} {n}: {r(info['medida'])}", ln=True)

        pdf.ln(5)

    return pdf.output(dest='S').encode('latin1')

def generar_pdf_optimizacion(todos):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(190, 10, "OPTIMIZACION LINEA 25", ln=True, align="C")
    pdf.ln(10)

    for p, piezas in todos.items():
        if p != "VIDRIO" and piezas:
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(190, 8, p, ln=True)

            barras = optimizar_barras(piezas)
            pdf.set_font("Helvetica", "", 10)

            for i, b in enumerate(barras, 1):
                pdf.cell(
                    190, 6,
                    f"Tira {i}: {[r(x) for x in b]} | sobra {r(600 - sum(b))} cm",
                    ln=True
                )

            pdf.ln(4)

    return pdf.output(dest='S').encode('latin1')

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
st.title("Sistema Linea 25")

if "pedido" not in st.session_state:
    st.session_state.pedido = []

if "cotizacion" not in st.session_state:
    st.session_state.cotizacion = []

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

    st.divider()
    modo = st.radio("Modo", ["Producción línea 25", "Cotización"])

# ---------- PRODUCCIÓN ----------
if modo == "Producción línea 25":

    st.header("Producción línea 25")

    with st.form("form"):
        c1, c2, c3 = st.columns(3)
        anc = c1.number_input("Ancho", 0.0)
        alt = c2.number_input("Alto", 0.0)
        hojas = c3.selectbox("Hojas", [2,3,4])

        ok = st.form_submit_button("Agregar")

        if ok and anc > 0 and alt > 0:
            riel = anc - 1.5

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
                    "RIEL SUPERIOR": {"medida": riel, "cant": 1},
                    "RIEL INFERIOR": {"medida": riel, "cant": 1},
                    "PIERNA": {"medida": alt-3.5, "cant": cp},
                    "GANCHO": {"medida": alt-3.5, "cant": 2},
                    "ZOCALO": {"medida": z, "cant": cz}
                },
                "vidrio": {"ancho": z+1.5, "alto": alt-15, "cant": hojas}
            })

    if st.session_state.pedido:

        todos = {"JAMBA":[],"RIEL SUPERIOR":[],"RIEL INFERIOR":[],"PIERNA":[],"GANCHO":[],"ZOCALO":[],"VIDRIO":[]}

        for v in st.session_state.pedido:
            for n, info in v["detalles"].items():
                todos[n] += [info["medida"]] * info["cant"]
            todos["VIDRIO"].append(v["vidrio"])

        if st.button("Calcular Optimización"):
            for p, piezas in todos.items():
                if p != "VIDRIO" and piezas:
                    st.write(f"--- {p} ---")
                    for i, b in enumerate(optimizar_barras(piezas),1):
                        st.write(f"Tira {i}: {[r(x) for x in b]} | sobra {r(600 - sum(b))} cm")

        st.download_button("PDF Ventanas", generar_pdf(st.session_state.pedido), "ventanas.pdf")
        st.download_button("PDF Optimización", generar_pdf_optimizacion(todos), "optimizacion.pdf")

        resumen = calcular_materiales(todos)

        st.subheader("Material a Comprar")
        for k,v in resumen.items():
            if k != "VIDRIO":
                st.write(f"{k}: {v} barras")
        st.write(f"VIDRIO: {resumen['VIDRIO']} planchas")

# ---------- COTIZACIÓN ----------
elif modo == "Cotización":

    st.header("Cotización")

    cliente = st.text_input("Cliente")
    fecha = datetime.now().strftime("%d/%m/%Y")

    c1,c2,c3 = st.columns(3)
    anc = c1.number_input("Ancho",0.0,key="c1")
    alt = c2.number_input("Alto",0.0,key="c2")
    hojas = c3.selectbox("Hojas",[2,3,4],key="c3")

    if st.button("Agregar Ventana"):
        if anc>0 and alt>0:
            riel = anc-1.5

            if hojas==2:
                z,cz,cp=(anc-16)/2,4,2
            elif hojas==3:
                z,cz,cp=(anc-26.5)/3,6,4
            else:
                z,cz,cp=(anc-30)/4,8,6

            st.session_state.cotizacion.append({
                "detalles":{
                    "JAMBA":{"medida":alt,"cant":2},
                    "RIEL SUPERIOR":{"medida":riel,"cant":1},
                    "RIEL INFERIOR":{"medida":riel,"cant":1},
                    "PIERNA":{"medida":alt-3.5,"cant":cp},
                    "GANCHO":{"medida":alt-3.5,"cant":2},
                    "ZOCALO":{"medida":z,"cant":cz}
                },
                "vidrio":{"ancho":z+1.5,"alto":alt-15,"cant":hojas}
            })

    color_al = st.selectbox("Color aluminio", list(PRECIOS_ALUMINIO.keys()))
    color_vid = st.selectbox("Color vidrio", list(PRECIOS_VIDRIO.keys()))
    porcentaje = st.number_input("Ganancia %",0.0,100.0,30.0)

    if st.session_state.cotizacion and st.button("Calcular"):

        todos = {"JAMBA":[],"RIEL SUPERIOR":[],"RIEL INFERIOR":[],"PIERNA":[],"GANCHO":[],"ZOCALO":[],"VIDRIO":[]}

        for v in st.session_state.cotizacion:
            for n,info in v["detalles"].items():
                todos[n]+= [info["medida"]]*info["cant"]
            todos["VIDRIO"].append(v["vidrio"])

        mat = calcular_materiales(todos)

        total_al=0
        detalle=[]

        for p,barras in mat.items():
            if p!="VIDRIO":
                precio=PRECIOS_ALUMINIO[color_al][p]
                sub=barras*precio
                total_al+=sub
                detalle.append(f"{p}: {barras} x {precio} = {sub}")

        planchas=mat["VIDRIO"]
        total_vid=planchas*PRECIOS_VIDRIO[color_vid]

        subtotal=total_al+total_vid
        ganancia=subtotal*(porcentaje/100)
        total=subtotal+ganancia

        st.success(f"TOTAL: {total:.2f} Bs")

        if st.button("Generar PDF"):
            pdf=FPDF()
            pdf.add_page()

            pdf.set_font("Helvetica","B",16)
            pdf.cell(190,10,"COTIZACION",ln=True,align="C")

            pdf.set_font("Helvetica","",11)
            pdf.cell(190,8,f"Cliente: {cliente}",ln=True)
            pdf.cell(190,8,f"Fecha: {fecha}",ln=True)

            for d in detalle:
                pdf.cell(190,7,d,ln=True)

            pdf.cell(190,8,f"Vidrio: {planchas} x {total_vid}",ln=True)
            pdf.cell(190,8,f"Ganancia: {ganancia:.2f}",ln=True)

            pdf.set_font("Helvetica","B",12)
            pdf.cell(190,10,f"TOTAL: {total:.2f} Bs",ln=True)

            pdf_bytes = pdf.output(dest='S').encode('latin1')

            st.download_button(
                "⬇ Descargar PDF",
                data=pdf_bytes,
                file_name="cotizacion.pdf",
                mime="application/pdf"
            )
