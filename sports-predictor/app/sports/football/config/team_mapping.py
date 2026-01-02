"""
Team Name Mapping Configuration.

Este módulo centraliza la traducción de nombres de equipos entre distintas fuentes 
(e.g., Rushbet/Kambi) y el estándar de API-Football.
"""

# Mapeo Principal: { "Nombre Rushbet": (API_ID, "Nombre API-Football") }
TEAM_NAME_MAP = {
    # --- ESPAÑA (La Liga) ---
    "Athletic Club": (531, "Athletic Club"),
    "Atlético de Madrid": (530, "Atletico Madrid"),
    "Atlético Madrid": (530, "Atletico Madrid"),
    "FC Barcelona": (529, "Barcelona"),
    "Barcelona": (529, "Barcelona"),
    "Real Betis": (543, "Real Betis"),
    "Celta de Vigo": (538, "Celta Vigo"),
    "RC Celta": (538, "Celta Vigo"),
    "RCD Espanyol": (740, "Espanyol"),
    "Espanyol": (740, "Espanyol"),
    "Getafe CF": (546, "Getafe"),
    "Getafe": (546, "Getafe"),
    "Girona FC": (547, "Girona"),
    "Girona": (547, "Girona"),
    "UD Las Palmas": (724, "Las Palmas"),
    "Las Palmas": (724, "Las Palmas"),
    "CD Leganés": (723, "Leganes"),
    "Leganés": (723, "Leganes"),
    "RCD Mallorca": (798, "Mallorca"),
    "Mallorca": (798, "Mallorca"),
    "CA Osasuna": (727, "Osasuna"),
    "Osasuna": (727, "Osasuna"),
    "Rayo Vallecano": (728, "Rayo Vallecano"),
    "Real Madrid": (541, "Real Madrid"),
    "Real Sociedad": (548, "Real Sociedad"),
    "Sevilla FC": (536, "Sevilla"),
    "Sevilla": (536, "Sevilla"),
    "Valencia CF": (532, "Valencia"),
    "Valencia": (532, "Valencia"),
    "Real Valladolid": (720, "Valladolid"),
    "Valladolid": (720, "Valladolid"),
    "Villarreal CF": (533, "Villarreal"),
    "Villarreal": (533, "Villarreal"),
    "Alavés": (712, "Alaves"),
    "Deportivo Alavés": (712, "Alaves"),
    
    # --- INGLATERRA (Premier League) ---
    "Man City": (50, "Manchester City"),
    "Manchester City": (50, "Manchester City"),
    "Man Utd": (33, "Manchester United"),
    "Manchester United": (33, "Manchester United"),
    "Arsenal": (42, "Arsenal"),
    "Liverpool": (40, "Liverpool"),
    "Chelsea": (49, "Chelsea"),
    "Tottenham": (47, "Tottenham"),
    "Tottenham Hotspur": (47, "Tottenham"),
    "Newcastle": (34, "Newcastle"),
    "Aston Villa": (66, "Aston Villa"),
    "West Ham": (48, "West Ham"),
}

def get_mapped_team_id(rushbet_name: str) -> int:
    """Retorna el ID de API-Football dado el nombre de Rushbet."""
    # 1. Normalización básica (strip)
    clean_name = rushbet_name.strip()
    
    # 2. Búsqueda directa
    if clean_name in TEAM_NAME_MAP:
        return TEAM_NAME_MAP[clean_name][0]
        
    # 3. Búsqueda case-insensitive
    for key, (tid, _) in TEAM_NAME_MAP.items():
        if key.lower() == clean_name.lower():
            return tid
            
    return None

def get_mapped_team_name(rushbet_name: str) -> str:
    """Retorna el nombre estándar de API-Football."""
    if rushbet_name in TEAM_NAME_MAP:
        return TEAM_NAME_MAP[rushbet_name][1]
    return rushbet_name
