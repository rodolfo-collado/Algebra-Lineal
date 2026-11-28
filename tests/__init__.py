"""Pruebas de PyGebra.

Toda la suite y los runners de navegador (python -m tests.<nombre>_browser) escriben su
cuaderno de resoluciones en un temporal propio, nunca en el de la app instalada.
"""

import atexit
import os
import shutil
import tempfile

if "ALGEBRA_RESOLUCIONES" not in os.environ:
    _CARPETA = tempfile.mkdtemp(prefix="pygebra-resoluciones-")
    os.environ["ALGEBRA_RESOLUCIONES"] = os.path.join(_CARPETA, "resoluciones.sqlite3")
    atexit.register(shutil.rmtree, _CARPETA, True)
