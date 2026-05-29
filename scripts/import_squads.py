import os
import sys
import requests
from bs4 import BeautifulSoup
from sqlmodel import Session, select

# Asegurar que el path sea correcto para poder importar 'app'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import engine
from app.sports.football.models import Team, Player

WIKI_URL = "https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_squads"

def scrape_squads(session: Session):
    print(f"Descargando datos de {WIKI_URL}...")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'
    }
    response = requests.get(WIKI_URL, headers=headers)
    if response.status_code != 200:
        print(f"Error descargando la página. Status code: {response.status_code}")
        return
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # En Wikipedia, cada equipo tiene un encabezado <h3> (usualmente)
    # y luego viene la tabla de jugadores.
    
    # Buscar todos los h3
    h3_tags = soup.find_all('h3')
    
    for h3 in h3_tags:
        # El nombre del equipo suele estar dentro de un span con clase mw-headline
        headline = h3.find('span', class_='mw-headline')
        if not headline:
            continue
            
        team_name = headline.text.strip()
        
        # Ignorar encabezados que no sean de equipos
        if team_name in ['Coaches representation by country', 'References', 'External links', 'Player representation by league system', 'Player representation by club']:
            continue
            
        print(f"\nProcesando equipo: {team_name}")
        
        # Buscar el equipo en la BD
        team = session.exec(select(Team).where(Team.name == team_name)).first()
        if not team:
            print(f"  [!] Equipo {team_name} no encontrado en la BD. Creándolo...")
            team = Team(name=team_name)
            session.add(team)
            session.commit()
            session.refresh(team)
            
        # Buscar la siguiente tabla
        # En Wikipedia, la tabla sigue después del h3 (puede haber un div u otro tag en medio)
        current = h3.find_next_sibling()
        table = None
        while current and current.name not in ['h2', 'h3']:
            if current.name == 'table' and 'sortable' in current.get('class', []):
                table = current
                break
            current = current.find_next_sibling()
            
        if not table:
            print(f"  [!] No se encontró tabla de jugadores para {team_name}")
            continue
            
        # Parsear jugadores
        rows = table.find_all('tr')[1:] # Saltar cabecera
        players_added = 0
        for row in rows:
            cols = row.find_all(['th', 'td'])
            if len(cols) < 5:
                continue
                
            # Formato típico: No | Pos | Name | DOB | Caps | Goals | Club
            # El nombre suele ser la 3ra columna (index 2)
            # A veces tiene una bandera o es un <th>
            name_cell = cols[2]
            
            # Limpiar notas al pie ej. "Lionel Messi (c)"
            player_name = name_cell.text.replace('(c)', '').strip()
            # Limpiar referencias ej. "[1]"
            import re
            player_name = re.sub(r'\[.*?\]', '', player_name).strip()
            
            pos = cols[1].text.strip()
            
            # Revisar si ya existe
            existing_player = session.exec(
                select(Player).where((Player.name == player_name) & (Player.team_id == team.id))
            ).first()
            
            if not existing_player:
                new_player = Player(
                    name=player_name,
                    position=pos,
                    team_id=team.id
                )
                session.add(new_player)
                players_added += 1
                
        session.commit()
        print(f"  ✓ {players_added} jugadores nuevos añadidos a {team_name}.")

if __name__ == "__main__":
    with Session(engine) as session:
        scrape_squads(session)
        print("\n¡Importación de Squads finalizada exitosamente!")
