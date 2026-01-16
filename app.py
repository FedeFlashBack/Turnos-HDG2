import streamlit as st
import pandas as pd
from datetime import date, timedelta
import qrcode
from io import BytesIO
import calendar

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Turno-HDG2", page_icon="🏭", layout="centered")

# --- ESTILOS VISUALES ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 10px; background-color: #FF4B4B; color: white; font-weight: bold; }
    div[data-testid="stMetricValue"] { font-size: 1rem; }
    h1, h2, h3 { text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- DATOS ---
nombres = { 
    "52A": "52A (Palacios)", 
    "52B": "52B (Schneider)", 
    "52C": "52C (Troncoso)", 
    "52D": "52D (Gallardo)" 
}
# Días cortos para el Excel (L, M, M, J, V, S, D)
dias_esp_corto = ["L", "M", "M", "J", "V", "S", "D"]
dias_esp = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
meses_esp = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

# --- FERIADOS HASTA 2030 (Estimados + Fijos) ---
feriados = []
for anio in range(2025, 2031):
    feriados.extend([
        date(anio, 1, 1), date(anio, 3, 24), date(anio, 4, 2), date(anio, 5, 1),
        date(anio, 5, 25), date(anio, 6, 20), date(anio, 7, 9), date(anio, 8, 17),
        date(anio, 10, 12), date(anio, 11, 20), date(anio, 12, 8), date(anio, 12, 25)
    ])
# Feriados móviles específicos conocidos
feriados.extend([
    date(2025, 3, 3), date(2025, 3, 4), date(2025, 4, 18),
    date(2026, 2, 16), date(2026, 2, 17), date(2026, 4, 3),
])

# --- PATRÓN DE TURNOS ---
patron_detalle = [
    "M1","M2","M3","M4","M5","M6", "F1", 
    "N1","N2","N3","N4","N5","N6", "F1","F2","F3", 
    "T1","T2","T3","T4","T5","T6", "F1","F2"
]

# --- FUNCIONES DE CÁLCULO ---
def calcular_estado_dia(fecha):
    offsets = {"52A": 14, "52B": 20, "52C": 2, "52D": 8}
    fecha_base = date(2025, 1, 1)
    diff = (fecha - fecha_base).days
    estado = {}
    es_feriado = fecha in feriados
    marca = " 🇦🇷" if es_feriado else ""
    for grupo in ["52A", "52B", "52C", "52D"]:
        codigo = patron_detalle[(offsets[grupo] + diff) % 24]
        estado[grupo] = {"texto": codigo, "feriado": es_feriado, "marca": marca}
    return estado

def obtener_tabla_diaria(fecha_inicio, dias_a_mostrar):
    datos = []
    for i in range(dias_a_mostrar):
        fecha_actual = fecha_inicio + timedelta(days=i)
        estado = calcular_estado_dia(fecha_actual)
        fila = {
            "Fecha": fecha_actual.strftime("%d/%m"),
            "Día": dias_esp[fecha_actual.weekday()],
            "52A": estado["52A"]["texto"] + estado["52A"]["marca"],
            "52B": estado["52B"]["texto"] + estado["52B"]["marca"],
            "52C": estado["52C"]["texto"] + estado["52C"]["marca"],
            "52D": estado["52D"]["texto"] + estado["52D"]["marca"],
        }
        datos.append(fila)
    return pd.DataFrame(datos)

def colorear_celdas_web(val):
    val_str = str(val)
    color = ''
    weight = 'normal'
    if '🇦🇷' in val_str: color = '#ffb3b3'; weight = 'bold'
    elif 'M' in val_str: color = '#fffec8'
    elif 'T' in val_str: color = '#ffdcf5'
    elif 'N' in val_str: color = '#d0e0ff'
    elif 'F' in val_str: color = '#d9f2d0'
    return f'background-color: {color}; color: black; font-weight: {weight}'

# --- FUNCIÓN GENERADOR DE EXCEL PARA IMPRIMIR (HELADERA) 🎨 ---
def generar_excel_anual(anio):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook = writer.book
        ws = workbook.add_worksheet(f'Turnos {anio}')

        # CONFIGURACIÓN DE IMPRESIÓN
        ws.set_landscape() # Hoja Horizontal
        ws.set_paper(9)    # Tamaño A4
        ws.fit_to_pages(1, 0) # Ajustar ancho a 1 página
        ws.set_margins(0.5, 0.5, 0.5, 0.5)

        # FORMATOS
        # Título del Mes (Gris claro)
        fmt_titulo = workbook.add_format({'bold': True, 'font_size': 14, 'bg_color': '#DDDDDD', 'border': 1, 'align': 'left'})
        
        # Fila de Letras (D, L, M...) -> AMARILLO/DORADO (Como en la foto)
        fmt_dias_letras = workbook.add_format({'bold': True, 'align': 'center', 'bg_color': '#FFEB9C', 'border': 1, 'font_size': 9})
        
        # Fila de Números (1, 2, 3...) -> BLANCO/GRIS
        fmt_dias_numeros = workbook.add_format({'bold': True, 'align': 'center', 'bg_color': '#F2F2F2', 'border': 1, 'font_size': 9})
        
        # Nombre del Grupo (Lateral)
        fmt_grupo = workbook.add_format({'bold': True, 'border': 1, 'font_size': 10, 'align': 'left'})
        
        # Colores de Turnos (Celdas de datos)
        fmt_m = workbook.add_format({'bg_color': '#FFFEC8', 'align': 'center', 'border': 1, 'font_size': 9})
        fmt_t = workbook.add_format({'bg_color': '#FFDCF5', 'align': 'center', 'border': 1, 'font_size': 9})
        fmt_n = workbook.add_format({'bg_color': '#D0E0FF', 'align': 'center', 'border': 1, 'font_size': 9})
        fmt_f = workbook.add_format({'bg_color': '#D9F2D0', 'align': 'center', 'border': 1, 'font_size': 9, 'color': '#555555'}) # Letra gris suave
        fmt_fer = workbook.add_format({'bg_color': '#FFB3B3', 'align': 'center', 'border': 1, 'bold': True, 'font_size': 9})

        # Anchos de columna
        ws.set_column(0, 0, 18) # Columna Nombres un poco más ancha
        ws.set_column(1, 31, 2.8) # Columnas Días (más finitas para que entren bien)

        fila = 0
        grupos = ["52A", "52B", "52C", "52D"]

        for mes in range(1, 13):
            # 1. TÍTULO MES
            ws.merge_range(fila, 0, fila, 31, f"{meses_esp[mes]} {anio}", fmt_titulo)
            fila += 1
            
            # 2. FILA DE LETRAS (D, L, M...) - En un cuadrado separado
            dias_en_mes = calendar.monthrange(anio, mes)[1]
            ws.write(fila, 0, "DÍA", fmt_dias_letras)
            for d in range(1, dias_en_mes + 1):
                dia_semana = dias_esp_corto[date(anio, mes, d).weekday()]
                ws.write(fila, d, dia_semana, fmt_dias_letras)
            fila += 1

            # 3. FILA DE NÚMEROS (1, 2, 3...) - En otro cuadrado separado
            ws.write(fila, 0, "FECHA", fmt_dias_numeros)
            for d in range(1, dias_en_mes + 1):
                ws.write(fila, d, d, fmt_dias_numeros)
            fila += 1

            # 4. FILAS DE DATOS (Los Turnos)
            for gr in grupos:
                ws.write(fila, 0, nombres[gr], fmt_grupo)
                for d in range(1, dias_en_mes + 1):
                    fecha = date(anio, mes, d)
                    info = calcular_estado_dia(fecha)
                    letra = info[gr]["texto"][0] # Solo la letra M, T, N, F
                    es_fer = info[gr]["feriado"]
                    
                    estilo = fmt_f # Por defecto Franco
                    if es_fer: estilo = fmt_fer
                    elif letra == 'M': estilo = fmt_m
                    elif letra == 'T': estilo = fmt_t
                    elif letra == 'N': estilo = fmt_n
                    
                    ws.write(fila, d, letra, estilo)
                fila += 1
            
            fila += 1 # Espacio en blanco entre meses

    return output.getvalue()

# ================= INTERFAZ DE USUARIO =================

st.title("🏭 Turno-HDG2")

# --- 1. TABLERO HOY ---
st.markdown("### 📢 Estado de Planta (Hoy)")
hoy = date.today()
estado_hoy = calcular_estado_dia(hoy)
# Buscamos quién está en cada turno
q_m = [k for k,v in estado_hoy.items() if "M" in v["texto"]][0]
q_t = [k for k,v in estado_hoy.items() if "T" in v["texto"]][0]
q_n = [k for k,v in estado_hoy.items() if "N" in v["texto"]][0]
q_f = [k for k,v in estado_hoy.items() if "F" in v["texto"]][0]

c1, c2, c3, c4 = st.columns(4)
c1.metric("☀️ Mañana", q_m, estado_hoy[q_m]["texto"])
c2.metric("🌆 Tarde", q_t, estado_hoy[q_t]["texto"])
c3.metric("🌙 Noche", q_n, estado_hoy[q_n]["texto"])
c4.metric("🏖️ Franco", q_f, estado_hoy[q_f]["texto"])

st.divider()

# --- 2. BUSCADOR RÁPIDO ---
st.write("### 📅 Calendario Diario")
grupo_clave = st.selectbox("Ver cronograma de:", ["52A", "52B", "52C", "52D"], format_func=lambda x: nombres[x])
c1, c2 = st.columns(2)
fecha = c1.date_input("Desde:", date.today())
dias = c2.slider("Días:", 1, 45, 14)

if st.button("Ver Tabla"):
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
    cols = ["Fecha", "Día", grupo_clave] + [c for c in ["52A", "52B", "52C", "52D"] if c != grupo_clave]
    st.dataframe(df[cols].style.applymap(colorear_celdas_web, subset=["52A", "52B", "52C", "52D"]), 
                 use_container_width=True, hide_index=True, column_config=cfg)

st.divider()

# --- 3. DESCARGA PARA LA HELADERA (ACTUALIZADO) ---
st.write("### ❄️ Calendario Anual ")
st.info("Descarga el año completo en formato calendario. Ideal para imprimir.")

col_anio, col_btn = st.columns([1, 2])
anio_sel = col_anio.selectbox("Año a imprimir:", range(2025, 2031))

if col_btn.button("Generar Excel para Imprimir"):
    with st.spinner("Preparando hoja A4..."):
        excel_data = generar_excel_anual(anio_sel)
        st.success("¡Listo!")
        st.download_button(
            label=f"📥 Descargar Año {anio_sel}",
            data=excel_data,
            file_name=f"Turnos_anual_{anio_sel}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# --- 4. QR ---
st.divider()
with st.expander("📱 Descargar QR"):
    # TU LINK
    url = "https://turnos-hdg2-ynyvrw9zsvyrqvet8r746z.streamlit.app/" 
    qr = qrcode.make(url)
    buf = BytesIO()
    qr.save(buf, format="PNG")
    st.download_button("⬇️ Descargar QR", buf.getvalue(), "qr_turnos.png", "image/png")
