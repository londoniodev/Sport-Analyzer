"""
Football Team Stats - Statistics calculations for football teams.
"""
from sqlmodel import Session, select
from sqlalchemy import func
from app.sports.football.models import TeamMatchStats, Fixture, PlayerMatchStats


def get_team_squad_rating(team_id: int, last_n_games: int, session: Session) -> float:
    """
    Calculates the 'Squad Rating' (Calidad de Plantilla) for a team based on the average 
    match ratings of their core players in the last N games.
    """
    # 1. Get the last N fixture IDs for this team
    fixture_stmt = (
        select(Fixture.id)
        .where((Fixture.home_team_id == team_id) | (Fixture.away_team_id == team_id))
        .where(Fixture.home_score != None) # Only completed matches
        .order_by(Fixture.date.desc())
        .limit(last_n_games)
    )
    fixture_ids = session.exec(fixture_stmt).all()
    
    if not fixture_ids:
        return 6.5 # Default average football rating if no data
        
    # 2. Get player stats for this team in those fixtures
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
        .limit(14) # Top 14 most used players (Starting XI + 3 frequent subs)
    )
    results = session.exec(player_stmt).all()
    
    if not results:
        return 6.5
        
    # 3. Average the ratings of these core players
    total_rating = sum(float(r.avg_rating) for r in results)
    return total_rating / len(results)


def get_team_elo_rating(team_id: int, session: Session) -> float:
    """
    Returns the team's Elo rating. Defaults to 1500 if not found.
    """
    from app.sports.football.models import Team
    team = session.exec(select(Team).where(Team.id == team_id)).first()
    if team and team.elo_rating is not None:
        return team.elo_rating
    return 1500.0


def get_h2h_modifier(home_team_id: int, away_team_id: int, session: Session, max_adjustment: float = 0.15) -> float:
    """
    Calculates a Head-to-Head (H2H) multiplier based on historical matchups.
    If home_team historically dominates away_team, returns a value > 1.0 (e.g., 1.15).
    If away_team dominates, returns a value < 1.0 (e.g., 0.85).
    Returns exactly 1.0 if there is no history or history is perfectly even.
    """
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
    if total_matches == 0:
        return 1.0
        
    home_points = 0.0
    for match in history:
        # Determine who won
        if match.home_team_id == home_team_id:
            if match.home_score > match.away_score: home_points += 1.0
            elif match.home_score == match.away_score: home_points += 0.5
        else:
            if match.away_score > match.home_score: home_points += 1.0
            elif match.away_score == match.home_score: home_points += 0.5
            
    # Win rate from home_team's perspective (0.0 to 1.0)
    win_rate = home_points / total_matches
    
    # Calculate base modifier: shift 0.5 to 0, multiply by double the max adjustment
    # If win_rate is 1.0 (100% wins), diff is +0.5 * 2 * max_adj = +max_adj
    # If win_rate is 0.0 (0% wins), diff is -0.5 * 2 * max_adj = -max_adj
    raw_adjustment = (win_rate - 0.5) * 2 * max_adjustment
    
    # Scale down effect if there are very few matches (confidence factor)
    # E.g., 1 match = 33% effect, 2 matches = 66% effect, >=3 matches = 100% effect
    confidence = min(1.0, total_matches / 3.0)
    
    final_modifier = 1.0 + (raw_adjustment * confidence)
    return final_modifier


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
# NUEVAS FUNCIONES PARA PREDICCIONES
# =============================================================================

def get_team_goals_avg(team_id: int, last_n_games: int, session: Session, use_weighted: bool = False, alpha: float = 0.1) -> float:
    """
    Calcula el promedio de goles anotados por el equipo en los últimos N partidos.
    Si use_weighted=True, usa Media Ponderada Exponencial (EWMA).
    """
    statement = (
        select(Fixture, TeamMatchStats)
        .join(TeamMatchStats, (TeamMatchStats.fixture_id == Fixture.id) & (TeamMatchStats.team_id == team_id))
        .where((Fixture.home_team_id == team_id) | (Fixture.away_team_id == team_id))
        .where(Fixture.home_score != None)
        .order_by(Fixture.date.desc())
        .limit(last_n_games)
    )
    results = session.exec(statement).all()
    
    if not results:
        return 0.0
    
    goals_list = []
    for f, stats in results:
        if stats and stats.expected_goals is not None:
            goals_list.append(stats.expected_goals)
        else:
            if f.home_team_id == team_id:
                goals_list.append(f.home_score or 0)
            else:
                goals_list.append(f.away_score or 0)
    
    if use_weighted:
        return calculate_dynamic_weighted_avg(goals_list, alpha)
    
    return sum(goals_list) / len(goals_list)


def get_team_goals_conceded_avg(team_id: int, last_n_games: int, session: Session, use_weighted: bool = False, alpha: float = 0.1) -> float:
    """
    Calcula el promedio de goles recibidos por el equipo en los últimos N partidos.
    Si use_weighted=True, usa Media Ponderada Exponencial (EWMA).
    """
    # Para los concedidos, buscamos las estadísticas del RIVAL
    statement = (
        select(Fixture, TeamMatchStats)
        .join(TeamMatchStats, (TeamMatchStats.fixture_id == Fixture.id) & (TeamMatchStats.team_id != team_id))
        .where((Fixture.home_team_id == team_id) | (Fixture.away_team_id == team_id))
        .where(Fixture.home_score != None)
        .order_by(Fixture.date.desc())
        .limit(last_n_games)
    )
    results = session.exec(statement).all()
    
    if not results:
        return 0.0
    
    conceded_list = []
    for f, stats in results:
        if stats and stats.expected_goals is not None:
            conceded_list.append(stats.expected_goals)
        else:
            if f.home_team_id == team_id:
                conceded_list.append(f.away_score or 0)
            else:
                conceded_list.append(f.home_score or 0)
    
    if use_weighted:
        return calculate_dynamic_weighted_avg(conceded_list, alpha)
    
    return sum(conceded_list) / len(conceded_list)


def get_team_btts_pct(team_id: int, last_n_games: int, session: Session) -> float:
    """
    Calcula el porcentaje de partidos donde AMBOS equipos marcaron.
    Retorna 0.0 a 1.0 (0% a 100%)
    Útil para: Mercado BTTS (Ambos Equipos Marcarán)
    """
    fixtures = (
        select(Fixture)
        .where((Fixture.home_team_id == team_id) | (Fixture.away_team_id == team_id))
        .where(Fixture.home_score != None)
        .order_by(Fixture.date.desc())
        .limit(last_n_games)
    )
    results = session.exec(fixtures).all()
    
    if not results:
        return 0.0
    
    btts_count = sum(
        1 for f in results 
        if (f.home_score or 0) > 0 and (f.away_score or 0) > 0
    )
    
    return btts_count / len(results)


def get_team_clean_sheet_pct(team_id: int, last_n_games: int, session: Session) -> float:
    """
    Calcula el porcentaje de partidos donde el equipo NO recibió gol.
    Retorna 0.0 a 1.0 (0% a 100%)
    Útil para: Victoria sin recibir gol, Clean Sheet
    """
    fixtures = (
        select(Fixture)
        .where((Fixture.home_team_id == team_id) | (Fixture.away_team_id == team_id))
        .where(Fixture.home_score != None)
        .order_by(Fixture.date.desc())
        .limit(last_n_games)
    )
    results = session.exec(fixtures).all()
    
    if not results:
        return 0.0
    
    clean_sheet_count = 0
    for f in results:
        if f.home_team_id == team_id:
            if (f.away_score or 0) == 0:
                clean_sheet_count += 1
        else:
            if (f.home_score or 0) == 0:
                clean_sheet_count += 1
    
    return clean_sheet_count / len(results)


def get_team_fouls_avg(team_id: int, last_n_games: int, session: Session) -> float:
    """
    Calcula el promedio de faltas cometidas por el equipo.
    Útil para: Mercado de Faltas
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
    
    total_fouls = sum(r.fouls or 0 for r in results)
    return total_fouls / len(results)


def get_team_over_under_pct(team_id: int, last_n_games: int, threshold: float, session: Session) -> dict:
    """
    Calcula el porcentaje de partidos Over/Under X goles totales.
    
    Args:
        threshold: Línea de goles (ej: 2.5, 1.5, 3.5)
        
    Returns:
        {"over_pct": float, "under_pct": float}
    
    Útil para: Mercado Over/Under
    """
    fixtures = (
        select(Fixture)
        .where((Fixture.home_team_id == team_id) | (Fixture.away_team_id == team_id))
        .where(Fixture.home_score != None)
        .order_by(Fixture.date.desc())
        .limit(last_n_games)
    )
    results = session.exec(fixtures).all()
    
    if not results:
        return {"over_pct": 0.0, "under_pct": 0.0}
    
    over_count = sum(
        1 for f in results 
        if ((f.home_score or 0) + (f.away_score or 0)) > threshold
    )
    
    over_pct = over_count / len(results)
    return {
        "over_pct": over_pct,
        "under_pct": 1.0 - over_pct
    }


def get_team_stats_summary(team_id: int, last_n_games: int, session: Session) -> dict:
    """
    Returns a unified summary of team statistics for the prediction UI.
    """
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

