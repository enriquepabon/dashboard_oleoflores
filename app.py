"""
Oleoflores BI Dashboard
=======================

Aplicación principal de Business Intelligence para el Grupo Oleoflores.
Visualización de la cadena de valor Farm-to-Fork.

Ejecutar con: streamlit run app.py
"""

# Cargar variables de entorno desde .env (DEBE ir antes de otros imports)
from dotenv import load_dotenv
load_dotenv()

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
from src.ai_chat import (
    initialize_chat_session,
    add_data_to_context,
    remove_data_from_context,
    render_chat_panel,
    render_data_selector
)
from src.auth import (
    handle_authentication,
    render_user_badge,
    is_admin,
    get_auth_status
)
from src.admin_panel import render_admin_sidebar_button

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
# AUTENTICACIÓN - DESHABILITADA
# =============================================================================
# La autenticación ahora se maneja con Streamlit Cloud nativo
# (Settings > Sharing > Private - only viewers you choose)
#
# Para reactivar autenticación custom, descomentar:
# if not handle_authentication():
#     st.stop()

# =============================================================================
# ESTILOS CSS PERSONALIZADOS
# =============================================================================

st.markdown("""
<!-- Preconnect hints for faster font loading -->
<link rel="preconnect" href="https://fonts.googleapis.com" crossorigin>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>

<!-- Preload critical fonts to reduce CLS -->
<link rel="preload" href="https://fonts.gstatic.com/s/inter/v18/UcCO3FwrK3iLTeHuS_nVMrMxCp50SjIw2boKoduKmMEVuLyfAZ9hiA.woff2" as="font" type="font/woff2" crossorigin>

<!-- Skip Navigation Link for Accessibility -->
<a href="#main-content" class="skip-link">Saltar al contenido principal</a>

<style>
    /* =========================================================================
       OLEOFLORES BI DASHBOARD - GOOGLE LANGUAGE EXPLORER STYLE
       ========================================================================= */
    
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* -------------------------------------------------------------------------
       CSS VARIABLES - DESIGN SYSTEM
       ------------------------------------------------------------------------- */
    
    :root {
        --bg-primary: #0a0a0a;
        --bg-secondary: #141414;
        --bg-card: #171717;
        --bg-card-hover: #1f1f1f;
        --border-color: rgba(255, 255, 255, 0.1);
        --border-hover: rgba(255, 255, 255, 0.2);
        --text-primary: #ffffff;
        --text-secondary: #a1a1aa;
        --text-muted: #71717a;
        --accent-blue: #60a5fa;
        --accent-blue-light: #93c5fd;
        --accent-blue-dark: #3b82f6;
        --success: #34d399;
        --warning: #fbbf24;
        --error: #f87171;
        --radius-sm: 8px;
        --radius-md: 12px;
        --radius-lg: 16px;
    }
    
    /* -------------------------------------------------------------------------
       KEYFRAME ANIMATIONS - MINIMAL
       ------------------------------------------------------------------------- */
    
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    @keyframes slideUp {
        from { 
            opacity: 0;
            transform: translateY(10px);
        }
        to { 
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    /* -------------------------------------------------------------------------
       ACCESSIBILITY - SKIP LINK
       ------------------------------------------------------------------------- */
    
    .skip-link {
        position: absolute;
        top: -9999px;
        left: -9999px;
        background: var(--accent-blue);
        color: var(--bg-primary);
        padding: 10px 20px;
        font-weight: 600;
        z-index: 10000;
        border-radius: var(--radius-sm);
        text-decoration: none;
        visibility: hidden;
    }
    
    .skip-link:focus {
        top: -9999px;
        visibility: hidden;
    }
    
    /* -------------------------------------------------------------------------
       ACCESSIBILITY - FOCUS STYLES
       ------------------------------------------------------------------------- */
    
    *:focus-visible {
        outline: 2px solid var(--accent-blue);
        outline-offset: 2px;
    }
    
    button:focus-visible,
    [role="button"]:focus-visible,
    a:focus-visible,
    input:focus-visible,
    select:focus-visible,
    textarea:focus-visible {
        outline: 2px solid var(--accent-blue);
        outline-offset: 2px;
        box-shadow: 0 0 0 4px rgba(77, 159, 255, 0.2);
    }
    
    /* -------------------------------------------------------------------------
       BASE STYLES - PURE DARK THEME
       ------------------------------------------------------------------------- */
    
    .stApp {
        background: var(--bg-primary) !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        min-height: 100vh;
    }
    
    /* Headers - Clean White */
    .stApp h1, .stApp h2, .stApp h3 {
        color: var(--text-primary) !important;
        font-weight: 600;
        letter-spacing: -0.02em;
    }
    
    .stApp h1 {
        font-size: 2.5rem !important;
        font-weight: 600 !important;
        color: var(--text-primary) !important;
        -webkit-text-fill-color: var(--text-primary) !important;
        background: none !important;
        animation: none !important;
    }
    
    .stApp h2 {
        font-size: 1.5rem !important;
        color: var(--text-primary) !important;
    }
    
    .stApp h3 {
        font-size: 1.125rem !important;
        color: var(--text-secondary) !important;
    }
    
    /* General text */
    .stApp, .stApp p, .stApp span, .stApp label {
        color: var(--text-secondary);
        line-height: 1.6;
    }
    
    .stMarkdown {
        color: var(--text-secondary);
    }
    
    .stMarkdown p {
        margin-bottom: 0.5rem;
    }
    
    /* -------------------------------------------------------------------------
       SIDEBAR - MINIMAL DARK
       ------------------------------------------------------------------------- */
    
    section[data-testid="stSidebar"] {
        background: var(--bg-primary) !important;
        border-right: 1px solid var(--border-color);
    }
    
    section[data-testid="stSidebar"] > div {
        padding-top: 1rem;
    }
    
    section[data-testid="stSidebar"] .stMarkdown h3 {
        color: var(--text-secondary) !important;
        font-size: 0.75rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-top: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid var(--border-color);
    }
    
    /* Sidebar title styling */
    .sidebar-title {
        color: var(--text-primary) !important;
        font-size: 1.75rem !important;
        font-weight: 600 !important;
        margin-bottom: 0.25rem;
        -webkit-text-fill-color: var(--text-primary) !important;
        background: none !important;
        animation: none !important;
    }
    
    .sidebar-subtitle {
        color: var(--text-muted) !important;
        font-size: 0.8rem;
        margin-bottom: 1.5rem;
        letter-spacing: 0.05em;
        font-weight: 400;
    }
    
    /* -------------------------------------------------------------------------
       METRIC CARDS - MINIMAL STYLE (Google Language Explorer)
       ------------------------------------------------------------------------- */
    
    div[data-testid="metric-container"] {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-lg);
        padding: 20px;
        transition: all 0.2s ease;
        animation: slideUp 0.3s ease-out;
        position: relative;
    }
    
    div[data-testid="metric-container"]::before,
    div[data-testid="metric-container"]::after {
        display: none;
    }
    
    div[data-testid="metric-container"]:hover {
        border-color: var(--border-hover);
        background: var(--bg-card-hover);
        transform: none;
        box-shadow: none;
    }
    
    div[data-testid="metric-container"] label {
        color: var(--text-secondary) !important;
        font-weight: 400;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }
    
    div[data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: var(--text-primary) !important;
        font-weight: 400;
        font-size: 2rem !important;
        letter-spacing: -0.02em;
    }
    
    div[data-testid="metric-container"] [data-testid="stMetricDelta"] {
        font-weight: 500;
        font-size: 0.85rem;
    }
    
    /* -------------------------------------------------------------------------
       BUTTONS - MINIMAL STYLE
       ------------------------------------------------------------------------- */
    
    .stButton > button {
        background: var(--accent-blue);
        color: var(--bg-primary);
        border: none;
        border-radius: var(--radius-md);
        padding: 0.625rem 1.25rem;
        font-weight: 500;
        font-size: 0.875rem;
        transition: all 0.2s ease;
        box-shadow: none;
    }
    
    .stButton > button::before {
        display: none;
    }
    
    .stButton > button:hover {
        background: var(--accent-blue-light);
        transform: none;
        box-shadow: none;
    }
    
    .stButton > button:active {
        background: var(--accent-blue-dark);
    }
    
    /* Secondary buttons - outlined style */
    .stButton > button[kind="secondary"] {
        background: transparent;
        color: var(--text-primary);
        border: 1px solid var(--border-color);
    }
    
    .stButton > button[kind="secondary"]:hover {
        background: var(--bg-card);
        border-color: var(--border-hover);
    }
    
    /* Download buttons */
    .stDownloadButton > button {
        background: transparent;
        color: var(--text-primary);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
        font-weight: 500;
        box-shadow: none;
    }
    
    .stDownloadButton > button:hover {
        background: var(--bg-card);
        border-color: var(--border-hover);
        transform: none;
    }
    
    /* -------------------------------------------------------------------------
       FORM ELEMENTS - MINIMAL
       ------------------------------------------------------------------------- */
    
    /* Select boxes */
    .stSelectbox > div > div {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
        color: var(--text-primary);
        transition: border-color 0.2s ease;
    }
    
    .stSelectbox > div > div:hover {
        border-color: var(--border-hover);
        box-shadow: none;
    }
    
    /* Multiselect */
    .stMultiSelect > div > div {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
    }
    
    /* Checkbox */
    .stCheckbox label span {
        color: var(--text-secondary) !important;
        font-weight: 400;
    }
    
    /* Radio buttons */
    div[data-testid="stRadio"] > label {
        color: var(--text-secondary) !important;
        font-weight: 500;
    }
    
    div[data-testid="stRadio"] label[data-checked="true"] {
        color: var(--accent-blue) !important;
    }
    
    /* File uploader */
    .stFileUploader {
        background: var(--bg-card);
        border: 1px dashed var(--border-color);
        border-radius: var(--radius-lg);
        padding: 1rem;
        transition: border-color 0.2s ease;
    }
    
    .stFileUploader:hover {
        border-color: var(--border-hover);
        background: var(--bg-card);
        box-shadow: none;
    }
    
    /* -------------------------------------------------------------------------
       DIVIDERS & SEPARATORS - SUBTLE
       ------------------------------------------------------------------------- */
    
    hr {
        margin: 1.5rem 0;
        border: none;
        height: 1px;
        background: var(--border-color);
    }
    
    .stDivider {
        background: var(--border-color) !important;
    }
    
    /* -------------------------------------------------------------------------
       EXPANDERS - MINIMAL
       ------------------------------------------------------------------------- */
    
    .streamlit-expanderHeader {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
        color: var(--text-primary) !important;
        font-weight: 500;
        transition: border-color 0.2s ease;
    }
    
    .streamlit-expanderHeader:hover {
        border-color: var(--border-hover);
        background: var(--bg-card) !important;
    }
    
    .streamlit-expanderContent {
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-top: none;
        border-radius: 0 0 var(--radius-md) var(--radius-md);
    }
    
    /* -------------------------------------------------------------------------
       DATA TABLES - MINIMAL STYLE
       ------------------------------------------------------------------------- */
    
    .stDataFrame {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-lg);
        overflow: hidden;
        animation: fadeIn 0.3s ease-out;
    }
    
    .stDataFrame [data-testid="stDataFrameResizable"] {
        background: transparent !important;
    }
    
    /* Table headers with blue accent */
    .stDataFrame thead th,
    .stDataFrame [data-testid="glideDataEditor"] [role="columnheader"] {
        background: rgba(77, 159, 255, 0.1) !important;
        color: var(--text-primary) !important;
        font-weight: 600 !important;
        font-size: 0.8rem !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        padding: 14px 12px !important;
        border-bottom: 1px solid var(--border-color) !important;
    }
    
    /* Table rows */
    .stDataFrame tbody tr,
    .stDataFrame [data-testid="glideDataEditor"] [role="row"] {
        transition: background 0.15s ease;
        border-bottom: 1px solid var(--border-color);
    }
    
    .stDataFrame tbody tr:hover,
    .stDataFrame [data-testid="glideDataEditor"] [role="row"]:hover {
        background: var(--bg-card-hover) !important;
        transform: none;
        box-shadow: none;
    }
    
    /* Table cells */
    .stDataFrame td,
    .stDataFrame [data-testid="glideDataEditor"] [role="gridcell"] {
        color: var(--text-secondary) !important;
        font-size: 0.875rem;
        padding: 10px 12px !important;
    }
    
    /* -------------------------------------------------------------------------
       ALERTS & MESSAGES - MINIMAL
       ------------------------------------------------------------------------- */
    
    .stAlert {
        border-radius: var(--radius-md);
        border: 1px solid var(--border-color);
        animation: fadeIn 0.3s ease-out;
    }
    
    .alert-warning {
        background: rgba(251, 191, 36, 0.1);
        border-left: 3px solid var(--warning);
        padding: 1rem;
        border-radius: 0 var(--radius-md) var(--radius-md) 0;
    }
    
    .alert-error {
        background: rgba(248, 113, 113, 0.1);
        border-left: 3px solid var(--error);
        padding: 1rem;
        border-radius: 0 var(--radius-md) var(--radius-md) 0;
    }
    
    .alert-success {
        background: rgba(52, 211, 153, 0.1);
        border-left: 3px solid var(--success);
        padding: 1rem;
        border-radius: 0 var(--radius-md) var(--radius-md) 0;
    }
    
    /* -------------------------------------------------------------------------
       TABS - MINIMAL STYLE
       ------------------------------------------------------------------------- */
    
    .stTabs [data-baseweb="tab-list"] {
        background: transparent;
        border-radius: 0;
        padding: 0;
        gap: 0;
        border-bottom: 1px solid var(--border-color);
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        color: var(--text-secondary);
        border-radius: 0;
        font-weight: 500;
        padding: 12px 16px;
        border-bottom: 2px solid transparent;
        margin-bottom: -1px;
        transition: all 0.2s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: transparent;
        color: var(--text-primary);
    }
    
    .stTabs [aria-selected="true"] {
        background: transparent !important;
        color: var(--accent-blue) !important;
        border-bottom: 2px solid var(--accent-blue) !important;
        box-shadow: none;
    }
    
    /* -------------------------------------------------------------------------
       PLOTLY CHARTS CONTAINER - MINIMAL
       ------------------------------------------------------------------------- */
    
    .js-plotly-plot {
        border-radius: var(--radius-lg);
        overflow: hidden;
    }
    
    .js-plotly-plot .plotly {
        border-radius: var(--radius-lg);
    }
    
    /* Chart containers */
    .stPlotlyChart {
        background: var(--bg-card);
        border-radius: var(--radius-lg);
        padding: 1rem;
        border: 1px solid var(--border-color);
        transition: border-color 0.2s ease;
    }
    
    .stPlotlyChart:hover {
        border-color: var(--border-hover);
        box-shadow: none;
    }
    
    /* -------------------------------------------------------------------------
       SCROLLBAR STYLING - MINIMAL
       ------------------------------------------------------------------------- */
    
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--bg-secondary);
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--text-muted);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--text-secondary);
    }
    
    /* -------------------------------------------------------------------------
       CAPTIONS & SMALL TEXT
       ------------------------------------------------------------------------- */
    
    .stCaption, small, .stApp small {
        color: var(--text-muted) !important;
        font-size: 0.8rem;
    }
    
    /* -------------------------------------------------------------------------
       COLUMN CONTAINERS
       ------------------------------------------------------------------------- */
    
    .stApp .element-container {
        animation: fadeIn 0.3s ease-out;
    }
    
    /* -------------------------------------------------------------------------
       LAYOUT - SCROLL FIX
       ------------------------------------------------------------------------- */
    
    .stApp {
        overflow-y: auto !important;
        overflow-x: hidden !important;
        height: auto !important;
    }
    
    .stApp > div:first-child {
        overflow: visible !important;
        height: auto !important;
    }
    
    .stApp .stMainBlockContainer,
    .stApp .block-container {
        overflow: visible !important;
        height: auto !important;
        max-height: none !important;
    }
    
    .stApp .stMain,
    .stApp [data-testid="stAppViewContainer"],
    .stApp [data-testid="stVerticalBlock"] {
        overflow-y: auto !important;
        overflow-x: hidden !important;
        height: auto !important;
    }
    
    section[data-testid="stSidebar"] {
        width: 300px !important;
        min-width: 300px !important;
        overflow-y: auto !important;
    }
    
    .stStatusWidget {
        min-height: 24px;
    }
    
    .stApp > header {
        background: transparent !important;
    }
    
    [data-testid="stStatusWidget"],
    .stProgress,
    .stApp [data-testid="stDecoration"],
    .stDeployButton,
    div[data-testid="stDecoration"] {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        opacity: 0 !important;
    }
    
    .stApp [data-testid="stVerticalBlockBorderWrapper"] {
        height: auto !important;
        min-height: auto !important;
    }
    
    /* -------------------------------------------------------------------------
       PROGRESS BARS - BLUE ACCENT (Like Language Explorer)
       ------------------------------------------------------------------------- */
    
    .stProgress > div > div {
        background: linear-gradient(90deg, var(--accent-blue), var(--accent-blue-light));
        border-radius: 4px;
    }
    
    .stProgress > div {
        background: var(--bg-secondary);
        border-radius: 4px;
    }
    
    /* -------------------------------------------------------------------------
       INFO CARDS HELPER CLASSES
       ------------------------------------------------------------------------- */
    
    .info-card {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-lg);
        padding: 16px 20px;
        transition: border-color 0.2s ease;
    }
    
    .info-card:hover {
        border-color: var(--border-hover);
    }
    
    .info-card-label {
        color: var(--text-secondary);
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 8px;
    }
    
    .info-card-value {
        color: var(--text-primary);
        font-size: 1.75rem;
        font-weight: 400;
    }
    
    .info-card-subtext {
        color: var(--text-muted);
        font-size: 0.8rem;
        margin-top: 4px;
    }
    
</style>
""", unsafe_allow_html=True)

# =============================================================================
# 4.2 - SIDEBAR: LOGO Y TÍTULO
# =============================================================================

with st.sidebar:
    # Logo icono (ancho completo del sidebar)
    st.image("assets/Iconopalma.png", use_container_width=True)
    st.markdown("""
    <div style="text-align: center; padding: 0.5rem 0;">
        <h1 class="sidebar-title">Oleoflores</h1>
        <p class="sidebar-subtitle">Business Intelligence Dashboard</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Autenticación deshabilitada - usando Streamlit Cloud nativo
    # render_user_badge()
    # render_admin_sidebar_button()
    # if st.button("🚪 Cerrar Sesión", ...): ...
    
    st.divider()

# =============================================================================
# 4.3 - SIDEBAR: SELECTOR DE VISTA (NAVEGACIÓN)
# =============================================================================

    st.markdown("### 📊 Navegación")
    
    vista_seleccionada = st.radio(
        "Seleccionar Vista",
        options=["🏠 Resumen Ejecutivo", "🌾 Upstream", "🏭 Downstream", "🥜 Balance Almendra"],
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
    
    # ========== SELECTOR DE MES/AÑO ==========
    col_mes, col_año = st.columns(2)
    with col_mes:
        mes_sel = st.selectbox(
            "Mes",
            options=list(range(1, 13)),
            index=mes_actual - 1,
            format_func=lambda x: datetime(2000, x, 1).strftime('%B').capitalize(),
            key="mes_selector"
        )
    with col_año:
        año_sel = st.selectbox(
            "Año",
            options=list(range(2020, año_actual + 1)),
            index=año_actual - 2020,
            key="año_selector"
        )
    
    # Calcular semanas del mes SELECCIONADO
    semanas_mes = calcular_semanas_mes(año_sel, mes_sel)
    
    # Nombre del mes seleccionado
    nombre_mes = datetime(año_sel, mes_sel, 1).strftime('%B').capitalize()
    
    # ========== CREAR OPCIONES DE PERÍODO ==========
    opciones_periodo = []
    
    # Agregar semanas del mes seleccionado
    for semana, (inicio, fin) in semanas_mes.items():
        opciones_periodo.append(f"📊 {semana} ({inicio.day}-{fin.day} {nombre_mes[:3]})")
    
    # Agregar opciones de acumulado
    opciones_periodo.append(f"📆 Mes completo ({nombre_mes})")
    opciones_periodo.append("📅 Año (YTD)")
    opciones_periodo.append("🔧 Personalizado")
    
    periodo_seleccionado = st.selectbox(
        "Rango de fechas",
        options=opciones_periodo,
        index=0,  # Por defecto: S1
        key="periodo_selector"
    )
    
    # ========== CALCULAR FECHAS SEGÚN PERÍODO ==========
    from calendar import monthrange
    
    if "Personalizado" in periodo_seleccionado:
        col_fecha1, col_fecha2 = st.columns(2)
        with col_fecha1:
            fecha_inicio = st.date_input(
                "Desde",
                value=datetime(año_sel, mes_sel, 1).date()
            )
        with col_fecha2:
            fecha_fin = st.date_input(
                "Hasta",
                value=datetime(año_sel, mes_sel, monthrange(año_sel, mes_sel)[1]).date()
            )
    elif "Mes completo" in periodo_seleccionado:
        # Mes completo seleccionado
        fecha_inicio = datetime(año_sel, mes_sel, 1).date()
        fecha_fin = datetime(año_sel, mes_sel, monthrange(año_sel, mes_sel)[1]).date()
    elif "YTD" in periodo_seleccionado:
        # Año hasta la fecha (Year to Date)
        fecha_inicio = datetime(año_sel, 1, 1).date()
        fecha_fin = datetime(año_sel, mes_sel, monthrange(año_sel, mes_sel)[1]).date()
    else:
        # Es una semana (S1, S2, S3, S4, S5)
        for semana, (inicio, fin) in semanas_mes.items():
            if semana in periodo_seleccionado:
                fecha_inicio = inicio
                fecha_fin = fin
                break
        else:
            # Fallback
            fecha_inicio = datetime(año_sel, mes_sel, 1).date()
            fecha_fin = datetime(año_sel, mes_sel, monthrange(año_sel, mes_sel)[1]).date()
    
    # Mostrar rango seleccionado
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
    
    # ==========================================================================
    # SINCRONIZACIÓN AUTOMÁTICA CON GOOGLE DRIVE
    # ==========================================================================
    
    with st.expander("☁️ Sincronizar desde Google Drive", expanded=True):
        # Importar módulo de sincronización
        try:
            from scripts.sync_google_drive import check_google_drive_config, sync_from_google_drive
            SYNC_AVAILABLE = True
        except ImportError:
            SYNC_AVAILABLE = False
        
        if not SYNC_AVAILABLE:
            st.warning("⚠️ Módulo de sincronización no disponible")
        else:
            # Verificar configuración
            config = check_google_drive_config()
            
            if not config['available']:
                st.error("❌ Dependencias no instaladas")
                st.code("pip install google-api-python-client google-auth", language="bash")
            elif not config['ready']:
                st.warning("⚠️ Configuración incompleta")
                if not config['file_id_set']:
                    st.caption("• GOOGLE_DRIVE_FILE_ID no configurado")
                if not config['credentials_available']:
                    st.caption("• Credenciales de servicio no encontradas")
                st.caption("Configura las variables en .env")
            else:
                st.success("✅ Google Drive configurado")
                
                # Mostrar última sincronización
                if 'last_sync' in st.session_state:
                    st.caption(f"Última sync: {st.session_state.last_sync}")
                
                # Botón de sincronización manual
                if st.button("🔄 Sincronizar ahora", type="primary", use_container_width=True):
                    with st.spinner("📥 Descargando desde Google Drive..."):
                        result = sync_from_google_drive()
                        
                        if result['success']:
                            st.session_state.last_sync = result['timestamp']
                            st.success(f"✅ {result['records_upstream']} registros actualizados")
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error(result['message'])
    
    # Cargador manual: Excel de Seguimiento Agroindustrial
    with st.expander("📊 Cargar Seguimiento Mensual", expanded=False):
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
    
    # ==========================================================================
    # PANEL DE CHAT IA
    # ==========================================================================
    
    # Inicializar sesión de chat
    initialize_chat_session()
    
    # Renderizar panel de chat
    render_chat_panel()
    
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

# Header principal - Banner (ancho completo)
st.markdown('<div id="main-content"></div>', unsafe_allow_html=True)
st.image("assets/banner2.png", use_container_width=True)

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
        total_cpo = df_upstream['cpo_real'].sum()
        total_cpo_ppto = df_upstream['cpo_presupuesto'].sum()
        
        # TEA = CPO / RFF × 100 (cálculo correcto, no promedio)
        tea_real = (total_cpo / total_rff * 100) if total_rff > 0 else 0
        # TEA Meta ponderado por RFF
        tea_meta = sum(df_upstream.groupby('zona').apply(
            lambda x: x['tea_meta'].iloc[0] * x['rff_real'].sum() / total_rff if total_rff > 0 else 0
        ))
        
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
            delta_tea = tea_real - tea_meta
            st.metric(
                label="🎯 TEA%",
                value=f"{tea_real:.1f}%",
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
            # Header con selector para IA
            hdr_col1, hdr_col2 = st.columns([0.9, 0.1])
            with hdr_col1:
                st.subheader("📦 RFF Procesada")
            with hdr_col2:
                rff_selected = st.checkbox("📌", key="sel_rff", help="Seleccionar para análisis IA")
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
            
            # Agregar al contexto si está seleccionado
            if rff_selected:
                add_data_to_context("tabla_rff", df_rff_display, "Tabla RFF Procesada por Planta")
        
        with col2:
            # Header con selector para IA
            hdr_col1, hdr_col2 = st.columns([0.9, 0.1])
            with hdr_col1:
                st.subheader("🛢️ CPO")
            with hdr_col2:
                cpo_selected = st.checkbox("📌", key="sel_cpo", help="Seleccionar para análisis IA")
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
            
            # Agregar al contexto si está seleccionado
            if cpo_selected:
                add_data_to_context("tabla_cpo", df_cpo_display, "Tabla CPO por Planta")
        
        with col3:
            # Header con selector para IA
            hdr_col1, hdr_col2 = st.columns([0.9, 0.1])
            with hdr_col1:
                st.subheader("🎯 TAE%")
            with hdr_col2:
                tea_selected = st.checkbox("📌", key="sel_tea", help="Seleccionar para análisis IA")
            # Calcular TEA correctamente: TEA = CPO Total / RFF Total × 100
            # NO usar promedio de TEA diarios
            
            tea_data = []
            for zona in df_zona['zona'].unique():
                df_z = df_upstream[df_upstream['zona'] == zona]
                rff_total = df_z['rff_real'].sum()
                cpo_total = df_z['cpo_real'].sum()
                tea_real = (cpo_total / rff_total * 100) if rff_total > 0 else 0
                tea_meta = df_z['tea_meta'].iloc[0] if len(df_z) > 0 else 0
                
                tea_data.append({
                    'Planta': zona,
                    'TEA ME': tea_meta,
                    'TEA Real': tea_real,
                })
            
            df_tea = pd.DataFrame(tea_data)
            df_tea['Dif'] = df_tea['TEA Real'] - df_tea['TEA ME']
            # Para TEA, positivo es bueno
            df_tea['Semáforo'] = df_tea['Dif'].apply(lambda x: '🟢' if x >= 0 else ('🟡' if x >= -0.5 else '🔴'))
            df_tea['DIF'] = df_tea.apply(lambda x: f"{x['Semáforo']} {x['Dif']:+.1f}%", axis=1)
            
            # Agregar fila TOTAL (TEA total = CPO Total / RFF Total)
            rff_total_all = df_upstream['rff_real'].sum()
            cpo_total_all = df_upstream['cpo_real'].sum()
            tea_real_total = (cpo_total_all / rff_total_all * 100) if rff_total_all > 0 else 0
            # TEA ME ponderado por RFF
            tea_me_total = sum(df_upstream.groupby('zona').apply(
                lambda x: x['tea_meta'].iloc[0] * x['rff_real'].sum() / rff_total_all if rff_total_all > 0 else 0
            ))
            
            total_tea = pd.DataFrame({
                'Planta': ['**TOTAL**'],
                'TEA ME': [tea_me_total],
                'TEA Real': [tea_real_total],
            })
            total_tea['Dif'] = total_tea['TEA Real'] - total_tea['TEA ME']
            total_tea['Semáforo'] = total_tea['Dif'].apply(lambda x: '🟢' if x >= 0 else ('🟡' if x >= -0.5 else '🔴'))
            total_tea['DIF'] = total_tea.apply(lambda x: f"{x['Semáforo']} {x['Dif']:+.1f}%", axis=1)
            
            df_tea_display = pd.concat([df_tea[['Planta', 'TEA ME', 'TEA Real', 'DIF']], 
                                        total_tea[['Planta', 'TEA ME', 'TEA Real', 'DIF']]])
            df_tea_display['TEA ME'] = df_tea_display['TEA ME'].apply(lambda x: f"{x:.1f}%")
            df_tea_display['TEA Real'] = df_tea_display['TEA Real'].apply(lambda x: f"{x:.1f}%")
            
            st.dataframe(df_tea_display, use_container_width=True, hide_index=True)
            
            # Agregar al contexto si está seleccionado
            if tea_selected:
                add_data_to_context("tabla_tea", df_tea_display, "Tabla TAE% (Tasa de Extracción) por Planta")
        
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
            st.subheader("🎯 TEA% Total")
            # TEA = CPO / RFF × 100 (cálculo correcto)
            rff_total = df_upstream['rff_real'].sum()
            cpo_total = df_upstream['cpo_real'].sum()
            tea_actual = (cpo_total / rff_total * 100) if rff_total > 0 else 0
            # TEA Meta ponderado por RFF
            tea_meta = sum(df_upstream.groupby('zona').apply(
                lambda x: x['tea_meta'].iloc[0] * x['rff_real'].sum() / rff_total if rff_total > 0 else 0
            ))
            
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
    st.markdown("Producción de refinerías, fraccionamiento, oleína y margarinas.")
    
    if df_downstream is not None and not df_downstream.empty:
        # Detectar columna de producto (puede ser 'producto' o 'refineria' según formato)
        col_producto = 'producto' if 'producto' in df_downstream.columns else 'refineria'
        
        # =====================================================================
        # FILA 1: KPIs PRINCIPALES
        # =====================================================================
        
        # Calcular totales por producto
        def get_totales(nombre):
            df_p = df_downstream[df_downstream[col_producto] == nombre]
            me = df_p['produccion_me'].sum() if not df_p.empty else 0
            real = df_p['produccion_real'].sum() if not df_p.empty else 0
            return me, real
        
        me_ref1, real_ref1 = get_totales('Refinería 1')
        me_ref2, real_ref2 = get_totales('Refinería 2')
        me_oleina, real_oleina = get_totales('Total Oleína')
        me_marg, real_marg = get_totales('Margarinas')
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            cumpl = (real_ref1 / me_ref1 * 100) if me_ref1 > 0 else 0
            st.metric(
                "🏭 Refinería 1",
                f"{real_ref1:,.0f} Ton",
                delta=f"{real_ref1 - me_ref1:+,.0f} ({cumpl:.0f}%)"
            )
        
        with col2:
            cumpl = (real_ref2 / me_ref2 * 100) if me_ref2 > 0 else 0
            st.metric(
                "🏭 Refinería 2",
                f"{real_ref2:,.0f} Ton",
                delta=f"{real_ref2 - me_ref2:+,.0f} ({cumpl:.0f}%)"
            )
        
        with col3:
            cumpl = (real_oleina / me_oleina * 100) if me_oleina > 0 else 0
            st.metric(
                "🫒 Oleína",
                f"{real_oleina:,.0f} Ton",
                delta=f"{real_oleina - me_oleina:+,.0f} ({cumpl:.0f}%)"
            )
        
        with col4:
            cumpl = (real_marg / me_marg * 100) if me_marg > 0 else 0
            st.metric(
                "🧈 Margarinas",
                f"{real_marg:,.0f} Ton",
                delta=f"{real_marg - me_marg:+,.0f} ({cumpl:.0f}%)"
            )
        
        st.divider()
        
        # =====================================================================
        # FILA 2: TABLA COMPLETA CON SEMÁFOROS
        # =====================================================================
        col_tabla, col_grafico = st.columns([1, 1])
        
        with col_tabla:
            st.subheader("📊 Cumplimiento por Producto")
            
            # Crear tabla con todos los productos
            data_down = []
            productos_mostrar = [
                ('REFINERÍA 1', 'Refinería 1'),
                ('REFINERÍA 2', 'Refinería 2'),
                ('OLEÍNA', 'Total Oleína'),
                ('MARGARINAS', 'Margarinas'),
            ]
            
            total_me = 0
            total_real = 0
            
            for nombre_display, nombre_data in productos_mostrar:
                me, real = get_totales(nombre_data)
                total_me += me
                total_real += real
                pct = (real / me * 100) if me > 0 else 0
                
                data_down.append({
                    'Producto': nombre_display,
                    'ME (Ton)': f"{me:,.0f}",
                    'Real (Ton)': f"{real:,.0f}",
                    'Diferencia': f"{real - me:+,.0f}",
                    '% Cumpl': f"{get_semaforo_color(pct)} {pct:.1f}%"
                })
            
            # Total
            pct_total = (total_real / total_me * 100) if total_me > 0 else 0
            data_down.append({
                'Producto': '**TOTAL**',
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
            nombres = ['Ref 1', 'Ref 2', 'Oleína', 'Marg.']
            metas = [me_ref1, me_ref2, me_oleina, me_marg]
            reales = [real_ref1, real_ref2, real_oleina, real_marg]
            
            df_comparativo = pd.DataFrame({
                'Producto': nombres,
                'Meta': metas,
                'Real': reales
            })
            
            fig_barras = create_grouped_bar_chart(
                df_comparativo,
                x_column='Producto',
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
        
        # Solo mostrar refinerías para evolución diaria
        df_ref = df_downstream[df_downstream[col_producto].isin(['Refinería 1', 'Refinería 2'])]
        
        if not df_ref.empty:
            df_evolucion = df_ref.groupby(['fecha', col_producto]).agg({
                'produccion_real': 'sum',
                'produccion_me': 'sum'
            }).reset_index()
            
            # Pivot para gráfico
            df_pivot = df_evolucion.pivot(index='fecha', columns=col_producto, values='produccion_real').reset_index()
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
                
                # Renombrar columnas según el formato
                if col_producto == 'producto':
                    cols_rename = ['Fecha', 'Producto', 'Tipo', 'Meta (Ton)', 'Real (Ton)', '% Cumpl']
                else:
                    cols_rename = ['Fecha', 'Producto', 'Meta (Ton)', 'Real (Ton)', '% Cumpl']
                df_display.columns = cols_rename[:len(df_display.columns)]
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
# VISTA: BALANCE ALMENDRA
# =============================================================================

elif vista_seleccionada == "🥜 Balance Almendra":
    
    st.header("🥜 Balance Almendra")
    st.markdown("Procesamiento diario de nuez, almendra y CKPO de todas las plantas.")
    
    # Importar módulo de balance
    try:
        from src.balance_almendra import (
            process_file_with_gemini, 
            save_daily_balance, 
            get_daily_balance,
            generate_balance_analysis,
            get_api_key,
            PLANTAS_CONFIG
        )
        BALANCE_MODULE_AVAILABLE = True
    except ImportError as e:
        BALANCE_MODULE_AVAILABLE = False
        st.error(f"❌ Módulo de balance no disponible: {e}")
    
    if BALANCE_MODULE_AVAILABLE:
        
        # Verificar API key
        api_key = get_api_key()
        if not api_key:
            st.warning("⚠️ GOOGLE_API_KEY no configurada. Necesaria para procesar reportes con IA.")
        
        # Tabs principales
        tab_carga, tab_balance, tab_historial = st.tabs([
            "📤 Cargar Reportes", 
            "📊 Balance del Día",
            "📈 Historial"
        ])
        
        # =====================================================================
        # TAB: CARGA DE REPORTES
        # =====================================================================
        with tab_carga:
            st.markdown("### 📤 Cargar Reportes Diarios")
            st.markdown("Sube los 4 reportes de las plantas para procesar el balance del día.")
            
            # Layout de 4 columnas para los uploads
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**🏭 CZZ (Codazzi) - Expellers**")
                file_czz = st.file_uploader(
                    "Reporte CZZ",
                    type=['pdf', 'png', 'jpg'],
                    key="balance_czz",
                    label_visibility="collapsed"
                )
                
                st.markdown("**🌴 A&G (Aceites & Grasas)**")
                file_ag = st.file_uploader(
                    "Reporte A&G",
                    type=['pdf', 'png', 'jpg'],
                    key="balance_ag",
                    label_visibility="collapsed"
                )
            
            with col2:
                st.markdown("**🌾 MLB (María La Baja)**")
                file_mlb = st.file_uploader(
                    "Reporte MLB",
                    type=['pdf', 'png', 'jpg'],
                    key="balance_mlb",
                    label_visibility="collapsed"
                )
                
                st.markdown("**🚛 SINÚ (Transporte)**")
                file_sinu = st.file_uploader(
                    "Reporte Sinú",
                    type=['pdf', 'png', 'jpg'],
                    key="balance_sinu",
                    label_visibility="collapsed"
                )
            
            # Contador de archivos
            archivos_cargados = sum([1 for f in [file_czz, file_ag, file_mlb, file_sinu] if f is not None])
            st.info(f"📁 {archivos_cargados}/4 archivos cargados")
            
            # Campo de contexto del usuario
            st.markdown("---")
            st.markdown("**📝 Contexto adicional (opcional)**")
            contexto_usuario = st.text_area(
                "Agrega información adicional para el análisis IA",
                placeholder="Ej: Hubo un paro programado en MLB, se esperan bajos volúmenes...",
                key="contexto_usuario_balance",
                height=100,
                label_visibility="collapsed"
            )
            
            # Botón de procesamiento
            if archivos_cargados > 0:
                if st.button("🤖 Procesar con IA", type="primary", use_container_width=True, disabled=not api_key):
                    
                    import tempfile
                    
                    resultados = []
                    archivos_map = {
                        'CZZ': file_czz,
                        'A&G': file_ag,
                        'MLB': file_mlb,
                        'SINU': file_sinu
                    }
                    
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    for i, (planta, archivo) in enumerate(archivos_map.items()):
                        if archivo is not None:
                            status_text.text(f"🔄 Procesando {planta}...")
                            
                            # Guardar archivo temporal
                            ext = archivo.name.split('.')[-1]
                            with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{ext}') as tmp:
                                tmp.write(archivo.getvalue())
                                tmp_path = tmp.name
                            
                            try:
                                # Procesar con IA
                                data = process_file_with_gemini(tmp_path, api_key)
                                data['planta'] = planta  # Asegurar nombre de planta
                                resultados.append(data)
                                
                                if 'error' in data:
                                    st.warning(f"⚠️ {planta}: {data['error']}")
                                else:
                                    st.success(f"✅ {planta} procesado correctamente")
                                    
                            except Exception as e:
                                st.error(f"❌ Error procesando {planta}: {str(e)}")
                                resultados.append({'error': str(e), 'planta': planta})
                            finally:
                                os.unlink(tmp_path)
                        
                        progress_bar.progress((i + 1) / 4)
                    
                    status_text.text("✨ Procesamiento completado")
                    
                    # Guardar resultados
                    if resultados:
                        df_balance = save_daily_balance(resultados)
                        if df_balance is not None:
                            st.session_state['balance_results'] = resultados
                            st.session_state['balance_contexto_usuario'] = contexto_usuario
                            st.success(f"💾 Datos guardados: {len(df_balance)} registros")
                            
                            # Generar análisis (incluyendo contexto del usuario)
                            with st.spinner("🤖 Generando análisis IA..."):
                                ctx = st.session_state.get('balance_contexto_usuario', '') or ''
                                analisis = generate_balance_analysis(resultados, ctx)
                                st.session_state['balance_analysis'] = analisis
                            
                            st.rerun()
        
        # =====================================================================
        # TAB: BALANCE DEL DÍA
        # =====================================================================
        with tab_balance:
            st.markdown("### 📊 Balance del Día")
            
            # Cargar datos del día más reciente
            df_balance = get_daily_balance()
            
            if df_balance.empty:
                st.info("📭 No hay datos de balance. Carga los reportes en la pestaña anterior.")
            else:
                fecha_balance = df_balance['fecha'].iloc[0]
                st.markdown(f"**📅 Fecha: {fecha_balance}**")
                
                # KPIs principales
                st.markdown("#### 📈 Resumen General")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    nuez_total = df_balance['nuez_inventario_final_kg'].sum() if 'nuez_inventario_final_kg' in df_balance.columns else 0
                    st.metric("🌰 Inventario Nuez", f"{nuez_total/1000:,.1f} Ton")
                
                with col2:
                    almendra_total = df_balance['almendra_inventario_final_kg'].sum() if 'almendra_inventario_final_kg' in df_balance.columns else 0
                    st.metric("🥜 Almendra Final", f"{almendra_total/1000:,.1f} Ton")
                
                with col3:
                    almendra_emp = df_balance['almendra_inventario_empacada_kg'].sum() if 'almendra_inventario_empacada_kg' in df_balance.columns else 0
                    st.metric("📦 Almendra Empacada", f"{almendra_emp/1000:,.1f} Ton")
                
                with col4:
                    ckpo_total = df_balance['ckpo_inventario_final_kg'].sum() if 'ckpo_inventario_final_kg' in df_balance.columns else 0
                    st.metric("🛢️ CKPO Final", f"{ckpo_total/1000:,.1f} Ton")
                
                st.divider()
                
                # Función auxiliar para obtener columna segura
                def safe_cols(df, cols):
                    return [c for c in cols if c in df.columns]
                
                # Tablas de detalle
                st.markdown("#### 🌰 Balance de Nuez por Planta")
                nuez_cols = safe_cols(df_balance, ['planta', 'nuez_inventario_inicial_kg', 'nuez_entrada_kg', 'nuez_produccion_kg', 'nuez_consumo_kg', 'nuez_inventario_final_kg'])
                if len(nuez_cols) > 1:
                    df_nuez = df_balance[nuez_cols].copy()
                    df_nuez.columns = ['Planta'] + ['Inv. Inicial', 'Entrada', 'Producción', 'Consumo', 'Inv. Final'][:len(nuez_cols)-1]
                    st.dataframe(df_nuez, use_container_width=True, hide_index=True)
                
                col_izq, col_der = st.columns(2)
                
                with col_izq:
                    st.markdown("#### 🥜 Balance de Almendra")
                    alm_cols = safe_cols(df_balance, ['planta', 'almendra_inventario_inicial_kg', 'almendra_produccion_kg', 'almendra_compra_kg', 'almendra_traslado_expeller_kg', 'almendra_inventario_final_kg'])
                    if len(alm_cols) > 1:
                        df_almendra = df_balance[alm_cols].copy()
                        col_names = ['Planta']
                        mapping = {'almendra_inventario_inicial_kg': 'Inv. Inicial', 'almendra_produccion_kg': 'Producción', 
                                   'almendra_compra_kg': 'Compra', 'almendra_traslado_expeller_kg': 'Traslado Exp.', 
                                   'almendra_inventario_final_kg': 'Inv. Final'}
                        col_names += [mapping.get(c, c) for c in alm_cols[1:]]
                        df_almendra.columns = col_names
                        st.dataframe(df_almendra, use_container_width=True, hide_index=True)
                
                with col_der:
                    st.markdown("#### 🛢️ Balance CKPO (Expellers)")
                    ckpo_cols = safe_cols(df_balance, ['planta', 'ckpo_inventario_inicial_kg', 'ckpo_produccion_kg', 'ckpo_despacho_kg', 'ckpo_traslado_refineria_kg', 'ckpo_inventario_final_kg'])
                    if len(ckpo_cols) > 1:
                        df_ckpo = df_balance[ckpo_cols].copy()
                        col_names = ['Planta']
                        mapping = {'ckpo_inventario_inicial_kg': 'Inv. Inicial', 'ckpo_produccion_kg': 'Producción',
                                   'ckpo_despacho_kg': 'Despacho', 'ckpo_traslado_refineria_kg': 'Traslado Ref.',
                                   'ckpo_inventario_final_kg': 'Inv. Final'}
                        col_names += [mapping.get(c, c) for c in ckpo_cols[1:]]
                        df_ckpo.columns = col_names
                        st.dataframe(df_ckpo, use_container_width=True, hide_index=True)
                
                # Torta
                st.markdown("#### 🍞 Balance Torta de Palmiste")
                torta_cols = safe_cols(df_balance, ['planta', 'torta_inventario_inicial_kg', 'torta_produccion_kg', 'torta_despacho_kg', 'torta_inventario_final_kg'])
                if len(torta_cols) > 1:
                    df_torta = df_balance[torta_cols].copy()
                    col_names = ['Planta']
                    mapping = {'torta_inventario_inicial_kg': 'Inv. Inicial', 'torta_produccion_kg': 'Producción',
                               'torta_despacho_kg': 'Despacho', 'torta_inventario_final_kg': 'Inv. Final'}
                    col_names += [mapping.get(c, c) for c in torta_cols[1:]]
                    df_torta.columns = col_names
                    st.dataframe(df_torta, use_container_width=True, hide_index=True)
                
                # Análisis IA
                st.divider()
                st.markdown("#### 🤖 Análisis IA")
                
                # Mostrar contexto del usuario si existe
                if 'balance_contexto_usuario' in st.session_state and st.session_state['balance_contexto_usuario']:
                    st.info(f"📝 **Contexto del usuario:** {st.session_state['balance_contexto_usuario']}")
                
                if 'balance_analysis' in st.session_state:
                    st.markdown(st.session_state['balance_analysis'])
                else:
                    # Intentar generar análisis desde datos guardados
                    if 'balance_results' in st.session_state:
                        with st.spinner("Generando análisis..."):
                            contexto = st.session_state.get('balance_contexto_usuario', '')
                            analisis = generate_balance_analysis(st.session_state['balance_results'], contexto)
                            st.markdown(analisis)
                    else:
                        st.info("El análisis se generará cuando proceses nuevos reportes.")
        
        # =====================================================================
        # TAB: HISTORIAL
        # =====================================================================
        with tab_historial:
            st.markdown("### 📈 Historial de Balance")
            
            # Cargar todos los datos
            balance_path = "data/balance_almendra.csv"
            if os.path.exists(balance_path):
                try:
                    df_historico = pd.read_csv(balance_path)
                except Exception:
                    df_historico = pd.DataFrame()
                
                # Validar que hay datos y columna fecha
                if not df_historico.empty and 'fecha' in df_historico.columns:
                    df_historico = df_historico.dropna(subset=['fecha'])
                    
                if not df_historico.empty and 'fecha' in df_historico.columns:
                    # Selector de fecha
                    fechas_disponibles = sorted(df_historico['fecha'].unique(), reverse=True)
                    fecha_sel = st.selectbox(
                        "Seleccionar fecha",
                        options=fechas_disponibles,
                        index=0
                    )
                    
                    # Mostrar datos de la fecha seleccionada
                    df_fecha = df_historico[df_historico['fecha'] == fecha_sel]
                    
                    st.markdown(f"**📅 Balance del {fecha_sel}**")
                    st.dataframe(df_fecha, use_container_width=True, hide_index=True)
                    
                    # Gráfico de tendencia
                    st.markdown("#### 📊 Tendencia de Inventarios")
                    
                    # Usar columnas existentes para el gráfico
                    trend_cols = []
                    for col in ['nuez_inventario_final_kg', 'almendra_inventario_final_kg', 'ckpo_inventario_final_kg']:
                        if col in df_historico.columns:
                            trend_cols.append(col)
                    
                    if trend_cols:
                        df_trend = df_historico.groupby('fecha')[trend_cols].sum().reset_index()
                        
                        import plotly.express as px
                        
                        fig = px.line(
                            df_trend, 
                            x='fecha', 
                            y=trend_cols,
                            labels={'value': 'Kilogramos', 'fecha': 'Fecha', 'variable': 'Producto'},
                            title='Evolución de Inventarios Finales'
                        )
                        fig.update_layout(
                            template='plotly_dark',
                            paper_bgcolor='rgba(0,0,0,0)',
                            plot_bgcolor='rgba(0,0,0,0)'
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("📊 No hay columnas de inventario para graficar.")
                else:
                    st.info("📭 No hay datos históricos disponibles.")
            else:
                st.info("📭 Aún no se han procesado reportes. Carga los reportes diarios para comenzar.")


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
