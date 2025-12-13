"""
Módulo de Autenticación - Oleoflores Dashboard
==============================================

Maneja autenticación con Google OAuth y control de acceso
basado en usuarios autorizados con correos @oleoflores.com.

Requiere Streamlit >= 1.42.0 para soporte nativo de OIDC.
"""

import streamlit as st
from typing import Optional

# =============================================================================
# CONFIGURACIÓN
# =============================================================================

ALLOWED_DOMAIN = "oleoflores.com"

# =============================================================================
# FUNCIONES DE AUTENTICACIÓN
# =============================================================================

def get_authorized_users() -> list:
    """
    Obtiene la lista de usuarios autorizados desde secrets.
    
    Returns:
        list: Lista de emails autorizados
    """
    try:
        return st.secrets.get("auth", {}).get("users", {}).get("authorized", [])
    except Exception:
        return []


def get_admin_users() -> list:
    """
    Obtiene la lista de administradores desde secrets.
    
    Returns:
        list: Lista de emails con permisos de admin
    """
    try:
        return st.secrets.get("auth", {}).get("users", {}).get("admins", [])
    except Exception:
        return []


def is_admin(email: str) -> bool:
    """
    Verifica si el email tiene permisos de administrador.
    
    Args:
        email: Email del usuario
        
    Returns:
        bool: True si es administrador
    """
    if not email:
        return False
    return email.lower() in [e.lower() for e in get_admin_users()]


def is_authorized(email: str) -> bool:
    """
    Verifica si el email está en la lista de usuarios autorizados.
    
    Args:
        email: Email del usuario
        
    Returns:
        bool: True si está autorizado
    """
    if not email:
        return False
    return email.lower() in [e.lower() for e in get_authorized_users()]


def is_valid_domain(email: str) -> bool:
    """
    Verifica si el email pertenece al dominio corporativo.
    
    Args:
        email: Email del usuario
        
    Returns:
        bool: True si el dominio es válido
    """
    if not email:
        return False
    return email.lower().endswith(f"@{ALLOWED_DOMAIN}")


def check_authentication() -> bool:
    """
    Verifica el estado completo de autenticación del usuario.
    
    Flujo:
    1. Verificar si está logueado (st.user.is_logged_in)
    2. Verificar dominio del email (@oleoflores.com)
    3. Verificar si está en lista de autorizados
    
    Returns:
        bool: True si el usuario está autenticado y autorizado
    """
    # Verificar si está logueado
    if not st.user.is_logged_in:
        return False
    
    email = getattr(st.user, 'email', None)
    
    if not email:
        return False
    
    # Verificar dominio corporativo
    if not is_valid_domain(email):
        return False
    
    # Verificar si está autorizado
    if not is_authorized(email):
        return False
    
    return True


def get_auth_status() -> dict:
    """
    Obtiene el estado detallado de autenticación.
    
    Returns:
        dict: Estado con is_logged_in, is_valid_domain, is_authorized, email, name
    """
    is_logged_in = st.user.is_logged_in
    email = getattr(st.user, 'email', None) if is_logged_in else None
    name = getattr(st.user, 'name', None) if is_logged_in else None
    
    return {
        'is_logged_in': is_logged_in,
        'is_valid_domain': is_valid_domain(email) if email else False,
        'is_authorized': is_authorized(email) if email else False,
        'is_admin': is_admin(email) if email else False,
        'email': email,
        'name': name
    }


# =============================================================================
# COMPONENTES UI
# =============================================================================

def render_login_page():
    """
    Renderiza la página de inicio de sesión con branding Oleoflores.
    """
    # Estilos para la página de login
    st.markdown("""
    <style>
        .login-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 80vh;
            text-align: center;
        }
        .login-logo {
            font-size: 5rem;
            margin-bottom: 1rem;
        }
        .login-title {
            font-size: 2.5rem;
            font-weight: 600;
            color: #ffffff;
            margin-bottom: 0.5rem;
        }
        .login-subtitle {
            font-size: 1rem;
            color: #a1a1aa;
            margin-bottom: 2rem;
        }
        .login-card {
            background: #171717;
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            padding: 2rem;
            max-width: 400px;
            margin: 0 auto;
        }
        .login-info {
            color: #71717a;
            font-size: 0.85rem;
            margin-top: 1.5rem;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Contenedor principal
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div class="login-container">
            <div class="login-logo">🌴</div>
            <h1 class="login-title">Oleoflores</h1>
            <p class="login-subtitle">Business Intelligence Dashboard</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Card de login
        with st.container():
            st.markdown('<div class="login-card">', unsafe_allow_html=True)
            st.markdown("### 🔐 Iniciar Sesión")
            st.markdown("Accede con tu cuenta corporativa de Google")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Botón de login con Google
            if st.button("🚀 Iniciar sesión con Google", use_container_width=True, type="primary"):
                st.login()
            
            st.markdown("""
            <p class="login-info">
                ⚠️ Solo usuarios con correo @oleoflores.com autorizados pueden acceder.
            </p>
            """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)


def render_access_denied(reason: str = "generic"):
    """
    Renderiza página de acceso denegado según el motivo.
    
    Args:
        reason: 'domain' | 'not_authorized' | 'generic'
    """
    messages = {
        'domain': {
            'icon': '🚫',
            'title': 'Acceso Restringido',
            'message': 'Solo se permiten correos corporativos **@oleoflores.com**',
            'detail': 'Por favor, inicia sesión con tu cuenta corporativa de Google.'
        },
        'not_authorized': {
            'icon': '🔒',
            'title': 'Usuario No Autorizado',
            'message': 'Tu cuenta no tiene acceso a este dashboard.',
            'detail': 'Contacta al administrador para solicitar acceso.'
        },
        'generic': {
            'icon': '⚠️',
            'title': 'Acceso Denegado',
            'message': 'No tienes permisos para acceder.',
            'detail': 'Verifica tus credenciales e intenta nuevamente.'
        }
    }
    
    msg = messages.get(reason, messages['generic'])
    
    st.markdown("""
    <style>
        .denied-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 60vh;
            text-align: center;
        }
        .denied-icon {
            font-size: 4rem;
            margin-bottom: 1rem;
        }
        .denied-card {
            background: rgba(248, 113, 113, 0.1);
            border: 1px solid rgba(248, 113, 113, 0.3);
            border-radius: 16px;
            padding: 2rem;
            max-width: 500px;
            margin: 0 auto;
        }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown(f"""
        <div class="denied-container">
            <div class="denied-icon">{msg['icon']}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f'<div class="denied-card">', unsafe_allow_html=True)
        st.markdown(f"### {msg['title']}")
        st.markdown(msg['message'])
        st.markdown(f"*{msg['detail']}*")
        
        # Mostrar email del usuario si está logueado
        if st.user.is_logged_in:
            email = getattr(st.user, 'email', 'desconocido')
            st.info(f"📧 Sesión iniciada como: **{email}**")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("🔄 Intentar con otra cuenta", use_container_width=True):
                st.logout()
        with col_b:
            if st.button("🚪 Cerrar sesión", use_container_width=True, type="secondary"):
                st.logout()
        
        st.markdown('</div>', unsafe_allow_html=True)


def handle_authentication() -> bool:
    """
    Maneja el flujo completo de autenticación.
    Debe llamarse al inicio de la aplicación.
    
    Returns:
        bool: True si el usuario puede acceder, False si debe detenerse
    """
    auth_status = get_auth_status()
    
    # Caso 1: No está logueado -> mostrar login
    if not auth_status['is_logged_in']:
        render_login_page()
        return False
    
    # Caso 2: Logueado pero dominio incorrecto
    if not auth_status['is_valid_domain']:
        render_access_denied('domain')
        return False
    
    # Caso 3: Dominio correcto pero no autorizado
    if not auth_status['is_authorized']:
        render_access_denied('not_authorized')
        return False
    
    # Caso 4: Todo OK
    return True


def render_user_badge():
    """
    Renderiza un badge con información del usuario logueado.
    Para usar en el sidebar.
    """
    if not st.user.is_logged_in:
        return
    
    email = getattr(st.user, 'email', '')
    name = getattr(st.user, 'name', email.split('@')[0] if email else 'Usuario')
    is_admin_user = is_admin(email)
    
    role = "🔑 Administrador" if is_admin_user else "👤 Usuario"
    
    st.markdown(f"""
    <div style="
        background: rgba(96, 165, 250, 0.1);
        border: 1px solid rgba(96, 165, 250, 0.3);
        border-radius: 12px;
        padding: 12px;
        margin: 10px 0;
    ">
        <div style="font-weight: 600; color: #ffffff; margin-bottom: 4px;">
            {name}
        </div>
        <div style="font-size: 0.8rem; color: #a1a1aa;">
            {email}
        </div>
        <div style="font-size: 0.75rem; color: #60a5fa; margin-top: 4px;">
            {role}
        </div>
    </div>
    """, unsafe_allow_html=True)
