"""
Oleoflores BI Dashboard
=======================

Aplicación principal de Business Intelligence para el Grupo Oleoflores.
Visualización de la cadena de valor Farm-to-Fork.

Ejecutar con: streamlit run app.py
"""

import streamlit as st

# =============================================================================
# CONFIGURACIÓN DE PÁGINA
# =============================================================================

st.set_page_config(
    page_title="Oleoflores BI Dashboard",
    page_icon="🌴",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": "### Oleoflores BI Dashboard v1.0\nSistema de Business Intelligence para análisis de la cadena de valor."
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
    
    /* Títulos de sección */
    .section-header {
        color: #2E7D32;
        font-weight: 600;
        border-bottom: 2px solid #F9A825;
        padding-bottom: 10px;
        margin-bottom: 20px;
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e0e0e0;
    }
    
    /* Botones */
    .stButton > button {
        background-color: #2E7D32;
        color: white;
        border: none;
        border-radius: 5px;
    }
    
    .stButton > button:hover {
        background-color: #1B5E20;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# HEADER PRINCIPAL
# =============================================================================

st.title("🌴 Oleoflores BI Dashboard")
st.markdown("**Sistema de Business Intelligence** | Cadena de Valor Farm-to-Fork")
st.divider()

# =============================================================================
# CONTENIDO TEMPORAL (Se reemplazará en tareas posteriores)
# =============================================================================

st.info("""
👋 **Bienvenido al Dashboard de Oleoflores**

Este dashboard está en desarrollo. Las siguientes funcionalidades se implementarán próximamente:

- 📊 **Resumen Ejecutivo**: KPIs principales y tendencias
- 🌾 **Upstream**: Análisis de campo y extracción (RFF, TEA, CPO)
- 🏭 **Downstream**: Refinería, productos y flujo de masa (Sankey)
- 📤 **Carga de Datos**: Upload de archivos CSV/Excel
- 🚨 **Alertas**: Sistema de notificaciones para valores fuera de rango
""")

# Placeholder para mostrar que la app funciona
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="📦 Toneladas RFF",
        value="--",
        delta="Pendiente"
    )

with col2:
    st.metric(
        label="🎯 TEA Promedio",
        value="--%",
        delta="Pendiente"
    )

with col3:
    st.metric(
        label="🛢️ Producción CPO",
        value="--",
        delta="Pendiente"
    )

with col4:
    st.metric(
        label="🧈 Margarinas",
        value="--",
        delta="Pendiente"
    )

st.divider()

# Footer
st.markdown(
    "<div style='text-align: center; color: #666666; font-size: 12px;'>"
    "Oleoflores BI Dashboard v1.0 | © 2024 Grupo Oleoflores"
    "</div>",
    unsafe_allow_html=True
)

