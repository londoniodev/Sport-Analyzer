import streamlit as st
import pandas as pd
from ..styles import _apply_table_styles
from .common import _render_as_card

def _render_scorers_markets(markets: list):
    """Renderiza tabla consolidada de goleadores (Primer Gol + Marcará)."""
    players_data = {}
    
    first_scorer_mkt = []
    anytime_scorer_mkt = []
    
    for m in markets:
        lbl = m.get("label", "").lower()
        if "primer" in lbl and "goleador" in lbl:
            first_scorer_mkt.extend(m.get("outcomes", []))
        elif "marca" in lbl or "marcará" in lbl or "cualquier momento" in lbl:
            anytime_scorer_mkt.extend(m.get("outcomes", []))
            
    if not first_scorer_mkt and not anytime_scorer_mkt:
        st.info("No hay datos de goleadores disponibles.")
        return

    st.markdown(f"<p style='margin-bottom:4px;font-weight:bold;'>Goleadores</p>", unsafe_allow_html=True)

    for out in first_scorer_mkt:
        name = out.get("participant") or out.get("label")
        if not name: continue
        
        if name not in players_data:
            players_data[name] = {"Jugador": name, "Primer Gol": None, "Marcará": None}
        players_data[name]["Primer Gol"] = out.get("odds")

    for out in anytime_scorer_mkt:
        name = out.get("participant") or out.get("label")
        if not name: continue
        
        if "ningún" in name.lower() or name == "Sí":
             continue

        if name not in players_data:
            players_data[name] = {"Jugador": name, "Primer Gol": None, "Marcará": None}
        players_data[name]["Marcará"] = out.get("odds")
    
    data_list = list(players_data.values())
    if not data_list: return
        
    df = pd.DataFrame(data_list)
    
    df["_sort_first"] = df["Primer Gol"].fillna(9999)
    df["_sort_any"] = df["Marcará"].fillna(9999)
    df = df.sort_values(by=["_sort_first", "_sort_any"])
    
    cols = ["Jugador", "Primer Gol", "Marcará"]
    final_df = df[cols]
    
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


def _render_player_cards_markets(markets: list):
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
                    players_data[p_name] = {"Jugador": p_name}
                
                players_data[p_name][col_name] = out.get("odds")
        
        data_list = list(players_data.values())
        if data_list:
            st.markdown(f"<p style='margin-bottom:4px;font-weight:bold;'>Tarjetas de Jugadores</p>", unsafe_allow_html=True)
            df = pd.DataFrame(data_list)
            
            if "Tarjeta" not in df.columns: df["Tarjeta"] = None
            if "Roja" not in df.columns: df["Roja"] = None
            
            cols_to_show = ["Jugador"]
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
                               val_col_name: str = "Total", 
                               is_binary: bool = False,
                               line_format_div_1000: bool = False):
    """Renderizador genérico para tablas de jugadores."""
    if not markets: return

    st.markdown(f"<p style='margin-bottom:4px;font-weight:bold;'>{title}</p>", unsafe_allow_html=True)
    
    players_data = []
    
    for m in markets:
        for out in m.get("outcomes", []):
            p_name = out.get("participant") or out.get("label")
            if not p_name: continue
            
            odds = out.get("odds")
            line = out.get("line")
            
            row = {"Equipo": "-", "Jugador": p_name}
            
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


def _render_player_shots(markets: list):
    _render_generic_player_table(markets, "Disparos a Puerta", 
                               val_col_name="Cantidad", 
                               is_binary=False, 
                               line_format_div_1000=True)

def _render_player_specials(markets: list):
    data_map = {}
    
    for m in markets:
        lbl = m.get("label", "").lower()
        
        tipo = None
        if "asistencia" in lbl: tipo = "Asistencia"
        elif "fuera del área" in lbl or "penal" in lbl: tipo = "Fuera Área" 
        elif "cabeza" in lbl: tipo = "Cabeza"
        
        if not tipo: continue
        
        for out in m.get("outcomes", []):
            p_name = out.get("participant") or out.get("label")
            if not p_name: continue
            
            if p_name not in data_map:
                data_map[p_name] = {"Jugador": p_name}
            
            data_map[p_name][tipo] = out.get("odds")
            
    if not data_map: return
    
    st.markdown(f"<p style='margin-bottom:4px;font-weight:bold;'>Apuestas Especiales Jugador</p>", unsafe_allow_html=True)
    df = pd.DataFrame(list(data_map.values()))
    
    for c in ["Asistencia", "Fuera Área", "Cabeza"]:
        if c not in df.columns: df[c] = None
        
    final_cols = ["Jugador", "Asistencia", "Fuera Área", "Cabeza"]
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

def _render_player_assists(markets: list):
    _render_generic_player_table(markets, "Asistencias", is_binary=True)

def _render_player_goals(markets: list):
    _render_generic_player_table(markets, "Goles del Jugador (2+ / Hat-trick)", is_binary=True)

def _render_goalkeeper_saves(markets: list):
    _render_generic_player_table(markets, "Paradas del Portero", 
                               val_col_name="Cantidad", 
                               is_binary=False, 
                               line_format_div_1000=True)
