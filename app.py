import streamlit as st

# Función para acomodar piezas en barras de 600cm
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

st.set_page_config(page_title="App Línea 25", page_icon="📐")
st.title("🛠️ Sistema de Ventanas - Línea 25")

# Guardar los datos mientras la app esté abierta
if 'pedido' not in st.session_state:
    st.session_state.pedido = []

# --- FORMULARIO DE INGRESO ---
with st.form("nueva_ventana"):
    st.subheader("Ingresar nueva ventana")
    col1, col2 = st.columns(2)
    with col1: ancho = st.number_input("Ancho total (cm)", min_value=0.0)
    with col2: alto = st.number_input("Alto total (cm)", min_value=0.0)
    div = st.selectbox("Número de divisiones",)
    
    submit = st.form_submit_button("➕ Agregar Ventana")

    if submit:
        if ancho > 0 and alto > 0:
            # Lógica de la Línea 25
            jamba, riel = alto, ancho - 1.5
            pierna, gancho = alto - 3.5, alto - 3.5
            if div == 2: zocalo, c_z, c_p = (ancho-16)/2, 4, 2
            elif div == 3: zocalo, c_z, c_p = (ancho-26.5)/3, 6, 4
            else: zocalo, c_z, c_p = (ancho-30)/4, 8, 6
            
            st.session_state.pedido.append({
                "medida": f"{ancho}x{alto}", "div": div,
                "piezas": {"JAMBA": [jamba]*2, "RIEL": [riel]*2, "PIERNA": [pierna]*c_p, "GANCHO": [gancho]*2, "ZOCALO": [zocalo]*c_z},
                "vidrio": f"{div} de {alto-15}x{zocalo+1.5:.1f}"
            })
            st.success(f"Ventana de {ancho}x{alto} agregada correctamente.")
        else:
            st.error("Por favor, ingresa medidas válidas.")

# --- RESULTADOS Y OPTIMIZACIÓN ---
if st.session_state.pedido:
    if st.button("🗑️ Borrar todo el pedido"):
        st.session_state.pedido = []
        st.rerun()

    st.divider()
    st.header("📋 Resumen del Pedido")
    todos_los_perfiles = {"JAMBA": [], "RIEL": [], "PIERNA": [], "GANCHO": [], "ZOCALO": []}
    
    for i, v in enumerate(st.session_state.pedido, 1):
        with st.expander(f"Ventana #{i} - {v['medida']} ({v['div']} hojas)"):
            st.write(f"*Vidrios:* {v['vidrio']} cm")
            for p, lista in v['piezas'].items():
                todos_los_perfiles[p].extend(lista)

    if st.button("🪚 CALCULAR PLAN DE CORTE"):
        st.header("📏 Optimización de Barras (600cm)")
        total_tiras = 0
        for perfil, piezas in todos_los_perfiles.items():
            if piezas:
                st.subheader(f"🔹 Perfil: {perfil}")
                barras = optimizar_barras(piezas)
                total_tiras += len(barras)
                for j, b in enumerate(barras, 1):
                    # Redondeamos a 1 decimal para que sea legible
                    b_redondeado = [round(x, 1) for x in b]
                    st.write(f"*Tira {j}:* {b_redondeado} | Sobra: {600-sum(b):.1f}cm")
        st.metric("TOTAL DE TIRAS A COMPRAR", f"{total_tiras} de 6 metros")
