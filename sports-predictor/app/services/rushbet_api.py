
import requests
import time
from typing import List, Dict, Any, Optional

class RushbetClient:
    """
    Client for interacting with Rushbet's internal API (Kambi).
    Note: This uses undocumented endpoints derived from network analysis.
    """
    
    # Base configuration derived from reverse engineering
    BASE_URL = "https://us1.offering-api.kambicdn.com/offering/v2018/rsico"
    MARKET = "CO"
    LANG = "es_ES"
    CLIENT_ID = "2" # Can be 2 or 200
    CHANNEL_ID = "1"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Origin": "https://www.rushbet.co",
            "Referer": "https://www.rushbet.co/"
        })
        
    def get_football_events(self) -> List[Dict[str, Any]]:
        """
        Fetch upcoming football events with main odds.
        """
        endpoint = f"{self.BASE_URL}/listView/football.json"
        
        params = {
            "lang": self.LANG,
            "market": self.MARKET,
            "client_id": self.CLIENT_ID,
            "channel_id": self.CHANNEL_ID,
            "nc_id": int(time.time() * 1000),
            "useCombined": "true"
        }
        
        try:
            response = self.session.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            return self._parse_events(data.get("events", []))
            
        except requests.RequestException as e:
            print(f"Error fetching Rushbet data: {e}")
            return []
            
    def _parse_events(self, raw_events: List[Dict]) -> List[Dict[str, Any]]:
        """
        Parse raw Kambi event objects into simplified dictionaries.
        """
        parsed_events = []
        
        for ev in raw_events:
            event_info = ev.get("event", {})
            offers = ev.get("betOffers", [])
            
            # Basic info
            event_id = event_info.get("id")
            name = event_info.get("name")
            start_time = event_info.get("start")
            league = "Unknown"
            
            # Extract league path
            path = event_info.get("path", [])
            if path:
                # Usually last item is league, second last is country
                league = path[-1].get("name") if path else "Unknown"
                
            # Parse 1X2 Odds (Match Winner)
            # Kambi usually puts Match Winner as the first offer, or look for criterion.id=1005906 or label "Full Time" (es: "Tiempo Reglamentario")
            odds_1x2 = {"1": None, "X": None, "2": None}
            
            for offer in offers:
                # Heuristic: Match Winner often has 3 outcomes and is closed=False
                # Filter strictly by label if possible, but "Resultado Final" or "Tiempo Reglamentario" varies
                # Let's look for the offer with 3 outcomes usually representing 1, X, 2
                outcomes = offer.get("outcomes", [])
                if len(outcomes) == 3 and not offer.get("suspended"):
                    # Assuming standard order 1, X, 2. Kambi labels are often "1", "X", "2" or Team Names
                    # We map by outcome.label or outcome.type
                    
                    for out in outcomes:
                        label = out.get("label")
                        decimal_odds = out.get("odds", 0) / 1000.0 # Kambi uses integer odds (e.g. 2500 -> 2.5)
                        
                        if label == "1" or label == event_info.get("homeName"):
                            odds_1x2["1"] = decimal_odds
                        elif label == "X" or label == "Empate":
                            odds_1x2["X"] = decimal_odds
                        elif label == "2" or label == event_info.get("awayName"):
                            odds_1x2["2"] = decimal_odds
                            
                    break # Stop after finding the first main market
            
            item = {
                "id": event_id,
                "name": name,
                "league": league,
                "start_time": start_time,
                "home_team": event_info.get("homeName"),
                "away_team": event_info.get("awayName"),
                "odds_1": odds_1x2["1"],
                "odds_x": odds_1x2["X"],
                "odds_2": odds_1x2["2"]
            }
            parsed_events.append(item)
            
        return parsed_events
