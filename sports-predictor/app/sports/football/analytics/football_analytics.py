"""
Football Analytics - Main analytics class implementing ISportAnalytics.
"""
from typing import Any, Dict
from sqlmodel import Session
from app.core.interfaces import ISportAnalytics
from app.sports.football.analytics.team_stats import (
    get_team_corners_avg,
    get_team_possession_avg,
    get_team_cards_avg
)
from app.sports.football.analytics.impact_engine import get_team_corners_with_player
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
            "home_team": {
                "corners_avg": get_team_corners_avg(home_team_id, 10, session),
                "possession_avg": get_team_possession_avg(home_team_id, 10, session),
                "cards_avg": get_team_cards_avg(home_team_id, 10, session),
            },
            "away_team": {
                "corners_avg": get_team_corners_avg(away_team_id, 10, session),
                "possession_avg": get_team_possession_avg(away_team_id, 10, session),
                "cards_avg": get_team_cards_avg(away_team_id, 10, session),
            }
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
        return {
            "corners_avg": get_team_corners_avg(competitor_id, last_n_events, session),
            "possession_avg": get_team_possession_avg(competitor_id, last_n_events, session),
            "cards_avg": get_team_cards_avg(competitor_id, last_n_events, session),
        }
    
    def get_player_impact_on_corners(
        self, 
        team_id: int, 
        player_id: int, 
        session: Session
    ) -> float:
        """
        Football-specific: Get player impact on team corners.
        """
        return get_team_corners_with_player(team_id, player_id, session)
