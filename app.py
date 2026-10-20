
import streamlit as st
import sqlite3
from pathlib import Path
from datetime import datetime, date, time
import pandas as pd

# ==========================================
# FACHADA VISUAL DE HUBSPACE
# ==========================================

st.markdown("""
<style>

/* Fondo general */
.stApp {
    background-color: #F3F7FC;
    color: #172B4D;
}

/* Ocultar elementos visuales predeterminados */
#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

/* Barra superior */
header[data-testid="stHeader"] {
    background-color: #F3F7FC;
}

/* Panel lateral */
section[data-testid="stSidebar"] {
    background-color: #102A43;
}

section[data-testid="stSidebar"] * {
    color: #FFFFFF;
}

/* Títulos */
h1, h2, h3 {
    color: #102A43;
}

/* Botones */
.stButton > button {
    background-color: #168AAD;
    color: white;
    border: none;
    border-radius: 10px;
    padding: 0.55rem 1rem;
    font-weight: 600;
    transition: 0.2s;
}

.stButton > button:hover {
    background-color: #126782;
    color: white;
    border: none;
}

/* Campos de entrada */
.stTextInput input,
.stSelectbox div[data-baseweb="select"],
.stDateInput input,
.stTimeInput input {
    border-radius: 8px;
}

/* Tablas */
[data-testid="stDataFrame"] {
    border: 1px solid #D9E4F2;
    border-radius: 10px;
}

/* Contenedores */
div[data-testid="stMetric"] {
    background-color: #FFFFFF;
    border: 1px solid #D9E4F2;
    padding: 18px;
    border-radius: 14px;
}

/* Separadores */
hr {
    border-color: #D9E4F2;
}

</style>
""", unsafe_allow_html=True)

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



opciones_menu = [
    "Inicio",
    "Espacios disponibles",
    "Nueva reserva",
    "Mis reservas",
    "Registro de uso",
    "Administración"
]

if "destino_hubspace" not in st.session_state:
    st.session_state["destino_hubspace"] = "Inicio"

if st.session_state["destino_hubspace"] not in opciones_menu:
    st.session_state["destino_hubspace"] = "Inicio"

seccion = st.sidebar.radio(
    "NAVEGACIÓN",
    opciones_menu,
    key="destino_hubspace"
)



if seccion == "Inicio":

    # Encabezado principal
    st.markdown("""
        <div style="
            background: linear-gradient(120deg, #102A43, #168AAD);
            padding: 32px;
            border-radius: 18px;
            color: white;
            margin-bottom: 25px;
        ">
            <p style="
                color: #BDEBFF;
                font-size: 14px;
                margin-bottom: 8px;
            ">HUB DE PROVIDENCIA · PLATAFORMA DE GESTIÓN</p>

            <h1 style="
                color: white;
                margin: 0;
                font-size: 36px;
            ">Bienvenido a HubSpace</h1>

            <p style="
                color: white;
                font-size: 17px;
                margin-top: 12px;
                margin-bottom: 0;
            ">
                Gestiona espacios, organiza reservas y consulta
                la actividad del Hub desde un solo lugar.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Indicadores de la plataforma
    st.subheader("Resumen de actividad")

    total_espacios = consultar_datos("""
        SELECT COUNT(*) AS total
        FROM espacios
        WHERE activo = 1
    """).iloc[0]["total"]

    total_reservas = consultar_datos("""
        SELECT COUNT(*) AS total
        FROM reservas
    """).iloc[0]["total"]

    pendientes = consultar_datos("""
        SELECT COUNT(*) AS total
        FROM reservas
        WHERE estado = 'pendiente'
    """).iloc[0]["total"]

    usos_activos = consultar_datos("""
        SELECT COUNT(*) AS total
        FROM registros_uso
        WHERE hora_salida IS NULL
    """).iloc[0]["total"]

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Espacios activos", int(total_espacios))
    col2.metric("Reservas registradas", int(total_reservas))
    col3.metric("Solicitudes pendientes", int(pendientes))
    col4.metric("Usos en curso", int(usos_activos))

    st.divider()

    # Accesos rápidos
    st.subheader("¿Qué necesitas hacer?")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### 📅 Reservar")
        st.write("Encuentra un espacio para tu próxima actividad.")
        if st.button("Nueva reserva", use_container_width=True):
            st.session_state["destino_hubspace"] = "Nueva reserva"
            st.rerun()

    with col2:
        st.markdown("### 🏢 Espacios")
        st.write("Consulta los espacios disponibles en el Hub.")
        if st.button("Ver espacios", use_container_width=True):
            st.session_state["destino_hubspace"] = "Espacios disponibles"
            st.rerun()

    with col3:
        st.markdown("### 🕒 Registro de uso")
        st.write("Registra ingresos y salidas de los espacios.")
        if st.button("Gestionar uso", use_container_width=True):
            st.session_state["destino_hubspace"] = "Registro de uso"
            st.rerun()

    st.divider()

    # Últimas reservas
    st.subheader("Actividad reciente")

    ultimas_reservas = consultar_datos("""
        SELECT
            r.id_reserva AS 'N.º reserva',
            u.nombre AS 'Usuario',
            e.nombre AS 'Espacio',
            r.inicio AS 'Inicio',
            r.termino AS 'Término',
            r.estado AS 'Estado'
        FROM reservas r
        JOIN usuarios u ON r.id_usuario = u.id_usuario
        JOIN espacios e ON r.id_espacio = e.id_espacio
        ORDER BY r.creada_en DESC
        LIMIT 5
    """)

    if ultimas_reservas.empty:
        st.info("Todavía no hay reservas registradas.")
    else:
        st.dataframe(
            ultimas_reservas,
            use_container_width=True,
            hide_index=True
        )

    st.caption(
        "HubSpace · Prototipo de gestión integrada de espacios"
    )


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

elif seccion == "Registro de uso":
    st.header("🕒 Registro de uso de espacios")
    st.write("Registra el ingreso y la salida de los usuarios.")

    # Mostrar reservas confirmadas
    reservas_uso = consultar_datos("""
        SELECT
            r.id_reserva AS codigo,
            u.nombre AS usuario,
            e.nombre AS espacio,
            r.inicio AS inicio,
            r.termino AS termino
        FROM reservas r
        JOIN usuarios u ON r.id_usuario = u.id_usuario
        JOIN espacios e ON r.id_espacio = e.id_espacio
        WHERE r.estado = 'confirmada'
        ORDER BY r.inicio
    """)

    if reservas_uso.empty:
        st.info("No hay reservas confirmadas para mostrar.")

    else:
        st.subheader("Reservas disponibles")
        st.dataframe(
            reservas_uso,
            use_container_width=True,
            hide_index=True
        )

        codigo = st.selectbox(
            "Selecciona el código de la reserva",
            reservas_uso["codigo"].tolist()
        )

        uso_actual = consultar_datos("""
            SELECT id_uso, hora_ingreso, hora_salida
            FROM registros_uso
            WHERE id_reserva = ?
            ORDER BY id_uso DESC
            LIMIT 1
        """, (codigo,))

        if uso_actual.empty or pd.notna(
            uso_actual.iloc[0]["hora_salida"]
        ):
            
            if st.button("🟢 Registrar ingreso"):
                try:
                    ahora_dt = datetime.now()
                    ahora = ahora_dt.strftime("%Y-%m-%d %H:%M:%S")
            
                    with sqlite3.connect(str(RUTA_BD)) as conexion:
                        conexion.execute("BEGIN IMMEDIATE")
            
                        reserva = conexion.execute("""
                            SELECT id_usuario, id_espacio, inicio, termino
                            FROM reservas
                            WHERE id_reserva = ?
                              AND estado = 'confirmada'
                        """, (codigo,)).fetchone()
            
                        if reserva is None:
                            raise ValueError(
                                "La reserva ya no existe o no está confirmada."
                            )
            
                        id_usuario, id_espacio, inicio, termino = reserva
            
                        inicio_dt = datetime.fromisoformat(inicio)
                        termino_dt = datetime.fromisoformat(termino)
            
                        if ahora_dt < inicio_dt:
                            raise ValueError(
                                "Todavía no comienza el horario reservado."
                            )
            
                        if ahora_dt > termino_dt:
                            raise ValueError(
                                "El horario de esta reserva ya terminó."
                            )
            
                        # Verificar si la reserva ya tiene un uso abierto
                        uso_abierto = conexion.execute("""
                            SELECT id_uso
                            FROM registros_uso
                            WHERE id_reserva = ?
                              AND hora_salida IS NULL
                            LIMIT 1
                        """, (codigo,)).fetchone()
            
                        if uso_abierto is not None:
                            raise ValueError(
                                "Esta reserva ya tiene un ingreso sin salida."
                            )
            
                        # Evitar que el mismo usuario tenga dos usos simultáneos
                        otro_uso = conexion.execute("""
                            SELECT ru.id_uso
                            FROM registros_uso ru
                            WHERE ru.id_usuario = ?
                              AND ru.hora_salida IS NULL
                            LIMIT 1
                        """, (id_usuario,)).fetchone()
            
                        if otro_uso is not None:
                            raise ValueError(
                                "Este usuario ya tiene otro uso en curso. "
                                "Debe registrar su salida primero."
                            )
            
                        conexion.execute("""
                            INSERT INTO registros_uso (
                                id_espacio,
                                id_usuario,
                                id_reserva,
                                hora_ingreso,
                                hora_salida
                            )
                            VALUES (?, ?, ?, ?, NULL)
                        """, (
                            id_espacio,
                            id_usuario,
                            codigo,
                            ahora
                        ))
            
                        conexion.commit()
            
                    st.success("Ingreso registrado correctamente.")
                    st.rerun()
            
                except ValueError as error:
                    st.warning(str(error))
            
                except Exception as error:
                    st.error("No se pudo registrar el ingreso.")
                    st.code(str(error))
                    
            if st.button("🔴 Registrar salida"):
                try:
                    ahora_dt = datetime.now()
                    ahora = ahora_dt.strftime("%Y-%m-%d %H:%M:%S")
                    id_uso = int(uso_actual.iloc[0]["id_uso"])
            
                    with sqlite3.connect(str(RUTA_BD)) as conexion:
                        conexion.execute("BEGIN IMMEDIATE")
            
                        registro = conexion.execute("""
                            SELECT hora_ingreso, hora_salida
                            FROM registros_uso
                            WHERE id_uso = ?
                        """, (id_uso,)).fetchone()
            
                        if registro is None:
                            raise ValueError(
                                "No se encontró el registro de ingreso."
                            )
            
                        hora_ingreso, hora_salida = registro
            
                        if hora_salida is not None:
                            raise ValueError(
                                "Este uso ya tiene una salida registrada."
                            )
            
                        ingreso_dt = datetime.fromisoformat(hora_ingreso)
            
                        if ahora_dt < ingreso_dt:
                            raise ValueError(
                                "La salida no puede ser anterior al ingreso."
                            )
            
                        cursor = conexion.execute("""
                            UPDATE registros_uso
                            SET hora_salida = ?
                            WHERE id_uso = ?
                              AND hora_salida IS NULL
                        """, (ahora, id_uso))
            
                        if cursor.rowcount != 1:
                            raise ValueError(
                                "No se pudo cerrar el registro de uso."
                            )
            
                        conexion.commit()
            
                    st.success("Salida registrada correctamente.")
                    st.rerun()
            
                except ValueError as error:
                    st.warning(str(error))
            
                except Exception as error:
                    st.error("No se pudo registrar la salida.")
                    st.code(str(error))

    st.divider()
    st.subheader("📋 Historial de uso de espacios")

    historial_uso = consultar_datos("""
        SELECT
            u.nombre AS Persona,
            e.nombre AS Espacio,
            ru.hora_ingreso AS Ingreso,
            ru.hora_salida AS Salida
        FROM registros_uso ru
        JOIN usuarios u ON ru.id_usuario = u.id_usuario
        JOIN espacios e ON ru.id_espacio = e.id_espacio
        ORDER BY ru.hora_ingreso DESC
    """)

    if historial_uso.empty:
        st.info("Todavía no hay registros de uso.")
    else:
        historial_uso["Ingreso"] = pd.to_datetime(
            historial_uso["Ingreso"], errors="coerce"
        )
        historial_uso["Salida"] = pd.to_datetime(
            historial_uso["Salida"], errors="coerce"
        )

        ahora = pd.Timestamp.now()
        salida_efectiva = historial_uso["Salida"].fillna(ahora)

        minutos = (
            (salida_efectiva - historial_uso["Ingreso"])
            .dt.total_seconds() / 60
        ).clip(lower=0)

        historial_uso["Tiempo de uso"] = minutos.apply(
            lambda m: (
                f"{int(m // 60)} h {int(m % 60)} min"
                if pd.notna(m) else "No disponible"
            )
        )

        historial_uso["Estado"] = historial_uso["Salida"].apply(
            lambda s: "Finalizado" if pd.notna(s) else "En curso"
        )

        historial_uso["Ingreso"] = historial_uso["Ingreso"].dt.strftime(
            "%d-%m-%Y %H:%M"
        ).fillna("No disponible")

        historial_uso["Salida"] = historial_uso["Salida"].apply(
            lambda s: s.strftime("%d-%m-%Y %H:%M")
            if pd.notna(s) else "Pendiente"
        )

        st.dataframe(
            historial_uso[
                ["Persona", "Espacio", "Ingreso", "Salida",
                 "Tiempo de uso", "Estado"]
            ],
            use_container_width=True,
            hide_index=True
        )

elif seccion == "Administración":
    st.header("🛠️ Administración")
    st.write("Revisa las solicitudes pendientes de autorización.")

    pendientes = consultar_datos("""
        SELECT r.id_reserva AS codigo,
               u.nombre AS solicitante,
               e.nombre AS espacio,
               r.inicio AS inicio,
               r.termino AS termino
        FROM reservas r
        JOIN usuarios u ON r.id_usuario = u.id_usuario
        JOIN espacios e ON r.id_espacio = e.id_espacio
        WHERE r.estado = 'pendiente'
        ORDER BY r.inicio
    """)

    if pendientes.empty:
        st.success("No hay solicitudes pendientes.")
    else:
        st.dataframe(
            pendientes,
            use_container_width=True,
            hide_index=True
        )

        codigo = st.selectbox(
            "Selecciona una solicitud",
            pendientes["codigo"].tolist()
        )

        col1, col2 = st.columns(2)

        with col1:
            aprobar = st.button("✅ Aprobar solicitud")

        with col2:
            rechazar = st.button("❌ Rechazar solicitud")
  
        if aprobar or rechazar:
            nuevo_estado = "confirmada" if aprobar else "rechazada"

            try:
                with sqlite3.connect(str(RUTA_BD)) as conexion:
                    reserva = conexion.execute("""
                        SELECT id_reserva, estado
                        FROM reservas
                        WHERE id_reserva = ?
                    """, (codigo,)).fetchone()

                    if reserva is None:
                        st.error("No se encontró la solicitud.")

                    elif reserva[1] != "pendiente":
                        st.warning(
                            f"La solicitud ya tiene estado: {reserva[1]}."
                        )

                    else:
                        conexion.execute("""
                            UPDATE reservas
                            SET estado = ?
                            WHERE id_reserva = ?
                        """, (nuevo_estado, codigo))

                        conexion.execute("""
                            INSERT INTO historial
                                (id_reserva, actor_id, accion, detalle)
                            VALUES (?, ?, ?, ?)
                        """, (
                            codigo,
                            reserva[0],
                            nuevo_estado,
                            f"Solicitud {nuevo_estado} desde Administración"
                        ))

                        conexion.commit()

                        estado_guardado = conexion.execute("""
                            SELECT estado
                            FROM reservas
                            WHERE id_reserva = ?
                        """, (codigo,)).fetchone()

                        if estado_guardado and estado_guardado[0] == nuevo_estado:
                            st.success(
                                f"¡Solicitud {codigo} actualizada! "
                                f"Estado: {nuevo_estado}."
                            )
                        else:
                            st.error(
                                "El estado no coincide con el esperado."
                            )

            except Exception as error:
                st.error("No se pudo actualizar la solicitud.")
                st.code(str(error))
