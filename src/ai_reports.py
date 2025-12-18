"""
AI Reports Module - Generación de Reportes con IA
==================================================

Este módulo proporciona funcionalidad para generar reportes
ejecutivos en Markdown y exportarlos a PDF.

Uso:
    from src.ai_reports import generate_executive_report, export_report_to_pdf
"""

import os
import io
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
import pandas as pd

# =============================================================================
# CONFIGURACIÓN
# =============================================================================

REPORT_TEMPLATE = """# Reporte Ejecutivo - Oleoflores

**Fecha de generación:** {fecha}  
**Período:** {periodo}

---

## 📊 Resumen Ejecutivo

{resumen_ejecutivo}

---

## 📈 Indicadores Clave

{indicadores}

---

## 🔍 Análisis Detallado

{analisis}

---

## 💡 Recomendaciones

{recomendaciones}

---

## 📋 Datos de Respaldo

{datos_respaldo}

---

*Reporte generado automáticamente por Oleoflores BI Dashboard con asistencia de IA.*
"""

REPORT_SYSTEM_PROMPT = """Eres un analista senior generando un reporte ejecutivo para la alta gerencia.
El reporte debe ser:
- Profesional y conciso
- Enfocado en insights accionables
- Con recomendaciones estratégicas
- En español

Estructura tu respuesta en las secciones indicadas."""


# =============================================================================
# FUNCIONES DE GENERACIÓN
# =============================================================================

def generate_executive_report(
    all_data: Dict[str, Any],
    periodo: str = "Período actual",
    additional_context: str = "",
    model: str = None
) -> str:
    """
    Genera un reporte ejecutivo completo en Markdown.
    
    Args:
        all_data: Diccionario con todos los datos del dashboard
            {key: {'data': DataFrame/dict, 'description': str}}
        periodo: Descripción del período del reporte
        additional_context: Contexto adicional del usuario
        model: Modelo de IA a usar
    
    Returns:
        str: Reporte en formato Markdown
    """
    from src.ai_chat import query_ai, get_available_providers
    
    providers = get_available_providers()
    if not any(providers.values()):
        return _generate_basic_report(all_data, periodo)
    
    # Preparar datos para el prompt
    data_sections = []
    kpis_summary = []
    
    for key, value in all_data.items():
        data = value.get('data')
        description = value.get('description', key)
        
        # Formatear datos
        if isinstance(data, pd.DataFrame):
            if len(data) > 15:
                formatted = data.head(15).to_markdown(index=False)
                formatted += f"\n... ({len(data)} filas totales)"
            else:
                formatted = data.to_markdown(index=False)
        elif isinstance(data, dict):
            formatted = str(data)
        else:
            formatted = str(data)
        
        data_sections.append(f"### {description}\n{formatted}")
        
        # Extraer KPIs si es posible
        if isinstance(data, pd.DataFrame):
            for col in data.columns:
                if any(x in col.lower() for x in ['total', 'real', 'meta', 'sum']):
                    if data[col].dtype in ['int64', 'float64']:
                        kpis_summary.append(f"- {description} - {col}: {data[col].sum():,.0f}")
    
    all_data_formatted = "\n\n".join(data_sections)
    kpis_text = "\n".join(kpis_summary) if kpis_summary else "No hay KPIs disponibles"
    
    # Prompt para IA
    prompt = f"""{REPORT_SYSTEM_PROMPT}

**Período:** {periodo}
{f'**Contexto adicional:** {additional_context}' if additional_context else ''}

**Datos disponibles:**

{all_data_formatted}

**KPIs detectados:**
{kpis_text}

Genera un reporte ejecutivo con las siguientes secciones (responde en Markdown):

1. **Resumen Ejecutivo** (2-3 párrafos): Visión general del estado de operaciones
2. **Indicadores Clave** (lista): Los 5-7 KPIs más importantes con su estado
3. **Análisis Detallado** (3-4 párrafos): Análisis de tendencias, anomalías y comparaciones
4. **Recomendaciones** (lista numerada): 3-5 acciones prioritarias

Sé conciso pero completo."""

    try:
        ai_analysis = query_ai(prompt, model)
        
        # Parsear respuesta o usar como está
        fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
        
        # Intentar extraer secciones de la respuesta de IA
        sections = _parse_ai_response(ai_analysis)
        
        report = REPORT_TEMPLATE.format(
            fecha=fecha,
            periodo=periodo,
            resumen_ejecutivo=sections.get('resumen', ai_analysis[:500]),
            indicadores=sections.get('indicadores', 'Ver análisis completo'),
            analisis=sections.get('analisis', ai_analysis),
            recomendaciones=sections.get('recomendaciones', 'Ver análisis completo'),
            datos_respaldo=_format_data_summary(all_data)
        )
        
        return report
        
    except Exception as e:
        return _generate_basic_report(all_data, periodo, error=str(e))


def _parse_ai_response(response: str) -> Dict[str, str]:
    """Intenta parsear la respuesta de IA en secciones."""
    sections = {
        'resumen': '',
        'indicadores': '',
        'analisis': '',
        'recomendaciones': ''
    }
    
    # Buscar secciones por headers
    current_section = None
    lines = response.split('\n')
    current_content = []
    
    for line in lines:
        line_lower = line.lower()
        
        if 'resumen' in line_lower and ('#' in line or '**' in line):
            if current_section and current_content:
                sections[current_section] = '\n'.join(current_content)
            current_section = 'resumen'
            current_content = []
        elif 'indicador' in line_lower and ('#' in line or '**' in line):
            if current_section and current_content:
                sections[current_section] = '\n'.join(current_content)
            current_section = 'indicadores'
            current_content = []
        elif 'análisis' in line_lower and ('#' in line or '**' in line):
            if current_section and current_content:
                sections[current_section] = '\n'.join(current_content)
            current_section = 'analisis'
            current_content = []
        elif 'recomendacion' in line_lower and ('#' in line or '**' in line):
            if current_section and current_content:
                sections[current_section] = '\n'.join(current_content)
            current_section = 'recomendaciones'
            current_content = []
        elif current_section:
            current_content.append(line)
    
    # Última sección
    if current_section and current_content:
        sections[current_section] = '\n'.join(current_content)
    
    # Si no se parseó bien, usar la respuesta completa
    if not any(sections.values()):
        sections['analisis'] = response
    
    return sections


def _generate_basic_report(
    all_data: Dict[str, Any],
    periodo: str,
    error: str = None
) -> str:
    """Genera un reporte básico sin IA."""
    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
    
    error_msg = f"\n\n> ⚠️ Nota: {error}" if error else ""
    
    return f"""# Reporte Ejecutivo - Oleoflores

**Fecha de generación:** {fecha}  
**Período:** {periodo}
{error_msg}

---

## 📊 Datos del Dashboard

{_format_data_summary(all_data)}

---

*Reporte generado por Oleoflores BI Dashboard.*
*Para análisis con IA, configure OPENAI_API_KEY o GOOGLE_API_KEY.*
"""


def _format_data_summary(all_data: Dict[str, Any]) -> str:
    """Formatea un resumen de los datos para el reporte."""
    summary_parts = []
    
    for key, value in all_data.items():
        data = value.get('data')
        description = value.get('description', key)
        
        if isinstance(data, pd.DataFrame):
            summary_parts.append(f"### {description}\n\n{data.to_markdown(index=False)}")
        elif isinstance(data, dict):
            items = [f"- **{k}:** {v}" for k, v in data.items()]
            summary_parts.append(f"### {description}\n\n" + "\n".join(items))
        else:
            summary_parts.append(f"### {description}\n\n{data}")
    
    return "\n\n---\n\n".join(summary_parts) if summary_parts else "No hay datos disponibles"


# =============================================================================
# FUNCIONES DE EXPORTACIÓN
# =============================================================================

def export_report_to_pdf(markdown_content: str) -> Optional[bytes]:
    """
    Convierte contenido Markdown a PDF.
    
    Args:
        markdown_content: Contenido del reporte en Markdown
    
    Returns:
        bytes: Contenido del PDF o None si falla
    """
    try:
        import markdown
        
        # Convertir Markdown a HTML
        html_content = markdown.markdown(
            markdown_content,
            extensions=['tables', 'fenced_code', 'nl2br']
        )
        
        # Agregar estilos CSS
        styled_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{
                    font-family: 'Helvetica Neue', Arial, sans-serif;
                    font-size: 11pt;
                    line-height: 1.6;
                    color: #333;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 40px;
                }}
                h1 {{
                    color: #1a5f2a;
                    border-bottom: 2px solid #1a5f2a;
                    padding-bottom: 10px;
                }}
                h2 {{
                    color: #2d7a3e;
                    margin-top: 30px;
                }}
                h3 {{
                    color: #444;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                    font-size: 10pt;
                }}
                th, td {{
                    border: 1px solid #ddd;
                    padding: 8px;
                    text-align: left;
                }}
                th {{
                    background-color: #1a5f2a;
                    color: white;
                }}
                tr:nth-child(even) {{
                    background-color: #f9f9f9;
                }}
                blockquote {{
                    border-left: 4px solid #ffc107;
                    padding-left: 15px;
                    color: #666;
                    margin: 20px 0;
                }}
                hr {{
                    border: none;
                    border-top: 1px solid #ddd;
                    margin: 30px 0;
                }}
                ul, ol {{
                    margin: 15px 0;
                }}
                li {{
                    margin: 5px 0;
                }}
                strong {{
                    color: #1a5f2a;
                }}
                .emoji {{
                    font-size: 1.2em;
                }}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """
        
        # Intentar usar weasyprint
        try:
            from weasyprint import HTML
            pdf_bytes = HTML(string=styled_html).write_pdf()
            return pdf_bytes
        except ImportError:
            pass
        
        # Fallback: pdfkit (requiere wkhtmltopdf)
        try:
            import pdfkit
            pdf_bytes = pdfkit.from_string(styled_html, False)
            return pdf_bytes
        except ImportError:
            pass
        
        # Si ningún generador está disponible, retornar None
        return None
        
    except Exception as e:
        print(f"Error generando PDF: {e}")
        return None


def get_pdf_availability() -> Tuple[bool, str]:
    """
    Verifica si la exportación a PDF está disponible.
    
    Returns:
        Tuple[bool, str]: (disponible, mensaje)
    """
    try:
        from weasyprint import HTML
        return True, "weasyprint disponible"
    except ImportError:
        pass
    
    try:
        import pdfkit
        return True, "pdfkit disponible"
    except ImportError:
        pass
    
    return False, "Instala 'weasyprint' o 'pdfkit' para exportar a PDF"


def export_report_to_html(markdown_content: str) -> str:
    """
    Convierte contenido Markdown a HTML con estilos inline.
    Alternativa cuando PDF no está disponible.
    
    Args:
        markdown_content: Contenido del reporte en Markdown
    
    Returns:
        str: Contenido HTML
    """
    try:
        import markdown
        html = markdown.markdown(
            markdown_content,
            extensions=['tables', 'fenced_code', 'nl2br']
        )
        return html
    except ImportError:
        # Conversión básica sin librería markdown
        html = markdown_content.replace('\n', '<br>\n')
        html = html.replace('# ', '<h1>').replace('## ', '<h2>').replace('### ', '<h3>')
        return f"<html><body>{html}</body></html>"
