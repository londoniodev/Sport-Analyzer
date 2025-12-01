from typing import List, Optional
from sqlmodel import Field, Relationship, SQLModel
from datetime import datetime

class League(SQLModel, table=True):
    id: int = Field(primary_key=True)
    name: str
    country: str
    season: int

class Team(SQLModel, table=True):
    id: int = Field(primary_key=True)
    name: str
    logo_url: str

class Player(SQLModel, table=True):
    id: int = Field(primary_key=True)
    name: str
    position: Optional[str] = None

class Coach(SQLModel, table=True):
    id: int = Field(primary_key=True)
    name: str

class Fixture(SQLModel, table=True):
    id: int = Field(primary_key=True)
    date: datetime
    league_id: int = Field(foreign_key="league.id")
    home_team_id: int = Field(foreign_key="team.id")
    away_team_id: int = Field(foreign_key="team.id")
    home_score: int
    away_score: int
    referee_name: Optional[str] = None
    home_coach_id: int = Field(foreign_key="coach.id")
    away_coach_id: int = Field(foreign_key="coach.id")

    league: "League" = Relationship()
    home_team: "Team" = Relationship(sa_relationship_kwargs={'foreign_keys': '[Fixture.home_team_id]'})
    away_team: "Team" = Relationship(sa_relationship_kwargs={'foreign_keys': '[Fixture.away_team_id]'})
    home_coach: "Coach" = Relationship(sa_relationship_kwargs={'foreign_keys': '[Fixture.home_coach_id]'})
    away_coach: "Coach" = Relationship(sa_relationship_kwargs={'foreign_keys': '[Fixture.away_coach_id]'})

class TeamMatchStats(SQLModel, table=True):
    fixture_id: int = Field(primary_key=True, foreign_key="fixture.id")
    team_id: int = Field(primary_key=True, foreign_key="team.id")
    possession: int
    shots_on_goal: int
    total_shots: int
    corner_kicks: int
    fouls: int
    yellow_cards: int
    red_cards: int

    fixture: "Fixture" = Relationship()
    team: "Team" = Relationship()

class PlayerMatchStats(SQLModel, table=True):
    fixture_id: int = Field(primary_key=True, foreign_key="fixture.id")
    player_id: int = Field(primary_key=True, foreign_key="player.id")
    team_id: int = Field(foreign_key="team.id")
    minutes_played: int
    rating: float
    shots: int
    passes_key: int
    dribbles_success: int
    cards_yellow: int
    cards_red: int

    fixture: "Fixture" = Relationship()
    player: "Player" = Relationship()
    team: "Team" = Relationship()
