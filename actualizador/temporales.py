"""El intento de descarga conserva sus archivos hasta descartarlos o cerrar PyGebra."""

import logging
import os
import shutil
import subprocess
import tempfile
import weakref
from pathlib import Path


def _borrar_al_salir(carpeta, pid):
    # El instalador lee su propio EXE. El proceso de limpieza debe sobrevivir a PyGebra.
    comando = (
        f"$proceso = Get-Process -Id {pid} -ErrorAction SilentlyContinue; "
        "if ($proceso) { $proceso.WaitForExit() }; "
        "Remove-Item -LiteralPath $env:PYGEBRA_DESCARGA_TEMPORAL -Recurse -Force -ErrorAction Stop"
    )
    powershell = Path(os.environ["SystemRoot"]) / "System32/WindowsPowerShell/v1.0/powershell.exe"
    return subprocess.Popen(
        [str(powershell), "-NoProfile", "-NonInteractive", "-Command", comando],
        env={**os.environ, "PYGEBRA_DESCARGA_TEMPORAL": str(carpeta)},
        # Windows retiene el directorio de trabajo hasta que sale el auxiliar.
        cwd=powershell.parent,
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        # Windows PowerShell puede salir sin ejecutar -Command con DETACHED_PROCESS.
        creationflags=subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP,
    )


class DescargaTemporal:
    def __init__(self, actualizador, base):
        base.mkdir(parents=True, exist_ok=True)
        self.ruta = Path(tempfile.mkdtemp(prefix="PyGebra-actualizacion-", dir=base))
        self.proceso_instalador = None
        self.descartar = weakref.finalize(actualizador, self._limpiar)

    def _limpiar(self):
        try:
            proceso = self.proceso_instalador
            if os.name == "nt" and proceso is not None and proceso.poll() is None:
                _borrar_al_salir(self.ruta, proceso.pid)
                return
            try:
                shutil.rmtree(self.ruta)
            except OSError:
                if not self.ruta.exists():
                    return
                if os.name != "nt":
                    raise
                # Una descarga en el hilo daemon puede tener un .part abierto al salir.
                _borrar_al_salir(self.ruta, os.getpid())
        except OSError:
            logging.getLogger(__name__).exception("No se pudo limpiar %s", self.ruta)
