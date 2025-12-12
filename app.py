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
import zipfile  # <--- NUEVA LIBRERÍA NECESARIA

# --- 1. CONFIGURACIÓN ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, 'assets', 'usp_pictograms')
LOG_FILE = os.path.join(BASE_DIR, 'bitacora_dispensacion.csv')

st.set_page_config(
    page_title="Sistema de Dispensación",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
#   ESTILOS CSS "REACT-LIKE" (ANIMACIONES)
# ==========================================
st.markdown("""
<style>
    :root { --transition-speed: 0.3s; }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
    .block-container { padding-top: 2rem; padding-bottom: 5rem; animation: fadeIn 0.8s ease-out; }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 12px !important;
        border: 1px solid rgba(128, 128, 128, 0.2) !important;
        background-color: var(--secondary-background-color);
        transition: all var(--transition-speed) cubic-bezier(0.25, 0.8, 0.25, 1);
        padding: 20px !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
        border-color: var(--primary-color) !important;
    }
    .stTextInput input, .stSelectbox div[data-baseweb="select"] {
        border-radius: 8px !important;
        border: 1px solid rgba(128, 128, 128, 0.3) !important;
        background-color: transparent !important;
    }
    div.stButton > button {
        border-radius: 8px; font-weight: 600; letter-spacing: 0.5px;
        transition: all 0.2s ease-in-out; box-shadow: 0 2px 5px rgba(0,0,0,0.05); border: none;
    }
    div.stButton > button:hover { transform: scale(1.02); box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
    h1, h2, h3 { font-family: 'Segoe UI', sans-serif; color: var(--text-color); }
    .footer-clean { margin-top: 50px; padding-top: 20px; border-top: 1px solid rgba(128,128,128,0.2); text-align: center; font-size: 0.8rem; opacity: 0.7; }
</style>
""", unsafe_allow_html=True)

if not os.path.exists(ASSETS_DIR):
    st.error(f"Error Crítico: No existe la carpeta {ASSETS_DIR}. Verifica los assets.")

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
        st.error(f"Error al guardar bitácora: {e}")

# --- 3. GENERADOR QR DE AUDIO ---
def generar_qr_audio(texto_a_leer):
    if len(texto_a_leer) > 250:
        texto_seguro = texto_a_leer[:250] 
    else:
        texto_seguro = texto_a_leer
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

# --- 5. GESTIÓN DE RECURSOS Y DATOS ---
def get_img(name):
    if not name: return None
    target = name.lower()
    for f in os.listdir(ASSETS_DIR):
        if f.lower() == target: return os.path.join(ASSETS_DIR, f)
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
    "No tomar de noche": "49.GIF", "NO con leche": "23.GIF", "Cada 8 horas": "16.GIF", "Cada 6 horas": "15.GIF"
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

# --- LISTA PRECARGADA DE EJEMPLO (AMPLIABLE A 200) ---
MEDICAMENTOS_TOP_COLOMBIA = [
    {"med": "Acetaminofén 500mg", "dosis": "1 tableta", "via": "Vía Oral (Tragar)", "frec": "Cada 6 horas", "alertas": ["No alcohol", "Leer etiqueta"]},
    {"med": "Losartán 50mg", "dosis": "1 tableta", "via": "Vía Oral (Tragar)", "frec": "Mañana (AM)", "alertas": ["No embarazo", "Llamar al doctor"]},
    {"med": "Amoxicilina 500mg", "dosis": "1 cápsula", "via": "Vía Oral (Tragar)", "frec": "Cada 8 horas", "alertas": ["Completar tratamiento", "No alcohol"]},
    {"med": "Omeprazol 20mg", "dosis": "1 cápsula", "via": "Vía Oral (Tragar)", "frec": "Estómago vacío", "alertas": ["Mañana (AM)"]},
    {"med": "Ibuprofeno 400mg", "dosis": "1 tableta", "via": "Vía Oral (Tragar)", "frec": "Con alimentos", "alertas": ["No alcohol", "Leer etiqueta"]},
    {"med": "Salbutamol Inhalador", "dosis": "2 Puffs", "via": "Inhalador", "frec": "Cada 6 horas", "alertas": ["Agitar vigorosamente", "Lavarse las manos"]},
    {"med": "Metformina 850mg", "dosis": "1 tableta", "via": "Vía Oral (Tragar)", "frec": "Con alimentos", "alertas": ["No alcohol"]},
    {"med": "Amlodipino 5mg", "dosis": "1 tableta", "via": "Vía Oral (Tragar)", "frec": "Mañana (AM)", "alertas": ["No conducir (Mareo)"]},
    {"med": "Atorvastatina 20mg", "dosis": "1 tableta", "via": "Vía Oral (Tragar)", "frec": "Noche", "alertas": ["No alcohol", "No embarazo"]},
    {"med": "Loratadina 10mg", "dosis": "1 tableta", "via": "Vía Oral (Tragar)", "frec": "Noche", "alertas": ["Causa somnolencia"]},
    # ... Aquí puedes seguir añadiendo hasta llegar a 200 ...
]

# --- 6. GENERADOR PDF (CORE) ---
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
    if alertas:
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

# --- FUNCIÓN NUEVA: GENERAR ZIP MASIVO ---
def generar_pack_masivo(profesional, hacer_braille, espejo, hacer_qr):
    mem_zip = io.BytesIO()
    
    with zipfile.ZipFile(mem_zip, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        progress_bar = st.progress(0)
        total = len(MEDICAMENTOS_TOP_COLOMBIA)
        
        for i, item in enumerate(MEDICAMENTOS_TOP_COLOMBIA):
            pdf_bytes = generar_pdf(
                paciente="GENERALIZADO", # Nombre genérico
                med=item['med'],
                dosis=item['dosis'],
                via=item['via'],
                frec=item['frec'],
                alertas=item.get('alertas', []),
                hacer_braille=hacer_braille,
                espejo=espejo,
                hacer_qr=hacer_qr,
                profesional=profesional
            )
            # Limpiar nombre de archivo
            safe_name = "".join([c for c in item['med'] if c.isalnum() or c in (' ', '-', '_')]).strip()
            zf.writestr(f"{safe_name}.pdf", pdf_bytes)
            progress_bar.progress((i + 1) / total)
            
    mem_zip.seek(0)
    return mem_zip.getvalue()

# ==========================================
# --- 7. INTERFAZ UI (LAYOUT REACT) ---
# ==========================================

# Encabezado Minimalista
st.markdown("<h1>Sistema de Dispensación Inclusiva</h1>", unsafe_allow_html=True)
st.markdown("<p style='opacity:0.6; margin-bottom: 30px;'>Gestión Farmacéutica Accesible • Colombia</p>", unsafe_allow_html=True)

# Tarjeta Principal: Configuración Global y Profesional
with st.container(border=True):
    col_adm1, col_adm2 = st.columns(2)
    profesional_resp = col_adm1.text_input("Profesional Responsable", placeholder="Dr. / Q.F. Nombre Apellido")
    
    # Configuración de Salida Global
    col_adm2.markdown("**Configuración de Salida**")
    c_cfg1, c_cfg2, c_cfg3 = col_adm2.columns(3)
    bra = c_cfg1.toggle("Guía Braille", value=True)
    espejo = c_cfg2.toggle("Modo Espejo", value=True)
    qr_act = c_cfg3.toggle("QR de Audio", value=True)

st.markdown("---")

# --- PESTAÑAS PARA MODOS DE TRABAJO ---
tab1, tab2 = st.tabs(["💊 Prescripción Individual", "📦 Generación Masiva (Top 200)"])

# === PESTAÑA 1: INDIVIDUAL ===
with tab1:
    col_main_1, col_main_2 = st.columns([1, 2], gap="medium")
    
    with col_main_1:
        with st.container(border=True):
            nom = st.text_input("Nombre del Paciente", placeholder="Nombre del paciente")
            
    with col_main_2:
        with st.container(border=True):
            st.markdown("### Datos del Medicamento")
            c_med1, c_med2 = st.columns(2)
            med = c_med1.text_input("Medicamento", placeholder="Nombre del medicamento")
            dos = c_med2.text_input("Dosis", placeholder="Dosis del medicamento")

            st.markdown("---")
            c_sel1, c_sel2 = st.columns(2)
            v = c_sel1.selectbox("Vía de Administración", list(MAPA_VIA.keys()))
            f = c_sel2.selectbox("Frecuencia", list(MAPA_FRECUENCIA.keys()))
            
            # Micro-visualización
            c_img1, c_img2 = st.columns(2)
            icon_via = get_img(MAPA_VIA.get(v))
            if icon_via: c_img1.image(icon_via, width=50)
            icon_frec = get_img(MAPA_FRECUENCIA.get(f))
            if icon_frec: c_img2.image(icon_frec, width=50)

    # Sección Alertas
    with st.container(border=True):
        st.markdown("### Seguridad del Paciente")
        a = st.multiselect("Seleccione precauciones:", list(MAPA_ALERTAS.keys()))
        if a:
            st.write("")
            cols_alert = st.columns(8)
            for i, al in enumerate(a):
                im = get_img(MAPA_ALERTAS.get(al))
                if im: cols_alert[i%8].image(im, width=40)

    # Footer Tab 1
    st.markdown("<br>", unsafe_allow_html=True)
    c_legal, c_action = st.columns([2, 1])
    with c_legal:
        st.caption("Al generar, confirma que los datos corresponden a la orden médica.")
    with c_action:
        if st.button("GENERAR PDF INDIVIDUAL", type="primary"):
            if not profesional_resp or not nom:
                st.error("Falta Profesional o Paciente")
            else:
                with st.spinner("Creando PDF..."):
                    try:
                        pdf_bytes = generar_pdf(nom, med, dos, v, f, a, bra, espejo, qr_act, profesional_resp)
                        registrar_auditoria(profesional_resp, nom, med, dos)
                        file_id = int(time.time())
                        st.download_button(
                            label="DESCARGAR PDF",
                            data=pdf_bytes,
                            file_name=f"Guia_{med}_{file_id}.pdf",
                            mime="application/pdf"
                        )
                        st.success("¡Hecho!")
                    except Exception as e:
                        st.error(f"Error: {e}")

# === PESTAÑA 2: MASIVO ===
with tab2:
    st.info("💡 Este módulo genera automáticamente un archivo .ZIP con las fichas de los medicamentos más comunes en Colombia. El nombre del paciente se ocultará (GENERALIZADO).")
    
    st.markdown(f"**Medicamentos cargados en base de datos:** {len(MEDICAMENTOS_TOP_COLOMBIA)} items")
    
    with st.expander("Ver lista de medicamentos cargados"):
        st.json(MEDICAMENTOS_TOP_COLOMBIA)
        
    st.markdown("### Generar Pack")
    if st.button("GENERAR PACK COMPLETO (.ZIP)", type="primary", use_container_width=True):
        if not profesional_resp:
            st.error("Por favor ingrese el nombre del Profesional Responsable arriba.")
        else:
            with st.spinner("Procesando lote de medicamentos... esto puede tomar unos momentos"):
                try:
                    zip_bytes = generar_pack_masivo(profesional_resp, bra, espejo, qr_act)
                    st.success("¡Lote generado exitosamente!")
                    
                    ahora_str = datetime.now().strftime("%Y%m%d_%H%M")
                    st.download_button(
                        label="📥 DESCARGAR PACK COMPLETOS (ZIP)",
                        data=zip_bytes,
                        file_name=f"Pack_Medicamentos_Col_{ahora_str}.zip",
                        mime="application/zip",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"Error generando el masivo: {e}")

st.markdown('<div class="footer-clean">Sistema de Dispensación Inclusiva v11.3 (Módulo Masivo)</div>', unsafe_allow_html=True)
