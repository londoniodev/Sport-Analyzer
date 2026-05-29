import os
import sys
from sqlmodel import Session, select, func
from sqlalchemy import or_

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.core.database import engine, _demo_mode
from app.sports.football.models import Team, Fixture, Player

def run_diagnostics(session: Session):
    print("=========================================")
    print("   DIAGNÓSTICO DE DATOS DEL MUNDIAL")
    print("=========================================\n")
    
    # 1. Obtener todos los equipos (Selecciones)
    teams = session.exec(select(Team).order_by(Team.name)).all()
    
    print(f"Total de equipos evaluados: {len(teams)}\n")
    
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
            missing_matches.append(f"{team.name}: {matches_count} partidos")
            
        # Contar jugadores
        players_count = session.exec(
            select(func.count(Player.id))
            .where(Player.team_id == team.id)
        ).one()
        
        if players_count < 11:
            missing_players.append(f"{team.name}: {players_count} jugadores")
            
    # RESULTADOS PARTIDOS
    print("--- 1. AUDITORÍA DE PARTIDOS (Mínimo esperado: 20) ---")
    if not missing_matches:
        print("✅ ¡PERFECTO! Todos los equipos tienen al menos 20 partidos históricos.")
    else:
        print(f"❌ ADVERTENCIA: Hay {len(missing_matches)} equipos con historial insuficiente:")
        for m in missing_matches:
            print(f"   - {m}")
            
    print("\n--- 2. AUDITORÍA DE PLANTILLAS (Mínimo esperado: 11) ---")
    if not missing_players:
        print("✅ ¡PERFECTO! Todos los equipos tienen al menos un 11 inicial.")
    else:
        print(f"❌ ADVERTENCIA: Hay {len(missing_players)} equipos con plantillas incompletas:")
        for p in missing_players:
            print(f"   - {p}")
            
    print("\n=========================================")
    print("NOTA: Si faltan datos, ejecuta el botón de")
    print("'Actualizar Elos y Plantillas' desde la UI.")
    print("=========================================")

if __name__ == "__main__":
    if _demo_mode or engine is None:
        print("Error: No hay conexión a la base de datos.")
        sys.exit(1)
        
    with Session(engine) as session:
        run_diagnostics(session)
