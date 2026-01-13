import streamlit as st
import pandas as pd
import io
import base64
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image as RLImage

# --- CONFIGURACIÓN WEB ---
st.set_page_config(
    page_title="Reporte Técnico Web",
    page_icon="📝",
    layout="centered" # Centrado para móviles
)

# --- 1. FUNCIÓN DE FIRMA ---
def signature_component():
    html_code = """
    <div style="text-align: center; font-family: sans-serif;">
    <h3>Firma Digital</h3>
    <canvas id="sig-canvas" width="300" height="150" style="border:1px solid #333; background-color: white; touch-action: none; border-radius:5px;"></canvas>
    <br>
    <button onclick="clearCanvas()" style="background-color: #ff4444; color: white; border: none; padding:5px 20px; border-radius:4px;">Borrar</button>
    </div>
    <script>
    var canvas = document.getElementById('sig-canvas');
    var ctx = canvas.getContext('2d');
    var drawing = false;

    canvas.addEventListener('mousedown', startDraw);
    canvas.addEventListener('mousemove', draw);
    canvas.addEventListener('mouseup', stopDraw);
    canvas.addEventListener('touchstart', startDraw);
    canvas.addEventListener('touchmove', draw);
    canvas.addEventListener('touchend', stopDraw);

    function getPos(e) {
        var rect = canvas.getBoundingClientRect();
        if (e.touches) {
            return { x: e.touches[0].clientX - rect.left, y: e.touches[0].clientY - rect.top };
        }
        return { x: e.clientX - rect.left, y: e.clientY - rect.top };
    }

    function startDraw(e) {
        e.preventDefault();
        drawing = true;
        draw(e);
    }
    function stopDraw() {
        drawing = false;
        ctx.beginPath();
    }
    function draw(e) {
        if (!drawing) return;
        e.preventDefault();
        var pos = getPos(e);
        ctx.lineWidth = 3;
        ctx.lineCap = 'round';
        ctx.strokeStyle = '#000000';
        ctx.lineTo(pos.x, pos.y);
        ctx.stroke();
        ctx.beginPath();
        ctx.moveTo(pos.x, pos.y);
    }
    function clearCanvas() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
    }
    function saveSignature() {
        var dataURL = canvas.toDataURL();
        var base64 = dataURL.split(',')[1];
        window.parent.postMessage({type: 'signature', data: base64}, '*');
    }
    </script>
    """
    st.components.v1.html(html_code, height=250)
    if 'signature_data' in st.session_state:
        st.success("✅ Firma capturada.")
        img_data = st.session_state['signature_data']
        img = Image.open(io.BytesIO(base64.b64decode(img_data)))
        st.image(img, width=200)

# --- 2. FORMULARIO VERTICAL ---
st.title("📝 App Móvil - Reportes")
st.caption("Complete el formulario y firme al final.")

# Estado inicial de datos (si no hay excel, empezamos en blanco)
if 'historial_excel' not in st.session_state:
    st.session_state.historial_excel = pd.DataFrame(columns=["Name", "Company", "Purpose", "Time In", "Time Out", "Date", "Firma"])

with st.form("reporte_form"):
    # Campos Verticales
    name = st.text_input("Name (Nombre Técnico):", value="Tu Nombre")
    company = st.text_input("Company (Cliente):", value="Empresa XYZ")
    date = st.date_input("Date (Fecha):", value=datetime.today())
    purpose = st.selectbox("Purpose of Visit:", ["Mantenimiento", "Instalación", "Reparación", "Auditoría"])
    
    time_in = st.time_input("Time In:")
    time_out = st.time_input("Time Out:")
    
    description = st.text_area("Description (Descripción):", "Detalles del trabajo realizado...")
    
    # Firma
    st.markdown("### ✍️ Firma Digital")
    signature_component()
    
    submit = st.form_submit_button("💾 PROCESAR Y DESCARGAR ARCHIVOS")

# --- 3. LÓGICA AL PROCESAR ---
if submit:
    # Validar firma
    if 'signature_data' not in st.session_state:
        st.error("⚠️ Por favor, firme en el recuadro blanco antes de continuar.")
        st.stop()

    # 1. ACTUALIZAR EXCEL EN MEMORIA
    nueva_fila = {
        "Name": name, "Company": company, "Purpose": purpose,
        "Time In": time_in, "Time Out": time_out, "Date": date,
        "Firma": st.session_state.signature_data
    }
    # Concatenar historial
    df_nuevo = pd.concat([st.session_state.historial_excel, pd.DataFrame([nueva_fila])], ignore_index=True)
    st.session_state.historial_excel = df_nuevo

    st.success("✅ Procesado exitoso. Puedes descargar los archivos abajo.")
    
    # --- DESCARGAS ---
    
    # A. DESCARGAR EXCEL
    buffer_excel = io.BytesIO()
    with pd.ExcelWriter(buffer_excel, engine='openpyxl') as writer:
        df_nuevo.to_excel(writer, index=False, sheet_name='Visitas')
    st.download_button(
        label="📊 Descargar Excel Actualizado (.xlsx)",
        data=buffer_excel,
        file_name=f"Visitas_{date.strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # B. DESCARGAR PDF
    buffer_pdf = io.BytesIO()
    doc = SimpleDocTemplate(buffer_pdf, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Justify', alignment=4))
    
    elements.append(Paragraph("REPORTE DE VISITA TÉCNICA", styles['Title']))
    elements.append(Paragraph(f"<b>Fecha:</b> {date}", styles['Normal']))
    elements.append(Paragraph(f"<b>Empresa:</b> {company}", styles['Normal']))
    elements.append(Paragraph(f"<b>Técnico:</b> {name}", styles['Normal']))
    elements.append(Paragraph(f"<b>Propósito:</b> {purpose}", styles['Normal']))
    elements.append(Paragraph(f"<b>Hora:</b> {time_in} - {time_out}", styles['Normal']))
    elements.append(Paragraph(f"<b>Descripción:</b> {description}", styles['Justify']))
    
    # Firma en PDF
    img_bytes = base64.b64decode(st.session_state.signature_data)
    img_stream = io.BytesIO(img_bytes)
    img_pdf = RLImage(img_stream, width=200, height=100, hAlign='RIGHT')
    elements.append(img_pdf)
    
    doc.build(elements)
    st.download_button(
        label="📄 Descargar PDF (.pdf)",
        data=buffer_pdf,
        file_name=f"Reporte_{company}.pdf",
        mime="application/pdf"
    )

    # C. DESCARGAR JPG (Imagen del Reporte)
    # Creamos una imagen blanca y escribimos encima para imitar el PDF
    img_jpg = Image.new('RGB', (600, 800), color=(255, 255, 255))
    d = ImageDraw.Draw(img_jpg)
    
    # Intentar usar fuente básica del sistema
    try:
        # Fuentes estándar de Windows/Linux
        font = ImageFont.truetype("arial.ttf", 20)
        font_peque = ImageFont.truetype("arial.ttf", 14)
    except:
        # Fallback si no encuentra arial (en Linux Cloud)
        font = ImageFont.load_default()
        font_peque = ImageFont.load_default()

    # Dibujar textos
    d.text((30, 50), "REPORTE DE VISITA", fill=(0, 0, 0), font=font)
    d.text((30, 100), f"Fecha: {date}", fill=(0, 0, 0), font=font_peque)
    d.text((30, 130), f"Empresa: {company}", fill=(0, 0, 0), font=font_peque)
    d.text((30, 160), f"Tecnico: {name}", fill=(0, 0, 0), font=font_peque)
    d.text((30, 190), f"Propósito: {purpose}", fill=(0, 0, 0), font=font_peque)
    d.text((30, 220), f"Horario: {time_in} - {time_out}", fill=(0, 0, 0), font=font_peque)
    
    # Descripción (multilínea simplificada)
    desc_text = description
    y_text = 280
    for line in desc_text.split('\n'):
        d.text((30, y_text), line, fill=(0,0,0), font=font_peque)
        y_text += 25

    # Pegar la firma
    firma_img = Image.open(io.BytesIO(img_bytes))
    # Redimensionar firma para que quepa en la imagen final
    firma_img = firma_img.resize((200, 100))
    img_jpg.paste(firma_img, (350, 650))
    
    # Guardar JPG en memoria
    buffer_jpg = io.BytesIO()
    img_jpg.save(buffer_jpg, format="JPEG", quality=95)
    
    st.download_button(
        label="🖼️ Descargar Imagen Reporte (.jpg)",
        data=buffer_jpg,
        file_name=f"Foto_Reporte_{company}.jpg",
        mime="image/jpeg"
    )
