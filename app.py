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
    
    # Función para calcular semanas del mes
    def calcular_semanas_mes(año, mes):
        """
        Calcula las semanas del mes según la lógica:
        - S1: Del 1ro del mes al primer domingo
        - S2-S4: De lunes a domingo
        - S5: Del último lunes al fin del mes (si aplica)
        """
        from calendar import monthrange
        
        # Primer día del mes
        primer_dia = datetime(año, mes, 1).date()
        # Último día del mes
        ultimo_dia = datetime(año, mes, monthrange(año, mes)[1]).date()
        
        semanas = {}
        
        # S1: Del 1ro al primer domingo
        dia_actual = primer_dia
        # Encontrar el primer domingo (weekday() = 6)
        while dia_actual.weekday() != 6 and dia_actual <= ultimo_dia:
            dia_actual += timedelta(days=1)
        
        if dia_actual <= ultimo_dia:
            semanas['S1'] = (primer_dia, dia_actual)
            dia_actual += timedelta(days=1)  # Lunes siguiente
        else:
            semanas['S1'] = (primer_dia, ultimo_dia)
            return semanas
        
        # S2, S3, S4, S5...
        num_semana = 2
        while dia_actual <= ultimo_dia and num_semana <= 5:
            inicio_semana = dia_actual
            # Buscar el domingo o fin de mes
            while dia_actual.weekday() != 6 and dia_actual < ultimo_dia:
                dia_actual += timedelta(days=1)
            
            semanas[f'S{num_semana}'] = (inicio_semana, dia_actual)
            dia_actual += timedelta(days=1)
            num_semana += 1
        
        return semanas
    
    # Fecha actual
    hoy = datetime.now().date()
    año_actual = hoy.year
    mes_actual = hoy.month
    
    # Calcular semanas del mes actual
    semanas_mes = calcular_semanas_mes(año_actual, mes_actual)
    
    # Selector de mes (para ver meses anteriores)
    meses_disponibles = []
    for i in range(12):
        fecha_mes = hoy.replace(day=1) - timedelta(days=i*30)
        meses_disponibles.append(fecha_mes.strftime('%B %Y').capitalize())
    
    # Crear opciones de período
    opciones_periodo = ["📆 Mes (MTD)", "📅 Año (YTD)"]
    
    # Agregar semanas del mes actual
    for semana, (inicio, fin) in semanas_mes.items():
        opciones_periodo.insert(len(opciones_periodo)-2, f"📊 {semana} ({inicio.day}-{fin.day} {inicio.strftime('%b')})")
    
    opciones_periodo.append("🔧 Personalizado")
    
    periodo_seleccionado = st.selectbox(
        "Rango de fechas",
        options=opciones_periodo,
        index=0  # Por defecto: Mes (MTD)
    )
    
    # Calcular fechas según período seleccionado
    if "Personalizado" in periodo_seleccionado:
        col_fecha1, col_fecha2 = st.columns(2)
        with col_fecha1:
            fecha_inicio = st.date_input(
                "Desde",
                value=hoy.replace(day=1),
                max_value=hoy
            )
        with col_fecha2:
            fecha_fin = st.date_input(
                "Hasta",
                value=hoy,
                max_value=hoy
            )
    elif "MTD" in periodo_seleccionado:
        # Mes hasta la fecha (Month to Date)
        fecha_inicio = hoy.replace(day=1)
        fecha_fin = hoy
    elif "YTD" in periodo_seleccionado:
        # Año hasta la fecha (Year to Date)
        fecha_inicio = datetime(año_actual, 1, 1).date()
        fecha_fin = hoy
    else:
        # Es una semana (S1, S2, S3, S4, S5)
        for semana, (inicio, fin) in semanas_mes.items():
            if semana in periodo_seleccionado:
                fecha_inicio = inicio
                fecha_fin = fin
                break
        else:
            # Fallback
            fecha_inicio = hoy.replace(day=1)
            fecha_fin = hoy
    
    # Mostrar rango seleccionado
    st.caption(f"📆 {fecha_inicio.strftime('%d/%m/%Y')} → {fecha_fin.strftime('%d/%m/%Y')}")
    
    # Selector de mes anterior (opcional)
    with st.expander("📅 Ver otro mes", expanded=False):
        col_mes, col_año = st.columns(2)
        with col_mes:
            mes_sel = st.selectbox(
                "Mes",
                options=list(range(1, 13)),
                index=mes_actual - 1,
                format_func=lambda x: datetime(2000, x, 1).strftime('%B').capitalize()
            )
        with col_año:
            año_sel = st.selectbox(
                "Año",
                options=list(range(2020, año_actual + 1)),
                index=año_actual - 2020
            )
        
        if st.button("📊 Ver mes completo"):
            from calendar import monthrange
            fecha_inicio = datetime(año_sel, mes_sel, 1).date()
            fecha_fin = datetime(año_sel, mes_sel, monthrange(año_sel, mes_sel)[1]).date()
            st.caption(f"📆 {fecha_inicio.strftime('%d/%m/%Y')} → {fecha_fin.strftime('%d/%m/%Y')}")
    
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
    
    # Cargador principal: Excel de Seguimiento Agroindustrial
    with st.expander("📊 Cargar Seguimiento Mensual", expanded=True):
        st.caption("Sube el archivo Excel de Seguimiento Agroindustria")
        
        uploaded_seguimiento = st.file_uploader(
            "Archivo de Seguimiento",
            type=['xlsx'],
            key="seguimiento_upload",
            help="Excel con formato: SEGUIMIENTO AGROINDUSTRIA [MES].xlsx",
            label_visibility="collapsed"
        )
        
        if uploaded_seguimiento is not None:
            # Procesar el archivo de seguimiento
            try:
                from scripts.convert_excel_seguimiento import convert_excel_to_csv
                import tempfile
                import shutil
                
                # Guardar archivo temporal
                with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
                    tmp.write(uploaded_seguimiento.getvalue())
                    tmp_path = tmp.name
                
                # Rutas de salida
                output_upstream = "data/upstream.csv"
                output_downstream = "data/downstream.csv"
                
                # Convertir
                with st.spinner("🔄 Procesando Excel..."):
                    df_up, df_down = convert_excel_to_csv(
                        tmp_path, 
                        output_upstream, 
                        output_downstream
                    )
                
                # Limpiar temporal
                os.unlink(tmp_path)
                
                if df_up is not None and not df_up.empty:
                    # Mostrar resumen
                    st.success(f"✅ Datos actualizados!")
                    st.metric("📊 Registros", f"{len(df_up)} días")
                    
                    # Mostrar rango de fechas
                    fecha_min = df_up['fecha'].min()
                    fecha_max = df_up['fecha'].max()
                    st.caption(f"📅 {fecha_min} → {fecha_max}")
                    
                    # Limpiar caché para recargar datos
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error("❌ No se pudieron extraer datos")
                    
            except Exception as e:
                st.error(f"❌ Error al procesar: {str(e)}")
    
    # Cargador alternativo: archivos CSV individuales
    with st.expander("📁 Cargar CSV individual", expanded=False):
        # Upload para Upstream
        uploaded_upstream = st.file_uploader(
            "Datos Upstream (CSV)",
            type=['csv'],
            key="upstream_upload",
            help="CSV con formato del dashboard"
        )
        
        # Upload para Downstream
        uploaded_downstream = st.file_uploader(
            "Datos Downstream (CSV)",
            type=['csv'],
            key="downstream_upload",
            help="CSV con datos de Refinería"
        )
        
        if uploaded_upstream or uploaded_downstream:
            st.success("✅ Archivos cargados")
    
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
        
        # Refinería (si hay datos downstream)
        if df_downstream is not None and not df_downstream.empty:
            total_refineria = df_downstream['produccion_real'].sum()
            total_ref_ppto = df_downstream['produccion_me'].sum()
        else:
            total_refineria = 0
            total_ref_ppto = 0
        
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
            delta_ref = total_refineria - total_ref_ppto
            st.metric(
                label="🏭 Refinería",
                value=f"{total_refineria:,.0f}",
                delta=f"{delta_ref:+,.0f} vs Ppto"
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
            st.markdown("**Niveles de Tanques CPO**")
            # Gráficos de tanques por zona
            if all(col in df_upstream.columns for col in ['tanque_1', 'tanque_2']):
                tabs_tanques = st.tabs(["🌴 Codazzi", "🏭 MLB", "🌾 A&G", "🌿 Sinú"])
                
                # Colores por zona
                colores_zona = {
                    "Codazzi": "#F9A825",  # Dorado
                    "MLB": "#1565C0",       # Azul
                    "A&G": "#2E7D32",       # Verde
                    "Sinú": "#EF6C00"       # Naranja
                }
                
                for i, zona in enumerate(["Codazzi", "MLB", "A&G", "Sinú"]):
                    with tabs_tanques[i]:
                        df_zona_filter = df_upstream[df_upstream['zona'] == zona]
                        if not df_zona_filter.empty:
                            df_zona_tank = df_zona_filter.iloc[-1]
                            
                            # Recopilar todos los tanques (incluyendo los con valor > 0)
                            tanques = {}
                            for j in range(1, 5):
                                col_tank_name = f'tanque_{j}'
                                if col_tank_name in df_upstream.columns:
                                    valor = df_zona_tank[col_tank_name]
                                    if valor > 0:
                                        tanques[f'TK {j}'] = valor
                            
                            if tanques:
                                # Mostrar info del inventario total
                                total_tanques = sum(tanques.values())
                                st.metric(f"Inventario Total {zona}", f"{total_tanques:,.0f} Ton")
                                
                                fig_tank = create_tank_chart(
                                    tanques=tanques,
                                    title="",
                                    color_lleno=colores_zona.get(zona, "#F9A825")
                                )
                                st.plotly_chart(fig_tank, use_container_width=True)
                            else:
                                st.info(f"Sin inventario en tanques para {zona}")
                        else:
                            st.warning(f"No hay datos para {zona}")
        
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
        # FILA 4: ALMENDRA Y KPO (Planta Expeller - Codazzi)
        # =====================================================================
        if 'almendra_real' in df_upstream.columns:
            st.subheader("🥜 Almendra y KPO (Planta Expeller - Codazzi)")
            
            # Filtrar solo datos de Codazzi (única planta con expeller)
            df_expeller = df_upstream[df_upstream['almendra_real'] > 0]
            
            if not df_expeller.empty:
                col_tabla_alm, col_extraccion = st.columns([2, 1])
                
                with col_tabla_alm:
                    # Calcular totales
                    alm_real = df_expeller['almendra_real'].sum()
                    alm_meta = df_expeller['almendra_presupuesto'].sum()
                    kpo_real = df_expeller['kpo_real'].sum()
                    kpo_meta = df_expeller['kpo_presupuesto'].sum()
                    extraccion = df_expeller['extraccion_almendra'].mean()
                    
                    # Crear tabla combinada
                    data_expeller = []
                    
                    # Almendra
                    pct_alm = (alm_real / alm_meta * 100) if alm_meta > 0 else 0
                    data_expeller.append({
                        'Producto': 'ALMENDRA',
                        'ME': f"{alm_meta:,.0f}",
                        'Real': f"{alm_real:,.0f}",
                        'Dif': f"{alm_real - alm_meta:+,.0f}",
                        '% Cumpl': f"{get_semaforo_color(pct_alm)} {pct_alm:.0f}%"
                    })
                    
                    # KPO
                    pct_kpo = (kpo_real / kpo_meta * 100) if kpo_meta > 0 else 0
                    data_expeller.append({
                        'Producto': 'KPO',
                        'ME': f"{kpo_meta:,.0f}",
                        'Real': f"{kpo_real:,.0f}",
                        'Dif': f"{kpo_real - kpo_meta:+,.0f}",
                        '% Cumpl': f"{get_semaforo_color(pct_kpo)} {pct_kpo:.0f}%"
                    })
                    
                    # Extracción
                    pct_ext = (extraccion / 41.0 * 100) if extraccion > 0 else 0
                    data_expeller.append({
                        'Producto': 'EXTRACCIÓN',
                        'ME': "41.0%",
                        'Real': f"{extraccion:.1f}%",
                        'Dif': f"{extraccion - 41.0:+.1f}%",
                        '% Cumpl': f"{get_semaforo_color(pct_ext)} {pct_ext:.0f}%"
                    })
                    
                    df_expeller_table = pd.DataFrame(data_expeller)
                    st.dataframe(df_expeller_table, use_container_width=True, hide_index=True)
                
                with col_extraccion:
                    # Mostrar métricas de extracción
                    promedio_diario = alm_real / len(df_expeller) if len(df_expeller) > 0 else 0
                    st.metric("📊 Promedio Diario", f"{promedio_diario:,.1f} Ton")
                    st.metric("🎯 % Extracción", f"{extraccion:.2f}%", 
                             delta=f"{extraccion - 41.0:+.2f}% vs meta")
            else:
                st.info("📭 No hay datos de Almendra/KPO en el período seleccionado")
        
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
    st.markdown("Producción de refinerías, cumplimiento y tendencias.")
    
    if df_downstream is not None and not df_downstream.empty:
        # =====================================================================
        # FILA 1: KPIs PRINCIPALES
        # =====================================================================
        
        # Calcular totales por refinería
        df_ref1 = df_downstream[df_downstream['refineria'] == 'Refinería 1']
        df_ref2 = df_downstream[df_downstream['refineria'] == 'Refinería 2']
        
        total_me_ref1 = df_ref1['produccion_me'].sum() if not df_ref1.empty else 0
        total_real_ref1 = df_ref1['produccion_real'].sum() if not df_ref1.empty else 0
        total_me_ref2 = df_ref2['produccion_me'].sum() if not df_ref2.empty else 0
        total_real_ref2 = df_ref2['produccion_real'].sum() if not df_ref2.empty else 0
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            cumpl_ref1 = (total_real_ref1 / total_me_ref1 * 100) if total_me_ref1 > 0 else 0
            delta_ref1 = total_real_ref1 - total_me_ref1
            st.metric(
                "🏭 Refinería 1",
                f"{total_real_ref1:,.0f} Ton",
                delta=f"{delta_ref1:+,.0f} ({cumpl_ref1:.0f}%)"
            )
        
        with col2:
            cumpl_ref2 = (total_real_ref2 / total_me_ref2 * 100) if total_me_ref2 > 0 else 0
            delta_ref2 = total_real_ref2 - total_me_ref2
            st.metric(
                "🏭 Refinería 2",
                f"{total_real_ref2:,.0f} Ton",
                delta=f"{delta_ref2:+,.0f} ({cumpl_ref2:.0f}%)"
            )
        
        with col3:
            total_me = total_me_ref1 + total_me_ref2
            total_real = total_real_ref1 + total_real_ref2
            cumpl_total = (total_real / total_me * 100) if total_me > 0 else 0
            st.metric(
                "📊 Total Producción",
                f"{total_real:,.0f} Ton",
                delta=f"Meta: {total_me:,.0f}"
            )
        
        with col4:
            dias_produccion = len(df_downstream['fecha'].unique())
            promedio_diario = total_real / dias_produccion if dias_produccion > 0 else 0
            st.metric(
                "📅 Promedio Diario",
                f"{promedio_diario:,.0f} Ton",
                delta=f"{dias_produccion} días"
            )
        
        st.divider()
        
        # =====================================================================
        # FILA 2: TABLA CON SEMÁFOROS + GRÁFICO DE BARRAS
        # =====================================================================
        col_tabla, col_grafico = st.columns([1, 1])
        
        with col_tabla:
            st.subheader("📊 Cumplimiento por Refinería")
            
            # Crear tabla de downstream con semáforos
            data_down = []
            
            # Refinería 1
            pct_ref1 = cumpl_ref1
            data_down.append({
                'Refinería': 'REFINERÍA 1',
                'ME (Ton)': f"{total_me_ref1:,.0f}",
                'Real (Ton)': f"{total_real_ref1:,.0f}",
                'Diferencia': f"{total_real_ref1 - total_me_ref1:+,.0f}",
                '% Cumpl': f"{get_semaforo_color(pct_ref1)} {pct_ref1:.1f}%"
            })
            
            # Refinería 2
            pct_ref2 = cumpl_ref2
            data_down.append({
                'Refinería': 'REFINERÍA 2',
                'ME (Ton)': f"{total_me_ref2:,.0f}",
                'Real (Ton)': f"{total_real_ref2:,.0f}",
                'Diferencia': f"{total_real_ref2 - total_me_ref2:+,.0f}",
                '% Cumpl': f"{get_semaforo_color(pct_ref2)} {pct_ref2:.1f}%"
            })
            
            # Total
            pct_total = cumpl_total
            data_down.append({
                'Refinería': '**TOTAL**',
                'ME (Ton)': f"{total_me:,.0f}",
                'Real (Ton)': f"{total_real:,.0f}",
                'Diferencia': f"{total_real - total_me:+,.0f}",
                '% Cumpl': f"{get_semaforo_color(pct_total)} {pct_total:.1f}%"
            })
            
            df_down_table = pd.DataFrame(data_down)
            st.dataframe(df_down_table, use_container_width=True, hide_index=True)
        
        with col_grafico:
            st.subheader("📊 Real vs Meta")
            
            # Gráfico de barras comparativo
            df_comparativo = pd.DataFrame({
                'Refinería': ['Refinería 1', 'Refinería 2'],
                'Meta': [total_me_ref1, total_me_ref2],
                'Real': [total_real_ref1, total_real_ref2]
            })
            
            fig_barras = create_grouped_bar_chart(
                df_comparativo,
                x_column='Refinería',
                y_columns=['Real', 'Meta'],
                y_names=['Real', 'Meta'],
                title=''
            )
            st.plotly_chart(fig_barras, use_container_width=True)
        
        st.divider()
        
        # =====================================================================
        # FILA 3: EVOLUCIÓN DIARIA
        # =====================================================================
        st.subheader("📈 Evolución Diaria de Producción")
        
        # Agregar por fecha y refinería
        df_evolucion = df_downstream.groupby(['fecha', 'refineria']).agg({
            'produccion_real': 'sum',
            'produccion_me': 'sum'
        }).reset_index()
        
        # Pivot para gráfico
        df_pivot = df_evolucion.pivot(index='fecha', columns='refineria', values='produccion_real').reset_index()
        df_pivot = df_pivot.fillna(0)
        
        col_ref = [c for c in df_pivot.columns if c != 'fecha']
        
        if col_ref:
            fig_linea = create_trend_line_chart(
                df_pivot,
                x_column='fecha',
                y_columns=col_ref,
                y_names=col_ref,
                title=''
            )
            st.plotly_chart(fig_linea, use_container_width=True)
        
        # =====================================================================
        # FILA 4: TABLA DETALLADA
        # =====================================================================
        st.divider()
        col_tabla, col_export = st.columns([3, 1])
        
        with col_tabla:
            with st.expander("📋 Ver datos detallados"):
                # Formatear tabla para mostrar
                df_display = df_downstream.copy()
                df_display['produccion_me'] = df_display['produccion_me'].apply(lambda x: f"{x:,.0f}")
                df_display['produccion_real'] = df_display['produccion_real'].apply(lambda x: f"{x:,.0f}")
                df_display['cumplimiento'] = df_display['cumplimiento'].apply(lambda x: f"{x:.1f}%")
                df_display.columns = ['Fecha', 'Refinería', 'Meta (Ton)', 'Real (Ton)', '% Cumplimiento']
                st.dataframe(df_display, use_container_width=True, hide_index=True)
        
        with col_export:
            # Botón de exportación
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
