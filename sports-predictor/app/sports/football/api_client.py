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

# Setup logger
logger = logging.getLogger(__name__)

API_KEY = os.getenv("API_KEY")
BASE_URL = "https://v3.football.api-sports.io"

headers = {
    'x-rapidapi-key': API_KEY,
    'x-rapidapi-host': 'v3.football.api-sports.io'
}


class FootballAPIClient(ISportAPIClient):
    """API client for football data from API-Sports."""
    
    def get_events(self, league_id: int, season: int) -> List[Dict[str, Any]]:
        """
        Fetch fixtures for a league and season.
        """
        logger.info(f"Fetching fixtures for league {league_id}, season {season}")
        url = f"{BASE_URL}/fixtures"
        params = {'league': league_id, 'season': season}
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json().get('response', [])
        logger.info(f"Successfully fetched {len(data)} fixtures")
        return data
    
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
