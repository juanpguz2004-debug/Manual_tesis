import streamlit as st
from fpdf import FPDF
import os
import unicodedata
import time
import qrcode
import urllib.parse
from datetime import datetime, timedelta
import io
import tempfile
import csv

# --- 1. CONFIGURACIÓN ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, 'assets', 'usp_pictograms')
LOG_FILE = os.path.join(BASE_DIR, 'bitacora_dispensacion.csv')

st.set_page_config(page_title="Sistema de Dispensación Inclusiva", page_icon="💊", layout="wide")

# ==========================================
#      ESTILOS CSS Y ANIMACIONES (NUEVO)
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap');

    /* Fondo general y tipografía */
    .stApp {
        background-color: #f4f8fb;
        font-family: 'Poppins', sans-serif;
    }

    /* Animación de entrada suave */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .main-container {
        animation: fadeIn 0.8s ease-out;
    }

    /* Títulos */
    h1 {
        color: #2c3e50;
        font-weight: 600;
        text-align: center;
        padding-bottom: 10px;
    }
    
    h3 {
        color: #34495e;
        border-bottom: 2px solid #3498db;
        padding-bottom: 5px;
        margin-top: 20px;
    }

    /* Estilo de Tarjetas (Contenedores) */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: white;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        border: 1px solid #e1e8ed;
        padding: 20px;
        transition: transform 0.2s;
    }
    
    div[data-testid="stVerticalBlockBorderWrapper"]:hover {
        border-color: #3498db;
    }

    /* Inputs y Selects */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] {
        border-radius: 8px;
        border: 1px solid #ced4da;
    }

    /* Botón Principal */
    div.stButton > button {
        background: linear-gradient(90deg, #3498db 0%, #2980b9 100%);
        color: white;
        border: none;
        padding: 12px 24px;
        border-radius: 10px;
        font-size: 16px;
        font-weight: 600;
        box-shadow: 0 4px 6px rgba(52, 152, 219, 0.3);
        transition: all 0.3s ease;
        width: 100%;
    }

    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(52, 152, 219, 0.4);
        background: linear-gradient(90deg, #2980b9 0%, #3498db 100%);
    }

    /* Alertas y tags */
    .stMultiSelect span {
        background-color: #e8f4f8;
        color: #2980b9;
        border-radius: 15px;
    }
    
    /* Footer discreto */
    .footer-legal {
        font-size: 0.8rem;
        color: #95a5a6;
        text-align: center;
        margin-top: 30px;
        border-top: 1px solid #eee;
        padding-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

if not os.path.exists(ASSETS_DIR):
    st.error(f"❌ Error Crítico: No existe la carpeta {ASSETS_DIR}. Verifica los assets.")

# --- 2. LOG DE AUDITORÍA ---
def registrar_auditoria(profesional, paciente, medicamento, dosis):
    existe = os.path.exists(LOG_FILE)
    try:
        with open(LOG_FILE, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not existe:
                writer.writerow(["FECHA_HORA", "PROFESIONAL", "PACIENTE", "MEDICAMENTO", "DOSIS", "ESTADO"])
            ahora = (datetime.utcnow() - timedelta(hours=5)).strftime("%Y-%m-%d %H:%M:%S")
            writer.writerow([ahora, profesional, paciente, medicamento, dosis, "GENERADO"])
    except Exception as e:
        st.error(f"⚠️ Error al guardar bitácora: {e}")

# --- 3. GENERADOR QR DE AUDIO ---
def generar_qr_audio(texto_a_leer):
    if len(texto_a_leer) > 250:
        st.warning("⚠️ ADVERTENCIA: Texto truncado por seguridad del QR.")
    texto_seguro = texto_a_leer[:250] 
    base_url = "https://translate.google.com/translate_tts?ie=UTF-8&client=gtx&tl=es&q="
    url_final = base_url + urllib.parse.quote(texto_seguro)
    qr = qrcode.QRCode(box_size=10, border=2)
    qr.add_data(url_final)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer

# --- 4. BRAILLELIB ---
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

# --- 5. GESTIÓN DE RECURSOS ---
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

# --- 6. GENERADOR PDF ---
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
    pdf.cell(60, 10, txt="FRECUENCIA/INGESTION", align='C', ln=1)
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

    if hacer_qr:
        al_str = ", ".join(alertas) if alertas else "Ninguna"
        texto_audio = f"Hola. Sus indicaciones: {med}. Frecuencia: {frec}. Vía {via}. Alertas: {al_str}."
        qr_buffer = generar_qr_audio(texto_audio)
        pdf.set_auto_page_break(auto=False)
        pdf.set_xy(150, 240) 
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
            tmp_file.write(qr_buffer.getvalue())
            tmp_path = tmp_file.name
        try:
            pdf.image(tmp_path, w=40)
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
        pdf.set_xy(150, 280)
        pdf.set_font("Arial", "B", 8)
        pdf.cell(40, 5, "ESCANEA PARA OÍR", align='C')
        pdf.set_auto_page_break(auto=True, margin=15)

    pdf.set_y(-25)
    pdf.set_font("Arial", "I", 7)
    pdf.set_text_color(100, 100, 100)
    disclaimer = "AVISO LEGAL: Herramienta de apoyo conforme a Ley 1581/2012 (Habeas Data).No sustituye prescripción médica."
    pdf.multi_cell(0, 3, disclaimer, align='L')
    pdf.set_text_color(0, 0, 0)

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
        pdf.cell(0, 5, txt="Sistema braille v11.2", align='C')

    return bytes(pdf.output(dest='S'))

# ==========================================
# --- 7. INTERFAZ UI (REDISEÑADA) ---
# ==========================================

# Contenedor principal con animación de entrada
main_cont = st.container()
with main_cont:
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    
    # Encabezado Centrado
    col_h1, col_h2, col_h3 = st.columns([1,2,1])
    with col_h2:
        st.title("🖨️ Dispensación Inclusiva")
        st.markdown("<div style='text-align: center; color: #7f8c8d; margin-top: -15px;'>Colombia • Accesibilidad • Seguridad</div>", unsafe_allow_html=True)
    
    st.markdown("---")

    # --- BLOQUE 1: DATOS ADMINISTRATIVOS Y CLÍNICOS ---
    c1, c2 = st.columns([1, 2], gap="large")
    
    with c1:
        st.markdown("### 🏥 Admisión")
        with st.container(border=True):
            profesional_resp = st.text_input("👨‍⚕️ Profesional Responsable", placeholder="Dr/a. Nombre Apellido")
            nom = st.text_input("👤 Nombre Paciente", value="Juan Perez")
            
        st.markdown("### ⚙️ Accesibilidad")
        with st.container(border=True):
            bra = st.toggle("📝 Hoja Braille", value=True)
            espejo = st.toggle("🔄 Modo Espejo (Punzar)", value=True, help="Invierte el Braille para punzar manualmente.")
            qr_act = st.toggle("🔊 Incluir QR Audio", value=True, help="Genera código para lectura en voz alta.")

    with c2:
        st.markdown("### 💊 Prescripción")
        with st.container(border=True):
            col_med1, col_med2 = st.columns(2)
            med = col_med1.text_input("Medicamento", value="AMOXICILINA")
            col_med1.caption("Verifique ortografía exacta.")
            
            dos = col_med2.text_input("Dosis / Concentración", value="500 mg")
            col_med2.caption("Ej: 500mg, 1 Tableta.")
            
            st.divider()
            
            # Selectores visuales
            col_sel1, col_sel2 = st.columns(2)
            v = col_sel1.selectbox("Vía de Administración", list(MAPA_VIA.keys()))
            f = col_sel2.selectbox("Frecuencia / Horario", list(MAPA_FRECUENCIA.keys()))
            
            # Previsualización pequeña de iconos
            cp = st.columns(6)
            im1 = get_img(MAPA_VIA.get(v))
            if im1: cp[0].image(im1, width=50)
            im2 = get_img(MAPA_FRECUENCIA.get(f))
            if im2: cp[1].image(im2, width=50)

    # --- BLOQUE 2: SEGURIDAD Y ALERTAS ---
    st.markdown("### ⚠️ Precauciones y Alertas")
    with st.container(border=True):
        a = st.multiselect("Seleccione las etiquetas de precaución aplicables:", list(MAPA_ALERTAS.keys()))
        
        # Galería dinámica de iconos seleccionados
        if a:
            st.markdown("**Previsualización:**")
            cols = st.columns(8)
            for i, al in enumerate(a):
                im3 = get_img(MAPA_ALERTAS.get(al))
                if im3: cols[i%8].image(im3, width=40, caption=al[:10]+"..")

    # --- BLOQUE 3: LEGAL Y ACCIÓN ---
    st.markdown("---")
    
    col_leg1, col_leg2 = st.columns([3, 1])
    with col_leg1:
        st.info("🔒 **Habeas Data (Ley 1581/2012):** Los datos procesados aquí son temporales y se usan estrictamente para la generación de la guía accesible.")
        aceptar_terminos = st.checkbox("✅ Certifico la veracidad de los datos y acepto el tratamiento para la generación del documento.")

    with col_leg2:
        st.write("") # Espaciador
        st.write("")
        btn_generar = st.button("GENERAR GUÍA PDF ✨", type="primary")

    # LÓGICA DE BOTÓN
    if btn_generar:
        if not profesional_resp:
            st.toast("⚠️ Falta el nombre del profesional.", icon="👨‍⚕️")
        elif not aceptar_terminos:
            st.toast("⛔ Debe aceptar los términos legales.", icon="⚖️")
        else:
            with st.spinner("🔄 Procesando Braille, Audio y Gráficos..."):
                try:
                    pdf_bytes = generar_pdf(nom, med, dos, v, f, a, bra, espejo, qr_act, profesional_resp)
                    registrar_auditoria(profesional_resp, nom, med, dos)
                    time.sleep(1) # Pequeña pausa para efecto visual
                    
                    st.toast("✅ ¡Documento generado con éxito!", icon="🎉")
                    st.balloons()
                    
                    file_id = int(time.time())
                    st.download_button(
                        label="📥 DESCARGAR DOCUMENTO PDF",
                        data=pdf_bytes,
                        file_name=f"Guia_{med}_{file_id}.pdf",
                        mime="application/pdf",
                        type="secondary",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"Error técnico: {e}")

    st.markdown('<div class="footer-legal">Desarrollado para cumplimiento de normativa de accesibilidad farmacéutica en Colombia. v11.2</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
