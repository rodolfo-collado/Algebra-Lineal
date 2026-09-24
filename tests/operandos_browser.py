"""Pruebas DOM con la aplicación real: python -m tests.operandos_browser.

Abrir http://127.0.0.1:8877/__pruebas/. No requiere dependencias nuevas.
"""

import os
from pathlib import Path
from wsgiref.simple_server import make_server

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "frontend.web.algebra_web.settings")

from django.core.wsgi import get_wsgi_application
from django.contrib.staticfiles.handlers import StaticFilesHandler

aplicacion = StaticFilesHandler(get_wsgi_application())


def pruebas(environ, start_response):
    ruta = environ["PATH_INFO"]
    if ruta == "/__pruebas/":
        contenido = ('<!doctype html><html lang="es"><meta charset="utf-8">'
                     '<title>PyGebra: operandos múltiples</title><h1>Operandos múltiples</h1>'
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
    print("Pruebas DOM: http://127.0.0.1:8877/__pruebas/", flush=True)
    make_server("127.0.0.1", 8877, pruebas).serve_forever()
