"""
Poisson Distribution Model for Football Predictions.

This is the core statistical model used for:
- Goal predictions (over/under, exact, BTTS)
- Match result (1X2)
- Handicaps
- Correct score
"""
import math
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class TeamStrength:
    """Attack and defense strength for a team."""
    attack: float  # Goals scored relative to league average
    defense: float  # Goals conceded relative to league average


class PoissonModel:
    """
    Poisson probability distribution for football goal predictions.
    
    The Poisson distribution models the probability of a given number of events
    occurring in a fixed interval, making it ideal for goals in football.
    
    P(X=k) = (λ^k × e^(-λ)) / k!
    
    Where λ (lambda) = expected number of goals
    """
    
    def __init__(self, league_avg_home_goals: float = 1.5, league_avg_away_goals: float = 1.2):
        """
        Initialize with league averages.
        
        Args:
            league_avg_home_goals: Average goals scored by home teams in the league
            league_avg_away_goals: Average goals scored by away teams in the league
        """
        self.league_avg_home = league_avg_home_goals
        self.league_avg_away = league_avg_away_goals
    
    @staticmethod
    def poisson_probability(k: int, lambda_: float) -> float:
        """
        Calculate P(X=k) for Poisson distribution.
        
        Args:
            k: Number of events (goals)
            lambda_: Expected value (mean)
        
        Returns:
            Probability of exactly k goals
        """
        if lambda_ <= 0:
            return 1.0 if k == 0 else 0.0
        return (lambda_ ** k) * math.exp(-lambda_) / math.factorial(k)
    
    def calculate_expected_goals(
        self,
        home_team: TeamStrength,
        away_team: TeamStrength
    ) -> Tuple[float, float]:
        """
        Calculate expected goals (xG) for both teams.
        
        Formula:
            xG_home = home_attack × away_defense × league_avg_home
            xG_away = away_attack × home_defense × league_avg_away
        
        Args:
            home_team: Home team's attack/defense strength
            away_team: Away team's attack/defense strength
        
        Returns:
            Tuple of (home_xG, away_xG)
        """
        home_xg = home_team.attack * away_team.defense * self.league_avg_home
        away_xg = away_team.attack * home_team.defense * self.league_avg_away
        return (home_xg, away_xg)
    
    def prob_exact_goals(self, goals: int, lambda_: float) -> float:
        """
        P(X = goals) - Probability of scoring EXACTLY this many goals.
        
        Example: P(team scores exactly 3 goals)
        """
        return self.poisson_probability(goals, lambda_)
    
    def prob_over(self, threshold: float, lambda_: float) -> float:
        """
        P(X > threshold) - Probability of scoring MORE than threshold.
        
        Example: P(over 2.5) = P(X >= 3) = 1 - P(X=0) - P(X=1) - P(X=2)
        
        Args:
            threshold: The line (e.g., 2.5 for over 2.5)
            lambda_: Expected goals
        """
        goals_needed = int(threshold) + 1  # For 2.5, we need >= 3
        prob_under = sum(self.poisson_probability(k, lambda_) for k in range(goals_needed))
        return 1 - prob_under
    
    def prob_under(self, threshold: float, lambda_: float) -> float:
        """
        P(X < threshold) - Probability of scoring LESS than threshold.
        
        Example: P(under 2.5) = P(X <= 2) = P(X=0) + P(X=1) + P(X=2)
        """
        goals_max = int(threshold)  # For 2.5, max is 2
        return sum(self.poisson_probability(k, lambda_) for k in range(goals_max + 1))
    
    def prob_at_least(self, goals: int, lambda_: float) -> float:
        """
        P(X >= goals) - Probability of scoring AT LEAST this many goals.
        
        Example: P(at least 1 goal) = 1 - P(X=0)
        """
        prob_less = sum(self.poisson_probability(k, lambda_) for k in range(goals))
        return 1 - prob_less
    
    def get_goal_distribution(
        self, 
        lambda_: float, 
        max_goals: int = 10
    ) -> Dict[int, float]:
        """
        Get full probability distribution for 0 to max_goals.
        
        Returns:
            Dict mapping goals -> probability
            e.g., {0: 0.22, 1: 0.33, 2: 0.25, 3: 0.12, ...}
        """
        return {k: self.poisson_probability(k, lambda_) for k in range(max_goals + 1)}
    
    def get_match_scoreline_matrix(
        self,
        home_xg: float,
        away_xg: float,
        max_goals: int = 6
    ) -> Dict[Tuple[int, int], float]:
        """
        Generate probability matrix for all scorelines.
        
        Returns:
            Dict mapping (home_goals, away_goals) -> probability
            e.g., {(0,0): 0.05, (1,0): 0.12, (0,1): 0.08, ...}
        """
        matrix = {}
        for home_goals in range(max_goals + 1):
            for away_goals in range(max_goals + 1):
                prob_home = self.poisson_probability(home_goals, home_xg)
                prob_away = self.poisson_probability(away_goals, away_xg)
                matrix[(home_goals, away_goals)] = prob_home * prob_away
        return matrix
    
    def prob_match_result(
        self,
        home_xg: float,
        away_xg: float,
        max_goals: int = 10
    ) -> Dict[str, float]:
        """
        Calculate 1X2 probabilities.
        
        Returns:
            {"home_win": P, "draw": P, "away_win": P}
        """
        home_win = 0.0
        draw = 0.0
        away_win = 0.0
        
        for home_goals in range(max_goals + 1):
            for away_goals in range(max_goals + 1):
                prob_home = self.poisson_probability(home_goals, home_xg)
                prob_away = self.poisson_probability(away_goals, away_xg)
                prob_scoreline = prob_home * prob_away
                
                if home_goals > away_goals:
                    home_win += prob_scoreline
                elif home_goals == away_goals:
                    draw += prob_scoreline
                else:
                    away_win += prob_scoreline
        
        return {
            "home_win": home_win,
            "draw": draw,
            "away_win": away_win
        }
    
    def prob_btts(self, home_xg: float, away_xg: float) -> float:
        """
        Both Teams To Score probability.
        
        P(BTTS) = P(home >= 1) × P(away >= 1)
                = (1 - P(home=0)) × (1 - P(away=0))
        """
        prob_home_scores = 1 - self.poisson_probability(0, home_xg)
        prob_away_scores = 1 - self.poisson_probability(0, away_xg)
        return prob_home_scores * prob_away_scores
    
    def prob_total_goals(
        self,
        home_xg: float,
        away_xg: float,
        lines: List[float] = [0.5, 1.5, 2.5, 3.5, 4.5]
    ) -> Dict[str, Dict[str, float]]:
        """
        Calculate over/under probabilities for multiple lines.
        
        Returns:
            {
                "2.5": {"over": 0.55, "under": 0.45},
                "3.5": {"over": 0.30, "under": 0.70},
                ...
            }
        """
        total_xg = home_xg + away_xg
        result = {}
        
        for line in lines:
            over = self.prob_over(line, total_xg)
            result[str(line)] = {
                "over": round(over, 4),
                "under": round(1 - over, 4)
            }
        
        return result
    
    def prob_odd_even_total(self, home_xg: float, away_xg: float, max_goals: int = 15) -> Dict[str, float]:
        """
        Calculate probability of odd vs even total goals.
        """
        matrix = self.get_match_scoreline_matrix(home_xg, away_xg, max_goals=max_goals // 2)
        
        prob_even = 0.0
        prob_odd = 0.0
        
        for (home_g, away_g), prob in matrix.items():
            total = home_g + away_g
            if total % 2 == 0:
                prob_even += prob
            else:
                prob_odd += prob
        
        return {"even": prob_even, "odd": prob_odd}
