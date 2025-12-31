"""
Script de Migración de Base de Datos - Añade columnas faltantes a la tabla 'football_league'.
Este script se creó para solucionar un error de 'UndefinedColumn' cuando la base de datos
no estaba sincronizada con los últimos cambios en el modelo de SQLModel.
"""
import os
import sys
from pathlib import Path

# Configuración de rutas para importar módulos
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
env_path = PROJECT_ROOT / '.env'
load_dotenv(env_path)

from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print(f"ERROR: DATABASE_URL no encontrada")
    print(f"Buscando .env en: {env_path}")
    print(f"Existe el archivo: {env_path.exists()}")
    exit(1)

print(f"Conectando a la base de datos...")
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    try:
        # Añadir columna 'league_type' si no existe
        # Nota: Se usa VARCHAR(50) para almacenar 'League', 'Cup', etc.
        conn.execute(text("""
            ALTER TABLE football_league 
            ADD COLUMN IF NOT EXISTS league_type VARCHAR(50)
        """))
        print("Añadida: league_type")
        
        # Añadir columna 'logo_url' para almacenar el link a la imagen oficial
        conn.execute(text("""
            ALTER TABLE football_league 
            ADD COLUMN IF NOT EXISTS logo_url VARCHAR(500)
        """))
        print("Añadida: logo_url")
        
        # Añadir columna 'region' para agrupar ligas por continentes (Europe, South America, etc.)
        conn.execute(text("""
            ALTER TABLE football_league 
            ADD COLUMN IF NOT EXISTS region VARCHAR(50)
        """))
        print("Añadida: region")
        
        # Confirmar los cambios
        conn.commit()
        print("\n✅ ¡Migración completada con éxito!")
        
    except Exception as e:
        # En caso de error, deshacer cambios parciales
        print(f"\n❌ Error en la migración: {e}")
        conn.rollback()
