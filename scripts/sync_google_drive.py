"""
Google Drive Sync Module para Oleoflores BI Dashboard
======================================================

Descarga automática de archivos Excel desde Google Drive
y los convierte al formato del dashboard.

Soporta 3 archivos:
1. GEO_CPO: Datos CPO/RFF de Sinú y MLB
2. CZZ_CPKO: Datos Almendra/CPKO de Codazzi Expeller
3. SEGUIMIENTO: Datos UPSTREAM (Codazzi, A&G) y DOWNSTREAM (Refinerías)

Configuración requerida en .env:
- GOOGLE_DRIVE_FILE_ID_GEO_CPO: ID del archivo GEO CPO
- GOOGLE_DRIVE_FILE_ID_CPKO: ID del archivo CZZ CPKO
- GOOGLE_DRIVE_FILE_ID_DOWNSTREAM: ID del archivo SEGUIMIENTO (o GOOGLE_DRIVE_FILE_ID legacy)
- GOOGLE_SERVICE_ACCOUNT_JSON: JSON de credenciales (contenido completo)
  o
- GOOGLE_SERVICE_ACCOUNT_FILE: Ruta al archivo JSON de credenciales

Uso:
    python scripts/sync_google_drive.py
"""

import os
import sys
import json
import tempfile
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Intentar importar dependencias de Google
try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseDownload
    import io
    GOOGLE_DRIVE_AVAILABLE = True
except ImportError:
    GOOGLE_DRIVE_AVAILABLE = False

# Importar convertidores locales
try:
    from convert_excel_seguimiento import convert_excel_to_csv
    from convert_geo_cpo import convert_geo_cpo_to_csv
    from convert_czz_cpko import convert_cpko_to_csv
except ImportError:
    # Si se ejecuta desde otro directorio
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    try:
        from convert_excel_seguimiento import convert_excel_to_csv
        from convert_geo_cpo import convert_geo_cpo_to_csv
        from convert_czz_cpko import convert_cpko_to_csv
    except ImportError as e:
        print(f"⚠️ No se pudieron importar convertidores: {e}")
        convert_excel_to_csv = None
        convert_geo_cpo_to_csv = None
        convert_cpko_to_csv = None


# ============================================================================
# CONFIGURACIÓN
# ============================================================================

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def get_credentials():
    """
    Obtiene las credenciales de Google desde variables de entorno.
    
    Soporta dos formatos:
    1. GOOGLE_SERVICE_ACCOUNT_JSON: El JSON completo como string
    2. GOOGLE_SERVICE_ACCOUNT_FILE: Ruta al archivo JSON
    """
    # Opción 1: JSON como string (ideal para cloud/secrets)
    json_str = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
    if json_str:
        try:
            info = json.loads(json_str)
            return service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
        except json.JSONDecodeError as e:
            print(f"❌ Error parseando GOOGLE_SERVICE_ACCOUNT_JSON: {e}")
            return None
    
    # Opción 2: Archivo JSON local
    file_path = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE', 'credentials/service_account.json')
    if os.path.exists(file_path):
        return service_account.Credentials.from_service_account_file(file_path, scopes=SCOPES)
    
    print("❌ No se encontraron credenciales de Google.")
    print("   Configure GOOGLE_SERVICE_ACCOUNT_JSON o GOOGLE_SERVICE_ACCOUNT_FILE en .env")
    return None


def download_file_from_drive(file_id: str, credentials) -> str:
    """
    Descarga un archivo de Google Drive.
    
    Args:
        file_id: ID del archivo en Google Drive
        credentials: Credenciales de servicio
    
    Returns:
        str: Ruta al archivo temporal descargado
    """
    # Construir servicio de Drive
    service = build('drive', 'v3', credentials=credentials)
    
    # Obtener información del archivo
    file_metadata = service.files().get(fileId=file_id, fields='name,mimeType').execute()
    file_name = file_metadata.get('name', 'download.xlsx')
    mime_type = file_metadata.get('mimeType', '')
    
    print(f"📂 Archivo encontrado: {file_name}")
    print(f"   Tipo: {mime_type}")
    
    # Crear archivo temporal
    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, file_name)
    
    # Descargar según el tipo
    # Google Sheets nativo: application/vnd.google-apps.spreadsheet
    # Excel subido a Drive: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
    is_google_sheets = mime_type == 'application/vnd.google-apps.spreadsheet'
    
    if is_google_sheets:
        # Es un Google Sheets nativo, exportar como Excel
        print(f"   → Exportando Google Sheets como Excel...")
        request = service.files().export_media(
            fileId=file_id,
            mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    else:
        # Es un archivo binario (Excel nativo .xlsx/.xls)
        print(f"   → Descargando archivo Excel nativo...")
        request = service.files().get_media(fileId=file_id)
    
    # Descargar
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    
    done = False
    while not done:
        status, done = downloader.next_chunk()
        if status:
            print(f"   Descargando: {int(status.progress() * 100)}%")
    
    # Guardar archivo
    with open(temp_path, 'wb') as f:
        f.write(fh.getvalue())
    
    print(f"✅ Descargado: {temp_path}")
    return temp_path


def sync_from_google_drive(
    file_id: str = None,
    output_upstream: str = "data/upstream.csv",
    output_downstream: str = "data/downstream.csv"
) -> dict:
    """
    Sincroniza datos desde Google Drive.
    
    Args:
        file_id: ID del archivo (opcional, usa .env por defecto)
        output_upstream: Ruta de salida para upstream.csv
        output_downstream: Ruta de salida para downstream.csv
    
    Returns:
        dict: Resultado de la sincronización
    """
    result = {
        'success': False,
        'message': '',
        'timestamp': datetime.now().isoformat(),
        'records_upstream': 0,
        'records_downstream': 0
    }
    
    # Verificar que las dependencias están instaladas
    if not GOOGLE_DRIVE_AVAILABLE:
        result['message'] = "❌ Instala las dependencias: pip install google-api-python-client google-auth"
        return result
    
    # Obtener file_id
    if file_id is None:
        file_id = os.getenv('GOOGLE_DRIVE_FILE_ID')
    
    if not file_id:
        result['message'] = "❌ GOOGLE_DRIVE_FILE_ID no configurado en .env"
        return result
    
    # Obtener credenciales
    credentials = get_credentials()
    if credentials is None:
        result['message'] = "❌ No se pudieron cargar las credenciales de Google"
        return result
    
    try:
        # Descargar archivo
        print(f"\n🔄 Sincronizando desde Google Drive...")
        print(f"   File ID: {file_id[:20]}...")
        
        excel_path = download_file_from_drive(file_id, credentials)
        
        # Convertir a CSV
        print(f"\n📊 Convirtiendo Excel a CSV...")
        df_up, df_down = convert_excel_to_csv(
            excel_path,
            output_upstream,
            output_downstream
        )
        
        # Limpiar archivo temporal
        if os.path.exists(excel_path):
            os.remove(excel_path)
        
        # Resultado exitoso
        result['success'] = True
        result['message'] = "✅ Sincronización completada"
        result['records_upstream'] = len(df_up) if df_up is not None else 0
        result['records_downstream'] = len(df_down) if df_down is not None else 0
        
        print(f"\n✨ Sincronización completada:")
        print(f"   Upstream: {result['records_upstream']} registros")
        print(f"   Downstream: {result['records_downstream']} registros")
        
    except Exception as e:
        result['message'] = f"❌ Error: {str(e)}"
        print(result['message'])
    
    return result


def check_google_drive_config() -> dict:
    """
    Verifica la configuración de Google Drive para todos los archivos.
    
    Returns:
        dict: Estado de la configuración
    """
    config = {
        'available': GOOGLE_DRIVE_AVAILABLE,
        'credentials_available': False,
        'files': {
            'geo_cpo': bool(os.getenv('GOOGLE_DRIVE_FILE_ID_GEO_CPO')),
            'cpko': bool(os.getenv('GOOGLE_DRIVE_FILE_ID_CPKO')),
            'downstream': bool(os.getenv('GOOGLE_DRIVE_FILE_ID_DOWNSTREAM') or 
                              os.getenv('GOOGLE_DRIVE_FILE_ID')),  # Legacy fallback
        },
        'ready': False
    }
    
    if GOOGLE_DRIVE_AVAILABLE:
        creds = get_credentials()
        config['credentials_available'] = creds is not None
        # Ready if credentials available and at least one file configured
        config['ready'] = config['credentials_available'] and any(config['files'].values())
    
    return config


def sync_all_files(
    output_upstream: str = None,
    output_downstream: str = None
) -> dict:
    """
    Sincroniza todos los archivos configurados desde Google Drive.
    
    Orden de procesamiento:
    1. SEGUIMIENTO (A&G, Codazzi RFF/CPO) -> upstream base + downstream
    2. GEO_CPO (Sinú, MLB) -> merge with upstream
    3. CPKO (Almendra Codazzi) -> merge with upstream
    
    Returns:
        dict: Resultado de la sincronización
    """
    result = {
        'success': False,
        'message': '',
        'timestamp': datetime.now().isoformat(),
        'files_processed': [],
        'records_upstream': 0,
        'records_downstream': 0
    }
    
    if not GOOGLE_DRIVE_AVAILABLE:
        result['message'] = "❌ Instala las dependencias: pip install google-api-python-client google-auth"
        return result
    
    credentials = get_credentials()
    if credentials is None:
        result['message'] = "❌ No se pudieron cargar las credenciales de Google"
        return result
    
    # Definir rutas de salida
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if output_upstream is None:
        output_upstream = os.path.join(base_dir, 'data', 'upstream.csv')
    if output_downstream is None:
        output_downstream = os.path.join(base_dir, 'data', 'downstream.csv')
    
    print(f"\n{'='*60}")
    print("🔄 OLEOFLORES - SINCRONIZACIÓN COMPLETA")
    print(f"{'='*60}")
    
    try:
        # 1. Procesar SEGUIMIENTO (Codazzi/A&G upstream + downstream)
        file_id = os.getenv('GOOGLE_DRIVE_FILE_ID_DOWNSTREAM') or os.getenv('GOOGLE_DRIVE_FILE_ID')
        if file_id and convert_excel_to_csv:
            print(f"\n📥 1/3 Descargando SEGUIMIENTO...")
            try:
                excel_path = download_file_from_drive(file_id, credentials)
                print(f"📊 Procesando...")
                df_up, df_down = convert_excel_to_csv(excel_path, output_upstream, output_downstream)
                os.remove(excel_path)
                result['files_processed'].append('SEGUIMIENTO')
                result['records_downstream'] = len(df_down) if df_down is not None else 0
            except Exception as e:
                print(f"   ⚠️ Error: {e}")
        else:
            print(f"   ⏭️ SEGUIMIENTO no configurado")
        
        # 2. Procesar GEO_CPO (Sinú, MLB)
        file_id = os.getenv('GOOGLE_DRIVE_FILE_ID_GEO_CPO')
        if file_id and convert_geo_cpo_to_csv:
            print(f"\n📥 2/3 Descargando GEO_CPO...")
            try:
                excel_path = download_file_from_drive(file_id, credentials)
                print(f"📊 Procesando...")
                df = convert_geo_cpo_to_csv(excel_path, output_upstream)
                os.remove(excel_path)
                result['files_processed'].append('GEO_CPO')
            except Exception as e:
                print(f"   ⚠️ Error: {e}")
        else:
            print(f"   ⏭️ GEO_CPO no configurado")
        
        # 3. Procesar CPKO (Almendra Codazzi)
        file_id = os.getenv('GOOGLE_DRIVE_FILE_ID_CPKO')
        if file_id and convert_cpko_to_csv:
            print(f"\n📥 3/3 Descargando CPKO...")
            try:
                excel_path = download_file_from_drive(file_id, credentials)
                print(f"📊 Procesando...")
                df = convert_cpko_to_csv(excel_path, output_upstream)
                os.remove(excel_path)
                result['files_processed'].append('CPKO')
            except Exception as e:
                print(f"   ⚠️ Error: {e}")
        else:
            print(f"   ⏭️ CPKO no configurado")
        
        # Contar registros finales
        if os.path.exists(output_upstream):
            import pandas as pd
            df_final = pd.read_csv(output_upstream)
            result['records_upstream'] = len(df_final)
        
        result['success'] = len(result['files_processed']) > 0
        result['message'] = f"✅ Sincronizados: {', '.join(result['files_processed'])}"
        
        print(f"\n{'='*60}")
        print(f"✅ SINCRONIZACIÓN COMPLETADA")
        print(f"{'='*60}")
        print(f"📁 Archivos procesados: {', '.join(result['files_processed'])}")
        print(f"📊 Upstream: {result['records_upstream']} registros")
        print(f"📊 Downstream: {result['records_downstream']} registros")
        
    except Exception as e:
        result['message'] = f"❌ Error: {str(e)}"
        print(result['message'])
    
    return result


# ============================================================================
# CLI
# ============================================================================

def main():
    """Punto de entrada para ejecución desde línea de comandos."""
    print("=" * 60)
    print("🔄 OLEOFLORES - SYNC GOOGLE DRIVE")
    print("=" * 60)
    
    # Verificar configuración
    config = check_google_drive_config()
    
    if not config['available']:
        print("\n❌ Dependencias de Google no instaladas.")
        print("   Ejecuta: pip install google-api-python-client google-auth")
        return
    
    if not config['credentials_available']:
        print("\n❌ Credenciales de servicio no encontradas.")
        print("   Configure GOOGLE_SERVICE_ACCOUNT_JSON o GOOGLE_SERVICE_ACCOUNT_FILE")
        return
    
    # Mostrar archivos configurados
    print("\n📋 Archivos configurados:")
    for name, configured in config['files'].items():
        status = "✅" if configured else "❌"
        print(f"   {status} {name.upper()}")
    
    if not config['ready']:
        print("\n⚠️ Ningún archivo configurado.")
        print("   Configure al menos un GOOGLE_DRIVE_FILE_ID_* en .env")
        return
    
    # Ejecutar sincronización completa
    result = sync_all_files()
    
    if result['success']:
        print(f"\n✅ Listo! Datos actualizados a las {result['timestamp']}")
    else:
        print(f"\n❌ Error: {result['message']}")
        sys.exit(1)


if __name__ == "__main__":
    main()

