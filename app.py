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
    layout="centered" # Centrado ideal para móviles
)

# --- 1. ESTADO INICIAL (Para no usar Excel externo en la Nube) ---
# Como en la nube el archivo Excel se borra al reiniciar, usamos memoria.
if 'historial_excel' not in st.session_state:
    st.session_state.historial_excel = pd.DataFrame(columns=["Name", "Company", "Purpose", "Time In", "Time Out", "Date", "Firma"])

# --- 2. FORMULARIO VERTICAL Y FIRMA ---
st.title("📱 App Móvil - Reportes Técnicos")
st.caption("Complete el formulario verticalmente y firme al final.")

with st.form("reporte_form"):
    # SECCIÓN INFORMACIÓN VERTICAL (Sin columnas para que sea una lista larga)
    st.markdown("### 📝 Información General")
    name = st.text_input("Name (Nombre Técnico):", value="Tu Nombre")
    company = st.text_input("Company (Cliente):", value="Empresa XYZ")
    date = st.date_input("Date (Fecha):", value=datetime.today())
    
    st.markdown("### 🛠️ Detalles de la Visita")
    purpose = st.selectbox("Purpose of Visit:", ["Mantenimiento", "Instalación", "Reparación", "Auditoría"])
    time_in = st.time_input("Time In (Hora Entrada):", value=datetime.now().time())
    time_out = st.time_input("Time Out (Hora Salida):", value=datetime.now().time())
    
    description = st.text_area("Description (Descripción):", "Detalles del trabajo realizado...")
    
    # SECCIÓN FIRMA (MÉTODO CÁMARA ESTABLE)
    st.markdown("### ✍️ Firma Digital")
    st.caption("En celular, presiona el botón para abrir la Cámara. Firma en papel o usa la función de firma del móvil.")
    # key="signature" y camera=True permiten usar la cámara nativa del móvil
    signature_file = st.file_uploader("Tomar Foto de Firma / Subir", type=['jpg', 'png'], key="signature", accept_multiple_files=False, camera=True)
    
    if signature_file is not None:
        st.success("✅ Foto de firma cargada.")
        # Leemos los bytes de la imagen
        img_bytes = signature_file.read()
        # Guardamos bytes en session_state para el PDF
        st.session_state['signature_bytes'] = img_bytes
        
        # Mostramos miniatura
        st.image(Image.open(io.BytesIO(img_bytes)), width=150)
    else:
        st.warning("⚠️ Es necesario una foto de firma para generar el reporte.")

    submitted = st.form_submit_button("💾 PROCESAR Y DESCARGAR ARCHIVOS")

# --- 3. PROCESAR Y GENERAR ARCHIVOS ---
if submitted:
    # Validar que haya firma
    if 'signature_bytes' not in st.session_state:
        st.error("⚠️ Por favor, sube o toma una foto de la firma antes de continuar.")
        st.stop()

    # 1. ACTUALIZAR MEMORIA EXCEL
    nueva_fila = {
        "Name": name, "Company": company, "Purpose": purpose,
        "Time In": time_in, "Time Out": time_out, "Date": date,
        "Firma": "Firma Guardada" # Texto para el Excel
    }
    
    # Guardar en memoria (Session State)
    df_nuevo = pd.concat([st.session_state.historial_excel, pd.DataFrame([nueva_fila])], ignore_index=True)
    st.session_state.historial_excel = df_nuevo

    st.success("✅ Procesado exitoso.")
    
    # --- DESCARGAS ---

    # A. EXCEL
    st.markdown("---")
    st.subheader("📊 Descargar Excel (Historial)")
    
    buffer_excel = io.BytesIO()
    with pd.ExcelWriter(buffer_excel, engine='openpyxl') as writer:
        df_nuevo.to_excel(writer, index=False, sheet_name='Visitas')
    
    st.download_button(
        label="📥 Descargar Historial Excel (.xlsx)",
        data=buffer_excel,
        file_name=f"Visitas_{date.strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # B. PDF
    st.subheader("📄 Generar PDF de Esta Visita")
    buffer_pdf = io.BytesIO()
    doc = SimpleDocTemplate(buffer_pdf, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    elements = []
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Justify', alignment=4)) # Texto justificado

    # Título y Datos
    elements.append(Paragraph("REPORTE DE VISITA TÉCNICA", styles['Title']))
    elements.append(Paragraph(f"<b>Empresa:</b> {company}  <b>Fecha:</b> {date.strftime('%d/%m/%Y')}", styles['Normal']))
    elements.append(Paragraph(f"<b>Técnico:</b> {name}", styles['Normal']))
    elements.append(Paragraph(f"<b>Propósito:</b> {purpose}", styles['Normal']))
    elements.append(Paragraph(f"<b>Horario:</b> {time_in.strftime('%H:%M')} - {time_out.strftime('%H:%M')}", styles['Normal']))
    elements.append(Paragraph("<b>Descripción:</b>", styles['Heading4']))
    elements.append(Paragraph(description, styles['Justify']))

    # Insertar Firma en PDF (Directamente desde Bytes, sin Base64)
    img_stream = io.BytesIO(st.session_state['signature_bytes'])
    img_pdf = RLImage(img_stream, width=200, height=100, hAlign='RIGHT')
    elements.append(img_pdf)
    elements.append(Paragraph("<i>Firma del Técnico</i>", styles['Normal']))

    doc.build(elements)

    st.download_button(
        label="📄 Descargar Reporte PDF (.pdf)",
        data=buffer_pdf,
        file_name=f"Reporte_{company}_{date.strftime('%Y%m%d')}.pdf",
        mime="application/pdf"
    )

    # C. JPG (Imagen Plana)
    st.subheader("🖼️ Generar Foto Plana del Reporte (JPG)")
    # Creamos imagen blanca
    img_jpg = Image.new('RGB', (600, 800), color=(255, 255, 255))
    d = ImageDraw.Draw(img_jpg)
    
    # Fuentes (Intentamos Arial, sino default)
    try: 
        font = ImageFont.truetype("arial.ttf", 24)
        font_peque = ImageFont.truetype("arial.ttf", 18)
    except: 
        font = ImageFont.load_default()
        font_peque = ImageFont.load_default()

    # Dibujar textos
    d.text((30, 50), "REPORTE DE VISITA", fill=(0, 0, 0), font=font)
    d.text((30, 100), f"Fecha: {date.strftime('%d/%m/%Y')}", fill=(0, 0, 0), font=font_peque)
    d.text((30, 140), f"Empresa: {company}", fill=(0, 0, 0), font=font_peque)
    d.text((30, 180), f"Tecnico: {name}", fill=(0, 0, 0), font=font_peque)
    d.text((30, 220), f"Actividad: {purpose}", fill=(0, 0, 0), font=font_peque)
    
    y_text = 280
    for line in description.split('\n'):
        d.text((30, y_text), line, fill=(0, 0, 0), font=font_peque)
        y_text += 30

    # Pegar Firma
    firma_stream = io.BytesIO(st.session_state['signature_bytes'])
    firma_img = Image.open(firma_stream)
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
