"""
Script para convertir el archivo GEO_CPO Excel al formato upstream del dashboard.

Este archivo contiene datos detallados diarios de:
- Extractora Sinú (hoja: BD Sinu)
- Extractora MLB (hoja: Base de Datos)

Datos incluidos:
- Inventario Inicial/Final (kg)
- Despachos (kg)
- Producción CPO (kg)
- RFF Procesada (kg)
- % Extracción (TEA)

Uso:
    python scripts/convert_geo_cpo.py
    python scripts/convert_geo_cpo.py "ruta/al/archivo.xlsx"
"""

import pandas as pd
import numpy as np
import sys
import os
from datetime import datetime

# ============================================================================
# CONFIGURACIÓN DE HOJAS POR PLANTA
# ============================================================================

# Estructura de cada hoja: Plantas con su hoja y columnas
PLANTAS_GEO = {
    'Sinú': {
        'sheet_name': 'BD Sinu',
        'header_row': 2,  # Fila con headers (0-indexed)
        'data_start_row': 4,  # Fila donde empiezan los datos (fila 3 tiene "Información")
        'columns': {
            'fecha': 0,           # Información/Fecha
            'inv_inicial': 1,     # Inv. Inicial
            'despachos': 2,       # Despachos
            'produccion_cpo': 4,  # Producción CPO (columna 4, no 3 que es acumulado)
            'rff_procesada': 6,   # RFF Procesada (columna 6, no 5 que es acumulado)
            'extraccion': 8,      # Extracción (columna 8, no 7 que es acumulado)
            'inv_final': 10,      # Inv. Final
        },
        'tea_meta': 22.0,  # TEA meta para Sinú
    },
    'MLB': {
        'sheet_name': 'Base de Datos',
        'header_row': 2,
        'data_start_row': 4,  # Fila donde empiezan los datos (fila 3 tiene "Información")
        'columns': {
            'fecha': 0,
            'inv_inicial': 1,
            'despachos': 2,
            'produccion_cpo': 4,
            'rff_procesada': 6,
            'extraccion': 8,
            'inv_final': 10,
        },
        'tea_meta': 18.6,
    },
    'A&G': {
        'sheet_name': 'Base de Datos',
        'header_row': 2,
        'data_start_row': 4,
        'columns': {
            'fecha': 0,           # Fecha compartida en columna 0
            'inv_inicial': 15,    # Inv. Inicial A&G
            'despachos': 16,      # Despachos
            'produccion_cpo': 18, # Producción CPO
            'rff_procesada': 20,  # RFF Procesada
            'extraccion': 22,     # Extracción
            'inv_final': 24,      # Inv. Final
        },
        'tea_meta': 23.5,
    },
    'Codazzi': {
        'sheet_name': 'Base de Datos',
        'header_row': 2,
        'data_start_row': 4,
        'columns': {
            'fecha': 0,           # Fecha compartida en columna 0
            'inv_inicial': 29,    # Inv. Inicial Codazzi
            'despachos': 30,      # Compra (usamos como despachos inverso)
            'produccion_cpo': 33, # Producción CPO
            'rff_procesada': 35,  # RFF Procesada
            'extraccion': 37,     # Extracción
            'inv_final': 39,      # Inv. Final
        },
        'tea_meta': 21.6,
    },
}


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


def extract_plant_data(file_path: str, planta: str, config: dict) -> list:
    """
    Extrae los datos de una planta específica.
    
    Args:
        file_path: Ruta al archivo Excel
        planta: Nombre de la planta
        config: Configuración de columnas para la planta
    
    Returns:
        list: Lista de diccionarios con los datos diarios
    """
    records = []
    
    try:
        df = pd.read_excel(file_path, sheet_name=config['sheet_name'], header=None)
        print(f"   📊 Hoja '{config['sheet_name']}': {len(df)} filas")
    except Exception as e:
        print(f"   ⚠️ Error leyendo hoja {config['sheet_name']}: {e}")
        return records
    
    cols = config['columns']
    tea_meta = config['tea_meta']
    
    # Iterar desde la fila de datos
    for i in range(config['data_start_row'], len(df)):
        row = df.iloc[i]
        
        # Obtener fecha
        fecha_raw = row.iloc[cols['fecha']]
        
        # Validar que es una fecha válida
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
        produccion_cpo = safe_float(row.iloc[cols['produccion_cpo']])
        rff_procesada = safe_float(row.iloc[cols['rff_procesada']])
        extraccion = safe_float(row.iloc[cols['extraccion']])
        inv_final = safe_float(row.iloc[cols['inv_final']])
        
        # Convertir extracción de decimal a porcentaje si es necesario
        if 0 < extraccion < 1:
            extraccion = extraccion * 100
        
        # Solo agregar si hay datos (RFF o CPO > 0, o hay inventario)
        if rff_procesada > 0 or produccion_cpo > 0 or inv_inicial > 0:
            
            # Convertir de kg a toneladas
            rff_ton = rff_procesada / 1000
            cpo_ton = produccion_cpo / 1000
            inv_inicial_ton = inv_inicial / 1000
            inv_final_ton = inv_final / 1000
            despachos_ton = despachos / 1000
            
            # Calcular presupuestos (basado en TEA meta)
            rff_ppto = rff_ton  # Asumir mismo RFF como presupuesto
            cpo_ppto = rff_ton * (tea_meta / 100)
            
            # Palmiste estimado (~5% del RFF)
            palmiste_real = rff_ton * 0.05
            palmiste_ppto = rff_ppto * 0.05
            
            record = {
                'fecha': fecha.strftime('%Y-%m-%d'),
                'zona': planta,
                'rff_real': round(rff_ton, 2),
                'rff_presupuesto': round(rff_ppto, 2),
                'cpo_real': round(cpo_ton, 2),
                'cpo_presupuesto': round(cpo_ppto, 2),
                'palmiste_real': round(palmiste_real, 2),
                'palmiste_presupuesto': round(palmiste_ppto, 2),
                'tea_real': round(extraccion, 2),
                'tea_meta': tea_meta,
                'almendra_real': 0,
                'almendra_presupuesto': 0,
                'kpo_real': 0,
                'kpo_presupuesto': 0,
                'extraccion_almendra': 0,
                'acidez': 0,
                'humedad': 0,
                'impurezas': 0,
                'inventario_cpo': round(inv_final_ton, 2),
                'tanque_1': 0,
                'tanque_2': 0,
                'tanque_3': 0,
                'tanque_4': 0,
            }
            records.append(record)
    
    return records


# ============================================================================
# CONFIGURACIÓN DE TANQUES (HOJAS DE MEDIDAS)
# ============================================================================

TANQUES_CONFIG = {
    'Sinú': {
        'sheet_name': 'Medidas_Sinu',
        'fecha_col': 1,
        'data_start_row': 4,
        'tanques': {
            'tanque_1': 6,   # Kg
            'tanque_2': 11,  # Kg
        },
        'capacidades': {'TK 1': 180, 'TK 2': 460},  # Toneladas
    },
    'MLB': {
        'sheet_name': 'Medidas_Tn_Alm',
        'fecha_col': 1,
        'data_start_row': 4,
        'tanques': {
            'tanque_1': 6,   # Kg
            'tanque_2': 11,  # Kg
        },
        'capacidades': {'TK 1': 200, 'TK 2': 500},
    },
    'A&G': {
        'sheet_name': 'Medidas_Tn_Alm',
        'fecha_col': 1,
        'data_start_row': 4,
        'tanques': {
            'tanque_1': 17,  # Kg
            'tanque_2': 22,  # Kg
        },
        'capacidades': {'TK 1': 2004, 'TK 2': 2000},
    },
    'Codazzi': {
        'sheet_name': 'Medidas_Tn_Alm',
        'fecha_col': 1,
        'data_start_row': 4,
        'tanques': {
            'tanque_1': 28,  # TK2 -> tanque_1 (Kg)
            'tanque_2': 33,  # TK3 -> tanque_2 (Kg)
            'tanque_3': 38,  # TK4 -> tanque_3 (Kg)
            'tanque_4': 43,  # TK6 -> tanque_4 (Kg)
        },
        'capacidades': {'TK 2': 1200, 'TK 3': 1200, 'TK 4': 1200, 'TK 6': 1200},
    },
}


def extract_tank_data(file_path: str) -> dict:
    """
    Extrae datos de tanques de las hojas Medidas_Sinu y Medidas_Tn_Alm.
    
    Returns:
        dict: {(fecha, zona): {'tanque_1': valor, 'tanque_2': valor, ...}}
    """
    tank_data = {}
    
    for planta, config in TANQUES_CONFIG.items():
        try:
            df = pd.read_excel(file_path, sheet_name=config['sheet_name'], header=None)
        except Exception as e:
            print(f"   ⚠️ Error leyendo hoja {config['sheet_name']}: {e}")
            continue
        
        for i in range(config['data_start_row'], len(df)):
            fecha_raw = df.iloc[i, config['fecha_col']]
            
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
            
            fecha_str = fecha.strftime('%Y-%m-%d')
            key = (fecha_str, planta)
            
            # Extraer valores de tanques (en kg -> convertir a toneladas)
            tank_data[key] = {}
            for tank_name, col_idx in config['tanques'].items():
                valor_kg = safe_float(df.iloc[i, col_idx])
                tank_data[key][tank_name] = round(valor_kg / 1000, 2)  # kg -> ton
    
    return tank_data


def merge_tank_data(records: list, tank_data: dict) -> list:
    """
    Fusiona datos de tanques con los registros existentes.
    """
    for record in records:
        key = (record['fecha'], record['zona'])
        if key in tank_data:
            for tank_name, valor in tank_data[key].items():
                record[tank_name] = valor
    
    return records


# ============================================================================
# CONFIGURACIÓN DE CALIDAD (HOJA Calidad Tnk)
# ============================================================================

CALIDAD_CONFIG = {
    'MLB': {
        'sheet_name': 'Calidad Tnk',
        'fecha_col': 0,
        'data_start_row': 4,
        'tanques': {
            'TK1': {'acidez': 1, 'humedad': 2, 'impurezas': 3, 'h_i': 4},
            'TK2': {'acidez': 5, 'humedad': 6, 'impurezas': 7, 'h_i': 8},
        }
    },
    'A&G': {
        'sheet_name': 'Calidad Tnk',
        'fecha_col': 0,
        'data_start_row': 4,
        'tanques': {
            'TK1': {'acidez': 9, 'humedad': 10, 'impurezas': 11, 'h_i': 12},
            'TK2': {'acidez': 13, 'humedad': 14, 'impurezas': 15, 'h_i': 16},
        }
    },
    'Codazzi': {
        'sheet_name': 'Calidad Tnk',
        'fecha_col': 0,
        'data_start_row': 4,
        'tanques': {
            'TK2': {'acidez': 17, 'humedad': 18, 'impurezas': 19, 'h_i': 20},
            'TK3': {'acidez': 21, 'humedad': 22, 'impurezas': 23, 'h_i': 24},
            'TK4': {'acidez': 25, 'humedad': 26, 'impurezas': 27, 'h_i': 28},
            'TK6': {'acidez': 29, 'humedad': 30, 'impurezas': 31, 'h_i': 32},
        }
    },
    'Sinú': {
        'sheet_name': 'Calidad Tnk',
        'fecha_col': 0,
        'data_start_row': 4,
        'tanques': {
            'TK1': {'acidez': 33, 'humedad': 34, 'impurezas': 35, 'h_i': 36},
            'TK2': {'acidez': 37, 'humedad': 38, 'impurezas': 39, 'h_i': 40},
        }
    },
}


def extract_quality_data(file_path: str) -> dict:
    """
    Extrae datos de calidad de la hoja Calidad Tnk.
    
    Returns:
        dict: {(fecha, zona): {'acidez': valor_promedio, 'humedad': ..., 'impurezas': ..., 'h_i': ...}}
    """
    quality_data = {}
    
    try:
        df = pd.read_excel(file_path, sheet_name='Calidad Tnk', header=None)
    except Exception as e:
        print(f"   ⚠️ Error leyendo hoja Calidad Tnk: {e}")
        return quality_data
    
    for planta, config in CALIDAD_CONFIG.items():
        for i in range(config['data_start_row'], len(df)):
            fecha_raw = df.iloc[i, config['fecha_col']]
            
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
            
            fecha_str = fecha.strftime('%Y-%m-%d')
            key = (fecha_str, planta)
            
            # Promediar calidad de todos los tanques de la planta
            acidez_vals = []
            humedad_vals = []
            impurezas_vals = []
            h_i_vals = []
            
            for tk_name, cols in config['tanques'].items():
                a = safe_float(df.iloc[i, cols['acidez']])
                h = safe_float(df.iloc[i, cols['humedad']])
                imp = safe_float(df.iloc[i, cols['impurezas']])
                hi = safe_float(df.iloc[i, cols['h_i']])
                
                if a > 0:  # Solo incluir si hay datos
                    acidez_vals.append(a)
                    humedad_vals.append(h)
                    impurezas_vals.append(imp)
                    h_i_vals.append(hi)
            
            if acidez_vals:
                quality_data[key] = {
                    'acidez': round(sum(acidez_vals) / len(acidez_vals), 2),
                    'humedad': round(sum(humedad_vals) / len(humedad_vals), 2),
                    'impurezas': round(sum(impurezas_vals) / len(impurezas_vals), 3),
                    'h_i': round(sum(h_i_vals) / len(h_i_vals), 2),
                }
    
    return quality_data


def merge_quality_data(records: list, quality_data: dict) -> list:
    """
    Fusiona datos de calidad con los registros existentes.
    """
    for record in records:
        key = (record['fecha'], record['zona'])
        if key in quality_data:
            record['acidez'] = quality_data[key]['acidez']
            record['humedad'] = quality_data[key]['humedad']
            record['impurezas'] = quality_data[key]['impurezas']
            # H+I se calcula como humedad + impurezas si no está en los datos
    
    return records


def merge_with_existing_data(df_new: pd.DataFrame, csv_path: str, 
                             plantas_to_update: list) -> pd.DataFrame:
    """
    Combina los nuevos datos con el histórico existente.
    
    Solo actualiza las plantas especificadas (Sinú, MLB), preservando
    datos de otras plantas (Codazzi, A&G) del archivo existente.
    
    Args:
        df_new: DataFrame con los nuevos datos
        csv_path: Ruta al archivo CSV histórico
        plantas_to_update: Lista de plantas a actualizar
    
    Returns:
        DataFrame combinado
    """
    if df_new.empty:
        return df_new
    
    # Obtener rango de fechas de los nuevos datos
    df_new['fecha'] = pd.to_datetime(df_new['fecha'])
    fecha_min = df_new['fecha'].min()
    fecha_max = df_new['fecha'].max()
    
    if not os.path.exists(csv_path):
        print(f"   📋 Sin histórico previo, creando nuevo archivo")
        df_new['fecha'] = df_new['fecha'].dt.strftime('%Y-%m-%d')
        return df_new
    
    try:
        df_historico = pd.read_csv(csv_path)
        df_historico['fecha'] = pd.to_datetime(df_historico['fecha'])
        
        registros_antes = len(df_historico)
        
        # Separar datos que NO se actualizan (otras plantas + fechas fuera del rango)
        mask_keep = (
            (~df_historico['zona'].isin(plantas_to_update)) |  # Otras plantas
            (df_historico['fecha'] < fecha_min) |              # Fechas anteriores
            (df_historico['fecha'] > fecha_max)                # Fechas posteriores
        )
        
        df_preserved = df_historico[mask_keep]
        registros_eliminados = registros_antes - len(df_preserved)
        
        print(f"   📋 Histórico: {registros_antes} registros")
        print(f"   🔄 Actualizando {registros_eliminados} registros de {', '.join(plantas_to_update)}")
        
        # Combinar
        df_combined = pd.concat([df_preserved, df_new], ignore_index=True)
        
    except Exception as e:
        print(f"   ⚠️ Error leyendo histórico ({e}), usando solo datos nuevos")
        df_combined = df_new
    
    # Ordenar por fecha y zona
    df_combined = df_combined.sort_values(['fecha', 'zona']).reset_index(drop=True)
    df_combined['fecha'] = df_combined['fecha'].dt.strftime('%Y-%m-%d')
    
    return df_combined


def convert_geo_cpo_to_csv(file_path: str, output_path: str = None) -> pd.DataFrame:
    """
    Convierte el archivo GEO_CPO Excel al formato upstream del dashboard.
    
    Args:
        file_path: Ruta al archivo Excel GEO_CPO
        output_path: Ruta de salida para upstream.csv (opcional)
    
    Returns:
        DataFrame con los datos procesados
    """
    print(f"\n{'='*60}")
    print(f"🔄 CONVERTIR GEO_CPO A UPSTREAM")
    print(f"{'='*60}")
    print(f"📂 Archivo: {os.path.basename(file_path)}")
    
    if not os.path.exists(file_path):
        print(f"❌ Archivo no encontrado: {file_path}")
        return pd.DataFrame()
    
    # Recopilar todos los registros
    all_records = []
    plantas_procesadas = []
    
    for planta, config in PLANTAS_GEO.items():
        print(f"\n📍 Procesando {planta}...")
        records = extract_plant_data(file_path, planta, config)
        
        if records:
            all_records.extend(records)
            plantas_procesadas.append(planta)
            print(f"   ✅ {len(records)} registros extraídos")
        else:
            print(f"   ⚠️ Sin datos para {planta}")
    
    if not all_records:
        print("\n❌ No se extrajeron datos")
        return pd.DataFrame()
    
    # Extraer datos de tanques
    print(f"\n📊 Extrayendo niveles de tanques...")
    tank_data = extract_tank_data(file_path)
    all_records = merge_tank_data(all_records, tank_data)
    print(f"   ✅ Datos de tanques fusionados para {len(tank_data)} registros")
    
    # Extraer datos de calidad
    print(f"\n🔬 Extrayendo calidad del aceite...")
    quality_data = extract_quality_data(file_path)
    all_records = merge_quality_data(all_records, quality_data)
    print(f"   ✅ Datos de calidad fusionados para {len(quality_data)} registros")
    
    # Crear DataFrame
    df = pd.DataFrame(all_records)
    
    # Definir ruta de salida
    if output_path is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        output_path = os.path.join(base_dir, 'data', 'upstream.csv')
    
    # Merge con histórico
    print(f"\n📚 Procesando histórico...")
    df = merge_with_existing_data(df, output_path, plantas_procesadas)
    
    # Guardar
    df.to_csv(output_path, index=False)
    
    # Resumen
    print(f"\n{'='*60}")
    print(f"✅ CONVERSIÓN COMPLETADA")
    print(f"{'='*60}")
    print(f"💾 Guardado: {output_path}")
    print(f"📊 Total registros: {len(df)}")
    
    print(f"\n📈 RESUMEN POR PLANTA:")
    for zona in df['zona'].unique():
        df_zona = df[df['zona'] == zona]
        rff_total = df_zona['rff_real'].sum()
        cpo_total = df_zona['cpo_real'].sum()
        tea_prom = df_zona['tea_real'].mean()
        print(f"  {zona}: RFF={rff_total:,.0f} Ton, CPO={cpo_total:,.0f} Ton, TEA={tea_prom:.1f}%")
    
    return df


def main():
    """Punto de entrada principal."""
    # Determinar archivo de entrada
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        # Buscar archivo por patrón
        data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
        pattern_files = [f for f in os.listdir(data_dir) if 'GEO_CPO' in f and f.endswith('.xlsx')]
        
        if not pattern_files:
            # Fallback a nombre específico
            file_path = os.path.join(data_dir, '12_Dic_2025_GEO_CPO_Inv_y Extr.xlsx')
        else:
            # Usar el más reciente
            pattern_files.sort(key=lambda f: os.path.getmtime(os.path.join(data_dir, f)), reverse=True)
            file_path = os.path.join(data_dir, pattern_files[0])
    
    print(f"📁 Usando archivo: {os.path.basename(file_path)}")
    
    # Convertir
    convert_geo_cpo_to_csv(file_path)


if __name__ == "__main__":
    main()
