"""
Abstract interfaces for sport-specific implementations.
Each sport must implement these to plug into the system.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List
from sqlmodel import Session


class ISportAPIClient(ABC):
    """Interface for external API integrations."""
    
    @abstractmethod
    def get_events(self, league_id: int, season: int) -> List[Dict[str, Any]]:
        """Fetch events (matches/games) from external API."""
        ...
    
    @abstractmethod
    def get_event_stats(self, event_id: int) -> List[Dict[str, Any]]:
        """Fetch statistics for a specific event."""
        ...
    
    @abstractmethod
    def get_event_lineups(self, event_id: int) -> List[Dict[str, Any]]:
        """Fetch lineups/rosters for a specific event."""
        ...


class ISportETL(ABC):
    """Interface for Extract-Transform-Load operations."""
    
    @abstractmethod
    def sync_league_data(self, league_id: int, season: int) -> None:
        """Sync all data for a league/season from API to database."""
        ...
    
    @abstractmethod
    def sync_event_details(self, event_id: int) -> None:
        """Sync detailed stats and lineups for a specific event."""
        ...


class ISportAnalytics(ABC):
    """Interface for sport-specific analytics."""
    
    @abstractmethod
    def get_prediction_metrics(self, event_id: int, session: Session) -> Dict[str, Any]:
        """Calculate prediction metrics for an upcoming event."""
        ...
    
    @abstractmethod
    def get_competitor_stats(self, competitor_id: int, last_n_events: int, session: Session) -> Dict[str, Any]:
        """Get aggregated stats for a competitor (team/player)."""
        ...


class ISportBettingMarkets(ABC):
    """Interface for betting market definitions."""
    
    @abstractmethod
    def get_available_markets(self) -> List[str]:
        """Return list of available betting market categories."""
        ...
    
    @abstractmethod
    def get_market_definition(self, market_key: str) -> Dict[str, Any]:
        """Get details about a specific market type."""
        ...
