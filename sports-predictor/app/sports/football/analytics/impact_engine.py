"""
Football Impact Engine - Calculate player impact on team metrics.

Uses xGC (Expected Goal Contributions) methodology based on academic research:
- xGC = xG + xA (Expected Goals + Expected Assists)
- Player Contribution = Player xGC / Team Total xGC
"""
from typing import Dict, List, Optional
from sqlmodel import Session, select, func
from app.sports.football.models import (
    TeamMatchStats, PlayerMatchStats, PlayerSeasonStats, Fixture, Player
)


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
    Calculate the average team goals when a specific player plays (45+ mins).
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

    # Get team's scores in those fixtures
    home_stmt = select(Fixture).where(
        Fixture.id.in_(player_fixtures_ids),
        Fixture.home_team_id == team_id
    )
    away_stmt = select(Fixture).where(
        Fixture.id.in_(player_fixtures_ids),
        Fixture.away_team_id == team_id
    )
    
    home_fixtures = session.exec(home_stmt).all()
    away_fixtures = session.exec(away_stmt).all()
    
    total_goals = sum(f.home_score or 0 for f in home_fixtures)
    total_goals += sum(f.away_score or 0 for f in away_fixtures)
    total_matches = len(home_fixtures) + len(away_fixtures)
    
    return total_goals / total_matches if total_matches > 0 else 0.0


def calculate_player_contribution(player_id: int, team_id: int, session: Session, season: int = 2026) -> Dict[str, float]:
    """
    Calculate a player's xGC (Expected Goal Contributions) and their percentage
    of the team's total offensive output.
    
    Uses PlayerSeasonStats (xG, xA) when available for more accurate calculations.
    Falls back to raw goals/assists from PlayerMatchStats if advanced stats unavailable.
    
    Based on academic research: xGC = xG + xA (Expected Goals + Expected Assists)
    
    Returns:
        {
            "goals": int,
            "assists": int,
            "xg": float (expected goals),
            "xa": float (expected assists),
            "xgc": float (xG + xA or goals + assists),
            "team_total_xgc": float,
            "contribution_pct": float (0.0 to 1.0),
            "data_source": str ("season_stats" or "match_stats")
        }
    """
    # Try to get advanced stats from PlayerSeasonStats first
    season_stats = session.get(PlayerSeasonStats, (player_id, team_id, season))
    
    if season_stats and (season_stats.xg is not None or season_stats.xa is not None):
        # Use advanced xG/xA stats
        player_xg = season_stats.xg or 0.0
        player_xa = season_stats.xa or 0.0
        player_xgc = season_stats.xgc or (player_xg + player_xa)
        player_goals = season_stats.goals or 0
        player_assists = season_stats.assists or 0
        data_source = "season_stats"
        
        # Get team totals from PlayerSeasonStats
        team_stats_stmt = select(
            func.sum(PlayerSeasonStats.xg),
            func.sum(PlayerSeasonStats.xa),
            func.sum(PlayerSeasonStats.xgc)
        ).where(
            PlayerSeasonStats.team_id == team_id,
            PlayerSeasonStats.season == season
        )
        team_result = session.exec(team_stats_stmt).first()
        
        team_total_xgc = team_result[2] or 0.0 if team_result else 0.0
        if team_total_xgc == 0.0 and team_result:
            team_total_xgc = (team_result[0] or 0.0) + (team_result[1] or 0.0)
    else:
        # Fallback to raw goals/assists from PlayerMatchStats
        player_stats_stmt = select(
            func.sum(PlayerMatchStats.goals),
            func.sum(PlayerMatchStats.assists)
        ).where(
            PlayerMatchStats.player_id == player_id,
            PlayerMatchStats.team_id == team_id
        )
        result = session.exec(player_stats_stmt).first()
        
        player_goals = result[0] or 0 if result else 0
        player_assists = result[1] or 0 if result else 0
        player_xg = float(player_goals)  # Approximate xG with actual goals
        player_xa = float(player_assists)
        player_xgc = player_goals + player_assists
        data_source = "match_stats"
        
        # Get team totals from PlayerMatchStats
        team_stats_stmt = select(
            func.sum(PlayerMatchStats.goals),
            func.sum(PlayerMatchStats.assists)
        ).where(
            PlayerMatchStats.team_id == team_id
        )
        team_result = session.exec(team_stats_stmt).first()
        
        team_total_goals = team_result[0] or 0 if team_result else 0
        team_total_assists = team_result[1] or 0 if team_result else 0
        team_total_xgc = team_total_goals + team_total_assists
    
    contribution_pct = player_xgc / team_total_xgc if team_total_xgc > 0 else 0.0
    
    return {
        "goals": player_goals,
        "assists": player_assists,
        "xg": player_xg,
        "xa": player_xa,
        "xgc": player_xgc,
        "team_total_xgc": team_total_xgc,
        "contribution_pct": contribution_pct,
        "data_source": data_source
    }


def adjust_xg_for_lineup(
    team_id: int,
    base_xg: float,
    missing_player_ids: List[int],
    session: Session,
    importance_factor: float = 1.0
) -> float:
    """
    Adjust a team's expected goals based on which key players are missing.
    
    Formula: xG_adjusted = xG_base × (1 - sum(Player_Contribution × Importance_Factor))
    
    Args:
        team_id: The team's ID
        base_xg: The team's baseline expected goals
        missing_player_ids: List of player IDs who are NOT playing
        importance_factor: Multiplier for player importance (1.0 = full impact, 0.5 = rotation)
    
    Returns:
        Adjusted xG value
    """
    total_missing_contribution = 0.0
    
    for player_id in missing_player_ids:
        contribution = calculate_player_contribution(player_id, team_id, session)
        total_missing_contribution += contribution["contribution_pct"]
    
    # Cap the reduction at 50% (even without all key players, team can still score)
    max_reduction = 0.5
    reduction = min(total_missing_contribution * importance_factor, max_reduction)
    
    adjusted_xg = base_xg * (1 - reduction)
    return adjusted_xg


def get_top_contributors(team_id: int, session: Session, season: int = 2026, limit: int = 5) -> List[Dict]:
    """
    Get the top goal contributors for a team.
    
    Uses PlayerSeasonStats (xG, xA) when available, falls back to PlayerMatchStats.
    Returns list of players sorted by xGC.
    """
    # First try to get from PlayerSeasonStats (more accurate)
    season_stmt = select(PlayerSeasonStats).where(
        PlayerSeasonStats.team_id == team_id,
        PlayerSeasonStats.season == season
    ).order_by(
        PlayerSeasonStats.xgc.desc()
    ).limit(limit)
    
    season_results = session.exec(season_stmt).all()
    
    if season_results:
        # Use season stats
        contributors = []
        for stats in season_results:
            player = session.get(Player, stats.player_id)
            contributors.append({
                "player_id": stats.player_id,
                "name": player.name if player else "Unknown",
                "position": player.position if player else None,
                "goals": stats.goals or 0,
                "assists": stats.assists or 0,
                "xg": stats.xg or 0.0,
                "xa": stats.xa or 0.0,
                "xgc": stats.xgc or ((stats.xg or 0) + (stats.xa or 0)),
                "data_source": "season_stats"
            })
        return contributors
    
    # Fallback to PlayerMatchStats
    match_stmt = select(
        PlayerMatchStats.player_id,
        func.sum(PlayerMatchStats.goals).label("total_goals"),
        func.sum(PlayerMatchStats.assists).label("total_assists")
    ).where(
        PlayerMatchStats.team_id == team_id
    ).group_by(
        PlayerMatchStats.player_id
    ).order_by(
        (func.sum(PlayerMatchStats.goals) + func.sum(PlayerMatchStats.assists)).desc()
    ).limit(limit)
    
    results = session.exec(match_stmt).all()
    
    contributors = []
    for player_id, goals, assists in results:
        player = session.get(Player, player_id)
        xgc = (goals or 0) + (assists or 0)
        
        contributors.append({
            "player_id": player_id,
            "name": player.name if player else "Unknown",
            "position": player.position if player else None,
            "goals": goals or 0,
            "assists": assists or 0,
            "xg": float(goals or 0),
            "xa": float(assists or 0),
            "xgc": xgc,
            "data_source": "match_stats"
        })
    
    return contributors


def get_player_impact_score(player_id: int, team_id: int, session: Session, season: int = 2026) -> dict:
    """
    Calculate a player's overall impact score based on various metrics.
    Returns a dict with impact scores for different categories.
    """
    corners_impact = get_team_corners_with_player(team_id, player_id, session)
    goals_impact = get_team_goals_with_player(team_id, player_id, session)
    contribution = calculate_player_contribution(player_id, team_id, session, season)
    
    return {
        "corners_impact": corners_impact,
        "goals_impact": goals_impact,
        "xg": contribution["xg"],
        "xa": contribution["xa"],
        "xgc": contribution["xgc"],
        "contribution_pct": contribution["contribution_pct"],
        "data_source": contribution["data_source"],
        "overall_impact": contribution["contribution_pct"]
    }
