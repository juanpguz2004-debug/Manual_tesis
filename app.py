import streamlit as st
from fpdf import FPDF
import os
import unicodedata
import time
import pybraille  # Asegúrate de tener esto en requirements.txt

# --- 1. CONFIGURACIÓN ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, 'assets', 'usp_pictograms')

st.set_page_config(page_title="SMEFI Pro", page_icon="💊", layout="wide")
st.title("🖨️ Sistema de Dispensación Inclusiva (SMEFI)")
st.markdown("**Versión 7.5 (Library Edition):** Integración PyBraille + Renderizado Vectorial.")

if not os.path.exists(ASSETS_DIR):
    st.error(f"❌ Error Crítico: No existe la carpeta {ASSETS_DIR}. Verifica los assets.")

# --- 2. MOTOR BRAILLE (LIBRARY WRAPPER) ---
class BrailleRenderer:
    """
    Motor híbrido: Usa pybraille para la traducción lógica,
    pero dibuja vectorialmente usando Bitmasks para no depender de fuentes .ttf
    """
    
    @staticmethod
    def texto_a_unicode(texto):
        """
        Usa la librería pybraille para convertir texto normal a String Braille Unicode.
        Ejemplo: "Hola" -> "⠓⠕⠇⠁"
        """
        # Pre-procesamiento para asegurar que pybraille reciba caracteres limpios
        texto_limpio = unicodedata.normalize('NFC', str(texto)).lower()
        
        # Corrección manual de la 'ñ' si la librería no la soporta nativamente (común en libs inglesas)
        # La ñ en español suele ser puntos 1-2-4-5-6 (⠻)
        texto_tratado = ""
        for char in texto_limpio:
            if char == 'ñ':
                texto_tratado += "⠻" 
            elif char == 'á': texto_tratado += "⠷"
            elif char == 'é': texto_tratado += "⠮"
            elif char == 'í': texto_tratado += "⠌"
            elif char == 'ó': texto_tratado += "⠬"
            elif char == 'ú': texto_tratado += "⠾"
            elif char == 'ü': texto_tratado += "⠳"
            else:
                try:
                    # Intentamos convertir con la librería
                    texto_tratado += pybraille.convert(char)
                except:
                    # Si falla (caracter raro), ponemos un espacio
                    texto_tratado += " "
        
        return texto_tratado

    @staticmethod
    def dibujar_en_pdf(pdf, braille_unicode, x_start, y_start, espejo=False):
        """
        Dibuja los puntos basándose en el código Unicode del caracter.
        Unicode Braille va de 0x2800 (vacío) a 0x28FF.
        Los bits indican los puntos:
        Bit 0 = Punto 1 | Bit 3 = Punto 4
        Bit 1 = Punto 2 | Bit 4 = Punto 5
        Bit 2 = Punto 3 | Bit 5 = Punto 6
        """
        # Configuración Física
        scale = 1.2
        r = 0.55 * scale 
        spacing_dot = 2.5 * scale
        spacing_char = 6.5 * scale
        spacing_line = 11.0 * scale
        margin_right = 190
        
        cur_x, cur_y = x_start, y_start
        
        for char in braille_unicode:
            # Detectar salto de línea
            if cur_x + spacing_char > margin_right:
                cur_x = x_start
                cur_y += spacing_line
                if cur_y > 260: break 

            # Obtener valor del caracter (ej: 0x2801) y restar base 0x2800 para tener los bits
            codepoint = ord(char)
            if not (0x2800 <= codepoint <= 0x28FF):
                # No es braille, saltar
                continue
                
            bits = codepoint - 0x2800
            
            # Definir posiciones físicas
            # Columna izquierda (1,2,3) y derecha (4,5,6)
            pos_1 = (cur_x, cur_y)
            pos_2 = (cur_x, cur_y + spacing_dot)
            pos_3 = (cur_x, cur_y + spacing_dot * 2)
            pos_4 = (cur_x + spacing_dot, cur_y)
            pos_5 = (cur_x + spacing_dot, cur_y + spacing_dot)
            pos_6 = (cur_x + spacing_dot, cur_y + spacing_dot * 2)
            
            puntos_activos = []
            
            # Logica de Espejo (Cruzar columnas)
            if espejo:
                # Si es espejo:
                # Bit 0 (Punto 1) se dibuja en Pos 4
                if bits & 0x01: puntos_activos.append(pos_4) # 1 -> 4
                if bits & 0x02: puntos_activos.append(pos_5) # 2 -> 5
                if bits & 0x04: puntos_activos.append(pos_6) # 3 -> 6
                if bits & 0x08: puntos_activos.append(pos_1) # 4 -> 1
                if bits & 0x10: puntos_activos.append(pos_2) # 5 -> 2
                if bits & 0x20: puntos_activos.append(pos_3) # 6 -> 3
            else:
                # Normal
                if bits & 0x01: puntos_activos.append(pos_1)
                if bits & 0x02: puntos_activos.append(pos_2)
                if bits & 0x04: puntos_activos.append(pos_3)
                if bits & 0x08: puntos_activos.append(pos_4)
                if bits & 0x10: puntos_activos.append(pos_5)
                if bits & 0x20: puntos_activos.append(pos_6)

            # Dibujar Guías (Sombra)
            pdf.set_fill_color(245, 245, 245) # Gris muy claro
            for p_coord in [pos_1, pos_2, pos_3, pos_4, pos_5, pos_6]:
                pdf.circle(p_coord[0], p_coord[1], r, 'F')

            # Dibujar Puntos (Negro)
            pdf.set_fill_color(0, 0, 0)
            for p_coord in puntos_activos:
                pdf.circle(p_coord[0], p_coord[1], r, 'F')
            
            cur_x += spacing_char
            
        return cur_y

# --- 3. GESTIÓN DE RECURSOS ---
def get_img(name):
    if not name: return None
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
def generar_pdf(paciente, med, dosis, via, frec, alertas, hacer_braille, espejo):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15) 
    
    # --- PÁGINA 1: VISUAL ---
    pdf.add_page()
    pdf.set_font("Arial", "B", 24)
    pdf.cell(0, 15, txt=f"{str(med).upper()}", ln=True, align='C')
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, txt=f"PACIENTE: {str(paciente).upper()} | DOSIS: {str(dosis).upper()}", ln=True, align='C')
    pdf.line(10, 35, 200, 35)
    
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
        pdf.set_auto_page_break(auto=False) # CONTROL MANUAL DE PÁGINA
        
        modo_txt = "MODO ESPEJO (PUNZAR)" if espejo else "MODO LECTURA (FRONTAL)"
        
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, txt=f"GUÍA TÁCTIL - {modo_txt}", ln=True, align='C')
        pdf.set_font("Arial", "", 10)
        pdf.multi_cell(0, 5, txt="INSTRUCCIONES: Punzar puntos negros por el reverso.", align='C')
        pdf.ln(10)
        
        # 1. Obtener texto plano
        texto_plano = f"PAC:{paciente} MED:{med} DOSIS:{dosis} VIA:{via} TOMA:{frec}"
        
        # 2. Convertir a Unicode Braille usando la librería + Fixes
        braille_unicode = BrailleRenderer.texto_a_unicode(texto_plano)
        
        # 3. Dibujar vectorialmente
        y_final = BrailleRenderer.dibujar_en_pdf(pdf, braille_unicode, 10, 45, espejo=espejo)
        
        # Pie de página seguro
        if y_final > 250:
            pdf.add_page()
            pdf.set_auto_page_break(auto=False)
            
        pdf.set_y(-25)
        pdf.set_font("Courier", "", 8)
        pdf.set_text_color(120, 120, 120)
        clean_debug = (texto_plano[:85] + '...') if len(texto_plano) > 85 else texto_plano
        pdf.cell(0, 5, txt=f"Contenido: {clean_debug}", align='C', ln=1)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", "I", 8)
        pdf.cell(0, 5, txt="SMEFI System v7.5 - Powered by PyBraille", align='C')

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
    espejo = cd.toggle("Modo Espejo (Para Punzar)", value=True, help="Actívalo para invertir los puntos horizontalmente (para punzones). Desactívalo para leer en pantalla.")

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
