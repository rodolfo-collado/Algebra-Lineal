"""Regresiones en DOM real: uv run python -m tests.presentacion_browser.

Abrir http://127.0.0.1:8876/. Sin dependencias nuevas; sirve los componentes
y scripts de producción con valores exactos preparados por Django.
"""

import os
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "frontend.web.algebra_web.settings")
import django
django.setup()

from django.template import Context, Template

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "frontend/web/calculadora"


def fixture():
    contenido = Template('''{% load numeros %}
        <input id="entrada" value="1/3" aria-label="Entrada original">
        {% numeric_results %}<section id="resultado">
        {% include "calculadora/components/numeric_format.html" %}
        <code id="solucion">x1 = 1/3</code><code id="mitad">x2 = 1/2</code>
        <code id="entero">x3 = 4</code>
        <details id="pasos"><summary>Ver procedimiento</summary><code>F1 = (1/3)F1</code>
        <table aria-label="Matriz con factor 1/3"><tr><td>1/3</td><td>-1/3</td></tr></table></details>
        </section>{% endnumeric_results %}''').render(Context())
    base = (APP / "templates/calculadora/base.html").read_text(encoding="utf-8")
    tema_inicial = re.search(r"<script>(.*?)</script>", base, re.S).group(1)
    return f'''<!doctype html><html lang="es" data-theme="light"><meta charset="utf-8">
        <script>
        const seed = parent.seed || {{}};
        const memory = new Map(Object.entries(seed.values || {{}}));
        Object.defineProperty(window, "localStorage", {{value: {{
            getItem(key) {{ if(seed.blocked) throw new Error("sin almacenamiento"); return memory.get(key) ?? null; }},
            setItem(key, value) {{ if(seed.blocked) throw new Error("sin almacenamiento"); memory.set(key, value); }}
        }}}});
        window.requests = 0;
        window.fetch = () => {{ window.requests++; throw new Error("petición inesperada"); }};
        window.XMLHttpRequest = function() {{ window.requests++; throw new Error("petición inesperada"); }};
        {tema_inicial}
        </script><button id="theme-toggle"><span class="theme-toggle-text">Tema</span></button>
        {contenido}<script src="/numeros.js"></script><script src="/tema.js"></script></html>'''.encode()


class PaginaPruebas(BaseHTTPRequestHandler):
    def do_GET(self):
        recursos = {
            "/": ("text/html", b'<!doctype html><html lang="es"><meta charset="utf-8"><title>PyGebra: regresiones de presentacion</title><h1>Presentacion numerica y tema</h1><ol id="resultados"></ol><p id="total">Ejecutando...</p><script src="/pruebas.js"></script></html>'),
            "/fixture": ("text/html", fixture()),
            "/numeros.js": ("text/javascript", (APP / "static/calculadora/numeros.js").read_bytes()),
            "/tema.js": ("text/javascript", (APP / "static/calculadora/tema.js").read_bytes()),
            "/pruebas.js": ("text/javascript", (ROOT / "tests/presentacion_browser.js").read_bytes()),
        }
        recurso = recursos.get(urlsplit(self.path).path)
        if recurso is None:
            self.send_error(404)
            return
        tipo, contenido = recurso
        self.send_response(200)
        self.send_header("Content-Type", tipo + "; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(contenido)


if __name__ == "__main__":
    print("Pruebas DOM: http://127.0.0.1:8876/", flush=True)
    ThreadingHTTPServer(("127.0.0.1", 8876), PaginaPruebas).serve_forever()
