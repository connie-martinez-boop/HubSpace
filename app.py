
import streamlit as st
import sqlite3
from pathlib import Path
from datetime import datetime, date, time
import pandas as pd

st.set_page_config(
    page_title="HubSpace",
    page_icon="🏢",
    layout="wide"
)

RUTA_BD = Path(__file__).parent / "hubspace.db"


def consultar_datos(consulta, parametros=()):
    with sqlite3.connect(str(RUTA_BD)) as conexion:
        return pd.read_sql_query(
            consulta, conexion, params=parametros
        )


def crear_reserva(id_usuario, id_espacio, inicio, termino):
    inicio_dt = datetime.fromisoformat(inicio)
    termino_dt = datetime.fromisoformat(termino)

    if inicio_dt >= termino_dt:
        return False, "La hora de término debe ser posterior al inicio."

    with sqlite3.connect(str(RUTA_BD)) as conexion:
        conexion.execute("PRAGMA foreign_keys = ON")

        usuario = conexion.execute(
            "SELECT id_usuario FROM usuarios "
            "WHERE id_usuario = ? AND activo = 1",
            (id_usuario,)
        ).fetchone()

        espacio = conexion.execute(
            "SELECT requiere_autorizacion FROM espacios "
            "WHERE id_espacio = ? AND activo = 1",
            (id_espacio,)
        ).fetchone()

        if usuario is None or espacio is None:
            return False, "El usuario o el espacio no está disponible."

        conflicto = conexion.execute("""
            SELECT id_reserva
            FROM reservas
            WHERE id_espacio = ?
              AND estado IN ('confirmada', 'pendiente')
              AND inicio < ?
              AND termino > ?
        """, (id_espacio, termino, inicio)).fetchone()

        if conflicto:
            return False, (
                "Ese horario se cruza con otra solicitud o reserva. "
                "Prueba con otro horario."
            )

        estado = (
            "pendiente" if espacio[0] == 1 else "confirmada"
        )

        with conexion:
            cursor = conexion.execute("""
                INSERT INTO reservas
                    (id_usuario, id_espacio, inicio, termino, estado)
                VALUES (?, ?, ?, ?, ?)
            """, (id_usuario, id_espacio, inicio, termino, estado))

            id_reserva = cursor.lastrowid

            conexion.execute("""
                INSERT INTO historial
                    (id_reserva, actor_id, accion, detalle)
                VALUES (?, ?, ?, ?)
            """, (
                id_reserva,
                id_usuario,
                "creacion",
                f"Reserva creada con estado: {estado}"
            ))

    return True, f"Solicitud registrada. Código: {id_reserva}. Estado: {estado}."


st.title("🏢 HubSpace")
st.subheader("Sistema integrado de reserva y uso de espacios")

st.info(
    "Prototipo académico con datos ficticios. "
    "No utilizar para gestionar reservas reales."
)

seccion = st.sidebar.radio(
    "Navegación",
    ["Inicio", "Espacios disponibles", "Nueva reserva", "Mis reservas"]
)

if seccion == "Inicio":
    st.header("¡Bienvenido a HubSpace!")
    st.write(
        "Consulta espacios, solicita reservas y revisa "
        "la información de uso del edificio."
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("Módulos", "4")
    col2.metric("Base de datos", "SQLite")
    col3.metric("Estado", "Prototipo")

elif seccion == "Espacios disponibles":
    st.header("🏢 Espacios disponibles")

    espacios = consultar_datos("""
        SELECT nombre AS 'Nombre',
               tipo AS 'Tipo',
               capacidad AS 'Capacidad',
               CASE WHEN requiere_autorizacion = 1
                    THEN 'Sí' ELSE 'No'
               END AS 'Requiere autorización'
        FROM espacios
        WHERE activo = 1
        ORDER BY tipo, nombre
    """)

    st.dataframe(espacios, use_container_width=True, hide_index=True)
    st.caption(f"Total de espacios registrados: {len(espacios)}")

elif seccion == "Nueva reserva":
    st.header("📅 Crear una reserva")
    st.write("Completa los datos para registrar tu solicitud.")

    usuarios = consultar_datos("""
        SELECT id_usuario, nombre
        FROM usuarios
        WHERE activo = 1 AND rol = 'usuario'
        ORDER BY nombre
    """)

    espacios = consultar_datos("""
        SELECT id_espacio, nombre, tipo, requiere_autorizacion
        FROM espacios
        WHERE activo = 1
        ORDER BY nombre
    """)

    if usuarios.empty or espacios.empty:
        st.warning("Faltan usuarios o espacios en la base de datos.")
    else:
        with st.form("formulario_reserva"):
            usuario_elegido = st.selectbox(
                "Persona que solicita",
                usuarios["id_usuario"].tolist(),
                format_func=lambda x: usuarios.loc[
                    usuarios["id_usuario"] == x, "nombre"
                ].iloc[0]
            )

            espacio_elegido = st.selectbox(
                "Espacio",
                espacios["id_espacio"].tolist(),
                format_func=lambda x: espacios.loc[
                    espacios["id_espacio"] == x, "nombre"
                ].iloc[0]
            )

            fecha = st.date_input(
                "Fecha de la reserva",
                value=date.today()
            )

            col1, col2 = st.columns(2)

            with col1:
                hora_inicio = st.time_input(
                    "Hora de inicio", value=time(10, 0)
                )

            with col2:
                hora_termino = st.time_input(
                    "Hora de término", value=time(11, 0)
                )

            enviar = st.form_submit_button("Registrar solicitud")

        if enviar:
            inicio = datetime.combine(
                fecha, hora_inicio
            ).isoformat(timespec="minutes")

            termino = datetime.combine(
                fecha, hora_termino
            ).isoformat(timespec="minutes")

            correcto, mensaje = crear_reserva(
                usuario_elegido,
                espacio_elegido,
                inicio,
                termino
            )

            if correcto:
                st.success(mensaje)
            else:
                st.error(mensaje)

elif seccion == "Mis reservas":
    st.header("📋 Historial de reservas")

    usuarios = consultar_datos("""
        SELECT id_usuario, nombre
        FROM usuarios
        WHERE activo = 1 AND rol = 'usuario'
        ORDER BY nombre
    """)

    if usuarios.empty:
        st.warning("No hay usuarios registrados.")
    else:
        usuario_elegido = st.selectbox(
            "Selecciona una persona",
            usuarios["id_usuario"].tolist(),
            format_func=lambda x: usuarios.loc[
                usuarios["id_usuario"] == x, "nombre"
            ].iloc[0]
        )

        reservas = consultar_datos("""
            SELECT r.id_reserva AS 'Código',
                   e.nombre AS 'Espacio',
                   r.inicio AS 'Inicio',
                   r.termino AS 'Término',
                   r.estado AS 'Estado'
            FROM reservas r
            JOIN espacios e ON r.id_espacio = e.id_espacio
            WHERE r.id_usuario = ?
            ORDER BY r.inicio DESC
        """, (usuario_elegido,))

        if reservas.empty:
            st.info("Esta persona todavía no tiene reservas.")
        else:
            st.dataframe(
                reservas, use_container_width=True, hide_index=True
            )

        except Exception as error:
            st.error("No se pudo consultar la base de datos.")
            st.caption(str(error))

