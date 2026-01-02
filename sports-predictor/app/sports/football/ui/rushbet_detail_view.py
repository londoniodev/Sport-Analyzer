"""
Vista de detalle de partido de Rushbet.
Muestra mercados de apuestas organizados según especificación exacta.
"""

import streamlit as st
import pandas as pd
from app.services.rushbet_api import RushbetClient
from app.ui import render_icon

# Componentes refactorizados
from .components.constants import (
    TABS_CONFIG, 
    NOMBRES_CATEGORIAS, 
    get_dynamic_order
)
from .components.market_logic import (
    _redistribute_markets, 
    _sort_markets_by_order
)
from .components.renderers.header import _render_match_header
from .components.renderers.common import _render_category_markets
from .components.renderers.players import (
    _render_generic_player_table,
    _render_scorers_markets,
    _render_player_cards_markets,
    _render_player_shots,
    _render_player_specials,
    _render_player_assists,
    _render_player_goals,
    _render_goalkeeper_saves
)
from .components.styles import _apply_table_styles
from app.sports.football.etl import FootballETL


def _render_debug_logs(markets):
    with st.expander("Logs del Sistema (Debug) - JSON CRUDO", expanded=False):
        st.write("Estructura completa de mercados (JSON):")
        st.json(markets)


def show_match_detail_view():
    """Vista dedicada para mostrar detalles completos de un partido."""
    
    if "selected_event_id" not in st.session_state or not st.session_state.selected_event_id:
        st.warning("No hay partido seleccionado.")
        if st.button("Volver a la lista", icon=":material/arrow_back:"):
            st.session_state.rushbet_view = "list"
            st.rerun()
        return
    
    event_id = st.session_state.selected_event_id
    event_basic = st.session_state.get("selected_event_data", {})
    
    client = RushbetClient()
    with st.spinner("Cargando mercados..."):
        details = client.get_event_details(event_id)
    
    if not details:
        st.error("No se pudieron cargar los detalles.")
        # Botón de volver por si falla
        if st.button("Volver", icon=":material/arrow_back:"):
            st.session_state.rushbet_view = "list"
            st.rerun()
        return
    
    home_team = details.get("home_team", event_basic.get("home_team", "Local"))
    away_team = details.get("away_team", event_basic.get("away_team", "Visitante"))
    home_id = details.get("home_id")
    away_id = details.get("away_id")
    markets_raw = details.get("markets", {})
    
    # --- FILA DE BOTONES DE ACCIÓN ---
    col_v, col_d, col_a = st.columns([1, 2, 2])
    with col_v:
        if st.button("Volver", icon=":material/arrow_back:"):
            st.session_state.rushbet_view = "list"
            st.session_state.selected_event_id = None
            st.rerun()
            
    with col_d:
        if home_id and away_id:
            if st.button("📥 Descargar Historial (Ult. 20)", help=f"Sincroniza los últimos 20 partidos de {home_team} y {away_team} desde API-Football"):
                with st.status("Sincronizando historial de equipos...", expanded=True) as status:
                    etl = FootballETL()
                    
                    st.write(f"⏳ Sincronizando **{home_team}**...")
                    h_count = etl.sync_team_history(home_id, 20)
                    st.write(f"✅ {h_count} partidos procesados.")
                    
                    st.write(f"⏳ Sincronizando **{away_team}**...")
                    a_count = etl.sync_team_history(away_id, 20)
                    st.write(f"✅ {a_count} partidos procesados.")
                    
                    status.update(label="¡Historial Sincronizado!", state="complete", expanded=False)
                st.success(f"Sincronización finalizada: {h_count + a_count} partidos totales en base de datos.")

    with col_a:
        do_analysis = st.toggle("📈 Mostrar Análisis Dinámico", 
                                help="Calcula probabilidades en tiempo real usando el modelo Poisson Ajustado (Dixon-Coles + EWMA). Requiere haber descargado el historial.")

    # --- CÁLCULO DE PREDICCIONES (Si aplica) ---
    predictions = None
    if do_analysis and home_id and away_id:
        from app.sports.football.analytics import get_full_match_prediction
        from app.core.database import get_session
        
        with next(get_session()) as session:
            # Verificar si hay datos
            check_stmt = (
                select(Fixture)
                .where((Fixture.home_team_id == home_id) | (Fixture.away_team_id == home_id))
                .limit(5)
            )
            has_data = session.exec(check_stmt).first()
            
            if has_data:
                predictions = get_full_match_prediction(home_id, away_id, session)
            else:
                st.sidebar.warning("⚠️ No hay datos históricos para este equipo. Usa el botón 'Descargar Historial' para habilitar el análisis.")
                do_analysis = False

    # --- PROCESAMIENTO Y LIMPIEZA DE MERCADOS ---
    markets = _redistribute_markets(markets_raw)
    
    # Encabezado
    _render_match_header(details, event_basic)
    
    # GENERAR ORDEN DINÁMICO
    ORDEN_POR_CATEGORIA = get_dynamic_order(home_team, away_team)
    
    # PESTAÑAS PRINCIPALES
    tabs = st.tabs(["PARTIDO", "JUGADORES", "HANDICAP"])
    
    # 1. PESTAÑA PARTIDO
    with tabs[0]:
        categories = TABS_CONFIG["PARTIDO"]
        has_content = False
        for cat_key in categories:
            cat_markets = markets.get(cat_key, [])
            if not cat_markets: continue
            
            has_content = True
            orden = ORDEN_POR_CATEGORIA.get(cat_key)
            if orden:
                cat_markets = _sort_markets_by_order(cat_markets, orden)
            
            cat_name = NOMBRES_CATEGORIAS.get(cat_key, cat_key)
            expanded = (cat_key == "tiempo_reglamentario")
            with st.expander(f"{cat_name} ({len(cat_markets)})", expanded=expanded):
                _render_category_markets(
                    cat_markets, 
                    home_team, 
                    away_team, 
                    orden,
                    analysis_data=predictions if do_analysis else None
                )
                
        if not has_content:
            st.info("No hay mercados de partido disponibles.")

    # 2. PESTAÑA JUGADORES
    with tabs[1]:
        # Orden específico solicitado:
        # Disparos, Goleador, Tarjetas, Especiales, Asistencias, Goles, Paradas
        # Nota: Actualizado para pasar home_team y away_team a funciones que lo requieran
        
        has_players = False
        
        # Definir orden y mapeo de renderizadores
        player_sections = [
            ("disparos_jugador", _render_player_shots),
            ("goleador", _render_scorers_markets),
            ("tarjetas_jugador", _render_player_cards_markets),
            ("apuestas_especiales_jugador", _render_player_specials),
            ("asistencias_jugador", _render_player_assists),
            ("goles_jugador", _render_player_goals),
            ("paradas_portero", _render_goalkeeper_saves),
        ]
        
        for market_key, renderer_func in player_sections:
            if market_key in markets:
                m_list = markets[market_key]
                title = NOMBRES_CATEGORIAS.get(market_key, market_key)
                with st.expander(f"{title} ({len(m_list)})", expanded=False):
                    renderer_func(
                        m_list, 
                        home_team, 
                        away_team, 
                        home_id, 
                        away_id,
                        do_analysis=do_analysis
                    )
                has_players = True
                
        if not has_players:
            st.info("No hay mercados de jugadores disponibles.")

    # 3. PESTAÑA HANDICAP
    with tabs[2]:
        categories = TABS_CONFIG["HANDICAP"]
        has_handicap = False
        for cat_key in categories:
            cat_markets = markets.get(cat_key, [])
            if not cat_markets: continue
            
            has_handicap = True
            orden = ORDEN_POR_CATEGORIA.get(cat_key) # Usa orden general o específico si existe
            
            cat_name = NOMBRES_CATEGORIAS.get(cat_key, cat_key)
            with st.expander(f"{cat_name} ({len(cat_markets)})", expanded=True):
                # Usar renderizador genérico de categorías para listas de handicap
                _render_category_markets(
                    cat_markets, 
                    home_team, 
                    away_team, 
                    orden,
                    analysis_data=predictions if do_analysis else None
                )

        if not has_handicap:
            st.info("No hay mercados de hándicap disponibles.")

    # --- DEBUG LOGS DETALLADOS ---
    _render_debug_logs(markets)
