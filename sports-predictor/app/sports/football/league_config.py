"""
Configuración de Ligas - Lista centralizada de ligas permitidas para el ETL.
Edita este archivo para agregar o quitar ligas fácilmente.

Para encontrar el ID de una liga, usa: https://www.api-football.com/documentation-v3#tag/Leagues
O sincroniza todas las ligas y busca en la tabla football_league.
"""

# ═══════════════════════════════════════════════════════════════════════════════
# LIGAS ACTIVAS - Agregar/quitar IDs aquí para modificar qué ligas se sincronizan
# ═══════════════════════════════════════════════════════════════════════════════

PRIORITY_LEAGUES = {
    # ─────────────────────────────────────────────────────────────────────────
    # TIER 1: Ligas principales con mayor volumen de apuestas
    # ─────────────────────────────────────────────────────────────────────────
    "TIER_1": [
        39,   # Inglaterra - Premier League
        140,  # España - La Liga
        135,  # Italia - Serie A
        78,   # Alemania - Bundesliga
        61,   # Francia - Ligue 1
        2,    # UEFA - Champions League
        13,   # CONMEBOL - Libertadores
        239,  # Colombia - Liga BetPlay
    ],
    
    # ─────────────────────────────────────────────────────────────────────────
    # TIER 2: Ligas secundarias con buen mercado de apuestas
    # ─────────────────────────────────────────────────────────────────────────
    "TIER_2": [
        3,    # UEFA - Europa League
        40,   # Inglaterra - Championship
        71,   # Brasil - Serie A
        253,  # USA - MLS
        262,  # México - Liga MX
        94,   # Portugal - Primeira Liga
        88,   # Países Bajos - Eredivisie
        307,  # Arabia Saudí - Pro League  # <-- NUEVA: Liga Saudí
        # 128, # Argentina - Primera División (descomentear para agregar)
        # 11,  # Copa del Rey España (descomentear para agregar)
    ],
    
    # ─────────────────────────────────────────────────────────────────────────
    # INTERNACIONALES: Torneos de selecciones
    # ─────────────────────────────────────────────────────────────────────────
    "INTERNATIONAL": [
        1,    # FIFA - Mundial
        4,    # UEFA - Eurocopa
        9,    # CONMEBOL - Copa América
        # 37, # Amistosos internacionales (descomentear para agregar)
    ],
}

# ═══════════════════════════════════════════════════════════════════════════════
# NO MODIFICAR - Generación automática del set de IDs permitidos
# ═══════════════════════════════════════════════════════════════════════════════

ALLOWED_LEAGUE_IDS = set(
    league_id 
    for tier in PRIORITY_LEAGUES.values() 
    for league_id in tier
)

def get_all_league_ids() -> set:
    """Retorna el set de todos los IDs de ligas permitidas."""
    return ALLOWED_LEAGUE_IDS

def get_leagues_by_tier(tier: str) -> list:
    """Retorna la lista de IDs para un tier específico."""
    return PRIORITY_LEAGUES.get(tier, [])

def is_league_allowed(league_id: int) -> bool:
    """Verifica si una liga está en la lista de permitidas."""
    return league_id in ALLOWED_LEAGUE_IDS


# ═══════════════════════════════════════════════════════════════════════════════
# MAPEO DE REGIONES - Para categorizar ligas por continente
# ═══════════════════════════════════════════════════════════════════════════════

REGION_MAP = {
    'Europa': [
        'England', 'Spain', 'Italy', 'Germany', 'France', 'Portugal', 'Netherlands', 
        'Austria', 'Belgium', 'Croatia', 'Scotland', 'Norway', 'Switzerland',
        'Poland', 'Wales', 'Estonia', 'Denmark', 'Ukraine', 'Israel', 'Iceland',
        'Sweden', 'Turkey', 'Greece', 'Georgia', 'Serbia', 'Hungary', 
        'Czech Republic', 'Slovakia'
    ],
    'Sudamérica': [
        'Brazil', 'Argentina', 'Colombia', 'Ecuador', 'Paraguay', 'Uruguay', 'Bolivia'
    ],
    'Norteamérica': [
        'USA', 'Mexico', 'Canada', 'Curacao', 'Haiti', 'Panama', 'Costa Rica', 'Jamaica'
    ],
    'África': [
        'Algeria', 'Cape Verde', 'Ivory Coast', 'Egypt', 'Ghana', 'Morocco', 
        'Senegal', 'South Africa', 'Tunisia', 'Mali'
    ],
    'Asia': [
        'Saudi Arabia', 'Australia', 'South Korea', 'Iran', 'Japan', 'Jordan', 
        'Qatar', 'Uzbekistan', 'Iraq'
    ],
    'Oceanía': [
        'New Zealand', 'Solomon Islands'
    ],
    'Internacional': ['World']
}

def get_region(country: str) -> str:
    """Determina la región de un país."""
    for region, countries in REGION_MAP.items():
        if country in countries:
            return region
    return 'Otros'
