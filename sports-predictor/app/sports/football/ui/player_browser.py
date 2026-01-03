"""
Vista para explorar la base de datos de jugadores.
Permite filtrar por Liga y Equipo.
"""
import streamlit as st
import pandas as pd
from sqlmodel import select
from app.core.database import get_session
from app.sports.football.models import Player, Team, League, Fixture

def show_player_browser():
    st.title("🏃 Explorador de Jugadores")
    
    with next(get_session()) as session:
        # 1. Filtro de Liga
        leagues = session.exec(select(League).order_by(League.name)).all()
        league_options = {l.name: l.id for l in leagues}
        
        selected_league_name = st.selectbox(
            "Filtrar por Liga", 
            ["Todas"] + list(league_options.keys())
        )
        
        # 2. Construir Query Base
        # Queremos: Player -> Team. 
        # Pero Team no tiene league_id directo. Lo "deducimos" de los Fixtures o 
        # simplemente mostramos todos los equipos si no hay liga seleccionada.
        
        # Estrategia: 
        # Si hay Liga seleccionada -> Buscar Teams que han jugado en esa Liga (via Fixture)
        
        selected_league_id = league_options.get(selected_league_name)
        
        available_teams = []
        if selected_league_id:
            # Subquery o Join complejo para hallar equipos de esta liga
            # Select distinct team_id from Fixture where league_id = X
            # (Simplificación: buscamos equipos locales o visitantes en partidos de esa liga)
            
            # Opción más rápida: Traer todos y filtrar en Python si son pocos, 
            # pero mejor hacerlo bien en SQL.
            
            stmt = (
                select(Team)
                .join(Fixture, (Fixture.home_team_id == Team.id) | (Fixture.away_team_id == Team.id))
                .where(Fixture.league_id == selected_league_id)
                .distinct()
                .order_by(Team.name)
            )
            available_teams = session.exec(stmt).all()
        else:
            # Todos los equipos (Cuidado si son muchos)
            available_teams = session.exec(select(Team).order_by(Team.name)).all()
            
        team_options = {t.name: t.id for t in available_teams}
        
        # 3. Filtro de Equipo
        selected_team_name = st.selectbox(
            "Filtrar por Equipo",
            ["Todos"] + list(team_options.keys())
        )
        
        # 4. Buscador de Texto
        search_query = st.text_input("Buscar Jugador por Nombre", "")
        
        # 5. Ejecutar Consulta de Jugadores
        # Query: Player join Team
        query = select(Player, Team).join(Team, Player.team_id == Team.id)
        
        if selected_team_name != "Todos":
            query = query.where(Team.id == team_options[selected_team_name])
        elif selected_league_id:
            # Si eligió liga pero no equipo, filtramos jugadores cuyos equipos están en esa liga
            # (Reusamos la lógica de arriba o filtramos por ID in valid_team_ids)
            valid_team_ids = [t.id for t in available_teams]
            query = query.where(Player.team_id.in_(valid_team_ids))
            
        if search_query:
            query = query.where(Player.name.ilike(f"%{search_query}%"))
            
        # Limite por seguridad
        query = query.limit(500)
        
        results = session.exec(query).all()
        
        # 6. Mostrar Tabla
        if not results:
            st.warning("No se encontraron jugadores con esos filtros.")
            return

        data = []
        for player, team in results:
            data.append({
                "ID": player.id,
                "Jugador": player.name,
                "Posición": player.position,
                "Equipo": team.name,
                "Nacionalidad": player.nationality,
                "Edad": player.age
            })
            
        df = pd.DataFrame(data)
        st.dataframe(
            df, 
            use_container_width=True,
            column_config={
                "ID": st.column_config.NumberColumn(format="%d"),
            }
        )
        st.caption(f"Mostrando {len(df)} jugadores.")
