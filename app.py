import streamlit as st
import pandas as pd
from datetime import date, timedelta
import qrcode
from io import BytesIO

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Turnos-HDG2", page_icon="🏭", layout="centered")

# --- ESTILOS VISUALES ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 10px; background-color: #FF4B4B; color: white; font-weight: bold; }
    div[data-testid="stMetricValue"] { font-size: 1.1rem; }
    </style>
    """, unsafe_allow_html=True)

# --- DATOS ---
nombres = { "52A": "52A (Palacios)", "52B": "52B (Schneider)", "52C": "52C (Troncoso)", "52D": "52D (Gallardo)" }
dias_esp = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]

# --- FUNCIÓN DE COLORES (NUEVO 🎨) ---
def colorear_celdas(val):
    color = ''
    font_weight = 'normal'
    val_str = str(val)
    
    if 'M' in val_str and 'Mañana' in val_str:
        color = '#fffec8' # Amarillo
    elif 'T' in val_str and 'Tarde' in val_str:
        color = '#ffdcf5' # Naranja suave
    elif 'N' in val_str and 'Noche' in val_str:
        color = '#d0e0ff' # Azul
    elif 'F' in val_str and 'Franco' in val_str:
        color = '#d9f2d0' # Verde
        font_weight = 'bold'
        
    return f'background-color: {color}; color: black; font-weight: {font_weight}'

# --- LÓGICA DE TURNOS ---
def obtener_turnos(fecha_inicio, dias_a_mostrar):
    patron = ["M","M","M","M","M","M", "F", "N","N","N","N","N","N", "F","F","F", "T","T","T","T","T","T", "F","F"]
    offsets = {"52A": 14, "52B": 20, "52C": 2, "52D": 8}
    fecha_base = date(2025, 1, 1)
    iconos = {"M": "☀️ M - Mañana", "T": "🌆 T - Tarde", "N": "🌙 N - Noche", "F": "🏖️ F - Franco"}
    
    datos = []
    for i in range(dias_a_mostrar):
        fecha_actual = fecha_inicio + timedelta(days=i)
        diff = (fecha_actual - fecha_base).days
        
        fila = {
            "Fecha": fecha_actual.strftime("%d/%m"),
            "Día": dias_esp[fecha_actual.weekday()],
            "52A": iconos[patron[(offsets["52A"] + diff) % 24]],
            "52B": iconos[patron[(offsets["52B"] + diff) % 24]],
            "52C": iconos[patron[(offsets["52C"] + diff) % 24]],
            "52D": iconos[patron[(offsets["52D"] + diff) % 24]]
        }
        datos.append(fila)
    return pd.DataFrame(datos)

# --- PANTALLA PRINCIPAL ---
st.title("🏭 Rotación de Turnos")
st.write("Selecciona tu grupo:")

# Selector
grupo = st.selectbox("Grupo:", ["52A", "52B", "52C", "52D"], format_func=lambda x: nombres[x])

# Filtros
c1, c2 = st.columns(2)
fecha = c1.date_input("Desde:", date.today())
dias = c2.slider("Días:", 1, 31, 14)

if st.button("Buscar Turnos"):
    df = obtener_turnos(fecha, dias)
    
    # Mensaje resumen
    hoy_val = df.iloc[0][grupo]
    st.info(f"El {dias_esp[fecha.weekday()]} {fecha.strftime('%d/%m')} estás de: **{hoy_val}**")

    # Ordenar y Mostrar
    cols = ["Fecha", "Día", grupo] + [c for c in ["52A", "52B", "52C", "52D"] if c != grupo]
    st.dataframe(
        df[cols].style.applymap(colorear_celdas), 
        use_container_width=True, 
        hide_index=True
    )

# --- SECCIÓN QR ---
st.divider()
st.header("📱 QR para compartir")
st.write("Escanea o descarga este QR para entrar a la App:")

# 👇👇👇 ¡ATENCIÓN! PEGA TU LINK ACÁ ABAJO 👇👇👇
url = "https://turnos-hdg2-ynyvrw9zsvyrqvet8r746z.streamlit.app/" 
# 👆👆👆 BORRA LO QUE HAY Y PEGA TU LINK REAL 👆👆👆

qr = qrcode.make(url)
buf = BytesIO()
qr.save(buf, format="PNG")
img_bytes = buf.getvalue()

c1, c2 = st.columns([1, 2])
with c1:
    st.image(img_bytes, caption="Escaneame", width=150)
with c2:
    st.download_button("⬇️ Descargar Imagen QR", img_bytes, "qr_turnos.png", "image/png")
