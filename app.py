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
conn.commit()

# ---------------- UTIL ----------------
def r(x): return round(x,1)

def optimizar_barras(piezas, largo=600):
    piezas = sorted(piezas, reverse=True)
    barras=[]
    for p in piezas:
        for b in barras:
            if sum(b)+p<=largo:
                b.append(p)
                break
        else:
            barras.append([p])
    return barras

# ---------------- PDF M2 ----------------
def pdf_m2(lista, cliente, total):
    pdf=FPDF(); pdf.add_page()

    pdf.set_font("Helvetica","B",16)
    pdf.cell(190,10,"COTIZACION",ln=True,align="C")

    pdf.set_font("Helvetica","",10)
    pdf.cell(190,6,f"Cliente: {cliente}",ln=True)
    pdf.cell(190,6,f"Fecha: {datetime.now().strftime('%d/%m/%Y')}",ln=True)

    y_base=pdf.get_y()+5
    col=0

    for i,v in enumerate(lista):
        x=15+(col*95)
        y=y_base

        pdf.set_xy(x,y)
        pdf.cell(80,5,f"V{i+1}: {r(v['ancho'])}x{r(v['alto'])}",ln=False)

        y+=6
        w=60; h=35

        pdf.rect(x,y,w,h)

        for j in range(1,v["hojas"]):
            pdf.line(x+(w/v["hojas"])*j,y,x+(w/v["hojas"])*j,y+h)

        # ancho
        pdf.line(x,y+h+2,x+w,y+h+2)
        pdf.text(x+w/2-10,y+h+6,f"{r(v['ancho'])}")

        # alto
        pdf.line(x-3,y,x-3,y+h)
        pdf.text(x-15,y+h/2,f"{r(v['alto'])}")

        col+=1
        if col==2:
            col=0
            y_base+=55

    pdf.set_y(y_base+5)
    pdf.cell(190,10,f"TOTAL: {r(total)} Bs",ln=True)

    return pdf.output(dest="S").encode("latin1")

# ---------------- APP ----------------
st.set_page_config(layout="wide")
st.title("🛠️ Sistema Línea 25 PRO")

# estado global completo
if "app_data" not in st.session_state:
    st.session_state.app_data={
        "produccion":[],
        "cotizacion":[],
        "m2":[]
    }

data=st.session_state.app_data

# ---------------- SIDEBAR ----------------
with st.sidebar:
    modo=st.radio("Modo",["Producción","Cotización","Cotización m²","Historial"])

    st.divider()
    nombre=st.text_input("Nombre proyecto")

    if st.button("💾 Guardar TODO"):
        c.execute("INSERT INTO proyectos(nombre,data) VALUES (?,?)",
                  (nombre,json.dumps(data)))
        conn.commit()
        st.success("Guardado completo")

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

        data["produccion"].append({
            "medida":f"{anc}x{alt}",
            "div":hojas,
            "detalles":{
                "JAMBA":{"medida":alt,"cant":2},
                "RIEL SUPERIOR":{"medida":anc-1.5,"cant":1},
                "RIEL INFERIOR":{"medida":anc-1.5,"cant":1},
                "PIERNA":{"medida":alt-3.5,"cant":cp},
                "GANCHO":{"medida":alt-3.5,"cant":2},
                "ZOCALO":{"medida":z,"cant":cz}
            },
            "vidrio":{"ancho":z+1.5,"alto":alt-15,"cant":hojas}
        })

    for i,v in enumerate(data["produccion"]):
        with st.expander(f"{v['medida']}"):
            for n,info in v["detalles"].items():
                st.write(f"{info['cant']} {n}: {r(info['medida'])}")

            if st.button("❌ Eliminar",key=f"p{i}"):
                data["produccion"].pop(i)
                st.rerun()

# ================= COTIZACIÓN =================
elif modo=="Cotización":

    st.header("Cotización")

    anc=st.number_input("Ancho",0.0)
    alt=st.number_input("Alto",0.0)
    hojas=st.selectbox("Hojas",[2,3,4])

    if st.button("Agregar"):
        data["cotizacion"].append({"ancho":anc,"alto":alt,"hojas":hojas})

    for i,v in enumerate(data["cotizacion"]):
        st.write(f"{i+1}) {v['ancho']}x{v['alto']}")

        if st.button("❌",key=f"c{i}"):
            data["cotizacion"].pop(i)
            st.rerun()

# ================= M2 =================
elif modo=="Cotización m²":

    st.header("Cotización m²")

    cliente=st.text_input("Cliente")
    precio=st.number_input("Precio m²",100.0,1000.0,300.0)

    anc=st.number_input("Ancho",0.0)
    alt=st.number_input("Alto",0.0)
    hojas=st.selectbox("Hojas",[2,3,4])

    if st.button("Agregar"):
        area=(anc*alt)/10000
        total=area*precio
        data["m2"].append({
            "ancho":anc,"alto":alt,"hojas":hojas,"total":total
        })

    total_general=0

    for i,v in enumerate(data["m2"]):
        st.write(f"{i+1}) {v['ancho']}x{v['alto']} → {r(v['total'])}")

        if st.button("❌",key=f"m{i}"):
            data["m2"].pop(i)
            st.rerun()

        total_general+=v["total"]

    if total_general>0:
        st.success(f"TOTAL: {r(total_general)} Bs")

        pdf=pdf_m2(data["m2"],cliente,total_general)
        st.download_button("📄 PDF",pdf,"cotizacion.pdf")

# ================= HISTORIAL =================
elif modo=="Historial":

    st.header("Historial")

    for row in c.execute("SELECT id,nombre FROM proyectos ORDER BY id DESC"):
        col1,col2=st.columns([3,1])

        with col1:
            st.write(row[1])

        with col2:
            if st.button("Cargar",key=row[0]):
                d=c.execute("SELECT data FROM proyectos WHERE id=?",(row[0],)).fetchone()[0]
                st.session_state.app_data=json.loads(d)
                st.success("Cargado completo")
                st.rerun()
