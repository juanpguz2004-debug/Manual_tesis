import streamlit as st
from fpdf import FPDF
import os
import unicodedata
import time

# --- 1. CONFIGURACIÓN ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, 'assets', 'usp_pictograms')

st.set_page_config(page_title="SMEFI Pro", page_icon="💊", layout="wide")
st.title("🖨️ Sistema de Dispensación Inclusiva (SMEFI)")
st.markdown("**Versión 7.0 (Professional):** Core Braille Estándar + Control de Paginación.")

if not os.path.exists(ASSETS_DIR):
    st.error(f"❌ Error Crítico: No existe la carpeta {ASSETS_DIR}. Verifica los assets.")

# --- 2. CORE BRAILLE (LIBRERÍA NATIVA) ---
class BrailleEngine:
    """
    Motor de traducción Braille Grado 1 (Español).
    Implementación profesional basada en mapeo directo de caracteres.
    """
    # Mapa estándar Braille (Puntos 1-6)
    MAPA_CHARS = {
        'a': [1], 'b': [1,2], 'c': [1,4], 'd': [1,4,5], 'e': [1,5],
        'f': [1,2,4], 'g': [1,2,4,5], 'h': [1,2,5], 'i': [2,4], 'j': [2,4,5],
        'k': [1,3], 'l': [1,2,3], 'm': [1,3,4], 'n': [1,3,4,5], 'o': [1,3,5],
        'p': [1,2,3,4], 'q': [1,2,3,4,5], 'r': [1,2,3,5], 's': [2,3,4], 't': [2,3,4,5],
        'u': [1,3,6], 'v': [1,2,3,6], 'w': [2,4,5,6], 'x': [1,3,4,6], 'y': [1,3,4,5,6], 'z': [1,3,5,6],
        'á': [1,2,3,5,6], 'é': [2,3,4,6], 'í': [3,4], 'ó': [3,4,6], 'ú': [2,3,4,5,6], 'ü': [1,2,5,6],
        'ñ': [1,2,4,5,6],
        '1': [1], '2': [1,2], '3': [1,4], '4': [1,4,5], '5': [1,5],
        '6': [1,2,4], '7': [1,2,4,5], '8': [1,2,5], '9': [2,4], '0': [2,4,5],
        ',': [2], ';': [2,3], ':': [2,5], '.': [2,5,6], '!': [2,3,5], 
        '(': [2,3,5,6], ')': [2,3,5,6], '?': [2,6], '-': [3,6], '/': [3,4], 
        ' ': [] # Espacio
    }
    SIGNO_NUMERO = [3, 4, 5, 6]
    SIGNO_MAYUS = [4, 6]

    @staticmethod
    def traducir(texto):
        """ Convierte string a lista de listas de puntos """
        secuencia_puntos = []
        # Normalizar Unicode (evitar tildes separadas)
        texto = unicodedata.normalize('NFC', str(texto))
        
        modo_numero = False
        
        for char in texto:
            es_mayus = char.isupper()
            char_lower = char.lower()
            
            # Manejo de Números
            if char_lower.isdigit():
                if not modo_numero:
                    secuencia_puntos.append(BrailleEngine.SIGNO_NUMERO)
                    modo_numero = True
                secuencia_puntos.append(BrailleEngine.MAPA_CHARS.get(char_lower, []))
                continue
            
            # Reset modo número si encontramos letra o espacio (pero no , o .)
            if modo_numero and char_lower not in [',', '.', ':']:
                modo_numero = False
                
            # Manejo de Mayúsculas (Opcional, desactivado para simplificar lectura médica, activar si se requiere)
            # if es_mayus: secuencia_puntos.append(BrailleEngine.SIGNO_MAYUS)
            
            # Obtener puntos
            puntos = BrailleEngine.MAPA_CHARS.get(char_lower, [])
            secuencia_puntos.append(puntos)
            
        return secuencia_puntos

def dibujar_braille(pdf, texto, x_inicio, y_inicio, es_espejo=True):
    """ Dibuja los puntos físicamente en el PDF """
    secuencia = BrailleEngine.traducir(texto)
    
    # Parámetros Físicos (Calibrados)
    scale = 1.1
    radio = 0.55 * scale
    espacio_punto = 2.5 * scale
    espacio_caracter = 6.2 * scale
    espacio_linea = 11.0 * scale
    margen_derecho = 190
    
    cur_x, cur_y = x_inicio, y_inicio
    
    # Matriz de Transformación (Espejo vs Normal)
    # Espejo (Reverso): 1->4, 2->5, 3->6
    # Normal (Frontal): 1->1, 2->2, 3->3
    mapa_espejo = {1:4, 2:5, 3:6, 4:1, 5:2, 6:3}
    
    for puntos_char in secuencia:
        # Salto de línea
        if cur_x + espacio_caracter > margen_derecho:
            cur_x = x_inicio
            cur_y += espacio_linea
            # Freno de emergencia si se sale de la página
            if cur_y > 260: break 
            
        # Aplicar espejo si es necesario
        puntos_finales = [mapa_espejo[p] for p in puntos_char] if es_espejo else puntos_char
        
        # Dibujar guías (gris muy claro)
        pdf.set_fill_color(245, 245, 245)
        coordenadas = {
            1: (cur_x, cur_y),
            2: (cur_x, cur_y + espacio_punto),
            3: (cur_x, cur_y + espacio_punto * 2),
            4: (cur_x + espacio_punto, cur_y),
            5: (cur_x + espacio_punto, cur_y + espacio_punto),
            6: (cur_x + espacio_punto, cur_y + espacio_punto * 2)
        }
        
        # Puntos activos (Negro)
        pdf.set_fill_color(0, 0, 0)
        for p in puntos_finales:
            if p in coordenadas:
                cx, cy = coordenadas[p]
                pdf.circle(cx, cy, radio, 'F')
            
        cur_x += espacio_caracter
        
    return cur_y # Devolvemos la posición Y final

# --- 3. GESTIÓN DE RECURSOS ---
def get_img(name):
    if not name: return None
    # Búsqueda robusta (insensible a mayúsculas)
    target = name.lower()
    for f in os.listdir(ASSETS_DIR):
        if f.lower() == target: return os.path.join(ASSETS_DIR, f)
    return None

# --- DATOS USP ---
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

# --- 4. GENERACIÓN PDF ---
def generar_pdf(paciente, med, dosis, via, frec, alertas, hacer_braille, braille_espejo):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15) # Default para la pág 1
    
    # --- PÁGINA 1: VISUAL ---
    pdf.add_page()
    pdf.set_font("Arial", "B", 24)
    pdf.cell(0, 15, txt=f"{str(med).upper()}", ln=True, align='C')
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, txt=f"PACIENTE: {str(paciente).upper()} | DOSIS: {str(dosis).upper()}", ln=True, align='C')
    pdf.line(10, 35, 200, 35)
    
    # Bloque Principal
    y_bloque = 50
    pdf.set_xy(20, y_bloque)
    pdf.cell(60, 10, txt="VÍA / ACCIÓN", align='C', ln=1)
    
    img_via = get_img(MAPA_VIA.get(via))
    if img_via:
        pdf.set_xy(20, y_bloque+10)
        pdf.set_font("Arial", "B", 10)
        pdf.multi_cell(60, 4, txt=str(via).upper(), align='C')
        pdf.image(img_via, x=35, y=pdf.get_y()+2, w=30)
        
    pdf.set_xy(110, y_bloque)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(60, 10, txt="HORARIO", align='C', ln=1)
    img_frec = get_img(MAPA_FRECUENCIA.get(frec))
    if img_frec:
        pdf.set_xy(110, y_bloque+10)
        pdf.set_font("Arial", "B", 10)
        pdf.multi_cell(60, 4, txt=str(frec).upper(), align='C')
        pdf.image(img_frec, x=125, y=pdf.get_y()+2, w=30)

    # Bloque Alertas
    y_al = 120
    pdf.set_xy(10, y_al)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, txt="PRECAUCIONES:", ln=1)
    
    cx, cy, col = 20, y_al+15, 0
    for al in alertas:
        img_al = get_img(MAPA_ALERTAS.get(al))
        if img_al:
            if col == 4: cx, cy, col = 20, cy+50, 0
            pdf.set_xy(cx-5, cy)
            pdf.set_font("Arial", "B", 8)
            pdf.multi_cell(40, 3, txt=str(al).upper(), align='C')
            pdf.image(img_al, x=cx, y=pdf.get_y()+2, w=22)
            cx += 45
            col += 1

    # --- PÁGINA 2: BRAILLE ---
    if hacer_braille:
        pdf.add_page()
        # **CRÍTICO:** Desactivar salto automático para esta página.
        # Esto previene que al dibujar puntos cerca del final, salte y deje la hoja en blanco.
        pdf.set_auto_page_break(auto=False)
        
        titulo_modo = "ESPEJO (PUNZADO REVERSO)" if braille_espejo else "NORMAL (LECTURA FRONTAL)"
        
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, txt=f"GUÍA TÁCTIL - {titulo_modo}", ln=True, align='C')
        pdf.set_font("Arial", "", 10)
        instruccion = "Punzar por el reverso." if braille_espejo else "Lectura visual directa."
        pdf.multi_cell(0, 5, txt=f"INSTRUCCIONES: {instruccion}", align='C')
        pdf.ln(10)
        
        # Construcción texto a convertir
        al_txt = ", ".join(alertas) if alertas else "NINGUNA"
        # Limpieza de texto para el Braille
        texto_braille = f"PAC:{paciente} MED:{med} DOSIS:{dosis} VIA:{via} TOMA:{frec}"
        
        # Dibujar Braille y obtener posición final Y
        y_final = dibujar_braille(pdf, texto_braille, 10, 45, es_espejo=braille_espejo)
        
        # Pie de página Inteligente
        # Si sobra espacio en la hoja actual, ponerlo ahí. Si no, nueva hoja.
        if y_final > 250:
            pdf.add_page()
            pdf.set_auto_page_break(auto=False)
            y_final = 20 # Reset Y para nueva página
            
        pdf.set_y(-25) # Forzar posición al final absoluto
        pdf.set_font("Courier", "", 8)
        pdf.set_text_color(100, 100, 100)
        clean_debug = (texto_braille[:90] + '...') if len(texto_braille) > 90 else texto_braille
        pdf.cell(0, 5, txt=f"Texto Fuente: {clean_debug}", align='C', ln=1)
        
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", "I", 8)
        pdf.cell(0, 5, txt="SMEFI System v7.0", align='C')

    return bytes(pdf.output(dest='S'))

# --- 5. INTERFAZ UI ---
c1, c2 = st.columns([1, 3])
with c2: st.subheader("Datos del Tratamiento")

with st.container(border=True):
    ca, cb = st.columns(2)
    nom = ca.text_input("Nombre Paciente", value="Juan Perez")
    med = ca.text_input("Medicamento", value="AMOXICILINA")
    dos = cb.text_input("Dosis", value="500 mg")
    
    st.markdown("---")
    cc, cd = st.columns(2)
    bra = cc.toggle("Generar Hoja Braille", value=True)
    # Nuevo control para depurar espejo vs normal
    espejo = cd.toggle("Modo Espejo (Para Punzar)", value=True, help="Desactívalo para ver el Braille al derecho y verificar traducción.")

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
        pdf_bytes = generar_pdf(nom, med, dos, v, f, a, bra, espejo)
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
