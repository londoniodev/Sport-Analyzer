"""
Sports Predictor - Multi-Sport Betting Analysis Application
Modern UI with Dark/Light Theme Toggle
"""
import os
import sys
from pathlib import Path

# Add project root to sys.path to allow running as script
# This resolves 'ModuleNotFoundError: No module named 'app''
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

import streamlit as st
from app.core.database import init_db
from app.core.registry import SportRegistry
from app.ui.theme import get_theme_css, render_icon, render_feature_card
import app.sports.football # Trigger registration


def init_session_state():
    """Initialize session state variables."""
    if "dark_mode" not in st.session_state:
        st.session_state.dark_mode = True
    if "selected_sport" not in st.session_state:
        st.session_state.selected_sport = None


def main():
    # Page config
    st.set_page_config(
        page_title="Sports Predictor",
        page_icon="⚽",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize
    init_session_state()
    
    # Apply theme CSS
    st.markdown(get_theme_css(st.session_state.dark_mode), unsafe_allow_html=True)
    
    # Initialize database
    try:
        init_db()
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return
    
    # ═══════════════════════════════════════════════════════
    # SIDEBAR
    # ═══════════════════════════════════════════════════════
    with st.sidebar:

        # Logo and title
        st.markdown(f"""
        <div style="text-align: center; padding: 10px 0 20px 0;">
            <div style="font-size: 40px; color: var(--accent); margin-bottom: 5px;">
                {render_icon("analytics", "large")}
            </div>
            <h1 style="font-size: 1.4rem; margin: 0; font-weight: 700;">Sports Predictor</h1>
            <p style="opacity: 0.7; font-size: 0.8rem; color: var(--text-secondary); margin: 0;">AI Analysis System</p>
        </div>
        <div style='margin: 0 0 20px 0; border-top: 1px solid var(--border);'></div>
        """, unsafe_allow_html=True)
        
        # 1. Sport Selector (Top)
        sports = SportRegistry.list_sports()
        selected_view = None
        sport_config = None
        
        if sports:
            sport_options = {f"{s.name}": s.key for s in sports}
            st.caption("DEPORTE")
            selected_display = st.selectbox(
                "Seleccionar Deporte",
                list(sport_options.keys()),
                label_visibility="collapsed"
            )
            selected_sport = sport_options.get(selected_display)
            st.session_state.selected_sport = selected_sport
            
            # 2. Navigation (Middle)
            sport_config = SportRegistry.get(selected_sport)
            if sport_config and sport_config.ui_views:
                st.markdown("<div style='margin: 20px 0;'></div>", unsafe_allow_html=True) # Small gap
                st.caption("NAVEGACIÓN")
                
                view_labels = {
                    "dashboard": "Panel de Control",
                    "prediction": "Predicciones",
                    "analysis": "Análisis",
                    "live_odds": "Eventos Rushbet",
                }
                
                # Default view initialization
                if "selected_view" not in st.session_state:
                     st.session_state.selected_view = list(sport_config.ui_views.keys())[0]
                
                # ensure selected_view variable is set for main content
                selected_view = st.session_state.selected_view

                # Render buttons
                for view_key in sport_config.ui_views.keys():
                    label = view_labels.get(view_key, view_key.title())
                    
                    if view_key == st.session_state.selected_view:
                        if st.button(label, use_container_width=True, key=f"nav_{view_key}", type="primary"):
                             pass 
                    else:
                        if st.button(label, use_container_width=True, key=f"nav_{view_key}"):
                            st.session_state.selected_view = view_key
                            st.rerun()
        else:
            st.warning("Sin deportes disponibles")

        # Spacer
        st.markdown("<div style='flex-grow: 1;'></div>", unsafe_allow_html=True)
        
        # 3. Theme Toggle (Bottom)
        st.markdown("<div style='margin: 30px 0 10px 0; border-top: 1px solid var(--border);'></div>", unsafe_allow_html=True)
        
        # Compact theme selector layout
        col_theme, col_ver = st.columns([2, 1])
        with col_theme:
            st.caption("APARIENCIA")
            theme_options = ["Oscuro", "Claro"]
            default_idx = 0 if st.session_state.dark_mode else 1
            
            selected_theme = st.radio(
                "Tema",
                options=theme_options,
                index=default_idx,
                horizontal=True,
                label_visibility="collapsed"
            )
            
            # Detect change
            is_dark_selected = selected_theme == "Oscuro"
            if is_dark_selected != st.session_state.dark_mode:
                st.session_state.dark_mode = is_dark_selected
                st.rerun()
        
        with col_ver:
             st.markdown(f"""
                <div style="font-size: 0.7rem; color: var(--text-secondary); text-align: right; padding-top: 25px;">
                    v1.2.0
                </div>
            """, unsafe_allow_html=True)
    
    # ═══════════════════════════════════════════════════════
    # MAIN CONTENT
    # ═══════════════════════════════════════════════════════
    if sport_config and selected_view:
        view_function = sport_config.ui_views.get(selected_view)
        if view_function:
            view_function()
        else:
            st.error("Vista no encontrada")
    else:
        # Welcome screen
        st.markdown(f"""
        <div style="text-align: center; padding: 60px 20px;">
            <div style="color: var(--accent); margin-bottom: 20px;">
                {render_icon("monitoring", "large")}
            </div>
            <h1 style="font-size: 3rem; margin-bottom: 16px;">Bienvenido</h1>
            <p style="font-size: 1.2rem; color: var(--text-secondary); max-width: 600px; margin: 0 auto;">
                Sistema de predicción deportiva de alto rendimiento.
                Selecciona un deporte para comenzar.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Feature cards
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(render_feature_card(
                "functions", "Modelos Poisson", "Distribución estadística avanzada para cálculo de goles."
            ), unsafe_allow_html=True)
        
        with col2:
            st.markdown(render_feature_card(
                "leaderboard", "Rating ELO", "Algoritmo de clasificación de fuerza relativa de equipos."
            ), unsafe_allow_html=True)
        
        with col3:
            st.markdown(render_feature_card(
                "trending_up", "Value Bets", "Detección automática de oportunidades de mercado."
            ), unsafe_allow_html=True)


if __name__ == "__main__":
    main()
