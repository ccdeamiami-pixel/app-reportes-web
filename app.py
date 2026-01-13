import streamlit as st
import pandas as pd
import io
import base64
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image as RLImage

# Importar el componente de firma profesional
from streamlit_signature_pad import signature_pad

# --- CONFIGURACIÓN ---
st.set_page_config(
    page_title="Reporte Técnico Web",
    page_icon="✍️",
    layout="centered" # Centrado ideal para vertical
)

# --- 1. ESTADO INICIAL (MEMORIA) ---
if 'historial_excel' not in st.session_state:
    st.session_state.historial_excel = pd.DataFrame(columns=["Name", "Company", "Purpose", "Time In", "Time Out", "Date", "Firma"])

# --- 2. INTERFAZ VERTICAL ---
st.title("📱 App Móvil - Reportes Técnicos")
st.caption("Complete los campos verticalmente y firme con el dedo al final.")

# --- CAMPOS VERTICALES ---
st.markdown("### 📝 Información General")
name = st.text_input("Name (Nombre Técnico):", value="Tu Nombre")
company = st.text_input("Company (Cliente):", value="Empresa XYZ")
date = st.date_input("Date (Fecha):", value=datetime.today())

st.markdown("### 🛠️ Detalles de la Visita")
purpose = st.selectbox("Purpose of Visit (Motivo):", ["Mantenimiento", "Instalación", "Reparación", "Auditoría"])

time_in = st.time_input("Time In (Hora Entrada):", value=datetime.now().time())
time_out = st.time_input("Time Out (Hora Salida):", value=datetime.now().time())

description = st.text_area("Description (Descripción):", "Detalles del trabajo realizado...")

# --- FIRMA DIGITAL (CON DEDO) ---
st.markdown("### ✍️ Firma Digital")
st.caption("Firme en el recuadro blanco usando su dedo (táctil).")
# Usamos streamlit-signature-pad (Key es importante para que funcione)
signature_data = signature_pad(key="sig", stroke_width=3, stroke_color='#000000')

# --- BOTÓN DE PROCESADO ---
# Usamos st.button normal para evitar el error de "Missing Submit Button" del st.form
if st.button("💾 PROCESAR Y GENERAR DESCARGAS", type="primary"):
    # 1. Verificar Firma
    if not signature_data['is_signed']:
        st.error("⚠️ Por favor, firme en el recuadro blanco antes de continuar.")
        st.stop()
    
    # 2. Decodificar la firma (de base64 a bytes)
    # La firma viene en formato 'data:image/png;base64,iVBORw...'
    signature_bytes = base64.b64decode(signature_data['signature'])
    st.session_state['signature_bytes'] = signature_bytes
    
    # 3. Actualizar Excel (Memoria)
    nueva_fila = {
        "Name": name, "Company": company, "Purpose": purpose,
        "Time In": time_in, "Time Out": time_out, "Date": date,
        "Firma": "Firma Capturada"
    }
    df_nuevo = pd.concat([st.session_state.historial_excel, pd.DataFrame([nueva_fila])], ignore_index=True)
    st.session_state.historial_excel = df_nuevo
    
    st.success("✅ Procesado exitoso.")
    
    # --- DESCARGAS ---
    st.markdown("---")
    st.subheader("📥 Descargar Archivos")
    
    # A. EXCEL
    buffer_excel = io.BytesIO()
    with pd.ExcelWriter(buffer_excel, engine='openpyxl') as writer:
        df_nuevo.to_excel(writer, index=False, sheet_name='Visitas')
    st.download_button(
        label="📊 Descargar Historial Excel (.xlsx)",
        data=buffer_excel,
        file_name=f"Visitas_{date.strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # B. PDF
    buffer_pdf = io.BytesIO()
    doc = SimpleDocTemplate(buffer_pdf, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    elements = []
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Justify', alignment=4))
    
    elements.append(Paragraph("REPORTE DE VISITA TÉCNICA", styles['Title']))
    elements.append(Paragraph(f"<b>Fecha:</b> {date}   <b>Técnico:</b> {name}", styles['Normal']))
    elements.append(Paragraph(f"<b>Empresa:</b> {company}", styles['Normal']))
    elements.append(Paragraph(f"<b>Propósito:</b> {purpose}", styles['Normal']))
    elements.append(Paragraph(f"<b>Horario:</b> {time_in} - {time_out}", styles['Normal']))
    elements.append(Paragraph(f"<b>Descripción:</b>", styles['Heading4']))
    elements.append(Paragraph(description, styles['Justify']))
    
    # Firma PDF
    img_stream = io.BytesIO(signature_bytes)
    img_pdf = RLImage(img_stream, width=200, height=100, hAlign='RIGHT')
    elements.append(img_pdf)
    elements.append(Paragraph("Firma del Técnico", styles['Normal']))
    
    doc.build(elements)
    st.download_button(
        label="📄 Descargar PDF",
        data=buffer_pdf,
        file_name=f"Reporte_{company}.pdf",
        mime="application/pdf"
    )

    # C. JPG
    img_jpg = Image.new('RGB', (600, 800), color=(255, 255, 255))
    d = ImageDraw.Draw(img_jpg)
    try: font = ImageFont.truetype("arial.ttf", 24); font_small = ImageFont.truetype("arial.ttf", 18)
    except: font = ImageFont.load_default(); font_small = ImageFont.load_default()
    
    d.text((30, 50), "REPORTE DE VISITA", fill=(0,0,0), font=font)
    d.text((30, 100), f"Fecha: {date}", fill=(0,0,0), font=font_small)
    d.text((30, 140), f"Empresa: {company}", fill=(0,0,0), font=font_small)
    d.text((30, 180), f"Técnico: {name}", fill=(0,0,0), font=font_small)
    d.text((30, 220), f"Propósito: {purpose}", fill=(0,0,0), font=font_small)
    
    y_text = 280
    for line in description.split('\n'):
        d.text((30, y_text), line, fill=(0,0,0), font=font_small)
        y_text += 25
    
    firma_img = Image.open(io.BytesIO(signature_bytes))
    firma_img = firma_img.resize((200, 100))
    img_jpg.paste(firma_img, (350, 650))
    
    buffer_jpg = io.BytesIO()
    img_jpg.save(buffer_jpg, format="JPEG", quality=95)
    
    st.download_button(
        label="🖼️ Descargar Foto Reporte (.jpg)",
        data=buffer_jpg,
        file_name=f"Foto_Reporte_{company}.jpg",
        mime="image/jpeg"
    )
