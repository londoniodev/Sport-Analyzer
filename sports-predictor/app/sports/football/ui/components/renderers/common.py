import streamlit as st
import pandas as pd
from ..styles import _apply_table_styles, get_card_html
from ..market_logic import _sort_markets_by_order, _get_market_format

def _render_category_markets(markets: list, home_team: str, away_team: str, orden: list = None):
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
            _render_as_list(label, outcomes, label_map)
        else:
            _render_as_card(label, outcomes, label_map)


def _render_as_card(label: str, outcomes: list, label_map: dict):
    """Renderiza mercado como cards horizontales."""
    st.markdown(f"<p style='margin-bottom:4px;font-weight:bold;'>{label}</p>", unsafe_allow_html=True)
    
    unique_outcomes = {}
    for out in outcomes:
        key = (out.get("label"), out.get("line"))
        unique_outcomes[key] = out
    
    sorted_outcomes = list(unique_outcomes.values())
    
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
            
            # Negrita para equipos/empate en resultado final
            if out_label in ["1", "X", "2"] and "resultado final" in label.lower():
                display_label = f"<b>{display_label}</b>"
            elif out_label in label_map.values(): 
                 display_label = f"<b>{display_label}</b>"

            st.markdown(get_card_html(display_label, odds), unsafe_allow_html=True)
    
    st.markdown("")


def _render_as_list(label: str, outcomes: list, label_map: dict):
    """Renderiza mercado como tabla con todas las líneas."""
    has_lines = any(out.get("line") for out in outcomes)
    
    if has_lines:
        st.markdown(f"<p style='margin-bottom:4px;font-weight:bold;'>{label}</p>", unsafe_allow_html=True)
        
        lines_data = {}
        processed_keys = set()
        
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
        
        rows = [lines_data[k] for k in sorted(lines_data.keys())]
        
        if rows:
            df = pd.DataFrame(rows)
            
            first_col = [c for c in df.columns if c in ["Valor", "Comienza en"]][0]
            cols = [first_col] + [c for c in df.columns if c != first_col]
            
            priority_cols = ["Más de", "Menos de", "Si", "No", "Empate"]
            sorted_cols = [first_col]
            remaining = [c for c in cols if c != first_col]
            
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
                    column_config[col] = st.column_config.NumberColumn(
                        label=col,
                        format="%.2f"
                    )
            
            styler = _apply_table_styles(df, numeric_cols_for_style)

            st.dataframe(
                styler, 
                hide_index=True, 
                use_container_width=True,
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
             st.markdown(f"<p style='margin-bottom:4px;font-weight:bold;'>{label}</p>", unsafe_allow_html=True)
             
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
                 data.append({
                     col_name_res: out.get("label"),
                     "Cuota": out.get("odds")
                 })
             
             df_rc = pd.DataFrame(data)
             styler_rc = _apply_table_styles(df_rc, ["Cuota"])

             st.dataframe(
                 styler_rc, 
                 hide_index=True, 
                 use_container_width=True,
                 column_config={
                     "Cuota": st.column_config.NumberColumn(format="%.2f")
                 }
             )
        else:
             _render_as_card(label, final_outcomes, label_map)
    
    st.markdown("")
