"""
Goalscorer Predictor - Player Goal Scoring Markets.

Uses xG (expected goals) per player to predict goalscorer markets.
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
import math


@dataclass
class PlayerGoalPrediction:
    """Prediction for a single player's goal probability."""
    player_id: int
    player_name: str
    team_id: int
    expected_minutes: float
    xg_per_90: float
    prob_to_score: float       # Anytime scorer
    prob_2_plus_goals: float   # Score 2+ goals
    prob_first_scorer: float   # First goalscorer


@dataclass
class GoalscorerPrediction:
    """Complete goalscorer market prediction."""
    home_scorers: List[PlayerGoalPrediction]
    away_scorers: List[PlayerGoalPrediction]
    anytime_scorer: Dict[str, float]   # {player_name: P}
    first_scorer: Dict[str, float]     # {player_name: P}
    

class GoalscorerPredictor:
    """
    Predictor for goalscorer betting markets.
    
    Markets:
    - Anytime Scorer (player scores at any point)
    - First Scorer (player scores first goal)
    - Last Scorer (player scores last goal)
    - 2+ Goals (player scores multiple)
    
    Uses xG (Expected Goals) methodology:
    - xG per shot based on location/situation
    - Player's shooting volume (shots per 90)
    - Expected playing time
    """
    
    def __init__(self, avg_goals_per_match: float = 2.7):
        """
        Args:
            avg_goals_per_match: Average total goals per match in the league
        """
        self.avg_goals_per_match = avg_goals_per_match
    
    def predict_player(
        self,
        player_id: int,
        player_name: str,
        team_id: int,
        shots_per_90: float,
        xg_per_shot: float,
        expected_minutes: float,
        team_xg: float
    ) -> PlayerGoalPrediction:
        """
        Generate prediction for a single player.
        
        Args:
            player_id: Player's database ID
            player_name: Player's name
            team_id: Team's database ID
            shots_per_90: Average shots per 90 minutes
            xg_per_shot: Average xG per shot (typically 0.08-0.15)
            expected_minutes: Expected minutes to play in match
            team_xg: Team's expected goals for the match
        
        Returns:
            PlayerGoalPrediction with all probabilities
        """
        # Calculate player's xG for the match
        xg_per_90 = shots_per_90 * xg_per_shot
        match_xg = xg_per_90 * (expected_minutes / 90)
        
        # Probability to score at least once
        # P(score >= 1) = 1 - P(score = 0) = 1 - e^(-xG)
        prob_to_score = 1 - math.exp(-match_xg) if match_xg > 0 else 0
        
        # Probability to score 2+ goals
        # P(score >= 2) = 1 - P(0) - P(1) = 1 - e^(-xG) - xG*e^(-xG)
        prob_2_plus = 1 - math.exp(-match_xg) * (1 + match_xg) if match_xg > 0 else 0
        
        # First scorer probability (simplified)
        # Proportional to xG share of team's total xG
        if team_xg > 0 and prob_to_score > 0:
            xg_share = match_xg / team_xg
            # Probability team scores first AND this player is the scorer
            # Simplified: assume roughly equal home/away first scorer chance
            prob_first = xg_share * 0.5  # 50% chance team scores first
        else:
            prob_first = 0
        
        return PlayerGoalPrediction(
            player_id=player_id,
            player_name=player_name,
            team_id=team_id,
            expected_minutes=expected_minutes,
            xg_per_90=round(xg_per_90, 3),
            prob_to_score=round(prob_to_score, 4),
            prob_2_plus_goals=round(prob_2_plus, 4),
            prob_first_scorer=round(prob_first, 4)
        )
    
    def predict_match(
        self,
        home_players: List[Dict],
        away_players: List[Dict],
        home_xg: float,
        away_xg: float
    ) -> GoalscorerPrediction:
        """
        Generate predictions for all players in a match.
        
        Args:
            home_players: List of dicts with player info:
                         {"id", "name", "shots_per_90", "xg_per_shot", "expected_minutes"}
            away_players: Same format for away team
            home_xg: Home team expected goals
            away_xg: Away team expected goals
        
        Returns:
            GoalscorerPrediction with all markets
        """
        home_scorers = []
        away_scorers = []
        
        for player in home_players:
            pred = self.predict_player(
                player_id=player.get("id", 0),
                player_name=player.get("name", "Unknown"),
                team_id=player.get("team_id", 0),
                shots_per_90=player.get("shots_per_90", 0),
                xg_per_shot=player.get("xg_per_shot", 0.1),
                expected_minutes=player.get("expected_minutes", 90),
                team_xg=home_xg
            )
            home_scorers.append(pred)
        
        for player in away_players:
            pred = self.predict_player(
                player_id=player.get("id", 0),
                player_name=player.get("name", "Unknown"),
                team_id=player.get("team_id", 0),
                shots_per_90=player.get("shots_per_90", 0),
                xg_per_shot=player.get("xg_per_shot", 0.1),
                expected_minutes=player.get("expected_minutes", 90),
                team_xg=away_xg
            )
            away_scorers.append(pred)
        
        # Build anytime scorer dict
        anytime = {}
        for p in home_scorers + away_scorers:
            anytime[p.player_name] = p.prob_to_score
        
        # Build first scorer dict (normalized)
        first_scorer = {}
        total_first = sum(p.prob_first_scorer for p in home_scorers + away_scorers)
        if total_first > 0:
            for p in home_scorers + away_scorers:
                first_scorer[p.player_name] = round(p.prob_first_scorer / total_first, 4)
        
        # Add "No Goal" option
        prob_no_goal = math.exp(-(home_xg + away_xg))
        first_scorer["No goalscorer"] = round(prob_no_goal, 4)
        
        return GoalscorerPrediction(
            home_scorers=sorted(home_scorers, key=lambda x: x.prob_to_score, reverse=True),
            away_scorers=sorted(away_scorers, key=lambda x: x.prob_to_score, reverse=True),
            anytime_scorer=dict(sorted(anytime.items(), key=lambda x: x[1], reverse=True)),
            first_scorer=dict(sorted(first_scorer.items(), key=lambda x: x[1], reverse=True))
        )
    
    def get_top_scorers(
        self,
        prediction: GoalscorerPrediction,
        top_n: int = 5
    ) -> Dict[str, List[Dict]]:
        """
        Get top N most likely scorers from each team.
        """
        return {
            "home": [
                {"name": p.player_name, "prob": p.prob_to_score}
                for p in prediction.home_scorers[:top_n]
            ],
            "away": [
                {"name": p.player_name, "prob": p.prob_to_score}
                for p in prediction.away_scorers[:top_n]
            ]
        }
