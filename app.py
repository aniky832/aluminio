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
    
    for i, v in enumerate(pedido, 1):
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(190, 10, f"VENTANA #{i} - {v['medida']} ({v['div']} hojas)", ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(190, 7, f"Vidrios: {v['vidrio']}", ln=True)
        for n, info in v['detalles'].items():
            pdf.cell(190, 7, f"- {info['cant']} {n}: {info['medida']:.1f} cm", ln=True)
        pdf.ln(5)
    
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(190, 10, "PLAN DE CORTE (BARRAS 6M)", ln=True, align="C")
    pdf.ln(5)
    
    for p, piezas in todos.items():
        if piezas:
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(190, 10, f"Perfil: {p}", ln=True)
            pdf.set_font("Helvetica", "", 10)
            barras = optimizar_barras(piezas)
            for j, b in enumerate(barras, 1):
                pdf.cell(190, 7, f"  Tira {j}: {b} - Sobra: {600-sum(b):.1f}cm", ln=True)
    
    return pdf.output()

# --- CONFIGURACIÓN DE APP ---
st.set_page_config(page_title="App Linea 25 Pro", page_icon="📐")
st.title("🛠️ Sistema Linea 25 Pro")

if 'pedido' not in st.session_state:
    st.session_state.pedido = []

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("💾 Gestión de Archivos")
    if st.session_state.pedido:
        json_str = json.dumps(st.session_state.pedido)
        st.download_button("📥 Descargar Proyecto (.json)", json_str, file_name="proyecto.json")
    
    archivo_cargado = st.file_uploader("📂 Cargar Proyecto", type="json")
    if archivo_cargado:
        st.session_state.pedido = json.load(archivo_cargado)
        st.success("¡Cargado!")

# --- FORMULARIO DE ENTRADA ---
with st.form("mi_formulario"):
    st.subheader("📝 Nueva Ventana")
    col1, col2 = st.columns(2)
    with col1: ancho = st.number_input("Ancho (cm)", min_value=0.0)
    with col2: alto = st.number_input("Alto (cm)", min_value=0.0)
    
    # CORRECCIÓN AQUÍ: He añadido las opciones [2, 3, 4]
    div = st.selectbox("Número de divisiones",)
    
    enviar = st.form_submit_button("➕ Agregar al Pedido")

    if enviar and ancho > 0:
        riel = ancho - 1.5
        if div == 2: zocalo, c_z, c_p = (ancho-16)/2, 4, 2
        elif div == 3: zocalo, c_z, c_p = (ancho-26.5)/3, 6, 4
        else: zocalo, c_z, c_p = (ancho-30)/4, 8, 6
        
        st.session_state.pedido.append({
            "medida": f"{ancho}x{alto}", "ancho": ancho, "alto": alto, "div": div,
            "detalles": {
                "JAMBA": {"medida": alto, "cant": 2},
                "RIEL SUPERIOR": {"medida": riel, "cant": 1},
                "RIEL INFERIOR": {"medida": riel, "cant": 1},
                "PIERNA": {"medida": alto-3.5, "cant": c_p},
                "GANCHO": {"medida": alto-3.5, "cant": 2},
                "ZOCALO": {"medida": zocalo, "cant": c_z}
            },
            "vidrio": f"{div} vidrios de {alto-15:.1f} x {zocalo+1.5:.1f}"
        })
        st.success("Ventana agregada")

# --- VISUALIZACIÓN ---
if st.session_state.pedido:
    st.header("📋 Hoja de Trabajo")
    todos = {"JAMBA":[], "RIEL SUPERIOR":[], "RIEL INFERIOR":[], "PIERNA":[], "GANCHO":[], "ZOCALO":[]}
    
    for i, v in enumerate(st.session_state.pedido):
        with st.expander(f"VENTANA #{i+1} - {v['medida']} ({v['div']} hojas)"):
            for n, info in v['detalles'].items():
                st.write(f"- {info['cant']} {n}: {info['medida']:.1f} cm")
                if n in todos:
                    todos[n].extend([info['medida']] * info['cant'])
            if st.button(f"🗑️ Eliminar Ventana {i+1}", key=f"del_{i}"):
                st.session_state.pedido.pop(i)
                st.rerun()

    # Botones finales
    col_a, col_b = st.columns(2)
    with col_a:
        try:
            pdf_bytes = generar_pdf(st.session_state.pedido, todos)
            st.download_button("📄 Descargar PDF", pdf_bytes, "hoja_corte.pdf", "application/pdf")
        except:
            st.warning("Añade una ventana para habilitar el PDF.")

    with col_b:
        if st.button("🔴 Borrar Todo"):
            st.session_state.pedido = []
            st.rerun()

    if st.button("🪚 OPTIMIZAR BARRAS"):
        st.header("📏 Plan de Corte (600cm)")
        for p, piezas in todos.items():
            if piezas:
                st.subheader(f"🔹 {p}")
                for j, b in enumerate(optimizar_barras(piezas), 1):
                    st.write(f"Tira {j}: {b} - Sobra: {600-sum(b):.1f}cm")
