import os
from typing import Optional, List, Dict, Any
import uvicorn
from fastapi import FastAPI, BackgroundTasks, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlmodel import Session, select, func

from app.core.database import get_session
from app.sports.football.models import Team, Player, League, Fixture, Injury
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
        leagues = session.exec(select(League).order_by(League.region, League.name)).all()
        leagues_data = [{"id": l.id, "name": l.name, "country": l.country, "region": l.region} for l in leagues]

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


# ==========================================
# 2. Teams & Players
# ==========================================
@app.get("/api/teams")
def get_teams(session: Session = Depends(get_session)):
    teams = session.exec(select(Team).order_by(Team.name)).all()
    return [{"id": t.id, "name": t.name, "code": t.code, "country": t.country, "logo": t.logo} for t in teams]

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
def get_rushbet_event_detail(event_id: int):
    try:
        client = RushbetClient()
        detail = client.get_event_detail(event_id)
        if not detail:
            raise HTTPException(status_code=404, detail="Event not found")
        return detail
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
