from sqlmodel import Session, select
from app.database.models import TeamMatchStats

def get_team_corners_avg(team_id: int, last_n_games: int, session: Session):
    """
    Calcula el promedio de córners para un equipo en los últimos N partidos.
    """
    statement = select(TeamMatchStats).where(TeamMatchStats.team_id == team_id).order_by(TeamMatchStats.fixture_id.desc()).limit(last_n_games)
    results = session.exec(statement).all()
    if not results:
        return 0.0
    
    total_corners = sum(r.corner_kicks for r in results)
    return total_corners / len(results)
