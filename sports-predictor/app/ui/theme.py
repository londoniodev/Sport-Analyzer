"""
UI Theme and Styling Configuration.
Custom CSS for dark/light mode with modern aesthetics and Material Symbols.
"""

# Material Symbols Font (Outlined)
ICON_FONT = """
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" />
"""

LIGHT_THEME = f"""
{ICON_FONT}
<style>
    /* Light Theme Variables */
    :root {{
        --bg-primary: #ffffff;
        --bg-secondary: #f3f4f6;
        --bg-card: #ffffff;
        --text-primary: #111827;  /* Dark gray almost black */
        --text-secondary: #4b5563; /* Medium gray */
        --accent: #2563eb;
        --accent-hover: #1d4ed8;
        --success: #059669;
        --warning: #d97706;
        --danger: #dc2626;
        --border: #e5e7eb;
        --shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
        --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
    }}
    
    /* Global Reset */
    .stApp {{
        background-color: var(--bg-secondary) !important;
        color: var(--text-primary) !important;
    }}
    
    /* Headers matching text primary */
    h1, h2, h3, h4, h5, h6, .stMarkdown, p {{
        color: var(--text-primary) !important;
    }}
    
    /* Cards */
    .prediction-card {{
        background: var(--bg-card);
        border-radius: 12px;
        padding: 24px;
        box-shadow: var(--shadow);
        border: 1px solid var(--border);
        margin-bottom: 20px;
        transition: transform 0.2s, box-shadow 0.2s;
    }}
    
    .prediction-card:hover {{
        box-shadow: var(--shadow-lg);
        transform: translateY(-2px);
    }}
    
    /* Metric Cards - Modern & Clean */
    .metric-box {{
        background: white;
        color: var(--text-primary);
        padding: 16px;
        border-radius: 10px;
        border: 1px solid var(--border);
        box-shadow: var(--shadow);
        text-align: center;
        min-width: 130px;
    }}
    
    .metric-box-accent {{ border-left: 4px solid var(--accent); }}
    .metric-box-success {{ border-left: 4px solid var(--success); }}
    .metric-box-warning {{ border-left: 4px solid var(--warning); }}
    .metric-box-danger {{ border-left: 4px solid var(--danger); }}
    
    .metric-value {{
        font-size: 1.8rem;
        font-weight: 700;
        margin-bottom: 4px;
        color: var(--text-primary);
    }}
    
    .metric-label {{
        font-size: 0.85rem;
        color: var(--text-secondary);
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    
    /* Probability Bars */
    .prob-bar-container {{
        background: #e5e7eb;
        border-radius: 6px;
        overflow: hidden;
        height: 36px;
        display: flex;
        margin: 8px 0;
    }}
    
    .prob-bar {{
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: 600;
        font-size: 0.85rem;
    }}
    
    .prob-home {{ background: var(--accent); }}
    .prob-draw {{ background: #9ca3af; }}
    .prob-away {{ background: var(--danger); }}
    
    /* Tables */
    table {{
        color: var(--text-primary) !important;
        background: var(--bg-card) !important;
    }}
    
    thead tr th {{
        background: #f9fafb !important;
        color: var(--text-primary) !important;
        border-bottom: 2px solid var(--border) !important;
    }}
    
    tbody tr td {{
        border-bottom: 1px solid var(--border) !important;
    }}
    
    /* Sidebar */
    section[data-testid="stSidebar"] {{
        background: white !important;
        border-right: 1px solid var(--border);
    }}
    
    section[data-testid="stSidebar"] .stMarkdown {{
        color: var(--text-primary) !important;
    }}
    
    /* Inputs */
    .stTextInput input, .stSelectbox select, .stNumberInput input {{
        background: white !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border) !important;
    }}
    
    /* Material Icons Helper */
    .icon {{
        font-family: 'Material Symbols Outlined';
        font-weight: normal;
        font-style: normal;
        font-size: 24px;
        line-height: 1;
        letter-spacing: normal;
        text-transform: none;
        display: inline-block;
        white-space: nowrap;
        word-wrap: normal;
        direction: ltr;
        vertical-align: middle;
        margin-right: 8px;
    }}
    
    .icon-small {{ font-size: 18px; }}
    .icon-large {{ font-size: 32px; }}
</style>
"""

DARK_THEME = f"""
{ICON_FONT}
<style>
    /* Dark Theme Variables */
    :root {{
        --bg-primary: #0f172a;
        --bg-secondary: #1e293b;
        --bg-card: #1e293b;
        --text-primary: #f8fafc;
        --text-secondary: #94a3b8;
        --accent: #3b82f6;
        --accent-hover: #60a5fa;
        --success: #10b981;
        --warning: #f59e0b;
        --danger: #ef4444;
        --border: #334155;
        --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        --shadow-lg: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
    }}
    
    /* Base Styles */
    .stApp {{
        background-color: var(--bg-primary) !important;
        color: var(--text-primary) !important;
    }}
    
    .stApp > header {{
        background: transparent !important;
    }}
    
    /* Typography */
    h1, h2, h3, h4, h5, h6, .stMarkdown, p {{
        color: var(--text-primary) !important;
    }}
    
    /* Cards */
    .prediction-card {{
        background: var(--bg-card);
        border-radius: 12px;
        padding: 24px;
        box-shadow: var(--shadow);
        border: 1px solid var(--border);
        margin-bottom: 20px;
        transition: transform 0.2s;
    }}
    
    .prediction-card:hover {{
        box-shadow: var(--shadow-lg);
        border-color: var(--accent);
    }}
    
    /* Metric Cards - Modern Dark */
    .metric-box {{
        background: #0f172a;
        color: var(--text-primary);
        padding: 16px;
        border-radius: 10px;
        border: 1px solid var(--border);
        box-shadow: var(--shadow);
        text-align: center;
        min-width: 130px;
    }}
    
    .metric-box-accent {{ border-left: 4px solid var(--accent); background: rgba(59, 130, 246, 0.1); }}
    .metric-box-success {{ border-left: 4px solid var(--success); background: rgba(16, 185, 129, 0.1); }}
    .metric-box-warning {{ border-left: 4px solid var(--warning); background: rgba(245, 158, 11, 0.1); }}
    .metric-box-danger {{ border-left: 4px solid var(--danger); background: rgba(239, 68, 68, 0.1); }}
    
    .metric-value {{
        font-size: 1.8rem;
        font-weight: 700;
        margin-bottom: 4px;
        color: var(--text-primary);
    }}
    
    .metric-label {{
        font-size: 0.85rem;
        color: var(--text-secondary);
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    
    /* Probability Bars */
    .prob-bar-container {{
        background: #374151;
        border-radius: 6px;
        overflow: hidden;
        height: 36px;
        display: flex;
        margin: 8px 0;
    }}
    
    .prob-bar {{
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: 600;
        font-size: 0.85rem;
    }}
    
    .prob-home {{ background: linear-gradient(90deg, #2563eb, #3b82f6); }}
    .prob-draw {{ background: linear-gradient(90deg, #4b5563, #6b7280); }}
    .prob-away {{ background: linear-gradient(90deg, #dc2626, #ef4444); }}
    
    /* Tables */
    table {{
        color: var(--text-primary) !important;
        background: var(--bg-card) !important;
        border-collapse: collapse;
        width: 100%;
    }}
    
    thead tr th {{
        background: #334155 !important;
        color: var(--text-primary) !important;
        padding: 12px;
        text-align: left;
    }}
    
    tbody tr td {{
        border-bottom: 1px solid var(--border) !important;
        padding: 12px;
        color: var(--text-secondary);
    }}
    
    /* Sidebar */
    section[data-testid="stSidebar"] {{
        background: var(--bg-secondary) !important;
        border-right: 1px solid var(--border);
    }}
    
    /* Inputs */
    .stTextInput input, .stSelectbox select, .stNumberInput input {{
        background: var(--bg-primary) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border) !important;
    }}
    
    /* Material Icons Helper */
    .icon {{
        font-family: 'Material Symbols Outlined';
        font-weight: normal;
        font-style: normal;
        font-size: 24px;
        line-height: 1;
        letter-spacing: normal;
        text-transform: none;
        display: inline-block;
        white-space: nowrap;
        word-wrap: normal;
        direction: ltr;
        vertical-align: middle;
        margin-right: 8px;
    }}
    
    .icon-small {{ font-size: 18px; }}
    .icon-large {{ font-size: 32px; }}
</style>
"""

MOBILE_NAV_CSS = """
<style>
    /* Mobile Navigation Container */
    /* Target the parent container of the anchor using :has() */
    div[data-testid="stVerticalBlock"]:has(#mobile-nav-anchor) {
        /* Desktop: Hidden */
        display: none;
    }

    /* Mobile Media Query */
    @media (max-width: 768px) {
        div[data-testid="stVerticalBlock"]:has(#mobile-nav-anchor) {
            display: flex;
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            z-index: 999999;
            background: rgba(255, 255, 255, 0.95); /* Light theme default */
            border-top: 1px solid var(--border);
            padding: 8px 12px 20px 12px; /* Extra bottom padding for safe area */
            gap: 8px;
            box-shadow: 0 -4px 6px -1px rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            width: 100% !important;
            margin: 0 !important;
        }

        /* Dark mode overrides applied automatically via CSS variables 
           but we explicitly set background for robustness */
        .stApp[data-theme="dark"] div[data-testid="stVerticalBlock"]:has(#mobile-nav-anchor) {
            background: rgba(15, 23, 42, 0.95);
        }

        /* Styling the buttons inside the nav */
        div[data-testid="stVerticalBlock"]:has(#mobile-nav-anchor) button {
            border: none !important;
            background: transparent !important;
            box-shadow: none !important;
            color: var(--text-secondary) !important;
            padding: 4px !important;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: auto !important;
            min-height: 50px;
            gap: 4px;
        }

        /* Active state (Primary buttons in Streamlit) */
        div[data-testid="stVerticalBlock"]:has(#mobile-nav-anchor) button[kind="primary"] {
            color: var(--accent) !important;
            background: rgba(59, 130, 246, 0.1) !important;
            border-radius: 8px;
        }
        
        div[data-testid="stVerticalBlock"]:has(#mobile-nav-anchor) button:hover {
            color: var(--accent) !important;
        }
        
        /* Adjust main content padding to prevent overlap */
        .block-container {
            padding-bottom: 90px !important;
        }
    }
</style>
"""

def get_theme_css(is_dark: bool = True) -> str:
    """Return CSS for the selected theme."""
    base_theme = DARK_THEME if is_dark else LIGHT_THEME
    return base_theme + MOBILE_NAV_CSS


def render_icon(name: str, size: str = "normal", color: str = "inherit") -> str:
    """Render a Material Symbol icon."""
    size_cls = f"icon-{size}" if size != "normal" else ""
    style = f"color: {color};" if color != "inherit" else ""
    return f'<span class="icon {size_cls}" style="{style}">{name}</span>'


def render_metric_card(value: str, label: str, variant: str = "accent") -> str:
    """Render a styled metric card focusing on readability."""
    return f"""
    <div class="metric-box metric-box-{variant}">
        <div class="metric-value">{value}</div>
        <div class="metric-label">{label}</div>
    </div>
    """


def render_probability_bar(home: float, draw: float, away: float) -> str:
    """Render a visual probability bar for 1X2."""
    home_pct = home * 100
    draw_pct = draw * 100
    away_pct = away * 100
    
    return f"""
    <div class="prob-bar-container">
        <div class="prob-bar prob-home" style="width: {home_pct}%">{home_pct:.0f}%</div>
        <div class="prob-bar prob-draw" style="width: {draw_pct}%">{draw_pct:.0f}%</div>
        <div class="prob-bar prob-away" style="width: {away_pct}%">{away_pct:.0f}%</div>
    </div>
    """


def render_feature_card(icon: str, title: str, description: str) -> str:
    """Render a feature card with icon."""
    return f"""
    <div class="prediction-card" style="text-align: center;">
        <div style="margin-bottom: 12px; color: var(--accent);">
            {render_icon(icon, "large")}
        </div>
        <h3 style="margin-bottom: 8px; font-size: 1.1rem;">{title}</h3>
        <p style="opacity: 0.8; font-size: 0.9rem; margin: 0; color: var(--text-secondary);">{description}</p>
    </div>
    """
