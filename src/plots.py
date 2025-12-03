"""
Oleoflores BI Dashboard - Módulo de Visualizaciones
====================================================

Este módulo contiene funciones para generar gráficos interactivos con Plotly:
- Scorecards (KPIs)
- Gauge Charts (Velocímetros)
- Bar Charts (Barras agrupadas)
- Heatmaps (Mapas de calor)
- Sankey Diagrams (Flujo de masa)
- Area Charts (Áreas apiladas)
- Bullet Charts (Cumplimiento)
- Line Charts (Tendencias)
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import List, Dict, Optional, Tuple

from .utils import (
    COLORS, 
    CHART_COLORS, 
    SANKEY_COLORS,
    formato_numero,
    formato_porcentaje,
    get_color_variacion,
    get_flecha_variacion
)

# =============================================================================
# CONFIGURACIÓN COMÚN DE GRÁFICOS
# =============================================================================

LAYOUT_DEFAULTS = {
    "font": {"family": "Inter, sans-serif", "color": COLORS["texto_principal"]},
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor": "rgba(0,0,0,0)",
    "margin": {"l": 40, "r": 40, "t": 60, "b": 40},
    "hoverlabel": {
        "bgcolor": "white",
        "font_size": 12,
        "font_family": "Inter, sans-serif"
    }
}


def apply_layout_defaults(fig: go.Figure, title: str = None, height: int = 400) -> go.Figure:
    """Aplica configuración común a todos los gráficos."""
    fig.update_layout(
        **LAYOUT_DEFAULTS,
        title={
            "text": title,
            "font": {"size": 16, "color": COLORS["texto_principal"]},
            "x": 0.5,
            "xanchor": "center"
        } if title else None,
        height=height
    )
    return fig


# =============================================================================
# 3.1 - SCORECARDS (KPIs)
# =============================================================================

def create_scorecard(
    value: float,
    title: str,
    delta: float = None,
    delta_reference: float = None,
    prefix: str = "",
    suffix: str = "",
    icon: str = "",
    invert_delta: bool = False
) -> go.Figure:
    """
    Crea un scorecard/tarjeta KPI con valor y variación.
    
    Args:
        value: Valor principal a mostrar
        title: Título del KPI
        delta: Variación absoluta (opcional)
        delta_reference: Valor de referencia para calcular delta (opcional)
        prefix: Prefijo del valor (ej: "$")
        suffix: Sufijo del valor (ej: "%", "Ton")
        icon: Emoji o icono para el título
        invert_delta: Si True, delta positivo es negativo (ej: mermas)
    
    Returns:
        Figura Plotly tipo Indicator
    """
    # Calcular delta si se proporciona referencia
    if delta is None and delta_reference is not None and delta_reference != 0:
        delta = value - delta_reference
    
    # Determinar color del delta
    if delta is not None:
        delta_color = get_color_variacion(delta, invertir=invert_delta)
        delta_increasing_color = COLORS["verde_oleo"] if not invert_delta else COLORS["rojo_alerta"]
        delta_decreasing_color = COLORS["rojo_alerta"] if not invert_delta else COLORS["verde_oleo"]
    else:
        delta_increasing_color = COLORS["verde_oleo"]
        delta_decreasing_color = COLORS["rojo_alerta"]
    
    # Crear indicador
    fig = go.Figure()
    
    fig.add_trace(go.Indicator(
        mode="number+delta" if delta is not None else "number",
        value=value,
        title={
            "text": f"{icon} {title}" if icon else title,
            "font": {"size": 14, "color": COLORS["texto_secundario"]}
        },
        number={
            "prefix": prefix,
            "suffix": suffix,
            "font": {"size": 36, "color": COLORS["texto_principal"]},
            "valueformat": ",.0f" if suffix in ["Ton", ""] else ",.1f"
        },
        delta={
            "reference": value - delta if delta else None,
            "relative": False,
            "valueformat": ",.0f",
            "increasing": {"color": delta_increasing_color},
            "decreasing": {"color": delta_decreasing_color},
            "font": {"size": 14}
        } if delta is not None else None,
        domain={"x": [0, 1], "y": [0, 1]}
    ))
    
    fig.update_layout(
        height=150,
        margin={"l": 20, "r": 20, "t": 50, "b": 20},
        paper_bgcolor="rgba(0,0,0,0)",
    )
    
    return fig


# =============================================================================
# 3.2 - GAUGE CHART (VELOCÍMETRO - TEA)
# =============================================================================

def create_gauge_chart(
    value: float,
    title: str = "TEA",
    min_val: float = 0,
    max_val: float = 35,
    target: float = 23,
    thresholds: List[Tuple[float, str]] = None,
    suffix: str = "%"
) -> go.Figure:
    """
    Crea un gráfico de velocímetro/gauge para indicadores como TEA.
    
    Args:
        value: Valor actual
        title: Título del indicador
        min_val: Valor mínimo de la escala
        max_val: Valor máximo de la escala
        target: Valor objetivo/meta
        thresholds: Lista de tuplas (valor, color) para rangos
        suffix: Sufijo del valor
    
    Returns:
        Figura Plotly tipo Indicator Gauge
    """
    # Rangos por defecto para TEA
    if thresholds is None:
        thresholds = [
            (18, COLORS["rojo_alerta"]),    # 0-18: Bajo (rojo)
            (22, COLORS["dorado"]),          # 18-22: Aceptable (amarillo)
            (25, COLORS["verde_oleo"]),      # 22-25: Óptimo (verde)
            (35, COLORS["dorado"])           # 25-35: Alto (amarillo)
        ]
    
    # Construir steps para el gauge (colores con transparencia via rgba)
    steps = []
    prev_val = min_val
    for threshold_val, color in thresholds:
        # Convertir hex a rgba con transparencia
        if color.startswith("#"):
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)
            color_rgba = f"rgba({r}, {g}, {b}, 0.3)"
        else:
            color_rgba = color
        steps.append({
            "range": [prev_val, threshold_val],
            "color": color_rgba
        })
        prev_val = threshold_val
    
    fig = go.Figure()
    
    fig.add_trace(go.Indicator(
        mode="gauge+number+delta",
        value=value,
        title={
            "text": title,
            "font": {"size": 18, "color": COLORS["texto_principal"]}
        },
        number={
            "suffix": suffix,
            "font": {"size": 32, "color": COLORS["texto_principal"]}
        },
        delta={
            "reference": target,
            "valueformat": ".1f",
            "suffix": suffix,
            "increasing": {"color": COLORS["verde_oleo"]},
            "decreasing": {"color": COLORS["rojo_alerta"]}
        },
        gauge={
            "axis": {
                "range": [min_val, max_val],
                "tickwidth": 1,
                "tickcolor": COLORS["texto_secundario"],
                "tickfont": {"size": 10}
            },
            "bar": {"color": COLORS["verde_oleo"], "thickness": 0.75},
            "bgcolor": "white",
            "borderwidth": 2,
            "bordercolor": COLORS["gris_claro"],
            "steps": steps,
            "threshold": {
                "line": {"color": COLORS["texto_principal"], "width": 4},
                "thickness": 0.75,
                "value": target
            }
        },
        domain={"x": [0, 1], "y": [0, 1]}
    ))
    
    # Agregar anotación de meta
    fig.add_annotation(
        x=0.5, y=-0.15,
        text=f"Meta: {target}{suffix}",
        showarrow=False,
        font={"size": 12, "color": COLORS["texto_secundario"]}
    )
    
    fig.update_layout(
        height=300,
        margin={"l": 30, "r": 30, "t": 60, "b": 40},
        paper_bgcolor="rgba(0,0,0,0)",
    )
    
    return fig


# =============================================================================
# 3.3 - GROUPED BAR CHART (BARRAS AGRUPADAS)
# =============================================================================

def create_grouped_bar_chart(
    df: pd.DataFrame,
    x_column: str,
    y_columns: List[str],
    y_names: List[str] = None,
    title: str = "Comparativa Real vs Meta",
    colors: List[str] = None,
    orientation: str = "v",
    show_values: bool = True
) -> go.Figure:
    """
    Crea un gráfico de barras agrupadas para comparativas.
    
    Args:
        df: DataFrame con los datos
        x_column: Columna para el eje X (ej: 'zona')
        y_columns: Lista de columnas para las barras (ej: ['rff_real', 'rff_presupuesto'])
        y_names: Nombres para la leyenda
        title: Título del gráfico
        colors: Colores personalizados para las barras
        orientation: 'v' vertical, 'h' horizontal
        show_values: Mostrar valores sobre las barras
    
    Returns:
        Figura Plotly Bar
    """
    if colors is None:
        colors = [COLORS["verde_oleo"], COLORS["dorado"]]
    
    if y_names is None:
        y_names = [col.replace('_', ' ').title() for col in y_columns]
    
    fig = go.Figure()
    
    for i, (col, name) in enumerate(zip(y_columns, y_names)):
        color = colors[i % len(colors)]
        
        if orientation == "v":
            fig.add_trace(go.Bar(
                x=df[x_column],
                y=df[col],
                name=name,
                marker_color=color,
                text=df[col].apply(lambda x: f"{x:,.0f}") if show_values else None,
                textposition="outside",
                textfont={"size": 10}
            ))
        else:
            fig.add_trace(go.Bar(
                y=df[x_column],
                x=df[col],
                name=name,
                marker_color=color,
                orientation="h",
                text=df[col].apply(lambda x: f"{x:,.0f}") if show_values else None,
                textposition="outside",
                textfont={"size": 10}
            ))
    
    fig.update_layout(
        barmode="group",
        xaxis_title=x_column.replace('_', ' ').title() if orientation == "v" else None,
        yaxis_title="Toneladas" if orientation == "v" else x_column.replace('_', ' ').title(),
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "center",
            "x": 0.5
        },
        bargap=0.2,
        bargroupgap=0.1
    )
    
    fig = apply_layout_defaults(fig, title, height=400)
    
    return fig


# =============================================================================
# 3.4 - HEATMAP (MAPA DE CALOR - COSECHA)
# =============================================================================

def create_heatmap(
    df: pd.DataFrame,
    x_column: str = "fecha",
    y_column: str = "zona",
    value_column: str = "rff_real",
    title: str = "Intensidad de Cosecha",
    colorscale: str = "YlGn",
    show_values: bool = True
) -> go.Figure:
    """
    Crea un mapa de calor para visualizar intensidad de datos.
    
    Args:
        df: DataFrame con los datos
        x_column: Columna para eje X (ej: 'fecha' o día)
        y_column: Columna para eje Y (ej: 'zona')
        value_column: Columna con los valores
        title: Título del gráfico
        colorscale: Escala de colores ('YlGn', 'RdYlGn', 'Blues', etc.)
        show_values: Mostrar valores en las celdas
    
    Returns:
        Figura Plotly Heatmap
    """
    # Pivotar datos para formato matriz
    pivot_df = df.pivot_table(
        index=y_column,
        columns=x_column,
        values=value_column,
        aggfunc='sum'
    ).fillna(0)
    
    # Formatear fechas si es columna de fecha
    if x_column == 'fecha':
        pivot_df.columns = [col.strftime('%d/%m') if hasattr(col, 'strftime') else col 
                          for col in pivot_df.columns]
    
    # Crear texto para las celdas
    text = pivot_df.values.astype(int).astype(str) if show_values else None
    
    fig = go.Figure()
    
    fig.add_trace(go.Heatmap(
        z=pivot_df.values,
        x=pivot_df.columns.tolist(),
        y=pivot_df.index.tolist(),
        colorscale=colorscale,
        text=text,
        texttemplate="%{text}" if show_values else None,
        textfont={"size": 10},
        hoverongaps=False,
        hovertemplate=(
            f"<b>{y_column.title()}</b>: %{{y}}<br>"
            f"<b>{x_column.title()}</b>: %{{x}}<br>"
            f"<b>{value_column.replace('_', ' ').title()}</b>: %{{z:,.0f}}<br>"
            "<extra></extra>"
        ),
        colorbar={
            "title": {"text": "Toneladas", "side": "right"},
            "thickness": 15,
            "len": 0.7
        }
    ))
    
    fig.update_layout(
        xaxis_title="Día" if x_column == "fecha" else x_column.title(),
        yaxis_title=y_column.title(),
        yaxis={"autorange": "reversed"}
    )
    
    fig = apply_layout_defaults(fig, title, height=350)
    
    return fig


# =============================================================================
# 3.5 - SANKEY DIAGRAM (FLUJO DE MASA)
# =============================================================================

def create_sankey_diagram(
    df: pd.DataFrame = None,
    cpo_entrada: float = None,
    oleina: float = None,
    rbd: float = None,
    margarinas: float = None,
    mermas: float = None,
    title: str = "Flujo de Masa - Refinería"
) -> go.Figure:
    """
    Crea un diagrama Sankey para visualizar el flujo de masa en refinería.
    
    Args:
        df: DataFrame con datos agregados (opcional)
        cpo_entrada: Total CPO de entrada
        oleina: Producción de oleína
        rbd: Producción de RBD
        margarinas: Producción de margarinas
        mermas: Total de mermas
        title: Título del gráfico
    
    Returns:
        Figura Plotly Sankey
    """
    # Si se proporciona DataFrame, extraer valores
    if df is not None:
        cpo_entrada = df['cpo_entrada'].sum() if 'cpo_entrada' in df.columns else cpo_entrada
        oleina = df['oleina_real'].sum() if 'oleina_real' in df.columns else oleina
        rbd = df['rbd_real'].sum() if 'rbd_real' in df.columns else rbd
        margarinas = df['margarinas_real'].sum() if 'margarinas_real' in df.columns else margarinas
        mermas = df['mermas'].sum() if 'mermas' in df.columns else mermas
    
    # Valores por defecto si no se proporcionan
    cpo_entrada = cpo_entrada or 1000
    oleina = oleina or 400
    rbd = rbd or 300
    margarinas = margarinas or 200
    mermas = mermas or 100
    
    # Nodos: 0=CPO Entrada, 1=Refinería, 2=Oleína, 3=RBD, 4=Margarinas, 5=Mermas
    nodes = {
        "label": [
            f"CPO Entrada<br>{cpo_entrada:,.0f} Ton",
            "Refinería",
            f"Oleína<br>{oleina:,.0f} Ton",
            f"RBD<br>{rbd:,.0f} Ton",
            f"Margarinas<br>{margarinas:,.0f} Ton",
            f"Mermas<br>{mermas:,.0f} Ton"
        ],
        "color": [
            SANKEY_COLORS["cpo_entrada"],
            SANKEY_COLORS["refineria"],
            SANKEY_COLORS["oleina"],
            SANKEY_COLORS["rbd"],
            SANKEY_COLORS["margarinas"],
            SANKEY_COLORS["mermas"]
        ],
        "pad": 20,
        "thickness": 30,
        "line": {"color": "black", "width": 0.5}
    }
    
    # Enlaces con transparencia
    links = {
        "source": [0, 1, 1, 1, 1],       # CPO -> Refinería, Refinería -> productos
        "target": [1, 2, 3, 4, 5],       # Destinos
        "value": [cpo_entrada, oleina, rbd, margarinas, mermas],
        "color": [
            "rgba(249, 168, 37, 0.4)",   # CPO a Refinería
            "rgba(21, 101, 192, 0.4)",   # Refinería a Oleína
            "rgba(0, 131, 143, 0.4)",    # Refinería a RBD
            "rgba(123, 31, 162, 0.4)",   # Refinería a Margarinas
            "rgba(198, 40, 40, 0.4)"     # Refinería a Mermas
        ],
        "hovertemplate": (
            "%{source.label} → %{target.label}<br>"
            "<b>%{value:,.0f} Toneladas</b><br>"
            "<extra></extra>"
        )
    }
    
    fig = go.Figure()
    
    fig.add_trace(go.Sankey(
        node=nodes,
        link=links,
        textfont={"size": 12, "color": COLORS["texto_principal"]}
    ))
    
    fig = apply_layout_defaults(fig, title, height=450)
    
    return fig


# =============================================================================
# 3.6 - AREA CHART (ÁREAS APILADAS - INVENTARIOS)
# =============================================================================

def create_area_chart(
    df: pd.DataFrame,
    x_column: str = "fecha",
    y_columns: List[str] = None,
    y_names: List[str] = None,
    title: str = "Evolución de Inventarios",
    stacked: bool = True,
    colors: List[str] = None
) -> go.Figure:
    """
    Crea un gráfico de áreas apiladas para evolución temporal.
    
    Args:
        df: DataFrame con los datos
        x_column: Columna para eje X (usualmente fecha)
        y_columns: Columnas para las áreas
        y_names: Nombres para la leyenda
        title: Título del gráfico
        stacked: Si True, áreas apiladas
        colors: Colores personalizados
    
    Returns:
        Figura Plotly Area
    """
    if y_columns is None:
        y_columns = ['oleina_real', 'rbd_real', 'margarinas_real']
    
    if y_names is None:
        y_names = [col.replace('_real', '').replace('_', ' ').title() for col in y_columns]
    
    if colors is None:
        colors = CHART_COLORS[:len(y_columns)]
    
    fig = go.Figure()
    
    # Ordenar por fecha
    df = df.sort_values(x_column)
    
    stackgroup = "one" if stacked else None
    
    for i, (col, name) in enumerate(zip(y_columns, y_names)):
        if col not in df.columns:
            continue
            
        fig.add_trace(go.Scatter(
            x=df[x_column],
            y=df[col],
            name=name,
            mode="lines",
            stackgroup=stackgroup,
            line={"width": 0.5, "color": colors[i % len(colors)]},
            fillcolor=colors[i % len(colors)].replace(")", ", 0.6)").replace("rgb", "rgba") 
                      if "rgb" in colors[i % len(colors)] else colors[i % len(colors)],
            hovertemplate=(
                f"<b>{name}</b><br>"
                "Fecha: %{x}<br>"
                "Valor: %{y:,.0f} Ton<br>"
                "<extra></extra>"
            )
        ))
    
    fig.update_layout(
        xaxis_title="Fecha",
        yaxis_title="Toneladas",
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "center",
            "x": 0.5
        },
        hovermode="x unified"
    )
    
    fig = apply_layout_defaults(fig, title, height=400)
    
    return fig


# =============================================================================
# 3.7 - BULLET CHART (CUMPLIMIENTO POR SKU)
# =============================================================================

def create_bullet_chart(
    categories: List[str],
    actuals: List[float],
    targets: List[float],
    title: str = "Cumplimiento por Producto",
    show_percentage: bool = True
) -> go.Figure:
    """
    Crea un gráfico bullet para mostrar cumplimiento vs meta.
    
    Args:
        categories: Lista de categorías/productos
        actuals: Valores reales
        targets: Valores meta
        title: Título del gráfico
        show_percentage: Mostrar porcentaje de cumplimiento
    
    Returns:
        Figura Plotly con barras bullet
    """
    fig = go.Figure()
    
    # Calcular máximo para escala
    max_val = max(max(actuals), max(targets)) * 1.2
    
    for i, (cat, actual, target) in enumerate(zip(categories, actuals, targets)):
        y_pos = len(categories) - i - 1
        pct = (actual / target * 100) if target > 0 else 0
        
        # Barra de fondo (meta + margen)
        fig.add_trace(go.Bar(
            x=[max_val],
            y=[cat],
            orientation='h',
            marker_color=COLORS["gris_claro"],
            showlegend=False,
            hoverinfo='skip'
        ))
        
        # Barra de meta
        fig.add_trace(go.Bar(
            x=[target],
            y=[cat],
            orientation='h',
            marker_color=COLORS["dorado"],
            opacity=0.5,
            name="Meta" if i == 0 else None,
            showlegend=(i == 0),
            hovertemplate=f"<b>{cat}</b><br>Meta: %{{x:,.0f}} Ton<extra></extra>"
        ))
        
        # Barra de valor real
        color = COLORS["verde_oleo"] if actual >= target else COLORS["rojo_alerta"]
        fig.add_trace(go.Bar(
            x=[actual],
            y=[cat],
            orientation='h',
            marker_color=color,
            name="Real" if i == 0 else None,
            showlegend=(i == 0),
            text=f"{actual:,.0f} ({pct:.0f}%)" if show_percentage else f"{actual:,.0f}",
            textposition="outside",
            textfont={"size": 11, "color": COLORS["texto_principal"]},
            hovertemplate=f"<b>{cat}</b><br>Real: %{{x:,.0f}} Ton<br>Cumplimiento: {pct:.1f}%<extra></extra>"
        ))
        
        # Línea de meta
        fig.add_shape(
            type="line",
            x0=target, x1=target,
            y0=y_pos - 0.4, y1=y_pos + 0.4,
            line={"color": COLORS["texto_principal"], "width": 3}
        )
    
    fig.update_layout(
        barmode="overlay",
        xaxis_title="Toneladas",
        yaxis_title=None,
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "center",
            "x": 0.5
        },
        xaxis={"range": [0, max_val]}
    )
    
    fig = apply_layout_defaults(fig, title, height=50 + len(categories) * 60)
    
    return fig


# =============================================================================
# 3.8 - LINE CHART (TENDENCIAS - REAL VS PRESUPUESTO)
# =============================================================================

def create_trend_line_chart(
    df: pd.DataFrame,
    x_column: str = "fecha",
    y_real: str = "valor_real",
    y_presupuesto: str = "valor_presupuesto",
    title: str = "Tendencia Real vs Presupuesto",
    y_title: str = "Toneladas",
    show_area: bool = True,
    show_markers: bool = True
) -> go.Figure:
    """
    Crea un gráfico de líneas para comparar tendencias Real vs Presupuesto.
    
    Args:
        df: DataFrame con los datos
        x_column: Columna para eje X
        y_real: Columna de valores reales
        y_presupuesto: Columna de valores presupuestados
        title: Título del gráfico
        y_title: Título del eje Y
        show_area: Mostrar área bajo la curva de diferencia
        show_markers: Mostrar puntos en las líneas
    
    Returns:
        Figura Plotly Line
    """
    fig = go.Figure()
    
    # Ordenar por fecha
    df = df.sort_values(x_column)
    
    mode = "lines+markers" if show_markers else "lines"
    
    # Área de diferencia (opcional)
    if show_area and y_real in df.columns and y_presupuesto in df.columns:
        fig.add_trace(go.Scatter(
            x=df[x_column],
            y=df[y_presupuesto],
            mode="lines",
            line={"width": 0},
            showlegend=False,
            hoverinfo='skip'
        ))
        
        fig.add_trace(go.Scatter(
            x=df[x_column],
            y=df[y_real],
            mode="lines",
            fill="tonexty",
            fillcolor="rgba(46, 125, 50, 0.1)",
            line={"width": 0},
            showlegend=False,
            hoverinfo='skip'
        ))
    
    # Línea de presupuesto
    if y_presupuesto in df.columns:
        fig.add_trace(go.Scatter(
            x=df[x_column],
            y=df[y_presupuesto],
            mode=mode,
            name="Presupuesto",
            line={
                "color": COLORS["dorado"],
                "width": 2,
                "dash": "dash"
            },
            marker={"size": 6},
            hovertemplate=(
                "<b>Presupuesto</b><br>"
                "Fecha: %{x}<br>"
                "Valor: %{y:,.0f}<br>"
                "<extra></extra>"
            )
        ))
    
    # Línea de real
    if y_real in df.columns:
        fig.add_trace(go.Scatter(
            x=df[x_column],
            y=df[y_real],
            mode=mode,
            name="Real",
            line={
                "color": COLORS["verde_oleo"],
                "width": 3
            },
            marker={"size": 8},
            hovertemplate=(
                "<b>Real</b><br>"
                "Fecha: %{x}<br>"
                "Valor: %{y:,.0f}<br>"
                "<extra></extra>"
            )
        ))
    
    fig.update_layout(
        xaxis_title="Fecha",
        yaxis_title=y_title,
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "center",
            "x": 0.5
        },
        hovermode="x unified"
    )
    
    fig = apply_layout_defaults(fig, title, height=400)
    
    return fig


# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================

def create_empty_chart(message: str = "No hay datos disponibles") -> go.Figure:
    """Crea un gráfico vacío con mensaje."""
    fig = go.Figure()
    
    fig.add_annotation(
        x=0.5, y=0.5,
        xref="paper", yref="paper",
        text=message,
        showarrow=False,
        font={"size": 16, "color": COLORS["texto_secundario"]}
    )
    
    fig.update_layout(
        xaxis={"visible": False},
        yaxis={"visible": False},
        height=300,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    
    return fig


# =============================================================================
# GRÁFICO DE TANQUES (NIVELES DE INVENTARIO)
# =============================================================================

def create_tank_chart(
    tanques: Dict[str, float],
    capacidades: Dict[str, float] = None,
    title: str = "Niveles de Tanques",
    color_lleno: str = "#F9A825",
    color_vacio: str = "#E0E0E0"
) -> go.Figure:
    """
    Crea un gráfico de barras que simula tanques con niveles de llenado.
    
    Args:
        tanques: Diccionario {nombre_tanque: nivel_actual}
        capacidades: Diccionario {nombre_tanque: capacidad_maxima}
        title: Título del gráfico
        color_lleno: Color de la parte llena
        color_vacio: Color de la parte vacía
    
    Returns:
        Figura Plotly con gráfico de tanques
    """
    if capacidades is None:
        # Capacidad por defecto: 1000 toneladas por tanque
        capacidades = {k: 1000 for k in tanques.keys()}
    
    nombres = list(tanques.keys())
    niveles = list(tanques.values())
    caps = [capacidades.get(n, 1000) for n in nombres]
    vacios = [c - n for c, n in zip(caps, niveles)]
    
    fig = go.Figure()
    
    # Parte llena (abajo)
    fig.add_trace(go.Bar(
        x=nombres,
        y=niveles,
        name="Nivel Actual",
        marker_color=color_lleno,
        text=[f"{n:,.0f}" for n in niveles],
        textposition="inside",
        textfont={"size": 12, "color": "white"},
        hovertemplate="<b>%{x}</b><br>Nivel: %{y:,.0f} Ton<extra></extra>"
    ))
    
    # Parte vacía (arriba)
    fig.add_trace(go.Bar(
        x=nombres,
        y=vacios,
        name="Capacidad Disponible",
        marker_color=color_vacio,
        hovertemplate="<b>%{x}</b><br>Disponible: %{y:,.0f} Ton<extra></extra>"
    ))
    
    fig.update_layout(
        barmode="stack",
        showlegend=False,
        yaxis_title="Toneladas",
        xaxis_title=None,
        height=300,
        margin={"l": 40, "r": 20, "t": 40, "b": 40},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    
    if title:
        fig.update_layout(title={"text": title, "font": {"size": 14}})
    
    return fig


# =============================================================================
# TABLA ESTILIZADA CON SEMÁFOROS (PARA STREAMLIT)
# =============================================================================

def get_semaforo_color(porcentaje: float, invertir: bool = False) -> str:
    """
    Retorna el color del semáforo según el porcentaje de cumplimiento.
    
    Args:
        porcentaje: Porcentaje de cumplimiento (0-100+)
        invertir: Si True, más alto es peor (ej: mermas)
    
    Returns:
        Color emoji: 🔴 (rojo), 🟡 (amarillo), 🟢 (verde)
    """
    if invertir:
        if porcentaje <= 95:
            return "🟢"
        elif porcentaje <= 105:
            return "🟡"
        else:
            return "🔴"
    else:
        if porcentaje >= 100:
            return "🟢"
        elif porcentaje >= 95:
            return "🟡"
        else:
            return "🔴"


def format_table_with_semaforo(
    df: pd.DataFrame,
    col_real: str,
    col_meta: str,
    nombre_indicador: str = "Indicador"
) -> pd.DataFrame:
    """
    Formatea un DataFrame agregando columnas de diferencia, % y semáforo.
    
    Args:
        df: DataFrame con datos por zona/planta
        col_real: Nombre de la columna con valores reales
        col_meta: Nombre de la columna con valores meta
        nombre_indicador: Nombre para la columna de indicador
    
    Returns:
        DataFrame formateado con columnas adicionales
    """
    df = df.copy()
    
    # Calcular diferencia y porcentaje
    df['Diferencia'] = df[col_real] - df[col_meta]
    df['% Cumpl'] = (df[col_real] / df[col_meta] * 100).round(1)
    df['Semáforo'] = df['% Cumpl'].apply(get_semaforo_color)
    
    # Formatear para mostrar
    df['% Cumpl'] = df.apply(lambda x: f"{x['Semáforo']} {x['% Cumpl']:.0f}%", axis=1)
    
    return df


# =============================================================================
# TABLA DE CALIDAD (ACIDEZ, HUMEDAD, IMPUREZAS)
# =============================================================================

def create_quality_table(
    df: pd.DataFrame,
    zona_col: str = 'zona',
    acidez_col: str = 'acidez',
    humedad_col: str = 'humedad',
    impurezas_col: str = 'impurezas'
) -> pd.DataFrame:
    """
    Crea una tabla de parámetros de calidad por zona.
    
    Args:
        df: DataFrame con datos
        zona_col: Columna de zona
        acidez_col: Columna de acidez
        humedad_col: Columna de humedad
        impurezas_col: Columna de impurezas
    
    Returns:
        DataFrame con promedios de calidad por zona
    """
    # Filtrar solo zonas con datos de calidad
    df_quality = df[df[acidez_col] > 0].copy()
    
    if df_quality.empty:
        return pd.DataFrame()
    
    # Agrupar por zona
    result = df_quality.groupby(zona_col).agg({
        acidez_col: 'mean',
        humedad_col: 'mean',
        impurezas_col: 'mean'
    }).round(2).reset_index()
    
    # Renombrar columnas
    result.columns = ['Planta', 'Acidez %', 'Humedad %', 'Impurezas %']
    
    # Agregar semáforos de calidad
    # Acidez: < 5% es bueno
    result['Acidez %'] = result['Acidez %'].apply(
        lambda x: f"{'🟢' if x < 4 else '🟡' if x < 5 else '🔴'} {x:.2f}%"
    )
    # Humedad: < 0.5% es bueno
    result['Humedad %'] = result['Humedad %'].apply(
        lambda x: f"{'🟢' if x < 0.3 else '🟡' if x < 0.5 else '🔴'} {x:.2f}%"
    )
    # Impurezas: < 0.1% es bueno
    result['Impurezas %'] = result['Impurezas %'].apply(
        lambda x: f"{'🟢' if x < 0.1 else '🟡' if x < 0.2 else '🔴'} {x:.2f}%"
    )
    
    return result

