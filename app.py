import streamlit as st
from fpdf import FPDF
import os
import unicodedata

# --- 1. CONFIGURACIÓN E INICIALIZACIÓN ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, 'assets', 'usp_pictograms')

st.set_page_config(page_title="SMEFI Final", page_icon="💊", layout="wide")
st.title("🖨️ Sistema de Dispensación Inclusiva (SMEFI)")
st.markdown("**Versión 5.1 (Estable):** Braille Grado 1 (Números Correctos) + Pictogramas Completos.")

if not os.path.exists(ASSETS_DIR):
    st.error(f"❌ Error: Verifica que exista la carpeta {ASSETS_DIR}")

# --- 2. MOTOR DE TRADUCCIÓN BRAILLE (BRAILLE ENGINE) ---
# Mapeo de letras a puntos (1-6)
CHAR_TO_DOTS = {
    'a': [1], 'b': [1,2], 'c': [1,4], 'd': [1,4,5], 'e': [1,5],
    'f': [1,2,4], 'g': [1,2,4,5], 'h': [1,2,5], 'i': [2,4], 'j': [2,4,5],
    'k': [1,3], 'l': [1,2,3], 'm': [1,3,4], 'n': [1,3,4,5], 'o': [1,3,5],
    'p': [1,2,3,4], 'q': [1,2,3,4,5], 'r': [1,2,3,5], 's': [2,3,4], 't': [2,3,4,5],
    'u': [1,3,6], 'v': [1,2,3,6], 'w': [2,4,5,6], 'x': [1,3,4,6], 'y': [1,3,4,5,6], 'z': [1,3,5,6],
    'á': [1,2,3,5,6], 'é': [2,3,4,6], 'í': [3,4], 'ó': [3,4,6], 'ú': [2,3,4,5,6], 'ü': [1,2,5,6],
    'ñ': [1,2,4,5,6],
    ',': [2], ';': [2,3], ':': [2,5], '.': [2,5,6], '!': [2,3,5], '(': [2,3,5,6], ')': [2,3,5,6],
    '-': [3,6], '/': [3,4], ' ': []
}

# Mapeo de Números (Sistema Numérico Braille: Prefijo + a-j)
NUM_TO_LETTER = {
    '1': 'a', '2': 'b', '3': 'c', '4': 'd', '5': 'e',
    '6': 'f', '7': 'g', '8': 'h', '9': 'i', '0': 'j'
}
SIGNO_NUMERO = [3, 4, 5, 6] # Prefijo indispensable para números

def texto_a_puntos_braille(texto):
    """
    Convierte texto humano a una lista de patrones de puntos.
    Ej: "10" -> [[3,4,5,6], [1], [2,4,5]] (Signo # + A + J)
    """
    resultado_puntos = []
    texto = texto.lower() # Estandarizamos a minúsculas para Grado 1
    
    es_numero = False
    
    for char in texto:
        if char.isdigit():
            if not es_numero:
                resultado_puntos.append(SIGNO_NUMERO) # Activar modo número
                es_numero = True
            letra_equivalente = NUM_TO_LETTER[char]
            resultado_puntos.append(CHAR_TO_DOTS.get(letra_equivalente, []))
        else:
            # Si veníamos de números y ahora es letra o símbolo (menos punto/coma), cerramos modo número
            if es_numero and char not in ['.', ',']:
                es_numero = False
            
            # Normalizar caracteres (quitar acentos raros si no están en mapa)
            char_norm = unicodedata.normalize('NFC', char)
            if char_norm in CHAR_TO_DOTS:
                resultado_puntos.append(CHAR_TO_DOTS[char_norm])
            else:
                resultado_puntos.append([]) # Espacio si no se reconoce
                
    return resultado_puntos

def dibujar_braille_en_pdf(pdf, lista_puntos, x_start, y_start):
    """
    Dibuja los puntos vectoriales en el PDF con lógica de espejo.
    """
    # Configuración Física (Estándar Marburg)
    scale = 1.1
    dot_r = 0.55 * scale
    w_dot = 2.5 * scale
    h_dot = 2.5 * scale
    w_char = 6.2 * scale
    h_line = 11.0 * scale
    margin_right = 190
    
    cur_x, cur_y = x_start, y_start
    
    # Espejo (1<->4, 2<->5, 3<->6) para punzado reverso
    mirror = {1:4, 2:5, 3:6, 4:1, 5:2, 6:3}

    for puntos_caracter in lista_puntos:
        # Salto de línea si llegamos al borde derecho
        if cur_x + w_char > margin_right:
            cur_x = x_start
            cur_y += h_line
            # Si se acaba la hoja verticalmente, paramos (en un sistema real se agregaría pág)
            if cur_y > 270: break 

        # Invertir puntos para espejo
        puntos_espejo = [mirror[p] for p in puntos_caracter if p in mirror]
        
        # Dibujar guías visuales (Gris claro)
        pdf.set_fill_color(240, 240, 240)
        
        # Diccionario de coordenadas CORREGIDO
        coords = {
            1: (cur_x, cur_y),
            2: (cur_x, cur_y + h_dot),
            3: (cur_x, cur_y + h_dot * 2),          # <--- ERROR CORREGIDO AQUÍ
            4: (cur_x + w_dot, cur_y),
            5: (cur_x + w_dot, cur_y + h_dot),
            6: (cur_x + w_dot, cur_y + h_dot * 2)
        }
        
        # Dibujar puntos negros (Activos)
        pdf.set_fill_color(0, 0, 0)
        for p in puntos_espejo:
            cx, cy = coords[p]
            pdf.circle(cx, cy, dot_r, 'F')
            
        cur_x += w_char

# --- 3. BASE DE DATOS DE IMÁGENES ---
def get_img(name):
    if not name: return None
    path = os.path.join(ASSETS_DIR, name)
    if os.path.exists(path): return path
    # Intento insensible a mayúsculas
    for f in os.listdir(ASSETS_DIR):
        if f.lower() == name.lower():
            return os.path.join(ASSETS_DIR, f)
    return None

MAPA_VIA = {
    "Vía Oral (Tragar)": "01.GIF", "Masticar": "43.GIF", "Sublingual": "46.GIF",
    "Disolver en agua": "45.GIF", "Diluir en agua": "44.GIF", "Inhalador": "71.GIF",
    "Spray Nasal": "77.GIF", "Gotas Nariz": "09.GIF", "Gotas Ojos": "29.GIF",
    "Gotas Oído": "31.GIF", "Inyección": "61.GIF", "Vía Rectal": "27.GIF",
    "Vía Vaginal": "25.GIF", "Gárgaras": "58.GIF", "Tomar con agua": "38.GIF",
    "No tragar": "56.GIF", "Uso Nasal (Secuencia)": "10.GIF", "Uso Ojos (Secuencia)": "30.GIF",
    "Uso Oído (Secuencia)": "32.GIF", "Uso Rectal (Secuencia)": "28.GIF",
    "Uso Vaginal (Secuencia)": "26.GIF", "Óvulo Vaginal": "66.GIF"
}

MAPA_FRECUENCIA = {
    "--- Seleccionar ---": None, "Mañana (AM)": "67.GIF", "Noche": "22.GIF",
    "2 veces al día": "04.GIF", "2 veces al día (Con comidas)": "03.GIF",
    "3 veces al día": "16.GIF", "3 veces al día (Con comidas)": "14.GIF",
    "4 veces al día": "15.GIF", "4 veces al día (Con comidas)": "13.GIF",
    "1h ANTES de comer": "05.GIF", "1h DESPUÉS de comer": "06.GIF",
    "2h ANTES de comer": "07.GIF", "2h DESPUÉS de comer": "08.GIF",
    "Con alimentos": "18.GIF", "Estómago vacío": "19.GIF", "Con leche": "68.GIF",
    "No tomar de noche": "49.GIF", "NO con leche": "23.GIF"
}

MAPA_ALERTAS = {
    "Venenoso / Tóxico": "81.GIF", "No alcohol": "40.GIF", 
    "No conducir (Sueño)": "50.GIF", "No conducir (Mareo)": "72.GIF",
    "No triturar": "33.GIF", "No masticar": "48.GIF", "Agitar vigorosamente": "39.GIF",
    "Refrigerar": "20.GIF", "No refrigerar": "52.GIF", "No congelar": "51.GIF",
    "Proteger luz solar": "69.GIF", "No embarazo": "34.GIF", "No lactancia": "36.GIF",
    "No compartir": "54.GIF", "No fumar": "55.GIF", "Tomar agua extra": "57.GIF",
    "Causa somnolencia": "24.GIF", "Llamar al doctor": "42.GIF", "Emergencia": "59.GIF",
    "Lavarse las manos": "41.GIF", "Leer etiqueta": "78.GIF", "Flamable": "80.GIF",
    "No agitar": "53.GIF", "Mantener alejado niños": "17.GIF"
}

# --- 4. GENERADOR DE PDF ---
def generar_pdf_final(paciente, med, dosis, via, frec, alertas, hacer_braille):
    pdf = FPDF()
    
    # --- PÁGINA 1: VISUAL ---
    pdf.add_page()
    pdf.set_font("Arial", "B", 24)
    pdf.cell(0, 15, txt=f"{med.upper()}", ln=True, align='C')
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, txt=f"PACIENTE: {paciente.upper()}", ln=True, align='C')
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, txt=f"DOSIS: {dosis.upper()}", ln=True, align='C')
    pdf.line(10, 42, 200, 42)
    
    # Bloque Vía/Frec
    y_start = 55
    pdf.set_xy(20, y_start)
    pdf.cell(60, 10, txt="VÍA / ACCIÓN", align='C', ln=1)
    
    path1 = get_img(MAPA_VIA.get(via))
    if path1:
        pdf.set_xy(20, y_start+10)
        pdf.set_font("Arial", "B", 10)
        pdf.multi_cell(60, 4, txt=via.upper(), align='C')
        pdf.image(path1, x=35, y=pdf.get_y()+2, w=30)
        
    pdf.set_xy(110, y_start)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(60, 10, txt="HORARIO", align='C', ln=1)
    
    path2 = get_img(MAPA_FRECUENCIA.get(frec))
    if path2:
        pdf.set_xy(110, y_start+10)
        pdf.set_font("Arial", "B", 10)
        pdf.multi_cell(60, 4, txt=frec.upper(), align='C')
        pdf.image(path2, x=125, y=pdf.get_y()+2, w=30)

    # Bloque Alertas
    y_alert = 125
    pdf.set_xy(10, y_alert)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, txt="PRECAUCIONES:", ln=1)
    
    cx, cy = 20, y_alert + 15
    col = 0
    for al in alertas:
        path_a = get_img(MAPA_ALERTAS.get(al))
        if path_a:
            if col == 4: cx, cy, col = 20, cy+50, 0
            pdf.set_xy(cx-5, cy)
            pdf.set_font("Arial", "B", 8)
            pdf.multi_cell(40, 3, txt=al.upper(), align='C')
            pdf.image(path_a, x=cx, y=pdf.get_y()+2, w=22)
            cx += 45
            col += 1

    # --- PÁGINA 2: BRAILLE ENGINE ---
    if hacer_braille:
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, txt="GUÍA TÁCTIL (BRAILLE ESPEJO)", ln=True, align='C')
        pdf.set_font("Arial", "", 10)
        pdf.multi_cell(0, 5, txt="INSTRUCCIONES: Punzar los puntos negros por el reverso de la hoja.", align='C')
        pdf.ln(10)
        
        # 1. Construir texto plano (CADENA DINÁMICA REPARADA)
        str_alert = ", ".join(alertas) if alertas else "NINGUNA"
        # Usamos texto plano forzando la actualización
        texto_raw = f"PAC:{paciente}. MED:{med} {dosis}. VIA:{via}. TOMA:{frec}. PRE:{str_alert}."
        
        # 2. Traducir texto -> lista de puntos
        lista_puntos_braille = texto_a_puntos_braille(texto_raw)
        
        # 3. Renderizar puntos en PDF
        dibujar_braille_en_pdf(pdf, lista_puntos_braille, 10, 45)
        
        pdf.set_y(-15)
        pdf.set_font("Arial", "I", 8)
        pdf.cell(0, 10, txt="SMEFI System - Braille Engine v1.0", align='C')

    return bytes(pdf.output(dest='S'))

# --- 5. UI ---
col1, col2 = st.columns([1, 3])
with col2: st.subheader("Datos del Tratamiento")

with st.container(border=True):
    c_a, c_b = st.columns(2)
    p_nom = c_a.text_input("Nombre Paciente", "Juan Perez")
    p_med = c_a.text_input("Medicamento", "AMOXICILINA")
    p_dos = c_b.text_input("Dosis", "500 mg")
    p_br = c_b.toggle("Generar Hoja Braille")

c3, c4 = st.columns(2)
with c3:
    v_sel = st.selectbox("Vía", list(MAPA_VIA.keys()))
    f_sel = st.selectbox("Frecuencia", list(MAPA_FRECUENCIA.keys()))
    
    cp = st.columns(2)
    i1 = get_img(MAPA_VIA.get(v_sel))
    if i1: cp[0].image(i1, width=60)
    i2 = get_img(MAPA_FRECUENCIA.get(f_sel))
    if i2: cp[1].image(i2, width=60)

with c4:
    a_sel = st.multiselect("Alertas", list(MAPA_ALERTAS.keys()))
    if a_sel:
        ac = st.columns(4)
        for i, a in enumerate(a_sel):
            ia = get_img(MAPA_ALERTAS.get(a))
            if ia: ac[i%4].image(ia, width=40)

st.write("")
if st.button("GENERAR GUÍA PDF", type="primary", use_container_width=True):
    try:
        pdf_bytes = generar_pdf_final(p_nom, p_med, p_dos, v_sel, f_sel, a_sel, p_br)
        st.success("✅ Documento generado correctamente")
        st.download_button("📥 DESCARGAR PDF", pdf_bytes, f"Guia_{p_med}.pdf", "application/pdf")
    except Exception as e:
        st.error(f"Error: {e}")
