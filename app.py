import streamlit as st
import pandas as pd
import io
import base64
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image as RLImage

# --- CONFIGURACIÓN ---
st.set_page_config(
    page_title="Reporte Técnico Web",
    page_icon="📱",
    layout="centered"
)

# --- 1. FORMULARIO VERTICAL Y FIRMA ---
st.title("📱 App Móvil - Reportes Técnicos")
st.caption("Complete los datos y firme.")

# Estado inicial (Memoria de la sesión para el historial)
if 'historial_excel' not in st.session_state:
    st.session_state.historial_excel = pd.DataFrame(columns=["Name", "Company", "Purpose", "Time In", "Time Out", "Date", "Firma"])

# --- FORMULARIO (USANDO st.camera_input QUE ES COMPATIBLE) ---
with st.form("reporte_form"):
    st.markdown("### 📝 Información General")
    
    # Campos Verticales
    name = st.text_input("Name (Nombre Técnico):", value="Tu Nombre")
    company = st.text_input("Company (Cliente):", value="Empresa XYZ")
    date = st.date_input("Date (Fecha):", value=datetime.today())
    
    st.markdown("### 🛠️ Detalles de la Visita")
    purpose = st.selectbox("Purpose of Visit (Motivo):", 
                                ["Mantenimiento", "Instalación", "Reparación", "Auditoría"])
    
    time_in = st.time_input("Time In (Hora Entrada):", value=datetime.now().time())
    time_out = st.time_input("Time Out (Hora Salida):", value=datetime.now().time())
    
    description = st.text_area("Description (Descripción):", "Detalles del trabajo realizado...")
    
    # --- FIRMA DIGITAL (CAMERA INPUT) ---
    st.markdown("### ✍️ Firma Digital")
    st.caption("En el celular, presiona el botón para abrir la Cámara y sacar una foto de tu firma.")
    
    # Usamos st.camera_input (Este es el widget que funciona bien en móviles y dentro de formularios)
    picture = st.camera_input("Fotografiar Firma", key="sig")

    submitted = st.form_submit_button("💾 PROCESAR Y GENERAR DESCARGAS")

# --- 2. LÓGICA DE PROCESAMIENTO ---
if submitted:
    # 1. Verificar Firma
    if not picture:
        st.error("⚠️ Es necesario tomar una foto de la firma para generar el reporte.")
        st.stop()
    
    # 2. Guardar Firma en Bytes (para el PDF)
    # picture devuelve una lista de imágenes, tomamos la primera [0]
    signature_bytes = picture[0].tobytes()
    st.session_state['signature_bytes'] = signature_bytes

    # 3. Guardar en Excel (Memoria)
    nueva_fila = {
        "Name": name, "Company": company, "Purpose": purpose,
        "Time In": time_in, "Time Out": time_out, "Date": date,
        "Firma": "Firma Cargada" # Texto para el Excel
    }
    
    df_nuevo = pd.concat([st.session_state.historial_excel, pd.DataFrame([nueva_fila])], ignore_index=True)
    st.session_state.historial_excel = df_nuevo
    
    st.success("✅ Reporte procesado.")

    # --- 4. GENERAR DESCARGAS ---
    st.markdown("---")
    st.subheader("📥 Archivos Generados")
    
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
    styles.add(ParagraphStyle(name='Justify', alignment=4)) # Justificar texto
    
    # Cabecera PDF
    elements.append(Paragraph("REPORTE DE VISITA TÉCNICA", styles['Title']))
    elements.append(Paragraph(f"<b>Fecha:</b> {date}   <b>Técnico:</b> {name}", styles['Normal']))
    elements.append(Paragraph(f"<b>Empresa:</b> {company}", styles['Normal']))
    elements.append(Paragraph(f"<b>Propósito:</b> {purpose}", styles['Normal']))
    elements.append(Paragraph(f"<b>Horario:</b> {time_in} - {time_out}", styles['Normal']))
    elements.append(Paragraph("<b>Descripción:</b>", styles['Heading4']))
    elements.append(Paragraph(description, styles['Justify']))
    
    # Firma PDF
    img_stream = io.BytesIO(signature_bytes)
    img_pdf = RLImage(img_stream, width=200, height=100, hAlign='RIGHT')
    elements.append(img_pdf)
    elements.append(Paragraph("Firma del Técnico", styles['Normal']))
    
    doc.build(elements)
    
    st.download_button(
        label="📄 Descargar PDF (.pdf)",
        data=buffer_pdf,
        file_name=f"Reporte_{company}_{date}.pdf",
        mime="application/pdf"
    )

    # C. JPG (Imagen Plana)
    img_jpg = Image.new('RGB', (600, 800), color=(255, 255, 255))
    d = ImageDraw.Draw(img_jpg)
    
    # Fuentes
    try:
        font = ImageFont.truetype("arial.ttf", 24)
        font_small = ImageFont.truetype("arial.ttf", 18)
    except:
        font = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # Dibujar Textos
    d.text((30, 50), "REPORTE DE VISITA", fill=(0, 0, 0), font=font)
    d.text((30, 100), f"Fecha: {date}", fill=(0, 0, 0), font=font_small)
    d.text((30, 130), f"Empresa: {company}", fill=(0, 0, 0), font=font_small)
    d.text((30, 160), f"Técnico: {name}", fill=(0, 0, 0), font=font_small)
    d.text((30, 190), f"Actividad: {purpose}", fill=(0, 0, 0), font=font_small)
    
    # Descripción
    y_text = 280
    for line in description.split('\n'):
        d.text((30, y_text), line, fill=(0, 0, 0), font=font_small)
        y_text += 25

    # Firma
    firma_img = Image.open(io.BytesIO(signature_bytes))
    firma_img = firma_img.resize((200, 100))
    img_jpg.paste(firma_img, (350, 650))
    
    # Guardar JPG
    buffer_jpg = io.BytesIO()
    img_jpg.save(buffer_jpg, format="JPEG", quality=95)

    st.download_button(
        label="🖼️ Descargar Foto Reporte (.jpg)",
        data=buffer_jpg,
        file_name=f"Foto_Reporte_{company}.jpg",
        mime="image/jpeg"
    )
