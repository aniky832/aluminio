import streamlit as st
import json
from fpdf import FPDF

# --- FUNCIONES DE APOYO ---
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
        pdf.cell(190, 7, f"Vidrios: {v['vidrio']}", ln=True)
        for n, info in v['detalles'].items():
            pdf.cell(190, 7, f"- {info['cant']} {n}: {info['medida']:.1f} cm", ln=True)
        pdf.ln(5)
    return pdf.output(dest='S').encode('latin-1')

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="App Linea 25", page_icon="📐")
st.title("🛠️ Sistema Linea 25 Pro")

if 'pedido' not in st.session_state:
    st.session_state.pedido = []

# --- FORMULARIO ---
with st.form("nuevo_registro"):
    st.subheader("📝 Nueva Ventana")
    c1, c2 = st.columns(2)
    with c1: ancho = st.number_input("Ancho (cm)", min_value=0.0)
    with c2: alto = st.number_input("Alto (cm)", min_value=0.0)
    
    # OPCIONES FIJAS PARA EVITAR EL ERROR
    opciones_div = [2, 3, 4]
    div = st.selectbox("Número de divisiones", options=opciones_div)
    
    enviar = st.form_submit_button("➕ Agregar al Pedido")

    if enviar and ancho > 0 and alto > 0:
        riel = ancho - 1.5
        if div == 2: z, cz, cp = (ancho-16)/2, 4, 2
        elif div == 3: z, cz, cp = (ancho-26.5)/3, 6, 4
        else: z, cz, cp = (ancho-30)/4, 8, 6
        
        st.session_state.pedido.append({
            "medida": f"{ancho}x{alto}", "div": div,
            "detalles": {
                "JAMBA": {"medida": alto, "cant": 2},
                "RIEL SUP.": {"medida": riel, "cant": 1},
                "RIEL INF.": {"medida": riel, "cant": 1},
                "PIERNA": {"medida": alto-3.5, "cant": cp},
                "GANCHO": {"medida": alto-3.5, "cant": 2},
                "ZOCALO": {"medida": z, "cant": cz}
            },
            "vidrio": f"{div} de {alto-15:.1f}x{z+1.5:.1f}"
        })
        st.success("¡Agregada!")

# --- RESULTADOS ---
if st.session_state.pedido:
    todos = {"JAMBA":[], "RIEL SUP.":[], "RIEL INF.":[], "PIERNA":[], "GANCHO":[], "ZOCALO":[]}
    for i, v in enumerate(st.session_state.pedido):
        with st.expander(f"VENTANA #{i+1}"):
            for n, info in v['detalles'].items():
                st.write(f"{info['cant']} {n}: {info['medida']:.1f}cm")
                todos[n].extend([info['medida']] * info['cant'])
    
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("🪚 Optimizar"):
            for p, piezas in todos.items():
                if piezas:
                    st.write(f"*{p}*")
                    for j, b in enumerate(optimizar_barras(piezas), 1):
                        st.write(f"Tira {j}: {b}")
    with col_b:
        pdf_bytes = generar_pdf(st.session_state.pedido, todos)
        st.download_button("📄 PDF", pdf_bytes, "corte.pdf", "application/pdf")
