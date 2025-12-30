"""
Football ETL - Extract, Transform, Load for football data.
"""
import logging
from typing import Any, Dict
from sqlmodel import Session
from app.core.interfaces import ISportETL
from app.core.database import get_session
from app.sports.football.api_client import FootballAPIClient
from app.sports.football.models import (
    League, Team, Player, Coach, Fixture, TeamMatchStats, PlayerMatchStats
)


# Setup logger
logger = logging.getLogger(__name__)


class FootballETL(ISportETL):
    """ETL operations for football data."""
    
    def __init__(self):
        self.api_client = FootballAPIClient()
    
    def sync_league_data(self, league_id: int, season: int) -> None:
        """
        Sync all data for a football league/season.
        """
        logger.info(f"Starting sync for league {league_id}, season {season}")
        fixtures_data = self.api_client.get_events(league_id, season)
        
        session = next(get_session())
        try:
            count = 0
            for fixture_data in fixtures_data:
                self._process_fixture(fixture_data, session)
                count += 1
            session.commit()
            logger.info(f"Successfully synced {count} fixtures for league {league_id}")
        except Exception as e:
            logger.error(f"Error syncing league {league_id}: {str(e)}")
            session.rollback()
            raise e
        finally:
            session.close()
    
    def sync_event_details(self, event_id: int) -> None:
        """
        Sync detailed stats and lineups for a specific fixture.
        """
        logger.info(f"Starting detailed sync for fixture {event_id}")
        stats_data = self.api_client.get_event_stats(event_id)
        lineups_data = self.api_client.get_event_lineups(event_id)
        
        session = next(get_session())
        try:
            self._process_stats(event_id, stats_data, session)
            self._process_lineups(event_id, lineups_data, session)
            session.commit()
            logger.info(f"Successfully synced details for fixture {event_id}")
        except Exception as e:
            logger.error(f"Error syncing details for fixture {event_id}: {str(e)}")
            session.rollback()
            raise e
        finally:
            session.close()
    
    def _process_fixture(self, data: Dict[str, Any], session: Session) -> None:
        """Process and save a single fixture."""
        # Extract fixture info
        fixture_info = data.get('fixture', {})
        league_info = data.get('league', {})
        teams_info = data.get('teams', {})
        goals_info = data.get('goals', {})
        
        # Upsert league
        league = self._upsert_league(league_info, session)
        
        # Upsert teams
        home_team = self._upsert_team(teams_info.get('home', {}), session)
        away_team = self._upsert_team(teams_info.get('away', {}), session)
        
        # Create or update fixture
        fixture = session.get(Fixture, fixture_info.get('id'))
        if not fixture:
            fixture = Fixture(
                id=fixture_info.get('id'),
                date=fixture_info.get('date'),
                league_id=league.id if league else None,
                home_team_id=home_team.id if home_team else None,
                away_team_id=away_team.id if away_team else None,
                home_score=goals_info.get('home'),
                away_score=goals_info.get('away'),
                referee_name=fixture_info.get('referee')
            )
            session.add(fixture)
    
    def _upsert_league(self, data: Dict[str, Any], session: Session) -> League:
        """Create or update a league."""
        if not data.get('id'):
            return None
        
        league = session.get(League, data.get('id'))
        if not league:
            league = League(
                id=data.get('id'),
                name=data.get('name', ''),
                country=data.get('country', ''),
                season=data.get('season')
            )
            session.add(league)
        return league
    
    def _upsert_team(self, data: Dict[str, Any], session: Session) -> Team:
        """Create or update a team."""
        if not data.get('id'):
            return None
        
        team = session.get(Team, data.get('id'))
        if not team:
            team = Team(
                id=data.get('id'),
                name=data.get('name', ''),
                logo_url=data.get('logo')
            )
            session.add(team)
        return team
    
    def _process_stats(self, fixture_id: int, stats_data: list, session: Session) -> None:
        """Process and save match statistics."""
        for team_stats in stats_data:
            team_info = team_stats.get('team', {})
            statistics = team_stats.get('statistics', [])
            
            # Convert list of stats to dict
            stats_dict = {s.get('type'): s.get('value') for s in statistics}
            
            team_match_stats = TeamMatchStats(
                fixture_id=fixture_id,
                team_id=team_info.get('id'),
                possession=self._parse_int(stats_dict.get('Ball Possession', '0%').replace('%', '')),
                shots_on_goal=stats_dict.get('Shots on Goal', 0),
                total_shots=stats_dict.get('Total Shots', 0),
                corner_kicks=stats_dict.get('Corner Kicks', 0),
                fouls=stats_dict.get('Fouls', 0),
                yellow_cards=stats_dict.get('Yellow Cards', 0),
                red_cards=stats_dict.get('Red Cards', 0)
            )
            session.merge(team_match_stats)
    
    def _process_lineups(self, fixture_id: int, lineups_data: list, session: Session) -> None:
        """Process and save lineup data."""
        # TODO: Implement lineup processing
        pass
    
    def _parse_int(self, value) -> int:
        """Safely parse an integer."""
        try:
            return int(value) if value else 0
        except (ValueError, TypeError):
            return 0
