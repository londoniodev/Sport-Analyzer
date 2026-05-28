import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

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

@app.get("/api/sports")
def get_sports():
    return ["Fútbol", "Baloncesto", "Tenis"]

@app.get("/api/matches")
def get_matches(sport: str = "Fútbol"):
    # Return mock statistical data representing Python Poisson & ELO calculations
    if sport.lower() == "fútbol":
        return [
            {
                "id": "1",
                "homeTeam": "Real Madrid",
                "awayTeam": "Barcelona",
                "homeElo": 1950,
                "awayElo": 1890,
                "poissonHomeWin": 48,
                "poissonDraw": 24,
                "poissonAwayWin": 28,
                "recommendedBet": "Real Madrid (1X)",
                "valueOdds": 1.85,
                "realOdds": 2.10,
                "edge": 13.5
            },
            {
                "id": "2",
                "homeTeam": "Manchester City",
                "awayTeam": "Arsenal",
                "homeElo": 1980,
                "awayElo": 1910,
                "poissonHomeWin": 52,
                "poissonDraw": 23,
                "poissonAwayWin": 25,
                "recommendedBet": "Over 2.5 Goles",
                "valueOdds": 1.70,
                "realOdds": 1.95,
                "edge": 14.7
            },
            {
                "id": "3",
                "homeTeam": "Bayern Munich",
                "awayTeam": "Borussia Dortmund",
                "homeElo": 1900,
                "awayElo": 1810,
                "poissonHomeWin": 61,
                "poissonDraw": 19,
                "poissonAwayWin": 20,
                "recommendedBet": "Bayern Munich (-1 AH)",
                "valueOdds": 1.55,
                "realOdds": 1.80,
                "edge": 16.1
            },
            {
                "id": "4",
                "homeTeam": "Juventus",
                "awayTeam": "Inter Milan",
                "homeElo": 1820,
                "awayElo": 1880,
                "poissonHomeWin": 30,
                "poissonDraw": 29,
                "poissonAwayWin": 41,
                "recommendedBet": "Inter Milan (Draw No Bet)",
                "valueOdds": 2.10,
                "realOdds": 2.45,
                "edge": 16.6
            }
        ]
    elif sport.lower() == "baloncesto":
        return [
            {
                "id": "b1",
                "homeTeam": "LA Lakers",
                "awayTeam": "Boston Celtics",
                "homeElo": 1780,
                "awayElo": 1820,
                "poissonHomeWin": 45,
                "poissonDraw": 0,
                "poissonAwayWin": 55,
                "recommendedBet": "Celtics -3.5",
                "valueOdds": 1.91,
                "realOdds": 2.05,
                "edge": 7.3
            }
        ]
    else:
        return []

# Serve React frontend in production
frontend_path = "frontend/dist"
if os.path.exists(frontend_path):
    app.mount("/assets", StaticFiles(directory=f"{frontend_path}/assets"), name="assets")
    
    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str):
        if full_path.startswith("api"):
            return None
        return FileResponse(f"{frontend_path}/index.html")
else:
    @app.get("/")
    def read_root():
        return {"message": "Welcome to Sport Analyzer API (Development mode, compile React frontend to serve it here)", "status": "online"}

if __name__ == "__main__":
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)
