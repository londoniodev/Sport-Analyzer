"""
Football Dashboard - Modern UI for Data Management with Dynamic League Selector.
"""
import streamlit as st
from app.ui import render_metric_card, render_icon
from app.core.database import get_session
from app.sports.football.models import Fixture, Team, Player, League, Injury
from sqlmodel import select, func


def show_dashboard():
    """Display the football dashboard with professional UI."""
    
    # Header
    st.markdown(f"""
    <div style="margin-bottom: 24px;">
        <h1 style="margin: 0;">{render_icon('dashboard')} Panel de Control</h1>
        <p style="color: var(--text-secondary); margin-top: 8px;">Gestión de datos, sincronización y estado del sistema</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Stats Overview
    st.markdown(f"### {render_icon('database')} Estadísticas de la Base de Datos", unsafe_allow_html=True)
    
    # Fetch real counts
    session = next(get_session())
    try:
        fixtures_count = session.exec(select(func.count(Fixture.id))).one()
        teams_count = session.exec(select(func.count(Team.id))).one()
        players_count = session.exec(select(func.count(Player.id))).one()
        leagues_count = session.exec(select(func.count(League.id))).one()
        injuries_count = session.exec(select(func.count(Injury.id))).one()
        
        # Get leagues for dynamic selector
        leagues_in_db = session.exec(select(League).order_by(League.region, League.name)).all()
    except Exception:
        fixtures_count = teams_count = players_count = leagues_count = injuries_count = 0
        leagues_in_db = []
    finally:
        session.close()

    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(render_metric_card(str(fixtures_count), "Partidos", "accent"), unsafe_allow_html=True)
    with col2:
        st.markdown(render_metric_card(str(teams_count), "Equipos", "success"), unsafe_allow_html=True)
    with col3:
        st.markdown(render_metric_card(str(players_count), "Jugadores", "warning"), unsafe_allow_html=True)
    with col4:
        st.markdown(render_metric_card(str(leagues_count), "Ligas", "danger"), unsafe_allow_html=True)
    with col5:
        st.markdown(render_metric_card(str(injuries_count), "Lesiones", "accent"), unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ═══════════════════════════════════════════════════════
    # SYNC SECTION - REDESIGNED
    # ═══════════════════════════════════════════════════════
    st.markdown(f"### {render_icon('sync')} Sincronización de Datos", unsafe_allow_html=True)
    
    # Build league options - Merge DB with Static for better UX
    static_leagues = [
        (39, "Premier League", "England", "Europe"),
        (140, "La Liga", "Spain", "Europe"),
        (135, "Serie A", "Italy", "Europe"),
        (78, "Bundesliga", "Germany", "Europe"),
        (61, "Ligue 1", "France", "Europe"),
        (2, "Champions League", "World", "Europe"),
        (13, "Copa Libertadores", "South America", "South America"),
        (239, "Liga BetPlay", "Colombia", "South America"),
        (128, "Liga Profesional", "Argentina", "South America"),
        (71, "Brasileirão", "Brazil", "South America"),
        (253, "MLS", "USA", "North America"),
        (262, "Liga MX", "Mexico", "North America"),
        (3, "Europa League", "World", "Europe"),
        (11, "Copa Sudamericana", "South America", "South America"),
        (40, "Championship", "England", "Europe"),
        (94, "Primeira Liga", "Portugal", "Europe"),
        (88, "Eredivisie", "Netherlands", "Europe"),
        (307, "Pro League", "Saudi Arabia", "Asia"),
    ]

    # Create a dict of existing leagues to avoid duplicates
    db_league_ids = {l.id for l in leagues_in_db}
    
    # Start with DB leagues
    final_options = []
    
    # Helper to format label
    def format_league_label(name, country):
        return f"{name} ({country})"

    # Add DB leagues first
    for league in leagues_in_db:
        final_options.append({
            "id": league.id,
            "label": format_league_label(league.name, league.country),
            "region": league.region or "Other"
        })

    # Add static leagues if not in DB
    for lid, name, country, region in static_leagues:
        if lid not in db_league_ids:
            final_options.append({
                "id": lid,
                "label": format_league_label(name, country),
                "region": region
            })
    
    # Sort options
    final_options.sort(key=lambda x: x["label"])
    
    # Prepare list for selectbox
    league_options = [(opt["id"], opt["label"]) for opt in final_options]
    
    # Extract available regions for filtering
    available_regions = sorted(list(set(opt["region"] for opt in final_options)))

    # Main sync card with expander for cleaner look
    with st.expander("Configuración de Descarga", expanded=True):
        
        # Region Filter (Top for better flow)
        selected_region = "Todas"
        if available_regions:
            col_filter, _ = st.columns([1, 2])
            with col_filter:
                selected_region = st.selectbox(
                    "Filtrar por Región",
                    options=["Todas"] + sorted(available_regions),
                    index=0
                )
        
        # Apply filter
        filtered_options = league_options
        if selected_region != "Todas":
            filtered_options = [(opt["id"], opt["label"]) for opt in final_options if opt["region"] == selected_region]

        # Row 1: League and Season
        col_league, col_season = st.columns([3, 1])
        
        with col_league:
            league_id = st.selectbox(
                "Competición",
                options=filtered_options,
                format_func=lambda x: x[1],
            )
        
        with col_season:
            season = st.selectbox(
                "Temporada",
                options=[2026, 2025, 2024, 2023, 2022],
                index=0
            )

        # Options
        sync_details = st.checkbox("Incluir Detalles (Alineaciones)", value=False, help="Descarga lineups y estadísticas de jugadores")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Row 3: Action buttons
        b1, b2, b3 = st.columns(3)
        
        with b1:
            sync_button = st.button("Sincronizar Liga", type="primary", use_container_width=True)
        
        with b2:
            batch_btn = st.button("Sync Prioritarias", type="secondary", use_container_width=True, help="Todas las Tier 1 y 2")
             
        with b3:
            injuries_btn = st.button("Sync Lesiones", type="secondary", use_container_width=True)

        # Logic implementation
        if sync_button:
            with st.spinner(f"Sincronizando {league_id[1]}..."):
                try:
                    from app.sports.football.etl import FootballETL
                    etl = FootballETL()
                    count = etl.sync_league_data(league_id=league_id[0], season=season, sync_details=sync_details)
                    st.success(f"Operación completada: {count} partidos sincronizados.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

        if batch_btn:
             with st.spinner("Sincronizando Tier 1 y Tier 2..."):
                try:
                    from app.sports.football.etl import FootballETL
                    etl = FootballETL()
                    res = etl.sync_priority_leagues(season=season, sync_details=False)
                    st.success(f"Batch completado: {res['success']} ligas procesadas correctamente.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error Batch: {e}")

        if injuries_btn:
            with st.spinner("Buscando lesiones..."):
                try:
                    from app.sports.football.etl import FootballETL
                    etl = FootballETL()
                    count = etl.sync_injuries(league_id=league_id[0], season=season)
                    st.success(f"Lesiones actualizadas: {count}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error Lesiones: {e}")
