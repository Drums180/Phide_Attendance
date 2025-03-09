import qrcode
import os
import pandas as pd

# Crear la carpeta para guardar los QR
output_folder = "afi_qr_codes"
os.makedirs(output_folder, exist_ok=True)

# Ruta del archivo CSV
csv_path = "databases/fraternos.csv"

# Verificar si el archivo existe
if os.path.exists(csv_path):
    df_fraternos = pd.read_csv(csv_path, dtype=str)  # Cargar como string para evitar errores
    df_fraternos.columns = df_fraternos.columns.str.strip()  # Eliminar espacios en nombres de columnas
    df_fraternos.rename(columns={"Matricula": "id", "Nombre Completo": "nombre", "Comite": "comite"}, inplace=True)

    # Verificar que las columnas necesarias existen
    if {"id", "nombre", "comite"}.issubset(df_fraternos.columns):
        # Filtrar solo los fraternos con el valor 'AFI' en la columna 'comite'
        df_afi = df_fraternos[df_fraternos["comite"].str.upper() == "AFI"]

        # Generar y guardar los QR dentro de la carpeta especificada
        for _, row in df_afi.iterrows():
            matricula = row["id"]
            nombre_completo = row["nombre"]

            # Dividir el nombre en partes
            partes_nombre = nombre_completo.split()

            # Obtener el primer nombre y primer apellido
            primer_nombre = partes_nombre[0] if len(partes_nombre) > 0 else "Desconocido"
            primer_apellido = partes_nombre[1] if len(partes_nombre) > 1 else "SinApellido"

            # Crear nombre de archivo seguro (sin espacios ni caracteres especiales)
            nombre_archivo = f"{primer_nombre}_{primer_apellido}".replace(" ", "_")

            # Generar QR con el valor de la matrícula
            qr = qrcode.make(matricula)  
            qr_path = os.path.join(output_folder, f"QR_{nombre_archivo}.png")  # Ruta de guardado
            qr.save(qr_path)  # Guarda el QR en la carpeta

            print(f"✅ QR generado y guardado en {qr_path} para {nombre_completo} ({matricula})")

        if df_afi.empty:
            print("⚠ No se encontraron fraternos con el valor 'AFI' en la columna 'Comite'.")
    else:
        print("⚠ ERROR: 'fraternos.csv' no contiene las columnas necesarias ('id', 'nombre', 'comite').")
else:
    print("⚠ ERROR: No se encontró el archivo 'fraternos.csv'. Verifica que esté en la carpeta 'databases/'.")