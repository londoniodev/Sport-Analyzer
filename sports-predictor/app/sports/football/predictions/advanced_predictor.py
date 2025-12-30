"""
Advanced Predictor - Corners, Cards, and Shots.

Uses Poisson distribution and historical averages to predict advanced markets.
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
from app.sports.football.predictions.poisson_model import PoissonModel


@dataclass
class CornerPrediction:
    """Corner predictions for a match."""
    home_expected: float
    away_expected: float
    total_expected: float
    over_under: Dict[str, Dict[str, float]]  # {"8.5": {"over": P, "under": P}, ...}
    most_corners: Dict[str, float]  # {"home": P, "draw": P, "away": P}


@dataclass
class CardPrediction:
    """Card predictions for a match."""
    home_expected: float
    away_expected: float
    total_expected: float
    over_under: Dict[str, Dict[str, float]]  # {"3.5": {"over": P, "under": P}, ...}


@dataclass
class ShotPrediction:
    """Shot predictions for a match."""
    home_shots_expected: float
    away_shots_expected: float
    home_on_goal_expected: float
    away_on_goal_expected: float


class AdvancedPredictor:
    """
    Predictor for advanced betting markets (Corners, Cards, Shots).
    """
    
    CORNER_LINES = [7.5, 8.5, 9.5, 10.5, 11.5, 12.5]
    CARD_LINES = [2.5, 3.5, 4.5, 5.5, 6.5]
    
    def __init__(self, poisson: Optional[PoissonModel] = None):
        self.poisson = poisson or PoissonModel()
        
    def predict_corners(
        self,
        home_corner_avg: float,
        away_corner_avg: float,
        home_corner_conceded_avg: float,
        away_corner_conceded_avg: float
    ) -> CornerPrediction:
        """
        Predict corners based on historical offensive and defensive averages.
        
        Formula for expected corners per team:
        home_expected = (home_avg_for + away_avg_against) / 2
        away_expected = (away_avg_for + home_avg_against) / 2
        """
        home_expected = (home_corner_avg + away_corner_conceded_avg) / 2
        away_expected = (away_corner_avg + home_corner_conceded_avg) / 2
        total_expected = home_expected + away_expected
        
        # Over/Under
        over_under = self.poisson.prob_total_goals(home_expected, away_expected, self.CORNER_LINES)
        
        # Most Corners (1X2 Corners)
        most_corners = self.poisson.prob_match_result(home_expected, away_expected, max_goals=20)
        
        return CornerPrediction(
            home_expected=round(home_expected, 2),
            away_expected=round(away_expected, 2),
            total_expected=round(total_expected, 2),
            over_under=over_under,
            most_corners=most_corners
        )
        
    def predict_cards(
        self,
        home_card_avg: float,
        away_card_avg: float,
        ref_card_avg: float = 4.5
    ) -> CardPrediction:
        """
        Predict cards based on team aggression and referee statistics.
        
        Formula:
        total_expected = (home_avg + away_avg + ref_avg) / 2
        """
        # Weighting teams and referee
        team_avg = (home_card_avg + away_card_avg)
        total_expected = (team_avg + ref_card_avg) / 2
        
        home_expected = total_expected * (home_card_avg / (team_avg if team_avg > 0 else 1))
        away_expected = total_expected * (away_card_avg / (team_avg if team_avg > 0 else 1))
        
        over_under = self.poisson.prob_total_goals(home_expected, away_expected, self.CARD_LINES)
        
        return CardPrediction(
            home_expected=round(home_expected, 2),
            away_expected=round(away_expected, 2),
            total_expected=round(total_expected, 2),
            over_under=over_under
        )
        
    def predict_shots(
        self,
        home_shots_avg: float,
        away_shots_avg: float,
        home_on_goal_avg: float,
        away_on_goal_avg: float
    ) -> ShotPrediction:
        """
        Predict shots and shots on goal.
        """
        return ShotPrediction(
            home_shots_expected=round(home_shots_avg, 2),
            away_shots_expected=round(away_shots_avg, 2),
            home_on_goal_expected=round(home_on_goal_avg, 2),
            away_on_goal_expected=round(away_on_goal_avg, 2)
        )
