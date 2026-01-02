"""
Advanced Predictor - Córners, Tarjetas y Tiros usando estadísticas dinámicas.
"""
import math
from typing import Dict, List, Optional
from scipy.stats import norm
from app.sports.football.analytics.models.poisson import PoissonEngine

class AdvancedPredictor:
    """Predictor para mercados avanzados (Córners, Tarjetas, Tiros)."""

    @staticmethod
    def predict_corners(home_avg: float, away_avg: float, home_conceded: float, away_conceded: float) -> Dict:
        """Predice córners usando distribución Normal."""
        home_xc = (home_avg + away_conceded) / 2
        away_xc = (away_avg + home_conceded) / 2
        total_xc = home_xc + away_xc
        
        std = math.sqrt((home_xc * 0.35)**2 + (away_xc * 0.35)**2)
        
        lines = [7.5, 8.5, 9.5, 10.5, 11.5, 12.5]
        over_under = {}
        for line in lines:
            over_prob = 1 - norm.cdf(line, loc=total_xc, scale=std)
            over_under[str(line)] = {"over": round(over_prob, 4), "under": round(1 - over_prob, 4)}
            
        # 1x2 Córners (Simple approximation based on mean diff)
        diff_sigma = math.sqrt((home_xc * 0.35)**2 + (away_xc * 0.35)**2)
        p_home_more = 1 - norm.cdf(0.5, loc=home_xc - away_xc, scale=diff_sigma)
        p_away_more = norm.cdf(-0.5, loc=home_xc - away_xc, scale=diff_sigma)
        p_equal = 1 - (p_home_more + p_away_more)
            
        return {
            "expected": {"home": round(home_xc, 2), "away": round(away_xc, 2), "total": round(total_xc, 2)},
            "over_under": over_under,
            "1x2": {"home": round(p_home_more, 4), "draw": round(p_equal, 4), "away": round(p_away_more, 4)}
        }

    @staticmethod
    def predict_cards(home_avg: float, away_avg: float, ref_avg: float = 4.5) -> Dict:
        """Predice tarjetas."""
        total_expected = (home_avg + away_avg + ref_avg) / 2
        lines = [3.5, 4.5, 5.5, 6.5]
        over_under = {}
        from app.sports.football.analytics.models.poisson import poisson_probability
        for line in lines:
            under_prob = sum(poisson_probability(total_expected, k) for k in range(int(line) + 1))
            over_under[str(line)] = {"over": round(1 - under_prob, 4), "under": round(under_prob, 4)}
            
        return {"expected": round(total_expected, 2), "over_under": over_under}

    @staticmethod
    def predict_shots(home_shots: Dict, away_shots: Dict) -> Dict:
        """Predice tiros Totales y a Puerta."""
        # Se asume que home_shots es dict {"total": X, "on_goal": Y}
        exp_total = (home_shots["total"] + away_shots["total"])
        exp_on_goal = (home_shots["on_goal"] + away_shots["on_goal"])
        
        return {
            "expected_total": round(exp_total, 2),
            "expected_on_goal": round(exp_on_goal, 2),
            "home_expected": round(home_shots["total"], 2),
            "away_expected": round(away_shots["total"], 2)
        }
        
    @staticmethod
    def predict_fouls(home_fouls: float, away_fouls: float) -> Dict:
        """Predice faltas totales y por equipo."""
        return {
            "total_expected": round(home_fouls + away_fouls, 2),
            "home_expected": round(home_fouls, 2),
            "away_expected": round(away_fouls, 2)
        }
