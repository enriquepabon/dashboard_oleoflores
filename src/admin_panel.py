"""
Panel de Administración - Oleoflores Dashboard
===============================================

Panel para gestionar usuarios autorizados del dashboard.
Solo accesible por administradores.
"""

import streamlit as st
from src.auth import get_authorized_users, get_admin_users, is_admin, ALLOWED_DOMAIN

# =============================================================================
# PANEL DE ADMINISTRACIÓN
# =============================================================================

def render_admin_panel():
    """
    Renderiza el panel completo de administración.
    """
    user_info = st.session_state.get('user_info', {})
    email = user_info.get('email', '')
    
    if not is_admin(email):
        st.error("⛔ No tienes permisos de administrador.")
        return
    
    st.markdown("### 🔐 Panel de Administración")
    
    tab1, tab2, tab3 = st.tabs(["👥 Usuarios", "➕ Agregar", "📋 Configuración"])
    
    with tab1:
        _render_user_list()
    
    with tab2:
        _render_add_user_form()
    
    with tab3:
        _render_config_generator()


def _render_user_list():
    """Muestra la lista actual de usuarios autorizados."""
    authorized = get_authorized_users()
    admins = get_admin_users()
    
    st.markdown("#### Usuarios Autorizados")
    
    if not authorized:
        st.info("No hay usuarios autorizados configurados.")
        return
    
    st.markdown(f"**Total:** {len(authorized)} usuarios")
    
    for email in authorized:
        role = "🔑 Admin" if email.lower() in [a.lower() for a in admins] else "👤 Usuario"
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"📧 `{email}`")
        with col2:
            st.markdown(f"*{role}*")
    
    st.divider()
    st.markdown("#### Administradores")
    
    if not admins:
        st.warning("⚠️ No hay administradores configurados.")
    else:
        for email in admins:
            st.markdown(f"🔑 `{email}`")


def _render_add_user_form():
    """Formulario para agregar/eliminar usuarios."""
    st.markdown("#### Gestionar Usuarios")
    
    st.info("""
    ⚠️ Los cambios requieren actualizar secrets en Streamlit Cloud.
    Usa el tab "Configuración" para generar el código.
    """)
    
    if 'pending_users' not in st.session_state:
        st.session_state.pending_users = list(get_authorized_users())
    
    if 'pending_admins' not in st.session_state:
        st.session_state.pending_admins = list(get_admin_users())
    
    # Agregar usuario
    st.markdown("##### ➕ Agregar Usuario")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        new_email = st.text_input("Email", placeholder=f"usuario@{ALLOWED_DOMAIN}", key="new_user_email")
    with col2:
        make_admin = st.checkbox("Admin", key="new_user_admin")
    
    if st.button("Agregar", type="primary", key="btn_add_user"):
        if not new_email:
            st.error("Ingresa un email.")
        elif not new_email.lower().endswith(f"@{ALLOWED_DOMAIN}"):
            st.error(f"Debe ser @{ALLOWED_DOMAIN}")
        elif new_email.lower() in [e.lower() for e in st.session_state.pending_users]:
            st.warning("Ya está en la lista.")
        else:
            st.session_state.pending_users.append(new_email.lower())
            if make_admin:
                st.session_state.pending_admins.append(new_email.lower())
            st.success(f"✅ {new_email} agregado")
            st.rerun()
    
    # Eliminar usuario
    st.markdown("##### ➖ Eliminar Usuario")
    
    if st.session_state.pending_users:
        user_to_remove = st.selectbox("Seleccionar", options=st.session_state.pending_users, key="user_to_remove")
        
        if st.button("Eliminar", type="secondary", key="btn_remove_user"):
            st.session_state.pending_users.remove(user_to_remove)
            if user_to_remove in st.session_state.pending_admins:
                st.session_state.pending_admins.remove(user_to_remove)
            st.success(f"✅ {user_to_remove} eliminado")
            st.rerun()


def _render_config_generator():
    """Genera la configuración TOML para secrets."""
    st.markdown("#### 📋 Generar Configuración")
    
    users = st.session_state.get('pending_users', get_authorized_users())
    admins = st.session_state.get('pending_admins', get_admin_users())
    
    users_str = ',\n    '.join([f'"{u}"' for u in users])
    admins_str = ',\n    '.join([f'"{a}"' for a in admins])
    
    config = f'''# Google OAuth (streamlit-google-auth)
[google_oauth]
client_id = "TU_CLIENT_ID.apps.googleusercontent.com"
client_secret = "TU_CLIENT_SECRET"
redirect_uri = "https://TU-APP.streamlit.app"
cookie_key = "TU_COOKIE_SECRET"

# Usuarios autorizados
[auth_users]
authorized = [
    {users_str}
]
admins = [
    {admins_str}
]'''
    
    st.code(config, language="toml")
    
    if st.button("🔄 Resetear lista", key="btn_reset"):
        st.session_state.pending_users = list(get_authorized_users())
        st.session_state.pending_admins = list(get_admin_users())
        st.rerun()


def render_admin_sidebar_button():
    """Renderiza botón de admin en sidebar (solo para admins)."""
    user_info = st.session_state.get('user_info', {})
    email = user_info.get('email', '')
    
    if not is_admin(email):
        return
    
    with st.expander("🔐 Administración", expanded=False):
        render_admin_panel()
