"""
Vista principal de eventos de Rushbet.
Muestra tabla de eventos con opción de navegar al detalle de cada partido.
"""

import streamlit as st
import pandas as pd
from app.services.rushbet_api import RushbetClient
from app.ui import render_icon
from app.sports.football.ui.rushbet_detail_view import show_match_detail_view


def show_rushbet_view():
    """
    Vista principal para mostrar cuotas en vivo de Rushbet.
    Maneja la navegación entre lista y detalle de partido.
    """
    
    # Inicializar estado de navegación
    if "rushbet_view" not in st.session_state:
        st.session_state.rushbet_view = "list"
    if "rushbet_data" not in st.session_state:
        st.session_state.rushbet_data = None
    if "selected_event_id" not in st.session_state:
        st.session_state.selected_event_id = None
    
    # Enrutamiento de vistas
    if st.session_state.rushbet_view == "detail" and st.session_state.selected_event_id:
        show_match_detail_view()
    else:
        _show_events_list()


def _show_events_list():
    """Muestra la lista de eventos con filtros."""
    
    st.markdown(f"## {render_icon('monitoring')} Eventos Rushbet", unsafe_allow_html=True)
    st.markdown("Explora cuotas en tiempo real. Haz clic en un partido para ver todos los mercados.")
    
    col1, col2 = st.columns([1, 4])
    
    with col1:
        load_btn = st.button("Cargar Eventos", icon=":material/refresh:", type="primary", width='stretch')
        
    if load_btn:
        with st.spinner("Conectando con Rushbet/Kambi..."):
            client = RushbetClient()
            events = client.get_football_events()
            if events:
                st.session_state.rushbet_data = pd.DataFrame(events)
            else:
                st.error("No se pudieron cargar eventos o la conexión falló.")
    
    # Mostrar datos si existen
    if st.session_state.rushbet_data is not None:
        df = st.session_state.rushbet_data.copy()
        
        # --- FILTROS ---
        with st.expander("🔍 Filtros", expanded=True):
            f_col1, f_col2, f_col3 = st.columns(3)
            
            df["start_dt"] = pd.to_datetime(df["start_time"])
            unique_teams = sorted(set(df["home_team"].unique()) | set(df["away_team"].unique()))
            unique_leagues = sorted(df["league"].unique())
            
            with f_col1:
                min_date = df["start_dt"].min().date()
                selected_date = st.date_input("Fecha", value=min_date, min_value=min_date)
            
            with f_col2:
                selected_leagues = st.multiselect("Liga", unique_leagues)
            
            with f_col3:
                selected_teams = st.multiselect("Equipo", unique_teams)
        
        # Aplicar filtros
        if selected_date:
            df = df[df["start_dt"].dt.date == selected_date]
        
        if selected_leagues:
            df = df[df["league"].isin(selected_leagues)]
            
        if selected_teams:
            df = df[df["home_team"].isin(selected_teams) | df["away_team"].isin(selected_teams)]
        
        if not df.empty:
            st.success(f"Mostrando {len(df)} eventos. Selecciona uno para ver detalles.")
            
            # Encabezados de la tabla
            header_cols = st.columns([0.6, 1.5, 1.8, 1.8, 0.7, 0.7, 0.7, 1])
            with header_cols[0]:
                st.markdown("**Hora**")
            with header_cols[1]:
                st.markdown("**Liga**")
            with header_cols[2]:
                st.markdown("**Local**")
            with header_cols[3]:
                st.markdown("**Visitante**")
            with header_cols[4]:
                st.markdown("**1**")
            with header_cols[5]:
                st.markdown("**X**")
            with header_cols[6]:
                st.markdown("**2**")
            with header_cols[7]:
                st.markdown("")
            
            st.markdown("<hr style='margin: 4px 0; border-color: #334155;'>", unsafe_allow_html=True)
            
            # Mostrar cada evento como una fila
            for idx, row in df.iterrows():
                _render_event_card(row)
        else:
            st.warning("No hay eventos que coincidan con los filtros.")
    else:
        st.info("Presiona 'Cargar Eventos' para obtener los datos más recientes.")


def _render_event_card(event):
    """Renderiza un evento como fila de la tabla con botón de detalle."""
    
    event_id = event.get("id")
    home_team = event.get("home_team", "Local")
    away_team = event.get("away_team", "Visitante")
    league = event.get("league", "")
    
    # Formatear hora
    try:
        start_dt = pd.to_datetime(event.get("start_time"))
        time_str = start_dt.strftime("%H:%M")
    except:
        time_str = "--:--"
    
    odds_1 = event.get("odds_1", 0) or 0
    odds_x = event.get("odds_x", 0) or 0
    odds_2 = event.get("odds_2", 0) or 0
    
    # Contenedor de la fila
    with st.container():
        cols = st.columns([0.6, 1.5, 1.8, 1.8, 0.7, 0.7, 0.7, 1])
        
        with cols[0]:
            st.markdown(f"{time_str}")
        
        with cols[1]:
            # Liga con texto truncado si es muy largo
            league_display = league[:20] + "..." if len(league) > 20 else league
            st.markdown(f"<span style='color: #94a3b8; font-size: 13px;'>{league_display}</span>", unsafe_allow_html=True)
        
        with cols[2]:
            st.markdown(f"<b>{home_team}</b>", unsafe_allow_html=True)
        
        with cols[3]:
            st.markdown(f"<b>{away_team}</b>", unsafe_allow_html=True)
        
        with cols[4]:
            st.markdown(f"<span style='color: #22c55e;'>{odds_1:.2f}</span>" if odds_1 else "-", unsafe_allow_html=True)
        
        with cols[5]:
            st.markdown(f"<span style='color: #eab308;'>{odds_x:.2f}</span>" if odds_x else "-", unsafe_allow_html=True)
        
        with cols[6]:
            st.markdown(f"<span style='color: #ef4444;'>{odds_2:.2f}</span>" if odds_2 else "-", unsafe_allow_html=True)
        
        with cols[7]:
            if st.button("Ver más", key=f"detail_{event_id}", icon=":material/open_in_new:", width='stretch'):
                st.session_state.selected_event_id = event_id
                st.session_state.selected_event_data = event.to_dict()
                st.session_state.rushbet_view = "detail"
                st.rerun()
        
        # Línea separadora sutil
        st.markdown("<hr style='margin: 2px 0; border-color: #1e293b;'>", unsafe_allow_html=True)
