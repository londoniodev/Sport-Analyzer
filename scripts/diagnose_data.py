import os
import sys
from sqlmodel import Session, select, func
from sqlalchemy import or_

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.core.database import engine, _demo_mode
from app.sports.football.models import Team, Fixture, Player

from app.sports.football.analytics.worldcup_scoring import WORLD_CUP_TEAM_IDS

def run_diagnostics(session: Session):
    print("=========================================")
    print("   DIAGNÓSTICO DE DATOS DEL MUNDIAL")
    print("=========================================\n")
    
    # 1. Obtener los equipos del Mundial que están en la DB
    teams = session.exec(select(Team).where(Team.id.in_(WORLD_CUP_TEAM_IDS)).order_by(Team.name)).all()
    
    found_ids = {t.id for t in teams}
    missing_from_db = [tid for tid in WORLD_CUP_TEAM_IDS if tid not in found_ids]
    
    print(f"Total de selecciones del Mundial encontradas en DB: {len(teams)}/48")
    if missing_from_db:
        print(f"❌ ADVERTENCIA: Hay {len(missing_from_db)} selecciones del Mundial no encontradas en la DB (IDs: {missing_from_db})")
    print("")
    
    missing_matches = []
    missing_players = []
    
    for team in teams:
        # Contar partidos
        matches_count = session.exec(
            select(func.count(Fixture.id))
            .where((Fixture.home_team_id == team.id) | (Fixture.away_team_id == team.id))
            .where(Fixture.home_score != None)
        ).one()
        
        if matches_count < 20:
            missing_matches.append(f"{team.name} (ID: {team.id}): {matches_count} partidos")
            
        # Contar jugadores
        players_count = session.exec(
            select(func.count(Player.id))
            .where(Player.team_id == team.id)
        ).one()
        
        if players_count < 11:
            missing_players.append(f"{team.name} (ID: {team.id}): {players_count} jugadores")
            
    # RESULTADOS PARTIDOS
    print("--- 1. AUDITORÍA DE PARTIDOS DEL MUNDIAL (Mínimo esperado: 20) ---")
    if not missing_matches and not missing_from_db:
        print("✅ ¡PERFECTO! Todas las selecciones del Mundial tienen al menos 20 partidos históricos.")
    else:
        if missing_matches:
            print(f"❌ ADVERTENCIA: Hay {len(missing_matches)} selecciones con historial insuficiente:")
            for m in missing_matches:
                print(f"   - {m}")
        else:
            print("✅ Todos los equipos registrados tienen al menos 20 partidos históricos (pero faltan algunos equipos en la DB).")
            
    print("\n--- 2. AUDITORÍA DE PLANTILLAS DEL MUNDIAL (Mínimo esperado: 11) ---")
    if not missing_players and not missing_from_db:
        print("✅ ¡PERFECTO! Todas las selecciones del Mundial tienen al menos un 11 inicial.")
    else:
        if missing_players:
            print(f"❌ ADVERTENCIA: Hay {len(missing_players)} selecciones con plantillas incompletas:")
            for p in missing_players:
                print(f"   - {p}")
        else:
            print("✅ Todos los equipos registrados tienen al menos un 11 inicial (pero faltan algunos equipos en la DB).")
            
    print("\n=========================================")
    print("NOTA: Si faltan datos, ejecuta el botón de")
    print("'Actualizar Elos y Plantillas' en la UI o")
    print("el botón de descarga masiva de datos.")
    print("=========================================")

if __name__ == "__main__":
    if _demo_mode or engine is None:
        print("Error: No hay conexión a la base de datos.")
        sys.exit(1)
        
    with Session(engine) as session:
        run_diagnostics(session)
