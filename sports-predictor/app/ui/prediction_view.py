import streamlit as st
from app.database.config import get_session
from app.analytics.team_stats import get_team_corners_avg
from app.analytics.impact_engine import get_team_corners_with_player
from app.database.models import Fixture, Team, Player

def show_prediction_view():
    st.title("Analizador de Partido (Pre-Match)")

    session = next(get_session())

    # Mock data - Reemplazar con datos reales de la BD
    fixtures = session.query(Fixture).all()
    teams = session.query(Team).all()
    players = session.query(Player).all()
    
    selected_fixture = st.selectbox("Elegir Partido", fixtures, format_func=lambda f: f"{f.home_team.name} vs {f.away_team.name}")

    if selected_fixture:
        home_team = selected_fixture.home_team
        away_team = selected_fixture.away_team

        st.subheader(f"Análisis para {home_team.name} vs {away_team.name}")

        # Simulación de selección de alineación
        probable_lineup_ids = st.multiselect(
            f"Alineación Probable para {home_team.name}",
            [p.id for p in players if p.team_id == home_team.id], # Filtrar por equipo
            format_func=lambda p_id: next(p for p in players if p.id == p_id).name
        )

        avg_corners_general = get_team_corners_avg(home_team.id, 10, session)
        st.write(f"Promedio Córners {home_team.name} (General): {avg_corners_general:.2f}")

        if probable_lineup_ids:
            # Lógica para calcular córners con la alineación seleccionada
            # Esto es una simplificación. La lógica real sería más compleja.
            avg_corners_with_players = 0
            for player_id in probable_lineup_ids:
                 avg_corners_with_players += get_team_corners_with_player(home_team.id, player_id, session)
            
            avg_corners_with_players = avg_corners_with_players / len(probable_lineup_ids) if probable_lineup_ids else 0

            st.write(f"Promedio Córners {home_team.name} (Con estos {len(probable_lineup_ids)} jugadores): **{avg_corners_with_players:.2f}**")

        st.write(f"Árbitro: {selected_fixture.referee_name} (Promedio Tarjetas: 3.5 - BAJO)") # Dato de ejemplo
