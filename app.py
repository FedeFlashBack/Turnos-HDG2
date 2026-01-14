import streamlit as st
import pandas as pd
from datetime import date, timedelta
import qrcode
from io import BytesIO

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Turno-HDG2", page_icon="🏭", layout="centered")

# --- ESTILOS VISUALES ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 10px; background-color: #FF4B4B; color: white; font-weight: bold; }
    div[data-testid="stMetricValue"] { font-size: 1.1rem; }
    </style>
    """, unsafe_allow_html=True)

# --- DATOS DE EQUIPOS ---
nombres = { 
    "52A": "52A (Palacios)", 
    "52B": "52B (Schneider)", 
    "52C": "52C (Troncoso)", 
    "52D": "52D (Gallardo)" 
}

dias_esp = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]

# --- FERIADOS ARGENTINA (2025 y 2026) ---
feriados = [
    # --- 2025 ---
    date(2025, 1, 1), date(2025, 3, 3), date(2025, 3, 4), date(2025, 3, 24),
    date(2025, 4, 2), date(2025, 4, 18), date(2025, 5, 1), date(2025, 5, 25),
    date(2025, 6, 17), date(2025, 6, 20), date(2025, 7, 9), date(2025, 8, 17),
    date(2025, 10, 12), date(2025, 11, 20), date(2025, 12, 8), date(2025, 12, 25),
    
    # --- 2026 (NUEVO) ---
    date(2026, 1, 1),   # Año Nuevo
    date(2026, 2, 16),  # Carnaval Lunes
    date(2026, 2, 17),  # Carnaval Martes
    date(2026, 3, 24),  # Memoria
    date(2026, 4, 2),   # Malvinas
    date(2026, 4, 3),   # Viernes Santo (Cae el 3 en 2026)
    date(2026, 5, 1),   # Trabajador
    date(2026, 5, 25),  # Revolución Mayo
    date(2026, 6, 17),  # Güemes
    date(2026, 6, 20),  # Belgrano
    date(2026, 7, 9),   # Independencia
    date(2026, 8, 17),  # San Martín
    date(2026, 10, 12), # Diversidad
    date(2026, 11, 20), # Soberanía
    date(2026, 12, 8),  # Inmaculada Concepción (TU PEDIDO)
    date(2026, 12, 25)  # Navidad
]

# --- PATRÓN DETALLADO ---
patron_detalle = [
    "M1","M2","M3","M4","M5","M6", # Mañanas
    "F1",                          # Franco
    "N1","N2","N3","N4","N5","N6", # Noches
    "F1","F2","F3",                # Francos
    "T1","T2","T3","T4","T5","T6", # Tardes
    "F1","F2"                      # Francos
]

# --- FUNCIÓN DE COLORES 🎨 ---
def colorear_celdas(val):
    color = ''
    weight = 'normal'
    val_str = str(val)
    
    # Prioridad: Si es Feriado (tiene bandera), color especial
    if '🇦🇷' in val_str:
        color = '#ffb3b3' # Rojo más visible para feriados
        weight = 'bold'
    elif 'M' in val_str:
        color = '#fffec8' # Amarillo
    elif 'T' in val_str:
        color = '#ffdcf5' # Naranja/Rosa
    elif 'N' in val_str:
        color = '#d0e0ff' # Azul
    elif 'F' in val_str:
        color = '#d9f2d0' # Verde
        
    return f'background-color: {color}; color: black; font-weight: {weight}'

# --- LÓGICA DE TURNOS ---
def obtener_turnos(fecha_inicio, dias_a_mostrar):
    offsets = {"52A": 14, "52B": 20, "52C": 2, "52D": 8}
    fecha_base = date(2025, 1, 1)
    
    datos = []
    for i in range(dias_a_mostrar):
        fecha_actual = fecha_inicio + timedelta(days=i)
        diff = (fecha_actual - fecha_base).days
        
        # Detectar Feriado
        es_feriado = fecha_actual in feriados
        marca_feriado = " 🇦🇷" if es_feriado else ""
        
        # Obtener código del día
        codigo_a = patron_detalle[(offsets["52A"] + diff) % 24] + marca_feriado
        codigo_b = patron_detalle[(offsets["52B"] + diff) % 24] + marca_feriado
        codigo_c = patron_detalle[(offsets["52C"] + diff) % 24] + marca_feriado
        codigo_d = patron_detalle[(offsets["52D"] + diff) % 24] + marca_feriado
        
        fila = {
            "Fecha": fecha_actual.strftime("%d/%m"),
            "Día": dias_esp[fecha_actual.weekday()],
            "52A": codigo_a,
            "52B": codigo_b,
            "52C": codigo_c,
            "52D": codigo_d
        }
        datos.append(fila)
    return pd.DataFrame(datos)

# --- PANTALLA PRINCIPAL ---
st.title("🏭 Rotación de Turnos")
st.write("Selecciona tu grupo para ver tu rotación detallada.")

# Selector
grupo_clave = st.selectbox("Tu Grupo:", ["52A", "52B", "52C", "52D"], format_func=lambda x: nombres[x])

# Filtros
c1, c2 = st.columns(2)
fecha = c1.date_input("Desde:", date.today())
dias = c2.slider("Días a ver:", 1, 31, 14)

if st.button("Buscar Turnos"):
    df = obtener_turnos(fecha, dias)
    
    # Mensaje resumen
    hoy_val = df.iloc[0][grupo_clave]
    st.info(f"El **{fecha.strftime('%d/%m')}** tu turno es: **{hoy_val}**")

    # Configuración de columnas
    config_columnas = {
        "Fecha": st.column_config.TextColumn("📅 Fecha", width="small"),
        "Día": st.column_config.TextColumn("Día", width="small"),
        "52A": st.column_config.TextColumn(nombres["52A"], width="small"),
        "52B": st.column_config.TextColumn(nombres["52B"], width="small"),
        "52C": st.column_config.TextColumn(nombres["52C"], width="small"),
        "52D": st.column_config.TextColumn(nombres["52D"], width="small"),
    }

    config_columnas[grupo_clave] = st.column_config.TextColumn(
        f"🔴 {nombres[grupo_clave]}", width="medium"
    )

    # Ordenar columnas
    cols = ["Fecha", "Día", grupo_clave] + [c for c in ["52A", "52B", "52C", "52D"] if c != grupo_clave]
    
    st.dataframe(
        df[cols].style.applymap(colorear_celdas), 
        use_container_width=True, 
        hide_index=True,
        column_config=config_columnas
    )

# --- REFERENCIAS Y QR ---
st.divider()

with st.expander("ℹ️ Referencias"):
    st.markdown("""
    * **M1-M6**: Mañana.
    * **T1-T6**: Tarde.
    * **N1-N6**: Noche.
    * **F1-F3**: Franco.
    * **🇦🇷**: Feriado Nacional (Pago extra o compensatorio).
    """)

with st.expander("📱 Descargar QR"):
    # 👇👇👇 ¡ACORDATE DE PONER TU LINK DE NUEVO! 👇👇👇
    url = "https://turnos-hdg2-ynyvrw9zsvyrqvet8r746z.streamlit.app/" 
    qr = qrcode.make(url)
    buf = BytesIO()
    qr.save(buf, format="PNG")
    st.download_button("⬇️ Descargar QR", buf.getvalue(), "qr_turnos.png", "image/png")
