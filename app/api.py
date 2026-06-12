import os
import logging
from typing import Optional, List, Dict, Any
import uvicorn
from fastapi import FastAPI, BackgroundTasks, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlmodel import Session, select, func

logger = logging.getLogger("api")

from app.core.database import get_session, init_db
from app.sports.football.models import Team, Player, League, Fixture, Injury, WorldCupPrediction
from app.sports.football.etl import FootballETL
from app.services.rushbet_api import RushbetClient
from app.sports.football.analytics.predictive.goals import (
    get_full_match_prediction,
    predict_goals_markets,
    predict_halftime_markets,
    predict_handicap_markets
)
from app.sports.football.analytics.predictive.advanced import AdvancedPredictor
from app.sports.football.analytics.data.team_stats import get_team_stats_summary

app = FastAPI(
    title="Sport Analyzer API",
    description="High-performance sports prediction engine using ELO and Poisson statistical models.",
    version="2.0.0"
)

# Enable CORS for frontend communications
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    print("Initializing Database...")
    init_db()


# ==========================================
# 1. Dashboard & Database Stats
# ==========================================
@app.get("/api/database/stats")
def get_db_stats(session: Session = Depends(get_session)):
    try:
        fixtures_count = session.exec(select(func.count(Fixture.id))).one()
        teams_count = session.exec(select(func.count(Team.id))).one()
        players_count = session.exec(select(func.count(Player.id))).one()
        leagues_count = session.exec(select(func.count(League.id))).one()
        injuries_count = session.exec(select(func.count(Injury.id))).one()
        
        # Get leagues for dynamic selector
        db_leagues = session.exec(select(League).order_by(League.region, League.name)).all()
        leagues_data = [{"id": l.id, "name": l.name, "country": l.country, "region": l.region} for l in db_leagues]
        
        # Merge with static leagues to allow syncing new ones
        static_leagues = [
            (39, "Premier League", "England", "Europe"), (140, "La Liga", "Spain", "Europe"),
            (135, "Serie A", "Italy", "Europe"), (78, "Bundesliga", "Germany", "Europe"),
            (61, "Ligue 1", "France", "Europe"), (2, "Champions League", "World", "Europe"),
            (13, "Copa Libertadores", "South America", "South America"), (239, "Liga BetPlay", "Colombia", "South America"),
            (128, "Liga Profesional", "Argentina", "South America"), (71, "Brasileirão", "Brazil", "South America"),
            (253, "MLS", "USA", "North America"), (262, "Liga MX", "Mexico", "North America"),
            (3, "Europa League", "World", "Europe"), (11, "Copa Sudamericana", "South America", "South America"),
            (40, "Championship", "England", "Europe"), (94, "Primeira Liga", "Portugal", "Europe"),
            (88, "Eredivisie", "Netherlands", "Europe"), (307, "Pro League", "Saudi Arabia", "Asia"),
        ]
        
        db_league_ids = {l.id for l in db_leagues}
        for lid, name, country, region in static_leagues:
            if lid not in db_league_ids:
                leagues_data.append({"id": lid, "name": name, "country": country, "region": region})
                
        # Sort leagues alphabetically by name
        leagues_data.sort(key=lambda x: x["name"])

        return {
            "counts": {
                "fixtures": fixtures_count,
                "teams": teams_count,
                "players": players_count,
                "leagues": leagues_count,
                "injuries": injuries_count
            },
            "leagues": leagues_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class SyncLeagueRequest(BaseModel):
    league_id: int
    season: int
    sync_details: bool = False

def run_sync_task(league_id: int, season: int, sync_details: bool):
    try:
        etl = FootballETL()
        etl.sync_league_data(league_id=league_id, season=season, sync_details=sync_details)
    except Exception as e:
        print(f"Error in background sync: {e}")

@app.post("/api/etl/sync")
def sync_league(req: SyncLeagueRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(run_sync_task, req.league_id, req.season, req.sync_details)
    return {"message": "Sync started in background", "league_id": req.league_id, "season": req.season}

def run_sync_priority_task(season: int):
    try:
        etl = FootballETL()
        etl.sync_priority_leagues(season=season, sync_details=False)
    except Exception as e:
        print(f"Error in background batch sync: {e}")

@app.post("/api/etl/sync-priority")
def sync_priority(season: int, background_tasks: BackgroundTasks):
    background_tasks.add_task(run_sync_priority_task, season)
    return {"message": "Batch sync started in background"}

def run_sync_injuries_task(league_id: int, season: int):
    try:
        etl = FootballETL()
        etl.sync_injuries(league_id=league_id, season=season)
    except Exception as e:
        print(f"Error in background injuries sync: {e}")

@app.post("/api/etl/sync-injuries")
def sync_injuries(req: SyncLeagueRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(run_sync_injuries_task, req.league_id, req.season)
    return {"message": "Injuries sync started in background"}


# ==========================================
# 2. Teams & Players
# ==========================================
@app.get("/api/teams")
def get_teams(league_id: Optional[int] = None, session: Session = Depends(get_session)):
    if league_id:
        stmt = (
            select(Team)
            .join(Fixture, (Fixture.home_team_id == Team.id) | (Fixture.away_team_id == Team.id))
            .where(Fixture.league_id == league_id)
            .distinct()
            .order_by(Team.name)
        )
        teams = session.exec(stmt).all()
    else:
        teams = session.exec(select(Team).order_by(Team.name)).all()
        
    return [{"id": t.id, "name": t.name} for t in teams]

@app.get("/api/teams/{team_id}/stats")
def get_team_stats(team_id: int, session: Session = Depends(get_session)):
    """Fetch aggregated historic stats for a team to populate manual sliders."""
    stats = get_team_stats_summary(team_id, 20, session)
    if not stats:
        raise HTTPException(status_code=404, detail="No enough matches for stats")
    return stats

@app.get("/api/players")
def get_players(
    league_id: Optional[int] = None, 
    team_id: Optional[int] = None, 
    search: Optional[str] = None,
    limit: int = 100,
    session: Session = Depends(get_session)
):
    query = select(Player, Team).join(Team, Player.team_id == Team.id)
    
    if team_id:
        query = query.where(Team.id == team_id)
    elif league_id:
        # Simplification: players from teams that played in this league
        stmt = select(Team.id).join(Fixture, (Fixture.home_team_id == Team.id) | (Fixture.away_team_id == Team.id)).where(Fixture.league_id == league_id).distinct()
        valid_team_ids = session.exec(stmt).all()
        query = query.where(Player.team_id.in_(valid_team_ids))
        
    if search:
        query = query.where(Player.name.ilike(f"%{search}%"))
        
    query = query.limit(limit)
    results = session.exec(query).all()
    
    return [
        {
            "id": p.id,
            "name": p.name,
            "position": p.position,
            "team_id": t.id,
            "team_name": t.name,
            "nationality": p.nationality,
            "age": p.age,
            "photo": p.photo
        }
        for p, t in results
    ]


# ==========================================
# 3. Predictions
# ==========================================
class ManualPredictionRequest(BaseModel):
    home_name: str = "Local"
    away_name: str = "Visitante"
    home_attack: float
    home_defense: float
    home_corners: float
    home_corners_conceded: float
    home_cards: float
    home_shots: float
    away_attack: float
    away_defense: float
    away_corners: float
    away_corners_conceded: float
    away_cards: float
    away_shots: float

@app.get("/api/predict/database")
def predict_database(home_id: int, away_id: int, session: Session = Depends(get_session)):
    """Automatic predictions based entirely on DB historical data."""
    try:
        prediction = get_full_match_prediction(home_id, away_id, session)
        return prediction
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/predict/manual")
def predict_manual(req: ManualPredictionRequest):
    """Calculates predictions based on manual slider parameters."""
    home_xg = req.home_attack * (req.away_defense / 1.0) * 1.1
    away_xg = req.away_attack * (req.home_defense / 1.0) * 0.9
    
    preds = predict_goals_markets(home_xg, away_xg)
    ht_preds = predict_halftime_markets(home_xg, away_xg)
    handicaps = predict_handicap_markets(home_xg, away_xg)
    
    corners_preds = AdvancedPredictor.predict_corners(
        req.home_corners, req.away_corners, req.home_corners_conceded, req.away_corners_conceded
    )
    
    cards_preds = AdvancedPredictor.predict_cards(
        req.home_cards, req.away_cards
    )
    
    shots_preds = AdvancedPredictor.predict_shots(
        {"total": req.home_shots, "on_goal": req.home_shots * 0.35},
        {"total": req.away_shots, "on_goal": req.away_shots * 0.35}
    )
    
    return {
        "expected_goals": {"home": round(home_xg, 2), "away": round(away_xg, 2)},
        "1x2": {
            "home_win": preds["1x2"]["home"],
            "draw": preds["1x2"]["draw"],
            "away_win": preds["1x2"]["away"]
        },
        "btts": preds["btts"],
        "over_under": preds["over_under"],
        "correct_score_top5": preds["correct_score"],
        "halftime": ht_preds,
        "handicaps": handicaps,
        "corners": corners_preds,
        "cards": cards_preds,
        "shots": shots_preds
    }


# ==========================================
# 4. Rushbet Live Odds
# ==========================================
@app.get("/api/rushbet")
def get_rushbet_events():
    try:
        client = RushbetClient()
        events = client.get_football_events()
        return events
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/rushbet/{event_id}")
def get_rushbet_event_detail(event_id: int, session: Session = Depends(get_session)):
    try:
        client = RushbetClient()
        detail = client.get_event_details(event_id)
        if not detail:
            raise HTTPException(status_code=404, detail="Event not found")
            
        home_team = detail.get("home_team", "")
        away_team = detail.get("away_team", "")
        scraper_home_id = detail.get("home_id")
        scraper_away_id = detail.get("away_id")
        
        from app.sports.football.config.team_mapping import get_mapped_team_id
        
        mapped_home_id = get_mapped_team_id(home_team, session)
        mapped_away_id = get_mapped_team_id(away_team, session)
        
        session.commit() # Commit possible new mappings
        
        detail["predictions"] = None
        # Solo inyectar predicciones si los equipos se mapearon a IDs numéricos de nuestra BD
        if isinstance(mapped_home_id, int) and isinstance(mapped_away_id, int):
            check_stmt = select(Fixture).where((Fixture.home_team_id == mapped_home_id) | (Fixture.away_team_id == mapped_home_id)).limit(1)
            if session.exec(check_stmt).first():
                detail["predictions"] = get_full_match_prediction(mapped_home_id, mapped_away_id, session)
        
        return detail
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# 5. World Cup 2026
# ==========================================

# Global sync progress tracker
_wc_sync_status = {"running": False, "total": 0, "processed": 0, "current_team": "", "errors": []}

def _run_worldcup_sync(resume: bool = True):
    """Background task: sync World Cup fixtures + history for all 48 teams."""
    from app.sports.football.analytics.worldcup_scoring import (
        WORLD_CUP_TEAM_IDS, WORLD_CUP_LEAGUE_ID, WORLD_CUP_SEASON
    )
    global _wc_sync_status
    _wc_sync_status = {"running": True, "total": len(WORLD_CUP_TEAM_IDS) + 1, "processed": 0, "current_team": "Fixtures del Mundial", "errors": []}
    
    etl = FootballETL()
    
    # Step 1: Sync World Cup fixtures (league_id=1, season=2026)
    if not resume:
        try:
            etl.sync_league_data(league_id=WORLD_CUP_LEAGUE_ID, season=WORLD_CUP_SEASON, sync_details=True)
        except Exception as e:
            _wc_sync_status["errors"].append(f"WC Fixtures: {e}")
    _wc_sync_status["processed"] = 1
    
    # Step 2: Sync last 20 matches for each of the 48 national teams
    with etl._get_db_session() as session:
        for i, team_id in enumerate(WORLD_CUP_TEAM_IDS):
            _wc_sync_status["current_team"] = f"Team ID {team_id}"
            
            if resume:
                # Check if this team already has enough fixtures in the DB
                count = session.exec(
                    select(func.count(Fixture.id))
                    .where((Fixture.home_team_id == team_id) | (Fixture.away_team_id == team_id))
                ).one()
                if count >= 15:
                    logger.info(f"Team {team_id} already has {count} fixtures. Skipping.")
                    _wc_sync_status["processed"] = i + 2
                    continue
                    
            try:
                etl.sync_team_history(team_id, last_n=20)
            except Exception as e:
                _wc_sync_status["errors"].append(f"Team {team_id}: {e}")
            _wc_sync_status["processed"] = i + 2  # +2 because fixtures was step 1
    
    _wc_sync_status["running"] = False
    _wc_sync_status["current_team"] = "Completado"

@app.post("/api/worldcup/sync")
def start_worldcup_sync(background_tasks: BackgroundTasks, resume: bool = Query(True, description="Skip already synced teams")):
    """Inicia la descarga masiva de datos del Mundial en segundo plano."""
    if _wc_sync_status.get("running"):
        return {"message": "Sync already in progress", "status": _wc_sync_status}
    background_tasks.add_task(_run_worldcup_sync, resume)
    return {"message": "World Cup sync started in background", "resume_mode": resume}

@app.get("/api/worldcup/sync/status")
@app.get("/api/worldcup/sync-status")
def get_worldcup_sync_status():
    """Devuelve el progreso de la sincronización del Mundial."""
    return _wc_sync_status

@app.get("/api/worldcup/fixtures")
def get_worldcup_fixtures(session: Session = Depends(get_session)):
    """Lista los partidos del Mundial 2026 con resultados."""
    from app.sports.football.analytics.worldcup_scoring import WORLD_CUP_LEAGUE_ID
    stmt = (
        select(Fixture, Team)
        .join(Team, Fixture.home_team_id == Team.id)
        .where(Fixture.league_id == WORLD_CUP_LEAGUE_ID)
        .order_by(Fixture.date)
    )
    results = session.exec(stmt).all()
    
    fixtures = []
    for fixture, home_team in results:
        away_team = session.get(Team, fixture.away_team_id)
        fixtures.append({
            "id": fixture.id,
            "date": fixture.date.isoformat() if fixture.date else None,
            "home_team_id": fixture.home_team_id,
            "away_team_id": fixture.away_team_id,
            "home_team_name": home_team.name if home_team else "?",
            "away_team_name": away_team.name if away_team else "?",
            "home_score": fixture.home_score,
            "away_score": fixture.away_score
        })
    return fixtures

@app.get("/api/worldcup/predict/{home_id}/{away_id}")
def predict_worldcup_match(home_id: int, away_id: int, session: Session = Depends(get_session)):
    """Predice un partido del mundial usando la misma lógica que el engine, pero como endpoint suelto."""
    try:
        from app.sports.football.analytics.predictive.goals import calculate_expected_goals
        from app.sports.football.analytics.models.poisson import PoissonEngine
        import math
        
        # Base Poisson Calculation
        home_xg, away_xg, home_squad, away_squad = calculate_expected_goals(
            home_team_id=home_id, 
            away_team_id=away_id, 
            session=session, 
            last_n_games=20, 
            home_advantage=1.0, # Sede neutral
            use_weighted=True
        )
        
        # Build score matrix
        max_goals = 6
        correct_scores = {}
        home_win_prob = 0.0
        away_win_prob = 0.0
        draw_prob = 0.0
        
        for h in range(max_goals + 1):
            for a in range(max_goals + 1):
                prob = PoissonEngine.get_joint_probability(home_xg, h, away_xg, a)
                score_str = f"{h}-{a}"
                correct_scores[score_str] = prob
                
                if h > a:
                    home_win_prob += prob
                elif a > h:
                    away_win_prob += prob
                else:
                    draw_prob += prob

        # Sort top scores
        top_scores = dict(sorted(correct_scores.items(), key=lambda item: item[1], reverse=True)[:5])

        return {
            "probabilities": {
                "home": home_win_prob,
                "draw": draw_prob,
                "away": away_win_prob
            },
            "expected_goals": {
                "home": home_xg,
                "away": away_xg
            },
            "squad_rating": {
                "home": home_squad,
                "away": away_squad
            },
            "correct_score_top5": top_scores
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/worldcup/sync-data")
def sync_worldcup_data(background_tasks: BackgroundTasks):
    """Sincroniza los squads desde Wikipedia y los puntos Elo."""
    from scripts.import_elo import import_elo_ratings
    from scripts.import_squads import scrape_squads
    from app.core.database import Session, engine

    def run_sync():
        with Session(engine) as session:
            try:
                import_elo_ratings(session)
                scrape_squads(session)
            except Exception as e:
                print("Error syncing world cup data:", e)

    background_tasks.add_task(run_sync)
    return {"status": "ok", "message": "Sincronización de datos del Mundial (Elo y Convocatorias) iniciada en segundo plano."}

class ScorePredictionRequest(BaseModel):
    fixture_id: int
    predicted_home_score: int
    predicted_away_score: int

@app.post("/api/worldcup/predict-score")
def save_score_prediction(req: ScorePredictionRequest, session: Session = Depends(get_session)):
    """Guarda o actualiza la predicción de marcador del usuario para un partido."""
    # Check if prediction already exists for this fixture
    existing = session.exec(
        select(WorldCupPrediction).where(WorldCupPrediction.fixture_id == req.fixture_id)
    ).first()
    
    if existing:
        existing.predicted_home_score = req.predicted_home_score
        existing.predicted_away_score = req.predicted_away_score
        session.add(existing)
    else:
        pred = WorldCupPrediction(
            fixture_id=req.fixture_id,
            predicted_home_score=req.predicted_home_score,
            predicted_away_score=req.predicted_away_score
        )
        session.add(pred)
    
    session.commit()
    return {"message": "Prediction saved", "fixture_id": req.fixture_id}

@app.get("/api/worldcup/predictions")
def get_all_predictions(session: Session = Depends(get_session)):
    """Lista todas las predicciones del usuario con puntos calculados."""
    from app.sports.football.analytics.worldcup_scoring import calculate_match_points, get_points_label
    
    preds = session.exec(
        select(WorldCupPrediction).order_by(WorldCupPrediction.fixture_id)
    ).all()
    
    total_points = 0
    result = []
    for p in preds:
        fixture = session.get(Fixture, p.fixture_id)
        home_team = session.get(Team, fixture.home_team_id) if fixture else None
        away_team = session.get(Team, fixture.away_team_id) if fixture else None
        
        # Recalculate points if actual scores are available
        points = 0
        label = ""
        if fixture and fixture.home_score is not None and fixture.away_score is not None:
            points = calculate_match_points(
                p.predicted_home_score, p.predicted_away_score,
                fixture.home_score, fixture.away_score
            )
            label = get_points_label(points)
            # Update stored points
            if p.points_earned != points:
                p.points_earned = points
                p.actual_home_score = fixture.home_score
                p.actual_away_score = fixture.away_score
                session.add(p)
        
        total_points += points
        result.append({
            "id": p.id,
            "fixture_id": p.fixture_id,
            "home_team": home_team.name if home_team else "?",
            "away_team": away_team.name if away_team else "?",
            "predicted_home": p.predicted_home_score,
            "predicted_away": p.predicted_away_score,
            "actual_home": fixture.home_score if fixture else None,
            "actual_away": fixture.away_score if fixture else None,
            "points": points,
            "label": label
        })
    
    session.commit()
    return {"predictions": result, "total_points": total_points}

@app.get("/api/worldcup/team-stats/{team_id}")
def get_worldcup_team_stats(team_id: int, session: Session = Depends(get_session)):
    """Obtiene resumen de estadísticas históricas de una selección."""
    stats = get_team_stats_summary(team_id, 20, session)
    if not stats:
        return {"error": "No data available for this team"}
    return stats


# ==========================================
# Static Files & Fallback
# ==========================================
frontend_path = "frontend/dist"
if os.path.exists(frontend_path):
    app.mount("/assets", StaticFiles(directory=f"{frontend_path}/assets"), name="assets")
    
    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str):
        if full_path.startswith("api"):
            raise HTTPException(status_code=404, detail="API route not found")
        return FileResponse(f"{frontend_path}/index.html")
else:
    @app.get("/")
    def read_root():
        return {"message": "Welcome to Sport Analyzer API (Development mode, compile React frontend to serve it here)", "status": "online"}

if __name__ == "__main__":
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)
