"""Utilidades compartidas por las pruebas: salida de terminal y HTML de resultados."""

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


def capturar_con_resultado(funcion, *argumentos):
    """Como capturar, pero tambien devuelve lo que la funcion retorna."""
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        resultado = funcion(*argumentos)

    return resultado, buffer.getvalue()


def elemento_html(html, posicion, etiqueta):
    """El elemento `etiqueta` que abre antes de `posicion`, hasta su cierre real aunque anide otros iguales."""
    inicio = html.rindex(f"<{etiqueta}", 0, posicion)
    profundidad = 0
    for marca in re.finditer(rf"<(/?){etiqueta}\b[^>]*>", html[inicio:]):
        profundidad += -1 if marca.group(1) else 1
        if not profundidad:
            return html[inicio:inicio + marca.end()]
    raise AssertionError(f"<{etiqueta}> sin cerrar")
