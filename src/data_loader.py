"""
Oleoflores BI Dashboard - Módulo de Carga de Datos (ETL)
=========================================================

Este módulo contiene las funciones para:
- Cargar archivos CSV y Excel
- Validar estructura de columnas
- Limpiar y transformar datos
- Calcular variaciones y métricas derivadas
"""

import pandas as pd
import streamlit as st
from datetime import datetime
from typing import Tuple, Optional, List, Union
import os

from .utils import UPSTREAM_COLUMNS, DOWNSTREAM_COLUMNS

# =============================================================================
# 2.1 - FUNCIÓN DE CARGA DE ARCHIVOS
# =============================================================================

def load_file(
    file_path: Union[str, st.runtime.uploaded_file_manager.UploadedFile],
    file_type: str = "auto"
) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """
    Carga un archivo CSV o Excel y retorna un DataFrame.
    
    Args:
        file_path: Ruta al archivo o objeto UploadedFile de Streamlit
        file_type: Tipo de archivo ('csv', 'excel', 'auto' para detectar)
    
    Returns:
        Tuple[DataFrame o None, mensaje de error o None]
    
    Ejemplo:
        df, error = load_file("data/upstream.csv")
        if error:
            st.error(error)
    """
    try:
        # Determinar el tipo de archivo
        if file_type == "auto":
            if isinstance(file_path, str):
                if file_path.endswith('.csv'):
                    file_type = 'csv'
                elif file_path.endswith(('.xlsx', '.xls')):
                    file_type = 'excel'
                else:
                    return None, f"Formato de archivo no soportado: {file_path}"
            else:
                # Es un UploadedFile de Streamlit
                name = file_path.name.lower()
                if name.endswith('.csv'):
                    file_type = 'csv'
                elif name.endswith(('.xlsx', '.xls')):
                    file_type = 'excel'
                else:
                    return None, f"Formato de archivo no soportado: {file_path.name}"
        
        # Cargar según el tipo
        if file_type == 'csv':
            df = pd.read_csv(file_path, encoding='utf-8')
        elif file_type == 'excel':
            df = pd.read_excel(file_path, engine='openpyxl')
        else:
            return None, f"Tipo de archivo no reconocido: {file_type}"
        
        if df.empty:
            return None, "El archivo está vacío"
        
        return df, None
        
    except FileNotFoundError:
        return None, f"Archivo no encontrado: {file_path}"
    except pd.errors.EmptyDataError:
        return None, "El archivo está vacío o no tiene datos válidos"
    except Exception as e:
        return None, f"Error al cargar el archivo: {str(e)}"


# =============================================================================
# 2.2 - FUNCIÓN DE VALIDACIÓN DE COLUMNAS
# =============================================================================

def validate_columns(
    df: pd.DataFrame,
    dataset_type: str
) -> Tuple[bool, List[str]]:
    """
    Valida que el DataFrame tenga las columnas requeridas.
    
    Args:
        df: DataFrame a validar
        dataset_type: 'upstream' o 'downstream'
    
    Returns:
        Tuple[es_válido, lista de columnas faltantes]
    
    Ejemplo:
        is_valid, missing = validate_columns(df, 'upstream')
        if not is_valid:
            st.error(f"Columnas faltantes: {missing}")
    """
    if dataset_type == 'upstream':
        required_columns = UPSTREAM_COLUMNS
    elif dataset_type == 'downstream':
        required_columns = DOWNSTREAM_COLUMNS
    else:
        return False, [f"Tipo de dataset no reconocido: {dataset_type}"]
    
    # Normalizar nombres de columnas (lowercase, sin espacios)
    df_columns = [col.lower().strip().replace(' ', '_') for col in df.columns]
    required_normalized = [col.lower().strip().replace(' ', '_') for col in required_columns]
    
    missing_columns = []
    for col in required_normalized:
        if col not in df_columns:
            missing_columns.append(col)
    
    return len(missing_columns) == 0, missing_columns


# =============================================================================
# 2.3 - FUNCIÓN DE LIMPIEZA DE VALORES NUMÉRICOS
# =============================================================================

def clean_numeric_values(df: pd.DataFrame, columns: List[str] = None) -> pd.DataFrame:
    """
    Limpia valores numéricos eliminando caracteres de formato.
    
    Operaciones:
    - Elimina comas de miles (1,234 -> 1234)
    - Convierte porcentajes (25% -> 25.0)
    - Elimina espacios
    - Convierte a float
    
    Args:
        df: DataFrame a limpiar
        columns: Lista de columnas a limpiar (None = todas las numéricas)
    
    Returns:
        DataFrame con valores limpios
    """
    df = df.copy()
    
    # Si no se especifican columnas, detectar las que parecen numéricas
    if columns is None:
        columns = []
        for col in df.columns:
            if col.lower() not in ['fecha', 'zona', 'refineria', 'date']:
                columns.append(col)
    
    for col in columns:
        if col not in df.columns:
            continue
            
        # Convertir a string para manipular
        df[col] = df[col].astype(str)
        
        # Eliminar espacios
        df[col] = df[col].str.strip()
        
        # Eliminar símbolo de porcentaje
        df[col] = df[col].str.replace('%', '', regex=False)
        
        # Eliminar comas de miles
        df[col] = df[col].str.replace(',', '', regex=False)
        
        # Eliminar símbolo de moneda si existe
        df[col] = df[col].str.replace('$', '', regex=False)
        
        # Reemplazar valores vacíos o 'nan' con NaN real
        df[col] = df[col].replace(['', 'nan', 'NaN', 'null', 'None', '-'], pd.NA)
        
        # Convertir a numérico
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    return df


# =============================================================================
# 2.4 - FUNCIÓN DE NORMALIZACIÓN DE FECHAS
# =============================================================================

def normalize_dates(df: pd.DataFrame, date_column: str = 'fecha') -> pd.DataFrame:
    """
    Normaliza columnas de fecha a formato datetime estándar.
    
    Formatos soportados:
    - YYYY-MM-DD
    - DD/MM/YYYY
    - DD-MM-YYYY
    - MM/DD/YYYY
    
    Args:
        df: DataFrame con columna de fecha
        date_column: Nombre de la columna de fecha
    
    Returns:
        DataFrame con fecha normalizada
    """
    df = df.copy()
    
    if date_column not in df.columns:
        # Buscar columnas alternativas
        alt_names = ['date', 'Fecha', 'DATE', 'fecha_registro']
        for alt in alt_names:
            if alt in df.columns:
                date_column = alt
                break
        else:
            return df  # No se encontró columna de fecha
    
    try:
        # Intentar conversión automática
        df[date_column] = pd.to_datetime(df[date_column], dayfirst=True, errors='coerce')
        
        # Renombrar a 'fecha' si tiene otro nombre
        if date_column != 'fecha':
            df = df.rename(columns={date_column: 'fecha'})
            
    except Exception:
        pass  # Si falla, mantener como está
    
    return df


# =============================================================================
# 2.5 - FUNCIÓN DE CÁLCULO DE VARIACIONES
# =============================================================================

def calculate_variations(df: pd.DataFrame, pairs: List[Tuple[str, str]] = None) -> pd.DataFrame:
    """
    Calcula variaciones entre columnas Real y Presupuesto.
    
    Para cada par (real, presupuesto) calcula:
    - variacion_absoluta = real - presupuesto
    - variacion_porcentual = ((real - presupuesto) / presupuesto) * 100
    - cumplimiento = (real / presupuesto) * 100
    
    Args:
        df: DataFrame con datos
        pairs: Lista de tuplas (columna_real, columna_presupuesto)
               Si None, detecta automáticamente pares *_real/*_presupuesto
    
    Returns:
        DataFrame con columnas de variación añadidas
    """
    df = df.copy()
    
    # Auto-detectar pares si no se especifican
    if pairs is None:
        pairs = []
        for col in df.columns:
            if col.endswith('_real'):
                base_name = col.replace('_real', '')
                presupuesto_col = f"{base_name}_presupuesto"
                if presupuesto_col in df.columns:
                    pairs.append((col, presupuesto_col))
    
    for real_col, presupuesto_col in pairs:
        if real_col not in df.columns or presupuesto_col not in df.columns:
            continue
        
        base_name = real_col.replace('_real', '')
        
        # Variación absoluta
        var_abs_col = f"{base_name}_var_abs"
        df[var_abs_col] = df[real_col] - df[presupuesto_col]
        
        # Variación porcentual
        var_pct_col = f"{base_name}_var_pct"
        df[var_pct_col] = ((df[real_col] - df[presupuesto_col]) / df[presupuesto_col] * 100).round(2)
        df[var_pct_col] = df[var_pct_col].replace([float('inf'), float('-inf')], pd.NA)
        
        # Porcentaje de cumplimiento
        cumpl_col = f"{base_name}_cumplimiento"
        df[cumpl_col] = (df[real_col] / df[presupuesto_col] * 100).round(2)
        df[cumpl_col] = df[cumpl_col].replace([float('inf'), float('-inf')], pd.NA)
    
    return df


# =============================================================================
# 2.6 - FUNCIÓN INTEGRADA PARA UPSTREAM
# =============================================================================

@st.cache_data(ttl=3600)  # Cache por 1 hora
def load_upstream_data(
    file_path: Union[str, st.runtime.uploaded_file_manager.UploadedFile] = "data/upstream.csv"
) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """
    Carga, valida y limpia datos Upstream (Campo/Extractora).
    
    Pipeline:
    1. Cargar archivo
    2. Validar columnas
    3. Limpiar valores numéricos
    4. Normalizar fechas
    5. Calcular variaciones
    
    Args:
        file_path: Ruta al archivo o UploadedFile
    
    Returns:
        Tuple[DataFrame procesado o None, mensaje de error o None]
    """
    # 1. Cargar archivo
    df, error = load_file(file_path)
    if error:
        return None, error
    
    # Normalizar nombres de columnas
    df.columns = [col.lower().strip().replace(' ', '_') for col in df.columns]
    
    # 2. Validar columnas
    is_valid, missing = validate_columns(df, 'upstream')
    if not is_valid:
        return None, f"Columnas faltantes en archivo Upstream: {', '.join(missing)}"
    
    # 3. Limpiar valores numéricos
    numeric_cols = [col for col in df.columns if col not in ['fecha', 'zona']]
    df = clean_numeric_values(df, numeric_cols)
    
    # 4. Normalizar fechas
    df = normalize_dates(df, 'fecha')
    
    # 5. Calcular variaciones
    df = calculate_variations(df)
    
    # Ordenar por fecha y zona
    df = df.sort_values(['fecha', 'zona']).reset_index(drop=True)
    
    return df, None


# =============================================================================
# 2.7 - FUNCIÓN INTEGRADA PARA DOWNSTREAM
# =============================================================================

@st.cache_data(ttl=3600)  # Cache por 1 hora
def load_downstream_data(
    file_path: Union[str, st.runtime.uploaded_file_manager.UploadedFile] = "data/downstream.csv"
) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """
    Carga, valida y limpia datos Downstream (Refinería/Productos).
    
    Pipeline:
    1. Cargar archivo
    2. Validar columnas
    3. Limpiar valores numéricos
    4. Normalizar fechas
    5. Calcular variaciones
    
    Args:
        file_path: Ruta al archivo o UploadedFile
    
    Returns:
        Tuple[DataFrame procesado o None, mensaje de error o None]
    """
    # 1. Cargar archivo
    df, error = load_file(file_path)
    if error:
        return None, error
    
    # Normalizar nombres de columnas
    df.columns = [col.lower().strip().replace(' ', '_') for col in df.columns]
    
    # 2. Validar columnas
    is_valid, missing = validate_columns(df, 'downstream')
    if not is_valid:
        return None, f"Columnas faltantes en archivo Downstream: {', '.join(missing)}"
    
    # 3. Limpiar valores numéricos
    numeric_cols = [col for col in df.columns if col not in ['fecha', 'refineria']]
    df = clean_numeric_values(df, numeric_cols)
    
    # 4. Normalizar fechas
    df = normalize_dates(df, 'fecha')
    
    # 5. Calcular variaciones
    df = calculate_variations(df)
    
    # Ordenar por fecha y refinería
    df = df.sort_values(['fecha', 'refineria']).reset_index(drop=True)
    
    return df, None


# =============================================================================
# 2.8 - FUNCIONES DE MANEJO DE ERRORES Y MENSAJES
# =============================================================================

def get_file_info(file_path: str) -> dict:
    """
    Obtiene información sobre un archivo.
    
    Args:
        file_path: Ruta al archivo
    
    Returns:
        Diccionario con información del archivo
    """
    info = {
        "exists": False,
        "size": 0,
        "modified": None,
        "error": None
    }
    
    try:
        if os.path.exists(file_path):
            info["exists"] = True
            info["size"] = os.path.getsize(file_path)
            info["modified"] = datetime.fromtimestamp(os.path.getmtime(file_path))
        else:
            info["error"] = f"El archivo no existe: {file_path}"
    except Exception as e:
        info["error"] = str(e)
    
    return info


def format_error_message(error_type: str, details: str = None) -> str:
    """
    Formatea mensajes de error para mostrar al usuario.
    
    Args:
        error_type: Tipo de error ('file_not_found', 'invalid_format', 'missing_columns', etc.)
        details: Detalles adicionales del error
    
    Returns:
        Mensaje de error formateado
    """
    messages = {
        "file_not_found": "📁 **Archivo no encontrado**\n\nVerifique que el archivo exista en la ubicación especificada.",
        "invalid_format": "📄 **Formato de archivo inválido**\n\nSolo se aceptan archivos CSV (.csv) y Excel (.xlsx)",
        "missing_columns": "📋 **Columnas faltantes**\n\nEl archivo no tiene todas las columnas requeridas.",
        "empty_file": "📭 **Archivo vacío**\n\nEl archivo no contiene datos.",
        "parse_error": "⚠️ **Error al procesar**\n\nNo se pudieron leer los datos del archivo.",
    }
    
    message = messages.get(error_type, f"❌ **Error**: {error_type}")
    
    if details:
        message += f"\n\n**Detalles:** {details}"
    
    return message


def display_data_summary(df: pd.DataFrame, title: str = "Resumen de Datos"):
    """
    Muestra un resumen del DataFrame cargado en Streamlit.
    
    Args:
        df: DataFrame a mostrar
        title: Título del resumen
    """
    st.subheader(title)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Registros", f"{len(df):,}")
    
    with col2:
        st.metric("Columnas", f"{len(df.columns)}")
    
    with col3:
        if 'fecha' in df.columns:
            fecha_min = df['fecha'].min()
            if pd.notna(fecha_min):
                st.metric("Fecha Inicio", fecha_min.strftime("%d/%m/%Y"))
    
    with col4:
        if 'fecha' in df.columns:
            fecha_max = df['fecha'].max()
            if pd.notna(fecha_max):
                st.metric("Fecha Fin", fecha_max.strftime("%d/%m/%Y"))


# =============================================================================
# FUNCIONES AUXILIARES DE FILTRADO
# =============================================================================

def filter_by_date_range(
    df: pd.DataFrame,
    start_date: datetime = None,
    end_date: datetime = None,
    date_column: str = 'fecha'
) -> pd.DataFrame:
    """
    Filtra DataFrame por rango de fechas.
    
    Args:
        df: DataFrame a filtrar
        start_date: Fecha inicial
        end_date: Fecha final
        date_column: Nombre de la columna de fecha
    
    Returns:
        DataFrame filtrado
    """
    df = df.copy()
    
    if date_column not in df.columns:
        return df
    
    if start_date:
        df = df[df[date_column] >= pd.Timestamp(start_date)]
    
    if end_date:
        df = df[df[date_column] <= pd.Timestamp(end_date)]
    
    return df


def filter_by_zones(
    df: pd.DataFrame,
    zones: List[str],
    zone_column: str = 'zona'
) -> pd.DataFrame:
    """
    Filtra DataFrame por zonas seleccionadas.
    
    Args:
        df: DataFrame a filtrar
        zones: Lista de zonas a incluir
        zone_column: Nombre de la columna de zona
    
    Returns:
        DataFrame filtrado
    """
    if not zones or zone_column not in df.columns:
        return df
    
    return df[df[zone_column].isin(zones)].copy()


def aggregate_by_period(
    df: pd.DataFrame,
    period: str = 'W',
    date_column: str = 'fecha',
    agg_columns: List[str] = None,
    agg_func: str = 'sum'
) -> pd.DataFrame:
    """
    Agrega datos por período (diario, semanal, mensual).
    
    Args:
        df: DataFrame a agregar
        period: 'D' (día), 'W' (semana), 'M' (mes), 'Y' (año)
        date_column: Columna de fecha
        agg_columns: Columnas a agregar (None = todas numéricas)
        agg_func: Función de agregación ('sum', 'mean', 'max', 'min')
    
    Returns:
        DataFrame agregado
    """
    df = df.copy()
    
    if date_column not in df.columns:
        return df
    
    # Asegurar que la fecha sea datetime
    df[date_column] = pd.to_datetime(df[date_column])
    
    # Columnas a agregar
    if agg_columns is None:
        agg_columns = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
    
    # Agrupar y agregar
    df_agg = df.groupby(pd.Grouper(key=date_column, freq=period))[agg_columns].agg(agg_func)
    df_agg = df_agg.reset_index()
    
    return df_agg

