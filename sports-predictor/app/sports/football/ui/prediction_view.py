"""
Football Prediction View - Modern UI for Match Predictions.
"""
import streamlit as st
from app.ui.theme import render_probability_bar, render_metric_card, render_icon
from app.sports.football.predictions import (
    PoissonModel, GoalsPredictor, MatchResultPredictor,
    CornersPredictor, HandicapPredictor, ExactScorePredictor
)


def show_prediction_view():
    """Display the prediction dashboard with professional UI."""
    
    # Header
    st.markdown(f"""
    <div style="margin-bottom: 24px;">
        <h1 style="margin: 0;">{render_icon('query_stats')} Predicción de Partido</h1>
        <p style="color: var(--text-secondary); margin-top: 8px;">Análisis pre-partido con probabilidades para todos los mercados</p>
    </div>
    """, unsafe_allow_html=True)
    
    # ═══════════════════════════════════════════════════════
    # Match Input
    with st.expander("⚙️ Configuración del Partido", expanded=True):
        col1, col2, col3 = st.columns([2, 1, 2])
        
        # Predefined list of top teams
        teams = sorted([
            "Real Madrid", "Barcelona", "Atletico Madrid", "Sevilla", "Valencia",
            "Manchester City", "Arsenal", "Liverpool", "Manchester United", "Chelsea", "Tottenham",
            "Bayern Munich", "Dortmund", "Leverkusen", "RB Leipzig",
            "PSG", "Monaco", "Marseille",
            "Inter Milan", "AC Milan", "Juventus", "Napoli", "Roma",
            "Benfica", "Porto", "Sporting CP"
        ])
        
        with col1:
            st.markdown(f"### {render_icon('home')} Local", unsafe_allow_html=True)
            home_name = st.selectbox("Equipo Local", teams, index=teams.index("Real Madrid"), key="home_name")
            home_attack = st.slider("Goles marcados/partido (Local)", 0.5, 3.5, 1.8, 0.1, key="home_attack")
            home_defense = st.slider("Goles recibidos/partido (Local)", 0.5, 2.5, 0.9, 0.1, key="home_defense")
            home_corners = st.slider("Córners/partido (Local)", 3.0, 10.0, 5.5, 0.5, key="home_corners")
            home_cards = st.slider("Tarjetas/partido (Local)", 0.5, 5.0, 2.1, 0.1, key="home_cards")
            home_shots = st.slider("Remates/partido (Local)", 5.0, 20.0, 12.5, 0.5, key="home_shots")
        
        with col2:
            st.markdown("<div style='text-align: center; padding-top: 60px; font-size: 1.5rem; color: var(--text-secondary);'>VS</div>", unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"### {render_icon('flight')} Visitante", unsafe_allow_html=True)
            away_name = st.selectbox("Equipo Visitante", teams, index=teams.index("Barcelona"), key="away_name")
            away_attack = st.slider("Goles marcados/partido (Visitante)", 0.5, 3.5, 1.5, 0.1, key="away_attack")
            away_defense = st.slider("Goles recibidos/partido (Visitante)", 0.5, 2.5, 1.1, 0.1, key="away_defense")
            away_corners = st.slider("Córners/partido (Visitante)", 3.0, 10.0, 5.0, 0.5, key="away_corners")
            away_cards = st.slider("Tarjetas/partido (Visitante)", 0.5, 5.0, 2.5, 0.1, key="away_cards")
            away_shots = st.slider("Remates/partido (Visitante)", 5.0, 20.0, 10.5, 0.5, key="away_shots")
    
    # ═══════════════════════════════════════════════════════
    # CALCULATE PREDICTIONS
    # ═══════════════════════════════════════════════════════
    poisson = PoissonModel(league_avg_home_goals=1.5, league_avg_away_goals=1.2)
    
    # Calculate xG
    home_xg = home_attack * (away_defense / 1.0) * 1.1  # Home advantage
    away_xg = away_attack * (home_defense / 1.0) * 0.9
    
    # Get predictions
    match_result = poisson.prob_match_result(home_xg, away_xg)
    goals_predictor = GoalsPredictor(poisson)
    goals_pred = goals_predictor.predict(home_xg, away_xg)
    
    from app.sports.football.predictions import AdvancedPredictor
    adv_predictor = AdvancedPredictor(poisson)
    
    # Corners
    corners_pred = adv_predictor.predict_corners(
        home_corner_avg=home_corners,
        away_corner_avg=away_corners,
        home_corner_conceded_avg=home_defense * 4, # Fallback estimate
        away_corner_conceded_avg=away_defense * 4
    )
    
    # Cards
    cards_pred = adv_predictor.predict_cards(
        home_card_avg=home_cards,
        away_card_avg=away_cards,
        ref_card_avg=4.5 # Standard average
    )
    
    # Shots
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
    # MAIN PREDICTION DISPLAY
    # ═══════════════════════════════════════════════════════
    
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
    
    # ═══════════════════════════════════════════════════════
    # MARKET TABS
    # ═══════════════════════════════════════════════════════
    # Using Material Icons syntax for Streamlit tabs
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        ":material/sports_soccer: Goles", 
        ":material/trending_up: Hándicap", 
        ":material/scoreboard: Marcador", 
        ":material/flag: Córners", 
        ":material/style: Tarjetas",
        ":material/ads_click: Remates",
        ":material/summarize: Resumen"
    ])
    
    # TAB 1: GOALS
    with tab1:
        import pandas as pd
        
        col1, col2 = st.columns([3, 2])
        
        with col1:
            st.markdown(f"#### {render_icon('sports_soccer')} Probabilidades de Goles (Over/Under)", unsafe_allow_html=True)
            st.caption("Predicción basada en la distribución de Poisson de ambos equipos.")
            
            # Prepare data for DataFrame
            data = []
            for line, probs in goals_pred.over_under.items():
                row = {
                    "Línea": f"{line} Goles",
                    "Más (%)": probs["over"],
                    "Más (Cuota)": round(1/probs["over"], 2) if probs["over"] > 0 else 0,
                    "Menos (%)": probs["under"],
                    "Menos (Cuota)": round(1/probs["under"], 2) if probs["under"] > 0 else 0,
                }
                data.append(row)
            
            df_goals = pd.DataFrame(data)
            
            st.dataframe(
                df_goals,
                column_config={
                    "Línea": st.column_config.TextColumn(
                        "Línea",
                        help="Umbral de goles totales en el partido (suma de ambos equipos)",
                        width="medium"
                    ),
                    "Más (%)": st.column_config.ProgressColumn(
                        "Más (Over)",
                        help="Probabilidad de que haya MÁS goles que la línea indicada",
                        format="%.1f%%",
                        min_value=0,
                        max_value=1,
                    ),
                    "Más (Cuota)": st.column_config.NumberColumn(
                        "Cuota Over",
                        format="%.2f",
                        help="Cuota decimal estimada para el mercado Over"
                    ),
                    "Menos (%)": st.column_config.ProgressColumn(
                        "Menos (Under)",
                        help="Probabilidad de que haya MENOS goles que la línea indicada",
                        format="%.1f%%",
                        min_value=0,
                        max_value=1,
                    ),
                    "Menos (Cuota)": st.column_config.NumberColumn(
                        "Cuota Under",
                        format="%.2f",
                        help="Cuota decimal estimada para el mercado Under"
                    ),
                },
                hide_index=True,
                use_container_width=True
            )
        
        with col2:
            st.markdown(f"#### {render_icon('compare_arrows')} Ambos Marcan (BTTS)", unsafe_allow_html=True)
            st.info("BTTS (Both Teams To Score): Probabilidad de que ambos equipos anoten al menos un gol.", icon="ℹ️")
            
            btts_yes = goals_pred.btts["yes"]
            btts_no = goals_pred.btts["no"]
            
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                st.metric("Sí", f"{btts_yes*100:.1f}%", f"@ {round(1/btts_yes, 2)}")
            with col_b2:
                st.metric("No", f"{btts_no*100:.1f}%", f"@ {round(1/btts_no, 2)}")
            
            st.markdown("---")
            st.markdown("#### Par / Impar")
            st.caption("Predicción sobre si la suma total de goles será par o impar.")
            
            # Simple chart for Odd/Even
            odd_even_df = pd.DataFrame({
                "Resultado": ["Par", "Impar"],
                "Probabilidad": [goals_pred.odd_even['even'], goals_pred.odd_even['odd']]
            })
            st.dataframe(
                odd_even_df,
                column_config={
                    "Probabilidad": st.column_config.ProgressColumn(
                        "Prob (%)",
                        format="%.1f%%",
                        min_value=0,
                        max_value=1,
                    )
                },
                hide_index=True,
                use_container_width=True
            )
    
    # TAB 2: HANDICAP
    with tab2:
        st.markdown(f"### {render_icon('trending_up')} Hándicap Asiático", unsafe_allow_html=True)
        st.info("El hándicap asiático añade o resta goles virtuales al resultado final para equilibrar el partido.", icon="ℹ️")
        
        col1, col2 = st.columns(2)
        
        # Prepare Data
        ah_data_home = []
        ah_data_away = []
        
        for line, probs in handicap_pred.asian_handicaps.items():
            win_prob = probs.get('win', 0)
            void_prob = probs.get('void', 0)
            # Create row
            row = {
                "Línea": line.replace('home_', '').replace('away_', ''),
                "Probabilidad": win_prob,
                "Cuota": round(1/win_prob, 2) if win_prob > 0 else 0,
                "Void": void_prob
            }
            
            if "home" in line:
                ah_data_home.append(row)
            elif "away" in line:
                ah_data_away.append(row)
        
        # Display Tables
        with col1:
            st.markdown(f"**Favoritismo Local ({home_name})**")
            st.dataframe(
                pd.DataFrame(ah_data_home).sort_values("Línea"),
                column_config={
                    "Línea": st.column_config.TextColumn("Línea (+/-)", help="Goles sumados/restados al local"),
                    "Probabilidad": st.column_config.ProgressColumn(
                        "Ganar (%)", 
                        format="%.1f%%", 
                        min_value=0, max_value=1,
                        help="Probabilidad de ganar la apuesta"
                    ),
                    "Cuota": st.column_config.NumberColumn("Cuota Est.", format="%.2f"),
                    "Void": st.column_config.NumberColumn("Void (%)", format="%.0f%%", help="Probabilidad de devolución (empate tras hándicap)")
                },
                hide_index=True,
                use_container_width=True
            )
        
        with col2:
            st.markdown(f"**Favoritismo Visitante ({away_name})**")
            st.dataframe(
                pd.DataFrame(ah_data_away).sort_values("Línea"),
                column_config={
                    "Línea": st.column_config.TextColumn("Línea (+/-)", help="Goles sumados/restados al visitante"),
                    "Probabilidad": st.column_config.ProgressColumn(
                        "Ganar (%)", 
                        format="%.1f%%", 
                        min_value=0, max_value=1,
                        help="Probabilidad de ganar la apuesta"
                    ),
                    "Cuota": st.column_config.NumberColumn("Cuota Est.", format="%.2f"),
                    "Void": st.column_config.NumberColumn("Void (%)", format="%.0f%%", help="Probabilidad de devolución")
                },
                hide_index=True,
                use_container_width=True
            )
    
    # TAB 3: EXACT SCORE
    with tab3:
        st.markdown(f"#### {render_icon('scoreboard')} Top Marcadores Probables", unsafe_allow_html=True)
        
        cols = st.columns(5)
        for i, (score, prob) in enumerate(exact_pred.top_scorelines[:5]):
            with cols[i]:
                odds = round(1/prob, 2) if prob > 0 else "-"
                st.markdown(f"""
                <div style="background: var(--bg-card); border: 1px solid var(--border);
                            padding: 12px; border-radius: 8px; text-align: center;">
                    <div style="font-size: 1.4rem; font-weight: 700; color: var(--accent);">{score}</div>
                    <div style="font-size: 0.9rem;">{prob*100:.1f}%</div>
                    <div style="font-size: 0.75rem; opacity: 0.8;">Cuota: {odds}</div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"#### {render_icon('difference')} Margen de Victoria", unsafe_allow_html=True)
        margins = exact_pred.victory_margin
        col1, col2, col3 = st.columns(3)
        with col1:
            st.progress(margins['home_1'], text=f"{home_name} por 1 gol ({margins['home_1']*100:.1f}%)")
            st.progress(margins['home_2'], text=f"{home_name} por 2 goles ({margins['home_2']*100:.1f}%)")
        with col2:
            st.progress(margins['draw_0-0'], text=f"Empate 0-0 ({margins['draw_0-0']*100:.1f}%)")
            st.progress(margins['draw_with_goals'], text=f"Empate con goles ({margins['draw_with_goals']*100:.1f}%)")
        with col3:
            st.progress(margins['away_1'], text=f"{away_name} por 1 gol ({margins['away_1']*100:.1f}%)")
            st.progress(margins['away_2'], text=f"{away_name} por 2 goles ({margins['away_2']*100:.1f}%)")
    
    # TAB 4: CORNERS
    with tab4:
        col1, col2 = st.columns([3, 2])
        with col1:
            st.markdown(f"#### {render_icon('flag')} Probabilidades de Córners (Over)", unsafe_allow_html=True)
            corners_data = []
            for line, probs in corners_pred.over_under.items():
                corners_data.append({
                    "Línea": f"+ {line} Córners",
                    "Probabilidad": probs["over"],
                    "Cuota Justa": round(1/probs["over"], 2) if probs["over"] > 0 else 0
                })
            
            st.dataframe(
                pd.DataFrame(corners_data),
                column_config={
                    "Línea": st.column_config.TextColumn("Mercado", width="medium"),
                    "Probabilidad": st.column_config.ProgressColumn("Prob (%)", format="%.1f%%", min_value=0, max_value=1),
                    "Cuota Justa": st.column_config.NumberColumn("Cuota Justa", format="%.2f")
                },
                hide_index=True, use_container_width=True
            )
        
        with col2:
            st.markdown("#### Quién tendrá más córners")
            st.caption("Predicción basada en Poisson de promedios históricos.")
            most = corners_pred.most_corners
            st.markdown(f"""
            <div style="display: flex; flex-direction: column; gap: 10px;">
                {render_metric_card(f"{most['home_win']*100:.1f}%", home_name, "accent")}
                {render_metric_card(f"{most['draw']*100:.1f}%", "Igual Cantidad", "warning")}
                {render_metric_card(f"{most['away_win']*100:.1f}%", away_name, "danger")}
            </div>
            """, unsafe_allow_html=True)
            
    # TAB 5: CARDS
    with tab5:
        col1, col2 = st.columns([3, 2])
        with col1:
            st.markdown(f"#### {render_icon('style')} Probabilidades de Tarjetas (Over)", unsafe_allow_html=True)
            cards_data = []
            for line, probs in cards_pred.over_under.items():
                cards_data.append({
                    "Línea": f"+ {line} Tarjetas",
                    "Probabilidad": probs["over"],
                    "Cuota Justa": round(1/probs["over"], 2) if probs["over"] > 0 else 0
                })
            st.dataframe(pd.DataFrame(cards_data), column_config={
                "Línea": st.column_config.TextColumn("Mercado"),
                "Probabilidad": st.column_config.ProgressColumn("Prob (%)", format="%.1f%%", min_value=0, max_value=1),
                "Cuota Justa": st.column_config.NumberColumn("Cuota Justa", format="%.2f")
            }, hide_index=True, use_container_width=True)
            
        with col2:
            st.markdown("#### Agresividad Esperada")
            st.markdown(render_metric_card(f"{cards_pred.total_expected:.1f}", "Tarjetas Totales", "warning"), unsafe_allow_html=True)
            st.markdown(f"**Local ({home_name}):** {cards_pred.home_expected:.1f}")
            st.markdown(f"**Visitante ({away_name}):** {cards_pred.away_expected:.1f}")
            st.info("Modelo ajustado por promedios de equipos y tendencia del árbitro (est. 4.5 tarjetas/partido).")

    # TAB 6: SHOTS
    with tab6:
        st.markdown(f"#### {render_icon('ads_click')} Remates y Puntería", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**{home_name}**")
            st.markdown(render_metric_card(f"{shots_pred.home_shots_expected:.1f}", "Remates Totales", "accent"), unsafe_allow_html=True)
            st.markdown(f"**Remates a Puerta:** {shots_pred.home_on_goal_expected:.1f}")
        with col2:
            st.markdown(f"**{away_name}**")
            st.markdown(render_metric_card(f"{shots_pred.away_shots_expected:.1f}", "Remates Totales", "danger"), unsafe_allow_html=True)
            st.markdown(f"**Remates a Puerta:** {shots_pred.away_on_goal_expected:.1f}")
        st.caption("Predicción basada en volumen ofensivo histórico de los últimos 10 partidos.")

    # TAB 7: SUMMARY
    with tab7:
        st.markdown(f"### {render_icon('summarize')} Resumen Estratégico", unsafe_allow_html=True)
        summary_data = {
            "Mercado": [
                "Victoria Local", "Empate", "Victoria Visitante",
                "Over 2.5 Goles", "Over 9.5 Córners", "Over 3.5 Tarjetas",
                "BTTS Sí"
            ],
            "Probabilidad (%)": [
                f"{match_result['home_win']*100:.1f}%",
                f"{match_result['draw']*100:.1f}%",
                f"{match_result['away_win']*100:.1f}%",
                f"{goals_pred.over_under['2.5']['over']*100:.1f}%",
                f"{corners_pred.over_under['9.5']['over']*100:.1f}%",
                f"{cards_pred.over_under['3.5']['over']*100:.1f}%",
                f"{goals_pred.btts['yes']*100:.1f}%"
            ],
            "Cuota Justa": [
                round(1/match_result['home_win'], 2),
                round(1/match_result['draw'], 2),
                round(1/match_result['away_win'], 2),
                round(1/goals_pred.over_under['2.5']['over'], 2),
                round(1/corners_pred.over_under['9.5']['over'], 2),
                round(1/cards_pred.over_under['3.5']['over'], 2),
                round(1/goals_pred.btts['yes'], 2)
            ]
        }
        st.dataframe(pd.DataFrame(summary_data), hide_index=True, use_container_width=True)
