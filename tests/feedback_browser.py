"""P27.4 en DOM real: uv run --locked python -m tests.feedback_browser.

Abrir http://127.0.0.1:8880/__pruebas/. Reutiliza el servidor de pruebas existente.
"""

from pathlib import Path
from wsgiref.simple_server import make_server

from tests.operandos_browser import aplicacion, ServidorConHilos


def pruebas(environ, start_response):
    ruta = environ["PATH_INFO"]
    if ruta == "/__pruebas/":
        contenido = ('<!doctype html><html lang="es"><meta charset="utf-8">'
                     '<title>PyGebra: feedback P27.4</title><h1>Feedback P27.4</h1>'
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
    print("Pruebas DOM: http://127.0.0.1:8880/__pruebas/", flush=True)
    make_server("127.0.0.1", 8880, pruebas, server_class=ServidorConHilos).serve_forever()
