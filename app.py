import streamlit as st
from fpdf import FPDF
import os

# --- 1. CONFIGURACIÓN DE RUTAS ---
# Esto detecta automáticamente dónde está tu carpeta assets/usp_pictograms
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, 'assets', 'usp_pictograms')

# --- 2. CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Generador USP", page_icon="💊")

st.title("🖨️ Generador de Guías Farmacéuticas Inclusivas")
st.markdown("**Prototipo de Tesis:** Herramienta de dispensación para pacientes con barreras de comunicación.")

# Verificación de diagnóstico (Para que sepas si Python encuentra la carpeta)
if os.path.exists(ASSETS_DIR):
    archivos_encontrados = os.listdir(ASSETS_DIR)
    st.sidebar.success(f"✅ Carpeta de iconos encontrada. {len(archivos_encontrados)} imágenes disponibles.")
else:
    st.sidebar.error("❌ NO se encontró la carpeta 'assets/usp_pictograms'. Por favor créala.")

# --- 3. MAPEO DE IMÁGENES (AQUÍ DEBES EDITAR) ---
# Conecta la opción del menú con el NOMBRE EXACTO de tu archivo en la carpeta.
# Si tu archivo se llama 'reloj.gif', pon 'reloj.gif' aquí.

MAPA_FRECUENCIA = {
    "--- Seleccionar ---": None,
    "Mañana (Desayuno)": "morning.gif",  # <--- CAMBIA ESTO POR TU NOMBRE DE ARCHIVO REAL
    "Noche (Cena)": "night.gif",         # <--- CAMBIA ESTO
    "Cada 8 Horas": "8hours.gif",        # <--- CAMBIA ESTO
    "1 vez al día": "once_daily.gif"     # <--- CAMBIA ESTO
}

MAPA_ALERTA = {
    "Ninguna": None,
    "Tomar con comida": "take_with_food.gif", # <--- CAMBIA ESTO
    "No conducir": "no_driving.gif",          # <--- CAMBIA ESTO
    "Agitar antes de usar": "shake.gif"       # <--- CAMBIA ESTO
}

# --- 4. FUNCIÓN GENERADORA DEL PDF ---
def generar_pdf(paciente, medicamento, dosis, frecuencia, alerta, es_ciego):
    pdf = FPDF()
    pdf.add_page()
    
    # Encabezado
    pdf.set_font("Arial", "B", 20)
    pdf.cell(0, 15, txt=f"GUÍA: {medicamento.upper()}", ln=True, align='C')
    
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, txt=f"Paciente: {paciente} | Dosis: {dosis}", ln=True, align='C')
    pdf.ln(10) # Espacio vacío

    # --- INSERCIÓN DE PICTOGRAMAS ---
    # Posición inicial Y (altura)
    y_img = 60 
    
    # 1. Pictograma de Frecuencia
    archivo_frec = MAPA_FRECUENCIA.get(frecuencia)
    if archivo_frec:
        ruta_img = os.path.join(ASSETS_DIR, archivo_frec)
        if os.path.exists(ruta_img):
            # Insertar imagen (x, y, ancho)
            try:
                pdf.image(ruta_img, x=30, y=y_img, w=50)
                pdf.set_xy(30, y_img + 55)
                pdf.set_font("Arial", "B", 12)
                pdf.cell(50, 10, txt="CUÁNDO TOMAR", align='C')
            except Exception as e:
                st.error(f"Error al cargar imagen {archivo_frec}: {e}")
    
    # 2. Pictograma de Alerta
    archivo_alert = MAPA_ALERTA.get(alerta)
    if archivo_alert:
        ruta_img = os.path.join(ASSETS_DIR, archivo_alert)
        if os.path.exists(ruta_img):
            pdf.image(ruta_img, x=130, y=y_img, w=50)
            pdf.set_xy(130, y_img + 55)
            pdf.set_font("Arial", "B", 12)
            pdf.cell(50, 10, txt="PRECAUCIÓN", align='C')

    # --- LÓGICA BRAILLE (Simulación para Tesis) ---
    if es_ciego:
        pdf.set_y(220)
        pdf.set_font("Arial", "I", 10)
        pdf.cell(0, 10, txt="--- CORTE AQUÍ PARA GUÍA TÁCTIL (PUNZADO) ---", ln=True, align='C', border='T')
        
        pdf.set_font("Courier", "B", 24)
        # Simulamos texto Braille (puntos)
        pdf.cell(0, 20, txt=". : . : .. : .", ln=True, align='C')
        pdf.set_font("Arial", "", 8)
        pdf.cell(0, 5, txt="(Instrucción al Farmacéutico: Punzar puntos negros por el reverso)", ln=True, align='C')

    return pdf.output(dest='S').encode('latin-1')

# --- 5. INTERFAZ DE USUARIO ---
with st.container():
    col1, col2 = st.columns(2)
    with col1:
        nombre = st.text_input("Nombre del Paciente")
        med = st.text_input("Medicamento", "Amoxicilina")
    with col2:
        dosis = st.text_input("Dosis", "500 mg")
        check_ciego = st.checkbox("Generar Guía Táctil (Ciegos)")

    st.markdown("### Selección de Pictogramas USP")
    c1, c2 = st.columns(2)
    
    with c1:
        frec_sel = st.selectbox("Frecuencia de toma", list(MAPA_FRECUENCIA.keys()))
        # Previsualización en pantalla
        img_file = MAPA_FRECUENCIA.get(frec_sel)
        if img_file:
            ruta = os.path.join(ASSETS_DIR, img_file)
            if os.path.exists(ruta):
                st.image(ruta, width=100, caption="Previsualización")
            else:
                st.warning(f"⚠️ Archivo no encontrado: {img_file}")

    with c2:
        alerta_sel = st.selectbox("Alertas / Precauciones", list(MAPA_ALERTA.keys()))
        # Previsualización en pantalla
        img_file_a = MAPA_ALERTA.get(alerta_sel)
        if img_file_a:
            ruta = os.path.join(ASSETS_DIR, img_file_a)
            if os.path.exists(ruta):
                st.image(ruta, width=100, caption="Previsualización")
    
    # Botón de Acción
    if st.button("GENERAR GUÍA PDF", type="primary"):
        if frec_sel == "--- Seleccionar ---":
            st.error("Por favor selecciona una frecuencia.")
        else:
            pdf_bytes = generar_pdf(nombre, med, dosis, frec_sel, alerta_sel, check_ciego)
            st.success("¡Guía generada exitosamente!")
            st.download_button(
                label="📥 Descargar PDF Listo para Imprimir",
                data=pdf_bytes,
                file_name=f"Guia_{med}.pdf",
                mime="application/pdf"
            )
