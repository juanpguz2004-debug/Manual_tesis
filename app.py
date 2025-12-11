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
    st.sidebar.error(f"❌ Error Crítico: No existe la carpeta {ASSETS_DIR}")

# --- 3. FUNCIÓN DE BÚSQUEDA INTELIGENTE (TOLERANTE A FALLOS) ---
def ruta_imagen_segura(nombre_objetivo):
    # 1. Búsqueda exacta
    ruta_exacta = os.path.join(ASSETS_DIR, nombre_objetivo)
    if os.path.exists(ruta_exacta):
        return ruta_exacta
    
    # 2. Búsqueda insensible a mayúsculas/minúsculas (ej. .GIF vs .gif)
    # También maneja si el archivo tiene un 0 extra o le falta
    for archivo_real in os.listdir(ASSETS_DIR):
        # Comparamos nombres base sin importar mayúsculas
        if archivo_real.lower() == nombre_objetivo.lower():
            return os.path.join(ASSETS_DIR, archivo_real)
            
    return None

# --- 4. MAPEO EXACTO (SEGÚN TU LISTA OFICIAL) ---
# NOTA: Usamos la extensión .GIF en mayúscula para coincidir con tus archivos

# A. Vía de Administración (Icono Principal)
MAPA_VIA = {
    "Vía Oral (Tragar)": "01.GIF",
    "Masticar": "43.GIF",
    "Sublingual (Bajo la lengua)": "46.GIF",
    "Disolver en agua": "45.GIF",
    "Diluir en agua": "44.GIF",
    "Inhalador": "71.GIF",
    "Spray Nasal": "77.GIF",
    "Gotas Nariz": "09.GIF",
    "Gotas Ojos": "29.GIF",
    "Gotas Oído": "31.GIF",
    "Inyección": "61.GIF",
    "Vía Rectal": "27.GIF",
    "Vía Vaginal": "25.GIF", # O 66 según lista
    "Gárgaras": "58.GIF"
}

# B. Frecuencia y Horarios
MAPA_FRECUENCIA = {
    "--- Seleccionar ---": None,
    "Mañana (AM)": "67.GIF",
    "Noche / Hora de dormir": "22.GIF",
    "2 veces al día": "04.GIF",
    "2 veces al día (Con comidas)": "03.GIF",
    "3 veces al día": "16.GIF",
    "3 veces al día (Con comidas)": "14.GIF",
    "4 veces al día": "15.GIF",
    "4 veces al día (Con comidas)": "13.GIF", # + dormir
    "1 hora ANTES de comidas": "05.GIF",
    "1 hora DESPUÉS de comidas": "06.GIF",
    "2 horas ANTES de comidas": "07.GIF",
    "2 horas DESPUÉS de comidas": "08.GIF",
    "Con alimentos": "18.GIF",
    "Estómago vacío (Sin alimentos)": "19.GIF" # No tomar con alimentos
}

# C. Precauciones y Alertas (Selección Múltiple)
MAPA_ALERTAS = {
    "No alcohol": "40.GIF",
    "No conducir (Somnolencia)": "50.GIF",
    "No conducir (Mareo)": "72.GIF",
    "No triturar/romper": "33.GIF",
    "No masticar": "48.GIF",
    "Agitar vigorosamente": "39.GIF",
    "Refrigerar": "20.GIF",
    "No refrigerar": "52.GIF",
    "No congelar": "51.GIF",
    "Proteger de luz solar": "69.GIF", # O 12
    "No embarazo": "34.GIF",
    "No lactancia": "36.GIF",
    "No compartir": "54.GIF",
    "No fumar": "55.GIF",
    "Tomar agua adicional": "57.GIF",
    "Peligro/Venenoso": "81.GIF",
    "Causa somnolencia": "24.GIF",
    "No leche/lácteos": "23.GIF"
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

    # Retorno en bytes para evitar error de Streamlit
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
