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
    create_empty_chart,
    create_tank_chart,
    get_semaforo_color,
    format_table_with_semaforo,
    create_quality_table
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
        # =====================================================================
        # FILA 1: TABLAS CON SEMÁFOROS (RFF, CPO, TEA)
        # =====================================================================
        col1, col2, col3 = st.columns(3)
        
        # Agregar datos por zona
        df_zona = df_upstream.groupby('zona').agg({
            'rff_real': 'sum',
            'rff_presupuesto': 'sum',
            'cpo_real': 'sum',
            'cpo_presupuesto': 'sum',
            'tea_real': 'mean',
            'tea_meta': 'mean'
        }).reset_index()
        
        with col1:
            st.subheader("📦 RFF Procesada")
            # Crear tabla RFF con semáforos
            df_rff = df_zona[['zona', 'rff_presupuesto', 'rff_real']].copy()
            df_rff.columns = ['Planta', 'ME', 'Real']
            df_rff['Dif'] = df_rff['Real'] - df_rff['ME']
            df_rff['%'] = (df_rff['Real'] / df_rff['ME'] * 100)
            df_rff['% Cumpl'] = df_rff['%'].apply(lambda x: f"{get_semaforo_color(x)} {x:.0f}%")
            
            # Agregar fila TOTAL
            total_rff = pd.DataFrame({
                'Planta': ['**TOTAL**'],
                'ME': [df_rff['ME'].sum()],
                'Real': [df_rff['Real'].sum()],
                'Dif': [df_rff['Dif'].sum()],
                '%': [df_rff['Real'].sum() / df_rff['ME'].sum() * 100],
            })
            total_rff['% Cumpl'] = total_rff['%'].apply(lambda x: f"{get_semaforo_color(x)} {x:.0f}%")
            
            df_rff_display = pd.concat([df_rff[['Planta', 'ME', 'Real', 'Dif', '% Cumpl']], 
                                        total_rff[['Planta', 'ME', 'Real', 'Dif', '% Cumpl']]])
            df_rff_display['ME'] = df_rff_display['ME'].apply(lambda x: f"{x:,.0f}")
            df_rff_display['Real'] = df_rff_display['Real'].apply(lambda x: f"{x:,.0f}")
            df_rff_display['Dif'] = df_rff_display['Dif'].apply(lambda x: f"{x:+,.0f}")
            
            st.dataframe(df_rff_display, use_container_width=True, hide_index=True)
        
        with col2:
            st.subheader("🛢️ CPO")
            # Crear tabla CPO con semáforos
            df_cpo = df_zona[['zona', 'cpo_presupuesto', 'cpo_real']].copy()
            df_cpo.columns = ['Planta', 'CPO ME', 'CPO Real']
            df_cpo['Dif TM'] = df_cpo['CPO Real'] - df_cpo['CPO ME']
            df_cpo['%'] = (df_cpo['CPO Real'] / df_cpo['CPO ME'] * 100)
            df_cpo['% Cumpl'] = df_cpo['%'].apply(lambda x: f"{get_semaforo_color(x)} {x:.0f}%")
            
            # Agregar fila TOTAL
            total_cpo = pd.DataFrame({
                'Planta': ['**TOTAL**'],
                'CPO ME': [df_cpo['CPO ME'].sum()],
                'CPO Real': [df_cpo['CPO Real'].sum()],
                'Dif TM': [df_cpo['Dif TM'].sum()],
                '%': [df_cpo['CPO Real'].sum() / df_cpo['CPO ME'].sum() * 100],
            })
            total_cpo['% Cumpl'] = total_cpo['%'].apply(lambda x: f"{get_semaforo_color(x)} {x:.0f}%")
            
            df_cpo_display = pd.concat([df_cpo[['Planta', 'CPO ME', 'CPO Real', 'Dif TM', '% Cumpl']], 
                                        total_cpo[['Planta', 'CPO ME', 'CPO Real', 'Dif TM', '% Cumpl']]])
            df_cpo_display['CPO ME'] = df_cpo_display['CPO ME'].apply(lambda x: f"{x:,.0f}")
            df_cpo_display['CPO Real'] = df_cpo_display['CPO Real'].apply(lambda x: f"{x:,.0f}")
            df_cpo_display['Dif TM'] = df_cpo_display['Dif TM'].apply(lambda x: f"{x:+,.0f}")
            
            st.dataframe(df_cpo_display, use_container_width=True, hide_index=True)
        
        with col3:
            st.subheader("🎯 TAE%")
            # Crear tabla TEA con semáforos
            df_tea = df_zona[['zona', 'tea_meta', 'tea_real']].copy()
            df_tea.columns = ['Planta', 'TEA ME', 'TEA Real']
            df_tea['Dif'] = df_tea['TEA Real'] - df_tea['TEA ME']
            # Para TEA, positivo es bueno
            df_tea['Semáforo'] = df_tea['Dif'].apply(lambda x: '🟢' if x >= 0 else ('🟡' if x >= -0.5 else '🔴'))
            df_tea['DIF'] = df_tea.apply(lambda x: f"{x['Semáforo']} {x['Dif']:+.1f}%", axis=1)
            
            # Agregar fila TOTAL
            total_tea = pd.DataFrame({
                'Planta': ['**TOTAL**'],
                'TEA ME': [df_tea['TEA ME'].iloc[:-1].mean() if len(df_tea) > 1 else df_tea['TEA ME'].mean()],
                'TEA Real': [df_tea['TEA Real'].iloc[:-1].mean() if len(df_tea) > 1 else df_tea['TEA Real'].mean()],
            })
            total_tea['Dif'] = total_tea['TEA Real'] - total_tea['TEA ME']
            total_tea['Semáforo'] = total_tea['Dif'].apply(lambda x: '🟢' if x >= 0 else ('🟡' if x >= -0.5 else '🔴'))
            total_tea['DIF'] = total_tea.apply(lambda x: f"{x['Semáforo']} {x['Dif']:+.1f}%", axis=1)
            
            df_tea_display = pd.concat([df_tea[['Planta', 'TEA ME', 'TEA Real', 'DIF']], 
                                        total_tea[['Planta', 'TEA ME', 'TEA Real', 'DIF']]])
            df_tea_display['TEA ME'] = df_tea_display['TEA ME'].apply(lambda x: f"{x:.1f}%")
            df_tea_display['TEA Real'] = df_tea_display['TEA Real'].apply(lambda x: f"{x:.1f}%")
            
            st.dataframe(df_tea_display, use_container_width=True, hide_index=True)
        
        st.divider()
        
        # =====================================================================
        # FILA 2: INVENTARIO CPO + TANQUES
        # =====================================================================
        st.subheader("🏗️ Inventario CPO y Niveles de Tanques")
        
        col_inv, col_tank = st.columns([1, 2])
        
        with col_inv:
            # Tabla de inventario CPO
            if 'inventario_cpo' in df_upstream.columns:
                df_inv = df_upstream.groupby('zona').agg({
                    'inventario_cpo': 'last'
                }).reset_index()
                df_inv.columns = ['Planta', 'TM']
                df_inv['TM'] = df_inv['TM'].apply(lambda x: f"{x:,.0f}")
                
                # Total
                total_inv = df_upstream.groupby('zona')['inventario_cpo'].last().sum()
                df_inv_total = pd.DataFrame({'Planta': ['**TOTAL**'], 'TM': [f"{total_inv:,.0f}"]})
                df_inv = pd.concat([df_inv, df_inv_total])
                
                st.markdown("**Inventario CPO por Planta**")
                st.dataframe(df_inv, use_container_width=True, hide_index=True)
        
        with col_tank:
            # Gráficos de tanques por zona
            if all(col in df_upstream.columns for col in ['tanque_1', 'tanque_2']):
                tabs_tanques = st.tabs(["Codazzi", "MLB", "A&G", "Sinú"])
                
                for i, zona in enumerate(["Codazzi", "MLB", "A&G", "Sinú"]):
                    with tabs_tanques[i]:
                        df_zona_tank = df_upstream[df_upstream['zona'] == zona].iloc[-1] if zona in df_upstream['zona'].values else None
                        
                        if df_zona_tank is not None:
                            tanques = {}
                            for j in range(1, 5):
                                col_tank_name = f'tanque_{j}'
                                if col_tank_name in df_upstream.columns and df_zona_tank[col_tank_name] > 0:
                                    tanques[f'TK {j}'] = df_zona_tank[col_tank_name]
                            
                            if tanques:
                                fig_tank = create_tank_chart(
                                    tanques=tanques,
                                    title=f"Tanques CPO - {zona}",
                                    color_lleno="#F9A825" if zona != "Codazzi" else "#F9A825"
                                )
                                st.plotly_chart(fig_tank, use_container_width=True)
                            else:
                                st.info(f"No hay datos de tanques para {zona}")
        
        st.divider()
        
        # =====================================================================
        # FILA 3: PARÁMETROS DE CALIDAD
        # =====================================================================
        if 'acidez' in df_upstream.columns:
            st.subheader("🔬 Parámetros de Calidad del CPO")
            
            df_calidad = create_quality_table(df_upstream)
            if not df_calidad.empty:
                st.dataframe(df_calidad, use_container_width=True, hide_index=True)
                st.caption("🟢 Óptimo | 🟡 Aceptable | 🔴 Fuera de rango")
        
        st.divider()
        
        # =====================================================================
        # FILA 4: ALMENDRA Y KPO (si existen los datos)
        # =====================================================================
        if 'almendra_real' in df_upstream.columns:
            st.subheader("🥜 Almendra y KPO")
            
            col_alm, col_kpo = st.columns(2)
            
            with col_alm:
                # Solo Codazzi tiene datos de almendra
                df_alm = df_upstream[df_upstream['almendra_real'] > 0].groupby('zona').agg({
                    'almendra_presupuesto': 'sum',
                    'almendra_real': 'sum'
                }).reset_index()
                
                if not df_alm.empty:
                    df_alm['Dif'] = df_alm['almendra_real'] - df_alm['almendra_presupuesto']
                    df_alm['%'] = (df_alm['almendra_real'] / df_alm['almendra_presupuesto'] * 100)
                    df_alm['% Cumpl'] = df_alm['%'].apply(lambda x: f"{get_semaforo_color(x)} {x:.0f}%")
                    df_alm.columns = ['Producto', 'ME', 'Real', 'Dif', '%', '% Cumpl']
                    df_alm['Producto'] = 'ALMENDRA'
                    df_alm['ME'] = df_alm['ME'].apply(lambda x: f"{x:,.0f}")
                    df_alm['Real'] = df_alm['Real'].apply(lambda x: f"{x:,.0f}")
                    df_alm['Dif'] = df_alm['Dif'].apply(lambda x: f"{x:+,.0f}")
                    
                    st.dataframe(df_alm[['Producto', 'ME', 'Real', 'Dif', '% Cumpl']], 
                                use_container_width=True, hide_index=True)
            
            with col_kpo:
                df_kpo = df_upstream[df_upstream['kpo_real'] > 0].groupby('zona').agg({
                    'kpo_presupuesto': 'sum',
                    'kpo_real': 'sum',
                    'extraccion_almendra': 'mean'
                }).reset_index()
                
                if not df_kpo.empty:
                    df_kpo['Dif'] = df_kpo['kpo_real'] - df_kpo['kpo_presupuesto']
                    df_kpo['%'] = (df_kpo['kpo_real'] / df_kpo['kpo_presupuesto'] * 100)
                    df_kpo['% Cumpl'] = df_kpo['%'].apply(lambda x: f"{get_semaforo_color(x)} {x:.0f}%")
                    df_kpo['Extracción'] = df_kpo['extraccion_almendra'].apply(lambda x: f"{x:.1f}%")
                    df_kpo.columns = ['Producto', 'ME', 'Real', 'Extracción %', 'Dif', '%', '% Cumpl', 'Extracción']
                    df_kpo['Producto'] = 'KPO'
                    
                    st.markdown(f"**Extracción Almendra:** {df_kpo['Extracción'].iloc[0]}")
                    df_kpo_display = df_kpo[['Producto', 'ME', 'Real', 'Dif', '% Cumpl']].copy()
                    df_kpo_display['ME'] = df_kpo['ME'].apply(lambda x: f"{x:,.0f}")
                    df_kpo_display['Real'] = df_kpo['Real'].apply(lambda x: f"{x:,.0f}")
                    df_kpo_display['Dif'] = df_kpo['Dif'].apply(lambda x: f"{x:+,.0f}")
                    st.dataframe(df_kpo_display, use_container_width=True, hide_index=True)
        
        st.divider()
        
        # =====================================================================
        # FILA 5: GRÁFICOS ADICIONALES
        # =====================================================================
        col_graph1, col_graph2 = st.columns(2)
        
        with col_graph1:
            st.subheader("📊 RFF por Zona: Real vs Meta")
            fig_barras = create_grouped_bar_chart(
                df_zona,
                x_column='zona',
                y_columns=['rff_real', 'rff_presupuesto'],
                y_names=['Real', 'Presupuesto'],
                title=''
            )
            st.plotly_chart(fig_barras, use_container_width=True)
        
        with col_graph2:
            st.subheader("🎯 TEA Promedio")
            tea_actual = df_upstream['tea_real'].mean()
            tea_meta = df_upstream['tea_meta'].mean()
            
            fig_gauge = create_gauge_chart(
                value=tea_actual,
                title='',
                target=tea_meta
            )
            st.plotly_chart(fig_gauge, use_container_width=True)
        
        # Heatmap
        st.subheader("🗓️ Mapa de Calor - Intensidad de Cosecha")
        fig_heatmap = create_heatmap(
            df_upstream,
            x_column='fecha',
            y_column='zona',
            value_column='rff_real',
            title=''
        )
        st.plotly_chart(fig_heatmap, use_container_width=True)
        
        # Exportación
        st.divider()
        col_tabla, col_export = st.columns([3, 1])
        
        with col_tabla:
            with st.expander("📋 Ver todos los datos"):
                st.dataframe(df_upstream, use_container_width=True, hide_index=True)
        
        with col_export:
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
        # =====================================================================
        # FILA 1: TABLA CON SEMÁFOROS + INVENTARIO
        # =====================================================================
        col_tabla, col_inv = st.columns([2, 1])
        
        with col_tabla:
            st.subheader("🏭 Producción Downstream")
            
            # Agregar datos por refinería/producto
            df_ref1 = df_downstream[df_downstream['refineria'] == 1].agg({
                'cpo_entrada': 'sum',
                'oleina_real': 'sum',
                'oleina_presupuesto': 'sum',
                'rbd_real': 'sum',
                'rbd_presupuesto': 'sum',
                'margarinas_real': 'sum',
                'margarinas_presupuesto': 'sum'
            })
            
            df_ref2 = df_downstream[df_downstream['refineria'] == 2].agg({
                'cpo_entrada': 'sum',
                'rbd_real': 'sum',
                'rbd_presupuesto': 'sum'
            })
            
            # Crear tabla de downstream
            data_down = []
            
            # Refinería 1
            pct_ref1 = (df_ref1['cpo_entrada'] / 8670 * 100) if 8670 > 0 else 0
            data_down.append({
                'Planta': 'REFINERIA 1',
                'ME': f"{8670:,.0f}",
                'Real': f"{df_ref1['cpo_entrada']:,.0f}",
                'Dif': f"{df_ref1['cpo_entrada'] - 8670:+,.0f}",
                '% Cumpl': f"{get_semaforo_color(pct_ref1)} {pct_ref1:.0f}%"
            })
            
            # Refinería 2
            pct_ref2 = (df_ref2['cpo_entrada'] / 770 * 100) if 770 > 0 else 0
            data_down.append({
                'Planta': 'REFINERIA 2',
                'ME': f"{770:,.0f}",
                'Real': f"{df_ref2['cpo_entrada']:,.0f}",
                'Dif': f"{df_ref2['cpo_entrada'] - 770:+,.0f}",
                '% Cumpl': f"{get_semaforo_color(pct_ref2)} {pct_ref2:.0f}%"
            })
            
            # Oleína
            pct_oleina = (df_ref1['oleina_real'] / df_ref1['oleina_presupuesto'] * 100) if df_ref1['oleina_presupuesto'] > 0 else 0
            data_down.append({
                'Planta': 'OLEINA',
                'ME': f"{df_ref1['oleina_presupuesto']:,.0f}",
                'Real': f"{df_ref1['oleina_real']:,.0f}",
                'Dif': f"{df_ref1['oleina_real'] - df_ref1['oleina_presupuesto']:+,.0f}",
                '% Cumpl': f"{get_semaforo_color(pct_oleina)} {pct_oleina:.0f}%"
            })
            
            # Margarinas
            pct_marg = (df_ref1['margarinas_real'] / df_ref1['margarinas_presupuesto'] * 100) if df_ref1['margarinas_presupuesto'] > 0 else 0
            data_down.append({
                'Planta': 'MARGARINAS',
                'ME': f"{df_ref1['margarinas_presupuesto']:,.0f}",
                'Real': f"{df_ref1['margarinas_real']:,.0f}",
                'Dif': f"{df_ref1['margarinas_real'] - df_ref1['margarinas_presupuesto']:+,.0f}",
                '% Cumpl': f"{get_semaforo_color(pct_marg)} {pct_marg:.0f}%"
            })
            
            # Total
            total_me = 8670 + 770 + df_ref1['oleina_presupuesto'] + df_ref1['margarinas_presupuesto']
            total_real = df_ref1['cpo_entrada'] + df_ref2['cpo_entrada'] + df_ref1['oleina_real'] + df_ref1['margarinas_real']
            pct_total = (total_real / total_me * 100) if total_me > 0 else 0
            data_down.append({
                'Planta': '**TOTAL**',
                'ME': f"{total_me:,.0f}",
                'Real': f"{total_real:,.0f}",
                'Dif': f"{total_real - total_me:+,.0f}",
                '% Cumpl': f"{get_semaforo_color(pct_total)} {pct_total:.0f}%"
            })
            
            df_down_table = pd.DataFrame(data_down)
            st.dataframe(df_down_table, use_container_width=True, hide_index=True)
        
        with col_inv:
            st.subheader("📦 Inventario")
            
            # Inventario de productos terminados
            if 'inventario_rbd' in df_downstream.columns:
                last_inv = df_downstream.iloc[-1]
                inv_data = [
                    {'Producto': 'RBD', 'TM': f"{last_inv.get('inventario_rbd', 0):,.0f}"},
                    {'Producto': 'Oleína', 'TM': f"{last_inv.get('inventario_oleina', 0):,.0f}"},
                    {'Producto': 'Margarinas', 'TM': f"{last_inv.get('inventario_margarinas', 0):,.0f}"},
                ]
                df_inv_down = pd.DataFrame(inv_data)
                st.dataframe(df_inv_down, use_container_width=True, hide_index=True)
        
        st.divider()
        
        # =====================================================================
        # FILA 2: DIAGRAMA SANKEY
        # =====================================================================
        st.subheader("🔀 Flujo de Masa - Refinería")
        
        fig_sankey = create_sankey_diagram(
            df=df_downstream,
            title=''
        )
        st.plotly_chart(fig_sankey, use_container_width=True)
        
        st.divider()
        
        # =====================================================================
        # FILA 3: Area Chart + Bullet Chart
        # =====================================================================
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
