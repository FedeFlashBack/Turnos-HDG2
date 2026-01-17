import streamlit as st
import pandas as pd
from datetime import date, timedelta, datetime
from zoneinfo import ZoneInfo
from io import BytesIO
import calendar
import qrcode

# ================== CONFIGURACIÓN ==================
st.set_page_config(page_title="Turno-HDG2", page_icon="🏭", layout="centered")

TZ_AR = ZoneInfo("America/Argentina/Buenos_Aires")

def hoy_ar() -> date:
    return datetime.now(TZ_AR).date()

# ================== ESTILOS ==================
st.markdown("""
<style>
.stButton>button { width: 100%; border-radius: 10px; background-color: #FF4B4B; color: white; font-weight: bold; }
div[data-testid="stMetricValue"] { font-size: 1rem; }
h1, h2, h3 { text-align: center; }
</style>
""", unsafe_allow_html=True)

# ================== DATOS ==================
nombres = {
    "52A": "52A (Palacios)",
    "52B": "52B (Schneider)",
    "52C": "52C (Troncoso)",
    "52D": "52D (Gallardo)"
}

GRUPOS = ["52A", "52B", "52C", "52D"]

dias_esp = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
dias_esp_corto = ["Lu", "Ma", "Mi", "Ju", "Vi", "Sa", "Do"]
meses_esp = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
             "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

# ================== FERIADOS (holidays) ==================
try:
    import holidays
    feriados_ar = holidays.country_holidays("AR", years=range(2025, 2031))
    feriados_set = set(feriados_ar.keys())
except Exception:
    # Fallback (menos exacto para móviles)
    feriados_set = set()
    for anio in range(2025, 2031):
        feriados_set.update({
            date(anio, 1, 1), date(anio, 3, 24), date(anio, 4, 2), date(anio, 5, 1),
            date(anio, 5, 25), date(anio, 6, 20), date(anio, 7, 9), date(anio, 8, 17),
            date(anio, 10, 12), date(anio, 11, 20), date(anio, 12, 8), date(anio, 12, 25),
        })

# ================== PATRÓN DE TURNOS ==================
patron_detalle = [
    "M1", "M2", "M3", "M4", "M5", "M6", "F1",
    "N1", "N2", "N3", "N4", "N5", "N6", "F1", "F2", "F3",
    "T1", "T2", "T3", "T4", "T5", "T6", "F1", "F2"
]

offsets = {"52A": 14, "52B": 20, "52C": 2, "52D": 8}
fecha_base = date(2025, 1, 1)

# ================== FUNCIONES ==================
def calcular_estado_dia(fecha: date) -> dict:
    diff = (fecha - fecha_base).days
    es_feriado = fecha in feriados_set
    marca = " 🇦🇷" if es_feriado else ""

    estado = {}
    for grupo in GRUPOS:
        codigo = patron_detalle[(offsets[grupo] + diff) % 24]
        estado[grupo] = {"texto": codigo, "feriado": es_feriado, "marca": marca}
    return estado

@st.cache_data(show_spinner=False)
def obtener_tabla_diaria(fecha_inicio: date, dias_a_mostrar: int) -> pd.DataFrame:
    """
    Devuelve:
    - FechaISO: YYYY-MM-DD (para exportar a Excel/CSV sin que Excel invente meses)
    - Fecha: dd/mm (para mostrar en la app)
    """
    datos = []
    for i in range(dias_a_mostrar):
        fecha_actual = fecha_inicio + timedelta(days=i)
        estado = calcular_estado_dia(fecha_actual)
        datos.append({
            "FechaISO": fecha_actual.strftime("%Y-%m-%d"),
            "Fecha": fecha_actual.strftime("%d/%m"),
            "Día": dias_esp[fecha_actual.weekday()],
            "52A": estado["52A"]["texto"] + estado["52A"]["marca"],
            "52B": estado["52B"]["texto"] + estado["52B"]["marca"],
            "52C": estado["52C"]["texto"] + estado["52C"]["marca"],
            "52D": estado["52D"]["texto"] + estado["52D"]["marca"],
        })
    return pd.DataFrame(datos)

def colorear_celdas_web(val) -> str:
    val_str = str(val)
    color = ""
    weight = "normal"
    if "🇦🇷" in val_str:
        color = "#ffb3b3"; weight = "bold"
    elif "M" in val_str:
        color = "#fffec8"
    elif "T" in val_str:
        color = "#ffdcf5"
    elif "N" in val_str:
        color = "#d0e0ff"
    elif "F" in val_str:
        color = "#d9f2d0"
    return f"background-color: {color}; color: black; font-weight: {weight}"

@st.cache_data(show_spinner=False)
def exportar_tabla_excel(df: pd.DataFrame) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Turnos")
    return output.getvalue()

@st.cache_data(show_spinner=False)
def exportar_tabla_csv_iphone(df: pd.DataFrame) -> bytes:
    """
    CSV compatible con iPhone/iOS:
    - UTF-8 con BOM (utf-8-sig)
    - Remueve emoji 🇦🇷 (a veces rompe previsualizadores)
    """
    df_csv = df.copy()
    # sacamos el emoji para evitar crashes en algunos viewers
    df_csv = df_csv.replace(" 🇦🇷", " AR", regex=False)
    text = df_csv.to_csv(index=False, encoding="utf-8-sig")
    return text.encode("utf-8-sig")

@st.cache_data(show_spinner=False)
def generar_excel_anual(anio: int) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        workbook = writer.book
        ws = workbook.add_worksheet(f"Turnos {anio}")

        ws.set_landscape()
        ws.set_paper(9)          # A4
        ws.fit_to_pages(1, 0)
        ws.set_margins(0.5, 0.5, 0.5, 0.5)

        fmt_titulo = workbook.add_format({"bold": True, "font_size": 14, "bg_color": "#DDDDDD", "border": 1, "align": "left"})
        fmt_dias_letras = workbook.add_format({"bold": True, "align": "center", "bg_color": "#FFEB9C", "border": 1, "font_size": 9})
        fmt_dias_numeros = workbook.add_format({"bold": True, "align": "center", "bg_color": "#F2F2F2", "border": 1, "font_size": 9})
        fmt_grupo = workbook.add_format({"bold": True, "border": 1, "font_size": 10, "align": "left"})

        fmt_m = workbook.add_format({"bg_color": "#FFFEC8", "align": "center", "border": 1, "font_size": 9})
        fmt_t = workbook.add_format({"bg_color": "#FFDCF5", "align": "center", "border": 1, "font_size": 9})
        fmt_n = workbook.add_format({"bg_color": "#D0E0FF", "align": "center", "border": 1, "font_size": 9})
        fmt_f = workbook.add_format({"bg_color": "#D9F2D0", "align": "center", "border": 1, "font_size": 9, "color": "#555555"})
        fmt_fer = workbook.add_format({"bg_color": "#FFB3B3", "align": "center", "border": 1, "bold": True, "font_size": 9})

        ws.set_column(0, 0, 18)
        ws.set_column(1, 31, 2.8)

        fila = 0
        for mes in range(1, 13):
            ws.merge_range(fila, 0, fila, 31, f"{meses_esp[mes]} {anio}", fmt_titulo)
            fila += 1

            dias_en_mes = calendar.monthrange(anio, mes)[1]

            ws.write(fila, 0, "DÍA", fmt_dias_letras)
            for d in range(1, dias_en_mes + 1):
                dia_semana = dias_esp_corto[date(anio, mes, d).weekday()]
                ws.write(fila, d, dia_semana, fmt_dias_letras)
            fila += 1

            ws.write(fila, 0, "FECHA", fmt_dias_numeros)
            for d in range(1, dias_en_mes + 1):
                ws.write(fila, d, d, fmt_dias_numeros)
            fila += 1

            for gr in GRUPOS:
                ws.write(fila, 0, nombres[gr], fmt_grupo)
                for d in range(1, dias_en_mes + 1):
                    f = date(anio, mes, d)
                    info = calcular_estado_dia(f)[gr]
                    letra = info["texto"][0]
                    es_fer = info["feriado"]

                    estilo = fmt_f
                    if es_fer:
                        estilo = fmt_fer
                    elif letra == "M":
                        estilo = fmt_m
                    elif letra == "T":
                        estilo = fmt_t
                    elif letra == "N":
                        estilo = fmt_n

                    ws.write(fila, d, letra, estilo)
                fila += 1

            fila += 1

    return output.getvalue()

def preparar_excel_para_descarga(df_mostrado: pd.DataFrame, df_original: pd.DataFrame) -> pd.DataFrame:
    """
    Devuelve un df igual al mostrado pero con columna Fecha en formato ISO para Excel/CSV.
    """
    df_excel = df_mostrado.copy()
    df_excel["Fecha"] = df_original["FechaISO"].values
    df_excel = df_excel.drop(columns=["FechaISO"], errors="ignore")
    return df_excel

# ================== UI ==================
st.title("🏭 Turno-HDG2")

# --- ESTADO DE PLANTA (HOY) ---
hoy = hoy_ar()
estado_hoy = calcular_estado_dia(hoy)

st.markdown("### 📢 Estado de Planta (Hoy)")
st.caption(f"📌 {dias_esp[hoy.weekday()]} {hoy.strftime('%d/%m/%Y')}")

if estado_hoy["52A"]["feriado"]:
    st.warning("🇦🇷 Hoy es feriado.")

q_m = [k for k, v in estado_hoy.items() if "M" in v["texto"]][0]
q_t = [k for k, v in estado_hoy.items() if "T" in v["texto"]][0]
q_n = [k for k, v in estado_hoy.items() if "N" in v["texto"]][0]
q_f = [k for k, v in estado_hoy.items() if "F" in v["texto"]][0]

c1, c2, c3, c4 = st.columns(4)
c1.metric("☀️ Mañana", nombres[q_m], estado_hoy[q_m]["texto"])
c2.metric("🌆 Tarde", nombres[q_t], estado_hoy[q_t]["texto"])
c3.metric("🌙 Noche", nombres[q_n], estado_hoy[q_n]["texto"])
c4.metric("🏖️ Franco", nombres[q_f], estado_hoy[q_f]["texto"])

# --- ACCESO RÁPIDO (SE ABRE Y CIERRA) ---
if "show_rapido" not in st.session_state:
    st.session_state.show_rapido = False

with st.expander("⚡ Acceso rápido: próximos 14 días", expanded=st.session_state.show_rapido):
    colA, colB = st.columns(2)
    if colA.button("📅 Mostrar", key="btn_mostrar_rapido"):
        st.session_state.show_rapido = True
        st.rerun()
    if colB.button("❌ Cerrar", key="btn_cerrar_rapido"):
        st.session_state.show_rapido = False
        st.rerun()

    if st.session_state.show_rapido:
        df_rapido = obtener_tabla_diaria(hoy, 14)

        df_rapido_mostrar = df_rapido[["Fecha", "Día", "52A", "52B", "52C", "52D"]]

        st.dataframe(
            df_rapido_mostrar.style.applymap(colorear_celdas_web, subset=GRUPOS),
            use_container_width=True,
            hide_index=True
        )

        # Excel: FechaISO
        df_rapido_excel = df_rapido_mostrar.copy()
        df_rapido_excel["Fecha"] = df_rapido["FechaISO"]
        excel_rapido = exportar_tabla_excel(df_rapido_excel)

        # CSV iPhone: UTF-8 BOM + sin emoji
        csv_rapido = exportar_tabla_csv_iphone(df_rapido_excel)

        d1, d2 = st.columns(2)
        with d1:
            st.download_button(
                label="📥 Excel (14 días)",
                data=excel_rapido,
                file_name=f"turnos_prox14_{hoy.strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="dl_rapido_14_xlsx"
            )
        with d2:
            st.download_button(
                label="📄 CSV iPhone (14 días)",
                data=csv_rapido,
                file_name=f"turnos_prox14_{hoy.strftime('%Y%m%d')}.csv",
                mime="text/csv",
                key="dl_rapido_14_csv"
            )

st.divider()

# --- TABS (UNA SE VE, LAS OTRAS SE OCULTAN) ---
tabs = st.tabs(["📅 Calendario Diario", "❄️ Calendario Anual (para imprimir)", "📱 QR"])

# =======================
# TAB 1: CALENDARIO DIARIO
# =======================
with tabs[0]:
    grupo_clave = st.selectbox(
        "Ver cronograma de:",
        GRUPOS,
        format_func=lambda x: nombres[x],
        key="t0_grupo"
    )

    c1, c2 = st.columns(2)
    fecha = c1.date_input("Desde:", hoy_ar(), key="t0_fecha")
    dias = c2.slider("Días:", 1, 45, 14, key="t0_dias")

    if st.button("Ver Tabla", key="t0_btn_ver"):
        df = obtener_tabla_diaria(fecha, dias)

        cfg = {
            "Fecha": st.column_config.TextColumn("📅 Fecha", width="small"),
            "Día": st.column_config.TextColumn("Día", width="small"),
            "52A": st.column_config.TextColumn(nombres["52A"], width="small"),
            "52B": st.column_config.TextColumn(nombres["52B"], width="small"),
            "52C": st.column_config.TextColumn(nombres["52C"], width="small"),
            "52D": st.column_config.TextColumn(nombres["52D"], width="small"),
        }
        cfg[grupo_clave] = st.column_config.TextColumn(f"🔴 {nombres[grupo_clave]}", width="medium")

        cols = ["Fecha", "Día", grupo_clave] + [c for c in GRUPOS if c != grupo_clave]
        df_mostrar = df[cols]

        st.dataframe(
            df_mostrar.style.applymap(colorear_celdas_web, subset=GRUPOS),
            use_container_width=True,
            hide_index=True,
            column_config=cfg
        )

        # Excel/CSV (usar FechaISO)
        df_excel = preparar_excel_para_descarga(df_mostrar, df)

        excel_diario = exportar_tabla_excel(df_excel)
        csv_diario = exportar_tabla_csv_iphone(df_excel)

        d1, d2 = st.columns(2)
        with d1:
            st.download_button(
                label="📥 Descargar Excel",
                data=excel_diario,
                file_name=f"turnos_{grupo_clave}_{fecha.strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="t0_dl_excel"
            )
        with d2:
            st.download_button(
                label="📄 Descargar CSV iPhone",
                data=csv_diario,
                file_name=f"turnos_{grupo_clave}_{fecha.strftime('%Y%m%d')}.csv",
                mime="text/csv",
                key="t0_dl_csv"
            )

# =======================
# TAB 2: ANUAL (HELADERA)
# =======================
with tabs[1]:
    st.write("### ❄️ Calendario Anual (para imprimir)")
    st.info("Descarga el año completo en formato calendario. Ideal para imprimir.")

    col_anio, col_btn = st.columns([1, 2])
    anio_sel = col_anio.selectbox("Año a imprimir:", range(2025, 2031), key="anio_sel")

    if col_btn.button("Generar Excel para Imprimir", key="btn_excel_anual"):
        excel_data = generar_excel_anual(anio_sel)
        st.success("¡Listo!")
        st.download_button(
            label=f"📥 Descargar Año {anio_sel}",
            data=excel_data,
            file_name=f"Turnos_anual_{anio_sel}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="dl_excel_anual"
        )

# =======================
# TAB 3: QR
# =======================
with tabs[2]:
    st.write("### 📱 QR de la App")
    url = "https://turnos-hdg2-ynyvrw9zsvyrqvet8r746z.streamlit.app/"

    st.link_button("🔗 Abrir la app", url)
    st.code(url, language="text")

    qr = qrcode.make(url)
    buf = BytesIO()
    qr.save(buf, format="PNG")
    qr_bytes = buf.getvalue()

    st.image(qr_bytes, caption="Escaneá y listo.", use_container_width=False)
    st.download_button(
        label="⬇️ Descargar QR",
        data=qr_bytes,
        file_name="qr_turnos.png",
        mime="image/png",
        key="dl_qr"
    )
