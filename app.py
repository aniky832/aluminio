import streamlit as st

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

st.set_page_config(page_title="App Linea 25", page_icon="📐")
st.title("🛠️ Sistema Linea 25")

if 'pedido' not in st.session_state:
    st.session_state.pedido = []

with st.form("mi_formulario"):
    st.subheader("📝 Nueva Ventana")
    col1, col2 = st.columns(2)
    with col1: ancho = st.number_input("Ancho total (cm)", min_value=0.0, step=0.1)
    with col2: alto = st.number_input("Alto total (cm)", min_value=0.0, step=0.1)
    
    # OPCIONES SIN EL SIGNO IGUAL PARA EVITAR ERRORES
    opciones = [2, 3, 4]
    div = st.selectbox("Numero de divisiones", opciones)
    
    enviar = st.form_submit_button("➕ Agregar Ventana")

    if enviar:
        if ancho > 0 and alto > 0:
            jamba, riel = alto, ancho - 1.5
            pierna, gancho = alto - 3.5, alto - 3.5
            if div == 2: zocalo, c_z, c_p = (ancho-16)/2, 4, 2
            elif div == 3: zocalo, c_z, c_p = (ancho-26.5)/3, 6, 4
            else: zocalo, c_z, c_p = (ancho-30)/4, 8, 6
            
            st.session_state.pedido.append({
                "medida": f"{ancho}x{alto}", "div": div,
                "detalles": {
                    "JAMBA": {"medida": jamba, "cant": 2},
                    "RIEL": {"medida": riel, "cant": 2},
                    "PIERNA": {"medida": pierna, "cant": c_p},
                    "GANCHO": {"medida": gancho, "cant": 2},
                    "ZOCALO": {"medida": zocalo, "cant": c_z}
                },
                "vidrio": f"{div} vidrios de {alto-15} x {zocalo+1.5:.1f}"
            })
            st.success("Ventana agregada.")

if st.session_state.pedido:
    if st.button("🗑️ Borrar pedido"):
        st.session_state.pedido = []; st.rerun()

    st.header("📋 1. Hoja de Corte")
    todos = {"JAMBA":[], "RIEL":[], "PIERNA":[], "GANCHO":[], "ZOCALO":[]}
    for i, v in enumerate(st.session_state.pedido, 1):
        with st.expander(f"VENTANA #{i} - {v['medida']}"):
            st.write(f"Vidrios: {v['vidrio']}")
            for n, info in v['detalles'].items():
                st.write(f"- {info['cant']} {n}: {info['medida']:.1f} cm")
                todos[n].extend([info['medida']] * info['cant'])

    if st.button("🪚 2. OPTIMIZAR BARRAS"):
        st.header("📏 Plan de Corte (600cm)")
        total = 0
        for p, piezas in todos.items():
            if piezas:
                st.subheader(f"🔹 {p}")
                barras = optimizar_barras(piezas)
                total += len(barras)
                for j, b in enumerate(barras, 1):
                    st.write(f"Tira {j}: {[round(x,1) for x in b]}")
        st.metric("Total de tiras", total)
