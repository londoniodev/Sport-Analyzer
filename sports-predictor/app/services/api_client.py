import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")
BASE_URL = "https://v3.football.api-sports.io"

headers = {
    'x-rapidapi-key': API_KEY,
    'x-rapidapi-host': 'v3.football.api-sports.io'
}

def get_fixtures(league_id: int, season: int):
    """
    Obtiene los partidos para una liga y temporada específicas.
    """
    url = f"{BASE_URL}/fixtures"
    params = {'league': league_id, 'season': season}
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()['response']

def get_fixture_lineups(fixture_id: int):
    """
    Obtiene las alineaciones para un partido específico.
    """
    url = f"{BASE_URL}/fixtures/lineups"
    params = {'fixture': fixture_id}
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()['response']

def get_fixture_stats(fixture_id: int):
    """
    Obtiene las estadísticas para un partido específico.
    """
    url = f"{BASE_URL}/fixtures/statistics"
    params = {'fixture': fixture_id}
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()['response']
