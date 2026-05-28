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
    fixtures = (
        select(Fixture)
        .where((Fixture.home_team_id == team_id) | (Fixture.away_team_id == team_id))
        .where(Fixture.home_score != None)  # Solo partidos jugados
        .order_by(Fixture.date.desc())
        .limit(last_n_games)
    )
    results = session.exec(fixtures).all()
    
    if not results:
        return 0.0
    
    goals_list = []
    for f in results:
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
    
    conceded_list = []
    for f in results:
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

