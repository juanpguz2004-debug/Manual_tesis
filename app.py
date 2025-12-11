import streamlit as st
from fpdf import FPDF
import os

# --- 1. CONFIGURACIÓN DE RUTAS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, 'assets', 'usp_pictograms')

# --- 2. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="SMEFI Prototipo", page_icon="💊", layout="wide")
st.title("🖨️ Sistema de Dispensación Inclusiva (SMEFI)")
st.markdown("**Prototipo Funcional de Tesis:** Generación de guías con Pictogramas USP, Braille y LSC.")

# Verificación de carpeta
if os.path.exists(ASSETS_DIR):
    archivos_reales = os.listdir(ASSETS_DIR)
    st.sidebar.success(f"✅ Librería USP conectada: {len(archivos_reales)} archivos.")
else:
    st.sidebar.error(f"❌ Error: No existe la carpeta {ASSETS_DIR}")

# --- 3. FUNCIÓN DE BÚSQUEDA INTELIGENTE ---
def ruta_imagen_segura(nombre_archivo):
    # Busca exacto (ej: '1.gif')
    ruta_exacta = os.path.join(ASSETS_DIR, nombre_archivo)
    if os.path.exists(ruta_exacta):
        return ruta_exacta
    
    # Busca con ceros a la izquierda (ej: si pides '1.gif' pero existe '01.gif')
    if len(nombre_archivo.split('.')[0]) == 1:
        nombre_cero = "0" + nombre_archivo
        ruta_cero = os.path.join(ASSETS_DIR, nombre_cero)
        if os.path.exists(ruta_cero):
            return ruta_cero

    return None

# --- 4. BASES DE DATOS DE PICTOGRAMAS (MAPEO COMPLETO) ---

# A. Vía de Administración (Icono Principal)
MAPA_VIA = {
    "Vía Oral (Tragar)": "1.gif",
    "Masticar": "43.gif",
    "Sublingual (Bajo la lengua)": "46.gif",
    "Disolver en agua": "45.gif",
    "Inhalador": "71.gif",
    "Spray Nasal": "77.gif",
    "Gotas Nariz": "9.gif",
    "Gotas Ojos": "29.gif",
    "Gotas Oído": "31.gif",
    "Inyección": "61.gif",
    "Vía Rectal": "27.gif",
    "Vía Vaginal": "25.gif",
    "Gárgaras": "58.gif"
}

# B. Frecuencia y Horarios
MAPA_FRECUENCIA = {
    "--- Seleccionar ---": None,
    "Mañana (AM)": "67.gif",
    "Noche / Hora de dormir": "22.gif",
    "2 veces al día": "4.gif",
    "2 veces al día (Con comidas)": "3.gif",
    "3 veces al día": "16.gif",
    "3 veces al día (Con comidas)": "14.gif",
    "4 veces al día": "15.gif",
    "1 hora ANTES de comidas": "5.gif",
    "1 hora DESPUÉS de comidas": "6.gif",
    "2 horas ANTES de comidas": "7.gif",
    "Con alimentos": "18.gif",
    "Estómago vacío (Sin alimentos)": "19.gif"
}

# C. Precauciones y Alertas (Selección Múltiple)
MAPA_ALERTAS = {
    "No alcohol": "40.gif",
    "No conducir (Somnolencia)": "50.gif",
    "No conducir (Mareo)": "72.gif",
    "No triturar/romper": "33.gif",
    "No masticar": "48.gif",
    "Agitar vigorosamente": "39.gif",
    "Refrigerar": "20.gif",
    "No refrigerar": "52.gif",
    "No congelar": "51.gif",
    "Proteger de luz solar": "69.gif",
    "No embarazo": "34.gif",
    "No lactancia": "36.gif",
    "No compartir": "54.gif",
    "No fumar": "55.gif",
    "Tomar agua adicional": "57.gif",
    "Peligro/Venenoso": "81.gif"
}

# --- 5. MOTOR DE GENERACIÓN PDF ---
def generar_pdf(paciente, medicamento, dosis, via_key, frecuencia_key, lista_alertas, es_ciego):
    pdf = FPDF()
    pdf.add_page()
    
    # A. Encabezado
    pdf.set_font("Arial", "B", 24)
    pdf.cell(0, 15, txt=f"{medicamento.upper()}", ln=True, align='C')
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, txt=f"Dosis: {dosis}", ln=True, align='C')
    pdf.line(10, 35, 200, 35)
    
    # B. Sección Principal (Vía + Frecuencia)
    y_start = 50
    
    # --- Columna Izquierda: VÍA ---
    pdf.set_xy(20, y_start)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(50, 10, txt="VÍA / ACCIÓN", align='C')
    
    archivo_via = MAPA_VIA.get(via_key)
    if archivo_via:
        ruta = ruta_imagen_segura(archivo_via)
        if ruta:
            pdf.image(ruta, x=30, y=y_start+10, w=30)
    
    # --- Columna Centro: FRECUENCIA ---
    pdf.set_xy(80, y_start)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(50, 10, txt="HORARIO", align='C')
    
    archivo_frec = MAPA_FRECUENCIA.get(frecuencia_key)
    if archivo_frec:
        ruta = ruta_imagen_segura(archivo_frec)
        if ruta:
            pdf.image(ruta, x=90, y=y_start+10, w=30)

    # --- Sección Inferior: ALERTAS (Grid dinámico) ---
    y_alertas = y_start + 60
    pdf.set_xy(10, y_alertas)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, txt="PRECAUCIONES IMPORTANTES:", ln=True, align='L')
    
    x_icon = 20
    y_icon = y_alertas + 15
    count = 0
    
    for alerta_key in lista_alertas:
        nombre_archivo = MAPA_ALERTAS.get(alerta_key)
        if nombre_archivo:
            ruta = ruta_imagen_segura(nombre_archivo)
            if ruta:
                # Si llegamos a 4 iconos, bajamos de línea
                if count == 4: 
                    x_icon = 20
                    y_icon += 40
                    count = 0
                
                pdf.image(ruta, x=x_icon, y=y_icon, w=30)
                
                # Etiqueta pequeña debajo del icono
                pdf.set_font("Arial", "", 7)
                pdf.set_xy(x_icon-5, y_icon+30)
                pdf.multi_cell(40, 3, txt=alerta_key, align='C')
                
                x_icon += 45
                count += 1

    # D. Zona Braille (Espejo)
    if es_ciego:
        pdf.set_y(240)
        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 5, txt="- - - - - - - - CORTE AQUÍ PARA GUÍA TÁCTIL - - - - - - - -", ln=True, align='C')
        pdf.ln(2)
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 5, txt="INSTRUCCIÓN (TÉCNICA ESPEJO): Punzar por el reverso en los puntos.", ln=True, align='C')
        
        pdf.ln(5)
        pdf.set_font("Courier", "B", 30)
        pdf.cell(0, 15, txt=". :  . :  .. :  .", ln=True, align='C')

    # Retorno en bytes (Corrección crítica)
    return bytes(pdf.output(dest='S'))

# --- 6. INTERFAZ STREAMLIT ---
col_logo, col_titulo = st.columns([1, 4])
with col_titulo:
    st.subheader("Configuración del Tratamiento")

with st.container(border=True):
    c1, c2 = st.columns(2)
    with c1:
        nombre = st.text_input("Paciente", "Maria Gonzales")
        med = st.text_input("Medicamento", "AMOXICILINA")
    with c2:
        dosis = st.text_input("Dosis", "500 mg")
        es_ciego = st.toggle("Generar Guía Braille")

    st.divider()
    
    # Nuevas Columnas para mejor organización
    c3, c4 = st.columns(2)
    
    with c3:
        st.info("ℹ️ Información de Toma")
        via_sel = st.selectbox("Vía de Administración", list(MAPA_VIA.keys()))
        frec_sel = st.selectbox("Frecuencia / Horario", list(MAPA_FRECUENCIA.keys()))
        
        # Previsualización Pequeña
        cols_prev = st.columns(2)
        if via_sel:
            ruta = ruta_imagen_segura(MAPA_VIA[via_sel])
            if ruta: cols_prev[0].image(ruta, width=70, caption="Vía")
        if frec_sel:
            archivo = MAPA_FRECUENCIA.get(frec_sel)
            if archivo:
                ruta = ruta_imagen_segura(archivo)
                if ruta: cols_prev[1].image(ruta, width=70, caption="Frecuencia")

    with c4:
        st.warning("⚠️ Seguridad del Paciente")
        alertas_sel = st.multiselect("Seleccione Precauciones:", list(MAPA_ALERTAS.keys()))
        
        # Previsualización en Grid
        if alertas_sel:
            cols_alerta = st.columns(4)
            for i, alerta in enumerate(alertas_sel):
                ruta = ruta_imagen_segura(MAPA_ALERTAS[alerta])
                if ruta:
                    # Usamos módulo para distribuir en columnas
                    cols_alerta[i % 4].image(ruta, width=50)

    st.write("")
    btn_generar = st.button("GENERAR GUÍA PDF", type="primary", use_container_width=True)

if btn_generar:
    try:
        pdf_bytes = generar_pdf(nombre, med, dosis, via_sel, frec_sel, alertas_sel, es_ciego)
        st.success("✅ ¡Guía generada correctamente!")
        st.download_button(
            label="📄 DESCARGAR PDF FINAL",
            data=pdf_bytes,
            file_name=f"Guia_{med}.pdf",
            mime="application/pdf"
        )
    except Exception as e:
        st.error(f"Error técnico: {e}")
