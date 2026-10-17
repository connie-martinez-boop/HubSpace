
import streamlit as st
import sqlite3
from pathlib import Path
import pandas as pd
import plotly.express as px

# Configuración general
st.set_page_config(
    page_title="HubSpace",
    page_icon="🏢",
    layout="wide"
)

# Presentación
st.title("🏢 HubSpace")
st.subheader("Sistema integrado de reserva y uso de espacios")

st.write(
    "Plataforma de demostración para gestionar reservas, "
    "solicitudes de laboratorio y uso de espacios."
)

st.info(
    "Prototipo académico con datos ficticios. "
    "No utilizar para gestionar reservas reales del edificio."
)

st.divider()

st.header("Bienvenido a HubSpace")
st.write(
    "Desde esta plataforma podrás consultar información "
    "de espacios, gestionar reservas y revisar indicadores."
)
