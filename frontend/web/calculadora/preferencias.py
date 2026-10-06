"""Preferencias de presentación que la app de escritorio recuerda entre aperturas.

Solo tres claves con valores cerrados. WebView2 corre en modo privado, así que
nada más (entradas, resultados, historial ni navegación) sobrevive al cierre.
"""

import json
import os
import tempfile
import threading
from pathlib import Path

from django.conf import settings


# Waitress atiende con varios hilos. Leer y escribir en serie evita que una escritura
# pise a otra (numeros.js envía formato y precisión a la vez) y que Windows rechace el
# reemplazo mientras otro hilo tiene el archivo abierto para leerlo.
_ACCESO = threading.RLock()
VALORES = {
    "pygebra-tema": ("light", "dark"),
    "pygebra-formato-numerico": ("exacto", "decimal"),
    "pygebra-precision-decimal": ("2", "4", "6", "8"),
}


def _archivo():
    ruta = settings.DESKTOP_PREFERENCES_FILE
    return Path(ruta) if settings.DESKTOP_MODE and ruta else None


def leer():
    """Preferencias guardadas y válidas; un archivo ausente o dañado no impide abrir."""
    archivo = _archivo()
    if archivo is None:
        return {}
    try:
        with _ACCESO:
            datos = json.loads(archivo.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    if not isinstance(datos, dict):
        return {}
    return {clave: valor for clave, valor in datos.items() if valor in VALORES.get(clave, ())}


def guardar(clave, valor):
    """Guarda una de las tres preferencias; cualquier otra clave o valor se rechaza."""
    archivo = _archivo()
    if archivo is None or valor not in VALORES.get(clave, ()):
        return False
    with _ACCESO:
        archivo.parent.mkdir(parents=True, exist_ok=True)
        # Reemplazo atómico: cerrar la app a mitad de escritura no deja un JSON a medias.
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=archivo.parent, suffix=".tmp", delete=False
        ) as temporal:
            json.dump(leer() | {clave: valor}, temporal, indent=2)
        try:
            os.replace(temporal.name, archivo)
        except OSError:
            os.unlink(temporal.name)
            raise
    return True
