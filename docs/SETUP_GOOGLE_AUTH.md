# Configuración de Google OAuth para Oleoflores Dashboard

## Requisitos Previos

- Cuenta de Google Cloud Platform con acceso al proyecto de la organización
- URL del dashboard desplegado en Streamlit Cloud

## Paso 1: Crear Proyecto en Google Cloud

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un nuevo proyecto: `Oleoflores-Dashboard`
3. Selecciona el proyecto creado

## Paso 2: Configurar OAuth Consent Screen

1. Ve a **APIs & Services > OAuth consent screen**
2. Selecciona **Internal** (solo usuarios de tu organización @oleoflores.com)
3. Completa los campos:
   - **Nombre de app:** `Oleoflores BI Dashboard`
   - **Email de soporte:** tu email de administrador
   - **Logo:** (opcional)
   - **Dominios autorizados:** `streamlit.app`
4. Guarda y continúa
5. En **Scopes**, agrega:
   - `email`
   - `profile`
   - `openid`
6. Guarda y continúa hasta completar

## Paso 3: Crear Credenciales OAuth 2.0

1. Ve a **APIs & Services > Credentials**
2. Click en **+ CREATE CREDENTIALS > OAuth client ID**
3. Tipo de aplicación: **Web application**
4. Nombre: `Oleoflores Dashboard`
5. En **Authorized redirect URIs**, agrega:
   - `http://localhost:8501/oauth2callback` (desarrollo local)
   - `https://TU-APP.streamlit.app/oauth2callback` (producción)
6. Click en **Create**
7. **Guarda** el `Client ID` y `Client Secret` que se muestran

## Paso 4: Generar Cookie Secret

Ejecuta este comando en Python:

```python
import secrets
print(secrets.token_hex(32))
```

Guarda el resultado.

## Paso 5: Configurar Streamlit Cloud

1. Ve a [Streamlit Cloud](https://share.streamlit.io/)
2. Abre tu app y ve a **Settings > Secrets**
3. Agrega la siguiente configuración (reemplaza los valores):

```toml
# ===========================================
# GOOGLE OAUTH AUTHENTICATION
# ===========================================

[auth]
# Cambia TU-APP por tu URL real
redirect_uri = "https://TU-APP.streamlit.app/oauth2callback"
# El secret que generaste en el Paso 4
cookie_secret = "TU_COOKIE_SECRET_GENERADO"
# Del Paso 3
client_id = "TU_CLIENT_ID.apps.googleusercontent.com"
client_secret = "TU_CLIENT_SECRET"
# No cambiar - URL estándar de Google
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"

# ===========================================
# USUARIOS AUTORIZADOS
# ===========================================

[auth.users]
# Lista de emails autorizados (deben ser @oleoflores.com)
authorized = [
    "admin@oleoflores.com",
    "usuario1@oleoflores.com",
    "usuario2@oleoflores.com"
]

# Administradores (pueden ver panel de gestión de usuarios)
admins = [
    "admin@oleoflores.com"
]
```

4. Guarda los secrets
5. La app se reiniciará automáticamente

## Paso 6: Prueba Local (Opcional)

Para probar localmente antes de desplegar:

1. Crea/edita `.streamlit/secrets.toml` (no subir a git!)
2. Agrega la configuración del Paso 5 con `redirect_uri = "http://localhost:8501/oauth2callback"`
3. Ejecuta: `streamlit run app.py`
4. Prueba el login

## Gestión de Usuarios

### Agregar usuarios

1. Los administradores pueden usar el **Panel de Administración** en el sidebar
2. El panel genera la configuración TOML actualizada
3. Copia y pega en Streamlit Cloud > Settings > Secrets

### Eliminar usuarios

1. Usa el Panel de Administración para generar la lista sin el usuario
2. Actualiza los secrets en Streamlit Cloud

## Troubleshooting

### Error: "redirect_uri_mismatch"

- Verifica que la URI en Google Cloud coincida **exactamente** con la de secrets.toml
- Incluye el protocolo (`https://`) y el path (`/oauth2callback`)

### Error: "access_denied"

- Verifica que el usuario esté en la lista `authorized`
- Verifica que el email termine en `@oleoflores.com`

### Error: "unauthorized_client"

- Verifica que OAuth Consent Screen esté configurado como "Internal"
- El usuario debe pertenecer a la organización Google Workspace
