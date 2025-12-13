"""
Módulo Balance Almendra - Procesamiento de reportes con IA
===========================================================

Procesa reportes diarios de las 4 plantas (PDFs e imágenes) usando 
OpenAI GPT-4o-mini Vision para extraer datos estructurados de:
- Inventarios de nuez y almendra
- Procesamiento en palmistería y expellers
- Producción de CKPO y torta

Uso:
    from src.balance_almendra import process_reports, get_daily_balance
"""

import os
import json
import base64
import re
from datetime import datetime, date
from typing import Optional, Dict, List, Any
import pandas as pd

# Intentar importar OpenAI
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Intentar importar PyMuPDF para PDFs
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False


# ============================================================================
# CONFIGURACIÓN
# ============================================================================

PLANTAS_CONFIG = {
    'CZZ': {
        'nombre': 'Codazzi',
        'tipo': 'expeller',
        'descripcion': 'Planta con expellers - Procesa almendra → CKPO + Torta'
    },
    'A&G': {
        'nombre': 'Aceites & Grasas',
        'tipo': 'palmisteria',
        'descripcion': 'Palmistería - Procesa nuez → almendra'
    },
    'MLB': {
        'nombre': 'María La Baja',
        'tipo': 'palmisteria', 
        'descripcion': 'Palmistería - Procesa nuez → almendra'
    },
    'SINU': {
        'nombre': 'Sinú',
        'tipo': 'transporte',
        'descripcion': 'Solo transporte de nuez (no procesa)'
    }
}

# Prompt para extracción de datos
EXTRACTION_PROMPT = """
Analiza este reporte de planta de procesamiento de palma africana y extrae los datos en formato JSON.

IMPORTANTE: 
- Extrae SOLO los valores numéricos que puedas identificar claramente
- Si un valor no está presente, usa null
- Los valores están en kilogramos (Kg) a menos que se indique Ton
- Convierte toneladas a kilogramos multiplicando por 1000
- "Saldo anterior" = inventario inicial, "Existencia" o "Saldo final" = inventario final

Responde ÚNICAMENTE con el JSON, sin texto adicional ni markdown:

{
  "fecha": "YYYY-MM-DD",
  "planta": "nombre de la planta (CZZ, A&G, MLB, SINU)",
  "nuez": {
    "inventario_inicial_kg": null,
    "entrada_kg": null,
    "produccion_kg": null,
    "consumo_kg": null,
    "inventario_final_kg": null
  },
  "almendra": {
    "inventario_inicial_kg": null,
    "produccion_kg": null,
    "compra_kg": null,
    "traslado_expeller_kg": null,
    "despacho_kg": null,
    "inventario_silos_kg": null,
    "inventario_empacada_kg": null,
    "inventario_final_kg": null
  },
  "ckpo": {
    "inventario_inicial_kg": null,
    "produccion_kg": null,
    "despacho_kg": null,
    "traslado_refineria_kg": null,
    "inventario_final_kg": null
  },
  "torta": {
    "inventario_inicial_kg": null,
    "produccion_kg": null,
    "despacho_kg": null,
    "inventario_final_kg": null
  },
  "metricas": {
    "tea_palmiste_pct": null,
    "recuperacion_almendra_pct": null,
    "eficiencia_expeller": null
  },
  "operacion": {
    "horas_trabajadas": null,
    "expellers_trabajados": null,
    "vagonetas_procesadas": null
  },
  "comentarios_operativos": "texto con observaciones operativas y mecánicas",
  "problemas_detectados": ["lista de problemas identificados"]
}
"""


# ============================================================================
# FUNCIONES DE PROCESAMIENTO
# ============================================================================

def get_api_key() -> Optional[str]:
    """Obtiene la API key de OpenAI desde variables de entorno o Streamlit secrets."""
    # Primero intentar variable de entorno
    api_key = os.getenv('OPENAI_API_KEY')
    if api_key:
        return api_key
    
    # Intentar Streamlit secrets
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and 'OPENAI_API_KEY' in st.secrets:
            return st.secrets['OPENAI_API_KEY']
    except:
        pass
    
    return None


def read_pdf_as_images(pdf_path: str) -> List[bytes]:
    """
    Convierte un PDF a imágenes para procesamiento con Vision.
    
    Returns:
        Lista de imágenes en bytes (PNG)
    """
    if not PYMUPDF_AVAILABLE:
        raise ImportError("PyMuPDF (fitz) no está instalado. Instala con: pip install pymupdf")
    
    images = []
    doc = fitz.open(pdf_path)
    
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        # Renderizar a imagen con buena resolución
        mat = fitz.Matrix(2, 2)  # 2x zoom
        pix = page.get_pixmap(matrix=mat)
        img_bytes = pix.tobytes("png")
        images.append(img_bytes)
    
    doc.close()
    return images


def read_image_file(image_path: str) -> bytes:
    """Lee un archivo de imagen y retorna sus bytes."""
    with open(image_path, 'rb') as f:
        return f.read()


def process_file_with_openai(file_path: str, api_key: str) -> Dict[str, Any]:
    """
    Procesa un archivo (PDF o imagen) con OpenAI GPT-4o-mini Vision.
    
    Args:
        file_path: Ruta al archivo
        api_key: API key de OpenAI
    
    Returns:
        dict: Datos extraídos en formato estructurado
    """
    if not OPENAI_AVAILABLE:
        raise ImportError("openai no está instalado. Instala con: pip install openai")
    
    # Inicializar cliente
    client = OpenAI(api_key=api_key)
    
    # Determinar tipo de archivo
    ext = os.path.splitext(file_path)[1].lower()
    
    # Preparar imágenes
    image_urls = []
    
    if ext == '.pdf':
        # Convertir PDF a imágenes
        images = read_pdf_as_images(file_path)
        for img_bytes in images:
            base64_image = base64.b64encode(img_bytes).decode('utf-8')
            image_urls.append(f"data:image/png;base64,{base64_image}")
    elif ext in ['.png', '.jpg', '.jpeg']:
        img_bytes = read_image_file(file_path)
        mime_type = 'image/png' if ext == '.png' else 'image/jpeg'
        base64_image = base64.b64encode(img_bytes).decode('utf-8')
        image_urls.append(f"data:{mime_type};base64,{base64_image}")
    else:
        raise ValueError(f"Tipo de archivo no soportado: {ext}")
    
    # Construir mensaje con imágenes
    content = [{"type": "text", "text": EXTRACTION_PROMPT}]
    for url in image_urls:
        content.append({
            "type": "image_url",
            "image_url": {"url": url, "detail": "high"}
        })
    
    # Llamar a OpenAI GPT-4o-mini (más económico con visión)
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # Modelo más económico con soporte de visión
        messages=[
            {
                "role": "user",
                "content": content
            }
        ],
        max_tokens=2000
    )
    
    # Obtener respuesta
    response_text = response.choices[0].message.content.strip()
    
    # Limpiar respuesta (a veces viene con markdown)
    if response_text.startswith('```'):
        response_text = re.sub(r'^```json?\n?', '', response_text)
        response_text = re.sub(r'\n?```$', '', response_text)
    
    try:
        data = json.loads(response_text)
        data['_source_file'] = os.path.basename(file_path)
        data['_processed_at'] = datetime.now().isoformat()
        return data
    except json.JSONDecodeError as e:
        return {
            'error': f'Error parseando JSON: {str(e)}',
            'raw_response': response_text,
            '_source_file': os.path.basename(file_path)
        }


# Alias para compatibilidad
def process_file_with_gemini(file_path: str, api_key: str) -> Dict[str, Any]:
    """Alias que redirige a OpenAI (para compatibilidad con código existente)."""
    # Obtener API key de OpenAI
    openai_key = get_api_key()
    if not openai_key:
        raise ValueError("OPENAI_API_KEY no configurada")
    return process_file_with_openai(file_path, openai_key)


def process_multiple_reports(file_paths: List[str]) -> List[Dict[str, Any]]:
    """
    Procesa múltiples reportes y retorna los datos extraídos.
    
    Args:
        file_paths: Lista de rutas a archivos
    
    Returns:
        Lista de diccionarios con datos extraídos
    """
    api_key = get_api_key()
    if not api_key:
        raise ValueError("OPENAI_API_KEY no configurada")
    
    results = []
    for path in file_paths:
        try:
            data = process_file_with_openai(path, api_key)
            results.append(data)
        except Exception as e:
            results.append({
                'error': str(e),
                '_source_file': os.path.basename(path)
            })
    
    return results


# ============================================================================
# FUNCIONES DE ALMACENAMIENTO
# ============================================================================

def flatten_report_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Aplana un diccionario anidado de reporte a formato tabular.
    """
    flat = {
        'fecha': data.get('fecha'),
        'planta': data.get('planta'),
        # Nuez
        'nuez_inventario_inicial_kg': data.get('nuez', {}).get('inventario_inicial_kg'),
        'nuez_entrada_kg': data.get('nuez', {}).get('entrada_kg'),
        'nuez_produccion_kg': data.get('nuez', {}).get('produccion_kg'),
        'nuez_consumo_kg': data.get('nuez', {}).get('consumo_kg'),
        'nuez_inventario_final_kg': data.get('nuez', {}).get('inventario_final_kg'),
        # Almendra
        'almendra_inventario_inicial_kg': data.get('almendra', {}).get('inventario_inicial_kg'),
        'almendra_produccion_kg': data.get('almendra', {}).get('produccion_kg'),
        'almendra_compra_kg': data.get('almendra', {}).get('compra_kg'),
        'almendra_traslado_expeller_kg': data.get('almendra', {}).get('traslado_expeller_kg'),
        'almendra_despacho_kg': data.get('almendra', {}).get('despacho_kg'),
        'almendra_inventario_silos_kg': data.get('almendra', {}).get('inventario_silos_kg'),
        'almendra_inventario_empacada_kg': data.get('almendra', {}).get('inventario_empacada_kg'),
        'almendra_inventario_final_kg': data.get('almendra', {}).get('inventario_final_kg'),
        # CKPO
        'ckpo_inventario_inicial_kg': data.get('ckpo', {}).get('inventario_inicial_kg'),
        'ckpo_produccion_kg': data.get('ckpo', {}).get('produccion_kg'),
        'ckpo_despacho_kg': data.get('ckpo', {}).get('despacho_kg'),
        'ckpo_traslado_refineria_kg': data.get('ckpo', {}).get('traslado_refineria_kg'),
        'ckpo_inventario_final_kg': data.get('ckpo', {}).get('inventario_final_kg'),
        # Torta
        'torta_inventario_inicial_kg': data.get('torta', {}).get('inventario_inicial_kg'),
        'torta_produccion_kg': data.get('torta', {}).get('produccion_kg'),
        'torta_despacho_kg': data.get('torta', {}).get('despacho_kg'),
        'torta_inventario_final_kg': data.get('torta', {}).get('inventario_final_kg'),
        # Métricas
        'tea_palmiste_pct': data.get('metricas', {}).get('tea_palmiste_pct'),
        'recuperacion_almendra_pct': data.get('metricas', {}).get('recuperacion_almendra_pct'),
        # Operación
        'horas_trabajadas': data.get('operacion', {}).get('horas_trabajadas'),
        'expellers_trabajados': data.get('operacion', {}).get('expellers_trabajados'),
        # Comentarios
        'comentarios': data.get('comentarios_operativos', ''),
        'problemas': '; '.join(data.get('problemas_detectados', [])) if data.get('problemas_detectados') else '',
    }
    return flat


def save_daily_balance(reports_data: List[Dict[str, Any]], output_path: str = 'data/balance_almendra.csv'):
    """
    Guarda los datos de reportes en el CSV acumulativo.
    
    Args:
        reports_data: Lista de diccionarios con datos de reportes
        output_path: Ruta al archivo CSV
    """
    # Aplanar datos
    flat_records = [flatten_report_data(r) for r in reports_data if 'error' not in r]
    
    if not flat_records:
        return None
    
    df_new = pd.DataFrame(flat_records)
    
    # Si existe archivo, combinar
    if os.path.exists(output_path):
        df_existing = pd.read_csv(output_path)
        
        # Eliminar registros del mismo día y planta
        for record in flat_records:
            if record['fecha'] and record['planta']:
                mask = ~((df_existing['fecha'] == record['fecha']) & 
                        (df_existing['planta'] == record['planta']))
                df_existing = df_existing[mask]
        
        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
    else:
        df_combined = df_new
    
    # Ordenar y guardar
    df_combined = df_combined.sort_values(['fecha', 'planta']).reset_index(drop=True)
    df_combined.to_csv(output_path, index=False)
    
    return df_combined


def get_daily_balance(fecha: Optional[str] = None, output_path: str = 'data/balance_almendra.csv') -> pd.DataFrame:
    """
    Obtiene el balance de almendra para una fecha específica o el más reciente.
    
    Args:
        fecha: Fecha en formato YYYY-MM-DD (None = más reciente)
        output_path: Ruta al archivo CSV
    
    Returns:
        DataFrame con el balance del día
    """
    if not os.path.exists(output_path):
        return pd.DataFrame()
    
    try:
        df = pd.read_csv(output_path)
    except Exception:
        return pd.DataFrame()
    
    # Validar que hay datos
    if df.empty or 'fecha' not in df.columns:
        return pd.DataFrame()
    
    # Filtrar filas con fecha válida
    df = df.dropna(subset=['fecha'])
    if df.empty:
        return pd.DataFrame()
    
    if fecha:
        return df[df['fecha'] == fecha]
    else:
        # Retornar fecha más reciente
        latest_date = df['fecha'].max()
        return df[df['fecha'] == latest_date]


# ============================================================================
# ANÁLISIS CON IA
# ============================================================================

def generate_balance_analysis(reports_data: List[Dict[str, Any]], contexto_usuario: str = "") -> str:
    """
    Genera un análisis del balance de almendra usando IA (OpenAI).
    
    Args:
        reports_data: Lista de datos de reportes procesados
        contexto_usuario: Contexto adicional proporcionado por el usuario
    
    Returns:
        str: Análisis en texto
    """
    api_key = get_api_key()
    if not api_key:
        return "❌ OPENAI_API_KEY no configurada para generar análisis"
    
    if not OPENAI_AVAILABLE:
        return "❌ openai no está instalado"
    
    # Preparar resumen de datos
    resumen = "DATOS DEL BALANCE DE ALMENDRA:\n\n"
    for data in reports_data:
        if 'error' not in data:
            resumen += f"Planta: {data.get('planta', 'N/A')}\n"
            resumen += f"Fecha: {data.get('fecha', 'N/A')}\n"
            
            # Incluir datos de inventarios
            if data.get('nuez'):
                nuez = data['nuez']
                resumen += f"  Nuez - Inicial: {nuez.get('inventario_inicial_kg')}, Final: {nuez.get('inventario_final_kg')}, Consumo: {nuez.get('consumo_kg')}\n"
            if data.get('almendra'):
                alm = data['almendra']
                resumen += f"  Almendra - Inicial: {alm.get('inventario_inicial_kg')}, Final: {alm.get('inventario_final_kg')}, Producción: {alm.get('produccion_kg')}\n"
            if data.get('ckpo'):
                ckpo = data['ckpo']
                resumen += f"  CKPO - Inicial: {ckpo.get('inventario_inicial_kg')}, Final: {ckpo.get('inventario_final_kg')}, Producción: {ckpo.get('produccion_kg')}\n"
            
            if data.get('comentarios_operativos'):
                resumen += f"  Comentarios: {data['comentarios_operativos']}\n"
            if data.get('problemas_detectados'):
                resumen += f"  Problemas: {', '.join(data['problemas_detectados'])}\n"
            resumen += "\n"
    
    # Agregar contexto del usuario si existe
    contexto_adicional = ""
    if contexto_usuario and contexto_usuario.strip():
        contexto_adicional = f"""
        
CONTEXTO ADICIONAL DEL USUARIO:
{contexto_usuario}

Incluye este contexto en tu análisis.
"""
    
    # Prompt de análisis
    analysis_prompt = f"""
    Eres un analista experto en plantas extractoras de aceite de palma.
    
    Analiza los siguientes datos del balance diario de almendra y genera un reporte ejecutivo:
    
    {resumen}
    {contexto_adicional}
    
    Tu análisis debe incluir:
    1. **Resumen General**: Estado general del procesamiento de almendra
    2. **Alertas**: Problemas operativos o mecánicos detectados
    3. **Inventarios**: Estado de los inventarios de nuez, almendra y CKPO (inicial vs final)
    4. **Eficiencia**: Comentarios sobre la eficiencia del proceso
    5. **Recomendaciones**: Sugerencias para mejorar operaciones
    
    Responde en español, de forma concisa y profesional.
    """
    
    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Económico para análisis de texto
            messages=[
                {"role": "user", "content": analysis_prompt}
            ],
            max_tokens=1500
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ Error generando análisis: {str(e)}"

