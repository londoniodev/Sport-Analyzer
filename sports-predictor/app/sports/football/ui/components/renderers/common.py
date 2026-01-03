import streamlit as st
import pandas as pd
from ..styles import _apply_table_styles, get_card_html, get_section_title_html, render_styled_table
from ..market_logic import _sort_markets_by_order, _get_market_format

def _render_category_markets(markets: list, home_team: str, away_team: str, orden: list = None, analysis_data: dict = None):
    """Renderiza los mercados de una categoría."""
    
    label_map = {"1": home_team, "X": "Empate", "2": away_team, "Over": "Más de", "Under": "Menos de"}
    
    # 1. AGRUPAR MERCADOS POR LABEL
    grouped_markets = {}
    for market in markets:
        lbl = market.get("label", "Mercado")
        if lbl not in grouped_markets:
            grouped_markets[lbl] = []
        grouped_markets[lbl].extend(market.get("outcomes", []))
    
    # Reconstruir lista de mercados únicos consolidados
    consolidated_markets = []
    for lbl, outcomes in grouped_markets.items():
        consolidated_markets.append({"label": lbl, "outcomes": outcomes})

    # 2. ORDENAR
    if orden:
        final_markets = _sort_markets_by_order(consolidated_markets, orden)
    else:
        final_markets = consolidated_markets

    for market in final_markets:
        label = market.get("label", "Mercado")
        outcomes = market.get("outcomes", [])
        
        if not outcomes:
            continue
        
        # Determinar formato
        has_lines = any(out.get("line") for out in outcomes)
        
        if orden:
            formato = _get_market_format(label, orden)
            is_list = formato == "list" or has_lines
        else:
            is_list = has_lines or len(outcomes) > 4
        
        if is_list:
            _render_as_list(label, outcomes, label_map, analysis_data)
        else:
            _render_as_card(label, outcomes, label_map, analysis_data)


def _render_as_card(label: str, outcomes: list, label_map: dict, analysis_data: dict = None):
    """Renderiza mercado como cards horizontales con probabilidades opcionales."""
    st.markdown(get_section_title_html(label), unsafe_allow_html=True)
    
    unique_outcomes = {}
    for out in outcomes:
        key = (out.get("label"), out.get("line"))
        unique_outcomes[key] = out
    
    sorted_outcomes = list(unique_outcomes.values())
    
    # Obtener probabilidades según el tipo de mercado
    probs = {}
    label_lower = label.lower()
    if analysis_data:
        if "resultado final" in label_lower or label_lower == "1x2":
            data_1x2 = analysis_data.get("1x2", {})
            probs = {"1": data_1x2.get("home_win"), "X": data_1x2.get("draw"), "2": data_1x2.get("away_win")}
        elif "ambos equipos" in label_lower or "btts" in label_lower:
            data_btts = analysis_data.get("btts", {})
            probs = {"Sí": data_btts.get("yes"), "Yes": data_btts.get("yes"), "No": data_btts.get("no")}
        elif "doble oportunidad" in label_lower and "parte" not in label_lower:
            data_1x2 = analysis_data.get("1x2", {})
            h, d, a = data_1x2.get("home_win", 0), data_1x2.get("draw", 0), data_1x2.get("away_win", 0)
            probs = {"1X": h + d, "12": h + a, "X2": d + a}
        elif "sin empate" in label_lower or "draw no bet" in label_lower:
            # Draw No Bet (determinar si es 1ª parte o tiempo completo)
            if "parte" in label_lower or "mitad" in label_lower:
                data_1x2 = analysis_data.get("halftime", {}).get("1x2", {})
                h, a = data_1x2.get("home", 0), data_1x2.get("away", 0)
            else:
                data_1x2 = analysis_data.get("1x2", {})
                h, a = data_1x2.get("home_win", 0), data_1x2.get("away_win", 0)
            total = h + a
            if total > 0:
                probs = {"1": h / total, "2": a / total}
        elif "descanso" in label_lower and "/" not in label_lower:
            # 1X2 Medio Tiempo (sin HT/FT)
            ht_data = analysis_data.get("halftime", {}).get("1x2", {})
            probs = {"1": ht_data.get("home"), "X": ht_data.get("draw"), "2": ht_data.get("away")}
        elif "gol en ambas mitades" in label_lower:
            # Probabilidad de gol en ambas mitades usando datos de halftime
            ht_ou = analysis_data.get("halftime", {}).get("over_under", {})
            if "0.5" in ht_ou:
                # Aproximación: P(gol 1ª) * P(gol 2ª)
                prob_goal_ht = ht_ou.get("0.5", {}).get("over", 0.5)
                # Asumimos similar para 2ª mitad
                prob_both = prob_goal_ht * prob_goal_ht * 1.2  # Factor correlación
                probs = {"Sí": min(prob_both, 0.95), "Yes": min(prob_both, 0.95), "No": max(1 - prob_both, 0.05)}
        elif ("mayor" in label_lower or "más" in label_lower) and ("esquina" in label_lower or "corner" in label_lower):
            # Mayor número de corners: 1X2
            corners_data = analysis_data.get("corners") if analysis_data else None
            if corners_data:
                corners_winner = corners_data.get("winner", {})
                if corners_winner:
                    probs = {"1": corners_winner.get("home"), "X": corners_winner.get("draw"), "2": corners_winner.get("away")}
        elif ("mayor" in label_lower or "más" in label_lower) and "tarjeta" in label_lower:
            # Mayor número de tarjetas: 1X2
            cards_data = analysis_data.get("cards") if analysis_data else None
            if cards_data:
                cards_winner = cards_data.get("winner", {})
                if cards_winner:
                    probs = {"1": cards_winner.get("home"), "X": cards_winner.get("draw"), "2": cards_winner.get("away")}
    
    n_cols = min(len(sorted_outcomes), 4)
    if n_cols == 0: n_cols = 1
    cols = st.columns(n_cols)
    
    for i, outcome in enumerate(sorted_outcomes):
        with cols[i % n_cols]:
            odds = outcome.get("odds", 0)
            out_label = outcome.get("label", "")
            line = outcome.get("line")
            
            display_label = label_map.get(out_label, out_label)
            if line:
                display_label = f"{display_label} ({line})"
            
            # Obtener probabilidad si existe
            prob = probs.get(out_label)
            
            # Negrita para equipos/empate en resultado final
            if out_label in ["1", "X", "2"] and "resultado final" in label.lower():
                display_label = f"<b>{display_label}</b>"
            elif out_label in label_map.values(): 
                 display_label = f"<b>{display_label}</b>"

            st.markdown(get_card_html(display_label, odds, prob), unsafe_allow_html=True)
    
    st.markdown("")


def _render_as_list(label: str, outcomes: list, label_map: dict, analysis_data: dict = None):
    """Renderiza mercado como tabla con todas las líneas."""
    has_lines = any(out.get("line") for out in outcomes)
    
    if has_lines:
        st.markdown(get_section_title_html(label), unsafe_allow_html=True)
        
        lines_data = {}
        processed_keys = set()
        
        # Datos de Poisson si están disponibles
        poisson_ou = analysis_data.get("over_under", {}) if analysis_data else {}
        poisson_handicaps = analysis_data.get("handicaps", {}) if analysis_data else {}
        
        # Detectar tipo de mercado
        label_lower = label.lower()
        # Total de goles del PARTIDO (no de un equipo, no de una mitad específica de equipo)
        is_specific_team = " de " in label_lower and ("mitad" in label_lower or "parte" in label_lower)
        is_total_goals = ("total de goles" in label_lower 
                          and "equipo" not in label_lower 
                          and not is_specific_team)
        is_handicap = "hándicap" in label_lower or "handicap" in label_lower or "asiático" in label_lower
        # Corners y tarjetas (solo mercados totales del partido)
        is_total_corners = ("esquina" in label_lower or "corner" in label_lower) and "total" in label_lower and not is_specific_team
        is_total_cards = ("tarjeta" in label_lower) and "total" in label_lower and not is_specific_team
        
        for out in outcomes:
            raw_line = out.get("line")
            odds = out.get("odds", 0)
            out_label = out.get("label", "")
            
            unique_key = (raw_line, out_label, odds)
            if unique_key in processed_keys:
                continue
            processed_keys.add(unique_key)
            
            display_line = raw_line
            line_sort_key = 0
            
            if raw_line is not None:
                try:
                    val = float(raw_line)
                    # Normalización de líneas tipo "2500" -> "2.5"
                    if abs(val) >= 50: 
                        val = val / 1000.0
                    
                    if val.is_integer():
                        base_str = str(int(val))
                    else:
                        base_str = str(val)
                    
                    is_handicap_mkt = "hándicap" in label.lower() or "handicap" in label.lower() or "asiático" in label.lower()
                    if is_handicap_mkt and val > 0:
                        display_line = f"+{base_str}"
                    else:
                        display_line = base_str
                    
                    line_sort_key = val
                except:
                    display_line = str(raw_line)
                    line_sort_key = 0
            else:
                display_line = ""

            col_name_first = "Valor"
            if "3-way" in label.lower():
                col_name_first = "Comienza en"

            if line_sort_key not in lines_data:
                lines_data[line_sort_key] = {col_name_first: display_line}
            
            display_label = label_map.get(out_label, out_label)
            lines_data[line_sort_key][display_label] = odds
            
            # --- INYECCIÓN DE PROBABILIDAD (POISSON) ---
            # Over/Under
            if is_total_goals and str(line_sort_key) in poisson_ou:
                p_data = poisson_ou[str(line_sort_key)]
                prob_val = p_data["over"] if out_label == "Over" else p_data["under"]
                prob_col_name = f"Prob. % ({display_label})"
                lines_data[line_sort_key][prob_col_name] = round(prob_val * 100, 1)
            
            # Handicap Asiático
            if is_handicap and str(line_sort_key) in poisson_handicaps:
                h_data = poisson_handicaps[str(line_sort_key)]
                # Mapear labels: "1" = home win, "2" = away win
                if out_label == "1":
                    prob_val = h_data.get("win", 0)
                elif out_label == "2":
                    prob_val = h_data.get("loss", 0)
                else:
                    prob_val = h_data.get("push", 0)
                prob_col_name = f"Prob. % ({display_label})"
                lines_data[line_sort_key][prob_col_name] = round(prob_val * 100, 1)
            
            # Corners (Total de Esquinas)
            corners_data = analysis_data.get("corners", {}) if analysis_data else {}
            if is_total_corners and corners_data:
                corners_ou = corners_data.get("over_under", {})
                if str(line_sort_key) in corners_ou:
                    c_data = corners_ou[str(line_sort_key)]
                    prob_val = c_data["over"] if out_label == "Over" else c_data["under"]
                    prob_col_name = f"Prob. % ({display_label})"
                    lines_data[line_sort_key][prob_col_name] = round(prob_val * 100, 1)
            
            # Tarjetas (Total de Tarjetas)
            cards_data = analysis_data.get("cards", {}) if analysis_data else {}
            if is_total_cards and cards_data:
                cards_ou = cards_data.get("over_under", {})
                if str(line_sort_key) in cards_ou:
                    t_data = cards_ou[str(line_sort_key)]
                    prob_val = t_data["over"] if out_label == "Over" else t_data["under"]
                    prob_col_name = f"Prob. % ({display_label})"
                    lines_data[line_sort_key][prob_col_name] = round(prob_val * 100, 1)

        rows = [lines_data[k] for k in sorted(lines_data.keys())]
        
        if rows:
            df = pd.DataFrame(rows)
            
            first_col = [c for c in df.columns if c in ["Valor", "Comienza en"]][0]
            
            # Ordenar columnas inteligentemente
            priority_cols = ["Más de", "Prob. % (Más de)", "Menos de", "Prob. % (Menos de)", "Si", "No", "Empate"]
            sorted_cols = [first_col]
            remaining = [c for c in df.columns if c != first_col]
            
            for p in priority_cols:
                if p in remaining:
                    sorted_cols.append(p)
                    remaining.remove(p)
            sorted_cols.extend(remaining)
            
            df = df[sorted_cols]
            
            column_config = {}
            numeric_cols_for_style = []
            
            for col in sorted_cols:
                if col != first_col:
                    numeric_cols_for_style.append(col)
                    if "Prob. %" in col:
                        column_config[col] = st.column_config.NumberColumn(
                            label=col,
                            format="%.1f%%"
                        )
                    else:
                        column_config[col] = st.column_config.NumberColumn(
                            label=col,
                            format="%.2f"
                        )
            
            styler = _apply_table_styles(df, numeric_cols_for_style)

            st.dataframe(
                styler, 
                hide_index=True, 
                width='stretch',
                column_config=column_config
            )
    else:
        # Sin líneas (ej. Resultado Correcto)
        unique_outcomes = {}
        for out in outcomes:
            key = (out.get("label"), out.get("odds"))
            unique_outcomes[key] = out
            
        final_outcomes = list(unique_outcomes.values())
        
        label_lower = label.lower()
        is_result_correct = "resultado correct" in label_lower or "marcador" in label_lower
        is_half_time_full_time = "descanso" in label_lower or "medio tiempo" in label_lower
        
        if is_result_correct or is_half_time_full_time:
             st.markdown(get_section_title_html(label), unsafe_allow_html=True)
             
             # Obtener matriz de probabilidades Poisson si está disponible
             score_matrix = analysis_data.get("score_matrix", {}) if analysis_data else {}
             
             if is_result_correct:
                 def get_score_sort_key(outcome):
                     lbl = outcome.get("label", "")
                     try:
                         if "-" in lbl:
                             parts = lbl.split("-")
                             p1 = int(''.join(filter(str.isdigit, parts[0])))
                             p2 = int(''.join(filter(str.isdigit, parts[1])))
                             return (p1, p2)
                         return (999, 999)
                     except:
                         return (999, 999)

                 final_outcomes.sort(key=get_score_sort_key)

             data = []
             col_name_res = "Resultado"
             if is_half_time_full_time:
                 col_name_res = "Descanso / Final"
             
             for out in final_outcomes:
                 lbl = out.get("label", "")
                 row = {
                     col_name_res: lbl,
                     "Cuota": out.get("odds")
                 }
                 
                 # Agregar probabilidad Poisson si está disponible
                 if score_matrix and is_result_correct and "-" in lbl:
                     try:
                         parts = lbl.split("-")
                         home_goals = int(''.join(filter(str.isdigit, parts[0])))
                         away_goals = int(''.join(filter(str.isdigit, parts[1])))
                         score_key = f"{home_goals}-{away_goals}"
                         if score_key in score_matrix:
                             row["Prob. %"] = round(score_matrix[score_key] * 100, 1)
                     except:
                         pass
                 
                 # HT/FT: calcular probabilidad combinando medio tiempo y final
                 if is_half_time_full_time and analysis_data and "/" in lbl:
                     try:
                         ht_data = analysis_data.get("halftime", {}).get("1x2", {})
                         ft_data = analysis_data.get("1x2", {})
                         
                         parts = lbl.split("/")
                         ht_result = parts[0].strip()
                         ft_result = parts[1].strip()
                         
                         # Mapear 1, X, 2 a probabilidades
                         ht_map = {"1": ht_data.get("home", 0), "X": ht_data.get("draw", 0), "2": ht_data.get("away", 0)}
                         ft_map = {"1": ft_data.get("home_win", 0), "X": ft_data.get("draw", 0), "2": ft_data.get("away_win", 0)}
                         
                         ht_prob = ht_map.get(ht_result, 0)
                         ft_prob = ft_map.get(ft_result, 0)
                         
                         # Probabilidad aproximada (independencia asumida, ajuste conservador)
                         combined_prob = ht_prob * ft_prob * 1.5  # Factor de correlación
                         if combined_prob > 0:
                             row["Prob. %"] = round(min(combined_prob * 100, 99.9), 1)
                     except:
                         pass
                 
                 data.append(row)
             
             df_rc = pd.DataFrame(data)
             
             # Columnas numéricas
             numeric_cols = ["Cuota"]
             col_config = {"Cuota": st.column_config.NumberColumn(format="%.2f")}
             
             if "Prob. %" in df_rc.columns:
                 numeric_cols.append("Prob. %")
                 col_config["Prob. %"] = st.column_config.NumberColumn(format="%.1f%%")
             
             styler_rc = _apply_table_styles(df_rc, numeric_cols)

             st.dataframe(
                 styler_rc, 
                 hide_index=True, 
                 width='stretch',
                 column_config=col_config
             )
        else:
             _render_as_card(label, final_outcomes, label_map)
    
    st.markdown("")
