"""
Generador Semi-Automático de Mapeo de Equipos
==============================================
Este script consulta la base de datos para obtener todos los equipos
y genera el archivo team_mapping.py con el formato correcto.

Uso:
    python scripts/generate_team_mapping.py

El script genera variantes de nombres comunes automáticamente.
"""
import os
import sys
from pathlib import Path

# Setup path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / '.env')

from sqlalchemy import create_engine, text

# Variantes de nombres comunes (alias -> nombre canónico)
ALIAS_PATTERNS = {
    # Prefijos/Sufijos comunes
    "FC ": "",
    " FC": "",
    "CF ": "",
    " CF": "",
    "AC ": "",
    " AC": "",
    "SC ": "",
    " SC": "",
    "RC ": "",
    " RC": "",
    "Real ": "",
    "Atlético ": "Atletico ",
    "Athletic ": "",
    # Abreviaciones comunes
    "United": "Utd",
    "City": "",
    "Manchester": "Man",
    # Otros
    "Wolverhampton Wanderers": "Wolves",
    "Tottenham Hotspur": "Tottenham",
    "Brighton & Hove Albion": "Brighton",
    "West Ham United": "West Ham",
    "Newcastle United": "Newcastle",
    "Nottingham Forest": "Nott'm Forest",
    "Sheffield United": "Sheffield Utd",
}

def get_database_url():
    url = os.getenv("DATABASE_URL")
    if not url:
        host = os.getenv("DB_HOST", "localhost")
        port = os.getenv("DB_PORT", "5432")
        name = os.getenv("DB_NAME", "sports_predictor")
        user = os.getenv("DB_USER", "postgres")
        pwd = os.getenv("DB_PASSWORD", "")
        url = f"postgresql://{user}:{pwd}@{host}:{port}/{name}"
    return url

def generate_aliases(name: str) -> list:
    """Genera variantes del nombre del equipo."""
    aliases = [name]
    
    # Aplicar patrones de alias
    for pattern, replacement in ALIAS_PATTERNS.items():
        if pattern in name:
            variant = name.replace(pattern, replacement).strip()
            if variant and variant != name and variant not in aliases:
                aliases.append(variant)
    
    return aliases

def fetch_teams_from_db():
    """Obtiene todos los equipos de la base de datos agrupados por liga."""
    engine = create_engine(get_database_url())
    
    query = text("""
        SELECT DISTINCT
            t.id AS team_id,
            t.name AS team_name,
            l.id AS league_id,
            l.name AS league_name
        FROM football_team t
        JOIN football_fixture f ON (t.id = f.home_team_id OR t.id = f.away_team_id)
        JOIN football_league l ON f.league_id = l.id
        ORDER BY l.name, t.name
    """)
    
    with engine.connect() as conn:
        result = conn.execute(query)
        return result.fetchall()

def generate_mapping_file(teams_data):
    """Genera el contenido del archivo team_mapping.py"""
    
    lines = [
        '"""',
        'Mapeo de nombres de equipos de Rushbet a IDs de API-Football.',
        '',
        'Este archivo es GENERADO SEMI-AUTOMÁTICAMENTE.',
        'Puedes agregar alias manualmente para nombres que varían en Rushbet.',
        '"""',
        '',
        '# Mapeo principal: nombre_rushbet -> id_api_football',
        'TEAM_NAME_MAP = {',
    ]
    
    # Agrupar por liga para mejor legibilidad
    current_league = None
    
    for row in teams_data:
        team_id, team_name, league_id, league_name = row
        
        # Comentario de sección por liga
        if league_name != current_league:
            if current_league is not None:
                lines.append('')  # Línea en blanco entre ligas
            lines.append(f'    # --- {league_name} ---')
            current_league = league_name
        
        # Nombre principal
        lines.append(f'    "{team_name}": {team_id},')
        
        # Generar aliases
        aliases = generate_aliases(team_name)
        for alias in aliases[1:]:  # Skip el primero (es el original)
            lines.append(f'    "{alias}": {team_id},  # Alias')
    
    lines.append('}')
    lines.append('')
    lines.append('')
    lines.append('def get_mapped_team_id(team_name: str) -> int | None:')
    lines.append('    """')
    lines.append('    Busca el ID de API-Football para un nombre de equipo de Rushbet.')
    lines.append('    Retorna None si no hay mapeo.')
    lines.append('    """')
    lines.append('    # Búsqueda exacta')
    lines.append('    if team_name in TEAM_NAME_MAP:')
    lines.append('        return TEAM_NAME_MAP[team_name]')
    lines.append('    ')
    lines.append('    # Búsqueda case-insensitive')
    lines.append('    lower_name = team_name.lower()')
    lines.append('    for key, value in TEAM_NAME_MAP.items():')
    lines.append('        if key.lower() == lower_name:')
    lines.append('            return value')
    lines.append('    ')
    lines.append('    return None')
    lines.append('')
    
    return '\n'.join(lines)

def main():
    print("🔍 Consultando base de datos...")
    teams = fetch_teams_from_db()
    
    if not teams:
        print("❌ No se encontraron equipos en la base de datos.")
        print("   Asegúrate de haber sincronizado al menos una liga.")
        return
    
    print(f"✅ Encontrados {len(teams)} equipos.")
    
    # Generar contenido
    content = generate_mapping_file(teams)
    
    # Guardar archivo
    output_path = ROOT / "app" / "sports" / "football" / "config" / "team_mapping.py"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Archivo generado: {output_path}")
    print("")
    print("📝 PRÓXIMOS PASOS:")
    print("   1. Revisa el archivo generado")
    print("   2. Agrega manualmente aliases para nombres que varían en Rushbet")
    print("   3. Ejemplo: Si Rushbet usa 'Man Utd', agrega:")
    print('      "Man Utd": 33,  # Alias manual')

if __name__ == "__main__":
    main()
