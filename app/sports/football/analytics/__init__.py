# Football Analytics unified module
from .models.poisson import PoissonEngine, poisson_probability
from .models.elo import ELORating

from .predictive.goals import (
    calculate_expected_goals,
    predict_goals_markets,
    get_full_match_prediction
)
from .predictive.advanced import AdvancedPredictor
from .predictive.players import PlayerPredictor

from .data.team_stats import (
    get_team_corners_avg,
    get_team_corners_conceded_avg,
    get_team_shots_avg,
    get_team_possession_avg,
    get_team_cards_avg,
    get_team_goals_avg,
    get_team_goals_conceded_avg,
    get_team_btts_pct,
    get_team_clean_sheet_pct,
    get_team_fouls_avg,
    get_team_over_under_pct
)

from .impact_engine import get_player_impact_score
from .football_analytics import FootballAnalytics

__all__ = [
    'FootballAnalytics',
    'PoissonEngine',
    'ELORating',
    'AdvancedPredictor',
    'PlayerPredictor',
    'calculate_expected_goals',
    'predict_goals_markets',
    'get_full_match_prediction',
    'get_player_impact_score',
    # Stats exports
    'get_team_corners_avg',
    'get_team_corners_conceded_avg',
    'get_team_shots_avg',
    'get_team_possession_avg',
    'get_team_cards_avg',
    'get_team_goals_avg',
    'get_team_goals_conceded_avg',
    'get_team_btts_pct',
    'get_team_clean_sheet_pct',
    'get_team_fouls_avg',
    'get_team_over_under_pct'
]

