import sqlite3
import pandas as pd
import os

# Crear la carpeta si no existe
output_folder = "databases"
os.makedirs(output_folder, exist_ok=True)

# Conectar a la base de datos
conn = sqlite3.connect(os.path.join(output_folder, "registro_asistencia.db"))

# Leer los datos en un DataFrame con las nuevas columnas
df = pd.read_sql_query("SELECT id, nombre, comite, fecha, hora, tipo FROM asistencia", conn)

# Ruta completa para guardar el CSV en la carpeta databases
csv_path = os.path.join(output_folder, "registro_asistencia.csv")

# Guardar como CSV
df.to_csv(csv_path, index=False)

print(f"✅ Archivo exportado: {csv_path}")