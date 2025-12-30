"""
Match Result Predictor - 1X2, Double Chance, Draw No Bet.

Combines Poisson and ELO models for match outcome predictions.
"""
from typing import Dict, Optional
from dataclasses import dataclass
from sqlmodel import Session
from app.sports.football.predictions.poisson_model import PoissonModel, TeamStrength
from app.sports.football.predictions.elo_rating import ELORating


@dataclass
class MatchPrediction:
    """Complete match prediction result."""
    home_team_id: int
    away_team_id: int
    home_xg: float
    away_xg: float
    result_1x2: Dict[str, float]
    double_chance: Dict[str, float]
    draw_no_bet: Dict[str, float]


class MatchResultPredictor:
    """
    Predictor for match result markets:
    - 1X2 (Home/Draw/Away)
    - Double Chance (1X, 12, X2)
    - Draw No Bet (DNB)
    """
    
    def __init__(
        self,
        poisson: Optional[PoissonModel] = None,
        elo: Optional[ELORating] = None
    ):
        self.poisson = poisson or PoissonModel()
        self.elo = elo or ELORating()
    
    def calculate_team_strength(
        self,
        team_id: int,
        goals_scored_avg: float,
        goals_conceded_avg: float,
        league_avg_goals: float
    ) -> TeamStrength:
        """
        Calculate attack and defense strength relative to league average.
        
        Attack strength = team's goals scored / league average
        Defense strength = team's goals conceded / league average
        """
        attack = goals_scored_avg / league_avg_goals if league_avg_goals > 0 else 1.0
        defense = goals_conceded_avg / league_avg_goals if league_avg_goals > 0 else 1.0
        return TeamStrength(attack=attack, defense=defense)
    
    def predict(
        self,
        home_team_id: int,
        away_team_id: int,
        home_attack_avg: float,
        home_defense_avg: float,
        away_attack_avg: float,
        away_defense_avg: float,
        league_avg_goals: float = 1.35
    ) -> MatchPrediction:
        """
        Generate complete match prediction.
        
        Args:
            home_team_id: Home team ID
            away_team_id: Away team ID
            home_attack_avg: Home team avg goals scored per match
            home_defense_avg: Home team avg goals conceded per match
            away_attack_avg: Away team avg goals scored per match
            away_defense_avg: Away team avg goals conceded per match
            league_avg_goals: League average goals per team per match
        
        Returns:
            MatchPrediction with all market probabilities
        """
        # Calculate team strengths
        home_strength = self.calculate_team_strength(
            home_team_id, home_attack_avg, home_defense_avg, league_avg_goals
        )
        away_strength = self.calculate_team_strength(
            away_team_id, away_attack_avg, away_defense_avg, league_avg_goals
        )
        
        # Calculate expected goals
        home_xg, away_xg = self.poisson.calculate_expected_goals(home_strength, away_strength)
        
        # 1X2 probabilities
        result_1x2 = self.poisson.prob_match_result(home_xg, away_xg)
        
        # Double Chance: 1X, 12, X2
        double_chance = {
            "1X": round(result_1x2["home_win"] + result_1x2["draw"], 4),
            "12": round(result_1x2["home_win"] + result_1x2["away_win"], 4),
            "X2": round(result_1x2["draw"] + result_1x2["away_win"], 4)
        }
        
        # Draw No Bet (remove draw, redistribute)
        non_draw_prob = result_1x2["home_win"] + result_1x2["away_win"]
        if non_draw_prob > 0:
            draw_no_bet = {
                "home": round(result_1x2["home_win"] / non_draw_prob, 4),
                "away": round(result_1x2["away_win"] / non_draw_prob, 4)
            }
        else:
            draw_no_bet = {"home": 0.5, "away": 0.5}
        
        return MatchPrediction(
            home_team_id=home_team_id,
            away_team_id=away_team_id,
            home_xg=round(home_xg, 2),
            away_xg=round(away_xg, 2),
            result_1x2=result_1x2,
            double_chance=double_chance,
            draw_no_bet=draw_no_bet
        )
    
    def get_value_bets(
        self, 
        prediction: MatchPrediction,
        bookmaker_odds: Dict[str, float],
        min_edge: float = 0.05
    ) -> Dict[str, Dict]:
        """
        Identify value bets where our probability > implied probability.
        
        Args:
            prediction: Our calculated prediction
            bookmaker_odds: Decimal odds from bookmaker {"home_win": 2.10, ...}
            min_edge: Minimum edge required (5% default)
        
        Returns:
            Dict of value bets with edge calculations
        """
        value_bets = {}
        
        for market, our_prob in prediction.result_1x2.items():
            if market in bookmaker_odds:
                odds = bookmaker_odds[market]
                implied_prob = 1 / odds
                edge = our_prob - implied_prob
                
                if edge >= min_edge:
                    value_bets[market] = {
                        "our_probability": round(our_prob, 4),
                        "implied_probability": round(implied_prob, 4),
                        "odds": odds,
                        "edge": round(edge, 4),
                        "kelly_stake": round(edge / (odds - 1), 4) if odds > 1 else 0
                    }
        
        return value_bets
