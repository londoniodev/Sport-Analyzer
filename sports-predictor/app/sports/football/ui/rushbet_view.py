
import streamlit as st
import pandas as pd
from app.services.rushbet_api import RushbetClient
from app.ui.theme import render_icon

def show_rushbet_view():
    """
    View for displaying live odds from Rushbet (Kambi).
    """
    st.markdown(f"## {render_icon('monitoring')} Cuotas en Vivo - Rushbet", unsafe_allow_html=True)
    st.markdown("Explora cuotas en tiempo real extraídas directamente de la API de Rushbet.")
    
    col1, col2 = st.columns([1, 4])
    
    # Initialize session state for data persistence
    if "rushbet_data" not in st.session_state:
        st.session_state.rushbet_data = None
        
    col1, col2 = st.columns([1, 4])
    
    with col1:
        load_btn = st.button("Cargar Eventos", icon=":material/refresh:", type="primary", use_container_width=True)
        
    if load_btn:
        with st.spinner("Conectando con Rushbet/Kambi..."):
            client = RushbetClient()
            events = client.get_football_events()
            if events:
                st.session_state.rushbet_data = pd.DataFrame(events)
            else:
                st.error("No se pudieron cargar eventos o la conexión falló.")
    
    # Display if data exists
    if st.session_state.rushbet_data is not None:
        df = st.session_state.rushbet_data.copy()
        
        # --- FILTERS ---
        with st.expander("🔍 Filtros", expanded=True):
            f_col1, f_col2, f_col3 = st.columns(3)
            
            # Prepare data for filtering
            df["start_dt"] = pd.to_datetime(df["start_time"])
            unique_teams = sorted(set(df["home_team"].unique()) | set(df["away_team"].unique()))
            unique_leagues = sorted(df["league"].unique())
            
            with f_col1:
                # Date filter: show events from this date onwards
                min_date = df["start_dt"].min().date()
                selected_date = st.date_input("Fecha", value=min_date, min_value=min_date)
            
            with f_col2:
                # League filter
                selected_leagues = st.multiselect("Liga", unique_leagues)
            
            with f_col3:
                # Team filter
                selected_teams = st.multiselect("Equipo", unique_teams)
        
        # Apply Filters
        if selected_date:
            df = df[df["start_dt"].dt.date == selected_date]
        
        if selected_leagues:
            df = df[df["league"].isin(selected_leagues)]
            
        if selected_teams:
            # Filter if either home or away team is in selection
            df = df[df["home_team"].isin(selected_teams) | df["away_team"].isin(selected_teams)]
        
        if not df.empty:
            st.success(f"Mostrando {len(df)} eventos.")
            
            # Select and rename columns for clean display
            display_cols = [
                "start_time", "league", "home_team", "away_team", 
                "odds_1", "odds_x", "odds_2"
            ]
            
            available_cols = [c for c in display_cols if c in df.columns]
            display_df = df[available_cols].copy()
            
            display_df.rename(columns={
                "start_time": "Hora",
                "league": "Liga",
                "home_team": "Local",
                "away_team": "Visitante",
                "odds_1": "1",
                "odds_x": "X",
                "odds_2": "2"
            }, inplace=True)
            
            # Format time
            try:
                display_df["Hora"] = pd.to_datetime(display_df["Hora"]).dt.strftime("%H:%M") # Just time since date is filtered
            except:
                pass
                
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Hora": st.column_config.TextColumn("Hora"),
                    "Liga": st.column_config.TextColumn("Liga"),
                    "1": st.column_config.NumberColumn("1 (Local)", format="%.2f"),
                    "X": st.column_config.NumberColumn("X (Empate)", format="%.2f"),
                    "2": st.column_config.NumberColumn("2 (Visita)", format="%.2f"),
                }
            )
        else:
            st.warning("No hay eventos que coincidan con los filtros.")
    else:
        st.info("Presiona 'Cargar Eventos' para obtener los datos más recientes.")
