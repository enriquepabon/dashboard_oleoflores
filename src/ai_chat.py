"""
AI Chat Module para Oleoflores BI Dashboard
============================================

Este módulo proporciona funcionalidad de chat con IA para analizar
datos seleccionados del dashboard.

Soporta múltiples proveedores:
- Google Gemini (más económico): pip install google-generativeai
- OpenAI: pip install openai

Configuración via variables de entorno:
- GOOGLE_API_KEY para Gemini
- OPENAI_API_KEY para OpenAI
"""

# Cargar variables de entorno desde .env (por si se importa antes que app.py)
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import pandas as pd
import os
from typing import Optional, Dict, Any, List
import json

# =============================================================================
# DETECCIÓN DE PROVEEDORES DISPONIBLES
# =============================================================================

# Intentar importar Google Gemini (más económico)
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# Intentar importar OpenAI
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# =============================================================================
# CONFIGURACIÓN
# =============================================================================

# Modelos disponibles (ordenados por costo)
MODELS = {
    "gemini-1.5-flash-latest": {"provider": "gemini", "name": "Gemini 1.5 Flash", "cost": "Gratis"},
    "gemini-1.5-pro-latest": {"provider": "gemini", "name": "Gemini 1.5 Pro", "cost": "~$1.25/1M tokens"},
    "gpt-4o-mini": {"provider": "openai", "name": "GPT-4o Mini", "cost": "~$0.15/1M tokens"},
    "gpt-4o": {"provider": "openai", "name": "GPT-4o", "cost": "~$5/1M tokens"},
}

DEFAULT_MODEL = "gemini-1.5-flash-latest"  # El más económico por defecto
MAX_CONTEXT_TOKENS = 4000

SYSTEM_PROMPT = """Eres un analista experto en agroindustria y procesamiento de palma de aceite.
Trabajas para Oleoflores, una empresa colombiana dedicada a la producción de aceite de palma.

Tu rol es analizar los datos del dashboard y responder preguntas de manera:
- Clara y concisa
- Basada únicamente en los datos proporcionados
- Con insights accionables cuando sea posible
- En español

Métricas clave que manejas:
- RFF (Racimos de Fruta Fresca): Materia prima en toneladas
- CPO (Crude Palm Oil): Aceite crudo producido en toneladas  
- TEA/TAE (Tasa de Extracción de Aceite): CPO/RFF × 100, indica eficiencia
- ME (Meta/Estimado): Valores presupuestados

Zonas de operación: Codazzi, MLB, A&G, Sinú

Si no tienes suficiente información para responder, indícalo claramente."""

# =============================================================================
# FUNCIONES DE INICIALIZACIÓN
# =============================================================================

def initialize_chat_session():
    """Inicializa el estado de sesión para el chat."""
    if 'selected_data' not in st.session_state:
        st.session_state.selected_data = {}
    
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    if 'chat_open' not in st.session_state:
        st.session_state.chat_open = False
    
    if 'ai_model' not in st.session_state:
        st.session_state.ai_model = DEFAULT_MODEL


def get_available_providers() -> Dict[str, bool]:
    """Retorna los proveedores disponibles."""
    return {
        "gemini": GEMINI_AVAILABLE and bool(os.getenv("GOOGLE_API_KEY")),
        "openai": OPENAI_AVAILABLE and bool(os.getenv("OPENAI_API_KEY"))
    }


def get_available_models() -> List[str]:
    """Retorna solo los modelos de proveedores disponibles."""
    providers = get_available_providers()
    available = []
    
    for model_id, info in MODELS.items():
        if providers.get(info["provider"], False):
            available.append(model_id)
    
    return available


def check_any_api_configured() -> bool:
    """Verifica si hay alguna API configurada."""
    providers = get_available_providers()
    return any(providers.values())


# =============================================================================
# CLIENTES DE IA
# =============================================================================

def get_gemini_model(model_name: str = "gemini-1.5-flash"):
    """Obtiene el modelo de Gemini si está disponible."""
    if not GEMINI_AVAILABLE:
        return None
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return None
    
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(model_name)


def get_openai_client():
    """Obtiene el cliente de OpenAI si está disponible."""
    if not OPENAI_AVAILABLE:
        return None
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    
    return OpenAI(api_key=api_key)


# =============================================================================
# FUNCIONES DE CONTEXTO
# =============================================================================

def add_data_to_context(key: str, data: Any, description: str = ""):
    """Agrega datos al contexto seleccionado."""
    if 'selected_data' not in st.session_state:
        st.session_state.selected_data = {}
    
    st.session_state.selected_data[key] = {
        'data': data,
        'description': description,
        'type': type(data).__name__
    }


def remove_data_from_context(key: str):
    """Quita datos del contexto seleccionado."""
    if 'selected_data' in st.session_state and key in st.session_state.selected_data:
        del st.session_state.selected_data[key]


def clear_context():
    """Limpia todo el contexto seleccionado."""
    st.session_state.selected_data = {}


def get_context_items() -> List[str]:
    """Retorna lista de items seleccionados."""
    if 'selected_data' not in st.session_state:
        return []
    return list(st.session_state.selected_data.keys())


def format_data_for_context(data: Any) -> str:
    """Formatea datos para incluir en el prompt del chat."""
    if isinstance(data, pd.DataFrame):
        if len(data) > 50:
            data = data.head(50)
            truncated = True
        else:
            truncated = False
        
        result = data.to_markdown(index=False)
        if truncated:
            result += "\n... (datos truncados, mostrando primeras 50 filas)"
        return result
    
    elif isinstance(data, dict):
        return json.dumps(data, indent=2, ensure_ascii=False, default=str)
    
    elif isinstance(data, list):
        return json.dumps(data, indent=2, ensure_ascii=False, default=str)
    
    else:
        return str(data)


def build_context_prompt() -> str:
    """Construye el prompt con todo el contexto seleccionado."""
    if 'selected_data' not in st.session_state or not st.session_state.selected_data:
        return "No hay datos seleccionados para analizar."
    
    context_parts = []
    
    for key, item in st.session_state.selected_data.items():
        description = item.get('description', key)
        data = item.get('data')
        formatted = format_data_for_context(data)
        
        context_parts.append(f"### {description}\n\n{formatted}")
    
    return "\n\n---\n\n".join(context_parts)


def get_context_summary() -> str:
    """Genera un resumen breve del contexto seleccionado."""
    if 'selected_data' not in st.session_state or not st.session_state.selected_data:
        return "Sin datos seleccionados"
    
    items = []
    for key, item in st.session_state.selected_data.items():
        desc = item.get('description', key)
        items.append(f"• {desc}")
    
    return "\n".join(items)


# =============================================================================
# FUNCIONES DE CHAT
# =============================================================================

def query_gemini(question: str, model_name: str = "gemini-1.5-flash") -> str:
    """Envía pregunta a Google Gemini."""
    model = get_gemini_model(model_name)
    
    if model is None:
        if not GEMINI_AVAILABLE:
            return "❌ Instala google-generativeai: `pip install google-generativeai`"
        return "❌ Configura GOOGLE_API_KEY"
    
    context = build_context_prompt()
    
    prompt = f"""{SYSTEM_PROMPT}

## Datos del Dashboard

{context}

---

## Pregunta del Usuario

{question}"""
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"❌ Error Gemini: {str(e)}"


def query_openai(question: str, model_name: str = "gpt-4o-mini") -> str:
    """Envía pregunta a OpenAI."""
    client = get_openai_client()
    
    if client is None:
        if not OPENAI_AVAILABLE:
            return "❌ Instala openai: `pip install openai`"
        return "❌ Configura OPENAI_API_KEY"
    
    context = build_context_prompt()
    
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"""## Datos del Dashboard

{context}

---

## Pregunta del Usuario

{question}"""}
    ]
    
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=0.7,
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ Error OpenAI: {str(e)}"


def query_ai(question: str, model: str = None) -> str:
    """
    Envía pregunta al modelo de IA seleccionado.
    Automáticamente detecta el proveedor basado en el modelo.
    """
    if model is None:
        model = st.session_state.get('ai_model', DEFAULT_MODEL)
    
    model_info = MODELS.get(model)
    
    if model_info is None:
        return f"❌ Modelo no reconocido: {model}"
    
    provider = model_info["provider"]
    
    if provider == "gemini":
        return query_gemini(question, model)
    elif provider == "openai":
        return query_openai(question, model)
    else:
        return f"❌ Proveedor no soportado: {provider}"


def add_to_history(question: str, answer: str):
    """Agrega una interacción al historial del chat."""
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    st.session_state.chat_history.append({
        'question': question,
        'answer': answer
    })


def clear_history():
    """Limpia el historial del chat."""
    st.session_state.chat_history = []


# =============================================================================
# COMPONENTES DE UI
# =============================================================================

def render_data_selector(key: str, description: str, data: Any) -> bool:
    """Renderiza un checkbox para seleccionar datos."""
    is_selected = key in st.session_state.get('selected_data', {})
    
    selected = st.checkbox(
        "📌",
        value=is_selected,
        key=f"select_{key}",
        help=f"Seleccionar para análisis IA: {description}"
    )
    
    if selected and not is_selected:
        add_data_to_context(key, data, description)
    elif not selected and is_selected:
        remove_data_from_context(key)
    
    return selected


def render_chat_panel():
    """Renderiza el panel de chat en el sidebar."""
    st.markdown("### 🤖 Chat IA")
    
    # Verificar proveedores
    providers = get_available_providers()
    
    if not any(providers.values()):
        # Mostrar instrucciones de configuración
        st.warning("⚠️ Configura una API de IA")
        
        with st.expander("📋 Instrucciones", expanded=True):
            st.markdown("""
**Opción 1: Google Gemini (más económico)**
```bash
pip install google-generativeai
export GOOGLE_API_KEY='tu-api-key'
```
[Obtener API key gratis](https://makersuite.google.com/app/apikey)

**Opción 2: OpenAI**
```bash
pip install openai
export OPENAI_API_KEY='tu-api-key'
```
            """)
        return
    
    # Selector de modelo
    available_models = get_available_models()
    
    if len(available_models) > 1:
        model_options = {m: f"{MODELS[m]['name']} ({MODELS[m]['cost']})" for m in available_models}
        selected_model = st.selectbox(
            "🧠 Modelo:",
            options=available_models,
            format_func=lambda x: model_options[x],
            key="model_selector"
        )
        st.session_state.ai_model = selected_model
    else:
        selected_model = available_models[0]
        st.session_state.ai_model = selected_model
        st.caption(f"🧠 Usando: {MODELS[selected_model]['name']}")
    
    st.success(f"✅ IA Conectada")
    
    # Contexto seleccionado
    context_summary = get_context_summary()
    with st.expander("📌 Datos seleccionados", expanded=False):
        if context_summary == "Sin datos seleccionados":
            st.caption("Selecciona tablas o gráficas con el icono 📌")
        else:
            st.markdown(context_summary)
            if st.button("🗑️ Limpiar selección", key="clear_context"):
                clear_context()
                st.rerun()
    
    st.divider()
    
    # Campo de pregunta
    question = st.text_area(
        "💬 Tu pregunta:",
        placeholder="Ej: ¿Por qué la TEA está baja en Codazzi?",
        height=80,
        key="chat_question"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        send_btn = st.button("📤 Enviar", type="primary", use_container_width=True)
    with col2:
        if st.button("🗑️ Limpiar chat", use_container_width=True):
            clear_history()
            st.rerun()
    
    if send_btn and question.strip():
        with st.spinner("🔄 Analizando..."):
            answer = query_ai(question)
            add_to_history(question, answer)
            st.rerun()
    
    st.divider()
    
    # Historial
    if 'chat_history' in st.session_state and st.session_state.chat_history:
        st.markdown("**📜 Historial:**")
        for i, item in enumerate(reversed(st.session_state.chat_history[-5:])):
            with st.container():
                st.markdown(f"**🧑 Tú:** {item['question']}")
                st.markdown(f"**🤖 IA:** {item['answer']}")
                st.divider()
