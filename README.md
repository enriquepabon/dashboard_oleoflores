# 🌴 Oleoflores BI Dashboard

Sistema de Business Intelligence para el **Grupo Oleoflores**. Dashboard interactivo para visualización de la cadena de valor completa (Farm-to-Fork).

## 📋 Características

- **Resumen Ejecutivo**: KPIs principales con indicadores de variación
- **Upstream (Agroindustria)**: Análisis de RFF, TEA y producción por zona
- **Downstream (Refinería)**: Flujo de masa con diagrama Sankey, inventarios y cumplimiento
- **Carga de Datos**: Upload de archivos CSV/Excel sin integración a ERP
- **Alertas Visuales**: Notificaciones para valores fuera de rango
- **Exportación**: Descarga de datos filtrados en formato CSV

## 🚀 Instalación

### Requisitos Previos
- Python 3.9 o superior
- pip (gestor de paquetes de Python)

### Pasos de Instalación

1. **Clonar o descargar el proyecto**
```bash
cd "Dashboard Oleoflores"
```

2. **Crear entorno virtual (recomendado)**
```bash
python -m venv venv

# En Windows:
venv\Scripts\activate

# En macOS/Linux:
source venv/bin/activate
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Ejecutar la aplicación**
```bash
streamlit run app.py
```

5. **Abrir en el navegador**
   - La aplicación se abrirá automáticamente en `http://localhost:8501`

## 📁 Estructura del Proyecto

```
Dashboard Oleoflores/
├── app.py                 # Aplicación principal Streamlit
├── requirements.txt       # Dependencias del proyecto
├── README.md             # Este archivo
├── src/                  # Módulos de código
│   ├── __init__.py       # Inicializador del paquete
│   ├── data_loader.py    # Carga y procesamiento de datos
│   ├── plots.py          # Funciones de visualización
│   └── utils.py          # Constantes y utilidades
├── data/                 # Archivos de datos (CSV/Excel)
│   ├── upstream.csv      # Datos de campo y extracción
│   └── downstream.csv    # Datos de refinería
├── assets/               # Recursos estáticos
│   └── logo.png          # Logo corporativo
└── tasks/                # Documentación del proyecto
    ├── prd-*.md          # Product Requirements Document
    └── tasks-*.md        # Lista de tareas
```

## 📊 Estructura de Datos

### Archivo Upstream (upstream.csv)
| Columna | Descripción | Tipo |
|---------|-------------|------|
| fecha | Fecha del registro | date |
| zona | Zona de operación (Codazzi, MLB, A&G, Sinú) | string |
| rff_real | Toneladas RFF recibidas (real) | float |
| rff_presupuesto | Toneladas RFF presupuestadas | float |
| cpo_real | Producción CPO real | float |
| cpo_presupuesto | Producción CPO presupuestada | float |
| tea_real | Tasa de Extracción de Aceite real | float |
| tea_meta | TEA meta técnica | float |

### Archivo Downstream (downstream.csv)
| Columna | Descripción | Tipo |
|---------|-------------|------|
| fecha | Fecha del registro | date |
| refineria | Número de refinería (1, 2) | int |
| cpo_entrada | CPO de entrada a refinería | float |
| oleina_real | Producción oleína real | float |
| oleina_presupuesto | Producción oleína presupuestada | float |
| margarinas_real | Producción margarinas real | float |
| margarinas_presupuesto | Producción margarinas presupuestada | float |
| mermas | Mermas del proceso | float |

## 🎨 Paleta de Colores

| Color | Hex | Uso |
|-------|-----|-----|
| Verde Oleo | `#2E7D32` | Valores positivos, éxito |
| Dorado | `#F9A825` | Neutro, aceite |
| Rojo Alerta | `#C62828` | Valores negativos, alertas |
| Fondo | `#f9f9f9` | Fondo principal |

## 🔧 Solución de Problemas

### El archivo CSV no se carga correctamente
- Verificar que las columnas coincidan con la estructura esperada
- Asegurar que los números no tengan caracteres especiales (excepto punto decimal)
- Las fechas deben estar en formato YYYY-MM-DD o DD/MM/YYYY

### Los gráficos no se muestran
- Verificar que los datos no estén vacíos
- Revisar que no haya valores nulos en columnas críticas

### Error de dependencias
```bash
pip install --upgrade -r requirements.txt
```

## 📝 Notas de Versión

### v1.0.0 (Diciembre 2024)
- Versión inicial del dashboard
- Módulos: Resumen Ejecutivo, Upstream, Downstream
- Carga de datos CSV/Excel
- Sistema de alertas visuales
- Exportación a CSV

## 👥 Equipo

Desarrollado para **Grupo Oleoflores** por el equipo de Business Intelligence.

## 📄 Licencia

Uso interno - Grupo Oleoflores © 2024

