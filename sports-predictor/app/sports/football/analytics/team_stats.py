"""
Football Team Stats - Statistics calculations for football teams.
"""
from sqlmodel import Session, select
from app.sports.football.models import TeamMatchStats, Fixture


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


def get_team_corners_conceded_avg(team_id: int, last_n_games: int, session: Session) -> float:
    """
    Calculate average corners conceded by a team (opponents' corners).
    """
    # Find last N fixture IDs for this team
    fixture_stmt = (
        select(Fixture.id)
        .where((Fixture.home_team_id == team_id) | (Fixture.away_team_id == team_id))
        .order_by(Fixture.date.desc())
        .limit(last_n_games)
    )
    fixture_ids = session.exec(fixture_stmt).all()
    
    if not fixture_ids:
        return 0.0
        
    # Get stats of the OTHER team in those same fixtures
    opponent_stats_stmt = (
        select(TeamMatchStats)
        .where(TeamMatchStats.fixture_id.in_(fixture_ids))
        .where(TeamMatchStats.team_id != team_id)
    )
    results = session.exec(opponent_stats_stmt).all()
    
    if not results:
        return 0.0
        
    total_conceded = sum(r.corner_kicks or 0 for r in results)
    return total_conceded / len(results)


def get_team_shots_avg(team_id: int, last_n_games: int, session: Session) -> dict:
    """
    Calculate average total shots and shots on goal.
    """
    statement = (
        select(TeamMatchStats)
        .where(TeamMatchStats.team_id == team_id)
        .order_by(TeamMatchStats.fixture_id.desc())
        .limit(last_n_games)
    )
    results = session.exec(statement).all()
    
    if not results:
        return {"total": 0.0, "on_goal": 0.0}
    
    total_shots = sum(r.total_shots or 0 for r in results)
    total_on_goal = sum(r.shots_on_goal or 0 for r in results)
    
    return {
        "total": total_shots / len(results),
        "on_goal": total_on_goal / len(results)
    }


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
