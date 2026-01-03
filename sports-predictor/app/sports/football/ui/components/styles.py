import pandas as pd

def _apply_table_styles(df: pd.DataFrame, numeric_cols: list = None):
    """
    Aplica estilos estandarizados a las tablas:
    1. Centrado de encabezados y celdas.
    2. Mapa de calor (Heatmap) con degradado: Rojo (Min) -> Amarillo (Medio) -> Verde (Max).
    """
    # Centrado CSS robusto con !important para todas las celdas y encabezados
    styler = df.style.set_properties(**{
        'text-align': 'center !important', 
        'vertical-align': 'middle !important'
    }).set_table_styles([
        {'selector': 'th', 'props': [('text-align', 'center !important'), ('vertical-align', 'middle !important')]},
        {'selector': 'td', 'props': [('text-align', 'center !important'), ('vertical-align', 'middle !important')]},
        {'selector': 'th.col_heading', 'props': [('text-align', 'center !important')]},
        {'selector': 'th.row_heading', 'props': [('text-align', 'center !important')]}
    ])
    
    if not numeric_cols:
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        
    def get_gradient_style(s):
        # Si no hay variación, devolver lista vacía
        if s.nunique() <= 1 or s.empty:
            return ['' for _ in s]
            
        s_min = s.min()
        s_max = s.max()
        rng = s_max - s_min
        
        # Colores RGB para interpolación
        # Min: #ef4444 (Red-500) -> (239, 68, 68)
        # Mid: #eab308 (Yellow-500) -> (234, 179, 8)
        # Max: #22c55e (Green-500) -> (34, 197, 94)
        
        c_min = (239, 68, 68)   # Red
        c_mid = (234, 179, 8)   # Yellow
        c_max = (34, 197, 94)   # Green
        
        styles = []
        for val in s:
            if pd.isna(val):
                styles.append('')
                continue
                
            # Normalizar 0..1
            norm = (val - s_min) / rng if rng != 0 else 0
            
            # Interpolación
            if norm <= 0.5:
                # Interpolar entre Min y Mid (norm va de 0 a 0.5 -> reescalar a 0..1)
                local_norm = norm / 0.5
                r = int(c_min[0] + (c_mid[0] - c_min[0]) * local_norm)
                g = int(c_min[1] + (c_mid[1] - c_min[1]) * local_norm)
                b = int(c_min[2] + (c_mid[2] - c_min[2]) * local_norm)
            else:
                # Interpolar entre Mid y Max (norm va de 0.5 a 1 -> reescalar a 0..1)
                local_norm = (norm - 0.5) / 0.5
                r = int(c_mid[0] + (c_max[0] - c_mid[0]) * local_norm)
                g = int(c_mid[1] + (c_max[1] - c_mid[1]) * local_norm)
                b = int(c_mid[2] + (c_max[2] - c_mid[2]) * local_norm)
                
            # Determinar color de texto (Blanco para extremos oscuros, Negro para amarillo brillante)
            lum = (0.299*r + 0.587*g + 0.114*b)
            text_color = '#000000' if lum > 140 else '#ffffff'
            
            # Formatear CSS con transparencia ligera
            styles.append(f'background-color: rgba({r},{g},{b}, 0.7); color: {text_color}; font-weight: bold;')
            
        return styles

    # Aplicar a columnas numéricas
    for col in numeric_cols:
        if col in df.columns:
            styler = styler.apply(get_gradient_style, subset=[col])
            
    return styler

def render_styled_table(df: pd.DataFrame, numeric_cols: list = None):
    """
    Renderiza una tabla estilizada como HTML para usar con st.markdown.
    Incluye centrado de texto y mapa de calor.
    """
    styler = _apply_table_styles(df, numeric_cols)
    # Ocultar índice y generar HTML
    html = styler.hide(axis='index').to_html()
    # Inyectar CSS adicional para centrado forzado
    css = """
    <style>
    .dataframe-container table {
        width: 100%;
        border-collapse: collapse;
    }
    .dataframe-container th, .dataframe-container td {
        text-align: center !important;
        vertical-align: middle !important;
        padding: 8px !important;
    }
    .dataframe-container th {
        background-color: #1e3a5f;
        color: white;
        font-weight: bold;
    }
    </style>
    """
    return f'<div class="dataframe-container">{css}{html}</div>'

def get_card_html(label: str, odds: float, prob: float = None) -> str:
    """
    Genera el HTML para una 'Card' de apuesta estandarizada.
    
    Estilo:
    - Fondo oscuro (#0E1117)
    - Borde sutil (#4a5568)
    - Label blanco
    - Cuota verde neón (#22c55e) grande y negrita
    - Probabilidad en amarillo si está disponible
    
    Args:
        label: Etiqueta del outcome
        odds: Cuota decimal
        prob: Probabilidad (0.0 - 1.0) opcional
    """
    # Formatear cuota y probabilidad
    if prob is not None:
        prob_pct = round(prob * 100, 1)
        value_display = f"{odds:.2f} <span style='color:#FFD700;font-size:14px;'>({prob_pct}%)</span>"
    else:
        value_display = f"{odds:.2f}"
    
    return f"""
    <div style="background:#0E1117;border:1px solid #4a5568;border-radius:8px;padding:10px;text-align:center;margin:2px;height:100%;">
        <div style="color:#ffffff;font-size:11px;line-height:1.2;margin-bottom:4px;">{label}</div>
        <div style="color:#22c55e;font-size:18px;font-weight:bold;">{value_display}</div>
    </div>
    """

def get_section_title_html(title: str) -> str:
    """
    Genera el HTML para un título de sección estandarizado.
    
    Estilo:
    - Margen inferior: 4px
    - Fuente en negrita
    """
    return f"<p style='margin-bottom:4px;font-weight:bold;text-align:center;'>{title}</p>"
