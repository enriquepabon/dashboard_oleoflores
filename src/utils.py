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
    # =========================================================================
    # GOOGLE LANGUAGE EXPLORER STYLE - Minimal Dark Theme with Blue Accent
    # =========================================================================
    
    # Fondos - Negro puro minimalista
    "fondo": "#0e0e0e",                    # Fondo principal (negro puro)
    "fondo_secundario": "#1a1a1a",         # Nivel secundario
    "fondo_terciario": "#252525",          # Nivel adicional
    "fondo_tarjeta": "#1e1e1e",            # Fondo de tarjetas
    "fondo_glass": "rgba(255,255,255,0.05)", # Efecto sutil
    "fondo_hover": "rgba(255,255,255,0.08)", # Hover states
    
    # Colores principales - Azul como acento principal
    "verde_oleo": "#4d9fff",               # Azul principal (reemplaza verde)
    "verde_oscuro": "#3d7fcf",             # Azul oscuro para gradientes
    "verde_glow": "rgba(77, 159, 255, 0.3)", # Azul para efectos glow
    "dorado": "#fbbf24",                   # Amarillo/dorado para warnings
    "dorado_claro": "#fcd34d",             # Dorado para hover
    "rojo_alerta": "#f87171",              # Rojo suave (alerta)
    
    # Texto - Alto Contraste
    "texto_principal": "#ffffff",          # Texto blanco
    "texto_secundario": "#8b8b8b",         # Gris para labels
    "texto_muted": "#6b6b6b",              # Texto deshabilitado
    
    # Acentos adicionales
    "azul_info": "#4d9fff",                # Azul principal
    "naranja": "#fb923c",                  # Naranja
    "cyan": "#22d3ee",                     # Cyan
    "purple": "#a78bfa",                   # Púrpura
    "rosa": "#f472b6",                     # Rosa
    
    # UI Elements
    "gris_claro": "#2a2a2a",               # Bordes y separadores
    "borde": "rgba(255,255,255,0.08)",     # Bordes sutiles
    "borde_activo": "rgba(77,159,255,0.5)", # Borde con glow azul
    "glass_border": "rgba(255,255,255,0.1)", # Bordes glass
    "glass_shadow": "rgba(0,0,0,0.3)",     # Sombras
}

# Paleta para gráficos - Azul como color primario
CHART_COLORS = [
    "#4d9fff",  # Azul principal
    "#82b9ff",  # Azul claro
    "#22d3ee",  # Cyan
    "#a78bfa",  # Púrpura
    "#fbbf24",  # Amarillo
    "#fb923c",  # Naranja
    "#f472b6",  # Rosa
    "#34d399",  # Verde menta
]

# Colores para el diagrama Sankey - Usando tonos azules
SANKEY_COLORS = {
    "cpo_entrada": "#fbbf24",     # Entrada CPO (dorado)
    "refineria": "#4d9fff",       # Refinería (azul)
    "oleina": "#22d3ee",          # Oleína (cyan)
    "rbd": "#82b9ff",             # RBD (azul claro)
    "margarinas": "#a78bfa",      # Margarinas (púrpura)
    "mermas": "#f87171",          # Mermas (rojo)
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

# Columnas extendidas para upstream (opcionales)
UPSTREAM_COLUMNS_EXTENDED = UPSTREAM_COLUMNS + [
    "almendra_real",
    "almendra_presupuesto",
    "kpo_real",
    "kpo_presupuesto",
    "extraccion_almendra",
    "acidez",
    "humedad",
    "impurezas",
    "inventario_cpo",
    "tanque_1",
    "tanque_2",
    "tanque_3",
    "tanque_4",
]

# Columnas para datos DOWNSTREAM (formato completo)
DOWNSTREAM_COLUMNS = [
    "fecha",
    "producto",
    "tipo",
    "produccion_me",
    "produccion_real",
    "cumplimiento",
]

# Columnas extendidas para downstream (formato anterior - compatibilidad)
DOWNSTREAM_COLUMNS_LEGACY = [
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

DOWNSTREAM_COLUMNS_EXTENDED = DOWNSTREAM_COLUMNS_LEGACY + [
    "inventario_rbd",
    "inventario_oleina",
    "inventario_margarinas",
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


# =============================================================================
# 6.1 - VALIDACIÓN DE RANGOS DE DATOS
# =============================================================================

# Configuración de rangos válidos para alertas
DATA_RANGES = {
    "tea_real": {
        "min": 0,
        "max": 35,
        "nombre": "TEA",
        "unidad": "%",
        "mensaje_bajo": "TEA muy baja - posible problema de extracción",
        "mensaje_alto": "TEA fuera de rango técnico esperado"
    },
    "tea_meta": {
        "min": 0,
        "max": 35,
        "nombre": "Meta TEA",
        "unidad": "%"
    },
    "rff_real": {
        "min": 0,
        "max": None,  # Sin límite superior
        "nombre": "RFF",
        "unidad": "Ton",
        "mensaje_bajo": "Valor de RFF no puede ser negativo"
    },
    "cpo_real": {
        "min": 0,
        "max": None,
        "nombre": "CPO",
        "unidad": "Ton"
    },
    "mermas": {
        "min": 0,
        "max": None,
        "nombre": "Mermas",
        "unidad": "Ton",
        "alerta_porcentaje": 15,  # Alerta si mermas > 15% del CPO entrada
        "mensaje_alto": "Mermas excesivas detectadas"
    }
}


def validate_data_ranges(df, dataset_type="upstream"):
    """
    Valida que los datos estén dentro de rangos lógicos.
    
    Args:
        df: DataFrame a validar
        dataset_type: 'upstream' o 'downstream'
    
    Returns:
        Lista de diccionarios con alertas encontradas:
        [{"tipo": "warning"|"error", "columna": str, "mensaje": str, "valores": list}]
    """
    alertas = []
    
    if df is None or df.empty:
        return alertas
    
    # Validaciones específicas por tipo de dataset
    if dataset_type == "upstream":
        # Validar TEA
        if 'tea_real' in df.columns:
            tea_config = DATA_RANGES.get("tea_real", {})
            
            # TEA negativa
            tea_negativa = df[df['tea_real'] < 0]
            if not tea_negativa.empty:
                alertas.append({
                    "tipo": "error",
                    "columna": "tea_real",
                    "mensaje": "🚨 TEA con valores negativos detectados",
                    "detalle": f"{len(tea_negativa)} registros con TEA < 0",
                    "valores": tea_negativa['tea_real'].tolist()[:5]
                })
            
            # TEA fuera de rango (> 35%)
            tea_alta = df[df['tea_real'] > 35]
            if not tea_alta.empty:
                alertas.append({
                    "tipo": "error",
                    "columna": "tea_real",
                    "mensaje": "🚨 TEA fuera de rango técnico (>35%)",
                    "detalle": f"{len(tea_alta)} registros con TEA > 35%",
                    "valores": tea_alta['tea_real'].tolist()[:5]
                })
            
            # TEA muy baja (< 15%) - advertencia
            tea_baja = df[(df['tea_real'] > 0) & (df['tea_real'] < 15)]
            if not tea_baja.empty:
                alertas.append({
                    "tipo": "warning",
                    "columna": "tea_real",
                    "mensaje": "⚠️ TEA inusualmente baja (<15%)",
                    "detalle": f"{len(tea_baja)} registros - verificar proceso de extracción",
                    "valores": tea_baja['tea_real'].tolist()[:5]
                })
        
        # Validar RFF negativo
        if 'rff_real' in df.columns:
            rff_negativa = df[df['rff_real'] < 0]
            if not rff_negativa.empty:
                alertas.append({
                    "tipo": "error",
                    "columna": "rff_real",
                    "mensaje": "🚨 RFF con valores negativos",
                    "detalle": f"{len(rff_negativa)} registros inválidos",
                    "valores": rff_negativa['rff_real'].tolist()[:5]
                })
        
        # Validar CPO > RFF (imposible físicamente)
        if 'cpo_real' in df.columns and 'rff_real' in df.columns:
            cpo_mayor_rff = df[df['cpo_real'] > df['rff_real']]
            if not cpo_mayor_rff.empty:
                alertas.append({
                    "tipo": "error",
                    "columna": "cpo_real",
                    "mensaje": "🚨 CPO mayor que RFF (físicamente imposible)",
                    "detalle": f"{len(cpo_mayor_rff)} registros con inconsistencia",
                    "valores": []
                })
    
    elif dataset_type == "downstream":
        # Validar mermas excesivas
        if 'mermas' in df.columns and 'cpo_entrada' in df.columns:
            df_temp = df.copy()
            df_temp['pct_mermas'] = (df_temp['mermas'] / df_temp['cpo_entrada'] * 100).fillna(0)
            mermas_altas = df_temp[df_temp['pct_mermas'] > 15]
            
            if not mermas_altas.empty:
                alertas.append({
                    "tipo": "warning",
                    "columna": "mermas",
                    "mensaje": "⚠️ Mermas superiores al 15% del CPO entrada",
                    "detalle": f"{len(mermas_altas)} registros con mermas elevadas",
                    "valores": mermas_altas['pct_mermas'].round(1).tolist()[:5]
                })
        
        # Validar valores negativos
        for col in ['oleina_real', 'rbd_real', 'margarinas_real', 'mermas']:
            if col in df.columns:
                negativos = df[df[col] < 0]
                if not negativos.empty:
                    alertas.append({
                        "tipo": "error",
                        "columna": col,
                        "mensaje": f"🚨 {col.replace('_', ' ').title()} con valores negativos",
                        "detalle": f"{len(negativos)} registros inválidos",
                        "valores": negativos[col].tolist()[:5]
                    })
    
    return alertas


def get_alert_summary(alertas):
    """
    Genera un resumen de alertas para mostrar en el dashboard.
    
    Args:
        alertas: Lista de alertas de validate_data_ranges()
    
    Returns:
        dict con conteo por tipo y lista formateada
    """
    if not alertas:
        return {
            "total": 0,
            "errores": 0,
            "advertencias": 0,
            "lista": []
        }
    
    errores = [a for a in alertas if a["tipo"] == "error"]
    advertencias = [a for a in alertas if a["tipo"] == "warning"]
    
    return {
        "total": len(alertas),
        "errores": len(errores),
        "advertencias": len(advertencias),
        "lista": alertas
    }


# =============================================================================
# 6.4 - EXPORTACIÓN DE DATOS
# =============================================================================

def export_to_csv(df, filename_prefix="datos"):
    """
    Prepara un DataFrame para exportación a CSV.
    
    Args:
        df: DataFrame a exportar
        filename_prefix: Prefijo para el nombre del archivo
    
    Returns:
        tuple: (csv_string, filename_sugerido)
    """
    from datetime import datetime
    
    if df is None or df.empty:
        return None, None
    
    # Generar nombre de archivo con timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{filename_prefix}_{timestamp}.csv"
    
    # Convertir a CSV
    csv_string = df.to_csv(index=False)
    
    return csv_string, filename


def prepare_export_data(df, include_variations=True):
    """
    Prepara datos para exportación, incluyendo columnas calculadas.
    
    Args:
        df: DataFrame original
        include_variations: Si incluir columnas de variación
    
    Returns:
        DataFrame preparado para exportación
    """
    if df is None or df.empty:
        return df
    
    df_export = df.copy()
    
    # Formatear fechas si existen
    if 'fecha' in df_export.columns:
        df_export['fecha'] = df_export['fecha'].dt.strftime('%Y-%m-%d')
    
    # Redondear valores numéricos
    numeric_cols = df_export.select_dtypes(include=['float64']).columns
    for col in numeric_cols:
        df_export[col] = df_export[col].round(2)
    
    return df_export
