"""
Corners Predictor - Corner Kick Betting Markets.

Uses historical averages and player impact analysis.
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
from scipy.stats import norm
import math


@dataclass
class CornersPrediction:
    """Prediction for corner kick markets."""
    home_avg_corners: float
    away_avg_corners: float
    total_avg: float
    total_std: float
    over_under: Dict[str, Dict[str, float]]  # {"8.5": {"over": P, "under": P}}
    more_corners_1x2: Dict[str, float]       # {"home": P, "draw": P, "away": P}
    team_corners: Dict[str, Dict]            # Per-team over/under
    race_to: Dict[str, Dict[str, float]]     # Race to X corners


class CornersPredictor:
    """
    Predictor for corner kick markets.
    
    Uses Normal distribution (not Poisson) because:
    - Corners are more continuous than goals
    - Higher average reduces Poisson accuracy
    - Normal approximation works well for λ >= 5
    
    Markets:
    - Total Corners Over/Under
    - More Corners (1X2)
    - Team Corners Over/Under
    - Race to X Corners
    """
    
    DEFAULT_LINES = [7.5, 8.5, 9.5, 10.5, 11.5, 12.5]
    TEAM_LINES = [3.5, 4.5, 5.5, 6.5]
    RACE_TO = [3, 5, 7, 9]
    
    def __init__(self, default_std_factor: float = 0.35):
        """
        Args:
            default_std_factor: Standard deviation as fraction of mean
                               (0.35 means std = 35% of average)
        """
        self.std_factor = default_std_factor
    
    def predict(
        self,
        home_corners_avg: float,
        away_corners_avg: float,
        home_corners_std: Optional[float] = None,
        away_corners_std: Optional[float] = None,
        lines: Optional[List[float]] = None
    ) -> CornersPrediction:
        """
        Generate corner predictions.
        
        Args:
            home_corners_avg: Home team average corners per match
            away_corners_avg: Away team average corners per match
            home_corners_std: Home team std deviation (optional)
            away_corners_std: Away team std deviation (optional)
        """
        lines = lines or self.DEFAULT_LINES
        
        # Calculate totals
        total_avg = home_corners_avg + away_corners_avg
        
        # Estimate std if not provided
        home_std = home_corners_std or home_corners_avg * self.std_factor
        away_std = away_corners_std or away_corners_avg * self.std_factor
        
        # Combined std for total (assuming independence)
        total_std = math.sqrt(home_std**2 + away_std**2)
        
        # Over/Under for total corners (using Normal distribution)
        over_under = {}
        for line in lines:
            over_prob = 1 - norm.cdf(line, loc=total_avg, scale=total_std)
            over_under[str(line)] = {
                "over": round(over_prob, 4),
                "under": round(1 - over_prob, 4)
            }
        
        # More corners 1X2
        more_corners = self._calculate_more_corners(
            home_corners_avg, away_corners_avg, home_std, away_std
        )
        
        # Team corners
        team_corners = {
            "home": self._team_corner_lines(home_corners_avg, home_std),
            "away": self._team_corner_lines(away_corners_avg, away_std)
        }
        
        # Race to X corners
        race_to = self._calculate_race_to(home_corners_avg, away_corners_avg)
        
        return CornersPrediction(
            home_avg_corners=round(home_corners_avg, 2),
            away_avg_corners=round(away_corners_avg, 2),
            total_avg=round(total_avg, 2),
            total_std=round(total_std, 2),
            over_under=over_under,
            more_corners_1x2=more_corners,
            team_corners=team_corners,
            race_to=race_to
        )
    
    def _team_corner_lines(
        self,
        avg: float,
        std: float
    ) -> Dict[str, float]:
        """Calculate over/under for a single team."""
        result = {}
        for line in self.TEAM_LINES:
            over_prob = 1 - norm.cdf(line, loc=avg, scale=std)
            result[f"over_{line}"] = round(over_prob, 4)
            result[f"under_{line}"] = round(1 - over_prob, 4)
        return result
    
    def _calculate_more_corners(
        self,
        home_avg: float,
        away_avg: float,
        home_std: float,
        away_std: float
    ) -> Dict[str, float]:
        """
        Calculate probability of which team gets more corners.
        
        Uses the difference of two normal distributions.
        """
        # Difference: Home - Away
        diff_mean = home_avg - away_avg
        diff_std = math.sqrt(home_std**2 + away_std**2)
        
        # P(Home > Away) = P(diff > 0)
        prob_home = 1 - norm.cdf(0, loc=diff_mean, scale=diff_std)
        
        # P(Draw) ≈ probability density at 0 (approximation)
        # In reality, corners are integers, so we estimate draw probability
        prob_draw = 0.15  # Typical draw rate for corners
        
        # Adjust for draw
        prob_home_adj = prob_home * (1 - prob_draw)
        prob_away_adj = (1 - prob_home) * (1 - prob_draw)
        
        return {
            "home": round(prob_home_adj, 4),
            "draw": round(prob_draw, 4),
            "away": round(prob_away_adj, 4)
        }
    
    def _calculate_race_to(
        self,
        home_avg: float,
        away_avg: float
    ) -> Dict[str, Dict[str, float]]:
        """
        Calculate "Race to X corners" probabilities.
        
        Simplified: Uses proportion of corners each team typically gets.
        """
        total_avg = home_avg + away_avg
        home_ratio = home_avg / total_avg if total_avg > 0 else 0.5
        away_ratio = away_avg / total_avg if total_avg > 0 else 0.5
        
        race_to = {}
        for target in self.RACE_TO:
            # Probability that match reaches this many total corners
            reach_prob = 1 - norm.cdf(target - 0.5, loc=total_avg, scale=total_avg * 0.35)
            
            # Of matches that reach target, which team gets there first?
            # Simplified: proportional to corner ratio
            race_to[f"race_to_{target}"] = {
                "home": round(reach_prob * home_ratio, 4),
                "away": round(reach_prob * away_ratio, 4),
                "neither": round(1 - reach_prob, 4)
            }
        
        return race_to
    
    def predict_with_player_impact(
        self,
        base_prediction: CornersPrediction,
        player_impact: float
    ) -> CornersPrediction:
        """
        Adjust prediction based on player lineup impact.
        
        Args:
            base_prediction: Standard prediction
            player_impact: Adjustment factor (e.g., 1.1 = +10% corners)
        
        Returns:
            Adjusted prediction
        """
        # Adjust averages
        adjusted_home = base_prediction.home_avg_corners * player_impact
        adjusted_away = base_prediction.away_avg_corners  # Assume impact is for home team
        
        # Regenerate prediction
        return self.predict(adjusted_home, adjusted_away)
