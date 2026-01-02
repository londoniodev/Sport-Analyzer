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

def _apply_table_styles(df: pd.DataFrame, numeric_cols: list = None):
    """
    Aplica estilos estandarizados a las tablas:
    1. Centrado de encabezados y celdas.
    2. Mapa de calor (Heatmap) con degradado: Rojo (Min) -> Amarillo (Medio) -> Verde (Max).
    """
    # Centrado CSS robusto
    styler = df.style.set_properties(**{
        'text-align': 'center', 
        'vertical-align': 'middle'
    }).set_table_styles([
        {'selector': 'th', 'props': [('text-align', 'center !important')]},
        {'selector': 'td', 'props': [('text-align', 'center !important')]}
    ])
    
    if not numeric_cols:
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        
    def get_gradient_style(s):
        # Si no hay variación, devolver lista vacía
        if s.nunique() <= 1 or s.empty:
            return ['' for _ in s]
            
        s_min = s.min()
        s_max = s.max()
        rng = s_max - s_min
        
        # Colores RGB para interpolación
        # Rojo (Min): #7f1d1d (Rojo muy oscuro para fondo) -> mejor usaremos un rojo visible pero no chillón
        # Ajuste: Usaremos colores que contrasten bien en modo oscuro pero se noten.
        # Min: Rojo (#991b1b)
        # Mid: Amarillo (#a16207) - Un amarillo ocre para que el texto blanco se lea, o negro?
        # Max: Verde (#166534)
        
        # Intentemos colores más "brillantes" con opacidad o saturación controlada:
        # Min: #ef4444 (Red-500)
        # Mid: #eab308 (Yellow-500)
        # Max: #22c55e (Green-500)
        
        # Definición RGB
        c_min = (239, 68, 68)   # Red
        c_mid = (234, 179, 8)   # Yellow
        c_max = (34, 197, 94)   # Green
        
        styles = []
        for val in s:
            if pd.isna(val):
                styles.append('')
                continue
                
            # Normalizar 0..1
            norm = (val - s_min) / rng if rng != 0 else 0
            
            # Interpolación
            if norm <= 0.5:
                # Interpolar entre Min y Mid (norm va de 0 a 0.5 -> reescalar a 0..1)
                local_norm = norm / 0.5
                r = int(c_min[0] + (c_mid[0] - c_min[0]) * local_norm)
                g = int(c_min[1] + (c_mid[1] - c_min[1]) * local_norm)
                b = int(c_min[2] + (c_mid[2] - c_min[2]) * local_norm)
            else:
                # Interpolar entre Mid y Max (norm va de 0.5 a 1 -> reescalar a 0..1)
                local_norm = (norm - 0.5) / 0.5
                r = int(c_mid[0] + (c_max[0] - c_mid[0]) * local_norm)
                g = int(c_mid[1] + (c_max[1] - c_mid[1]) * local_norm)
                b = int(c_mid[2] + (c_max[2] - c_mid[2]) * local_norm)
                
            # Determinar color de texto (Blanco para extremos oscuros, Negro para amarillo brillante)
            # Aproximación simple de luminancia: (0.299*R + 0.587*G + 0.114*B)
            lum = (0.299*r + 0.587*g + 0.114*b)
            text_color = '#000000' if lum > 140 else '#ffffff'
            
            # Formatear CSS con transparencia ligera para no ser tan agresivo
            styles.append(f'background-color: rgba({r},{g},{b}, 0.7); color: {text_color}; font-weight: bold;')
            
        return styles

    # Aplicar a clumnas numéricas
    for col in numeric_cols:
        if col in df.columns:
            styler = styler.apply(get_gradient_style, subset=[col])
            
    return styler

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
                if cat_markets:
                    cat_name = NOMBRES_CATEGORIAS.get(cat_key, cat_key)
                    with st.expander(f"{cat_name} ({len(cat_markets)})", expanded=(cat_key == "tiempo_reglamentario")):
                        if cat_key == "goleador":
                            _render_scorers_markets(cat_markets)
                        elif cat_key == "tarjetas_jugador":
                            _render_player_cards_markets(cat_markets)
                        else:
                            _render_category_markets(cat_markets, home_team, away_team, orden)

    # --- DEBUG LOGS DETALLADOS ---
    _render_debug_logs(markets)


def _render_scorers_markets(markets: list):
    """Renderiza tabla consolidada de goleadores (Primer Gol + Marcará)."""
    # 1. Extraer datos
    players_data = {}
    
    # Identificar mercados
    first_scorer_mkt = []
    anytime_scorer_mkt = []
    
    for m in markets:
        lbl = m.get("label", "").lower()
        if "primer" in lbl and "goleador" in lbl:
            first_scorer_mkt.extend(m.get("outcomes", []))
        elif "marca" in lbl or "marcará" in lbl or "cualquier momento" in lbl:
            anytime_scorer_mkt.extend(m.get("outcomes", []))
            
    if not first_scorer_mkt and not anytime_scorer_mkt:
        st.info("No hay datos de goleadores disponibles.")
        return

    # Título unificado
    st.markdown(f"<p style='margin-bottom:4px;font-weight:bold;'>Goleadores</p>", unsafe_allow_html=True)

    # 2. Procesar Primer Goleador
    for out in first_scorer_mkt:
        # Priorizar participant si existe, sino label
        name = out.get("participant") or out.get("label")
        if not name: continue
        
        if name not in players_data:
            players_data[name] = {"Jugador": name, "Primer Gol": None, "Marcará": None}
        players_data[name]["Primer Gol"] = out.get("odds")

    # 3. Procesar Marcará
    for out in anytime_scorer_mkt:
        # Priorizar participant si existe (para casos donde label es "Sí")
        name = out.get("participant") or out.get("label")
        if not name: continue
        
        # Ignorar "Ningún Goleador" si sale como Sí/No o similar
        if "ningún" in name.lower() or name == "Sí":
             # Si después de todo el nombre sigue siendo "Sí", algo falla en los datos o es un mercado binario sin participante
             # pero en el JSON vimos participant="Florian..."
             continue

        if name not in players_data:
            players_data[name] = {"Jugador": name, "Primer Gol": None, "Marcará": None}
        players_data[name]["Marcará"] = out.get("odds")
    
    # 4. Crear DataFrame
    data_list = list(players_data.values())
    if not data_list:
        return
        
    df = pd.DataFrame(data_list)
    
    # Ordenar: Prioridad a quienes tienen cuota de Primer Gol más baja, luego Marcará
    df["_sort_first"] = df["Primer Gol"].fillna(9999)
    df["_sort_any"] = df["Marcará"].fillna(9999)
    df = df.sort_values(by=["_sort_first", "_sort_any"])
    
    # Seleccionar columnas finales
    cols = ["Jugador", "Primer Gol", "Marcará"]
    final_df = df[cols]
    
    # 5. Renderizar tabla con estilos
    # APLICAR ESTILOS CENTRALIZADOS
    # 'Primer Gol' y 'Marcará' son las numéricas
    numeric_cols = ["Primer Gol", "Marcará"]
    styler = _apply_table_styles(final_df, numeric_cols)
    
    column_config = {
        "Primer Gol": st.column_config.NumberColumn(format="%.2f"),
        "Marcará": st.column_config.NumberColumn(format="%.2f")
    }

    # Calcular altura dinámica: ~35px por fila + 38px encabezado
    # Mínimo 150px, sin máximo (o un máximo muy alto si se prefiere)
    # Ajustar según CSS de Streamlit actual, 35 es un estándar razonable.
    rows_count = len(final_df)
    dynamic_height = (rows_count + 1) * 35 + 3
    
    st.dataframe(
        styler, 
        hide_index=True, 
        use_container_width=True,
        column_config=column_config,
        height=dynamic_height
    )
    st.markdown("")


def _render_player_cards_markets(markets: list):
    """Renderiza mercados de tarjetas de jugadores en tabla consolidada."""
    player_list_markets = []
    other_markets = []
    
    # 1. Clasificar mercados
    for m in markets:
        outcomes = m.get("outcomes", [])
        lbl = m.get("label", "").lower()
        # "Recibirá tarjeta" es genérico, "tarjeta roja" específico.
        if "recibirá" in lbl:
            player_list_markets.append(m)
        else:
            other_markets.append(m)
            
    # 2. Procesar datos de jugadores consolidado
    if player_list_markets:
        players_data = {}
        
        # Mapeo de columnas: label del mercado -> nombre columna
        # "Recibirá una tarjeta" -> "Tarjeta"
        # "Recibirá una tarjeta roja" -> "Roja"
        
        for m in player_list_markets:
            raw_label = m.get("label", "")
            lbl_lower = raw_label.lower()
            
            col_name = "Tarjeta" # Default
            if "roja" in lbl_lower:
                col_name = "Roja"
            elif "tarjeta" in lbl_lower and "roja" not in lbl_lower:
                col_name = "Tarjeta"
            else:
                col_name = raw_label # Fallback
                
            for out in m.get("outcomes", []):
                # Usar participant si existe (igual que en goleadores)
                p_name = out.get("participant") or out.get("label")
                if not p_name or p_name == "Sí": 
                    continue
                    
                if p_name not in players_data:
                    players_data[p_name] = {"Jugador": p_name}
                
                players_data[p_name][col_name] = out.get("odds")
        
        # 3. Crear DataFrame Unificado
        data_list = list(players_data.values())
        if data_list:
            st.markdown(f"<p style='margin-bottom:4px;font-weight:bold;'>Tarjetas de Jugadores</p>", unsafe_allow_html=True)
            df = pd.DataFrame(data_list)
            
            # Asegurar columnas existen
            if "Tarjeta" not in df.columns: df["Tarjeta"] = None
            if "Roja" not in df.columns: df["Roja"] = None
            
            # Columnas a mostrar
            cols_to_show = ["Jugador"]
            numeric_cols = []
            
            if df["Tarjeta"].notna().any():
                cols_to_show.append("Tarjeta")
                numeric_cols.append("Tarjeta")
            if df["Roja"].notna().any():
                cols_to_show.append("Roja")
                numeric_cols.append("Roja")
                
            # Ordenar: Prioridad a Tarjeta (más común/baja cuota)
            if "Tarjeta" in df.columns:
                df = df.sort_values(by="Tarjeta")
            elif "Roja" in df.columns:
                 df = df.sort_values(by="Roja")
                 
            final_df = df[cols_to_show]
            
            # Estilos
            styler = _apply_table_styles(final_df, numeric_cols)
            
            column_config = {
                "Tarjeta": st.column_config.NumberColumn(format="%.2f"),
                "Roja": st.column_config.NumberColumn(format="%.2f")
            }
            
            # Altura dinámica
            rows_count = len(final_df)
            dynamic_height = (rows_count + 1) * 35 + 3
            
            st.dataframe(
                styler,
                hide_index=True,
                use_container_width=True,
                column_config=column_config,
                height=dynamic_height
            )
            st.markdown("")

    # 4. Renderizar Otros (Cards estándar - ej. Total tarjetas equipo)
    if other_markets:
        if player_list_markets: st.markdown("---")
        for m in other_markets:
            _render_as_card(m.get("label"), m.get("outcomes", []), {})


def _render_debug_logs(markets):
    with st.expander("Logs del Sistema (Debug) - JSON CRUDO", expanded=False):
        st.write("Estructura completa de mercados (JSON):")
        st.json(markets)


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
    """Renderiza el encabezado del partido con diseño mejorado."""
    home_team = details.get("home_team", event_basic.get("home_team", "Local"))
    away_team = details.get("away_team", event_basic.get("away_team", "Visitante"))
    state = details.get("state", "NOT_STARTED")
    score = details.get("score", {})
    
    state_display = "PRÓXIMO"
    score_display = "VS"
    time_display = ""
    
    if state == "STARTED":
        state_display = "EN VIVO"
        score_display = f"{score.get('home', 0)} - {score.get('away', 0)}"
    elif state == "FINISHED":
        state_display = "FINALIZADO"
        score_display = f"{score.get('home', 0)} - {score.get('away', 0)}"
    else:
        start_time = details.get("start_time", event_basic.get("start_time"))
        if start_time:
            try:
                dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                # Ajustar a hora local aproximada o dejar en UTC si no hay info de zona
                # Mostramos solo hora por simplicidad
                time_display = dt.strftime('%H:%M')
            except:
                pass
    
    # CSS personalizado para el header
    st.markdown(f"""
        <style>
            .match-header-container {{
                background-color: #0f172a;
                border-radius: 12px;
                padding: 24px;
                margin-bottom: 24px;
                display: flex;
                align-items: center;
                justify-content: space-between;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
                border: 1px solid #1e293b;
            }}
            .team-name {{
                font-size: 24px;
                font-weight: 700;
                color: #f8fafc;
                width: 35%;
                text-align: center;
            }}
            .match-info {{
                display: flex;
                flex-direction: column;
                align-items: center;
                width: 30%;
            }}
            .match-score {{
                font-size: 48px;
                font-weight: 800;
                color: #ffffff;
                line-height: 1.2;
            }}
            .match-time {{
                font-size: 32px;
                font-weight: 700;
                color: #ffffff;
            }}
            .match-status {{
                margin-top: 8px;
                padding: 4px 12px;
                border-radius: 99px;
                font-size: 12px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
            .status-live {{
                background-color: #22c55e;
                color: #052e16;
            }}
            .status-upcoming {{
                background-color: #334155;
                color: #94a3b8;
            }}
            .status-finished {{
                 background-color: #ef4444;
                color: #450a0a;
            }}
            .team-label {{
                font-size: 12px;
                text-transform: uppercase;
                letter-spacing: 1px;
                color: #64748b;
                margin-top: 4px;
                display: block;
            }}
            /* Ajuste mobile */
            @media (max-width: 640px) {{
                .match-header-container {{
                    flex-direction: column;
                    text-align: center;
                    gap: 16px;
                }}
                .team-name {{
                    width: 100%;
                }}
            }}
        </style>
    """, unsafe_allow_html=True)

    status_class = "status-upcoming"
    if state == "STARTED": status_class = "status-live"
    elif state == "FINISHED": status_class = "status-finished"
    
    center_content = ""
    if state in ["STARTED", "FINISHED"]:
        center_content = f'<div class="match-score">{score_display}</div>'
    else:
        if time_display:
            center_content = f'<div class="match-time">{time_display}</div>'
        else:
             center_content = f'<div class="match-score">VS</div>'

    html = f"""
<div class="match-header-container">
<div class="team-name">
{home_team}
<span class="team-label">Local</span>
</div>
<div class="match-info">
{center_content}
<div class="match-status {status_class}">{state_display}</div>
</div>
<div class="team-name">
{away_team}
<span class="team-label">Visitante</span>
</div>
</div>
"""
    
    st.markdown(html, unsafe_allow_html=True)


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
    # NO imprimir label aquí globalmente, hacerlo en cada bloque para evitar duplicados en fallback
    
    has_lines = any(out.get("line") for out in outcomes)
    
    if has_lines:
        st.markdown(f"<p style='margin-bottom:4px;font-weight:bold;'>{label}</p>", unsafe_allow_html=True)
        
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
            
            # Normalizar línea
            display_line = raw_line
            line_sort_key = 0
            
            if raw_line is not None:
                try:
                    val = float(raw_line)
                    # Heurística: Si la magnitud es >= 50, asumimos que está escalado por 1000
                    # Handicap 3-Way usa valores como -6000 (-6), -4000 (-4)
                    if abs(val) >= 50: 
                        val = val / 1000.0
                    
                    if val.is_integer():
                        base_str = str(int(val))
                    else:
                        base_str = str(val)
                    
                    is_handicap_mkt = "hándicap" in label.lower() or "handicap" in label.lower() or "asiático" in label.lower()
                    if is_handicap_mkt and val > 0:
                        display_line = f"+{base_str}"
                    else:
                        display_line = base_str
                    
                    line_sort_key = val
                except:
                    display_line = str(raw_line)
                    line_sort_key = 0
            else:
                display_line = ""

            # Determinar nombre columna principal
            col_name_first = "Valor"
            if "3-way" in label.lower():
                col_name_first = "Comienza en"

            if line_sort_key not in lines_data:
                lines_data[line_sort_key] = {col_name_first: display_line}
            
            display_label = label_map.get(out_label, out_label)
            # Guardar el valor raw, el formateo será visual en dataframe
            lines_data[line_sort_key][display_label] = odds
        
        # Crear DataFrame
        rows = [lines_data[k] for k in sorted(lines_data.keys())]
        
        if rows:
            df = pd.DataFrame(rows)
            
            # Obtener nombre dinámico de primera columna
            first_col = [c for c in df.columns if c in ["Valor", "Comienza en"]][0]
            
            cols = [first_col] + [c for c in df.columns if c != first_col]
            
            # Prioridades de columnas
            priority_cols = ["Más de", "Menos de", "Si", "No", "Empate"] # Empate importante en 3-way
            sorted_cols = [first_col]
            remaining = [c for c in cols if c != first_col]
            
            for p in priority_cols:
                if p in remaining:
                    sorted_cols.append(p)
                    remaining.remove(p)
            sorted_cols.extend(remaining)
            
            df = df[sorted_cols]
            
            # Configurar columnas para 2 decimales y preparar lista de numéricas para estilo
            column_config = {}
            numeric_cols_for_style = []
            
            for col in sorted_cols:
                if col != first_col:
                    numeric_cols_for_style.append(col)
                    column_config[col] = st.column_config.NumberColumn(
                        label=col,
                        format="%.2f"
                    )
            
            # APLICAR ESTILOS CENTRALIZADOS
            styler = _apply_table_styles(df, numeric_cols_for_style)

            st.dataframe(
                styler, 
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
        
        label_lower = label.lower()
        is_result_correct = "resultado correct" in label_lower or "marcador" in label_lower
        is_half_time_full_time = "descanso" in label_lower or "medio tiempo" in label_lower
        
        # Si es Resultado Correcto O Descanso/Tiempo reglamentario -> TABLA
        if is_result_correct or is_half_time_full_time:
             st.markdown(f"<p style='margin-bottom:4px;font-weight:bold;'>{label}</p>", unsafe_allow_html=True)
             
             # Ordenamiento específico
             if is_result_correct:
                 # Función para ordenar: 1-0 -> (1, 0)
                 def get_score_sort_key(outcome):
                     lbl = outcome.get("label", "")
                     try:
                         # Buscar patrón N-M
                         if "-" in lbl:
                             parts = lbl.split("-")
                             p1 = part_to_int(parts[0])
                             p2 = part_to_int(parts[1])
                             return (p1, p2)
                         return (999, 999) # Otros al final
                     except:
                         return (999, 999)
                
                 def part_to_int(p):
                     return int(''.join(filter(str.isdigit, p)))

                 # Ordenar outcomes
                 final_outcomes.sort(key=get_score_sort_key)

             data = []
             col_name_res = "Resultado"
             # Ajustar nombre columna para D/T
             if is_half_time_full_time:
                 col_name_res = "Descanso / Final"
             
             for out in final_outcomes:
                 data.append({
                     col_name_res: out.get("label"),
                     "Cuota": out.get("odds")
                 })
             
             df_rc = pd.DataFrame(data)
             
             # Estilos
             # APLICAR ESTILOS CENTRALIZADOS
             styler_rc = _apply_table_styles(df_rc, ["Cuota"])

             st.dataframe(
                 styler_rc, 
                 hide_index=True, 
                 use_container_width=True,
                 column_config={
                     "Cuota": st.column_config.NumberColumn(format="%.2f")
                 }
             )
        else:
             # Fallback a cards (ya imprime su propio label)
             _render_as_card(label, final_outcomes, label_map)
    
    st.markdown("")
