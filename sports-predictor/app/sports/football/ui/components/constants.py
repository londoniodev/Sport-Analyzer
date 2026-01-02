# Tipos de visualización
CARD = "card"
LIST = "list"

# Mapeo de Tabs a Categorías API
TABS_CONFIG = {
    "PARTIDO": ["tiempo_reglamentario", "medio_tiempo", "corners", "tarjetas_equipo", "disparos_equipo", "faltas_equipo", "eventos_partido"],
    "JUGADORES": ["disparos_jugador", "goleador", "tarjetas_jugador", "apuestas_especiales_jugador", "asistencias_jugador", "goles_jugador", "paradas_portero"],
    "HANDICAP": ["handicap_3way", "lineas_asiaticas"]
}

# Nombres legibles
NOMBRES_CATEGORIAS = {
    "tiempo_reglamentario": "Tiempo Reglamentario",
    "medio_tiempo": "Medio Tiempo",
    "corners": "Tiros de Esquina",
    "tarjetas_equipo": "Partido y Tarjetas del Equipo",
    "disparos_equipo": "Partido y Disparos del Equipo",
    "faltas_equipo": "Partido y Faltas del Equipo",
    "eventos_partido": "Eventos del Partido",
    "disparos_jugador": "Disparos a Puerta del Jugador",
    "goleador": "Goleador",
    "tarjetas_jugador": "Tarjetas Jugadores",
    "apuestas_especiales_jugador": "Apuestas Especiales Jugador",
    "asistencias_jugador": "Asistencias del Jugador",
    "goles_jugador": "Goles del Jugador",
    "paradas_portero": "Paradas del Portero",
    "handicap_3way": "Hándicap 3-Way",
    "lineas_asiaticas": "Líneas Asiáticas"
}

def get_dynamic_order(home_team: str, away_team: str):
    """Genera el orden de mercados dinámicamente usando los nombres de equipos."""
    h = home_team.lower()
    a = away_team.lower()
    
    # 1. TIEMPO REGLAMENTARIO (orden exacto del usuario)
    orden_tiempo_reg = [
        ("resultado final", CARD),
        ("total de goles", LIST),
        ("doble oportunidad", CARD),
        ("ambos equipos marcarán", CARD),
        ("resultado correcto", LIST),
        ("apuesta sin empate", CARD),
        (f"total de goles de {h}", LIST),
        (f"total de goles de {a}", LIST),
        ("descanso/tiempo reglamentario", LIST),
        ("hándicap ", LIST),
        (f"victoria de {h} y ambos equipos marcan", CARD),
        (f"victoria de {a} y ambos equipos marcan", CARD),
        ("gol en ambas mitades", CARD),
    ]

    # 2. MEDIO TIEMPO (orden exacto del usuario)
    orden_medio_tiempo = [
        ("descanso", CARD),
        ("apuesta sin empate - 1", CARD),
        ("apuesta sin empate - 1.ª parte", CARD),
        ("doble oportunidad - 1", CARD),
        ("doble oportunidad - 1.ª parte", CARD),
        ("ambos equipos marcarán - 1", CARD),
        ("ambos equipos marcarán - 1.ª parte", CARD),
        ("total de goles - 1", LIST),
        ("total de goles - 1.ª parte", LIST),
        (f"total de goles de {h} - 1ª mitad", LIST),
        (f"total de goles de {a} - 1ª mitad", LIST),
        ("resultado correcto - 1", LIST),
        ("resultado correcto - 1.ª parte", LIST),
        ("2ª parte", CARD),
        ("2.ª parte", CARD),
        ("apuesta sin empate - 2", CARD),
        ("apuesta sin empate - 2.ª parte", CARD),
        ("doble oportunidad - 2", CARD),
        ("doble oportunidad - 2.ª parte", CARD),
        ("ambos equipos marcarán - 2", CARD),
        ("ambos equipos marcarán - 2.ª parte", CARD),
        ("total de goles - 2", LIST),
        ("total de goles - 2.ª parte", LIST),
        (f"total de goles de {h} - 2ª mitad", LIST),
        (f"total de goles de {a} - 2ª mitad", LIST),
    ]

    # 3. TIROS DE ESQUINA (orden exacto del usuario)
    orden_corners = [
        ("total de tiros de esquina", LIST),
        (f"total de tiros de esquina a favor de {h}", LIST),
        (f"total de tiros de esquina a favor de {a}", LIST),
        ("más tiros de esquina", CARD),
        ("hándicap de tiros de esquina 3-way", LIST),
        ("siguiente tiro de esquina", CARD),
        ("total de tiros de esquina - 1", LIST),
        ("total de tiros de esquina - 1.ª parte", LIST),
        (f"número total de tiros de esquina por parte de {h} - 1ª parte", LIST),
        (f"número total de tiros de esquina por parte de {a} - 1ª parte", LIST),
        ("total de tiros de esquina - 2", LIST),
        ("total de tiros de esquina - 2.ª parte", LIST),
        (f"número total de tiros de esquina por parte de {h} - 2ª parte", LIST),
        (f"número total de tiros de esquina por parte de {a} - 2ª parte", LIST),
        ("más córners - 1", CARD),
        ("más córners - 1.ª parte", CARD),
        ("más córners - 2", CARD),
        ("más córners - 2.ª parte", CARD),
    ]

    # 4. PARTIDO Y TARJETAS DEL EQUIPO (orden exacto del usuario)
    orden_tarjetas = [
        ("total de tarjetas", LIST),
        (f"total de tarjetas - {h}", LIST),
        (f"total de tarjetas - {a}", LIST),
        ("tarjeta roja mostrada", CARD),
        (f"tarjeta roja a {h}", CARD),
        (f"tarjeta roja a {a}", CARD),
        ("más tarjetas", CARD),
        ("tarjetas hándicap 3-way", LIST),
    ]

    # 5. PARTIDO Y DISPAROS DEL EQUIPO (orden exacto del usuario)
    orden_disparos = [
        ("número total de disparos a puerta", LIST),
        (f"número total de tiros a puerta por parte de {h}", LIST),
        (f"número total de tiros a puerta por parte de {a}", LIST),
        ("más tiros a puerta", CARD),
    ]
    
    # 6. PARTIDO Y FALTAS DEL EQUIPO
    orden_faltas = [
        ("faltas concedidas", LIST),
        (f"número total de faltas cometidas por {h}", LIST),
        (f"número total de faltas cometidas por {a}", LIST),
    ]

    # 7. HANDICAP 3-WAY (orden exacto del usuario)
    # Columnas: Comienza con, Equipo Local, Equipo Visitante, Empate
    orden_handicap_3way = [
        ("hándicap 3-way", LIST),
        ("handicap 3-way", LIST),
    ]
    
    # 8. LINEAS ASIATICAS (orden exacto del usuario)
    orden_asiaticas = [
        ("hándicap asiático", LIST),
        ("handicap asiático", LIST),
        ("total asiático", LIST),
        ("hándicap asiático - 1", LIST),
        ("hándicap asiático - 1.ª parte", LIST),
        ("total asiático - 1", LIST),
        ("total asiático - 1.ª parte", LIST),
    ]

    # 9. EVENTOS DEL PARTIDO (orden exacto del usuario)
    orden_eventos = [
        ("primer gol", CARD),
        ("gol en propia meta", CARD),
        (f"victoria de {h} sin recibir goles en contra", CARD),
        (f"victoria de {a} sin recibir goles en contra", CARD),
        (f"{h} gana al menos una mitad", CARD),
        (f"{a} gana al menos una mitad", CARD),
        ("al palo durante el partido", CARD),
        (f"{h} al palo durante el partido", CARD),
        (f"{a} al palo durante el partido", CARD),
    ]

    return {
        "tiempo_reglamentario": orden_tiempo_reg,
        "medio_tiempo": orden_medio_tiempo,
        "corners": orden_corners,
        "tarjetas_equipo": orden_tarjetas,
        "disparos_equipo": orden_disparos,
        "faltas_equipo": orden_faltas,
        "eventos_partido": orden_eventos,
        "handicap_3way": orden_handicap_3way,
        "lineas_asiaticas": orden_asiaticas,
    }

