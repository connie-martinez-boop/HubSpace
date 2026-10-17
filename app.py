
import streamlit as st
import sqlite3
from pathlib import Path
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="HubSpace",
    page_icon="🏢",
    layout="wide"
)

# Base de datos: solo para esta primera versión
RUTA_BD = Path(__file__).parent / "hubspace.db"

st.title("🏢 HubSpace")
st.subheader("Sistema integrado de reserva y uso de espacios")

st.info(
    "Prototipo académico con datos ficticios. "
    "No utilizar para reservas reales."
)

# Navegación
seccion = st.sidebar.radio(
    "Navegación",
    ["Inicio", "Espacios disponibles"]
)

if seccion == "Inicio":
    st.header("¡Bienvenido a HubSpace!")
    st.write(
        "Consulta espacios, gestiona reservas y "
        "revisa indicadores de uso del edificio."
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("Módulos", "2")
    col2.metric("Base de datos", "SQLite")
    col3.metric("Estado", "Prototipo")

elif seccion == "Espacios disponibles":
    st.header("🏢 Espacios disponibles")

    if not RUTA_BD.exists():
        st.warning(
            "La base de datos todavía no está instalada "
            "en la aplicación publicada."
        )
        st.write(
            "En el siguiente paso conectaremos la base "
            "de datos de prueba de HubSpace."
        )
    else:
        try:
            with sqlite3.connect(str(RUTA_BD)) as conexion:
                espacios = pd.read_sql_query(
                    """
                    SELECT
                        nombre AS 'Nombre',
                        tipo AS 'Tipo',
                        capacidad AS 'Capacidad',
                        CASE
                            WHEN requiere_autorizacion = 1
                            THEN 'Sí'
                            ELSE 'No'
                        END AS 'Requiere autorización'
                    FROM espacios
                    WHERE activo = 1
                    ORDER BY tipo, nombre
                    """,
                    conexion
                )

            if espacios.empty:
                st.warning("No hay espacios registrados.")
            else:
                st.dataframe(
                    espacios,
                    use_container_width=True,
                    hide_index=True
                )
                st.caption(
                    f"Total de espacios registrados: {len(espacios)}"
                )

        except Exception as error:
            st.error("No se pudo consultar la base de datos.")
            st.caption(str(error))

