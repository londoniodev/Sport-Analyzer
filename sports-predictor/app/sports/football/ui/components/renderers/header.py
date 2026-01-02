import streamlit as st
from datetime import datetime

def _render_match_header(details: dict, event_basic: dict):
    """Renderiza el encabezado del partido con diseño mejorado."""
    home_team = details.get("home_team", event_basic.get("home_team", "Local"))
    away_team = details.get("away_team", event_basic.get("away_team", "Visitante"))
    state = details.get("state", "NOT_STARTED")
    score = details.get("score", {})
    
    state_display = "PRÓXIMO"
    score_display = "VS"
    time_display = ""
    
    if state == "STARTED":
        state_display = "EN VIVO"
        score_display = f"{score.get('home', 0)} - {score.get('away', 0)}"
    elif state == "FINISHED":
        state_display = "FINALIZADO"
        score_display = f"{score.get('home', 0)} - {score.get('away', 0)}"
    else:
        start_time = details.get("start_time", event_basic.get("start_time"))
        if start_time:
            try:
                dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                # Ajustar a hora local aproximada o dejar en UTC si no hay info de zona
                # Mostramos solo hora por simplicidad
                time_display = dt.strftime('%H:%M')
            except:
                pass
    
    # CSS personalizado para el header
    st.markdown(f"""
        <style>
            .match-header-container {{
                background-color: #0f172a;
                border-radius: 12px;
                padding: 24px;
                margin-bottom: 24px;
                display: flex;
                align-items: center;
                justify-content: space-between;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
                border: 1px solid #1e293b;
            }}
            .team-name {{
                font-size: 24px;
                font-weight: 700;
                color: #f8fafc;
                width: 35%;
                text-align: center;
            }}
            .match-info {{
                display: flex;
                flex-direction: column;
                align-items: center;
                width: 30%;
            }}
            .match-score {{
                font-size: 48px;
                font-weight: 800;
                color: #ffffff;
                line-height: 1.2;
            }}
            .match-time {{
                font-size: 32px;
                font-weight: 700;
                color: #ffffff;
            }}
            .match-status {{
                margin-top: 8px;
                padding: 4px 12px;
                border-radius: 99px;
                font-size: 12px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
            .status-live {{
                background-color: #22c55e;
                color: #052e16;
            }}
            .status-upcoming {{
                background-color: #334155;
                color: #94a3b8;
            }}
            .status-finished {{
                 background-color: #ef4444;
                color: #450a0a;
            }}
            .team-label {{
                font-size: 12px;
                text-transform: uppercase;
                letter-spacing: 1px;
                color: #64748b;
                margin-top: 4px;
                display: block;
            }}
            /* Ajuste mobile */
            @media (max-width: 640px) {{
                .match-header-container {{
                    flex-direction: column;
                    text-align: center;
                    gap: 16px;
                }}
                .team-name {{
                    width: 100%;
                }}
            }}
        </style>
    """, unsafe_allow_html=True)

    status_class = "status-upcoming"
    if state == "STARTED": status_class = "status-live"
    elif state == "FINISHED": status_class = "status-finished"
    
    center_content = ""
    if state in ["STARTED", "FINISHED"]:
        center_content = f'<div class="match-score">{score_display}</div>'
    else:
        if time_display:
            center_content = f'<div class="match-time">{time_display}</div>'
        else:
             center_content = f'<div class="match-score">VS</div>'

    html = f"""
<div class="match-header-container">
<div class="team-name">
{home_team}
<span class="team-label">Local</span>
</div>
<div class="match-info">
{center_content}
<div class="match-status {status_class}">{state_display}</div>
</div>
<div class="team-name">
{away_team}
<span class="team-label">Visitante</span>
</div>
</div>
"""
    
    st.markdown(html, unsafe_allow_html=True)
