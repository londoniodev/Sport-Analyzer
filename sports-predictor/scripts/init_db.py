"""
Database Initialization Script - Create all tables.
"""
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / '.env')

from sqlmodel import SQLModel
from sqlalchemy import create_engine, text

# Import all models so SQLModel registers them
from app.sports.football.models import (
    League, Team, Player, Coach, Fixture, 
    TeamMatchStats, PlayerMatchStats, PlayerSeasonStats, Injury
)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # Fallback - try to build from parts
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432") 
    DB_NAME = os.getenv("DB_NAME", "sports_predictor")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASS = os.getenv("DB_PASSWORD", "")
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

print(f"Connecting to database...")
engine = create_engine(DATABASE_URL)

# Create all tables
print("Creating tables...")
SQLModel.metadata.create_all(engine)

# Verify tables exist
with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name LIKE 'football_%'
        ORDER BY table_name
    """))
    tables = [row[0] for row in result]
    
print(f"\nTables created ({len(tables)}):")
for t in tables:
    print(f"  - {t}")
