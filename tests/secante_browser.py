"""Pruebas DOM de Secante en Métodos abiertos: uv run --locked python -m tests.secante_browser."""

from pathlib import Path
from wsgiref.simple_server import make_server
from tests.operandos_browser import ServidorConHilos, aplicacion


def pruebas(environ, start_response):
    if environ["PATH_INFO"] == "/__pruebas/":
        contenido = ('<!doctype html><html lang="es"><meta charset="utf-8">'
                     '<link rel="icon" href="/static/calculadora/favicon.svg">'
                     '<title>Secante: pruebas DOM</title><h1>Secante</h1>'
                     '<ol id="resultados"></ol><p id="total">Ejecutando…</p>'
                     '<script src="/__pruebas/pruebas.js"></script></html>').encode()
        tipo = "text/html"
    elif environ["PATH_INFO"] == "/__pruebas/pruebas.js":
        contenido = Path(__file__).with_suffix(".js").read_bytes()
        tipo = "text/javascript"
    else:
        return aplicacion(environ, start_response)
    start_response("200 OK", [("Content-Type", tipo + "; charset=utf-8")])
    return [contenido]


if __name__ == "__main__":
    print("Secante: http://127.0.0.1:8902/__pruebas/", flush=True)
    make_server("127.0.0.1", 8902, pruebas, server_class=ServidorConHilos).serve_forever()
