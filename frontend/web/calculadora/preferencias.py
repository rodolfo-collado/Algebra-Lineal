"""Preferencias de presentación que la app de escritorio recuerda entre aperturas.

Solo tres claves con valores cerrados. WebView2 corre en modo privado, así que
nada más (entradas, resultados, historial ni navegación) sobrevive al cierre.
"""

import json
import os
import tempfile
import threading
from contextlib import contextmanager
from pathlib import Path

from django.conf import settings


# Serializa los hilos; el lock del sistema operativo también coordina instancias.
_ACCESO = threading.RLock()
VALORES = {
    "pygebra-tema": ("light", "dark"),
    "pygebra-formato-numerico": ("exacto", "decimal"),
    "pygebra-precision-decimal": ("2", "4", "6", "8"),
}


def _archivo():
    ruta = settings.DESKTOP_PREFERENCES_FILE
    return Path(ruta) if settings.DESKTOP_MODE and ruta else None


@contextmanager
def _bloqueo(archivo):
    # El archivo de lock es estable aunque preferencias.json se reemplace. Cerrarlo
    # libera el lock también al morir el proceso; no contiene preferencias.
    with archivo.with_suffix(".lock").open("a+b") as candado:
        if os.name == "nt":
            import msvcrt

            candado.seek(0)
            msvcrt.locking(candado.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl

            fcntl.flock(candado.fileno(), fcntl.LOCK_EX)
        yield


def _leer(archivo):
    try:
        datos = json.loads(archivo.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    if not isinstance(datos, dict):
        return {}
    return {clave: valor for clave, valor in datos.items() if valor in VALORES.get(clave, ())}


def leer():
    """Preferencias guardadas y válidas; un archivo ausente o dañado no impide abrir."""
    archivo = _archivo()
    if archivo is None:
        return {}
    try:
        with _ACCESO:
            if not archivo.exists():
                return {}
            with _bloqueo(archivo):
                return _leer(archivo)
    except OSError:
        return {}


def guardar(clave, valor):
    """Guarda una de las tres preferencias; cualquier otra clave o valor se rechaza."""
    archivo = _archivo()
    if archivo is None or valor not in VALORES.get(clave, ()):
        return False
    with _ACCESO:
        archivo.parent.mkdir(parents=True, exist_ok=True)
        with _bloqueo(archivo):
            # El lock cubre lectura + modificación + reemplazo, no solo la escritura.
            temporal = tempfile.NamedTemporaryFile(
                "w", encoding="utf-8", dir=archivo.parent, suffix=".tmp", delete=False
            )
            try:
                with temporal:
                    json.dump(_leer(archivo) | {clave: valor}, temporal, indent=2)
                    temporal.flush()
                    os.fsync(temporal.fileno())
                os.replace(temporal.name, archivo)
            finally:
                Path(temporal.name).unlink(missing_ok=True)
    return True
