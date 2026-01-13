import streamlit as st
import pandas as pd
from datetime import date, timedelta
from zoneinfo import ZoneInfo

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Rotación Cañuelas", page_icon="🏭", layout="centered")

# --- ESTILOS VISUALES (CSS) ---
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

# --- CONSTANTES ---
PATRON = ["M","M","M","M","M","M","F", "N","N","N","N","N","N","F","F","F", "T","T","T","T","T","T","F","F"]
OFFSETS = {"52A": 14, "52B": 20, "52C": 2, "52D": 8}
FECHA_BASE = date(2025, 1, 1)

ICONOS = {"M": "☀️ Mañana", "T": "🌆 Tarde", "N": "🌙 Noche", "F": "🏖️ Franco"}
DIAS_ES = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]

def hoy_ar() -> date:
    return pd.Timestamp.now(tz=ZoneInfo("America/Argentina/Buenos_Aires")).date()

def nombre_dia_es(fecha: date) -> str:
    return DIAS_ES[fecha.weekday()]

@st.cache_data(show_spinner=False)
def obtener_turnos(fecha_inicio: date, dias_a_mostrar: int) -> pd.DataFrame:
    datos = []
    for i in range(dias_a_mostrar):
        fecha_actual = fecha_inicio + timedelta(days=i)
        diff = (fecha_actual - FECHA_BASE).days

        fila = {"Fecha": fecha_actual, "Día": nombre_dia_es(fecha_actual)}

        # guardo código + display para cada equipo
        for eq, off in OFFSETS.items():
            idx = (off + diff) % len(PATRON)
            codigo = PATRON[idx]
            fila[eq] = ICONOS[codigo]
            fila[f"{eq}_cod"] = codigo  # para stats / estilo

        datos.append(fila)

    return pd.DataFrame(datos)

def estilo_turnos(df: pd.DataFrame, cols_turnos: list[str], mi_grupo: str):
    # Colores suaves
    def color_por_texto(texto: str) -> str:
        if "Mañana" in str(texto): return "background-color: #fff3cd;"  # amarillo suave
        if "Tarde"  in str(texto): return "background-color: #d1ecf1;"  # celeste suave
        if "Noche"  in str(texto): return "background-color: #e2e3ff;"  # violeta suave
        if "Franco" in str(texto): return "background-color: #d4edda;"  # verde suave
        return ""

    styler = df.style.applymap(color_por_texto, subset=cols_turnos)

    # Resalto tu columna (más fuerte, pero sin gritar)
    styler = styler.set_properties(subset=[mi_grupo], **{"font-weight": "800", "border": "2px solid #FF4B4B"})
    return styler

# --- UI ---
st.title("🏭 Rotación de Turnos")
st.write("Elegí tu grupo, buscá fechas y listo. Esto no falla… salvo que el universo se ponga creativo.")

# 1) Selector de grupo
grupo_seleccionado = st.selectbox(
    "¿A qué grupo perteneces?",
    ["52A", "52B", "52C", "52D"],
    format_func=lambda x: nombres[x]
)

st.divider()

# 2) Filtros
c1, c2, c3 = st.columns([2, 1, 1])

col1, col2 = st.columns(2)
with col1:
    fecha_elegida = st.date_input("Fecha de inicio", date.today())
    df = obtener_turnos(fecha_elegida, int(cantidad_dias))
turno_hoy = df.iloc[0][grupo_seleccionado]
st.success(f"Hola **{grupo_seleccionado}**: El día {fecha_elegida.strftime('%d/%m')} entras de **{turno_hoy}**")
with col2:
    cantidad_dias = st.slider("Días a ver", min_value=1, max_value=31, value=7)

solo_mi_grupo = st.checkbox("👁️ Ver solo mi grupo", value=False)

# 3) Acción principal
if st.button("Buscar Turnos"):
    df = obtener_turnos(st.session_state["fecha_inicio"], int(cantidad_dias))

    turno_hoy = df.iloc[0][grupo_seleccionado]
    st.success(f"Hola **{grupo_seleccionado}**: El **{st.session_state['fecha_inicio'].strftime('%d/%m')}** entrás de **{turno_hoy}**")

    # --- Stats rápidas del rango para TU grupo ---
    cod_col = f"{grupo_seleccionado}_cod"
    conteo = df[cod_col].value_counts().to_dict()
    m = conteo.get("M", 0)
    t = conteo.get("T", 0)
    n = conteo.get("N", 0)
    f = conteo.get("F", 0)

    s1, s2, s3, s4 = st.columns(4)
    s1.metric("☀️ Mañanas", m)
    s2.metric("🌆 Tardes", t)
    s3.metric("🌙 Noches", n)
    s4.metric("🏖️ Francos", f)

    # --- Columnas a mostrar ---
    base_cols = ["Fecha", "Día"]
    turnos_cols = [grupo_seleccionado] if solo_mi_grupo else ["52A", "52B", "52C", "52D"]

    # Orden: Fecha, Día, TU grupo primero, luego resto (si aplica)
    if not solo_mi_grupo:
        orden = base_cols + [grupo_seleccionado] + [c for c in ["52A","52B","52C","52D"] if c != grupo_seleccionado]
    else:
        orden = base_cols + [grupo_seleccionado]

    df_view = df[orden].copy()

    # Column config (limpio)
    column_config = {
        "Fecha": st.column_config.DateColumn("📅 Fecha", format="DD/MM", width="small"),
        "Día": st.column_config.TextColumn("Día", width="small"),
        "52A": st.column_config.TextColumn("52A", width="small"),
        "52B": st.column_config.TextColumn("52B", width="small"),
        "52C": st.column_config.TextColumn("52C", width="small"),
        "52D": st.column_config.TextColumn("52D", width="small"),
    }
    column_config[grupo_seleccionado] = st.column_config.TextColumn(
        f"🔴 TU TURNO ({grupo_seleccionado})",
        width="medium",
        help="Este es tu horario"
    )

    # --- Tabla con colores ---
    st.dataframe(
        estilo_turnos(df_view, [c for c in turnos_cols if c in df_view.columns], grupo_seleccionado),
        use_container_width=True,
        hide_index=True,
        column_config=column_config
    )

    # --- Descargar CSV (lo que estás viendo) ---
    csv_bytes = df_view.to_csv(index=False).encode("utf-8-sig")  # utf-8-sig abre lindo en Excel
    st.download_button(
        "⬇️ Descargar CSV",
        data=csv_bytes,
        file_name=f"rotacion_{grupo_seleccionado}_{st.session_state['fecha_inicio'].strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )
