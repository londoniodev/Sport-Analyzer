"""
Exact Score Predictor - Correct Score Betting Markets.

Uses bivariate Poisson for scoreline probabilities.
"""
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from app.sports.football.predictions.poisson_model import PoissonModel


@dataclass
class ExactScorePrediction:
    """Prediction for exact/correct score markets."""
    home_xg: float
    away_xg: float
    scorelines: Dict[str, float]          # {"1-0": P, "2-1": P, ...}
    top_scorelines: List[Tuple[str, float]]  # Sorted by probability
    victory_margin: Dict[str, float]      # {"home_1": P, "home_2": P, ...}


class ExactScorePredictor:
    """
    Predictor for exact/correct score markets.
    
    Markets:
    - Correct Score (e.g., 2-1, 0-0)
    - Victory Margin (e.g., Home by 1, Home by 2+)
    - Highest Scoring Half
    """
    
    MAX_GOALS = 6  # Consider scorelines up to 6-6
    
    def __init__(self, poisson: Optional[PoissonModel] = None):
        self.poisson = poisson or PoissonModel()
    
    def predict(
        self,
        home_xg: float,
        away_xg: float,
        max_goals: int = 6
    ) -> ExactScorePrediction:
        """
        Generate exact score predictions.
        
        Args:
            home_xg: Expected goals for home team
            away_xg: Expected goals for away team
            max_goals: Maximum goals per team to consider
        """
        # Get scoreline matrix
        matrix = self.poisson.get_match_scoreline_matrix(home_xg, away_xg, max_goals)
        
        # Convert to string format
        scorelines = {}
        for (home_g, away_g), prob in matrix.items():
            key = f"{home_g}-{away_g}"
            scorelines[key] = round(prob, 4)
        
        # Sort by probability
        sorted_scores = sorted(scorelines.items(), key=lambda x: x[1], reverse=True)
        top_scorelines = sorted_scores[:15]  # Top 15 most likely
        
        # Victory margin
        victory_margin = self._calculate_victory_margin(matrix)
        
        return ExactScorePrediction(
            home_xg=round(home_xg, 2),
            away_xg=round(away_xg, 2),
            scorelines=scorelines,
            top_scorelines=top_scorelines,
            victory_margin=victory_margin
        )
    
    def _calculate_victory_margin(self, matrix: Dict) -> Dict[str, float]:
        """
        Calculate probability of each victory margin.
        
        e.g., Home by 1, Home by 2, Home by 3+, Draw, Away by 1, etc.
        """
        margins = {
            "home_1": 0.0,
            "home_2": 0.0,
            "home_3+": 0.0,
            "draw_0-0": 0.0,
            "draw_with_goals": 0.0,
            "away_1": 0.0,
            "away_2": 0.0,
            "away_3+": 0.0
        }
        
        for (home_g, away_g), prob in matrix.items():
            diff = home_g - away_g
            
            if diff == 0:
                if home_g == 0:
                    margins["draw_0-0"] += prob
                else:
                    margins["draw_with_goals"] += prob
            elif diff == 1:
                margins["home_1"] += prob
            elif diff == 2:
                margins["home_2"] += prob
            elif diff >= 3:
                margins["home_3+"] += prob
            elif diff == -1:
                margins["away_1"] += prob
            elif diff == -2:
                margins["away_2"] += prob
            elif diff <= -3:
                margins["away_3+"] += prob
        
        return {k: round(v, 4) for k, v in margins.items()}
    
    def get_grouped_scores(
        self,
        prediction: ExactScorePrediction
    ) -> Dict[str, Dict[str, float]]:
        """
        Group scorelines into categories for easier analysis.
        """
        groups = {
            "home_wins": {},
            "draws": {},
            "away_wins": {},
            "high_scoring": {},  # 4+ total goals
            "low_scoring": {}    # 0-2 total goals
        }
        
        for score, prob in prediction.scorelines.items():
            home_g, away_g = map(int, score.split("-"))
            total = home_g + away_g
            
            if home_g > away_g:
                groups["home_wins"][score] = prob
            elif home_g == away_g:
                groups["draws"][score] = prob
            else:
                groups["away_wins"][score] = prob
            
            if total >= 4:
                groups["high_scoring"][score] = prob
            elif total <= 2:
                groups["low_scoring"][score] = prob
        
        # Sort each group by probability
        for group in groups:
            groups[group] = dict(
                sorted(groups[group].items(), key=lambda x: x[1], reverse=True)[:5]
            )
        
        return groups
    
    def get_score_probability(
        self,
        home_xg: float,
        away_xg: float,
        home_goals: int,
        away_goals: int
    ) -> float:
        """
        Get probability of a specific scoreline.
        
        Convenience method for quick lookups.
        """
        prob_home = self.poisson.prob_exact_goals(home_goals, home_xg)
        prob_away = self.poisson.prob_exact_goals(away_goals, away_xg)
        return round(prob_home * prob_away, 4)
