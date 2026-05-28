"""
Sistema de Auto-Matching de Equipos.

Este módulo resuelve nombres de equipos de Rushbet a IDs de API-Football
usando fuzzy matching y persistencia en base de datos.
"""
import logging
from typing import Optional
from datetime import datetime
from sqlmodel import Session, select

try:
    from rapidfuzz import fuzz, process
    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    RAPIDFUZZ_AVAILABLE = False
    logging.warning("rapidfuzz no instalado. Fuzzy matching limitado.")

from app.sports.football.models import Team, TeamMapping

logger = logging.getLogger(__name__)

# Umbrales de confianza
CONFIDENCE_AUTO_MATCH = 0.85  # >= 85% confianza: auto-guardar como verificado
CONFIDENCE_TENTATIVE = 0.60   # >= 60% confianza: guardar pero no verificado
CONFIDENCE_REJECT = 0.50      # < 50% confianza: no guardar


def get_mapped_team_id(source_name: str, session: Optional[Session] = None) -> Optional[int]:
    """
    Busca el ID de API-Football para un nombre de equipo externo.
    
    1. Primero busca en la tabla de mapeos existentes
    2. Si no existe, intenta auto-match con fuzzy logic
    3. Guarda el resultado para futuras consultas
    
    Args:
        source_name: Nombre del equipo como aparece en Rushbet
        session: Sesión de BD opcional
        
    Returns:
        ID del equipo o None si no se encuentra
    """
    if not source_name:
        return None
    
    clean_name = source_name.strip()
    
    # Crear sesión si no se provee
    if session is None:
        from app.core.database import get_session
        session = next(get_session())
        should_close = True
    else:
        should_close = False
    
    try:
        # 1. Buscar en mapeos existentes
        existing = session.exec(
            select(TeamMapping).where(TeamMapping.source_name == clean_name)
        ).first()
        
        if existing and existing.api_football_id:
            return existing.api_football_id
        
        # 2. Intentar auto-match
        match_result = _auto_match_team(clean_name, session)
        
        if match_result:
            team_id, confidence = match_result
            
            # 3. Guardar el mapeo
            _save_mapping(clean_name, team_id, confidence, session)
            session.commit()
            
            return team_id
        
        return None
        
    except Exception as e:
        logger.error(f"Error en get_mapped_team_id: {e}")
        return None
    finally:
        if should_close:
            session.close()


def _auto_match_team(source_name: str, session: Session) -> Optional[tuple[int, float]]:
    """
    Intenta encontrar automáticamente el equipo más similar.
    
    Returns:
        Tuple (team_id, confidence_score) o None
    """
    # Obtener todos los equipos de la BD
    all_teams = session.exec(select(Team)).all()
    if not all_teams:
        return None
    
    # Preparar lista de nombres para comparar
    team_names = [(t.id, t.name) for t in all_teams]
    
    if RAPIDFUZZ_AVAILABLE:
        # Usar rapidfuzz para matching avanzado
        return _fuzzy_match_rapidfuzz(source_name, team_names)
    else:
        # Fallback a matching simple
        return _fuzzy_match_simple(source_name, team_names)


def _fuzzy_match_rapidfuzz(source_name: str, team_names: list[tuple[int, str]]) -> Optional[tuple[int, float]]:
    """Matching usando rapidfuzz (más preciso)."""
    choices = {name: team_id for team_id, name in team_names}
    
    # Usar múltiples métodos y promediar
    results = []
    
    # 1. Token Sort Ratio (bueno para orden diferente de palabras)
    match1 = process.extractOne(
        source_name, 
        choices.keys(),
        scorer=fuzz.token_sort_ratio
    )
    if match1:
        results.append((choices[match1[0]], match1[1] / 100))
    
    # 2. Partial Ratio (bueno para substrings)
    match2 = process.extractOne(
        source_name,
        choices.keys(),
        scorer=fuzz.partial_ratio
    )
    if match2:
        results.append((choices[match2[0]], match2[1] / 100))
    
    # 3. Weighted Ratio (balance general)
    match3 = process.extractOne(
        source_name,
        choices.keys(),
        scorer=fuzz.WRatio
    )
    if match3:
        results.append((choices[match3[0]], match3[1] / 100))
    
    if not results:
        return None
    
    # Tomar el mejor resultado
    best = max(results, key=lambda x: x[1])
    
    if best[1] >= CONFIDENCE_REJECT:
        logger.info(f"Auto-match: '{source_name}' -> ID {best[0]} (confianza: {best[1]:.2%})")
        return best
    
    return None


def _fuzzy_match_simple(source_name: str, team_names: list[tuple[int, str]]) -> Optional[tuple[int, float]]:
    """Matching simple sin dependencias externas."""
    source_lower = source_name.lower()
    
    best_match = None
    best_score = 0.0
    
    for team_id, team_name in team_names:
        name_lower = team_name.lower()
        
        # Coincidencia exacta
        if source_lower == name_lower:
            return (team_id, 1.0)
        
        # Substring match
        if source_lower in name_lower or name_lower in source_lower:
            # Calcular "score" basado en longitud
            score = len(min(source_lower, name_lower, key=len)) / len(max(source_lower, name_lower, key=len))
            if score > best_score:
                best_score = score
                best_match = team_id
        
        # Word overlap
        source_words = set(source_lower.split())
        name_words = set(name_lower.split())
        overlap = len(source_words & name_words)
        if overlap > 0:
            score = overlap / max(len(source_words), len(name_words))
            if score > best_score:
                best_score = score
                best_match = team_id
    
    if best_match and best_score >= CONFIDENCE_REJECT:
        return (best_match, best_score)
    
    return None


def _save_mapping(source_name: str, team_id: int, confidence: float, session: Session) -> None:
    """Guarda o actualiza un mapeo en la base de datos."""
    existing = session.exec(
        select(TeamMapping).where(TeamMapping.source_name == source_name)
    ).first()
    
    if existing:
        existing.api_football_id = team_id
        existing.confidence_score = confidence
        existing.verified = confidence >= CONFIDENCE_AUTO_MATCH
        existing.updated_at = datetime.utcnow()
        session.add(existing)
    else:
        mapping = TeamMapping(
            source_name=source_name,
            source="rushbet",
            api_football_id=team_id,
            confidence_score=confidence,
            verified=confidence >= CONFIDENCE_AUTO_MATCH
        )
        session.add(mapping)
    
    logger.info(f"Mapeo guardado: '{source_name}' -> {team_id} (conf: {confidence:.2%}, verified: {confidence >= CONFIDENCE_AUTO_MATCH})")


def verify_mapping(source_name: str, correct_team_id: int, session: Session) -> bool:
    """
    Verificación manual de un mapeo.
    Permite corregir errores del auto-match.
    """
    existing = session.exec(
        select(TeamMapping).where(TeamMapping.source_name == source_name)
    ).first()
    
    if existing:
        existing.api_football_id = correct_team_id
        existing.confidence_score = 1.0
        existing.verified = True
        existing.updated_at = datetime.utcnow()
    else:
        existing = TeamMapping(
            source_name=source_name,
            source="rushbet",
            api_football_id=correct_team_id,
            confidence_score=1.0,
            verified=True
        )
    
    session.add(existing)
    session.commit()
    
    logger.info(f"Mapeo verificado manualmente: '{source_name}' -> {correct_team_id}")
    return True


def get_unverified_mappings(session: Session) -> list[TeamMapping]:
    """Obtiene mapeos pendientes de verificación manual."""
    return session.exec(
        select(TeamMapping).where(TeamMapping.verified == False)
    ).all()
