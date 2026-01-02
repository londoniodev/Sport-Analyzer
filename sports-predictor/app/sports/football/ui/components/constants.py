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
    
    # 1. TIEMPO REGLAMENTARIO
    orden_tiempo_reg = [
        ("resultado final", CARD),
        ("1x2", CARD),
        ("total de goles", LIST), 
        ("doble oportunidad", CARD),
        ("ambos equipos marcarán", CARD),
        ("ambos equipos", CARD),
        ("resultado correcto", LIST),
        ("marcador correcto", LIST),
        ("apuesta sin empate", CARD),
        
        (f"total de goles de {h}", LIST),
        (f"total de goles de {a}", LIST),
        
        ("descanso/tiempo", LIST),
        ("medio tiempo/final", LIST),
        ("hándicap", LIST),
        ("handicap", LIST),
        
        (f"victoria de {h} y ambos", CARD),
        (f"victoria de {a} y ambos", CARD),
        
        ("gol en ambas mitades", CARD),
    ]

    # 2. MEDIO TIEMPO
    orden_medio_tiempo = [
        ("descanso", CARD),
        ("apuesta sin empate - 1", CARD), 
        ("apuesta sin empate -1", CARD),
        ("doble oportunidad - 1", CARD),
        ("doble oportunidad -1", CARD),
        ("ambos equipos marcarán - 1", CARD),
        ("total de goles - 1", LIST),
        
        (f"total de goles de {h} - 1", LIST),
        (f"total de goles de {a} - 1", LIST),
        
        ("resultado correcto - 1", LIST),
        
        ("2° parte", CARD),
        ("2ª parte", CARD),
        ("2.ª parte", CARD),
        
        ("apuesta sin empate - 2", CARD),
        ("doble oportunidad - 2", CARD),
        ("ambos equipos marcarán - 2", CARD),
        
        ("total de goles - 2", LIST),
        (f"total de goles de {h} - 2", LIST),
        (f"total de goles de {a} - 2", LIST),
    ]

    # 3. CORNERS
    orden_corners = [
        ("total de tiros de esquina", LIST), 
        ("total de esquina", LIST),
        
        (f"esquina a favor de {h}", LIST),
        (f"esquina a favor de {a}", LIST),
        
        ("más tiros de esquina", CARD),
        ("mas tiros de esquina", CARD),
        ("más córners", CARD),
        
        ("hándicap de tiros de esquina", LIST),
        ("handicap de esquina", LIST),
        
        ("siguiente tiro de esquina", CARD),
        
        # Mitades
        ("total de tiros de esquina - 1", LIST),
        (f"esquina por parte de {h} - 1", LIST),
        (f"esquina por parte de {a} - 1", LIST),
        
        ("total de tiros de esquina - 2", LIST),
        (f"esquina a favor de {h} - 2", LIST),
        (f"esquina a favor de {a} - 2", LIST),
        
        ("más córners - 1", CARD),
        ("más córners - 2", CARD),
    ]

    # 4. PARTIDO Y TARJETAS
    orden_tarjetas = [
        ("total de tarjetas", LIST), 
        (f"total de tarjeta {h}", LIST),
        (f" - {h}", LIST), 
        (f"total de tarjeta {a}", LIST),
        (f" - {a}", LIST),
        
        ("tarjeta roja mostrada", CARD),
        (f"tarjeta roja a {h}", CARD),
        (f"tarjeta roja a {a}", CARD),
        
        ("más tarjetas", CARD),
        ("tarjetas hándicap", LIST),
    ]

    # 5. DISPAROS EQUIPO
    orden_disparos = [
        ("número total de disparos", LIST),
        ("número total de tiros", LIST),
        ("tiros a puerta", LIST),
        
        (f"tiros a puerta por parte de {h}", LIST),
        (f"por parte de {h}", LIST),
        
        (f"tiros a puerta por parte de {a}", LIST),
        (f"por parte de {a}", LIST),
        
        ("más tiros a puerta", CARD),
    ]

    # 6. EVENTOS
    orden_eventos = [
        ("primer gol", CARD),
        ("propia meta", CARD),
        (f"victoria de {h} sin recibir", CARD),
        (f"victoria de {a} sin recibir", CARD),
        (f"{h} gana al menos", CARD),
        (f"{a} gana al menos", CARD),
        ("al palo", CARD),
    ]
    
    # Static ones
    orden_handicap_3way = [
        ("hándicap 3-way", LIST),
        ("handicap 3-way", LIST),
    ]
    
    orden_asiaticas = [
        ("hándicap asiático", LIST),
        ("handicap asiático", LIST),
        ("total asiático", LIST),
    ]

    return {
        "tiempo_reglamentario": orden_tiempo_reg,
        "medio_tiempo": orden_medio_tiempo,
        "corners": orden_corners,
        "tarjetas_equipo": orden_tarjetas,
        "disparos_equipo": orden_disparos,
        "eventos_partido": orden_eventos,
        "handicap_3way": orden_handicap_3way,
        "lineas_asiaticas": orden_asiaticas,
    }
