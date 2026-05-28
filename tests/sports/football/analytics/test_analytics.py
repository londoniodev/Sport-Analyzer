
import pytest
from app.sports.football.analytics.models.poisson import PoissonEngine
from app.sports.football.analytics.predictive.goals import predict_goals_markets
from app.sports.football.analytics.predictive.advanced import AdvancedPredictor

class TestPoissonEngine:
    def test_get_probability_sanity(self):
        # P(X=0) for lambda=1 is e^-1 = 0.367879
        prob = PoissonEngine.get_probability(1.0, 0)
        assert abs(prob - 0.367879) < 0.0001
        
    def test_get_over_under_probabilities(self):
        lambda_val = 1.0
        thresholds = [0.5, 1.5]
        # P(X <= 0) = 0.3679 -> Over 0.5 = 1 - 0.3679 = 0.6321
        # P(X <= 1) = P(0) + P(1) = 0.3679 + 0.3679 = 0.7358 -> Over 1.5 = 0.2642
        
        results = PoissonEngine.get_over_under_probabilities(lambda_val, thresholds)
        
        assert "0.5" in results
        assert "1.5" in results
        assert abs(results["0.5"]["under"] - 0.3679) < 0.001
        assert abs(results["0.5"]["over"] - 0.6321) < 0.001
        
class TestGoalsPredictor:
    def test_predict_goals_markets_structure(self):
        result = predict_goals_markets(1.5, 1.2)
        assert "1x2" in result
        assert "btts" in result
        assert "over_under" in result
        assert "over_under_home" in result
        assert "over_under_away" in result
        
        # Check newly refactored home/away over/under
        assert "0.5" in result["over_under_home"]
        assert "over" in result["over_under_home"]["0.5"]
        
class TestAdvancedPredictor:
    def test_predict_corners_structure(self):
        # Test with arbitrary average values
        result = AdvancedPredictor.predict_corners(5.0, 4.0, 4.5, 5.5)
        
        assert "expected" in result
        assert "over_under" in result
        assert "over_under_home" in result
        assert "over_under_away" in result
        
        # Check team corners structure (refactored part)
        assert "1.5" in result["over_under_home"]
        assert result["over_under_home"]["1.5"]["over"] + result["over_under_home"]["1.5"]["under"] == 1.0

    def test_predict_cards_structure(self):
        result = AdvancedPredictor.predict_cards(2.0, 2.5)
        
        assert "expected" in result
        assert "over_under" in result
        assert "over_under_home" in result
        assert "over_under_away" in result
        
        # Check team cards structure (refactored part)
        assert "0.5" in result["over_under_home"]
