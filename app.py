import streamlit as st
import json
from fpdf import FPDF
import math
from datetime import datetime

# ---------------- UTIL ----------------
def r(x): return round(x,1)

# ---------------- OPTIMIZACIÓN ----------------
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

# ---------------- PDF ----------------
def pdf_ventanas(pedido):
    pdf=FPDF(); pdf.add_page()
    pdf.set_font("Helvetica","B",16)
    pdf.cell(190,10,"PRODUCCION LINEA 25",ln=True,align="C")

    for v in pedido:
        pdf.set_font("Helvetica","B",12)
        pdf.cell(190,8,f"{v['medida']} ({v['div']} hojas)",ln=True)

        pdf.set_font("Helvetica","",10)
        for n,i in v["detalles"].items():
            pdf.cell(190,6,f"{i['cant']} {n}: {r(i['medida'])}",ln=True)

        vid=v["vidrio"]
        pdf.cell(190,6,f"{vid['cant']} vidrio: {r(vid['alto'])} x {r(vid['ancho'])}",ln=True)
        pdf.ln(3)

    return pdf.output(dest="S").encode("latin1")

def pdf_optimizacion(todos):
    pdf=FPDF(); pdf.add_page()
    pdf.set_font("Helvetica","B",16)
    pdf.cell(190,10,"OPTIMIZACION",ln=True,align="C")

    for p,piezas in todos.items():
        if p!="VIDRIO" and piezas:
            pdf.cell(190,8,p,ln=True)
            for i,b in enumerate(optimizar_barras(piezas),1):
                pdf.cell(190,6,f"Tira {i}: {[r(x) for x in b]} | sobra {r(600-sum(b))}",ln=True)

    return pdf.output(dest="S").encode("latin1")

# ---------------- MATERIALES ----------------
def calcular_materiales(todos):
    resumen={}
    for p,piezas in todos.items():
        if p!="VIDRIO":
            resumen[p]=len(optimizar_barras(piezas))

    total_area=sum(v["ancho"]*v["alto"]*v["cant"] for v in todos["VIDRIO"])
    resumen["VIDRIO"]=math.ceil(total_area/(330*214))
    return resumen

# ---------------- PRECIOS ----------------
PRECIOS_AL = {
"MT":{"RIEL SUPERIOR":187,"RIEL INFERIOR":187,"ZOCALO":177,"GANCHO":171,"JAMBA":159,"PIERNA":171},
"CH":{"RIEL SUPERIOR":191,"RIEL INFERIOR":191,"ZOCALO":180,"GANCHO":171,"JAMBA":160,"PIERNA":171},
"BR":{"RIEL SUPERIOR":192,"RIEL INFERIOR":192,"ZOCALO":183,"GANCHO":171,"JAMBA":167,"PIERNA":171},
"CH.O":{"RIEL SUPERIOR":191,"RIEL INFERIOR":191,"ZOCALO":172,"GANCHO":169,"JAMBA":166,"PIERNA":169},
"MD":{"RIEL SUPERIOR":215,"RIEL INFERIOR":215,"ZOCALO":192,"GANCHO":173,"JAMBA":177,"PIERNA":173}
}

PRECIOS_VID={"Bronce":500,"Incoloro":490,"Gris":780,"Estipoly Incoloro":320}

# ---------------- APP ----------------
st.set_page_config(layout="wide")
st.title("🛠️ Sistema Linea 25 PRO")

# estado
if "pedido" not in st.session_state:
    st.session_state.pedido=[]
if "cot_m2" not in st.session_state:
    st.session_state.cot_m2=[]

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.header("Proyecto")

    if st.session_state.pedido:
        st.download_button("Guardar",json.dumps(st.session_state.pedido),"proyecto.json")

    file=st.file_uploader("Abrir",type="json")
    if file:
        st.session_state.pedido=json.load(file)

    if st.button("Nuevo"):
        st.session_state.pedido=[]
        st.rerun()

    modo=st.radio("Modo",["Producción","Cotización","Cotización m²"])

# ================= PRODUCCIÓN =================
if modo=="Producción":

    st.header("Producción")

    anc=st.number_input("Ancho",0.0,key="p_a")
    alt=st.number_input("Alto",0.0,key="p_h")
    hojas=st.selectbox("Hojas",[2,3,4],key="p_hj")

    if st.button("Agregar"):
        if hojas==2: z,cz,cp=(anc-16)/2,4,2
        elif hojas==3: z,cz,cp=(anc-26.5)/3,6,4
        else: z,cz,cp=(anc-30)/4,8,6

        st.session_state.pedido.append({
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

    if st.session_state.pedido:

        todos={"JAMBA":[],"RIEL SUPERIOR":[],"RIEL INFERIOR":[],"PIERNA":[],"GANCHO":[],"ZOCALO":[],"VIDRIO":[]}

        for i,v in enumerate(st.session_state.pedido):
            with st.expander(v["medida"]):
                for n,info in v["detalles"].items():
                    st.write(f"{info['cant']} {n}: {r(info['medida'])}")
                    todos[n]+= [info["medida"]]*info["cant"]

                vid=v["vidrio"]
                st.write(f"{vid['cant']} vidrio: {r(vid['alto'])} x {r(vid['ancho'])}")
                todos["VIDRIO"].append(vid)

                if st.button("Eliminar",key=f"del{i}"):
                    st.session_state.pedido.pop(i)
                    st.rerun()

        if st.button("Optimizar"):
            for p,piezas in todos.items():
                if p!="VIDRIO":
                    for i,b in enumerate(optimizar_barras(piezas),1):
                        st.write(f"{p} Tira {i}: {[r(x) for x in b]}")

        st.download_button("PDF Ventanas",pdf_ventanas(st.session_state.pedido),"ventanas.pdf")
        st.download_button("PDF Optimización",pdf_optimizacion(todos),"optimizacion.pdf")

# ================= COTIZACIÓN =================
elif modo=="Cotización":

    st.header("Cotización")

    cliente=st.text_input("Cliente")
    color_al=st.selectbox("Color aluminio",list(PRECIOS_AL.keys()))
    color_vid=st.selectbox("Color vidrio",list(PRECIOS_VID.keys()))
    ganancia=st.number_input("Ganancia %",0.0,100.0,30.0)

    anc=st.number_input("Ancho",0.0,key="c_a")
    alt=st.number_input("Alto",0.0,key="c_h")
    hojas=st.selectbox("Hojas",[2,3,4],key="c_hj")

    if st.button("Calcular"):
        if hojas==2: z,cz,cp=(anc-16)/2,4,2
        elif hojas==3: z,cz,cp=(anc-26.5)/3,6,4
        else: z,cz,cp=(anc-30)/4,8,6

        todos={"JAMBA":[alt]*2,"RIEL SUPERIOR":[anc-1.5],"RIEL INFERIOR":[anc-1.5],
               "PIERNA":[alt-3.5]*cp,"GANCHO":[alt-3.5]*2,"ZOCALO":[z]*cz,
               "VIDRIO":[{"ancho":z+1.5,"alto":alt-15,"cant":hojas}]}

        mat=calcular_materiales(todos)

        total=0
        detalle=[]

        for p,b in mat.items():
            if p!="VIDRIO":
                sub=b*PRECIOS_AL[color_al][p]
                total+=sub
                detalle.append(f"{p}: {b} x {PRECIOS_AL[color_al][p]} = {sub}")

        vid_total=mat["VIDRIO"]*PRECIOS_VID[color_vid]
        total+=vid_total
        detalle.append(f"VIDRIO: {mat['VIDRIO']} x {PRECIOS_VID[color_vid]} = {vid_total}")

        total_final=total+(total*ganancia/100)

        st.success(f"TOTAL: {r(total_final)} Bs")

# ================= COTIZACIÓN m² =================
elif modo=="Cotización m²":

    st.header("Cotización m²")

    cliente=st.text_input("Cliente")
    precio=st.number_input("Precio m²",100.0,1000.0,300.0)

    anc=st.number_input("Ancho",0.0,key="m2_a")
    alt=st.number_input("Alto",0.0,key="m2_h")
    hojas=st.selectbox("Hojas",[2,3,4])

    if st.button("Agregar m2"):
        if anc>0 and alt>0:
            area=(anc*alt)/10000
            total=area*precio
            st.session_state.cot_m2.append({
                "ancho":anc,"alto":alt,"hojas":hojas,"total":total
            })

    total_general=0

    for i,v in enumerate(st.session_state.cot_m2):
        st.write(f"{i+1}) {r(v['ancho'])} x {r(v['alto'])} | {v['hojas']} hojas → {r(v['total'])}")
        total_general+=v["total"]

    if total_general>0:
        st.success(f"TOTAL: {r(total_general)} Bs")

    if st.button("PDF m2"):

        pdf=FPDF(); pdf.add_page()

        pdf.set_font("Helvetica","B",16)
        pdf.cell(190,10,"COTIZACION m2",ln=True,align="C")

        pdf.set_font("Helvetica","",11)
        pdf.cell(190,8,f"Cliente: {cliente}",ln=True)
        pdf.cell(190,8,f"Fecha: {datetime.now().strftime('%d/%m/%Y')}",ln=True)

        y_base=pdf.get_y()+5
        col=0

        for i,v in enumerate(st.session_state.cot_m2):

            x=15+(col*95)
            y=y_base

            pdf.set_xy(x,y)
            pdf.cell(80,5,f"V{i+1}: {r(v['ancho'])}x{r(v['alto'])}",ln=False)

            y+=6
            w=60; h=35

            pdf.rect(x,y,w,h)

            for j in range(1,v["hojas"]):
                pdf.line(x+(w/v["hojas"])*j,y,x+(w/v["hojas"])*j,y+h)

            # flechas
            pdf.line(x,y+h+2,x+w,y+h+2)
            pdf.line(x,y+h+2,x+3,y+h-1)
            pdf.line(x+w,y+h+2,x+w-3,y+h-1)

            pdf.text(x+w/2-10,y+h+6,f"{r(v['ancho'])}")

            pdf.line(x-3,y,x-3,y+h)
            pdf.line(x-3,y,x,y+3)
            pdf.line(x-3,y+h,x,y+h-3)

            pdf.text(x-15,y+h/2,f"{r(v['alto'])}")

            col+=1
            if col==2:
                col=0
                y_base+=55

        pdf.set_y(y_base+5)
        pdf.cell(190,10,f"TOTAL: {r(total_general)} Bs",ln=True)

        st.download_button("Descargar PDF",pdf.output(dest="S").encode("latin1"),"cot_m2.pdf")
