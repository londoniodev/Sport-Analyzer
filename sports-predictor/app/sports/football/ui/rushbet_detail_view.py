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
# CONFIGURACIÓN DE CATEGORÍAS Y TABS
# ═══════════════════════════════════════════════════════

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
        "goleador": "Goleador",
        "disparos_jugador": "Disparos a Puerta del Jugador",
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

# Mercados que se muestran como cards (pocos outcomes)
CARD_MARKETS = [
    "resultado final", "1x2", "doble oportunidad", "ambos equipos",
    "apuesta sin empate", "descanso", "primer gol", "gol en ambas",
    "más tarjetas", "más córners", "tarjeta roja", "más tiros"
]

# Mercados que se muestran como lista/tabla (múltiples líneas)
LIST_MARKETS = [
    "total de goles", "más/menos", "over", "under", "resultado correcto",
    "hándicap", "handicap"
]


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
    
    # ═══════════════════════════════════════════════════════
    # ENCABEZADO DEL PARTIDO
    # ═══════════════════════════════════════════════════════
    _render_match_header(details, event_basic)
    
    # ═══════════════════════════════════════════════════════
    # RESULTADO FINAL DESTACADO
    # ═══════════════════════════════════════════════════════
    tiempo_reg = markets.get("tiempo_reglamentario", [])
    resultado_final = _find_market(tiempo_reg, ["resultado final", "1x2", "tiempo reglamentario"])
    
    if resultado_final:
        _render_resultado_final(resultado_final, home_team, away_team)
    
    # ═══════════════════════════════════════════════════════
    # PESTAÑAS PRINCIPALES
    # ═══════════════════════════════════════════════════════
    
    # Contar mercados por tab para mostrar solo los que tienen datos
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
                
                # Excluir resultado final ya mostrado arriba
                if cat_key == "tiempo_reglamentario" and resultado_final:
                    cat_markets = [m for m in cat_markets if m != resultado_final]
                
                if cat_markets:
                    with st.expander(f"**{cat_name}** ({len(cat_markets)})", expanded=False):
                        _render_category_markets(cat_markets, home_team, away_team)


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
        st.markdown(f"### {home_team}")
        st.caption("Local")
    
    with cols[1]:
        if state in ["STARTED", "FINISHED"]:
            st.markdown(f"## {score.get('home', 0)} - {score.get('away', 0)}")
        else:
            start_time = details.get("start_time", event_basic.get("start_time"))
            if start_time:
                try:
                    dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                    st.markdown(f"## {dt.strftime('%H:%M')}")
                except:
                    st.markdown("## VS")
            else:
                st.markdown("## VS")
        
        if state == "STARTED":
            st.markdown("<span style='background:#22c55e;color:white;padding:4px 12px;border-radius:12px;font-size:12px;'>EN VIVO</span>", unsafe_allow_html=True)
        else:
            st.caption(state_labels.get(state, state))
    
    with cols[2]:
        st.markdown(f"### {away_team}")
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
    st.markdown("### Resultado Final")
    
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
        
        label_lower = label.lower()
        
        # Determinar formato: card o lista
        is_list = any(p in label_lower for p in LIST_MARKETS) or len(outcomes) > 4
        
        if is_list:
            _render_as_list(label, outcomes, label_map)
        else:
            _render_as_card(label, outcomes, label_map)


def _render_as_card(label: str, outcomes: list, label_map: dict):
    """Renderiza mercado como cards horizontales."""
    st.markdown(f"**{label}**")
    
    cols = st.columns(len(outcomes))
    for i, outcome in enumerate(outcomes):
        with cols[i]:
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
    """Renderiza mercado como tabla/lista."""
    st.markdown(f"**{label}**")
    
    # Agrupar por línea si existe
    has_lines = any(out.get("line") for out in outcomes)
    
    if has_lines:
        # Agrupar outcomes por línea
        lines_data = {}
        for out in outcomes:
            line = out.get("line", "")
            if line not in lines_data:
                lines_data[line] = {}
            
            out_label = out.get("label", "")
            lines_data[line][out_label] = out.get("odds", 0)
        
        # Crear DataFrame
        rows = []
        for line, odds_dict in sorted(lines_data.items(), key=lambda x: float(x[0]) if x[0] else 0):
            row = {"Línea": line}
            for k, v in odds_dict.items():
                display_k = label_map.get(k, k)
                row[display_k] = f"{v:.2f}" if v else "-"
            rows.append(row)
        
        if rows:
            df = pd.DataFrame(rows)
            st.dataframe(df, hide_index=True, use_container_width=True)
    else:
        # Lista simple
        cols = st.columns(min(len(outcomes), 6))
        for i, out in enumerate(outcomes):
            with cols[i % len(cols)]:
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


def _render_statistics(stats_data: dict):
    """Renderiza estadísticas del partido."""
    stats = stats_data.get("stats", {})
    events = stats_data.get("events", [])
    
    if not stats and not events:
        st.info("No hay estadísticas disponibles.")
        return
    
    if stats:
        st.markdown("### Estadísticas")
        for stat_name, values in stats.items():
            home_val = values.get("home", 0)
            away_val = values.get("away", 0)
            total = (home_val or 0) + (away_val or 0)
            home_pct = (home_val or 0) / total * 100 if total > 0 else 50
            
            cols = st.columns([1, 2, 1])
            with cols[0]:
                st.markdown(f"**{home_val}**")
            with cols[1]:
                st.caption(stat_name)
                st.markdown(f"""
                <div style="display:flex;height:8px;border-radius:4px;overflow:hidden;background:#1e293b;">
                    <div style="width:{home_pct}%;background:#3b82f6;"></div>
                    <div style="width:{100-home_pct}%;background:#ef4444;"></div>
                </div>
                """, unsafe_allow_html=True)
            with cols[2]:
                st.markdown(f"**{away_val}**")
