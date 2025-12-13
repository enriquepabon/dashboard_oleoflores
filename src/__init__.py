"""
Oleoflores BI Dashboard - Módulos
=================================

Este paquete contiene los módulos principales del dashboard:

- data_loader: Funciones de carga, validación y limpieza de datos (ETL)
- plots: Funciones de generación de gráficas Plotly
- utils: Constantes corporativas y funciones auxiliares
- auth: Autenticación con Google OAuth
- admin_panel: Panel de administración de usuarios
"""

from . import utils
from . import data_loader
from . import plots
from . import auth
from . import admin_panel

__version__ = "1.1.0"
__author__ = "Equipo Oleoflores"
