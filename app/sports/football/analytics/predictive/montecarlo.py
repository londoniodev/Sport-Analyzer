"""
Monte Carlo Engine - Simulación vectorizada de partidos y grupos usando NumPy.
"""
import numpy as np
from typing import Dict
from app.sports.football.analytics.models.poisson import calculate_dixon_coles_tau

class MonteCarloEngine:
    """Simulador Montecarlo para el Mundial."""

    @staticmethod
    def simulate_match(home_xg: float, away_xg: float, rho: float = 0.1, n: int = 10000) -> Dict:
        """
        Simula N partidos usando numpy vectorizado.
        Aplica Dixon-Coles aproximado para corregir marcadores de baja puntuación.
        """
        # Vectorized generation of base goals
        home_goals = np.random.poisson(home_xg, n)
        away_goals = np.random.poisson(away_xg, n)
        
        # Count occurrences of each scoreline
        scores, counts = np.unique(np.vstack((home_goals, away_goals)).T, axis=0, return_counts=True)
        
        distribution = {}
        for score, count in zip(scores, counts):
            h, a = score
            # Apply Dixon-Coles tau correction per unique scoreline
            tau = calculate_dixon_coles_tau(h, a, home_xg, away_xg, rho)
            weighted_count = count * tau
            distribution[f"{h}-{a}"] = weighted_count
            
        # Normalize probabilities so they sum to 1.0
        total_weight = sum(distribution.values())
        if total_weight > 0:
            distribution = {k: v / total_weight for k, v in distribution.items()}
            
        # Calculate 1X2 Probabilities
        home_win, draw, away_win = 0.0, 0.0, 0.0
        for score_str, prob in distribution.items():
            h, a = map(int, score_str.split('-'))
            if h > a:
                home_win += prob
            elif h < a:
                away_win += prob
            else:
                draw += prob
                
        return {
            "simulations": n,
            "score_distribution": distribution,
            "result_probs": {
                "home": home_win,
                "draw": draw,
                "away": away_win
            }
        }

    @staticmethod
    def simulate_team_shootout(home_elo: float, away_elo: float) -> str:
        """
        Función determinística para decidir el ganador en caso de empate a 90'
        basada en una probabilidad cruzada con la diferencia de Elo.
        Se usa para avanzar equipos en el bracket de la UI sin depender del azar (Montecarlo)
        y sin alterar los goles del partido original.
        """
        elo_diff = home_elo - away_elo
        prob_home = 0.5 + (elo_diff / 1000.0) * 0.5
        # Cap the probability between 35% and 65% to ensure upsets are possible in a real shootout,
        # although this deterministic function will just pick the favorite.
        prob_home = max(0.35, min(0.65, prob_home))
        
        return 'home' if prob_home >= 0.5 else 'away'
