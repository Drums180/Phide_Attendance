import streamlit as st
import sqlite3
import datetime
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import pytz
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from streamlit_qrcode_scanner import qrcode_scanner

# ---------------- CONEXIÓN GOOGLE SHEETS ----------------
def conectar_google_sheets(sheet_name, worksheet_name):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["google_service_account"]
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(dict(creds_dict), scope)
    client = gspread.authorize(credentials)
    sheet = client.open(sheet_name).worksheet(worksheet_name)
    return sheet

# Función para guardar asistencia en Google Sheets
def guardar_registro_google(matricula, nombre, comite, fecha, hora, tipo):
    sheet = conectar_google_sheets("Registro Fraternos", "Asistencia")
    sheet.append_row([matricula, nombre, comite, fecha, hora, tipo])

# Función para leer la hoja completa desde Google Sheets
def leer_datos_google():
    sheet = conectar_google_sheets("Registro Fraternos", "Asistencia")
    data = sheet.get_all_records()
    return pd.DataFrame(data)

# Estado local de registros para evitar errores de Check-in/Check-out duplicados
registro_local = {}

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
            if matricula in fraternos:
                fraterno = fraternos[matricula]
                nombre = fraterno["nombre"]
                comite = fraterno["comite"]

                # Obtener hora actual con zona horaria de México
                mexico_tz = pytz.timezone("America/Mexico_City")
                ahora = datetime.datetime.now(mexico_tz)
                fecha_actual = ahora.strftime("%Y-%m-%d")
                hora_actual = ahora.strftime("%H:%M:%S")

                st.write(f"📅 Fecha actual: {fecha_actual} / 🕒 Hora actual: {hora_actual}")

                # Leer historial desde Google Sheets
                df_existente = leer_datos_google()
                df_existente["matricula"] = df_existente["matricula"].astype(str).str.strip()
                matricula = str(matricula).strip()

                df_usuario = df_existente[df_existente["matricula"] == matricula].copy()
                st.write(f"🔍 Registros encontrados en Google Sheets para esta matrícula: {len(df_usuario)}")

                tipo_registro = "Check-in"  # Valor por defecto

                if not df_usuario.empty:
                    df_usuario["fecha"] = pd.to_datetime(df_usuario["fecha"], errors="coerce")
                    df_usuario["hora"] = pd.to_datetime(df_usuario["hora"], format="%H:%M:%S", errors="coerce")
                    df_usuario["fecha_date"] = df_usuario["fecha"].dt.date

                    fecha_actual_dt = datetime.datetime.strptime(fecha_actual, "%Y-%m-%d").date()
                    df_hoy = df_usuario[df_usuario["fecha_date"] == fecha_actual_dt]

                    st.write(f"📘 Registros hoy: {len(df_hoy)}")
                    st.write(df_hoy[["fecha", "hora", "tipo"]])

                    if not df_hoy.empty:
                        ultimo_registro = df_hoy.sort_values(by="hora").iloc[-1]
                        if ultimo_registro["tipo"] == "Check-in":
                            tipo_registro = "Check-out"

                guardar_registro_google(matricula, nombre, comite, fecha_actual, hora_actual, tipo_registro)
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
        mexico_tz = pytz.timezone("America/Mexico_City")
        hoy = datetime.datetime.now(mexico_tz).strftime("%Y-%m-%d")
        df = leer_datos_google()
        if "fecha" in df.columns:
            st.dataframe(df[df["fecha"] == hoy])
        else:
            st.info("No hay registros aún para mostrar.")
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
        df_historial = leer_datos_google()
        df_historial = df_historial[df_historial["matricula"] == matricula]

        if not df_historial.empty:
            # Convertir las columnas de fecha y hora
            df_historial["hora"] = pd.to_datetime(df_historial["hora"])
            df_historial["fecha"] = pd.to_datetime(df_historial["fecha"], format="%Y-%m-%d")
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

    df_historial = leer_datos_google()

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

        df_asistencia = leer_datos_google()

        if not df_asistencia.empty:
            csv_path = "databases/registro_asistencia.csv"
            df_asistencia.to_csv(csv_path, index=False)

            with open(csv_path, "rb") as file:
                st.download_button("📥 Descargar CSV", file, "registro_asistencia.csv", "text/csv")
        else:
            st.warning("No hay datos en la base de datos para exportar.")

    elif export_password_input:
        st.error("❌ Contraseña incorrecta. Intente de nuevo.")
