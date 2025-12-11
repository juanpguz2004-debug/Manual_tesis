import streamlit as st
from fpdf import FPDF
import os

# --- 1. CONFIGURACIÓN DE RUTAS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Asegúrate de que tus archivos 1.gif, 2.gif estén dentro de esta carpeta:
ASSETS_DIR = os.path.join(BASE_DIR, 'assets', 'usp_pictograms')

# --- 2. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Generador USP", page_icon="💊")
st.title("🖨️ Generador de Guías Farmacéuticas Inclusivas")
st.markdown("**Sistema de Dispensación Accesible (SMEFI):** Prototipo funcional v1.0")

# Verificación de carpeta
if os.path.exists(ASSETS_DIR):
    total_imgs = len(os.listdir(ASSETS_DIR))
    st.sidebar.success(f"✅ Librería USP conectada: {total_imgs} pictogramas cargados.")
else:
    st.sidebar.error(f"❌ Error: No se encuentra la carpeta {ASSETS_DIR}")

# --- 3. MAPEO EXACTO SEGÚN INDEX.PDF ---
# Clave = Lo que ve el farmacéutico
# Valor = El nombre del archivo en tu carpeta de GitHub (número.gif)

MAPA_FRECUENCIA = {
    "--- Seleccionar ---": None,
    "1 vez al día (Mañana)": "67.gif",      # Index 67: Take in the morning
    "1 vez al día (Noche)": "14.gif",       # Index 14: Take at bedtime
    "2 veces al día (Cada 12h)": "4.gif",   # Index 4: Take 2 times a day
    "3 veces al día (Cada 8h)": "31.gif",   # Index 31: Take 3 times a day
    "4 veces al día (Cada 6h)": "19.gif"    # Index 19: Take 4 times a day
}

MAPA_ALERTA = {
    "Ninguna": None,
    "Tomar con comida": "70.gif",           # Index 70: Take with meals
    "Tomar con agua": "39.gif",             # Index 39: Take with glass of water
    "Agitar antes de usar": "30.gif",       # Index 30: Shake well
    "No conducir": "50.gif",                # Index 50: Do not drive if sleepy
    "No tomar alcohol": "29.gif",           # Index 29: Do not drink alcohol
    "No triturar/masticar": "48.gif"        # Index 48: Do not chew
}

# --- 4. MOTOR DE GENERACIÓN PDF ---
def generar_pdf(paciente, medicamento, dosis, frecuencia, alerta, es_ciego):
    pdf = FPDF()
    pdf.add_page()
    
    # A. Encabezado Accesible (Alto Contraste / Fuente Grande)
    pdf.set_font("Arial", "B", 24)
    pdf.cell(0, 15, txt=f"{medicamento.upper()}", ln=True, align='C')
    pdf.set_font("Arial", "B", 18)
    pdf.cell(0, 10, txt=f"{dosis}", ln=True, align='C')
    
    pdf.line(10, 35, 200, 35) # Línea separadora
    
    # B. Inserción de Pictogramas
    y_img = 50 
    
    # Pictograma 1: Frecuencia
    archivo_frec = MAPA_FRECUENCIA.get(frecuencia)
    if archivo_frec:
        ruta_img = os.path.join(ASSETS_DIR, archivo_frec)
        if os.path.exists(ruta_img):
            try:
                # Insertamos imagen (x=20, y=50, w=60)
                pdf.image(ruta_img, x=20, y=y_img, w=60)
                # Texto explicativo debajo
                pdf.set_xy(20, y_img + 65)
                pdf.set_font("Arial", "B", 14)
                pdf.cell(60, 10, txt="CUÁNDO TOMAR", align='C')
            except Exception as e:
                st.error(f"Error cargando imagen {archivo_frec}: {e}")
    
    # Pictograma 2: Alerta (Si aplica)
    archivo_alert = MAPA_ALERTA.get(alerta)
    if archivo_alert:
        ruta_img = os.path.join(ASSETS_DIR, archivo_alert)
        if os.path.exists(ruta_img):
            try:
                # Insertamos imagen a la derecha (x=120)
                pdf.image(ruta_img, x=120, y=y_img, w=60)
                # Texto explicativo
                pdf.set_xy(120, y_img + 65)
                pdf.set_font("Arial", "B", 14)
                pdf.cell(60, 10, txt="PRECAUCIÓN", align='C')
            except Exception as e:
                st.error(f"Error cargando imagen {archivo_alert}: {e}")

    # C. Zona de Punzado Braille (Espejo)
    if es_ciego:
        pdf.set_y(220)
        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 5, txt="----------------- CORTE AQUÍ PARA ZONA TÁCTIL -----------------", ln=True, align='C')
        pdf.ln(5)
        
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, txt="INSTRUCCIÓN PARA EL FARMACÉUTICO:", ln=True, align='C')
        pdf.set_font("Arial", "", 10)
        pdf.multi_cell(0, 5, txt="1. Voltee esta hoja.\n2. Coloque sobre una superficie blanda (goma/foami).\n3. Presione con un bolígrafo sobre los puntos negros guía.", align='C')
        
        # Simulación visual de los puntos guía
        pdf.ln(10)
        pdf.set_font("Courier", "B", 30) # Courier es monoespaciada, sirve para simular
        pdf.cell(0, 15, txt=". : . : .. : .", ln=True, align='C')
        pdf.cell(0, 15, txt=".. . : . : . .", ln=True, align='C')

    # D. Metadatos de Trazabilidad
    pdf.set_y(-20)
    pdf.set_font("Arial", "I", 8)
    pdf.cell(0, 10, txt=f"Paciente: {paciente} | Generado por Sistema SMEFI | Basado en USP Pictograms", align='C')

    return pdf.output(dest='S').encode('latin-1')

# --- 5. INTERFAZ DE USUARIO (FRONTEND) ---
with st.container():
    col1, col2 = st.columns(2)
    with col1:
        nombre = st.text_input("Nombre del Paciente", "Juan Pérez")
        med = st.text_input("Medicamento", "IBUPROFENO")
    with col2:
        dosis = st.text_input("Dosis", "800 mg")
        check_ciego = st.checkbox("Activar Guía de Punzado (Braille)")

    st.divider()
    
    st.subheader("Configuración de Pictogramas")
    c1, c2 = st.columns(2)
    
    with c1:
        frec_sel = st.selectbox("Frecuencia (Posología)", list(MAPA_FRECUENCIA.keys()))
        # Previsualización
        img_file = MAPA_FRECUENCIA.get(frec_sel)
        if img_file:
            ruta = os.path.join(ASSETS_DIR, img_file)
            if os.path.exists(ruta):
                st.image(ruta, width=120, caption=f"Icono USP #{img_file}")
            else:
                st.warning("⚠️ Imagen no encontrada en assets")

    with c2:
        alerta_sel = st.selectbox("Alertas y Precauciones", list(MAPA_ALERTA.keys()))
        # Previsualización
        img_file_a = MAPA_ALERTA.get(alerta_sel)
        if img_file_a:
            ruta = os.path.join(ASSETS_DIR, img_file_a)
            if os.path.exists(ruta):
                st.image(ruta, width=120, caption=f"Icono USP #{img_file_a}")

    st.divider()

    # Botón Principal
    if st.button("GENERAR GUÍA DE DISPENSACIÓN", type="primary"):
        if frec_sel == "--- Seleccionar ---":
            st.error("⚠️ Debes seleccionar una frecuencia para el paciente.")
        else:
            try:
                pdf_bytes = generar_pdf(nombre, med, dosis, frec_sel, alerta_sel, check_ciego)
                st.success("✅ Guía generada correctamente. Lista para imprimir.")
                
                # Botón de Descarga
                st.download_button(
                    label="📄 Descargar PDF",
                    data=pdf_bytes,
                    file_name=f"Guia_{med}_{nombre}.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"Hubo un error generando el PDF: {e}")
