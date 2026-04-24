import streamlit as st
import json
from fpdf import FPDF

# --- FUNCIONES ---
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
    return pdf.output()

# --- APP ---
st.set_page_config(page_title="App Linea 25 Pro", layout="wide")
st.title("🛠️ Sistema Linea 25 Pro")

if 'pedido' not in st.session_state:
    st.session_state.pedido = []

# BARRA LATERAL
with st.sidebar:
    st.header("📂 Proyectos")
    if st.session_state.pedido:
        js = json.dumps(st.session_state.pedido)
        st.download_button("📥 Guardar Proyecto", js, "proyecto.json")
    
    subido = st.file_uploader("📂 Abrir Proyecto", type="json")
    if subido:
        st.session_state.pedido = json.load(subido)
        st.success("¡Cargado!")
    
    if st.button("🗑️ Nuevo Proyecto"):
        st.session_state.pedido = []
        st.rerun()

# FORMULARIO
with st.form("main_form"):
    st.subheader("📝 Nueva Ventana")
    col1, col2, col3 = st.columns(3)
    with col1: anc = st.number_input("Ancho (cm)", min_value=0.0)
    with col2: alt = st.number_input("Alto (cm)", min_value=0.0)
    # LÍNEA 64 CORREGIDA:
    with col3: hojas = st.selectbox("Hojas", options=)
    
    enviar = st.form_submit_button("➕ Agregar")

    if enviar and anc > 0 and alt > 0:
        r = anc - 1.5
        if hojas == 2: z, cz, cp = (anc-16)/2, 4, 2
        elif hojas == 3: z, cz, cp = (anc-26.5)/3, 6, 4
        else: z, cz, cp = (anc-30)/4, 8, 6
        
        st.session_state.pedido.append({
            "medida": f"{anc}x{alt}", "div": hojas,
            "detalles": {
                "JAMBA": {"medida": alt, "cant": 2},
                "RIEL SUPERIOR": {"medida": r, "cant": 1},
                "RIEL INFERIOR": {"medida": r, "cant": 1},
                "PIERNA": {"medida": alt-3.5, "cant": cp},
                "GANCHO": {"medida": alt-3.5, "cant": 2},
                "ZOCALO": {"medida": z, "cant": cz}
            },
            "vidrio": f"{hojas} de {alt-15:.1f} x {z+1.5:.1f}"
        })

# RESULTADOS
if st.session_state.pedido:
    st.divider()
    todos = {"JAMBA":[], "RIEL SUPERIOR":[], "RIEL INFERIOR":[], "PIERNA":[], "GANCHO":[], "ZOCALO":[]}
    
    c_l, c_o = st.columns(2)
    with c_l:
        st.subheader("📋 Lista de Corte")
        for i, v in enumerate(st.session_state.pedido):
            with st.expander(f"VENTANA #{i+1}"):
                for n, info in v['detalles'].items():
                    st.write(f"{info['cant']} {n}: {info['medida']:.1f}cm")
                    todos[n].extend([info['medida']] * info['cant'])
                if st.button(f"Eliminar", key=f"d{i}"):
                    st.session_state.pedido.pop(i); st.rerun()
        
        pdf = generar_pdf(st.session_state.pedido, todos)
        st.download_button("📄 Descargar PDF", pdf, "corte.pdf", "application/pdf")

    with c_o:
        st.subheader("🪚 Optimización")
        if st.button("Calcular Barras"):
            for p, piezas in todos.items():
                if piezas:
                    st.write(f"**{p}**")
                    for j, b in enumerate(optimizar_barras(piezas), 1):
                        st.write(f"Tira {j}: {b}")
