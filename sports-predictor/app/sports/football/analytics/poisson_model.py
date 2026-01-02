"""
Poisson Model - Predictor de goles basado en distribución Poisson.

La distribución de Poisson es ideal para modelar eventos discretos (goles) 
que ocurren con una tasa promedio conocida (xG / promedio de goles).

Fórmula: P(k) = (λ^k * e^(-λ)) / k!
Donde:
- λ = tasa esperada de goles (xG o promedio histórico)
- k = número de goles a calcular
- e ≈ 2.71828
"""
from typing import Dict, List, Tuple
from math import exp, factorial
from sqlmodel import Session
from app.sports.football.analytics.team_stats import (
    get_team_goals_avg,
    get_team_goals_conceded_avg
)


def poisson_probability(lambda_val: float, k: int) -> float:
    """
    Calcula la probabilidad de exactamente k eventos dado un lambda.
    P(X = k) = (λ^k * e^(-λ)) / k!
    """
    if lambda_val <= 0:
        return 1.0 if k == 0 else 0.0
    return (lambda_val ** k) * exp(-lambda_val) / factorial(k)


def calculate_dixon_coles_tau(home_goals: int, away_goals: int, home_xg: float, away_xg: float, rho: float = 0.1) -> float:
    """
    Función de ajuste Dixon-Coles para corregir subestimación de empates y marcadores bajos.
    """
    if rho == 0:
        return 1.0
        
    if home_goals == 0 and away_goals == 0:
        return 1 - (home_xg * away_xg * rho)
    elif home_goals == 1 and away_goals == 0:
        return 1 + (away_xg * rho)
    elif home_goals == 0 and away_goals == 1:
        return 1 + (home_xg * rho)
    elif home_goals == 1 and away_goals == 1:
        return 1 - rho
    else:
        return 1.0


def calculate_expected_goals(
    home_team_id: int,
    away_team_id: int,
    session: Session,
    last_n_games: int = 20,
    home_advantage: float = 1.1,
    use_weighted: bool = True  # Activado por defecto para el modo Dinámico
) -> Tuple[float, float]:
    """
    Calcula los goles esperados para cada equipo usando EWMA (Media Ponderada Exponencial).
    """
    # Estadísticas ofensivas ponderadas
    home_attack = get_team_goals_avg(home_team_id, last_n_games, session, use_weighted=use_weighted)
    away_attack = get_team_goals_avg(away_team_id, last_n_games, session, use_weighted=use_weighted)
    
    # Estadísticas defensivas ponderadas
    home_defense = get_team_goals_conceded_avg(home_team_id, last_n_games, session, use_weighted=use_weighted)
    away_defense = get_team_goals_conceded_avg(away_team_id, last_n_games, session, use_weighted=use_weighted)
    
    # xG dinámico
    home_xg = ((home_attack + away_defense) / 2) * home_advantage
    away_xg = (away_attack + home_defense) / 2
    
    return home_xg, away_xg


def predict_match_probabilities(
    home_xg: float,
    away_xg: float,
    max_goals: int = 6,
    rho: float = 0.1  # Parámetro de dependencia para Dixon-Coles
) -> Dict[str, float]:
    """
    Calcula probabilidades usando Poisson con ajuste Dixon-Coles.
    """
    home_win = 0.0
    draw = 0.0
    away_win = 0.0
    btts_yes = 0.0
    
    for home_goals in range(max_goals + 1):
        for away_goals in range(max_goals + 1):
            prob_home = poisson_probability(home_xg, home_goals)
            prob_away = poisson_probability(away_xg, away_goals)
            
            # Aplicar ajuste dinámico Dixon-Coles
            tau = calculate_dixon_coles_tau(home_goals, away_goals, home_xg, away_xg, rho)
            joint_prob = prob_home * prob_away * tau
            
            if home_goals > away_goals:
                home_win += joint_prob
            elif home_goals < away_goals:
                away_win += joint_prob
            else:
                draw += joint_prob
            
            if home_goals > 0 and away_goals > 0:
                btts_yes += joint_prob
    
    # Normalizar (Dixon-Coles puede alterar ligeramente la suma total)
    total = home_win + draw + away_win
    if total > 0:
        home_win /= total
        draw /= total
        away_win /= total
        
    return {
        "home_win": round(home_win, 4),
        "draw": round(draw, 4),
        "away_win": round(away_win, 4),
        "btts_yes": round(btts_yes, 4),
        "btts_no": round(1 - btts_yes, 4)
    }


def predict_over_under(
    home_xg: float,
    away_xg: float,
    thresholds: List[float] = [0.5, 1.5, 2.5, 3.5, 4.5],
    max_goals: int = 8,
    rho: float = 0.1
) -> Dict[str, Dict[str, float]]:
    """
    Calcula Over/Under con ajuste Dixon-Coles.
    """
    results = {}
    
    for threshold in thresholds:
        over_prob = 0.0
        total_prob = 0.0
        
        for home_goals in range(max_goals + 1):
            for away_goals in range(max_goals + 1):
                tau = calculate_dixon_coles_tau(home_goals, away_goals, home_xg, away_xg, rho)
                prob = poisson_probability(home_xg, home_goals) * poisson_probability(away_xg, away_goals) * tau
                
                total_prob += prob
                if (home_goals + away_goals) > threshold:
                    over_prob += prob
        
        # Normalización
        if total_prob > 0:
            over_prob /= total_prob
            
        results[str(threshold)] = {
            "over": round(over_prob, 4),
            "under": round(1 - over_prob, 4)
        }
    
    return results


def predict_correct_score(
    home_xg: float,
    away_xg: float,
    max_goals: int = 5,
    rho: float = 0.1
) -> Dict[str, float]:
    """
    Calcula Resultado Correcto con ajuste Dixon-Coles.
    """
    results = {}
    total_prob = 0.0
    
    for home_goals in range(max_goals + 1):
        for away_goals in range(max_goals + 1):
            tau = calculate_dixon_coles_tau(home_goals, away_goals, home_xg, away_xg, rho)
            prob = poisson_probability(home_xg, home_goals) * poisson_probability(away_xg, away_goals) * tau
            total_prob += prob
            score = f"{home_goals}-{away_goals}"
            results[score] = prob
            
    # Normalización y redondeo
    if total_prob > 0:
        results = {k: round(v/total_prob, 4) for k, v in results.items()}
    
    return dict(sorted(results.items(), key=lambda x: x[1], reverse=True))


def get_full_match_prediction(
    home_team_id: int,
    away_team_id: int,
    session: Session,
    last_n_games: int = 20,
    use_weighted: bool = True
) -> Dict:
    """
    Genera predicción completa usando el modelo dinámico ajustado.
    """
    home_xg, away_xg = calculate_expected_goals(
        home_team_id, away_team_id, session, last_n_games, use_weighted=use_weighted
    )
    
    match_probs = predict_match_probabilities(home_xg, away_xg)
    over_under = predict_over_under(home_xg, away_xg)
    correct_score = predict_correct_score(home_xg, away_xg)
    
    return {
        "expected_goals": {
            "home": round(home_xg, 2),
            "away": round(away_xg, 2),
            "total": round(home_xg + away_xg, 2)
        },
        "1x2": {
            "home_win": match_probs["home_win"],
            "draw": match_probs["draw"],
            "away_win": match_probs["away_win"]
        },
        "btts": {
            "yes": match_probs["btts_yes"],
            "no": match_probs["btts_no"]
        },
        "over_under": over_under,
        "correct_score_top5": dict(list(correct_score.items())[:5])
    }
