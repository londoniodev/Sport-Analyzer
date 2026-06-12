import os
import sys
from sqlmodel import Session, select

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.core.database import engine, _demo_mode
from app.sports.football.models import Team

EXPECTED_NAMES = [
    "Mexico", "South Africa", "South Korea", "Czech Republic",
    "Canada", "Bosnia", "Qatar", "Switzerland",
    "Brazil", "Morocco", "Haiti", "Scotland",
    "USA", "Paraguay", "Australia", "Turkey",
    "Germany", "Curacao", "Ivory Coast", "Ecuador",
    "Netherlands", "Japan", "Sweden", "Tunisia",
    "Belgium", "Egypt", "Iran", "New Zealand",
    "Spain", "Cape Verde", "Saudi Arabia", "Uruguay",
    "France", "Senegal", "Iraq", "Norway",
    "Argentina", "Algeria", "Austria", "Jordan",
    "Portugal", "DR Congo", "Uzbekistan", "Colombia",
    "England", "Croatia", "Ghana", "Panama"
]

def find_ids():
    if _demo_mode or engine is None:
        print("Error: No connection to DB.")
        return
        
    with Session(engine) as session:
        print("=========================================")
        print(" BÚSQUEDA DE IDs CORRECTOS EN LA DB")
        print("=========================================\n")
        
        for name in EXPECTED_NAMES:
            # Clean name for search
            search_name = name.replace("USA", "United States").replace("DR Congo", "Congo DR").replace("Ivory Coast", "Cote d'Ivoire")
            
            # Query by name (case-insensitive)
            stmt = select(Team).where(Team.name.ilike(f"%{search_name}%"))
            teams = session.exec(stmt).all()
            
            # If not found, try alternative names
            if not teams and name == "Bosnia":
                teams = session.exec(select(Team).where(Team.name.ilike("%bosnia%"))).all()
            if not teams and name == "Curacao":
                teams = session.exec(select(Team).where(Team.name.ilike("%curacao%"))).all()
            if not teams and name == "Cape Verde":
                teams = session.exec(select(Team).where(Team.name.ilike("%cape verde%"))).all()
            if not teams and name == "Czech Republic":
                teams = session.exec(select(Team).where(Team.name.ilike("%czech%"))).all()
            if not teams and name == "Turkey":
                teams = session.exec(select(Team).where(Team.name.ilike("%turkey%") | Team.name.ilike("%türkiye%"))).all()
                
            if teams:
                print(f"✅ {name}:")
                for t in teams:
                    print(f"   - {t.name} (ID: {t.id})")
            else:
                print(f"❌ {name}: NOT FOUND IN DB")

if __name__ == "__main__":
    find_ids()
