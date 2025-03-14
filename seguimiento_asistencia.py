# los que estan en ciencias basicas (de 1er a 5to) 80% durante todo el semestre
# ciencias clinicas (6to a 10mo) tienen que cumplir con 70%

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from IPython.core.display import display

# Define the path to the font file (make sure this matches your file location)
font_path = "Pangram-Regular.ttf"

# Load the font
pangram_font = fm.FontProperties(fname=font_path)

# Verify the font is correctly loaded
print(f"Using font: {pangram_font.get_name()}")

# Function to apply the font to Matplotlib globally
def apply_custom_font(font_prop):
    plt.rcParams['font.family'] = font_prop.get_name()
    plt.rcParams['font.size'] = 14
    plt.rcParams['axes.titlesize'] = 16
    plt.rcParams['axes.labelsize'] = 14

# Apply the font globally
apply_custom_font(pangram_font)

# Cargar el dataset
file_path = "databases/asistencia_sesiones.csv"  # Asegúrate de cambiar la ruta si es necesario
df = pd.read_csv(file_path)

# Limpiar nombres de columnas
df.columns = df.columns.str.strip()

# Mapeo de valores de asistencia (ahora "Justificación" cuenta como 1)
attendance_values = {
    "Sí asistió": 1,
    "Llegada tarde": 0.5,
    "Justificación": 1,  # Ahora cuenta como asistencia
    "No asistió": 0,
    "Aviso de falta": 0
}

# Extraer las columnas de sesiones (a partir de la 4ta columna)
session_columns = df.columns[3:]

# Convertir valores de asistencia a numéricos
attendance_numeric = df[session_columns].replace(attendance_values)

# Calcular asistencia actual (sin contar sesiones futuras con NaN)
current_attendance = attendance_numeric.apply(lambda row: row.dropna().sum() / len(row.dropna()) * 100, axis=1)

# Calcular asistencia total (considerando sesiones futuras)
total_attendance = attendance_numeric.apply(lambda row: row.sum() / len(row) * 100, axis=1)

# Contar número de justificaciones por estudiante
justifications_count = df[session_columns].apply(lambda row: (row == "Justificación").sum(), axis=1)

# Calcular porcentaje de justificaciones usadas
max_justifications = 4
justifications_percentage = (justifications_count / max_justifications) * 100

# Crear dataframe con los cálculos
summary_df = pd.DataFrame({
    "Nombre completo": df["Nombre completo"],
    "Matrícula": df["Matrícula"],
    "Asistencia actual (%)": current_attendance,
    "Asistencia total (%)": total_attendance,
    "Justificaciones usadas (%)": justifications_percentage
})

# Seleccionar un estudiante de prueba (puedes cambiar el índice)
sample_student = summary_df.iloc[0]

# Función para gráfico de anillo (Donut chart) con mismo color en ambas asistencias
def plot_donut_chart(value, title, color):
    fig, ax = plt.subplots(figsize=(3.5, 3.5))
    wedges, texts = ax.pie(
        [value, 100 - value],
        colors=[color, "lightgray"],
        startangle=90,
        wedgeprops={'width': 0.3}
    )

    # Fuente estilizada en DejaVu Sans
    font_props = {"fontsize": 18, "fontweight": "bold", "family": pangram_font}

    # Texto en el centro con porcentaje
    ax.text(0, 0, f"{value:.0f}%", ha="center", va="center", **font_props)

    plt.title(title, fontsize=14, fontweight="bold", family= pangram_font)
    plt.show()

# Asignar colores según el porcentaje de asistencia actual
if sample_student["Asistencia actual (%)"] >= 80:
    color = "green"
elif sample_student["Asistencia actual (%)"] >= 50:
    color = "orange"
else:
    color = "red"

# Función para gráfico de barra de justificaciones usadas
def plot_progress_bar(value, title):
    fig, ax = plt.subplots(figsize=(4.5, 1))
    ax.barh(0, value, color="red", height=0.5, alpha=0.8)
    ax.barh(0, 100 - value, left=value, color="lightgray", height=0.5, alpha=0.5)
    
    ax.set_xlim(0, 100)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.axis("off")

    # Texto centrado dentro de la barra con fuente estilizada
    ax.text(value / 2, 0, f"{value:.0f}%", va="center", ha="center", fontsize=16, fontweight="bold", family= pangram_font, color="white")

    plt.title(title, fontsize=14, fontweight="bold", family= pangram_font)
    plt.show()

# Generar visualizaciones con el mismo color para asistencia total
plot_donut_chart(sample_student["Asistencia actual (%)"], "Asistencia Actual", color)
plot_donut_chart(sample_student["Asistencia total (%)"], "Asistencia Total", color)
plot_progress_bar(sample_student["Justificaciones usadas (%)"], "Justificaciones Usadas")