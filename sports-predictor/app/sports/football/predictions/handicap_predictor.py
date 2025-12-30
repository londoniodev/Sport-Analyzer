"""
Handicap Predictor - Asian & European Handicap Markets.

Calculates probabilities for handicap betting lines.
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
from app.sports.football.predictions.poisson_model import PoissonModel


@dataclass
class HandicapPrediction:
    """Prediction for handicap markets."""
    home_xg: float
    away_xg: float
    european_handicaps: Dict[str, Dict[str, float]]  # {"home_-1": {"win": P, "draw": P, "lose": P}}
    asian_handicaps: Dict[str, Dict[str, float]]     # {"home_-1.5": {"win": P, "lose": P}}


class HandicapPredictor:
    """
    Predictor for handicap betting markets.
    
    European Handicap (3-way): Win/Draw/Lose with virtual score
    Asian Handicap: Win/Lose only (draw refunded or split)
    """
    
    # Common handicap lines
    EUROPEAN_LINES = [-2, -1, 0, 1, 2]  # Integer handicaps
    ASIAN_LINES = [-2.5, -2, -1.5, -1, -0.5, 0, 0.5, 1, 1.5, 2, 2.5]  # Half/Full lines
    
    def __init__(self, poisson: Optional[PoissonModel] = None):
        self.poisson = poisson or PoissonModel()
    
    def predict(
        self,
        home_xg: float,
        away_xg: float,
        european_lines: Optional[List[int]] = None,
        asian_lines: Optional[List[float]] = None
    ) -> HandicapPrediction:
        """
        Generate handicap predictions.
        
        Args:
            home_xg: Expected goals for home team
            away_xg: Expected goals for away team
        """
        european_lines = european_lines or self.EUROPEAN_LINES
        asian_lines = asian_lines or self.ASIAN_LINES
        
        # Get scoreline matrix
        matrix = self.poisson.get_match_scoreline_matrix(home_xg, away_xg, max_goals=8)
        
        # European handicaps (3-way)
        european = {}
        for line in european_lines:
            european[f"home_{line:+d}"] = self._european_handicap(matrix, line, is_home=True)
            european[f"away_{line:+d}"] = self._european_handicap(matrix, -line, is_home=False)
        
        # Asian handicaps (2-way)
        asian = {}
        for line in asian_lines:
            asian[f"home_{line:+.1f}"] = self._asian_handicap(matrix, line, is_home=True)
            asian[f"away_{line:+.1f}"] = self._asian_handicap(matrix, -line, is_home=False)
        
        return HandicapPrediction(
            home_xg=round(home_xg, 2),
            away_xg=round(away_xg, 2),
            european_handicaps=european,
            asian_handicaps=asian
        )
    
    def _european_handicap(
        self,
        matrix: Dict,
        handicap: int,
        is_home: bool
    ) -> Dict[str, float]:
        """
        Calculate European (3-way) handicap probabilities.
        
        The handicap is added to the team's score.
        E.g., Home -1 means home starts at -1, so they need to win by 2+.
        """
        win_prob = 0.0
        draw_prob = 0.0
        lose_prob = 0.0
        
        for (home_g, away_g), prob in matrix.items():
            # Apply handicap
            if is_home:
                adjusted_home = home_g + handicap
                adjusted_away = away_g
            else:
                adjusted_home = home_g
                adjusted_away = away_g + handicap
            
            # Determine outcome
            if is_home:
                if adjusted_home > adjusted_away:
                    win_prob += prob
                elif adjusted_home == adjusted_away:
                    draw_prob += prob
                else:
                    lose_prob += prob
            else:
                if adjusted_away > adjusted_home:
                    win_prob += prob
                elif adjusted_away == adjusted_home:
                    draw_prob += prob
                else:
                    lose_prob += prob
        
        return {
            "win": round(win_prob, 4),
            "draw": round(draw_prob, 4),
            "lose": round(lose_prob, 4)
        }
    
    def _asian_handicap(
        self,
        matrix: Dict,
        handicap: float,
        is_home: bool
    ) -> Dict[str, float]:
        """
        Calculate Asian (2-way) handicap probabilities.
        
        Half-point handicaps (.5) have no draw - it's win or lose.
        Whole/Quarter point handicaps (.0, .25, .75) can have push/split.
        """
        win_prob = 0.0
        lose_prob = 0.0
        push_prob = 0.0  # For whole number handicaps
        
        for (home_g, away_g), prob in matrix.items():
            # Calculate goal difference from team's perspective
            if is_home:
                diff = (home_g + handicap) - away_g
            else:
                diff = (away_g + handicap) - home_g
            
            # Determine outcome
            if diff > 0:
                win_prob += prob
            elif diff < 0:
                lose_prob += prob
            else:
                push_prob += prob  # Exact draw with handicap = push
        
        # For half-point lines, there's no push
        if handicap % 1 != 0:  # Has decimal (e.g., -1.5)
            return {
                "win": round(win_prob, 4),
                "lose": round(lose_prob, 4)
            }
        else:
            # For whole numbers, push returns stake
            return {
                "win": round(win_prob, 4),
                "push": round(push_prob, 4),
                "lose": round(lose_prob, 4)
            }
    
    def get_best_handicap_value(
        self,
        prediction: HandicapPrediction,
        bookmaker_odds: Dict[str, float],
        min_edge: float = 0.03
    ) -> Dict[str, Dict]:
        """
        Find handicap lines with value compared to bookmaker odds.
        """
        value_bets = {}
        
        for line, probs in prediction.asian_handicaps.items():
            if "win" in probs and line in bookmaker_odds:
                odds = bookmaker_odds[line]
                implied = 1 / odds
                edge = probs["win"] - implied
                
                if edge >= min_edge:
                    value_bets[line] = {
                        "probability": probs["win"],
                        "odds": odds,
                        "edge": round(edge, 4)
                    }
        
        return value_bets
