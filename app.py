import streamlit as st
import pandas as pd
from datetime import date, timedelta

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Turnos-HDG2", page_icon="🏭", layout="centered")

# --- ESTILOS CSS ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 10px; background-color: #FF4B4B; color: white; font-weight: bold; }
    div[data-testid="stMetricValue"] { font-size: 1.1rem; }
    </style>
    """, unsafe_allow_html=True)

# --- DATOS ---
nombres = { "52A": "52A (Palacios)", "52B": "52B (Schneider)", "52C": "52C (Troncoso)", "52D": "52D (Gallardo)" }
dias_esp = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]

# --- FUNCIÓN DE COLORES (LA MAGIA 🎨) ---
def colorear_celdas(val):
    color = ''
    font_weight = 'normal'
    
    # Buscamos letras clave en el texto (M, T, N, F)
    if 'M' in str(val) and 'Mañana' in str(val):
        color = '#fffec8' # Amarillo patito suave
    elif 'T' in str(val) and 'Tarde' in str(val):
        color = '#ffdcf5' # Rosado/Naranja suave
    elif 'N' in str(val) and 'Noche' in str(val):
        color = '#d0e0ff' # Azul suave
    elif 'F' in str(val) and 'Franco' in str(val):
        color = '#d9f2d0' # Verde suave
        font_weight = 'bold'
        
    return f'background-color: {color}; color: black; font-weight: {font_weight}'

# --- LÓGICA ---
def obtener_turnos(fecha_inicio, dias_a_mostrar):
    patron = ["M","M","M","M","M","M", "F", "N","N","N","N","N","N", "F","F","F", "T","T","T","T","T","T", "F","F"]
    offsets = {"52A": 14, "52B": 20, "52C": 2, "52D": 8}
    fecha_base = date(2025, 1, 1)
    
    # Usamos textos cortos para que la tabla no se rompa en el celu
    iconos = {"M": "☀️ M", "T": "🌆 T", "N": "🌙 N", "F": "🏖️ F"}
    
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

# --- INTERFAZ ---
st.title("🏭 Rotación de Turnos")

# Opción para Login (SOLO VISUAL POR AHORA)
modo = st.radio("Modo de acceso:", ["Invitado (Solo ver)", "Mi Usuario (Cargar Horas)"], horizontal=True)

if modo == "Mi Usuario (Cargar Horas)":
    st.warning("⚠️ Función en desarrollo: Próximamente podrás guardar tus extras con un PIN de 4 dígitos.")
    # Aquí iría el campo para poner el PIN

# Selector de Grupo
grupo = st.selectbox("Tu Grupo:", ["52A", "52B", "52C", "52D"], format_func=lambda x: nombres[x])

# Filtros
c1, c2 = st.columns(2)
fecha = c1.date_input("Desde:", date.today())
dias = c2.slider("Días:", 1, 31, 10)

if st.button("Buscar Turnos"):
    df = obtener_turnos(fecha, dias)
    
    # Mensaje resumen
    hoy_val = df.iloc[0][grupo]
    st.info(f"El {dias_esp[fecha.weekday()]} {fecha.strftime('%d/%m')} estás de: **{hoy_val}**")

    # Ordenar columnas (Tu grupo primero)
    cols = ["Fecha", "Día", grupo] + [c for c in ["52A", "52B", "52C", "52D"] if c != grupo]
    df_show = df[cols]
    
    # APLICAR COLORES 🎨
    # Esto pinta la tabla según el contenido
    st.dataframe(
        df_show.style.applymap(colorear_celdas), 
        use_container_width=True, 
        hide_index=True
    )

# --- QR ---
import qrcode
from io import BytesIO
st.divider()
with st.expander("📱 Descargar QR"):
    st.write("Link directo para imprimir:")
    # PONE TU LINK REAL ACÁ
    url = "https://turnos-hdg2-ynyvrw9zsvyrqvet8r746z.streamlit.app/" 
    qr = qrcode.make(url)
    buf = BytesIO()
    qr.save(buf, format="PNG")
    st.download_button("⬇️ Bajar QR", buf.getvalue(), "qr.png", "image/png")
