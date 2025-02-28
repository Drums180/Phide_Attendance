import streamlit as st
import sqlite3
import datetime
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from streamlit_qrcode_scanner import qrcode_scanner

# Configuración de la contraseña 🔐
PASSWORD = "fraternos2025"  # ✅ Cambia esto a la contraseña que quieras

# Cargar datos de fraternos desde CSV
csv_path = "databases/fraternos.csv"

if os.path.exists(csv_path):
    df_fraternos = pd.read_csv(csv_path, dtype=str)  # Cargar como string para evitar errores
    df_fraternos.columns = df_fraternos.columns.str.strip()  # Eliminar espacios en nombres de columnas
    df_fraternos.rename(columns={"Matricula": "matricula", "Nombre Completo": "nombre", "Comite": "comite"}, inplace=True)

    # Verificar que las columnas necesarias existen
    if not {"matricula", "nombre", "comite"}.issubset(df_fraternos.columns):
        st.error("⚠ 'fraternos.csv' no contiene las columnas necesarias ('matricula', 'nombre', 'comite').")
        df_fraternos = pd.DataFrame(columns=["matricula", "nombre", "comite"])
else:
    st.error("⚠ No se encontró el archivo 'fraternos.csv'. Verifica que esté en la carpeta 'databases/'.")
    df_fraternos = pd.DataFrame(columns=["matricula", "nombre", "comite"])

# Convertir CSV en un diccionario {matricula: {nombre, comité}}
fraternos = {row["matricula"]: {"nombre": row["nombre"], "comite": row["comite"]} for _, row in df_fraternos.iterrows()}

# Conectar a la base de datos
conn = sqlite3.connect("registro_asistencia.db", check_same_thread=False)
cursor = conn.cursor()

# Crear tabla si no existe (id autoincremental y matricula como FOREIGN KEY)
cursor.execute('''CREATE TABLE IF NOT EXISTS asistencia (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    matricula TEXT,
    nombre TEXT,
    comite TEXT,
    fecha TEXT,
    hora TEXT,
    tipo TEXT,
    FOREIGN KEY(matricula) REFERENCES fraternos(matricula)
)''')
conn.commit()

# Crear pestañas en la app
tab1, tab2, tab3, tab4 = st.tabs(["📋 Registro", "🔎 Historial de Asistencia", "📊 Horas por Comité", "📤 Exportar Datos"])

# --------------- PESTAÑA 1: Registro de Asistencia con Contraseña ---------------
with tab1:
    st.title("📋 Registro de Asistencia (Acceso Restringido 🔒)")

    # Solicitar contraseña antes de mostrar la pestaña
    password_input = st.text_input("Ingrese la contraseña para acceder:", type="password")

    if password_input == PASSWORD:
        st.success("✅ Contraseña correcta. Accediendo al registro...")

        # --------- Escaneo de Código QR ---------
        st.subheader("📷 Escaneo de Código QR")
        qr_code = qrcode_scanner("Escanea tu código QR")

        def registrar_asistencia(matricula):
            """ Función para registrar Check-in o Check-out """
            if matricula in fraternos:
                fraterno = fraternos[matricula]
                nombre = fraterno["nombre"]
                comite = fraterno["comite"]
                fecha_actual = datetime.date.today().strftime("%Y-%m-%d")
                hora_actual = datetime.datetime.now().strftime("%H:%M:%S")

                # Verificar si ya hizo check-in hoy
                cursor.execute("SELECT tipo FROM asistencia WHERE matricula=? AND fecha=? ORDER BY id DESC LIMIT 1",
                            (matricula, fecha_actual))
                ultimo_registro = cursor.fetchone()

                if not ultimo_registro or ultimo_registro[0] == "Check-out":
                    tipo_registro = "Check-in"
                else:
                    tipo_registro = "Check-out"

                # Guardar en la base de datos
                cursor.execute("INSERT INTO asistencia (matricula, nombre, comite, fecha, hora, tipo) VALUES (?, ?, ?, ?, ?, ?)",
                            (matricula, nombre, comite, fecha_actual, hora_actual, tipo_registro))
                conn.commit()

                st.success(f"✅ Registro exitoso: {tipo_registro} para {nombre}")
            else:
                st.error("⚠ Fraterno no encontrado en 'fraternos.csv'. Verifique la matrícula.")

        if qr_code:
            st.success(f"QR detectado: {qr_code}")
            registrar_asistencia(qr_code)

        # --------- Ingreso Manual de Matrícula ---------
        st.subheader("✍ Registro Manual")
        manual_matricula = st.text_input("Ingrese la matrícula del fraterno:")
        if st.button("Registrar Check-in / Check-out Manualmente"):
            registrar_asistencia(manual_matricula)

        # --------- Mostrar registros del día ---------
        st.subheader("📅 Registros del Día")
        df = pd.read_sql("SELECT * FROM asistencia WHERE fecha = ?", conn, params=(datetime.date.today().strftime("%Y-%m-%d"),))
        st.dataframe(df)

    elif password_input:
        st.error("❌ Contraseña incorrecta. Intente de nuevo.")
        
# --------------- PESTAÑA 2: Historial de Asistencia ---------------
with tab2:
    st.title("🔎 Historial de Asistencia")

    # Buscar fraterno por matrícula
    matricula = st.text_input("Ingrese la matrícula del fraterno para ver su historial")

    if matricula in fraternos:
        nombre = fraternos[matricula]["nombre"]
        st.subheader(f"Historial de asistencia de {nombre}")

        # Cargar historial del fraterno
        df_historial = pd.read_sql("SELECT * FROM asistencia WHERE matricula = ?", conn, params=(matricula,))

        if not df_historial.empty:
            # Convertir las columnas de fecha y hora
            df_historial["hora"] = pd.to_datetime(df_historial["hora"])
            df_historial["fecha"] = pd.to_datetime(df_historial["fecha"])
            df_historial["fecha_formateada"] = df_historial["fecha"].dt.strftime("%b %d")  # Formato Feb 23

            # Agrupar por fecha y calcular horas trabajadas
            horas_trabajadas = []
            fechas = []
            df_grouped = df_historial.groupby("fecha")

            for fecha, grupo in df_grouped:
                checkins = grupo[grupo["tipo"] == "Check-in"]["hora"].sort_values().tolist()
                checkouts = grupo[grupo["tipo"] == "Check-out"]["hora"].sort_values().tolist()

                horas_del_dia = 0
                for i in range(min(len(checkins), len(checkouts))):  # Solo contamos pares Check-in / Check-out
                    horas_del_dia += (checkouts[i] - checkins[i]).total_seconds() / 3600  # Convertir a horas

                if horas_del_dia > 0:
                    horas_trabajadas.append(horas_del_dia)
                    fechas.append(fecha.strftime("%b %d"))

            total_horas = sum(horas_trabajadas)
            st.metric(label="Total de Horas Trabajadas", value=f"{total_horas:.2f} horas")

            # Graficar las horas trabajadas por día (en color lila)
            st.subheader("📊 Horas trabajadas por día")
            fig, ax = plt.subplots(figsize=(8, 4))
            ax.bar(fechas, horas_trabajadas, color="#9370DB")  # Lila
            ax.set_xlabel("Fecha (Mes Día)")
            ax.set_ylabel("Horas Trabajadas")
            ax.set_title(f"Registro de Horas de {nombre}")
            ax.tick_params(axis='x', rotation=45)
            st.pyplot(fig)

            # Mostrar tabla de historial
            st.subheader("📋 Registro de Check-in / Check-out")
            st.dataframe(df_historial)

        else:
            st.warning(f"No hay registros para {nombre}")
    elif matricula:
        st.error("⚠ Fraterno no encontrado en 'fraternos.csv'. Verifique la matrícula.")

# --------------- PESTAÑA 3: Horas por Comité ---------------
with tab3:
    st.title("📊 Horas Totales por Comité")

    df_historial = pd.read_sql("SELECT * FROM asistencia", conn)

    if not df_historial.empty:
        df_historial["hora"] = pd.to_datetime(df_historial["hora"])
        df_historial["fecha"] = pd.to_datetime(df_historial["fecha"])
        df_historial["fecha_formateada"] = df_historial["fecha"].dt.strftime("%b %d")

        df_historial["horas"] = df_historial.groupby(["matricula", "fecha"])["hora"].diff().dt.total_seconds() / 3600
        df_historial = df_historial.dropna()

        df_comites = df_historial.groupby(["comite", "fecha_formateada"])["horas"].sum().reset_index()

        st.subheader("📊 Horas trabajadas por comité")
        fig, ax = plt.subplots(figsize=(10, 5))
        palette = sns.color_palette("husl")  # Paleta con lila incluido
        sns.barplot(data=df_comites, x="fecha_formateada", y="horas", hue="comite", ax=ax, palette=palette)
        ax.set_xlabel("Fecha (Mes Día)")
        ax.set_ylabel("Horas Trabajadas")
        ax.set_title("Horas trabajadas por comité")
        ax.tick_params(axis='x', rotation=45)
        st.pyplot(fig)

        st.dataframe(df_comites)
    else:
        st.warning("No hay registros aún.")
        
# --------------- PESTAÑA 4: Exportar Datos a CSV ---------------
with tab4:
    st.title("📤 Exportar Datos a CSV (Acceso Restringido 🔒)")

    # Solicitar contraseña antes de permitir la exportación
    export_password_input = st.text_input("Ingrese la contraseña para exportar los datos:", type="password")

    if export_password_input == PASSWORD:
        st.success("✅ Contraseña correcta. Puede exportar los datos.")

        df_asistencia = pd.read_sql("SELECT * FROM asistencia", conn)

        if not df_asistencia.empty:
            csv_path = "databases/registro_asistencia.csv"
            df_asistencia.to_csv(csv_path, index=False)

            with open(csv_path, "rb") as file:
                st.download_button("📥 Descargar CSV", file, "registro_asistencia.csv", "text/csv")
        else:
            st.warning("No hay datos en la base de datos para exportar.")
    
    elif export_password_input:
        st.error("❌ Contraseña incorrecta. Intente de nuevo.")