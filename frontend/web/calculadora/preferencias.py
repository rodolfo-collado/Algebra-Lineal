"""Preferencias de presentación que la app de escritorio recuerda entre aperturas.

Solo tres claves con valores cerrados. WebView2 corre en modo privado, así que
nada más (entradas, resultados, historial ni navegación) sobrevive al cierre.
"""

import json
import os
import tempfile
import threading
from contextlib import contextmanager
from collections import OrderedDict
from pathlib import Path
from uuid import UUID

from django.conf import settings


# Serializa los hilos; el lock del sistema operativo también coordina instancias.
_ACCESO = threading.RLock()
# Solo memoria del servidor: el orden no se guarda en preferencias.json.
_ESCRITURAS = OrderedDict()
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


def guardar(clave, valor, escritura=None):
    """Guarda una de las tres preferencias; cualquier otra clave o valor se rechaza."""
    archivo = _archivo()
    if archivo is None or valor not in VALORES.get(clave, ()):
        return False
    orden = None
    if escritura is not None:
        try:
            sesion, numero = escritura.split(":")
            orden = int(numero)
            if str(UUID(sesion)) != sesion or str(orden) != numero or not 0 < orden <= 2**53 - 1:
                return False
        except (AttributeError, TypeError, ValueError):
            return False
    with _ACCESO:
        if orden is not None and orden <= _ESCRITURAS.get((sesion, clave), 0):
            return True
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
        if orden is not None:
            _ESCRITURAS[sesion, clave] = orden
            _ESCRITURAS.move_to_end((sesion, clave))
            # ponytail: 256 claves de sesión bastan para una ventana por servidor.
            if len(_ESCRITURAS) > 256:
                _ESCRITURAS.popitem(last=False)
    return True
