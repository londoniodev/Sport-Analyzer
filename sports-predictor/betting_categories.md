# Categorías de Apuestas y Estadísticas Predictivas

Esta es una lista de las categorías y mercados de apuestas disponibles en la aplicación. Para cada mercado se especifican las **opciones fijas** y las **estadísticas predictivas** recomendadas.

---

## 1. Resultado del Partido (Tiempo Reglamentario)

| Mercado | Opciones | Estadísticas Predictivas |
|---------|----------|--------------------------|
| **Resultado Final (1X2)** | `Equipo 1`, `Empate`, `Equipo 2` | ELO Rating, xG (Expected Goals), Forma reciente (últimos 5), Head-to-Head histórico, Ventaja local |
| **Doble Oportunidad** | `1X`, `12`, `X2` | Derivado de 1X2, probabilidad combinada |
| **Apuesta sin empate** | `Equipo 1`, `Equipo 2` | ELO Rating sin factor empate, xG diferencial |
| **Ambos equipos marcarán (BTTS)** | `Sí`, `No` | % BTTS histórico por equipo, xG ofensivo vs xGA defensivo |
| **Resultado Correcto** | `0-0`, `1-0`, `2-1`, etc. | Distribución Poisson basada en xG, promedios de goles |
| **Descanso/Final** | Combinaciones `1/1`, `1/X`, `X/2`, etc. | Rendimiento por mitades, tendencia de goles por período |
| **Victoria + BTTS** | `Local + Sí`, `Visitante + Sí` | Combinación de modelos 1X2 y BTTS |
| **Gol en ambas mitades** | `Sí`, `No` | Distribución temporal de goles, promedios por mitad |

---

## 2. Goles (Over/Under)

| Mercado | Opciones | Estadísticas Predictivas |
|---------|----------|--------------------------|
| **Total de goles** | `Más de X.5`, `Menos de X.5` | xG total esperado, promedio goles/partido, Poisson |
| **Total de goles por equipo** | `Más de X.5`, `Menos de X.5` | xG por equipo, promedio goles anotados |
| **Total de goles por mitad** | `Más de X.5`, `Menos de X.5` | % goles por período, distribución temporal |
| **Primer gol** | `Equipo 1`, `Sin goles`, `Equipo 2` | Tiempo promedio al primer gol, xG primeros 15 min |

---

## 3. Hándicaps y Líneas Asiáticas

| Mercado | Opciones | Estadísticas Predictivas |
|---------|----------|--------------------------|
| **Hándicap 3-Way** | `Equipo 1 (±X)`, `Empate`, `Equipo 2 (±X)` | Margen de victoria esperado, xG diferencial |
| **Hándicap Asiático** | `±0.25`, `±0.5`, `±0.75`, `±1.0`... | Distribución de resultados, varianza de goles |
| **Total Asiático** | `Más/Menos de X.25/X.5/X.75` | xG total con ajuste de varianza |

---

## 4. Medio Tiempo (1ª y 2ª Parte)

| Mercado | Opciones | Estadísticas Predictivas |
|---------|----------|--------------------------|
| **Descanso (1X2 - 1ª parte)** | `1`, `X`, `2` | Rendimiento 1ª mitad, xG primeros 45 min |
| **Total goles 1ª/2ª parte** | `Más de X.5`, `Menos de X.5` | Distribución temporal de goles |
| **Resultado Correcto - 1ª parte** | `0-0`, `1-0`, etc. | Poisson ajustado a 45 min |

---

## 5. Tiros de Esquina (Córners)

| Mercado | Opciones | Estadísticas Predictivas |
|---------|----------|--------------------------|
| **Más Tiros de Esquina** | `Equipo 1`, `Empate`, `Equipo 2` | Promedio corners/partido, estilo de juego (posesión, ataques) |
| **Total de Tiros de Esquina** | `Más de X.5`, `Menos de X.5` | Promedio combinado corners, correlación con posesión |
| **Total por equipo** | `Más de X.5`, `Menos de X.5` | Corners forzados vs concedidos |
| **Hándicap Corners 3-Way** | `Equipo 1 (±X)`, `Empate`, `Equipo 2 (±X)` | Diferencial promedio de corners |
| **Siguiente Córner** | `Equipo 1`, `Sin córner`, `Equipo 2` | Momentum de juego (live) |

---

## 6. Tarjetas

| Mercado | Opciones | Estadísticas Predictivas |
|---------|----------|--------------------------|
| **Total de Tarjetas** | `Más de X.5`, `Menos de X.5` | Promedio tarjetas/partido, historial árbitro |
| **Total por equipo** | `Más de X.5`, `Menos de X.5` | Tarjetas recibidas promedio, intensidad defensiva |
| **Tarjeta Roja mostrada** | `Sí`, `No` | Historial rojas, árbitro, rivalidad |
| **Más Tarjetas** | `Equipo 1`, `Empate`, `Equipo 2` | Diferencial de tarjetas recibidas |
| **Jugador recibirá tarjeta** | `Sí` (por jugador) | Tarjetas acumuladas, posición, minutos jugados |

---

## 7. Disparos

| Mercado | Opciones | Estadísticas Predictivas |
|---------|----------|--------------------------|
| **Total de Disparos a Puerta** | `Más de X.5`, `Menos de X.5` | Promedio tiros a puerta, estilo ofensivo |
| **Total por equipo** | `Más de X.5`, `Menos de X.5` | xG vs tiros reales, eficiencia ofensiva |
| **Más Tiros a Puerta** | `Equipo 1`, `Empate`, `Equipo 2` | Dominio ofensivo, posesión |
| **Disparos del Jugador** | `Más de X.5` | Promedio tiros por 90 min, minutos esperados |

---

## 8. Goleador (Mercados de Jugador)

> [!NOTE]
> Para optimizar recursos, se calcula dinámicamente basándose en el **Top 5 de goleadores** por equipo.

| Mercado | Opciones | Estadísticas Predictivas |
|---------|----------|--------------------------|
| **Primer Goleador** | Lista de jugadores | xG del jugador, probabilidad de titular, % primer gol histórico |
| **Marcará (Anytime)** | `Sí` (por jugador) | xG/90, minutos esperados, momento de forma |
| **Marca al menos 2 goles** | `Sí` (por jugador) | xG acumulado, historial de dobletes |
| **Hat-trick** | `Sí` (por jugador) | Muy baja probabilidad, usar xG^3 |

---

## 9. Asistencias de Jugador

| Mercado | Opciones | Estadísticas Predictivas |
|---------|----------|--------------------------|
| **Dará una Asistencia** | `Sí` (por jugador) | xA/90, Key Passes/90, posición (mediocampistas ofensivos) |
| **Marcará o Asistirá** | `Sí` (por jugador) | Combinación xG + xA, participaciones en gol |

---

## 10. Paradas del Portero

| Mercado | Opciones | Estadísticas Predictivas |
|---------|----------|--------------------------|
| **Paradas del Portero** | `Más de X.5`, `Menos de X.5` | xG rival (más xG = más oportunidades de paradas), save % |

---

## 11. Eventos del Partido

| Mercado | Opciones | Estadísticas Predictivas |
|---------|----------|--------------------------|
| **Gol en Propia Meta** | `Sí`, `No` | Historial muy bajo (~1-2%), corners/centros concedidos |
| **Victoria sin recibir gol** | `Equipo 1 Sí`, `Equipo 2 Sí` | Clean sheet %, xGA defensivo |
| **Gana al menos una mitad** | `Equipo 1`, `Equipo 2` | Rendimiento por mitades, consistencia |
| **Al Palo** | `Sí`, `No` | Correlación con tiros fuera del arco |
| **Fueras de Juego** | `Más de X.5`, `Menos de X.5` | Línea defensiva, estilo ofensivo rival |

---

## 12. Faltas

| Mercado | Opciones | Estadísticas Predictivas |
|---------|----------|--------------------------|
| **Faltas Concedidas** | `Más de X.5`, `Menos de X.5` | Promedio faltas/partido, intensidad defensiva |
| **Faltas cometidas por equipo** | Por equipo | Estilo de juego, presión alta vs baja |

---

## Fuentes de Datos Recomendadas

| Estadística | Fuentes |
|-------------|---------|
| **xG / xGA** | Understat, FBref, WhoScored |
| **ELO Rating** | ClubELO, FiveThirtyEight |
| **Forma Reciente** | API-Football, FlashScore |
| **Corners/Tarjetas/Disparos** | API-Football, Sofascore |
| **Estadísticas de Jugador** | FBref, Transfermarkt, SofaScore |
| **Historial Árbitro** | Transfermarkt, BetStudy |

---

## Modelos Predictivos Sugeridos

| Tipo de Mercado | Modelo Recomendado |
|-----------------|-------------------|
| **1X2 / Doble Oportunidad** | Regresión Logística Multinomial, ELO-based |
| **Over/Under Goles** | Distribución Poisson, xG-based |
| **BTTS** | Clasificación Binaria (Random Forest, XGBoost) |
| **Resultado Correcto** | Poisson Bivariado |
| **Corners/Tarjetas** | Regresión Poisson para conteos |
| **Goleador/Asistencias** | xG/xA individuales + minutos esperados |
| **Hándicaps** | Margen esperado + distribución normal/Poisson |
