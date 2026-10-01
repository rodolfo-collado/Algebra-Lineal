"""DOM P26.9 en la aplicación real: python -m tests.inversa_browser.

Abrir http://127.0.0.1:8879/__pruebas/. No requiere dependencias nuevas.
"""

import os
from pathlib import Path
from socketserver import ThreadingMixIn
from wsgiref.simple_server import WSGIServer, make_server

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "frontend.web.algebra_web.settings")

from django.core.wsgi import get_wsgi_application
from django.contrib.staticfiles.handlers import StaticFilesHandler
from django.test import Client

aplicacion = StaticFilesHandler(get_wsgi_application())


def pruebas(environ, start_response):
    ruta = environ["PATH_INFO"]
    if ruta == "/__pruebas/":
        contenido = ('<!doctype html><html lang="es"><meta charset="utf-8">'
                     '<title>PyGebra: propiedades de la inversa</title><h1>Propiedades de la inversa</h1>'
                     '<ol id="resultados"></ol><p id="total">Ejecutando…</p>'
                     '<script src="/__pruebas/pruebas.js"></script></html>').encode()
        tipo = "text/html"
    elif ruta == "/__pruebas/pruebas.js":
        contenido = Path(__file__).with_suffix(".js").read_bytes()
        tipo = "text/javascript"
    elif ruta == "/__pruebas/inicial-3/":
        # Documento que comienza fuera de 2×2, para ejercitar la plantilla
        # inerte del método sin depender de una transición previa desde 2×2.
        contenido = Client().post("/matrices/inversa/", {"orden": "3", "ajustar": "1"}).content
        tipo = "text/html"
    else:
        return aplicacion(environ, start_response)
    start_response("200 OK", [("Content-Type", tipo + "; charset=utf-8"), ("Cache-Control", "no-store")])
    return [contenido]


class ServidorConHilos(ThreadingMixIn, WSGIServer):
    daemon_threads = True


if __name__ == "__main__":
    print("Pruebas DOM: http://127.0.0.1:8879/__pruebas/", flush=True)
    make_server("127.0.0.1", 8879, pruebas, server_class=ServidorConHilos).serve_forever()
