import smtplib
import pandas as pd
import os
import mimetypes
import unicodedata
from email.message import EmailMessage

# --- Configuración de Correo ---
EMAIL_SENDER = ""
EMAIL_PASSWORD = ""  
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# --- Cargar datos de fraternos ---
csv_path = "databases/fraternos.csv"
image_folder = "afi_qr_codes"

if not os.path.exists(csv_path):
    print("⚠ No se encontró 'fraternos.csv'. Verifica la ruta.")
    exit()

df_fraternos = pd.read_csv(csv_path, dtype=str)
df_fraternos.columns = df_fraternos.columns.str.strip()
df_fraternos.rename(columns={"Matricula": "matricula", "Nombre Completo": "nombre", "Comite": "comite", "Correo": "correo"}, inplace=True)

# Filtrar solo los fraternos del comité 'AFI'
df_afi = df_fraternos[df_fraternos["comite"].str.upper() == "AFI"]

# --- Función para eliminar acentos y convertir espacios a '_' ---
def remove_accents(input_str):
    """ Elimina acentos y convierte espacios en '_' """
    return ''.join(
        c for c in unicodedata.normalize('NFD', input_str)
        if unicodedata.category(c) != 'Mn'
    ).replace(" ", "_")

# --- Función para enviar el correo ---
def send_email(to_email, name, qr_image):
    msg = EmailMessage()
    msg["Subject"] = f"📢 Bienvenidos al Mundial Contra el Cáncer edición XIII"
    msg["From"] = EMAIL_SENDER
    msg["To"] = to_email

    # Contenido HTML del correo
    html_content = f"""
    <html>
    <body style="font-family: Manrope, sans-serif; color: #333;">
        <h2 style="color: #412263;">✨ ¡Gracias por tu interés en ser parte de Phi Delta Epsilon! ✨</h2>
        <p>Querido/a <b>{name}</b>,</p>

        <p>Nos emociona mucho contar con tu participación en el <b>Mundial Contra el Cáncer edición XIII</b>.</p>

        <p>Sabemos que estás en tu proceso para convertirte en un fraterno y queremos decirte que participar en este evento es una excelente oportunidad para integrarte, conocer a los miembros de la fraternidad y crear conexiones valiosas.</p>

        <p>El compromiso y la dedicación que demuestres en estas actividades son fundamentales para tu integración, y estamos muy emocionados de recibirte. Este evento no solo es un espacio para aprender y colaborar, sino también para conocernos mejor y disfrutar juntos mientras apoyamos una causa tan importante.</p>

        <br><br>

        <h3>🛑 Importante: Registro de Asistencia con código QR</h3>
        <p>Para optimizar tiempos, utilizaremos <b>códigos QR</b> para la toma de asistencia.</p>
        <ul>
            <li>Dirígete a la mesa de registro con la imagen adjunta de tu QR.</li>
            <li><b>Escanea tu <b>check-in</b> y <b>check-out</b> para contar tus horas.</li>
            <li>Si no haces <b>check-out</b>, las horas <u>no serán contabilizadas</u>.</li>
        </ul>

        <p><b>Tu código QR es único e individual y no deberá ser compartido con los demás.</b> Es tu responsabilidad tu toma de asistencia.</p>

        <br><br>

        <h3>⏳ Horarios Flexibles</h3>
        <p>Puedes venir en diferentes momentos del día, por ejemplo, una hora por la mañana y otra por la tarde. Esto con el fin de que se acomode a tus horarios. Deberás de realizar check-in y check-out en cada ocasión para que sea contabilizada.</p>

        <p>Nos sentimos <b>afortunados</b> de que quieras formar parte de Phi Delta Epsilon. ¡Te esperamos con ansias en el evento y estamos seguros de que será el comienzo de algo increíble!</p>

        <p>En caso de algún error o comentario, favor de notificarme por este medio o WhatsApp.</p>

        <br><br>

        <p>Saludos, <br>
        <b>Marian Martínez</b> <br>
        <i>Secretaría Gestión 2025</i></p>
    </body>
    </html>
    """

    msg.set_content("Este correo requiere un cliente compatible con HTML.")
    msg.add_alternative(html_content, subtype="html")

    # Adjuntar imagen del QR en máxima calidad
    if os.path.exists(qr_image):
        with open(qr_image, "rb") as img:
            img_data = img.read()
            img_type = mimetypes.guess_type(qr_image)[0] or "application/octet-stream"
            msg.add_attachment(img_data, maintype="image", subtype="png", filename=os.path.basename(qr_image))
    else:
        print(f"⚠ No se encontró la imagen de QR para {name}.")

    # Enviar correo
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
            print(f"✅ Correo enviado a {name} ({to_email})")
    except Exception as e:
        print(f"❌ Error al enviar correo a {name}: {e}")

# --- Enviar correos solo a los fraternos AFI ---
for _, row in df_afi.iterrows():
    matricula = row["matricula"]
    nombre_completo = row["nombre"]
    correo = row["correo"]

    # Crear nombre de archivo seguro (sin espacios ni caracteres especiales)
    partes_nombre = nombre_completo.split()
    primer_nombre = partes_nombre[0] if len(partes_nombre) > 0 else "Desconocido"
    primer_apellido = partes_nombre[1] if len(partes_nombre) > 1 else "SinApellido"
    nombre_archivo = f"{primer_nombre}_{primer_apellido}".replace(" ", "_")

    # Ruta del QR
    qr_image = os.path.join(image_folder, f"QR_{nombre_archivo}.png")

    # Enviar el correo con el QR adjunto
    send_email(correo, nombre_completo, qr_image)