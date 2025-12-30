"""
Sport Registry - Central hub for discovering and loading sport modules.
"""
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Type


@dataclass
class SportConfig:
    """Configuration for a registered sport."""
    key: str                           # e.g., "football", "basketball"
    name: str                          # e.g., "Fútbol", "Baloncesto"
    icon: str                          # e.g., "⚽", "🏀"
    api_client_class: Type             # Class implementing ISportAPIClient
    etl_class: Type                    # Class implementing ISportETL
    analytics_class: Type              # Class implementing ISportAnalytics
    models: List[Type]                 # List of SQLModel classes for this sport
    betting_markets: Optional[Type] = None  # Class implementing ISportBettingMarkets
    ui_views: Dict[str, Callable] = field(default_factory=dict)  # {"dashboard": show_dashboard, ...}


class SportRegistry:
    """
    Singleton registry for all available sports.
    Sports auto-register themselves when their module is imported.
    """
    _instance = None
    _sports: Dict[str, SportConfig] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def register(cls, config: SportConfig) -> None:
        """Register a new sport configuration."""
        cls._sports[config.key] = config
        print(f"✓ Registered sport: {config.name} ({config.icon})")
    
    @classmethod
    def get(cls, key: str) -> Optional[SportConfig]:
        """Get a sport configuration by key."""
        return cls._sports.get(key)
    
    @classmethod
    def list_sports(cls) -> List[SportConfig]:
        """Get all registered sports."""
        return list(cls._sports.values())
    
    @classmethod
    def get_sport_options(cls) -> Dict[str, str]:
        """Get dict of {display_name: key} for UI dropdowns."""
        return {f"{s.icon} {s.name}": s.key for s in cls._sports.values()}
    
    @classmethod
    def get_all_models(cls) -> List[Type]:
        """Get all models from all registered sports (for DB init)."""
        all_models = []
        for sport in cls._sports.values():
            all_models.extend(sport.models)
        return all_models


# Convenience function for sport registration decorator
def register_sport(config: SportConfig):
    """Decorator/function to register a sport on module load."""
    SportRegistry.register(config)
    return config
