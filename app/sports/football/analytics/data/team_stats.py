"""
Football Team Stats - Statistics calculations for football teams.
"""
from typing import List
from sqlmodel import Session, select
from sqlalchemy import func
from app.sports.football.models import TeamMatchStats, Fixture, PlayerMatchStats, Team


# =============================================================================
# HELPER FUNCTIONS (DATABASE QUERIES)
# =============================================================================

def _get_team_match_stats(team_id: int, last_n_games: int, session: Session) -> List[TeamMatchStats]:
    """Returns the TeamMatchStats for the given team in their last N games."""
    statement = (
        select(TeamMatchStats)
        .where(TeamMatchStats.team_id == team_id)
        .order_by(TeamMatchStats.fixture_id.desc())
        .limit(last_n_games)
    )
    return session.exec(statement).all()

def _get_opponent_match_stats(team_id: int, last_n_games: int, session: Session) -> List[TeamMatchStats]:
    """Returns the TeamMatchStats of the OPPONENT in the given team's last N games."""
    fixture_stmt = (
        select(Fixture.id)
        .where((Fixture.home_team_id == team_id) | (Fixture.away_team_id == team_id))
        .where(Fixture.home_score != None)
        .order_by(Fixture.date.desc())
        .limit(last_n_games)
    )
    fixture_ids = session.exec(fixture_stmt).all()
    
    if not fixture_ids:
        return []
        
    opponent_stats_stmt = (
        select(TeamMatchStats)
        .where(TeamMatchStats.fixture_id.in_(fixture_ids))
        .where(TeamMatchStats.team_id != team_id)
    )
    return session.exec(opponent_stats_stmt).all()

def _get_team_fixtures(team_id: int, last_n_games: int, session: Session) -> List[Fixture]:
    """Returns the completed Fixture models for the given team in their last N games."""
    statement = (
        select(Fixture)
        .where((Fixture.home_team_id == team_id) | (Fixture.away_team_id == team_id))
        .where(Fixture.home_score != None)
        .order_by(Fixture.date.desc())
        .limit(last_n_games)
    )
    return session.exec(statement).all()

def calculate_dynamic_weighted_avg(values: list, alpha: float = 0.1) -> float:
    """
    Calcula una media ponderada exponencialmente (EWMA).
    El valor en el índice 0 (más reciente) tiene peso 1.0.
    Cada valor posterior i tiene peso (1-alpha)^i.
    """
    if not values:
        return 0.0
    
    total_weighted_sum = 0.0
    total_weights = 0.0
    
    for i, val in enumerate(values):
        weight = (1 - alpha) ** i
        total_weighted_sum += val * weight
        total_weights += weight
        
    return total_weighted_sum / total_weights if total_weights > 0 else 0.0


# =============================================================================
# STATS CALCULATORS
# =============================================================================

def get_team_squad_rating(team_id: int, last_n_games: int, session: Session) -> float:
    """Calculates the 'Squad Rating' based on average player ratings."""
    fixtures = _get_team_fixtures(team_id, last_n_games, session)
    if not fixtures: return 6.5
    
    fixture_ids = [f.id for f in fixtures]
    
    player_stmt = (
        select(
            PlayerMatchStats.player_id, 
            func.sum(PlayerMatchStats.minutes_played).label('total_minutes'),
            func.avg(PlayerMatchStats.rating).label('avg_rating')
        )
        .where(PlayerMatchStats.fixture_id.in_(fixture_ids))
        .where(PlayerMatchStats.team_id == team_id)
        .where(PlayerMatchStats.rating != None)
        .group_by(PlayerMatchStats.player_id)
        .order_by(func.sum(PlayerMatchStats.minutes_played).desc())
        .limit(14) # Top 14 most used players
    )
    results = session.exec(player_stmt).all()
    
    if not results: return 6.5
    return sum(float(r.avg_rating) for r in results) / len(results)

def get_team_elo_rating(team_id: int, session: Session) -> float:
    """Returns the team's Elo rating. Defaults to 1500 if not found."""
    team = session.exec(select(Team).where(Team.id == team_id)).first()
    if team and team.elo_rating is not None:
        return team.elo_rating
    return 1500.0

def get_h2h_modifier(home_team_id: int, away_team_id: int, session: Session, max_adjustment: float = 0.15) -> float:
    """Calculates a Head-to-Head (H2H) multiplier based on historical matchups."""
    statement = (
        select(Fixture)
        .where(
            ((Fixture.home_team_id == home_team_id) & (Fixture.away_team_id == away_team_id)) |
            ((Fixture.home_team_id == away_team_id) & (Fixture.away_team_id == home_team_id))
        )
        .where(Fixture.home_score != None)
    )
    history = session.exec(statement).all()
    
    total_matches = len(history)
    if total_matches == 0: return 1.0
        
    home_points = 0.0
    for match in history:
        if match.home_team_id == home_team_id:
            if match.home_score > match.away_score: home_points += 1.0
            elif match.home_score == match.away_score: home_points += 0.5
        else:
            if match.away_score > match.home_score: home_points += 1.0
            elif match.away_score == match.home_score: home_points += 0.5
            
    win_rate = home_points / total_matches
    raw_adjustment = (win_rate - 0.5) * 2 * max_adjustment
    confidence = min(1.0, total_matches / 3.0)
    
    return 1.0 + (raw_adjustment * confidence)

def get_team_corners_avg(team_id: int, last_n_games: int, session: Session) -> float:
    results = _get_team_match_stats(team_id, last_n_games, session)
    if not results: return 0.0
    return sum(r.corner_kicks or 0 for r in results) / len(results)

def get_team_corners_conceded_avg(team_id: int, last_n_games: int, session: Session) -> float:
    results = _get_opponent_match_stats(team_id, last_n_games, session)
    if not results: return 0.0
    return sum(r.corner_kicks or 0 for r in results) / len(results)

def get_team_shots_avg(team_id: int, last_n_games: int, session: Session) -> dict:
    results = _get_team_match_stats(team_id, last_n_games, session)
    if not results: return {"total": 0.0, "on_goal": 0.0}
    return {
        "total": sum(r.total_shots or 0 for r in results) / len(results),
        "on_goal": sum(r.shots_on_goal or 0 for r in results) / len(results)
    }

def get_team_possession_avg(team_id: int, last_n_games: int, session: Session) -> float:
    results = _get_team_match_stats(team_id, last_n_games, session)
    if not results: return 0.0
    return sum(r.possession or 0 for r in results) / len(results)

def get_team_cards_avg(team_id: int, last_n_games: int, session: Session) -> dict:
    results = _get_team_match_stats(team_id, last_n_games, session)
    if not results: return {"yellow": 0.0, "red": 0.0}
    return {
        "yellow": sum(r.yellow_cards or 0 for r in results) / len(results),
        "red": sum(r.red_cards or 0 for r in results) / len(results)
    }

def get_team_fouls_avg(team_id: int, last_n_games: int, session: Session) -> float:
    results = _get_team_match_stats(team_id, last_n_games, session)
    if not results: return 0.0
    return sum(r.fouls or 0 for r in results) / len(results)

def get_team_btts_pct(team_id: int, last_n_games: int, session: Session) -> float:
    results = _get_team_fixtures(team_id, last_n_games, session)
    if not results: return 0.0
    btts_count = sum(1 for f in results if (f.home_score or 0) > 0 and (f.away_score or 0) > 0)
    return btts_count / len(results)

def get_team_clean_sheet_pct(team_id: int, last_n_games: int, session: Session) -> float:
    results = _get_team_fixtures(team_id, last_n_games, session)
    if not results: return 0.0
    clean_sheet_count = sum(1 for f in results if (f.home_team_id == team_id and (f.away_score or 0) == 0) or (f.away_team_id == team_id and (f.home_score or 0) == 0))
    return clean_sheet_count / len(results)

def get_team_over_under_pct(team_id: int, last_n_games: int, threshold: float, session: Session) -> dict:
    results = _get_team_fixtures(team_id, last_n_games, session)
    if not results: return {"over_pct": 0.0, "under_pct": 0.0}
    over_count = sum(1 for f in results if ((f.home_score or 0) + (f.away_score or 0)) > threshold)
    over_pct = over_count / len(results)
    return {"over_pct": over_pct, "under_pct": 1.0 - over_pct}

def get_team_goals_avg(team_id: int, last_n_games: int, session: Session, use_weighted: bool = False, alpha: float = 0.1) -> float:
    """Calculates average goals scored by the team."""
    statement = (
        select(Fixture, TeamMatchStats)
        .join(TeamMatchStats, (TeamMatchStats.fixture_id == Fixture.id) & (TeamMatchStats.team_id == team_id))
        .where((Fixture.home_team_id == team_id) | (Fixture.away_team_id == team_id))
        .where(Fixture.home_score != None)
        .order_by(Fixture.date.desc())
        .limit(last_n_games)
    )
    results = session.exec(statement).all()
    
    if not results: return 0.0
    
    goals_list = []
    for f, stats in results:
        if stats and stats.expected_goals is not None:
            goals_list.append(stats.expected_goals)
        else:
            goals_list.append(f.home_score if f.home_team_id == team_id else f.away_score)
            
    if use_weighted:
        return calculate_dynamic_weighted_avg(goals_list, alpha)
    return sum(goals_list) / len(goals_list)

def get_team_goals_conceded_avg(team_id: int, last_n_games: int, session: Session, use_weighted: bool = False, alpha: float = 0.1) -> float:
    """Calculates average goals conceded by the team (fetching opponent's stats)."""
    statement = (
        select(Fixture, TeamMatchStats)
        .join(TeamMatchStats, (TeamMatchStats.fixture_id == Fixture.id) & (TeamMatchStats.team_id != team_id))
        .where((Fixture.home_team_id == team_id) | (Fixture.away_team_id == team_id))
        .where(Fixture.home_score != None)
        .order_by(Fixture.date.desc())
        .limit(last_n_games)
    )
    results = session.exec(statement).all()
    
    if not results: return 0.0
    
    conceded_list = []
    for f, stats in results:
        if stats and stats.expected_goals is not None:
            conceded_list.append(stats.expected_goals)
        else:
            conceded_list.append(f.away_score if f.home_team_id == team_id else f.home_score)
            
    if use_weighted:
        return calculate_dynamic_weighted_avg(conceded_list, alpha)
    return sum(conceded_list) / len(conceded_list)

def get_team_stats_summary(team_id: int, last_n_games: int, session: Session) -> dict:
    corners_avg = get_team_corners_avg(team_id, last_n_games, session)
    corners_conceded_avg = get_team_corners_conceded_avg(team_id, last_n_games, session)
    possession_avg = get_team_possession_avg(team_id, last_n_games, session)
    cards = get_team_cards_avg(team_id, last_n_games, session)
    shots = get_team_shots_avg(team_id, last_n_games, session)
    goals_scored_avg = get_team_goals_avg(team_id, last_n_games, session)
    goals_conceded_avg = get_team_goals_conceded_avg(team_id, last_n_games, session)

    return {
        "goals_scored_avg": goals_scored_avg,
        "goals_conceded_avg": goals_conceded_avg,
        "corners_avg": corners_avg,
        "corners_conceded_avg": corners_conceded_avg,
        "possession_avg": possession_avg,
        "cards_yellow_avg": cards["yellow"],
        "cards_total_avg": cards["yellow"] + cards["red"],
        "shots_avg": shots["total"],
        "shots_on_goal_avg": shots["on_goal"]
    }
