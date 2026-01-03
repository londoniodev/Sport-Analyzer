"""
Goals Predictor - Predicciones de goles y resultados usando el motor Poisson.
"""
from typing import Dict, List, Tuple
from sqlmodel import Session
from app.sports.football.analytics.models.poisson import PoissonEngine
from app.sports.football.analytics.data.team_stats import (
    get_team_goals_avg,
    get_team_goals_conceded_avg
)

def calculate_expected_goals(
    home_team_id: int,
    away_team_id: int,
    session: Session,
    last_n_games: int = 20,
    home_advantage: float = 1.1,
    use_weighted: bool = True
) -> Tuple[float, float]:
    """Calcula los goles esperados (xG) para los dos equipos."""
    home_attack = get_team_goals_avg(home_team_id, last_n_games, session, use_weighted=use_weighted)
    away_attack = get_team_goals_avg(away_team_id, last_n_games, session, use_weighted=use_weighted)
    home_defense = get_team_goals_conceded_avg(home_team_id, last_n_games, session, use_weighted=use_weighted)
    away_defense = get_team_goals_conceded_avg(away_team_id, last_n_games, session, use_weighted=use_weighted)
    
    home_xg = ((home_attack + away_defense) / 2) * home_advantage
    away_xg = (away_attack + home_defense) / 2
    return home_xg, away_xg

def predict_goals_markets(home_xg: float, away_xg: float, max_goals: int = 6, rho: float = 0.1) -> Dict:
    """Predice mercados principales de goles (1X2, Over/Under, BTTS)."""
    home_win = 0.0
    draw = 0.0
    away_win = 0.0
    btts_yes = 0.0
    correct_scores = {}
    
    for h in range(max_goals + 1):
        for a in range(max_goals + 1):
            prob = PoissonEngine.get_joint_probability(home_xg, h, away_xg, a, rho)
            
            if h > a: home_win += prob
            elif h < a: away_win += prob
            else: draw += prob
            
            if h > 0 and a > 0: btts_yes += prob
            
            # Resultado correcto top scorelines
            correct_scores[f"{h}-{a}"] = prob

    total = home_win + draw + away_win
    if total > 0:
        home_win /= total; draw /= total; away_win /= total

    ou_thresholds = [0.5, 1.5, 2.5, 3.5, 4.5]
    over_under = {}
    for t in ou_thresholds:
        o_prob = 0.0
        for h in range(max_goals + 1):
            for a in range(max_goals + 1):
                if (h + a) > t:
                    o_prob += PoissonEngine.get_joint_probability(home_xg, h, away_xg, a, rho)
        over_under[str(t)] = {"over": round(o_prob/total, 4) if total > 0 else 0, "under": round(1 - o_prob/total, 4) if total > 0 else 1}

    return {
        "1x2": {"home": round(home_win, 4), "draw": round(draw, 4), "away": round(away_win, 4)},
        "btts": {"yes": round(btts_yes/total, 4) if total > 0 else 0, "no": round(1 - btts_yes/total, 4) if total > 0 else 1},
        "over_under": over_under,
        "correct_score": dict(sorted(correct_scores.items(), key=lambda x: x[1], reverse=True)[:5])
    }

def predict_halftime_markets(home_xg: float, away_xg: float, rho: float = 0.1) -> Dict:
    """Predice mercados de 1ª Mitad (asumiendo ~45% del xG total)."""
    # Factor de ajuste para primera mitad (promedio histórico ~45% de goles)
    HT_FACTOR = 0.45
    ht_home_xg = home_xg * HT_FACTOR
    ht_away_xg = away_xg * HT_FACTOR
    
    # Calculamos 1x2 y Goles usando el motor normal pero con xG reducido
    preds = predict_goals_markets(ht_home_xg, ht_away_xg, max_goals=4, rho=rho)
    
    return {
        "1x2": preds["1x2"],
        "btts": preds["btts"],
        "over_under": {
            "0.5": preds["over_under"]["0.5"],
            "1.5": preds["over_under"]["1.5"]
        },
        "correct_score_top3": dict(list(preds["correct_score"].items())[:3])
    }

def predict_handicap_markets(home_xg: float, away_xg: float, max_goals: int = 8) -> Dict:
    """Predice Hándicaps Asiáticos y Europeos (3-Way)."""
    # Aproximación usando diferencias de Poisson
    handicaps = {}
    lines = [-1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5]
    
    import math
    from scipy.stats import skellam # Usaremos skellam si estuviéramos importando, 
    # pero para mantenerlo simple sin dependencias extra, usamos simulación de matriz
    
    # Matriz de probabilidad
    probs = {}
    for h in range(max_goals + 1):
        for a in range(max_goals + 1):
            p = PoissonEngine.get_joint_probability(home_xg, h, away_xg, a)
            diff = h - a
            probs[diff] = probs.get(diff, 0.0) + p

    # Asian Handicap
    for line in lines:
        win = 0.0
        push = 0.0
        loss = 0.0
        
        for diff, prob in probs.items():
            if diff + line > 0: win += prob
            elif diff + line == 0: push += prob
            else: loss += prob
            
        handicaps[str(line)] = {"win": round(win, 4), "push": round(push, 4), "loss": round(loss, 4)}
        
    return handicaps


def predict_corners_markets(home_corners_avg: float, away_corners_avg: float) -> Dict:
    """Predice mercados de corners usando Poisson simple."""
    total_expected = home_corners_avg + away_corners_avg
    
    # Over/Under para corners
    thresholds = [4.5, 5.5, 6.5, 7.5, 8.5, 9.5, 10.5, 11.5]
    over_under = {}
    
    for t in thresholds:
        over_prob = 1 - PoissonEngine.get_cumulative_probability(total_expected, int(t))
        over_under[str(t)] = {"over": round(over_prob, 4), "under": round(1 - over_prob, 4)}
    
    # Quién tendrá más corners (1X2)
    home_prob = 0.0
    draw_prob = 0.0
    away_prob = 0.0
    
    for h in range(15):
        for a in range(15):
            p_h = PoissonEngine.get_probability(home_corners_avg, h)
            p_a = PoissonEngine.get_probability(away_corners_avg, a)
            joint = p_h * p_a
            if h > a:
                home_prob += joint
            elif h < a:
                away_prob += joint
            else:
                draw_prob += joint
    
    # Over/Under por equipo
    ou_home = {}
    ou_away = {}
    for t in thresholds_total:
         # Ajustar threshold para equipo (aprox mitad del total o rangos típicos de equipo)
         # Usaremos rangos fijos típicos para equipos: 1.5 a 8.5
         pass

    team_thresholds = [2.5, 3.5, 4.5, 5.5, 6.5, 7.5]
    for t in team_thresholds:
        p_home = 1 - PoissonEngine.get_cumulative_probability(home_corners_avg, int(t))
        ou_home[str(t)] = {"over": round(p_home, 4), "under": round(1 - p_home, 4)}
        
        p_away = 1 - PoissonEngine.get_cumulative_probability(away_corners_avg, int(t))
        ou_away[str(t)] = {"over": round(p_away, 4), "under": round(1 - p_away, 4)}

    return {
        "expected": {"home": round(home_corners_avg, 2), "away": round(away_corners_avg, 2), "total": round(total_expected, 2)},
        "over_under": over_under,
        "over_under_home": ou_home,
        "over_under_away": ou_away,
        "winner": {"home": round(home_prob, 4), "draw": round(draw_prob, 4), "away": round(away_prob, 4)}
    }


def predict_cards_markets(home_cards_avg: float, away_cards_avg: float) -> Dict:
    """Predice mercados de tarjetas usando Poisson simple."""
    total_expected = home_cards_avg + away_cards_avg
    
    # Over/Under para tarjetas
    thresholds = [2.5, 3.5, 4.5, 5.5, 6.5]
    over_under = {}
    
    for t in thresholds:
        over_prob = 1 - PoissonEngine.get_cumulative_probability(total_expected, int(t))
        over_under[str(t)] = {"over": round(over_prob, 4), "under": round(1 - over_prob, 4)}
    
    # Quién tendrá más tarjetas (1X2)
    home_prob = 0.0
    draw_prob = 0.0
    away_prob = 0.0
    
    for h in range(10):
        for a in range(10):
            p_h = PoissonEngine.get_probability(home_cards_avg, h)
            p_a = PoissonEngine.get_probability(away_cards_avg, a)
            joint = p_h * p_a
            if h > a:
                home_prob += joint
            elif h < a:
                away_prob += joint
            else:
                draw_prob += joint
    
    # Over/Under por equipo
    ou_home = {}
    ou_away = {}
    team_thresholds = [0.5, 1.5, 2.5, 3.5, 4.5]
    for t in team_thresholds:
        p_home = 1 - PoissonEngine.get_cumulative_probability(home_cards_avg, int(t))
        ou_home[str(t)] = {"over": round(p_home, 4), "under": round(1 - p_home, 4)}
        
        p_away = 1 - PoissonEngine.get_cumulative_probability(away_cards_avg, int(t))
        ou_away[str(t)] = {"over": round(p_away, 4), "under": round(1 - p_away, 4)}

    return {
        "expected": {"home": round(home_cards_avg, 2), "away": round(away_cards_avg, 2), "total": round(total_expected, 2)},
        "over_under": over_under,
        "over_under_home": ou_home,
        "over_under_away": ou_away,
        "winner": {"home": round(home_prob, 4), "draw": round(draw_prob, 4), "away": round(away_prob, 4)}
    }


def get_full_match_prediction(home_id: int, away_id: int, session: Session) -> Dict:
    """Función de alto nivel para la UI que integra xG y Predicciones."""
    from app.sports.football.analytics.data.team_stats import (
        get_team_corners_avg,
        get_team_cards_avg
    )
    
    home_xg, away_xg = calculate_expected_goals(home_id, away_id, session)
    preds = predict_goals_markets(home_xg, away_xg)
    ht_preds = predict_halftime_markets(home_xg, away_xg)
    handicaps = predict_handicap_markets(home_xg, away_xg)
    
    # Corners predictions
    home_corners = get_team_corners_avg(home_id, 20, session)
    away_corners = get_team_corners_avg(away_id, 20, session)
    corners_preds = predict_corners_markets(home_corners, away_corners) if (home_corners + away_corners) > 0 else None
    
    # Cards predictions
    home_cards = get_team_cards_avg(home_id, 20, session)
    away_cards = get_team_cards_avg(away_id, 20, session)
    home_cards_total = home_cards.get("yellow", 0) + home_cards.get("red", 0)
    away_cards_total = away_cards.get("yellow", 0) + away_cards.get("red", 0)
    cards_preds = predict_cards_markets(home_cards_total, away_cards_total) if (home_cards_total + away_cards_total) > 0 else None
    
    return {
        "expected_goals": {"home": round(home_xg, 2), "away": round(away_xg, 2)},
        "1x2": {
            "home_win": preds["1x2"]["home"],
            "draw": preds["1x2"]["draw"],
            "away_win": preds["1x2"]["away"]
        },
        "btts": preds["btts"],
        "over_under": preds["over_under"],
        "correct_score_top5": preds["correct_score"],
        "score_matrix": preds["correct_score"],
        "halftime": ht_preds,
        "handicaps": handicaps,
        "corners": corners_preds,
        "cards": cards_preds
    }

