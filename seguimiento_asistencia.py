import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

# 📌 Load custom font (Pangram or fallback)
try:
    font_path = "Pangram-Regular.ttf"
    pangram_font = fm.FontProperties(fname=font_path)
    font_name = pangram_font.get_name()
    print(f"✅ Using font: {font_name}")
except Exception:
    print("⚠ Font not found, using default.")
    pangram_font = fm.FontProperties(family="DejaVu Sans")

# ✅ Apply font globally in Matplotlib
plt.rcParams["font.family"] = pangram_font.get_name()
plt.rcParams["axes.titlesize"] = 16
plt.rcParams["axes.labelsize"] = 14
plt.rcParams["font.size"] = 14

# 📌 Load datasets
df_asistencia = pd.read_csv("databases/asistencia_sesiones.csv")
df_fraternos = pd.read_csv("databases/fraternos.csv")

# ✅ Clean column names
df_asistencia.columns = df_asistencia.columns.str.strip()
df_fraternos.columns = df_fraternos.columns.str.strip()

# 📌 Attendance value mapping
attendance_values = {
    "Sí asistió": 1,
    "Llegada tarde": 0.5,
    "Justificación": 1,
    "No asistió": 0,
    "Aviso de falta": 0
}

# Extract session columns
session_columns = df_asistencia.columns[3:]
attendance_numeric = df_asistencia[session_columns].replace(attendance_values)

# 📌 Calculate attendance percentages
num_sesiones_actuales = df_asistencia[session_columns].dropna(how="all", axis=1).shape[1]
porcentaje_maximo_posible = (num_sesiones_actuales / len(session_columns)) * 100
current_attendance = attendance_numeric.apply(lambda row: row.dropna().sum() / len(row.dropna()) * 100, axis=1)
total_attendance = attendance_numeric.apply(lambda row: row.sum() / len(row) * 100, axis=1)
justifications_count = df_asistencia[session_columns].apply(lambda row: (row == "Justificación").sum(), axis=1)
justifications_percentage = (justifications_count / 4) * 100  # 4 is the max allowed

# 📌 Clean `Semestre` column
df_asistencia["Semestre"] = df_asistencia["Semestre"].astype(str).str.replace("°", "", regex=True).astype(float)
df_asistencia["Semestre"] = pd.to_numeric(df_asistencia["Semestre"], errors="coerce")

# 📌 Merge fraternos data (add email)
df_merged = df_asistencia.merge(df_fraternos[["Matricula", "Correo"]], left_on="Matricula", right_on="Matricula", how="left")

# 📌 Add attendance calculations to merged data
df_merged["Asistencia actual (%)"] = current_attendance
df_merged["Asistencia total (%)"] = total_attendance
df_merged["Justificaciones usadas (%)"] = justifications_percentage

# 📌 Create summary DataFrame
summary_df = df_merged[["Nombre completo", "Matricula", "Semestre", "Correo", "Asistencia actual (%)", "Asistencia total (%)", "Justificaciones usadas (%)"]]

# Select a sample student
sample_student = summary_df.iloc[1]
nombre = sample_student["Nombre completo"]
semestre = int(sample_student["Semestre"])
correo = sample_student["Correo"]

# 📌 Determine required attendance based on semester
required_attendance = 80 if semestre <= 5 else 70

# 📌 Define color scale for attendance performance
def get_attendance_color(value):
    if value >= 80:
        return "green"
    elif value >= 50:
        return "orange"
    return "red"

# 📌 Generate attendance donut chart
def plot_donut_chart(value, filename, color):
    fig, ax = plt.subplots(figsize=(3.5, 3.5))
    ax.pie([value, 100 - value], colors=[color, "lightgray"], startangle=90, wedgeprops={'width': 0.3})
    ax.text(0, 0, f"{value:.0f}%", ha="center", va="center", fontsize=18, fontweight="bold", fontproperties=pangram_font)
    plt.axis("equal")
    plt.savefig(filename, bbox_inches="tight", transparent=True)
    plt.close()

# 📌 Generate justifications bar chart
def plot_progress_bar(value, filename):
    fig, ax = plt.subplots(figsize=(4.5, 1))
    ax.barh(0, value, color="red", height=0.5, alpha=0.8)
    ax.barh(0, 100 - value, left=value, color="lightgray", height=0.5, alpha=0.5)
    ax.set_xlim(0, 100)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.axis("off")
    ax.text(value / 2, 0, f"{value:.0f}%", va="center", ha="center", fontsize=16, fontweight="bold", fontproperties=pangram_font, color="white")
    plt.savefig(filename, bbox_inches="tight", transparent=True)
    plt.close()

# Assign color for total attendance based on actual attendance
color_actual = get_attendance_color(sample_student["Asistencia actual (%)"])
color_total = color_actual  # ✅ Keep the same color for consistency

plot_donut_chart(sample_student["Asistencia actual (%)"], "attendance_actual.png", color_actual)
plot_donut_chart(sample_student["Asistencia total (%)"], "attendance_total.png", color_total)
plot_progress_bar(sample_student["Justificaciones usadas (%)"], "justifications.png")

# 📌 Email setup
sender_email = "marian.martinezu@udem.edu"
password = os.getenv("EMAIL_PASSWORD")  # ⚠ Use environment variable for security

# 📌 Loop through all students and send emails
for index, student in summary_df.iterrows():
    nombre = student["Nombre completo"]
    semestre = int(student["Semestre"])
    correo = student["Correo"]

    if pd.isna(correo):  # Skip students without email
        print(f"❌ No email registered for {nombre}, skipping...")
        continue

    required_attendance = 80 if semestre <= 5 else 70
    color_actual = get_attendance_color(student["Asistencia actual (%)"])
    color_total = color_actual  # ✅ Keep the same color for consistency

    plot_donut_chart(student["Asistencia actual (%)"], "attendance_actual.png", color_actual)
    plot_donut_chart(student["Asistencia total (%)"], "attendance_total.png", color_total)
    plot_progress_bar(student["Justificaciones usadas (%)"], "justifications.png")

    # 📌 Mensaje según el color de asistencia actual
    if color_actual == "green":
        asistencia_mensaje = "¡Vas excelente! Sigue así y mantén tu compromiso."
    elif color_actual == "orange":
        asistencia_mensaje = "Cuidado, algunas faltas más podrían afectar tu cumplimiento. Asegúrate de mantener tu asistencia en los próximos eventos."
    else:  # Rojo
        asistencia_mensaje = "Es muy importante evitar más faltas para no afectar el cumplimiento del reglamento."

    # 📌 Mensaje según justificaciones usadas
    if student["Justificaciones usadas (%)"] == 0:
        justificaciones_mensaje = "No has utilizado ninguna justificación, por lo que aún cuentas con las 4 disponibles."
    elif student["Justificaciones usadas (%)"] < 100:
        justificaciones_mensaje = "Has utilizado algunas justificaciones. Asegúrate de administrar bien las restantes para evitar problemas futuros."
    else:
        justificaciones_mensaje = "Has utilizado todas tus justificaciones. Cualquier falta adicional será contabilizada como inasistencia, sin posibilidad de justificación."

    # 📌 Email HTML Content
    msg = MIMEMultipart("related")
    msg["Subject"] = "PhiDE | Progreso de asistencia PR´25"
    msg["From"] = sender_email
    msg["To"] = correo

    html_content = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: "{pangram_font.get_name()}", sans-serif;
                color: #333;
            }}
            .container {{
                width: 600px;
                padding: 20px;
                border-radius: 10px;
                background: #f8f9fa;
                text-align: left;
            }}
            .title {{
                font-size: 22px;
                font-weight: bold;
                color: #9D4EDD;
            }}
            .highlight {{
                font-size: 18px;
                font-weight: bold;
                color: #008000;
            }}
            .warning {{
                font-size: 18px;
                font-weight: bold;
                color: #FF8C00;
            }}
            .alert {{
                font-size: 18px;
                font-weight: bold;
                color: #FF0000;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <p class="title">Querid@ {nombre},</p>
            <p>La asistencia es un compromiso fundamental para permanecer como miembro activo de PhiDE. 
            Según el reglamento, debes cumplir con al menos <b>{required_attendance}%</b> de asistencia durante el semestre.</p>
            
            <p><b>Puntos a tomar en cuenta:</b></p>
            <ul style="text-align: left; list-style-position: inside; padding-left: 20px;">
                <li>Las faltas deben justificarse con al menos 48 horas de anticipación (si es posible).</li>
                <li>Las justificaciones deben enviarse a <b><a href="mailto:marian.martinezu@udem.edu">marian.martinezu@udem.edu</a></b>.</li>
                <li>Solo se permiten <b>4 faltas justificadas</b> en todo el semestre.</li>
            </ul>

            <p>Actualmente se han llevado a cabo <b>{num_sesiones_actuales}</b> sesiones. Este es tu progreso:</p>

            <img src="cid:attendance_actual" width="200px">
            <p>Tu asistencia actual: <b class="{ 'highlight' if color_actual == 'green' else 'warning' if color_actual == 'orange' else 'alert' }">
    {student["Asistencia actual (%)"]:.1f}%</b></p>
            <p><b class="{ 'highlight' if color_actual == 'green' else 'warning' if color_actual == 'orange' else 'alert' }">{asistencia_mensaje}</b></p>

            <img src="cid:attendance_total" width="200px">
            <p>El porcentaje esperado hasta hoy es de <b>{porcentaje_maximo_posible:.1f}%</b>. Si vas bien en tu progreso actual, es muy probable que termines con un porcentaje adecuado.</p>

            <img src="cid:justifications" width="250px">
            <p>Justificaciones usadas: <b>{student["Justificaciones usadas (%)"]:.1f}%</b></p>
            <p><b class="{ 'highlight' if student['Justificaciones usadas (%)'] == 0 else 'warning' if student['Justificaciones usadas (%)'] < 100 else 'alert' }">{justificaciones_mensaje}</b></p>

            <p>Muchas gracias por tu compromiso con la familia PhiDE.<br>
            Si tienes dudas o crees que hay un error en tu registro, contesta este correo.</p>

            <p>Atentamente, <br> <b>Secretaría Marian Martínez</b></p>
        </div>
    </body>
    </html>
    """

    msg.attach(MIMEText(html_content, "html"))

    # Attach images
    for img_path, cid in [("attendance_actual.png", "attendance_actual"), ("attendance_total.png", "attendance_total"), ("justifications.png", "justifications")]:
        with open(img_path, "rb") as img_file:
            img = MIMEImage(img_file.read(), name=os.path.basename(img_path))
            img.add_header("Content-ID", f"<{cid}>")
            msg.attach(img)

    # 📌 Send Email
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, correo, msg.as_string())

    print(f"✅ Email sent successfully to {nombre} -> {correo}")