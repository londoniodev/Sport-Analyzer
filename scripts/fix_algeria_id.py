import os
import sys
from sqlmodel import Session, select, text

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.core.database import engine, _demo_mode
from app.sports.football.models import Team

def fix_algeria_id():
    if _demo_mode or engine is None:
        print("Error: No database connection found.")
        sys.exit(1)
        
    print("Iniciando migración de ID de Argelia (1532 -> 1559)...")
    
    with Session(engine) as session:
        # Buscar el equipo con ID incorrecto (1532)
        algeria_1532 = session.exec(select(Team).where(Team.id == 1532)).first()
        if not algeria_1532:
            print("No se encontró el equipo Argelia con ID 1532. Verificando ID 1559...")
            algeria_1559 = session.exec(select(Team).where(Team.id == 1559)).first()
            if algeria_1559:
                print("✅ Argelia ya está registrada correctamente con ID 1559.")
            else:
                print("❌ Argelia no está registrada con ninguno de los dos IDs.")
            return

        # Verificar si ya existe el ID 1559
        algeria_1559 = session.exec(select(Team).where(Team.id == 1559)).first()
        if not algeria_1559:
            print("Creando registro de Argelia con ID 1559...")
            # Insertar directamente con ID 1559 usando SQL crudo para evitar que el auto-increment interfiera
            session.execute(
                text("INSERT INTO football_team (id, name, elo_rating) VALUES (:id, :name, :elo_rating)"),
                {"id": 1559, "name": algeria_1532.name, "elo_rating": algeria_1532.elo_rating}
            )
            session.commit()
            print("✅ Registro de Argelia creado con ID 1559.")

        # Tablas y columnas a actualizar
        ref_updates = [
            ("football_player", "team_id"),
            ("football_fixture", "home_team_id"),
            ("football_fixture", "away_team_id"),
            ("football_team_match_stats", "team_id"),
            ("football_player_match_stats", "team_id"),
            ("football_player_season_stats", "team_id"),
            ("football_injury", "team_id"),
        ]

        # Realizar actualizaciones de claves foráneas
        for table, col in ref_updates:
            # Comprobar si la tabla existe en la BD
            try:
                # Usar raw SQL para actualizar
                res = session.execute(
                    text(f"UPDATE {table} SET {col} = 1559 WHERE {col} = 1532")
                )
                session.commit()
                print(f"  - Actualizada tabla {table} ({col}): {res.rowcount} filas modificadas.")
            except Exception as e:
                session.rollback()
                print(f"  - Error al actualizar {table} ({col}): {e}")

        # Finalmente, eliminar el equipo viejo 1532
        try:
            session.execute(text("DELETE FROM football_team WHERE id = 1532"))
            session.commit()
            print("✅ Registro de Argelia con ID 1532 eliminado exitosamente.")
        except Exception as e:
            session.rollback()
            print(f"❌ Error al eliminar el registro 1532: {e}")
            
        print("\n¡Migración completada con éxito!")

if __name__ == "__main__":
    fix_algeria_id()
