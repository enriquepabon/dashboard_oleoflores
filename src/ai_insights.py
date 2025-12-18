"""
AI Insights Module - Generación de Insights Contextuales
=========================================================

Este módulo proporciona funcionalidad para generar insights
contextuales rápidos sobre gráficas y tablas específicas.

Uso:
    from src.ai_insights import generate_quick_insight, get_suggested_questions
"""

import os
import pandas as pd
from typing import Optional, Dict, Any, List
import json

# =============================================================================
# CONFIGURACIÓN
# =============================================================================

INSIGHT_SYSTEM_PROMPT = """Eres un analista experto en agroindustria de palma de aceite.
Genera insights breves, claros y accionables en español.
Enfócate en:
- Anomalías o desviaciones significativas
- Tendencias importantes
- Comparaciones con metas/presupuestos
- Recomendaciones prácticas

Responde en máximo 2-3 oraciones. Sé directo y específico."""

CHART_CONTEXTS = {
    "rff": "RFF (Racimos de Fruta Fresca) en toneladas - materia prima procesada",
    "cpo": "CPO (Crude Palm Oil) en toneladas - aceite crudo producido",
    "tea": "TEA/TAE (Tasa de Extracción de Aceite) = CPO/RFF × 100 - eficiencia de extracción",
    "tanques": "Niveles de tanques de almacenamiento de CPO",
    "calidad": "Parámetros de calidad: Acidez, Humedad, H+I",
    "downstream": "Producción de refinería: Oleína, Margarinas, productos terminados",
    "balance": "Balance de almendra: Inventarios y procesamiento de nuez/almendra"
}

SUGGESTED_QUESTIONS_BY_CONTEXT = {
    "rff": [
        "¿Por qué la producción está por debajo de la meta?",
        "¿Qué planta tiene mejor rendimiento?",
        "¿Cómo se compara con el mes anterior?"
    ],
    "cpo": [
        "¿Por qué bajó la producción de CPO?",
        "¿Qué factores afectan el rendimiento?",
        "¿Hay correlación con la calidad del RFF?"
    ],
    "tea": [
        "¿Por qué la TEA está por debajo de la meta?",
        "¿Qué planta necesita atención?",
        "¿Cómo mejorar la eficiencia de extracción?"
    ],
    "tanques": [
        "¿Hay riesgo de sobrecapacidad?",
        "¿Cuándo necesitaremos despachar?",
        "¿Qué planta tiene más inventario?"
    ],
    "calidad": [
        "¿Hay problemas de acidez?",
        "¿Qué lotes tienen parámetros fuera de norma?",
        "¿Cómo está la tendencia de calidad?"
    ],
    "downstream": [
        "¿Se está cumpliendo la meta de producción?",
        "¿Qué producto tiene mejor rendimiento?",
        "¿Hay cuellos de botella?"
    ],
    "balance": [
        "¿Cómo está el balance de inventarios?",
        "¿Hay desviaciones en el procesamiento?",
        "¿Qué planta procesa más eficientemente?"
    ],
    "default": [
        "¿Qué anomalías detectas en estos datos?",
        "¿Cuál es el resumen ejecutivo?",
        "¿Qué recomendaciones tienes?"
    ]
}


# =============================================================================
# FUNCIONES DE UTILIDAD
# =============================================================================

def detect_context_type(data: Any, title: str = "") -> str:
    """
    Detecta el tipo de contexto basado en los datos y título.
    
    Args:
        data: DataFrame o dict con los datos
        title: Título de la gráfica/tabla
    
    Returns:
        str: Tipo de contexto detectado
    """
    title_lower = title.lower()
    
    if any(x in title_lower for x in ["rff", "racimo", "fruta"]):
        return "rff"
    elif any(x in title_lower for x in ["cpo", "aceite crudo"]):
        return "cpo"
    elif any(x in title_lower for x in ["tea", "tae", "extracción"]):
        return "tea"
    elif any(x in title_lower for x in ["tanque", "nivel", "almacenamiento"]):
        return "tanques"
    elif any(x in title_lower for x in ["calidad", "acidez", "humedad"]):
        return "calidad"
    elif any(x in title_lower for x in ["refinería", "oleína", "margarina", "downstream"]):
        return "downstream"
    elif any(x in title_lower for x in ["almendra", "nuez", "balance", "ckpo"]):
        return "balance"
    
    # Detectar por columnas si es DataFrame
    if isinstance(data, pd.DataFrame):
        cols = " ".join(data.columns.astype(str)).lower()
        if "rff" in cols:
            return "rff"
        elif "cpo" in cols:
            return "cpo"
        elif "tea" in cols:
            return "tea"
    
    return "default"


def format_data_for_insight(data: Any, max_rows: int = 20) -> str:
    """
    Formatea datos para incluir en el prompt de insight.
    
    Args:
        data: DataFrame, dict o lista
        max_rows: Máximo de filas a incluir
    
    Returns:
        str: Datos formateados
    """
    if isinstance(data, pd.DataFrame):
        if len(data) > max_rows:
            data = data.head(max_rows)
            return data.to_markdown(index=False) + f"\n... (mostrando {max_rows} de {len(data)} filas)"
        return data.to_markdown(index=False)
    
    elif isinstance(data, dict):
        return json.dumps(data, indent=2, ensure_ascii=False, default=str)
    
    elif isinstance(data, list):
        return json.dumps(data[:max_rows], indent=2, ensure_ascii=False, default=str)
    
    return str(data)


# =============================================================================
# FUNCIONES PRINCIPALES
# =============================================================================

def get_suggested_questions(data: Any, title: str = "") -> List[str]:
    """
    Retorna preguntas sugeridas basadas en el contexto de los datos.
    
    Args:
        data: Datos de la gráfica/tabla
        title: Título de la visualización
    
    Returns:
        List[str]: Lista de preguntas sugeridas
    """
    context_type = detect_context_type(data, title)
    return SUGGESTED_QUESTIONS_BY_CONTEXT.get(context_type, SUGGESTED_QUESTIONS_BY_CONTEXT["default"])


def generate_quick_insight(
    data: Any,
    title: str,
    model: str = None,
    additional_context: str = ""
) -> str:
    """
    Genera un insight rápido sobre los datos proporcionados.
    
    Args:
        data: DataFrame, dict o lista con los datos
        title: Título de la gráfica/tabla
        model: Modelo de IA a usar (None = usar default)
        additional_context: Contexto adicional opcional
    
    Returns:
        str: Insight generado
    """
    # Importar aquí para evitar circular imports
    from src.ai_chat import query_ai, get_available_providers
    
    # Verificar que hay proveedor disponible
    providers = get_available_providers()
    if not any(providers.values()):
        return "⚠️ No hay API de IA configurada. Configura OPENAI_API_KEY o GOOGLE_API_KEY."
    
    # Detectar contexto
    context_type = detect_context_type(data, title)
    context_description = CHART_CONTEXTS.get(context_type, "Datos del dashboard")
    
    # Formatear datos
    formatted_data = format_data_for_insight(data)
    
    # Construir prompt
    prompt = f"""Analiza estos datos y genera un insight breve (2-3 oraciones máximo):

**Tipo de datos:** {context_description}
**Título:** {title}

**Datos:**
{formatted_data}

{f'**Contexto adicional:** {additional_context}' if additional_context else ''}

Genera un insight accionable enfocándote en lo más importante o anomalías detectadas."""
    
    # Usar el sistema de chat existente
    try:
        # Temporalmente agregar contexto y hacer query
        insight = query_ai(prompt, model)
        return insight
    except Exception as e:
        return f"❌ Error generando insight: {str(e)}"


def analyze_comparison(
    data1: Any,
    title1: str,
    data2: Any,
    title2: str,
    model: str = None
) -> str:
    """
    Genera un análisis comparativo entre dos conjuntos de datos.
    
    Args:
        data1: Primer conjunto de datos
        title1: Título del primer conjunto
        data2: Segundo conjunto de datos
        title2: Título del segundo conjunto
        model: Modelo de IA a usar
    
    Returns:
        str: Análisis comparativo
    """
    from src.ai_chat import query_ai, get_available_providers
    
    providers = get_available_providers()
    if not any(providers.values()):
        return "⚠️ No hay API de IA configurada."
    
    formatted1 = format_data_for_insight(data1)
    formatted2 = format_data_for_insight(data2)
    
    prompt = f"""Compara estos dos conjuntos de datos y genera un análisis breve:

**Datos 1 - {title1}:**
{formatted1}

**Datos 2 - {title2}:**
{formatted2}

Genera un análisis comparativo enfocándote en:
1. Diferencias clave
2. Posibles causas
3. Recomendaciones

Responde en 3-4 oraciones máximo."""
    
    try:
        return query_ai(prompt, model)
    except Exception as e:
        return f"❌ Error en análisis comparativo: {str(e)}"


def generate_dashboard_summary(
    all_data: Dict[str, Any],
    model: str = None
) -> str:
    """
    Genera un resumen ejecutivo del dashboard completo.
    
    Args:
        all_data: Diccionario con todos los datos del dashboard
        model: Modelo de IA a usar
    
    Returns:
        str: Resumen ejecutivo
    """
    from src.ai_chat import query_ai, get_available_providers
    
    providers = get_available_providers()
    if not any(providers.values()):
        return "⚠️ No hay API de IA configurada."
    
    # Formatear todos los datos
    data_sections = []
    for key, value in all_data.items():
        formatted = format_data_for_insight(value.get('data'), max_rows=10)
        description = value.get('description', key)
        data_sections.append(f"### {description}\n{formatted}")
    
    all_formatted = "\n\n---\n\n".join(data_sections)
    
    prompt = f"""Genera un resumen ejecutivo breve basado en todos estos datos del dashboard:

{all_formatted}

El resumen debe incluir:
1. **Estado General:** Una línea sobre el estado de operaciones
2. **Puntos Destacados:** 2-3 items positivos o negativos importantes
3. **Recomendación Principal:** Una acción sugerida

Formato: Markdown breve y conciso."""
    
    try:
        return query_ai(prompt, model)
    except Exception as e:
        return f"❌ Error generando resumen: {str(e)}"
