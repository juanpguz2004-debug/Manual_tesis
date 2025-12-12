import streamlit as st
from fpdf import FPDF
import os
import unicodedata

# --- 1. CONFIGURACIÓN DE RUTAS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, 'assets', 'usp_pictograms')

# --- 2. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="SMEFI Prototipo", page_icon="💊", layout="wide")
st.title("🖨️ Sistema de Dispensación Inclusiva (SMEFI)")
st.markdown("**Prototipo Funcional:** Generación de guías con Braille Completo (Espejo) y Pictogramas.")

# Verificación de carpeta
if os.path.exists(ASSETS_DIR):
    archivos_reales = os.listdir(ASSETS_DIR)
    st.sidebar.success(f"✅ Librería USP conectada: {len(archivos_reales)} archivos.")
else:
    st.sidebar.error(f"❌ Error Crítico: No existe la carpeta {ASSETS_DIR}")

# --- 3. DICCIONARIO BRAILLE (ESTÁNDAR 6 PUNTOS) ---
BRAILLE_CHARS = {
    'A': [1], 'B': [1,2], 'C': [1,4], 'D': [1,4,5], 'E': [1,5],
    'F': [1,2,4], 'G': [1,2,4,5], 'H': [1,2,5], 'I': [2,4], 'J': [2,4,5],
    'K': [1,3], 'L': [1,2,3], 'M': [1,3,4], 'N': [1,3,4,5], 'O': [1,3,5],
    'P': [1,2,3,4], 'Q': [1,2,3,4,5], 'R': [1,2,3,5], 'S': [2,3,4], 'T': [2,3,4,5],
    'U': [1,3,6], 'V': [1,2,3,6], 'W': [2,4,5,6], 'X': [1,3,4,6], 'Y': [1,3,4,5,6], 'Z': [1,3,5,6],
    '1': [1], '2': [1,2], '3': [1,4], '4': [1,4,5], '5': [1,5],
    '6': [1,2,4], '7': [1,2,4,5], '8': [1,2,5], '9': [2,4], '0': [2,4,5],
    ' ': [], '.': [2,5,6], ',': [2], ':': [2,5], ';': [2,3],
    '(': [2,3,5,6], ')': [2,3,5,6], '/': [3,4], '-': [3,6]
}

# --- 4. FUNCIÓN DIBUJAR BRAILLE ESPEJO (ROBUSTA) ---
def dibujar_texto_braille(pdf, texto, x_start, y_start, scale=1.5):
    """
    Dibuja los puntos Braille en el PDF invirtiendo columnas para efecto espejo.
    Maneja saltos de línea automáticos si el texto es largo.
    """
    # Limpiar texto
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn').upper()
    
    current_x = x_start
    current_y = y_start
    
    # Configuración de la rejilla Braille (mm)
    dot_radius = 0.6 * scale
    col_spacing = 2.5 * scale  # Espacio entre columna izq y der de una celda
    line_spacing = 2.5 * scale # Espacio entre filas de puntos
    char_spacing = 6.5 * scale # Espacio entre letras
    
    # Mapeo de Espejo (Mirroring): Para punzar por detrás
    # 1(Izq) -> 4(Der), 2 -> 5, 3 -> 6
    mirror_map = {1:4, 2:5, 3:6, 4:1, 5:2, 6:3}

    for char in texto:
        # Control de margen derecho (Salto de línea automático)
        if current_x > 190:  # Margen derecho aprox
            current_x = x_start
            current_y += 12  # Salto de renglón Braille (más alto para legibilidad)
            
        puntos = BRAILLE_CHARS.get(char, [])
        puntos_espejo = [mirror_map[p] for p in puntos]
        
        # Fondo gris suave (guía visual)
        pdf.set_fill_color(245, 245, 245)
        positions = {
            1: (current_x, current_y),
            2: (current_x, current_y + line_spacing),
            3: (current_x, current_y + line_spacing * 2),
            4: (current_x + col_spacing, current_y),
            5: (current_x + col_spacing, current_y + line_spacing),
            6: (current_x + col_spacing, current_y + line_spacing * 2),
        }
        
        # Dibujar puntos activos (Negro)
        pdf.set_fill_color(0, 0, 0)
        for p_num in puntos_espejo:
            pos = positions[p_num]
            pdf.circle(pos[0], pos[1], dot_radius, 'F')
            
        current_x += char_spacing

# --- 5. FUNCIONES AUXILIARES ---
def ruta_imagen_segura(nombre_objetivo):
    ruta_exacta = os.path.join(ASSETS_DIR, nombre_objetivo)
    if os.path.exists(ruta_exacta): return ruta_exacta
    for archivo_real in os.listdir(ASSETS_DIR):
        if archivo_real.lower() == nombre_objetivo.lower():
            return os.path.join(ASSETS_DIR, archivo_real)
    return None

# Mapeos Completos
MAPA_VIA = {
    "Vía Oral (Tragar)": "01.GIF", "Masticar": "43.GIF", "Sublingual (Bajo la lengua)": "46.GIF",
    "Disolver en agua": "45.GIF", "Diluir en agua": "44.GIF", "Inhalador": "71.GIF",
    "Spray Nasal": "77.GIF", "Gotas Nariz": "09.GIF", "Gotas Ojos": "29.GIF",
    "Gotas Oído": "31.GIF", "Inyección": "61.GIF", "Vía Rectal": "27.GIF",
    "Vía Vaginal": "25.GIF", "Gárgaras": "58.GIF"
}
MAPA_FRECUENCIA = {
    "--- Seleccionar ---": None, "Mañana (AM)": "67.GIF", "Noche / Hora de dormir": "22.GIF",
    "2 veces al día": "04.GIF", "2 veces al día (Con comidas)": "03.GIF", 
    "3 veces al día": "16.GIF", "3 veces al día (Con comidas)": "14.GIF",
    "4 veces al día": "15.GIF", "4 veces al día (Con comidas)": "13.GIF",
    "1 hora ANTES de comidas": "05.GIF", "1 hora DESPUÉS de comidas": "06.GIF", 
    "2 horas ANTES de comidas": "07.GIF", "2 horas DESPUÉS de comidas": "08.GIF", 
    "Con alimentos": "18.GIF", "Estómago vacío": "19.GIF"
}
MAPA_ALERTAS = {
    "No alcohol": "40.GIF", "No conducir (Somnolencia)": "50.GIF", "No conducir (Mareo)": "72.GIF",
    "No triturar": "33.GIF", "No masticar": "48.GIF", "Agitar vigorosamente": "39.GIF",
    "Refrigerar": "20.GIF", "No refrigerar": "52.GIF", "No congelar": "51.GIF",
    "Proteger de luz solar": "69.GIF", "No embarazo": "34.GIF", "No lactancia": "36.GIF",
    "No compartir": "54.GIF", "No fumar": "55.GIF", "Tomar agua adicional": "57.GIF",
    "Peligro / Venenoso": "81.GIF", "Causa somnolencia": "24.GIF", "No leche ni lácteos": "23.GIF"
}

# --- 6. MOTOR DE GENERACIÓN PDF ---
def generar_pdf(paciente, medicamento, dosis, via_key, frecuencia_key, lista_alertas, es_ciego):
    pdf = FPDF()
    pdf.add_page()
    
    # ENCABEZADO
    pdf.set_font("Arial", "B", 24)
    pdf.cell(0, 15, txt=f"{medicamento.upper()}", ln=True, align='C')
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, txt=f"PACIENTE: {paciente.upper()}", ln=True, align='C')
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, txt=f"DOSIS: {dosis.upper()}", ln=True, align='C')
    pdf.line(10, 42, 200, 42)
    
    # BLOQUE 1: PICTOGRAMAS (TEXTO ARRIBA)
    y_bloque_1 = 50 
    
    # Vía
    pdf.set_xy(20, y_bloque_1)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(60, 10, txt="VÍA / ACCIÓN", align='C')
    archivo_via = MAPA_VIA.get(via_key)
    if archivo_via:
        ruta = ruta_imagen_segura(archivo_via)
        if ruta:
            # Texto
            pdf.set_xy(20, y_bloque_1 + 12)
            pdf.set_font("Arial", "B", 10)
            pdf.multi_cell(60, 4, txt=via_key.upper(), align='C')
            # Imagen
            pdf.image(ruta, x=35, y=y_bloque_1 + 25, w=30)
    
    # Frecuencia
    pdf.set_xy(100, y_bloque_1)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(60, 10, txt="HORARIO", align='C')
    archivo_frec = MAPA_FRECUENCIA.get(frecuencia_key)
    if archivo_frec:
        ruta = ruta_imagen_segura(archivo_frec)
        if ruta:
            # Texto
            pdf.set_xy(100, y_bloque_1 + 12)
            pdf.set_font("Arial", "B", 10)
            pdf.multi_cell(60, 4, txt=frecuencia_key.upper(), align='C')
            # Imagen
            pdf.image(ruta, x=115, y=y_bloque_1 + 25, w=30)

    # BLOQUE 2: ALERTAS (TEXTO ARRIBA)
    y_alertas = 115 
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
                if count == 4: 
                    x_curr = 20
                    y_curr += 55
                    count = 0
                
                # Texto
                pdf.set_font("Arial", "B", 8)
                pdf.set_xy(x_curr - 5, y_curr) 
                pdf.multi_cell(40, 3, txt=alerta_key.upper(), align='C')
                
                # Imagen
                pdf.image(ruta, x=x_curr, y=y_curr + 12, w=25)
                
                x_curr += 45
                count += 1

    # === ZONA BRAILLE GENERADA AUTOMÁTICAMENTE (TOUCH MAP) ===
    if es_ciego:
        # Línea de corte
        pdf.set_y(210)
        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 5, txt="_" * 60, ln=True, align='C')
        pdf.cell(0, 5, txt="ZONA DE PUNZADO BRAILLE (ESPEJO - PUNZAR POR EL REVERSO)", ln=True, align='C')
        
        # 1. CONSTRUCCIÓN DE LA CADENA COMPLETA DE TEXTO
        # Se traduce TODO lo relevante para el paciente
        alertas_str = ", ".join(lista_alertas) if lista_alertas else "NINGUNA"
        texto_completo_paciente = (
            f"PAC:{paciente}. MED:{medicamento} {dosis}. "
            f"VIA:{via_key}. TOMA:{frecuencia_key}. "
            f"PRE:{alertas_str}."
        )
        
        # 2. Dibujar los puntos (Motor Braille Multilínea)
        braille_start_y = 225 
        braille_start_x = 10 
        
        # Llamamos a la función que convierte todo el texto a puntos
        dibujar_texto_braille(pdf, texto_completo_paciente, braille_start_x, braille_start_y)
        
        # Instrucción final
        pdf.set_y(-15)
        pdf.set_font("Arial", "I", 8)
        pdf.cell(0, 10, txt="SMEFI: Use un punzón sobre los puntos negros para generar relieve legible.", align='C')

    return bytes(pdf.output(dest='S'))

# --- 7. INTERFAZ ---
col_logo, col_titulo = st.columns([1, 4])
with col_titulo: st.subheader("Configuración del Tratamiento")

with st.container(border=True):
    c1, c2 = st.columns(2)
    with c1:
        nombre = st.text_input("Paciente", "Maria Gonzales")
        med = st.text_input("Medicamento", "AMOXICILINA")
    with c2:
        dosis = st.text_input("Dosis", "500 mg")
        es_ciego = st.toggle("Generar Guía Braille Completa")

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
        st.warning("⚠️ Seguridad")
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
        st.download_button("📄 DESCARGAR PDF FINAL", pdf_bytes, file_name=f"Guia_{med}.pdf", mime="application/pdf")
    except Exception as e:
        st.error(f"Error técnico: {e}")
