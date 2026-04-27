import streamlit as st
import json
from fpdf import FPDF
import math
import sqlite3
from datetime import datetime

# ---------------- DB ----------------
conn = sqlite3.connect("datos.db", check_same_thread=False)
c = conn.cursor()

c.execute("""CREATE TABLE IF NOT EXISTS proyectos(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT,
    data TEXT
)""")

c.execute("""CREATE TABLE IF NOT EXISTS cot_m2(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente TEXT,
    total REAL,
    fecha TEXT
)""")
conn.commit()

# ---------------- UTIL ----------------
def r(x): return round(x,1)

# ---------------- OPTIMIZAR ----------------
def optimizar_barras(piezas, largo=600):
    piezas = sorted(piezas, reverse=True)
    barras=[]
    for p in piezas:
        colocado=False
        for b in barras:
            if sum(b)+p<=largo:
                b.append(p)
                colocado=True
                break
        if not colocado:
            barras.append([p])
    return barras

# ---------------- PRECIOS ----------------
PRECIOS_AL = {
"MT":{"RIEL SUPERIOR":187,"RIEL INFERIOR":187,"ZOCALO":177,"GANCHO":171,"JAMBA":159,"PIERNA":171},
"CH":{"RIEL SUPERIOR":191,"RIEL INFERIOR":191,"ZOCALO":180,"GANCHO":171,"JAMBA":160,"PIERNA":171},
"BR":{"RIEL SUPERIOR":192,"RIEL INFERIOR":192,"ZOCALO":183,"GANCHO":171,"JAMBA":167,"PIERNA":171},
"CH.O":{"RIEL SUPERIOR":191,"RIEL INFERIOR":191,"ZOCALO":172,"GANCHO":169,"JAMBA":166,"PIERNA":169},
"MD":{"RIEL SUPERIOR":215,"RIEL INFERIOR":215,"ZOCALO":192,"GANCHO":173,"JAMBA":177,"PIERNA":173}
}

PRECIOS_VID={"Bronce":500,"Incoloro":490,"Gris":780,"Estipoly Incoloro":320}

# ---------------- ESTADO ----------------
if "pedido" not in st.session_state:
    st.session_state.pedido=[]
if "cot_lista" not in st.session_state:
    st.session_state.cot_lista=[]
if "cot_m2" not in st.session_state:
    st.session_state.cot_m2=[]

st.set_page_config(layout="wide")
st.title("🛠️ Sistema Línea 25 PRO")

# ---------------- SIDEBAR ----------------
with st.sidebar:
    modo=st.radio("Modo",["Producción","Cotización","Cotización m²","Historial"])

    st.divider()
    st.subheader("💾 Guardar proyecto")
    nombre=st.text_input("Nombre proyecto")

    if st.button("Guardar en BD"):
        data=json.dumps(st.session_state.pedido)
        c.execute("INSERT INTO proyectos(nombre,data) VALUES (?,?)",(nombre,data))
        conn.commit()
        st.success("Guardado")

# ================= PRODUCCIÓN =================
if modo=="Producción":

    st.header("Producción")

    anc=st.number_input("Ancho",0.0)
    alt=st.number_input("Alto",0.0)
    hojas=st.selectbox("Hojas",[2,3,4])

    if st.button("Agregar"):
        if hojas==2: z,cz,cp=(anc-16)/2,4,2
        elif hojas==3: z,cz,cp=(anc-26.5)/3,6,4
        else: z,cz,cp=(anc-30)/4,8,6

        st.session_state.pedido.append({
            "ancho":anc,"alto":alt,"hojas":hojas
        })

    for i,v in enumerate(st.session_state.pedido):

        col1,col2=st.columns(2)

        with col1:
            st.write(f"Ventana {i+1}: {v['ancho']}x{v['alto']} ({v['hojas']})")

        with col2:
            if st.button("✏️ Editar",key=f"editp{i}"):
                st.session_state[f"edit_p_{i}"]=True

            if st.button("❌ Eliminar",key=f"delp{i}"):
                st.session_state.pedido.pop(i)
                st.rerun()

        if st.session_state.get(f"edit_p_{i}"):

            nuevo_a=st.number_input("Nuevo ancho",value=v["ancho"],key=f"ea{i}")
            nuevo_h=st.number_input("Nuevo alto",value=v["alto"],key=f"eh{i}")
            nuevo_hojas=st.selectbox("Hojas",[2,3,4],index=[2,3,4].index(v["hojas"]),key=f"ehj{i}")

            if st.button("Guardar cambios",key=f"savep{i}"):
                st.session_state.pedido[i]={
                    "ancho":nuevo_a,
                    "alto":nuevo_h,
                    "hojas":nuevo_hojas
                }
                st.session_state[f"edit_p_{i}"]=False
                st.rerun()

# ================= COTIZACIÓN =================
elif modo=="Cotización":

    st.header("Cotización")

    color_al=st.selectbox("Color aluminio",list(PRECIOS_AL.keys()))
    color_vid=st.selectbox("Color vidrio",list(PRECIOS_VID.keys()))
    ganancia=st.number_input("Ganancia %",0.0,100.0,30.0)

    anc=st.number_input("Ancho",0.0,key="c1")
    alt=st.number_input("Alto",0.0,key="c2")
    hojas=st.selectbox("Hojas",[2,3,4],key="c3")

    if st.button("Agregar"):
        st.session_state.cot_lista.append({"ancho":anc,"alto":alt,"hojas":hojas})

    total=0

    for i,v in enumerate(st.session_state.cot_lista):

        st.write(f"{i+1}) {v['ancho']}x{v['alto']} ({v['hojas']})")

        if st.button("✏️ Editar",key=f"editc{i}"):
            st.session_state[f"edit_c_{i}"]=True

        if st.button("❌ Eliminar",key=f"delc{i}"):
            st.session_state.cot_lista.pop(i)
            st.rerun()

        if st.session_state.get(f"edit_c_{i}"):

            na=st.number_input("Nuevo ancho",value=v["ancho"],key=f"eca{i}")
            nh=st.number_input("Nuevo alto",value=v["alto"],key=f"ech{i}")

            if st.button("Guardar",key=f"savec{i}"):
                st.session_state.cot_lista[i]["ancho"]=na
                st.session_state.cot_lista[i]["alto"]=nh
                st.session_state[f"edit_c_{i}"]=False
                st.rerun()

        total+= (v["ancho"]*v["alto"])/10000*300

    total=total+(total*ganancia/100)

    if total>0:
        st.success(f"TOTAL: {r(total)} Bs")

# ================= COTIZACIÓN m² =================
elif modo=="Cotización m²":

    st.header("Cotización m²")

    cliente=st.text_input("Cliente")
    precio=st.number_input("Precio m²",100.0,1000.0,300.0)

    anc=st.number_input("Ancho",0.0,key="m1")
    alt=st.number_input("Alto",0.0,key="m2")
    hojas=st.selectbox("Hojas",[2,3,4],key="m3")

    if st.button("Agregar m2"):
        area=(anc*alt)/10000
        total=area*precio
        st.session_state.cot_m2.append({
            "ancho":anc,"alto":alt,"hojas":hojas,"total":total
        })

    total_general=0

    for i,v in enumerate(st.session_state.cot_m2):

        st.write(f"{i+1}) {v['ancho']}x{v['alto']} → {r(v['total'])}")

        if st.button("✏️ Editar",key=f"editm{i}"):
            st.session_state[f"edit_m_{i}"]=True

        if st.button("❌ Eliminar",key=f"delm{i}"):
            st.session_state.cot_m2.pop(i)
            st.rerun()

        if st.session_state.get(f"edit_m_{i}"):

            na=st.number_input("Nuevo ancho",value=v["ancho"],key=f"ema{i}")
            nh=st.number_input("Nuevo alto",value=v["alto"],key=f"emh{i}")

            if st.button("Guardar",key=f"savem{i}"):
                st.session_state.cot_m2[i]["ancho"]=na
                st.session_state.cot_m2[i]["alto"]=nh
                st.session_state[f"edit_m_{i}"]=False
                st.rerun()

        total_general+=v["total"]

    if total_general>0:
        st.success(f"TOTAL: {r(total_general)} Bs")

    if st.button("Guardar en BD"):
        c.execute("INSERT INTO cot_m2(cliente,total,fecha) VALUES (?,?,?)",
                  (cliente,total_general,datetime.now().strftime("%d/%m/%Y")))
        conn.commit()
        st.success("Guardado en historial")

# ================= HISTORIAL =================
elif modo=="Historial":

    st.header("Historial")

    st.subheader("Proyectos")
    for row in c.execute("SELECT id,nombre FROM proyectos"):
        if st.button(f"Cargar {row[1]}"):
            data=c.execute("SELECT data FROM proyectos WHERE id=?",(row[0],)).fetchone()[0]
            st.session_state.pedido=json.loads(data)
            st.success("Proyecto cargado")

    st.subheader("Cotizaciones m²")
    for row in c.execute("SELECT cliente,total,fecha FROM cot_m2"):
        st.write(f"{row[0]} | {row[1]} Bs | {row[2]}")
