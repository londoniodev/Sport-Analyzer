"""
Football Impact Engine - Calculate player impact on team metrics.
"""
from sqlmodel import Session, select
from app.sports.football.models import TeamMatchStats, PlayerMatchStats


def get_team_corners_with_player(team_id: int, player_id: int, session: Session) -> float:
    """
    Calculate the average corners for a team when a specific player plays (45+ mins).
    """
    # Find fixtures where the player played more than 45 minutes
    player_fixtures_stmt = select(PlayerMatchStats.fixture_id).where(
        PlayerMatchStats.player_id == player_id,
        PlayerMatchStats.team_id == team_id,
        PlayerMatchStats.minutes_played > 45
    )
    player_fixtures_ids = session.exec(player_fixtures_stmt).all()

    if not player_fixtures_ids:
        return 0.0

    # Calculate average corners in those fixtures
    corners_stmt = select(TeamMatchStats).where(
        TeamMatchStats.team_id == team_id,
        TeamMatchStats.fixture_id.in_(player_fixtures_ids)
    )
    results = session.exec(corners_stmt).all()

    if not results:
        return 0.0

    total_corners = sum(r.corner_kicks or 0 for r in results)
    return total_corners / len(results)


def get_team_goals_with_player(team_id: int, player_id: int, session: Session) -> float:
    """
    Calculate the average team goals when a specific player plays.
    """
    # This would require accessing Fixture scores, which we'd need to join
    # For now, return a placeholder
    return 0.0


def get_player_impact_score(player_id: int, team_id: int, session: Session) -> dict:
    """
    Calculate a player's overall impact score based on various metrics.
    Returns a dict with impact scores for different categories.
    """
    corners_impact = get_team_corners_with_player(team_id, player_id, session)
    
    return {
        "corners_impact": corners_impact,
        "goals_impact": 0.0,  # TODO: Implement
        "overall_impact": corners_impact  # Simplified for now
    }
