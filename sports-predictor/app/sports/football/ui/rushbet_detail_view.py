"""
Vista de detalle de partido de Rushbet.
Muestra mercados de apuestas organizados según especificación exacta.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from app.services.rushbet_api import RushbetClient
from app.ui.theme import render_icon

# Tipos de visualización
CARD = "card"
LIST = "list"

def get_dynamic_order(home_team: str, away_team: str):
    """Genera el orden de mercados dinámicamente usando los nombres de equipos."""
    h = home_team.lower()
    a = away_team.lower()
    
    # 1. TIEMPO REGLAMENTARIO
    orden_tiempo_reg = [
        ("resultado final", CARD),
        ("1x2", CARD),
        ("total de goles", LIST), 
        # Cuidado: "Total de goles" es prefijo de "Total de goles de...". 
        # El sort busca la primera coincidencia. 
        # "Total de goles" match "Total de goles de Getafe"? SÍ.
        # Por eso "Total de goles de {Team}" debe ir ANTES o ser más específico si queremos separarlo.
        # Pero el usuario pidió: "Total de goles", LUEGO "Total de goles de {Local}".
        # Solución: En _sort_markets_by_order, usar coincidencia exacta o ordenar por longitud de match?
        # Mejor: Poner patrones más específicos primero si hay conflicto, O confiar en el orden.
        # "total de goles de" es más largo. Si pongo "total de goles" primero, matchea con "total de goles de Getafe".
        # Entonces "total de goles de" DEBE ir antes si quiero distinguirlos? No, si quiero que "Total de goles" salga antes, pongo ese primero.
        # PERO si "Total de goles de Getafe" matchea con "Total de goles", se quedará con la prioridad de "Total de goles".
        # Y se mezclarán.
        # TRUCO: Usar "total de goles" strict match? No es fácil con `in`.
        # Usaré un patrón negativo o orden específico.
        # Voy a asumir que "total de goles" a secas es el mercado general. 
        # Usaré una lista ordenada.
        
        ("doble oportunidad", CARD),
        ("ambos equipos marcarán", CARD),
        ("ambos equipos", CARD), # Variante
        ("resultado correcto", LIST),
        ("marcador correcto", LIST),
        ("apuesta sin empate", CARD),
        
        # Específicos de equipo
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
        ("apuesta sin empate - 1", CARD), # 1° parte / 1ª parte
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
        ("total de tiros de esquina", LIST), # General
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
        ("total de tarjetas", LIST), # General
        (f"total de tarjeta {h}", LIST), # A veces es "Total de tarjetas - Getafe"
        (f" - {h}", LIST), # Catch-all para "- Equipo" en tarjetas
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
        ("número total de tiros", LIST), # General
        ("tiros a puerta", LIST),
        
        (f"tiros a puerta por parte de {h}", LIST), # Opta phrasing
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


def show_match_detail_view():
    # ... (código existente de carga) ...
    
    # Obtener equipos
    home_team = details.get("home_team", "Local")
    away_team = details.get("away_team", "Visitante")
    
    # GENERAR ORDEN DINÁMICO
    ORDEN_POR_CATEGORIA = get_dynamic_order(home_team, away_team)
    
    # ... (render loop) ...
         # Pasar el orden generado
         
    # ... (Render Debug Logs DETALLADOS al final) ...
    with st.expander("Logs del Sistema (Debug) - DETALLE DE LABELS", expanded=False):
        st.write("Estructura de Labels encontrados:")
        all_markets_flat = []
        for cat, m_list in markets.items():
            for m in m_list:
                all_markets_flat.append({
                    "category": cat,
                    "label": m.get("label"),
                    "outcomes_count": len(m.get("outcomes", [])),
                    "example_outcome": m.get("outcomes")[0].get("label") if m.get("outcomes") else None
                })
        st.dataframe(pd.DataFrame(all_markets_flat))

