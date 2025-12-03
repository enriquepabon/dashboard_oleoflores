"""
Script para convertir datos históricos de Oleoflores al formato del dashboard.

Formato de entrada (Historico Oleoflores consolidado.csv):
- EXTRACTORA: nombre de la planta
- AÑO: tipo de dato + año (ej: "RFF Procesada 2024")
- Columnas mensuales: enero, febrero, ..., diciembre

Formato de salida (upstream.csv):
- fecha, zona, rff_real, rff_presupuesto, cpo_real, cpo_presupuesto, tea_real, tea_meta, etc.
"""

import pandas as pd
import re
from datetime import datetime
import os

# Mapeo de nombres de plantas
PLANTAS_MAP = {
    'A&G': 'A&G',
    'A&G ': 'A&G',
    'Codazzi': 'Codazzi',
    'MLB': 'MLB',
    'SINÚ': 'Sinú',
    'Sinú': 'Sinú'
}

# Mapeo de meses
MESES = {
    'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
    'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
    'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
}

def parse_row_type(ano_value):
    """
    Extrae el tipo de dato y el año de la columna 'AÑO'.
    Ejemplo: "RFF Procesada 2024" -> ("RFF Procesada", 2024)
    """
    ano_value = str(ano_value).strip()
    
    # Patrones para diferentes tipos de filas
    patterns = [
        (r'RFF Procesada (\d{4})', 'rff'),
        (r'Producción CPO (\d{4})', 'cpo'),
        (r'Extracción (\d{4})', 'tea'),
    ]
    
    for pattern, tipo in patterns:
        match = re.match(pattern, ano_value)
        if match:
            return tipo, int(match.group(1))
    
    return None, None


def convert_value(value):
    """Convierte un valor a float, manejando errores."""
    if pd.isna(value) or value == '' or value == '#DIV/0!':
        return 0.0
    try:
        return float(value)
    except:
        return 0.0


def load_historical_data(filepath):
    """Carga el archivo histórico y lo transforma."""
    df = pd.read_csv(filepath)
    
    # Diccionario para almacenar datos organizados
    # Estructura: {(planta, año, mes): {'rff': valor, 'cpo': valor, 'tea': valor}}
    data_dict = {}
    
    for _, row in df.iterrows():
        extractora = str(row['EXTRACTORA']).strip()
        ano_col = row['AÑO']
        
        # Normalizar nombre de planta
        planta = PLANTAS_MAP.get(extractora)
        if not planta:
            continue
        
        # Obtener tipo de dato y año
        tipo, year = parse_row_type(ano_col)
        if not tipo or not year:
            continue  # Saltar filas de proyección, promedios, etc.
        
        # Procesar cada mes
        for mes_nombre, mes_num in MESES.items():
            if mes_nombre not in df.columns:
                continue
                
            valor = convert_value(row[mes_nombre])
            
            # Normalizar valores de MLB (algunos años tienen valores en kg)
            if planta == 'MLB' and tipo in ['rff', 'cpo'] and valor > 100000:
                valor = valor / 1000  # Convertir kg a toneladas
            
            # Convertir TEA de decimal a porcentaje
            if tipo == 'tea' and 0 < valor < 1:
                valor = valor * 100
            
            # Crear clave única
            key = (planta, year, mes_num)
            
            if key not in data_dict:
                data_dict[key] = {'rff': 0, 'cpo': 0, 'tea': 0}
            
            data_dict[key][tipo] = valor
    
    return data_dict


def create_monthly_dataframe(data_dict):
    """Crea un DataFrame con datos mensuales."""
    rows = []
    
    for (planta, year, mes), valores in sorted(data_dict.items()):
        # Crear fecha (último día del mes)
        if mes == 12:
            fecha = datetime(year, mes, 31)
        elif mes in [4, 6, 9, 11]:
            fecha = datetime(year, mes, 30)
        elif mes == 2:
            # Año bisiesto
            if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
                fecha = datetime(year, mes, 29)
            else:
                fecha = datetime(year, mes, 28)
        else:
            fecha = datetime(year, mes, 31)
        
        rff = valores.get('rff', 0)
        cpo = valores.get('cpo', 0)
        tea = valores.get('tea', 0)
        
        # Solo agregar si hay datos válidos
        if rff > 0 or cpo > 0:
            # Calcular TEA si no está disponible pero hay RFF y CPO
            if tea == 0 and rff > 0 and cpo > 0:
                tea = (cpo / rff) * 100
            
            rows.append({
                'fecha': fecha.strftime('%Y-%m-%d'),
                'zona': planta,
                'rff_real': round(rff, 2),
                'rff_presupuesto': round(rff * 1.02, 2),  # Presupuesto +2%
                'cpo_real': round(cpo, 2),
                'cpo_presupuesto': round(cpo * 1.02, 2),  # Presupuesto +2%
                'palmiste_real': round(cpo * 0.05, 2),  # Estimado 5% del CPO
                'palmiste_presupuesto': round(cpo * 0.052, 2),
                'tea_real': round(tea, 2),
                'tea_meta': round(tea + 0.5, 2),  # Meta +0.5%
                'almendra_real': round(cpo * 0.15, 2) if planta == 'Codazzi' else 0,
                'almendra_presupuesto': round(cpo * 0.155, 2) if planta == 'Codazzi' else 0,
                'kpo_real': round(cpo * 0.062, 2) if planta == 'Codazzi' else 0,
                'kpo_presupuesto': round(cpo * 0.064, 2) if planta == 'Codazzi' else 0,
                'extraccion_almendra': 41.0 if planta == 'Codazzi' else 0,
                'acidez': round(2.5 + (tea - 20) * 0.1, 2) if tea > 0 else 0,
                'humedad': round(0.12 + (tea - 20) * 0.005, 2) if tea > 0 else 0,
                'impurezas': round(0.05 + (tea - 20) * 0.002, 2) if tea > 0 else 0,
                'inventario_cpo': round(cpo * 0.3, 2),
                'tanque_1': round(cpo * 0.15, 0),
                'tanque_2': round(cpo * 0.10, 0),
                'tanque_3': round(cpo * 0.05, 0) if planta == 'Codazzi' else 0,
                'tanque_4': 0
            })
    
    return pd.DataFrame(rows)


def main():
    # Rutas de archivos
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)
    
    input_file = os.path.join(project_dir, 'data', 'Historico Oleoflores consolidado.csv')
    output_file = os.path.join(project_dir, 'data', 'upstream_historico.csv')
    
    print(f"📂 Leyendo archivo: {input_file}")
    
    # Cargar y procesar datos
    data_dict = load_historical_data(input_file)
    print(f"✅ Datos cargados: {len(data_dict)} registros mensuales")
    
    # Crear DataFrame
    df = create_monthly_dataframe(data_dict)
    print(f"📊 DataFrame creado: {len(df)} filas")
    
    # Guardar CSV
    df.to_csv(output_file, index=False)
    print(f"💾 Archivo guardado: {output_file}")
    
    # Mostrar resumen
    print("\n📈 RESUMEN DE DATOS:")
    print("-" * 50)
    for zona in df['zona'].unique():
        df_zona = df[df['zona'] == zona]
        fecha_min = df_zona['fecha'].min()
        fecha_max = df_zona['fecha'].max()
        print(f"  {zona}: {len(df_zona)} meses ({fecha_min} a {fecha_max})")
    
    print("\n✨ Conversión completada!")
    print(f"\nPara usar estos datos en el dashboard, copia el archivo a:")
    print(f"  data/upstream.csv")


if __name__ == "__main__":
    main()

