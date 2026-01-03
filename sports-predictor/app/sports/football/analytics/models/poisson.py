"""
Poisson Model - Predictor de goles basado en distribución Poisson.
"""
from typing import Dict, List, Tuple
from math import exp, factorial
from sqlmodel import Session


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


class PoissonEngine:
    """
    Motor estadístico Poisson con soporte para ajustes dinámicos.
    """
    
    @staticmethod
    def get_probability(lambda_val: float, k: int) -> float:
        """Calcula la probabilidad de exactamente k eventos."""
        return poisson_probability(lambda_val, k)
    
    @staticmethod
    def get_cumulative_probability(lambda_val: float, k: int) -> float:
        """Calcula P(X <= k), la probabilidad acumulada hasta k eventos."""
        return sum(poisson_probability(lambda_val, i) for i in range(k + 1))
    
    @staticmethod
    def get_joint_probability(home_xg: float, home_goals: int, away_xg: float, away_goals: int, rho: float = 0.1) -> float:
        """Calcula la probabilidad conjunta de un marcador específico con ajuste Dixon-Coles."""
        prob_home = poisson_probability(home_xg, home_goals)
        prob_away = poisson_probability(away_xg, away_goals)
        tau = calculate_dixon_coles_tau(home_goals, away_goals, home_xg, away_xg, rho)
        return prob_home * prob_away * tau

