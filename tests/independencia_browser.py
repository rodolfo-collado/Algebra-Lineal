"""Pruebas DOM de Independencia lineal: uv run --locked node tests/navegador.mjs independencia."""

from pathlib import Path
from wsgiref.simple_server import make_server

from tests.operandos_browser import ServidorConHilos, aplicacion


def pruebas(environ, start_response):
    ruta = environ["PATH_INFO"]
    if ruta == "/__pruebas/":
        contenido = ('<!doctype html><html lang="es"><meta charset="utf-8">'
                     '<link rel="icon" href="/static/calculadora/favicon.svg">'
                     '<title>Independencia lineal: pruebas DOM</title><h1>Independencia lineal</h1>'
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
    with make_server("127.0.0.1", 0, pruebas, server_class=ServidorConHilos) as servidor:
        print(f"Independencia lineal: http://127.0.0.1:{servidor.server_port}/__pruebas/", flush=True)
        servidor.serve_forever()
