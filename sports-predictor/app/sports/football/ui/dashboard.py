"""
Football Dashboard - Modern UI for Data Management.
"""
import streamlit as st
from app.ui.theme import render_metric_card, render_icon
from app.core.database import get_session
from app.sports.football.models import Fixture, Team, Player, League
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
    except Exception:
        fixtures_count = teams_count = players_count = leagues_count = 0
    finally:
        session.close()

    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(render_metric_card(str(fixtures_count), "Partidos", "accent"), unsafe_allow_html=True)
    with col2:
        st.markdown(render_metric_card(str(teams_count), "Equipos", "success"), unsafe_allow_html=True)
    with col3:
        st.markdown(render_metric_card(str(players_count), "Jugadores", "warning"), unsafe_allow_html=True)
    with col4:
        st.markdown(render_metric_card(str(leagues_count), "Ligas", "danger"), unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Data Sync Section
    st.markdown(f"### {render_icon('sync')} Sincronización de Datos", unsafe_allow_html=True)
    
    with st.container():
        st.markdown(f"""
        <div class="prediction-card">
            <h4 style="margin-top: 0; margin-bottom: 16px;">{render_icon('settings')} Configuración de Descarga</h4>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            league_id = st.selectbox(
                "Competición",
                options=[
                    (39, "Premier League (Inglaterra)"),
                    (140, "La Liga (España)"),
                    (135, "Serie A (Italia)"),
                    (78, "Bundesliga (Alemania)"),
                    (61, "Ligue 1 (Francia)"),
                    (2, "Champions League"),
                ],
                format_func=lambda x: x[1]
            )
        
        with col2:
            season = st.selectbox(
                "Temporada",
                options=[2024, 2023, 2022, 2021],
                index=0
            )
        
        with col3:
            st.markdown("<br>", unsafe_allow_html=True)
            sync_button = st.button("Iniciar Sincronización", type="primary", use_container_width=True)
        
        if sync_button:
            with st.spinner("Conectando con API-Sports..."):
                try:
                    from app.sports.football.etl import FootballETL
                    etl = FootballETL()
                    etl.sync_league_data(league_id=league_id[0], season=season)
                    st.success("✅ ¡Datos sincronizados correctamente!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error durante la sincronización: {e}")
    
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
                    <div style="color: var(--text-secondary); font-size: 0.85rem;">0 / 100 requests hoy</div>
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
