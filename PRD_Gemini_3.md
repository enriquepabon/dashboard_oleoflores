# 📄 PRD: Oleoflores Business Intelligence Suite (v1.0)

## 1. Resumen Ejecutivo
Desarrollo de una aplicación web de Business Intelligence escalable y dinámica para el **Grupo Oleoflores**. El objetivo es migrar de reportes estáticos en Excel a un dashboard interactivo que visualice la cadena de valor completa (Farm-to-Fork), permitiendo análisis semanal, mensual y anual de indicadores de Upstream (Campo/Extractora) y Downstream (Refinería/Productos).

## 2. Stack Tecnológico Definido
* **Lenguaje:** Python 3.9+
* **Framework Web:** Streamlit (por su rapidez de despliegue y facilidad de mantenimiento).
* **Visualización:** Plotly Graph Objects (para máxima interactividad y personalización).
* **Manipulación de Datos:** Pandas.
* **Entorno de Desarrollo:** Cursor (AI-First Code Editor).

## 3. Arquitectura de Datos (Data Ingestion)
La aplicación debe leer archivos CSV exportados del Excel maestro `20251201 SEGUIMIENTO AGROINDUSTRIA...`.

### Estructura de Archivos Esperada (Input)
El sistema debe procesar los siguientes datasets clave:
1.  **UPSTREAM (Dataset A):** Contiene RFF (Recepción de Fruta), Producción CPO, Palmiste y TEA (Tasa de Extracción).
    * *Granularidad:* Diaria/Semanal.
    * *Dimensiones:* Zonas (Codazzi, MLB, A&G, Sinú).
2.  **DOWNSTREAM (Dataset B):** Contiene Refinería (1 y 2), Oleína, Margarinas y Mermas.
    * *Granularidad:* Diaria/Semanal.
    * *Comparativa:* Planta (Presupuesto) vs. Real.
3.  **COSTOS/ACUMULADOS (Dataset C):** Datos históricos y acumulados anuales para proyecciones.

### Requerimientos de ETL (Extract, Transform, Load)
* **Limpieza Automática:** El código debe detectar y reparar formatos numéricos (ej. eliminar "," de miles, convertir "%" a float).
* **Manejo de Fechas:** Unificación de columnas de fecha a formato `datetime` estándar.
* **Cálculo de Deltas:** Calcular dinámicamente `Variación = Real - Presupuesto` y `% Cumplimiento`.

## 4. Requerimientos Funcionales (Estructura de la App)

### 4.1. Barra Lateral (Sidebar) de Navegación y Filtros
* **Selector de Vista:** [Resumen Ejecutivo, Upstream, Downstream, Simulación].
* **Filtros Globales:**
    * Rango de Fechas (Semana, Mes, Año, YTD).
    * Selector de Zona (Solo afecta vistas Upstream).

### 4.2. Módulo 1: Resumen Ejecutivo (C-Level)
* **Objetivo:** Vista de pájaro del estado de la compañía.
* **Componentes:**
    * **Scorecards (KPIs):** 4 Tarjetas grandes con [Valor Actual] + [Indicador de Variación (Flecha Verde/Roja)].
        * KPIs: Toneladas RFF Procesadas, TEA Promedio, Producción CPO, Producción Margarinas.
    * **Gráfico de Tendencia Macro:** Línea de tiempo comparando `Producción Total Real` vs `Presupuesto`.

### 4.3. Módulo 2: UPSTREAM (Agroindustria)
* **Objetivo:** Análisis de eficiencia en campo y extracción.
* **Gráficos Clave:**
    * **Bar Chart Grouped:** RFF por Zona (Codazzi, MLB, etc.) comparando Real vs Meta.
    * **Gauge Chart (Velocímetro):** Para el indicador **TEA** (Tasa de Extracción de Aceite). Debe mostrar el % actual frente a la meta técnica.
    * **Heatmap de Cosecha:** Eje X = Días del mes, Eje Y = Zonas, Color = Intensidad de recepción (Toneladas). Permite ver picos de cosecha.

### 4.4. Módulo 3: DOWNSTREAM (Refinería y B2C)
* **Objetivo:** Balance de masas e inventarios.
* **Gráficos Clave:**
    * **Sankey Diagram (CRÍTICO):** Visualización del flujo de masa.
        * *Flujo:* Entrada CPO -> Refinería -> [Oleína, RBD, Margarinas, Mermas].
        * Debe evidenciar visualmente dónde se pierde masa.
    * **Area Chart (Stacked):** Evolución de inventarios de producto terminado.
    * **Bullet Graph:** Cumplimiento de ventas/producción por SKU (Oleína vs Margarina).

## 5. Requerimientos No Funcionales (UI/UX)
* **Estilo Corporativo:**
    * Fondo: Gris muy claro (`#f9f9f9`) o Blanco.
    * Colores Gráficas: Verde Oleo (`#2E7D32`), Dorado Aceite (`#F9A825`), Alerta Rojo (`#C62828`).
* **Modularidad:** El código debe estar separado en `app.py` (interfaz), `data_loader.py` (lógica de datos) y `plots.py` (configuración de gráficas).
* **Performance:** Carga de datos inicial en caché (`@st.cache_data`) para evitar lentitud al cambiar filtros.

---

## 6. Guía de Implementación para Cursor (Paso a Paso)

Para empezar a desarrollar esto en Cursor, te sugiero crear una carpeta para el proyecto, abrir Cursor allí ("Open Folder") y seguir estos pasos usando el chat (Command + L):

### Paso 1: Configuración Inicial
Copia y pega esto en el chat de Cursor:
> "Inicializa un proyecto de Streamlit profesional. Crea la estructura de carpetas: `data/` (para los csv), `src/` (para los módulos) y un archivo `app.py` en la raíz. Genera un archivo `requirements.txt` que incluya: streamlit, pandas, plotly, openpyxl."

### Paso 2: Ingesta de Datos (El paso más importante)
Sube los CSVs a la carpeta `data/` y dile a Cursor:
> "He subido los archivos CSV de Oleoflores a la carpeta data. Analiza la estructura de columnas de los archivos `UPSTREAM.csv` y `DOWNSTREAM.csv`. Crea un script en `src/data_loader.py` que limpie los datos: convierte fechas a datetime, limpia caracteres numéricos extraños y devuelve dataframes limpios listos para graficar. Usa `@st.cache_data` para optimizar."

### Paso 3: Creación de Visualizaciones
> "Crea un módulo `src/plots.py`. Quiero una función que genere un **Diagrama de Sankey** usando Plotly Graph Objects. La función debe recibir un dataframe y mapear el flujo desde 'Entrada CPO' hacia 'Refinería' y luego hacia los productos finales ('Oleína', 'Margarinas'). Usa colores corporativos (verdes y amarillos)."

### Paso 4: Ensamblaje del Dashboard
> "En `app.py`, importa los módulos de `src`. Crea un layout con un sidebar para filtros de fecha. Implementa pestañas (Tabs) para separar 'Resumen', 'Upstream' y 'Downstream'. En la pestaña Downstream, invoca la función del diagrama de Sankey que creaste."

---