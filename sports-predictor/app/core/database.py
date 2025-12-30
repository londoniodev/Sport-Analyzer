"""
Database configuration - shared across all sports.
Supports demo mode without database for predictions.
"""
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Database is optional - predictions work without it
engine = None
_demo_mode = False

if DATABASE_URL:
    try:
        from sqlmodel import create_engine, SQLModel, Session
        engine = create_engine(DATABASE_URL, echo=False)
    except Exception as e:
        print(f"⚠ Database connection failed: {e}")
        _demo_mode = True
else:
    _demo_mode = True
    print("ℹ️ Running in DEMO mode (no database configured)")


def is_demo_mode() -> bool:
    """Check if app is running without database."""
    return _demo_mode


def init_db():
    """Initialize database with all registered sport models."""
    # Always discover sports (for registry to work)
    from app.sports import discover_sports
    discover_sports()
    
    # Only create tables if database is connected
    if engine is not None:
        from sqlmodel import SQLModel
        SQLModel.metadata.create_all(engine)
    else:
        print("ℹ️ Skipping database init (demo mode)")


def get_session():
    """Yield a database session (or None in demo mode)."""
    if engine is None:
        yield None
        return
    
    from sqlmodel import Session
    with Session(engine) as session:
        yield session

