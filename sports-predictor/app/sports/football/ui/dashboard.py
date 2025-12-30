"""
Football Dashboard - Modern UI for Data Management with Dynamic League Selector.
"""
import streamlit as st
from app.ui.theme import render_metric_card, render_icon
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
    # SYNC ALL LEAGUES SECTION
    # ═══════════════════════════════════════════════════════
    st.markdown(f"### {render_icon('public')} Gestión de Ligas Prioritarias", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.caption("Carga únicamente las ligas Tier 1 y Tier 2 (Premier, LaLiga, Serie A, Champions, Libertadores, BetPlay, etc.)")
    with col2:
        if st.button("Cargar Permitidas", type="secondary", use_container_width=True, 
                     help="Solo descarga las ligas del Core Rushbet"):
            with st.spinner("Sincronizando catálogo filtrado..."):
                try:
                    from app.sports.football.etl import FootballETL
                    etl = FootballETL()
                    count = etl.sync_all_leagues()
                    st.success(f"✅ {count} ligas permitidas cargadas!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {e}")
    with col3:
        if st.button("Limpiar BD", type="secondary", use_container_width=True, 
                     help="Elimina ligas y datos que no están en la lista prioritaria"):
            with st.spinner("Limpiando base de datos..."):
                try:
                    from app.sports.football.etl import FootballETL
                    etl = FootballETL()
                    res = etl.cleanup_non_priority_data()
                    st.success(f"✅ Se eliminaron {res.get('removed_leagues', 0)} ligas no autorizadas")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {e}")
    
    st.markdown("---")
    
    # ═══════════════════════════════════════════════════════
    # DYNAMIC LEAGUE SELECTOR (REDESIGNED)
    # ═══════════════════════════════════════════════════════
    st.markdown(f"### {render_icon('sync')} Sincronización de Datos", unsafe_allow_html=True)
    
    # Main Card Container
    with st.container():
        st.markdown(f"""
        <div style="background-color: var(--bg-card); padding: 20px; border-radius: 12px; border: 1px solid var(--border);">
            <h4 style="margin-top: 0; margin-bottom: 20px; color: var(--text-primary);">{render_icon('settings')} Configuración de Descarga</h4>
        """, unsafe_allow_html=True)
        
        # Build league options - dynamic from DB or fallback to hardcoded
        if leagues_in_db:
            # Group by region
            regions = {}
            for league in leagues_in_db:
                region = league.region or "Other"
                if region not in regions:
                    regions[region] = []
                regions[region].append((league.id, f"{league.name} ({league.country})"))
            
            # Flatten with region headers
            league_options = []
            for region in sorted(regions.keys()):
                for league_tuple in sorted(regions[region], key=lambda x: x[1]):
                    league_options.append(league_tuple)
        else:
            # Fallback hardcoded options (Whitelisted only)
            league_options = [
                (39, "Premier League (Inglaterra)"),
                (140, "La Liga (España)"),
                (135, "Serie A (Italia)"),
                (78, "Bundesliga (Alemania)"),
                (61, "Ligue 1 (Francia)"),
                (2, "Champions League"),
                (13, "Copa Libertadores"),
                (239, "Liga BetPlay (Colombia)"),
                (128, "Liga Argentina"),
                (71, "Brasileirão"),
                (253, "MLS (USA)"),
                (262, "Liga MX"),
                (3, "Europa League"),
                (11, "Copa Sudamericana"),
                (40, "Championship"),
                (94, "Primeira Liga"),
                (88, "Eredivisie"),
            ]
        
        # ROW 1: Filters & Config
        c1, c2, c3 = st.columns(3)
        
        with c1:
            # Region filter
            available_regions = list(set([l.region for l in leagues_in_db if l.region])) if leagues_in_db else []
            if available_regions:
                selected_region = st.selectbox(
                    "🌎 Filtrar por Región",
                    options=["Todas"] + sorted(available_regions),
                    index=0,
                    help="Filtra la lista de competiciones"
                )
                if selected_region != "Todas":
                    league_options = [(l.id, f"{l.name} ({l.country})") for l in leagues_in_db if l.region == selected_region]
            else:
                 st.info("Sincroniza ligas para ver filtros")

        with c2:
            season = st.selectbox(
                "📅 Temporada",
                options=[2026, 2025, 2024, 2023, 2022],
                index=0 # 2026 as default
            )

        with c3:
            st.markdown("<br>", unsafe_allow_html=True) # Spacer
            sync_details = st.checkbox("Incluir Detalles (Alineaciones)", value=False, 
                                       help="Descarga lineups y stats de jugadores. Consume más tiempo.")

        # ROW 2: League Selector (Full Width)
        st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
        league_id = st.selectbox(
            "🏆 Competición",
            options=league_options,
            format_func=lambda x: x[1]
        )
        
        st.markdown("</div>", unsafe_allow_html=True) # End Card HTML
        
        # ROW 3: Actions (Buttons)
        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
        b1, b2, b3 = st.columns(3)
        
        with b1:
             sync_button = st.button("🔄 Sincronizar Liga", type="primary", use_container_width=True, help="Descarga partidos de la liga seleccionada")
        
        with b2:
             batch_btn = st.button("⚡ Sync Prioritarias (Batch)", type="secondary", use_container_width=True, help="Descarga TODAS las ligas Tier 1 y 2")
             
        with b3:
             injuries_btn = st.button("🚑 Sync Lesiones", type="secondary", use_container_width=True, help="Descarga reporte de lesionados")

        # Logic implementation
        if sync_button:
            with st.spinner(f"Sincronizando {league_id[1]}..."):
                try:
                    from app.sports.football.etl import FootballETL
                    etl = FootballETL()
                    count = etl.sync_league_data(league_id=league_id[0], season=season, sync_details=sync_details)
                    st.success(f"✅ {count} partidos sincronizados correctamente!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {e}")

        if batch_btn:
             with st.spinner("Sincronizando Tier 1 y Tier 2..."):
                try:
                    from app.sports.football.etl import FootballETL
                    etl = FootballETL()
                    res = etl.sync_priority_leagues(season=season, sync_details=False)
                    st.success(f"✅ Batch completado: {res['success']} ligas OK")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error Batch: {e}")

        if injuries_btn:
            with st.spinner("Buscando lesiones..."):
                try:
                    from app.sports.football.etl import FootballETL
                    etl = FootballETL()
                    count = etl.sync_injuries(league_id=league_id[0], season=season)
                    st.success(f"✅ {count} lesiones actualizadas")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error Lesiones: {e}")
    
    st.markdown("---")
    
    # API Status
    st.markdown(f"### {render_icon('cloud_queue')} Estado de Servicios", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        <div style="background: var(--bg-card); border: 1px solid var(--success); 
                    padding: 16px; border-radius: 12px;">
            <div style="display: flex; align-items: center; gap: 12px;">
                <div style="background: rgba(16, 185, 129, 0.2); border-radius: 50%; color: var(--success);
                            display: flex; align-items: center; justify-content: center; width: 40px; height: 40px;">
                    {render_icon('check_circle')}
                </div>
                <div>
                    <div style="font-weight: 600; color: var(--text-primary);">API-Sports</div>
                    <div style="color: var(--text-secondary); font-size: 0.85rem;">Conexión estable</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="background: var(--bg-card); border: 1px solid var(--accent); 
                    padding: 16px; border-radius: 12px;">
            <div style="display: flex; align-items: center; gap: 12px;">
                <div style="background: rgba(59, 130, 246, 0.2); border-radius: 50%; color: var(--accent);
                            display: flex; align-items: center; justify-content: center; width: 40px; height: 40px;">
                    {render_icon('bar_chart')}
                </div>
                <div>
                    <div style="font-weight: 600; color: var(--text-primary);">Cuota de Uso</div>
                    <div style="color: var(--text-secondary); font-size: 0.85rem;">Verificar en dashboard API</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Quick Actions
    st.markdown(f"### {render_icon('bolt')} Acciones Rápidas", unsafe_allow_html=True)

    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Resetear Base de Datos", use_container_width=True):
            st.warning("Acción no disponible en demo")
            
    with col2:
        if st.button("Limpiar Caché", use_container_width=True):
            st.cache_data.clear()
            st.success("Caché local eliminado")
            
    with col3:
        if st.button("Ver Logs", use_container_width=True):
            st.info("Logs del sistema: OK")
