import streamlit as st
import pandas as pd
from datetime import date, timedelta

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Rotación Cañuelas", page_icon="🏭", layout="centered")

# --- ESTILOS VISUALES ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 10px; background-color: #FF4B4B; color: white; font-weight: bold; }
    div[data-testid="stMetricValue"] { font-size: 1.1rem; }
    </style>
    """, unsafe_allow_html=True)

# --- NOMBRES DE LOS REFERENTES ---
nombres = {
    "52A": "52A (Palacios)",
    "52B": "52B (Schneider)",
    "52C": "52C (Troncoso)",
    "52D": "52D (Gallardo)"
}

# --- TRUCO PARA DÍAS EN ESPAÑOL ---
def traducir_dia(fecha):
    dias_esp = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
    return dias_esp[fecha.weekday()]

# --- MOTOR DE CÁLCULO ---
def obtener_turnos(fecha_inicio, dias_a_mostrar):
    # Patrón: 6M - 1F - 6N - 3F - 6T - 2F
    patron = ["M","M","M","M","M","M", "F", "N","N","N","N","N","N", "F","F","F", "T","T","T","T","T","T", "F","F"]
    
    offsets = {"52A": 14, "52B": 20, "52C": 2, "52D": 8}
    fecha_base = date(2025, 1, 1)
    
    iconos = {
        "M": "☀️ Mañana", 
        "T": "🌆 Tarde", 
        "N": "🌙 Noche", 
        "F": "🏖️ Franco"
    }
    
    datos = []
    
    for i in range(dias_a_mostrar):
        fecha_actual = fecha_inicio + timedelta(days=i)
        diff = (fecha_actual - fecha_base).days
        
        # Calcular índices
        idx_a = (offsets["52A"] + diff) % 24
        idx_b = (offsets["52B"] + diff) % 24
        idx_c = (offsets["52C"] + diff) % 24
        idx_d = (offsets["52D"] + diff) % 24
        
        fila = {
            "Fecha": fecha_actual,
            "Fecha_Texto": fecha_actual.strftime("%d/%m"),
            "Día": traducir_dia(fecha_actual), # <--- AQUÍ USAMOS LA TRADUCCIÓN
            "52A": iconos[patron[idx_a]],
            "52B": iconos[patron[idx_b]],
            "52C": iconos[patron[idx_c]],
            "52D": iconos[patron[idx_d]]
        }
        datos.append(fila)
        
    return pd.DataFrame(datos)

# --- INTERFAZ GRÁFICA ---

st.title("🏭 Rotación de Turnos")
st.write("Selecciona tu grupo para ver tu calendario.")

# 1. Selector de Grupo
grupo_seleccionado = st.selectbox(
    "¿A qué grupo perteneces?",
    ["52A", "52B", "52C", "52D"],
    format_func=lambda x: nombres[x]
)

st.divider()

# 2. Filtros
col1, col2 = st.columns(2)
with col1:
    fecha_elegida = st.date_input("Fecha de inicio", date.today())
with col2:
    cantidad_dias = st.slider("Días a ver", 1, 31, 7)

# 3. Resultados
if st.button("Buscar Turnos"):
    df = obtener_turnos(fecha_elegida, cantidad_dias)
    
    turno_hoy = df.iloc[0][grupo_seleccionado]
    dia_nombre = traducir_dia(fecha_elegida)
    
    st.success(f"Hola **{grupo_seleccionado}**: El **{dia_nombre} {fecha_elegida.strftime('%d/%m')}** entras de **{turno_hoy}**")

    # Configurar columnas
    column_config = {
        "Fecha": st.column_config.TextColumn("📅", width="small"),
        "Fecha_Texto": st.column_config.TextColumn("Fecha", width="small"),
        "Día": st.column_config.TextColumn("Día", width="small"),
        "52A": st.column_config.TextColumn("52A", width="small"),
        "52B": st.column_config.TextColumn("52B", width="small"),
        "52C": st.column_config.TextColumn("52C", width="small"),
        "52D": st.column_config.TextColumn("52D", width="small"),
    }
    
    column_config[grupo_seleccionado] = st.column_config.TextColumn(
        f"🔴 TU TURNO", 
        width="medium"
    )

    # Ordenar columnas
    cols_ordenadas = ["Fecha_Texto", "Día", grupo_seleccionado] + [c for c in ["52A", "52B", "52C", "52D"] if c != grupo_seleccionado]
    
    st.dataframe(
        df[cols_ordenadas],
        use_container_width=True,
        hide_index=True,
        column_config=column_config
    )
