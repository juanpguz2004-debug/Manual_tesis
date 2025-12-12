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
st.markdown("**Versión Final:** Braille Multipágina (Paginación Automática) + Pictogramas USP.")

if os.path.exists(ASSETS_DIR):
    archivos_reales = os.listdir(ASSETS_DIR)
    st.sidebar.success(f"✅ Librería USP conectada: {len(archivos_reales)} archivos.")
else:
    st.sidebar.error(f"❌ Error Crítico: No existe la carpeta {ASSETS_DIR}")

# --- 3. DICCIONARIO BRAILLE ---
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

# --- 4. MOTOR BRAILLE CON PAGINACIÓN ---
def dibujar_braille_paginado(pdf, texto_completo, x_inicial, y_inicial):
    """
    Dibuja Braille espejado. Si se acaba la hoja, crea una nueva automáticamente.
    """
    # Limpieza de texto
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto_completo) if unicodedata.category(c) != 'Mn').upper()
    
    current_x = x_inicial
    current_y = y_inicial
    
    # Configuración de tamaño (OPTIMIZADO PARA ESPACIO)
    scale = 1.0           # Escala 1.0 es el estándar legible mínimo
    dot_radius = 0.5 * scale
    w_dot = 2.3 * scale   # Distancia horizontal entre puntos
    h_dot = 2.3 * scale   # Distancia vertical entre puntos
    w_char = 6.0 * scale  # Ancho de celda
    h_line = 10.0 * scale # Altura de renglón
    
    margin_right = 190    # Margen derecho (mm)
    margin_bottom = 260   # Margen inferior (mm) - Deja espacio para pie de página
    margin_top_new_page = 40 # Donde empezar en la nueva hoja

    # Mapeo Espejo (1<->4, 2<->5, 3<->6)
    mirror_map = {1:4, 2:5, 3:6, 4:1, 5:2, 6:3}

    for char in texto:
        # 1. ¿Cabe en la línea actual?
        if current_x + w_char > margin_right:
            current_x = x_inicial     # Reset X
            current_y += h_line       # Bajar Y (Nuevo renglón)
            
        # 2. ¿Cabe en la página actual?
        if current_y + h_line > margin_bottom:
            pdf.add_page()            # NUEVA PÁGINA
            
            # Re-imprimir encabezado de guía en la nueva hoja
            pdf.set_font("Arial", "I", 10)
            pdf.cell(0, 10, txt="...continuación Guía Táctil (Braille Espejo)...", ln=True, align='C')
            
            current_x = x_inicial     # Reset X
            current_y = margin_top_new_page # Reset Y arriba
            
        puntos = BRAILLE_CHARS.get(char, [])
        puntos_espejo = [mirror_map[p] for p in puntos]
        
        # Dibujar Guía Gris (Celda vacía)
        pdf.set_fill_color(245, 245, 245)
        positions = {
            1: (current_x, current_y),
            2: (current_x, current_y + h_dot),
            3: (current_x, current_y + h_dot * 2),
            4: (current_x + w_dot, current_y),
            5: (current_x + w_dot, current_y + h_dot),
            6: (current_x + w_dot, current_y + h_dot * 2),
        }
        
        # Dibujar Puntos Negros (Activos)
        pdf.set_fill_color(0, 0, 0)
        for p_num in puntos_espejo:
            pos = positions[p_num]
            pdf.circle(pos[0], pos[1], dot_radius, 'F')
            
        current_x += w_char

# --- 5. FUNCIONES AUXILIARES ---
def ruta_imagen_segura(nombre_objetivo):
    if not nombre_objetivo: return None
    ruta_exacta = os.path.join(ASSETS_DIR, nombre_objetivo)
    if os.path.exists(ruta_exacta): return ruta_exacta
    for archivo_real in os.listdir(ASSETS_DIR):
        if archivo_real.lower() == nombre_objetivo.lower():
            return os.path.join(ASSETS_DIR, archivo_real)
    return None

# --- 6. MAPEOS ---
MAPA_VIA = {
    "Vía Oral (Tragar)": "01.GIF", "Masticar": "43.GIF", "Sublingual": "46.GIF",
    "Disolver en agua": "45.GIF", "Diluir en agua": "44.GIF", "Inhalador": "71.GIF",
    "Spray Nasal": "77.GIF", "Gotas Nariz": "09.GIF", "Gotas Ojos": "29.GIF",
    "Gotas Oído": "31.GIF", "Inyección": "61.GIF", "Vía Rectal": "27.GIF",
    "Vía Vaginal": "25.GIF", "Gárgaras": "58.GIF"
}
MAPA_FRECUENCIA = {
    "--- Seleccionar ---": None, "Mañana (AM)": "67.GIF", "Noche / Hora de dormir": "22.GIF",
    "2 veces/día": "04.GIF", "2 veces/día (Comidas)": "03.GIF", 
    "3 veces/día": "16.GIF", "3 veces/día (Comidas)": "14.GIF",
    "4 veces/día": "15.GIF", "4 veces/día (Comidas)": "13.GIF",
    "1h antes comer": "05.GIF", "1h después comer": "06.GIF", 
    "2 horas ANTES de comidas": "07.GIF", "2 horas DESPUÉS de comidas": "08.GIF", 
    "Con alimentos": "18.GIF", "Estómago vacío": "19.GIF"
}
MAPA_ALERTAS = {
    "No alcohol": "40.GIF", "No conducir (Somnolencia)": "50.GIF", "No conducir (Mareo)": "72.GIF",
    "No triturar": "33.GIF", "No masticar": "48.GIF", "Agitar vigorosamente": "39.GIF",
    "Refrigerar": "20.GIF", "No refrigerar": "52.GIF", "No congelar": "51.GIF",
    "Proteger luz solar": "69.GIF", "No embarazo": "34.GIF", "No lactancia": "36.GIF",
    "No compartir": "54.GIF", "No fumar": "55.GIF", "Tomar agua adicional": "57.GIF",
    "Peligro": "81.GIF", "Causa somnolencia": "24.GIF", "No leche ni lácteos": "23.GIF"
}

# --- 7. GENERADOR PDF ---
def generar_pdf(paciente, medicamento, dosis, via_key, frecuencia_key, lista_alertas, es_ciego):
    pdf = FPDF()
    
    # === PÁGINA 1: VISUAL (Pictogramas) ===
    pdf.add_page()
    
    # Encabezado
    pdf.set_font("Arial", "B", 24)
    pdf.cell(0, 15, txt=f"{medicamento.upper()}", ln=True, align='C')
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, txt=f"PACIENTE: {paciente.upper()} | DOSIS: {dosis.upper()}", ln=True, align='C')
    pdf.line(10, 35, 200, 35)
    
    # Pictogramas (Texto Arriba)
    y_bloque_1 = 50 
    
    # Vía
    pdf.set_xy(20, y_bloque_1)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(60, 10, txt="VÍA / ACCIÓN", align='C')
    archivo_via = MAPA_VIA.get(via_key)
    if archivo_via:
        ruta = ruta_imagen_segura(archivo_via)
        if ruta:
            pdf.set_xy(20, y_bloque_1 + 12)
            pdf.set_font("Arial", "B", 10)
            pdf.multi_cell(60, 4, txt=via_key.upper(), align='C')
            pdf.image(ruta, x=35, y=y_bloque_1 + 25, w=30)
    
    # Frecuencia
    pdf.set_xy(100, y_bloque_1)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(60, 10, txt="HORARIO", align='C')
    archivo_frec = MAPA_FRECUENCIA.get(frecuencia_key)
    if archivo_frec:
        ruta = ruta_imagen_segura(archivo_frec)
        if ruta:
            pdf.set_xy(100, y_bloque_1 + 12)
            pdf.set_font("Arial", "B", 10)
            pdf.multi_cell(60, 4, txt=frecuencia_key.upper(), align='C')
            pdf.image(ruta, x=115, y=y_bloque_1 + 25, w=30)

    # Alertas
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
                pdf.set_font("Arial", "B", 8)
                pdf.set_xy(x_curr - 5, y_curr) 
                pdf.multi_cell(40, 3, txt=alerta_key.upper(), align='C')
                pdf.image(ruta, x=x_curr, y=y_curr + 12, w=25)
                x_curr += 45
                count += 1

    # === PÁGINA 2+: BRAILLE (Multipágina Automática) ===
    if es_ciego:
        pdf.add_page() # Primera página de Braille
        
        # Encabezado Braille
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, txt="GUÍA TÁCTIL (BRAILLE ESPEJO)", ln=True, align='C')
        pdf.set_font("Arial", "", 10)
        pdf.multi_cell(0, 5, txt="INSTRUCCIONES: Punzar puntos negros por el reverso.", align='C')
        pdf.ln(5)
        
        # Construcción del Texto
        alertas_str = ", ".join(lista_alertas) if lista_alertas else "NINGUNA"
        frec_texto = frecuencia_key if frecuencia_key else "NO INDICADO"
        
        # Información completa
        texto_completo = (
            f"PACIENTE: {paciente}. MEDICAMENTO: {medicamento} {dosis}. "
            f"VIA: {via_key}. TOMA: {frec_texto}. "
            f"PRECAUCIONES: {alertas_str}."
        )
        
        # Dibujar Puntos (Con soporte multipágina)
        braille_x = 10
        braille_y = 40
        dibujar_braille_paginado(pdf, texto_completo, braille_x, braille_y)
        
        # Pie de página (Solo en la última hoja generada)
        pdf.set_y(-15)
        pdf.set_font("Arial", "I", 8)
        pdf.cell(0, 10, txt="Sistema SMEFI - Módulo de Accesibilidad Táctil", align='C')

    return bytes(pdf.output(dest='S'))

# --- 8. INTERFAZ ---
col1, col2 = st.columns(2)
with col1:
    nombre = st.text_input("Paciente", "JUAN PEREZ")
    med = st.text_input("Medicamento", "AMOXICILINA")
with col2:
    dosis = st.text_input("Dosis", "500 MG")
    es_ciego = st.toggle("Generar Guía Braille Completa")

st.divider()

c3, c4 = st.columns(2)
with c3:
    st.info("ℹ️ Información de Toma")
    via_sel = st.selectbox("Vía de Administración", list(MAPA_VIA.keys()))
    frec_sel = st.selectbox("Frecuencia / Horario", list(MAPA_FRECUENCIA.keys()))
    
    cols_prev = st.columns(2)
    if via_sel:
        r = ruta_imagen_segura(MAPA_VIA[via_sel])
        if r: cols_prev[0].image(r, width=70)
    
    if frec_sel:
        nombre_archivo = MAPA_FRECUENCIA.get(frec_sel)
        if nombre_archivo:
            r = ruta_imagen_segura(nombre_archivo)
            if r: cols_prev[1].image(r, width=70)

with c4:
    st.warning("⚠️ Seguridad")
    alertas_sel = st.multiselect("Seleccione Precauciones:", list(MAPA_ALERTAS.keys()))
    if alertas_sel:
        cols = st.columns(4)
        for i, a in enumerate(alertas_sel):
            r = ruta_imagen_segura(MAPA_ALERTAS[a])
            if r: cols[i%4].image(r, width=40)

st.write("")
if st.button("GENERAR GUÍA PDF", type="primary", use_container_width=True):
    try:
        pdf_bytes = generar_pdf(nombre, med, dosis, via_sel, frec_sel, alertas_sel, es_ciego)
        st.success("✅ Guía Generada Exitosamente")
        st.download_button("📄 DESCARGAR PDF FINAL", pdf_bytes, file_name=f"Guia_{med}.pdf", mime="application/pdf")
    except Exception as e:
        st.error(f"Error técnico: {e}")
