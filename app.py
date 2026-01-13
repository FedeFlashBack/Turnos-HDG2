import streamlit as st
import pandas as pd
from datetime import date, timedelta

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Rotación 52C", page_icon="📅", layout="centered")

# --- ESTILOS PARA CELULAR ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 10px; background-color: #0068C9; color: white; font-weight: bold; padding: 10px; }
    div[data-testid="stMetricValue"] { font-size: 1.1rem; }
    </style>
    """, unsafe_allow_html=True)

# --- LÓGICA DEL TURNO ---
def obtener_turnos(fecha_inicio, dias_a_mostrar):
    # Patrón: 6M - 1F - 6N - 3F - 6T - 2F (Total 24 días)
    patron = ["M","M","M","M","M","M", "F", "N","N","N","N","N","N", "F","F","F", "T","T","T","T","T","T", "F","F"]
    
    # Offsets desde 1 Enero 2025
    offsets = {"52A": 14, "52B": 20, "52C": 2, "52D": 8}
    fecha_base = date(2025, 1, 1)
    
    # Textos bonitos
    iconos = {
        "M": "☀️ Mañana (06-14)", 
        "T": "🌆 Tarde (14-22)", 
        "N": "🌙 Noche (22-06)", 
        "F": "🏖️ Franco"
    }
    
    datos = []
    
    for i in range(dias_a_mostrar):
        fecha_actual = fecha_inicio + timedelta(days=i)
        diff = (fecha_actual - fecha_base).days
        
        # Calcular índices
        idx_c = (offsets["52C"] + diff) % 24 # TÚ
        idx_a = (offsets["52A"] + diff) % 24
        idx_b = (offsets["52B"] + diff) % 24
        idx_d = (offsets["52D"] + diff) % 24
        
        fila = {
            "Fecha": fecha_actual.strftime("%d/%m"),
            "Día": fecha_actual.strftime("%a"),
            "YO (52C)": iconos[patron[idx_c]], 
            "Equipo": f"52A:{patron[idx_a]} | 52B:{patron[idx_b]} | 52D:{patron[idx_d]}"
        }
        datos.append(fila)
        
    return pd.DataFrame(datos)

# --- INTERFAZ ---
st.title("📅 Turnos 52C")
st.write("Consulta rápida de tu rotación y el equipo.")

# Selectores
col1, col2 = st.columns([2, 1])
with col1:
    fecha = st.date_input("Fecha Inicio", date.today())
with col2:
    dias = st.number_input("Días", 1, 30, 7)

# Botón y Resultados
if st.button("Buscar Turnos"):
    df = obtener_turnos(fecha, dias)
    
    # Tarjeta del día
    turno_hoy = df.iloc[0]["YO (52C)"]
    st.info(f"El **{fecha.strftime('%d/%m')}** tu turno es: **{turno_hoy}**")
    
    # Tabla
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Fecha": st.column_config.TextColumn("📅", width="small"),
            "Día": st.column_config.TextColumn("Día", width="small"),
            "YO (52C)": st.column_config.TextColumn("👑 TU TURNO", width="medium"),
            "Equipo": st.column_config.TextColumn("👥 Resto Equipo", width="large"),
        }
    )
