"""P27.10 en DOM real: uv run --locked python -m tests.residual_browser.

Abrir http://127.0.0.1:8886/__pruebas/. Reutiliza la aplicación y el servidor
de runners existentes; sin dependencias nuevas. Tab real y forced-colors se
verifican además en Browser/Chromium.
"""

from pathlib import Path
from wsgiref.simple_server import make_server

from tests.operandos_browser import ServidorConHilos, aplicacion


def pruebas(environ, start_response):
    ruta = environ["PATH_INFO"]
    if ruta == "/__pruebas/":
        contenido = ('<!doctype html><html lang="es"><meta charset="utf-8">'
                     '<link rel="icon" href="/static/calculadora/favicon.svg">'
                     '<title>PyGebra: residual P27.10</title><h1>Accesibilidad y responsive P27.10</h1>'
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
    print("P27.10: http://127.0.0.1:8886/__pruebas/", flush=True)
    make_server("127.0.0.1", 8886, pruebas, server_class=ServidorConHilos).serve_forever()
