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
    st.sidebar.success(f"✅ Librería conectada: {len(archivos_reales)} archivos.")
else:
    st.sidebar.error(f"❌ Error Crítico: No existe la carpeta {ASSETS_DIR}")

# --- 3. FUNCIÓN DE BÚSQUEDA INTELIGENTE ---
def ruta_imagen_segura(nombre_archivo):
    ruta_exacta = os.path.join(ASSETS_DIR, nombre_archivo)
    if os.path.exists(ruta_exacta):
        return ruta_exacta
    # Búsqueda insensible a mayúsculas
    for archivo in os.listdir(ASSETS_DIR):
        if archivo.lower() == nombre_archivo.lower():
            return os.path.join(ASSETS_DIR, archivo)
    return None

# --- 4. MAPEO EXACTO ---
MAPA_FRECUENCIA = {
    "1 vez al día (Mañana)": "67.gif",
    "1 vez al día (Noche)": "13.gif", 
    "2 veces al día (Mañana/Noche)": "4.gif",
    "3 veces al día (Cada 8h)": "31.gif",
    "4 veces al día (Cada 6h)": "19.gif",
    "Con las comidas": "70.gif",
    "Estómago vacío (1h antes)": "5.gif"
}

MAPA_ALERTAS = {
    "Tomar con agua": "57.gif",
    "Agitar bien": "30.gif",
    "No conducir": "51.gif",
    "No alcohol": "36.gif", 
    "No triturar": "48.gif",
    "No embarazada": "32.gif",
    "Peligro / Veneno": "47.gif"
}

# --- 5. MOTOR DE GENERACIÓN PDF ---
def generar_pdf(paciente, medicamento, dosis, frecuencia_key, lista_alertas, es_ciego):
    pdf = FPDF()
    pdf.add_page()
    
    # A. Encabezado
    pdf.set_font("Arial", "B", 24)
    pdf.cell(0, 15, txt=f"{medicamento.upper()}", ln=True, align='C')
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, txt=f"Dosis: {dosis}", ln=True, align='C')
    pdf.line(10, 35, 200, 35)
    
    # B. Sección Posología (Izquierda)
    y_start = 50
    pdf.set_xy(10, y_start)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(90, 10, txt="CÓMO TOMARLO:", ln=True, align='C')
    
    archivo_frec = MAPA_FRECUENCIA.get(frecuencia_key)
    if archivo_frec:
        ruta = ruta_imagen_segura(archivo_frec)
        if ruta:
            pdf.image(ruta, x=35, y=y_start+10, w=40)
        else:
            # Fallback si no encuentra imagen
            pdf.set_xy(10, y_start+20)
            pdf.set_font("Arial", "I", 10)
            pdf.cell(90, 10, txt=f"[Icono {archivo_frec} no encontrado]", align='C')

    # C. Sección Alertas (Derecha - Múltiples)
    pdf.set_xy(105, y_start)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(90, 10, txt="PRECAUCIONES:", ln=True, align='C')
    
    x_icon = 110
    y_icon = y_start + 10
    count = 0
    
    for alerta_key in lista_alertas:
        nombre_archivo = MAPA_ALERTAS.get(alerta_key)
        if nombre_archivo:
            ruta = ruta_imagen_segura(nombre_archivo)
            if ruta:
                # Salto de línea si hay más de 2 iconos
                if count == 2: 
                    x_icon = 110
                    y_icon += 45
                
                pdf.image(ruta, x=x_icon, y=y_icon, w=35)
                x_icon += 40
                count += 1

    # D. Zona Braille
    if es_ciego:
        pdf.set_y(220)
        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 5, txt="----------------- CORTE AQUÍ PARA GUÍA TÁCTIL -----------------", ln=True, align='C')
        pdf.ln(5)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, txt="INSTRUCCIÓN (TÉCNICA ESPEJO):", ln=True, align='C')
        pdf.set_font("Arial", "", 10)
        pdf.multi_cell(0, 5, txt="Voltee la hoja. Use un bolígrafo sin tinta para presionar los puntos negros.", align='C')
        
        pdf.ln(10)
        pdf.set_font("Courier", "B", 30)
        pdf.cell(0, 15, txt=". :  . :  .. :  .", ln=True, align='C')

    # --- CORRECCIÓN CRÍTICA AQUÍ ---
    # Convertimos explícitamente el bytearray a bytes inmutables
    return bytes(pdf.output(dest='S'))

# --- 6. INTERFAZ STREAMLIT ---
col_logo, col_titulo = st.columns([1, 4])
with col_titulo:
    st.subheader("Configuración del Medicamento")

with st.container(border=True):
    c1, c2 = st.columns(2)
    with c1:
        nombre = st.text_input("Paciente", "Maria Gonzales")
        med = st.text_input("Medicamento", "IBUPROFENO")
    with c2:
        dosis = st.text_input("Dosis", "800 mg")
        es_ciego = st.toggle("Activar Modo Ciego (Guía Táctil)")

    st.divider()
    
    c3, c4 = st.columns(2)
    with c3:
        st.markdown("##### 🕒 Frecuencia")
        frec_sel = st.selectbox("Seleccione horario:", list(MAPA_FRECUENCIA.keys()))
        
        if frec_sel:
            archivo = MAPA_FRECUENCIA[frec_sel]
            ruta = ruta_imagen_segura(archivo)
            if ruta:
                st.image(ruta, width=100)
            else:
                st.warning(f"Falta imagen: {archivo}")

    with c4:
        st.markdown("##### ⚠️ Precauciones")
        alertas_sel = st.multiselect("Seleccione todas las que apliquen:", list(MAPA_ALERTAS.keys()))
        
        if alertas_sel:
            cols_prev = st.columns(len(alertas_sel))
            for i, alerta in enumerate(alertas_sel):
                archivo = MAPA_ALERTAS[alerta]
                ruta = ruta_imagen_segura(archivo)
                if ruta:
                    cols_prev[i].image(ruta, width=80, caption=alerta)

    st.write("")
    btn_generar = st.button("GENERAR GUÍA PDF", type="primary", use_container_width=True)

if btn_generar:
    try:
        pdf_bytes = generar_pdf(nombre, med, dosis, frec_sel, alertas_sel, es_ciego)
        
        st.success("✅ ¡Documento generado correctamente!")
        
        st.download_button(
            label="📄 DESCARGAR PDF FINAL",
            data=pdf_bytes,
            file_name=f"Guia_{med}.pdf",
            mime="application/pdf"
        )
            
    except Exception as e:
        st.error(f"Ocurrió un error técnico: {e}")
