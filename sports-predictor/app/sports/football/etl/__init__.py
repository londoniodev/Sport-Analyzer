"""
Football ETL - Proceso de Extracción, Transformación y Carga para datos de fútbol.
Este módulo se encarga de obtener datos de la API oficial (API-Sports),
procesarlos a los modelos de la base de datos y guardarlos de forma eficiente.
"""
import logging
import time
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Generator
from sqlmodel import Session, select
from app.core.interfaces import ISportETL
from app.core.database import get_session
from app.sports.football.api import FootballAPIClient
from app.sports.football.models import (
    League, Team, Player, Coach, Fixture, TeamMatchStats, PlayerMatchStats, Injury
)
# Configuración de ligas centralizada - editar league_config.py para agregar/quitar ligas
from app.sports.football.config.leagues import (
    PRIORITY_LEAGUES, ALLOWED_LEAGUE_IDS, REGION_MAP, get_region
)

# Configuración del sistema de logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class FootballETL(ISportETL):
    """Motor de ETL para datos de fútbol."""
    
    # La configuración de ligas ahora está en league_config.py
    # Para agregar/quitar ligas, editar ese archivo directamente.
    
    def __init__(self):
        # Cliente encargado de las peticiones HTTP a la API
        self.api_client = FootballAPIClient()
    
    # ═══════════════════════════════════════════════════════
    # GESTIÓN DE BASE DE DATOS
    # ═══════════════════════════════════════════════════════
    
    @contextmanager
    def _get_db_session(self) -> Generator[Session, None, None]:
        """
        Administrador de contexto para sesiones de base de datos.
        Asegura que los cambios se guarden (commit) o se cancelen (rollback) en caso de error.
        """
        session = next(get_session())
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error en la base de datos: {e}")
            raise
        finally:
            session.close()
    
    # ═══════════════════════════════════════════════════════
    # MÉTODOS PÚBLICOS DE SINCRONIZACIÓN
    # ═══════════════════════════════════════════════════════
    
    def sync_league_data(self, league_id: int, season: int, sync_details: bool = False) -> int:
        """
        Sincroniza todos los partidos (fixtures) de una liga y temporada específica.
        - sync_details: Si es True, descarga también estadísticas de jugadores y equipos.
        """
        logger.info(f"[SYNC] Iniciando sincronización de Liga {league_id}, Temporada {season}")
        
        # 1. Obtener partidos de la API
        fixtures_data = self.api_client.get_events(league_id, season)
        if not fixtures_data:
            logger.warning(f"[SYNC] No se encontraron partidos para la liga {league_id}")
            return 0
        
        # 2. Guardar cada partido en la base de datos
        fixture_ids = []
        with self._get_db_session() as session:
            for fixture_data in fixtures_data:
                fixture = self._process_fixture(fixture_data, session)
                if fixture:
                    fixture_ids.append(fixture.id)
        
        logger.info(f"[SYNC] Guardados {len(fixture_ids)} partidos para la liga {league_id}")
        
        # 3. Sincronizar detalles (estadísticas) si se solicita
        # Esto genera múltiples peticiones a la API, se hace en segundo plano
        if sync_details and fixture_ids:
            self._sync_fixture_details_batch(fixture_ids)
        
        return len(fixture_ids)
    
    def sync_priority_leagues(self, season: int = 2026, sync_details: bool = False) -> Dict[str, int]:
        """Sincroniza automáticamente todas las ligas de la lista 'whitelist'."""
        all_ids = list(ALLOWED_LEAGUE_IDS)
        logger.info(f"[BATCH] Sincronizando {len(all_ids)} ligas prioritarias")
        
        results = {"success": 0, "error": 0, "total": len(all_ids)}
        
        for league_id in all_ids:
            try:
                count = self.sync_league_data(league_id, season, sync_details)
                results["success"] += 1
                logger.info(f"[BATCH] Liga {league_id} completada: {count} partidos")
            except Exception as e:
                logger.error(f"[BATCH] Error en liga {league_id}: {e}")
                results["error"] += 1
        
        return results
    
    def sync_all_leagues(self) -> int:
        """
        Descarga el catálogo completo de ligas de la API pero solo guarda 
        aquellas que están en nuestra lista permitida.
        """
        logger.info("[CATALOG] Descargando catálogo de ligas desde la API")
        
        leagues_data = self.api_client.get_all_leagues()
        if not leagues_data:
            logger.warning("[CATALOG] La API no devolvió ligas")
            return 0
        
        count = 0
        with self._get_db_session() as session:
            for league_data in leagues_data:
                league_id = league_data.get('league', {}).get('id')
                if league_id in ALLOWED_LEAGUE_IDS:
                    self._process_league_full(league_data, session)
                    count += 1
        
        logger.info(f"[CATALOG] Sincronizadas {count} ligas permitidas")
        return count
    
    def sync_injuries(self, league_id: int, season: int) -> int:
        """Descarga y guarda las lesiones reportadas para una liga y temporada."""
        logger.info(f"[INJURIES] Liga {league_id}, Temporada {season}")
        
        injuries_data = self.api_client.get_injuries(league_id, season)
        if not injuries_data:
            return 0
        
        with self._get_db_session() as session:
            for injury_data in injuries_data:
                self._process_injury(injury_data, league_id, season, session)
        
        logger.info(f"[INJURIES] Sincronizadas {len(injuries_data)} lesiones")
        return len(injuries_data)
    
    def sync_event_details(self, event_id: int) -> None:
        """
        Descarga todos los detalles de un partido específico:
        - Estadísticas de equipo (posesión, tiros, etc.)
        - Alineaciones oficiales (jugadores iniciales y suplentes)
        - Estadísticas por jugador (calificación, pases, goles, etc.)
        """
        logger.info(f"[DETAILS] Procesando detalles del partido {event_id}")
        
        # 1. Llamadas en paralelo a la API
        stats_data = self.api_client.get_event_stats(event_id)
        lineups_data = self.api_client.get_event_lineups(event_id)
        players_data = self.api_client.get_fixture_players(event_id)
        
        # 2. Guardar datos procesados
        with self._get_db_session() as session:
            self._process_stats(event_id, stats_data, session)
            self._process_lineups(event_id, lineups_data, session)
            self._process_fixture_players(event_id, players_data, session)
    
    def cleanup_non_priority_data(self) -> Dict[str, int]:
        """
        Mantenimiento: Elimina de la base de datos local todas las ligas 
        que ya no están en la lista prioritaria.
        """
        logger.info("[CLEANUP] Iniciando limpieza de ligas no prioritarias")
        
        with self._get_db_session() as session:
            # Encontrar ligas no permitidas
            stmt = select(League).where(League.id.not_in(ALLOWED_LEAGUE_IDS))
            leagues_to_delete = session.exec(stmt).all()
            league_ids = [l.id for l in leagues_to_delete]
            
            # Borrar ligas
            for league in leagues_to_delete:
                session.delete(league)
            
            # Borrar partidos huérfanos asociados
            if league_ids:
                fixtures_stmt = select(Fixture).where(Fixture.league_id.in_(league_ids))
                for fix in session.exec(fixtures_stmt).all():
                    session.delete(fix)
            
            logger.info(f"[CLEANUP] Eliminadas {len(league_ids)} ligas de la base de datos")
            return {"removed_leagues": len(league_ids)}
    
    # ═══════════════════════════════════════════════════════
    # PROCESAMIENTO INTERNO (PRIVADO)
    # ═══════════════════════════════════════════════════════
    
    def _sync_fixture_details_batch(self, fixture_ids: List[int], delay: float = 0.5) -> None:
        """
        Sincroniza detalles por lotes con un pequeño retraso para evitar 
        bloqueos por límite de peticiones (Rate Limit) de la API.
        """
        logger.info(f"[DETAILS-BATCH] Procesando {len(fixture_ids)} partidos")
        
        for i, fid in enumerate(fixture_ids):
            try:
                self.sync_event_details(fid)
                if (i + 1) % 50 == 0:
                    logger.info(f"[DETAILS-BATCH] Progreso: {i + 1}/{len(fixture_ids)}")
                time.sleep(delay)
            except Exception as e:
                logger.warning(f"[DETAILS-BATCH] Partido {fid} falló: {e}")
    
    def _process_fixture(self, data: Dict[str, Any], session: Session) -> Optional[Fixture]:
        """Transforma los datos de un partido para guardarlos en SQLModel."""
        fixture_info = data.get('fixture', {})
        league_info = data.get('league', {})
        teams_info = data.get('teams', {})
        goals_info = data.get('goals', {})
        
        fixture_id = fixture_info.get('id')
        if not fixture_id:
            return None
        
        # Asegurar que las entidades relacionadas (Liga, Equipos) existan en la BD
        league = self._upsert_league(league_info, session)
        home_team = self._upsert_team(teams_info.get('home', {}), session)
        away_team = self._upsert_team(teams_info.get('away', {}), session)
        
        # "Upsert" de Fixture (si existe lo actualiza, si no lo crea)
        fixture = session.get(Fixture, fixture_id)
        if not fixture:
            fixture = Fixture(
                id=fixture_id,
                date=fixture_info.get('date'),
                league_id=league.id if league else None,
                home_team_id=home_team.id if home_team else None,
                away_team_id=away_team.id if away_team else None,
                home_score=goals_info.get('home'),
                away_score=goals_info.get('away')
            )
            session.add(fixture)
        
        return fixture
    
    def _upsert_league(self, data: Dict[str, Any], session: Session) -> Optional[League]:
        """Crea o actualiza una liga en la base de datos."""
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
        """Crea o actualiza un equipo."""
        team_id = data.get('id')
        if not team_id:
            return None
        
        team = session.get(Team, team_id)
        if not team:
            team = Team(
                id=team_id,
                name=data.get('name', '')
            )
            session.add(team)
        return team
    
    def _upsert_player(self, data: Dict[str, Any], team_id: int, session: Session) -> Optional[Player]:
        """Crea o actualiza un jugador."""
        player_id = data.get('id')
        if not player_id:
            return None
        
        player = session.get(Player, player_id)
        if not player:
            player = Player(
                id=player_id,
                name=data.get('name', ''),
                position=data.get('pos') or data.get('position'),
                team_id=team_id
            )
            session.add(player)
        return player
    
    def _process_league_full(self, data: Dict[str, Any], session: Session) -> None:
        """Procesa datos completos de una liga (incluyendo logotipo y región)."""
        league_info = data.get('league', {})
        league_id = league_info.get('id')
        
        if not league_id or league_id not in ALLOWED_LEAGUE_IDS:
            return
        
        # Si ya existe, no la sobreescribimos para ahorrar recursos
        if session.get(League, league_id):
            return
        
        country_info = data.get('country', {})
        country_name = country_info.get('name', '')
        region = get_region(country_name)
        
        # Determinar la temporada actual
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
            region=region
        )
        session.add(league)
    
    def _process_stats(self, fixture_id: int, stats_data: List, session: Session) -> None:
        """Procesa y guarda las estadísticas de equipo por partido."""
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
            # Merge: actualiza si existe la clave primaria compuesta (fixture_id + team_id)
            session.merge(team_match_stats)
    
    def _process_lineups(self, fixture_id: int, lineups_data: List, session: Session) -> None:
        """Procesa alineaciones (Titulares, Suplentes y Entrenador)."""
        for team_lineup in lineups_data:
            team_id = team_lineup.get('team', {}).get('id')
            
            # Jugadores titulares y suplentes
            for player_entry in team_lineup.get('startXI', []) + team_lineup.get('substitutes', []):
                player_info = player_entry.get('player', {})
                self._upsert_player(player_info, team_id, session)
            
            # Entrenador
            coach_info = team_lineup.get('coach', {})
            if coach_info.get('id') and not session.get(Coach, coach_info.get('id')):
                session.add(Coach(id=coach_info.get('id'), name=coach_info.get('name', '')))
    
    def _process_fixture_players(self, fixture_id: int, players_data: List, session: Session) -> None:
        """Procesa el rendimiento individual de cada jugador en un partido."""
        for team_data in players_data:
            team_id = team_data.get('team', {}).get('id')
            
            for player_entry in team_data.get('players', []):
                player_info = player_entry.get('player', {})
                stats_list = player_entry.get('statistics', [])
                
                if not player_info.get('id') or not stats_list:
                    continue
                
                self._upsert_player(player_info, team_id, session)
                
                # Extraer métricas clave del primer bloque de estadísticas
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
        """Guarda información sobre jugadores lesionados o ausentes."""
        player_info = data.get('player', {})
        team_info = data.get('team', {})
        fixture_info = data.get('fixture', {})
        
        if not player_info.get('id'):
            return
        
        # Asegurar que existan los registros básicos
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
    # UTILIDADES DE AYUDA
    # ═══════════════════════════════════════════════════════
    
    # La función get_region se importa desde league_config.py
    
    @staticmethod
    def _parse_int(value) -> int:
        """Parsea un entero de forma segura evitando errores de tipo."""
        try:
            return int(value) if value else 0
        except (ValueError, TypeError):
            return 0
    
    @staticmethod
    def _parse_float(value) -> float:
        """Parsea un número decimal de forma segura."""
        try:
            return float(value) if value else 0.0
        except (ValueError, TypeError):
            return 0.0
