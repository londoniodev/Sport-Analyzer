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
from app.sports.football.ui.dashboard import show_dashboard
from app.sports.football.ui.prediction_view import show_prediction_view
from app.sports.football.ui.rushbet_view import show_rushbet_view

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
    ui_views={
        "dashboard": show_dashboard,
        "prediction": show_prediction_view,
        "live_odds": show_rushbet_view,
    }
))
