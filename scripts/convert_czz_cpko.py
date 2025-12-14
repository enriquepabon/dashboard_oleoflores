"""
Script para convertir el archivo CZZ_CPKO Excel al formato upstream del dashboard.

Este archivo contiene datos detallados de la PLANTA EXPELLER CODAZZI:
- Almendra de Palma Procesada (Kg)
- Producción CPKO - Aceite Crudo de Palmiste (Kg)
- Inventario CPKO
- % Extracción

Uso:
    python scripts/convert_czz_cpko.py
    python scripts/convert_czz_cpko.py "ruta/al/archivo.xlsx"
"""

import pandas as pd
import numpy as np
import sys
import os
from datetime import datetime

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

CPKO_CONFIG = {
    'sheet_name': 'Base de Datos',
    'data_start_row': 2,  # Fila donde empiezan los datos (0-indexed)
    'columns': {
        'fecha': 0,              # Información/Fecha
        'inv_inicial': 1,        # Inv. Inicial CPKO
        'despachos': 2,          # Despachos
        'produccion_cpko': 4,    # Producción CPKO (col 4)
        'almendra_procesada': 6, # Almendra Procesada (col 6)
    },
}

# TEA meta para almendra/CPKO (meta estándar de extracción)
CPKO_EXTRACTION_META = 41.0  # 41% extracción de aceite de almendra


def safe_float(value):
    """Convierte un valor a float de forma segura."""
    if pd.isna(value) or value == '' or value == 0:
        return 0.0
    try:
        if isinstance(value, str):
            value = value.replace(',', '.')
        val = float(value)
        # Ignorar valores absurdos (negativos grandes = errores de fórmula)
        if val < -1000000:
            return 0.0
        return val
    except:
        return 0.0


def extract_cpko_data(file_path: str) -> list:
    """
    Extrae los datos de CPKO del archivo Excel.
    
    Args:
        file_path: Ruta al archivo Excel
    
    Returns:
        list: Lista de diccionarios con datos de almendra/CPKO
    """
    records = []
    config = CPKO_CONFIG
    
    try:
        df = pd.read_excel(file_path, sheet_name=config['sheet_name'], header=None)
        print(f"   📊 Hoja '{config['sheet_name']}': {len(df)} filas")
    except Exception as e:
        print(f"   ⚠️ Error leyendo hoja: {e}")
        return records
    
    cols = config['columns']
    
    # Iterar desde la fila de datos
    for i in range(config['data_start_row'], len(df)):
        row = df.iloc[i]
        
        # Obtener fecha
        fecha_raw = row.iloc[cols['fecha']]
        
        if pd.isna(fecha_raw):
            continue
        
        try:
            if isinstance(fecha_raw, pd.Timestamp):
                fecha = fecha_raw.date()
            elif isinstance(fecha_raw, datetime):
                fecha = fecha_raw.date()
            else:
                fecha = pd.to_datetime(fecha_raw).date()
        except:
            continue
        
        # Extraer valores
        inv_inicial = safe_float(row.iloc[cols['inv_inicial']])
        despachos = safe_float(row.iloc[cols['despachos']])
        produccion_cpko = safe_float(row.iloc[cols['produccion_cpko']])
        almendra_procesada = safe_float(row.iloc[cols['almendra_procesada']])
        
        # Solo agregar si hay datos válidos
        if almendra_procesada > 0 or produccion_cpko > 0 or inv_inicial > 0:
            
            # Calcular % extracción
            if almendra_procesada > 0:
                extraccion = (produccion_cpko / almendra_procesada) * 100
            else:
                extraccion = 0
            
            # Convertir de kg a toneladas
            almendra_ton = almendra_procesada / 1000
            cpko_ton = produccion_cpko / 1000
            inv_ton = inv_inicial / 1000
            
            record = {
                'fecha': fecha.strftime('%Y-%m-%d'),
                'zona': 'Codazzi',  # Almendra solo se procesa en Codazzi
                'almendra_real': round(almendra_ton, 2),
                'almendra_presupuesto': round(almendra_ton, 2),  # Usar real como ppto
                'kpo_real': round(cpko_ton, 2),
                'kpo_presupuesto': round(almendra_ton * (CPKO_EXTRACTION_META / 100), 2),
                'extraccion_almendra': round(extraccion, 2),
                'inventario_cpko': round(inv_ton, 2),
            }
            records.append(record)
    
    return records


def merge_cpko_with_upstream(cpko_records: list, upstream_path: str) -> pd.DataFrame:
    """
    Fusiona datos de CPKO con el archivo upstream existente.
    
    Actualiza los campos de almendra/kpo en los registros de Codazzi.
    
    Args:
        cpko_records: Lista de registros CPKO extraídos
        upstream_path: Ruta al archivo upstream.csv
    
    Returns:
        DataFrame actualizado
    """
    if not cpko_records:
        print("   ⚠️ Sin datos CPKO para fusionar")
        if os.path.exists(upstream_path):
            return pd.read_csv(upstream_path)
        return pd.DataFrame()
    
    df_cpko = pd.DataFrame(cpko_records)
    df_cpko['fecha'] = pd.to_datetime(df_cpko['fecha'])
    
    # Cargar upstream existente
    if not os.path.exists(upstream_path):
        print("   ⚠️ Archivo upstream.csv no existe")
        return pd.DataFrame()
    
    df_upstream = pd.read_csv(upstream_path)
    df_upstream['fecha'] = pd.to_datetime(df_upstream['fecha'])
    
    # Obtener rango de fechas CPKO
    fecha_min = df_cpko['fecha'].min()
    fecha_max = df_cpko['fecha'].max()
    
    print(f"   📅 Rango CPKO: {fecha_min.strftime('%Y-%m-%d')} a {fecha_max.strftime('%Y-%m-%d')}")
    print(f"   📊 {len(df_cpko)} registros CPKO a fusionar")
    
    # Crear índice para merge
    df_cpko = df_cpko.set_index(['fecha', 'zona'])
    
    # Actualizar registros de Codazzi dentro del rango
    mask = (
        (df_upstream['zona'] == 'Codazzi') &
        (df_upstream['fecha'] >= fecha_min) &
        (df_upstream['fecha'] <= fecha_max)
    )
    
    registros_actualizados = 0
    for idx in df_upstream[mask].index:
        row_fecha = df_upstream.loc[idx, 'fecha']
        row_zona = df_upstream.loc[idx, 'zona']
        
        try:
            cpko_row = df_cpko.loc[(row_fecha, row_zona)]
            
            # Actualizar campos de almendra/CPKO
            df_upstream.loc[idx, 'almendra_real'] = cpko_row['almendra_real']
            df_upstream.loc[idx, 'almendra_presupuesto'] = cpko_row['almendra_presupuesto']
            df_upstream.loc[idx, 'kpo_real'] = cpko_row['kpo_real']
            df_upstream.loc[idx, 'kpo_presupuesto'] = cpko_row['kpo_presupuesto']
            df_upstream.loc[idx, 'extraccion_almendra'] = cpko_row['extraccion_almendra']
            
            registros_actualizados += 1
        except KeyError:
            # No hay datos CPKO para esta fecha
            continue
    
    print(f"   ✅ {registros_actualizados} registros de Codazzi actualizados con datos CPKO")
    
    # Convertir fecha de vuelta a string
    df_upstream['fecha'] = df_upstream['fecha'].dt.strftime('%Y-%m-%d')
    
    return df_upstream


def convert_cpko_to_csv(file_path: str, upstream_path: str = None) -> pd.DataFrame:
    """
    Convierte el archivo CZZ_CPKO Excel y fusiona con upstream.
    
    Args:
        file_path: Ruta al archivo Excel CZZ_CPKO
        upstream_path: Ruta al archivo upstream.csv
    
    Returns:
        DataFrame actualizado
    """
    print(f"\n{'='*60}")
    print(f"🔄 CONVERTIR CZZ_CPKO - ALMENDRA/CPKO")
    print(f"{'='*60}")
    print(f"📂 Archivo: {os.path.basename(file_path)}")
    
    if not os.path.exists(file_path):
        print(f"❌ Archivo no encontrado: {file_path}")
        return pd.DataFrame()
    
    # Definir ruta upstream
    if upstream_path is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        upstream_path = os.path.join(base_dir, 'data', 'upstream.csv')
    
    # Extraer datos CPKO
    print(f"\n📍 Extrayendo datos CPKO (Expeller Codazzi)...")
    cpko_records = extract_cpko_data(file_path)
    
    if cpko_records:
        print(f"   ✅ {len(cpko_records)} registros extraídos")
        
        # Mostrar resumen
        df_temp = pd.DataFrame(cpko_records)
        almendra_total = df_temp['almendra_real'].sum()
        cpko_total = df_temp['kpo_real'].sum()
        ext_prom = df_temp['extraccion_almendra'].mean()
        print(f"   📊 Almendra: {almendra_total:,.1f} Ton, CPKO: {cpko_total:,.1f} Ton, Ext: {ext_prom:.1f}%")
    else:
        print(f"   ⚠️ Sin datos extraídos")
        return pd.DataFrame()
    
    # Fusionar con upstream
    print(f"\n📚 Fusionando con upstream.csv...")
    df = merge_cpko_with_upstream(cpko_records, upstream_path)
    
    if not df.empty:
        # Guardar
        df.to_csv(upstream_path, index=False)
        
        print(f"\n{'='*60}")
        print(f"✅ CONVERSIÓN COMPLETADA")
        print(f"{'='*60}")
        print(f"💾 Guardado: {upstream_path}")
        print(f"📊 Total registros: {len(df)}")
    
    return df


def main():
    """Punto de entrada principal."""
    # Determinar archivo de entrada
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        # Buscar archivo por patrón
        data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
        pattern_files = [f for f in os.listdir(data_dir) if 'CZZ' in f and 'CPKO' in f and f.endswith('.xlsx')]
        
        if not pattern_files:
            # Fallback a nombre específico
            file_path = os.path.join(data_dir, '12_Dic_ 2025_CZZ_Inv_y_Extracción_CPKO.xlsx')
        else:
            pattern_files.sort(key=lambda f: os.path.getmtime(os.path.join(data_dir, f)), reverse=True)
            file_path = os.path.join(data_dir, pattern_files[0])
    
    print(f"📁 Usando archivo: {os.path.basename(file_path)}")
    
    # Convertir
    convert_cpko_to_csv(file_path)


if __name__ == "__main__":
    main()
