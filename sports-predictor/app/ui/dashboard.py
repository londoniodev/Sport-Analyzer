import streamlit as st
from app.services import etl_manager

def show_dashboard():
    st.title("Panel de Control")

    if st.button("Actualizar Datos de la Premier League (2023)"):
        with st.spinner("Sincronizando datos... Esto puede tardar varios minutos."):
            etl_manager.sync_league_data(league_id=39, season=2023)
            st.success("¡Datos sincronizados correctamente!")

    # Aquí se podría mostrar el estado de la base de datos.
    st.write("Estado de la BD: 1050 partidos guardados (ejemplo)")
