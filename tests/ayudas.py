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


_SUBINDICE = re.compile(r"x([₀-₉]+)")
_DIGITOS = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")


def antes_de_p2711(html):
    """Deshace en el HTML de Reducción solo los cambios deliberados de P27.11.

    Las capturas congeladas (P26.3 y P26.4) siguen protegiendo todo lo demás:
    x₁ → x1, el panel «Resultado» → «Resultado final» y la leyenda de pivotes anterior.
    """
    html = html.replace('class="panel-title">Resultado</h3>', 'class="panel-title">Resultado final</h3>')
    html = re.sub(r"Los pivotes se resaltan en la [^<]+?\.",
                  "Las columnas resaltadas en la matriz final contienen un pivote.", html)
    return _SUBINDICE.sub(lambda m: "x" + m[1].translate(_DIGITOS), html)


def elemento_html(html, posicion, etiqueta):
    """El elemento `etiqueta` que abre antes de `posicion`, hasta su cierre real aunque anide otros iguales."""
    inicio = html.rindex(f"<{etiqueta}", 0, posicion)
    profundidad = 0
    for marca in re.finditer(rf"<(/?){etiqueta}\b[^>]*>", html[inicio:]):
        profundidad += -1 if marca.group(1) else 1
        if not profundidad:
            return html[inicio:inicio + marca.end()]
    raise AssertionError(f"<{etiqueta}> sin cerrar")
