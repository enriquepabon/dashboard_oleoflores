"""
Oleoflores BI Dashboard - Utilidades y Constantes
==================================================

Este módulo contiene:
- Constantes de colores corporativos
- Configuración de zonas y KPIs
- Funciones auxiliares reutilizables
"""

# =============================================================================
# COLORES CORPORATIVOS
# =============================================================================

COLORS = {
    # Colores principales
    "verde_oleo": "#2E7D32",      # Verde corporativo (positivo, éxito)
    "dorado": "#F9A825",          # Dorado/Amarillo (neutro, aceite)
    "rojo_alerta": "#C62828",     # Rojo (negativo, alerta)
    
    # Colores de fondo y texto
    "fondo": "#f9f9f9",           # Fondo principal (gris muy claro)
    "fondo_tarjeta": "#ffffff",   # Fondo de tarjetas (blanco)
    "texto_principal": "#333333", # Texto principal (gris oscuro)
    "texto_secundario": "#666666",# Texto secundario
    
    # Colores para gráficas
    "azul_info": "#1565C0",       # Azul informativo
    "naranja": "#EF6C00",         # Naranja para destacar
    "gris_claro": "#E0E0E0",      # Gris para fondos de gauge
}

# Paleta para gráficos de barras y líneas
CHART_COLORS = [
    "#2E7D32",  # Verde Oleo
    "#F9A825",  # Dorado
    "#1565C0",  # Azul
    "#EF6C00",  # Naranja
    "#7B1FA2",  # Púrpura
    "#00838F",  # Cyan oscuro
]

# Colores para el diagrama Sankey
SANKEY_COLORS = {
    "cpo_entrada": "#F9A825",     # Entrada CPO (dorado)
    "refineria": "#2E7D32",       # Refinería (verde)
    "oleina": "#1565C0",          # Oleína (azul)
    "rbd": "#00838F",             # RBD (cyan)
    "margarinas": "#7B1FA2",      # Margarinas (púrpura)
    "mermas": "#C62828",          # Mermas (rojo)
}

# =============================================================================
# CONFIGURACIÓN DE ZONAS
# =============================================================================

ZONAS = ["Codazzi", "MLB", "A&G", "Sinú"]

ZONAS_CONFIG = {
    "Codazzi": {"color": "#2E7D32", "icono": "🌴"},
    "MLB": {"color": "#1565C0", "icono": "🏭"},
    "A&G": {"color": "#F9A825", "icono": "🌾"},
    "Sinú": {"color": "#EF6C00", "icono": "🌿"},
}

# =============================================================================
# CONFIGURACIÓN DE KPIs
# =============================================================================

KPIS_CONFIG = {
    "rff_toneladas": {
        "nombre": "Toneladas RFF",
        "unidad": "Ton",
        "formato": "{:,.0f}",
        "icono": "📦",
    },
    "tea_promedio": {
        "nombre": "TEA Promedio",
        "unidad": "%",
        "formato": "{:.2f}%",
        "icono": "🎯",
        "rango_normal": (18, 25),  # Rango normal de TEA
        "rango_alerta": (0, 35),   # Rango antes de alerta crítica
    },
    "produccion_cpo": {
        "nombre": "Producción CPO",
        "unidad": "Ton",
        "formato": "{:,.0f}",
        "icono": "🛢️",
    },
    "produccion_margarinas": {
        "nombre": "Producción Margarinas",
        "unidad": "Ton",
        "formato": "{:,.0f}",
        "icono": "🧈",
    },
}

# =============================================================================
# CONFIGURACIÓN DE COLUMNAS ESPERADAS
# =============================================================================

UPSTREAM_COLUMNS = [
    "fecha",
    "zona",
    "rff_real",
    "rff_presupuesto",
    "cpo_real",
    "cpo_presupuesto",
    "palmiste_real",
    "palmiste_presupuesto",
    "tea_real",
    "tea_meta",
]

DOWNSTREAM_COLUMNS = [
    "fecha",
    "refineria",
    "cpo_entrada",
    "oleina_real",
    "oleina_presupuesto",
    "rbd_real",
    "rbd_presupuesto",
    "margarinas_real",
    "margarinas_presupuesto",
    "mermas",
]

# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================

def formato_numero(valor, decimales=0, con_signo=False):
    """
    Formatea un número con separadores de miles.
    
    Args:
        valor: Número a formatear
        decimales: Cantidad de decimales (default: 0)
        con_signo: Si True, agrega + para valores positivos
    
    Returns:
        String formateado
    """
    if valor is None:
        return "N/A"
    
    formato = f"{{:,.{decimales}f}}"
    resultado = formato.format(valor)
    
    if con_signo and valor > 0:
        resultado = f"+{resultado}"
    
    return resultado


def formato_porcentaje(valor, decimales=1):
    """
    Formatea un valor como porcentaje.
    
    Args:
        valor: Número a formatear (ej: 0.25 para 25%)
        decimales: Cantidad de decimales
    
    Returns:
        String formateado con símbolo %
    """
    if valor is None:
        return "N/A"
    
    return f"{valor:.{decimales}f}%"


def calcular_variacion(real, presupuesto):
    """
    Calcula la variación entre valor real y presupuesto.
    
    Args:
        real: Valor real
        presupuesto: Valor presupuestado
    
    Returns:
        tuple: (variacion_absoluta, variacion_porcentual)
    """
    if presupuesto is None or presupuesto == 0:
        return (None, None)
    
    variacion_abs = real - presupuesto
    variacion_pct = (variacion_abs / presupuesto) * 100
    
    return (variacion_abs, variacion_pct)


def get_color_variacion(variacion, invertir=False):
    """
    Retorna el color según si la variación es positiva o negativa.
    
    Args:
        variacion: Valor de la variación
        invertir: Si True, positivo es malo (ej: para mermas)
    
    Returns:
        Color hex string
    """
    if variacion is None:
        return COLORS["texto_secundario"]
    
    es_positivo = variacion >= 0
    
    if invertir:
        es_positivo = not es_positivo
    
    return COLORS["verde_oleo"] if es_positivo else COLORS["rojo_alerta"]


def get_flecha_variacion(variacion, invertir=False):
    """
    Retorna el emoji de flecha según la variación.
    
    Args:
        variacion: Valor de la variación
        invertir: Si True, positivo es malo
    
    Returns:
        Emoji de flecha (↑, ↓, →)
    """
    if variacion is None or variacion == 0:
        return "→"
    
    es_positivo = variacion > 0
    
    if invertir:
        es_positivo = not es_positivo
    
    return "↑" if es_positivo else "↓"

