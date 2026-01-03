import streamlit as st
import pandas as pd
from ..styles import _apply_table_styles, get_section_title_html, render_styled_table
from .common import _render_as_card

def _infer_team(outcome: dict, market_label: str, home_team: str, away_team: str, home_id=None, away_id=None) -> str:
    """Intenta inferir el equipo del jugador basado en datos disponibles."""
    # 1. ID Match (Prioridad)
    epid = outcome.get("eventParticipantId")
    if epid:
        if epid == home_id: return home_team
        if epid == away_id: return away_team

    # 2. Directamente del outcome (si la API lo provee)
    if "team" in outcome: return outcome["team"]
    if "competitorName" in outcome: return outcome["competitorName"]
    
    # 3. Contexto del Label del Mercado
    lbl_lower = market_label.lower()
    if home_team.lower() in lbl_lower: return home_team
    if away_team.lower() in lbl_lower: return away_team
    
    return "-"


def _get_player_weighted_prob(player_name: str, metric: str, threshold: float = 0.5, alpha: float = 0.15) -> float:
    """
    Calcula la probabilidad ponderada (EWMA) de que un jugador supere un umbral en una métrica.
    """
    from app.core.database import get_session
    from app.sports.football.models import PlayerMatchStats, Player, Fixture
    from app.sports.football.analytics.data.team_stats import calculate_dynamic_weighted_avg
    from sqlmodel import select
    
    with next(get_session()) as session:
        # 1. Buscar jugador por nombre
        player_stmt = select(Player).where(Player.name.contains(player_name))
        player_obj = session.exec(player_stmt).first()
        
        if not player_obj:
            return None
            
        # 2. Mapear métrica de la UI a la DB
        metric_map = {
            "goals": PlayerMatchStats.goals,
            "shots": PlayerMatchStats.shots,
            "shots_on_goal": PlayerMatchStats.shots_on_goal,
            "yellow_cards": PlayerMatchStats.yellow_cards,
            "saves": PlayerMatchStats.saves,
            "assists": PlayerMatchStats.assists
        }
        db_field = metric_map.get(metric)
        if db_field is None: return None
        
        # 3. Traer últimos 20 partidos
        stats_stmt = (
            select(db_field)
            .join(Fixture, Fixture.id == PlayerMatchStats.fixture_id)
            .where(PlayerMatchStats.player_id == player_obj.id)
            .order_by(Fixture.date.desc())
            .limit(20)
        )
        history = session.exec(stats_stmt).all()
        
        if not history:
            return None
            
        # 4. Convertir a binario según umbral
        occurrence = [1 if (val or 0) >= threshold else 0 for val in history]
        prob = calculate_dynamic_weighted_avg(occurrence, alpha=alpha)
        return round(prob * 100, 1)

def _render_scorers_markets(markets: list, home_team: str, away_team: str, home_id=None, away_id=None, do_analysis: bool = False):
    """Renderiza tabla consolidada de goleadores (Primer Gol + Marcará)."""
    players_data = {}
    
    first_scorer_mkt = []
    anytime_scorer_mkt = []
    
    for m in markets:
        lbl = m.get("label", "").lower()
        if "primer" in lbl and "goleador" in lbl:
            # Pasar contexto del mercado a los outcomes temporalmente si es necesario
            for out in m.get("outcomes", []):
                out["_market_label"] = m.get("label", "")
                first_scorer_mkt.append(out)
        elif "marca" in lbl or "marcará" in lbl or "cualquier momento" in lbl:
            for out in m.get("outcomes", []):
                out["_market_label"] = m.get("label", "")
                anytime_scorer_mkt.append(out)
            
    if not first_scorer_mkt and not anytime_scorer_mkt:
        st.info("No hay datos de goleadores disponibles.")
        return

    st.markdown(get_section_title_html("Goleadores"), unsafe_allow_html=True)

    # 1. CÁLCULO DE PROBABILIDADES DINÁMICAS (Si aplica)
    player_probs = {}
    if do_analysis:
        from app.core.database import get_session
        from app.sports.football.models import PlayerMatchStats, Player, Fixture
        from app.sports.football.analytics.data.team_stats import calculate_dynamic_weighted_avg
        from sqlmodel import select, or_
        
        with next(get_session()) as session:
            # Recopilar todos los nombres de jugadores únicos
            all_names = set()
            for out in first_scorer_mkt + anytime_scorer_mkt:
                name = out.get("participant") or out.get("label")
                if name: all_names.add(name)
            
            # Buscar stats para cada jugador
            for name in all_names:
                # Intento de matching por nombre (simplificado)
                player_stmt = select(Player).where(Player.name.contains(name))
                player_obj = session.exec(player_stmt).first()
                
                if player_obj:
                    # Traer últimos 20 partidos de este jugador
                    stats_stmt = (
                        select(PlayerMatchStats.goals)
                        .join(Fixture, Fixture.id == PlayerMatchStats.fixture_id)
                        .where(PlayerMatchStats.player_id == player_obj.id)
                        .order_by(Fixture.date.desc())
                        .limit(20)
                    )
                    goals_history = session.exec(stats_stmt).all()
                    if goals_history:
                        # Convertir a binario (marcó o no)
                        occurrence = [1 if g > 0 else 0 for g in goals_history]
                        prob = calculate_dynamic_weighted_avg(occurrence, alpha=0.15) # Alpha 0.15 para más sensibilidad
                        player_probs[name] = round(prob * 100, 1)

    # 2. PROCESAR OUTCOMES
    def process_player(out, key_type):
        name = out.get("participant") or out.get("label")
        if not name: return
        
        if "ningún" in name.lower() or (name == "Sí" and key_type == "Marcará"):
             return

        if name not in players_data:
            # Inferir equipo solo la primera vez
            team = _infer_team(out, out.get("_market_label", ""), home_team, away_team, home_id, away_id)
            players_data[name] = {
                "Equipo": team, 
                "Jugador": name, 
                "Primer Gol": None, 
                "Marcará": None, 
                "Prob. %": player_probs.get(name, "-")
            }
        
        # Si ya existe pero no tiene equipo, intentar inferir de nuevo
        if players_data[name]["Equipo"] == "-":
             team = _infer_team(out, out.get("_market_label", ""), home_team, away_team, home_id, away_id)
             if team != "-": players_data[name]["Equipo"] = team
             
        players_data[name][key_type] = out.get("odds")

    for out in first_scorer_mkt:
        process_player(out, "Primer Gol")

    for out in anytime_scorer_mkt:
         process_player(out, "Marcará")
    
    data_list = list(players_data.values())
    if not data_list: return
        
    df = pd.DataFrame(data_list)
    
    # Ordenar por probabilidad si existe, sino por cuota
    if do_analysis:
        df["_sort_prob"] = pd.to_numeric(df["Prob. %"], errors='coerce').fillna(0)
        df = df.sort_values(by=["_sort_prob"], ascending=False)
    else:
        df["_sort_any"] = df["Marcará"].fillna(9999)
        df = df.sort_values(by=["_sort_any"])
    
    cols = ["Equipo", "Jugador", "Primer Gol", "Marcará"]
    if do_analysis: cols.append("Prob. %")
    
    final_df = df[list(set(cols) & set(df.columns))]
    final_df = final_df[cols]
    
    numeric_cols = ["Primer Gol", "Marcará"]
    if do_analysis: numeric_cols.append("Prob. %")
    
    styler = _apply_table_styles(final_df, numeric_cols)
    
    column_config = {
        "Primer Gol": st.column_config.NumberColumn(format="%.2f"),
        "Marcará": st.column_config.NumberColumn(format="%.2f")
    }
    if do_analysis:
        column_config["Prob. %"] = st.column_config.NumberColumn(format="%.1f%%")
    
    rows_count = len(final_df)
    dynamic_height = (rows_count + 1) * 35 + 3
    
    st.dataframe(
        styler, 
        hide_index=True, 
        width='stretch',
        column_config=column_config,
        height=dynamic_height
    )
    st.markdown("")


def _render_player_cards_markets(markets: list, home_team: str, away_team: str, home_id=None, away_id=None):
    """Renderiza mercados de tarjetas de jugadores en tabla consolidada."""
    player_list_markets = []
    other_markets = []
    
    for m in markets:
        lbl = m.get("label", "").lower()
        if "recibirá" in lbl:
            player_list_markets.append(m)
        else:
            other_markets.append(m)
            
    if player_list_markets:
        players_data = {}
        
        for m in player_list_markets:
            raw_label = m.get("label", "")
            lbl_lower = raw_label.lower()
            
            col_name = "Tarjeta"
            if "roja" in lbl_lower:
                col_name = "Roja"
            elif "tarjeta" in lbl_lower and "roja" not in lbl_lower:
                col_name = "Tarjeta"
            else:
                col_name = raw_label 
                
            for out in m.get("outcomes", []):
                p_name = out.get("participant") or out.get("label")
                if not p_name or p_name == "Sí": 
                    continue
                    
                if p_name not in players_data:
                    team = _infer_team(out, raw_label, home_team, away_team, home_id, away_id)
                    players_data[p_name] = {"Equipo": team, "Jugador": p_name}
                
                players_data[p_name][col_name] = out.get("odds")
        
        data_list = list(players_data.values())
        if data_list:
            st.markdown(get_section_title_html("Tarjetas de Jugadores"), unsafe_allow_html=True)
            df = pd.DataFrame(data_list)
            
            if "Tarjeta" not in df.columns: df["Tarjeta"] = None
            if "Roja" not in df.columns: df["Roja"] = None
            
            cols_to_show = ["Equipo", "Jugador"]
            numeric_cols = []
            
            if df["Tarjeta"].notna().any():
                cols_to_show.append("Tarjeta")
                numeric_cols.append("Tarjeta")
            if df["Roja"].notna().any():
                cols_to_show.append("Roja")
                numeric_cols.append("Roja")
                
            if "Tarjeta" in df.columns:
                df = df.sort_values(by="Tarjeta")
            elif "Roja" in df.columns:
                 df = df.sort_values(by="Roja")
                 
            final_df = df[cols_to_show]
            styler = _apply_table_styles(final_df, numeric_cols)
            
            column_config = {
                "Tarjeta": st.column_config.NumberColumn(format="%.2f"),
                "Roja": st.column_config.NumberColumn(format="%.2f")
            }
            
            rows_count = len(final_df)
            dynamic_height = (rows_count + 1) * 35 + 3
            
            st.dataframe(
                styler,
                hide_index=True,
                width='stretch',
                column_config=column_config,
                height=dynamic_height
            )
            st.markdown("")

    if other_markets:
        if player_list_markets: st.markdown("---")
        
        label_map = {
            "1": home_team,
            "X": "Empate",
            "2": away_team,
            "Yes": "Sí",
            "No": "No"
        }
        
        for m in other_markets:
            _render_as_card(m.get("label"), m.get("outcomes", []), label_map)


def _render_generic_player_table(markets: list, title: str, 
                               home_team: str, away_team: str,
                               home_id=None, away_id=None,
                               val_col_name: str = "Total", 
                               is_binary: bool = False,
                               line_format_div_1000: bool = False,
                               do_analysis: bool = False,
                               metric: str = None):
    """Renderizador genérico para tablas de jugadores con soporte de análisis."""
    if not markets: return

    st.markdown(get_section_title_html(title), unsafe_allow_html=True)
    
    players_data = []
    
    for m in markets:
        m_label = m.get("label", "")
        for out in m.get("outcomes", []):
            p_name = out.get("participant") or out.get("label")
            if not p_name: continue

            if "más de" in p_name.lower() or "menos de" in p_name.lower():
                continue
            
            odds = out.get("odds")
            line = out.get("line")
            
            if line is None and not is_binary:
                continue
            
            team = _infer_team(out, m_label, home_team, away_team, home_id, away_id)
            row = {"Equipo": team, "Jugador": p_name}
            
            # Línea interpretada
            processed_line = 0.5
            if line is not None:
                try:
                    val = float(line)
                    if line_format_div_1000: val /= 1000.0
                    processed_line = val
                    
                    if val.is_integer(): val_str = str(int(val))
                    else: val_str = f"{val:.1f}"
                    
                    row[val_col_name] = f"Más de {val_str}"
                except:
                    row[val_col_name] = str(line)
            else:
                row[val_col_name] = "-"

            # --- ANÁLISIS ---
            if do_analysis and metric:
                row["Prob. %"] = _get_player_weighted_prob(p_name, metric, threshold=processed_line)
            
            col_cuota = "Cuota"
            row[col_cuota] = odds
            players_data.append(row)
            
    if not players_data: return
    
    df = pd.DataFrame(players_data)
    
    # Ordenar
    if do_analysis and "Prob. %" in df.columns:
        df["_sort"] = pd.to_numeric(df["Prob. %"], errors='coerce').fillna(0)
        df = df.sort_values(by=["_sort", "Cuota"], ascending=[False, True])
    else:
        df = df.sort_values(by=["Cuota"])

    # Columnas finales
    cols = ["Equipo", "Jugador", val_col_name]
    if do_analysis and "Prob. %" in df.columns: cols.append("Prob. %")
    cols.append("Cuota")
    
    df = df[[c for c in cols if c in df.columns]]
    
    numeric_cols = ["Cuota"]
    if "Prob. %" in df.columns: numeric_cols.append("Prob. %")
    
    styler = _apply_table_styles(df, numeric_cols)
    
    col_config = {
        "Cuota": st.column_config.NumberColumn(format="%.2f"),
        "Prob. %": st.column_config.NumberColumn(format="%.1f%%")
    }
            
    st.dataframe(
        styler,
        hide_index=True,
        width='stretch',
        column_config=col_config,
        height=min((len(df) + 1) * 35 + 3, 500)
    )
    st.markdown("")


def _render_player_shots(markets: list, home_team: str, away_team: str, home_id=None, away_id=None, do_analysis: bool = False):
    """Renderiza mercados de disparos."""
    shots_on_target = []
    total_shots = []
    
    for m in markets:
        lbl = m.get("label", "").lower()
        if "a puerta" in lbl or "al arco" in lbl:
            shots_on_target.append(m)
        else:
            total_shots.append(m)
            
    if shots_on_target:
        _render_generic_player_table(shots_on_target, "Disparos a Puerta", 
                                   home_team, away_team, home_id, away_id,
                                   val_col_name="Línea", 
                                   line_format_div_1000=True,
                                   do_analysis=do_analysis,
                                   metric="shots_on_goal")
                                   
    if total_shots:
        if shots_on_target: st.markdown("---")
        _render_generic_player_table(total_shots, "Disparos (Totales)", 
                                   home_team, away_team, home_id, away_id,
                                   val_col_name="Línea", 
                                   line_format_div_1000=True,
                                   do_analysis=do_analysis,
                                   metric="shots")


def _render_player_cards_markets(markets: list, home_team: str, away_team: str, home_id=None, away_id=None, do_analysis: bool = False):
    """Renderiza tarjetas de jugadores."""
    _render_generic_player_table(markets, "Tarjetas", 
                               home_team, away_team, home_id, away_id,
                               val_col_name="Tipo", 
                               is_binary=True,
                               do_analysis=do_analysis,
                               metric="yellow_cards")


def _render_player_specials(markets: list, home_team: str, away_team: str, home_id=None, away_id=None, do_analysis: bool = False):
    """Renderiza especiales (asistencias, cabeza, etc)."""
    data_map = {}
    
    for m in markets:
        lbl = m.get("label", "").lower()
        m_label = m.get("label", "")
        
        tipo = None
        metric = None
        if "asistencia" in lbl: 
            tipo = "Asistencia"
            metric = "assists"
        elif "fuera del área" in lbl: tipo = "Fuera Área" 
        elif "cabeza" in lbl: tipo = "Cabeza"
        
        if not tipo: continue
        
        for out in m.get("outcomes", []):
            p_name = out.get("participant") or out.get("label")
            if not p_name: continue
            
            if p_name not in data_map:
                team = _infer_team(out, m_label, home_team, away_team, home_id, away_id)
                data_map[p_name] = {"Equipo": team, "Jugador": p_name}
            
            data_map[p_name][tipo] = out.get("odds")
            if do_analysis and metric and "Prob. %" not in data_map[p_name]:
                data_map[p_name]["Prob. %"] = _get_player_weighted_prob(p_name, metric)
            
    if not data_map: 
        st.info("No hay datos de especiales disponibles.")
        return
    
    st.markdown(get_section_title_html("Apuestas Especiales Jugador"), unsafe_allow_html=True)
    df = pd.DataFrame(list(data_map.values()))
    
    numerics = ["Asistencia", "Fuera Área", "Cabeza", "Prob. %"]
    valid_numerics = [c for c in numerics if c in df.columns]
    
    styler = _apply_table_styles(df, valid_numerics)
    st.dataframe(styler, hide_index=True, width='stretch', height=(len(df)+1)*35+3)


def _render_player_assists(markets: list, home_team: str, away_team: str, home_id=None, away_id=None, do_analysis: bool = False):
    _render_generic_player_table(markets, "Asistencias", home_team, away_team, home_id, away_id, 
                               is_binary=True, do_analysis=do_analysis, metric="assists")


def _render_player_goals(markets: list, home_team: str, away_team: str, home_id=None, away_id=None, do_analysis: bool = False):
    """Renderiza mercados de goles extra."""
    if not markets: return
    
    label_map = {"Yes": "Sí", "No": "No"}
    
    for m in markets:
        label = m.get("label", "Goles del Jugador")
        # Aquí usamos cards porque suelen ser pocos mercados o muy específicos
        _render_as_card(label, m.get("outcomes", []), label_map)


def _render_goalkeeper_saves(markets: list, home_team: str, away_team: str, home_id=None, away_id=None, do_analysis: bool = False):
    """Renderiza mercados de paradas."""
    _render_generic_player_table(markets, "Paradas del Portero", 
                               home_team, away_team, home_id, away_id,
                               val_col_name="Línea", 
                               do_analysis=do_analysis,
                               metric="saves")
