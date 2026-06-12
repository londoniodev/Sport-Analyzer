import os
import sys
from sqlmodel import Session

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.core.database import engine, _demo_mode
from app.sports.football.models import Team
from app.sports.football.analytics.worldcup_scoring import WORLD_CUP_TEAM_IDS

# The list of teams by group in order
EXPECTED_NAMES = [
    # Group A
    "Mexico", "South Africa", "South Korea", "Czech Republic",
    # Group B
    "Canada", "Bosnia", "Qatar", "Switzerland",
    # Group C
    "Brazil", "Morocco", "Haiti", "Scotland",
    # Group D
    "USA", "Paraguay", "Australia", "Turkey",
    # Group E
    "Germany", "Curacao", "Ivory Coast", "Ecuador",
    # Group F
    "Netherlands", "Japan", "Sweden", "Tunisia",
    # Group G
    "Belgium", "Egypt", "Iran", "New Zealand",
    # Group H
    "Spain", "Cape Verde", "Saudi Arabia", "Uruguay",
    # Group I
    "France", "Senegal", "Iraq", "Norway",
    # Group J
    "Argentina", "Algeria", "Austria", "Jordan",
    # Group K
    "Portugal", "DR Congo", "Uzbekistan", "Colombia",
    # Group L
    "England", "Croatia", "Ghana", "Panama"
]

def check_ids():
    if _demo_mode or engine is None:
        print("Error: No connection to DB.")
        return
        
    with Session(engine) as session:
        print("=========================================")
        print(" VERIFICACIÓN DE MAPEO DE EQUIPOS")
        print("=========================================\n")
        
        mismatches = 0
        for i, tid in enumerate(WORLD_CUP_TEAM_IDS):
            team = session.get(Team, tid)
            expected = EXPECTED_NAMES[i]
            actual = team.name if team else "MISSING"
            
            # Simple check if expected is in actual (ignoring case)
            is_match = False
            if team:
                # E.g. "Bosnia and Herzegovina" contains "Bosnia"
                # "Curaçao" matches "Curacao" (replacing accents)
                def clean(s):
                    return s.lower().replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u").replace("ç", "c").replace("ñ", "n")
                
                c_expected = clean(expected)
                c_actual = clean(actual)
                if c_expected in c_actual or c_actual in c_expected:
                    is_match = True
                    
            if is_match:
                print(f"✅ ID {tid:4d} -> {actual} (Esperado: {expected})")
            else:
                print(f"❌ ID {tid:4d} -> {actual} (ESPERADO: {expected})")
                mismatches += 1
                
        print(f"\nTotal de discrepancias encontradas: {mismatches}")

if __name__ == "__main__":
    check_ids()
