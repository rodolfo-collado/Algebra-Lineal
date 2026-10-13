"""Menú de edición (clic derecho) en DOM real: uv run --locked python -m tests.menu_edicion_browser.

Abrir http://127.0.0.1:8890/__pruebas/. Sin dependencias nuevas. Los casos usan la aplicación
Django y los scripts de producción; contextmenu y teclas son eventos sintéticos en cada iframe.
/__pruebas/romanos/ comprueba con el backend cada romano que escribe el navegador.
"""

import json
from pathlib import Path
from wsgiref.simple_server import make_server

from backend.sistemas_numericos import romano_a_decimal
from tests.operandos_browser import ServidorConHilos, aplicacion


def romanos_invalidos(pares):
    """[[n, texto], …] → los pares que romano_a_decimal no lee exactamente como n."""
    invalidos = []
    for valor, texto in pares:
        try:
            if romano_a_decimal(texto).resultado != valor:
                invalidos.append([valor, texto])
        except ValueError as error:
            invalidos.append([valor, texto, str(error)])
    return invalidos


def pruebas(environ, start_response):
    ruta = environ["PATH_INFO"]
    if ruta == "/__pruebas/":
        contenido = ('<!doctype html><html lang="es"><meta charset="utf-8">'
                     '<link rel="icon" href="/static/calculadora/favicon.svg">'
                     '<title>PyGebra: menú de edición</title><h1>Menú de edición: seleccionar, rellenar y limpiar</h1>'
                     '<ol id="resultados"></ol><p id="total">Ejecutando…</p>'
                     '<script src="/__pruebas/pruebas.js"></script></html>').encode()
        tipo = "text/html"
    elif ruta == "/__pruebas/pruebas.js":
        contenido = Path(__file__).with_suffix(".js").read_bytes()
        tipo = "text/javascript"
    elif ruta == "/__pruebas/romanos/" and environ["REQUEST_METHOD"] == "POST":
        largo = int(environ.get("CONTENT_LENGTH") or 0)
        contenido = json.dumps(romanos_invalidos(json.loads(environ["wsgi.input"].read(largo)))).encode()
        tipo = "application/json"
    else:
        return aplicacion(environ, start_response)
    start_response("200 OK", [("Content-Type", tipo + "; charset=utf-8"), ("Cache-Control", "no-store")])
    return [contenido]


if __name__ == "__main__":
    print("Menú de edición: http://127.0.0.1:8890/__pruebas/", flush=True)
    make_server("127.0.0.1", 8890, pruebas, server_class=ServidorConHilos).serve_forever()
