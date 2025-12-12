import streamlit as st
from fpdf import FPDF
import os
import unicodedata

# --- 1. CONFIGURACIÓN E INICIALIZACIÓN ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, 'assets', 'usp_pictograms')

st.set_page_config(page_title="SMEFI Prototipo", page_icon="💊", layout="wide")
st.title("🖨️ Sistema de Dispensación Inclusiva (SMEFI)")
st.markdown("**Versión 4.0 (Final):** Braille Dinámico + Lista Completa USP (01-81).")

if not os.path.exists(ASSETS_DIR):
    st.error(f"❌ Error: No se encuentra la carpeta {ASSETS_DIR}")

# --- 2. MOTOR DE BRAILLE (TACTILE ENGINE) ---
# Diccionario Braille Unicode (6 puntos)
BRAILLE_MAP = {
    'A': [1], 'B': [1,2], 'C': [1,4], 'D': [1,4,5], 'E': [1,5],
    'F': [1,2,4], 'G': [1,2,4,5], 'H': [1,2,5], 'I': [2,4], 'J': [2,4,5],
    'K': [1,3], 'L': [1,2,3], 'M': [1,3,4], 'N': [1,3,4,5], 'O': [1,3,5],
    'P': [1,2,3,4], 'Q': [1,2,3,4,5], 'R': [1,2,3,5], 'S': [2,3,4], 'T': [2,3,4,5],
    'U': [1,3,6], 'V': [1,2,3,6], 'W': [2,4,5,6], 'X': [1,3,4,6], 'Y': [1,3,4,5,6], 'Z': [1,3,5,6],
    '1': [1], '2': [1,2], '3': [1,4], '4': [1,4,5], '5': [1,5],
    '6': [1,2,4], '7': [1,2,4,5], '8': [1,2,5], '9': [2,4], '0': [2,4,5],
    ' ': [], '.': [2,5,6], ',': [2], ':': [2,5], ';': [2,3], '-': [3,6],
    '(': [2,3,5,6], ')': [2,3,5,6], '/': [3,4], '+': [2,3,5]
}

def renderizar_braille_espejo(pdf, texto, x_start, y_start):
    """
    Convierte texto a círculos vectoriales (puntos) en modo espejo.
    Maneja el texto dinámico para que no se repita.
    """
    # 1. Normalización estricta (Mayúsculas sin tildes)
    texto_limpio = ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    ).upper()
    
    # 2. Configuración de dimensiones (Calibrado para punzón)
    scale = 1.2
    r_punto = 0.5 * scale  # Radio
    w_espacio = 2.5 * scale # Espacio entre puntos H
    h_espacio = 2.5 * scale # Espacio entre puntos V
    w_letra = 6.5 * scale   # Ancho celda
    h_linea = 12.0 * scale  # Salto de línea
    margen_derecho = 190
    
    cur_x, cur_y = x_start, y_start
    
    # Espejo: 1->4, 2->5, 3->6 (Inversión horizontal de la celda)
    espejo = {1:4, 2:5, 3:6, 4:1, 5:2, 6:3}

    for char in texto_limpio:
        # Salto de línea automático
        if cur_x + w_letra > margen_derecho:
            cur_x = x_start
            cur_y += h_linea
            
        # Obtener puntos del caracter
        puntos = BRAILLE_MAP.get(char, [])
        puntos_mirror = [espejo[p] for p in puntos]
        
        # Dibujar guías (gris claro)
        pdf.set_fill_color(240, 240, 240)
        coords = {
            1: (cur_x, cur_y),
            2: (cur_x, cur_y + h_espacio),
            3: (cur_x, cur_y + h_espacio*2),
            4: (cur_x + w_espacio, cur_y),
            5: (cur_x + w_espacio, cur_y + h_espacio),
            6: (cur_x + w_espacio, cur_y + h_espacio*2)
        }
        
        # Dibujar puntos negros (Donde se punza)
        pdf.set_fill_color(0, 0, 0)
        for p in puntos_mirror:
            px, py = coords[p]
            pdf.circle(px, py, r_punto, 'F')
            
        cur_x += w_letra

# --- 3. BASE DE DATOS COMPLETA (USP 01-81) ---
# Organizada lógicamente para los desplegables

MAPA_VIA = {
    "Vía Oral": "01.GIF",
    "Masticar": "43.GIF",
    "Sublingual": "46.GIF",
    "Disolver en agua": "45.GIF",
    "Diluir en agua": "44.GIF",
    "Tomar con agua": "38.GIF", # 38
    "Gárgaras": "58.GIF",
    "No tragar": "56.GIF",
    "Gotas Nariz": "09.GIF",
    "Uso Nasal (Secuencia)": "10.GIF",
    "Spray Nasal": "77.GIF",
    "Inhalador": "71.GIF",
    "Gotas Ojos": "29.GIF",
    "Uso Ojos (Secuencia)": "30.GIF",
    "Gotas Oído": "31.GIF",
    "Uso Oído (Secuencia)": "32.GIF",
    "Inyección": "61.GIF",
    "Vía Rectal": "27.GIF",
    "Uso Rectal (Secuencia)": "28.GIF",
    "Vía Vaginal": "25.GIF",
    "Uso Vaginal (Secuencia)": "26.GIF",
    "Óvulo Vaginal": "66.GIF"
}

MAPA_FRECUENCIA = {
    "--- Seleccionar ---": None,
    "Mañana (AM)": "67.GIF",
    "Noche / Al acostarse": "22.GIF",
    "No tomar de noche": "49.GIF",
    "2 veces al día": "04.GIF",
    "2 veces al día (Con comidas)": "03.GIF",
    "3 veces al día": "16.GIF",
    "3 veces al día (Con comidas)": "14.GIF",
    "4 veces al día": "15.GIF",
    "4 veces al día (+ Dormir)": "13.GIF",
    "1 hora ANTES de comer": "05.GIF",
    "1 hora DESPUÉS de comer": "06.GIF",
    "2 horas ANTES de comer": "07.GIF",
    "2 horas DESPUÉS de comer": "08.GIF",
    "Con alimentos": "18.GIF",
    "Sin alimentos (Estómago vacío)": "19.GIF",
    "Con leche": "68.GIF",
    "NO con leche/lácteos": "23.GIF"
}

MAPA_ALERTAS = {
    "Venenoso / Tóxico": "81.GIF", # CORREGIDO
    "No alcohol": "40.GIF",
    "No conducir (Sueño)": "50.GIF",
    "No conducir (Mareo)": "72.GIF",
    "Agitar vigorosamente": "39.GIF",
    "No agitar": "53.GIF",
    "Refrigerar": "20.GIF",
    "No refrigerar": "52.GIF",
    "No congelar": "51.GIF",
    "Alejar luz solar": "12.GIF",
    "No triturar/romper": "33.GIF",
    "No masticar": "48.GIF",
    "No compartir": "54.GIF",
    "Mantener alejado niños": "17.GIF",
    "No dar a bebés": "64.GIF",
    "No dar a niños": "65.GIF",
    "Embarazo: NO usar": "34.GIF",
    "Embarazo: Consultar": "35.GIF",
    "Lactancia: NO usar": "36.GIF",
    "Lactancia: Consultar": "37.GIF",
    "Flamable": "80.GIF",
    "Causa somnolencia": "24.GIF",
    "Causa mareos": "47.GIF",
    "Llamar al doctor": "42.GIF",
    "Emergencia": "59.GIF",
    "Tomar agua extra": "57.GIF",
    "Lavarse las manos": "41.GIF",
    "Leer etiqueta": "78.GIF"
}

# --- 4. FUNCIÓN IMAGEN SEGURA ---
def get_img_path(filename):
    if not filename: return None
    # Intento 1: Exacto
    path = os.path.join(ASSETS_DIR, filename)
    if os.path.exists(path): return path
    # Intento 2: Insensible a mayúsculas
    for f in os.listdir(ASSETS_DIR):
        if f.lower() == filename.lower():
            return os.path.join(ASSETS_DIR, f)
    return None

# --- 5. GENERADOR PDF (CORE) ---
def generar_pdf_final(paciente, med, dosis, via, frec, alertas_list, hacer_braille):
    pdf = FPDF()
    
    # === PÁGINA 1: VISUAL ===
    pdf.add_page()
    
    # Encabezado (Texto grande arriba)
    pdf.set_font("Arial", "B", 24)
    pdf.cell(0, 15, txt=f"{med.upper()}", ln=True, align='C')
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, txt=f"PACIENTE: {paciente.upper()}", ln=True, align='C')
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, txt=f"DOSIS: {dosis.upper()}", ln=True, align='C')
    pdf.line(10, 42, 200, 42)
    
    # --- BLOQUE SUPERIOR (VÍA + FREC) ---
    y_start = 55
    
    # Columna Vía
    pdf.set_xy(20, y_start)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(60, 10, txt="VÍA / ACCIÓN", align='C', ln=1)
    
    path_via = get_img_path(MAPA_VIA.get(via))
    if path_via:
        # Texto DESCRIPTIVO ARRIBA
        pdf.set_xy(20, y_start + 10)
        pdf.set_font("Arial", "B", 10)
        pdf.multi_cell(60, 5, txt=via.upper(), align='C')
        # Imagen ABAJO
        pdf.image(path_via, x=35, y=pdf.get_y() + 2, w=30)
    
    # Columna Frecuencia
    pdf.set_xy(110, y_start)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(60, 10, txt="HORARIO", align='C', ln=1)
    
    path_frec = get_img_path(MAPA_FRECUENCIA.get(frec))
    if path_frec:
        # Texto DESCRIPTIVO ARRIBA
        pdf.set_xy(110, y_start + 10)
        pdf.set_font("Arial", "B", 10)
        pdf.multi_cell(60, 5, txt=frec.upper(), align='C')
        # Imagen ABAJO
        pdf.image(path_frec, x=125, y=pdf.get_y() + 2, w=30)

    # --- BLOQUE INFERIOR (ALERTAS) ---
    y_alerts = 125
    pdf.set_xy(10, y_alerts)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, txt="PRECAUCIONES:", ln=1)
    
    x_curr = 20
    y_curr = y_alerts + 15
    col_count = 0
    
    for alerta in alertas_list:
        path_a = get_img_path(MAPA_ALERTAS.get(alerta))
        if path_a:
            # Control de filas (4 por fila)
            if col_count == 4:
                x_curr = 20
                y_curr += 50
                col_count = 0
            
            # Texto ARRIBA
            pdf.set_xy(x_curr - 5, y_curr)
            pdf.set_font("Arial", "B", 8)
            pdf.multi_cell(40, 3, txt=alerta.upper(), align='C')
            
            # Imagen ABAJO
            # Calculamos Y basado en dónde terminó el texto
            y_img = pdf.get_y() + 2
            pdf.image(path_a, x=x_curr, y=y_img, w=22)
            
            x_curr += 45
            col_count += 1

    # === PÁGINA 2: BRAILLE (Dinámico Real) ===
    if hacer_braille:
        pdf.add_page()
        
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, txt="GUÍA TÁCTIL (BRAILLE ESPEJO)", ln=True, align='C')
        pdf.set_font("Arial", "", 10)
        pdf.multi_cell(0, 5, txt="INSTRUCCIONES: Esta hoja contiene la información traducida a puntos invertidos. Coloque sobre superficie blanda y punce los puntos negros.", align='C')
        pdf.ln(10)
        
        # CADENA DINÁMICA: Se reconstruye con los datos actuales
        str_alertas = ", ".join(alertas_list) if alertas_list else "NINGUNA"
        str_frec = frec if frec else "VER INDICACIONES"
        
        texto_final = (
            f"PAC:{paciente}. MED:{med} {dosis}. "
            f"VIA:{via}. TOMA:{str_frec}. "
            f"PRE:{str_alertas}."
        )
        
        # Renderizar
        renderizar_braille_espejo(pdf, texto_final, 10, 40)
        
        pdf.set_y(-15)
        pdf.set_font("Arial", "I", 8)
        pdf.cell(0, 10, txt="SMEFI System - Módulo Braille", align='C')

    return bytes(pdf.output(dest='S'))

# --- 6. INTERFAZ DE USUARIO ---
col1, col2 = st.columns([1, 3])
with col2:
    st.subheader("Datos del Tratamiento")

with st.container(border=True):
    c1, c2 = st.columns(2)
    with c1:
        p_nombre = st.text_input("Nombre Paciente", "JUAN PEREZ")
        p_med = st.text_input("Medicamento", "IBUPROFENO")
    with c2:
        p_dosis = st.text_input("Dosis", "400 MG")
        p_braille = st.toggle("Generar Hoja Braille")

    st.divider()
    
    c3, c4 = st.columns(2)
    with c3:
        st.info("ℹ️ Vía y Frecuencia")
        sel_via = st.selectbox("Vía de Administración", list(MAPA_VIA.keys()))
        sel_frec = st.selectbox("Frecuencia", list(MAPA_FRECUENCIA.keys()))
        
        # Previas
        cols = st.columns(2)
        img1 = get_img_path(MAPA_VIA.get(sel_via))
        if img1: cols[0].image(img1, width=60)
        
        img2 = get_img_path(MAPA_FRECUENCIA.get(sel_frec))
        if img2: cols[1].image(img2, width=60)

    with c4:
        st.warning("⚠️ Precauciones")
        sel_alertas = st.multiselect("Seleccione todas las que apliquen:", list(MAPA_ALERTAS.keys()))
        
        if sel_alertas:
            acols = st.columns(4)
            for i, a in enumerate(sel_alertas):
                aimg = get_img_path(MAPA_ALERTAS.get(a))
                if aimg: acols[i%4].image(aimg, width=40)

st.write("")
if st.button("GENERAR GUÍA DE IMPRESIÓN", type="primary", use_container_width=True):
    try:
        pdf_data = generar_pdf_final(p_nombre, p_med, p_dosis, sel_via, sel_frec, sel_alertas, p_braille)
        st.success("✅ Documento creado exitosamente")
        st.download_button(
            label="📥 DESCARGAR PDF",
            data=pdf_data,
            file_name=f"Guia_{p_med}.pdf",
            mime="application/pdf"
        )
    except Exception as e:
        st.error(f"Error técnico: {e}")
