"""
Módulo de Autenticación - Oleoflores Dashboard
==============================================

Maneja autenticación con Google OAuth usando streamlit-google-auth.
Requiere que los usuarios tengan correo @oleoflores.com y estén autorizados.
"""

import streamlit as st
import json
import tempfile
import os

# =============================================================================
# CONFIGURACIÓN
# =============================================================================

ALLOWED_DOMAIN = "oleoflores.com"

# =============================================================================
# FUNCIONES DE CONFIGURACIÓN
# =============================================================================

def is_auth_configured() -> bool:
    """
    Verifica si la autenticación está configurada en secrets.
    """
    try:
        if "google_oauth" not in st.secrets:
            return False
        
        oauth = st.secrets["google_oauth"]
        required_keys = ["client_id", "client_secret"]
        
        for key in required_keys:
            if key not in oauth or not oauth[key]:
                return False
        
        return True
    except Exception:
        return False


def get_google_credentials():
    """
    Obtiene las credenciales de Google OAuth desde secrets.
    Returns dict con formato para streamlit-google-auth.
    """
    try:
        oauth = st.secrets["google_oauth"]
        return {
            "web": {
                "client_id": oauth["client_id"],
                "client_secret": oauth["client_secret"],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [oauth.get("redirect_uri", "http://localhost:8501")]
            }
        }
    except Exception:
        return None


def get_authorized_users() -> list:
    """Obtiene la lista de usuarios autorizados."""
    try:
        return list(st.secrets.get("auth_users", {}).get("authorized", []))
    except Exception:
        return []


def get_admin_users() -> list:
    """Obtiene la lista de administradores."""
    try:
        return list(st.secrets.get("auth_users", {}).get("admins", []))
    except Exception:
        return []


def is_admin(email: str) -> bool:
    """Verifica si el email es administrador."""
    if not email:
        return False
    return email.lower() in [e.lower() for e in get_admin_users()]


def is_authorized(email: str) -> bool:
    """Verifica si el email está autorizado."""
    if not email:
        return False
    return email.lower() in [e.lower() for e in get_authorized_users()]


def is_valid_domain(email: str) -> bool:
    """Verifica si el email es del dominio corporativo."""
    if not email:
        return False
    return email.lower().endswith(f"@{ALLOWED_DOMAIN}")


# =============================================================================
# COMPONENTES UI
# =============================================================================

def render_setup_pending():
    """Muestra mensaje cuando auth no está configurada."""
    st.markdown("""
    <div style="text-align: center; padding: 4rem 2rem;">
        <div style="font-size: 4rem;">🔧</div>
        <h2>Configuración Pendiente</h2>
        <p>La autenticación con Google OAuth aún no está configurada.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Diagnostic info
    try:
        if "google_oauth" not in st.secrets:
            st.error("❌ Falta sección `[google_oauth]` en secrets")
        else:
            oauth = st.secrets["google_oauth"]
            missing = []
            for key in ["client_id", "client_secret", "redirect_uri", "cookie_key"]:
                if key not in oauth:
                    missing.append(key)
            if missing:
                st.warning(f"⚠️ Faltan: `{', '.join(missing)}`")
    except Exception as e:
        st.error(f"Error: {e}")
    
    st.info("""
    **Configuración requerida en secrets:**
    ```toml
    [google_oauth]
    client_id = "xxx.apps.googleusercontent.com"
    client_secret = "xxx"
    redirect_uri = "https://tu-app.streamlit.app"
    cookie_key = "xxx"
    
    [auth_users]
    authorized = ["email@oleoflores.com"]
    admins = ["admin@oleoflores.com"]
    ```
    """)


def render_access_denied(reason: str = "generic"):
    """Muestra página de acceso denegado."""
    messages = {
        'domain': ('🚫', 'Solo correos @oleoflores.com'),
        'not_authorized': ('🔒', 'Usuario no autorizado. Contacta al administrador.'),
        'generic': ('⚠️', 'Acceso denegado')
    }
    
    icon, msg = messages.get(reason, messages['generic'])
    
    st.markdown(f"""
    <div style="text-align: center; padding: 4rem 2rem;">
        <div style="font-size: 4rem;">{icon}</div>
        <h2>{msg}</h2>
    </div>
    """, unsafe_allow_html=True)
    
    user_info = st.session_state.get('user_info', {})
    if user_info:
        st.info(f"📧 Sesión: **{user_info.get('email', 'N/A')}**")
    
    if st.button("🔄 Probar con otra cuenta", use_container_width=True):
        if "authenticator" in st.session_state:
            st.session_state["authenticator"].logout()
        st.session_state['connected'] = False
        st.rerun()


def handle_authentication() -> bool:
    """
    Maneja el flujo completo de autenticación.
    
    Returns:
        bool: True si usuario puede acceder
    """
    # Verificar si auth está configurada
    if not is_auth_configured():
        render_setup_pending()
        return False
    
    # Importar streamlit-google-auth
    try:
        from streamlit_google_auth import Authenticate
    except ImportError:
        st.error("❌ Falta instalar: `pip install streamlit-google-auth`")
        return False
    
    # Inicializar autenticador
    if "authenticator" not in st.session_state:
        try:
            # Crear archivo temporal con credenciales
            credentials = get_google_credentials()
            if not credentials:
                st.error("Error al obtener credenciales")
                return False
            
            # Guardar credenciales en archivo temporal
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
            json.dump(credentials, temp_file)
            temp_file.close()
            
            oauth = st.secrets["google_oauth"]
            
            authenticator = Authenticate(
                secret_credentials_path=temp_file.name,
                cookie_name='oleoflores_auth',
                cookie_key=oauth.get("cookie_key", "oleoflores_secret_key"),
                redirect_uri=oauth.get("redirect_uri", "http://localhost:8501"),
            )
            st.session_state["authenticator"] = authenticator
            st.session_state["temp_creds_file"] = temp_file.name
        except Exception as e:
            st.error(f"Error inicializando auth: {e}")
            return False
    
    # Verificar autenticación
    st.session_state["authenticator"].check_authentification()
    
    # Usuario no conectado -> mostrar login
    if not st.session_state.get('connected', False):
        render_login_page()
        return False
    
    # Usuario conectado - verificar permisos
    user_info = st.session_state.get('user_info', {})
    email = user_info.get('email', '')
    
    # Verificar dominio
    if not is_valid_domain(email):
        render_access_denied('domain')
        return False
    
    # Verificar autorización
    if not is_authorized(email):
        render_access_denied('not_authorized')
        return False
    
    return True


def render_login_page():
    """Renderiza la página de login."""
    st.markdown("""
    <style>
        .login-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 70vh;
            text-align: center;
        }
        .login-card {
            background: #171717;
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            padding: 2rem;
            max-width: 400px;
            margin: 0 auto;
        }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div class="login-container">
            <div style="font-size: 4rem;">🌴</div>
            <h1>Oleoflores</h1>
            <p style="color: #a1a1aa;">Business Intelligence Dashboard</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.markdown("### 🔐 Iniciar Sesión")
        st.markdown("Accede con tu cuenta corporativa de Google")
        
        # Mostrar botón de login
        st.session_state["authenticator"].login()
        
        st.markdown("""
        <p style="color: #71717a; font-size: 0.85rem; margin-top: 1rem;">
            ⚠️ Solo usuarios @oleoflores.com autorizados pueden acceder.
        </p>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)


def render_user_badge():
    """Renderiza badge de usuario en sidebar."""
    if not st.session_state.get('connected', False):
        return
    
    user_info = st.session_state.get('user_info', {})
    email = user_info.get('email', '')
    name = user_info.get('name', email.split('@')[0] if email else 'Usuario')
    is_admin_user = is_admin(email)
    
    role = "🔑 Admin" if is_admin_user else "👤 Usuario"
    
    st.markdown(f"""
    <div style="
        background: rgba(96, 165, 250, 0.1);
        border: 1px solid rgba(96, 165, 250, 0.3);
        border-radius: 12px;
        padding: 12px;
        margin: 10px 0;
    ">
        <div style="font-weight: 600; color: #ffffff;">{name}</div>
        <div style="font-size: 0.8rem; color: #a1a1aa;">{email}</div>
        <div style="font-size: 0.75rem; color: #60a5fa; margin-top: 4px;">{role}</div>
    </div>
    """, unsafe_allow_html=True)


def get_auth_status() -> dict:
    """Obtiene estado de autenticación."""
    connected = st.session_state.get('connected', False)
    user_info = st.session_state.get('user_info', {})
    email = user_info.get('email', '') if connected else ''
    
    return {
        'is_logged_in': connected,
        'is_valid_domain': is_valid_domain(email),
        'is_authorized': is_authorized(email),
        'is_admin': is_admin(email),
        'email': email,
        'name': user_info.get('name', '')
    }
