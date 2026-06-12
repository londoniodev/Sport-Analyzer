"""
World Cup 2026 - Scoring System for Polla Mundialista.

Implements the official scoring rules:
- Exact score: 12 pts
- Correct winner + same goal difference: 8 pts
- Correct draw (any score): 8 pts
- Correct winner (wrong difference): 5 pts
- Exact goals for one team: 2 pts
- Wrong prediction: 0 pts

Bonus:
- Correct penalty shootout qualifier: +3 pts
- Correct champion: +20 pts
- Correct runner-up: +10 pts
- Correct third place: +6 pts
"""


def calculate_match_points(
    pred_home: int,
    pred_away: int,
    actual_home: int,
    actual_away: int
) -> int:
    """
    Calcula los puntos obtenidos para una predicción de partido.
    Solo se otorga el mayor puntaje que aplique (no se acumulan).
    
    Args:
        pred_home: Goles predichos del equipo local
        pred_away: Goles predichos del equipo visitante
        actual_home: Goles reales del equipo local
        actual_away: Goles reales del equipo visitante
    
    Returns:
        Puntos ganados (0, 2, 5, 8, o 12)
    """
    # 1. Marcador exacto → 12 pts
    if pred_home == actual_home and pred_away == actual_away:
        return 12
    
    # Determinar resultados
    pred_diff = pred_home - pred_away
    actual_diff = actual_home - actual_away
    
    pred_result = "home" if pred_diff > 0 else ("away" if pred_diff < 0 else "draw")
    actual_result = "home" if actual_diff > 0 else ("away" if actual_diff < 0 else "draw")
    
    # 2. Empate correcto (sin importar goles) → 8 pts
    if pred_result == "draw" and actual_result == "draw":
        return 8
    
    # 3. Ganador correcto + misma diferencia de goles → 8 pts
    if pred_result == actual_result and pred_diff == actual_diff:
        return 8
    
    # 4. Ganador correcto (sin acertar diferencia) → 5 pts
    if pred_result == actual_result:
        return 5
    
    # 5. Goles exactos de uno de los dos equipos → 2 pts
    if pred_home == actual_home or pred_away == actual_away:
        return 2
    
    # 6. Predicción incorrecta → 0 pts
    return 0


def calculate_penalty_bonus(pred_qualifier_id: int, actual_qualifier_id: int) -> int:
    """
    Bono por acertar quién clasifica en penales.
    +3 pts si el partido se define en penales y aciertas al clasificado.
    """
    if pred_qualifier_id == actual_qualifier_id:
        return 3
    return 0


def calculate_podium_points(
    pred_champion: int,
    pred_runner_up: int,
    pred_third: int,
    actual_champion: int,
    actual_runner_up: int,
    actual_third: int
) -> int:
    """
    Calcula puntos del Podio Ideal (Final Soñada).
    - Campeón correcto: +20 pts
    - Subcampeón correcto: +10 pts
    - Tercer puesto correcto: +6 pts
    """
    points = 0
    if pred_champion == actual_champion:
        points += 20
    if pred_runner_up == actual_runner_up:
        points += 10
    if pred_third == actual_third:
        points += 6
    return points


def get_points_label(points: int) -> str:
    """Returns a human-readable label for the points earned."""
    labels = {
        12: "🎯 Marcador Exacto",
        8: "✅ Resultado + Diferencia",
        5: "👍 Ganador Correcto",
        2: "🔢 Goles Parciales",
        0: "❌ Incorrecto"
    }
    return labels.get(points, f"{points} pts")


# World Cup 2026 team API-Football IDs for bulk sync
WORLD_CUP_TEAM_IDS = [
    16, 1531, 17, 770,      # Group A: Mexico, South Africa, South Korea, Czech Republic
    5529, 1113, 1569, 15,   # Group B: Canada, Bosnia, Qatar, Switzerland
    6, 31, 2386, 1108,      # Group C: Brazil, Morocco, Haiti, Scotland
    2384, 2380, 20, 777,    # Group D: USA, Paraguay, Australia, Turkey
    25, 5530, 1501, 2382,   # Group E: Germany, Curacao, Ivory Coast, Ecuador
    1118, 12, 5, 28,        # Group F: Netherlands, Japan, Sweden, Tunisia
    1, 32, 22, 4673,        # Group G: Belgium, Egypt, Iran, New Zealand
    9, 1533, 23, 7,         # Group H: Spain, Cape Verde, Saudi Arabia, Uruguay
    2, 13, 1567, 1090,      # Group I: France, Senegal, Iraq, Norway
    26, 1559, 775, 1548,    # Group J: Argentina, Algeria, Austria, Jordan
    27, 1508, 1568, 8,      # Group K: Portugal, DR Congo, Uzbekistan, Colombia
    10, 3, 1504, 11         # Group L: England, Croatia, Ghana, Panama
]

WORLD_CUP_LEAGUE_ID = 1
WORLD_CUP_SEASON = 2026
