"""
Goals Predictor - Over/Under, BTTS, Odd/Even, Team Goals.

Handles all goal-related betting markets using Poisson distribution.
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
from app.sports.football.predictions.poisson_model import PoissonModel


@dataclass
class GoalsPrediction:
    """Complete goals prediction for a match."""
    home_xg: float
    away_xg: float
    total_xg: float
    over_under: Dict[str, Dict[str, float]]  # {"2.5": {"over": 0.55, "under": 0.45}}
    btts: Dict[str, float]  # {"yes": P, "no": P}
    odd_even: Dict[str, float]  # {"odd": P, "even": P}
    exact_goals: Dict[int, float]  # {0: P, 1: P, ...}
    team_goals: Dict[str, Dict]  # {"home": {"over_0.5": P, ...}, "away": {...}}


class GoalsPredictor:
    """
    Predictor for all goal-related markets.
    
    Markets covered:
    - Total Goals Over/Under (0.5, 1.5, 2.5, 3.5, 4.5, 5.5)
    - Both Teams To Score (BTTS)
    - Odd/Even Total Goals
    - Exact Total Goals
    - Team Goals Over/Under
    - First/Second Half Goals
    """
    
    DEFAULT_LINES = [0.5, 1.5, 2.5, 3.5, 4.5, 5.5]
    TEAM_LINES = [0.5, 1.5, 2.5, 3.5]
    
    def __init__(self, poisson: Optional[PoissonModel] = None):
        self.poisson = poisson or PoissonModel()
    
    def predict(
        self,
        home_xg: float,
        away_xg: float,
        lines: Optional[List[float]] = None
    ) -> GoalsPrediction:
        """
        Generate complete goals prediction for a match.
        
        Args:
            home_xg: Expected goals for home team
            away_xg: Expected goals for away team
            lines: Custom over/under lines (default: 0.5 to 5.5)
        
        Returns:
            GoalsPrediction with all market probabilities
        """
        lines = lines or self.DEFAULT_LINES
        total_xg = home_xg + away_xg
        
        # Over/Under for total goals
        over_under = self.poisson.prob_total_goals(home_xg, away_xg, lines)
        
        # BTTS
        btts_yes = self.poisson.prob_btts(home_xg, away_xg)
        btts = {"yes": round(btts_yes, 4), "no": round(1 - btts_yes, 4)}
        
        # Odd/Even
        odd_even = self.poisson.prob_odd_even_total(home_xg, away_xg)
        
        # Exact total goals (0 to 8)
        exact_goals = {}
        for total_goals in range(9):
            prob = self._prob_exact_total(home_xg, away_xg, total_goals)
            exact_goals[total_goals] = round(prob, 4)
        
        # Team-specific goals
        team_goals = {
            "home": self._team_goal_lines(home_xg),
            "away": self._team_goal_lines(away_xg)
        }
        
        return GoalsPrediction(
            home_xg=round(home_xg, 2),
            away_xg=round(away_xg, 2),
            total_xg=round(total_xg, 2),
            over_under=over_under,
            btts=btts,
            odd_even=odd_even,
            exact_goals=exact_goals,
            team_goals=team_goals
        )
    
    def _prob_exact_total(
        self, 
        home_xg: float, 
        away_xg: float, 
        total: int
    ) -> float:
        """
        P(home + away = total)
        
        Sum of all combinations: P(0,total) + P(1,total-1) + ... + P(total,0)
        """
        prob = 0.0
        for home_goals in range(total + 1):
            away_goals = total - home_goals
            prob_home = self.poisson.prob_exact_goals(home_goals, home_xg)
            prob_away = self.poisson.prob_exact_goals(away_goals, away_xg)
            prob += prob_home * prob_away
        return prob
    
    def _team_goal_lines(self, xg: float) -> Dict[str, float]:
        """Calculate over/under probabilities for a single team."""
        result = {}
        for line in self.TEAM_LINES:
            over = self.poisson.prob_over(line, xg)
            result[f"over_{line}"] = round(over, 4)
            result[f"under_{line}"] = round(1 - over, 4)
        
        # Also add "to score" (over 0.5) and "clean sheet" (under 0.5 for opponent)
        result["to_score"] = round(1 - self.poisson.prob_exact_goals(0, xg), 4)
        result["no_goal"] = round(self.poisson.prob_exact_goals(0, xg), 4)
        
        return result
    
    def predict_half_goals(
        self,
        home_xg: float,
        away_xg: float,
        first_half_ratio: float = 0.45
    ) -> Dict[str, Dict]:
        """
        Predict goals per half.
        
        Historical data shows ~45% of goals in first half, 55% in second.
        
        Args:
            home_xg: Total match xG for home
            away_xg: Total match xG for away
            first_half_ratio: Proportion of goals in first half (default 0.45)
        
        Returns:
            {"first_half": {...}, "second_half": {...}}
        """
        second_half_ratio = 1 - first_half_ratio
        
        # Adjust xG for each half
        home_xg_1h = home_xg * first_half_ratio
        away_xg_1h = away_xg * first_half_ratio
        home_xg_2h = home_xg * second_half_ratio
        away_xg_2h = away_xg * second_half_ratio
        
        lines_half = [0.5, 1.5, 2.5]
        
        return {
            "first_half": {
                "over_under": self.poisson.prob_total_goals(home_xg_1h, away_xg_1h, lines_half),
                "btts": round(self.poisson.prob_btts(home_xg_1h, away_xg_1h), 4)
            },
            "second_half": {
                "over_under": self.poisson.prob_total_goals(home_xg_2h, away_xg_2h, lines_half),
                "btts": round(self.poisson.prob_btts(home_xg_2h, away_xg_2h), 4)
            }
        }
    
    def predict_score_ranges(
        self,
        home_xg: float,
        away_xg: float
    ) -> Dict[str, float]:
        """
        Predict probability of different score ranges.
        
        Useful for "high scoring game" or "low scoring game" bets.
        """
        matrix = self.poisson.get_match_scoreline_matrix(home_xg, away_xg, max_goals=6)
        
        ranges = {
            "0-1_goals": 0.0,    # 0-0, 1-0, 0-1
            "2-3_goals": 0.0,    # Total 2 or 3
            "4-5_goals": 0.0,    # Total 4 or 5
            "6+_goals": 0.0      # Total 6+
        }
        
        for (h, a), prob in matrix.items():
            total = h + a
            if total <= 1:
                ranges["0-1_goals"] += prob
            elif total <= 3:
                ranges["2-3_goals"] += prob
            elif total <= 5:
                ranges["4-5_goals"] += prob
            else:
                ranges["6+_goals"] += prob
        
        return {k: round(v, 4) for k, v in ranges.items()}
