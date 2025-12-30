"""
Football Prediction View - Integrated with Database.
Loads teams and calculates stats from match history.
"""
import streamlit as st
from sqlmodel import select
from app.ui.theme import render_probability_bar, render_metric_card, render_icon
from app.sports.football.predictions import (
    PoissonModel, GoalsPredictor, MatchResultPredictor,
    CornersPredictor, HandicapPredictor, ExactScorePredictor, AdvancedPredictor
)
from app.core.database import get_session, is_demo_mode
from app.sports.football.models import Team, League, Fixture
from app.sports.football.analytics.team_stats import (
    get_team_corners_avg, get_team_corners_conceded_avg,
    get_team_possession_avg, get_team_cards_avg, get_team_shots_avg
)


def get_teams_from_db():
    """Load teams from database."""
    if is_demo_mode():
        return []
    
    session = next(get_session())
    try:
        stmt = select(Team).order_by(Team.name)
        return session.exec(stmt).all()
    finally:
        session.close()


def get_leagues_from_db():
    """Load leagues from database."""
    if is_demo_mode():
        return []
    
    session = next(get_session())
    try:
        stmt = select(League).order_by(League.name)
        return session.exec(stmt).all()
    finally:
        session.close()


def get_team_stats_from_db(team_id: int, last_n: int = 10):
    """Get calculated stats for a team from database."""
    if is_demo_mode() or not team_id:
        return None
    
    session = next(get_session())
    try:
        corners = get_team_corners_avg(team_id, last_n, session)
        corners_conceded = get_team_corners_conceded_avg(team_id, last_n, session)
        possession = get_team_possession_avg(team_id, last_n, session)
        cards = get_team_cards_avg(team_id, last_n, session)
        shots = get_team_shots_avg(team_id, last_n, session)
        
        # Calculate goals from fixtures
        home_stmt = select(Fixture).where(
            Fixture.home_team_id == team_id,
            Fixture.home_score.isnot(None)
        ).order_by(Fixture.date.desc()).limit(last_n)
        away_stmt = select(Fixture).where(
            Fixture.away_team_id == team_id,
            Fixture.away_score.isnot(None)
        ).order_by(Fixture.date.desc()).limit(last_n)
        
        home_fixtures = session.exec(home_stmt).all()
        away_fixtures = session.exec(away_stmt).all()
        
        goals_scored = sum(f.home_score or 0 for f in home_fixtures) + sum(f.away_score or 0 for f in away_fixtures)
        goals_conceded = sum(f.away_score or 0 for f in home_fixtures) + sum(f.home_score or 0 for f in away_fixtures)
        total_matches = len(home_fixtures) + len(away_fixtures)
        
        if total_matches == 0:
            return None
        
        return {
            "goals_scored_avg": goals_scored / total_matches,
            "goals_conceded_avg": goals_conceded / total_matches,
            "corners_avg": corners,
            "corners_conceded_avg": corners_conceded,
            "possession_avg": possession,
            "cards_yellow_avg": cards["yellow"],
            "cards_total_avg": cards["yellow"] + cards["red"],
            "shots_avg": shots["total"],
            "shots_on_goal_avg": shots["on_goal"],
            "matches_analyzed": total_matches
        }
    finally:
        session.close()


def show_prediction_view():
    """Display the prediction dashboard with database integration."""
    
    # Header
    st.markdown(f"""
    <div style="margin-bottom: 24px;">
        <h1 style="margin: 0;">{render_icon('query_stats')} Predicción de Partido</h1>
        <p style="color: var(--text-secondary); margin-top: 8px;">Análisis pre-partido con probabilidades para todos los mercados</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Load data from DB
    teams_db = get_teams_from_db()
    leagues_db = get_leagues_from_db()
    
    # Fallback teams if DB is empty
    fallback_teams = sorted([
        "Real Madrid", "Barcelona", "Atletico Madrid", "Sevilla", "Valencia",
        "Manchester City", "Arsenal", "Liverpool", "Manchester United", "Chelsea",
        "Bayern Munich", "Dortmund", "PSG", "Inter Milan", "Juventus"
    ])
    
    use_db = len(teams_db) > 0
    
    # ═══════════════════════════════════════════════════════
    # Match Input
    with st.expander("Configuración del Partido", expanded=True):
        
        # Data source indicator
        if use_db:
            st.success(f"Datos desde BD: {len(teams_db)} equipos disponibles", icon="✅")
        else:
            st.warning("Modo Demo: Ingresa los datos manualmente", icon="⚠️")
        
        col1, col2, col3 = st.columns([2, 1, 2])
        
        with col1:
            st.markdown(f"### {render_icon('home')} Local", unsafe_allow_html=True)
            
            if use_db:
                team_options = [(t.id, t.name) for t in teams_db]
                home_selection = st.selectbox(
                    "Equipo Local",
                    options=team_options,
                    format_func=lambda x: x[1],
                    key="home_team_select"
                )
                home_id = home_selection[0] if home_selection else None
                home_name = home_selection[1] if home_selection else "Local"
                
                # Get stats from DB
                home_stats = get_team_stats_from_db(home_id)
                
                if home_stats:
                    st.caption(f"Basado en {home_stats['matches_analyzed']} partidos")
                    home_attack = st.slider("Goles/partido", 0.5, 3.5, 
                                           float(home_stats["goals_scored_avg"]), 0.1, key="home_attack")
                    home_defense = st.slider("Goles recibidos/partido", 0.5, 2.5,
                                            float(home_stats["goals_conceded_avg"]), 0.1, key="home_defense")
                    home_corners = st.slider("Córners/partido", 3.0, 10.0,
                                            float(home_stats["corners_avg"]), 0.5, key="home_corners")
                    home_cards = st.slider("Tarjetas/partido", 0.5, 5.0,
                                          float(home_stats["cards_total_avg"]), 0.1, key="home_cards")
                    home_shots = st.slider("Remates/partido", 5.0, 20.0,
                                          float(home_stats["shots_avg"]), 0.5, key="home_shots")
                    home_corners_conceded = home_stats["corners_conceded_avg"]
                else:
                    st.info("Sin datos históricos - ajusta manualmente")
                    home_attack = st.slider("Goles/partido", 0.5, 3.5, 1.5, 0.1, key="home_attack")
                    home_defense = st.slider("Goles recibidos/partido", 0.5, 2.5, 1.0, 0.1, key="home_defense")
                    home_corners = st.slider("Córners/partido", 3.0, 10.0, 5.0, 0.5, key="home_corners")
                    home_cards = st.slider("Tarjetas/partido", 0.5, 5.0, 2.0, 0.1, key="home_cards")
                    home_shots = st.slider("Remates/partido", 5.0, 20.0, 12.0, 0.5, key="home_shots")
                    home_corners_conceded = 5.0
            else:
                home_name = st.selectbox("Equipo Local", fallback_teams, index=0, key="home_name")
                home_attack = st.slider("Goles/partido", 0.5, 3.5, 1.8, 0.1, key="home_attack")
                home_defense = st.slider("Goles recibidos/partido", 0.5, 2.5, 0.9, 0.1, key="home_defense")
                home_corners = st.slider("Córners/partido", 3.0, 10.0, 5.5, 0.5, key="home_corners")
                home_cards = st.slider("Tarjetas/partido", 0.5, 5.0, 2.1, 0.1, key="home_cards")
                home_shots = st.slider("Remates/partido", 5.0, 20.0, 12.5, 0.5, key="home_shots")
                home_corners_conceded = home_defense * 4
        
        with col2:
            st.markdown("<div style='text-align: center; padding-top: 60px; font-size: 1.5rem; color: var(--text-secondary);'>VS</div>", unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"### {render_icon('flight')} Visitante", unsafe_allow_html=True)
            
            if use_db:
                away_selection = st.selectbox(
                    "Equipo Visitante",
                    options=team_options,
                    format_func=lambda x: x[1],
                    index=min(1, len(team_options)-1),
                    key="away_team_select"
                )
                away_id = away_selection[0] if away_selection else None
                away_name = away_selection[1] if away_selection else "Visitante"
                
                away_stats = get_team_stats_from_db(away_id)
                
                if away_stats:
                    st.caption(f"Basado en {away_stats['matches_analyzed']} partidos")
                    away_attack = st.slider("Goles/partido", 0.5, 3.5,
                                           float(away_stats["goals_scored_avg"]), 0.1, key="away_attack")
                    away_defense = st.slider("Goles recibidos/partido", 0.5, 2.5,
                                            float(away_stats["goals_conceded_avg"]), 0.1, key="away_defense")
                    away_corners = st.slider("Córners/partido", 3.0, 10.0,
                                            float(away_stats["corners_avg"]), 0.5, key="away_corners")
                    away_cards = st.slider("Tarjetas/partido", 0.5, 5.0,
                                          float(away_stats["cards_total_avg"]), 0.1, key="away_cards")
                    away_shots = st.slider("Remates/partido", 5.0, 20.0,
                                          float(away_stats["shots_avg"]), 0.5, key="away_shots")
                    away_corners_conceded = away_stats["corners_conceded_avg"]
                else:
                    st.info("Sin datos históricos - ajusta manualmente")
                    away_attack = st.slider("Goles/partido", 0.5, 3.5, 1.3, 0.1, key="away_attack")
                    away_defense = st.slider("Goles recibidos/partido", 0.5, 2.5, 1.2, 0.1, key="away_defense")
                    away_corners = st.slider("Córners/partido", 3.0, 10.0, 4.5, 0.5, key="away_corners")
                    away_cards = st.slider("Tarjetas/partido", 0.5, 5.0, 2.3, 0.1, key="away_cards")
                    away_shots = st.slider("Remates/partido", 5.0, 20.0, 10.0, 0.5, key="away_shots")
                    away_corners_conceded = 5.0
            else:
                away_name = st.selectbox("Equipo Visitante", fallback_teams, index=1, key="away_name")
                away_attack = st.slider("Goles/partido", 0.5, 3.5, 1.5, 0.1, key="away_attack")
                away_defense = st.slider("Goles recibidos/partido", 0.5, 2.5, 1.1, 0.1, key="away_defense")
                away_corners = st.slider("Córners/partido", 3.0, 10.0, 5.0, 0.5, key="away_corners")
                away_cards = st.slider("Tarjetas/partido", 0.5, 5.0, 2.5, 0.1, key="away_cards")
                away_shots = st.slider("Remates/partido", 5.0, 20.0, 10.5, 0.5, key="away_shots")
                away_corners_conceded = away_defense * 4
    
    # ═══════════════════════════════════════════════════════
    # CALCULATE PREDICTIONS
    # ═══════════════════════════════════════════════════════
    poisson = PoissonModel(league_avg_home_goals=1.5, league_avg_away_goals=1.2)
    
    # Calculate xG with home advantage
    home_xg = home_attack * (away_defense / 1.0) * 1.1
    away_xg = away_attack * (home_defense / 1.0) * 0.9
    
    # Get predictions
    match_result = poisson.prob_match_result(home_xg, away_xg)
    goals_predictor = GoalsPredictor(poisson)
    goals_pred = goals_predictor.predict(home_xg, away_xg)
    
    adv_predictor = AdvancedPredictor(poisson)
    
    # Corners - use actual conceded averages if available
    corners_pred = adv_predictor.predict_corners(
        home_corner_avg=home_corners,
        away_corner_avg=away_corners,
        home_corner_conceded_avg=home_corners_conceded if 'home_corners_conceded' in dir() else home_defense * 4,
        away_corner_conceded_avg=away_corners_conceded if 'away_corners_conceded' in dir() else away_defense * 4
    )
    
    cards_pred = adv_predictor.predict_cards(
        home_card_avg=home_cards,
        away_card_avg=away_cards,
        ref_card_avg=4.5
    )
    
    shots_pred = adv_predictor.predict_shots(
        home_shots_avg=home_shots,
        away_shots_avg=away_shots,
        home_on_goal_avg=home_shots * 0.35,
        away_on_goal_avg=away_shots * 0.35
    )
    
    handicap_predictor = HandicapPredictor(poisson)
    handicap_pred = handicap_predictor.predict(home_xg, away_xg)
    exact_predictor = ExactScorePredictor(poisson)
    exact_pred = exact_predictor.predict(home_xg, away_xg)
    
    st.markdown("---")
    
    # ═══════════════════════════════════════════════════════
    # DISPLAY PREDICTIONS (same as before)
    # ═══════════════════════════════════════════════════════
    _display_predictions(
        home_name, away_name, home_xg, away_xg,
        match_result, goals_pred, corners_pred, cards_pred, shots_pred,
        handicap_pred, exact_pred
    )


def _display_predictions(home_name, away_name, home_xg, away_xg, 
                         match_result, goals_pred, corners_pred, cards_pred, 
                         shots_pred, handicap_pred, exact_pred):
    """Display all prediction results."""
    import pandas as pd
    
    # xG Display
    col_xg_title, _ = st.columns([2, 1])
    with col_xg_title:
        st.markdown(f"### {render_icon('assessment')} Goles Esperados (xG)", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(render_metric_card(f"{home_xg:.2f}", home_name, "accent"), unsafe_allow_html=True)
    with col2:
        st.markdown(render_metric_card(f"{home_xg + away_xg:.2f}", "Total Partido", "warning"), unsafe_allow_html=True)
    with col3:
        st.markdown(render_metric_card(f"{away_xg:.2f}", away_name, "danger"), unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 1X2 Probability Bar
    st.markdown(f"### {render_icon('balance')} Probabilidad 1X2", unsafe_allow_html=True)
    st.markdown(render_probability_bar(
        match_result["home_win"],
        match_result["draw"],
        match_result["away_win"]
    ), unsafe_allow_html=True)
    
    # Odds equivalent
    col1, col2, col3 = st.columns(3)
    with col1:
        odds_home = round(1 / match_result["home_win"], 2) if match_result["home_win"] > 0 else "-"
        st.metric(f"Victoria {home_name}", f"{match_result['home_win']*100:.1f}%", f"@ {odds_home}")
    with col2:
        odds_draw = round(1 / match_result["draw"], 2) if match_result["draw"] > 0 else "-"
        st.metric("Empate", f"{match_result['draw']*100:.1f}%", f"@ {odds_draw}")
    with col3:
        odds_away = round(1 / match_result["away_win"], 2) if match_result["away_win"] > 0 else "-"
        st.metric(f"Victoria {away_name}", f"{match_result['away_win']*100:.1f}%", f"@ {odds_away}")
    
    st.markdown("---")
    
    # Market Tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        ":material/sports_soccer: Goles", 
        ":material/trending_up: Hándicap", 
        ":material/scoreboard: Marcador", 
        ":material/flag: Córners", 
        ":material/style: Tarjetas",
        ":material/ads_click: Remates"
    ])
    
    # TAB 1: GOALS
    with tab1:
        col1, col2 = st.columns([3, 2])
        
        with col1:
            st.markdown(f"#### {render_icon('sports_soccer')} Over/Under Goles", unsafe_allow_html=True)
            data = []
            for line, probs in goals_pred.over_under.items():
                data.append({
                    "Línea": f"{line} Goles",
                    "Over (%)": probs["over"],
                    "Cuota Over": round(1/probs["over"], 2) if probs["over"] > 0 else 0,
                    "Under (%)": probs["under"],
                    "Cuota Under": round(1/probs["under"], 2) if probs["under"] > 0 else 0,
                })
            
            st.dataframe(
                pd.DataFrame(data),
                column_config={
                    "Over (%)": st.column_config.ProgressColumn("Over", format="%.1f%%", min_value=0, max_value=1),
                    "Under (%)": st.column_config.ProgressColumn("Under", format="%.1f%%", min_value=0, max_value=1),
                },
                hide_index=True, use_container_width=True
            )
        
        with col2:
            st.markdown(f"#### BTTS (Ambos Marcan)", unsafe_allow_html=True)
            btts_yes = goals_pred.btts["yes"]
            btts_no = goals_pred.btts["no"]
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                st.metric("Sí", f"{btts_yes*100:.1f}%", f"@ {round(1/btts_yes, 2)}")
            with col_b2:
                st.metric("No", f"{btts_no*100:.1f}%", f"@ {round(1/btts_no, 2)}")
    
    # TAB 2: HANDICAP
    with tab2:
        st.markdown(f"### {render_icon('trending_up')} Hándicap Asiático", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        
        ah_data_home = []
        ah_data_away = []
        for line, probs in handicap_pred.asian_handicaps.items():
            win_prob = probs.get('win', 0)
            row = {
                "Línea": line.replace('home_', '').replace('away_', ''),
                "Probabilidad": win_prob,
                "Cuota": round(1/win_prob, 2) if win_prob > 0 else 0
            }
            if "home" in line:
                ah_data_home.append(row)
            elif "away" in line:
                ah_data_away.append(row)
        
        with col1:
            st.markdown(f"**{home_name}**")
            st.dataframe(pd.DataFrame(ah_data_home).sort_values("Línea"), 
                        column_config={"Probabilidad": st.column_config.ProgressColumn("Prob", format="%.1f%%", min_value=0, max_value=1)},
                        hide_index=True, use_container_width=True)
        with col2:
            st.markdown(f"**{away_name}**")
            st.dataframe(pd.DataFrame(ah_data_away).sort_values("Línea"),
                        column_config={"Probabilidad": st.column_config.ProgressColumn("Prob", format="%.1f%%", min_value=0, max_value=1)},
                        hide_index=True, use_container_width=True)
    
    # TAB 3: EXACT SCORE
    with tab3:
        st.markdown(f"#### {render_icon('scoreboard')} Top 5 Marcadores Probables", unsafe_allow_html=True)
        cols = st.columns(5)
        for i, (score, prob) in enumerate(exact_pred.top_scorelines[:5]):
            with cols[i]:
                odds = round(1/prob, 2) if prob > 0 else "-"
                st.markdown(f"""
                <div style="background: var(--bg-card); border: 1px solid var(--border);
                            padding: 12px; border-radius: 8px; text-align: center;">
                    <div style="font-size: 1.4rem; font-weight: 700; color: var(--accent);">{score}</div>
                    <div style="font-size: 0.9rem;">{prob*100:.1f}%</div>
                    <div style="font-size: 0.75rem; opacity: 0.8;">@ {odds}</div>
                </div>
                """, unsafe_allow_html=True)
    
    # TAB 4: CORNERS
    with tab4:
        col1, col2 = st.columns([3, 2])
        with col1:
            st.markdown(f"#### {render_icon('flag')} Over/Under Córners", unsafe_allow_html=True)
            corners_data = []
            for line, probs in corners_pred.over_under.items():
                corners_data.append({
                    "Línea": f"+ {line}",
                    "Probabilidad": probs["over"],
                    "Cuota": round(1/probs["over"], 2) if probs["over"] > 0 else 0
                })
            st.dataframe(pd.DataFrame(corners_data),
                        column_config={"Probabilidad": st.column_config.ProgressColumn("Prob", format="%.1f%%", min_value=0, max_value=1)},
                        hide_index=True, use_container_width=True)
        
        with col2:
            st.markdown("#### Córners Esperados")
            st.metric(home_name, f"{corners_pred.home_expected:.1f}")
            st.metric(away_name, f"{corners_pred.away_expected:.1f}")
            st.metric("Total", f"{corners_pred.total_expected:.1f}")
    
    # TAB 5: CARDS
    with tab5:
        col1, col2 = st.columns([3, 2])
        with col1:
            st.markdown(f"#### {render_icon('style')} Over/Under Tarjetas", unsafe_allow_html=True)
            cards_data = []
            for line, probs in cards_pred.over_under.items():
                cards_data.append({
                    "Línea": f"+ {line}",
                    "Probabilidad": probs["over"],
                    "Cuota": round(1/probs["over"], 2) if probs["over"] > 0 else 0
                })
            st.dataframe(pd.DataFrame(cards_data),
                        column_config={"Probabilidad": st.column_config.ProgressColumn("Prob", format="%.1f%%", min_value=0, max_value=1)},
                        hide_index=True, use_container_width=True)
        
        with col2:
            st.markdown("#### Tarjetas Esperadas")
            st.metric("Total", f"{cards_pred.total_expected:.1f}")
            st.metric(home_name, f"{cards_pred.home_expected:.1f}")
            st.metric(away_name, f"{cards_pred.away_expected:.1f}")
    
    # TAB 6: SHOTS
    with tab6:
        st.markdown(f"#### {render_icon('ads_click')} Remates Esperados", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**{home_name}**")
            st.metric("Remates Totales", f"{shots_pred.home_shots_expected:.1f}")
            st.metric("A Puerta", f"{shots_pred.home_on_goal_expected:.1f}")
        with col2:
            st.markdown(f"**{away_name}**")
            st.metric("Remates Totales", f"{shots_pred.away_shots_expected:.1f}")
            st.metric("A Puerta", f"{shots_pred.away_on_goal_expected:.1f}")
