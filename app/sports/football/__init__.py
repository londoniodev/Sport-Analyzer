"""
Football (Soccer) Sport Module
Registers football as a sport in the application.
"""
from app.core.registry import SportConfig, register_sport

# Import all components
from app.sports.football.models import (
    League, Team, Player, Coach, Fixture, TeamMatchStats, PlayerMatchStats,
    PlayerSeasonStats, Injury
)
from app.sports.football.api import FootballAPIClient
from app.sports.football.etl import FootballETL
from app.sports.football.analytics import FootballAnalytics

# Register this sport
register_sport(SportConfig(
    key="football",
    name="Fútbol",
    icon="⚽",
    api_client_class=FootballAPIClient,
    etl_class=FootballETL,
    analytics_class=FootballAnalytics,
    models=[League, Team, Player, Coach, Fixture, TeamMatchStats, PlayerMatchStats, PlayerSeasonStats, Injury],
    betting_markets=None,  # TODO: Implement betting markets
    # Removing UI mapping since we migrated to React/FastAPI
    # "ui_modules": {
    #     "Dashboard": show_dashboard,
    #     "Predictions": show_prediction_view,
    #     "Rushbet Value": show_rushbet_view,
    #     "Player Stats": show_player_browser
    # }
))
