"""
Football ETL - Extract, Transform, Load for football data.
Refactored for cleaner code and better error handling.
"""
import logging
import time
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Generator
from sqlmodel import Session, select
from app.core.interfaces import ISportETL
from app.core.database import get_session
from app.sports.football.api_client import FootballAPIClient
from app.sports.football.models import (
    League, Team, Player, Coach, Fixture, TeamMatchStats, PlayerMatchStats, Injury
)

# Configure logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class FootballETL(ISportETL):
    """ETL operations for football data."""
    
    # Priority leagues by tier - single source of truth
    PRIORITY_LEAGUES = {
        "TIER_1": [2, 13, 39, 140, 135, 78, 61, 239],      # Champions, Libertadores, Top 5 Leagues, BetPlay
        "TIER_2": [3, 40, 71, 253, 262, 94, 88, 11, 128],  # Europa, Championship, Brasileirao, MLS, etc.
        "INTERNATIONAL": [1, 4, 9, 37]                      # World Cup, Euro, etc.
    }
    
    # Derived set for fast lookup
    ALLOWED_LEAGUE_IDS = set(
        league_id 
        for tier in PRIORITY_LEAGUES.values() 
        for league_id in tier
    )
    
    # Region mapping - only for whitelisted league countries
    REGION_MAP = {
        'Europe': ['England', 'Spain', 'Italy', 'Germany', 'France', 'Portugal', 'Netherlands', 'World'],
        'South America': ['Brazil', 'Argentina', 'Colombia'],
        'North America': ['USA', 'Mexico']
    }
    
    def __init__(self):
        self.api_client = FootballAPIClient()
    
    # ═══════════════════════════════════════════════════════
    # SESSION HELPERS
    # ═══════════════════════════════════════════════════════
    
    @contextmanager
    def _get_db_session(self) -> Generator[Session, None, None]:
        """Context manager for database sessions with automatic commit/rollback."""
        session = next(get_session())
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            session.close()
    
    # ═══════════════════════════════════════════════════════
    # PUBLIC SYNC METHODS
    # ═══════════════════════════════════════════════════════
    
    def sync_league_data(self, league_id: int, season: int, sync_details: bool = False) -> int:
        """
        Sync all fixtures for a league/season.
        Returns count of fixtures synced.
        """
        logger.info(f"[SYNC] League {league_id}, Season {season}")
        
        fixtures_data = self.api_client.get_events(league_id, season)
        if not fixtures_data:
            logger.warning(f"[SYNC] No fixtures returned for league {league_id}")
            return 0
        
        fixture_ids = []
        with self._get_db_session() as session:
            for fixture_data in fixtures_data:
                fixture = self._process_fixture(fixture_data, session)
                if fixture:
                    fixture_ids.append(fixture.id)
        
        logger.info(f"[SYNC] Saved {len(fixture_ids)} fixtures for league {league_id}")
        
        # Sync details if requested
        if sync_details and fixture_ids:
            self._sync_fixture_details_batch(fixture_ids)
        
        return len(fixture_ids)
    
    def sync_priority_leagues(self, season: int = 2026, sync_details: bool = False) -> Dict[str, int]:
        """Sync all priority leagues (Tier 1, 2, and International)."""
        all_ids = list(self.ALLOWED_LEAGUE_IDS)
        logger.info(f"[BATCH] Starting sync for {len(all_ids)} priority leagues")
        
        results = {"success": 0, "error": 0, "total": len(all_ids)}
        
        for league_id in all_ids:
            try:
                count = self.sync_league_data(league_id, season, sync_details)
                results["success"] += 1
                logger.info(f"[BATCH] League {league_id}: {count} fixtures")
            except Exception as e:
                logger.error(f"[BATCH] League {league_id} failed: {e}")
                results["error"] += 1
        
        return results
    
    def sync_all_leagues(self) -> int:
        """Sync league metadata for all whitelisted leagues."""
        logger.info("[CATALOG] Fetching league catalog from API")
        
        leagues_data = self.api_client.get_all_leagues()
        if not leagues_data:
            logger.warning("[CATALOG] No leagues returned from API")
            return 0
        
        count = 0
        with self._get_db_session() as session:
            for league_data in leagues_data:
                league_id = league_data.get('league', {}).get('id')
                if league_id in self.ALLOWED_LEAGUE_IDS:
                    self._process_league_full(league_data, session)
                    count += 1
        
        logger.info(f"[CATALOG] Synced {count} whitelisted leagues")
        return count
    
    def sync_injuries(self, league_id: int, season: int) -> int:
        """Sync injury data for a league/season."""
        logger.info(f"[INJURIES] League {league_id}, Season {season}")
        
        injuries_data = self.api_client.get_injuries(league_id, season)
        if not injuries_data:
            return 0
        
        with self._get_db_session() as session:
            for injury_data in injuries_data:
                self._process_injury(injury_data, league_id, season, session)
        
        logger.info(f"[INJURIES] Synced {len(injuries_data)} injuries")
        return len(injuries_data)
    
    def sync_event_details(self, event_id: int) -> None:
        """Sync detailed stats, lineups, and player stats for a fixture."""
        logger.info(f"[DETAILS] Fixture {event_id}")
        
        stats_data = self.api_client.get_event_stats(event_id)
        lineups_data = self.api_client.get_event_lineups(event_id)
        players_data = self.api_client.get_fixture_players(event_id)
        
        with self._get_db_session() as session:
            self._process_stats(event_id, stats_data, session)
            self._process_lineups(event_id, lineups_data, session)
            self._process_fixture_players(event_id, players_data, session)
    
    def cleanup_non_priority_data(self) -> Dict[str, int]:
        """Remove all leagues and fixtures not in the whitelist."""
        logger.info("[CLEANUP] Removing non-priority data")
        
        with self._get_db_session() as session:
            # Find non-whitelisted leagues
            stmt = select(League).where(League.id.not_in(self.ALLOWED_LEAGUE_IDS))
            leagues_to_delete = session.exec(stmt).all()
            league_ids = [l.id for l in leagues_to_delete]
            
            # Delete leagues
            for league in leagues_to_delete:
                session.delete(league)
            
            # Delete orphaned fixtures
            if league_ids:
                fixtures_stmt = select(Fixture).where(Fixture.league_id.in_(league_ids))
                for fix in session.exec(fixtures_stmt).all():
                    session.delete(fix)
            
            logger.info(f"[CLEANUP] Removed {len(league_ids)} leagues")
            return {"removed_leagues": len(league_ids)}
    
    # ═══════════════════════════════════════════════════════
    # PRIVATE PROCESSING METHODS
    # ═══════════════════════════════════════════════════════
    
    def _sync_fixture_details_batch(self, fixture_ids: List[int], delay: float = 0.5) -> None:
        """Batch sync fixture details with rate limiting."""
        logger.info(f"[DETAILS-BATCH] Processing {len(fixture_ids)} fixtures")
        
        for i, fid in enumerate(fixture_ids):
            try:
                self.sync_event_details(fid)
                if (i + 1) % 50 == 0:
                    logger.info(f"[DETAILS-BATCH] Progress: {i + 1}/{len(fixture_ids)}")
                time.sleep(delay)
            except Exception as e:
                logger.warning(f"[DETAILS-BATCH] Fixture {fid} failed: {e}")
    
    def _process_fixture(self, data: Dict[str, Any], session: Session) -> Optional[Fixture]:
        """Process and save a single fixture."""
        fixture_info = data.get('fixture', {})
        league_info = data.get('league', {})
        teams_info = data.get('teams', {})
        goals_info = data.get('goals', {})
        
        fixture_id = fixture_info.get('id')
        if not fixture_id:
            return None
        
        # Upsert related entities
        league = self._upsert_league(league_info, session)
        home_team = self._upsert_team(teams_info.get('home', {}), session)
        away_team = self._upsert_team(teams_info.get('away', {}), session)
        
        # Check if fixture exists
        fixture = session.get(Fixture, fixture_id)
        if not fixture:
            fixture = Fixture(
                id=fixture_id,
                date=fixture_info.get('date'),
                league_id=league.id if league else None,
                home_team_id=home_team.id if home_team else None,
                away_team_id=away_team.id if away_team else None,
                home_score=goals_info.get('home'),
                away_score=goals_info.get('away'),
                referee_name=fixture_info.get('referee')
            )
            session.add(fixture)
        
        return fixture
    
    def _upsert_league(self, data: Dict[str, Any], session: Session) -> Optional[League]:
        """Create or update a league."""
        league_id = data.get('id')
        if not league_id:
            return None
        
        league = session.get(League, league_id)
        if not league:
            league = League(
                id=league_id,
                name=data.get('name', ''),
                country=data.get('country', ''),
                season=data.get('season')
            )
            session.add(league)
        return league
    
    def _upsert_team(self, data: Dict[str, Any], session: Session) -> Optional[Team]:
        """Create or update a team."""
        team_id = data.get('id')
        if not team_id:
            return None
        
        team = session.get(Team, team_id)
        if not team:
            team = Team(
                id=team_id,
                name=data.get('name', ''),
                logo_url=data.get('logo')
            )
            session.add(team)
        return team
    
    def _upsert_player(self, data: Dict[str, Any], team_id: int, session: Session) -> Optional[Player]:
        """Create or update a player."""
        player_id = data.get('id')
        if not player_id:
            return None
        
        player = session.get(Player, player_id)
        if not player:
            player = Player(
                id=player_id,
                name=data.get('name', ''),
                position=data.get('pos') or data.get('position'),
                team_id=team_id,
                photo_url=data.get('photo')
            )
            session.add(player)
        return player
    
    def _process_league_full(self, data: Dict[str, Any], session: Session) -> None:
        """Process full league data including type and region."""
        league_info = data.get('league', {})
        league_id = league_info.get('id')
        
        if not league_id or league_id not in self.ALLOWED_LEAGUE_IDS:
            return
        
        # Skip if already exists
        if session.get(League, league_id):
            return
        
        country_info = data.get('country', {})
        country_name = country_info.get('name', '')
        region = self._get_region(country_name)
        
        # Get current season
        current_season = 2026
        for s in data.get('seasons', []):
            if s.get('current'):
                current_season = s.get('year')
                break
        
        league = League(
            id=league_id,
            name=league_info.get('name', ''),
            country=country_name,
            season=current_season,
            league_type=league_info.get('type'),
            logo_url=league_info.get('logo'),
            region=region
        )
        session.add(league)
    
    def _process_stats(self, fixture_id: int, stats_data: List, session: Session) -> None:
        """Process match statistics."""
        for team_stats in stats_data:
            team_info = team_stats.get('team', {})
            statistics = team_stats.get('statistics', [])
            stats_dict = {s.get('type'): s.get('value') for s in statistics}
            
            team_match_stats = TeamMatchStats(
                fixture_id=fixture_id,
                team_id=team_info.get('id'),
                possession=self._parse_int(str(stats_dict.get('Ball Possession', '0')).replace('%', '')),
                shots_on_goal=stats_dict.get('Shots on Goal', 0),
                total_shots=stats_dict.get('Total Shots', 0),
                corner_kicks=stats_dict.get('Corner Kicks', 0),
                fouls=stats_dict.get('Fouls', 0),
                yellow_cards=stats_dict.get('Yellow Cards', 0),
                red_cards=stats_dict.get('Red Cards', 0)
            )
            session.merge(team_match_stats)
    
    def _process_lineups(self, fixture_id: int, lineups_data: List, session: Session) -> None:
        """Process lineup data."""
        for team_lineup in lineups_data:
            team_id = team_lineup.get('team', {}).get('id')
            
            # Process players (starting XI + subs)
            for player_entry in team_lineup.get('startXI', []) + team_lineup.get('substitutes', []):
                player_info = player_entry.get('player', {})
                self._upsert_player(player_info, team_id, session)
            
            # Process coach
            coach_info = team_lineup.get('coach', {})
            if coach_info.get('id') and not session.get(Coach, coach_info.get('id')):
                session.add(Coach(id=coach_info.get('id'), name=coach_info.get('name', '')))
    
    def _process_fixture_players(self, fixture_id: int, players_data: List, session: Session) -> None:
        """Process player statistics for a fixture."""
        for team_data in players_data:
            team_id = team_data.get('team', {}).get('id')
            
            for player_entry in team_data.get('players', []):
                player_info = player_entry.get('player', {})
                stats_list = player_entry.get('statistics', [])
                
                if not player_info.get('id') or not stats_list:
                    continue
                
                self._upsert_player(player_info, team_id, session)
                
                stats = stats_list[0]
                games = stats.get('games', {})
                shots = stats.get('shots', {})
                goals_data = stats.get('goals', {})
                passes = stats.get('passes', {})
                dribbles = stats.get('dribbles', {})
                cards = stats.get('cards', {})
                
                player_match_stats = PlayerMatchStats(
                    fixture_id=fixture_id,
                    player_id=player_info.get('id'),
                    team_id=team_id,
                    minutes_played=games.get('minutes'),
                    rating=self._parse_float(games.get('rating')),
                    shots=shots.get('total'),
                    goals=goals_data.get('total'),
                    assists=goals_data.get('assists'),
                    passes_key=passes.get('key'),
                    dribbles_success=dribbles.get('success'),
                    cards_yellow=1 if cards.get('yellow') else 0,
                    cards_red=1 if cards.get('red') else 0
                )
                session.merge(player_match_stats)
    
    def _process_injury(self, data: Dict[str, Any], league_id: int, season: int, session: Session) -> None:
        """Process injury data."""
        player_info = data.get('player', {})
        team_info = data.get('team', {})
        fixture_info = data.get('fixture', {})
        
        if not player_info.get('id'):
            return
        
        self._upsert_player(player_info, team_info.get('id'), session)
        self._upsert_team(team_info, session)
        
        injury = Injury(
            player_id=player_info.get('id'),
            team_id=team_info.get('id'),
            league_id=league_id,
            season=season,
            injury_type=player_info.get('type'),
            injury_reason=player_info.get('reason'),
            date_reported=fixture_info.get('date')
        )
        session.add(injury)
    
    # ═══════════════════════════════════════════════════════
    # UTILITY METHODS
    # ═══════════════════════════════════════════════════════
    
    def _get_region(self, country: str) -> str:
        """Map country to region."""
        for region, countries in self.REGION_MAP.items():
            if country in countries:
                return region
        return 'Other'
    
    @staticmethod
    def _parse_int(value) -> int:
        """Safely parse an integer."""
        try:
            return int(value) if value else 0
        except (ValueError, TypeError):
            return 0
    
    @staticmethod
    def _parse_float(value) -> float:
        """Safely parse a float."""
        try:
            return float(value) if value else 0.0
        except (ValueError, TypeError):
            return 0.0
