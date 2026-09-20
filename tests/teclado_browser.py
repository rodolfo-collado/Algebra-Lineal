"""Regresión DOM sin dependencias: uv run python -m tests.teclado_browser.

Abrir http://127.0.0.1:8766/ en un navegador. Cada caso usa un documento nuevo,
el componente Django real, el registro y el motor de producción.
"""

import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "frontend.web.algebra_web.settings")

import django

django.setup()

from django.template.loader import render_to_string

from frontend.web.calculadora.teclados import PERFILES, GrupoTeclas, Perfil, Tecla, perfiles_para


RAIZ = Path(__file__).resolve().parents[1]


def fixture():
    perfiles = perfiles_para(*PERFILES)
    # Un perfil ajeno a las herramientas demuestra que el motor admite extensiones.
    prueba = Perfil("prueba", (GrupoTeclas("Agrupación", (Tecla("( )", "()", "Paréntesis", 1),)),))
    perfiles[prueba.id] = {
        "ayuda": prueba.ayuda,
        "grupos": [{"nombre": "Agrupación", "teclas": [vars(prueba.teclas[0])]}],
    }
    componente = render_to_string("calculadora/components/math_keyboard.html", {"perfiles_teclado": perfiles})
    return f'''<!doctype html><html lang="es"><meta charset="utf-8"><title>Fixture teclado</title>
    <form id="entrada">
      <fieldset id="texto" data-perfil="sistema"><textarea aria-label="Texto" id="a"></textarea></fieldset>
      <fieldset id="celdas" data-perfil="numerico"><input aria-label="Celda" id="b" type="text"></fieldset>
      <input aria-label="Fuera de contexto" id="ajeno" type="text">
      <button type="button" id="otro">Otro control</button>
      {componente}
    </form><script src="/teclado.js"></script></html>'''.encode()


class PaginaPruebas(BaseHTTPRequestHandler):
    def do_GET(self):
        recursos = {
            "/": ("text/html", b'<!doctype html><html lang="es"><meta charset="utf-8"><title>Regresiones DOM P17</title><h1>Regresiones DOM P17</h1><ol id="resultados"></ol><p id="total">Ejecutando...</p><script src="/pruebas.js"></script></html>'),
            "/fixture": ("text/html", fixture()),
            "/teclado.js": ("text/javascript", (RAIZ / "frontend/web/calculadora/static/calculadora/teclado.js").read_bytes()),
            "/pruebas.js": ("text/javascript", (RAIZ / "tests/teclado_browser.js").read_bytes()),
        }
        if self.path not in recursos:
            self.send_error(404)
            return
        tipo, contenido = recursos[self.path]
        self.send_response(200)
        self.send_header("Content-Type", f"{tipo}; charset=utf-8")
        self.end_headers()
        self.wfile.write(contenido)


if __name__ == "__main__":
    print("Pruebas DOM: http://127.0.0.1:8766/", flush=True)
    ThreadingHTTPServer(("127.0.0.1", 8766), PaginaPruebas).serve_forever()
