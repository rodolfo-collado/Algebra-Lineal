"""P27.5 en DOM real: uv run --locked python -m tests.buscador_browser.

Abrir http://127.0.0.1:8881/__pruebas/. Sin dependencias nuevas.
"""

import json
from pathlib import Path
from wsgiref.simple_server import make_server

from tests.operandos_browser import aplicacion, ServidorConHilos
from frontend.web.calculadora import catalogo


CONSULTAS = (
    "matriz", "sistema de ecuaciones", "resolver sistema", "gauss", "inversa",
    "multiplicar matrices", "límites", "calcular inversa", "invertir matriz",
    "sumar vectores", "convertir a binario", "método de gauss", "transponer",
    "pasar decimal a binario", "restar vectores", "reducir matriz",
    "  MÉTODO   de GAUSS  ", "CALCULAR\u0085la\u00a0INVERSA", "li\u0301mites",
    "sistemas lineales", "ecuaciones lineales", "gauss binario", "zzz",
    "calcular la", "método de", "\ufeffinversa", "\ufeff", *catalogo.PALABRAS_VACIAS,
)


def pruebas(environ, start_response):
    ruta = environ["PATH_INFO"]
    if ruta == "/__pruebas/":
        contenido = ('<!doctype html><html lang="es"><meta charset="utf-8">'
                     '<link rel="icon" href="/static/calculadora/favicon.svg">'
                     '<title>PyGebra: buscador P27.5</title><h1>Buscador P27.5</h1>'
                     '<ol id="resultados"></ol><p id="total">Ejecutando…</p>'
                     '<script src="/__pruebas/pruebas.js"></script></html>').encode()
        tipo = "text/html"
    elif ruta == "/__pruebas/pruebas.js":
        contenido = Path(__file__).with_suffix(".js").read_bytes()
        tipo = "text/javascript"
    elif ruta == "/__pruebas/contrato.json":
        contenido = json.dumps([
            {"consulta": consulta, "ids": [h.id for h in catalogo.buscar_herramientas(consulta)]}
            for consulta in CONSULTAS
        ]).encode()
        tipo = "application/json"
    else:
        return aplicacion(environ, start_response)
    start_response("200 OK", [("Content-Type", tipo + "; charset=utf-8"), ("Cache-Control", "no-store")])
    return [contenido]


if __name__ == "__main__":
    print("Pruebas DOM: http://127.0.0.1:8881/__pruebas/", flush=True)
    make_server("127.0.0.1", 8881, pruebas, server_class=ServidorConHilos).serve_forever()
