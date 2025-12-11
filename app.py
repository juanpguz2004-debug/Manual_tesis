import streamlit as st
from fpdf import FPDF
import os
import unicodedata

# --- 1. CONFIGURACIÓN DE RUTAS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, 'assets', 'usp_pictograms')

# --- 2. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="SMEFI Prototipo", page_icon="💊", layout="wide")
st.title("🖨️ Sistema de Dispensación Inclusiva (SMEFI)")
st.markdown("**Versión Final:** Braille completo (Multilínea) + Pictogramas USP.")

# Verificación de carpeta
if os.path.exists(ASSETS_DIR):
    archivos_reales = os.listdir(ASSETS_DIR)
    st.sidebar.success(f"✅ Librería USP conectada: {len(archivos_reales)} archivos.")
else:
    st.sidebar.error(f"❌ Error Crítico: No existe la carpeta {ASSETS_DIR}")

# --- 3. DICCIONARIO BRAILLE (ESTÁNDAR 6 PUNTOS) ---
# Mapeo de caracteres a puntos activos (1-6)
BRAILLE_CHARS = {
    'A': [1], 'B': [1,2], 'C': [1,4], 'D': [1,4,5], 'E': [1,5],
    'F': [1,2,4], 'G': [1,2,4,5], 'H': [1,2,5], 'I': [2,4], 'J': [2,4,5],
    'K': [1,3], 'L': [1,2,3], 'M': [1,3,4], 'N': [1,3,4,5], 'O': [1,3,5],
    'P': [1,2,3,4], 'Q': [1,2,3,4,5], 'R': [1,2,3,5], 'S': [2,3,4], 'T': [2,3,4,5],
    'U': [1,3,6], 'V': [1,2,3,6], 'W': [2,4,5,6], 'X': [1,3,4,6], 'Y': [1,3,4,5,6], 'Z': [1,3,5,6],
    '1': [1], '2': [1,2], '3': [1,4], '4': [1,4,5], '5': [1,5],
    '6': [1,2,4], '7': [1,2,4,5], '8': [1,2,5], '9': [2,4], '0': [2,4,5],
    ' ': [], '.': [2,5,6], ',': [2], ':': [2,5], ';': [2,3],
    '(': [2,3,5,6], ')': [2,3,5,6], '/': [3,4], '-': [3,6]
}

# --- 4. MOTOR BRAILLE (TOUCHMAP GENERATOR) ---
def dibujar_braille_multilinea(pdf, texto_completo, x_inicial, y_inicial):
    """
    Dibuja texto Braille espejado respetando márgenes (salto de línea).
    """
    # 1. Normalizar texto (Quitar tildes, pasar a mayúsculas)
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto_completo) if unicodedata.category(c) != 'Mn').upper()
    
    # 2. Configuración de la celda Braille (mm)
    dot_radius = 0.5      # Radio del punto
    w_dot = 2.5           # Distancia horizontal entre puntos de una celda
    h_dot = 2.5           # Distancia vertical entre puntos
    w_char = 6.5          # Ancho total de una letra (espacio incluido)
    h_line = 12.0         # Altura de la línea (espacio entre renglones)
    margin_right = 190    # Margen derecho de la hoja
    
    current_x = x_inicial
    current_y = y_inicial
    
    # Mapeo de Espejo (Mirroring): Invertimos columnas para punzar desde atrás
    # 1(Izq) -> 4(Der), etc.
    mirror = {1:4, 2:5, 3:6, 4:1, 5:2, 6:3}

    for char in texto:
        # Verificar si cabe en la línea
        if current_x + w_char > margin_right:
            current_x = x_inicial # Reset X
            current_y += h_line   # Bajar Y
            
        puntos = BRAILLE_CHARS.get(char, [])
        
        # Convertir a puntos espejo
        puntos_espejo = [mirror[p] for p in puntos]
        
        # Posiciones relativas dentro de la celda (x, y)
        offsets = {
            1: (0, 0),       4: (w_dot, 0),
            2: (0, h_dot),   5: (w_dot, h_dot),
            3: (0, h_dot*2), 6: (w_dot, h_dot*2)
        }
        
        # Dibujar los puntos activos (Negros)
        pdf.set_fill_color(0, 0, 0)
        for p_num in puntos_espejo:
            dx, dy = offsets[p_num]
            # Dibujar círculo (x, y, radio)
            pdf.circle(current_x + dx, current_y + dy, dot_radius, 'F')
            
        current_x += w_char

# --- 5. FUNCIONES AUXILIARES (IMÁGENES) ---
def ruta_imagen_segura(nombre_objetivo):
    # Busca exacto
    ruta_exacta = os.path.join(ASSETS_DIR, nombre_objetivo)
    if os.path.exists(ruta_exacta): return ruta_exacta
    
    # Busca insensible a mayúsculas
    for f in os.listdir(ASSETS_DIR):
        if f.lower() == nombre_objetivo.lower():
            return os.path.join(ASSETS_DIR, f)
    return None

# --- 6. MAPEOS (Basados en tu lista numerada) ---
MAPA_VIA = {
    "Vía Oral (Tragar)": "01.GIF", 
    "Masticar": "43.GIF", 
    "Sublingual": "46.GIF",
    "Disolver en agua": "45.GIF", 
    "Diluir en agua": "44.GIF", 
    "Inhalador": "71.GIF",
    "Spray Nasal": "77.GIF", 
    "Gotas Nariz": "09.GIF", 
    "Gotas Ojos": "29.GIF",
    "Gotas Oído": "31.GIF", 
    "Inyección": "61.GIF", 
    "Vía Rectal": "27.GIF",
    "Vía Vaginal": "25.GIF", 
    "Gárgaras": "58.GIF"
}

MAPA_FRECUENCIA = {
    "--- Seleccionar ---": None, 
    "Mañana (AM)": "67.GIF", 
    "Noche / Hora de dormir": "22.GIF",
    "2 veces/día": "04.GIF", 
    "2 veces/día (Comidas)": "03.GIF", 
    "3 veces/día": "16.GIF", 
    "3 veces/día (Comidas)": "14.GIF",
    "4 veces/día": "15.GIF", 
    "4 veces/día (Comidas)": "13.GIF",
    "1h antes comer": "05.GIF", 
    "1h después comer": "06.GIF", 
    "Con alimentos": "18.GIF", 
    "Estómago vacío": "19.GIF"
}

MAPA_ALERTAS = {
    "No alcohol": "40.GIF", 
    "No conducir": "50.GIF", 
    "No triturar": "33.GIF",
    "Refrigerar": "20.GIF", 
    "No refrigerar": "52.GIF", 
    "No embarazo": "34.GIF",
    "No lactancia": "36.GIF", 
    "Peligro": "81.GIF", 
    "Causa sueño": "24.GIF"
}

# --- 7. MOTOR DE GENERACIÓN PDF ---
def generar_pdf(paciente, medicamento, dosis, via_key, frecuencia_key, lista_alertas, es_ciego):
    pdf = FPDF()
    pdf.add_page()
    
    # A. ENCABEZADO
    pdf.set_font("Arial", "B", 24)
    pdf.cell(0, 15, txt=f"{medicamento.upper()}", ln=True, align='C')
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, txt=f"PACIENTE: {paciente.upper()} | DOSIS: {dosis.upper()}", ln=True, align='C')
    pdf.line(10, 35, 200, 35)
    
    # B. PICTOGRAMAS (Texto Arriba, Imagen Abajo)
    y_start = 45 
    
    # Vía
    ruta_via = ruta_imagen_segura(MAPA_VIA.get(via_key, ""))
    if ruta_via:
        pdf.set_xy(20, y_start)
        pdf.set_font("Arial", "B", 10)
        # Texto Arriba
        pdf.multi_cell(60, 4, txt=via_key.upper(), align='C')
        # Imagen Abajo
        pdf.image(ruta_via, x=35, y=y_start+15, w=25)
    
    # Frecuencia
    ruta_frec = ruta_imagen_segura(MAPA_FRECUENCIA.get(frecuencia_key, ""))
    if ruta_frec:
        pdf.set_xy(100, y_start)
        pdf.set_font("Arial", "B", 10)
        # Texto Arriba
        pdf.multi_cell(60, 4, txt=frecuencia_key.upper(), align='C')
        # Imagen Abajo
        pdf.image(ruta_frec, x=115, y=y_start+15, w=25)

    # Alertas (Grid)
    y_alert = 95
    pdf.set_xy(10, y_alert)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 10, txt="PRECAUCIONES:", ln=True)
    
    x_curr = 20
    count = 0
    for alerta in lista_alertas:
        ruta = ruta_imagen_segura(MAPA_ALERTAS.get(alerta, ""))
        if ruta:
            if count == 4: break 
            pdf.set_font("Arial", "B", 7)
            # Texto Arriba
            pdf.set_xy(x_curr-5, y_alert+8)
            pdf.multi_cell(35, 3, txt=alerta.upper(), align='C')
            # Imagen Abajo
            pdf.image(ruta, x=x_curr, y=y_alert+18, w=20)
            x_curr += 45
            count += 1

    # C. ZONA BRAILLE GENERATIVA (Touch Map)
    if es_ciego:
        # Línea de corte
        pdf.set_y(150)
        pdf.set_font("Arial", "", 9)
        pdf.cell(0, 5, txt="_" * 65, ln=True, align='C')
        pdf.cell(0, 5, txt="ZONA DE PUNZADO BRAILLE (ESPEJO - PUNZAR POR EL REVERSO)", ln=True, align='C')
        
        # 1. Construir la CADENA COMPLETA DE DATOS
        alertas_str = ", ".join(lista_alertas) if lista_alertas else "NINGUNA"
        # Concatenamos Paciente, Med, Dosis, Via, Frecuencia y Alertas
        texto_para_braille = (
            f"PAC: {paciente}. MED: {medicamento} {dosis}. "
            f"VIA: {via_key}. TOMA: {frecuencia_key}. "
            f"ALERTAS: {alertas_str}."
        )
        
        # 2. Dibujar Puntos (Motor TouchMap)
        braille_y = 170
        braille_x = 10
        
        dibujar_braille_multilinea(pdf, texto_para_braille, braille_x, braille_y)
        
        # Instrucción Visual
        pdf.set_y(-15)
        pdf.set_font("Arial", "I", 8)
        pdf.cell(0, 10, txt="Instrucción: Voltee la hoja y presione sobre los puntos negros con un punzón.", align='C')

    return bytes(pdf.output(dest='S'))

# --- 8. INTERFAZ DE USUARIO ---
col1, col2 = st.columns(2)
with col1:
    nombre = st.text_input("Paciente", "JUAN PEREZ")
    med = st.text_input("Medicamento", "AMOXICILINA")
with col2:
    dosis = st.text_input("Dosis", "500 MG")
    es_ciego = st.toggle("Generar Guía Braille Automática")

st.divider()

c3, c4 = st.columns(2)
with c3:
    st.info("ℹ️ Información de Toma")
    via_sel = st.selectbox("Vía de Administración", list(MAPA_VIA.keys()))
    frec_sel = st.selectbox("Frecuencia / Horario", list(MAPA_FRECUENCIA.keys()))
    
    # Previas
    cols_p = st.columns(2)
    r1 = ruta_imagen_segura(MAPA_VIA[via_sel])
    if r1: cols_p[0].image(r1, width=60)
    
    r2 = ruta_imagen_segura(MAPA_FRECUENCIA.get(frec_sel))
    if r2: cols_p[1].image(r2, width=60)

with c4:
    st.warning("⚠️ Seguridad")
    alertas_sel = st.multiselect("Seleccione Precauciones:", list(MAPA_ALERTAS.keys()))
    if alertas_sel:
        cols = st.columns(4)
        for i, a in enumerate(alertas_sel):
            r = ruta_imagen_segura(MAPA_ALERTAS[a])
            if r: cols[i%4].image(r, width=40)

st.write("")
if st.button("GENERAR GUÍA PDF", type="primary", use_container_width=True):
    try:
        pdf_bytes = generar_pdf(nombre, med, dosis, via_sel, frec_sel, alertas_sel, es_ciego)
        st.success("✅ Guía Generada Exitosamente")
        st.download_button(
            label="📄 DESCARGAR PDF FINAL",
            data=pdf_bytes,
            file_name=f"Guia_{med}.pdf",
            mime="application/pdf"
        )
    except Exception as e:
        st.error(f"Error técnico: {e}")
