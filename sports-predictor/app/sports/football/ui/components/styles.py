import pandas as pd

def _apply_table_styles(df: pd.DataFrame, numeric_cols: list = None):
    """
    Aplica estilos estandarizados a las tablas:
    1. Centrado de encabezados y celdas.
    2. Mapa de calor (Heatmap) con degradado: Rojo (Min) -> Amarillo (Medio) -> Verde (Max).
    """
    # Centrado CSS robusto
    styler = df.style.set_properties(**{
        'text-align': 'center', 
        'vertical-align': 'middle'
    }).set_table_styles([
        {'selector': 'th', 'props': [('text-align', 'center !important')]},
        {'selector': 'td', 'props': [('text-align', 'center !important')]}
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

    # Aplicar a clumnas numéricas
    for col in numeric_cols:
        if col in df.columns:
            styler = styler.apply(get_gradient_style, subset=[col])
            
    return styler

def get_card_html(label: str, odds: float) -> str:
    """
    Genera el HTML para una 'Card' de apuesta estandarizada.
    
    Estilo:
    - Fondo oscuro azulado (#1e3a5f)
    - Borde sutil (#2d5a87)
    - Label gris claro (#94a3b8) pequeño
    - Cuota verde neón (#22c55e) grande y negrita
    - Efecto hover (opcional, por ahora estático)
    """
    return f"""
    <div style="background:#1e3a5f;border:1px solid #2d5a87;border-radius:8px;padding:10px;text-align:center;margin:2px;height:100%;">
        <div style="color:#94a3b8;font-size:11px;line-height:1.2;margin-bottom:4px;">{label}</div>
        <div style="color:#22c55e;font-size:18px;font-weight:bold;">{odds:.2f}</div>
    </div>
    """
