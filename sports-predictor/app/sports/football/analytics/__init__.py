# Football Analytics module
from app.sports.football.analytics.team_stats import get_team_corners_avg
from app.sports.football.analytics.impact_engine import get_team_corners_with_player
from app.sports.football.analytics.football_analytics import FootballAnalytics

__all__ = [
    'FootballAnalytics',
    'get_team_corners_avg',
    'get_team_corners_with_player',
]
