# 📊 PRD: Oleoflores Business Intelligence Suite (v1.0)

---

## 1. Introducción / Resumen Ejecutivo

### Descripción General
Desarrollo de una aplicación web de **Business Intelligence** escalable y dinámica para el **Grupo Oleoflores**. El objetivo principal es migrar de reportes estáticos en Excel a un dashboard interactivo que visualice la cadena de valor completa (Farm-to-Fork).

### Problema que Resuelve
Actualmente, el proceso de análisis de datos en Oleoflores depende de:
- Reportes manuales en Excel que consumen tiempo significativo
- Falta de visualización integrada de toda la cadena de valor
- Dificultad para comparar métricas Real vs Presupuesto en tiempo real
- Acceso limitado a información actualizada para diferentes niveles de la organización

### Solución Propuesta
Un dashboard interactivo basado en web que permita:
- Análisis semanal, mensual y anual de indicadores
- Visualización de datos Upstream (Campo/Extractora) y Downstream (Refinería/Productos)
- Carga de datos mediante archivos CSV/Excel sin integración directa a sistemas ERP
- Acceso diferenciado según el rol del usuario

---

## 2. Objetivos (Goals)

| ID | Objetivo | Métrica de Éxito | Prioridad |
|----|----------|------------------|-----------|
| G1 | Centralizar la visualización de KPIs de toda la cadena de valor | Dashboard operativo con 100% de métricas definidas | Alta |
| G2 | Reducir el tiempo de generación de reportes ejecutivos | De días a minutos (actualización inmediata al cargar CSV) | Alta |
| G3 | Facilitar la comparación Real vs Presupuesto | Variaciones calculadas automáticamente en todas las vistas | Alta |
| G4 | Democratizar el acceso a información para todos los niveles | Usuarios de C-Level hasta Analistas puedan usar el sistema | Media |
| G5 | Identificar rápidamente desviaciones y alertas | Sistema de alertas visuales para valores fuera de rango | Media |

---

## 3. Usuarios Objetivo

### 3.1 Perfiles de Usuario

| Perfil | Descripción | Necesidades Principales |
|--------|-------------|------------------------|
| **Ejecutivos C-Level** | CEO, CFO, COO | Vista de alto nivel, KPIs resumidos, tendencias macro |
| **Gerentes de Planta** | Responsables de operaciones en cada zona | Métricas operativas diarias, TEA, eficiencia de extracción |
| **Supervisores Operativos** | Personal de campo y extractora | Detalle de producción por zona, comparativas |
| **Analistas/Controllers** | Área financiera y de datos | Datos exportables, drill-down detallado, comparativas presupuestales |

### 3.2 Niveles de Acceso
Todos los usuarios tendrán acceso al sistema, pero las vistas estarán optimizadas para cada perfil:
- **Vista Ejecutiva**: Resumen con KPIs principales
- **Vista Operativa**: Detalle por zona y proceso
- **Vista Analítica**: Datos completos con capacidad de exportación

---

## 4. Historias de Usuario

### Historia 1: Monitoreo de TEA Diaria
> **Como** gerente de planta,  
> **Quiero** ver la Tasa de Extracción de Aceite (TEA) diaria de mi zona,  
> **Para** identificar problemas de extracción rápidamente y tomar acciones correctivas inmediatas.

**Criterios de Aceptación:**
- [ ] El dashboard muestra la TEA actualizada del día actual
- [ ] Se visualiza mediante un gráfico tipo Gauge (velocímetro)
- [ ] Se indica claramente si está por encima o debajo de la meta técnica
- [ ] Se puede filtrar por zona específica

### Historia 2: Resumen Ejecutivo Semanal
> **Como** ejecutivo,  
> **Quiero** ver un resumen semanal de producción vs presupuesto,  
> **Para** tomar decisiones estratégicas informadas sobre el negocio.

**Criterios de Aceptación:**
- [ ] Vista consolidada con los 4 KPIs principales en tarjetas (Scorecards)
- [ ] Indicadores visuales de variación (flechas verdes/rojas)
- [ ] Gráfico de tendencia comparando Real vs Presupuesto
- [ ] Selección de rango de fechas (semana, mes, YTD)

### Historia 3: Exportación de Datos para Análisis
> **Como** analista,  
> **Quiero** exportar los datos filtrados del dashboard,  
> **Para** realizar análisis adicionales en Excel u otras herramientas.

**Criterios de Aceptación:**
- [ ] Botón de exportación visible en cada vista de datos
- [ ] Exportación en formato CSV
- [ ] Los filtros aplicados se reflejan en los datos exportados
- [ ] Incluye todas las columnas relevantes del dataset

### Historia 4: Carga de Datos Actualizada
> **Como** usuario del sistema,  
> **Quiero** cargar un nuevo archivo CSV/Excel con datos actualizados,  
> **Para** que el dashboard refleje la información más reciente sin necesidad de soporte técnico.

**Criterios de Aceptación:**
- [ ] Interfaz de carga de archivos en la aplicación
- [ ] Validación automática del formato del archivo
- [ ] Mensaje de confirmación tras carga exitosa
- [ ] Actualización inmediata de todas las visualizaciones

### Historia 5: Visualización de Flujo de Masa
> **Como** gerente de producción,  
> **Quiero** ver el flujo completo de transformación del CPO hacia productos finales,  
> **Para** identificar dónde se generan mermas y optimizar el proceso.

**Criterios de Aceptación:**
- [ ] Diagrama Sankey mostrando: Entrada CPO → Refinería → Productos
- [ ] Visualización clara de las mermas en el proceso
- [ ] Colores diferenciados por tipo de producto
- [ ] Interactividad (hover para ver valores exactos)

---

## 5. Requerimientos Funcionales

### 5.1 Módulo de Carga de Datos
| ID | Requerimiento | Prioridad |
|----|---------------|-----------|
| RF-01 | El sistema debe permitir cargar archivos CSV y Excel (.xlsx) | Alta |
| RF-02 | El sistema debe validar la estructura de columnas del archivo cargado | Alta |
| RF-03 | El sistema debe mostrar errores claros si el formato es incorrecto | Alta |
| RF-04 | El sistema debe limpiar automáticamente formatos numéricos (eliminar ",", convertir "%") | Alta |
| RF-05 | El sistema debe unificar formatos de fecha a datetime estándar | Alta |

### 5.2 Módulo de Navegación y Filtros
| ID | Requerimiento | Prioridad |
|----|---------------|-----------|
| RF-06 | El sistema debe mostrar una barra lateral (sidebar) con navegación | Alta |
| RF-07 | El sistema debe permitir seleccionar vista: Resumen Ejecutivo, Upstream, Downstream | Alta |
| RF-08 | El sistema debe incluir filtros globales de fecha (Semana, Mes, Año, YTD) | Alta |
| RF-09 | El sistema debe incluir selector de Zona (aplicable a vistas Upstream) | Alta |
| RF-10 | Los filtros deben aplicarse en tiempo real sin recargar la página | Alta |

### 5.3 Módulo Resumen Ejecutivo (C-Level)
| ID | Requerimiento | Prioridad |
|----|---------------|-----------|
| RF-11 | El sistema debe mostrar 4 Scorecards con KPIs principales | Alta |
| RF-12 | Cada Scorecard debe incluir: Valor Actual + Indicador de Variación (flecha verde/roja) | Alta |
| RF-13 | KPIs a mostrar: Toneladas RFF, TEA Promedio, Producción CPO, Producción Margarinas | Alta |
| RF-14 | El sistema debe mostrar gráfico de línea: Producción Total Real vs Presupuesto | Alta |

### 5.4 Módulo UPSTREAM (Agroindustria)
| ID | Requerimiento | Prioridad |
|----|---------------|-----------|
| RF-15 | El sistema debe mostrar Bar Chart agrupado: RFF por Zona (Real vs Meta) | Alta |
| RF-16 | El sistema debe mostrar Gauge Chart para TEA con meta técnica | Alta |
| RF-17 | El sistema debe mostrar Heatmap de Cosecha (Días x Zonas x Intensidad) | Media |
| RF-18 | Zonas incluidas: Codazzi, MLB, A&G, Sinú | Alta |

### 5.5 Módulo DOWNSTREAM (Refinería y B2C)
| ID | Requerimiento | Prioridad |
|----|---------------|-----------|
| RF-19 | El sistema debe mostrar Diagrama Sankey del flujo de masa | Alta |
| RF-20 | Flujo Sankey: CPO → Refinería → [Oleína, RBD, Margarinas, Mermas] | Alta |
| RF-21 | El sistema debe mostrar Area Chart apilado de inventarios | Media |
| RF-22 | El sistema debe mostrar Bullet Graph de cumplimiento por SKU | Media |

### 5.6 Módulo de Exportación
| ID | Requerimiento | Prioridad |
|----|---------------|-----------|
| RF-23 | El sistema debe permitir exportar datos filtrados a CSV | Media |
| RF-24 | La exportación debe respetar los filtros aplicados | Media |

### 5.7 Sistema de Alertas
| ID | Requerimiento | Prioridad |
|----|---------------|-----------|
| RF-25 | El sistema debe mostrar alerta visual cuando un valor esté fuera de rango lógico | Alta |
| RF-26 | Ejemplo de alerta: TEA > 100% debe disparar indicador de error | Alta |
| RF-27 | Las alertas deben ser visualmente distinguibles (color rojo, ícono de advertencia) | Alta |

---

## 6. No-Goals (Fuera de Alcance v1.0)

Las siguientes funcionalidades **NO** serán incluidas en esta versión:

| ID | Funcionalidad Excluida | Razón |
|----|------------------------|-------|
| NG-01 | Integración en tiempo real con sistemas ERP/SAP | Se usará carga manual de CSV/Excel |
| NG-02 | Sistema de alertas automáticas por email | Fuera del MVP |
| NG-03 | Predicciones con Machine Learning | Complejidad adicional no requerida inicialmente |
| NG-04 | Gestión de usuarios y permisos (autenticación) | Se asume acceso controlado por red interna |
| NG-05 | Exportación a PDF/PowerPoint | No prioritario para v1.0 |
| NG-06 | Aplicación móvil nativa | El dashboard web será responsive |
| NG-07 | Histórico de versiones de archivos cargados | No requerido inicialmente |

---

## 7. Arquitectura de Datos

### 7.1 Stack Tecnológico
| Componente | Tecnología | Justificación |
|------------|------------|---------------|
| Lenguaje | Python 3.9+ | Ecosistema robusto para análisis de datos |
| Framework Web | Streamlit | Rapidez de despliegue, facilidad de mantenimiento |
| Visualización | Plotly Graph Objects | Máxima interactividad y personalización |
| Manipulación de Datos | Pandas | Estándar de la industria para ETL |
| Entorno de Desarrollo | Cursor | AI-First Code Editor |

### 7.2 Estructura de Archivos de Entrada

#### Dataset A: UPSTREAM
- **Contenido:** RFF (Recepción de Fruta), Producción CPO, Palmiste, TEA
- **Granularidad:** Diaria/Semanal
- **Dimensiones:** Zonas (Codazzi, MLB, A&G, Sinú)

#### Dataset B: DOWNSTREAM
- **Contenido:** Refinería (1 y 2), Oleína, Margarinas, Mermas
- **Granularidad:** Diaria/Semanal
- **Comparativa:** Planta (Presupuesto) vs Real

#### Dataset C: COSTOS/ACUMULADOS
- **Contenido:** Datos históricos y acumulados anuales
- **Uso:** Proyecciones y comparativas YTD

### 7.3 Requerimientos de ETL
- **Limpieza Automática:** Detectar y reparar formatos numéricos
- **Manejo de Fechas:** Unificación a formato `datetime` estándar
- **Cálculo de Deltas:** `Variación = Real - Presupuesto` y `% Cumplimiento`

---

## 8. Diseño y UI/UX

### 8.1 Principios de Diseño
- Interfaz limpia y profesional
- Priorizar la legibilidad de datos
- Navegación intuitiva entre módulos
- Responsive para diferentes tamaños de pantalla

### 8.2 Paleta de Colores Corporativa
| Elemento | Color | Código Hex |
|----------|-------|------------|
| Fondo principal | Gris muy claro | `#f9f9f9` |
| Verde Oleo (positivo) | Verde | `#2E7D32` |
| Dorado Aceite (neutro) | Amarillo/Dorado | `#F9A825` |
| Alerta Rojo (negativo) | Rojo | `#C62828` |
| Texto principal | Gris oscuro | `#333333` |

### 8.3 Componentes Visuales
- **Scorecards:** Tarjetas grandes con valor + indicador de variación
- **Gráficos de Barras:** Comparativas Real vs Meta
- **Gauge (Velocímetro):** Para indicadores porcentuales como TEA
- **Sankey Diagram:** Flujo de masa en refinería
- **Heatmap:** Intensidad de cosecha por zona y día
- **Area Chart:** Evolución de inventarios
- **Bullet Graph:** Cumplimiento por SKU

---

## 9. Manejo de Errores y Casos Edge

### 9.1 Escenarios y Comportamiento Esperado

| Escenario | Comportamiento del Sistema |
|-----------|---------------------------|
| Archivo CSV faltante | Mostrar mensaje de error claro indicando qué archivo falta. Usar último archivo disponible si existe. |
| Datos incompletos en una semana | Mostrar vacío en las visualizaciones afectadas. No interpolar ni estimar valores. |
| Valor fuera de rango lógico (ej. TEA > 100%) | Mostrar **alerta visual** destacada. Permitir visualización pero con indicador de advertencia. |
| Formato de archivo incorrecto | Rechazar carga y mostrar mensaje con el formato esperado. |
| Columnas faltantes en el archivo | Listar columnas faltantes en mensaje de error. |

### 9.2 Validaciones de Datos
- TEA debe estar entre 0% y 35% (alerta si excede)
- Fechas deben ser válidas y no futuras
- Valores numéricos no pueden ser negativos (excepto variaciones)
- Zonas deben coincidir con catálogo definido

---

## 10. Métricas de Éxito

### 10.1 KPIs del Proyecto

| Métrica | Valor Objetivo | Método de Medición |
|---------|----------------|-------------------|
| Tiempo de generación de reportes | < 5 minutos (vs horas actuales) | Tiempo desde carga de CSV hasta visualización completa |
| Disponibilidad del sistema | 99% uptime | Monitoreo de servidor |
| Adopción de usuarios | 80% de usuarios objetivo activos en mes 2 | Logs de acceso |
| Errores de datos detectados | Reducción 90% vs proceso manual | Comparativa con auditorías previas |
| Satisfacción de usuarios | > 4/5 en encuesta | Encuesta post-implementación |

### 10.2 Criterios de Aceptación del Proyecto
- [ ] Dashboard desplegado y accesible desde red interna
- [ ] Los 3 módulos principales funcionando (Resumen, Upstream, Downstream)
- [ ] Carga de archivos CSV operativa
- [ ] Todos los KPIs definidos visibles con datos reales
- [ ] Sistema de alertas para valores fuera de rango activo
- [ ] Exportación de datos a CSV funcional

---

## 11. Estructura de Código Recomendada

```
oleoflores-bi-dashboard/
├── app.py                 # Punto de entrada principal (interfaz Streamlit)
├── requirements.txt       # Dependencias del proyecto
├── README.md             # Documentación de uso
├── data/                 # Carpeta para archivos CSV de entrada
│   ├── upstream.csv
│   ├── downstream.csv
│   └── costos.csv
├── src/                  # Módulos de código
│   ├── __init__.py
│   ├── data_loader.py    # Lógica de carga y limpieza de datos
│   ├── plots.py          # Configuración de gráficas Plotly
│   └── utils.py          # Funciones auxiliares
└── assets/               # Recursos estáticos (logos, estilos)
    └── logo.png
```

---

## 12. Plan de Implementación Sugerido

### Fase 1: Fundamentos (Semana 1-2)
- [ ] Configuración del proyecto y entorno
- [ ] Desarrollo del módulo `data_loader.py`
- [ ] Pruebas de carga y limpieza de datos

### Fase 2: Visualizaciones Core (Semana 3-4)
- [ ] Desarrollo del módulo `plots.py`
- [ ] Implementación de Scorecards
- [ ] Implementación de gráficos Upstream (barras, gauge, heatmap)

### Fase 3: Visualizaciones Avanzadas (Semana 5-6)
- [ ] Diagrama Sankey (Downstream)
- [ ] Area charts y Bullet graphs
- [ ] Sistema de alertas visuales

### Fase 4: Integración y Pulido (Semana 7-8)
- [ ] Ensamblaje en `app.py`
- [ ] Implementación de filtros globales
- [ ] Exportación de datos
- [ ] Pruebas de usuario y ajustes

---

## 13. Preguntas Abiertas

| ID | Pregunta | Estado |
|----|----------|--------|
| Q1 | ¿Se requiere autenticación básica (usuario/contraseña) aunque no haya gestión de permisos? | Pendiente |
| Q2 | ¿Existe un manual de marca oficial de Oleoflores para usar logos oficiales? | Pendiente |
| Q3 | ¿Cuáles son los rangos "normales" esperados para cada KPI (para configurar alertas)? | Pendiente |
| Q4 | ¿Dónde se desplegará la aplicación? (servidor interno, cloud, etc.) | Pendiente |
| Q5 | ¿Se requiere soporte para múltiples idiomas? | Pendiente |

---

## 14. Apéndice: Dependencias Técnicas

### requirements.txt
```
streamlit>=1.28.0
pandas>=2.0.0
plotly>=5.18.0
openpyxl>=3.1.0
python-dateutil>=2.8.0
```

---

**Documento creado:** Diciembre 2024  
**Versión:** 1.0  
**Autor:** Equipo de Desarrollo Oleoflores  
**Última actualización:** Por definir tras revisión

---

