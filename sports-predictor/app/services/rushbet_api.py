
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
    
    # Patrones para identificar y excluir ligas de eSports
    ESPORTS_PATTERNS = [
        "esport", "iesport", "cyber", "battle", "batalla", 
        "2x6min", "2x5min", "2x4min", "2x3min", "simulated"
    ]
    
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
            
    def _is_esports(self, text: str) -> bool:
        """
        Verifica si el texto contiene patrones de eSports.
        """
        if not text:
            return False
        text_lower = text.lower()
        return any(pattern in text_lower for pattern in self.ESPORTS_PATTERNS)
    
    def _parse_events(self, raw_events: List[Dict]) -> List[Dict[str, Any]]:
        """
        Parse raw Kambi event objects into simplified dictionaries.
        Excluye automáticamente eventos de eSports.
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
            
            # Excluir eSports verificando nombre del evento y liga
            if self._is_esports(name) or self._is_esports(league):
                continue
                
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
    
    def get_event_details(self, event_id: int) -> Optional[Dict[str, Any]]:
        """Obtiene todos los mercados de apuestas disponibles para un evento específico."""
        endpoint = f"{self.BASE_URL}/betoffer/event/{event_id}.json"
        
        params = {
            "lang": self.LANG,
            "market": self.MARKET,
            "client_id": self.CLIENT_ID,
            "channel_id": self.CHANNEL_ID,
            "nc_id": int(time.time() * 1000)
        }
        
        try:
            response = self.session.get(endpoint, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            return self._parse_event_details(data)
        except requests.RequestException as e:
            print(f"Error fetching event details: {e}")
            return None
    
    def _parse_event_details(self, data: Dict) -> Dict[str, Any]:
        """Parsea datos completos de un evento con categorización detallada."""
        offers = data.get("betOffers", [])
        event_info = data.get("events", [{}])[0] if data.get("events") else {}
        
        home_team = event_info.get("homeName", "Local")
        away_team = event_info.get("awayName", "Visitante")
        
        result = {
            "event_id": event_info.get("id"),
            "name": event_info.get("name"),
            "home_team": home_team,
            "away_team": away_team,
            "start_time": event_info.get("start"),
            "state": event_info.get("state", "NOT_STARTED"),
            "score": event_info.get("score", {}),
            "markets": {
                # Tab: Partido
                "tiempo_reglamentario": [],
                "medio_tiempo": [],
                "corners": [],
                "tarjetas_equipo": [],
                "disparos_equipo": [],
                "eventos_partido": [],
                # Tab: Jugadores
                "goleador": [],
                "tarjetas_jugador": [],
                "apuestas_especiales_jugador": [],
                "asistencias_jugador": [],
                "goles_jugador": [],
                "paradas_portero": [],
                "disparos_jugador": [],
                # Tab: Handicap
                "handicap_3way": [],
                "lineas_asiaticas": []
            }
        }
        
        for offer in offers:
            if offer.get("suspended"):
                continue
            
            criterion = offer.get("criterion", {})
            offer_label = criterion.get("label", offer.get("label", ""))
            outcomes = offer.get("outcomes", [])
            
            parsed_outcomes = [{
                "label": out.get("label"),
                "odds": out.get("odds", 0) / 1000.0,
                "line": out.get("line"),
                "type": out.get("type"),
                "participant": out.get("participant"),
                "participant_name": out.get("participantName")
            } for out in outcomes]
            
            market_data = {
                "label": offer_label,
                "outcomes": parsed_outcomes,
                "criterion_id": criterion.get("id")
            }
            
            # Categorizar el mercado
            category = self._categorize_market(offer_label, outcomes)
            if category in result["markets"]:
                result["markets"][category].append(market_data)
        
        return result
    
    def _categorize_market(self, label: str, outcomes: list) -> str:
        """Categoriza un mercado basado en su label de forma robusta."""
        label_lower = label.lower()
        print(f"DEBUG: Categorizing '{label}'...")

        # 1. MEDIO TIEMPO (Prioridad Máxima y corrección de '1.ª')
        # Patrones que indican mitades explícitamente
        if any(x in label_lower for x in [
            "1ª parte", "2ª parte", "1.ª parte", "2.ª parte",
            "1ª mitad", "2ª mitad", "1.ª mitad", "2.ª mitad",
            "1° parte", "2° parte", "1° mitad", "2° mitad",
            "1st half", "2nd half", "- 1ª", "- 2ª"
        ]):
            # Excepción: "Gol en ambas mitades" va en tiempo reglamentario según usuario
            if "ambas mitades" in label_lower:
                pass 
            else:
                print(f"DEBUG: -> medio_tiempo (por patrón de mitad)")
                return "medio_tiempo"

        # 2. CORNERS
        if "esquina" in label_lower or "corner" in label_lower or "córner" in label_lower:
            print(f"DEBUG: -> corners")
            return "corners"

        # 3. LISTA BLANCA DE TIEMPO REGLAMENTARIO (Evita que caigan en Jugadores)
        # Estos mercados suelen tener participantes (equipos) pero SON de partido
        safe_team_markets = [
            "resultado final", "1x2", "doble oportunidad", "apuesta sin empate",
            "ambos equipos", "btts", "resultado correcto", "marcador correcto",
            "total de goles", "descanso/tiempo", "medio tiempo/final",
            "victoria de", "gol en ambas mitades", "ganador del partido"
        ]
        if any(x in label_lower for x in safe_team_markets):
            # Verificar que NO sea de mitades (ya filtrado arriba, pero por seguridad)
            # y que NO sea explícitamente de jugador (ej. "Total de goles de Haaland")
            # Pero "Total de goles de Getafe" SÍ es tiempo reglamentario.
            # La distinción clave es si menciona un jugador específico.
            
            # Si dice "total de goles" y tiene participante, verificar si es equipo o jugador
            # Asumimos que si cae aquí es equipo, la lógica de jugador es más específica abajo.
            print(f"DEBUG: -> tiempo_reglamentario (safe list)")
            return "tiempo_reglamentario"

        # 4. HANDICAP & ASIÁTICOS
        if "asiático" in label_lower or "asian" in label_lower:
            print(f"DEBUG: -> lineas_asiaticas")
            return "lineas_asiaticas"
        if "hándicap" in label_lower or "handicap" in label_lower:
            # Distinguir entre handicap normal (tab partido) y 3-way (tab handicap)
            if "3-way" in label_lower or "3 way" in label_lower or "3 opciones" in label_lower:
                print(f"DEBUG: -> handicap_3way")
                return "handicap_3way"
            # Si es solo handicap, el usuario lo puso en Tiempo Reglamentario ("Hándicap (lista)")
            print(f"DEBUG: -> tiempo_reglamentario (handicap simple)")
            return "tiempo_reglamentario"

        # 5. JUGADORES
        # Detección específica por palabras clave fuertes
        if any(x in label_lower for x in ["goleador", "primer gol", "marcará", "anytime scorer", "hat-trick", "asistenc", "disparo", "tiro", "pases", "faltas cometidas por", "fueras de juego por"]):
             is_player_prop = True
             # Refinar subcategoría
             if "asistencia" in label_lower: return "asistencias_jugador"
             if "tarjeta" in label_lower: return "tarjetas_jugador"
             if "disparo" in label_lower or "tiro" in label_lower:
                 # Cuidado: "tiros de esquina" ya se filtró. "tiros por parte de Getafe" es equipo.
                 if "parte de" in label_lower and "jugador" not in label_lower:
                     # Es equipo (ej: "tiros por parte de Getafe")
                     print(f"DEBUG: -> disparos_equipo")
                     return "disparos_equipo"
                 return "disparos_jugador"
             if "parada" in label_lower or "portero" in label_lower: return "paradas_portero"
             if "falta" in label_lower: return "apuestas_especiales_jugador" # O tarjeta
             
             # Goles
             if "goles" in label_lower or "2" in label_lower or "dos" in label_lower: return "goles_jugador"
             return "goleador" # Default disparos/goles

        # Detección genérica por participante (outcome tiene participantID)
        has_participant = any(out.get("participant") or out.get("participantName") for out in outcomes)
        if has_participant:
            # Aquí es delicado. "Total de goles de Getafe" tiene participante pero es Tiempo Reg.
            # Ya filtramos 'safe_team_markets' arriba.
            # Si llegamos aquí, es algo con participante que NO es corners, ni handicap 3way, ni safe list.
            
            if "tarjeta" in label_lower:
                # Si es "Tarjeta roja a Getafe" -> Tarjetas Equipo
                if "roja a" in label_lower or "total de tarjetas" in label_lower:
                     print(f"DEBUG: -> tarjetas_equipo")
                     return "tarjetas_equipo"
                return "tarjetas_jugador"
            
            print(f"DEBUG: -> apuestas_especiales_jugador (generic participant)")
            return "apuestas_especiales_jugador"

        # 6. CATEGORÍAS RESTANTES DE EQUIPO
        if "tarjeta" in label_lower:
            print(f"DEBUG: -> tarjetas_equipo")
            return "tarjetas_equipo"
        
        if "disparo" in label_lower or "tiro" in label_lower:
            print(f"DEBUG: -> disparos_equipo")
            return "disparos_equipo"

        if any(x in label_lower for x in ["propia meta", "sin recibir gol", "gana al menos", "al palo"]):
            print(f"DEBUG: -> eventos_partido")
            return "eventos_partido"

        # 7. DEFAULT
        print(f"DEBUG: -> tiempo_reglamentario (default)")
        return "tiempo_reglamentario"
    
    def get_event_statistics(self, event_id: int) -> Optional[Dict[str, Any]]:
        """Obtiene estadísticas del partido (disponible para eventos en vivo)."""
        endpoint = f"{self.BASE_URL}/event/{event_id}/statistics.json"
        
        params = {
            "lang": self.LANG,
            "market": self.MARKET,
            "client_id": self.CLIENT_ID,
            "channel_id": self.CHANNEL_ID,
            "nc_id": int(time.time() * 1000)
        }
        
        try:
            response = self.session.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return self._parse_statistics(data)
        except requests.RequestException as e:
            print(f"Error fetching statistics: {e}")
            return None
    
    def _parse_statistics(self, data: Dict) -> Dict[str, Any]:
        """Parsea las estadísticas de un partido."""
        stats = data.get("statistics", {})
        match_events = data.get("matchEvents", [])
        
        result = {"stats": {}, "events": []}
        
        for stat_group in stats.get("sets", []):
            for stat in stat_group.get("statistics", []):
                result["stats"][stat.get("name", "")] = {
                    "home": stat.get("home"),
                    "away": stat.get("away")
                }
        
        for event in match_events:
            result["events"].append({
                "type": event.get("type"),
                "team": event.get("team"),
                "player": event.get("player"),
                "minute": event.get("minute"),
                "extra_minute": event.get("extraMinute")
            })
        
        return result
