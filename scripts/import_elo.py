import os
import sys
from sqlmodel import Session, select

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.core.database import engine, _demo_mode
from app.sports.football.models import Team

# Top 50 Elo Ratings (Aproximados de eloratings.net para selecciones de Mundial)
ELO_DATA = {
    "Argentina": 2140,
    "France": 2110,
    "Spain": 2080,
    "Brazil": 2060,
    "England": 2050,
    "Portugal": 2040,
    "Netherlands": 2030,
    "Colombia": 2020,
    "Uruguay": 2010,
    "Belgium": 2000,
    "Croatia": 1990,
    "Italy": 1980, # Si clasificó
    "Germany": 1970,
    "Japan": 1940,
    "Switzerland": 1930,
    "Morocco": 1920,
    "Senegal": 1910,
    "USA": 1900,
    "United States": 1900,
    "Mexico": 1880,
    "Ecuador": 1870,
    "Iran": 1860,
    "South Korea": 1850,
    "Australia": 1830,
    "Serbia": 1820,
    "Turkey": 1810,
    "Wales": 1800,
    "Poland": 1790,
    "Canada": 1780,
    "Peru": 1770,
    "Chile": 1760,
    "Venezuela": 1750,
    "Paraguay": 1740,
    "Cameroon": 1730,
    "Nigeria": 1720,
    "Ivory Coast": 1710,
    "Egypt": 1700,
    "Algeria": 1690,
    "Saudi Arabia": 1680,
    "Qatar": 1670,
    "Tunisia": 1660,
    "Mali": 1650,
    "Costa Rica": 1640,
    "Panama": 1630,
    "Jamaica": 1620,
    "South Africa": 1610,
    "Ghana": 1600,
    "Bosnia and Herzegovina": 1590,
    "New Zealand": 1580,
    "Uzbekistan": 1570,
    "Curaçao": 1500,
    "Haiti": 1450
}

def import_elo_ratings(session: Session):
    print("Actualizando Elo Ratings de los equipos...")
    
    teams = session.exec(select(Team)).all()
    updated_count = 0
    
    for team in teams:
        # Buscar el equipo en nuestro diccionario (ignorar mayusculas/minusculas)
        # Algunos paises pueden tener nombres ligeramente distintos
        matched_elo = None
        for country, elo in ELO_DATA.items():
            if country.lower() == team.name.lower():
                matched_elo = elo
                break
        
        if matched_elo:
            team.elo_rating = matched_elo
            updated_count += 1
            print(f"  ✓ {team.name}: {matched_elo} puntos Elo")
        else:
            # Si no está en la lista, le damos un Elo base de equipo clasificado al mundial (aprox 1500-1600)
            team.elo_rating = 1550.0
            print(f"  - {team.name}: 1550 puntos (Default)")
            
    session.commit()
    print(f"\n¡Se actualizaron los ratings Elo de {updated_count} equipos!")

if __name__ == "__main__":
    if _demo_mode or engine is None:
        print("El sistema está en DEMO mode o no hay conexión a BD.")
        sys.exit(1)
        
    with Session(engine) as session:
        import_elo_ratings(session)
