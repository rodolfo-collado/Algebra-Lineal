"""Cuaderno de resoluciones en DOM real: python -m tests.resoluciones_browser.

Abrir http://127.0.0.1:8907/__pruebas/. El cuaderno es un archivo temporal propio
(tests/__init__.py fija ALGEBRA_RESOLUCIONES); /__pruebas/reiniciar lo vacía entre casos.
"""

import os
from pathlib import Path
from wsgiref.simple_server import make_server

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "frontend.web.algebra_web.settings")

from tests.operandos_browser import ServidorConHilos, aplicacion  # noqa: E402

from frontend.web.calculadora.resoluciones.almacen import almacen  # noqa: E402


def vaciar():
    cuaderno = almacen()
    cuaderno.eliminar([fila["id"] for fila in cuaderno.listar()])
    for ejercicio in cuaderno.ejercicios():
        cuaderno.disolver_ejercicio(ejercicio["id"])


def pruebas(environ, start_response):
    ruta = environ["PATH_INFO"]
    if ruta == "/__pruebas/":
        contenido = ('<!doctype html><html lang="es"><meta charset="utf-8">'
                     '<title>PyGebra: cuaderno de resoluciones</title><h1>Cuaderno de resoluciones</h1>'
                     '<ol id="resultados"></ol><p id="total">Ejecutando…</p>'
                     '<script src="/__pruebas/pruebas.js"></script></html>').encode()
        tipo = "text/html"
    elif ruta == "/__pruebas/pruebas.js":
        contenido, tipo = Path(__file__).with_suffix(".js").read_bytes(), "text/javascript"
    elif ruta == "/__pruebas/reiniciar":
        vaciar()
        contenido, tipo = b"{}", "application/json"
    else:
        return aplicacion(environ, start_response)
    start_response("200 OK", [("Content-Type", tipo + "; charset=utf-8"), ("Cache-Control", "no-store")])
    return [contenido]


if __name__ == "__main__":
    print("Cuaderno de resoluciones: http://127.0.0.1:8907/__pruebas/", flush=True)
    make_server("127.0.0.1", 8907, pruebas, server_class=ServidorConHilos).serve_forever()
