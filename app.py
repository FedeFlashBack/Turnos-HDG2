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
    div[data-testid="stMetricValue"] { font-size: 1rem; }
    </style>
    """, unsafe_allow_html=True)

# --- DATOS ---
nombres = { 
    "52A": "52A (Palacios)", 
    "52B": "52B (Schneider)", 
    "52C": "52C (Troncoso)", 
    "52D": "52D (Gallardo)" 
}
dias_esp = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]

# --- FERIADOS 2025 y 2026 ---
feriados = [
    date(2025, 1, 1), date(2025, 3, 3), date(2025, 3, 4), date(2025, 3, 24),
    date(2025, 4, 2), date(2025, 4, 18), date(2025, 5, 1), date(2025, 5, 25),
    date(2025, 6, 17), date(2025, 6, 20), date(2025, 7, 9), date(2025, 8, 17),
    date(2025, 10, 12), date(2025, 11, 20), date(2025, 12, 8), date(2025, 12, 25),
    date(2026, 1, 1), date(2026, 2, 16), date(2026, 2, 17), date(2026, 3, 24),
    date(2026, 4, 2), date(2026, 4, 3), date(2026, 5, 1), date(2026, 5, 25),
    date(2026, 6, 17), date(2026, 6, 20), date(2026, 7, 9), date(2026, 8, 17),
    date(2026, 10, 12), date(2026, 11, 20), date(2026, 12, 8), date(2026, 12, 25)
]

# --- PATRÓN DETALLADO ---
patron_detalle = [
    "M1","M2","M3","M4","M5","M6", # Mañana
    "F1",                          # Franco
    "N1","N2","N3","N4","N5","N6", # Noche
    "F1","F2","F3",                # Franco
    "T1","T2","T3","T4","T5","T6", # Tarde
    "F1","F2"                      # Franco
]

# --- FUNCIONES ---
def calcular_un_dia(fecha):
    offsets = {"52A": 14, "52B": 20, "52C": 2, "52D": 8}
    fecha_base = date(2025, 1, 1)
    diff = (fecha - fecha_base).days
    estado = {}
    for grupo in ["52A", "52B", "52C", "52D"]:
        codigo = patron_detalle[(offsets[grupo] + diff) % 24]
        estado[grupo] = codigo
    return estado

def obtener_tabla(fecha_inicio, dias_a_mostrar):
    datos = []
    for i in range(dias_a_mostrar):
        fecha_actual = fecha_inicio + timedelta(days=i)
        estado = calcular_un_dia(fecha_actual)
        marca = " 🇦🇷" if fecha_actual in feriados else ""
        fila = {
            "Fecha": fecha_actual.strftime("%d/%m"),
            "Día": dias_esp[fecha_actual.weekday()],
            "52A": estado["52A"] + marca,
            "52B": estado["52B"] + marca,
            "52C": estado["52C"] + marca,
            "52D": estado["52D"] + marca,
        }
        datos.append(fila)
    return pd.DataFrame(datos)

def colorear_celdas(val):
    val_str = str(val)
    color = ''
    weight = 'normal'
    if '🇦🇷' in val_str: color = '#ffb3b3'; weight = 'bold'
    elif 'M' in val_str: color = '#fffec8'
    elif 'T' in val_str: color = '#ffdcf5'
    elif 'N' in val_str: color = '#d0e0ff'
    elif 'F' in val_str: color = '#d9f2d0'
    return f'background-color: {color}; color: black; font-weight: {weight}'

# ================= INTERFAZ =================

st.title("🏭 Turno-HDG2")

# --- PANEL DE SITUACIÓN ACTUAL ---
st.markdown("### 📢 Estado de la Planta (Hoy)")
hoy = date.today()
estado_hoy = calcular_un_dia(hoy)
quien_m = [k for k,v in estado_hoy.items() if "M" in v][0]
quien_t = [k for k,v in estado_hoy.items() if "T" in v][0]
quien_n = [k for k,v in estado_hoy.items() if "N" in v][0]
quien_f = [k for k,v in estado_hoy.items() if "F" in v][0]

c1, c2, c3, c4 = st.columns(4)
c1.metric("☀️ Mañana", quien_m, estado_hoy[quien_m])
c2.metric("🌆 Tarde", quien_t, estado_hoy[quien_t])
c3.metric("🌙 Noche", quien_n, estado_hoy[quien_n])
c4.metric("🏖️ Franco", quien_f, estado_hoy[quien_f])

st.divider()

# --- BUSCADOR ---
st.write("### 📅 Calendario Detallado")
grupo_clave = st.selectbox("Ver cronograma de:", ["52A", "52B", "52C", "52D"], format_func=lambda x: nombres[x])

c1, c2 = st.columns(2)
fecha = c1.date_input("Desde:", date.today())
dias = c2.slider("Cantidad de días:", 1, 45, 14)

if st.button("Buscar Turnos"):
    df = obtener_tabla(fecha, dias)
    
    cfg = {
        "Fecha": st.column_config.TextColumn("📅 Fecha", width="small"),
        "Día": st.column_config.TextColumn("Día", width="small"),
        "52A": st.column_config.TextColumn(nombres["52A"], width="small"),
        "52B": st.column_config.TextColumn(nombres["52B"], width="small"),
        "52C": st.column_config.TextColumn(nombres["52C"], width="small"),
        "52D": st.column_config.TextColumn(nombres["52D"], width="small"),
    }
    cfg[grupo_clave] = st.column_config.TextColumn(f"🔴 {nombres[grupo_clave]}", width="medium")

    cols = ["Fecha", "Día", grupo_clave] + [c for c in ["52A", "52B", "52C", "52D"] if c != grupo_clave]
    
    # Tabla con corrección de colores (Solo pinta los equipos)
    st.dataframe(
        df[cols].style.applymap(colorear_celdas, subset=["52A", "52B", "52C", "52D"]), 
        use_container_width=True, 
        hide_index=True, 
        column_config=cfg
    )

    # Botón Excel
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📊 Descargar Excel (CSV)", csv, f'turnos_{grupo_clave}.csv', 'text/csv')

# --- REFERENCIAS ---
st.divider()
with st.expander("ℹ️ Referencias"):
    st.markdown("""
    * **M1-M6**: Mañana.
    * **T1-T6**: Tarde.
    * **N1-N6**: Noche.
    * **F1-F3**: Franco.
    * **🇦🇷**: Feriado Nacional.
    """)

# --- QR ---
with st.expander("📱 Descargar QR"):
    url = "https://turnos-hdg2-ynyvrw9zsvyrqvet8r746z.streamlit.app/" 
    qr = qrcode.make(url)
    buf = BytesIO()
    qr.save(buf, format="PNG")
    st.download_button("⬇️ Descargar QR", buf.getvalue(), "qr_turnos.png", "image/png")
