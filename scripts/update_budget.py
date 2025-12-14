#!/usr/bin/env python3
"""
Script para extraer datos de presupuesto (ME) del archivo de planeación.
Actualiza upstream.csv con los valores ME correctos día a día.
"""

import pandas as pd
import os
from datetime import datetime


# Configuración del mapeo de plantas
PLANTAS_ME = {
    'Codazzi': {'rff_row': 1, 'cpo_row': 2, 'pk_row': 13, 'pk_cpo_row': 14},
    'MLB': {'rff_row': 3, 'cpo_row': 4, 'pk_row': 15, 'pk_cpo_row': 16},
    'Sinú': {'rff_row': 5, 'cpo_row': 6, 'pk_row': 17, 'pk_cpo_row': 18},
    'A&G': {'rff_row': 7, 'cpo_row': 8, 'pk_row': 19, 'pk_cpo_row': 20},
}

# KPO (solo Codazzi tiene expeller)
KPO_CONFIG = {
    'pk_proceso_row': 25,
    'kpo_row': 26,
}


def extract_budget_data(budget_file: str) -> dict:
    """
    Extrae datos de presupuesto (ME) del archivo de planeación.
    
    Returns:
        dict: {(fecha_str, zona): {'rff_me': valor, 'cpo_me': valor, 'pk_me': valor}}
    """
    print(f"📂 Leyendo presupuesto: {os.path.basename(budget_file)}")
    
    df = pd.read_excel(budget_file, sheet_name='Resumen', header=None)
    
    # Obtener fechas del encabezado (fila 0, columnas 2 en adelante)
    fechas = []
    for col in range(2, df.shape[1]):
        fecha_val = df.iloc[0, col]
        if pd.notna(fecha_val) and isinstance(fecha_val, datetime):
            fechas.append((col, fecha_val.date()))
    
    print(f"   📅 Fechas encontradas: {len(fechas)} días")
    
    budget_data = {}
    
    for planta, config in PLANTAS_ME.items():
        for col, fecha in fechas:
            fecha_str = fecha.strftime('%Y-%m-%d')
            key = (fecha_str, planta)
            
            # RFF y CPO
            rff_me = df.iloc[config['rff_row'], col]
            cpo_me = df.iloc[config['cpo_row'], col]
            
            # Palmiste (PK)
            pk_me = 0
            if pd.notna(df.iloc[config['pk_row'], col]):
                pk_me_val = df.iloc[config['pk_cpo_row'], col]
                if pd.notna(pk_me_val):
                    pk_me = pk_me_val
            
            budget_data[key] = {
                'rff_presupuesto': float(rff_me) if pd.notna(rff_me) else 0,
                'cpo_presupuesto': float(cpo_me) if pd.notna(cpo_me) else 0,
                'palmiste_presupuesto': float(pk_me) if pd.notna(pk_me) else 0,
            }
    
    print(f"   ✅ {len(budget_data)} registros de presupuesto extraídos")
    return budget_data


def update_upstream_with_budget(upstream_path: str, budget_data: dict) -> pd.DataFrame:
    """
    Actualiza el archivo upstream.csv con los valores de presupuesto.
    """
    print(f"\n📊 Actualizando upstream con presupuesto...")
    
    df = pd.read_csv(upstream_path)
    df['fecha'] = pd.to_datetime(df['fecha']).dt.strftime('%Y-%m-%d')
    
    updated = 0
    for idx, row in df.iterrows():
        key = (row['fecha'], row['zona'])
        if key in budget_data:
            budget = budget_data[key]
            df.at[idx, 'rff_presupuesto'] = budget['rff_presupuesto']
            df.at[idx, 'cpo_presupuesto'] = budget['cpo_presupuesto']
            if 'palmiste_presupuesto' in df.columns:
                df.at[idx, 'palmiste_presupuesto'] = budget['palmiste_presupuesto']
            updated += 1
    
    print(f"   ✅ {updated} registros actualizados")
    
    # Guardar
    df.to_csv(upstream_path, index=False)
    print(f"   💾 Guardado: {upstream_path}")
    
    return df


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, 'data')
    
    # Buscar archivo de planeación más reciente
    budget_files = [f for f in os.listdir(data_dir) if 'PLANEA' in f and f.endswith('.xlsx')]
    
    if not budget_files:
        # Intentar buscar por patrón parcial
        budget_files = [f for f in os.listdir(data_dir) if 'DICIEMBRE' in f and 'PLANTAS' in f and f.endswith('.xlsx')]
    
    if not budget_files:
        print("❌ No se encontró archivo de planeación")
        return
    
    budget_file = os.path.join(data_dir, sorted(budget_files)[-1])
    upstream_path = os.path.join(data_dir, 'upstream.csv')
    
    # Extraer presupuesto
    budget_data = extract_budget_data(budget_file)
    
    # Actualizar upstream
    if os.path.exists(upstream_path):
        update_upstream_with_budget(upstream_path, budget_data)
    else:
        print(f"❌ No existe {upstream_path}")
    
    print("\n✅ Presupuesto actualizado correctamente")


if __name__ == '__main__':
    main()
