import streamlit as st
from fpdf import FPDF
import os
import unicodedata
import time

# --- 1. CONFIGURACIÓN ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, 'assets', 'usp_pictograms')

st.set_page_config(page_title="SMEFI Final", page_icon="💊", layout="wide")
st.title("🖨️ Sistema de Dispensación Inclusiva (SMEFI)")
st.markdown("**Versión 6.2 (Pagina Corregida):** Braille Nativo + Fix Páginas en Blanco.")

if not os.path.exists(ASSETS_DIR):
    st.error(f"❌ Error Crítico: No existe la carpeta {ASSETS_DIR}. Asegúrate de subir los iconos.")

# --- 2. MOTOR BRAILLE NATIVO ---
class BrailleConverter:
    """
    Convierte texto a coordenadas de puntos Braille (Estándar Español Grado 1).
    """
    # Mapeo de Puntos (1-6)
    CHAR_MAP = {
        'a': [1], 'b': [1,2], 'c': [1,4], 'd': [1,4,5], 'e': [1,5],
        'f': [1,2,4], 'g': [1,2,4,5], 'h': [1,2,5], 'i': [2,4], 'j': [2,4,5],
        'k': [1,3], 'l': [1,2,3], 'm': [1,3,4], 'n': [1,3,4,5], 'o': [1,3,5],
        'p': [1,2,3,4], 'q': [1,2,3,4,5], 'r': [1,2,3,5], 's': [2,3,4], 't': [2,3,4,5],
        'u': [1,3,6], 'v': [1,2,3,6], 'w': [2,4,5,6], 'x': [1,3,4,6], 'y': [1,3,4,5,6], 'z': [1,3,5,6],
        'á': [1,2,3,5,6], 'é': [2,3,4,6], 'í': [3,4], 'ó': [3,4,6], 'ú': [2,3,4,5,6], 'ü': [1,2,5,6],
        'ñ': [1,2,4,5,6],
        ',': [2], ';': [2,3], ':': [2,5], '.': [2,5,6], '!': [2,3,5], 
        '(': [2,3,5,6], ')': [2,3,5,6], '?': [2,6], '-': [3,6], '/': [3,4], 
        ' ': []
    }
    
    # Mapeo numérico (a=1, b=2...)
    NUM_MAP = {'1':'a', '2':'b', '3':'c', '4':'d', '5':'e', '6':'f', '7':'g', '8':'h', '9':'i', '0':'j'}
    NUM_SIGN = [3, 4, 5, 6] # Prefijo numérico

    @staticmethod
    def text_to_dots(texto):
        dots_sequence = []
        # Normalización para asegurar que 'á' sea un solo caracter y no 'a' + tilde
        texto = unicodedata.normalize('NFC', str(texto)).lower()
        is_number = False
        
        for char in texto:
            if char.isdigit():
                if not is_number:
                    dots_sequence.append(BrailleConverter.NUM_SIGN)
                    is_number = True
                mapped_char = BrailleConverter.NUM_MAP.get(char)
                dots_sequence.append(BrailleConverter.CHAR_MAP.get(mapped_char, []))
            else:
                if is_number and char not in [',', '.']: 
                    is_number = False 
                
                puntos = BrailleConverter.CHAR_MAP.get(char, [])
                dots_sequence.append(puntos)
        return dots_sequence

def render_braille_mirror(pdf, text, x_start, y_start):
    """ Dibuja los puntos en el PDF y devuelve la posición Y final """
    dots_seq = BrailleConverter.text_to_dots(text)
    
    # Configuración Física
    scale = 1.1
    r = 0.55 * scale 
    spacing_dot = 2.5 * scale
    spacing_char = 6.2 * scale
    spacing_line = 11.0 * scale
    margin_right = 190
    
    cur_x, cur_y = x_start, y_start
    mirror = {1:4, 2:5, 3:6, 4:1, 5:2, 6:3}

    for char_dots in dots_seq:
        if cur_x + spacing_char > margin_right:
            cur_x = x_start
            cur_y += spacing_line
            # Si nos pasamos de la página, paramos para evitar errores visuales
            if cur_y > 270: break 
            
        dots_mirror = [mirror[p] for p in char_dots if p in mirror]
        
        # Guías
        pdf.set_fill_color(240, 240, 240)
        coords = {
            1: (cur_x, cur_y), 2: (cur_x, cur_y + spacing_dot), 3: (cur_x, cur_y + spacing_dot * 2),
            4: (cur_x + spacing_dot, cur_y), 5: (cur_x + spacing_dot, cur_y + spacing_dot), 6: (cur_x + spacing_dot, cur_y + spacing_dot * 2)
        }
        
        pdf.set_fill_color(0, 0, 0)
        for p in dots_mirror:
            if p in coords:
                cx, cy = coords[p]
                pdf.circle(cx, cy, r, 'F')
            
        cur_x += spacing_char
        
    return cur_y # Devolvemos la posición final para saber dónde escribir después

# --- 3. GESTIÓN DE IMÁGENES ---
def get_img(name):
    if not name: return None
    path = os.path.join(ASSETS_DIR, name)
    if os.path.exists(path): return path
    for f in os.listdir(ASSETS_DIR):
        if f.lower() == name.lower(): return os.path.join(ASSETS_DIR, f)
    return None

# --- MAPEOS ---
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
    "Venenoso / Tóxico": "81.GIF", "No alcohol": "40.GIF", "No conducir (Sueño)": "50.GIF", 
    "No conducir (Mareo)": "72.GIF", "No triturar": "33.GIF", "No masticar": "48.GIF", 
    "Agitar vigorosamente": "39.GIF", "Refrigerar": "20.GIF", "No refrigerar": "52.GIF", 
    "No congelar": "51.GIF", "Proteger luz solar": "12.GIF", "No embarazo": "34.GIF", 
    "No lactancia": "36.GIF", "No compartir": "54.GIF", "No fumar": "55.GIF", 
    "Tomar agua extra": "57.GIF", "Causa somnolencia": "24.GIF", "Llamar al doctor": "42.GIF", 
    "Emergencia": "59.GIF", "Lavarse las manos": "41.GIF", "Leer etiqueta": "78.GIF", 
    "Flamable": "80.GIF", "No agitar": "53.GIF", "Mantener alejado niños": "17.GIF"
}

# --- 4. GENERADOR PDF ---
def generar_pdf(paciente, med, dosis, via, frec, alertas, hacer_braille):
    pdf = FPDF()
    
    # PÁGINA 1: VISUAL
    pdf.add_page()
    pdf.set_font("Arial", "B", 24)
    pdf.cell(0, 15, txt=f"{str(med).upper()}", ln=True, align='C')
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, txt=f"PACIENTE: {str(paciente).upper()} | DOSIS: {str(dosis).upper()}", ln=True, align='C')
    pdf.line(10, 35, 200, 35)
    
    # Bloque Vía/Frec
    y_start = 50
    pdf.set_xy(20, y_start)
    pdf.cell(60, 10, txt="VÍA / ACCIÓN", align='C', ln=1)
    
    p1 = get_img(MAPA_VIA.get(via))
    if p1:
        pdf.set_xy(20, y_start+10)
        pdf.set_font("Arial", "B", 10)
        pdf.multi_cell(60, 4, txt=str(via).upper(), align='C')
        pdf.image(p1, x=35, y=pdf.get_y()+2, w=30)
        
    pdf.set_xy(110, y_start)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(60, 10, txt="HORARIO", align='C', ln=1)
    p2 = get_img(MAPA_FRECUENCIA.get(frec))
    if p2:
        pdf.set_xy(110, y_start+10)
        pdf.set_font("Arial", "B", 10)
        pdf.multi_cell(60, 4, txt=str(frec).upper(), align='C')
        pdf.image(p2, x=125, y=pdf.get_y()+2, w=30)

    # Bloque Alertas
    y_al = 120
    pdf.set_xy(10, y_al)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, txt="PRECAUCIONES:", ln=1)
    
    cx, cy, col = 20, y_al+15, 0
    for al in alertas:
        p3 = get_img(MAPA_ALERTAS.get(al))
        if p3:
            if col == 4: cx, cy, col = 20, cy+50, 0
            pdf.set_xy(cx-5, cy)
            pdf.set_font("Arial", "B", 8)
            pdf.multi_cell(40, 3, txt=str(al).upper(), align='C')
            pdf.image(p3, x=cx, y=pdf.get_y()+2, w=22)
            cx += 45
            col += 1

    # PÁGINA 2: BRAILLE ENGINE
    if hacer_braille:
        pdf.add_page()
        # IMPORTANTE: Desactivar salto automático para evitar páginas en blanco por el footer
        pdf.set_auto_page_break(auto=False)
        
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, txt="GUÍA TÁCTIL (BRAILLE ESPEJO)", ln=True, align='C')
        pdf.set_font("Arial", "", 10)
        pdf.multi_cell(0, 5, txt="INSTRUCCIONES: Punzar puntos negros por el reverso.", align='C')
        pdf.ln(10)
        
        # Texto Braille
        al_str = ", ".join(alertas) if alertas else "NINGUNA"
        t_raw = f"PAC:{paciente} MED:{med} DOSIS:{dosis} VIA:{via} TOMA:{frec}"
        
        # Renderizado
        final_y = render_braille_mirror(pdf, t_raw, 10, 45)
        
        # Pie de página y Debug (Controlando posición para no saltar página)
        # Si el braille ocupa casi toda la hoja (>250), creamos nueva página para el footer
        if final_y > 250:
            pdf.add_page()
            pdf.set_auto_page_break(auto=False)
            
        pdf.set_y(-25) # Ir al final de la página actual
        
        pdf.set_font("Courier", "", 8)
        pdf.set_text_color(100, 100, 100)
        # Cortamos el texto si es muy largo para que no rompa el diseño
        texto_debug = (t_raw[:85] + '...') if len(t_raw) > 85 else t_raw
        pdf.cell(0, 5, txt=f"Referencia: {texto_debug}", align='C', ln=1)
        
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", "I", 8)
        pdf.cell(0, 5, txt="SMEFI System - Braille Engine v6.2", align='C')

    return bytes(pdf.output(dest='S')) # Retornamos bytes para Streamlit

# --- 5. INTERFAZ UI ---
c1, c2 = st.columns([1, 3])
with c2: st.subheader("Datos del Tratamiento")

with st.container(border=True):
    ca, cb = st.columns(2)
    nom = ca.text_input("Nombre Paciente", value="Juan Perez")
    med = ca.text_input("Medicamento", value="AMOXICILINA")
    dos = cb.text_input("Dosis", value="500 mg")
    bra = cb.toggle("Generar Hoja Braille", value=True)

c3, c4 = st.columns(2)
with c3:
    st.info("ℹ️ Información de Toma")
    v = st.selectbox("Vía", list(MAPA_VIA.keys()))
    f = st.selectbox("Frecuencia", list(MAPA_FRECUENCIA.keys()))
    
    cp = st.columns(2)
    im1 = get_img(MAPA_VIA.get(v))
    if im1: cp[0].image(im1, width=60)
    im2 = get_img(MAPA_FRECUENCIA.get(f))
    if im2: cp[1].image(im2, width=60)

with c4:
    st.warning("⚠️ Seguridad")
    a = st.multiselect("Alertas", list(MAPA_ALERTAS.keys()))
    if a:
        cols = st.columns(4)
        for i, al in enumerate(a):
            im3 = get_img(MAPA_ALERTAS.get(al))
            if im3: cols[i%4].image(im3, width=40)

st.write("")
if st.button("GENERAR GUÍA PDF", type="primary", use_container_width=True):
    try:
        pdf_bytes = generar_pdf(nom, med, dos, v, f, a, bra)
        st.success("✅ ¡Documento generado correctamente!")
        
        file_id = int(time.time())
        st.download_button(
            label="📥 DESCARGAR PDF",
            data=pdf_bytes,
            file_name=f"Guia_{med}_{file_id}.pdf",
            mime="application/pdf"
        )
    except Exception as e:
        st.error(f"Error técnico: {e}")
