import os
import pandas as pd

# Ruta de la base de datos de fraternos
csv_path = "databases/fraternos.csv"
# Ruta de la carpeta con las imágenes
image_folder = "formato_registro"

# Verificar si la base de datos existe
if not os.path.exists(csv_path):
    print("⚠ Error: No se encontró 'fraternos.csv'. Verifica la ruta.")
    exit()

# Cargar la base de datos de fraternos
df_fraternos = pd.read_csv(csv_path, dtype=str)
df_fraternos.columns = df_fraternos.columns.str.strip()
df_fraternos.rename(columns={"Matricula": "matricula", "Nombre Completo": "nombre", "Comite": "comite"}, inplace=True)

# Verificar si las columnas necesarias están presentes
if not {"matricula", "nombre", "comite"}.issubset(df_fraternos.columns):
    print("⚠ Error: 'fraternos.csv' no contiene las columnas necesarias ('matricula', 'nombre', 'comite').")
    exit()

# Obtener nombres ordenados alfabéticamente
nombres_ordenados = df_fraternos["nombre"].sort_values().tolist()

# Obtener lista de archivos en formato_registro ordenados numéricamente
imagenes = sorted([f for f in os.listdir(image_folder) if f.endswith(".png")], key=lambda x: int(os.path.splitext(x)[0]))

# Verificar que la cantidad de imágenes coincida con la cantidad de fraternos
if len(imagenes) != len(nombres_ordenados):
    print(f"⚠ Advertencia: Hay {len(imagenes)} imágenes pero {len(nombres_ordenados)} fraternos en la base de datos.")
    print("Revisa que los datos sean correctos antes de continuar.")

# Renombrar las imágenes
for i, nombre in enumerate(nombres_ordenados):
    nombre_limpio = nombre.replace(" ", "_").replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u").replace("ñ", "n")
    nuevo_nombre = f"{nombre_limpio}.png"
    
    imagen_actual = os.path.join(image_folder, imagenes[i])
    imagen_nueva = os.path.join(image_folder, nuevo_nombre)

    try:
        os.rename(imagen_actual, imagen_nueva)
        print(f"✅ {imagenes[i]} → {nuevo_nombre}")
    except Exception as e:
        print(f"❌ Error al renombrar {imagenes[i]}: {e}")

print("✅ Proceso de renombrado finalizado.")