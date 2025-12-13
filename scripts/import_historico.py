"""
Script para importar datos históricos al formato del dashboard.

Convierte el archivo 'Historico Oleoflores consolidado.csv' (datos mensuales 2007-2024)
al formato de upstream.csv para integrarlos con los datos diarios del 2025.

Uso:
    python scripts/import_historico.py
"""

import pandas as pd
import numpy as np
import os
import re
from datetime import datetime
import calendar

# Mapeo de nombres de plantas (normalización)
PLANTAS_MAPPING = {
    'A&G ': 'A&G',
    'A&G': 'A&G',
    'Codazzi': 'Codazzi',
    'MLB': 'MLB',
    'SINÚ': 'Sinú',
    'Sinú': 'Sinú',
}

# Mapeo de meses a números
MESES = {
    'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
    'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
    'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
}

# TEA metas históricas por defecto (valores promedio históricos por planta)
TEA_METAS_DEFAULT = {
    'A&G': 23.5,
    'Codazzi': 21.6,
    'MLB': 18.6,
    'Sinú': 22.0,
}


def parse_año_tipo(valor):
    """
    Parsea el campo AÑO para extraer el tipo de dato y el año.
    Ejemplo: 'RFF Procesada 2017' -> ('rff', 2017)
             'Producción CPO 2017' -> ('cpo', 2017)
             'Extracción 2017' -> ('tea', 2017)
    """
    valor = str(valor).strip()
    
    # Ignorar filas de proyección o promedio
    if 'Proyección' in valor or 'Promedio' in valor:
        return None, None
    
    # Buscar año (4 dígitos al final)
    match = re.search(r'(\d{4})$', valor)
    if not match:
        return None, None
    
    año = int(match.group(1))
    
    # Determinar tipo
    valor_lower = valor.lower()
    if 'rff' in valor_lower:
        return 'rff', año
    elif 'cpo' in valor_lower:
        return 'cpo', año
    elif 'extrac' in valor_lower:
        return 'tea', año
    
    return None, None


def import_historico(historico_path, output_path):
    """
    Importa el archivo histórico consolidado y lo convierte al formato upstream.csv.
    
    Args:
        historico_path: Ruta al archivo CSV histórico
        output_path: Ruta de salida para el upstream.csv
    """
    print(f"📂 Leyendo histórico: {historico_path}")
    
    # Leer CSV
    df = pd.read_csv(historico_path, encoding='utf-8-sig')
    print(f"   {len(df)} filas encontradas")
    
    # Estructura para almacenar datos procesados
    # Key: (planta, año, mes) -> Value: {rff, cpo, tea}
    datos = {}
    
    # Procesar cada fila
    for _, row in df.iterrows():
        planta_raw = str(row.iloc[0]).strip()
        planta = PLANTAS_MAPPING.get(planta_raw, planta_raw)
        
        if planta not in PLANTAS_MAPPING.values():
            continue
        
        tipo, año = parse_año_tipo(row.iloc[1])
        if tipo is None or año is None:
            continue
        
        # Procesar cada mes
        for mes_nombre, mes_num in MESES.items():
            valor = row.get(mes_nombre, 0)
            
            # Validar valor
            if pd.isna(valor) or valor == '' or valor == 0:
                valor = 0.0
            else:
                try:
                    valor = float(valor)
                except:
                    valor = 0.0
            
            key = (planta, año, mes_num)
            if key not in datos:
                datos[key] = {'rff': 0, 'cpo': 0, 'tea': 0}
            
            datos[key][tipo] = valor
    
    print(f"   {len(datos)} registros procesados")
    
    # Convertir a registros formato upstream
    records = []
    for (planta, año, mes), valores in datos.items():
        # Solo incluir si hay datos (RFF o CPO > 0)
        if valores['rff'] <= 0 and valores['cpo'] <= 0:
            continue
        
        # Calcular último día del mes
        ultimo_dia = calendar.monthrange(año, mes)[1]
        fecha = f"{año}-{mes:02d}-{ultimo_dia:02d}"
        
        # TEA: convertir de decimal a porcentaje si es necesario
        tea = valores['tea']
        if 0 < tea < 1:
            tea = tea * 100
        
        # TEA meta: usar el valor real histórico como meta
        tea_meta = TEA_METAS_DEFAULT.get(planta, 20.0)
        
        record = {
            'fecha': fecha,
            'zona': planta,
            'rff_real': round(valores['rff'], 2),
            'rff_presupuesto': 0,  # No hay presupuesto histórico
            'cpo_real': round(valores['cpo'], 2),
            'cpo_presupuesto': 0,  # No hay presupuesto histórico
            'palmiste_real': round(valores['cpo'] * 0.05, 2),  # Estimado 5% del CPO
            'palmiste_presupuesto': 0,
            'tea_real': round(tea, 2),
            'tea_meta': tea_meta,
            'almendra_real': 0,
            'almendra_presupuesto': 0,
            'kpo_real': 0,
            'kpo_presupuesto': 0,
            'extraccion_almendra': 0,
            'acidez': 0,
            'humedad': 0,
            'impurezas': 0,
            'inventario_cpo': 0,
            'tanque_1': 0,
            'tanque_2': 0,
            'tanque_3': 0,
            'tanque_4': 0,
        }
        records.append(record)
    
    # Crear DataFrame
    df_result = pd.DataFrame(records)
    df_result = df_result.sort_values(['fecha', 'zona']).reset_index(drop=True)
    
    # Guardar
    df_result.to_csv(output_path, index=False)
    print(f"💾 Guardado: {output_path}")
    print(f"   {len(df_result)} registros históricos creados")
    
    # Resumen por año
    print("\n📊 RESUMEN POR AÑO:")
    print("-" * 40)
    df_result['año'] = df_result['fecha'].str[:4]
    resumen = df_result.groupby('año').agg({
        'rff_real': 'sum',
        'cpo_real': 'sum'
    }).round(0)
    for año, row in resumen.iterrows():
        print(f"   {año}: RFF {row['rff_real']:,.0f} Ton, CPO {row['cpo_real']:,.0f} Ton")
    
    return df_result


def main():
    """Punto de entrada principal."""
    print("=" * 60)
    print("🔄 IMPORTAR HISTÓRICO OLEOFLORES")
    print("=" * 60)
    
    # Rutas
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    historico_path = os.path.join(base_dir, 'data', 'Historico Oleoflores consolidado.csv')
    output_path = os.path.join(base_dir, 'data', 'upstream.csv')
    
    if not os.path.exists(historico_path):
        print(f"❌ Archivo no encontrado: {historico_path}")
        return
    
    # Importar
    df = import_historico(historico_path, output_path)
    
    print("\n✨ Importación completada!")
    print(f"   Ahora puedes procesar los archivos de seguimiento 2025")
    print(f"   para agregar el detalle diario.")


if __name__ == "__main__":
    main()
