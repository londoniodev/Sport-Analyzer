"""
Database Migration Script - Add missing columns to football_league table.
Run once to fix the schema mismatch.
"""
import os
import sys
from pathlib import Path

# Add project root to path and load env from there
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

# Load .env from project root
env_path = PROJECT_ROOT / '.env'
load_dotenv(env_path)

from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print(f"ERROR: DATABASE_URL not found")
    print(f"Looked for .env at: {env_path}")
    print(f"Exists: {env_path.exists()}")
    exit(1)

print(f"Connecting to database...")
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    try:
        # Add league_type column if it doesn't exist
        conn.execute(text("""
            ALTER TABLE football_league 
            ADD COLUMN IF NOT EXISTS league_type VARCHAR(50)
        """))
        print("Added: league_type")
        
        # Add logo_url column if it doesn't exist
        conn.execute(text("""
            ALTER TABLE football_league 
            ADD COLUMN IF NOT EXISTS logo_url VARCHAR(500)
        """))
        print("Added: logo_url")
        
        # Add region column if it doesn't exist
        conn.execute(text("""
            ALTER TABLE football_league 
            ADD COLUMN IF NOT EXISTS region VARCHAR(50)
        """))
        print("Added: region")
        
        conn.commit()
        print("\nMigration completed successfully!")
        
    except Exception as e:
        print(f"\nMigration failed: {e}")
        conn.rollback()
