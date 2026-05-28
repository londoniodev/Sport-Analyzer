"""
Player Predictor - Probabilidades de goleadores y estadística individual.
"""
from typing import Dict, List
import math
from app.sports.football.analytics.models.poisson import poisson_probability

class PlayerPredictor:
    """Predictor para mercados de jugadores."""

    @staticmethod
    def predict_goalscorer_probs(xg_per_90: float, expected_minutes: int = 90) -> Dict[str, float]:
        """
        Calcula probabilidades de gol para un jugador.
        
        Args:
            xg_per_90: Goles esperados por 90 mins.
            expected_minutes: Minutos que se espera juegue.
            
        Returns:
            Dict con prob 'anytime', 'brace' (doblete), 'hat_trick'.
        """
        # Ajustar xG a los minutos esperados
        xg_match = xg_per_90 * (expected_minutes / 90.0)
        
        # P(0 goles)
        prob_0 = poisson_probability(xg_match, 0)
        
        # P(>= 1 gol) = 1 - P(0)
        prob_anytime = 1.0 - prob_0
        
        # P(>= 2 goles) = 1 - P(0) - P(1)
        prob_1 = poisson_probability(xg_match, 1)
        prob_brace = 1.0 - (prob_0 + prob_1)
        
        # P(>= 3 goles)
        prob_2 = poisson_probability(xg_match, 2)
        prob_hat_trick = 1.0 - (prob_0 + prob_1 + prob_2)
        
        return {
            "anytime": round(prob_anytime, 4),
            "brace": round(prob_brace, 4),
            "hat_trick": round(prob_hat_trick, 4)
        }

    @staticmethod
    def predict_stat_milestone_prob(avg_per_90: float, milestone: float, expected_minutes: int = 90) -> float:
        """
        Probabilidad de alcanzar X tiros, pases, entradas, etc.
        Ej: Probabilidad de +0.5 asistencias (dar 1 asistencia).
        """
        lambda_val = avg_per_90 * (expected_minutes / 90.0)
        
        # Si milestone es 0.5 (Over 0.5), necesitamos P(X >= 1) = 1 - P(0)
        # Si milestone es 1.5 (Over 1.5), necesitamos P(X >= 2) = 1 - P(0) - P(1)
        
        needed = math.floor(milestone) + 1
        prob_less = sum(poisson_probability(lambda_val, k) for k in range(needed))
        
        return round(1.0 - prob_less, 4)
