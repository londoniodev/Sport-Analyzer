from sqlmodel import Session, select
from app.database.models import TeamMatchStats, PlayerMatchStats

def get_team_corners_with_player(team_id: int, player_id: int, session: Session):
    """
    Calcula el promedio de córners de un equipo cuando un jugador específico juega.
    """
    # Encuentra los partidos en los que el jugador jugó más de 45 minutos.
    player_fixtures_stmt = select(PlayerMatchStats.fixture_id).where(
        PlayerMatchStats.player_id == player_id,
        PlayerMatchStats.team_id == team_id,
        PlayerMatchStats.minutes_played > 45
    )
    player_fixtures_ids = session.exec(player_fixtures_stmt).all()

    if not player_fixtures_ids:
        return 0.0

    # Calcula el promedio de córners en esos partidos.
    corners_stmt = select(TeamMatchStats).where(
        TeamMatchStats.team_id == team_id,
        TeamMatchStats.fixture_id.in_(player_fixtures_ids)
    )
    results = session.exec(corners_stmt).all()

    if not results:
        return 0.0

    total_corners = sum(r.corner_kicks for r in results)
    return total_corners / len(results)
