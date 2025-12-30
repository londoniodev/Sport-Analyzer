"""
Sport Selector - UI component to switch between sports.
"""
import streamlit as st
from app.core.registry import SportRegistry


def show_sport_selector() -> str:
    """
    Display a sport selector in the sidebar and return the selected sport key.
    """
    sports = SportRegistry.list_sports()
    
    if not sports:
        st.sidebar.warning("⚠️ No hay deportes registrados")
        return None
    
    # Create options dict {display_name: key}
    options = {f"{s.icon} {s.name}": s.key for s in sports}
    
    selected_display = st.sidebar.selectbox(
        "🏆 Seleccionar Deporte",
        list(options.keys()),
        index=0
    )
    
    return options.get(selected_display)


def get_sport_views(sport_key: str) -> dict:
    """
    Get the UI views for a selected sport.
    """
    sport = SportRegistry.get(sport_key)
    if not sport:
        return {}
    return sport.ui_views
