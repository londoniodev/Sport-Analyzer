"""
Vista de detalle de partido de Rushbet.
Muestra mercados de apuestas organizados según especificación exacta.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from app.services.rushbet_api import RushbetClient
from app.ui.theme import render_icon


# ═══════════════════════════════════════════════════════
# ORDEN EXACTO DE MERCADOS POR CATEGORÍA
# ═══════════════════════════════════════════════════════

# Orden dentro de Tiempo Reglamentario
ORDEN_TIEMPO_REG = [
    ("resultado final", "card"),
    ("1x2", "card"),
    ("tiempo reglamentario", "card"),
    ("total de goles", "list"),
    ("doble oportunidad", "card"),
    ("ambos equipos marcarán", "card"),
    ("ambos equipos", "card"),
    ("resultado correcto", "list"),
    ("marcador correcto", "list"),
    ("apuesta sin empate", "card"),
    ("total de goles de", "list"),  # Local/Visitante
    ("descanso/tiempo", "list"),
    ("medio tiempo/final", "list"),
    ("hándicap", "list"),
    ("handicap", "list"),
    ("victoria de", "card"),  # Victoria de X y ambos marcan
    ("y ambos equipos marcarán", "card"),
    ("gol en ambas mitades", "card"),
]

# Orden dentro de Medio Tiempo
ORDEN_MEDIO_TIEMPO = [
    ("descanso", "card"),
    ("1° parte", "card"),
    ("1ª parte", "card"),
    ("apuesta sin empate", "card"),
    ("doble oportunidad", "card"),
    ("ambos equipos marcarán", "card"),
    ("total de goles", "list"),
    ("total de goles de", "list"),
    ("resultado correcto", "list"),
    ("2° parte", "card"),
    ("2ª parte", "card"),
]

# Orden dentro de Tiros de Esquina
ORDEN_CORNERS = [
    ("total de tiros de esquina", "list"),
    ("total de esquina", "list"),
    ("esquina a favor de", "list"),
    ("más tiros de esquina", "card"),
    ("mas tiros de esquina", "card"),
    ("más córners", "card"),
    ("hándicap de tiros de esquina", "list"),
    ("handicap de esquina", "list"),
    ("siguiente tiro de esquina", "card"),
]

# Orden dentro de Tarjetas Equipo
ORDEN_TARJETAS = [
    ("total de tarjetas", "list"),
    ("total de tarjeta", "list"),
    ("tarjeta roja mostrada", "card"),
    ("tarjeta roja a", "card"),
    ("más tarjetas", "card"),
    ("tarjetas hándicap", "list"),
]

# Orden dentro de Disparos Equipo
ORDEN_DISPAROS = [
    ("número total de disparos", "list"),
    ("número total de tiros", "list"),
    ("tiros a puerta", "list"),
    ("más tiros a puerta", "card"),
    ("mas tiros a puerta", "card"),
]

# Orden Eventos del Partido
ORDEN_EVENTOS = [
    ("primer gol", "card"),
    ("propia meta", "card"),
    ("sin recibir goles", "card"),
    ("gana al menos una mitad", "card"),
    ("al palo", "card"),
]

# Orden Handicap 3-Way
ORDEN_HANDICAP_3WAY = [
    ("hándicap 3-way", "list"),
    ("handicap 3-way", "list"),
    ("hándicap 3", "list"),
]

# Orden Líneas Asiáticas
ORDEN_ASIATICAS = [
    ("hándicap asiático", "list"),
    ("handicap asiático", "list"),
    ("total asiático", "list"),
]

# Mapeo de categoría a orden
ORDEN_POR_CATEGORIA = {
    "tiempo_reglamentario": ORDEN_TIEMPO_REG,
    "medio_tiempo": ORDEN_MEDIO_TIEMPO,
    "corners": ORDEN_CORNERS,
    "tarjetas_equipo": ORDEN_TARJETAS,
    "disparos_equipo": ORDEN_DISPAROS,
    "eventos_partido": ORDEN_EVENTOS,
    "handicap_3way": ORDEN_HANDICAP_3WAY,
    "lineas_asiaticas": ORDEN_ASIATICAS,
}

# Estructura de tabs
TABS_CONFIG = {
    "Partido": ["tiempo_reglamentario", "medio_tiempo", "corners", "tarjetas_equipo", "disparos_equipo", "eventos_partido"],
    "Jugadores": ["disparos_jugador", "goleador", "tarjetas_jugador", "apuestas_especiales_jugador", "asistencias_jugador", "goles_jugador", "paradas_portero"],
    "Handicap": ["handicap_3way", "lineas_asiaticas"]
}

NOMBRES_CATEGORIAS = {
    "tiempo_reglamentario": "Tiempo Reglamentario",
    "medio_tiempo": "Medio Tiempo",
    "corners": "Tiros de Esquina",
    "tarjetas_equipo": "Partido y Tarjetas del Equipo",
    "disparos_equipo": "Partido y Disparos del Equipo",
    "eventos_partido": "Eventos del Partido",
    "disparos_jugador": "Disparos a Puerta del Jugador",
    "goleador": "Goleador",
    "tarjetas_jugador": "Tarjetas Jugadores",
    "apuestas_especiales_jugador": "Apuestas Especiales Jugador",
    "asistencias_jugador": "Asistencias del Jugador",
    "goles_jugador": "Goles del Jugador",
    "paradas_portero": "Paradas del Portero",
    "handicap_3way": "Hándicap 3-Way",
    "lineas_asiaticas": "Líneas Asiáticas"
}


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
    markets = details.get("markets", {})
    
    # Encabezado
    _render_match_header(details, event_basic)
    
    # Pestañas
    tabs_with_data = []
    for tab_name, categories in TABS_CONFIG.items():
        count = sum(len(markets.get(cat, [])) for cat in categories)
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
            for cat_key in categories:
                cat_markets = markets.get(cat_key, [])
                
                # Ordenar según especificación
                orden = ORDEN_POR_CATEGORIA.get(cat_key)
                if orden:
                    cat_markets = _sort_markets_by_order(cat_markets, orden)
                
                if cat_markets:
                    cat_name = NOMBRES_CATEGORIAS.get(cat_key, cat_key)
                    with st.expander(f"{cat_name} ({len(cat_markets)})", expanded=(cat_key == "tiempo_reglamentario")):
                        _render_category_markets(cat_markets, home_team, away_team, orden)

    # --- DEBUG LOGS (Solicitado por usuario) ---
    with st.expander("Logs del Sistema (Debug) - LABELS CRUDOS", expanded=True):
        st.markdown("### Categorías Crudas desde la API")
        
        # Recopilar todos los labels crudos organizados por su categoría actual
        raw_labels_by_cat = {}
        for cat, market_list in markets.items():
            labels = [m["label"] for m in market_list]
            if labels:
                raw_labels_by_cat[cat] = labels
        
        st.write(raw_labels_by_cat)
        
        st.markdown("---")
        st.markdown("### Lista Plana de Todos los Labels Encontrados")
        all_labels = []
        for m_list in markets.values():
            all_labels.extend([m["label"] for m in m_list])
        st.code("\n".join(sorted(all_labels)))


def _sort_markets_by_order(markets: list, orden: list) -> list:
    """Ordena mercados según lista de patrones."""
    def get_priority(market):
        label_lower = market.get("label", "").lower()
        for i, (pattern, _) in enumerate(orden):
            if pattern in label_lower:
                return i
        return 999
    
    return sorted(markets, key=get_priority)


def _get_market_format(label: str, orden: list) -> str:
    """Determina si el mercado es card o list según el orden."""
    label_lower = label.lower()
    for pattern, formato in orden:
        if pattern in label_lower:
            return formato
    return "card"


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


def _render_category_markets(markets: list, home_team: str, away_team: str, orden: list = None):
    """Renderiza los mercados de una categoría."""
    
    label_map = {"1": home_team, "X": "Empate", "2": away_team}
    
    for market in markets:
        label = market.get("label", "Mercado")
        outcomes = market.get("outcomes", [])
        
        if not outcomes:
            continue
        
        # Determinar formato
        has_lines = any(out.get("line") for out in outcomes)
        
        if orden:
            formato = _get_market_format(label, orden)
            is_list = formato == "list" or has_lines
        else:
            is_list = has_lines or len(outcomes) > 4
        
        if is_list:
            _render_as_list(label, outcomes, label_map)
        else:
            _render_as_card(label, outcomes, label_map)


def _render_as_card(label: str, outcomes: list, label_map: dict):
    """Renderiza mercado como cards horizontales."""
    st.markdown(f"<p style='margin-bottom:4px;font-weight:bold;'>{label}</p>", unsafe_allow_html=True)
    
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
    st.markdown(f"<p style='margin-bottom:4px;font-weight:bold;'>{label}</p>", unsafe_allow_html=True)
    
    has_lines = any(out.get("line") for out in outcomes)
    
    if has_lines:
        # Agrupar por línea
        lines_data = {}
        for out in outcomes:
            line = out.get("line")
            if line is None:
                line = ""
            
            try:
                line_key = float(line) if line else 0
            except:
                line_key = 0
            
            if line_key not in lines_data:
                lines_data[line_key] = {"Línea": line}
            
            out_label = out.get("label", "")
            display_label = label_map.get(out_label, out_label)
            lines_data[line_key][display_label] = out.get("odds", 0)
        
        # Crear DataFrame con TODAS las líneas
        rows = [lines_data[k] for k in sorted(lines_data.keys())]
        
        if rows:
            df = pd.DataFrame(rows)
            
            for col in df.columns:
                if col != "Línea":
                    df[col] = df[col].apply(lambda x: f"{x:.2f}" if isinstance(x, (int, float)) and x > 0 else "-")
            
            st.dataframe(df, hide_index=True, use_container_width=True)
    else:
        # Sin líneas - grid de cards
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
