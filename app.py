import streamlit as st
from fpdf import FPDF
import os

# --- 1. CONFIGURACIÓN DE RUTAS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, 'assets', 'usp_pictograms')

# --- 2. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="SMEFI Prototipo", page_icon="💊", layout="wide")
st.title("🖨️ Sistema de Dispensación Inclusiva (SMEFI)")
st.markdown("**Prototipo Funcional:** Guías con texto SUPERIOR para máxima legibilidad.")

# Verificación de carpeta
if os.path.exists(ASSETS_DIR):
    archivos_reales = os.listdir(ASSETS_DIR)
    st.sidebar.success(f"✅ Librería USP conectada: {len(archivos_reales)} archivos.")
else:
    st.sidebar.error(f"❌ Error Crítico: No existe la carpeta {ASSETS_DIR}")

# --- 3. FUNCIÓN DE BÚSQUEDA INTELIGENTE ---
def ruta_imagen_segura(nombre_objetivo):
    ruta_exacta = os.path.join(ASSETS_DIR, nombre_objetivo)
    if os.path.exists(ruta_exacta):
        return ruta_exacta
    for archivo_real in os.listdir(ASSETS_DIR):
        if archivo_real.lower() == nombre_objetivo.lower():
            return os.path.join(ASSETS_DIR, archivo_real)
    return None

# --- 4. MAPEO DE DATOS ---
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
    "Vía Vaginal": "25.GIF",
    "Gárgaras": "58.GIF"
}

MAPA_FRECUENCIA = {
    "--- Seleccionar ---": None,
    "Mañana (AM)": "67.gif",
    "Noche / Hora de dormir": "22.GIF",
    "2 veces al día": "04.GIF",
    "2 veces al día (Con comidas)": "03.GIF",
    "3 veces al día": "16.GIF",
    "3 veces al día (Con comidas)": "14.GIF",
    "4 veces al día": "15.GIF",
    "4 veces al día (Con comidas)": "13.GIF",
    "1 hora ANTES de comidas": "05.GIF",
    "1 hora DESPUÉS de comidas": "06.GIF",
    "2 horas ANTES de comidas": "07.GIF",
    "2 horas DESPUÉS de comidas": "08.GIF",
    "Con alimentos": "18.GIF",
    "Estómago vacío": "19.GIF"
}

MAPA_ALERTAS = {
    "No consumir alcohol": "40.GIF",
    "No conducir (Somnolencia)": "50.GIF",
    "No conducir (Mareo)": "72.GIF",
    "No triturar ni romper": "33.GIF",
    "No masticar": "48.GIF",
    "Agitar vigorosamente": "39.GIF",
    "Refrigerar": "20.GIF",
    "No refrigerar": "52.GIF",
    "No congelar": "51.GIF",
    "Proteger de luz solar": "69.GIF",
    "No embarazo": "34.GIF",
    "No lactancia": "36.GIF",
    "No compartir medicamento": "54.GIF",
    "No fumar": "55.GIF",
    "Tomar agua adicional": "57.GIF",
    "Peligro / Venenoso": "81.GIF",
    "Causa somnolencia": "24.GIF",
    "No leche ni lácteos": "23.GIF"
}

# --- 5. MOTOR DE GENERACIÓN PDF (TEXTO ARRIBA) ---
def generar_pdf(paciente, medicamento, dosis, via_key, frecuencia_key, lista_alertas, es_ciego):
    pdf = FPDF()
    pdf.add_page()
    
    # Encabezado
    pdf.set_font("Arial", "B", 24)
    pdf.cell(0, 15, txt=f"{medicamento.upper()}", ln=True, align='C')
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, txt=f"Dosis: {dosis.upper()}", ln=True, align='C')
    pdf.line(10, 35, 200, 35)
    
    # ============================
    # SECCIÓN 1: VÍA Y FRECUENCIA
    # ============================
    y_bloque_1 = 45 
    
    # --- VÍA (Izquierda) ---
    pdf.set_xy(20, y_bloque_1)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(60, 10, txt="VÍA / ACCIÓN", align='C')
    
    archivo_via = MAPA_VIA.get(via_key)
    if archivo_via:
        ruta = ruta_imagen_segura(archivo_via)
        if ruta:
            # 1. TEXTO (Arriba)
            pdf.set_xy(20, y_bloque_1 + 12)
            pdf.set_font("Arial", "B", 10)
            pdf.multi_cell(60, 4, txt=via_key.upper(), align='C')
            
            # 2. IMAGEN (Abajo del texto)
            # Y=65 fijo para asegurar que no choque con la 2da línea de texto
            pdf.image(ruta, x=35, y=y_bloque_1 + 25, w=30)
    
    # --- FRECUENCIA (Derecha) ---
    pdf.set_xy(100, y_bloque_1)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(60, 10, txt="HORARIO", align='C')
    
    archivo_frec = MAPA_FRECUENCIA.get(frecuencia_key)
    if archivo_frec:
        ruta = ruta_imagen_segura(archivo_frec)
        if ruta:
            # 1. TEXTO (Arriba)
            pdf.set_xy(100, y_bloque_1 + 12)
            pdf.set_font("Arial", "B", 10)
            pdf.multi_cell(60, 4, txt=frecuencia_key.upper(), align='C')
            
            # 2. IMAGEN (Abajo)
            pdf.image(ruta, x=115, y=y_bloque_1 + 25, w=30)

    # ============================
    # SECCIÓN 2: ALERTAS (Grid)
    # ============================
    # Empezamos bastante más abajo (Y=110) para dar espacio a los iconos de arriba
    y_alertas = 110 
    
    pdf.set_xy(10, y_alertas)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, txt="PRECAUCIONES:", ln=True, align='L')
    
    x_curr = 20
    y_curr = y_alertas + 15
    count = 0
    
    for alerta_key in lista_alertas:
        nombre_archivo = MAPA_ALERTAS.get(alerta_key)
        if nombre_archivo:
            ruta = ruta_imagen_segura(nombre_archivo)
            if ruta:
                # Salto de línea si hay más de 4 iconos
                if count == 4: 
                    x_curr = 20
                    y_curr += 55 # Espacio vertical entre filas
                    count = 0
                
                # 1. TEXTO (Arriba, centrado en su columna)
                pdf.set_font("Arial", "B", 8)
                pdf.set_xy(x_curr - 5, y_curr) 
                pdf.multi_cell(40, 3, txt=alerta_key.upper(), align='C')
                
                # 2. IMAGEN (Abajo del texto)
                # Calculamos Y dinámico o fijo: y_curr + 10 (aprox 3 líneas de texto)
                pdf.image(ruta, x=x_curr, y=y_curr + 12, w=25)
                
                x_curr += 45
                count += 1

    # D. Zona Braille
    if es_ciego:
        pdf.set_y(240)
        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 5, txt="- - - - - - CORTE AQUÍ PARA GUÍA TÁCTIL - - - - - -", ln=True, align='C')
        pdf.ln(2)
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 5, txt="INSTRUCCIÓN ESPEJO: Punzar por el reverso.", ln=True, align='C')
        
        pdf.ln(5)
        pdf.set_font("Courier", "B", 30)
        pdf.cell(0, 15, txt=". :  . :  .. :  .", ln=True, align='C')

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
    
    c3, c4 = st.columns(2)
    
    with c3:
        st.info("ℹ️ Información de Toma")
        via_sel = st.selectbox("Vía de Administración", list(MAPA_VIA.keys()))
        frec_sel = st.selectbox("Frecuencia / Horario", list(MAPA_FRECUENCIA.keys()))
        
        cols_prev = st.columns(2)
        if via_sel:
            ruta = ruta_imagen_segura(MAPA_VIA[via_sel])
            if ruta: 
                cols_prev[0].caption("VÍA")
                cols_prev[0].image(ruta, width=70)
        if frec_sel:
            archivo = MAPA_FRECUENCIA.get(frec_sel)
            if archivo:
                ruta = ruta_imagen_segura(archivo)
                if ruta: 
                    cols_prev[1].caption("HORARIO")
                    cols_prev[1].image(ruta, width=70)

    with c4:
        st.warning("⚠️ Seguridad del Paciente")
        alertas_sel = st.multiselect("Seleccione Precauciones:", list(MAPA_ALERTAS.keys()))
        
        if alertas_sel:
            cols_alerta = st.columns(4)
            for i, alerta in enumerate(alertas_sel):
                ruta = ruta_imagen_segura(MAPA_ALERTAS[alerta])
                if ruta:
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
