"""
Vista de detalle de partido de Rushbet.
Muestra mercados de apuestas organizados según especificación exacta.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from app.services.rushbet_api import RushbetClient
from app.ui.theme import render_icon

# Tipos de visualización
CARD = "card"
LIST = "list"

# ==========================================
# CONFIGURACIÓN DE PESTAÑAS (Estática)
# ==========================================
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

def get_dynamic_order(home_team: str, away_team: str):
    """Genera el orden de mercados dinámicamente usando los nombres de equipos."""
    h = home_team.lower()
    a = away_team.lower()
    
    # 1. TIEMPO REGLAMENTARIO
    orden_tiempo_reg = [
        ("resultado final", CARD),
        ("1x2", CARD),
        ("total de goles", LIST), 
        ("doble oportunidad", CARD),
        ("ambos equipos marcarán", CARD),
        ("ambos equipos", CARD),
        ("resultado correcto", LIST),
        ("marcador correcto", LIST),
        ("apuesta sin empate", CARD),
        
        # Específicos de equipo (match más largo debe ir antes si queremos precisión, 
        # pero para "Total de goles" vs "Total de goles de X", el usuario pidió primero el general)
        (f"total de goles de {h}", LIST),
        (f"total de goles de {a}", LIST),
        
        ("descanso/tiempo", LIST),
        ("medio tiempo/final", LIST),
        ("hándicap", LIST),
        ("handicap", LIST),
        
        (f"victoria de {h} y ambos", CARD),
        (f"victoria de {a} y ambos", CARD),
        
        ("gol en ambas mitades", CARD),
    ]

    # 2. MEDIO TIEMPO
    orden_medio_tiempo = [
        ("descanso", CARD),
        ("apuesta sin empate - 1", CARD), 
        ("apuesta sin empate -1", CARD),
        ("doble oportunidad - 1", CARD),
        ("doble oportunidad -1", CARD),
        ("ambos equipos marcarán - 1", CARD),
        ("total de goles - 1", LIST),
        
        (f"total de goles de {h} - 1", LIST),
        (f"total de goles de {a} - 1", LIST),
        
        ("resultado correcto - 1", LIST),
        
        ("2° parte", CARD),
        ("2ª parte", CARD),
        ("2.ª parte", CARD),
        
        ("apuesta sin empate - 2", CARD),
        ("doble oportunidad - 2", CARD),
        ("ambos equipos marcarán - 2", CARD),
        
        ("total de goles - 2", LIST),
        (f"total de goles de {h} - 2", LIST),
        (f"total de goles de {a} - 2", LIST),
    ]

    # 3. CORNERS
    orden_corners = [
        ("total de tiros de esquina", LIST), 
        ("total de esquina", LIST),
        
        (f"esquina a favor de {h}", LIST),
        (f"esquina a favor de {a}", LIST),
        
        ("más tiros de esquina", CARD),
        ("mas tiros de esquina", CARD),
        ("más córners", CARD),
        
        ("hándicap de tiros de esquina", LIST),
        ("handicap de esquina", LIST),
        
        ("siguiente tiro de esquina", CARD),
        
        # Mitades
        ("total de tiros de esquina - 1", LIST),
        (f"esquina por parte de {h} - 1", LIST),
        (f"esquina por parte de {a} - 1", LIST),
        
        ("total de tiros de esquina - 2", LIST),
        (f"esquina a favor de {h} - 2", LIST),
        (f"esquina a favor de {a} - 2", LIST),
        
        ("más córners - 1", CARD),
        ("más córners - 2", CARD),
    ]

    # 4. PARTIDO Y TARJETAS
    orden_tarjetas = [
        ("total de tarjetas", LIST), 
        (f"total de tarjeta {h}", LIST),
        (f" - {h}", LIST), 
        (f"total de tarjeta {a}", LIST),
        (f" - {a}", LIST),
        
        ("tarjeta roja mostrada", CARD),
        (f"tarjeta roja a {h}", CARD),
        (f"tarjeta roja a {a}", CARD),
        
        ("más tarjetas", CARD),
        ("tarjetas hándicap", LIST),
    ]

    # 5. DISPAROS EQUIPO
    orden_disparos = [
        ("número total de disparos", LIST),
        ("número total de tiros", LIST),
        ("tiros a puerta", LIST),
        
        (f"tiros a puerta por parte de {h}", LIST),
        (f"por parte de {h}", LIST),
        
        (f"tiros a puerta por parte de {a}", LIST),
        (f"por parte de {a}", LIST),
        
        ("más tiros a puerta", CARD),
    ]

    # 6. EVENTOS
    orden_eventos = [
        ("primer gol", CARD),
        ("propia meta", CARD),
        (f"victoria de {h} sin recibir", CARD),
        (f"victoria de {a} sin recibir", CARD),
        (f"{h} gana al menos", CARD),
        (f"{a} gana al menos", CARD),
        ("al palo", CARD),
    ]
    
    # Static ones
    orden_handicap_3way = [
        ("hándicap 3-way", LIST),
        ("handicap 3-way", LIST),
    ]
    
    orden_asiaticas = [
        ("hándicap asiático", LIST),
        ("handicap asiático", LIST),
        ("total asiático", LIST),
    ]

    return {
        "tiempo_reglamentario": orden_tiempo_reg,
        "medio_tiempo": orden_medio_tiempo,
        "corners": orden_corners,
        "tarjetas_equipo": orden_tarjetas,
        "disparos_equipo": orden_disparos,
        "eventos_partido": orden_eventos,
        "handicap_3way": orden_handicap_3way,
        "lineas_asiaticas": orden_asiaticas,
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
    
    # GENERAR ORDEN DINÁMICO
    ORDEN_POR_CATEGORIA = get_dynamic_order(home_team, away_team)
    
    # Pestañas
    tabs_with_data = []
    for tab_name, categories in TABS_CONFIG.items():
        count = sum(len(markets.get(cat, [])) for cat in categories)
        if count > 0:
            tabs_with_data.append((tab_name, categories, count))
    
    if not tabs_with_data:
        st.info("No hay mercados adicionales disponibles.")
        # Logs incluso si no hay data
        _render_debug_logs(markets)
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

    # --- DEBUG LOGS DETALLADOS ---
    _render_debug_logs(markets)


def _render_debug_logs(markets):
    with st.expander("Logs del Sistema (Debug) - DETALLE DE LABELS", expanded=False):
        st.write("Estructura de Labels encontrados:")
        all_markets_flat = []
        for cat, m_list in markets.items():
            for m in m_list:
                all_markets_flat.append({
                    "category": cat,
                    "label": m.get("label"),
                    "outcomes_count": len(m.get("outcomes", [])),
                    "example_outcome": m.get("outcomes")[0].get("label") if m.get("outcomes") else None
                })
        
        if all_markets_flat:
            st.dataframe(pd.DataFrame(all_markets_flat), use_container_width=True)
        else:
            st.info("No hay datos de mercados para mostrar en logs.")


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


def _render_category_markets(markets: list, home_team: str, away_team: str, orden: list = None):
    """Renderiza los mercados de una categoría."""
    
    label_map = {"1": home_team, "X": "Empate", "2": away_team, "Over": "Más de", "Under": "Menos de"}
    
    # 1. AGRUPAR MERCADOS POR LABEL
    # La API a veces devuelve múltiples objetos con el mismo label (ej. "Total de goles")
    grouped_markets = {}
    for market in markets:
        lbl = market.get("label", "Mercado")
        if lbl not in grouped_markets:
            grouped_markets[lbl] = []
        grouped_markets[lbl].extend(market.get("outcomes", []))
    
    # Reconstruir lista de mercados únicos consolidados
    consolidated_markets = []
    for lbl, outcomes in grouped_markets.items():
        consolidated_markets.append({"label": lbl, "outcomes": outcomes})

    # 2. ORDENAR
    if orden:
        # Usamos la lista consolidada
        final_markets = _sort_markets_by_order(consolidated_markets, orden)
    else:
        final_markets = consolidated_markets

    for market in final_markets:
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
    
    # Si hay muchos outcomes (ej. marcadores correctos duplicados por agrupación), 
    # mostrar solo únicos o limitar?
    # En card view solemos querer ver todo, pero cuidado con duplicados.
    # Deduplicar por label + line
    unique_outcomes = {}
    for out in outcomes:
        key = (out.get("label"), out.get("line"))
        unique_outcomes[key] = out
    
    sorted_outcomes = list(unique_outcomes.values())
    
    n_cols = min(len(sorted_outcomes), 4)
    if n_cols == 0: n_cols = 1
    cols = st.columns(n_cols)
    
    for i, outcome in enumerate(sorted_outcomes):
        with cols[i % n_cols]:
            odds = outcome.get("odds", 0)
            out_label = outcome.get("label", "")
            line = outcome.get("line")
            
            display_label = label_map.get(out_label, out_label)
            if line:
                display_label = f"{display_label} ({line})"
            
            # Negrita para equipos/empate en resultado final
            if out_label in ["1", "X", "2"] and "resultado final" in label.lower():
                display_label = f"<b>{display_label}</b>"
            elif out_label in label_map.values(): 
                 display_label = f"<b>{display_label}</b>"

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
        processed_keys = set()
        
        for out in outcomes:
            raw_line = out.get("line")
            odds = out.get("odds", 0)
            out_label = out.get("label", "")
            
            # Crear key única para evitar duplicados exactos
            unique_key = (raw_line, out_label, odds)
            if unique_key in processed_keys:
                continue
            processed_keys.add(unique_key)
            
            # Normalizar línea (Kambi suele enviar 2500 para 2.5)
            display_line = raw_line
            line_sort_key = 0
            
            if raw_line is not None:
                try:
                    val = float(raw_line)
                    # Heurística: Si es > 50, asumimos que está escalado por 1000
                    if val >= 50: 
                        val = val / 1000.0
                        if val.is_integer():
                            display_line = str(int(val))
                        else:
                            display_line = str(val)
                    else:
                        display_line = str(val).rstrip("0").rstrip(".") if "." in str(val) else str(val)
                    
                    line_sort_key = val
                except:
                    display_line = str(raw_line)
                    line_sort_key = 0
            else:
                display_line = ""

            if line_sort_key not in lines_data:
                lines_data[line_sort_key] = {"Valor": display_line}
            
            display_label = label_map.get(out_label, out_label)
            # Guardar el valor raw, el formateo será visual en dataframe
            lines_data[line_sort_key][display_label] = odds
        
        # Crear DataFrame
        rows = [lines_data[k] for k in sorted(lines_data.keys())]
        
        if rows:
            df = pd.DataFrame(rows)
            
            cols = ["Valor"] + [c for c in df.columns if c != "Valor"]
            
            # Prioridades de columnas
            priority_cols = ["Más de", "Menos de", "Si", "No"]
            sorted_cols = ["Valor"]
            remaining = [c for c in cols if c != "Valor"]
            
            for p in priority_cols:
                if p in remaining:
                    sorted_cols.append(p)
                    remaining.remove(p)
            sorted_cols.extend(remaining)
            
            df = df[sorted_cols]
            
            # Configurar columnas para 2 decimales
            column_config = {}
            for col in sorted_cols:
                if col != "Valor":
                    column_config[col] = st.column_config.NumberColumn(
                        label=col,
                        format="%.2f"
                    )
            
            st.dataframe(
                df, 
                hide_index=True, 
                use_container_width=True,
                column_config=column_config
            )
    else:
        # Sin líneas
        unique_outcomes = {}
        for out in outcomes:
            key = (out.get("label"), out.get("odds"))
            unique_outcomes[key] = out
            
        final_outcomes = list(unique_outcomes.values())
        
        # Si es Resultado Correcto, intentar tabla con formato
        if "resultado correct" in label.lower() or "marcador" in label.lower():
             data = []
             for out in final_outcomes:
                 data.append({
                     "Resultado": out.get("label"),
                     "Cuota": out.get("odds")
                 })
             
             df_rc = pd.DataFrame(data)
             st.dataframe(
                 df_rc, 
                 hide_index=True, 
                 use_container_width=True,
                 column_config={
                     "Cuota": st.column_config.NumberColumn(format="%.2f")
                 }
             )
        else:
             # Fallback a cards
             _render_as_card(label, final_outcomes, label_map)
    
    st.markdown("")
