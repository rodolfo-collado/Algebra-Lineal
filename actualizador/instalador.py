"""Entrega el control al instalador de Inno Setup ya verificado."""

import subprocess

from .verificacion import verificar


# /SILENT muestra solo el progreso; /ACTUALIZAR=1 hace que Inno Setup espere el cierre
# de PyGebra y la vuelva a abrir al terminar (installer/AlgebraLineal.iss).
ARGUMENTOS = ("/SILENT", "/NORESTART", "/ACTUALIZAR=1")


def lanzar(ruta, esperado, popen=subprocess.Popen):
    """Vuelve a comprobar el SHA-256 justo antes de ejecutar: nada sin verificar se ejecuta."""
    verificar(ruta, esperado)
    # Independiente de PyGebra: debe sobrevivir a su cierre.
    flags = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    popen([str(ruta), *ARGUMENTOS], cwd=str(ruta.parent), close_fds=True, creationflags=flags)
