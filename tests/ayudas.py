"""Utilidades compartidas por las pruebas de la interfaz de terminal."""

import io
import re
from contextlib import redirect_stdout

_ANSI = re.compile(r"\x1b\[[0-9;]*m")


def sin_ansi(texto):
    return _ANSI.sub("", texto)


def capturar(funcion, *argumentos):
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        funcion(*argumentos)

    return buffer.getvalue()
