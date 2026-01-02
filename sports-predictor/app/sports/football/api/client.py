"""
Football API Client - Integration with API-Sports.
"""
import os
import requests
import logging
from typing import Any, Dict, List
from dotenv import load_dotenv
from app.core.interfaces import ISportAPIClient

load_dotenv()

# Setup logger with visible output
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

API_KEY = os.getenv("API_KEY")
BASE_URL = "https://v3.football.api-sports.io"

# Log API key status on module load
if API_KEY:
    masked_key = API_KEY[:4] + "..." + API_KEY[-4:] if len(API_KEY) > 8 else "***"
    logger.info(f"API Key loaded: {masked_key}")
else:
    logger.warning("API_KEY environment variable is NOT SET!")

headers = {
    'x-rapidapi-key': API_KEY or '',
    'x-rapidapi-host': 'v3.football.api-sports.io'
}


class FootballAPIClient(ISportAPIClient):
    """API client for football data from API-Sports."""
    
    def get_events(self, league_id: int, season: int) -> List[Dict[str, Any]]:
        """
        Fetch fixtures for a league and season.
        """
        logger.info(f"[API-GET] Fixtures: league={league_id}, season={season}")
        url = f"{BASE_URL}/fixtures"
        params = {'league': league_id, 'season': season}
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            logger.info(f"[API-RESPONSE] Status: {response.status_code}")
            
            if response.status_code == 401:
                logger.error("API Key is invalid or expired!")
                return []
            
            response.raise_for_status()
            json_data = response.json()
            
            # Log API errors if present
            if json_data.get('errors'):
                logger.error(f"[API-ERROR] {json_data.get('errors')}")
                return []
            
            data = json_data.get('response', [])
            logger.info(f"[API-SUCCESS] Fetched {len(data)} fixtures")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"[API-EXCEPTION] {type(e).__name__}: {e}")
            return []
    
    def get_event_stats(self, event_id: int) -> List[Dict[str, Any]]:
        """
        Fetch statistics for a specific fixture.
        """
        logger.info(f"Fetching stats for fixture {event_id}")
        url = f"{BASE_URL}/fixtures/statistics"
        params = {'fixture': event_id}
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json().get('response', [])
        logger.info(f"Successfully fetched stats for {len(data)} teams in fixture {event_id}")
        return data
    
    def get_event_lineups(self, event_id: int) -> List[Dict[str, Any]]:
        """
        Fetch lineups for a specific fixture.
        """
        logger.info(f"Fetching lineups for fixture {event_id}")
        url = f"{BASE_URL}/fixtures/lineups"
        params = {'fixture': event_id}
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json().get('response', [])
        logger.info(f"Successfully fetched lineups for {len(data)} teams in fixture {event_id}")
        return data
    
    def get_leagues(self, country: str = None) -> List[Dict[str, Any]]:
        """
        Fetch available leagues, optionally filtered by country.
        """
        url = f"{BASE_URL}/leagues"
        params = {}
        if country:
            params['country'] = country
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json().get('response', [])
    
    def get_teams(self, league_id: int, season: int) -> List[Dict[str, Any]]:
        """
        Fetch teams for a league and season.
        """
        url = f"{BASE_URL}/teams"
        params = {'league': league_id, 'season': season}
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json().get('response', [])
    
    def get_all_leagues(self) -> List[Dict[str, Any]]:
        """
        Fetch ALL available leagues from API-Sports.
        Returns list with league info including country, type, and seasons.
        """
        logger.info("Fetching all available leagues")
        url = f"{BASE_URL}/leagues"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json().get('response', [])
        logger.info(f"Successfully fetched {len(data)} leagues")
        return data
    
    def get_injuries(self, league_id: int, season: int) -> List[Dict[str, Any]]:
        """
        Fetch injuries for a league and season.
        Returns player injuries with type, date, and expected return.
        """
        logger.info(f"Fetching injuries for league {league_id}, season {season}")
        url = f"{BASE_URL}/injuries"
        params = {'league': league_id, 'season': season}
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json().get('response', [])
        logger.info(f"Successfully fetched {len(data)} injury records")
        return data
    
    def get_players(self, team_id: int, season: int) -> List[Dict[str, Any]]:
        """
        Fetch all players for a team in a season.
        Includes statistics like goals, assists, xG, xA.
        """
        logger.info(f"Fetching players for team {team_id}, season {season}")
        url = f"{BASE_URL}/players"
        params = {'team': team_id, 'season': season}
        all_players = []
        page = 1
        
        while True:
            params['page'] = page
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            result = response.json()
            data = result.get('response', [])
            all_players.extend(data)
            
            # Check pagination
            paging = result.get('paging', {})
            if page >= paging.get('total', 1):
                break
            page += 1
        
        logger.info(f"Successfully fetched {len(all_players)} players for team {team_id}")
        return all_players
    
    def get_predictions(self, fixture_id: int) -> Dict[str, Any]:
        """
        Fetch pre-match predictions including probable lineup.
        Available ~24-48h before kickoff.
        """
        logger.info(f"Fetching predictions for fixture {fixture_id}")
        url = f"{BASE_URL}/predictions"
        params = {'fixture': fixture_id}
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json().get('response', [])
        logger.info(f"Successfully fetched predictions for fixture {fixture_id}")
        return data[0] if data else {}
    
    def get_fixture_players(self, fixture_id: int) -> List[Dict[str, Any]]:
        """
        Fetch player statistics for a specific fixture.
        Includes goals, assists, rating, minutes played.
        """
        logger.info(f"Fetching player stats for fixture {fixture_id}")
        url = f"{BASE_URL}/fixtures/players"
        params = {'fixture': fixture_id}
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json().get('response', [])
        logger.info(f"Successfully fetched player stats for {len(data)} teams in fixture {fixture_id}")
        return data

    def get_team_fixtures(self, team_id: int, last_n: int = 20) -> List[Dict[str, Any]]:
        """
        Fetch last N played fixtures for a specific team.
        Only returns finished matches (status = 'FT').
        
        Args:
            team_id: ID del equipo
            last_n: Número de últimos partidos a obtener
            
        Returns:
            Lista de fixtures ordenados del más reciente al más antiguo
        """
        logger.info(f"[API-GET] Team Fixtures: team={team_id}, last={last_n}")
        url = f"{BASE_URL}/fixtures"
        params = {
            'team': team_id,
            'last': last_n,
            'status': 'FT'  # Solo partidos finalizados
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            logger.info(f"[API-RESPONSE] Status: {response.status_code}")
            
            if response.status_code == 401:
                logger.error("API Key is invalid or expired!")
                return []
            
            response.raise_for_status()
            json_data = response.json()
            
            if json_data.get('errors'):
                logger.error(f"[API-ERROR] {json_data.get('errors')}")
                return []
            
            data = json_data.get('response', [])
            logger.info(f"[API-SUCCESS] Fetched {len(data)} fixtures for team {team_id}")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"[API-EXCEPTION] {type(e).__name__}: {e}")
            return []
