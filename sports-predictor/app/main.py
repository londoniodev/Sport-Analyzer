import streamlit as st
from app.ui.dashboard import show_dashboard
from app.ui.prediction_view import show_prediction_view
from app.database.config import init_db

def main():
    st.set_page_config(page_title="Sports Predictor", layout="wide")

    # Inicializar la base de datos
    try:
        init_db()
    except Exception as e:
        st.error(f"Error al conectar con la base de datos: {e}")
        return

    st.sidebar.title("Navegación")
    page = st.sidebar.radio("Ir a", ["Panel de Control", "Análisis de Partido"])

    if page == "Panel de Control":
        show_dashboard()
    elif page == "Análisis de Partido":
        show_prediction_view()

if __name__ == "__main__":
    main()
