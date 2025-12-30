"""
Football Team Stats - Statistics calculations for football teams.
"""
from sqlmodel import Session, select
from app.sports.football.models import TeamMatchStats


def get_team_corners_avg(team_id: int, last_n_games: int, session: Session) -> float:
    """
    Calculate the average corners for a team in the last N games.
    """
    statement = (
        select(TeamMatchStats)
        .where(TeamMatchStats.team_id == team_id)
        .order_by(TeamMatchStats.fixture_id.desc())
        .limit(last_n_games)
    )
    results = session.exec(statement).all()
    
    if not results:
        return 0.0
    
    total_corners = sum(r.corner_kicks or 0 for r in results)
    return total_corners / len(results)


def get_team_possession_avg(team_id: int, last_n_games: int, session: Session) -> float:
    """
    Calculate the average possession for a team in the last N games.
    """
    statement = (
        select(TeamMatchStats)
        .where(TeamMatchStats.team_id == team_id)
        .order_by(TeamMatchStats.fixture_id.desc())
        .limit(last_n_games)
    )
    results = session.exec(statement).all()
    
    if not results:
        return 0.0
    
    total_possession = sum(r.possession or 0 for r in results)
    return total_possession / len(results)


def get_team_cards_avg(team_id: int, last_n_games: int, session: Session) -> dict:
    """
    Calculate the average cards (yellow/red) for a team in the last N games.
    """
    statement = (
        select(TeamMatchStats)
        .where(TeamMatchStats.team_id == team_id)
        .order_by(TeamMatchStats.fixture_id.desc())
        .limit(last_n_games)
    )
    results = session.exec(statement).all()
    
    if not results:
        return {"yellow": 0.0, "red": 0.0}
    
    total_yellow = sum(r.yellow_cards or 0 for r in results)
    total_red = sum(r.red_cards or 0 for r in results)
    
    return {
        "yellow": total_yellow / len(results),
        "red": total_red / len(results)
    }
