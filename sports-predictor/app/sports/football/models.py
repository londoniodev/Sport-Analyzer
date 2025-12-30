"""
Football Models - Database models specific to football/soccer.
"""
from typing import Optional
from sqlmodel import Field, Relationship, SQLModel
from datetime import datetime


class League(SQLModel, table=True):
    """Football league/competition."""
    __tablename__ = "football_league"
    
    id: int = Field(primary_key=True)
    name: str
    country: str
    season: int


class Team(SQLModel, table=True):
    """Football team."""
    __tablename__ = "football_team"
    
    id: int = Field(primary_key=True)
    name: str
    logo_url: Optional[str] = None


class Player(SQLModel, table=True):
    """Football player."""
    __tablename__ = "football_player"
    
    id: int = Field(primary_key=True)
    name: str
    position: Optional[str] = None
    team_id: Optional[int] = Field(default=None, foreign_key="football_team.id")


class Coach(SQLModel, table=True):
    """Football coach/manager."""
    __tablename__ = "football_coach"
    
    id: int = Field(primary_key=True)
    name: str


class Fixture(SQLModel, table=True):
    """Football match/fixture."""
    __tablename__ = "football_fixture"
    
    id: int = Field(primary_key=True)
    date: datetime
    league_id: int = Field(foreign_key="football_league.id")
    home_team_id: int = Field(foreign_key="football_team.id")
    away_team_id: int = Field(foreign_key="football_team.id")
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    referee_name: Optional[str] = None
    home_coach_id: Optional[int] = Field(default=None, foreign_key="football_coach.id")
    away_coach_id: Optional[int] = Field(default=None, foreign_key="football_coach.id")

    # Relationships
    league: Optional["League"] = Relationship(
        sa_relationship_kwargs={'foreign_keys': '[Fixture.league_id]'}
    )
    home_team: Optional["Team"] = Relationship(
        sa_relationship_kwargs={'foreign_keys': '[Fixture.home_team_id]'}
    )
    away_team: Optional["Team"] = Relationship(
        sa_relationship_kwargs={'foreign_keys': '[Fixture.away_team_id]'}
    )
    home_coach: Optional["Coach"] = Relationship(
        sa_relationship_kwargs={'foreign_keys': '[Fixture.home_coach_id]'}
    )
    away_coach: Optional["Coach"] = Relationship(
        sa_relationship_kwargs={'foreign_keys': '[Fixture.away_coach_id]'}
    )


class TeamMatchStats(SQLModel, table=True):
    """Team statistics for a specific match."""
    __tablename__ = "football_team_match_stats"
    
    fixture_id: int = Field(primary_key=True, foreign_key="football_fixture.id")
    team_id: int = Field(primary_key=True, foreign_key="football_team.id")
    possession: Optional[int] = None
    shots_on_goal: Optional[int] = None
    total_shots: Optional[int] = None
    corner_kicks: Optional[int] = None
    fouls: Optional[int] = None
    yellow_cards: Optional[int] = None
    red_cards: Optional[int] = None

    # Relationships
    fixture: Optional["Fixture"] = Relationship()
    team: Optional["Team"] = Relationship()


class PlayerMatchStats(SQLModel, table=True):
    """Player statistics for a specific match."""
    __tablename__ = "football_player_match_stats"
    
    fixture_id: int = Field(primary_key=True, foreign_key="football_fixture.id")
    player_id: int = Field(primary_key=True, foreign_key="football_player.id")
    team_id: int = Field(foreign_key="football_team.id")
    minutes_played: Optional[int] = None
    rating: Optional[float] = None
    shots: Optional[int] = None
    passes_key: Optional[int] = None
    dribbles_success: Optional[int] = None
    cards_yellow: Optional[int] = None
    cards_red: Optional[int] = None

    # Relationships
    fixture: Optional["Fixture"] = Relationship()
    player: Optional["Player"] = Relationship()
    team: Optional["Team"] = Relationship()
