import sys
import os

# Add the project root to the python path
sys.path.append(os.getcwd())

from sqlmodel import select
from app.core.database import get_session
from app.sports.football.models import Team, Fixture

def extract_laliga_teams():
    LEAGUE_ID = 140
    
    with next(get_session()) as session:
        # 1. Find all matches for La Liga
        statement = select(Fixture).where(Fixture.league_id == LEAGUE_ID)
        fixtures = session.exec(statement).all()
        
        # 2. Extract unique team IDs
        team_ids = set()
        for f in fixtures:
            team_ids.add(f.home_team_id)
            team_ids.add(f.away_team_id)
            
        if not team_ids:
            print(f"No fixtures found for League ID {LEAGUE_ID}.")
            return
            
        # 3. Get Team details
        team_stmt = select(Team).where(Team.id.in_(team_ids)).order_by(Team.name)
        teams = session.exec(team_stmt).all()
        
        # 4. Generate Markdown
        md_content = f"# Equipos de La Liga (ID: {LEAGUE_ID})\n\n"
        md_content += f"**Total de equipos encontrados:** {len(teams)}\n\n"
        md_content += "| ID | Nombre |\n"
        md_content += "|----|--------|\n"
        
        for team in teams:
            md_content += f"| {team.id} | {team.name} |\n"
            
        # 5. Save to file
        output_path = r"C:\Users\Pc\.gemini\antigravity\brain\af91b715-5ef4-4e30-956f-00665d34ea4f\laliga_teams.md"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(md_content)
            
        print(f"Document generated at: {output_path}")
        print(md_content)

if __name__ == "__main__":
    extract_laliga_teams()
