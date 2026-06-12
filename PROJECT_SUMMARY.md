# Resumen del Proyecto Sport-Analyzer (Insumo para IAs)

Este documento sirve como contexto consolidado y guía técnica detallada de **Sport-Analyzer** para que agentes de Inteligencia Artificial (IAs) o nuevos desarrolladores comprendan rápidamente la arquitectura, el modelo de datos, la lógica predictiva y los puntos de integración del sistema sin necesidad de explorar todo el código fuente.

---

## 1. Descripción General del Proyecto

**Sport-Analyzer** es un motor de análisis y predicción deportiva de alto rendimiento y una plataforma interactiva de apuestas de valor y simulación de la **Copa Mundial de la FIFA 2026** (Polla Mundialista).

El sistema se compone de:
1. **Frontend**: Aplicación SPA moderna en React + TypeScript + TailwindCSS.
2. **Backend**: API REST de alto rendimiento implementada en FastAPI (Python) que utiliza SQLModel (una envoltura sobre SQLAlchemy y Pydantic) para interactuar con la base de datos de manera intuitiva y tipada.
3. **Base de Datos**: PostgreSQL 15 (desplegable en Docker), con soporte integrado para **Modo Demo** (ejecución en memoria/sin base de datos, en cuyo caso las predicciones funcionan con sliders manuales de estadísticas).
4. **Módulo de Raspado (Scraping) e Integraciones**:
   - Cliente inverso no oficial para Rushbet (proveedor Kambi) para obtener mercados en tiempo real y cuotas (odds).
   - Raspador de planteles del mundial desde Wikipedia.
   - Cargador de estadísticas de rendimiento y ELO de selecciones de fútbol.

---

## 2. Estructura de Directorios

El repositorio se organiza de la siguiente manera:

* **`/app`**: Código del backend FastAPI.
  * **`/core`**: Núcleo del sistema (inicialización de base de datos, interfaces abstractas e infraestructura de registro de deportes).
  * **`/services`**: Integración con servicios externos (Rushbet API y cliente HTTP base).
  * **`/sports`**: Módulos específicos de deportes.
    * **`/football`**: Implementación de fútbol (modelos, ETL, API-Football Client y el motor de analítica predictiva).
* **`/frontend`**: Interfaz de usuario en React.
  * **`/src/components`**: Vistas de Dashboard, Predicciones, Buscador de Jugadores, Rushbet y el módulo completo del Mundial 2026 (`/worldcup` con Bracket, Fixtures, Groups, Predictions).
* **`/scripts`**: Scripts de utilidad para inicializar base de datos, aplicar migraciones e importar datos de Elo y Squads (planteles).
* **`/tests`**: Suite de pruebas unitarias y de integración.

---

## 3. Arquitectura Extensible y Registro de Deportes

El backend está diseñado bajo el principio de **Abierto/Cerrado (Open/Closed)** para poder integrar nuevos deportes de forma modular.

### Interfaces Abstractas (`app/core/interfaces.py`)
Cualquier deporte que se desee integrar debe implementar las siguientes cuatro interfaces básicas:
1. `ISportAPIClient`: Para consumir datos de eventos, estadísticas y alineaciones desde APIs externas.
2. `ISportETL`: Para el proceso de carga de datos hacia la base de datos relacional.
3. `ISportAnalytics`: Para calcular las métricas y probabilidades predictivas.
4. `ISportBettingMarkets`: Para definir los mercados de apuestas disponibles del deporte.

### Registro y Auto-descubrimiento (`app/core/registry.py`)
Cada deporte se describe mediante un objeto `SportConfig`. El `SportRegistry` (un singleton) permite registrar y listar los deportes disponibles.
El archivo `app/sports/__init__.py` contiene una función de auto-descubrimiento (`discover_sports()`) que escanea automáticamente las subcarpetas del directorio `/sports` e importa cada paquete que implemente su registro decorado con `@register_sport`.

---

## 4. Módulo de Fútbol (Soccer)

Actualmente, el fútbol es el deporte principal y completamente desarrollado dentro de `app/sports/football/`.

### 4.1 Modelos de Datos (`app/sports/football/models/__init__.py`)
Utiliza clases de **SQLModel** que mapean directamente las tablas de la base de datos:
* **`League`**: Ligas o competiciones (id, nombre, país, temporada, tipo, región).
* **`Team`**: Equipos/selecciones con soporte para rating Elo (`elo_rating`).
* **`Player`**: Datos de jugadores (nombre, posición, equipo, nacionalidad, edad).
* **`Coach`**: Entrenadores/directores técnicos.
* **`Fixture`**: Partidos jugados y programados (equipos local/visitante, marcadores, entrenadores, fecha).
* **`TeamMatchStats`**: Estadísticas de equipo por partido (possession, tiros, tiros a puerta, corners, faltas, tarjetas amarillas/rojas, goles esperados).
* **`PlayerMatchStats`**: Estadísticas de rendimiento de jugador por partido (minutos, calificación de 1-10, goles, asistencias, pases clave, regates exitosos, tarjetas).
* **`PlayerSeasonStats`**: Estadísticas de jugador consolidadas para la temporada (usado para calcular la contribución de gol esperada xGC).
* **`Injury`**: Registro de lesiones e incapacidades de jugadores.
* **`TeamMapping`**: Tabla para mapear nombres de equipos externos (Rushbet/Kambi) a los IDs numéricos internos de API-Football usando fuzzy matching.
* **`Referee`**: Árbitros del partido.
* **`WorldCupPrediction`**: Tabla para la quiniela del Mundial 2026, guardando los marcadores predichos por el usuario, marcadores reales y puntos ganados.

### 4.2 Proceso ETL (`app/sports/football/etl/__init__.py`)
El motor de ETL interactúa con la API externa **API-Football** mediante `FootballAPIClient`. 
* **Sincronización de ligas**: `sync_league_data` descarga la información básica de partidos de una liga y temporada.
* **Descarga de estadísticas detalladas**: El método `sync_event_details` utiliza un `ThreadPoolExecutor` para descargar concurrentemente desde la API:
  1. Estadísticas de equipos (`get_event_stats`).
  2. Alineaciones oficiales (`get_event_lineups`).
  3. Rendimiento individual de jugadores (`get_fixture_players`).
* **Rate-Limit Friendly**: La sincronización de lotes de partidos (`_sync_fixture_details_batch`) procesa partido por partido con un retraso dinámico (e.g., 0.5s) y gestiona transacciones y commits aislados por partido para que el fallo en un registro no aborte todo el lote.
* **Optimización en consultas**: Para evitar el cuello de botella de consultas recurrentes individuales (el problema de consultas N+1), el ETL pre-carga todos los IDs de jugadores del lote en un mapa en memoria (`_get_existing_players_map`) antes de insertar o fusionar registros.

### 4.3 Motor de Analítica Predictiva (`app/sports/football/analytics/`)

El motor de predicciones calcula cuotas justas y probabilidades para diferentes mercados:

#### 1. Modelo de Poisson Bivariado (`models/poisson.py`)
Utiliza la distribución de Poisson para modelar el número de goles de cada equipo. La probabilidad de que el equipo local marque $x$ goles y el visitante marque $y$ goles se calcula como:
$$P(X=x, Y=y) = \frac{e^{-\lambda} \lambda^x}{x!} \times \frac{e^{-\mu} \mu^y}{y!}$$
donde $\lambda$ y $\mu$ son los goles esperados (xG) de local y visitante. El modelo implementa una corrección de correlación bivariada ($\rho$) para corregir la subestimación de empates de pocos goles (como 0-0 y 1-1).

#### 2. Cálculo de Goles Esperados (xG) Ajustado (`predictive/goals.py`)
La función `calculate_expected_goals` combina múltiples fuentes de datos:
1. **Estadísticas Históricas**: Calcula promedios ponderados de goles anotados y recibidos en los últimos N partidos (por defecto 20).
2. **Ventaja de Localía**: Aplica un factor base (e.g., 1.1x al local, 0.9x al visitante), el cual se omite en sedes neutrales como el Mundial.
3. **Modificador de Calidad Elo**: Ajusta el xG base según la diferencia de Elo entre ambos equipos:
   $$\text{Modificador de calidad} = 1.0 + \frac{\text{Elo}_{\text{local}} - \text{Elo}_{\text{visitante}}}{1000}$$
   Este modificador está limitado en un rango estricto de $[0.70, 1.30]$ para evitar distorsiones absurdas.
4. **Modificador Head-to-Head (H2H)**: Analiza el historial directo entre los dos equipos y ajusta el xG resultante en un máximo de $\pm 15\%$.

#### 3. Mercados de Goles, Mitades y Hándicaps
* **Mercados de Goles (`predictive/goals.py`)**: Calcula la probabilidad exacta para 1X2 (ganador local, empate, ganador visitante), Ambos Equipos Marcarán (BTTS), Over/Under de goles totales y por equipo (umbrales de 0.5 a 4.5), y un Top 5 de marcadores más probables.
* **Mercados de Mitad de Tiempo**: Asume que la primera mitad representa aproximadamente el $45\%$ del xG total y corre el motor de Poisson sobre este valor ajustado.
* **Hándicaps Asiáticos y Europeos (3-Way)**: Genera la matriz completa de diferencias de goles e itera sobre ella para calcular las probabilidades de ganar, perder o empatar (push) según cada línea de hándicap.

#### 4. Córners, Tarjetas y Tiros (`predictive/advanced.py`)
* **Córners**: Predice el total de tiros de esquina usando una **distribución Normal (Gaussiana)**, donde la media combinada se calcula de los córners generados por un equipo y concedidos por el rival, y la desviación estándar se modela en proporción a la media ($\sigma = \sqrt{(c_{\text{local}} \cdot 0.35)^2 + (c_{\text{visitante}} \cdot 0.35)^2}$).
* **Tarjetas**: Determina la expectativa de tarjetas totales considerando la media de tarjetas recibidas por el local, por el visitante y el promedio histórico de tarjetas del árbitro asignado. Las probabilidades de Over/Under se modelan con una distribución de Poisson.

#### 5. Impacto de Jugadores (`analytics/impact_engine.py`)
Calcula el índice de impacto de un jugador basándose en su contribución esperada de gol (xGC = xG + xA), precisión de regates, pases clave y minutos jugados, ponderado por la calidad del equipo rival.

---

## 5. Integración con Rushbet (Kambi offering API)

El sistema cuenta con un conector inverso para extraer cuotas y mercados directamente de la casa de apuestas Rushbet Colombia.

### 5.1 Cliente API (`app/services/rushbet_api.py`)
Consume endpoints JSON del CDN de Kambi (ej. `listView/football.json` y `betoffer/event/{event_id}.json`).
* **Exclusión de eSports**: Filtra y descarta eventos de deportes electrónicos y ligas virtuales analizando patrones como `"esport"`, `"cyber"`, `"2x6min"`, `"simulated"`, etc.
* **Clasificación de Mercados en Dos Niveles**:
  Categoriza de forma estructurada cuotas dinámicas buscando:
  1. *Coincidencia exacta*: Nombres estáticos normalizados como `"Resultado final"`, `"Ambos equipos marcarán"`, `"Total de tiros de esquina"`.
  2. *Patrones regex/palabras clave*: Expresiones dinámicas que contienen nombres de equipos, como `"Total de goles de [Equipo Local]"`, `"Goles de la 1ª mitad"`, `"Hándicap asiático"`.

### 5.2 Auto-Matching de Equipos (`app/sports/football/config/team_mapping.py`)
Permite conectar los eventos raspados de Rushbet con los registros internos de la base de datos:
1. **Fuzzy Matching Avanzado**: Si la librería `rapidfuzz` está disponible, calcula el score promediando tres algoritmos: `token_sort_ratio`, `partial_ratio` y `WRatio`. Si no está disponible, utiliza una lógica de superposición de palabras y similitud de longitud de caracteres.
2. **Umbrales de Confianza**:
   * $\ge 85\%$ confianza: El mapeo se crea e inserta marcado como `verified = True`.
   * $\ge 60\%$ confianza: Se guarda el mapeo pero queda marcado como tentativo (`verified = False`).
   * $< 50\%$ confianza: Se rechaza y no se guarda.
3. **Verificación Manual**: Provee un endpoint para que los usuarios validen o corrijan manualmente los mapeos tentativos a través de la UI.

---

## 6. Módulo Mundial de la FIFA 2026 (Polla/Quiniela)

Este módulo específico ofrece una experiencia interactiva para el mundial.

### 6.1 Sincronización de Datos del Mundial (`scripts/import_squads.py`, `scripts/import_elo.py`)
* **Squads**: Un scraper basado en BeautifulSoup4 que extrae la información actualizada de planteles de cada una de las 48 selecciones desde la página de Wikipedia `"2026 FIFA World Cup squads"`, registrando automáticamente a los jugadores y sus posiciones.
* **Elo Ratings**: Semillero de ratings Elo de las selecciones a partir de datos reales de `eloratings.net`.

### 6.2 Reglas de Puntuación de la Quiniela (`analytics/worldcup_scoring.py`)
El cálculo de puntos de las predicciones de marcadores sigue reglas precisas no acumulables (se otorga el puntaje máximo aplicable):
* **Marcador exacto**: 12 puntos.
* **Ganador correcto + misma diferencia de goles**: 8 puntos.
* **Empate correcto (cualquier marcador)**: 8 puntos.
* **Ganador correcto (diferente marcador/diferencia)**: 5 puntos.
* **Acertar cantidad exacta de goles de un solo equipo**: 2 puntos.
* **Predicción incorrecta**: 0 puntos.
* **Bono de definición por penales**: +3 puntos por acertar el equipo clasificado en tanda de penaltis.
* **Bono de Podio Final**: +20 puntos por Campeón exacto, +10 por Subcampeón y +6 por Tercer Puesto.

---

## 7. Interfaces de la API (Endpoints Principales)

* **Dashboard**: `/api/database/stats` (devuelve el conteo de registros y el listado de ligas soportadas).
* **ETL**:
  * `/api/etl/sync` (inicia la descarga de fixtures y detalles en segundo plano para una liga/temporada).
  * `/api/etl/sync-priority` (descarga en segundo plano todas las ligas prioritarias whitelisteadas).
  * `/api/etl/sync-injuries` (descarga lesiones de una liga).
* **Equipos y Jugadores**:
  * `/api/teams` y `/api/teams/{team_id}/stats` (estadísticas consolidadas para sliders del simulador manual).
  * `/api/players` (buscador de jugadores con filtros de equipo y liga).
* **Predictores**:
  * `/api/predict/database` (predicción automática consumiendo datos históricos de la BD).
  * `/api/predict/manual` (predicción en tiempo real usando parámetros enviados por JSON desde la UI).
* **Rushbet**: `/api/rushbet` (listado de partidos en vivo/próximos) y `/api/rushbet/{event_id}` (detalle de mercados cruzado con predicción automática del motor si se logra mapear a los equipos).
* **Mundial 2026**:
  * `/api/worldcup/fixtures` (partidos del mundial con marcadores).
  * `/api/worldcup/predict/{home_id}/{away_id}` (predicción automática Poisson en sede neutral).
  * `/api/worldcup/predict-score` (guarda la predicción del marcador del usuario).
  * `/api/worldcup/predictions` (obtiene todas las predicciones del usuario y recalcula los puntos totales).

---

## 8. Frontend Estructurado (React + Vite)

El frontend utiliza una interfaz oscura premium basada en TailwindCSS:
* **`DashboardView`**: Panel general de administración y control de sincronización de ligas.
* **`PredictionsView`**: Simulador interactivo que permite seleccionar dos equipos de la base de datos para predecir automáticamente, o ajustar sliders manuales de ataque, defensa, tiros, corners y tarjetas para simular escenarios personalizados.
* **`PlayerBrowserView`**: Buscador dinámico de jugadores por liga y club.
* **`RushbetView`**: Tablero que muestra partidos reales en vivo y calcula si hay discrepancias de valor entre las cuotas de Rushbet y las probabilidades justas de nuestro motor de Poisson (Value Bets).
* **`WorldCupView`**: Módulo del mundial organizado por pestañas:
  * *Grupos (`GroupsTab`)*: Tablas de posiciones del grupo A al L.
  * *Fixture (`FixturesTab`)*: Partidos del mundial y sus predicciones.
  * *Quiniela (`PredictionsTab`)*: Formulario para guardar predicciones de marcadores del usuario y ver el puntaje obtenido.
  * *Playoffs (`BracketTab`)*: Diagrama visual interactivo de las eliminatorias directas (dieciseisavos, octavos, cuartos, semis, final).

---

## 9. Instrucciones para Extender el Proyecto

### 9.1 ¿Cómo agregar un nuevo deporte? (Ejemplo: Baloncesto)
1. **Crear carpeta del deporte**: `/app/sports/basketball/`.
2. **Definir los modelos en `models/__init__.py`**: Crear las tablas SQLModel de baloncesto (e.g. `BasketballTeam`, `BasketballFixture`, `BasketballPlayerStats`).
3. **Crear el Cliente API en `api/__init__.py`**: Implementar `ISportAPIClient` para consumir desde la API de baloncesto elegida.
4. **Implementar el ETL en `etl/__init__.py`**: Implementar `ISportETL` adaptado a la estructura de baloncesto.
5. **Implementar la Analítica en `analytics/__init__.py`**: Implementar `ISportAnalytics` utilizando modelos estadísticos específicos para baloncesto (e.g., regresión lineal para puntos totales en lugar de Poisson).
6. **Registrar el deporte en `/app/sports/basketball/__init__.py`**:
   ```python
   from app.core.registry import SportConfig, register_sport
   from app.sports.basketball.api import BasketballAPIClient
   from app.sports.basketball.etl import BasketballETL
   from app.sports.basketball.analytics import BasketballAnalytics
   from app.sports.basketball.models import BasketballTeam # ...

   register_sport(SportConfig(
       key="basketball",
       name="Baloncesto",
       icon="🏀",
       api_client_class=BasketballAPIClient,
       etl_class=BasketballETL,
       analytics_class=BasketballAnalytics,
       models=[BasketballTeam, ...]
   ))
   ```
7. El sistema de auto-descubrimiento en `discover_sports()` cargará automáticamente el nuevo deporte al iniciar la API y generará las tablas correspondientes en la base de datos.
