import pandas as pd

# 📌 Cargar las bases de datos
asistencia_path = "databases/asistencia_sesiones.csv"
fraternos_path = "databases/fraternos.csv"

# Leer ambas bases
df_asistencia = pd.read_csv(asistencia_path)
df_fraternos = pd.read_csv(fraternos_path)

# Limpiar nombres de columnas
df_asistencia.columns = df_asistencia.columns.str.strip()
df_fraternos.columns = df_fraternos.columns.str.strip()

# 📌 Hacer merge en base a la columna "Matrícula"
df_merged = df_asistencia.merge(df_fraternos[["Matricula", "Correo"]], on="Matricula", how="left")

# 📌 Imprimir el nombre del fraterno y su correo correspondiente
for _, row in df_merged.iterrows():
    nombre = row["Nombre completo"]
    correo = row["Correo"]

    if pd.isna(correo):
        print(f"🔴 {nombre} NO tiene correo registrado.")
    else:
        print(f"✅ {nombre} -> {correo}")

sin_correo = df_merged[df_merged["Correo"].isna()]
print(sin_correo[["Nombre completo", "Matricula"]])