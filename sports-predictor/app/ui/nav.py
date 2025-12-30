"""
Mobile Navigation Component.
Renders a fixed bottom navigation bar for mobile devices.
"""
import streamlit as st
from app.core.registry import SportRegistry

def render_bottom_nav():
    """
    Render the mobile bottom navigation bar.
    This component uses CSS anchoring to fix itself to the bottom of the screen
    on mobile devices, while remaining hidden on desktop.
    """
    # Only render if a sport is selected
    if "selected_sport" not in st.session_state or not st.session_state.selected_sport:
        return

    # Get current sport config
    sport_config = SportRegistry.get(st.session_state.selected_sport)
    if not sport_config:
        return

    # Anchor ID for CSS targeting
    st.markdown('<span id="mobile-nav-anchor"></span>', unsafe_allow_html=True)
    
    # Navigation Items configuration
    # Map view keys to short labels and icons (Material Symbols)
    nav_items = [
        {"key": "dashboard", "label": "Inicio", "icon": "dashboard"},
        {"key": "prediction", "label": "Predic", "icon": "query_stats"},
        {"key": "analysis", "label": "Datos", "icon": "analytics"},
        {"key": "live_odds", "label": "Live", "icon": "bolt"},
    ]
    
    # Filter items that actually exist in the current sport config
    valid_items = [item for item in nav_items if item["key"] in sport_config.ui_views]
    
    if not valid_items:
        return

    # Render columns for buttons
    cols = st.columns(len(valid_items))
    
    # Current active view
    current_view = st.session_state.get("selected_view", "dashboard")
    
    for i, item in enumerate(valid_items):
        with cols[i]:
            # Determine if active
            is_active = (current_view == item["key"])
            
            # Button type
            btn_type = "primary" if is_active else "secondary"
            
            # We use a unique key for each button to avoid conflicts
            if st.button(
                item["label"], 
                key=f"mob_nav_{item['key']}", 
                type=btn_type, 
                use_container_width=True,
                icon=f":material/{item['icon']}:"
            ):
                if current_view != item["key"]:
                    st.session_state.selected_view = item["key"]
                    st.rerun()
