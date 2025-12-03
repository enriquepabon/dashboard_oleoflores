"""
Oleoflores BI Dashboard
=======================

Aplicación principal de Business Intelligence para el Grupo Oleoflores.
Visualización de la cadena de valor Farm-to-Fork.

Ejecutar con: streamlit run app.py
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

# Importar módulos locales
from src.data_loader import (
    load_upstream_data,
    load_downstream_data,
    filter_by_date_range,
    filter_by_zones,
    display_data_summary
)
from src.plots import (
    create_scorecard,
    create_gauge_chart,
    create_grouped_bar_chart,
    create_heatmap,
    create_sankey_diagram,
    create_area_chart,
    create_bullet_chart,
    create_trend_line_chart,
    create_empty_chart
)
from src.utils import (
    COLORS, 
    ZONAS, 
    KPIS_CONFIG,
    validate_data_ranges,
    get_alert_summary,
    export_to_csv,
    prepare_export_data
)

# =============================================================================
# 4.1 - CONFIGURACIÓN DE PÁGINA
# =============================================================================

st.set_page_config(
    page_title="Oleoflores BI Dashboard",
    page_icon="🌴",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": """
        ### 🌴 Oleoflores BI Dashboard v1.0
        
        Sistema de Business Intelligence para análisis de la cadena de valor Farm-to-Fork.
        
        **Módulos:**
        - Resumen Ejecutivo
        - Upstream (Campo/Extractora)
        - Downstream (Refinería/Productos)
        
        © 2024 Grupo Oleoflores
        """
    }
)

# =============================================================================
# ESTILOS CSS PERSONALIZADOS
# =============================================================================

st.markdown("""
<style>
    /* Fondo principal */
    .stApp {
        background-color: #f9f9f9;
    }
    
    /* Estilo para métricas/scorecards */
    div[data-testid="metric-container"] {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e0e0e0;
    }
    
    section[data-testid="stSidebar"] > div {
        padding-top: 1rem;
    }
    
    /* Títulos de sección en sidebar */
    .sidebar-title {
        color: #2E7D32;
        font-size: 1.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    
    .sidebar-subtitle {
        color: #666666;
        font-size: 0.85rem;
        margin-bottom: 1.5rem;
    }
    
    /* Botones */
    .stButton > button {
        background-color: #2E7D32;
        color: white;
        border: none;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        font-weight: 500;
    }
    
    .stButton > button:hover {
        background-color: #1B5E20;
        color: white;
    }
    
    /* Radio buttons estilizados */
    div[data-testid="stRadio"] > label {
        font-weight: 500;
        color: #333333;
    }
    
    /* Separadores */
    hr {
        margin: 1rem 0;
        border: none;
        border-top: 1px solid #e0e0e0;
    }
    
    /* Cards/Contenedores */
    .chart-container {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 1rem;
    }
    
    /* Alertas personalizadas */
    .alert-warning {
        background-color: #FFF3E0;
        border-left: 4px solid #F9A825;
        padding: 1rem;
        border-radius: 0 5px 5px 0;
    }
    
    .alert-error {
        background-color: #FFEBEE;
        border-left: 4px solid #C62828;
        padding: 1rem;
        border-radius: 0 5px 5px 0;
    }
    
    .alert-success {
        background-color: #E8F5E9;
        border-left: 4px solid #2E7D32;
        padding: 1rem;
        border-radius: 0 5px 5px 0;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# 4.2 - SIDEBAR: LOGO Y TÍTULO
# =============================================================================

with st.sidebar:
    # Logo y título
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0;">
        <span style="font-size: 3rem;">🌴</span>
        <h1 class="sidebar-title">Oleoflores</h1>
        <p class="sidebar-subtitle">Business Intelligence Dashboard</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()

# =============================================================================
# 4.3 - SIDEBAR: SELECTOR DE VISTA (NAVEGACIÓN)
# =============================================================================

    st.markdown("### 📊 Navegación")
    
    vista_seleccionada = st.radio(
        "Seleccionar Vista",
        options=["🏠 Resumen Ejecutivo", "🌾 Upstream", "🏭 Downstream"],
        index=0,
        label_visibility="collapsed"
    )
    
    st.divider()

# =============================================================================
# 4.4 - SIDEBAR: FILTROS DE FECHA
# =============================================================================

    st.markdown("### 📅 Período")
    
    # Opciones predefinidas de período
    periodo_opciones = {
        "Última Semana": 7,
        "Últimos 15 días": 15,
        "Último Mes": 30,
        "Último Trimestre": 90,
        "YTD (Año actual)": 365,
        "Personalizado": 0
    }
    
    periodo_seleccionado = st.selectbox(
        "Rango de fechas",
        options=list(periodo_opciones.keys()),
        index=0
    )
    
    # Calcular fechas según período
    fecha_fin = datetime.now().date()
    
    if periodo_seleccionado == "Personalizado":
        col_fecha1, col_fecha2 = st.columns(2)
        with col_fecha1:
            fecha_inicio = st.date_input(
                "Desde",
                value=fecha_fin - timedelta(days=30),
                max_value=fecha_fin
            )
        with col_fecha2:
            fecha_fin = st.date_input(
                "Hasta",
                value=fecha_fin,
                max_value=fecha_fin
            )
    else:
        dias = periodo_opciones[periodo_seleccionado]
        fecha_inicio = fecha_fin - timedelta(days=dias)
        st.caption(f"📆 {fecha_inicio.strftime('%d/%m/%Y')} - {fecha_fin.strftime('%d/%m/%Y')}")
    
    st.divider()

# =============================================================================
# 4.5 - SIDEBAR: SELECTOR DE ZONAS
# =============================================================================

    st.markdown("### 🗺️ Zonas")
    
    # Checkbox para seleccionar todas
    todas_zonas = st.checkbox("Seleccionar todas", value=True)
    
    if todas_zonas:
        zonas_seleccionadas = ZONAS
    else:
        zonas_seleccionadas = st.multiselect(
            "Filtrar por zona",
            options=ZONAS,
            default=ZONAS,
            label_visibility="collapsed"
        )
    
    if not zonas_seleccionadas:
        st.warning("⚠️ Selecciona al menos una zona")
        zonas_seleccionadas = ZONAS
    
    st.divider()

# =============================================================================
# 4.6 - SIDEBAR: CARGA DE ARCHIVOS
# =============================================================================

    st.markdown("### 📤 Cargar Datos")
    
    with st.expander("Subir archivos CSV/Excel", expanded=False):
        # Upload para Upstream
        uploaded_upstream = st.file_uploader(
            "Datos Upstream",
            type=['csv', 'xlsx'],
            key="upstream_upload",
            help="Archivo con datos de Campo/Extractora (RFF, CPO, TEA)"
        )
        
        # Upload para Downstream
        uploaded_downstream = st.file_uploader(
            "Datos Downstream",
            type=['csv', 'xlsx'],
            key="downstream_upload",
            help="Archivo con datos de Refinería (Oleína, Margarinas, Mermas)"
        )
        
        if uploaded_upstream or uploaded_downstream:
            st.success("✅ Archivos cargados correctamente")
    
    st.divider()
    
    # Footer del sidebar
    st.markdown("""
    <div style="text-align: center; color: #999; font-size: 0.75rem; padding: 1rem 0;">
        Oleoflores BI v1.0<br>
        © 2024 Grupo Oleoflores
    </div>
    """, unsafe_allow_html=True)

# =============================================================================
# CARGA DE DATOS
# =============================================================================

# Determinar fuente de datos (archivos subidos o datos de ejemplo)
@st.cache_data
def cargar_datos_upstream(uploaded_file=None):
    """Carga datos upstream desde archivo o ejemplo."""
    if uploaded_file is not None:
        return load_upstream_data(uploaded_file)
    return load_upstream_data("data/upstream.csv")

@st.cache_data
def cargar_datos_downstream(uploaded_file=None):
    """Carga datos downstream desde archivo o ejemplo."""
    if uploaded_file is not None:
        return load_downstream_data(uploaded_file)
    return load_downstream_data("data/downstream.csv")

# Cargar datos
df_upstream, error_upstream = cargar_datos_upstream(uploaded_upstream if 'uploaded_upstream' in dir() else None)
df_downstream, error_downstream = cargar_datos_downstream(uploaded_downstream if 'uploaded_downstream' in dir() else None)

# Aplicar filtros de fecha y zona si hay datos
if df_upstream is not None:
    df_upstream = filter_by_date_range(df_upstream, fecha_inicio, fecha_fin)
    df_upstream = filter_by_zones(df_upstream, zonas_seleccionadas)

if df_downstream is not None:
    df_downstream = filter_by_date_range(df_downstream, fecha_inicio, fecha_fin)

# =============================================================================
# 6.1/6.2/6.3 - VALIDACIÓN DE DATOS Y ALERTAS
# =============================================================================

# Validar datos y recolectar alertas
alertas_upstream = validate_data_ranges(df_upstream, "upstream") if df_upstream is not None else []
alertas_downstream = validate_data_ranges(df_downstream, "downstream") if df_downstream is not None else []
todas_alertas = alertas_upstream + alertas_downstream

# =============================================================================
# 4.7 - ÁREA PRINCIPAL: ROUTING DE VISTAS
# =============================================================================

# Header principal
st.title("🌴 Oleoflores BI Dashboard")

# Mostrar errores de carga si existen
if error_upstream:
    st.error(f"⚠️ Error cargando datos Upstream: {error_upstream}")
if error_downstream:
    st.error(f"⚠️ Error cargando datos Downstream: {error_downstream}")

# Mostrar alertas de validación de datos
if todas_alertas:
    resumen_alertas = get_alert_summary(todas_alertas)
    
    with st.expander(f"🚨 **{resumen_alertas['total']} Alertas Detectadas** ({resumen_alertas['errores']} errores, {resumen_alertas['advertencias']} advertencias)", expanded=True):
        for alerta in todas_alertas:
            if alerta["tipo"] == "error":
                st.error(f"{alerta['mensaje']}\n\n{alerta['detalle']}")
            else:
                st.warning(f"{alerta['mensaje']}\n\n{alerta['detalle']}")

# Indicador de filtros activos
filtros_activos = []
if periodo_seleccionado != "YTD (Año actual)":
    filtros_activos.append(f"📅 {periodo_seleccionado}")
if not todas_zonas:
    filtros_activos.append(f"🗺️ {len(zonas_seleccionadas)} zonas")

if filtros_activos:
    st.caption(f"Filtros activos: {' | '.join(filtros_activos)}")

st.divider()

# =============================================================================
# ROUTING: MOSTRAR VISTA SELECCIONADA
# =============================================================================

if vista_seleccionada == "🏠 Resumen Ejecutivo":
    # ----- VISTA: RESUMEN EJECUTIVO -----
    st.header("📊 Resumen Ejecutivo")
    st.markdown("Vista consolidada de los principales indicadores de la cadena de valor.")
    
    if df_upstream is not None and not df_upstream.empty:
        # KPIs en 4 columnas
        col1, col2, col3, col4 = st.columns(4)
        
        # Calcular KPIs
        total_rff = df_upstream['rff_real'].sum()
        total_rff_ppto = df_upstream['rff_presupuesto'].sum()
        tea_promedio = df_upstream['tea_real'].mean()
        tea_meta = df_upstream['tea_meta'].mean()
        total_cpo = df_upstream['cpo_real'].sum()
        total_cpo_ppto = df_upstream['cpo_presupuesto'].sum()
        
        # Margarinas (si hay datos downstream)
        if df_downstream is not None and not df_downstream.empty:
            total_margarinas = df_downstream['margarinas_real'].sum()
            total_marg_ppto = df_downstream['margarinas_presupuesto'].sum()
        else:
            total_margarinas = 0
            total_marg_ppto = 0
        
        with col1:
            delta_rff = total_rff - total_rff_ppto
            st.metric(
                label="📦 Toneladas RFF",
                value=f"{total_rff:,.0f}",
                delta=f"{delta_rff:+,.0f} vs Ppto"
            )
        
        with col2:
            delta_tea = tea_promedio - tea_meta
            st.metric(
                label="🎯 TEA Promedio",
                value=f"{tea_promedio:.1f}%",
                delta=f"{delta_tea:+.1f}% vs Meta"
            )
        
        with col3:
            delta_cpo = total_cpo - total_cpo_ppto
            st.metric(
                label="🛢️ Producción CPO",
                value=f"{total_cpo:,.0f}",
                delta=f"{delta_cpo:+,.0f} vs Ppto"
            )
        
        with col4:
            delta_marg = total_margarinas - total_marg_ppto
            st.metric(
                label="🧈 Margarinas",
                value=f"{total_margarinas:,.0f}",
                delta=f"{delta_marg:+,.0f} vs Ppto"
            )
        
        st.divider()
        
        # Gráfico de tendencia
        st.subheader("📈 Tendencia de Producción")
        
        # Agregar por fecha
        df_tendencia = df_upstream.groupby('fecha').agg({
            'rff_real': 'sum',
            'rff_presupuesto': 'sum',
            'cpo_real': 'sum',
            'cpo_presupuesto': 'sum'
        }).reset_index()
        
        fig_tendencia = create_trend_line_chart(
            df_tendencia,
            x_column='fecha',
            y_real='rff_real',
            y_presupuesto='rff_presupuesto',
            title='RFF: Real vs Presupuesto',
            y_title='Toneladas'
        )
        st.plotly_chart(fig_tendencia, use_container_width=True)
        
        # 6.4/6.5 - Botón de exportación en Resumen
        st.divider()
        col1, col2, col3 = st.columns([2, 1, 1])
        with col2:
            df_export_up = prepare_export_data(df_upstream)
            csv_up, fn_up = export_to_csv(df_export_up, "resumen_upstream")
            if csv_up:
                st.download_button(
                    label="📥 Upstream CSV",
                    data=csv_up,
                    file_name=fn_up,
                    mime="text/csv"
                )
        with col3:
            if df_downstream is not None:
                df_export_down = prepare_export_data(df_downstream)
                csv_down, fn_down = export_to_csv(df_export_down, "resumen_downstream")
                if csv_down:
                    st.download_button(
                        label="📥 Downstream CSV",
                        data=csv_down,
                        file_name=fn_down,
                        mime="text/csv"
                    )
        
    else:
        st.info("📭 No hay datos disponibles. Carga un archivo CSV/Excel para comenzar.")


elif vista_seleccionada == "🌾 Upstream":
    # ----- VISTA: UPSTREAM -----
    st.header("🌾 Upstream - Agroindustria")
    st.markdown("Análisis de eficiencia en campo y extracción por zona.")
    
    if df_upstream is not None and not df_upstream.empty:
        # Fila 1: Barras + Gauge TEA
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("📊 RFF por Zona: Real vs Meta")
            df_zona = df_upstream.groupby('zona').agg({
                'rff_real': 'sum',
                'rff_presupuesto': 'sum'
            }).reset_index()
            
            fig_barras = create_grouped_bar_chart(
                df_zona,
                x_column='zona',
                y_columns=['rff_real', 'rff_presupuesto'],
                y_names=['Real', 'Presupuesto'],
                title=''
            )
            st.plotly_chart(fig_barras, use_container_width=True)
        
        with col2:
            st.subheader("🎯 TEA Promedio")
            tea_actual = df_upstream['tea_real'].mean()
            tea_meta = df_upstream['tea_meta'].mean()
            
            fig_gauge = create_gauge_chart(
                value=tea_actual,
                title='',
                target=tea_meta
            )
            st.plotly_chart(fig_gauge, use_container_width=True)
        
        st.divider()
        
        # Fila 2: Heatmap de cosecha
        st.subheader("🗓️ Mapa de Calor - Intensidad de Cosecha")
        
        fig_heatmap = create_heatmap(
            df_upstream,
            x_column='fecha',
            y_column='zona',
            value_column='rff_real',
            title=''
        )
        st.plotly_chart(fig_heatmap, use_container_width=True)
        
        # Tabla resumen y exportación
        st.divider()
        col_tabla, col_export = st.columns([3, 1])
        
        with col_tabla:
            with st.expander("📋 Ver datos detallados"):
                st.dataframe(
                    df_upstream[['fecha', 'zona', 'rff_real', 'rff_presupuesto', 'tea_real', 'cpo_real']],
                    use_container_width=True,
                    hide_index=True
                )
        
        with col_export:
            # 6.4/6.5 - Botón de exportación
            df_export = prepare_export_data(df_upstream)
            csv_data, filename = export_to_csv(df_export, "upstream")
            if csv_data:
                st.download_button(
                    label="📥 Exportar CSV",
                    data=csv_data,
                    file_name=filename,
                    mime="text/csv",
                    help="Descargar datos filtrados en formato CSV"
                )
    else:
        st.info("📭 No hay datos de Upstream disponibles.")


elif vista_seleccionada == "🏭 Downstream":
    # ----- VISTA: DOWNSTREAM -----
    st.header("🏭 Downstream - Refinería y Productos")
    st.markdown("Balance de masas, inventarios y flujo de producción.")
    
    if df_downstream is not None and not df_downstream.empty:
        # Fila 1: Diagrama Sankey
        st.subheader("🔀 Flujo de Masa - Refinería")
        
        fig_sankey = create_sankey_diagram(
            df=df_downstream,
            title=''
        )
        st.plotly_chart(fig_sankey, use_container_width=True)
        
        st.divider()
        
        # Fila 2: Area Chart + Bullet Chart
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("📈 Evolución de Producción")
            
            # Agregar por fecha
            df_evolucion = df_downstream.groupby('fecha').agg({
                'oleina_real': 'sum',
                'rbd_real': 'sum',
                'margarinas_real': 'sum'
            }).reset_index()
            
            fig_area = create_area_chart(
                df_evolucion,
                x_column='fecha',
                y_columns=['oleina_real', 'rbd_real', 'margarinas_real'],
                y_names=['Oleína', 'RBD', 'Margarinas'],
                title=''
            )
            st.plotly_chart(fig_area, use_container_width=True)
        
        with col2:
            st.subheader("🎯 Cumplimiento por Producto")
            
            # Calcular totales para bullet chart
            productos = ['Oleína', 'RBD', 'Margarinas']
            reales = [
                df_downstream['oleina_real'].sum(),
                df_downstream['rbd_real'].sum(),
                df_downstream['margarinas_real'].sum()
            ]
            presupuestos = [
                df_downstream['oleina_presupuesto'].sum(),
                df_downstream['rbd_presupuesto'].sum(),
                df_downstream['margarinas_presupuesto'].sum()
            ]
            
            fig_bullet = create_bullet_chart(
                categories=productos,
                actuals=reales,
                targets=presupuestos,
                title=''
            )
            st.plotly_chart(fig_bullet, use_container_width=True)
        
        # Tabla resumen y exportación
        st.divider()
        col_tabla, col_export = st.columns([3, 1])
        
        with col_tabla:
            with st.expander("📋 Ver datos detallados"):
                st.dataframe(
                    df_downstream,
                    use_container_width=True,
                    hide_index=True
                )
        
        with col_export:
            # 6.4/6.5 - Botón de exportación
            df_export = prepare_export_data(df_downstream)
            csv_data, filename = export_to_csv(df_export, "downstream")
            if csv_data:
                st.download_button(
                    label="📥 Exportar CSV",
                    data=csv_data,
                    file_name=filename,
                    mime="text/csv",
                    help="Descargar datos filtrados en formato CSV"
                )
    else:
        st.info("📭 No hay datos de Downstream disponibles.")

# =============================================================================
# FOOTER
# =============================================================================

st.divider()
st.markdown(
    """
    <div style='text-align: center; color: #999999; font-size: 12px; padding: 1rem 0;'>
        🌴 <strong>Oleoflores BI Dashboard</strong> v1.0 | 
        Cadena de Valor Farm-to-Fork | 
        © 2024 Grupo Oleoflores
    </div>
    """,
    unsafe_allow_html=True
)
