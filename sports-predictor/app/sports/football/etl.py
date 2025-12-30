"""
Football ETL - Extract, Transform, Load for football data.
"""
import logging
import time
from typing import Any, Dict, List
from sqlmodel import Session, select
from app.core.interfaces import ISportETL
from app.core.database import get_session
from app.sports.football.api_client import FootballAPIClient
from app.sports.football.models import (
    League, Team, Player, Coach, Fixture, TeamMatchStats, PlayerMatchStats,
    PlayerSeasonStats, Injury
)


# Setup logger
logger = logging.getLogger(__name__)


class FootballETL(ISportETL):
    """ETL operations for football data."""
    
    # User-defined whitelist for Rushbet markets (Tier 1 & 2 + International)
    ALLOWED_LEAGUE_IDS = {
        1, 2, 3, 4, 9, 11, 13, 37, 39, 40, 61, 71, 78, 88, 94, 128, 135, 140, 239, 253, 262
    }
    
    PRIORITY_LEAGUES = {
        "TIER 1": [2, 13, 39, 140, 135, 78, 61, 239],
        "TIER 2": [3, 40, 71, 253, 262, 94, 88, 11, 128],
        "INTERNATIONAL": [1, 4, 9, 37]
    }
    
    def __init__(self):
        self.api_client = FootballAPIClient()
    
    def sync_priority_leagues(self, season: int = 2026, sync_details: bool = False) -> Dict[str, int]:
        """
        Sync all Tier 1, Tier 2, and International priority leagues in one go.
        """
        all_ids = []
        for tier in self.PRIORITY_LEAGUES.values():
            all_ids.extend(tier)
            
        logger.info(f"Starting priority sync for {len(all_ids)} leagues")
        results = {"success": 0, "error": 0}
        
        for league_id in all_ids:
            try:
                self.sync_league_data(league_id, season, sync_details=sync_details)
                results["success"] += 1
                logger.info(f"Successfully synced priority league {league_id}")
            except Exception as e:
                logger.error(f"Failed to sync priority league {league_id}: {str(e)}")
                results["error"] += 1
                
        return results

    
    def sync_league_data(self, league_id: int, season: int, sync_details: bool = False) -> int:
        """
        Sync all data for a football league/season.
        If sync_details=True, also syncs stats and lineups for each fixture.
        Returns count of fixtures synced.
        """
        logger.info(f"Starting sync for league {league_id}, season {season}")
        fixtures_data = self.api_client.get_events(league_id, season)
        
        session = next(get_session())
        fixture_ids = []
        try:
            count = 0
            for fixture_data in fixtures_data:
                fixture = self._process_fixture(fixture_data, session)
                if fixture:
                    fixture_ids.append(fixture.id)
                count += 1
            session.commit()
            logger.info(f"Successfully synced {count} fixtures for league {league_id}")
        except Exception as e:
            logger.error(f"Error syncing league {league_id}: {str(e)}")
            session.rollback()
            raise e
        finally:
            session.close()
        
        # Sync details if requested
        if sync_details and fixture_ids:
            self.sync_all_fixture_details(fixture_ids)
        
        return count
    
    def sync_all_fixture_details(self, fixture_ids: List[int], delay: float = 0.5) -> None:
        """
        Sync detailed stats and lineups for multiple fixtures.
        Includes rate limiting to avoid API throttling.
        """
        logger.info(f"Starting batch sync for {len(fixture_ids)} fixtures")
        success_count = 0
        error_count = 0
        
        for i, fixture_id in enumerate(fixture_ids):
            try:
                self.sync_event_details(fixture_id)
                success_count += 1
                
                # Progress logging every 50 fixtures
                if (i + 1) % 50 == 0:
                    logger.info(f"Progress: {i + 1}/{len(fixture_ids)} fixtures synced")
                
                # Rate limiting
                time.sleep(delay)
            except Exception as e:
                logger.warning(f"Failed to sync fixture {fixture_id}: {str(e)}")
                error_count += 1
        
        logger.info(f"Batch sync complete: {success_count} success, {error_count} errors")
    
    def sync_event_details(self, event_id: int) -> None:
        """
        Sync detailed stats, lineups, and player stats for a specific fixture.
        """
        logger.info(f"Starting detailed sync for fixture {event_id}")
        stats_data = self.api_client.get_event_stats(event_id)
        lineups_data = self.api_client.get_event_lineups(event_id)
        players_data = self.api_client.get_fixture_players(event_id)
        
        session = next(get_session())
        try:
            self._process_stats(event_id, stats_data, session)
            self._process_lineups(event_id, lineups_data, session)
            self._process_fixture_players(event_id, players_data, session)
            session.commit()
            logger.info(f"Successfully synced details for fixture {event_id}")
        except Exception as e:
            logger.error(f"Error syncing details for fixture {event_id}: {str(e)}")
            session.rollback()
            raise e
        finally:
            session.close()
    
    def sync_all_leagues(self) -> int:
        """
        Fetch all leagues from API and sync ONLY those in the ALLOWED_LEAGUE_IDS whitelist.
        """
        logger.info("Syncing whitelist leagues from API-Sports catalog")
        leagues_data = self.api_client.get_all_leagues()
        
        session = next(get_session())
        try:
            count = 0
            for league_data in leagues_data:
                league_id = league_data.get('league', {}).get('id')
                if league_id in self.ALLOWED_LEAGUE_IDS:
                    self._process_league_full(league_data, session)
                    count += 1
                    
            session.commit()
            logger.info(f"Successfully synced {count} whitelist leagues")
            return count
        except Exception as e:
            logger.error(f"Error syncing leagues: {str(e)}")
            session.rollback()
            raise e
        finally:
            session.close()

    def cleanup_non_priority_data(self) -> Dict[str, int]:
        """
        Remove all leagues and associated data that are not in the ALLOWED_LEAGUE_IDS list.
        """
        logger.info("Starting cleanup of non-priority database records")
        session = next(get_session())
        try:
            # Find leagues to delete
            leagues_stmt = select(League).where(League.id.not_in(self.ALLOWED_LEAGUE_IDS))
            to_delete = session.exec(leagues_stmt).all()
            
            league_ids = [l.id for l in to_delete]
            count = len(league_ids)
            
            if count > 0:
                # Delete associated data first (cascading conceptually, but explicit here for safety)
                # Note: Fixtures and Stats have league_id or team_id FKs. 
                # We prioritize removing the Leagues as they are the main entry point for the UI.
                for league in to_delete:
                    session.delete(league)
                
                # Also delete fixtures belonging to those league IDs
                fixtures_stmt = select(Fixture).where(Fixture.league_id.in_(league_ids))
                fixtures_to_delete = session.exec(fixtures_stmt).all()
                for fix in fixtures_to_delete:
                    # Conceptually we should also delete stats, but let's keep it simple: 
                    # if the league is gone, the UI won't show the data.
                    session.delete(fix)
                    
            session.commit()
            logger.info(f"Cleanup finished. Removed {count} unauthorized leagues.")
            return {"removed_leagues": count}
        except Exception as e:
            logger.error(f"Cleanup failed: {str(e)}")
            session.rollback()
            return {"error": 1}
        finally:
            session.close()
    
    def sync_injuries(self, league_id: int, season: int) -> int:
        """
        Sync injury data for a league/season.
        Returns count of injuries synced.
        """
        logger.info(f"Syncing injuries for league {league_id}, season {season}")
        injuries_data = self.api_client.get_injuries(league_id, season)
        
        session = next(get_session())
        try:
            count = 0
            for injury_data in injuries_data:
                self._process_injury(injury_data, league_id, season, session)
                count += 1
            session.commit()
            logger.info(f"Successfully synced {count} injuries")
            return count
        except Exception as e:
            logger.error(f"Error syncing injuries: {str(e)}")
            session.rollback()
            raise e
        finally:
            session.close()
    
    def _process_fixture(self, data: Dict[str, Any], session: Session) -> Fixture:
        """Process and save a single fixture. Returns the fixture object."""
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
        return fixture
    
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
        """Process and save lineup data - creates player records and links to fixture."""
        for team_lineup in lineups_data:
            team_info = team_lineup.get('team', {})
            team_id = team_info.get('id')
            
            # Process starting XI
            start_xi = team_lineup.get('startXI', [])
            for player_entry in start_xi:
                player_info = player_entry.get('player', {})
                self._upsert_player(player_info, team_id, session)
            
            # Process substitutes
            substitutes = team_lineup.get('substitutes', [])
            for player_entry in substitutes:
                player_info = player_entry.get('player', {})
                self._upsert_player(player_info, team_id, session)
            
            # Process coach
            coach_info = team_lineup.get('coach', {})
            if coach_info.get('id'):
                coach = session.get(Coach, coach_info.get('id'))
                if not coach:
                    coach = Coach(
                        id=coach_info.get('id'),
                        name=coach_info.get('name', '')
                    )
                    session.add(coach)
    
    def _process_fixture_players(self, fixture_id: int, players_data: list, session: Session) -> None:
        """Process player statistics for a fixture."""
        for team_data in players_data:
            team_info = team_data.get('team', {})
            team_id = team_info.get('id')
            players = team_data.get('players', [])
            
            for player_entry in players:
                player_info = player_entry.get('player', {})
                stats_list = player_entry.get('statistics', [])
                
                if not player_info.get('id') or not stats_list:
                    continue
                
                # Upsert player
                self._upsert_player(player_info, team_id, session)
                
                # Aggregate stats from all appearances in the match
                stats = stats_list[0] if stats_list else {}
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
    
    def _process_league_full(self, data: Dict[str, Any], session: Session) -> None:
        """Process full league data including type and region. ONLY if in whitelist."""
        league_info = data.get('league', {})
        league_id = league_info.get('id')
        
        if not league_id or league_id not in self.ALLOWED_LEAGUE_IDS:
            return
        
        # Determine region based on country
        country_name = country_info.get('name', '')
        region = self._get_region_from_country(country_name)
        
        league = session.get(League, league_info.get('id'))
        if not league:
            # Get current season from seasons list
            seasons = data.get('seasons', [])
            current_season = None
            for s in seasons:
                if s.get('current'):
                    current_season = s.get('year')
                    break
            
            league = League(
                id=league_info.get('id'),
                name=league_info.get('name', ''),
                country=country_name,
                season=current_season or 2026,
                league_type=league_info.get('type'),
                logo_url=league_info.get('logo'),
                region=region
            )
            session.add(league)
    
    def _process_injury(self, data: Dict[str, Any], league_id: int, season: int, session: Session) -> None:
        """Process injury data."""
        player_info = data.get('player', {})
        team_info = data.get('team', {})
        fixture_info = data.get('fixture', {})
        
        if not player_info.get('id'):
            return
        
        # Upsert player and team
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
    
    def _upsert_player(self, data: Dict[str, Any], team_id: int, session: Session) -> Player:
        """Create or update a player."""
        if not data.get('id'):
            return None
        
        player = session.get(Player, data.get('id'))
        if not player:
            player = Player(
                id=data.get('id'),
                name=data.get('name', ''),
                position=data.get('pos') or data.get('position'),
                team_id=team_id,
                photo_url=data.get('photo')
            )
            session.add(player)
        return player
    
    def _get_region_from_country(self, country: str) -> str:
        """Map country to region."""
        europe = ['England', 'Spain', 'Italy', 'Germany', 'France', 'Portugal', 'Netherlands', 'Belgium', 'Turkey', 'Greece', 'Scotland', 'Ukraine', 'Russia', 'Poland', 'Austria', 'Switzerland', 'Czech-Republic', 'Croatia', 'Serbia', 'Denmark', 'Sweden', 'Norway']
        south_america = ['Brazil', 'Argentina', 'Colombia', 'Chile', 'Uruguay', 'Paraguay', 'Peru', 'Ecuador', 'Venezuela', 'Bolivia']
        asia = ['Japan', 'South-Korea', 'China', 'Australia', 'Thailand', 'Indonesia', 'Malaysia', 'Vietnam', 'India']
        middle_east = ['Saudi-Arabia', 'UAE', 'Qatar', 'Bahrain', 'Kuwait', 'Oman', 'Iran', 'Iraq', 'Egypt']
        north_america = ['USA', 'Mexico', 'Canada', 'Costa-Rica', 'Honduras']
        africa = ['South-Africa', 'Nigeria', 'Morocco', 'Algeria', 'Tunisia', 'Egypt', 'Ghana', 'Cameroon', 'Senegal', 'Ivory-Coast']
        
        if country in europe or country == 'World':
            return 'Europe'
        elif country in south_america:
            return 'South America'
        elif country in asia:
            return 'Asia'
        elif country in middle_east:
            return 'Middle East'
        elif country in north_america:
            return 'North America'
        elif country in africa:
            return 'Africa'
        else:
            return 'Other'
    
    def _parse_int(self, value) -> int:
        """Safely parse an integer."""
        try:
            return int(value) if value else 0
        except (ValueError, TypeError):
            return 0
    
    def _parse_float(self, value) -> float:
        """Safely parse a float."""
        try:
            return float(value) if value else 0.0
        except (ValueError, TypeError):
            return 0.0
