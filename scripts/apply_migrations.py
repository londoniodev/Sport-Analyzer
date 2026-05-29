import os
import sys
from sqlalchemy import text
from sqlmodel import Session

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.core.database import engine

def apply_migrations():
    print("=========================================")
    print("   APLICANDO MIGRACIONES DE BASE DE DATOS")
    print("=========================================\n")
    
    if engine is None:
        print("Error: No database connection found (engine is None).")
        sys.exit(1)
        
    queries = [
        # Añadir elo_rating a football_team
        "ALTER TABLE football_team ADD COLUMN IF NOT EXISTS elo_rating FLOAT;",
        # Añadir expected_goals a football_team_match_stats
        "ALTER TABLE football_team_match_stats ADD COLUMN IF NOT EXISTS expected_goals FLOAT;"
    ]
    
    with Session(engine) as session:
        for q in queries:
            try:
                session.execute(text(q))
                print(f"✓ Ejecutado: {q}")
            except Exception as e:
                print(f"⚠ Error ejecutando '{q}': {e}")
                
        session.commit()
        print("\n✅ Migraciones completadas con éxito.")
        print("El motor ahora tiene los campos para el Elo y Expected Goals.")

if __name__ == "__main__":
    apply_migrations()
