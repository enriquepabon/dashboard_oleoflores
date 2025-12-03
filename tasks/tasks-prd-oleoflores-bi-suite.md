# 📋 Task List: Oleoflores Business Intelligence Suite

> **PRD de referencia:** `tasks/prd-oleoflores-bi-suite.md`  
> **Fecha de creación:** Diciembre 2024  
> **Estado:** Fase 2 - Sub-tareas Generadas ✅

---

## Relevant Files

| Archivo | Descripción |
|---------|-------------|
| `app.py` | Punto de entrada principal - Interfaz Streamlit con layout, sidebar y navegación |
| `requirements.txt` | Dependencias del proyecto (streamlit, pandas, plotly, openpyxl) |
| `README.md` | Documentación de instalación y uso del dashboard |
| `src/__init__.py` | Inicializador del paquete src |
| `src/data_loader.py` | Módulo ETL: carga, validación, limpieza y transformación de datos |
| `src/plots.py` | Funciones de generación de gráficas Plotly (Gauge, Sankey, Barras, etc.) |
| `src/utils.py` | Constantes (colores corporativos), funciones auxiliares y validadores |
| `data/upstream.csv` | Dataset de ejemplo - Datos Upstream (RFF, CPO, TEA por zona) |
| `data/downstream.csv` | Dataset de ejemplo - Datos Downstream (Refinería, productos, mermas) |
| `assets/` | Carpeta para recursos estáticos (logos, estilos CSS personalizados) |

### Notes

- Los archivos de datos (`data/*.csv`) son de ejemplo para desarrollo. En producción se cargarán dinámicamente mediante el uploader.
- El proyecto utiliza Streamlit con `@st.cache_data` para optimizar rendimiento en la carga de datos.
- Los colores corporativos están centralizados en `src/utils.py` como constantes reutilizables.
- Cada sub-tarea debe marcarse como completada `[x]` antes de pasar a la siguiente.
- Al completar todas las sub-tareas de una tarea padre, ejecutar tests y hacer commit.

---

## Tasks

- [x] 1.0 Configuración Inicial del Proyecto y Entorno de Desarrollo
  - [x] 1.1 Crear estructura de carpetas del proyecto (`src/`, `data/`, `assets/`, `tasks/`)
  - [x] 1.2 Crear archivo `requirements.txt` con dependencias (streamlit>=1.28.0, pandas>=2.0.0, plotly>=5.18.0, openpyxl>=3.1.0, python-dateutil>=2.8.0)
  - [x] 1.3 Crear archivo `src/__init__.py` vacío para inicializar el paquete
  - [x] 1.4 Crear archivo `src/utils.py` con constantes de colores corporativos (VERDE_OLEO=#2E7D32, DORADO=#F9A825, ROJO_ALERTA=#C62828, FONDO=#f9f9f9)
  - [x] 1.5 Crear archivo `app.py` base con configuración de página Streamlit (título, layout wide, favicon)
  - [x] 1.6 Crear archivo `README.md` con instrucciones de instalación y ejecución
  - [x] 1.7 Crear archivos CSV de ejemplo en `data/` con estructura definida para upstream y downstream

- [ ] 2.0 Desarrollo del Módulo de Carga y Procesamiento de Datos (ETL)
  - [ ] 2.1 Crear función `load_file()` en `data_loader.py` que acepte CSV y Excel (.xlsx) usando pandas
  - [ ] 2.2 Crear función `validate_columns()` que verifique que el archivo tenga las columnas requeridas según el tipo (upstream/downstream)
  - [ ] 2.3 Crear función `clean_numeric_values()` que elimine caracteres de formato (comas, símbolos %) y convierta a float
  - [ ] 2.4 Crear función `normalize_dates()` que unifique columnas de fecha a formato datetime estándar
  - [ ] 2.5 Crear función `calculate_variations()` que compute `Variación = Real - Presupuesto` y `% Cumplimiento`
  - [ ] 2.6 Crear función `load_upstream_data()` con decorador `@st.cache_data` que integre carga, validación y limpieza
  - [ ] 2.7 Crear función `load_downstream_data()` con decorador `@st.cache_data` que integre carga, validación y limpieza
  - [ ] 2.8 Implementar manejo de errores con mensajes claros para archivos faltantes, formato incorrecto o columnas ausentes

- [ ] 3.0 Desarrollo del Módulo de Visualizaciones
  - [ ] 3.1 Crear función `create_scorecard()` en `plots.py` que genere tarjeta KPI con valor actual, variación y flecha indicadora (verde/roja)
  - [ ] 3.2 Crear función `create_gauge_chart()` para indicador TEA tipo velocímetro con meta técnica y rangos de color
  - [ ] 3.3 Crear función `create_grouped_bar_chart()` para comparativa RFF por Zona (Real vs Meta) con colores corporativos
  - [ ] 3.4 Crear función `create_heatmap()` para mapa de calor de cosecha (Eje X: Días, Eje Y: Zonas, Color: Intensidad toneladas)
  - [ ] 3.5 Crear función `create_sankey_diagram()` para flujo de masa: CPO → Refinería → [Oleína, RBD, Margarinas, Mermas]
  - [ ] 3.6 Crear función `create_area_chart()` para evolución de inventarios apilados por producto
  - [ ] 3.7 Crear función `create_bullet_chart()` para cumplimiento por SKU (Oleína vs Margarina vs Meta)
  - [ ] 3.8 Crear función `create_trend_line_chart()` para gráfico de línea Producción Real vs Presupuesto en el tiempo

- [ ] 4.0 Implementación de la Interfaz Principal y Sistema de Navegación
  - [ ] 4.1 Configurar `st.set_page_config()` con título "Oleoflores BI Dashboard", layout="wide", icono personalizado
  - [ ] 4.2 Implementar sidebar con logo (si disponible) y título del dashboard
  - [ ] 4.3 Agregar selector de vista en sidebar usando `st.radio()`: [Resumen Ejecutivo, Upstream, Downstream]
  - [ ] 4.4 Implementar filtro de rango de fechas en sidebar usando `st.date_input()` con opciones predefinidas (Semana, Mes, YTD)
  - [ ] 4.5 Implementar selector de Zona en sidebar usando `st.multiselect()` con opciones: Codazzi, MLB, A&G, Sinú
  - [ ] 4.6 Agregar componente `st.file_uploader()` para carga de archivos CSV/Excel con validación
  - [ ] 4.7 Implementar lógica de routing que muestre la vista seleccionada en el área principal

- [ ] 5.0 Implementación de los Módulos de Vistas (Resumen, Upstream, Downstream)
  - [ ] 5.1 Crear vista "Resumen Ejecutivo" con 4 Scorecards en fila (RFF, TEA, CPO, Margarinas) usando `st.columns(4)`
  - [ ] 5.2 Agregar gráfico de tendencia (línea) Real vs Presupuesto debajo de los Scorecards en vista Resumen
  - [ ] 5.3 Crear vista "Upstream" con sección superior: Bar Chart de RFF por Zona + Gauge de TEA
  - [ ] 5.4 Agregar Heatmap de cosecha en la parte inferior de vista Upstream
  - [ ] 5.5 Crear vista "Downstream" con Diagrama Sankey prominente en la parte superior
  - [ ] 5.6 Agregar Area Chart de inventarios y Bullet Chart de cumplimiento en vista Downstream
  - [ ] 5.7 Asegurar que los filtros de fecha y zona se apliquen correctamente a todas las visualizaciones

- [ ] 6.0 Sistema de Alertas, Exportación y Validaciones Finales
  - [ ] 6.1 Crear función `validate_data_ranges()` en `utils.py` que detecte valores fuera de rango (TEA>35%, valores negativos, etc.)
  - [ ] 6.2 Implementar componente visual de alerta usando `st.warning()` y `st.error()` con íconos distintivos
  - [ ] 6.3 Mostrar alertas en el dashboard cuando se detecten valores anómalos con descripción del problema
  - [ ] 6.4 Crear función `export_to_csv()` que genere archivo CSV con los datos filtrados actuales
  - [ ] 6.5 Agregar botón de descarga en cada vista usando `st.download_button()` para exportar datos
  - [ ] 6.6 Realizar pruebas de integración: cargar datos reales, verificar filtros, validar visualizaciones
  - [ ] 6.7 Documentar en README.md las instrucciones de uso, estructura de archivos esperada y solución de problemas comunes

---

## Resumen de Progreso

| Tarea | Sub-tareas | Completadas | Estado |
|-------|------------|-------------|--------|
| 1.0 Configuración Inicial | 7 | 7 | ✅ Completada |
| 2.0 Módulo ETL | 8 | 0 | ⏳ Pendiente |
| 3.0 Módulo Visualizaciones | 8 | 0 | ⏳ Pendiente |
| 4.0 Interfaz Principal | 7 | 0 | ⏳ Pendiente |
| 5.0 Vistas Específicas | 7 | 0 | ⏳ Pendiente |
| 6.0 Alertas y Exportación | 7 | 0 | ⏳ Pendiente |
| **TOTAL** | **44** | **7** | **16%** |

---

## Diagrama de Dependencias

```
┌─────────────────────────────────────────────────────────────────┐
│                    1.0 CONFIGURACIÓN INICIAL                    │
│         (estructura, dependencias, constantes, setup)           │
└─────────────────────┬───────────────────────────────────────────┘
                      │
          ┌───────────┴───────────┐
          ▼                       ▼
┌─────────────────────┐   ┌─────────────────────┐
│   2.0 MÓDULO ETL    │   │ 3.0 VISUALIZACIONES │
│   (data_loader.py)  │   │    (plots.py)       │
└─────────┬───────────┘   └───────────┬─────────┘
          │                           │
          └─────────────┬─────────────┘
                        ▼
          ┌─────────────────────────┐
          │  4.0 INTERFAZ PRINCIPAL │
          │       (app.py)          │
          └───────────┬─────────────┘
                      ▼
          ┌─────────────────────────┐
          │     5.0 VISTAS          │
          │ (Resumen/Upstream/Down) │
          └───────────┬─────────────┘
                      ▼
          ┌─────────────────────────┐
          │ 6.0 ALERTAS/EXPORTACIÓN │
          │   (validación, CSV)     │
          └─────────────────────────┘
```

---

## Convenciones de Commits

Al completar cada tarea padre, usar el siguiente formato de commit:

```bash
git commit -m "feat(módulo): descripción breve" -m "- Detalle 1" -m "- Detalle 2" -m "Ref: Task X.0"
```

Ejemplos:
- `feat(setup): configuración inicial del proyecto`
- `feat(etl): módulo de carga y procesamiento de datos`
- `feat(plots): funciones de visualización Plotly`
- `feat(ui): interfaz principal con navegación y filtros`
- `feat(views): vistas Resumen, Upstream y Downstream`
- `feat(alerts): sistema de alertas y exportación CSV`

---

**Última actualización:** Diciembre 2024  
**Próximo paso:** Iniciar con tarea 1.1

