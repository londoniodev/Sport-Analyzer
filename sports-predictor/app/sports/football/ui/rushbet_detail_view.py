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
from .components.styles import _apply_table_styles  # Importamos por si acaso se necesita direct


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
    
    if st.button("Volver", icon=":material/arrow_back:"):
        st.session_state.rushbet_view = "list"
        st.session_state.selected_event_id = None
        st.rerun()
    
    client = RushbetClient()
    with st.spinner("Cargando mercados..."):
        details = client.get_event_details(event_id)
    
    if not details:
        st.error("No se pudieron cargar los detalles.")
        return
    
    home_team = details.get("home_team", event_basic.get("home_team", "Local"))
    away_team = details.get("away_team", event_basic.get("away_team", "Visitante"))
    home_id = details.get("home_id")
    away_id = details.get("away_id")
    markets_raw = details.get("markets", {})
    
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
            with st.expander(f"{cat_name} ({len(cat_markets)})", expanded=(cat_key == "tiempo_reglamentario")):
                _render_category_markets(cat_markets, home_team, away_team, orden)
                
        if not has_content:
            st.info("No hay mercados de partido disponibles.")

    # 2. PESTAÑA JUGADORES
    with tabs[1]:
        # Orden específico solicitado:
        # Disparos, Goleador, Tarjetas, Especiales, Asistencias, Goles, Paradas
        # Nota: Actualizado para pasar home_team y away_team a funciones que lo requieran
        
        has_players = False
        
        # Disparos
        if "disparos_jugador" in markets:
            _render_player_shots(markets["disparos_jugador"], home_team, away_team, home_id, away_id)
            has_players = True
            
        # Goleador
        if "goleador" in markets:
            _render_scorers_markets(markets["goleador"], home_team, away_team, home_id, away_id)
            has_players = True
            
        # Tarjetas
        if "tarjetas_jugador" in markets:
            _render_player_cards_markets(markets["tarjetas_jugador"], home_team, away_team, home_id, away_id)
            has_players = True
            
        # Especiales
        if "apuestas_especiales_jugador" in markets:
            _render_player_specials(markets["apuestas_especiales_jugador"], home_team, away_team, home_id, away_id)
            has_players = True
            
        # Asistencias
        if "asistencias_jugador" in markets:
            _render_player_assists(markets["asistencias_jugador"], home_team, away_team, home_id, away_id)
            has_players = True

        # Goles
        if "goles_jugador" in markets:
            _render_player_goals(markets["goles_jugador"], home_team, away_team, home_id, away_id)
            has_players = True

        # Paradas
        if "paradas_portero" in markets:
            _render_goalkeeper_saves(markets["paradas_portero"], home_team, away_team, home_id, away_id)
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
                _render_category_markets(cat_markets, home_team, away_team, orden)

        if not has_handicap:
            st.info("No hay mercados de hándicap disponibles.")

    # --- DEBUG LOGS DETALLADOS ---
    _render_debug_logs(markets)
