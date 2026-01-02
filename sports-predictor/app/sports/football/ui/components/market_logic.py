import copy

def _redistribute_markets(markets: dict) -> dict:
    """
    Reorganiza mercados mal ubicados en el JSON original hacia sus categorías correctas
    según la arquitectura de UI definida.
    """
    m = copy.deepcopy(markets)
    
    # 1. Mover 'Paradas del portero' desde tiempo_reglamentario o eventos
    # 2. Buscar 'Disparos jugador' mal ubicados
    
    search_cats = ["tiempo_reglamentario", "eventos_partido"]
    
    for src in search_cats:
        if src not in m: continue
        
        kept = []
        for mkt in m[src]:
            lbl = mkt.get("label", "").lower()
            moved = False
            
            # REGLA: Paradas del portero
            if "parada" in lbl and "portero" in lbl:
                if "paradas_portero" not in m: m["paradas_portero"] = []
                m["paradas_portero"].append(mkt)
                moved = True
                
            # REGLA: Disparos jugador (si apareciera aquí por error)
            elif "disparo" in lbl and "jugador" in lbl:
                 if "disparos_jugador" not in m: m["disparos_jugador"] = []
                 m["disparos_jugador"].append(mkt)
                 moved = True
                 
            # REGLA: Gol en ambas mitades -> MANTENER en Tiempo Reglamentario (Solicitud explicita)
            # REGLA: Victoria y ambos marcan -> MANTENER en Tiempo Reglamentario (Solicitud explicita)
            # Aunque vengan en eventos_partido, los movemos A tiempo_reglamentario si están en eventos
            elif src == "eventos_partido":
                if "gol en ambas mitades" in lbl or ("victoria" in lbl and "ambos" in lbl):
                     if "tiempo_reglamentario" not in m: m["tiempo_reglamentario"] = []
                     m["tiempo_reglamentario"].append(mkt)
                     moved = True

            if not moved:
                kept.append(mkt)
        
        m[src] = kept

    # 3. Separar 'Apuestas Especiales' de 'Asistencias'
    # En JSON, 'asistencias_jugador' a veces trae 'Marcará o dará asistencia'
    if "asistencias_jugador" in m:
        kept_asist = []
        for mkt in m["asistencias_jugador"]:
            lbl = mkt.get("label", "").lower()
            if "marcará o dará" in lbl or "asistencia" in lbl: # A veces vienen juntos
                 # Si es hibrido, va a especiales
                 if "marcará o dará" in lbl:
                     if "apuestas_especiales_jugador" not in m: m["apuestas_especiales_jugador"] = []
                     m["apuestas_especiales_jugador"].append(mkt)
                 else:
                     kept_asist.append(mkt)
            else:
                kept_asist.append(mkt)
        m["asistencias_jugador"] = kept_asist

    return m

def _sort_markets_by_order(markets: list, orden: list) -> list:
    """Ordena mercados según lista de patrones."""
    def get_priority(market):
        label_lower = market.get("label", "").lower()
        for i, (pattern, _) in enumerate(orden):
            if pattern in label_lower:
                return i
        return 999
    
    return sorted(markets, key=get_priority)

def _get_market_format(label: str, orden: list) -> str:
    """Determina si el mercado es card o list según el orden."""
    label_lower = label.lower()
    for pattern, formato in orden:
        if pattern in label_lower:
            return formato
    return "card"
