"""
Base models for all sports.
Each sport extends these abstract classes with sport-specific fields.
"""
from abc import ABC
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class BaseEvent(SQLModel):
    """
    Abstract base class for events (matches/games).
    Football: Fixture, Basketball: Game, etc.
    """
    id: int = Field(primary_key=True)
    date: datetime
    status: Optional[str] = None  # scheduled, live, finished, postponed


class BaseCompetitor(SQLModel):
    """
    Abstract base class for competitors (teams or individuals).
    """
    id: int = Field(primary_key=True)
    name: str
    logo_url: Optional[str] = None


class BaseLeague(SQLModel):
    """
    Abstract base class for leagues/competitions.
    """
    id: int = Field(primary_key=True)
    name: str
    country: Optional[str] = None
    season: Optional[int] = None


class BasePlayer(SQLModel):
    """
    Abstract base class for players/participants.
    """
    id: int = Field(primary_key=True)
    name: str
    position: Optional[str] = None


class BaseEventStats(SQLModel):
    """
    Abstract base class for event statistics.
    Each sport defines its own stat types.
    """
    event_id: int = Field(primary_key=True)
