import streamlit as st
from fpdf import FPDF
import os
import unicodedata
import time
import qrcode
import urllib.parse
from datetime import datetime, timedelta
import io  # NUEVO: Para manejo en memoria
import tempfile  # NUEVO: Para archivos temporales seguros

# --- 1. CONFIGURACIÓN ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, 'assets', 'usp_pictograms')

st.set_page_config(page_title="Sistema de Dispensación Inclusiva", page_icon="💊", layout="wide")
st.title("🖨️ Sistema de Dispensación Inclusiva")
st.markdown("**Versión 11.1 (Segura):** Audio QR en RAM y validación de privacidad.")

if not os.path.exists(ASSETS_DIR):
    st.error(f"❌ Error Crítico: No existe la carpeta {ASSETS_DIR}. Verifica los assets.")

# --- 2. GENERADOR QR DE AUDIO (OPTIMIZADO NIVEL 1) ---
def generar_qr_audio(texto_a_leer):
    """
    Genera un QR en memoria RAM.
    Avisa si el texto excede la capacidad segura de la URL.
    """
    # Validación de Seguridad: Aviso de corte de texto
    if len(texto_a_leer) > 250:
        st.warning("⚠️ ADVERTENCIA DE SEGURIDAD: El texto de audio es muy largo (>250 caracteres) y ha sido truncado. Verifique que las indicaciones críticas se escuchen en el QR.")
    
    texto_seguro = texto_a_leer[:250] 
    
    base_url = "https://translate.google.com/translate_tts?ie=UTF-8&client=gtx&tl=es&q="
    url_final = base_url + urllib.parse.quote(texto_seguro)
    
    qr = qrcode.QRCode(box_size=10, border=2)
    qr.add_data(url_final)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    # NUEVO: Manejo en RAM (io.BytesIO) para no escribir en disco duro
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer

# --- 3. BRAILLELIB (Motor Profesional) ---
class BrailleLib:
    UNICODE_MAP = {
        'a': 0x01, 'b': 0x03, 'c': 0x09, 'd': 0x19, 'e': 0x11,
        'f': 0x0B, 'g': 0x1B, 'h': 0x13, 'i': 0x0A, 'j': 0x1A,
        'k': 0x05, 'l': 0x07, 'm': 0x0D, 'n': 0x1D, 'o': 0x15,
        'p': 0x0F, 'q': 0x1F, 'r': 0x17, 's': 0x0E, 't': 0x1E,
        'u': 0x25, 'v': 0x27, 'w': 0x3A, 'x': 0x2D, 'y': 0x3D, 'z': 0x35,
        'á': 0x37, 'é': 0x2E, 'í': 0x0C, 'ó': 0x2C, 'ú': 0x3E, 'ü': 0x33, 'ñ': 0x3B,
        '1': 0x01, '2': 0x03, '3': 0x09, '4': 0x19, '5': 0x11,
        '6': 0x0B, '7': 0x1B, '8': 0x13, '9': 0x0A, '0': 0x1A,
        '(': 0x36, ')': 0x36, '?': 0x22, '-': 0x24, '/': 0x0C, 
        ',': 0x02, ';': 0x06, ':': 0x12, '.': 0x32, '!': 0x16, ' ': 0x00 
    }
    SIGNO_NUMERO = 0x3C
    
    @staticmethod
    def text_to_unicode_braille(texto):
        texto = unicodedata.normalize('NFC', str(texto)).lower()
        resultado = []
        is_number = False
        for char in texto:
            if char.isdigit():
                if not is_number:
                    resultado.append(chr(0x2800 + BrailleLib.SIGNO_NUMERO))
                    is_number = True
                val = BrailleLib.UNICODE_MAP.get(char, 0x00)
                resultado.append(chr(0x2800 + val))
            else:
                if is_number and char not in [',', '.']: is_number = False
                val = BrailleLib.UNICODE_MAP.get(char, 0x00)
                resultado.append(chr(0x2800 + val))
        return "".join(resultado)

    @staticmethod
    def render_on_pdf(pdf, text, x_start, y_start, espejo=True):
        full_braille = BrailleLib.text_to_unicode_braille(text)
        scale, s_dot, s_char, s_line = 1.2, 3.0, 7.8, 13.2
        r = 0.66
        margin_right = 190
        
        max_chars = int((margin_right - x_start) / s_char)
        words = full_braille.split(chr(0x2800))
        lines = []
        current_line = []
        current_len = 0
        for word in words:
            w_len = len(word)
            if current_len + w_len + 1 <= max_chars:
                current_line.append(word)
                current_len += w_len + 1
            else:
                if current_line: lines.append(chr(0x2800).join(current_line))
                current_line = [word]
                current_len = w_len
        if current_line: lines.append(chr(0x2800).join(current_line))
        
        cur_x, cur_y = x_start, y_start
        for line in lines:
            if cur_y > 250: 
                pdf.add_page()
                pdf.set_auto_page_break(False)
                cur_y = 20
                cur_x = x_start

            text_to_draw = line[::-1] if espejo else line
            
            for char in text_to_draw:
                bits = ord(char) - 0x2800
                if bits < 0 or bits > 255: continue 
                
                coords_norm = {
                    1: (cur_x, cur_y),           4: (cur_x + s_dot, cur_y),
                    2: (cur_x, cur_y + s_dot),   5: (cur_x + s_dot, cur_y + s_dot),
                    3: (cur_x, cur_y + s_dot*2), 6: (cur_x + s_dot, cur_y + s_dot*2)
                }
                
                puntos_activos = []
                for i in range(6):
                    punto_num = i + 1
                    if (bits >> i) & 1:
                        p_final = {1:4, 2:5, 3:6, 4:1, 5:2, 6:3}[punto_num] if espejo else punto_num
                        puntos_activos.append(coords_norm[p_final])

                pdf.set_fill_color(240, 240, 240)
                for _, (cx, cy) in coords_norm.items(): pdf.circle(cx, cy, r, 'F')
                pdf.set_fill_color(0, 0, 0)
                for (px, py) in puntos_activos: pdf.circle(px, py, r, 'F')
                
                cur_x += s_char
            cur_x = x_start
            cur_y += s_line
        return cur_y

# --- 4. GESTIÓN DE RECURSOS ---
def get_img(name):
    if not name: return None
    target = name.lower()
    for f in os.listdir(ASSETS_DIR):
        if f.lower() == target: return os.path.join(ASSETS_DIR, f)
    return None

# --- DATOS ---
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

# --- 5. GENERADOR PDF ---
def generar_pdf(paciente, med, dosis, via, frec, alertas, hacer_braille, espejo, hacer_qr, profesional):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # --- PÁGINA 1: VISUAL ---
    pdf.add_page()
    
    ahora_col = datetime.utcnow() - timedelta(hours=5)
    ahora = ahora_col.strftime("%d/%m/%Y %H:%M")
    pdf.set_font("Arial", "", 8)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, txt=f"Emitido: {ahora} | Profesional Resp: {str(profesional).upper()}", ln=True, align='R')
    pdf.set_text_color(0, 0, 0)
    
    pdf.set_font("Arial", "B", 24)
    pdf.cell(0, 15, txt=f"{str(med).upper()}", ln=True, align='C')
    
    pdf.set_font("Arial", "B", 10)
    pdf.set_text_color(220, 0, 0)
    pdf.cell(0, 5, txt="VERIFICAR DOSIS Y MEDICAMENTO ANTES DE ENTREGAR", ln=True, align='C')
    pdf.set_text_color(0, 0, 0)
    
    pdf.ln(2)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, txt=f"PACIENTE: {str(paciente).upper()} | DOSIS: {str(dosis).upper()}", ln=True, align='C')
    pdf.line(10, 45, 200, 45)
    
    y_bloque = 60
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

    y_al = 130
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

    # --- INSERCIÓN DE QR AUDIO (MODIFICADO SEGURO) ---
    if hacer_qr:
        al_str = ", ".join(alertas) if alertas else "Ninguna"
        texto_audio = f"Hola. Sus indicaciones: {med}. Frecuencia: {frec}. Vía {via}. Alertas: {al_str}."
        
        # Obtenemos el buffer de memoria (RAM), no un archivo
        qr_buffer = generar_qr_audio(texto_audio)
        
        pdf.set_auto_page_break(auto=False)
        pdf.set_xy(150, 240) 
        
        # TRUCO SEGURO: FPDF suele requerir un archivo físico. Creamos uno temporal que se borra al salir del bloque 'with'.
        # Esto evita dejar basura en el servidor (temp_audio_qr.png) y cumple la seguridad.
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
            tmp_file.write(qr_buffer.getvalue())
            tmp_path = tmp_file.name
        
        try:
            pdf.image(tmp_path, w=40)
        finally:
            # Borrado inmediato del disco
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

        pdf.set_xy(150, 280)
        pdf.set_font("Arial", "B", 8)
        pdf.cell(40, 5, "ESCANEA PARA OÍR", align='C')
        pdf.set_auto_page_break(auto=True, margin=15)

    pdf.set_y(-25)
    pdf.set_font("Arial", "I", 7)
    pdf.set_text_color(100, 100, 100)
    disclaimer = "AVISO LEGAL: Esta herramienta es un apoyo informativo y no sustituye el consejo médico profesional."
    pdf.multi_cell(0, 3, disclaimer, align='L')
    pdf.set_text_color(0, 0, 0)

    # --- PÁGINA 2: BRAILLE ---
    if hacer_braille:
        pdf.add_page()
        pdf.set_auto_page_break(False) 
        
        modo = "ESPEJO (PUNZADO)" if espejo else "NORMAL (VISUAL)"
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, txt=f"GUÍA TÁCTIL - {modo}", ln=True, align='C')
        pdf.set_font("Arial", "", 10)
        instrucc = "Punzar por el reverso." if espejo else "Lectura visual frontal."
        pdf.multi_cell(0, 5, txt=f"INSTRUCCIONES: {instrucc}", align='C')
        pdf.ln(10)
        
        al_str_br = ", ".join(alertas) if alertas else "NINGUNA"
        texto_tecnico = f"PAC:{paciente} MED:{med} DOSIS:{dosis} VIA:{via} TOMA:{frec} ALERT:{al_str_br}"
        
        last_y = BrailleLib.render_on_pdf(pdf, texto_tecnico, 10, 45, espejo)
        
        if last_y > 250:
            pdf.add_page()
            pdf.set_auto_page_break(False)
            
        pdf.set_y(-25)
        pdf.set_font("Courier", "", 8)
        pdf.set_text_color(128, 128, 128)
        debug_txt = (texto_tecnico[:85] + '...') if len(texto_tecnico) > 85 else texto_tecnico
        pdf.cell(0, 5, txt=f"Contenido: {debug_txt}", align='C', ln=1)
        
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", "I", 8)
        pdf.cell(0, 5, txt="Sistema braille v11.1", align='C')

    return bytes(pdf.output(dest='S'))

# --- 6. INTERFAZ UI ---
c1, c2 = st.columns([1, 3])
with c2: st.subheader("Datos del Tratamiento")

with st.container(border=True):
    profesional_resp = st.text_input("Nombre Profesional Responsable", placeholder="Ej. Dr. Ana Gomez / Farm. Luis Torres")
    
    ca, cb = st.columns(2)
    nom = ca.text_input("Nombre Paciente", value="Juan Perez")
    
    med = ca.text_input("Medicamento", value="AMOXICILINA")
    ca.caption("⚠️ Verifique ortografía exacta del medicamento.")
    
    dos = cb.text_input("Dosis", value="500 mg")
    ca.caption("⚠️ Verifique dosis del medicamento.")
    st.markdown("---")
    cc, cd, ce = st.columns(3)
    bra = cc.toggle("Hoja Braille", value=True)
    espejo = cd.toggle("Modo Espejo", value=True, help="Invierte el Braille para punzar.")
    qr_act = ce.toggle("Incluir QR Audio", value=True, help="Genera un código QR que lee el texto al escanearlo.")

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

# NUEVO: Aviso de Privacidad (Nivel 2)
st.markdown("---")
st.caption("🔒 **Aviso de Privacidad:**")
aceptar_terminos = st.checkbox("Entiendo que esta herramienta utiliza servicios de terceros (Google TTS) para generar el audio del QR y que no se deben incluir diagnósticos sensibles en el texto.")

st.write("")
if st.button("GENERAR GUÍA PDF", type="primary", use_container_width=True):
    if not profesional_resp:
        st.error("⚠️ Debe indicar el nombre del profesional responsable.")
    elif not aceptar_terminos:
        st.error("⛔ Debe aceptar el aviso de privacidad para continuar.")
    else:
        try:
            pdf_bytes = generar_pdf(nom, med, dos, v, f, a, bra, espejo, qr_act, profesional_resp)
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
