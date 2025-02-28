import smtplib
import pandas as pd
import os
import mimetypes
import unicodedata
from email.message import EmailMessage

# --- Configuración de Correo ---
EMAIL_SENDER = "marian.martinezu@udem.edu"
EMAIL_PASSWORD = "_Mares209*!"  
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# --- Cargar datos de fraternos ---
csv_path = "databases/fraternos.csv"
image_folder = "formato_registro"

if not os.path.exists(csv_path):
    print("⚠ No se encontró 'fraternos.csv'. Verifica la ruta.")
    exit()

df_fraternos = pd.read_csv(csv_path, dtype=str)
df_fraternos.columns = df_fraternos.columns.str.strip()
df_fraternos.rename(columns={"Matricula": "matricula", "Nombre Completo": "nombre", "Comite": "comite", "Correo": "correo"}, inplace=True)

# --- Diccionario de enlaces de WhatsApp por comité ---
whatsapp_groups = {
    "Registro": "https://chat.whatsapp.com/D6gOUnA901dC658qochoa6",
    "Canchas": "https://chat.whatsapp.com/ID0s81BEkhtF86zrJLd3ei",
    "Imagen": "https://chat.whatsapp.com/CdczK8Cs1wBAUuT8BC9QQo",
    "Mesa": "https://www.youtube.com/watch?v=wv_dJvjuC04"
}

# --- Función para eliminar acentos y convertir espacios a '_' ---
def remove_accents(input_str):
    """ Elimina acentos y convierte espacios en '_' """
    return ''.join(
        c for c in unicodedata.normalize('NFD', input_str)
        if unicodedata.category(c) != 'Mn'
    ).replace(" ", "_")

# --- Función para enviar el correo ---
def send_email(to_email, name, comite, qr_image):
    msg = EmailMessage()
    msg["Subject"] = f"📢 Importante: Registro de Asistencia Mundial PHIDE 2025"
    msg["From"] = EMAIL_SENDER
    msg["To"] = to_email

    # Obtener enlace de WhatsApp del comité
    whatsapp_link = whatsapp_groups.get(comite, None)
    whatsapp_message = (
        f'<p><b>Recuerda ingresar al grupo de WhatsApp de tu comité:</b> '
        f'<a href="{whatsapp_link}">Click aquí</a></p>'
        if whatsapp_link else
        "<p><b>Recuerda preguntar por el grupo de WhatsApp de tu comité en caso de que haya uno disponible.</b></p>"
    )

    # Contenido HTML del correo
    html_content = f"""
    <html>
    <body style="font-family: Manrope, sans-serif; color: #333;">
        <h2 style="color: #412263;">✨ ¡Gracias por ser parte del Mundial Contra el Cáncer edición XIII! ✨</h2>
        <p>Querido/a <b>{name}</b>,</p>

        <p>Nos llena de alegría contar contigo en el comité <b>{comite}</b>. Tu apoyo es <i>clave</i> para el éxito del evento.</p>
        
        {whatsapp_message}

        <br><br> <!-- Aquí agregamos el espacio en blanco -->

        <h3>🛑 Importante: Registro de Asistencia con código QR</h3>
        <p>Para optimizar tiempos, utilizaremos <b>códigos QR</b> para la toma de asistencia.</p>
        <ul>
            <li>Dirígete a la mesa de registro con la imagen adjunta de tu QR.</li>
            <li><b>Escanea tu <b>check-in</b> y <b>check-out</b> para contar tus horas.</li>
            <li>Si no haces <b>check-out</b>, las horas <u>no serán contabilizadas</u>.</li>
        </ul>

        <p><b>Tu código QR es único e individual y no deberá ser compartido con los demás.</b> Es tu responsabilidad tu toma de asistencia.</p>

        <br><br> <!-- Aquí agregamos el espacio en blanco -->

        <h3>⏳ Horarios Flexibles</h3>
        <p>Puedes venir en diferentes momentos del día, por ejemplo, una hora por la mañana y otra por la tarde. Esto con el fin de que se acomode a tus horarios. Deberás de realizar check-in y check-out en cada ocasión para que sea contabilizada.</p>

        <p>Nos sentimos <b>afortunados</b> de que seas parte de la fraternidad. Sin ti, este evento no sería posible. 💜</p>

        <p>En caso de algún error o comentario, favor de notificarme por este medio o WhatsApp.</p>

        <br><br> <!-- Aquí agregamos el espacio en blanco -->

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

# --- ENVÍO MASIVO DE CORREOS A TODOS LOS FRATERNOS ---
print("🚀 Enviando correos a todos los fraternos...")

for _, row in df_fraternos.iterrows():
    email = row["correo"]
    name = row["nombre"]
    comite = row["comite"]

    # Quitar acentos del nombre antes de buscar la imagen
    normalized_name = remove_accents(name)
    qr_image = os.path.join(image_folder, f"{normalized_name}.png")

    print(f"🔹 Enviando correo a {name} ({email}) del comité {comite}...")
    send_email(email, name, comite, qr_image)

print("✅ ¡Todos los correos han sido enviados exitosamente!")