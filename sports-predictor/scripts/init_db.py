"""
Script de Inicialización de Base de Datos - Crea todas las tablas.
Este script debe ejecutarse una vez al configurar el entorno por primera vez
para asegurar que todas las tablas de SQLModel existan en PostgreSQL.
"""
import os
import sys
from pathlib import Path

# Configuración de rutas para importar módulos de la aplicación
# Esto permite que el script encuentre la carpeta 'app' desde la carpeta 'scripts'
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Cargar variables de entorno desde el archivo .env en la raíz del proyecto
from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / '.env')

from sqlmodel import SQLModel
from sqlalchemy import create_engine, text

# IMPORTANTE: Se deben importar todos los modelos aquí para que SQLModel 
# los registre en los metadatos antes de llamar a create_all()
from app.sports.football.models import (
    League, Team, Player, Coach, Fixture, 
    TeamMatchStats, PlayerMatchStats, PlayerSeasonStats, Injury
)

# Obtener la URL de la base de datos desde el entorno
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # Si no existe DATABASE_URL, intentar construirla a partir de componentes individuales
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432") 
    DB_NAME = os.getenv("DB_NAME", "sports_predictor")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASS = os.getenv("DB_PASSWORD", "")
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

print(f"Conectando a la base de datos...")
engine = create_engine(DATABASE_URL)

# Comando principal: Crea las tablas si no existen basándose en los modelos importados
print("Creando tablas si no existen...")
SQLModel.metadata.create_all(engine)

# Verificación final: Listar las tablas creadas con el prefijo 'football_'
with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name LIKE 'football_%'
        ORDER BY table_name
    """))
    tables = [row[0] for row in result]
    
print(f"\nTablas verificadas en la base de datos ({len(tables)}):")
for t in tables:
    print(f"  - {t}")
