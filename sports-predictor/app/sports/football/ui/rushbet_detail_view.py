"""
Vista de detalle de partido de Rushbet.
Muestra mercados de apuestas completos, estadísticas y eventos del partido.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from app.services.rushbet_api import RushbetClient
from app.ui.theme import render_icon


def show_match_detail_view():
    """Vista dedicada para mostrar detalles completos de un partido."""
    
    # Verificar que hay un evento seleccionado
    if "selected_event_id" not in st.session_state or not st.session_state.selected_event_id:
        st.warning("No hay partido seleccionado. Vuelve a la lista de eventos.")
        if st.button("Volver a la lista", icon=":material/arrow_back:"):
            st.session_state.rushbet_view = "list"
            st.rerun()
        return
    
    event_id = st.session_state.selected_event_id
    event_basic = st.session_state.get("selected_event_data", {})
    
    # Botón de regreso
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("Volver", icon=":material/arrow_back:", use_container_width=True):
            st.session_state.rushbet_view = "list"
            st.session_state.selected_event_id = None
            st.rerun()
    
    # Cargar datos detallados
    client = RushbetClient()
    
    with st.spinner("Cargando detalles del partido..."):
        details = client.get_event_details(event_id)
        stats = client.get_event_statistics(event_id)
    
    if not details:
        st.error("No se pudieron cargar los detalles del partido.")
        return
    
    # ═══════════════════════════════════════════════════════
    # ENCABEZADO DEL PARTIDO
    # ═══════════════════════════════════════════════════════
    
    home_team = details.get("home_team", event_basic.get("home_team", "Local"))
    away_team = details.get("away_team", event_basic.get("away_team", "Visitante"))
    
    # Estado del partido
    state = details.get("state", "NOT_STARTED")
    score = details.get("score", {})
    
    state_labels = {
        "NOT_STARTED": "Próximo",
        "STARTED": "En Vivo",
        "FINISHED": "Finalizado"
    }
    state_label = state_labels.get(state, state)
    
    # Encabezado con equipos y marcador
    st.markdown("---")
    
    header_cols = st.columns([2, 1, 2])
    
    with header_cols[0]:
        st.markdown(f"### {home_team}")
        st.caption("Local")
    
    with header_cols[1]:
        if state == "STARTED" or state == "FINISHED":
            home_score = score.get("home", 0)
            away_score = score.get("away", 0)
            st.markdown(f"## {home_score} - {away_score}")
        else:
            # Mostrar hora de inicio
            start_time = details.get("start_time", event_basic.get("start_time"))
            if start_time:
                try:
                    dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                    st.markdown(f"## {dt.strftime('%H:%M')}")
                except:
                    st.markdown("## VS")
            else:
                st.markdown("## VS")
        
        # Badge de estado
        if state == "STARTED":
            st.markdown(f"<span style='background-color: #22c55e; color: white; padding: 4px 12px; border-radius: 12px; font-size: 12px;'>{state_label}</span>", unsafe_allow_html=True)
        else:
            st.caption(state_label)
    
    with header_cols[2]:
        st.markdown(f"### {away_team}")
        st.caption("Visitante")
    
    st.markdown("---")
    
    # ═══════════════════════════════════════════════════════
    # TABS DE MERCADOS
    # ═══════════════════════════════════════════════════════
    
    markets = details.get("markets", {})
    
    # Contar mercados por categoría
    tab_labels = []
    tab_data = []
    
    category_names = {
        "principal": "Principal",
        "goles": "Goles",
        "handicap": "Hándicap", 
        "mitades": "Mitades",
        "otros": "Otros"
    }
    
    for key, name in category_names.items():
        if markets.get(key):
            tab_labels.append(f"{name} ({len(markets[key])})")
            tab_data.append((key, markets[key]))
    
    # Agregar tab de estadísticas si hay datos
    if stats and (stats.get("stats") or stats.get("events")):
        tab_labels.append("Estadísticas")
        tab_data.append(("stats", stats))
    
    if not tab_labels:
        st.info("No hay mercados disponibles para este partido.")
        return
    
    tabs = st.tabs(tab_labels)
    
    for i, tab in enumerate(tabs):
        with tab:
            key, data = tab_data[i]
            
            if key == "stats":
                _render_statistics(data)
            else:
                _render_markets(data)


def _render_markets(markets_list: list):
    """Renderiza una lista de mercados de apuestas."""
    
    for market in markets_list:
        label = market.get("label", "Mercado")
        outcomes = market.get("outcomes", [])
        
        if not outcomes:
            continue
        
        with st.expander(f"**{label}**", expanded=True):
            # Crear columnas según cantidad de outcomes
            cols = st.columns(len(outcomes))
            
            for j, outcome in enumerate(outcomes):
                with cols[j]:
                    odds = outcome.get("odds", 0)
                    out_label = outcome.get("label", "")
                    line = outcome.get("line")
                    
                    display_label = out_label
                    if line:
                        display_label = f"{out_label} ({line})"
                    
                    # Estilo de botón con cuota
                    st.markdown(f"""
                    <div style="
                        background: linear-gradient(135deg, #1e3a5f 0%, #0f2944 100%);
                        border: 1px solid #2d5a87;
                        border-radius: 8px;
                        padding: 12px;
                        text-align: center;
                        margin: 4px 0;
                    ">
                        <div style="color: #94a3b8; font-size: 12px; margin-bottom: 4px;">{display_label}</div>
                        <div style="color: #22c55e; font-size: 20px; font-weight: bold;">{odds:.2f}</div>
                    </div>
                    """, unsafe_allow_html=True)


def _render_statistics(stats_data: dict):
    """Renderiza estadísticas y eventos del partido."""
    
    stats = stats_data.get("stats", {})
    events = stats_data.get("events", [])
    
    if not stats and not events:
        st.info("No hay estadísticas disponibles para este partido.")
        return
    
    # Estadísticas en dos columnas
    if stats:
        st.markdown("### Estadísticas del Partido")
        
        for stat_name, values in stats.items():
            home_val = values.get("home", 0)
            away_val = values.get("away", 0)
            
            # Calcular porcentajes para barras
            total = (home_val or 0) + (away_val or 0)
            if total > 0:
                home_pct = (home_val or 0) / total * 100
                away_pct = (away_val or 0) / total * 100
            else:
                home_pct = away_pct = 50
            
            cols = st.columns([1, 2, 1])
            
            with cols[0]:
                st.markdown(f"**{home_val}**")
            
            with cols[1]:
                st.caption(stat_name)
                # Barra de progreso dual
                st.markdown(f"""
                <div style="display: flex; height: 8px; border-radius: 4px; overflow: hidden; background: #1e293b;">
                    <div style="width: {home_pct}%; background: #3b82f6;"></div>
                    <div style="width: {away_pct}%; background: #ef4444;"></div>
                </div>
                """, unsafe_allow_html=True)
            
            with cols[2]:
                st.markdown(f"**{away_val}**")
    
    # Timeline de eventos
    if events:
        st.markdown("### Eventos del Partido")
        
        event_icons = {
            "GOAL": "⚽",
            "YELLOW_CARD": "🟨",
            "RED_CARD": "🟥",
            "SUBSTITUTION": "🔄",
            "PENALTY": "🎯"
        }
        
        for event in events:
            event_type = event.get("type", "")
            team = event.get("team", "")
            player = event.get("player", "")
            minute = event.get("minute", "")
            extra = event.get("extra_minute")
            
            icon = event_icons.get(event_type, "📋")
            time_str = f"{minute}'" if minute else ""
            if extra:
                time_str = f"{minute}+{extra}'"
            
            alignment = "flex-start" if team == "HOME" else "flex-end"
            bg_color = "#1e3a5f" if team == "HOME" else "#3a1e2f"
            
            st.markdown(f"""
            <div style="display: flex; justify-content: {alignment}; margin: 8px 0;">
                <div style="
                    background: {bg_color};
                    padding: 8px 16px;
                    border-radius: 8px;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                ">
                    <span style="font-size: 20px;">{icon}</span>
                    <span style="color: #e2e8f0;">{player}</span>
                    <span style="color: #94a3b8; font-size: 12px;">{time_str}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
