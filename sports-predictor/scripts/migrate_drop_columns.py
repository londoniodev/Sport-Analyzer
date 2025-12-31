"""
Script de Migración - Eliminar columnas no utilizadas.
Ejecutar una sola vez para limpiar las columnas de URL y referee.
"""
import os
import sys
from pathlib import Path

# Configuración de rutas
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / '.env')

from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("ERROR: DATABASE_URL no encontrada en .env")
    exit(1)

print("Conectando a la base de datos...")
engine = create_engine(DATABASE_URL)

# Columnas a eliminar
COLUMNS_TO_DROP = [
    ("football_league", "logo_url"),
    ("football_team", "logo_url"),
    ("football_player", "photo_url"),
    ("football_fixture", "referee_name"),
]

with engine.connect() as conn:
    for table, column in COLUMNS_TO_DROP:
        try:
            conn.execute(text(f"ALTER TABLE {table} DROP COLUMN IF EXISTS {column}"))
            print(f"✅ Eliminada: {table}.{column}")
        except Exception as e:
            print(f"⚠️ Error en {table}.{column}: {e}")
    
    conn.commit()
    print("\n✅ Migración completada!")
