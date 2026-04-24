import streamlit as st

# Función de optimización de barras
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

if 'pedido' not in st.session_state:
    st.session_state.pedido = []

# --- FORMULARIO DE INGRESO ---
with st.form("mi_formulario"):
    st.subheader("📝 Ingresar Nueva Ventana")
    col1, col2 = st.columns(2)
    with col1: 
        ancho = st.number_input("Ancho total (cm)", min_value=0.0, step=0.1, key="ancho")
    with col2: 
        alto = st.number_input("Alto total (cm)", min_value=0.0, step=0.1, key="alto")
    
    # LÍNEA 31 CORREGIDA: Ahora tiene la lista [2, 3, 4]
    div = st.selectbox("Número de divisiones", options=)
    
    enviar = st.form_submit_button("➕ Agregar Ventana al Pedido")

    if enviar:
        if ancho > 0 and alto > 0:
            jamba, riel = alto, ancho - 1.5
            pierna, gancho = alto - 3.5, alto - 3.5
            
            if div == 2:
                zocalo, c_z, c_p = (ancho-16)/2, 4, 2
            elif div == 3:
                zocalo, c_z, c_p = (ancho-26.5)/3, 6, 4
            else:
                zocalo, c_z, c_p = (ancho-30)/4, 8, 6
            
            st.session_state.pedido.append({
                "medida": f"{ancho}x{alto}", 
                "div": div,
                "detalles": {
                    "JAMBA": {"medida": jamba, "cant": 2},
                    "RIEL": {"medida": riel, "cant": 2},
                    "PIERNA": {"medida": pierna, "cant": c_p},
                    "GANCHO": {"medida": gancho, "cant": 2},
                    "ZOCALO": {"medida": zocalo, "cant": c_z}
                },
                "vidrio": f"{div} vidrios de {alto-15} x {zocalo+1.5:.1f}"
            })
            st.success(f"✅ Ventana {ancho}x{alto} agregada.")
        else:
            st.error("⚠️ Ingresa medidas mayores a 0.")

# --- MOSTRAR RESULTADOS ---
if st.session_state.pedido:
    if st.button("🗑️ Borrar todo el pedido"):
        st.session_state.pedido = []
        st.rerun()

    st.header("📋 1. Hoja de Corte por Ventana")
    todos_los_perfiles = {"JAMBA": [], "RIEL": [], "PIERNA": [], "GANCHO": [], "ZOCALO": []}
    
    for i, v in enumerate(st.session_state.pedido, 1):
        with st.expander(f"VENTANA #{i} - {v['medida']} ({v['div']} hojas)", expanded=True):
            st.write(f"*Vidrios:* {v['vidrio']} cm")
            for nombre, info in v['detalles'].items():
                st.write(f"- {info['cant']} {nombre}: *{info['medida']:.1f} cm*")
                todos_los_perfiles[nombre].extend([info['medida']] * info['cant'])

    st.divider()

    if st.button("🪚 2. CALCULAR PLAN DE CORTE GLOBAL"):
        st.header("📏 Plan de Corte (Barras de 600cm)")
        total_tiras = 0
        for perfil, piezas in todos_los_perfiles.items():
            if piezas:
                st.subheader(f"🔹 Perfil: {perfil}")
                barras = optimizar_barras(piezas)
                total_tiras += len(barras)
                for j, b in enumerate(barras, 1):
                    b_redondeado = [round(x,1) for x in b]
                    st.write(f"*Tira #{j}:* {b_redondeado} | Sobra: {600-sum(b):.1f}cm")
        
        st.divider()
        st.metric("TOTAL DE TIRAS A COMPRAR", f"{total_tiras} tiras")
