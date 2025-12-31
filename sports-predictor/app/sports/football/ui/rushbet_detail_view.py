"""
Vista de detalle de partido de Rushbet.
Muestra mercados de apuestas organizados en pestañas: Partido, Jugadores, Handicap.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from app.services.rushbet_api import RushbetClient
from app.ui.theme import render_icon


# ═══════════════════════════════════════════════════════
# ORDEN DE MERCADOS POR CATEGORÍA (según especificación)
# ═══════════════════════════════════════════════════════

# Orden específico dentro de Tiempo Reglamentario
TIEMPO_REG_ORDER = [
    "resultado final", "1x2", "tiempo reglamentario",
    "total de goles",
    "doble oportunidad",
    "ambos equipos marcarán", "ambos equipos", "btts",
    "resultado correcto", "marcador correcto",
    "apuesta sin empate",
    "total de goles de", "total goles",  # Para Local/Visitante
    "descanso/tiempo", "medio tiempo/final",
    "hándicap", "handicap",
    "victoria de", "y ambos equipos marcarán",
    "gol en ambas mitades"
]

# Estructura de tabs y subcategorías
TABS_CONFIG = {
    "Partido": {
        "tiempo_reglamentario": "Tiempo Reglamentario",
        "medio_tiempo": "Medio Tiempo",
        "corners": "Tiros de Esquina",
        "tarjetas_equipo": "Partido y Tarjetas del Equipo",
        "disparos_equipo": "Partido y Disparos del Equipo",
        "eventos_partido": "Eventos del Partido"
    },
    "Jugadores": {
        "disparos_jugador": "Disparos a Puerta del Jugador",
        "goleador": "Goleador",
        "tarjetas_jugador": "Tarjetas Jugadores",
        "apuestas_especiales_jugador": "Apuestas Especiales Jugador",
        "asistencias_jugador": "Asistencias del Jugador",
        "goles_jugador": "Goles del Jugador",
        "paradas_portero": "Paradas del Portero"
    },
    "Handicap": {
        "handicap_3way": "Hándicap 3-Way",
        "lineas_asiaticas": "Líneas Asiáticas"
    }
}


def show_match_detail_view():
    """Vista dedicada para mostrar detalles completos de un partido."""
    
    # Verificar evento seleccionado
    if "selected_event_id" not in st.session_state or not st.session_state.selected_event_id:
        st.warning("No hay partido seleccionado.")
        if st.button("Volver a la lista", icon=":material/arrow_back:"):
            st.session_state.rushbet_view = "list"
            st.rerun()
        return
    
    event_id = st.session_state.selected_event_id
    event_basic = st.session_state.get("selected_event_data", {})
    
    # Botón de regreso
    if st.button("Volver", icon=":material/arrow_back:"):
        st.session_state.rushbet_view = "list"
        st.session_state.selected_event_id = None
        st.rerun()
    
    # Cargar datos
    client = RushbetClient()
    with st.spinner("Cargando mercados..."):
        details = client.get_event_details(event_id)
        stats = client.get_event_statistics(event_id)
    
    if not details:
        st.error("No se pudieron cargar los detalles.")
        return
    
    home_team = details.get("home_team", event_basic.get("home_team", "Local"))
    away_team = details.get("away_team", event_basic.get("away_team", "Visitante"))
    markets = details.get("markets", {})
    
    # Encabezado del partido
    _render_match_header(details, event_basic)
    
    # Resultado Final destacado (siempre primero)
    tiempo_reg = markets.get("tiempo_reglamentario", [])
    resultado_final = _find_market(tiempo_reg, ["resultado final", "1x2", "tiempo reglamentario"])
    
    if resultado_final:
        _render_resultado_final(resultado_final, home_team, away_team)
    
    # Pestañas principales
    tabs_with_data = []
    for tab_name, categories in TABS_CONFIG.items():
        count = sum(len(markets.get(cat, [])) for cat in categories.keys())
        if count > 0:
            tabs_with_data.append((tab_name, categories, count))
    
    if not tabs_with_data:
        st.info("No hay mercados adicionales disponibles.")
        return
    
    tab_labels = [f"{name} ({count})" for name, _, count in tabs_with_data]
    tabs = st.tabs(tab_labels)
    
    for i, tab in enumerate(tabs):
        tab_name, categories, _ = tabs_with_data[i]
        
        with tab:
            for cat_key, cat_name in categories.items():
                cat_markets = markets.get(cat_key, [])
                
                # Excluir resultado final ya mostrado
                if cat_key == "tiempo_reglamentario" and resultado_final:
                    cat_markets = [m for m in cat_markets if m != resultado_final]
                
                # Ordenar mercados según el orden definido
                if cat_key == "tiempo_reglamentario":
                    cat_markets = _sort_markets(cat_markets, TIEMPO_REG_ORDER)
                
                if cat_markets:
                    with st.expander(f"{cat_name} ({len(cat_markets)})", expanded=(cat_key == "tiempo_reglamentario")):
                        _render_category_markets(cat_markets, home_team, away_team)


def _sort_markets(markets: list, order: list) -> list:
    """Ordena mercados según una lista de prioridad."""
    def get_priority(market):
        label_lower = market.get("label", "").lower()
        for i, pattern in enumerate(order):
            if pattern in label_lower:
                return i
        return 999  # Al final si no coincide
    
    return sorted(markets, key=get_priority)


def _render_match_header(details: dict, event_basic: dict):
    """Renderiza el encabezado del partido."""
    home_team = details.get("home_team", event_basic.get("home_team", "Local"))
    away_team = details.get("away_team", event_basic.get("away_team", "Visitante"))
    state = details.get("state", "NOT_STARTED")
    score = details.get("score", {})
    
    state_labels = {"NOT_STARTED": "Próximo", "STARTED": "En Vivo", "FINISHED": "Finalizado"}
    
    st.markdown("---")
    cols = st.columns([2, 1, 2])
    
    with cols[0]:
        st.markdown(f"<h3>{home_team}</h3>", unsafe_allow_html=True)
        st.caption("Local")
    
    with cols[1]:
        if state in ["STARTED", "FINISHED"]:
            st.markdown(f"<h2 style='text-align:center;'>{score.get('home', 0)} - {score.get('away', 0)}</h2>", unsafe_allow_html=True)
        else:
            start_time = details.get("start_time", event_basic.get("start_time"))
            if start_time:
                try:
                    dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                    st.markdown(f"<h2 style='text-align:center;'>{dt.strftime('%H:%M')}</h2>", unsafe_allow_html=True)
                except:
                    st.markdown("<h2 style='text-align:center;'>VS</h2>", unsafe_allow_html=True)
            else:
                st.markdown("<h2 style='text-align:center;'>VS</h2>", unsafe_allow_html=True)
        
        if state == "STARTED":
            st.markdown("<div style='text-align:center;'><span style='background:#22c55e;color:white;padding:4px 12px;border-radius:12px;font-size:12px;'>EN VIVO</span></div>", unsafe_allow_html=True)
        else:
            st.caption(state_labels.get(state, state))
    
    with cols[2]:
        st.markdown(f"<h3 style='text-align:right;'>{away_team}</h3>", unsafe_allow_html=True)
        st.caption("Visitante")
    
    st.markdown("---")


def _find_market(markets: list, patterns: list) -> dict:
    """Busca un mercado que coincida con los patrones."""
    for market in markets:
        label_lower = market.get("label", "").lower()
        if any(p in label_lower for p in patterns):
            return market
    return None


def _render_resultado_final(market: dict, home_team: str, away_team: str):
    """Renderiza el mercado de resultado final destacado."""
    st.markdown("<h3>Resultado Final</h3>", unsafe_allow_html=True)
    
    outcomes = market.get("outcomes", [])
    if len(outcomes) < 3:
        return
    
    cols = st.columns(3)
    label_map = {"1": home_team, "X": "Empate", "2": away_team}
    colors = ["#3b82f6", "#eab308", "#ef4444"]
    
    for i, outcome in enumerate(outcomes[:3]):
        with cols[i]:
            odds = outcome.get("odds", 0)
            out_label = outcome.get("label", "")
            display_label = label_map.get(out_label, out_label)
            
            st.markdown(f"""
            <div style="background:linear-gradient(135deg,#1e3a5f,#0f2944);border:2px solid {colors[i]};border-radius:12px;padding:16px;text-align:center;">
                <div style="color:#e2e8f0;font-size:14px;font-weight:500;margin-bottom:8px;">{display_label}</div>
                <div style="color:{colors[i]};font-size:28px;font-weight:bold;">{odds:.2f}</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("")


def _render_category_markets(markets: list, home_team: str, away_team: str):
    """Renderiza los mercados de una categoría."""
    
    label_map = {"1": home_team, "X": "Empate", "2": away_team}
    
    for market in markets:
        label = market.get("label", "Mercado")
        outcomes = market.get("outcomes", [])
        
        if not outcomes:
            continue
        
        # Determinar si es lista o card
        label_lower = label.lower()
        has_lines = any(out.get("line") for out in outcomes)
        is_list = has_lines or len(outcomes) > 4 or any(p in label_lower for p in ["total", "más/menos", "hándicap", "handicap", "resultado correcto"])
        
        if is_list:
            _render_as_list(label, outcomes, label_map)
        else:
            _render_as_card(label, outcomes, label_map)


def _render_as_card(label: str, outcomes: list, label_map: dict):
    """Renderiza mercado como cards horizontales."""
    st.markdown(f"<p style='margin-bottom:4px;'><b>{label}</b></p>", unsafe_allow_html=True)
    
    n_cols = min(len(outcomes), 4)
    cols = st.columns(n_cols)
    
    for i, outcome in enumerate(outcomes):
        with cols[i % n_cols]:
            odds = outcome.get("odds", 0)
            out_label = outcome.get("label", "")
            line = outcome.get("line")
            
            display_label = label_map.get(out_label, out_label)
            if line:
                display_label = f"{display_label} ({line})"
            
            st.markdown(f"""
            <div style="background:#1e3a5f;border:1px solid #2d5a87;border-radius:8px;padding:10px;text-align:center;margin:2px;">
                <div style="color:#94a3b8;font-size:11px;">{display_label}</div>
                <div style="color:#22c55e;font-size:18px;font-weight:bold;">{odds:.2f}</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("")


def _render_as_list(label: str, outcomes: list, label_map: dict):
    """Renderiza mercado como tabla con todas las líneas."""
    st.markdown(f"<p style='margin-bottom:4px;'><b>{label}</b></p>", unsafe_allow_html=True)
    
    has_lines = any(out.get("line") for out in outcomes)
    
    if has_lines:
        # Agrupar outcomes por línea
        lines_data = {}
        for out in outcomes:
            line = out.get("line")
            if line is None:
                line = ""
            line_key = float(line) if line else 0
            
            if line_key not in lines_data:
                lines_data[line_key] = {"Línea": line}
            
            out_label = out.get("label", "")
            display_label = label_map.get(out_label, out_label)
            lines_data[line_key][display_label] = out.get("odds", 0)
        
        # Crear DataFrame ordenado por línea
        rows = [lines_data[k] for k in sorted(lines_data.keys())]
        
        if rows:
            df = pd.DataFrame(rows)
            
            # Formatear columnas numéricas
            for col in df.columns:
                if col != "Línea":
                    df[col] = df[col].apply(lambda x: f"{x:.2f}" if isinstance(x, (int, float)) and x > 0 else "-")
            
            st.dataframe(df, hide_index=True, use_container_width=True)
    else:
        # Sin líneas, mostrar como grid
        n_cols = min(len(outcomes), 4)
        cols = st.columns(n_cols)
        
        for i, out in enumerate(outcomes):
            with cols[i % n_cols]:
                odds = out.get("odds", 0)
                out_label = out.get("label", "")
                display_label = label_map.get(out_label, out_label)
                
                st.markdown(f"""
                <div style="background:#1e3a5f;border:1px solid #2d5a87;border-radius:6px;padding:8px;text-align:center;margin:2px;">
                    <div style="color:#94a3b8;font-size:10px;">{display_label}</div>
                    <div style="color:#22c55e;font-size:16px;font-weight:bold;">{odds:.2f}</div>
                </div>
                """, unsafe_allow_html=True)
    
    st.markdown("")
