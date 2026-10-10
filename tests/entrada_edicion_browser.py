"""P27.9 y P28.1 en DOM real: uv run --locked python -m tests.entrada_edicion_browser.

Abrir http://127.0.0.1:8889/__pruebas/. Sin dependencias nuevas.
El ClipboardEvent sintético vive solo en el runner; Ctrl+V se valida en Browser.
Con forced-colors activo, abrir /__pruebas/?forced-colors=1 para verificar colores de sistema.
"""

from pathlib import Path
from wsgiref.simple_server import make_server

from tests.operandos_browser import ServidorConHilos, aplicacion


def pruebas(environ, start_response):
    ruta = environ["PATH_INFO"]
    if ruta == "/__pruebas/":
        contenido = ('<!doctype html><html lang="es"><meta charset="utf-8">'
                     '<link rel="icon" href="/static/calculadora/favicon.svg">'
                     '<title>PyGebra: entrada y selección</title><h1>Entrada y selección P27.9 / P28.1</h1>'
                     '<ol id="resultados"></ol><p id="total">Ejecutando…</p>'
                     '<script src="/__pruebas/pruebas.js"></script></html>').encode()
        tipo = "text/html"
    elif ruta == "/__pruebas/pruebas.js":
        contenido = Path(__file__).with_suffix(".js").read_bytes()
        tipo = "text/javascript"
    else:
        return aplicacion(environ, start_response)
    start_response("200 OK", [("Content-Type", tipo + "; charset=utf-8"), ("Cache-Control", "no-store")])
    return [contenido]


if __name__ == "__main__":
    print("P27.9: http://127.0.0.1:8889/__pruebas/", flush=True)
    make_server("127.0.0.1", 8889, pruebas, server_class=ServidorConHilos).serve_forever()
