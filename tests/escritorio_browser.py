"""P27.7 en DOM real: uv run --locked python -m tests.escritorio_browser.

Abrir http://127.0.0.1:8882/__pruebas/. Sirve la app real con DEBUG=False en modo
escritorio (o web con la cookie p277=web) y un archivo de preferencias temporal.
No sustituye la prueba en WebView2: aquí no existen el menú nativo ni sus atajos.
"""

import json
import os
import tempfile
import time
from pathlib import Path
from wsgiref.simple_server import make_server

# Las páginas de error propias solo se usan con DEBUG=False, como en escritorio.
os.environ["DJANGO_DEBUG"] = "0"

from django.core.exceptions import PermissionDenied, SuspiciousOperation  # noqa: E402
from django.core.handlers.wsgi import WSGIRequest  # noqa: E402
from django.test import override_settings  # noqa: E402
from django.views import csrf, defaults  # noqa: E402

from tests.operandos_browser import ServidorConHilos, aplicacion  # noqa: E402

ARCHIVO = Path(tempfile.mkdtemp(prefix="pygebra-p277-")) / "PyGebra" / "preferencias.json"
ERRORES = {
    "400": lambda request: defaults.bad_request(request, SuspiciousOperation("detalle interno")),
    "403": lambda request: defaults.permission_denied(request, PermissionDenied("detalle interno")),
    "csrf": lambda request: csrf.csrf_failure(request, reason="CSRF cookie not set."),
    "500": defaults.server_error,
}


def responder(start_response, contenido, tipo="text/html", estado="200 OK"):
    start_response(estado, [("Content-Type", tipo + "; charset=utf-8"), ("Cache-Control", "no-store")])
    return [contenido]


def pruebas(environ, start_response):
    ruta = environ["PATH_INFO"]
    escritorio = "p277=web" not in environ.get("HTTP_COOKIE", "")
    ajustes = override_settings(DESKTOP_MODE=escritorio, DESKTOP_PREFERENCES_FILE=str(ARCHIVO))
    if ruta == "/__pruebas/":
        return responder(start_response, (
            '<!doctype html><html lang="es"><meta charset="utf-8">'
            '<link rel="icon" href="/static/calculadora/favicon.svg">'
            '<title>PyGebra: escritorio P27.7</title><h1>Escritorio P27.7</h1>'
            '<ol id="resultados"></ol><p id="total">Ejecutando…</p>'
            '<script src="/__pruebas/pruebas.js"></script></html>').encode())
    if ruta == "/__pruebas/pruebas.js":
        return responder(start_response, Path(__file__).with_suffix(".js").read_bytes(), "text/javascript")
    if ruta == "/__pruebas/preferencias":
        contenido = ARCHIVO.read_bytes() if ARCHIVO.exists() else b"{}"
        return responder(start_response, contenido, "application/json")
    if ruta == "/__pruebas/reiniciar":
        ARCHIVO.unlink(missing_ok=True)
        return responder(start_response, json.dumps({"archivo": str(ARCHIVO)}).encode(), "application/json")
    if ruta.startswith("/__pruebas/error/"):
        with ajustes:
            respuesta = ERRORES[ruta.rstrip("/").rsplit("/", 1)[-1]](WSGIRequest(environ))
        return responder(start_response, respuesta.content, estado=f"{respuesta.status_code} {respuesta.reason_phrase}")
    if ruta == "/__pruebas/preferencia-lenta/":
        time.sleep(0.4)
        environ["PATH_INFO"] = "/preferencias/"
    with ajustes:
        # Django renderiza dentro de la llamada; los estáticos no dependen del modo.
        return aplicacion(environ, start_response)


if __name__ == "__main__":
    print("P27.7: http://127.0.0.1:8882/__pruebas/", flush=True)
    make_server("127.0.0.1", 8882, pruebas, server_class=ServidorConHilos).serve_forever()
