import streamlit as st
import pandas as pd
from ..styles import _apply_table_styles
from .common import _render_as_card

def _infer_team(outcome: dict, market_label: str, home_team: str, away_team: str, home_id=None, away_id=None) -> str:
    """Intenta inferir el equipo del jugador basado en datos disponibles."""
    # 1. ID Match (Prioridad)
    epid = outcome.get("eventParticipantId")
    if epid:
        if epid == home_id: return home_team
        if epid == away_id: return away_team

    # 2. Directamente del outcome (si la API lo provee)
    # Kambi a veces usa 'competitorName' o 'team' en el outcome
    if "team" in outcome: return outcome["team"]
    if "competitorName" in outcome: return outcome["competitorName"]
    
    # 3. Contexto del Label del Mercado
    # Ej: "Goleador - Real Madrid"
    lbl_lower = market_label.lower()
    if home_team.lower() in lbl_lower: return home_team
    if away_team.lower() in lbl_lower: return away_team
    
    # 3. Contexto del Criterio (si existe en outcome)
    # A veces hay field 'criterion' -> 'label'
    
    return "-"

def _render_scorers_markets(markets: list, home_team: str, away_team: str, home_id=None, away_id=None):
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

    st.markdown(f"<p style='margin-bottom:4px;font-weight:bold;'>Goleadores</p>", unsafe_allow_html=True)

    # Helper para procesar
    def process_player(out, key_type):
        name = out.get("participant") or out.get("label")
        if not name: return
        
        if "ningún" in name.lower() or (name == "Sí" and key_type == "Marcará"):
             return

        if name not in players_data:
            # Inferir equipo solo la primera vez
            team = _infer_team(out, out.get("_market_label", ""), home_team, away_team, home_id, away_id)
            players_data[name] = {"Equipo": team, "Jugador": name, "Primer Gol": None, "Marcará": None}
        
        # Si ya existe pero no tiene equipo, intentar inferir de nuevo (quizas este outcome si tiene info)
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
    
    df["_sort_first"] = df["Primer Gol"].fillna(9999)
    df["_sort_any"] = df["Marcará"].fillna(9999)
    df = df.sort_values(by=["_sort_first", "_sort_any"])
    
    cols = ["Equipo", "Jugador", "Primer Gol", "Marcará"]
    final_df = df[list(set(cols) & set(df.columns))]
    # Reordenar forzoso
    final_df = final_df[cols] if set(cols).issubset(df.columns) else final_df
    
    numeric_cols = ["Primer Gol", "Marcará"]
    styler = _apply_table_styles(final_df, numeric_cols)
    
    column_config = {
        "Primer Gol": st.column_config.NumberColumn(format="%.2f"),
        "Marcará": st.column_config.NumberColumn(format="%.2f")
    }

    rows_count = len(final_df)
    dynamic_height = (rows_count + 1) * 35 + 3
    
    st.dataframe(
        styler, 
        hide_index=True, 
        use_container_width=True,
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
            st.markdown(f"<p style='margin-bottom:4px;font-weight:bold;'>Tarjetas de Jugadores</p>", unsafe_allow_html=True)
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
                use_container_width=True,
                column_config=column_config,
                height=dynamic_height
            )
            st.markdown("")

    if other_markets:
        if player_list_markets: st.markdown("---")
        for m in other_markets:
            _render_as_card(m.get("label"), m.get("outcomes", []), {})


def _render_generic_player_table(markets: list, title: str, 
                               home_team: str, away_team: str,
                               home_id=None, away_id=None,
                               val_col_name: str = "Total", 
                               is_binary: bool = False,
                               line_format_div_1000: bool = False):
    """Renderizador genérico para tablas de jugadores."""
    if not markets: return

    st.markdown(f"<p style='margin-bottom:4px;font-weight:bold;'>{title}</p>", unsafe_allow_html=True)
    
    players_data = []
    
    for m in markets:
        m_label = m.get("label", "")
        for out in m.get("outcomes", []):
            p_name = out.get("participant") or out.get("label")
            if not p_name: continue
            
            odds = out.get("odds")
            line = out.get("line")
            
            team = _infer_team(out, m_label, home_team, away_team, home_id, away_id)
            row = {"Equipo": team, "Jugador": p_name}
            
            if not is_binary:
                if line is not None:
                     try: 
                         val = float(line)
                         if line_format_div_1000: val /= 1000.0
                         
                         if val.is_integer(): val_str = str(int(val))
                         else: val_str = f"{val:.1f}"
                         
                         row[val_col_name] = f"Más de {val_str}"
                     except:
                         row[val_col_name] = str(line)
                else:
                    row[val_col_name] = "-"
            
            col_cuota = "Valor de la apuesta" if not is_binary else "Sí"
            row[col_cuota] = odds
            
            players_data.append(row)
            
    if not players_data: return
    
    df = pd.DataFrame(players_data)
    
    numeric_cols = ["Valor de la apuesta", "Sí"]
    valid_numerics = [c for c in numeric_cols if c in df.columns]
    
    # Reordenar columnas para que Equipo sea la primera
    cols = list(df.columns)
    if "Equipo" in cols:
        cols.insert(0, cols.pop(cols.index("Equipo")))
        if "Jugador" in cols:
             cols.insert(1, cols.pop(cols.index("Jugador")))
    df = df[cols]

    styler = _apply_table_styles(df, valid_numerics)
    
    col_config = {}
    for c in valid_numerics:
        col_config[c] = st.column_config.NumberColumn(format="%.2f")
        
    rows_count = len(df)
    dynamic_height = min((rows_count + 1) * 35 + 3, 600)
    
    st.dataframe(
        styler,
        hide_index=True,
        use_container_width=True,
        column_config=col_config,
        height=dynamic_height
    )
    st.markdown("")


def _render_player_shots(markets: list, home_team: str, away_team: str, home_id=None, away_id=None):
    _render_generic_player_table(markets, "Disparos a Puerta", 
                               home_team, away_team, home_id, away_id,
                               val_col_name="Cantidad", 
                               is_binary=False, 
                               line_format_div_1000=True)

def _render_player_specials(markets: list, home_team: str, away_team: str, home_id=None, away_id=None):
    data_map = {}
    
    for m in markets:
        lbl = m.get("label", "").lower()
        m_label = m.get("label", "")
        
        tipo = None
        if "asistencia" in lbl: tipo = "Asistencia"
        elif "fuera del área" in lbl or "penal" in lbl: tipo = "Fuera Área" 
        elif "cabeza" in lbl: tipo = "Cabeza"
        
        if not tipo: continue
        
        for out in m.get("outcomes", []):
            p_name = out.get("participant") or out.get("label")
            if not p_name: continue
            
            if p_name not in data_map:
                team = _infer_team(out, m_label, home_team, away_team, home_id, away_id)
                data_map[p_name] = {"Equipo": team, "Jugador": p_name}
            
            data_map[p_name][tipo] = out.get("odds")
            
    if not data_map: return
    
    st.markdown(f"<p style='margin-bottom:4px;font-weight:bold;'>Apuestas Especiales Jugador</p>", unsafe_allow_html=True)
    df = pd.DataFrame(list(data_map.values()))
    
    for c in ["Asistencia", "Fuera Área", "Cabeza"]:
        if c not in df.columns: df[c] = None
        
    final_cols = ["Equipo", "Jugador", "Asistencia", "Fuera Área", "Cabeza"]
    df = df[[c for c in final_cols if c in df.columns]]
    
    numerics = ["Asistencia", "Fuera Área", "Cabeza"]
    styler = _apply_table_styles(df, numerics)
    
    col_conf = {c: st.column_config.NumberColumn(format="%.2f") for c in numerics}
    
    st.dataframe(
        styler,
        hide_index=True,
        use_container_width=True,
        column_config=col_conf,
        height=(len(df)+1)*35+3
    )

def _render_player_assists(markets: list, home_team: str, away_team: str, home_id=None, away_id=None):
    _render_generic_player_table(markets, "Asistencias", home_team, away_team, home_id, away_id, is_binary=True)

def _render_player_goals(markets: list, home_team: str, away_team: str, home_id=None, away_id=None):
    _render_generic_player_table(markets, "Goles del Jugador (2+ / Hat-trick)", home_team, away_team, home_id, away_id, is_binary=True)

def _render_goalkeeper_saves(markets: list, home_team: str, away_team: str, home_id=None, away_id=None):
    _render_generic_player_table(markets, "Paradas del Portero", 
                               home_team, away_team, home_id, away_id,
                               val_col_name="Cantidad", 
                               is_binary=False, 
                               line_format_div_1000=True)
