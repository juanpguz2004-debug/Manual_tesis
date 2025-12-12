import streamlit as st
from fpdf import FPDF
import os
import unicodedata
import time
import qrcode
import urllib.parse
from datetime import datetime # Necesario para fecha y hora

# --- 1. CONFIGURACIÓN ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, 'assets', 'usp_pictograms')

st.set_page_config(page_title="SMEFI Hospitalario", page_icon="🏥", layout="wide")
st.title("🏥 SMEFI - Sistema de Dispensación Inclusiva")
st.markdown("**Versión 13.0:** Trazabilidad, Disclaimer Legal y QR Anónimo.")

if not os.path.exists(ASSETS_DIR):
    st.error(f"❌ Error Crítico: No existe la carpeta {ASSETS_DIR}. Verifica los assets.")

# --- 2. GENERADOR QR (ANONIMIZADO) ---
def generar_qr_audio(med, dosis, via, alertas):
    """
    Genera QR de Audio SIN DATOS PERSONALES (PII).
    Solo contiene la información del tratamiento, eliminando el nombre del paciente.
    """
    # Construcción del texto seguro
    al_str = ", ".join(alertas) if alertas else "Ninguna"
    
    # Texto redactado para ser leído por la IA (Sin variable {paciente})
    texto_seguro = f"Atención paciente. Su tratamiento es: {med}. La dosis es: {dosis}. Administrar por: {via}. Precauciones: {al_str}."
    
    # Límite de seguridad para URL
    texto_url = texto_seguro[:250]
    
    # API Google TTS (Client 'gtx' para mayor compatibilidad)
    base_url = "https://translate.google.com/translate_tts?ie=UTF-8&client=gtx&tl=es&q="
    url_final = base_url + urllib.parse.quote(texto_url)
    
    qr = qrcode.QRCode(box_size=10, border=2)
    qr.add_data(url_final)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    qr_path = os.path.join(BASE_DIR, "temp_safe_qr.png")
    img.save(qr_path)
    return qr_path

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
        ',': 0x02, ';': 0x06, ':': 0x12, '.': 0x32, '!': 0x16, 
        '(': 0x36, ')': 0x36, '?': 0x22, '-': 0x24, '/': 0x0C, ' ': 0x00 
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
                coords_norm = {1:(cur_x,cur_y), 4:(cur_x+s_dot,cur_y), 2:(cur_x,cur_y+s_dot), 5:(cur_x+s_dot,cur_y+s_dot), 3:(cur_x,cur_y+s_dot*2), 6:(cur_x+s_dot,cur_y+s_dot*2)}
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

# --- DATOS SISTEMA ---
MAPA_VIA = {
    "Vía Oral (Tragar)": "01.GIF", "Masticar": "43.GIF", "Sublingual": "46.GIF",
    "Disolver en agua": "45.GIF", "Inhalador": "71.GIF", "Inyección": "61.GIF",
    "Gotas Ojos": "29.GIF", "Gotas Oído": "31.GIF", "Uso Rectal": "27.GIF"
}
MAPA_FRECUENCIA = {
    "Mañana (AM)": "67.GIF", "Noche": "22.GIF",
    "2 veces al día": "04.GIF", "3 veces al día": "16.GIF", "4 veces al día": "15.GIF",
    "Cada 8 horas": "16.GIF", "Con alimentos": "18.GIF", "Estómago vacío": "19.GIF"
}
MAPA_ALERTAS = {
    "Venenoso / Tóxico": "81.GIF", "No alcohol": "40.GIF", "No conducir (Sueño)": "50.GIF", 
    "No triturar": "33.GIF", "Refrigerar": "20.GIF", "No embarazo": "34.GIF", 
    "No lactancia": "36.GIF", "Mantener alejado niños": "17.GIF"
}

# --- 5. GENERADOR PDF ---
def generar_pdf(paciente, farmaceutico, med, dosis, via, frec, alertas, hacer_braille, espejo, hacer_qr):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # --- PÁGINA 1: VISUAL ---
    pdf.add_page()
    
    # 1. TRAZABILIDAD (HEADER)
    # Fecha y Hora exacta para auditoría clínica
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M") 
    pdf.set_font("Arial", "", 8)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 4, txt=f"Institución de Salud Nivel 3 | Dispensación Inclusiva", ln=True, align='R')
    pdf.cell(0, 4, txt=f"Resp: {farmaceutico.upper()} | Registro: {timestamp}", ln=True, align='R')
    pdf.set_text_color(0, 0, 0)
    
    # Título y Datos
    pdf.ln(5)
    pdf.set_font("Arial", "B", 24)
    # Convertimos a string por seguridad en el input abierto
    pdf.cell(0, 15, txt=f"{str(med).upper()}", ln=True, align='C')
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, txt=f"PACIENTE: {str(paciente).upper()} | DOSIS: {str(dosis).upper()}", ln=True, align='C')
    
    # 2. ADVERTENCIA VISUAL DE DOSIS (Requerimiento Seguridad)
    pdf.set_font("Arial", "B", 8)
    pdf.set_text_color(200, 0, 0) # Rojo Alerta
    pdf.cell(0, 5, txt="⚠ VERIFICAR DOSIS Y MEDICAMENTO ANTES DE ENTREGAR", ln=True, align='C')
    pdf.set_text_color(0, 0, 0)
    
    pdf.line(10, 50, 200, 50)
    
    # Bloques de Iconos
    y_bloque = 65
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

    # Alertas
    y_al = 135
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

    # 3. DISCLAIMER LEGAL (FOOTER PÁGINA 1)
    pdf.set_y(-25) # Subimos un poco para dar espacio
    pdf.set_font("Arial", "I", 7)
    pdf.multi_cell(0, 3, txt="AVISO LEGAL: Este documento es una herramienta de apoyo visual/táctil para la adherencia al tratamiento. No sustituye la receta médica oficial ni el criterio profesional. El farmacéutico es responsable de verificar que los datos ingresados coincidan con la prescripción médica original.", align='C')

    # --- QR AUDIO ANONIMIZADO ---
    if hacer_qr:
        # Enviamos datos, pero el QR NO contendrá el nombre del paciente
        qr_file = generar_qr_audio(med, dosis, via, alertas)
        
        pdf.set_auto_page_break(auto=False)
        pdf.set_xy(150, 240) 
        pdf.image(qr_file, w=40)
        pdf.set_xy(150, 280)
        pdf.set_font("Arial", "B", 8)
        pdf.cell(40, 5, "AUDIO GUÍA", align='C')
        pdf.set_auto_page_break(auto=True, margin=15)

    # --- PÁGINA 2: BRAILLE ---
    if hacer_braille:
        pdf.add_page()
        pdf.set_auto_page_break(False) 
        
        modo = "ESPEJO (PUNZADO)" if espejo else "NORMAL (VISUAL)"
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, txt=f"GUÍA TÁCTIL - {modo}", ln=True, align='C')
        pdf.set_font("Arial", "", 10)
        instrucc = "Punzar por el reverso." if espejo else "Lectura visual."
        pdf.multi_cell(0, 5, txt=f"INSTRUCCIONES: {instrucc}", align='C')
        pdf.ln(5)
        
        al_str_br = ", ".join(alertas) if alertas else "NINGUNA"
        texto_tecnico = f"PAC:{paciente} MED:{med} DOSIS:{dosis} VIA:{via} TOMA:{frec} ALERT:{al_str_br}"
        
        last_y = BrailleLib.render_on_pdf(pdf, texto_tecnico, 10, 45, espejo)
        
        # Pie de página braille
        if last_y > 250:
            pdf.add_page()
            pdf.set_auto_page_break(False)
            
        pdf.set_y(-20)
        pdf.set_font("Courier", "", 8)
        pdf.set_text_color(128, 128, 128)
        debug_txt = (texto_tecnico[:85] + '...') if len(texto_tecnico) > 85 else texto_tecnico
        pdf.cell(0, 5, txt=f"REF: {debug_txt}", align='C', ln=1)
        
        # Trazabilidad en página 2 también
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", "I", 6)
        pdf.cell(0, 5, txt=f"Generado por: {farmaceutico} | {timestamp}", align='C')

    return bytes(pdf.output(dest='S'))

# --- 6. INTERFAZ UI ---
c1, c2 = st.columns([1, 3])
with c1:
    st.image("https://cdn-icons-png.flaticon.com/512/3063/3063823.png", width=100)
with c2: 
    st.subheader("Módulo de Farmacia - Dispensación")

with st.container(border=True):
    col_auth, col_data = st.columns([1, 3])
    # Nuevo campo: Responsable
    farmaceutico = col_auth.text_input("Farmacéutico Responsable", "Lic. Turno Mañana")
    
    nom = col_data.text_input("Nombre Paciente", "Juan Perez")
    
    # 3. INPUT ABIERTO CON ADVERTENCIA (Requerimiento)
    c_med, c_dos = col_data.columns(2)
    
    # Text input libre para el medicamento (Flexibilidad)
    med = c_med.text_input("Medicamento (Nombre Genérico)", "AMOXICILINA")
    # Advertencia visual en pantalla
    if med:
        c_med.caption("⚠ Verifique ortografía contra receta médica.")
        
    dos = c_dos.text_input("Dosis / Concentración", "500 mg")
    if dos:
        c_dos.caption("⚠ Cuidado: Verificar Dosis Pediátrica/Adulta.")
    
    st.markdown("---")
    cc, cd, ce = st.columns(3)
    bra = cc.toggle("Hoja Braille", value=True)
    espejo = cd.toggle("Modo Espejo", value=True)
    qr_act = ce.toggle("Incluir QR Audio", value=True)

c3, c4 = st.columns(2)
with c3:
    st.info("ℹ️ Posología")
    v = st.selectbox("Vía", list(MAPA_VIA.keys()))
    f = st.selectbox("Frecuencia", list(MAPA_FRECUENCIA.keys()))
    
    cp = st.columns(2)
    im1 = get_img(MAPA_VIA.get(v))
    if im1: cp[0].image(im1, width=60)
    im2 = get_img(MAPA_FRECUENCIA.get(f))
    if im2: cp[1].image(im2, width=60)

with c4:
    st.warning("⚠️ Farmacovigilancia (Alertas)")
    a = st.multiselect("Precauciones", list(MAPA_ALERTAS.keys()))
    if a:
        cols = st.columns(4)
        for i, al in enumerate(a):
            im3 = get_img(MAPA_ALERTAS.get(al))
            if im3: cols[i%4].image(im3, width=40)

st.write("")
# Botón de generación con disclaimer visual
st.caption("Al generar este documento, el profesional confirma que ha validado los datos con la prescripción médica.")
if st.button("🖨️ GENERAR DOCUMENTO CLÍNICO", type="primary", use_container_width=True):
    try:
        # Pasamos el nuevo parámetro 'farmaceutico' a la función
        pdf_bytes = generar_pdf(nom, farmaceutico, med, dos, v, f, a, bra, espejo, qr_act)
        st.success("✅ Documento generado exitosamente.")
        
        file_id = int(time.time())
        st.download_button(
            label="📥 DESCARGAR PDF",
            data=pdf_bytes,
            file_name=f"SMEFI_{med}_{file_id}.pdf",
            mime="application/pdf"
        )
    except Exception as e:
        st.error(f"Error del sistema: {e}")
