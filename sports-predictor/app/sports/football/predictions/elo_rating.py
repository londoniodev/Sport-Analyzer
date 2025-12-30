"""
ELO Rating System for Football Teams.

ELO ratings measure relative team strength based on match results.
Originally from chess, adapted for football with home advantage factor.
"""
from dataclasses import dataclass
from typing import Dict, Optional, Tuple


@dataclass
class ELOConfig:
    """Configuration for ELO calculations."""
    k_factor: int = 32          # How much ratings change per match (higher = more volatile)
    home_advantage: int = 100   # ELO points added for home team
    initial_rating: int = 1500  # Starting rating for new teams


class ELORating:
    """
    ELO Rating system for calculating team strength.
    
    Formula:
        Expected = 1 / (1 + 10^((Rating_B - Rating_A) / 400))
        New_Rating = Old_Rating + K × (Actual - Expected)
    
    Where:
        - Actual = 1 for win, 0.5 for draw, 0 for loss
        - K = K-factor (sensitivity)
    """
    
    def __init__(self, config: Optional[ELOConfig] = None):
        self.config = config or ELOConfig()
        self._ratings: Dict[int, float] = {}  # team_id -> rating
    
    def get_rating(self, team_id: int) -> float:
        """Get current ELO rating for a team."""
        return self._ratings.get(team_id, self.config.initial_rating)
    
    def set_rating(self, team_id: int, rating: float) -> None:
        """Set ELO rating for a team."""
        self._ratings[team_id] = rating
    
    def expected_score(
        self, 
        team_a_rating: float, 
        team_b_rating: float,
        team_a_is_home: bool = True
    ) -> float:
        """
        Calculate expected score (probability of winning) for team A.
        
        Args:
            team_a_rating: ELO rating of team A
            team_b_rating: ELO rating of team B
            team_a_is_home: Whether team A is playing at home
        
        Returns:
            Expected score between 0 and 1
        """
        rating_diff = team_b_rating - team_a_rating
        
        if team_a_is_home:
            rating_diff -= self.config.home_advantage
        
        return 1 / (1 + 10 ** (rating_diff / 400))
    
    def update_ratings(
        self,
        home_team_id: int,
        away_team_id: int,
        home_goals: int,
        away_goals: int
    ) -> Tuple[float, float]:
        """
        Update ELO ratings after a match.
        
        Args:
            home_team_id: ID of home team
            away_team_id: ID of away team
            home_goals: Goals scored by home team
            away_goals: Goals scored by away team
        
        Returns:
            Tuple of (new_home_rating, new_away_rating)
        """
        home_rating = self.get_rating(home_team_id)
        away_rating = self.get_rating(away_team_id)
        
        # Expected scores
        expected_home = self.expected_score(home_rating, away_rating, team_a_is_home=True)
        expected_away = 1 - expected_home
        
        # Actual scores (1 = win, 0.5 = draw, 0 = loss)
        if home_goals > away_goals:
            actual_home, actual_away = 1.0, 0.0
        elif home_goals < away_goals:
            actual_home, actual_away = 0.0, 1.0
        else:
            actual_home, actual_away = 0.5, 0.5
        
        # Goal difference bonus (optional, makes big wins more impactful)
        goal_diff = abs(home_goals - away_goals)
        k_multiplier = 1 + (goal_diff - 1) * 0.1 if goal_diff > 1 else 1.0
        k = self.config.k_factor * k_multiplier
        
        # Update ratings
        new_home_rating = home_rating + k * (actual_home - expected_home)
        new_away_rating = away_rating + k * (actual_away - expected_away)
        
        self._ratings[home_team_id] = new_home_rating
        self._ratings[away_team_id] = new_away_rating
        
        return (new_home_rating, new_away_rating)
    
    def predict_match(
        self,
        home_team_id: int,
        away_team_id: int
    ) -> Dict[str, float]:
        """
        Predict match outcome probabilities based on ELO ratings.
        
        Note: This is a simplified prediction. For more accurate results,
        combine with Poisson model.
        
        Returns:
            {"home_win": P, "draw": P, "away_win": P}
        """
        home_rating = self.get_rating(home_team_id)
        away_rating = self.get_rating(away_team_id)
        
        expected_home = self.expected_score(home_rating, away_rating, team_a_is_home=True)
        expected_away = 1 - expected_home
        
        # Approximate draw probability (based on how close the match is)
        # Closer matches = higher draw probability
        rating_diff = abs(home_rating - away_rating + self.config.home_advantage)
        draw_prob = max(0.15, 0.30 - rating_diff / 1000)  # Between 15% and 30%
        
        # Adjust win probabilities
        remaining_prob = 1 - draw_prob
        home_win = expected_home * remaining_prob
        away_win = expected_away * remaining_prob
        
        return {
            "home_win": round(home_win, 4),
            "draw": round(draw_prob, 4),
            "away_win": round(away_win, 4)
        }
    
    def bulk_load_ratings(self, ratings: Dict[int, float]) -> None:
        """Load pre-calculated ratings for multiple teams."""
        self._ratings.update(ratings)
    
    def get_all_ratings(self) -> Dict[int, float]:
        """Get all current ratings."""
        return self._ratings.copy()
