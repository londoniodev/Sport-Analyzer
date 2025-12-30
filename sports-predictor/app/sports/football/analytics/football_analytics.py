"""
Football Analytics - Main analytics class implementing ISportAnalytics.
"""
from typing import Any, Dict
from sqlmodel import Session
from app.core.interfaces import ISportAnalytics
from app.sports.football.analytics.team_stats import (
    get_team_corners_avg,
    get_team_corners_conceded_avg,
    get_team_possession_avg,
    get_team_cards_avg,
    get_team_shots_avg
)
from app.sports.football.analytics.impact_engine import get_player_impact_score
from app.sports.football.models import Fixture


class FootballAnalytics(ISportAnalytics):
    """Analytics engine for football."""
    
    def get_prediction_metrics(self, event_id: int, session: Session) -> Dict[str, Any]:
        """
        Calculate prediction metrics for an upcoming football fixture.
        """
        fixture = session.get(Fixture, event_id)
        if not fixture:
            return {}
        
        home_team_id = fixture.home_team_id
        away_team_id = fixture.away_team_id
        
        return {
            "home_team": self.get_competitor_stats(home_team_id, 10, session),
            "away_team": self.get_competitor_stats(away_team_id, 10, session)
        }
    
    def get_competitor_stats(
        self, 
        competitor_id: int, 
        last_n_events: int, 
        session: Session
    ) -> Dict[str, Any]:
        """
        Get aggregated stats for a football team.
        """
        shots = get_team_shots_avg(competitor_id, last_n_events, session)
        cards = get_team_cards_avg(competitor_id, last_n_events, session)
        
        return {
            "corners_avg": get_team_corners_avg(competitor_id, last_n_events, session),
            "corners_conceded_avg": get_team_corners_conceded_avg(competitor_id, last_n_events, session),
            "possession_avg": get_team_possession_avg(competitor_id, last_n_events, session),
            "cards_yellow_avg": cards["yellow"],
            "cards_red_avg": cards["red"],
            "shots_total_avg": shots["total"],
            "shots_on_goal_avg": shots["on_goal"]
        }
    
    def get_player_impact(
        self, 
        team_id: int, 
        player_id: int, 
        session: Session
    ) -> Dict[str, Any]:
        """
        Get comprehensive player impact scores.
        """
        return get_player_impact_score(player_id, team_id, session)
