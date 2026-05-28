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
        
        lines = [4.5, 5.5, 6.5, 7.5, 8.5, 9.5, 10.5, 11.5, 12.5, 13.5, 14.5]
        over_under = {}
        for line in lines:
            over_prob = 1 - norm.cdf(line, loc=total_xc, scale=std)
            over_under[str(line)] = {"over": round(over_prob, 4), "under": round(1 - over_prob, 4)}
            
        # 1x2 Córners (Simple approximation based on mean diff)
        diff_sigma = math.sqrt((home_xc * 0.35)**2 + (away_xc * 0.35)**2)
        p_home_more = 1 - norm.cdf(0.5, loc=home_xc - away_xc, scale=diff_sigma)
        p_away_more = norm.cdf(-0.5, loc=home_xc - away_xc, scale=diff_sigma)
        p_equal = 1 - (p_home_more + p_away_more)
        
        # Team Corners O/U (Poisson approximation)
        from app.sports.football.analytics.models.poisson import poisson_probability
        team_lines = [1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5]
        
        ou_home = PoissonEngine.get_over_under_probabilities(home_xc, team_lines)
        ou_away = PoissonEngine.get_over_under_probabilities(away_xc, team_lines)
            
        return {
            "expected": {"home": round(home_xc, 2), "away": round(away_xc, 2), "total": round(total_xc, 2)},
            "over_under": over_under,
            "over_under_home": ou_home,
            "over_under_away": ou_away,
            "1x2": {"home": round(p_home_more, 4), "draw": round(p_equal, 4), "away": round(p_away_more, 4)},
            "winner": {"home": round(p_home_more, 4), "draw": round(p_equal, 4), "away": round(p_away_more, 4)} # Alias for winner
        }

    @staticmethod
    def predict_cards(home_avg: float, away_avg: float, ref_avg: float = 4.5) -> Dict:
        """Predice tarjetas."""
        total_expected = (home_avg + away_avg + ref_avg) / 2
        
        # Repartir total_expected según promedios relativos (aprox)
        if (home_avg + away_avg) > 0:
            h_ratio = home_avg / (home_avg + away_avg)
            a_ratio = away_avg / (home_avg + away_avg)
            h_exp = total_expected * h_ratio
            a_exp = total_expected * a_ratio
        else:
            h_exp = total_expected / 2
            a_exp = total_expected / 2
            
        lines = [2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5]
        over_under = PoissonEngine.get_over_under_probabilities(total_expected, lines)
        
        # Team Cards O/U
        team_lines = [0.5, 1.5, 2.5, 3.5, 4.5]
        ou_home = PoissonEngine.get_over_under_probabilities(h_exp, team_lines)
        ou_away = PoissonEngine.get_over_under_probabilities(a_exp, team_lines)
            
        return {
            "expected": round(total_expected, 2), 
            "over_under": over_under,
            "over_under_home": ou_home,
            "over_under_away": ou_away
        }

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
