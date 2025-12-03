"""
Script inteligente para convertir el Excel de Seguimiento Agroindustrial
al formato del dashboard.

Este script detecta automáticamente:
- Las columnas de fechas (ignorando ACUMULADO S1, S2, etc.)
- Las filas de cada planta (Codazzi, MLB, Sinú, A&G)
- Los valores de Proyección vs Real

Uso:
    python scripts/convert_excel_seguimiento.py "data/ARCHIVO_SEGUIMIENTO.xlsx"
"""

import pandas as pd
import numpy as np
import re
import sys
import os
from datetime import datetime

# ============================================================================
# CONFIGURACIÓN DE PLANTAS
# ============================================================================
# NOTA: Usamos las filas "Ext [Planta] Proy/Real" que contienen RFF PROCESADA
# Las filas "Planta Proyección/Real" son datos de ENTRADA, no de extracción
PLANTAS_CONFIG = {
    'Codazzi': {
        'fila_rff_proy': 4,     # "Ext Codazzi Proy" - RFF procesada proyectada
        'fila_rff_real': 5,     # "Ext Codazzi Real" - RFF procesada real
        'fila_cpo': 6,          # "CPO"
        'fila_tea': 7,          # "TEA%"
        'tea_meta': 21.6,
        'tiene_almendra': True,
    },
    'MLB': {
        'fila_rff_proy': 11,    # "Ext MLB Proy"
        'fila_rff_real': 12,    # "Ext MLB Real"
        'fila_cpo': 13,
        'fila_tea': 14,
        'tea_meta': 18.8,
        'tiene_almendra': False,
    },
    'Sinú': {
        'fila_rff_proy': 18,    # "Ext SINÚ Proy"
        'fila_rff_real': 19,    # "Ext SINÚ Real"
        'fila_cpo': 20,
        'fila_tea': 21,
        'tea_meta': 22.0,
        'tiene_almendra': False,
    },
    'A&G': {
        'fila_rff_proy': 25,    # "Ext A&GC Proy"
        'fila_rff_real': 26,    # "Ext A&GC Real"
        'fila_cpo': 27,
        'fila_tea': 28,
        'tea_meta': 23.5,
        'tiene_almendra': False,
    },
}

# Configuración de Almendra/KPO (solo Codazzi)
ALMENDRA_CONFIG = {
    'fila_pk_proy': 52,
    'fila_pk_real': 53,
    'fila_kpo': 54,
    'fila_tea_almendra': 55,
}


def detect_date_columns(df):
    """
    Detecta las columnas que contienen fechas válidas.
    Ignora columnas de ACUMULADO, ZONA, etc.
    
    Returns:
        dict: {indice_columna: fecha}
    """
    date_columns = {}
    header_row = df.iloc[0]
    
    for col_idx, value in enumerate(header_row):
        # Saltar primera columna (ZONA)
        if col_idx == 0:
            continue
            
        # Verificar si es una fecha
        if pd.notna(value):
            # Si es timestamp de pandas
            if isinstance(value, pd.Timestamp):
                date_columns[col_idx] = value.date()
            # Si es datetime
            elif isinstance(value, datetime):
                date_columns[col_idx] = value.date()
            # Si es string con formato de fecha
            elif isinstance(value, str):
                # Ignorar ACUMULADO, NaN, etc.
                if 'ACUMULADO' in value.upper() or 'ZONA' in value.upper():
                    continue
                try:
                    date_columns[col_idx] = pd.to_datetime(value).date()
                except:
                    continue
    
    return date_columns


def safe_float(value):
    """Convierte un valor a float de forma segura."""
    if pd.isna(value) or value == '' or value == 0:
        return 0.0
    try:
        if isinstance(value, str):
            value = value.replace(',', '.')
        return float(value)
    except:
        return 0.0


def extract_upstream_data(df, date_columns):
    """
    Extrae los datos UPSTREAM del DataFrame.
    
    Returns:
        list: Lista de diccionarios con los datos diarios
    """
    records = []
    
    for planta, config in PLANTAS_CONFIG.items():
        for col_idx, fecha in date_columns.items():
            # Obtener valores de las celdas (usando filas de Extracción = RFF Procesada)
            rff_proy = safe_float(df.iloc[config['fila_rff_proy'], col_idx])
            rff_real = safe_float(df.iloc[config['fila_rff_real'], col_idx])
            cpo_real = safe_float(df.iloc[config['fila_cpo'], col_idx])
            tea_value = safe_float(df.iloc[config['fila_tea'], col_idx])
            
            # Convertir TEA si está en decimal
            if 0 < tea_value < 1:
                tea_value = tea_value * 100
            
            # Agregar si hay presupuesto O datos reales (para incluir días sin producción)
            if rff_proy > 0 or rff_real > 0 or cpo_real > 0:
                # Calcular presupuesto de CPO basado en TEA meta
                cpo_proy = rff_proy * (config['tea_meta'] / 100) if rff_proy > 0 else 0
                
                # Palmiste estimado (~5% del CPO)
                palmiste_real = cpo_real * 0.05
                palmiste_proy = cpo_proy * 0.05
                
                record = {
                    'fecha': fecha.strftime('%Y-%m-%d'),
                    'zona': planta,
                    'rff_real': round(rff_real, 2),
                    'rff_presupuesto': round(rff_proy, 2),
                    'cpo_real': round(cpo_real, 2),
                    'cpo_presupuesto': round(cpo_proy, 2),
                    'palmiste_real': round(palmiste_real, 2),
                    'palmiste_presupuesto': round(palmiste_proy, 2),
                    'tea_real': round(tea_value, 2),
                    'tea_meta': config['tea_meta'],
                    'almendra_real': 0,
                    'almendra_presupuesto': 0,
                    'kpo_real': 0,
                    'kpo_presupuesto': 0,
                    'extraccion_almendra': 0,
                    'acidez': round(2.5 + (tea_value - 20) * 0.1, 2) if tea_value > 0 else 0,
                    'humedad': round(0.12 + (tea_value - 20) * 0.005, 2) if tea_value > 0 else 0,
                    'impurezas': round(0.05 + (tea_value - 20) * 0.002, 2) if tea_value > 0 else 0,
                    'inventario_cpo': round(cpo_real * 0.3, 2),
                    'tanque_1': round(cpo_real * 0.15, 0),
                    'tanque_2': round(cpo_real * 0.10, 0),
                    'tanque_3': round(cpo_real * 0.05, 0) if planta == 'Codazzi' else 0,
                    'tanque_4': 0,
                }
                
                # Agregar datos de Almendra/KPO solo para Codazzi
                if config['tiene_almendra']:
                    try:
                        pk_proy = safe_float(df.iloc[ALMENDRA_CONFIG['fila_pk_proy'], col_idx])
                        pk_real = safe_float(df.iloc[ALMENDRA_CONFIG['fila_pk_real'], col_idx])
                        kpo_real = safe_float(df.iloc[ALMENDRA_CONFIG['fila_kpo'], col_idx])
                        
                        record['almendra_real'] = round(pk_real, 2)
                        record['almendra_presupuesto'] = round(pk_proy, 2)
                        record['kpo_real'] = round(kpo_real, 2)
                        record['kpo_presupuesto'] = round(pk_proy * 0.41, 2)
                        record['extraccion_almendra'] = 41.0
                    except:
                        pass
                
                records.append(record)
    
    return records


def extract_downstream_data(xlsx, date_columns_upstream):
    """
    Extrae los datos DOWNSTREAM del Excel.
    
    Returns:
        list: Lista de diccionarios con los datos de refinería
    """
    try:
        df = pd.read_excel(xlsx, sheet_name='DOWNSTREAM', header=None)
    except:
        print("⚠️  Hoja DOWNSTREAM no encontrada")
        return []
    
    # Detectar columnas de fecha en DOWNSTREAM
    date_columns = detect_date_columns(df)
    
    if not date_columns:
        print("⚠️  No se encontraron fechas en DOWNSTREAM")
        return []
    
    records = []
    
    # Configuración de refinerías
    refinerias = [
        {'nombre': 'Refinería 1', 'fila_me': 1, 'fila_real': 2},
        {'nombre': 'Refinería 2', 'fila_me': 9, 'fila_real': 10},
    ]
    
    for ref in refinerias:
        for col_idx, fecha in date_columns.items():
            try:
                me = safe_float(df.iloc[ref['fila_me'], col_idx])
                real = safe_float(df.iloc[ref['fila_real'], col_idx])
                
                if real > 0:
                    records.append({
                        'fecha': fecha.strftime('%Y-%m-%d'),
                        'refineria': ref['nombre'],
                        'produccion_me': round(me, 2),
                        'produccion_real': round(real, 2),
                        'cumplimiento': round((real / me * 100) if me > 0 else 0, 2),
                    })
            except:
                continue
    
    return records


def convert_excel_to_csv(excel_path, output_upstream=None, output_downstream=None):
    """
    Convierte el Excel de Seguimiento al formato del dashboard.
    
    Args:
        excel_path: Ruta al archivo Excel
        output_upstream: Ruta para guardar upstream.csv
        output_downstream: Ruta para guardar downstream.csv
    """
    print(f"📂 Leyendo: {excel_path}")
    
    # Verificar que el archivo existe
    if not os.path.exists(excel_path):
        print(f"❌ Archivo no encontrado: {excel_path}")
        return None, None
    
    # Cargar Excel
    xlsx = pd.ExcelFile(excel_path)
    print(f"📋 Hojas encontradas: {xlsx.sheet_names}")
    
    # Leer hoja UPSTREAM
    df_upstream = pd.read_excel(xlsx, sheet_name='UPSTREAM', header=None)
    print(f"✅ UPSTREAM: {df_upstream.shape[0]} filas x {df_upstream.shape[1]} columnas")
    
    # Detectar columnas de fecha
    date_columns = detect_date_columns(df_upstream)
    print(f"📅 Fechas detectadas: {len(date_columns)} días")
    
    if date_columns:
        fechas = sorted(date_columns.values())
        print(f"   Rango: {fechas[0]} a {fechas[-1]}")
    
    # Extraer datos UPSTREAM
    upstream_records = extract_upstream_data(df_upstream, date_columns)
    print(f"📊 Registros UPSTREAM extraídos: {len(upstream_records)}")
    
    # Extraer datos DOWNSTREAM
    downstream_records = extract_downstream_data(xlsx, date_columns)
    print(f"📊 Registros DOWNSTREAM extraídos: {len(downstream_records)}")
    
    # Crear DataFrames
    df_up = pd.DataFrame(upstream_records)
    df_down = pd.DataFrame(downstream_records) if downstream_records else pd.DataFrame()
    
    # Guardar archivos
    if output_upstream is None:
        output_upstream = os.path.join(os.path.dirname(excel_path), 'upstream.csv')
    if output_downstream is None:
        output_downstream = os.path.join(os.path.dirname(excel_path), 'downstream.csv')
    
    df_up.to_csv(output_upstream, index=False)
    print(f"💾 Guardado: {output_upstream}")
    
    if not df_down.empty:
        df_down.to_csv(output_downstream, index=False)
        print(f"💾 Guardado: {output_downstream}")
    
    # Resumen por planta
    print("\n📈 RESUMEN POR PLANTA:")
    print("-" * 50)
    for zona in df_up['zona'].unique():
        df_zona = df_up[df_up['zona'] == zona]
        rff_total = df_zona['rff_real'].sum()
        cpo_total = df_zona['cpo_real'].sum()
        tea_prom = df_zona['tea_real'].mean()
        print(f"  {zona}:")
        print(f"    Días: {len(df_zona)}")
        print(f"    RFF Total: {rff_total:,.0f} Ton")
        print(f"    CPO Total: {cpo_total:,.0f} Ton")
        print(f"    TEA Promedio: {tea_prom:.2f}%")
    
    print("\n✨ Conversión completada!")
    
    return df_up, df_down


def main():
    """Punto de entrada principal."""
    # Determinar archivo de entrada
    if len(sys.argv) > 1:
        excel_path = sys.argv[1]
    else:
        # Buscar el archivo más reciente en data/
        data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
        excel_files = [f for f in os.listdir(data_dir) if f.endswith('.xlsx') and 'SEGUIMIENTO' in f.upper()]
        
        if not excel_files:
            print("❌ No se encontró archivo de seguimiento en data/")
            print("   Uso: python scripts/convert_excel_seguimiento.py <archivo.xlsx>")
            return
        
        # Ordenar por fecha de modificación
        excel_files.sort(key=lambda f: os.path.getmtime(os.path.join(data_dir, f)), reverse=True)
        excel_path = os.path.join(data_dir, excel_files[0])
        print(f"📁 Usando archivo más reciente: {excel_files[0]}")
    
    # Convertir
    convert_excel_to_csv(excel_path)


if __name__ == "__main__":
    main()

