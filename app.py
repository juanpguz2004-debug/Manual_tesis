import streamlit as st
from fpdf import FPDF
import os
import unicodedata
import pybraille  # <--- NUEVA LIBRERÍA

# --- 1. CONFIGURACIÓN ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, 'assets', 'usp_pictograms')

st.set_page_config(page_title="SMEFI Final", page_icon="💊", layout="wide")
st.title("🖨️ Sistema de Dispensación Inclusiva (SMEFI)")
st.markdown("**Versión Final:** Braille por Librería (pybraille) + Espejo Automático.")

if not os.path.exists(ASSETS_DIR):
    st.error(f"❌ Error: Falta la carpeta {ASSETS_DIR}")

# --- 2. MOTOR DE RENDERIZADO BRAILLE (LIBRERÍA + MATEMÁTICA) ---
def dibujar_braille_desde_libreria(pdf, texto_humano, x_start, y_start):
    """
    1. Usa pybraille para traducir (Texto -> Unicode Braille).
    2. Decodifica los puntos del Unicode.
    3. Aplica espejo y dibuja.
    """
    # 1. TRADUCCIÓN CON LIBRERÍA
    # Convertimos a minúsculas porque pybraille maneja mejor grado 1 así
    texto_traducido = pybraille.convert(texto_humano.lower())
    
    # Configuración Gráfica
    scale = 1.1
    dot_r = 0.55 * scale
    w_dot = 2.5 * scale
    h_dot = 2.5 * scale
    w_char = 6.2 * scale
    h_line = 11.0 * scale
    margin_right = 190
    
    cur_x, cur_y = x_start, y_start
    
    # Mapeo de Espejo para punzado reverso (1<->4, 2<->5, 3<->6)
    mirror_map = {1:4, 2:5, 3:6, 4:1, 5:2, 6:3}

    for char in texto_traducido:
        # Salto de línea automático
        if cur_x + w_char > margin_right:
            cur_x = x_start
            cur_y += h_line
            if cur_y > 270: break # Margen inferior seguridad

        # 2. DECODIFICACIÓN MATEMÁTICA DEL UNICODE
        # Los caracteres Braille van del U+2800 (vacío) al U+28FF
        # El bit 0 es punto 1, bit 1 es punto 2, etc.
        codepoint = ord(char)
        if not (0x2800 <= codepoint <= 0x28FF):
            # Si no es braille (ej. espacio normal), saltamos
            cur_x += w_char
            continue
            
        base = codepoint - 0x2800
        puntos_activos = []
        if base & 1: puntos_activos.append(1)
        if base & 2: puntos_activos.append(2)
        if base & 4: puntos_activos.append(3)
        if base & 8: puntos_activos.append(4)
        if base & 16: puntos_activos.append(5)
        if base & 32: puntos_activos.append(6)
        
        # 3. ESPEJO Y DIBUJO
        puntos_espejo = [mirror_map[p] for p in puntos_activos]
        
        # Guía gris
        pdf.set_fill_color(240, 240, 240)
        coords = {
            1: (cur_x, cur_y),
            2: (cur_x, cur_y + h_dot),
            3: (cur_x, cur_y + h_dot * 2),
            4: (cur_x + w_dot, cur_y),
            5: (cur_x + w_dot, cur_y + h_dot),
            6: (cur_x + w_dot, cur_y + h_dot * 2)
        }
        
        # Puntos negros
        pdf.set_fill_color(0, 0, 0)
        for p in puntos_espejo:
            cx, cy = coords[p]
            pdf.circle(cx, cy, dot_r, 'F')
            
        cur_x += w_char

# --- 3. BASE DE DATOS E IMÁGENES ---
def get_img(name):
    if not name: return None
    path = os.path.join(ASSETS_DIR, name)
    if os.path.exists(path): return path
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
    "Venenoso": "81.GIF", "No alcohol": "40.GIF", "No conducir (Sueño)": "50.GIF",
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
    
    # --- PÁGINA 1: VISUAL ---
    pdf.add_page()
    pdf.set_font("Arial", "B", 24)
    pdf.cell(0, 15, txt=f"{med.upper()}", ln=True, align='C')
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, txt=f"PACIENTE: {paciente.upper()} | DOSIS: {dosis.upper()}", ln=True, align='C')
    pdf.line(10, 35, 200, 35)
    
    # Bloque 1
    y_start = 50
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
    y_alert = 120
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

    # --- PÁGINA 2: BRAILLE (LIBRERÍA) ---
    if hacer_braille:
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, txt="GUÍA TÁCTIL (BRAILLE ESPEJO)", ln=True, align='C')
        pdf.set_font("Arial", "", 10)
        pdf.multi_cell(0, 5, txt="INSTRUCCIONES: Punzar puntos negros por el reverso.", align='C')
        pdf.ln(10)
        
        # Construcción Texto Plano
        str_alert = ", ".join(alertas) if alertas else "NINGUNA"
        # Forzar string nuevo para evitar cacheo
        texto_raw = f"PAC:{paciente}. MED:{med} {dosis}. VIA:{via}. TOMA:{frec}. PRE:{str_alert}."
        
        # Renderizado usando pybraille + matemática
        dibujar_braille_desde_libreria(pdf, texto_raw, 10, 45)
        
        pdf.set_y(-15)
        pdf.set_font("Arial", "I", 8)
        pdf.cell(0, 10, txt="SMEFI System - Powered by PyBraille", align='C')

    return bytes(pdf.output(dest='S'))

# --- 5. INTERFAZ ---
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
        # Pasamos variables directamente para asegurar frescura
        pdf_bytes = generar_pdf(p_nom, p_med, p_dos, v_sel, f_sel, a_sel, p_br)
        st.success("✅ Documento generado correctamente")
        st.download_button("📥 DESCARGAR PDF", pdf_bytes, f"Guia_{p_med}.pdf", "application/pdf")
    except Exception as e:
        st.error(f"Error: {e}")
